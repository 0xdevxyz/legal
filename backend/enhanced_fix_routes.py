"""
Enhanced Fix API Routes - Erweiterung (nicht Ersatz!) der bestehenden fix_routes.py

WICHTIG:
- Diese Routes sind OPTIONAL
- Bestehende fix_routes.py bleiben unverändert
- Neue Features können schrittweise aktiviert werden
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Router mit anderem Prefix (kein Konflikt mit bestehenden Routes!)
enhanced_router = APIRouter(prefix="/api/v2/enhanced-fixes", tags=["enhanced-fixes"])
security = HTTPBearer()

# Global references (set in main_production.py)
enhanced_fixer = None
db_pool = None
auth_service = None


class EnhancedFixRequest(BaseModel):
    """Request mit erweiterten Optionen"""
    issue_id: str
    issue_category: str
    company_info: Optional[Dict[str, str]] = None
    enable_preview: bool = True
    erecht24_project_id: Optional[str] = None


class PreviewRequest(BaseModel):
    """Request für Preview-Generierung"""
    fix_id: str
    original_content: str
    fix_content: str
    fix_type: str


class DeploymentRequest(BaseModel):
    """Request für Deployment"""
    fix_id: str
    method: str  # 'ftp', 'sftp', 'wordpress', 'netlify', 'vercel'
    credentials: Dict[str, str]
    target_path: str
    files: List[Dict[str, str]]
    backup_before_deploy: bool = True


class GitHubPRRequest(BaseModel):
    """Request für GitHub PR"""
    fix_id: str
    repository: str  # "owner/repo"
    github_token: str
    target_branch: str = "main"


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


@enhanced_router.get("/status")
async def get_enhanced_fixer_status():
    """
    Gibt Status der Enhanced Fixer Integration zurück
    
    Zeigt welche Features aktiviert sind
    """
    if not enhanced_fixer:
        return {
            "enhanced_fixer_active": False,
            "message": "Enhanced Fixer nicht initialisiert"
        }
    
    return enhanced_fixer.get_status()


@enhanced_router.post("/generate-with-priority")
async def generate_fix_with_priority(
    request: EnhancedFixRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generiert Fix mit korrekter Priorität
    
    WICHTIG: Hierarchie für Rechtstexte:
    1. eRecht24 API (wenn verfügbar) - ABMAHNSCHUTZ!
    2. Bestehende Templates (Fallback)
    3. KI-Generated (Notfall-Fallback)
    
    Returns:
        Fix mit Prioritäts-Information
    """
    if not enhanced_fixer:
        raise HTTPException(
            status_code=503,
            detail="Enhanced Fixer nicht verfügbar"
        )
    
    try:
        user_context = {
            'user_id': current_user['user_id'],
            'erecht24_project_id': request.erecht24_project_id
        }
        
        fix_result = await enhanced_fixer.generate_fix_with_priority(
            issue_category=request.issue_category,
            issue_data={'issue_id': request.issue_id},
            company_info=request.company_info,
            user_context=user_context
        )
        
        # Optional: Preview generieren
        preview_data = None
        if request.enable_preview and enhanced_fixer.enable_preview:
            try:
                preview_data = await enhanced_fixer.create_preview(
                    original_content="",  # TODO: Original von DB holen
                    fix_content=fix_result['content'],
                    fix_type=request.issue_category,
                    fix_id=request.issue_id
                )
            except Exception as e:
                logger.warning(f"⚠️ Preview konnte nicht erstellt werden: {e}")
        
        return {
            'success': True,
            'fix': fix_result,
            'preview': preview_data,
            'user_id': current_user['user_id']
        }
        
    except Exception as e:
        logger.error(f"❌ Enhanced Fix-Generierung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fix-Generierung fehlgeschlagen: {str(e)}"
        )


