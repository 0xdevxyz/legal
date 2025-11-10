"""
Lead Collection API for GDPR-Compliant Lead Generation
Handles lead collection, email verification, and statistics
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging
from datetime import datetime
from database_service import db_service
from email_service import email_service

logger = logging.getLogger(__name__)

lead_router = APIRouter(prefix="/api/leads", tags=["leads"])

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

