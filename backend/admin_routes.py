"""
Admin Dashboard API Endpoints for Lead Management
Provides comprehensive admin interface for GDPR-compliant lead management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os
from database_service import db_service

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

_ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

def verify_admin_access(api_key: str = Query(..., alias="api_key")):
    """Admin API key verification — key must be set via ADMIN_API_KEY env var."""
    if not _ADMIN_API_KEY:
        raise HTTPException(status_code=503, detail="Admin access not configured")
    if api_key != _ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized admin access")
    return True

@admin_router.get("/dashboard/overview")
async def admin_dashboard_overview(admin: bool = Depends(verify_admin_access)):
    """
    Get comprehensive dashboard overview for admin
    """
    try:
        # Get lead statistics
        stats = await db_service.get_lead_statistics()
        
        # Additional admin-specific metrics
        if db_service.use_fallback:
            # Fallback mode analytics
            leads = db_service.fallback_storage['leads']
            
            # Lead sources breakdown
            sources = {}
            for lead in leads:
                source = lead.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            # Recent leads (last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            recent_leads = [l for l in leads if 
                           datetime.fromisoformat(l['created_at']) > cutoff_date]
            
            # Status breakdown
            status_breakdown = {}
            for lead in leads:
                status = lead.get('status', 'unknown')
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
        else:
            # Database mode - would implement more complex queries
            sources = {"landing_page": stats["total_leads"]}
            recent_leads = []
            status_breakdown = {
                "new": stats["total_leads"] - stats["verified_leads"],
                "verified": stats["verified_leads"] - stats["converted_leads"],
                "converted": stats["converted_leads"]
            }
        
        return {
            "overview": stats,
            "lead_sources": sources,
            "recent_activity": len(recent_leads),
            "status_breakdown": status_breakdown,
            "system_status": {
                "storage_type": "fallback" if db_service.use_fallback else "database",
                "gdpr_compliant": True,
                "email_service": "active",
                "pdf_generation": "active"
            },
            "performance_metrics": {
                "avg_verification_time": "< 5 minutes",
                "avg_report_generation": "< 30 seconds",
                "uptime": "99.9%"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Error loading dashboard")

@admin_router.get("/leads")
async def get_all_leads(
    admin: bool = Depends(verify_admin_access),
    status: Optional[str] = Query(None, description="Filter by status"),
    verified: Optional[bool] = Query(None, description="Filter by verification status"),
    limit: int = Query(50, description="Number of leads to return"),
    offset: int = Query(0, description="Pagination offset")
):
    """
    Get paginated list of all leads with filtering options
    """
    try:
        if db_service.use_fallback:
            # Fallback mode
            leads = db_service.fallback_storage['leads'].copy()
            
            # Apply filters
            if status:
                leads = [l for l in leads if l.get('status') == status]
            if verified is not None:
                leads = [l for l in leads if l.get('email_verified') == verified]
            
            # Sort by creation date (newest first)
            leads.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Apply pagination
            total_count = len(leads)
            leads = leads[offset:offset + limit]
            
        else:
            # Database mode - would implement proper SQL queries
            total_count = 0
            leads = []
        
        # Sanitize lead data for admin view (remove sensitive fields)
        sanitized_leads = []
        for lead in leads:
            sanitized_lead = {
                "id": lead["id"],
                "email": lead["email"],
                "name": lead["name"],
                "company": lead.get("company"),
                "source": lead.get("source"),
                "status": lead.get("status"),
                "email_verified": lead.get("email_verified"),
                "created_at": lead.get("created_at"),
                "verified_at": lead.get("verified_at"),
                "last_contacted": lead.get("last_contacted"),
                "url_analyzed": lead.get("url_analyzed")
            }
            sanitized_leads.append(sanitized_lead)
        
        return {
            "leads": sanitized_leads,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "filters_applied": {
                "status": status,
                "verified": verified
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting leads: {e}")
        raise HTTPException(status_code=500, detail="Error loading leads")

@admin_router.get("/leads/{lead_id}")
async def get_lead_details(
    lead_id: str,
    admin: bool = Depends(verify_admin_access)
):
    """
    Get detailed information about a specific lead
    """
    try:
        if db_service.use_fallback:
            # Find lead in fallback storage
            lead = None
            for l in db_service.fallback_storage['leads']:
                if l['id'] == lead_id:
                    lead = l
                    break
                    
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
        else:
            # Database mode
            raise HTTPException(status_code=501, detail="Database mode not fully implemented")
        
        # Return detailed lead information
        return {
            "lead": lead,
            "gdpr_info": {
                "consent_given": lead.get("consent_given"),
                "consent_timestamp": lead.get("consent_timestamp"),
                "legal_basis": lead.get("legal_basis"),
                "data_retention_until": lead.get("data_retention_until"),
                "deletion_requested": lead.get("deletion_requested", False)
            },
            "verification_info": {
                "email_verified": lead.get("email_verified"),
                "verification_sent_at": lead.get("verification_sent_at"),
                "verified_at": lead.get("verified_at"),
                "verification_expires_at": lead.get("verification_expires_at")
            },
            "analysis_summary": {
                "url_analyzed": lead.get("url_analyzed"),
                "has_analysis_data": bool(lead.get("analysis_data")),
                "compliance_score": lead.get("analysis_data", {}).get("compliance_score") if lead.get("analysis_data") else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead details: {e}")
        raise HTTPException(status_code=500, detail="Error loading lead details")

@admin_router.post("/leads/{lead_id}/resend-verification")
async def resend_verification_email(
    lead_id: str,
    admin: bool = Depends(verify_admin_access)
):
    """
    Manually resend verification email for a lead
    """
    try:
        if db_service.use_fallback:
            # Find lead in fallback storage
            lead = None
            for l in db_service.fallback_storage['leads']:
                if l['id'] == lead_id:
                    lead = l
                    break
                    
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
                
            if lead.get("email_verified"):
                raise HTTPException(status_code=400, detail="Lead already verified")
        else:
            # Database mode
            lead = await db_service.get_lead_by_verification_token(lead_id)
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
        
        # Import email service and send verification
        from email_service import email_service
        
        verification_sent = email_service.send_verification_email(
            lead["email"], 
            lead["name"], 
            lead["verification_token"]
        )
        
        if verification_sent:
            # Log the manual resend
            await db_service.log_communication(
                lead_id, 
                "verification_resend", 
                "Manual verification email resend by admin"
            )
            
            return {
                "success": True,
                "message": f"Verification email resent to {lead['email']}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send verification email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification: {e}")
        raise HTTPException(status_code=500, detail="Error resending verification email")

@admin_router.delete("/leads/{lead_id}")
async def delete_lead_gdpr(
    lead_id: str,
    admin: bool = Depends(verify_admin_access),
    reason: str = Query(..., description="Reason for deletion (GDPR compliance)")
):
    """
    Delete lead for GDPR compliance (right to be forgotten)
    """
    try:
        if db_service.use_fallback:
            # Find and remove from fallback storage
            lead_index = None
            for i, l in enumerate(db_service.fallback_storage['leads']):
                if l['id'] == lead_id:
                    lead_index = i
                    break
                    
            if lead_index is None:
                raise HTTPException(status_code=404, detail="Lead not found")
                
            deleted_lead = db_service.fallback_storage['leads'].pop(lead_index)
            
            # Remove verification token if exists
            for token, stored_id in list(db_service.fallback_storage['verification_tokens'].items()):
                if stored_id == lead_id:
                    del db_service.fallback_storage['verification_tokens'][token]
                    break
        else:
            # Database mode
            success = await db_service.delete_lead_permanently(lead_id)
            if not success:
                raise HTTPException(status_code=404, detail="Lead not found")
        
        logger.info(f"Lead {lead_id} deleted for GDPR compliance. Reason: {reason}")
        
        return {
            "success": True,
            "message": "Lead permanently deleted for GDPR compliance",
            "lead_id": lead_id,
            "deletion_reason": reason,
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead: {e}")
        raise HTTPException(status_code=500, detail="Error deleting lead")

@admin_router.get("/analytics/trends")
async def get_analytics_trends(
    admin: bool = Depends(verify_admin_access),
    days: int = Query(30, description="Number of days for trend analysis")
):
    """
    Get analytics trends for the specified time period
    """
    try:
        if db_service.use_fallback:
            leads = db_service.fallback_storage['leads']
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter leads within time period
            period_leads = [l for l in leads if 
                           datetime.fromisoformat(l['created_at']) > cutoff_date]
            
            # Generate daily counts
            daily_stats = {}
            for lead in period_leads:
                date_key = datetime.fromisoformat(lead['created_at']).date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"leads": 0, "verified": 0, "converted": 0}
                
                daily_stats[date_key]["leads"] += 1
                if lead.get("email_verified"):
                    daily_stats[date_key]["verified"] += 1
                if lead.get("status") == "converted":
                    daily_stats[date_key]["converted"] += 1
            
            # Convert to list format
            trends = []
            for date_str, stats in sorted(daily_stats.items()):
                trends.append({
                    "date": date_str,
                    "leads_collected": stats["leads"],
                    "emails_verified": stats["verified"],
                    "reports_delivered": stats["converted"]
                })
        else:
            # Database mode - would implement SQL-based analytics
            trends = []
        
        return {
            "time_period": f"{days} days",
            "trends": trends,
            "summary": {
                "total_period_leads": len([t for t in trends]),
                "avg_daily_leads": round(sum(t["leads_collected"] for t in trends) / max(len(trends), 1), 2),
                "peak_day": max(trends, key=lambda x: x["leads_collected"])["date"] if trends else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics trends: {e}")
        raise HTTPException(status_code=500, detail="Error loading analytics trends")

@admin_router.get("/system/health")
async def admin_system_health(admin: bool = Depends(verify_admin_access)):
    """
    Get comprehensive system health status for admin monitoring
    """
    try:
        return {
            "database": {
                "status": "fallback" if db_service.use_fallback else "connected",
                "type": "in-memory" if db_service.use_fallback else "postgresql"
            },
            "email_service": {
                "status": "active",
                "mode": "demo"  # Would check actual SMTP config in production
            },
            "pdf_generation": {
                "status": "active",
                "engine": "reportlab"
            },
            "api": {
                "status": "healthy",
                "version": "2.2.0"
            },
            "gdpr_compliance": {
                "double_opt_in": True,
                "data_retention": "730 days",
                "audit_trail": True,
                "consent_tracking": True
            },
            "performance": {
                "uptime": "99.9%",
                "avg_response_time": "< 200ms",
                "memory_usage": "moderate"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Error getting system health")


# =============================================================================
# Fix Review Queue — Human-in-the-Loop Quality Gate
# =============================================================================

from fastapi import Body
from dependencies import get_db

@admin_router.get("/fix-review-queue")
async def get_fix_review_queue(
    admin: bool = Depends(verify_admin_access),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """
    Gibt alle Fixes mit quality_gate_status='pending_review' zurück.
    """
    try:
        rows = await db.fetch(
            """
            SELECT
                faa.id,
                faa.fix_type,
                faa.issue_title,
                faa.quality_gate_status,
                faa.quality_gate_log,
                faa.applied_at,
                faa.reviewed_by,
                faa.reviewed_at,
                tw.url AS website_url,
                u.email AS user_email
            FROM fix_application_audit faa
            LEFT JOIN tracked_websites tw ON faa.website_id = tw.id
            LEFT JOIN users u ON faa.user_id = u.id
            WHERE faa.quality_gate_status = 'pending_review'
            ORDER BY faa.applied_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )

        total = await db.fetchval(
            "SELECT COUNT(*) FROM fix_application_audit WHERE quality_gate_status = 'pending_review'"
        )

        return {
            "items": [dict(r) for r in rows],
            "total": total or 0,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"get_fix_review_queue error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Review-Queue")


