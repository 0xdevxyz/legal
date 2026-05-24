import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

VAULT_ROOT = Path(os.getenv("KNOWLEDGE_VAULT_PATH", "/home/clawd/saas/legal/knowledge"))
META_DIR = VAULT_ROOT / "_meta"
EMBEDDINGS_CACHE_FILE = META_DIR / "embeddings.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _parse_md_file(filepath: Path) -> Optional[Dict[str, Any]]:
    try:
        text = filepath.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {"path": str(filepath), "frontmatter": {}, "body": text, "full_text": text}

        parts = text.split("---", 2)
        if len(parts) < 3:
            return None

        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()

        return {
            "path": str(filepath),
            "filename": filepath.name,
            "frontmatter": fm,
            "body": body,
            "full_text": f"{fm.get('title', '')} {body}",
            "content_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
        }
    except Exception as e:
        logger.warning(f"Could not parse {filepath}: {e}")
        return None


class KnowledgeRetriever:
    def __init__(self, vault_root: Optional[Path] = None):
        self.vault_root = vault_root or VAULT_ROOT
        self._embeddings_cache: Dict[str, Dict[str, Any]] = {}
        self._documents: List[Dict[str, Any]] = []
        self._openai_client = None
        META_DIR.mkdir(parents=True, exist_ok=True)
        self._load_cache()

    def _get_client(self):
        if not self._openai_client and OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            except ImportError:
                logger.warning("openai not installed, keyword-based fallback will be used")
        return self._openai_client

    def _load_cache(self):
        if EMBEDDINGS_CACHE_FILE.exists():
            try:
                self._embeddings_cache = json.loads(EMBEDDINGS_CACHE_FILE.read_text())
                logger.debug(f"Loaded {len(self._embeddings_cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Could not load embeddings cache: {e}")
                self._embeddings_cache = {}

    def _save_cache(self):
        try:
            EMBEDDINGS_CACHE_FILE.write_text(json.dumps(self._embeddings_cache, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Could not save embeddings cache: {e}")

    def _load_documents(self) -> List[Dict[str, Any]]:
        docs = []
        for pattern in ["updates/*.md", "laws/*.md", "patterns/*.md"]:
            for filepath in sorted(self.vault_root.glob(pattern)):
                doc = _parse_md_file(filepath)
                if doc:
                    docs.append(doc)
        logger.debug(f"Loaded {len(docs)} documents from vault")
        return docs

    async def _embed_text(self, text: str) -> Optional[List[float]]:
        client = self._get_client()
        if not client:
            return None
        try:
            text_clean = text[:8000].replace("\n", " ")
            response = await client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text_clean,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            return None

    def _keyword_score(self, query: str, doc: Dict[str, Any]) -> float:
        query_lower = query.lower()
        text_lower = doc.get("full_text", "").lower()
        words = query_lower.split()
        hits = sum(1 for w in words if w in text_lower and len(w) > 3)
        return hits / max(len(words), 1)

    async def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.1) -> List[Dict[str, Any]]:
        documents = self._load_documents()
        if not documents:
            return []

        query_embedding = await self._embed_text(query)

        scored: List[Tuple[float, Dict[str, Any]]] = []

        for doc in documents:
            cache_key = doc["content_hash"]
            doc_embedding = self._embeddings_cache.get(cache_key, {}).get("vector")

            if query_embedding and doc_embedding:
                score = _cosine_similarity(query_embedding, doc_embedding)
            else:
                score = self._keyword_score(query, doc)

            fm = doc.get("frontmatter", {})
            relevance_boost = float(fm.get("relevance_score", 0.5)) * 0.1
            score += relevance_boost

            if score >= min_score:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "score": round(score, 4),
                "title": doc.get("frontmatter", {}).get("title", doc.get("filename", "")),
                "category": doc.get("frontmatter", {}).get("category", ""),
                "law_areas": doc.get("frontmatter", {}).get("law_areas", []),
                "impact": doc.get("frontmatter", {}).get("impact", ""),
                "date": doc.get("frontmatter", {}).get("date", ""),
                "source_url": doc.get("frontmatter", {}).get("source_url", ""),
                "summary": doc.get("body", "")[:400],
                "path": doc.get("path", ""),
                "filename": doc.get("filename", ""),
            }
            for score, doc in scored[:top_k]
        ]

    async def refresh_index(self) -> Dict[str, int]:
        documents = self._load_documents()
        new_count = 0
        skip_count = 0

        for doc in documents:
            cache_key = doc["content_hash"]
            if cache_key in self._embeddings_cache:
                skip_count += 1
                continue

            embedding = await self._embed_text(doc["full_text"])
            if embedding:
                self._embeddings_cache[cache_key] = {
                    "vector": embedding,
                    "path": doc["path"],
                    "title": doc.get("frontmatter", {}).get("title", ""),
                }
                new_count += 1
            else:
                skip_count += 1

        if new_count > 0:
            self._save_cache()

        logger.info(f"Index refresh: {new_count} new, {skip_count} skipped")
        return {"new": new_count, "skipped": skip_count, "total": len(documents)}

    async def search_hybrid(self, query: str, top_k: int = 5, language: str = "de") -> List[Dict]:
        documents = self._load_documents()
        if not documents:
            return []

        query_embedding = await self._embed_text(query)
        scored: List[Tuple[float, Dict[str, Any], str]] = []

        try:
            for doc in documents:
                fm = doc.get("frontmatter", {})
                doc_language = fm.get("language", "de")
                if doc_language != language:
                    continue

                bm25_score = self._keyword_score(query, doc)
                embedding_score = 0.0
                cache_key = doc.get("content_hash", "")
                doc_embedding = self._embeddings_cache.get(cache_key, {}).get("vector")

                if query_embedding and doc_embedding:
                    embedding_score = _cosine_similarity(query_embedding, doc_embedding)

                score = (0.4 * bm25_score) + (0.6 * embedding_score)
                if not query_embedding or not doc_embedding:
                    score = bm25_score

                if score <= 0:
                    continue

                if bm25_score > 0 and embedding_score > 0:
                    match_type = "hybrid"
                elif embedding_score > 0:
                    match_type = "embedding"
                else:
                    match_type = "keyword"

                scored.append((score, doc, match_type))

            scored.sort(key=lambda x: x[0], reverse=True)

            return [
                {
                    "doc_id": doc.get("filename", doc.get("path", "")),
                    "content": doc.get("body", doc.get("full_text", "")),
                    "score": round(score, 4),
                    "law_refs": doc.get("frontmatter", {}).get("law_areas", []),
                    "match_type": match_type,
                }
                for score, doc, match_type in scored[:top_k]
            ]
        except Exception as e:
            logger.warning(f"Hybrid search failed: {e}")
            return []

    async def get_applicable_laws(self, text: str) -> List[Dict]:
        try:
            results = await self.search_hybrid(text, top_k=5)
            law_scores: Dict[str, float] = {}

            for result in results:
                for law in result.get("law_refs", []):
                    law_scores[law] = law_scores.get(law, 0.0) + float(result.get("score", 0.0))

            total_score = sum(law_scores.values()) or 1.0
            laws = [
                {
                    "law": law,
                    "confidence": round(min(score / total_score, 1.0), 4),
                }
                for law, score in sorted(law_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            ]
            return laws
        except Exception as e:
            logger.warning(f"Applicable law detection failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        documents = self._load_documents()
        by_category: Dict[str, int] = {}
        by_impact: Dict[str, int] = {}

        for doc in documents:
            fm = doc.get("frontmatter", {})
            cat = fm.get("category", "unknown")
            imp = fm.get("impact", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            by_impact[imp] = by_impact.get(imp, 0) + 1

        return {
            "total_documents": len(documents),
            "cached_embeddings": len(self._embeddings_cache),
            "by_category": by_category,
            "by_impact": by_impact,
        }
