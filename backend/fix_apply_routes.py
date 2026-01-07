"""
Fix Apply Routes für Complyo
Endpoints für das Anwenden von Fixes via FTP, SFTP, GitHub PR, etc.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import asyncpg
from datetime import datetime

from .compliance_engine.deployment_engine import DeploymentEngine, DeploymentConfig, DeploymentResult
from .audit_service import FixAuditService

logger = logging.getLogger(__name__)

apply_router = APIRouter(prefix="/api/v2/fixes", tags=["fix-apply"])
security = HTTPBearer()

# Global references (set in main_production.py)
db_pool: Optional[asyncpg.Pool] = None
auth_service = None
audit_service: Optional[FixAuditService] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class ApplyFixRequest(BaseModel):
    """Request für Fix-Anwendung"""
    fix_id: str = Field(..., description="ID des anzuwendenden Fixes")
    deployment_method: str = Field(..., description="Methode: ftp, sftp, github_pr, netlify, vercel")
    
    # Credentials (verschlüsselt im Frontend übertragen)
    credentials: Dict[str, str] = Field(..., description="Deployment-Credentials")
    
    # Target
    target_path: str = Field(..., description="Ziel-Pfad auf dem Server")
    site_url: Optional[str] = Field(None, description="URL der Website")
    
    # Options
    backup_before_deploy: bool = Field(True, description="Backup vor Deployment erstellen?")
    user_confirmed: bool = Field(True, description="Hat User explizit bestätigt?")
    
    # Metadaten
    fix_category: Optional[str] = None
    fix_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ApplyFixResponse(BaseModel):
    """Response für Fix-Anwendung"""
    success: bool
    audit_id: str
    deployment_id: str
    deployment_method: str
    files_deployed: List[str]
    backup_created: bool
    backup_id: Optional[str]
    deployed_at: str
    rollback_available: bool
    error: Optional[str] = None
    message: str


class RollbackRequest(BaseModel):
    """Request für Rollback"""
    backup_id: str = Field(..., description="ID des Backups")
    deployment_method: str = Field(..., description="Original Deployment-Methode")
    credentials: Dict[str, str] = Field(..., description="Deployment-Credentials")
    target_path: str = Field(..., description="Ziel-Pfad auf dem Server")


class PreviewRequest(BaseModel):
    """Request für Staging-Preview (Premium)"""
    fix_id: str
    staging_subdomain: Optional[str] = None
    create_screenshots: bool = True


class ApplyStatusResponse(BaseModel):
    """Status eines Apply-Vorgangs"""
    apply_id: str
    status: str  # 'pending', 'deploying', 'deployed', 'failed'
    progress: int  # 0-100
    current_step: str
    error: Optional[str] = None


# ============================================================================
# Auth Helper
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")


# ============================================================================
# Apply Endpoints
# ============================================================================

@apply_router.post("/apply", response_model=ApplyFixResponse)
async def apply_fix(
    request: Request,
    apply_request: ApplyFixRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Wendet einen Fix an (FTP, SFTP, GitHub PR, etc.)
    
    **WICHTIG:** Erstellt vorher ein Backup (falls aktiviert) für Rollback!
    
    **Unterstützte Methoden:**
    - `ftp`: FTP Upload
    - `sftp`: SFTP/SSH Upload  
    - `github_pr`: GitHub Pull Request
    - `netlify`: Netlify Deployment
    - `vercel`: Vercel Deployment
    
    **Ablauf:**
    1. User-Bestätigung prüfen
    2. Backup erstellen (optional)
    3. Fix deployen
    4. Audit-Log schreiben
    5. User benachrichtigen
    """
    try:
        user_id = current_user.get('user_id')
        user_plan = current_user.get('plan', 'ai')
        
        logger.info(f"🚀 Apply fix request: {apply_request.fix_id} via {apply_request.deployment_method}")
        
        # 1. Validierung
        if not apply_request.user_confirmed:
            raise HTTPException(
                status_code=400,
                detail="User-Bestätigung erforderlich. Bitte bestätigen Sie explizit die Anwendung des Fixes."
            )
        
        # 2. Premium-Check für bestimmte Methoden
        if apply_request.deployment_method in ['sftp', 'ssh'] and user_plan not in ['managed', 'premium']:
            raise HTTPException(
                status_code=403,
                detail="SFTP/SSH-Deployment ist nur im Managed-Plan (3.000€/Mo) verfügbar. "
                       "Nutzen Sie stattdessen FTP oder GitHub PR."
            )
        
        # 3. Fix-Code aus Datenbank laden
        fix_code = await _get_fix_code(apply_request.fix_id, user_id)
        if not fix_code:
            raise HTTPException(
                status_code=404,
                detail=f"Fix {apply_request.fix_id} nicht gefunden oder nicht für diesen User verfügbar."
            )
        
        # 4. Deployment Config erstellen
        deployment_config = DeploymentConfig(
            method=apply_request.deployment_method,
            credentials=apply_request.credentials,
            target_path=apply_request.target_path,
            backup_before_deploy=apply_request.backup_before_deploy,
            files=[{
                'local_path': fix_code['file_path'],
                'remote_path': apply_request.target_path,
                'content': fix_code['code']
            }]
        )
        
        # 5. Deployment Engine ausführen
        deployment_engine = DeploymentEngine()
        deployment_result: DeploymentResult = await deployment_engine.deploy(deployment_config)
        
        # 6. Audit-Log schreiben
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')
        
        audit_id = await audit_service.log_fix_application(
            user_id=user_id,
            fix_id=apply_request.fix_id,
            fix_category=apply_request.fix_category or fix_code.get('category', 'unknown'),
            fix_type=apply_request.fix_type or fix_code.get('type', 'code'),
            deployment_method=apply_request.deployment_method,
            deployment_result={
                'deployment_id': deployment_result.deployment_id,
                'files_deployed': deployment_result.files_deployed,
                'deployed_at': deployment_result.deployed_at,
                'error': deployment_result.error
            },
            success=deployment_result.success,
            backup_id=deployment_result.backup_id,
            backup_location=None,  # TODO: Aus deployment_result extrahieren
            ip_address=ip_address,
            user_agent=user_agent,
            user_confirmed=apply_request.user_confirmed,
            metadata=apply_request.metadata
        )
        
        # 7. Erfolgs-Response
        message = "Fix erfolgreich angewendet!" if deployment_result.success else "Fix-Anwendung fehlgeschlagen."
        if deployment_result.backup_created:
            message += f" Backup erstellt: {deployment_result.backup_id}"
        
        return ApplyFixResponse(
            success=deployment_result.success,
            audit_id=audit_id,
            deployment_id=deployment_result.deployment_id,
            deployment_method=deployment_result.method,
            files_deployed=deployment_result.files_deployed,
            backup_created=deployment_result.backup_created,
            backup_id=deployment_result.backup_id,
            deployed_at=deployment_result.deployed_at,
            rollback_available=deployment_result.rollback_available,
            error=deployment_result.error,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Apply fix failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Anwenden des Fixes: {str(e)}"
        )


