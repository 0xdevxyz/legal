"""
GDPR API Endpoints for Data Rights Management
Implements GDPR Articles 17 (Right to Erasure) and 20 (Data Portability)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import logging
from gdpr_retention_service import gdpr_service
from email_service import email_service

logger = logging.getLogger(__name__)

gdpr_router = APIRouter(prefix="/api/gdpr", tags=["gdpr"])

class DataDeletionRequest(BaseModel):
    email: EmailStr
    reason: Optional[str] = "user_request"
    confirmation: bool = True

class DataExportRequest(BaseModel):
    email: EmailStr

class RetentionUpdateRequest(BaseModel):
    lead_id: str
    retention_days: int

@gdpr_router.post("/request-deletion")
async def request_data_deletion(
    request: DataDeletionRequest,
    background_tasks: BackgroundTasks
):
    """
    Handle user request for data deletion (GDPR Article 17 - Right to Erasure)
    """
    try:
        if not request.confirmation:
            raise HTTPException(
                status_code=400, 
                detail="Data deletion requires explicit confirmation"
            )
        
        logger.info(f"Processing data deletion request for {request.email}")
        
        # Process the deletion request
        result = await gdpr_service.request_data_deletion(
            request.email, 
            request.reason
        )
        
        if result["success"]:
            # Send confirmation email in background
            background_tasks.add_task(
                email_service.send_deletion_confirmation_email,
                request.email,
                result.get("reference_id", "unknown")
            )
            
            return {
                "success": True,
                "message": "Your data deletion request has been processed successfully",
                "details": {
                    "email": request.email,
                    "deletion_date": result.get("deletion_date"),
                    "reference_id": result.get("reference_id"),
                    "gdpr_article": "Article 17 - Right to erasure ('right to be forgotten')"
                }
            }
        else:
            return {
                "success": False,
                "message": result["message"],
                "email": request.email
            }
            
    except Exception as e:
        logger.error(f"Error processing deletion request: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to process data deletion request"
        )

@gdpr_router.post("/export-data")
async def export_personal_data(
    request: DataExportRequest,
    background_tasks: BackgroundTasks
):
    """
    Export all personal data for a user (GDPR Article 20 - Data Portability)
    """
    try:
        logger.info(f"Processing data export request for {request.email}")
        
        # Get all data for the user
        export_data = await gdpr_service.get_data_for_export(request.email)
        
        if export_data is None:
            raise HTTPException(
                status_code=404,
                detail="No data found for the provided email address"
            )
        
        # Send export data via email in background
        background_tasks.add_task(
            email_service.send_data_export_email,
            request.email,
            export_data
        )
        
        return {
            "success": True,
            "message": "Your data export has been generated and will be sent to your email address",
            "details": {
                "email": request.email,
                "export_generated_at": export_data["gdpr_data"]["export_generated_at"],
                "data_categories": list(export_data.keys()),
                "gdpr_article": "Article 20 - Right to data portability"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing data export request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process data export request"
        )

@gdpr_router.get("/retention-info")
async def get_retention_information(
    email: EmailStr = Query(..., description="Email address to check retention info")
):
    """
    Get data retention information for a specific email
    """
    try:
        from database_service import db_service
        
        lead = await db_service.get_lead_by_email(email)
        
        if not lead:
            raise HTTPException(
                status_code=404,
                detail="No data found for the provided email address"
            )
        
        return {
            "email": email,
            "data_retention_info": {
                "created_at": lead.get("created_at"),
                "data_retention_until": lead.get("data_retention_until"),
                "days_until_deletion": (
                    # Calculate days until deletion
                    None  # Would calculate in production
                ),
                "legal_basis": lead.get("legal_basis", "consent"),
                "can_request_deletion": True,
                "can_request_export": True
            },
            "gdpr_rights": {
                "right_to_access": "Article 15 - Right of access by the data subject",
                "right_to_rectification": "Article 16 - Right to rectification",
                "right_to_erasure": "Article 17 - Right to erasure ('right to be forgotten')",
                "right_to_data_portability": "Article 20 - Right to data portability"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting retention information: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve retention information"
        )

@gdpr_router.post("/admin/update-retention")
async def admin_update_retention_period(
    request: RetentionUpdateRequest,
    admin_api_key: str = Query(..., alias="admin_api_key")
):
    """
    Admin endpoint to update data retention period for a specific lead
    """
    # Simple admin authentication (use proper auth in production)
    if admin_api_key != "admin_complyo_2025":
        raise HTTPException(status_code=401, detail="Unauthorized admin access")
    
    try:
        if request.retention_days < 1 or request.retention_days > 3650:  # Max 10 years
            raise HTTPException(
                status_code=400,
                detail="Retention period must be between 1 and 3650 days"
            )
        
        success = await gdpr_service.update_retention_period(
            request.lead_id,
            request.retention_days
        )
        
        if success:
            return {
                "success": True,
                "message": f"Retention period updated to {request.retention_days} days",
                "lead_id": request.lead_id,
                "new_retention_days": request.retention_days
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating retention period: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update retention period"
        )

@gdpr_router.get("/admin/cleanup-status")
async def admin_get_cleanup_status(
    admin_api_key: str = Query(..., alias="admin_api_key")
):
    """
    Admin endpoint to get GDPR cleanup and deletion statistics
    """
    # Simple admin authentication
    if admin_api_key != "admin_complyo_2025":
        raise HTTPException(status_code=401, detail="Unauthorized admin access")
    
    try:
        stats = gdpr_service.get_deletion_statistics()
        
        return {
            "cleanup_status": {
                "is_running": gdpr_service.is_running,
                "retention_period_days": stats["retention_period_days"],
                "cleanup_interval_hours": stats["cleanup_interval_hours"]
            },
            "deletion_statistics": {
                "total_deletions": stats["total_deletions"],
                "automatic_deletions": stats["automatic_deletions"],
                "user_requested_deletions": stats["user_requested_deletions"],
                "recent_deletions_count": len(stats["recent_deletions"])
            },
            "recent_deletions": stats["recent_deletions"][:10]  # Last 10 deletions
        }
        
    except Exception as e:
        logger.error(f"Error getting cleanup status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cleanup status"
        )

@gdpr_router.post("/admin/run-cleanup")
async def admin_run_manual_cleanup(
    background_tasks: BackgroundTasks,
    admin_api_key: str = Query(..., alias="admin_api_key")
):
    """
    Admin endpoint to manually trigger GDPR cleanup process
    """
    # Simple admin authentication
    if admin_api_key != "admin_complyo_2025":
        raise HTTPException(status_code=401, detail="Unauthorized admin access")
    
    try:
        logger.info("Manual GDPR cleanup triggered by admin")
        
        # Run cleanup in background
        background_tasks.add_task(gdpr_service.perform_retention_cleanup)
        
        return {
            "success": True,
            "message": "Manual GDPR cleanup process started",
            "triggered_at": "now",
            "note": "Cleanup is running in the background. Check cleanup status for results."
        }
        
    except Exception as e:
        logger.error(f"Error triggering manual cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger manual cleanup"
        )

@gdpr_router.get("/privacy-policy")
async def get_privacy_policy_info():
    """
    Get privacy policy and GDPR compliance information
    """
    return {
        "privacy_policy": {
            "data_controller": "Complyo GmbH",
            "contact_email": "datenschutz@complyo.tech",
            "data_protection_officer": "dpo@complyo.tech",
            "legal_basis": "Article 6(1)(a) GDPR - Consent",
            "data_retention_period": "24 months from collection",
            "purposes_of_processing": [
                "Website compliance analysis",
                "Lead management and communication",
                "Service improvement and analytics"
            ]
        },
        "your_rights": {
            "right_to_access": "Request access to your personal data",
            "right_to_rectification": "Request correction of inaccurate data",
            "right_to_erasure": "Request deletion of your personal data",
            "right_to_data_portability": "Request export of your personal data",
            "right_to_object": "Object to processing of your personal data",
            "right_to_withdraw_consent": "Withdraw consent at any time"
        },
        "contact_information": {
            "exercise_rights": "Send requests to datenschutz@complyo.tech",
            "supervisory_authority": "Contact your local data protection authority",
            "response_time": "We will respond within 30 days"
        }
    }