"""
Complyo Audit Service
Rechtssicheres Logging aller Fix-Anwendungen für Haftungssicherheit
"""

import asyncpg
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AuditLogEntry:
    """Einzelner Audit-Log-Eintrag"""
    id: str
    user_id: int
    fix_id: str
    fix_category: Optional[str]
    fix_type: Optional[str]
    action_type: str
    deployment_method: Optional[str]
    applied_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    deployment_result: Optional[Dict]
    success: bool
    error_message: Optional[str]
    backup_id: Optional[str]
    backup_location: Optional[str]
    rollback_available: bool
    user_confirmed: bool
    confirmation_timestamp: Optional[datetime]
    metadata: Dict


class FixAuditService:
    """
    Service für rechtssicheres Audit-Logging
    
    Funktionen:
    - Log jede Fix-Anwendung
    - Log jeden Download
    - Log jeden Preview-Aufruf
    - Log jeden Rollback
    - Abruf des Audit-Logs für Dashboard
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        logger.info("✅ FixAuditService initialized")
    
    async def log_fix_generation(
        self,
        user_id: int,
        fix_id: str,
        fix_category: str,
        fix_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Loggt die Generierung eines Fixes
        
        Returns:
            audit_id (UUID als String)
        """
        try:
            audit_id = str(uuid.uuid4())
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO fix_application_audit (
                        id, user_id, fix_id, fix_category, fix_type,
                        action_type, applied_at, ip_address, user_agent,
                        success, user_confirmed, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    audit_id, user_id, fix_id, fix_category, fix_type,
                    'generated', datetime.now(), ip_address, user_agent,
                    True, False, json.dumps(metadata or {})
                )
            
            logger.info(f"✅ Fix generation logged: {fix_id} by user {user_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log fix generation: {e}")
            raise
    
    async def log_fix_download(
        self,
        user_id: int,
        fix_id: str,
        fix_category: str,
        fix_type: str,
        export_format: str = 'zip',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Loggt einen Fix-Download (ZIP, HTML, etc.)
        
        Returns:
            audit_id (UUID als String)
        """
        try:
            audit_id = str(uuid.uuid4())
            
            download_metadata = {
                'export_format': export_format,
                **(metadata or {})
            }
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO fix_application_audit (
                        id, user_id, fix_id, fix_category, fix_type,
                        action_type, deployment_method, applied_at,
                        ip_address, user_agent, success, user_confirmed, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """,
                    audit_id, user_id, fix_id, fix_category, fix_type,
                    'downloaded', 'zip_download', datetime.now(),
                    ip_address, user_agent, True, True, json.dumps(download_metadata)
                )
            
            logger.info(f"✅ Fix download logged: {fix_id} by user {user_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log fix download: {e}")
            raise
    
    async def log_fix_application(
        self,
        user_id: int,
        fix_id: str,
        fix_category: str,
        fix_type: str,
        deployment_method: str,
        deployment_result: Dict,
        success: bool,
        backup_id: Optional[str] = None,
        backup_location: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_confirmed: bool = True,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Loggt die Anwendung eines Fixes (FTP, SFTP, PR, etc.)
        
        Args:
            user_id: Benutzer-ID
            fix_id: Fix-Identifier
            fix_category: Kategorie (accessibility, cookies, etc.)
            fix_type: Typ (code, text, guide)
            deployment_method: Methode (ftp, sftp, github_pr, etc.)
            deployment_result: Ergebnis des Deployments (dict)
            success: War das Deployment erfolgreich?
            backup_id: ID des erstellten Backups (optional)
            backup_location: Pfad zum Backup (optional)
            ip_address: IP-Adresse des Users
            user_agent: User-Agent String
            user_confirmed: Hat User explizit bestätigt?
            metadata: Zusätzliche Metadaten
            
        Returns:
            audit_id (UUID als String)
        """
        try:
            audit_id = str(uuid.uuid4())
            confirmation_timestamp = datetime.now() if user_confirmed else None
            error_message = deployment_result.get('error') if not success else None
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO fix_application_audit (
                        id, user_id, fix_id, fix_category, fix_type,
                        action_type, deployment_method, applied_at,
                        ip_address, user_agent, deployment_result,
                        success, error_message, backup_id, rollback_available,
                        user_confirmed, confirmation_timestamp, metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                    )
                    """,
                    audit_id, user_id, fix_id, fix_category, fix_type,
                    'applied', deployment_method, datetime.now(),
                    ip_address, user_agent, json.dumps(deployment_result),
                    success, error_message, backup_id, backup_id is not None,
                    user_confirmed, confirmation_timestamp, json.dumps(metadata or {})
                )
            
            # Wenn Backup erstellt wurde, logge es separat
            if backup_id and backup_location:
                await self._log_backup(
                    backup_id=backup_id,
                    user_id=user_id,
                    audit_id=audit_id,
                    backup_location=backup_location,
                    deployment_method=deployment_method,
                    metadata=metadata
                )
            
            logger.info(f"✅ Fix application logged: {fix_id} via {deployment_method} (success={success})")
            return audit_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log fix application: {e}")
            raise
    
    async def log_fix_preview(
        self,
        user_id: int,
        fix_id: str,
        fix_category: str,
        preview_type: str = 'diff',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Loggt Preview-Aufruf (Diff-Viewer, Screenshot-Diff, etc.)
        
        Returns:
            audit_id (UUID als String)
        """
        try:
            audit_id = str(uuid.uuid4())
            
            preview_metadata = {
                'preview_type': preview_type,
                **(metadata or {})
            }
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO fix_application_audit (
                        id, user_id, fix_id, fix_category,
                        action_type, applied_at, ip_address, user_agent,
                        success, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    audit_id, user_id, fix_id, fix_category,
                    'previewed', datetime.now(), ip_address, user_agent,
                    True, json.dumps(preview_metadata)
                )
            
            logger.info(f"✅ Fix preview logged: {fix_id} by user {user_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log fix preview: {e}")
            # Preview-Logging sollte nicht kritisch sein
            return ""
    
    async def log_rollback(
        self,
        user_id: int,
        fix_id: str,
        backup_id: str,
        deployment_method: str,
        success: bool,
        rollback_result: Dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Loggt einen Rollback (Rückgängigmachen eines Fixes)
        
        Returns:
            audit_id (UUID als String)
        """
        try:
            audit_id = str(uuid.uuid4())
            error_message = rollback_result.get('error') if not success else None
            
            rollback_metadata = {
                'original_backup_id': backup_id,
                'rollback_result': rollback_result,
                **(metadata or {})
            }
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO fix_application_audit (
                        id, user_id, fix_id,
                        action_type, deployment_method, applied_at,
                        ip_address, user_agent, deployment_result,
                        success, error_message, backup_id,
                        user_confirmed, confirmation_timestamp, metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    )
                    """,
                    audit_id, user_id, fix_id,
                    'rolled_back', deployment_method, datetime.now(),
                    ip_address, user_agent, json.dumps(rollback_result),
                    success, error_message, backup_id,
                    True, datetime.now(), json.dumps(rollback_metadata)
                )
            
            # Update Backup-Status
            await self._mark_backup_restored(backup_id)
            
            logger.info(f"✅ Rollback logged: {fix_id} using backup {backup_id} (success={success})")
            return audit_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log rollback: {e}")
            raise
    
    async def get_user_audit_log(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        action_type: Optional[str] = None
    ) -> List[AuditLogEntry]:
        """
        Holt den Audit-Log für einen User
        
        Args:
            user_id: Benutzer-ID
            limit: Max. Anzahl Einträge
            offset: Offset für Pagination
            action_type: Filter nach Action-Type (optional)
            
        Returns:
            Liste von AuditLogEntry
        """
        try:
            async with self.db_pool.acquire() as conn:
                if action_type:
                    rows = await conn.fetch(
                        """
                        SELECT 
                            faa.id, faa.user_id, faa.fix_id, faa.fix_category, faa.fix_type,
                            faa.action_type, faa.deployment_method, faa.applied_at,
                            faa.ip_address, faa.user_agent, faa.deployment_result,
                            faa.success, faa.error_message, faa.backup_id,
                            faa.rollback_available, faa.user_confirmed,
                            faa.confirmation_timestamp, faa.metadata,
                            fb.backup_location
                        FROM fix_application_audit faa
                        LEFT JOIN fix_backups fb ON faa.backup_id = fb.backup_id
                        WHERE faa.user_id = $1 AND faa.action_type = $2
                        ORDER BY faa.applied_at DESC
                        LIMIT $3 OFFSET $4
                        """,
                        user_id, action_type, limit, offset
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT 
                            faa.id, faa.user_id, faa.fix_id, faa.fix_category, faa.fix_type,
                            faa.action_type, faa.deployment_method, faa.applied_at,
                            faa.ip_address, faa.user_agent, faa.deployment_result,
                            faa.success, faa.error_message, faa.backup_id,
                            faa.rollback_available, faa.user_confirmed,
                            faa.confirmation_timestamp, faa.metadata,
                            fb.backup_location
                        FROM fix_application_audit faa
                        LEFT JOIN fix_backups fb ON faa.backup_id = fb.backup_id
                        WHERE faa.user_id = $1
                        ORDER BY faa.applied_at DESC
                        LIMIT $2 OFFSET $3
                        """,
                        user_id, limit, offset
                    )
                
                entries = []
                for row in rows:
                    entry = AuditLogEntry(
                        id=str(row['id']),
                        user_id=row['user_id'],
                        fix_id=row['fix_id'],
                        fix_category=row['fix_category'],
                        fix_type=row['fix_type'],
                        action_type=row['action_type'],
                        deployment_method=row['deployment_method'],
                        applied_at=row['applied_at'],
                        ip_address=row['ip_address'],
                        user_agent=row['user_agent'],
                        deployment_result=json.loads(row['deployment_result']) if row['deployment_result'] else None,
                        success=row['success'],
                        error_message=row['error_message'],
                        backup_id=row['backup_id'],
                        backup_location=row['backup_location'],
                        rollback_available=row['rollback_available'],
                        user_confirmed=row['user_confirmed'],
                        confirmation_timestamp=row['confirmation_timestamp'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            logger.error(f"❌ Failed to get audit log: {e}")
            return []
    
    async def get_audit_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Holt Statistiken für einen User
        
        Returns:
            Dict mit Statistiken
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_actions,
                        COUNT(CASE WHEN action_type = 'generated' THEN 1 END) as fixes_generated,
                        COUNT(CASE WHEN action_type = 'downloaded' THEN 1 END) as fixes_downloaded,
                        COUNT(CASE WHEN action_type = 'applied' THEN 1 END) as fixes_applied,
                        COUNT(CASE WHEN action_type = 'rolled_back' THEN 1 END) as rollbacks,
                        COUNT(CASE WHEN success = true THEN 1 END) as successful_actions,
                        COUNT(CASE WHEN success = false THEN 1 END) as failed_actions,
                        MAX(applied_at) as last_action_at
                    FROM fix_application_audit
                    WHERE user_id = $1
                    """,
                    user_id
                )
                
                # Backup-Statistiken
                backup_row = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_backups,
                        SUM(backup_size_bytes) as total_backup_size,
                        COUNT(CASE WHEN is_restored = true THEN 1 END) as restored_backups
                    FROM fix_backups
                    WHERE user_id = $1
                    """,
                    user_id
                )
                
                return {
                    'total_actions': row['total_actions'],
                    'fixes_generated': row['fixes_generated'],
                    'fixes_downloaded': row['fixes_downloaded'],
                    'fixes_applied': row['fixes_applied'],
                    'rollbacks': row['rollbacks'],
                    'successful_actions': row['successful_actions'],
                    'failed_actions': row['failed_actions'],
                    'success_rate': round(row['successful_actions'] / max(row['total_actions'], 1) * 100, 1),
                    'last_action_at': row['last_action_at'].isoformat() if row['last_action_at'] else None,
                    'total_backups': backup_row['total_backups'],
                    'total_backup_size_mb': round((backup_row['total_backup_size'] or 0) / 1024 / 1024, 2),
                    'restored_backups': backup_row['restored_backups']
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get audit statistics: {e}")
            return {}
    
    async def _log_backup(
        self,
        backup_id: str,
        user_id: int,
        audit_id: str,
        backup_location: str,
        deployment_method: str,
        metadata: Optional[Dict] = None
    ):
        """Interne Methode zum Loggen eines Backups"""
        try:
            expires_at = datetime.now() + timedelta(days=30)
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO fix_backups (
                        backup_id, user_id, audit_id, backup_location,
                        deployment_method, created_at, expires_at, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    backup_id, user_id, audit_id, backup_location,
                    deployment_method, datetime.now(), expires_at,
                    json.dumps(metadata or {})
                )
            
            logger.info(f"✅ Backup logged: {backup_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log backup: {e}")
            # Nicht kritisch, kein raise
    
    async def _mark_backup_restored(self, backup_id: str):
        """Markiert ein Backup als wiederhergestellt"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE fix_backups
                    SET is_restored = true, restored_at = $1
                    WHERE backup_id = $2
                    """,
                    datetime.now(), backup_id
                )
            
            logger.info(f"✅ Backup marked as restored: {backup_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to mark backup as restored: {e}")
    
    async def cleanup_expired_backups(self) -> int:
        """
        Löscht abgelaufene Backups (>30 Tage)
        
        Returns:
            Anzahl gelöschter Backups
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM fix_backups
                    WHERE expires_at < $1 AND is_restored = false
                    """,
                    datetime.now()
                )
                
                # Parse "DELETE N" result
                deleted_count = int(result.split()[-1])
                
                logger.info(f"✅ Cleaned up {deleted_count} expired backups")
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired backups: {e}")
            return 0


# Convenience functions

async def create_audit_service(db_pool: asyncpg.Pool) -> FixAuditService:
    """Factory function für FixAuditService"""
    return FixAuditService(db_pool)

