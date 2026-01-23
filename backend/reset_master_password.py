#!/usr/bin/env python3
"""
Script zum Zurücksetzen des Master-User Passworts
Nutzt die bestehende Datenbankverbindung des Servers
"""

import sys
import os

# Füge Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import bcrypt
from database_service import DatabaseService

async def reset_master_password():
    """Setzt das Passwort für master@complyo.tech zurück"""
    
    email = "master@complyo.tech"
    new_password = "Master123!"  # Standard-Passwort
    
    # Nutze DatabaseService für Verbindung
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        # Prüfe ob User existiert
        user = await db_service.pool.fetchrow(
            "SELECT id, email, is_active FROM users WHERE email = $1",
            email
        )
        
        if not user:
            print(f"❌ Benutzer {email} existiert nicht!")
            print(f"   Bitte zuerst über /api/auth/register erstellen")
            return
        
        print(f"✓ Benutzer {email} gefunden (ID: {user['id']})")
        
        # Neues Passwort hashen
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Passwort aktualisieren
        await db_service.pool.execute(
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
        print(f"  Neues Passwort: {new_password}")
        print(f"  ⚠️  Bitte nach erstem Login ändern!")
        
        # Finale Prüfung
        final_user = await db_service.pool.fetchrow(
            "SELECT id, email, is_active, is_verified FROM users WHERE email = $1",
            email
        )
        
        print(f"\n✓ Finale Prüfung:")
        print(f"  Email: {final_user['email']}")
        print(f"  Aktiv: {final_user['is_active']}")
        print(f"  Verifiziert: {final_user['is_verified']}")
        print(f"\n✓ Login sollte jetzt funktionieren!")
        print(f"  URL: http://localhost:8002/api/auth/login")
        print(f"  Email: {email}")
        print(f"  Passwort: {new_password}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(reset_master_password())
