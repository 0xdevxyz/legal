"""
Fix API Routes für Complyo
Endpoints für KI-Fix Generierung und Export
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import os
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncpg

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

fix_router = APIRouter(prefix="/api/v2/fixes", tags=["fixes"])
security = HTTPBearer()

# Global references (set in main_production.py)
db_pool = None
auth_service = None
fix_generator = None
export_service = None

class FixRequest(BaseModel):
    issue_id: str
    issue_category: str
    

class ExportRequest(BaseModel):
    fix_id: int
    export_format: str = 'html'  # 'html', 'pdf', 'txt'

class ProposePRRequest(BaseModel):
    fix_id: int
    target_repo: str  # Format: "username/repo-name"
    github_token: str
    file_path: Optional[str] = None  # Optional: Ziel-Dateipfad im Repo

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        logger.info(f"User authenticated: {user_data.get('user_id')}")
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")

@fix_router.post("/generate", response_model=Dict[str, Any])
@limiter.limit("10/hour")  # AI Plan: 10 Fix-Generierungen pro Stunde
async def generate_fix(
    request: Request,
    fix_request: FixRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generiert einen KI-Fix für ein Issue
    
    - AI Plan: Code-Snippet + Step-by-Step Guide
    - Expert Plan: Vollständiges Dokument + Audit-Trail
    
    ⚠️ WICHTIG: Mit dem ersten Fix verfällt die 14-Tage-Geld-zurück-Garantie
    """
    try:
        # Validierung der Eingabedaten
        if not fix_request.issue_id or not fix_request.issue_id.strip():
            logger.warning(f"Invalid issue_id received: {fix_request.issue_id}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_input",
                    "message": "issue_id ist erforderlich und darf nicht leer sein."
                }
            )
        
        if not fix_request.issue_category or not fix_request.issue_category.strip():
            logger.warning(f"Invalid issue_category received: {fix_request.issue_category}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_input",
                    "message": "issue_category ist erforderlich und darf nicht leer sein."
                }
            )
        
        # Nutze globale Referenzen (gesetzt in main_production.py startup)
        if not fix_generator:
            logger.error("Fix generator not initialized!")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "service_unavailable",
                    "message": "Fix Generator Service ist nicht verfügbar. Bitte kontaktieren Sie den Support."
                }
            )
        
        if not db_pool:
            logger.error("Database pool not initialized!")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "service_unavailable",
                    "message": "Datenbankverbindung ist nicht verfügbar. Bitte kontaktieren Sie den Support."
                }
            )
        
        user_id = current_user['user_id']
        plan_type = current_user.get('plan', 'free')
        
        logger.info(f"🔧 Fix-Generierung gestartet: user_id={user_id}, issue_id={fix_request.issue_id}, category={fix_request.issue_category}, plan={plan_type}")
        
        # Check: Fix Limit, Domain Lock & ist dies der erste Fix?
        async with db_pool.acquire() as conn:
            user_limits = await conn.fetchrow(
                """
                SELECT 
                    fix_started, 
                    money_back_eligible,
                    fixes_used,
                    fixes_limit,
                    plan_type
                FROM user_limits 
                WHERE user_id = $1
                """,
                user_id
            )
            
            if not user_limits:
                # User hat keine Limits -> Erstelle Default Limits
                await conn.execute(
                    """
                    INSERT INTO user_limits (user_id, plan_type, fixes_used, fixes_limit)
                    VALUES ($1, $2, 0, 1)
                    """,
                    user_id, plan_type or 'free'
                )
                user_limits = await conn.fetchrow(
                    "SELECT fix_started, money_back_eligible, fixes_used, fixes_limit FROM user_limits WHERE user_id = $1",
                    user_id
                )
            
            # Check Fix Limit (Freemium Model)
            fixes_used = user_limits.get('fixes_used', 0) or 0
            fixes_limit = user_limits.get('fixes_limit', 1) or 1
            
            if fixes_used >= fixes_limit:
                # Limit reached -> Paywall
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail={
                        "error": "fix_limit_reached",
                        "message": "Sie haben Ihr Limit für kostenlose Fixes erreicht. Bitte upgraden Sie, um weitere Fixes zu generieren.",
                        "fixes_used": fixes_used,
                        "fixes_limit": fixes_limit,
                        "plan_type": user_limits.get('plan_type', 'free')
                    }
                )
            
            first_fix = not user_limits or not user_limits['fix_started']
        
        # Generiere Fix
        try:
            fix_data = await fix_generator.generate_fix(
                issue_id=fix_request.issue_id,
                issue_category=fix_request.issue_category,
                user_id=user_id,
                plan_type=plan_type
            )
            
            # ✅ Fix erfolgreich generiert -> Increment Counter
            async with db_pool.acquire() as conn:
                # Update Fix Counter
                await conn.execute(
                    """
                    UPDATE user_limits
                    SET 
                        fixes_used = COALESCE(fixes_used, 0) + 1,
                        fix_started = TRUE
                    WHERE user_id = $1
                    """,
                    user_id
                )
                
                # Track Fix in generated_fixes Tabelle
                await conn.execute(
                    """
                    INSERT INTO generated_fixes (user_id, issue_id, issue_category, fix_type, plan_type)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    user_id, fix_request.issue_id, fix_request.issue_category, 'code_snippet', plan_type
                )
            
            logger.info(f"✅ Fix erfolgreich generiert: user_id={user_id}, issue_id={fix_request.issue_id}, fixes_remaining={fixes_limit - (fixes_used + 1)}")
            
            return {
                'success': True,
                'fix': fix_data,
                'first_fix': first_fix,
                'money_back_warning': first_fix,
                'plan_type': plan_type,
                'fixes_remaining': fixes_limit - (fixes_used + 1)
            }
            
        except Exception as gen_error:
            logger.error(f"❌ Fix generation error for user {user_id}: {gen_error}", exc_info=True)
            
            # Check für spezifische Fehlertypen
            error_str = str(gen_error)
            
            if "Optimierungs-Limit" in error_str or "Export-Limit" in error_str:
                raise HTTPException(
                    status_code=403,
                    detail={
                        'error': 'limit_reached',
                        'message': error_str,
                        'upgrade_url': '/subscription/expert'
                    }
                )
            
            if "timeout" in error_str.lower() or "timed out" in error_str.lower():
                raise HTTPException(
                    status_code=504,
                    detail={
                        'error': 'timeout',
                        'message': 'Die Fix-Generierung hat zu lange gedauert. Bitte versuchen Sie es erneut.'
                    }
                )
            
            if "OpenRouter" in error_str or "API" in error_str:
                raise HTTPException(
                    status_code=503,
                    detail={
                        'error': 'ai_service_unavailable',
                        'message': 'KI-Service ist vorübergehend nicht verfügbar. Bitte versuchen Sie es in wenigen Minuten erneut.'
                    }
                )
            
            # Allgemeiner Fehler
            raise HTTPException(
                status_code=500,
                detail={
                    'error': 'generation_failed',
                    'message': f"Fix-Generierung fehlgeschlagen: {error_str}",
                    'support_message': 'Bitte kontaktieren Sie den Support, falls das Problem weiterhin besteht.'
                }
            )
    
    except HTTPException:
        raise
    except asyncpg.PostgresError as db_error:
        logger.error(f"❌ Database error in generate_fix: {db_error}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'database_error',
                'message': 'Datenbankfehler. Bitte versuchen Sie es später erneut.'
            }
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error in generate_fix endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'internal_error',
                'message': 'Ein unerwarteter Fehler ist aufgetreten. Bitte kontaktieren Sie den Support.'
            }
        )

@fix_router.post("/export", response_model=Dict[str, Any])
async def export_fix(
    request: ExportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Exportiert einen generierten Fix
    
    Limitierungen:
    - AI Plan: 10 Exports/Monat
    - Expert Plan: Unbegrenzt
    """
    try:
        # Nutze globale Referenz (gesetzt in main_production.py startup)
        if not fix_generator:
            raise HTTPException(
                status_code=500,
                detail="Fix generator not initialized"
            )
        
        user_id = current_user['user_id']
        plan_type = current_user['plan']
        
        logger.info(f"Exporting fix {request.fix_id} for user {user_id} in format {request.export_format}")
        
        # Für Expert Plan: Kein Limit
        if plan_type == 'expert':
            return {
                'success': True,
                'exported_at': datetime.now().isoformat(),
                'format': request.export_format,
                'message': 'Expert Plan: Unlimited exports'
            }
        
        # Für AI Plan: Export mit Limit-Check
        try:
            # Nutze globale Referenz (gesetzt in main_production.py startup)
            if not export_service:
                raise HTTPException(
                    status_code=500,
                    detail="Export service not initialized"
                )
            
            export_result = await export_service.export_fix(
                fix_id=request.fix_id,
                user_id=user_id,
                export_format=request.export_format
            )
            
            return export_result
            
        except Exception as export_error:
            if "Export-Limit" in str(export_error):
                raise HTTPException(
                    status_code=403,
                    detail={
                        'error': 'export_limit_reached',
                        'message': 'Sie haben Ihr monatliches Export-Limit (10) erreicht.',
                        'upgrade_url': '/subscription/expert',
                        'plan_upgrade': 'Expert Plan bietet unbegrenzte Exports'
                    }
                )
            
            raise HTTPException(
                status_code=500,
                detail=f"Export failed: {str(export_error)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in export_fix endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while exporting fix"
        )

@fix_router.get("/history", response_model=Dict[str, Any])
async def get_fix_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Gibt die Fix-History eines Users zurück
    """
    try:
        # Nutze globale Referenz (gesetzt in main_production.py startup)
        user_id = current_user['user_id']
        
        async with db_pool.acquire() as conn:
            fixes = await conn.fetch(
                """
                SELECT 
                    id,
                    issue_id,
                    issue_category,
                    fix_type,
                    plan_type,
                    generated_at,
                    exported,
                    exported_at,
                    export_format
                FROM generated_fixes
                WHERE user_id = $1
                ORDER BY generated_at DESC
                LIMIT 50
                """,
                user_id
            )
            
            return {
                'success': True,
                'fixes': [dict(f) for f in fixes],
                'total': len(fixes)
            }
    
    except Exception as e:
        logger.error(f"Error getting fix history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve fix history"
        )

@fix_router.get("/limits", response_model=Dict[str, Any])
async def get_user_limits(
    current_user: dict = Depends(get_current_user)
):
    """
    Gibt die aktuellen Plan-Limits eines Users zurück
    """
    try:
        # Nutze globale Referenz (gesetzt in main_production.py startup)
        user_id = current_user['user_id']
        
        async with db_pool.acquire() as conn:
            limits = await conn.fetchrow(
                """
                SELECT 
                    plan_type,
                    websites_count,
                    websites_max,
                    exports_this_month,
                    exports_max,
                    exports_reset_date,
                    fix_started,
                    money_back_eligible,
                    subscription_start
                FROM user_limits
                WHERE user_id = $1
                """,
                user_id
            )
            
            if not limits:
                # Return defaults for new users
                return {
                    'success': True,
                    'limits': {
                        'plan_type': current_user.get('plan', 'ai'),
                        'websites_count': 0,
                        'websites_max': 1,
                        'exports_this_month': 0,
                        'exports_max': 10,
                        'fix_started': False,
                        'money_back_eligible': True
                    }
                }
            
            # Calculate days until money back expires
            subscription = await conn.fetchrow(
                """
                SELECT 
                    refund_deadline,
                    refund_eligible,
                    fix_first_used_at
                FROM subscriptions
                WHERE user_id = $1 AND status = 'active'
                ORDER BY started_at DESC
                LIMIT 1
                """,
                user_id
            )
            
            money_back_days_left = None
            if subscription and subscription['refund_eligible'] and subscription['refund_deadline']:
                delta = subscription['refund_deadline'] - datetime.now()
                money_back_days_left = max(0, delta.days)
            
            return {
                'success': True,
                'limits': {
                    'plan_type': limits['plan_type'],
                    'websites_count': limits['websites_count'],
                    'websites_max': limits['websites_max'],
                    'exports_this_month': limits['exports_this_month'],
                    'exports_max': limits['exports_max'],
                    'exports_reset_date': limits['exports_reset_date'].isoformat() if limits['exports_reset_date'] else None,
                    'fix_started': limits['fix_started'],
                    'money_back_eligible': limits['money_back_eligible'],
                    'money_back_days_left': money_back_days_left,
                    'subscription_start': limits['subscription_start'].isoformat() if limits['subscription_start'] else None
                }
            }
    
    except Exception as e:
        logger.error(f"Error getting user limits: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user limits"
        )

@fix_router.get("/{fix_id}/download/{filename}")
async def download_fix(
    fix_id: int,
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download-Endpoint für exportierte Fixes
    """
    try:
        # Nutze globale Referenz (gesetzt in main_production.py startup)
        user_id = current_user['user_id']
        
        # Verify ownership
        async with db_pool.acquire() as conn:
            fix = await conn.fetchrow(
                "SELECT * FROM generated_fixes WHERE id = $1 AND user_id = $2",
                fix_id,
                user_id
            )
            
            if not fix:
                raise HTTPException(
                    status_code=404,
                    detail="Fix not found or access denied"
                )
        
        # Build file path
        export_dir = "/tmp/complyo_exports"
        file_path = os.path.join(export_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Export file not found"
            )
        
        # Determine media type
        media_type = "text/html" if filename.endswith('.html') else "application/pdf"
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to download file"
        )

