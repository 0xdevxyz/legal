"""
Production Database Service for GDPR-Compliant Lead Management
Replaces in-memory storage with PostgreSQL for production use
"""

import asyncpg
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://complyo_user:ComplYo2025SecurePass@localhost:5432/complyo_db")
        self.pool = None
        self.use_fallback = False
        self.fallback_storage = {
            'leads': [],
            'verification_tokens': {}
        }
        
    async def initialize(self):
        """Initialize database connection pool with fallback to in-memory storage"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool initialized")
            self.use_fallback = False
            return True
        except Exception as e:
            logger.warning(f"Database connection failed, using in-memory fallback: {e}")
            self.use_fallback = True
            return True  # Still successful, just using fallback
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """
        Create a new GDPR-compliant lead record
        """
        if self.use_fallback:
            return await self._create_lead_fallback(lead_data)
            
        try:
            async with self.get_connection() as conn:
                lead_id = str(uuid.uuid4())
                verification_token = str(uuid.uuid4())
                
                query = """
                INSERT INTO leads (
                    id, email, name, company, source, url_analyzed, analysis_data, session_id,
                    consent_given, consent_timestamp, consent_ip_address, consent_user_agent, legal_basis,
                    verification_token, verification_sent_at, verification_expires_at,
                    data_retention_until, status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                )
                """
                
                await conn.execute(
                    query,
                    lead_id,
                    lead_data['email'].lower(),
                    lead_data['name'],
                    lead_data.get('company'),
                    lead_data.get('source', 'landing_page'),
                    lead_data.get('url_analyzed'),
                    json.dumps(lead_data.get('analysis_data')) if lead_data.get('analysis_data') else None,
                    lead_data.get('session_id'),
                    True,  # consent_given
                    datetime.now(),  # consent_timestamp
                    lead_data.get('consent_ip_address'),
                    lead_data.get('consent_user_agent'),
                    'consent',  # legal_basis
                    verification_token,
                    datetime.now(),  # verification_sent_at
                    datetime.now() + timedelta(hours=24),  # verification_expires_at
                    datetime.now() + timedelta(days=730),  # data_retention_until (2 years)
                    'new'  # status
                )
                
                # Log consent
                await self.log_consent(lead_id, 'marketing', True, lead_data.get('consent_ip_address'), lead_data.get('consent_user_agent'))
                
                logger.info(f"Created GDPR-compliant lead: {lead_data['email']} with ID: {lead_id}")
                return lead_id, verification_token
                
        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            # Fallback to in-memory storage on database error
            logger.warning("Falling back to in-memory storage")
            return await self._create_lead_fallback(lead_data)
    
    async def _create_lead_fallback(self, lead_data: Dict[str, Any]) -> str:
        """Fallback method using in-memory storage"""
        lead_id = str(uuid.uuid4())
        verification_token = str(uuid.uuid4())
        
        lead_record = {
            "id": lead_id,
            "email": lead_data['email'].lower(),
            "name": lead_data['name'],
            "company": lead_data.get('company'),
            "source": lead_data.get('source', 'landing_page'),
            "url_analyzed": lead_data.get('url_analyzed'),
            "analysis_data": lead_data.get('analysis_data'),
            "session_id": lead_data.get('session_id'),
            "consent_given": True,
            "consent_timestamp": datetime.now().isoformat(),
            "consent_ip_address": lead_data.get('consent_ip_address'),
            "consent_user_agent": lead_data.get('consent_user_agent'),
            "legal_basis": 'consent',
            "email_verified": False,
            "verification_token": verification_token,
            "verification_sent_at": datetime.now().isoformat(),
            "verification_expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "data_retention_until": (datetime.now() + timedelta(days=730)).isoformat(),
            "status": 'new',
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.fallback_storage['leads'].append(lead_record)
        self.fallback_storage['verification_tokens'][verification_token] = lead_id
        
        logger.info(f"Created lead in fallback storage: {lead_data['email']} with ID: {lead_id}")
        return lead_id, verification_token
    
    async def get_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get lead by email address"""
        if self.use_fallback:
            return self._get_lead_by_email_fallback(email)
            
        try:
            async with self.get_connection() as conn:
                query = """
                SELECT * FROM leads WHERE email = $1 ORDER BY created_at DESC LIMIT 1
                """
                row = await conn.fetchrow(query, email.lower())
                
                if row:
                    lead = dict(row)
                    # Parse JSON fields
                    if lead['analysis_data']:
                        lead['analysis_data'] = json.loads(lead['analysis_data'])
                    return lead
                return None
                
        except Exception as e:
            logger.error(f"Error getting lead by email {email}: {e}")
            # Fallback to in-memory storage
            return self._get_lead_by_email_fallback(email)
    
    def _get_lead_by_email_fallback(self, email: str) -> Optional[Dict[str, Any]]:
        """Fallback method using in-memory storage"""
        for lead in self.fallback_storage['leads']:
            if lead['email'].lower() == email.lower():
                return lead
        return None
    
    async def get_lead_by_verification_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get lead by verification token"""
        if self.use_fallback:
            return self._get_lead_by_verification_token_fallback(token)
            
        try:
            async with self.get_connection() as conn:
                query = """
                SELECT * FROM leads WHERE verification_token = $1
                """
                row = await conn.fetchrow(query, token)
                
                if row:
                    lead = dict(row)
                    # Parse JSON fields
                    if lead['analysis_data']:
                        lead['analysis_data'] = json.loads(lead['analysis_data'])
                    return lead
                return None
                
        except Exception as e:
            logger.error(f"Error getting lead by token: {e}")
            return self._get_lead_by_verification_token_fallback(token)
    
    def _get_lead_by_verification_token_fallback(self, token: str) -> Optional[Dict[str, Any]]:
        """Fallback method using in-memory storage"""
        lead_id = self.fallback_storage['verification_tokens'].get(token)
        if lead_id:
            for lead in self.fallback_storage['leads']:
                if lead['id'] == lead_id:
                    return lead
        return None
    
    async def verify_email(self, verification_token: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Verify email address and update lead status"""
        if self.use_fallback:
            return self._verify_email_fallback(verification_token)
            
        try:
            async with self.get_connection() as conn:
                # Check if token exists and is not expired
                query = """
                SELECT id, email, verification_expires_at FROM leads 
                WHERE verification_token = $1 AND email_verified = FALSE
                """
                lead = await conn.fetchrow(query, verification_token)
                
                if not lead:
                    return False
                
                # Check if token is expired
                if lead['verification_expires_at'] < datetime.now():
                    return False
                
                # Update lead as verified
                update_query = """
                UPDATE leads SET 
                    email_verified = TRUE,
                    verified_at = $1,
                    status = 'verified',
                    updated_at = $1
                WHERE verification_token = $2
                """
                await conn.execute(update_query, datetime.now(), verification_token)
                
                # Log verification
                verification_query = """
                INSERT INTO email_verifications (lead_id, verification_token, status, verified_at, ip_address, user_agent)
                VALUES ($1, $2, 'verified', $3, $4, $5)
                """
                await conn.execute(
                    verification_query,
                    lead['id'],
                    verification_token,
                    datetime.now(),
                    ip_address,
                    user_agent
                )
                
                logger.info(f"Email verified for lead: {lead['email']}")
                return True
                
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return self._verify_email_fallback(verification_token)
    
    def _verify_email_fallback(self, verification_token: str) -> bool:
        """Fallback email verification using in-memory storage"""
        lead_id = self.fallback_storage['verification_tokens'].get(verification_token)
        if not lead_id:
            return False
            
        for lead in self.fallback_storage['leads']:
            if lead['id'] == lead_id:
                # Check if expired
                expires_at = datetime.fromisoformat(lead['verification_expires_at'])
                if expires_at < datetime.now():
                    return False
                    
                # Update lead
                lead['email_verified'] = True
                lead['verified_at'] = datetime.now().isoformat()
                lead['status'] = 'verified'
                lead['updated_at'] = datetime.now().isoformat()
                
                # Remove token
                del self.fallback_storage['verification_tokens'][verification_token]
                
                logger.info(f"Email verified for lead (fallback): {lead['email']}")
                return True
        return False
    
    async def update_lead_status_by_email(self, email: str, status: str) -> bool:
        """Update lead status by email address"""
        lead = await self.get_lead_by_email(email)
        if not lead:
            return False
        return await self.update_lead_status(lead['id'], status)
    
    async def update_lead_status(self, lead_id: str, status: str, **kwargs) -> bool:
        """Update lead status and additional fields"""
        if self.use_fallback:
            return self._update_lead_status_fallback(lead_id, status, **kwargs)
            
        try:
            async with self.get_connection() as conn:
                # Build dynamic update query
                set_clauses = ["status = $2", "updated_at = $3"]
                params = [lead_id, status, datetime.now()]
                param_count = 3
                
                for key, value in kwargs.items():
                    if key in ['last_contacted', 'report_sent_at']:
                        param_count += 1
                        set_clauses.append(f"{key} = ${param_count}")
                        params.append(value)
                
                query = f"""
                UPDATE leads SET {', '.join(set_clauses)}
                WHERE id = $1
                """
                
                await conn.execute(query, *params)
                logger.info(f"Updated lead {lead_id} status to {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return self._update_lead_status_fallback(lead_id, status, **kwargs)
    
    def _update_lead_status_fallback(self, lead_id: str, status: str, **kwargs) -> bool:
        """Fallback method for updating lead status"""
        for lead in self.fallback_storage['leads']:
            if lead['id'] == lead_id:
                lead['status'] = status
                lead['updated_at'] = datetime.now().isoformat()
                for key, value in kwargs.items():
                    if key in ['last_contacted', 'report_sent_at']:
                        lead[key] = value.isoformat() if hasattr(value, 'isoformat') else value
                logger.info(f"Updated lead {lead_id} status to {status} (fallback)")
                return True
        return False
    
    async def log_consent(self, lead_id: str, consent_type: str, granted: bool, ip_address: str = None, user_agent: str = None) -> bool:
        """Log consent for GDPR compliance"""
        if self.use_fallback:
            logger.info(f"Logged consent for lead {lead_id}: {consent_type} = {granted} (fallback mode)")
            return True
            
        try:
            async with self.get_connection() as conn:
                query = """
                INSERT INTO lead_consents (lead_id, consent_type, granted, ip_address, user_agent)
                VALUES ($1, $2, $3, $4, $5)
                """
                await conn.execute(query, lead_id, consent_type, granted, ip_address, user_agent)
                logger.info(f"Logged consent for lead {lead_id}: {consent_type} = {granted}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging consent: {e}")
            return True  # Don't fail the main operation if logging fails
    
    async def log_communication(self, lead_id: str, comm_type: str, subject: str, content: str = None) -> bool:
        """Log communication for GDPR compliance"""
        if self.use_fallback:
            logger.info(f"Logged communication for lead {lead_id}: {comm_type} (fallback mode)")
            return True
            
        try:
            async with self.get_connection() as conn:
                query = """
                INSERT INTO communication_log (lead_id, type, subject, content)
                VALUES ($1, $2, $3, $4)
                """
                await conn.execute(query, lead_id, comm_type, subject, content)
                logger.info(f"Logged communication for lead {lead_id}: {comm_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging communication: {e}")
            return True  # Don't fail the main operation if logging fails
    
    async def get_lead_statistics(self) -> Dict[str, Any]:
        """Get lead statistics for dashboard"""
        if self.use_fallback:
            return self._get_lead_statistics_fallback()
            
        try:
            async with self.get_connection() as conn:
                # Total leads
                total_leads = await conn.fetchval("SELECT COUNT(*) FROM leads")
                
                # Verified leads
                verified_leads = await conn.fetchval("SELECT COUNT(*) FROM leads WHERE email_verified = TRUE")
                
                # Converted leads (report sent)
                converted_leads = await conn.fetchval("SELECT COUNT(*) FROM leads WHERE status = 'converted'")
                
                # Leads in last 24 hours
                leads_24h = await conn.fetchval(
                    "SELECT COUNT(*) FROM leads WHERE created_at > $1",
                    datetime.now() - timedelta(hours=24)
                )
                
                # Calculate rates
                verification_rate = round((verified_leads / total_leads * 100), 2) if total_leads > 0 else 0
                conversion_rate = round((converted_leads / verified_leads * 100), 2) if verified_leads > 0 else 0
                
                return {
                    "total_leads": total_leads,
                    "verified_leads": verified_leads,
                    "converted_leads": converted_leads,
                    "leads_last_24h": leads_24h,
                    "verification_rate": verification_rate,
                    "conversion_rate": conversion_rate,
                    "gdpr_compliant": True,
                    "data_retention_days": 730,
                    "storage_type": "database"
                }
                
        except Exception as e:
            logger.error(f"Error getting lead statistics: {e}")
            return self._get_lead_statistics_fallback()
    
    def _get_lead_statistics_fallback(self) -> Dict[str, Any]:
        """Fallback method for getting lead statistics"""
        leads = self.fallback_storage['leads']
        total_leads = len(leads)
        verified_leads = len([l for l in leads if l.get('email_verified', False)])
        converted_leads = len([l for l in leads if l.get('status') == 'converted'])
        
        # Leads in last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        leads_24h = len([l for l in leads if 
                        datetime.fromisoformat(l['created_at']) > cutoff_time])
        
        verification_rate = round((verified_leads / total_leads * 100), 2) if total_leads > 0 else 0
        conversion_rate = round((converted_leads / verified_leads * 100), 2) if verified_leads > 0 else 0
        
        return {
            "total_leads": total_leads,
            "verified_leads": verified_leads,
            "converted_leads": converted_leads,
            "leads_last_24h": leads_24h,
            "verification_rate": verification_rate,
            "conversion_rate": conversion_rate,
            "gdpr_compliant": True,
            "data_retention_days": 730,
            "storage_type": "fallback"
        }
    
    async def get_leads_for_retention_cleanup(self) -> List[Dict[str, Any]]:
        """Get leads that need to be deleted due to GDPR data retention"""
        try:
            async with self.get_connection() as conn:
                query = """
                SELECT id, email, name, data_retention_until 
                FROM leads 
                WHERE data_retention_until < $1 AND deletion_requested = FALSE
                """
                rows = await conn.fetch(query, datetime.now())
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting leads for retention cleanup: {e}")
            return []
    
    async def mark_lead_for_deletion(self, lead_id: str) -> bool:
        """Mark lead for deletion (GDPR right to be forgotten)"""
        try:
            async with self.get_connection() as conn:
                query = """
                UPDATE leads SET 
                    deletion_requested = TRUE,
                    deletion_requested_at = $1
                WHERE id = $2
                """
                await conn.execute(query, datetime.now(), lead_id)
                logger.info(f"Marked lead {lead_id} for deletion")
                return True
                
        except Exception as e:
            logger.error(f"Error marking lead for deletion: {e}")
            return False
    
    async def delete_lead_permanently(self, lead_id: str) -> bool:
        """Permanently delete lead and all associated data"""
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    # Delete in correct order due to foreign key constraints
                    await conn.execute("DELETE FROM communication_log WHERE lead_id = $1", lead_id)
                    await conn.execute("DELETE FROM email_verifications WHERE lead_id = $1", lead_id)
                    await conn.execute("DELETE FROM lead_consents WHERE lead_id = $1", lead_id)
                    await conn.execute("DELETE FROM leads WHERE id = $1", lead_id)
                    
                logger.info(f"Permanently deleted lead {lead_id} and all associated data")
                return True
                
        except Exception as e:
            logger.error(f"Error permanently deleting lead: {e}")
            return False
    
    # ==================== AI COMPLIANCE ADD-ON METHODS ====================
    
    async def check_user_addon(self, user_id: str, addon_key: str) -> bool:
        """
        Check if user has an active add-on
        """
        if self.use_fallback:
            return False  # No add-ons in fallback mode
        
        try:
            async with self.get_connection() as conn:
                query = """
                    SELECT id FROM user_addons 
                    WHERE user_id = $1 AND addon_key = $2 
                    AND status = 'active'
                    AND (expires_at IS NULL OR expires_at > NOW())
                """
                result = await conn.fetchrow(query, user_id, addon_key)
                return result is not None
        
        except Exception as e:
            logger.error(f"Error checking user addon: {e}")
            return False
    
    async def get_addon_limits(self, user_id: str, addon_key: str) -> Dict[str, Any]:
        """
        Get limits for a user's add-on
        """
        if self.use_fallback:
            return {"ai_systems": 10}  # Default limit
        
        try:
            async with self.get_connection() as conn:
                query = """
                    SELECT limits FROM user_addons 
                    WHERE user_id = $1 AND addon_key = $2 
                    AND status = 'active'
                """
                result = await conn.fetchrow(query, user_id, addon_key)
                
                if result and result['limits']:
                    return json.loads(result['limits']) if isinstance(result['limits'], str) else result['limits']
                
                # Default limits
                return {"ai_systems": 10}
        
        except Exception as e:
            logger.error(f"Error getting addon limits: {e}")
            return {"ai_systems": 10}
    
    async def count_user_ai_systems(self, user_id: str) -> int:
        """
        Count active AI systems for a user
        """
        if self.use_fallback:
            return 0
        
        try:
            async with self.get_connection() as conn:
                query = """
                    SELECT COUNT(*) FROM ai_systems 
                    WHERE user_id = $1 AND status = 'active'
                """
                count = await conn.fetchval(query, user_id)
                return count or 0
        
        except Exception as e:
            logger.error(f"Error counting user AI systems: {e}")
            return 0
    
    async def create_user_addon(
        self, 
        user_id: str, 
        addon_key: str,
        addon_name: str,
        price_monthly: float,
        limits: Dict[str, Any],
        stripe_subscription_id: Optional[str] = None
    ) -> str:
        """
        Create a new user add-on subscription
        """
        if self.use_fallback:
            return str(uuid.uuid4())
        
        try:
            async with self.get_connection() as conn:
                addon_id = str(uuid.uuid4())
                
                query = """
                    INSERT INTO user_addons (
                        id, user_id, addon_key, addon_name, 
                        price_monthly, limits, stripe_subscription_id,
                        status, started_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'active', NOW())
                    ON CONFLICT (user_id, addon_key) 
                    DO UPDATE SET 
                        status = 'active',
                        price_monthly = EXCLUDED.price_monthly,
                        limits = EXCLUDED.limits,
                        stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                        started_at = NOW()
                    RETURNING id
                """
                
                result = await conn.fetchrow(
                    query,
                    addon_id,
                    user_id,
                    addon_key,
                    addon_name,
                    price_monthly,
                    json.dumps(limits),
                    stripe_subscription_id
                )
                
                logger.info(f"Created add-on {addon_key} for user {user_id}")
                return str(result['id'])
        
        except Exception as e:
            logger.error(f"Error creating user addon: {e}")
            return ""
    
    async def cancel_user_addon(self, user_id: str, addon_key: str) -> bool:
        """
        Cancel a user's add-on subscription
        """
        if self.use_fallback:
            return True
        
        try:
            async with self.get_connection() as conn:
                query = """
                    UPDATE user_addons 
                    SET status = 'cancelled', cancelled_at = NOW()
                    WHERE user_id = $1 AND addon_key = $2
                """
                await conn.execute(query, user_id, addon_key)
                logger.info(f"Cancelled add-on {addon_key} for user {user_id}")
                return True
        
        except Exception as e:
            logger.error(f"Error cancelling user addon: {e}")
            return False
    
    async def get_user_addons(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all add-ons for a user
        """
        if self.use_fallback:
            return []
        
        try:
            async with self.get_connection() as conn:
                query = """
                    SELECT * FROM user_addons 
                    WHERE user_id = $1
                    ORDER BY started_at DESC
                """
                rows = await conn.fetch(query, user_id)
                
                return [
                    {
                        "id": str(row['id']),
                        "addon_key": row['addon_key'],
                        "addon_name": row['addon_name'],
                        "price_monthly": float(row['price_monthly']),
                        "status": row['status'],
                        "limits": json.loads(row['limits']) if row['limits'] else {},
                        "started_at": row['started_at'],
                        "expires_at": row['expires_at'],
                        "cancelled_at": row['cancelled_at']
                    }
                    for row in rows
                ]
        
        except Exception as e:
            logger.error(f"Error getting user addons: {e}")
            return []

# Global database service instance
db_service = DatabaseService()