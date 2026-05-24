"""
Lead Collection API for GDPR-Compliant Lead Generation
Handles lead collection, email verification, and statistics
Also provides Early-Access Waitlist endpoints with Double-Opt-In.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
import logging
import secrets
import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from database_service import db_service
from email_service import email_service

_rate_limit_store: Dict[str, list] = defaultdict(list)
_RATE_LIMIT_MAX = 3
_RATE_LIMIT_WINDOW_MINUTES = 10

logger = logging.getLogger(__name__)

lead_router = APIRouter(prefix="/api/leads", tags=["leads"])

# ---------------------------------------------------------------------------
# Waitlist models
# ---------------------------------------------------------------------------

class WaitlistJoinRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    consent: bool
    website: Optional[str] = None
    source: Optional[str] = "early-access"

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()[:120]
        return v or None

    @validator("phone")
    def validate_phone(cls, v):
        if v is not None:
            v = v.strip()
            if v and not re.match(r'^[\+\d\s\-\(\)]{1,40}$', v):
                raise ValueError("Ungültiges Telefon-Format")
            return v[:40] if v else None
        return None

    @validator("consent")
    def validate_consent(cls, v):
        if not v:
            raise ValueError("Einwilligung ist erforderlich")
        return v

    @validator("source")
    def validate_source(cls, v):
        allowed = {"early-access", "complyo.de", "complyo.tech", "landing"}
        if v not in allowed:
            return "early-access"
        return v


class WaitlistJoinResponse(BaseModel):
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_ip(ip: str) -> str:
    salt = os.getenv("SECRET_SALT", "complyo-salt-2026")
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()


def _check_rate_limit(ip_hash: str) -> bool:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=_RATE_LIMIT_WINDOW_MINUTES)
    _rate_limit_store[ip_hash] = [
        ts for ts in _rate_limit_store[ip_hash] if ts > window_start
    ]
    if len(_rate_limit_store[ip_hash]) >= _RATE_LIMIT_MAX:
        return False
    _rate_limit_store[ip_hash].append(now)
    return True


# ---------------------------------------------------------------------------
# Waitlist endpoints
# ---------------------------------------------------------------------------

@lead_router.post("/waitlist", response_model=WaitlistJoinResponse)
async def join_waitlist(
    payload: WaitlistJoinRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Early-Access Waitlist Anmeldung (DSGVO-konform, Double-Opt-In)
    """
    if payload.website:
        return Response(status_code=204)

    client_ip = http_request.client.host if http_request.client else "0.0.0.0"
    ip_hash = _hash_ip(client_ip)
    user_agent = http_request.headers.get("user-agent", "")[:500]

    if not _check_rate_limit(ip_hash):
        raise HTTPException(
            status_code=429,
            detail="Zu viele Anfragen. Bitte versuchen Sie es später erneut.",
        )

    confirm_token = secrets.token_urlsafe(32)
    token_expires = datetime.now(timezone.utc) + timedelta(days=7)
    now = datetime.now(timezone.utc)

    try:
        existing = await db_service.execute_query(
            "SELECT id, confirmed_at FROM waitlist_leads WHERE email = $1",
            payload.email.lower(),
            fetch_one=True,
        )

        if existing:
            logger.info(f"Waitlist duplicate for {payload.email}")
            return WaitlistJoinResponse(
                status="already_registered",
                message="Diese E-Mail steht bereits auf der Warteliste.",
            )

        await db_service.execute_query(
            """
            INSERT INTO waitlist_leads
                (email, name, phone, consent_given_at, confirm_token,
                 confirm_token_expires_at, source, ip_hash, user_agent, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            payload.email.lower(),
            payload.name,
            payload.phone,
            now,
            confirm_token,
            token_expires,
            payload.source or "early-access",
            ip_hash,
            user_agent,
            now,
            fetch_one=False,
        )

        frontend_url = os.getenv("FRONTEND_URL", "https://complyo.de")
        confirm_url = f"{frontend_url}/api/leads/waitlist/confirm?token={confirm_token}"

        background_tasks.add_task(
            email_service.send_waitlist_confirmation,
            payload.email.lower(),
            payload.name or "",
            confirm_url,
        )

        background_tasks.add_task(
            email_service.send_waitlist_admin_notification,
            payload.email.lower(),
            payload.name or "",
            payload.phone or "",
            payload.source or "early-access",
        )

        logger.info(f"Waitlist registration pending confirmation: {payload.email}")
        return WaitlistJoinResponse(
            status="pending_confirmation",
            message="Danke! Wir haben dir eine Bestätigungsmail geschickt.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Waitlist join error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Speichern. Bitte versuchen Sie es erneut.",
        )


@lead_router.get("/waitlist/confirm")
async def confirm_waitlist(token: str):
    """
    Double-Opt-In Bestätigung via E-Mail-Link
    """
    frontend_url = os.getenv("FRONTEND_URL", "https://complyo.de")
    try:
        lead = await db_service.execute_query(
            """
            SELECT id, confirm_token_expires_at, confirmed_at
            FROM waitlist_leads
            WHERE confirm_token = $1
            """,
            token,
            fetch_one=True,
        )

        if not lead:
            logger.warning(f"Waitlist confirm: unknown token {token[:8]}…")
            return RedirectResponse(url=f"{frontend_url}/?confirmed=0", status_code=302)

        expires_at = lead.get("confirm_token_expires_at")
        if expires_at and datetime.now(timezone.utc) > expires_at:
            logger.warning(f"Waitlist confirm: expired token {token[:8]}…")
            return RedirectResponse(url=f"{frontend_url}/?confirmed=0", status_code=302)

        await db_service.execute_query(
            """
            UPDATE waitlist_leads
            SET confirmed_at = $1, confirm_token = NULL, confirm_token_expires_at = NULL
            WHERE id = $2
            """,
            datetime.now(timezone.utc),
            lead["id"],
            fetch_one=False,
        )

        logger.info(f"Waitlist confirmed for lead {lead['id']}")
        return RedirectResponse(url=f"{frontend_url}/?confirmed=1", status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Waitlist confirm error: {e}", exc_info=True)
        return RedirectResponse(url=f"{frontend_url}/?confirmed=0", status_code=302)


# TODO (future): GET /api/leads/waitlist — Admin-only CSV-Export der Warteliste


# ---------------------------------------------------------------------------
# Legacy lead endpoints (unchanged)
# ---------------------------------------------------------------------------

class LeadCollectionRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    url: str
    analysis_data: Dict[str, Any]
    session_id: str
    language: Optional[str] = "de"

class LeadCollectionResponse(BaseModel):
    success: bool
    verified: bool
    requires_verification: bool
    message: str
    lead_id: Optional[str] = None

@lead_router.post("/collect", response_model=LeadCollectionResponse)
async def collect_lead(
    request: LeadCollectionRequest,
    http_request: Request,
    background_tasks: BackgroundTasks
):
    """
    Collect a new lead with GDPR consent and send verification email
    
    This endpoint:
    1. Validates the lead data
    2. Stores lead in database with GDPR compliance
    3. Sends double opt-in verification email (German law requirement)
    4. Returns success status
    """
    try:
        # Get client information for GDPR audit trail
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")
        
        # Validate required fields
        if not request.name.strip():
            raise HTTPException(status_code=400, detail="Name is required")
        
        if not request.email.strip():
            raise HTTPException(status_code=400, detail="Email is required")
        
        logger.info(f"Processing lead collection for {request.email}")
        
        # Check if lead already exists
        existing_lead = await db_service.get_lead_by_email(request.email)
        
        if existing_lead:
            if existing_lead.get('email_verified'):
                # Lead already verified - send report immediately
                logger.info(f"Lead {request.email} already verified, sending report")
                
                # Send report in background
                background_tasks.add_task(
                    email_service.send_compliance_report,
                    request.email,
                    request.name,
                    request.analysis_data,
                    {
                        'name': request.name,
                        'email': request.email,
                        'company': request.company or ''
                    }
                )
                
                return LeadCollectionResponse(
                    success=True,
                    verified=True,
                    requires_verification=False,
                    message=f"Report wird sofort an {request.email} gesendet!",
                    lead_id=existing_lead['id']
                )
            else:
                # Lead exists but not verified - resend verification
                logger.info(f"Lead {request.email} exists but not verified, resending verification")
                
                verification_token = existing_lead.get('verification_token')
                if verification_token:
                    background_tasks.add_task(
                        email_service.send_verification_email,
                        request.email,
                        request.name,
                        verification_token,
                        request.language
                    )
                
                return LeadCollectionResponse(
                    success=True,
                    verified=False,
                    requires_verification=True,
                    message=f"Bestätigungs-E-Mail wurde erneut an {request.email} gesendet",
                    lead_id=existing_lead['id']
                )
        
        # Create new lead with GDPR compliance
        lead_data = {
            'name': request.name.strip(),
            'email': request.email.strip().lower(),
            'company': request.company.strip() if request.company else None,
            'source': 'landing_page',
            'url_analyzed': request.url,
            'analysis_data': request.analysis_data,
            'session_id': request.session_id,
            'consent_ip_address': client_ip,
            'consent_user_agent': user_agent,
            'language': request.language
        }
        
        lead_id, verification_token = await db_service.create_lead(lead_data)
        
        logger.info(f"Created new lead {lead_id} for {request.email}")
        
        # Send verification email in background
        background_tasks.add_task(
            email_service.send_verification_email,
            request.email,
            request.name,
            verification_token,
            request.language
        )
        
        return LeadCollectionResponse(
            success=True,
            verified=False,
            requires_verification=True,
            message=f"Bestätigungs-E-Mail wurde an {request.email} gesendet. Bitte prüfen Sie Ihr Postfach.",
            lead_id=lead_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Speichern Ihrer Daten. Bitte versuchen Sie es erneut."
        )

@lead_router.get("/verify/{token}")
async def verify_email(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Verify email address using verification token (Double Opt-In)
    
    After successful verification:
    1. Updates lead status to verified
    2. Sends compliance report PDF via email
    3. Returns success page
    """
    try:
        # Get client information for audit trail
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(f"Processing email verification for token: {token[:8]}...")
        
        # Get lead by verification token
        lead = await db_service.get_lead_by_verification_token(token)
        
        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Ungültiger oder abgelaufener Verifizierungslink"
            )
        
        # Check if already verified
        if lead.get('email_verified'):
            return {
                "success": True,
                "message": "E-Mail bereits verifiziert. Report wurde bereits gesendet.",
                "already_verified": True
            }
        
        # Verify email
        success = await db_service.verify_email(token, client_ip, user_agent)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Verifizierung fehlgeschlagen. Token möglicherweise abgelaufen."
            )
        
        logger.info(f"Email verified successfully for {lead['email']}")
        
        # Send compliance report in background
        background_tasks.add_task(
            email_service.send_compliance_report,
            lead['email'],
            lead['name'],
            lead.get('analysis_data', {}),
            {
                'name': lead['name'],
                'email': lead['email'],
                'company': lead.get('company', '')
            }
        )
        
        return {
            "success": True,
            "message": "E-Mail erfolgreich verifiziert! Ihr Compliance-Report wird in Kürze an Ihre E-Mail-Adresse gesendet.",
            "email": lead['email'],
            "report_sent": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler bei der Verifizierung. Bitte kontaktieren Sie den Support."
        )

@lead_router.get("/stats")
async def get_lead_statistics():
    """
    Get public lead statistics (for demo/transparency purposes)
    
    Returns anonymized statistics about lead generation
    """
    try:
        stats = await db_service.get_lead_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
            "gdpr_compliant": True
        }
        
    except Exception as e:
        logger.error(f"Error getting lead statistics: {e}")
        # Return default stats on error
        return {
            "success": True,
            "statistics": {
                "total_leads": 0,
                "verified_leads": 0,
                "converted_leads": 0,
                "gdpr_compliant": True
            },
            "timestamp": datetime.now().isoformat()
        }

@lead_router.post("/unsubscribe")
async def unsubscribe_lead(email: EmailStr):
    """
    Unsubscribe lead from marketing communications (GDPR Article 7)
    """
    try:
        success = await db_service.update_lead_status_by_email(email, 'unsubscribed')
        
        if success:
            logger.info(f"Lead {email} unsubscribed from communications")
            return {
                "success": True,
                "message": "Sie wurden erfolgreich von weiteren E-Mails abgemeldet."
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="E-Mail-Adresse nicht gefunden"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing lead: {e}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Abmelden. Bitte versuchen Sie es erneut."
        )