@apply_router.post("/rollback")
async def rollback_fix(
    request: Request,
    rollback_request: RollbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Macht einen angewendeten Fix rückgängig (Rollback)
    
    **Voraussetzung:** Backup muss vorhanden sein!
    
    **Ablauf:**
    1. Backup aus DB/Storage laden
    2. Backup auf Server deployen
    3. Audit-Log schreiben
    """
    try:
        user_id = current_user.get('user_id')
        
        logger.info(f"🔄 Rollback request: backup_id={rollback_request.backup_id}")
        
        # 1. Backup laden
        backup_info = await _get_backup_info(rollback_request.backup_id, user_id)
        if not backup_info:
            raise HTTPException(
                status_code=404,
                detail=f"Backup {rollback_request.backup_id} nicht gefunden."
            )
        
        # 2. Deployment Engine für Rollback
        deployment_engine = DeploymentEngine()
        
        rollback_result = await deployment_engine.rollback(
            backup_id=rollback_request.backup_id,
            config=DeploymentConfig(
                method=rollback_request.deployment_method,
                credentials=rollback_request.credentials,
                target_path=rollback_request.target_path,
                backup_before_deploy=False,
                files=[]
            )
        )
        
        # 3. Audit-Log schreiben
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')
        
        audit_id = await audit_service.log_rollback(
            user_id=user_id,
            fix_id=backup_info['fix_id'],
            backup_id=rollback_request.backup_id,
            deployment_method=rollback_request.deployment_method,
            success=rollback_result['success'],
            rollback_result=rollback_result,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            'success': rollback_result['success'],
            'audit_id': audit_id,
            'backup_id': rollback_request.backup_id,
            'message': 'Rollback erfolgreich durchgeführt!' if rollback_result['success'] else 'Rollback fehlgeschlagen.',
            'error': rollback_result.get('error')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Rollback: {str(e)}"
        )


@apply_router.post("/apply/preview")
async def preview_fix_on_staging(
    preview_request: PreviewRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Erstellt Staging-Preview mit Screenshot-Diff (Premium-Feature)
    
    **Nur für Managed-Plan (3.000€/Mo)!**
    
    **Ablauf:**
    1. Erstelle temporäre Subdomain (preview-{id}.complyo.tech)
    2. Deploye Fix auf Staging
    3. Erstelle Screenshots (Before/After)
    4. Generiere Diff-Image
    5. Warte auf User-Approval
    """
    try:
        user_id = current_user.get('user_id')
        user_plan = current_user.get('plan', 'ai')
        
        # Premium-Check
        if user_plan not in ['managed', 'premium']:
            raise HTTPException(
                status_code=403,
                detail="Staging-Preview ist nur im Managed-Plan (3.000€/Mo) verfügbar. "
                       "Im Standard-Plan nutzen Sie bitte den Diff-Viewer im Dashboard."
            )
        
        # TODO: Implementierung des Staging-Preview-Features
        # Siehe Phase 5 im Plan
        
        return {
            'success': True,
            'staging_url': f"https://preview-{preview_request.fix_id[:8]}.complyo.tech",
            'screenshot_before': None,
            'screenshot_after': None,
            'screenshot_diff': None,
            'status': 'deploying',
            'message': 'Staging-Environment wird erstellt...'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Staging preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@apply_router.get("/apply/status/{apply_id}")
async def get_apply_status(
    apply_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Holt den Status eines laufenden Apply-Vorgangs
    
    Für asynchrone Deployments (z.B. Netlify, Vercel)
    """
    try:
        user_id = current_user.get('user_id')
        
        # TODO: Implementierung von Background-Task-Tracking
        # Für jetzt: Audit-Log-Status zurückgeben
        
        audit_entry = await _get_audit_entry(apply_id, user_id)
        if not audit_entry:
            raise HTTPException(status_code=404, detail="Apply-Vorgang nicht gefunden")
        
        return ApplyStatusResponse(
            apply_id=apply_id,
            status='deployed' if audit_entry['success'] else 'failed',
            progress=100,
            current_step='completed',
            error=audit_entry.get('error_message')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get apply status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================

async def _get_fix_code(fix_id: str, user_id: int) -> Optional[Dict]:
    """
    Lädt Fix-Code aus Datenbank
    
    Returns:
        Dict mit fix_data oder None
    """
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    f.id, f.issue_id, f.issue_category, f.fix_type,
                    f.fix_data, f.generated_at
                FROM generated_fixes f
                WHERE f.id = $1 AND f.user_id = $2
                """,
                int(fix_id), user_id
            )
            
            if not row:
                return None
            
            fix_data = row['fix_data']
            
            return {
                'fix_id': str(row['id']),
                'category': row['issue_category'],
                'type': row['fix_type'],
                'code': fix_data.get('code', ''),
                'file_path': fix_data.get('file_path', 'index.html'),
                'generated_at': row['generated_at']
            }
            
    except Exception as e:
        logger.error(f"Failed to get fix code: {e}")
        return None


async def _get_backup_info(backup_id: str, user_id: int) -> Optional[Dict]:
    """
    Lädt Backup-Informationen aus Datenbank
    
    Returns:
        Dict mit backup_info oder None
    """
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    fb.backup_id, fb.backup_location, fb.backup_type,
                    fb.backed_up_files, fb.deployment_method,
                    faa.fix_id
                FROM fix_backups fb
                JOIN fix_application_audit faa ON fb.audit_id = faa.id
                WHERE fb.backup_id = $1 AND fb.user_id = $2
                AND fb.is_restored = false
                """,
                backup_id, user_id
            )
            
            if not row:
                return None
            
            return {
                'backup_id': row['backup_id'],
                'backup_location': row['backup_location'],
                'backup_type': row['backup_type'],
                'backed_up_files': row['backed_up_files'],
                'deployment_method': row['deployment_method'],
                'fix_id': row['fix_id']
            }
            
    except Exception as e:
        logger.error(f"Failed to get backup info: {e}")
        return None


async def _get_audit_entry(audit_id: str, user_id: int) -> Optional[Dict]:
    """
    Lädt Audit-Eintrag aus Datenbank
    
    Returns:
        Dict mit audit_entry oder None
    """
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, fix_id, action_type, deployment_method,
                    success, error_message, applied_at
                FROM fix_application_audit
                WHERE id = $1 AND user_id = $2
                """,
                audit_id, user_id
            )
            
            if not row:
                return None
            
            return dict(row)
            
    except Exception as e:
        logger.error(f"Failed to get audit entry: {e}")
        return None


# ============================================================================
# Initialization
# ============================================================================

def init_apply_routes(
    _db_pool: asyncpg.Pool,
    _auth_service,
    _audit_service: FixAuditService
):
    """Initialisiert die Apply-Routes mit Services"""
    global db_pool, auth_service, audit_service
    db_pool = _db_pool
    auth_service = _auth_service
    audit_service = _audit_service
    logger.info("✅ Fix Apply Routes initialized")