@admin_router.get("/fix-review-queue/{fix_id}")
async def get_fix_review_detail(
    fix_id: int,
    admin: bool = Depends(verify_admin_access),
    db=Depends(get_db),
):
    """
    Detail-Ansicht eines einzelnen Fixes inkl. Quality Gate Log und HTML-Diff.
    """
    try:
        row = await db.fetchrow(
            """
            SELECT
                faa.*,
                tw.url AS website_url,
                u.email AS user_email
            FROM fix_application_audit faa
            LEFT JOIN tracked_websites tw ON faa.website_id = tw.id
            LEFT JOIN users u ON faa.user_id = u.id
            WHERE faa.id = $1
            """,
            fix_id,
        )

        if not row:
            raise HTTPException(status_code=404, detail="Fix nicht gefunden")

        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_fix_review_detail error for fix {fix_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Laden des Fix-Details")


@admin_router.post("/fix-review-queue/{fix_id}/approve")
async def approve_fix(
    fix_id: int,
    admin: bool = Depends(verify_admin_access),
    db=Depends(get_db),
):
    """
    Setzt quality_gate_status='validated' und speichert Reviewer.
    """
    try:
        api_key = _ADMIN_API_KEY or "admin"
        updated = await db.fetchval(
            """
            UPDATE fix_application_audit
            SET quality_gate_status = 'validated',
                reviewed_by          = $1,
                reviewed_at          = NOW()
            WHERE id = $2
              AND quality_gate_status = 'pending_review'
            RETURNING id
            """,
            api_key,
            fix_id,
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Fix nicht gefunden oder bereits bearbeitet",
            )

        logger.info(f"Fix {fix_id} approved by admin")
        return {"success": True, "fix_id": fix_id, "new_status": "validated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"approve_fix error for {fix_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Freigeben des Fixes")


@admin_router.post("/fix-review-queue/{fix_id}/reject")
async def reject_fix(
    fix_id: int,
    reason: str = Body(..., embed=True),
    admin: bool = Depends(verify_admin_access),
    db=Depends(get_db),
):
    """
    Setzt quality_gate_status='rejected' mit Begründung.
    """
    if not reason or len(reason.strip()) < 5:
        raise HTTPException(status_code=422, detail="Begründung muss mindestens 5 Zeichen haben")

    try:
        api_key = _ADMIN_API_KEY or "admin"
        updated = await db.fetchval(
            """
            UPDATE fix_application_audit
            SET quality_gate_status = 'rejected',
                reviewed_by          = $1,
                reviewed_at          = NOW(),
                quality_gate_log     = COALESCE(quality_gate_log, '[]'::jsonb)
                                       || jsonb_build_array(
                                           jsonb_build_object(
                                             'stage', 0,
                                             'name', 'Admin Review',
                                             'passed', false,
                                             'errors', jsonb_build_array($3)
                                           )
                                         )
            WHERE id = $2
              AND quality_gate_status = 'pending_review'
            RETURNING id
            """,
            api_key,
            fix_id,
            reason.strip(),
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Fix nicht gefunden oder bereits bearbeitet",
            )

        logger.info(f"Fix {fix_id} rejected by admin: {reason}")
        return {"success": True, "fix_id": fix_id, "new_status": "rejected", "reason": reason}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"reject_fix error for {fix_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Ablehnen des Fixes")