@fix_router.get("/health")
async def health_check():
    """Health check für Fix-Service"""
    # Nutze globale Referenzen (gesetzt in main_production.py startup)
    return {
        "status": "healthy",
        "service": "fix-generator",
        "fix_generator_initialized": fix_generator is not None,
        "db_pool_initialized": db_pool is not None,
        "timestamp": datetime.now().isoformat()
    }

@fix_router.post("/propose-pr")
async def propose_pr_via_github(
    request: ProposePRRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Triggert GitHub Actions Workflow für automatische PR-Erstellung
    
    Workflow:
    1. Holt Fix-Daten aus DB
    2. Generiert Unified Diff
    3. Sendet repository_dispatch an GitHub
    4. GitHub Actions erstellt PR mit dem Patch
    
    Args:
        request: ProposePRRequest mit fix_id, target_repo, github_token
        current_user: Authentifizierter User
        
    Returns:
        Success-Message mit Workflow-Status
        
    Raises:
        HTTPException: Bei GitHub API-Fehlern oder fehlenden Daten
    """
    import base64
    import httpx
    
    try:
        user_id = current_user['user_id']
        
        logger.info(f"🚀 PR-Proposal gestartet: user_id={user_id}, fix_id={request.fix_id}, repo={request.target_repo}")
        
        # 1. Hole Fix-Daten aus DB
        async with db_pool.acquire() as conn:
            fix_record = await conn.fetchrow(
                """
                SELECT 
                    gf.id,
                    gf.issue_id,
                    gf.issue_category,
                    gf.fix_type,
                    gf.generated_at
                FROM generated_fixes gf
                WHERE gf.id = $1 AND gf.user_id = $2
                """,
                request.fix_id,
                user_id
            )
            
            if not fix_record:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "fix_not_found",
                        "message": f"Fix mit ID {request.fix_id} nicht gefunden oder gehört nicht zu diesem User."
                    }
                )
        
        # 2. Generiere Fix-Content (aus FixGenerator)
        fix_data = await fix_generator.generate_fix(
            issue_id=fix_record['issue_id'],
            issue_category=fix_record['issue_category'],
            user_id=user_id,
            plan_type=current_user.get('plan', 'ai')
        )
        
        # 3. Erstelle Unified Diff
        code = fix_data.get('code', '')
        file_path = request.file_path or f"fixes/{fix_record['issue_category']}.html"
        
        # Einfacher Patch (in Production: intelligentere Diff-Generierung)
        patch = f"""--- a/{file_path}
+++ b/{file_path}
@@ -1,0 +1,{len(code.splitlines())} @@
+{chr(10).join('+ ' + line for line in code.splitlines())}
"""
        
        patch_b64 = base64.b64encode(patch.encode()).decode()
        
        # 4. Trigger GitHub Actions via repository_dispatch
        github_url = f"https://api.github.com/repos/{request.target_repo}/dispatches"
        headers = {
            "Authorization": f"token {request.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "event_type": "ai-fix-proposal",
            "client_payload": {
                "title": f"🤖 Fix: {fix_record['issue_category'].title()} Compliance",
                "body": f"""## Automatischer Compliance-Fix

**Kategorie:** {fix_record['issue_category']}
**Issue ID:** {fix_record['issue_id']}
**Generiert:** {fix_record['generated_at']}

### Beschreibung
Dieser PR behebt automatisch erkannte Compliance-Probleme.

### Änderungen
- Datei: `{file_path}`
- Fix-Typ: {fix_record['fix_type']}

### Nächste Schritte
1. ✅ Code-Review durchführen
2. ✅ Lokal testen
3. ✅ Bei Bedarf anpassen
4. ✅ Mergen

---
🤖 Generiert von [Complyo](https://complyo.tech) | Fix-ID: {request.fix_id}
""",
                "patch_b64": patch_b64,
                "branch": f"complyo-fix-{request.fix_id}"
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(github_url, json=payload, headers=headers)
            
        if response.status_code == 204:
            logger.info(f"✅ GitHub Actions Workflow getriggert: {request.target_repo}")
            return {
                "success": True,
                "message": "PR-Workflow erfolgreich gestartet",
                "repo": request.target_repo,
                "branch": f"complyo-fix-{request.fix_id}",
                "github_actions_url": f"https://github.com/{request.target_repo}/actions"
            }
        else:
            error_text = response.text
            logger.error(f"❌ GitHub API Fehler {response.status_code}: {error_text}")
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "github_api_error",
                    "message": f"GitHub API Fehler: {response.status_code}",
                    "details": error_text,
                    "hint": "Prüfen Sie ob der GitHub Token gültig ist und 'repo' + 'workflow' Permissions hat."
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler in propose_pr: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "pr_proposal_failed",
                "message": f"PR-Erstellung fehlgeschlagen: {str(e)}"
            }
        )

