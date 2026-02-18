"""
Database initialization script for lead management tables
Run this to create the lead management tables if they don't exist
"""

import asyncio
import asyncpg
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required!")

async def init_lead_tables():
    """Initialize lead management tables"""
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)

        # Read SQL file
        sql_file = os.path.join(os.path.dirname(__file__), 'add_lead_management.sql')
        
        if not os.path.exists(sql_file):
            logger.error(f"❌ SQL file not found: {sql_file}")
            return False
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info("📄 Executing SQL migration...")
        
        # Execute SQL (split by semicolons and execute each statement)
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            try:
                await conn.execute(statement)
                logger.info(f"  ✅ Statement {i}/{len(statements)} executed")
            except Exception as e:
                # Ignore "already exists" errors
                if "already exists" in str(e).lower():
                    logger.info(f"  ⏩ Statement {i} skipped (already exists)")
                else:
                    logger.warning(f"  ⚠️  Statement {i} failed: {e}")

        # Close connection
        await conn.close()

        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize lead tables: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(init_lead_tables())
    exit(0 if success else 1)

