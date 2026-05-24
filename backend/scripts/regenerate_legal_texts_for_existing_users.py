"""
regenerate_legal_texts_for_existing_users.py

Migriert Bestandsuser vom alten eRecht24-System auf den neuen internen Generator.
Läuft einmalig nach Deployment und ist idempotent.

Ausführung:
    python3 regenerate_legal_texts_for_existing_users.py [--dry-run] [--user-id=123]
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DB_URL = os.getenv("DATABASE_URL")


async def get_affected_users(conn: asyncpg.Connection) -> list:
    return await conn.fetch(
        """
        SELECT DISTINCT u.id, u.email, u.company_name
        FROM users u
        WHERE EXISTS (
            SELECT 1 FROM _archived_erecht24_projects ep
            WHERE ep.user_id = u.id
        )
        AND NOT EXISTS (
            SELECT 1 FROM generated_documents gd
            WHERE gd.user_id = u.id
              AND (gd.metadata->>'generator') = 'legal_text_generator'
        )
        ORDER BY u.id
        """
    )


async def regenerate_for_user(
    conn: asyncpg.Connection,
    user_id: int,
    company_name: str,
    dry_run: bool,
) -> dict:
    if dry_run:
        logger.info(f"[DRY-RUN] Würde Rechtstexte für User {user_id} ({company_name}) re-generieren")
        return {"user_id": user_id, "dry_run": True, "generated": 0}

    pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=3)
    try:
        from legal_text_generator import LegalTextGenerator, DocumentType

        generator = LegalTextGenerator(pool)
        user_data = {
            "company_name": company_name or f"Unternehmen (User {user_id})",
            "email": "[BITTE AUSFÜLLEN]",
            "address": "[BITTE AUSFÜLLEN]",
        }
        generated = 0
        for doc_type in [DocumentType.IMPRINT, DocumentType.PRIVACY]:
            try:
                existing = await generator.get_active_document(user_id, doc_type)
                if existing and (existing.get("metadata") or {}).get("generator") == "legal_text_generator":
                    logger.info(f"  User {user_id}: {doc_type} bereits migriert — skip")
                    continue
                if doc_type == DocumentType.IMPRINT:
                    await generator.generate_imprint(user_id, user_data, regeneration_trigger="migration")
                elif doc_type == DocumentType.PRIVACY:
                    await generator.generate_privacy_policy(user_id, user_data, regeneration_trigger="migration")
                generated += 1
                logger.info(f"  ✅ User {user_id}: {doc_type} generiert")
            except Exception as e:
                logger.error(f"  ❌ User {user_id}: {doc_type} fehlgeschlagen: {e}")
        return {"user_id": user_id, "generated": generated}
    finally:
        await pool.close()


async def main(dry_run: bool = False, single_user_id: Optional[int] = None):
    if not DB_URL:
        logger.error("DATABASE_URL nicht gesetzt")
        sys.exit(1)

    conn = await asyncpg.connect(DB_URL)
    try:
        if single_user_id:
            row = await conn.fetchrow("SELECT id, email, company_name FROM users WHERE id = $1", single_user_id)
            users = [row] if row else []
        else:
            users = await get_affected_users(conn)

        logger.info(f"Betroffene User: {len(users)}")
        if not users:
            logger.info("Keine User zu migrieren.")
            return

        results = []
        for user in users:
            result = await regenerate_for_user(
                conn,
                user["id"],
                user.get("company_name") or "",
                dry_run,
            )
            results.append(result)

        total_gen = sum(r.get("generated", 0) for r in results)
        logger.info(f"\n{'='*50}")
        logger.info(f"Migration abgeschlossen:")
        logger.info(f"  User verarbeitet: {len(results)}")
        logger.info(f"  Dokumente generiert: {total_gen}")
        if dry_run:
            logger.info("  [DRY-RUN] Keine Dokumente gespeichert")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eRecht24 User-Migration")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--user-id", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, single_user_id=args.user_id))
