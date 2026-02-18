import os
import asyncio
import asyncpg
import logging

logger = logging.getLogger(__name__)


async def run_retention_cleanup():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is required!")

    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        deleted_consent = await conn.fetchval(
            "DELETE FROM cookie_consent_logs WHERE timestamp < NOW() - INTERVAL '1 year' RETURNING COUNT(*)"
        )
        deleted_ai_logs = await conn.fetchval(
            "DELETE FROM ai_call_logs WHERE created_at < NOW() - INTERVAL '90 days' RETURNING COUNT(*)"
        )
        deleted_verif = await conn.fetchval(
            "DELETE FROM email_verifications WHERE expires_at < NOW() RETURNING COUNT(*)"
        )
        msg = (
            f"Retention cleanup: consent_logs={deleted_consent or 0}, "
            f"ai_logs={deleted_ai_logs or 0}, email_verif={deleted_verif or 0}"
        )
        logger.info(msg)
        print(msg)

    await pool.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_retention_cleanup())
