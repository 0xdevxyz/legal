#!/usr/bin/env python3
"""
Script zum Erstellen/Reset des Master-Users
"""

import asyncio
import asyncpg
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

async def create_or_reset_master_user():
    """Erstellt oder setzt das Passwort für master@complyo.tech zurück"""
    
    # Database URL aus Environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback
        db_url = "postgresql://complyo_user:ComplYo2025SecurePass@localhost:5432/complyo_db"
    
    email = "master@complyo.tech"
    password = "Master123!"  # Standard-Passwort - sollte nach erstem Login geändert werden
    full_name = "Master User"
    
    try:
        conn = await asyncpg.connect(db_url)
        
        try:
            # Prüfe ob Benutzer existiert
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
                print(f"  Neues Passwort: {password}")
                print(f"  ⚠️  Bitte nach erstem Login ändern!")
                
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
                
                # User Limits initialisieren
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
                print(f"  Passwort: {password}")
                print(f"  Plan: Expert (unbegrenzt)")
                print(f"  ⚠️  Bitte nach erstem Login ändern!")
            
            # Finale Prüfung
            final_user = await conn.fetchrow(
                "SELECT id, email, is_active, is_verified FROM users WHERE email = $1",
                email
            )
            
            print(f"\n✓ Finale Prüfung:")
            print(f"  Email: {final_user['email']}")
            print(f"  Aktiv: {final_user['is_active']}")
            print(f"  Verifiziert: {final_user['is_verified']}")
            print(f"\n✓ Login sollte jetzt funktionieren!")
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_or_reset_master_user())
