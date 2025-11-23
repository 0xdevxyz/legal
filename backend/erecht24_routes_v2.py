"""
Complyo - eRecht24 & AI Fix Engine API Routes v2.0

Neue API-Endpoints für:
- eRecht24-Integration
- Unified Fix Generation
- Widget-Management
- Monitoring

© 2025 Complyo.tech
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import logging

from ai_fix_engine.unified_fix_engine import UnifiedFixEngine
from ai_fix_engine.monitoring import get_monitor, AICallMetrics, FixMetrics
from erecht24_integration import ERecht24Integration
from erecht24_manager import ERecht24Manager  # ✅ NEU: Unified Manager
from widget_manager import WidgetManager, WidgetType
# Import get_current_user from auth_routes, not auth_service
from auth_routes import get_current_user

logger = logging.getLogger(__name__)

# Testing/Development Flags
UNLIMITED_FIXES = os.getenv("UNLIMITED_FIXES", "false").lower() in ("true", "1", "yes")
BYPASS_PAYMENT = os.getenv("BYPASS_PAYMENT", "false").lower() in ("true", "1", "yes")

logger.info(f"🔧 Fix Engine v2 - UNLIMITED_FIXES: {UNLIMITED_FIXES}, BYPASS_PAYMENT: {BYPASS_PAYMENT}")

router = APIRouter(prefix="/api/v2", tags=["ai-fix-v2"])


# =============================================================================
# Request/Response Models
# =============================================================================

class GenerateFixRequest(BaseModel):
    """Request für Fix-Generierung"""
    issue: Dict[str, Any] = Field(..., description="Issue-Daten")
    context: Dict[str, Any] = Field(..., description="Website-Kontext")
    fix_type: Optional[str] = Field(None, description="Optional: code, text, widget, guide")
    user_skill: str = Field("intermediate", description="beginner, intermediate, advanced")


class GenerateFixResponse(BaseModel):
    """Response für Fix-Generierung"""
    success: bool
    fix_result: Optional[Dict[str, Any]]
    error: Optional[str]
    metadata: Dict[str, Any]


class LegalTextRequest(BaseModel):
    """Request für rechtssichere Texte"""
    domain: str
    text_type: str = Field(..., description="impressum, datenschutz, agb, widerruf")
    language: str = Field("de", description="de, en, fr")
    force_refresh: bool = Field(False, description="Cache ignorieren")


class FeedbackRequest(BaseModel):
    """User-Feedback für Fix"""
    fix_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    was_helpful: Optional[bool] = None
    was_applied: Optional[bool] = None
    tags: Optional[List[str]] = None


class WidgetConfigRequest(BaseModel):
    """Request für Widget-Konfiguration"""
    widget_type: str = Field(..., description="cookie-consent, accessibility, combined")
    detected_cookies: Optional[List[Dict[str, Any]]] = None
    analytics_tools: Optional[List[str]] = None
    accessibility_issues: Optional[List[Dict[str, Any]]] = None
    tech_stack: Optional[Dict[str, Any]] = None


# =============================================================================
# Dependency Injection
# =============================================================================

async def get_fix_engine() -> UnifiedFixEngine:
    """Dependency: Unified Fix Engine"""
    return UnifiedFixEngine()


async def get_erecht24_integration() -> ERecht24Integration:
    """Dependency: eRecht24 Integration (Legacy)"""
    from database_service import db_service
    return ERecht24Integration(db_service.pool)


async def get_erecht24_manager() -> ERecht24Manager:
    """Dependency: eRecht24 Manager (Unified)"""
    from database_service import db_service
    # Redis optional (wird später hinzugefügt)
    return ERecht24Manager(db_service.pool, redis_client=None)


async def get_widget_manager() -> WidgetManager:
    """Dependency: Widget Manager"""
    return WidgetManager()


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/fixes/generate", response_model=GenerateFixResponse)
async def generate_fix(
    request: GenerateFixRequest,
    current_user: Dict = Depends(get_current_user),
    engine: UnifiedFixEngine = Depends(get_fix_engine),
    background_tasks: BackgroundTasks = None
):
    """
    Generiert Fix mit der neuen Unified Engine
    
    **Features:**
    - Automatische Fix-Typ-Erkennung
    - AI-gestützte Generierung
    - Template-Fallback
    - Validation & Enrichment
    """
    try:
        # Check Fix Limits (unless bypassed)
        if not UNLIMITED_FIXES and not BYPASS_PAYMENT:
            # Import here to avoid circular dependency
            from database_service import db_pool
            
            user_id = current_user.get("user_id") or current_user.get("id")
            
            async with db_pool.acquire() as conn:
                user_limits = await conn.fetchrow(
                    "SELECT fixes_used, fixes_limit, plan_type FROM user_limits WHERE user_id = $1",
                    user_id
                )
            
            if user_limits:
                fixes_used = user_limits.get('fixes_used', 0) or 0
                fixes_limit = user_limits.get('fixes_limit', 1) or 1
                plan_type = user_limits.get('plan_type', 'free')
                
                if fixes_used >= fixes_limit:
                    logger.warning(f"🚫 Fix limit reached for user {user_id}: {fixes_used}/{fixes_limit}")
                    raise HTTPException(
                        status_code=402,  # Payment Required
                        detail={
                            "error": "fix_limit_reached",
                            "message": "Sie haben Ihr Limit für kostenlose Fixes erreicht. Bitte upgraden Sie, um weitere Fixes zu generieren.",
                            "fixes_used": fixes_used,
                            "fixes_limit": fixes_limit,
                            "plan_type": plan_type
                        }
                    )
        
        # Generate fix
        fix_result = await engine.generate_fix(
            issue=request.issue,
            context=request.context,
            fix_type=request.fix_type,
            user_skill=request.user_skill
        )
        
        # Log to monitoring (in background)
        if background_tasks:
            monitor = get_monitor()
            
            # Log AI call metrics
            if fix_result.metadata.get("ai_model"):
                background_tasks.add_task(
                    monitor.log_ai_call,
                    AICallMetrics(
                        model=fix_result.metadata["ai_model"],
                        tokens_used=fix_result.metadata.get("tokens_used", 0),
                        cost_usd=fix_result.metadata.get("cost_usd", 0.0),
                        response_time_ms=fix_result.metadata.get("response_time_ms", 0),
                        success=fix_result.status == "success",
                        error=None
                    ),
                    user_id=current_user.get("user_id")
                )
            
            # Log fix generation
            background_tasks.add_task(
                monitor.log_fix_generation,
                FixMetrics(
                    fix_id=fix_result.fix_id,
                    fix_type=fix_result.fix_type,
                    issue_category=request.issue.get("category", "unknown"),
                    validation_passed=fix_result.status == "success",
                    generation_time_ms=fix_result.generation_time_ms,
                    fallback_used=fix_result.fallback_used,
                    user_skill_level=request.user_skill
                ),
                user_id=current_user.get("user_id"),
                ai_model_used=fix_result.ai_model_used
            )
        
        # Convert to dict and return
        return GenerateFixResponse(
            success=True,
            fix_result=engine.to_dict(fix_result),
            error=None,
            metadata={
                "generation_time_ms": fix_result.generation_time_ms,
                "fallback_used": fix_result.fallback_used
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Fix generation failed: {e}", exc_info=True)
        return GenerateFixResponse(
            success=False,
            fix_result=None,
            error=str(e),
            metadata={}
        )


@router.post("/erecht24/setup")
async def setup_erecht24_project(
    domain: str,
    company_info: Optional[Dict[str, Any]] = None,
    current_user: Dict = Depends(get_current_user),
    erecht24: ERecht24Integration = Depends(get_erecht24_integration)
):
    """
    Erstellt eRecht24-Projekt für Domain
    
    **Prozess:**
    1. Prüft ob Projekt existiert
    2. Erstellt neues Projekt via eRecht24 API
    3. Speichert in DB
    4. Gibt Projekt-Info zurück
    """
    try:
        project = await erecht24.auto_create_project(
            user_id=current_user["user_id"],
            domain=domain,
            company_info=company_info
        )
        
        if not project:
            raise HTTPException(status_code=500, detail="Projekt-Erstellung fehlgeschlagen")
        
        return {
            "success": True,
            "project": project,
            "message": "eRecht24-Projekt erfolgreich erstellt" if not project.get("existing") else "Projekt existiert bereits"
        }
    
    except Exception as e:
        logger.error(f"❌ eRecht24 setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/legal-texts/{text_type}")
async def get_legal_text(
    text_type: str,
    domain: str,
    language: str = "de",
    force_refresh: bool = False,
    current_user: Dict = Depends(get_current_user),
    erecht24: ERecht24Integration = Depends(get_erecht24_integration)
):
    """
    Holt rechtssicheren Text
    
    **Priorität:**
    1. Cache (wenn gültig und nicht force_refresh)
    2. eRecht24 API
    3. AI-Generierung (Fallback)
    
    **Text-Typen:**
    - impressum
    - datenschutz
    - agb
    - widerruf
    """
    try:
        text = await erecht24.get_legal_text_with_fallback(
            user_id=current_user["user_id"],
            domain=domain,
            text_type=text_type,
            language=language,
            force_refresh=force_refresh
        )
        
        if not text:
            # Fallback to AI generation indicated
            return {
                "success": False,
                "text": None,
                "source": "none",
                "fallback_required": True,
                "message": f"Kein {text_type} verfügbar - AI-Generierung empfohlen"
            }
        
        return {
            "success": True,
            "text": text,
            "source": "erecht24" if not force_refresh else "erecht24_fresh",
            "text_type": text_type,
            "language": language
        }
    
    except Exception as e:
        logger.error(f"❌ Legal text fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/erecht24/sync/{project_id}")
async def sync_erecht24_texts(
    project_id: int,
    current_user: Dict = Depends(get_current_user),
    erecht24: ERecht24Integration = Depends(get_erecht24_integration)
):
    """
    Synchronisiert alle Texte für ein Projekt
    
    Holt alle verfügbaren Texte von eRecht24 und cached sie.
    """
    try:
        result = await erecht24.sync_all_texts(
            project_id=project_id,
            triggered_by="manual"
        )
        
        return {
            "success": result["status"] in ["success", "partial"],
            "result": result
        }
    
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/erecht24/webhook")
async def erecht24_webhook(
    project_id: str,
    webhook_data: Dict[str, Any],
    erecht24: ERecht24Integration = Depends(get_erecht24_integration)
):
    """
    Webhook-Endpoint für eRecht24
    
    Wird aufgerufen wenn Texte in eRecht24 aktualisiert werden.
    """
    try:
        result = await erecht24.handle_webhook(project_id, webhook_data)
        return result
    
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/erecht24/health")
async def get_erecht24_health(
    current_user: Dict = Depends(get_current_user),
    manager: ERecht24Manager = Depends(get_erecht24_manager)
):
    """
    🏥 Health-Check für eRecht24-Integration
    
    Zeigt Status von:
    - API-Verbindung
    - Redis-Cache
    - DB-Cache
    - Gesamtstatus
    
    Verwendung im Dashboard zur Anzeige von Service-Status
    """
    try:
        health_status = await manager.get_health_status()
        
        return {
            "success": True,
            "health": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "success": False,
            "health": {
                "overall": "error",
                "error": str(e)
            },
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/legal-texts-v2/{text_type}")
async def get_legal_text_v2(
    text_type: str,
    domain: str,
    language: str = "de",
    force_refresh: bool = False,
    current_user: Dict = Depends(get_current_user),
    manager: ERecht24Manager = Depends(get_erecht24_manager)
):
    """
    🆕 V2: Unified Legal Text Retrieval mit robuster Fallback-Kette
    
    **Fallback-Hierarchie:**
    1. eRecht24 Live-API
    2. Redis Cache (< 7 Tage)
    3. DB Cache (< 30 Tage)
    4. AI-Generator (mit Warnung)
    
    **Unterstützte Text-Typen:**
    - impressum
    - datenschutz / privacy_policy
    - agb
    - widerruf
    - disclaimer
    
    **Response:**
    ```json
    {
        "success": true,
        "content": "<html>...</html>",
        "source": "api"|"redis"|"db"|"ai",
        "last_updated": "2025-11-21T...",
        "cached": true|false,
        "warning": "..." (nur bei AI)
    }
    ```
    """
    try:
        result = await manager.get_legal_text(
            user_id=current_user["user_id"],
            domain=domain,
            text_type=text_type,
            language=language,
            force_refresh=force_refresh
        )
        
        if result.get("content"):
            return {
                "success": True,
                **result
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unbekannter Fehler"),
                "source": result.get("source", "none")
            }
    
    except Exception as e:
        logger.error(f"❌ Legal text retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/widgets/configure")
async def configure_widget(
    request: WidgetConfigRequest,
    current_user: Dict = Depends(get_current_user),
    widget_manager: WidgetManager = Depends(get_widget_manager)
):
    """
    Konfiguriert Widget basierend auf Website-Scan
    
    **Widget-Typen:**
    - cookie-consent
    - accessibility
    - combined
    """
    try:
        if request.widget_type == "cookie-consent":
            config = widget_manager.configure_cookie_widget(
                detected_cookies=request.detected_cookies or [],
                analytics_tools=request.analytics_tools or [],
                tech_stack=request.tech_stack
            )
            
            # Generate integration code
            site_id = f"complyo_{current_user['user_id']}"
            integration_code = await widget_manager.generate_cookie_widget_code(
                site_id=site_id,
                config=config
            )
        
        elif request.widget_type == "accessibility":
            config = widget_manager.configure_accessibility_widget(
                accessibility_issues=request.accessibility_issues or [],
                tech_stack=request.tech_stack
            )
            
            site_id = f"complyo_{current_user['user_id']}"
            integration_code = await widget_manager.generate_accessibility_widget_code(
                site_id=site_id,
                config=config
            )
        
        elif request.widget_type == "combined":
            cookie_config = widget_manager.configure_cookie_widget(
                detected_cookies=request.detected_cookies or [],
                analytics_tools=request.analytics_tools or [],
                tech_stack=request.tech_stack
            )
            
            a11y_config = widget_manager.configure_accessibility_widget(
                accessibility_issues=request.accessibility_issues or [],
                tech_stack=request.tech_stack
            )
            
            site_id = f"complyo_{current_user['user_id']}"
            integration_code = await widget_manager.generate_combined_widget_code(
                site_id=site_id,
                cookie_config=cookie_config,
                accessibility_config=a11y_config
            )
            
            config = {"cookie": cookie_config, "accessibility": a11y_config}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown widget type: {request.widget_type}")
        
        return {
            "success": True,
            "widget_type": request.widget_type,
            "config": config,
            "integration_code": integration_code,
            "preview_url": widget_manager.get_widget_preview_url(
                WidgetType(request.widget_type),
                site_id,
                config
            )
        }
    
    except Exception as e:
        logger.error(f"❌ Widget configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: Dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    User-Feedback für generierten Fix
    
    Hilft uns, die AI-Fix-Qualität zu verbessern.
    """
    try:
        monitor = get_monitor()
        
        # Log feedback (in background)
        if background_tasks:
            background_tasks.add_task(
                monitor.log_user_feedback,
                fix_id=feedback.fix_id,
                user_id=current_user["user_id"],
                rating=feedback.rating,
                feedback_text=feedback.feedback_text,
                was_helpful=feedback.was_helpful,
                was_applied=feedback.was_applied,
                tags=feedback.tags
            )
        else:
            # Synchron falls kein BackgroundTasks
            await monitor.log_user_feedback(
                fix_id=feedback.fix_id,
                user_id=current_user["user_id"],
                rating=feedback.rating,
                feedback_text=feedback.feedback_text,
                was_helpful=feedback.was_helpful,
                was_applied=feedback.was_applied,
                tags=feedback.tags
            )
        
        return {
            "success": True,
            "message": "Vielen Dank für Ihr Feedback!"
        }
    
    except Exception as e:
        logger.error(f"❌ Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(
    current_user: Dict = Depends(get_current_user)
):
    """
    Monitoring-Dashboard-Metriken
    
    **Requires:** Admin-Rechte
    """
    # Check if admin
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich")
    
    try:
        monitor = get_monitor()
        metrics = await monitor.get_dashboard_metrics()
        
        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Dashboard metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/ai-calls")
async def get_ai_call_stats(
    days: int = 30,
    current_user: Dict = Depends(get_current_user)
):
    """
    AI-Call-Statistiken
    
    **Requires:** Admin-Rechte
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich")
    
    try:
        monitor = get_monitor()
        stats = await monitor.get_ai_call_stats(
            start_date=datetime.now() - timedelta(days=days)
        )
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        logger.error(f"❌ AI call stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health-Check für AI Fix Engine v2
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "unified_engine": "ok",
            "erecht24_integration": "ok",
            "widget_manager": "ok",
            "monitoring": "ok"
        }
    }


# =============================================================================
# Exports
# =============================================================================

import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


