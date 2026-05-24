import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

VAULT_ROOT = Path(os.getenv("KNOWLEDGE_VAULT_PATH", "/home/clawd/saas/legal/knowledge"))


def _get_retriever():
    from knowledge.knowledge_retriever import KnowledgeRetriever
    return KnowledgeRetriever()


@router.get("/updates")
async def get_recent_updates(
    limit: int = Query(20, ge=1, le=100),
    impact: Optional[str] = Query(None, regex="^(high|medium|low)$"),
    law_area: Optional[str] = None,
):
    """Neueste Wissens-Updates aus dem Vault."""
    updates_dir = VAULT_ROOT / "updates"
    if not updates_dir.exists():
        return {"updates": [], "total": 0}

    import yaml
    items: List[Dict[str, Any]] = []

    for filepath in sorted(updates_dir.glob("*.md"), reverse=True):
        try:
            text = filepath.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            fm = yaml.safe_load(parts[1]) or {}

            if impact and fm.get("impact") != impact:
                continue
            if law_area and law_area not in (fm.get("law_areas") or []):
                continue

            items.append({
                "id": filepath.stem,
                "title": fm.get("title", filepath.stem),
                "date": str(fm.get("date", "")),
                "category": fm.get("category", ""),
                "law_areas": fm.get("law_areas", []),
                "impact": fm.get("impact", ""),
                "relevance_score": fm.get("relevance_score", 0),
                "source_type": fm.get("source_type", ""),
                "source_url": fm.get("source_url", ""),
                "tags": fm.get("tags", []),
                "obsidian_deep_link": f"obsidian://open?vault=knowledge&file=updates%2F{filepath.stem}",
                "filename": filepath.name,
            })

            if len(items) >= limit:
                break
        except Exception as e:
            logger.warning(f"Could not parse {filepath.name}: {e}")

    return {"updates": items, "total": len(items)}


@router.get("/updates/{update_id}")
async def get_update_detail(update_id: str):
    """Vollständiges Update-Dokument."""
    filepath = VAULT_ROOT / "updates" / f"{update_id}.md"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Update not found")

    import yaml
    text = filepath.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"id": update_id, "content": text}

    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()

    return {
        "id": update_id,
        "frontmatter": fm,
        "content": body,
        "obsidian_deep_link": f"obsidian://open?vault=knowledge&file=updates%2F{update_id}",
    }


@router.get("/laws")
async def get_law_pages():
    """Alle Law-Stammseiten."""
    laws_dir = VAULT_ROOT / "laws"
    if not laws_dir.exists():
        return {"laws": []}

    import yaml
    laws = []
    for filepath in sorted(laws_dir.glob("*.md")):
        try:
            text = filepath.read_text(encoding="utf-8")
            parts = text.split("---", 2)
            fm = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
            laws.append({
                "id": filepath.stem,
                "title": fm.get("title", filepath.stem),
                "law_areas": fm.get("law_areas", []),
                "affected_checks": fm.get("affected_checks", []),
                "tags": fm.get("tags", []),
                "obsidian_deep_link": f"obsidian://open?vault=knowledge&file=laws%2F{filepath.stem}",
            })
        except Exception as e:
            logger.warning(f"Could not parse {filepath.name}: {e}")

    return {"laws": laws}


@router.get("/search")
async def search_knowledge(q: str = Query(..., min_length=2), top_k: int = Query(10, ge=1, le=30)):
    """Semantic Search über den gesamten Knowledge Vault."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        retriever = _get_retriever()
        results = await retriever.retrieve(q, top_k=top_k)
        return {"query": q, "results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        raise HTTPException(status_code=500, detail="Search temporarily unavailable")


@router.get("/stats")
async def get_vault_stats():
    """Vault-Statistiken."""
    try:
        retriever = _get_retriever()
        stats = retriever.get_stats()
        stats["vault_path"] = str(VAULT_ROOT)
        stats["last_checked"] = datetime.now().isoformat()
        return stats
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return {"error": str(e), "last_checked": datetime.now().isoformat()}


@router.post("/trigger-refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    """Manueller Update-Trigger (Admin). Startet Knowledge-Update im Hintergrund."""
    async def run_update():
        try:
            from knowledge.knowledge_ingestion_service import KnowledgeIngestionService
            from knowledge.knowledge_classifier import KnowledgeClassifier
            from knowledge.md_writer import MDWriter
            from knowledge.knowledge_retriever import KnowledgeRetriever

            ingestion = KnowledgeIngestionService()
            classifier = KnowledgeClassifier()
            writer = MDWriter()
            retriever = KnowledgeRetriever()

            raw_items = await ingestion.ingest_all()
            classified = await classifier.classify_batch(raw_items)
            writer.write_batch(classified)
            await retriever.refresh_index()
            await ingestion.close()
            logger.info(f"Manual refresh complete: {len(classified)} items processed")
        except Exception as e:
            logger.error(f"Manual refresh failed: {e}")

    background_tasks.add_task(run_update)
    return {"status": "started", "message": "Knowledge refresh running in background"}
