#!/usr/bin/env python3
"""
eRecht24 Webhook Setup Script
Registriert die Complyo-Webhook-URL bei eRecht24 für automatische Gesetzesänderungen
"""

import asyncio
import os
import sys
from erecht24_rechtstexte_service import erecht24_rechtstexte_service

async def setup_erecht24_webhook():
    """
    Registriert Complyo als Client bei eRecht24
    """
    print("🚀 Starte eRecht24 Webhook-Registrierung...\n")
    
    # Webhook-URL (öffentlich erreichbar)
    webhook_url = os.getenv("ERECHT24_WEBHOOK_URL", "https://api.complyo.tech/webhooks/erecht24/law-update")
    
    print(f"📍 Webhook-URL: {webhook_url}")
    print(f"🔑 API Key: {erecht24_rechtstexte_service.api_key[:20]}...")
    print()
    
    # Registriere Client
    result = await erecht24_rechtstexte_service.create_client(
        push_uri=webhook_url,
        cms="Custom",
        cms_version="2.2.0",
        plugin_name="complyo-ai-compliance",
        author_mail="api@complyo.tech",
        push_method="POST"
    )
    
    if result:
        print("✅ Client erfolgreich registriert!")
        print(f"   Client ID: {result.get('client_id')}")
        print(f"   Status: {result.get('status', 'active')}")
        print()
        print("📋 Nächste Schritte:")
        print("   1. Webhook-URL ist jetzt bei eRecht24 hinterlegt")
        print("   2. Bei Gesetzesänderungen sendet eRecht24 automatisch Updates")
        print("   3. Updates werden in die 'legal_updates' Tabelle gespeichert")
        print("   4. Betroffene User werden automatisch benachrichtigt")
        print()
        print("🧪 Teste die Integration mit:")
        print(f"   curl -X POST http://localhost:8002/webhooks/erecht24/test")
        
        return result
    else:
        print("❌ Fehler bei der Client-Registrierung")
        print("   Mögliche Gründe:")
        print("   - API Key ungültig")
        print("   - Webhook-URL nicht erreichbar")
        print("   - eRecht24 API nicht verfügbar")
        print()
        print("💡 Im Demo-Modus werden Test-Daten verwendet")
        return None

async def test_webhook_integration():
    """
    Testet die Webhook-Integration durch Simulation
    """
    print("\n🧪 Teste Webhook-Integration...\n")
    
    import httpx
    
    test_payload = {
        "event": "law.updated",
        "data": {
            "update_type": "court_ruling",
            "title": "BGH: Neue Cookie-Consent Entscheidung",
            "description": "Der Bundesgerichtshof hat entschieden, dass Cookie-Banner ohne Vorauswahl zwingend erforderlich sind. Websites müssen ihre Cookie-Implementierung anpassen.",
            "severity": "critical",
            "action_required": "Prüfen Sie Ihre Website auf Konformität mit dem neuen Urteil",
            "source": "eRecht24",
            "effective_date": "2025-12-01",
            "url": "https://www.e-recht24.de/news/bgh-cookie-urteil-2025"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:8002/webhooks/erecht24/test",
                json=test_payload
            )
            
            if response.status_code == 200:
                print("✅ Test-Webhook erfolgreich verarbeitet!")
                print(f"   Response: {response.json()}")
                print()
                print("📊 Prüfe gespeicherte Updates:")
                print(f"   curl http://localhost:8002/api/legal/updates?limit=5")
            else:
                print(f"❌ Test fehlgeschlagen: {response.status_code}")
                print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")

async def list_existing_clients():
    """
    Zeigt alle bereits registrierten Clients an
    """
    print("\n📋 Liste registrierter Clients...\n")
    
    clients = await erecht24_rechtstexte_service.get_client_list()
    
    if clients:
        print(f"✅ {len(clients)} Client(s) gefunden:")
        for client in clients:
            print(f"   - ID: {client.get('client_id')}")
            print(f"     Push-URI: {client.get('push_uri')}")
            print(f"     Plugin: {client.get('plugin_name')}")
            print()
    else:
        print("⚠️  Keine Clients gefunden oder API-Zugriff fehlgeschlagen")

if __name__ == "__main__":
    print("=" * 60)
    print("   eRecht24 Webhook Setup für Complyo")
    print("=" * 60)
    print()
    
    # Prüfe Umgebungsvariablen
    if not os.getenv("ERECHT24_API_KEY"):
        print("⚠️  ERECHT24_API_KEY nicht gesetzt - verwende Development Key")
        print()
    
    loop = asyncio.get_event_loop()
    
    try:
        # 1. Liste existierende Clients
        loop.run_until_complete(list_existing_clients())
        
        # 2. Registriere neuen Client
        result = loop.run_until_complete(setup_erecht24_webhook())
        
        # 3. Teste Webhook
        if result or True:  # Immer testen, auch im Demo-Modus
            loop.run_until_complete(test_webhook_integration())
        
        print("\n" + "=" * 60)
        print("✅ Setup abgeschlossen!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        sys.exit(1)

