import asyncio
import aiohttp
import asyncpg
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GVL_URL = "https://vendor-list.consensu.org/v3/vendor-list.json"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://complyo_user:ComplYo2025SecurePass@localhost:5433/complyo_db"
)
BATCH_SIZE = 100


async def fetch_gvl(session: aiohttp.ClientSession) -> dict:
    logger.info(f"Fetching GVL from {GVL_URL}")
    async with session.get(GVL_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        resp.raise_for_status()
        return await resp.json(content_type=None)


async def upsert_vendors(pool: asyncpg.Pool, vendors: dict) -> int:
    upsert_sql = """
        INSERT INTO tcf_vendors (
            vendor_id, name, purposes, legitimate_interests,
            special_purposes, features, special_features, policy_url,
            is_active, last_updated
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, NOW())
        ON CONFLICT (vendor_id) DO UPDATE SET
            name                 = EXCLUDED.name,
            purposes             = EXCLUDED.purposes,
            legitimate_interests = EXCLUDED.legitimate_interests,
            special_purposes     = EXCLUDED.special_purposes,
            features             = EXCLUDED.features,
            special_features     = EXCLUDED.special_features,
            policy_url           = EXCLUDED.policy_url,
            is_active            = true,
            last_updated         = NOW()
    """
    items = list(vendors.values())
    count = 0
    async with pool.acquire() as conn:
        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i:i + BATCH_SIZE]
            records = []
            for v in batch:
                records.append((
                    v["id"],
                    v.get("name", ""),
                    v.get("purposes", []),
                    v.get("legIntPurposes", []),
                    v.get("specialPurposes", []),
                    v.get("features", []),
                    v.get("specialFeatures", []),
                    v.get("policyUrl", v.get("urls", [{}])[0].get("privacy", "") if v.get("urls") else ""),
                ))
            await conn.executemany(upsert_sql, records)
            count += len(records)
            logger.info(f"Upserted {count}/{len(items)} vendors")
    return count


async def mark_inactive_vendors(pool: asyncpg.Pool, active_ids: set):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE tcf_vendors SET is_active = false WHERE vendor_id != ALL($1::int[])",
            list(active_ids)
        )


async def run():
    db_url = DATABASE_URL.replace("postgresql://", "postgres://")
    pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=3)
    try:
        async with aiohttp.ClientSession() as session:
            gvl = await fetch_gvl(session)

        vendors = gvl.get("vendors", {})
        if not vendors:
            logger.error("GVL response has no vendors – aborting")
            sys.exit(1)

        logger.info(f"GVL version {gvl.get('vendorListVersion')}, {len(vendors)} vendors")

        count = await upsert_vendors(pool, vendors)
        await mark_inactive_vendors(pool, set(int(k) for k in vendors.keys()))
        logger.info(f"Sync complete. {count} vendors upserted.")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(run())
