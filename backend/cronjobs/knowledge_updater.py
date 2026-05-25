#!/usr/bin/env python3
"""
Knowledge Updater Cronjob
Läuft täglich um 07:00 Uhr.
Fetcht neue Compliance-Infos, klassifiziert sie mit KI und schreibt .md-Files in den Vault.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/complyo-knowledge-updater.log", mode="a"),
    ],
)
logger = logging.getLogger("knowledge_updater")

DATABASE_URL = os.getenv("DATABASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
KNOWLEDGE_VAULT_PATH = os.getenv(
    "KNOWLEDGE_VAULT_PATH", "/home/clawd/saas/legal/knowledge"
)


async def send_slack_notification(message: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(SLACK_WEBHOOK_URL, json={"text": message})
    except Exception as e:
        logger.warning(f"Slack notification failed: {e}")


async def run_knowledge_update():
    logger.info("=" * 60)
    logger.info(f"Knowledge Updater gestartet: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    db_pool = None
    if DATABASE_URL:
        try:
            import asyncpg
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
            logger.info("DB-Verbindung hergestellt")
        except Exception as e:
            logger.warning(f"DB-Verbindung fehlgeschlagen, ohne DB-Quellen: {e}")

    try:
        from knowledge.knowledge_ingestion_service import KnowledgeIngestionService
        from knowledge.knowledge_classifier import KnowledgeClassifier
        from knowledge.md_writer import MDWriter
        from knowledge.knowledge_retriever import KnowledgeRetriever

        ingestion = KnowledgeIngestionService(db_pool)
        classifier = KnowledgeClassifier()
        writer = MDWriter()
        retriever = KnowledgeRetriever()

        logger.info("Schritt 1/5: Daten-Ingestion...")
        raw_items = await ingestion.ingest_all()
        logger.info(f"  → {len(raw_items)} unique Items gefunden")

        logger.info("Schritt 2/5: KI-Klassifizierung...")
        classified_items = await classifier.classify_batch(raw_items)
        logger.info(f"  → {len(classified_items)} Items über Relevanz-Schwelle (>=0.6)")

        high_impact = [i for i in classified_items if i.impact == "high"]
        medium_impact = [i for i in classified_items if i.impact == "medium"]
        low_impact = [i for i in classified_items if i.impact == "low"]
        logger.info(f"  → High: {len(high_impact)} | Medium: {len(medium_impact)} | Low: {len(low_impact)}")

        logger.info("Schritt 3/5: .md-Files schreiben...")
        written_paths = writer.write_batch(classified_items)
        logger.info(f"  → {len(written_paths)} Dateien geschrieben")

        logger.info("Schritt 4/5: RAG-Index aktualisieren...")
        await retriever.refresh_index()
        logger.info("  → Index aktualisiert")

        logger.info("Schritt 5/5: Rule-Review für High-Impact Updates...")
        if db_pool and high_impact:
            await _trigger_rule_reviews(db_pool, high_impact)

        await ingestion.close()

        summary = (
            f"*complyo Knowledge Update – {datetime.now().strftime('%Y-%m-%d')}*\n"
            f"Neue Items gesamt: {len(classified_items)}\n"
            f":red_circle: High-Impact: {len(high_impact)}\n"
            f":large_yellow_circle: Medium: {len(medium_impact)}\n"
            f":white_circle: Low: {len(low_impact)}\n"
        )

        if high_impact:
            summary += "\n*High-Impact Updates:*\n"
            for item in high_impact[:5]:
                summary += f"• {item.title} ({', '.join(item.law_areas)})\n"

        logger.info("Update-Zusammenfassung:\n" + summary)

        if high_impact:
            await send_slack_notification(summary)

        logger.info("Knowledge Updater erfolgreich abgeschlossen")
        return {"success": True, "items_written": len(written_paths), "high_impact": len(high_impact)}

    except Exception as e:
        logger.error(f"Kritischer Fehler im Knowledge Updater: {e}", exc_info=True)
        await send_slack_notification(f":x: Knowledge Updater Fehler: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if db_pool:
            await db_pool.close()


async def _trigger_rule_reviews(db_pool, high_impact_items):
    try:
        from compliance_engine.rule_versioning_service import RuleVersioningService
        service = RuleVersioningService(db_pool)

        for item in high_impact_items:
            for check in item.affected_checks:
                logger.info(f"  Rule-Review für Check: {check} (Grund: {item.title[:50]})")
                async with db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO knowledge_rule_review_queue
                        (check_name, knowledge_file, title, law_areas, impact, created_at)
                        VALUES ($1, $2, $3, $4, $5, NOW())
                        ON CONFLICT (check_name, knowledge_file) DO NOTHING
                        """,
                        check,
                        f"{item.date}-{item.slug}.md",
                        item.title,
                        item.law_areas,
                        item.impact,
                    )
    except Exception as e:
        logger.warning(f"Rule-Review trigger fehlgeschlagen (non-critical): {e}")


if __name__ == "__main__":
    result = asyncio.run(run_knowledge_update())
    sys.exit(0 if result.get("success") else 1)
