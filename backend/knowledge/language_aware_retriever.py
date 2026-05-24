import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency fallback
    yaml = None

from backend.knowledge.knowledge_retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class LanguageAwareRetriever:
    def __init__(self, base_retriever: KnowledgeRetriever):
        self.base_retriever = base_retriever
        self.vault_root = base_retriever.vault_root
        self.laws_root = self.vault_root / "laws"
        self.mapping_file = self.laws_root / "_mapping.yaml"

    def detect_language(self, text: str) -> str:
        try:
            tokens = {token.strip(".,;:!?()[]{}\"'").lower() for token in text.split()}
            language_markers = {
                "de": {"die", "der", "das", "und", "oder", "ist", "für", "mit"},
                "en": {"the", "and", "or", "is", "for", "with"},
                "fr": {"le", "la", "les", "et", "ou", "est", "pour", "avec"},
            }
            scores = {
                language: len(tokens.intersection(markers))
                for language, markers in language_markers.items()
            }
            best_language = max(scores, key=scores.get)
            return best_language if scores[best_language] > 0 else "de"
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "de"

    async def search_multilingual(self, query: str, top_k: int = 5) -> List[Dict]:
        language = self.detect_language(query)
        try:
            results = await self.base_retriever.search_hybrid(query, top_k=top_k, language=language)
            language_dir = str(self.laws_root / language)
            filtered_results = [
                result for result in results
                if language_dir in result.get("doc_id", "") or language_dir in result.get("path", "")
            ]
            if filtered_results:
                return filtered_results[:top_k]

            results = await self.base_retriever.search_hybrid(query, top_k=top_k, language=language)
            if results:
                return results

            return await self.base_retriever.retrieve(query, top_k=top_k)
        except Exception as e:
            logger.warning(f"Multilingual search failed: {e}")
            try:
                return await self.base_retriever.retrieve(query, top_k=top_k)
            except Exception as fallback_error:
                logger.warning(f"Fallback retrieval failed: {fallback_error}")
                return []

    def _load_mapping(self) -> Dict[str, Any]:
        try:
            if not self.mapping_file.exists():
                return {}
            if yaml:
                return yaml.safe_load(self.mapping_file.read_text(encoding="utf-8")) or {}
            return {"raw": self.mapping_file.read_text(encoding="utf-8")}
        except Exception as e:
            logger.warning(f"Could not load norm mapping: {e}")
            return {}

    def _parse_mapping_text(self, law_id: str, target_language: str) -> Optional[Dict]:
        try:
            text = self.mapping_file.read_text(encoding="utf-8")
            blocks = text.split("\n  - de_id:")
            law_id_lower = law_id.lower()
            for block in blocks[1:]:
                candidate = "de_id:" + block
                if law_id_lower not in candidate.lower():
                    continue
                translation = None
                marker = f"      {target_language}: "
                for line in candidate.splitlines():
                    if line.startswith(marker):
                        translation = line.split(": ", 1)[1].strip().strip('"')
                        break
                return {
                    "law_id": law_id,
                    "target_language": target_language,
                    "translation": translation,
                    "raw": candidate.strip(),
                }
            return None
        except Exception as e:
            logger.warning(f"Fallback norm mapping parse failed: {e}")
            return None

    def get_norm_mapping(self, law_id: str, target_language: str) -> Optional[Dict]:
        try:
            mapping = self._load_mapping()
            if not mapping:
                return None

            if "raw" in mapping:
                return self._parse_mapping_text(law_id, target_language)

            law_id_lower = law_id.lower()
            for item in mapping.get("mappings", []):
                identifiers = [
                    str(item.get("de_id", "")),
                    str(item.get("eu_id", "")),
                    str(item.get("eur_lex_id", "")),
                ]
                if law_id_lower not in [identifier.lower() for identifier in identifiers]:
                    continue

                return {
                    "law_id": law_id,
                    "target_language": target_language,
                    "de_id": item.get("de_id"),
                    "eu_id": item.get("eu_id"),
                    "translation": item.get("translations", {}).get(target_language),
                    "eur_lex_id": item.get("eur_lex_id"),
                    "official_url": item.get("official_url"),
                    "article_mappings": item.get("article_mappings", []),
                }
            return None
        except Exception as e:
            logger.warning(f"Norm mapping lookup failed: {e}")
            return None
