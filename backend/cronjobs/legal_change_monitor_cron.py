#!/usr/bin/env python3
"""
Legal Change Monitor Cronjob
============================
Läuft täglich. Führt die VOLLSTÄNDIGE Legal-Change-Pipeline aus:

    Erkennung (LLM)  →  legal_updates  →  Regel-Versionierung
                     →  Rechtstext-Regeneration
                     →  automatische Erzeugung deklarativer Website-Prüfungen
                        (compliance_checks; in Testphase als 'pending_review')

Vorher war dieser Monitor in KEINEM Cron eingetragen und lief faktisch nie —
deshalb wurden neue Pflichten (z.B. der Widerrufsbutton) nie aufgegriffen.
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
        logging.FileHandler("/var/log/complyo-legal-monitor.log", mode="a"),
    ],
)
logger = logging.getLogger("legal_change_monitor_cron")

DATABASE_URL = os.getenv("DATABASE_URL", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


async def run() -> int:
    logger.info("=" * 60)
    logger.info(f"Legal Change Monitor gestartet: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    if not DATABASE_URL:
        logger.error("DATABASE_URL fehlt — Abbruch")
        return 1
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY fehlt — Monitor kann keine Änderungen erkennen")
        return 1

    import asyncpg
    from legal_change_monitor import LegalChangeMonitor

    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
    try:
        monitor = LegalChangeMonitor(OPENROUTER_API_KEY, db_pool=db_pool)
        summary = await monitor.monitor_and_persist()
        checks_created = sum(1 for c in summary.get("generated_checks", []) if c.get("created"))
        logger.info(
            f"Fertig: {summary.get('detected', 0)} erkannt, "
            f"{summary.get('new_saved', 0)} neu, "
            f"{checks_created} neue Prüfungen erzeugt "
            f"(Status hängt an AUTO_ACTIVATE_GENERATED_CHECKS)."
        )
        return 0
    except Exception as e:
        logger.error(f"Legal Change Monitor fehlgeschlagen: {e}", exc_info=True)
        return 1
    finally:
        await db_pool.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
