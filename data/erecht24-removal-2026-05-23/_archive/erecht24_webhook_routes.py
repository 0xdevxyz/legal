"""
eRecht24 Webhook Routes
Empfängt Webhooks von eRecht24 bei Gesetzesänderungen
"""

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Optional
import logging
import hashlib
import hmac
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/erecht24", tags=["webhooks"])

WEBHOOK_SECRET = os.getenv("ERECHT24_WEBHOOK_SECRET", "")

# Global reference (wird in main_production.py gesetzt)
db_pool = None

async def verify_webhook_signature(
    request: Request,
    x_erecht24_signature: Optional[str] = Header(None)
) -> bool:
    """
    Verifiziert die Webhook-Signatur von eRecht24
    
    Args:
        request: FastAPI Request-Objekt
        x_erecht24_signature: Signatur-Header
        
    Returns:
        True wenn Signatur gültig
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET nicht gesetzt - Signatur-Prüfung übersprungen")
        return True  # Im Demo-Modus akzeptieren
    
    if not x_erecht24_signature:
        logger.error("Keine Signatur im Webhook vorhanden")
        return False
    
    body = await request.body()
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, x_erecht24_signature)

@router.post("/law-update")
async def handle_law_update(
    request: Request,
    x_erecht24_signature: Optional[str] = Header(None)
):
    """
    Webhook-Endpoint für Gesetzesänderungen von eRecht24
    
    Payload-Beispiel:
    {
        "event": "law.updated",
        "data": {
            "update_type": "dsgvo",
            "title": "DSGVO Änderung 2025",
            "description": "Neue Cookie-Consent Anforderungen...",
            "severity": "warning",
            "action_required": true,
            "effective_date": "2026-01-01",
            "url": "https://..."
        }
    }
    """
    # Signatur-Verifikation
    is_valid = await verify_webhook_signature(request, x_erecht24_signature)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    try:
        payload = await request.json()
        logger.info(f"📨 Webhook empfangen: {payload.get('event')}")
        
        event = payload.get("event")
        data = payload.get("data", {})
        
        if event == "law.updated" or event == "law.created":
            await _handle_legal_update(data)
            return {"status": "processed", "message": "Legal update stored"}
        
        elif event == "compliance.alert":
            await _handle_compliance_alert(data)
            return {"status": "processed", "message": "Compliance alert sent"}
        
        else:
            logger.warning(f"Unbekannter Webhook-Event: {event}")
            return {"status": "ignored", "message": f"Unknown event: {event}"}
    
    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten des Webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _handle_legal_update(data: dict):
    """
    Speichert ein Legal Update und benachrichtigt betroffene User
    
    Args:
        data: Webhook-Daten
    """
    global db_pool
    if not db_pool:
        logger.warning("DB-Pool nicht verfügbar - Legal Update wird nicht gespeichert")
        return
    
    try:
        async with db_pool.acquire() as conn:
            # Legal Update in DB speichern
            update_id = await conn.fetchval("""
                INSERT INTO legal_updates (
                    update_type, 
                    title, 
                    description, 
                    severity,
                    action_required,
                    source,
                    published_at,
                    effective_date,
                    url
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """,
                data.get("update_type"),
                data.get("title"),
                data.get("description"),
                data.get("severity", "info"),
                data.get("action_required", False),
                "erecht24",
                datetime.now(),
                data.get("effective_date"),
                data.get("url")
            )
            
            logger.info(f"✅ Legal Update #{update_id} gespeichert: {data.get('title')}")
            
            # Benachrichtige alle betroffenen User
            if data.get("action_required"):
                await _notify_all_users(update_id)
    
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Legal Updates: {e}")
        raise

async def _handle_compliance_alert(data: dict):
    """
    Verarbeitet einen Compliance-Alert
    
    Args:
        data: Alert-Daten
    """
    logger.info(f"⚠️ Compliance-Alert: {data.get('message')}")
    
    # TODO: Implementierung für spezifische Compliance-Alerts
    # z.B. wenn ein bestimmtes Tool (Google Analytics) neue Anforderungen hat

async def _notify_all_users(update_id: int):
    """
    Erstellt Notifications für alle User mit aktiven Websites
    
    Args:
        update_id: ID des Legal Updates
    """
    global db_pool
    try:
        async with db_pool.acquire() as conn:
            # Hole alle User mit aktiven Websites
            users_with_websites = await conn.fetch("""
                SELECT DISTINCT u.id as user_id, tw.id as website_id
                FROM users u
                JOIN tracked_websites tw ON u.id = tw.user_id
                WHERE tw.status = 'active'
            """)
            
            if not users_with_websites:
                logger.info("Keine aktiven User mit Websites gefunden")
                return
            
            # Erstelle Notifications
            notifications = []
            for row in users_with_websites:
                notifications.append((
                    row['user_id'],
                    update_id,
                    row['website_id']
                ))
            
            # Bulk-Insert
            await conn.executemany("""
                INSERT INTO user_legal_notifications (user_id, legal_update_id, website_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, legal_update_id, website_id) DO NOTHING
            """, notifications)
            
            logger.info(f"📢 {len(notifications)} User-Notifications erstellt")
    
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Notifications: {e}")

# Test-Endpoint (nur für Entwicklung)
@router.post("/test")
async def test_webhook(request: Request):
    """
    Test-Endpoint um Webhooks manuell zu testen
    Nur in Entwicklungsumgebung verfügbar
    """
    if os.getenv("ENV") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    test_payload = {
        "event": "law.updated",
        "data": {
            "update_type": "court_ruling",
            "title": "Test: BGH Cookie-Urteil 2025",
            "description": "Dies ist ein Test-Update für Entwicklungszwecke. Der BGH hat entschieden, dass Cookie-Banner ohne Vorauswahl zwingend sind.",
            "severity": "critical",
            "action_required": "Prüfen Sie Ihre Website auf Konformität",
            "effective_date": "2026-01-01",
            "url": "https://example.com/test"
        }
    }
    
    await _handle_legal_update(test_payload["data"])
    
    return {
        "status": "test_successful",
        "message": "Test-Webhook wurde verarbeitet"
    }

