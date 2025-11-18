"""
Complyo Expert Service Routes
==============================
Endpoints für Expertservice-Anfragen
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/expert-service", tags=["expert-service"])

# Database pool (wird von main.py gesetzt)
db_pool = None

def set_db_pool(pool):
    """Setzt den Database Pool"""
    global db_pool
    return pool


class ExpertServiceRequest(BaseModel):
    site_id: str
    site_url: str
    scan_id: Optional[str] = None
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    company_name: Optional[str] = None
    service_type: str = "accessibility"  # accessibility, full_compliance, custom
    priority: str = "normal"  # normal, urgent
    issues_count: Optional[int] = None
    alt_text_count: Optional[int] = None
    pages_count: Optional[int] = 1
    additional_notes: Optional[str] = None


@router.post("/request")
async def create_expert_service_request(
    request: ExpertServiceRequest,
    user_id: Optional[str] = None
):
    """
    Erstellt eine neue Expertservice-Anfrage
    
    Args:
        request: Anfrage-Daten
        user_id: Optional User-ID (wenn eingeloggt)
        
    Returns:
        Request-ID und Bestätigung
    """
    try:
        if not db_pool:
            raise HTTPException(
                status_code=503,
                detail="Datenbank nicht verfügbar"
            )
        
        # Berechne Preis basierend auf Service-Typ
        estimated_price = 3000.00  # Base price
        if request.service_type == "full_compliance":
            estimated_price = 8000.00
        elif request.service_type == "custom":
            estimated_price = 0.00  # Wird individuell besprochen
        
        async with db_pool.acquire() as conn:
            # Speichere Anfrage in DB
            result = await conn.fetchrow(
                """
                INSERT INTO expert_service_requests (
                    user_id,
                    site_id,
                    site_url,
                    scan_id,
                    contact_name,
                    contact_email,
                    contact_phone,
                    company_name,
                    service_type,
                    priority,
                    estimated_price,
                    issues_count,
                    alt_text_count,
                    pages_count,
                    additional_notes,
                    status,
                    requested_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 
                    $11, $12, $13, $14, $15, 'pending', NOW()
                )
                RETURNING request_id, estimated_price
                """,
                user_id,
                request.site_id,
                request.site_url,
                request.scan_id,
                request.contact_name,
                request.contact_email,
                request.contact_phone,
                request.company_name,
                request.service_type,
                request.priority,
                estimated_price,
                request.issues_count,
                request.alt_text_count,
                request.pages_count,
                request.additional_notes
            )
            
            request_id = result['request_id']
            final_price = result['estimated_price']
        
        logger.info(f"✅ Expert service request created: {request_id} for {request.contact_email}")
        
        # 📧 Send Email Notification (in background)
        try:
            await _send_expert_request_email(
                request_id=request_id,
                contact_name=request.contact_name,
                contact_email=request.contact_email,
                site_url=request.site_url,
                service_type=request.service_type,
                estimated_price=final_price
            )
        except Exception as email_error:
            logger.error(f"❌ Failed to send email: {email_error}")
            # Don't fail the request if email fails
        
        return JSONResponse(
            content={
                "success": True,
                "request_id": request_id,
                "estimated_price": float(final_price),
                "status": "pending",
                "message": f"Vielen Dank! Ihre Anfrage {request_id} wurde erfolgreich übermittelt. "
                          f"Wir melden uns innerhalb von 24 Stunden bei Ihnen."
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating expert service request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Erstellen der Anfrage: {str(e)}"
        )


@router.get("/requests")
async def get_expert_service_requests(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    Holt Expertservice-Anfragen
    
    Args:
        user_id: Filter nach User-ID
        status: Filter nach Status
        limit: Maximale Anzahl
        
    Returns:
        Liste von Anfragen
    """
    try:
        if not db_pool:
            raise HTTPException(
                status_code=503,
                detail="Datenbank nicht verfügbar"
            )
        
        query = """
            SELECT 
                request_id,
                user_id,
                site_url,
                contact_name,
                contact_email,
                service_type,
                priority,
                estimated_price,
                issues_count,
                status,
                requested_at,
                contacted_at,
                completed_at
            FROM expert_service_requests
            WHERE 1=1
        """
        
        params = []
        param_idx = 1
        
        if user_id:
            query += f" AND user_id = ${param_idx}"
            params.append(user_id)
            param_idx += 1
        
        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1
        
        query += f" ORDER BY requested_at DESC LIMIT ${param_idx}"
        params.append(limit)
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        requests = [
            {
                "request_id": row['request_id'],
                "site_url": row['site_url'],
                "contact_name": row['contact_name'],
                "contact_email": row['contact_email'],
                "service_type": row['service_type'],
                "priority": row['priority'],
                "estimated_price": float(row['estimated_price']) if row['estimated_price'] else 0,
                "issues_count": row['issues_count'],
                "status": row['status'],
                "requested_at": row['requested_at'].isoformat() if row['requested_at'] else None,
                "contacted_at": row['contacted_at'].isoformat() if row['contacted_at'] else None,
                "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None
            }
            for row in rows
        ]
        
        return JSONResponse(
            content={
                "success": True,
                "requests": requests,
                "count": len(requests)
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching expert service requests: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Laden der Anfragen: {str(e)}"
        )


async def _send_expert_request_email(
    request_id: str,
    contact_name: str,
    contact_email: str,
    site_url: str,
    service_type: str,
    estimated_price: float
):
    """
    Sendet Email-Benachrichtigungen für Expert-Service-Anfragen
    
    Sendet 2 Emails:
    1. Bestätigung an Kunden
    2. Notification an Team
    """
    # TODO: Integrate with email_service
    # Für jetzt: Nur logging
    
    logger.info(f"""
    📧 EMAIL BENACHRICHTIGUNGEN:
    
    === AN KUNDE ({contact_email}) ===
    Betreff: Ihre Expertservice-Anfrage {request_id}
    
    Hallo {contact_name},
    
    vielen Dank für Ihre Anfrage zum Complyo Expertservice!
    
    **Ihre Anfrage:**
    - Request-ID: {request_id}
    - Website: {site_url}
    - Service: {service_type}
    - Geschätzter Preis: €{estimated_price:,.2f} (netto)
    
    **Nächste Schritte:**
    1. Wir prüfen Ihre Website im Detail
    2. Sie erhalten ein individuelles Angebot
    3. Nach Ihrer Freigabe setzen wir alles um (48h)
    
    Wir melden uns innerhalb von 24 Stunden bei Ihnen!
    
    Mit freundlichen Grüßen
    Ihr Complyo Team
    
    === AN TEAM (support@complyo.tech) ===
    Betreff: Neue Expertservice-Anfrage: {request_id}
    
    🚨 NEUE ANFRAGE:
    
    Request-ID: {request_id}
    Website: {site_url}
    Kontakt: {contact_name} ({contact_email})
    Service: {service_type}
    Preis: €{estimated_price:,.2f}
    
    👉 Dashboard: https://app.complyo.tech/admin/expert-requests/{request_id}
    """)
    
    # In production: Use email_service.send_email(...)
    pass

