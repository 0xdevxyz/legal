"""
AI Compliance Background Worker
Handles scheduled scans and notification processing
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AIComplianceWorker:
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every minute
    
    async def start(self):
        """Start the background worker"""
        logger.info("AI Compliance Worker starting...")
        self.running = True
        
        while self.running:
            try:
                await self.process_scheduled_scans()
                await self.process_scan_reminders()
            except Exception as e:
                logger.error(f"Worker error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the background worker"""
        logger.info("AI Compliance Worker stopping...")
        self.running = False
    
    async def process_scheduled_scans(self):
        """Process all due scheduled scans"""
        from database_service import db_service
        from ai_act_analyzer import ai_act_analyzer
        from ai_compliance_notification_service import ai_compliance_notification_service
        
        now = datetime.utcnow()
        
        query = """
            SELECT ss.*, s.name as system_name, s.description, s.vendor, s.purpose,
                   s.domain, s.risk_category as old_risk, s.compliance_score as old_score,
                   u.email, u.full_name
            FROM ai_scheduled_scans ss
            JOIN ai_systems s ON ss.ai_system_id = s.id
            JOIN users u ON ss.user_id = u.id
            WHERE ss.is_active = TRUE 
            AND ss.next_run_at <= $1
        """
        
        due_scans = await db_service.pool.fetch(query, now)
        
        for scan in due_scans:
            try:
                logger.info(f"Running scheduled scan for system: {scan['system_name']}")
                
                system_data = {
                    "id": str(scan['ai_system_id']),
                    "name": scan['system_name'],
                    "description": scan['description'] or "",
                    "vendor": scan['vendor'],
                    "purpose": scan['purpose'] or "",
                    "domain": scan['domain']
                }
                
                classification = await ai_act_analyzer.classify_system(system_data)
                compliance = await ai_act_analyzer.check_compliance(system_data, classification)
                
                new_score = compliance.get('compliance_score', 0)
                old_score = scan['old_score'] or 0
                
                update_query = """
                    UPDATE ai_systems 
                    SET risk_category = $1, risk_reasoning = $2, confidence_score = $3,
                        compliance_score = $4, last_assessment_date = NOW()
                    WHERE id = $5
                """
                await db_service.pool.execute(
                    update_query,
                    classification.get('risk_category'),
                    classification.get('reasoning'),
                    classification.get('confidence'),
                    new_score,
                    scan['ai_system_id']
                )
                
                scan_id = await self._save_scan_result(
                    scan['ai_system_id'],
                    scan['user_id'],
                    classification,
                    compliance
                )
                
                await self._update_next_run(scan['id'], scan['schedule_type'], scan['schedule_day'], scan['schedule_hour'])
                
                settings = await self._get_user_settings(scan['user_id'])
                
                if settings.get('email_on_scan_completed', False):
                    await self._create_notification(
                        scan['user_id'],
                        scan['ai_system_id'],
                        'scan_completed',
                        'info',
                        f"Scan abgeschlossen: {scan['system_name']}",
                        f"Compliance Score: {new_score}%"
                    )
                
                score_drop = old_score - new_score
                if score_drop >= settings.get('compliance_drop_threshold', 10):
                    await ai_compliance_notification_service.send_compliance_alert(
                        user_email=scan['email'],
                        user_name=scan['full_name'] or 'Nutzer',
                        system_name=scan['system_name'],
                        system_id=str(scan['ai_system_id']),
                        old_score=old_score,
                        new_score=new_score,
                        risk_category=classification.get('risk_category', 'unknown'),
                        findings=compliance.get('requirements_failed', [])
                    )
                    
                    await self._create_notification(
                        scan['user_id'],
                        scan['ai_system_id'],
                        'compliance_alert',
                        'critical' if score_drop >= 20 else 'warning',
                        f"Compliance-Score gesunken: {scan['system_name']}",
                        f"Score gefallen von {old_score}% auf {new_score}%"
                    )
                
                if classification.get('risk_category') in ['high', 'prohibited']:
                    if scan['old_risk'] not in ['high', 'prohibited']:
                        await ai_compliance_notification_service.send_high_risk_alert(
                            user_email=scan['email'],
                            user_name=scan['full_name'] or 'Nutzer',
                            system_name=scan['system_name'],
                            system_id=str(scan['ai_system_id']),
                            risk_category=classification.get('risk_category'),
                            risk_reasoning=classification.get('reasoning', '')
                        )
                
                logger.info(f"Scheduled scan completed for {scan['system_name']}: Score {new_score}%")
                
            except Exception as e:
                logger.error(f"Error processing scheduled scan for {scan.get('system_name')}: {e}")
    
    async def process_scan_reminders(self):
        """Send reminders for systems not scanned recently"""
        from database_service import db_service
        from ai_compliance_notification_service import ai_compliance_notification_service
        
        query = """
            SELECT u.id as user_id, u.email, u.full_name,
                   array_agg(json_build_object(
                       'id', s.id::text,
                       'name', s.name,
                       'last_assessment_date', s.last_assessment_date
                   )) as systems
            FROM users u
            JOIN ai_compliance_alert_settings als ON u.id = als.user_id
            JOIN ai_systems s ON u.id = s.user_id
            WHERE als.email_on_scan_reminder = TRUE
            AND s.status = 'active'
            AND (s.last_assessment_date IS NULL 
                 OR s.last_assessment_date < NOW() - (als.scan_reminder_days || ' days')::interval)
            AND NOT EXISTS (
                SELECT 1 FROM ai_compliance_notifications n
                WHERE n.user_id = u.id 
                AND n.notification_type = 'scan_reminder'
                AND n.created_at > NOW() - INTERVAL '7 days'
            )
            GROUP BY u.id, u.email, u.full_name
        """
        
        try:
            users_needing_reminder = await db_service.pool.fetch(query)
            
            for user in users_needing_reminder:
                systems = user['systems'] if user['systems'] else []
                
                if systems:
                    await ai_compliance_notification_service.send_scan_reminder(
                        user_email=user['email'],
                        user_name=user['full_name'] or 'Nutzer',
                        systems=systems
                    )
                    
                    await self._create_notification(
                        user['user_id'],
                        None,
                        'scan_reminder',
                        'info',
                        f"Scan-Erinnerung: {len(systems)} System(e)",
                        "Ihre KI-Systeme wurden länger nicht gescannt"
                    )
                    
                    logger.info(f"Sent scan reminder to {user['email']} for {len(systems)} systems")
        
        except Exception as e:
            logger.error(f"Error processing scan reminders: {e}")
    
    async def _save_scan_result(self, system_id, user_id, classification, compliance):
        """Save scan result to database"""
        from database_service import db_service
        import uuid
        import json
        
        scan_id = uuid.uuid4()
        
        query = """
            INSERT INTO ai_compliance_scans (
                id, ai_system_id, user_id, compliance_score, overall_risk_score,
                risk_assessment, findings, recommendations, requirements_met,
                requirements_failed, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'completed')
            RETURNING id
        """
        
        await db_service.pool.execute(
            query,
            scan_id,
            system_id,
            user_id,
            compliance.get('compliance_score', 0),
            classification.get('confidence', 0.5),
            json.dumps(classification),
            json.dumps(compliance.get('findings', [])),
            compliance.get('recommendations', ''),
            json.dumps(compliance.get('requirements_met', [])),
            json.dumps(compliance.get('requirements_failed', []))
        )
        
        return scan_id
    
    async def _update_next_run(self, schedule_id, schedule_type, schedule_day, schedule_hour):
        """Calculate and update next run time"""
        from database_service import db_service
        
        now = datetime.utcnow()
        
        if schedule_type == 'daily':
            next_run = now + timedelta(days=1)
        elif schedule_type == 'weekly':
            next_run = now + timedelta(days=7)
        elif schedule_type == 'monthly':
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1)
            else:
                next_run = now.replace(month=now.month + 1)
        else:
            next_run = now + timedelta(days=1)
        
        next_run = next_run.replace(hour=schedule_hour, minute=0, second=0, microsecond=0)
        
        query = """
            UPDATE ai_scheduled_scans 
            SET last_run_at = NOW(), next_run_at = $1, updated_at = NOW()
            WHERE id = $2
        """
        await db_service.pool.execute(query, next_run, schedule_id)
    
    async def _get_user_settings(self, user_id):
        """Get user's alert settings"""
        from database_service import db_service
        
        query = "SELECT * FROM ai_compliance_alert_settings WHERE user_id = $1"
        settings = await db_service.pool.fetchrow(query, user_id)
        
        if not settings:
            return {
                'email_on_compliance_drop': True,
                'email_on_high_risk': True,
                'email_on_scan_reminder': True,
                'email_on_scan_completed': False,
                'compliance_drop_threshold': 10,
                'scan_reminder_days': 30
            }
        
        return dict(settings)
    
    async def _create_notification(self, user_id, system_id, notif_type, severity, title, message):
        """Create in-app notification"""
        from database_service import db_service
        import uuid
        
        query = """
            INSERT INTO ai_compliance_notifications (
                id, user_id, ai_system_id, notification_type, severity, title, message
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await db_service.pool.execute(
            query,
            uuid.uuid4(),
            user_id,
            system_id,
            notif_type,
            severity,
            title,
            message
        )


ai_compliance_worker = AIComplianceWorker()


async def start_worker():
    """Start the AI compliance worker"""
    await ai_compliance_worker.start()


def run_worker():
    """Run the worker (for standalone execution)"""
    asyncio.run(start_worker())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_worker()
