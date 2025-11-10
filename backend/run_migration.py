#!/usr/bin/env python3
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://complyo_user:ComplYo2025SecurePass@localhost:5432/complyo_db")

async def run_migration():

    conn = await asyncpg.connect(DATABASE_URL)

    # Lese Migration SQL
    with open('migration_domain_locks_v2.sql', 'r') as f:
        migration_sql = f.read()
    
    # Entferne COMMIT (nicht unterstützt in asyncpg)
    migration_sql = migration_sql.replace('COMMIT;', '')
    
    # Führe Migration aus
    try:
        await conn.execute(migration_sql)

        # Prüfe, ob Tabelle erstellt wurde
        tables = await conn.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'domain_locks'
            """
        )
        
        if tables:
            print(f"✅ Tabelle 'domain_locks' erfolgreich erstellt")
            
            # Prüfe Spalten
            columns = await conn.fetch(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'domain_locks'
                ORDER BY ordinal_position
                """
            )
            
            print(f"\n📋 Spalten der domain_locks Tabelle:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Prüfe Funktionen
        functions = await conn.fetch(
            """
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_name IN ('check_domain_lock', 'check_fix_limit', 'increment_fix_counter', 'unlock_domain')
            """
        )
        
        if functions:
            print(f"\n✅ {len(functions)} Funktionen erstellt:")
            for func in functions:
                print(f"  - {func['routine_name']}()")
        
    except Exception as e:
        print(f"❌ Migration fehlgeschlagen: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())

