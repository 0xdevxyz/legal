#!/usr/bin/env python3
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://complyo_user:ComplYo2025SecurePass@localhost:5432/complyo_db")

async def cleanup():

    conn = await asyncpg.connect(DATABASE_URL)
    
    old_functions = [
        "DROP FUNCTION IF EXISTS check_domain_lock(integer, character varying) CASCADE;",
        "DROP FUNCTION IF EXISTS check_fix_limit(integer) CASCADE;",
        "DROP FUNCTION IF EXISTS increment_fix_counter(integer) CASCADE;",
        "DROP FUNCTION IF EXISTS reset_fix_counter(integer) CASCADE;",
    ]
    
    for func_drop in old_functions:
        try:
            await conn.execute(func_drop)
            print(f"✅ {func_drop.split('(')[0].replace('DROP FUNCTION IF EXISTS ', '')}")
        except Exception as e:
            print(f"⚠️ {e}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(cleanup())

