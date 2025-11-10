#!/usr/bin/env python3
"""
Test-Szenario für Freemium-Modell mit Domain-Locks

Testet die User Journey:
1. User scannt "complyo.tech" → 15 Issues gefunden
2. Klickt "KI-Fix" auf Issue #1 → ✅ Kostenloser Fix
3. Domain "complyo.tech" wird gelockt
4. Klickt "KI-Fix" auf Issue #2 → 💳 Paywall erscheint
5. Nach Zahlung: Unbegrenzte Fixes für "complyo.tech"
6. Neue Domain "example.com" → Neue Subscription erforderlich
"""

import asyncio
import asyncpg
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://complyo_user:ComplYo2025SecurePass@localhost:5432/complyo_db")

async def test_freemium_flow():

    # Verbinde mit Datenbank
    conn = await asyncpg.connect(DATABASE_URL)

    # Test-User erstellen (oder existierenden verwenden)
    test_email = "test-freemium@complyo.tech"
    
    # Lösche alten Test-User falls vorhanden
    await conn.execute("DELETE FROM domain_locks WHERE user_id IN (SELECT id FROM users WHERE email = $1)", test_email)
    await conn.execute("DELETE FROM user_limits WHERE user_id IN (SELECT id FROM users WHERE email = $1)", test_email)
    await conn.execute("DELETE FROM users WHERE email = $1", test_email)
    
    # Erstelle Test-User
    user = await conn.fetchrow(
        """
        INSERT INTO users (email, password_hash, full_name, is_active, created_at)
        VALUES ($1, 'test_hash', 'Test User', true, CURRENT_TIMESTAMP)
        RETURNING id, email
        """,
        test_email
    )
    user_id = user['id']
    print(f"👤 Test-User erstellt: {user['email']} (ID: {user_id})\n")
    
    # Initialisiere user_limits (Free Plan)
    await conn.execute(
        """
        INSERT INTO user_limits (user_id, plan_type, fixes_limit, fixes_used, websites_max, exports_max)
        VALUES ($1, 'free', 1, 0, 1, 5)
        """,
        user_id
    )

    # === TEST 1: Erste Domain scannen ===

    domain1 = "complyo.tech"
    
    # Prüfe Domain-Lock
    is_locked = await conn.fetchval(
        "SELECT check_domain_lock($1, $2)",
        user_id, domain1
    )
    print(f"🔒 Domain '{domain1}' gelockt? {is_locked}")
    
    # Prüfe Fix-Limit
    can_fix = await conn.fetchval(
        "SELECT check_fix_limit($1, $2)",
        user_id, domain1
    )
    print(f"✅ Kann Fix ausführen? {can_fix}")
    
    if can_fix:
        print(f"💡 User klickt 'KI-Fix' auf Issue #1...")
        
        # Führe Fix aus und inkrementiere Counter
        await conn.execute(
            "SELECT increment_fix_counter($1, $2)",
            user_id, domain1
        )
        print(f"✅ Fix #1 erfolgreich ausgeführt (KOSTENLOS)")
        
        # Domain-Lock wurde automatisch erstellt
        lock = await conn.fetchrow(
            "SELECT * FROM domain_locks WHERE user_id = $1 AND domain_name = $2",
            user_id, domain1
        )
        print(f"🔐 Domain-Lock erstellt: {lock['domain_name']} (fixes_used: {lock['fixes_used']}/{lock['fixes_limit']})")
    
    print()
    
    # === TEST 2: Zweiten Fix auf gleicher Domain ===

    can_fix = await conn.fetchval(
        "SELECT check_fix_limit($1, $2)",
        user_id, domain1
    )
    print(f"✅ Kann Fix ausführen? {can_fix}")
    
    if not can_fix:
        print(f"💳 PAYWALL erscheint!")
        print(f"   → '39€/Monat für unbegrenzte Fixes an dieser Domain'")
        print(f"   → User muss upgraden, um weiterzumachen")
        
        # Zeige aktuelle Limits
        limits = await conn.fetchrow(
            "SELECT * FROM user_limits WHERE user_id = $1",
            user_id
        )
        lock = await conn.fetchrow(
            "SELECT * FROM domain_locks WHERE user_id = $1 AND domain_name = $2",
            user_id, domain1
        )
        print(f"   → Aktueller Stand: {lock['fixes_used']}/{lock['fixes_limit']} Fixes verwendet")
    
    print()
    
    # === TEST 3: User upgraded (simuliere Zahlung) ===

    # Simuliere Stripe Checkout Success
    await conn.execute(
        """
        UPDATE user_limits
        SET plan_type = 'pro', fixes_limit = 999999, websites_max = 999, exports_max = 999
        WHERE user_id = $1
        """,
        user_id
    )
    print(f"✅ User wurde zu PRO upgraded")
    
    # Unlock die Domain
    await conn.execute(
        """
        UPDATE domain_locks
        SET is_unlocked = true, unlocked_at = CURRENT_TIMESTAMP
        WHERE user_id = $1 AND domain_name = $2
        """,
        user_id, domain1
    )
    print(f"🔓 Domain '{domain1}' wurde freigeschaltet (unbegrenzte Fixes)")
    
    print()
    
    # === TEST 4: Unbegrenzte Fixes nach Upgrade ===

    # Teste mehrere Fixes
    for i in range(2, 6):
        can_fix = await conn.fetchval(
            "SELECT check_fix_limit($1, $2)",
            user_id, domain1
        )
        
        if can_fix:
            await conn.execute(
                "SELECT increment_fix_counter($1, $2)",
                user_id, domain1
            )
            lock = await conn.fetchrow(
                "SELECT * FROM domain_locks WHERE user_id = $1 AND domain_name = $2",
                user_id, domain1
            )
            print(f"✅ Fix #{i} erfolgreich (fixes_used: {lock['fixes_used']})")
    
    print()
    
    # === TEST 5: Neue Domain scannen ===

    domain2 = "example.com"
    
    is_locked = await conn.fetchval(
        "SELECT check_domain_lock($1, $2)",
        user_id, domain2
    )
    print(f"🔒 Domain '{domain2}' gelockt? {is_locked}")
    
    can_fix = await conn.fetchval(
        "SELECT check_fix_limit($1, $2)",
        user_id, domain2
    )
    print(f"✅ Kann Fix ausführen? {can_fix}")
    
    if can_fix:
        print(f"💡 Neue Domain → 1 kostenloser Fix (unabhängig vom Plan)")
        await conn.execute(
            "SELECT increment_fix_counter($1, $2)",
            user_id, domain2
        )
        print(f"✅ Fix #1 auf '{domain2}' erfolgreich")
        
        lock = await conn.fetchrow(
            "SELECT * FROM domain_locks WHERE user_id = $1 AND domain_name = $2",
            user_id, domain2
        )
        print(f"🔐 Domain-Lock erstellt: {lock['domain_name']} (fixes_used: {lock['fixes_used']}/{lock['fixes_limit']})")
    
    print()
    
    # === TEST 6: Zweiter Fix auf neuer Domain ===

    can_fix = await conn.fetchval(
        "SELECT check_fix_limit($1, $2)",
        user_id, domain2
    )
    print(f"✅ Kann Fix ausführen? {can_fix}")
    
    if not can_fix:
        print(f"💳 PAYWALL erscheint!")
        print(f"   → 'Neue Domain-Subscription erforderlich (+39€/Monat)'")
        print(f"   → User muss für jede Domain separat zahlen")
        
        lock = await conn.fetchrow(
            "SELECT * FROM domain_locks WHERE user_id = $1 AND domain_name = $2",
            user_id, domain2
        )
        print(f"   → Aktueller Stand: {lock['fixes_used']}/{lock['fixes_limit']} Fixes verwendet")
    
    print()
    
    # === ZUSAMMENFASSUNG ===

    limits = await conn.fetchrow(
        "SELECT * FROM user_limits WHERE user_id = $1",
        user_id
    )
    print(f"User Plan: {limits['plan_type'].upper()}")
    print(f"Fixes Limit: {limits['fixes_limit']}")
    print(f"Fixes Used: {limits['fixes_used']}")
    print(f"Websites Max: {limits['websites_max']}")
    print()
    
    locks = await conn.fetch(
        "SELECT * FROM domain_locks WHERE user_id = $1 ORDER BY created_at",
        user_id
    )
    print(f"Domain-Locks ({len(locks)}):")
    for lock in locks:
        status = "🔓 UNLOCKED" if lock['is_unlocked'] else "🔒 LOCKED"
        print(f"  - {lock['domain_name']}: {lock['fixes_used']}/{lock['fixes_limit']} Fixes | {status}")
    
    print()

    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_freemium_flow())

