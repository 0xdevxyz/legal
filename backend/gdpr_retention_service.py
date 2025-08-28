"""
GDPR Data Retention and Deletion Service
Handles automated data retention compliance and right to be forgotten requests
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from database_service import db_service
from email_service import email_service
import json
import os

logger = logging.getLogger(__name__)

class GDPRRetentionService:
    def __init__(self):
        self.retention_period_days = int(os.getenv("GDPR_RETENTION_DAYS", "730"))  # 2 years default
        self.cleanup_interval_hours = int(os.getenv("GDPR_CLEANUP_INTERVAL_HOURS", "24"))  # Daily cleanup
        self.is_running = False
        self.deletion_log = []
        
    async def start_automated_cleanup(self):
        """Start the automated GDPR cleanup process"""
        if self.is_running:
            logger.warning("GDPR cleanup already running")
            return
            
        self.is_running = True
        logger.info(f"Starting GDPR automated cleanup - retention period: {self.retention_period_days} days")
        
        while self.is_running:
            try:
                await self.perform_retention_cleanup()
                await asyncio.sleep(self.cleanup_interval_hours * 3600)  # Convert hours to seconds
            except Exception as e:
                logger.error(f"Error in automated cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    def stop_automated_cleanup(self):
        """Stop the automated cleanup process"""
        self.is_running = False
        logger.info("GDPR automated cleanup stopped")
    
    async def perform_retention_cleanup(self) -> Dict[str, Any]:
        """
        Perform GDPR data retention cleanup
        Deletes leads that have exceeded their retention period
        """
        cleanup_results = {
            "timestamp": datetime.now().isoformat(),
            "leads_checked": 0,
            "leads_deleted": 0,
            "deletion_requests_processed": 0,
            "errors": []
        }
        
        try:
            logger.info("Starting GDPR retention cleanup...")
            
            # Get leads that need to be deleted due to retention policy
            expired_leads = await db_service.get_leads_for_retention_cleanup()
            cleanup_results["leads_checked"] = len(expired_leads)
            
            for lead in expired_leads:
                try:
                    # Send deletion notification before deleting (if email still valid)
                    await self._send_deletion_notification(lead)
                    
                    # Permanently delete the lead
                    success = await db_service.delete_lead_permanently(lead["id"])
                    
                    if success:
                        cleanup_results["leads_deleted"] += 1
                        
                        # Log the deletion
                        deletion_log_entry = {
                            "lead_id": lead["id"],
                            "email": lead["email"],
                            "deletion_reason": "automatic_retention_cleanup",
                            "retention_expired_date": lead["data_retention_until"],
                            "deleted_at": datetime.now().isoformat()
                        }
                        self.deletion_log.append(deletion_log_entry)
                        
                        logger.info(f"Deleted expired lead: {lead['email']} (ID: {lead['id']})")
                    else:
                        cleanup_results["errors"].append(f"Failed to delete lead {lead['id']}")
                        
                except Exception as e:
                    error_msg = f"Error deleting lead {lead['id']}: {str(e)}"
                    cleanup_results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Process explicit deletion requests (right to be forgotten)
            deletion_requests = await self._get_pending_deletion_requests()
            
            for request in deletion_requests:
                try:
                    success = await self.process_deletion_request(request["lead_id"], "right_to_be_forgotten")
                    if success:
                        cleanup_results["deletion_requests_processed"] += 1
                except Exception as e:
                    error_msg = f"Error processing deletion request {request['lead_id']}: {str(e)}"
                    cleanup_results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"GDPR cleanup completed: {cleanup_results['leads_deleted']} leads deleted, "
                       f"{cleanup_results['deletion_requests_processed']} deletion requests processed")
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error in retention cleanup: {e}")
            cleanup_results["errors"].append(str(e))
            return cleanup_results
    
    async def process_deletion_request(self, lead_id: str, reason: str = "user_request") -> bool:
        """
        Process a right to be forgotten request
        """
        try:
            # Get lead details before deletion for logging
            if db_service.use_fallback:
                lead = None
                for l in db_service.fallback_storage['leads']:
                    if l['id'] == lead_id:
                        lead = l
                        break
            else:
                # For database mode, would get lead details from database
                lead = {"id": lead_id, "email": "unknown"}
            
            if not lead:
                logger.warning(f"Lead {lead_id} not found for deletion request")
                return False
            
            # Send deletion confirmation email
            await self._send_deletion_confirmation(lead)
            
            # Mark for deletion first
            await db_service.mark_lead_for_deletion(lead_id)
            
            # Permanently delete the lead and all associated data
            success = await db_service.delete_lead_permanently(lead_id)
            
            if success:
                # Log the deletion
                deletion_log_entry = {
                    "lead_id": lead_id,
                    "email": lead.get("email", "unknown"),
                    "deletion_reason": reason,
                    "requested_at": datetime.now().isoformat(),
                    "deleted_at": datetime.now().isoformat(),
                    "gdpr_article": "Article 17 - Right to erasure"
                }
                self.deletion_log.append(deletion_log_entry)
                
                logger.info(f"Processed GDPR deletion request for lead {lead_id} - Reason: {reason}")
                return True
            else:
                logger.error(f"Failed to delete lead {lead_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing deletion request for lead {lead_id}: {e}")
            return False
    
    async def request_data_deletion(self, email: str, reason: str = "user_request") -> Dict[str, Any]:
        """
        Handle user request for data deletion (right to be forgotten)
        """
        try:
            # Find lead by email
            lead = await db_service.get_lead_by_email(email)
            
            if not lead:
                return {
                    "success": False,
                    "message": "No data found for the provided email address",
                    "email": email
                }
            
            # Process the deletion request
            success = await self.process_deletion_request(lead["id"], reason)
            
            if success:
                return {
                    "success": True,
                    "message": "Your data has been permanently deleted as requested",
                    "email": email,
                    "deletion_date": datetime.now().isoformat(),
                    "reference_id": lead["id"]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to process deletion request. Please contact support.",
                    "email": email
                }
                
        except Exception as e:
            logger.error(f"Error processing data deletion request for {email}: {e}")
            return {
                "success": False,
                "message": "An error occurred while processing your request",
                "email": email,
                "error": str(e)
            }
    
    async def get_data_for_export(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Export all data for a lead (GDPR data portability)
        """
        try:
            lead = await db_service.get_lead_by_email(email)
            
            if not lead:
                return None
            
            # Prepare comprehensive data export
            export_data = {
                "personal_data": {
                    "email": lead.get("email"),
                    "name": lead.get("name"),
                    "company": lead.get("company"),
                    "created_at": lead.get("created_at"),
                    "verified_at": lead.get("verified_at")
                },
                "consent_data": {
                    "consent_given": lead.get("consent_given"),
                    "consent_timestamp": lead.get("consent_timestamp"),
                    "consent_ip_address": lead.get("consent_ip_address"),
                    "legal_basis": lead.get("legal_basis")
                },
                "analysis_data": lead.get("analysis_data"),
                "technical_data": {
                    "source": lead.get("source"),
                    "session_id": lead.get("session_id"),
                    "url_analyzed": lead.get("url_analyzed"),
                    "email_verified": lead.get("email_verified"),
                    "status": lead.get("status")
                },
                "gdpr_data": {
                    "data_retention_until": lead.get("data_retention_until"),
                    "deletion_requested": lead.get("deletion_requested", False),
                    "export_generated_at": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Generated data export for {email}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error generating data export for {email}: {e}")
            return None
    
    async def update_retention_period(self, lead_id: str, new_retention_days: int) -> bool:
        """
        Update the data retention period for a specific lead
        """
        try:
            new_retention_date = datetime.now() + timedelta(days=new_retention_days)
            
            if db_service.use_fallback:
                # Fallback mode
                for lead in db_service.fallback_storage['leads']:
                    if lead['id'] == lead_id:
                        lead['data_retention_until'] = new_retention_date.isoformat()
                        lead['updated_at'] = datetime.now().isoformat()
                        logger.info(f"Updated retention period for lead {lead_id} to {new_retention_days} days")
                        return True
                return False
            else:
                # Database mode
                async with db_service.get_connection() as conn:
                    query = """
                    UPDATE leads SET 
                        data_retention_until = $1,
                        updated_at = $2
                    WHERE id = $3
                    """
                    await conn.execute(query, new_retention_date, datetime.now(), lead_id)
                    logger.info(f"Updated retention period for lead {lead_id} to {new_retention_days} days")
                    return True
                    
        except Exception as e:
            logger.error(f"Error updating retention period for lead {lead_id}: {e}")
            return False
    
    async def _send_deletion_notification(self, lead: Dict[str, Any]):
        """Send notification before automatic deletion"""
        try:
            subject = "Automatische Löschung Ihrer Daten - Complyo"
            
            # Create notification email content
            email_content = f"""
            Sehr geehrte/r {lead.get('name', 'Kunde/Kundin')},

            gemäß der Datenschutz-Grundverordnung (DSGVO) werden Ihre Daten automatisch nach Ablauf 
            der Aufbewahrungsfrist gelöscht.

            Ihre Daten wurden am {lead.get('data_retention_until', 'unbekannt')} zur Löschung vorgesehen.

            Falls Sie Fragen haben, kontaktieren Sie uns unter datenschutz@complyo.tech.

            Mit freundlichen Grüßen,
            Ihr Complyo Team
            """
            
            # Would send actual email in production
            logger.info(f"Deletion notification would be sent to {lead['email']}")
            
        except Exception as e:
            logger.error(f"Error sending deletion notification: {e}")
    
    async def _send_deletion_confirmation(self, lead: Dict[str, Any]):
        """Send confirmation after deletion"""
        try:
            subject = "Bestätigung der Datenlöschung - Complyo"
            
            email_content = f"""
            Sehr geehrte/r {lead.get('name', 'Kunde/Kundin')},

            hiermit bestätigen wir die vollständige Löschung Ihrer personenbezogenen Daten 
            aus unserem System gemäß Artikel 17 DSGVO (Recht auf Vergessenwerden).

            Löschung durchgeführt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}
            Referenz-ID: {lead['id']}

            Ihre Daten wurden permanent und unwiderruflich gelöscht.

            Mit freundlichen Grüßen,
            Ihr Complyo Team
            """
            
            # Would send actual email in production
            logger.info(f"Deletion confirmation would be sent to {lead['email']}")
            
        except Exception as e:
            logger.error(f"Error sending deletion confirmation: {e}")
    
    async def _get_pending_deletion_requests(self) -> List[Dict[str, Any]]:
        """Get leads marked for deletion"""
        try:
            if db_service.use_fallback:
                # Fallback mode
                return [
                    {"lead_id": l["id"], "email": l["email"]} 
                    for l in db_service.fallback_storage['leads'] 
                    if l.get("deletion_requested", False)
                ]
            else:
                # Database mode
                async with db_service.get_connection() as conn:
                    query = """
                    SELECT id as lead_id, email 
                    FROM leads 
                    WHERE deletion_requested = TRUE
                    """
                    rows = await conn.fetch(query)
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Error getting pending deletion requests: {e}")
            return []
    
    def get_deletion_statistics(self) -> Dict[str, Any]:
        """Get statistics about deletions performed"""
        return {
            "total_deletions": len(self.deletion_log),
            "automatic_deletions": len([d for d in self.deletion_log if d["deletion_reason"] == "automatic_retention_cleanup"]),
            "user_requested_deletions": len([d for d in self.deletion_log if d["deletion_reason"] in ["user_request", "right_to_be_forgotten"]]),
            "recent_deletions": [d for d in self.deletion_log if 
                               datetime.fromisoformat(d["deleted_at"]) > datetime.now() - timedelta(days=30)],
            "retention_period_days": self.retention_period_days,
            "cleanup_interval_hours": self.cleanup_interval_hours
        }

# Global GDPR retention service instance
gdpr_service = GDPRRetentionService()