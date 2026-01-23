#!/usr/bin/env python3
"""
Direktes Script zum Anlegen des Master-Users
Nutzt die gleiche Datenbankverbindung wie der Server
"""

import sys
import os

# Füge Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import bcrypt

async def create_master_user():
    """Erstellt den Master-User direkt in der Datenbank"""
    
    # Lade Environment-Variablen
    from dotenv import load_dotenv
    load_dotenv()
    
    # Nutze die gleiche Datenbankverbindung wie main_production.py
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback - versuche verschiedene Varianten
        db_user = os.getenv("DB_USER", "complyo_user")
        db_password = os.getenv("DB_PASSWORD", "ComplYo2025SecurePass")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "complyo_db")
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print(f"Verbinde mit Datenbank...")
    print(f"URL: {database_url.split('@')[0]}@***")
    
    email = "master@complyo.tech"
    password = "master123"
    full_name = "Master User"
    
    try:
        import asyncpg
        conn = await asyncpg.connect(database_url)
        
        try:
            # Prüfe ob User existiert
            user = await conn.fetchrow(
                "SELECT id, email, is_active FROM users WHERE email = $1",
                email
            )
            
            if user:
                print(f"✓ Benutzer {email} existiert bereits (ID: {user['id']})")
                
                # Passwort zurücksetzen
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                await conn.execute(
                    """
                    UPDATE users 
                    SET hashed_password = $1, 
                        is_active = TRUE, 
                        is_verified = TRUE
                    WHERE email = $2
                    """,
                    password_hash, email
                )
                
                print(f"✓ Passwort für {email} wurde zurückgesetzt")
                print(f"  Email: {email}")
                print(f"  Passwort: {password}")
                
            else:
                # Benutzer erstellen
                print(f"Erstelle neuen Benutzer: {email}")
                
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                user_id = await conn.fetchval(
                    """
                    INSERT INTO users (email, hashed_password, full_name, is_active, is_verified)
                    VALUES ($1, $2, $3, TRUE, TRUE)
                    RETURNING id
                    """,
                    email, password_hash, full_name
                )
                
                # User Limits initialisieren (Expert Plan - unbegrenzt)
                await conn.execute(
                    """
                    INSERT INTO user_limits (user_id, plan_type, websites_max, exports_max, exports_reset_date)
                    VALUES ($1, 'expert', -1, -1, CURRENT_DATE + INTERVAL '1 month')
                    ON CONFLICT (user_id) DO UPDATE SET
                        plan_type = 'expert',
                        websites_max = -1,
                        exports_max = -1
                    """,
                    user_id
                )
                
                print(f"✓ Benutzer {email} wurde erstellt (ID: {user_id})")
                print(f"  Email: {email}")
                print(f"  Passwort: {password}")
                print(f"  Plan: Expert (unbegrenzt)")
            
            # Finale Prüfung
            final_user = await conn.fetchrow(
                "SELECT id, email, is_active, is_verified, created_at FROM users WHERE email = $1",
                email
            )
            
            print(f"\n✓ Finale Prüfung:")
            print(f"  ID: {final_user['id']}")
            print(f"  Email: {final_user['email']}")
            print(f"  Aktiv: {final_user['is_active']}")
            print(f"  Verifiziert: {final_user['is_verified']}")
            print(f"  Erstellt: {final_user['created_at']}")
            print(f"\n✓ Login sollte jetzt funktionieren!")
            print(f"  URL: http://localhost:8002/api/auth/login")
            print(f"  Email: {email}")
            print(f"  Passwort: {password}")
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        print(f"\nVersuche alternative Verbindungsmethode...")
        
        # Alternative: Versuche über die bestehende Pool-Verbindung
        try:
            from database_service import DatabaseService
            db_service = DatabaseService()
            await db_service.initialize()
            
            if db_service.pool:
                # Gleiche Logik wie oben
                user = await db_service.pool.fetchrow(
                    "SELECT id, email, is_active FROM users WHERE email = $1",
                    email
                )
                
                if user:
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    await db_service.pool.execute(
                        "UPDATE users SET hashed_password = $1, is_active = TRUE, is_verified = TRUE WHERE email = $2",
                        password_hash, email
                    )
                    print(f"✓ Passwort zurückgesetzt über DatabaseService")
                else:
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    user_id = await db_service.pool.fetchval(
                        "INSERT INTO users (email, hashed_password, full_name, is_active, is_verified) VALUES ($1, $2, $3, TRUE, TRUE) RETURNING id",
                        email, password_hash, full_name
                    )
                    await db_service.pool.execute(
                        "INSERT INTO user_limits (user_id, plan_type, websites_max, exports_max, exports_reset_date) VALUES ($1, 'expert', -1, -1, CURRENT_DATE + INTERVAL '1 month')",
                        user_id
                    )
                    print(f"✓ Benutzer erstellt über DatabaseService")
            
            await db_service.close()
        except Exception as e2:
            print(f"❌ Auch alternative Methode fehlgeschlagen: {e2}")

if __name__ == "__main__":
    asyncio.run(create_master_user())
