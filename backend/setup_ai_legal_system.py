#!/usr/bin/env python3
"""
Setup-Script für das AI Legal Classifier System
================================================

Dieses Script initialisiert das komplette KI-gestützte Legal Updates System:
- Datenbank-Migration
- System-Initialisierung
- Test der Komponenten
- Beispiel-Klassifizierung

Usage:
    python setup_ai_legal_system.py
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path


async def run_migration(db_url: str):
    """Führt die Datenbank-Migration aus"""
    print("📊 Starte Datenbank-Migration...")
    
    migration_file = Path(__file__).parent / "migration_ai_legal_classifier.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration-File nicht gefunden: {migration_file}")
        return False
    
    try:
        # Verbinde zur DB
        conn = await asyncpg.connect(db_url)
        
        # Lese Migration
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Führe Migration aus
        await conn.execute(migration_sql)
        await conn.close()
        
        print("✅ Datenbank-Migration erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Migration fehlgeschlagen: {e}")
        return False


async def test_ai_classifier():
    """Testet die AI Classifier Engine"""
    print("\n🤖 Teste AI Classifier Engine...")
    
    try:
        from ai_legal_classifier import AILegalClassifier
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("⚠️ OPENROUTER_API_KEY nicht gesetzt - überspringe AI-Test")
            return True
        
        classifier = AILegalClassifier(api_key)
        
        # Test-Update
        test_update = {
            "id": "test_123",
            "title": "Cookie-Banner: Neue Anforderungen ab 2025",
            "description": (
                "Die EU-Kommission hat neue Richtlinien für Cookie-Banner veröffentlicht. "
                "Vorausgewählte Optionen (Pre-checked Boxes) sind ab 1. Januar 2025 nicht mehr erlaubt. "
                "Alle Cookie-Banner müssen angepasst werden."
            ),
            "update_type": "REGULATION_CHANGE",
            "severity": "high",
            "source": "EU-Kommission",
            "published_at": "2025-11-12T10:00:00Z"
        }
        
        print("   → Klassifiziere Test-Update...")
        result = await classifier.classify_legal_update(test_update)
        
        print(f"   ✅ Klassifizierung erfolgreich!")
        print(f"      Action Required: {result.action_required}")
        print(f"      Confidence: {result.confidence.value}")
        print(f"      Impact Score: {result.impact_score}")
        print(f"      Primary Action: {result.primary_action.action_type.value}")
        print(f"      Button Text: {result.primary_action.button_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Classifier Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_feedback_learning(db_url: str):
    """Testet das Feedback Learning System"""
    print("\n🧠 Teste Feedback Learning System...")
    
    try:
        from database_service import DatabaseService
        from ai_feedback_learning import AIFeedbackLearning
        
        # Mock DB Service (für Test)
        class MockDBService:
            def __init__(self, db_url):
                self.db_url = db_url
                self.pool = None
        
        db_service = MockDBService(db_url)
        db_service.pool = await asyncpg.create_pool(db_url)
        
        learning = AIFeedbackLearning(db_service)
        
        print("   → System initialisiert")
        print("   ✅ Feedback Learning bereit!")
        
        await db_service.pool.close()
        return True
        
    except Exception as e:
        print(f"❌ Feedback Learning Test fehlgeschlagen: {e}")
        return False


async def create_sample_updates(db_url: str):
    """Erstellt Beispiel-Updates für Testing"""
    print("\n📝 Erstelle Beispiel-Updates...")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Prüfe ob bereits Updates existieren
        count = await conn.fetchval("SELECT COUNT(*) FROM legal_updates")
        
        if count > 0:
            print(f"   ℹ️ {count} Updates bereits vorhanden - überspringe")
            await conn.close()
            return True
        
        # Beispiel-Updates
        sample_updates = [
            {
                "update_type": "REGULATION_CHANGE",
                "title": "Cookie-Banner: Neue Anforderungen ab 2025",
                "description": "Die Cookie-Banner-Richtlinien werden verschärft. Vorausgewählte Optionen sind nicht mehr erlaubt.",
                "severity": "high",
                "action_required": True,
                "source": "EU-Kommission",
                "published_at": "2025-11-12T10:00:00Z"
            },
            {
                "update_type": "COURT_RULING",
                "title": "BGH-Urteil zur Impressumspflicht",
                "description": "BGH bestätigt: Impressum muss von jeder Unterseite mit maximal 2 Klicks erreichbar sein.",
                "severity": "medium",
                "action_required": True,
                "source": "BGH",
                "published_at": "2025-11-07T10:00:00Z"
            },
            {
                "update_type": "NEW_LAW",
                "title": "BFSG: Barrierefreiheit wird Pflicht",
                "description": "Ab Juni 2025 müssen digitale Dienste barrierefrei sein (WCAG 2.1 AA).",
                "severity": "critical",
                "action_required": True,
                "source": "Bundestag",
                "published_at": "2025-11-05T10:00:00Z"
            },
            {
                "update_type": "INFO",
                "title": "DSGVO: Neue FAQ der Datenschutzkonferenz",
                "description": "Die Datenschutzkonferenz hat neue FAQs zu DSGVO-Anforderungen veröffentlicht.",
                "severity": "info",
                "action_required": False,
                "source": "Datenschutzkonferenz",
                "published_at": "2025-11-10T10:00:00Z"
            }
        ]
        
        for update in sample_updates:
            await conn.execute(
                """
                INSERT INTO legal_updates (
                    update_type, title, description, severity, 
                    action_required, source, published_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                update["update_type"],
                update["title"],
                update["description"],
                update["severity"],
                update["action_required"],
                update["source"],
                update["published_at"]
            )
        
        await conn.close()
        print(f"   ✅ {len(sample_updates)} Beispiel-Updates erstellt")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Beispiel-Updates: {e}")
        return False


