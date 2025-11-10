#!/usr/bin/env python3
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://complyo_user:ComplYo2025SecurePass@localhost:5432/complyo_db")

async def apply_fix():

    conn = await asyncpg.connect(DATABASE_URL)
    
    with open('fix_domain_lock_logic.sql', 'r') as f:
        fix_sql = f.read().replace('COMMIT;', '')
    
    await conn.execute(fix_sql)

    await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_fix())

