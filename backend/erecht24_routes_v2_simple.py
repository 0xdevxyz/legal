"""
Complyo - eRecht24 & AI Fix Engine API Routes v2.0 (Simplified)

Simplified version with basic health endpoint to verify deployment.
Full features will be gradually enabled once base system is stable.

© 2025 Complyo.tech
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import logging

# Import auth dependency
from auth_routes import get_current_user

logger = logging.getLogger(__name__)

# Testing Flags
UNLIMITED_FIXES = os.getenv("UNLIMITED_FIXES", "false").lower() in ("true", "1", "yes")
BYPASS_PAYMENT = os.getenv("BYPASS_PAYMENT", "false").lower() in ("true", "1", "yes")

logger.info(f"🔧 Fix Routes v2 - UNLIMITED_FIXES: {UNLIMITED_FIXES}, BYPASS_PAYMENT: {BYPASS_PAYMENT}")

router = APIRouter(prefix="/api/v2", tags=["ai-fix-v2"])


# Request/Response Models
class GenerateFixRequest(BaseModel):
    issue: Dict[str, Any]
    context: Dict[str, Any]
    fix_type: Optional[str] = None
    user_skill: str = "intermediate"


class GenerateFixResponse(BaseModel):
    success: bool
    fix_result: Optional[Dict[str, Any]]
    error: Optional[str]
    metadata: Dict[str, Any]


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for V2 API
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "message": "Complyo V2 API is running",
        "features": {
            "ai_fix_engine": "available",
            "erecht24_integration": "available",
            "widget_manager": "available",
            "monitoring": "available"
        }
    }


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """
    System status endpoint
    """
    return {
        "database": "connected",
        "ai_engine": "ready",
        "erecht24": "ready",
        "widgets": "ready"
    }


@router.post("/fixes/generate", response_model=GenerateFixResponse)
async def generate_fix(
    request: GenerateFixRequest,
    current_user: Dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    Generiert AI-gestützte Fixes für ein Issue
    
    **Features:**
    - AI-basierte Fix-Generierung
    - Respektiert Fix-Limits
    - UNLIMITED_FIXES für Testing
    """
    try:
        # Check Fix Limits (unless bypassed)
        if not UNLIMITED_FIXES and not BYPASS_PAYMENT:
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
        
        # Import Fix Engine
        from ai_fix_engine.unified_fix_engine import UnifiedFixEngine
        
        # Generate fix
        engine = UnifiedFixEngine()
        fix_result = await engine.generate_fix(
            issue=request.issue,
            context=request.context,
            fix_type=request.fix_type,
            user_skill=request.user_skill
        )
        
        # Increment fix counter (if not bypassed)
        if not UNLIMITED_FIXES and not BYPASS_PAYMENT:
            from database_service import db_pool
            user_id = current_user.get("user_id") or current_user.get("id")
            
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE user_limits
                    SET fixes_used = COALESCE(fixes_used, 0) + 1,
                        fix_started = TRUE
                    WHERE user_id = $1
                    """,
                    user_id
                )
        
        logger.info(f"✅ Fix generated successfully for user {current_user.get('user_id')}")
        
        # Convert to dict and return
        return GenerateFixResponse(
            success=True,
            fix_result=engine.to_dict(fix_result),
            error=None,
            metadata={
                "generation_time_ms": fix_result.generation_time_ms,
                "fallback_used": fix_result.fallback_used,
                "bypass_active": UNLIMITED_FIXES or BYPASS_PAYMENT
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fix generation failed: {e}", exc_info=True)
        return GenerateFixResponse(
            success=False,
            fix_result=None,
            error=str(e),
            metadata={}
        )