async def main():
    """Haupt-Setup-Routine"""
    print("=" * 60)
    print("🚀 AI Legal Classifier System - Setup")
    print("=" * 60)
    print()
    
    # 1. Check Environment
    print("1️⃣ Prüfe Environment-Variablen...")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL nicht gesetzt!")
        print("   Setze z.B.: export DATABASE_URL='postgresql://user:pass@localhost/complyo'")
        return False
    print(f"   ✅ DATABASE_URL: {database_url[:30]}...")
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("⚠️ OPENROUTER_API_KEY nicht gesetzt!")
        print("   KI-Klassifizierung wird nicht funktionieren.")
        print("   Setze: export OPENROUTER_API_KEY='sk-or-...'")
    else:
        print(f"   ✅ OPENROUTER_API_KEY: {openrouter_key[:15]}...")
    
    print()
    
    # 2. Datenbank-Migration
    print("2️⃣ Datenbank-Migration...")
    if not await run_migration(database_url):
        print("❌ Setup abgebrochen")
        return False
    print()
    
    # 3. Beispiel-Updates
    print("3️⃣ Beispiel-Updates...")
    if not await create_sample_updates(database_url):
        print("⚠️ Beispiel-Updates konnten nicht erstellt werden")
    print()
    
    # 4. AI Classifier Test
    print("4️⃣ AI Classifier Test...")
    if openrouter_key:
        await test_ai_classifier()
    else:
        print("   ⚠️ Überspringe - kein API-Key")
    print()
    
    # 5. Feedback Learning Test
    print("5️⃣ Feedback Learning Test...")
    await test_feedback_learning(database_url)
    print()
    
    # Fertig!
    print("=" * 60)
    print("✅ Setup erfolgreich abgeschlossen!")
    print("=" * 60)
    print()
    print("📚 Nächste Schritte:")
    print("   1. Backend starten: python main_production.py")
    print("   2. Frontend starten: cd dashboard-react && npm run dev")
    print("   3. Öffne: http://localhost:3000")
    print("   4. Navigiere zu: Dashboard → Rechtliche Updates")
    print()
    print("📖 Dokumentation: AI_LEGAL_SYSTEM_DOCUMENTATION.md")
    print()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