@enhanced_router.post("/preview")
async def create_preview(
    request: PreviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Erstellt Preview für Fix
    
    Zeigt Side-by-Side Vergleich und Diff
    """
    if not enhanced_fixer or not enhanced_fixer.enable_preview:
        raise HTTPException(
            status_code=503,
            detail="Preview-Feature nicht aktiviert"
        )
    
    try:
        preview_data = await enhanced_fixer.create_preview(
            original_content=request.original_content,
            fix_content=request.fix_content,
            fix_type=request.fix_type,
            fix_id=request.fix_id
        )
        
        if not preview_data:
            raise HTTPException(
                status_code=500,
                detail="Preview konnte nicht erstellt werden"
            )
        
        return {
            'success': True,
            'preview': preview_data
        }
        
    except Exception as e:
        logger.error(f"❌ Preview-Erstellung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview fehlgeschlagen: {str(e)}"
        )


@enhanced_router.get("/preview/{preview_id}")
async def get_preview(
    preview_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Holt Preview-HTML
    """
    if not enhanced_fixer or not enhanced_fixer.preview_engine:
        raise HTTPException(
            status_code=503,
            detail="Preview-Engine nicht verfügbar"
        )
    
    try:
        preview_html = await enhanced_fixer.preview_engine.get_preview(preview_id)
        
        if not preview_html:
            raise HTTPException(
                status_code=404,
                detail="Preview nicht gefunden"
            )
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=preview_html)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Preview abrufen fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview abrufen fehlgeschlagen: {str(e)}"
        )


@enhanced_router.post("/deploy")
async def deploy_fix(
    request: DeploymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Deployed Fix via verschiedene Methoden
    
    Unterstützt: FTP, SFTP, WordPress, Netlify, Vercel
    """
    if not enhanced_fixer or not enhanced_fixer.enable_deployment:
        raise HTTPException(
            status_code=503,
            detail="Deployment-Feature nicht aktiviert"
        )
    
    try:
        deployment_config = {
            'method': request.method,
            'credentials': request.credentials,
            'target_path': request.target_path,
            'files': request.files,
            'backup_before_deploy': request.backup_before_deploy
        }
        
        result = await enhanced_fixer.deploy_fix(deployment_config)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Deployment fehlgeschlagen"
            )
        
        return {
            'success': result['success'],
            'deployment': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Deployment fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deployment fehlgeschlagen: {str(e)}"
        )


@enhanced_router.post("/github-pr")
async def create_github_pr(
    request: GitHubPRRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Erstellt GitHub Pull Request mit Fix
    
    Automatische PR-Erstellung für Developer-Teams
    """
    if not enhanced_fixer or not enhanced_fixer.enable_github:
        raise HTTPException(
            status_code=503,
            detail="GitHub-Integration nicht aktiviert"
        )
    
    try:
        # Fix-Daten aus DB holen
        async with db_pool.acquire() as conn:
            fix_record = await conn.fetchrow(
                "SELECT * FROM generated_fixes WHERE id = $1 AND user_id = $2",
                int(request.fix_id), current_user['user_id']
            )
            
            if not fix_record:
                raise HTTPException(
                    status_code=404,
                    detail="Fix nicht gefunden"
                )
        
        fix_data = dict(fix_record)
        
        result = await enhanced_fixer.create_github_pr(
            repository=request.repository,
            github_token=request.github_token,
            fix_id=request.fix_id,
            fix_data=fix_data
        )
        
        if not result or not result['success']:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'GitHub PR konnte nicht erstellt werden')
            )
        
        return {
            'success': True,
            'pr': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GitHub PR fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub PR fehlgeschlagen: {str(e)}"
        )


@enhanced_router.get("/health")
async def enhanced_health_check():
    """Health-Check für Enhanced Features"""
    return {
        "status": "healthy",
        "service": "enhanced-fix-engine",
        "enhanced_fixer_initialized": enhanced_fixer is not None,
        "timestamp": datetime.now().isoformat()
    }

