"""
BFSG Accessibility Fix API Routes
Anfängerfreundliche Fix-Pipeline für Barrierefreiheit

Endpoints:
- POST /api/v2/accessibility/analyze - Issues kategorisieren
- POST /api/v2/accessibility/generate-fixes - Fixes generieren
- GET /api/v2/accessibility/download-bundle - Fix-Bundle herunterladen
- POST /api/v2/accessibility/generate-alt-text - Einzelnen Alt-Text generieren
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import io
from datetime import datetime

from compliance_engine.feature_engine import (
    FeatureEngine, FeatureId, StructuredIssue,
    AutoFixLevel, Difficulty, FixType, feature_engine
)
from compliance_engine.patch_service import (
    PatchService, FixPackage, PatchResult, patch_service
)
from accessibility_patch_generator import AccessibilityPatchGenerator

logger = logging.getLogger(__name__)

# Router Setup
accessibility_fix_router = APIRouter(
    prefix="/api/v2/accessibility",
    tags=["accessibility-fixes"]
)
security = HTTPBearer()

# Global references (set in main_production.py)
db_pool = None
auth_service = None
db_service = None  # Für Modul-Checks

# Service Instances
patch_generator = AccessibilityPatchGenerator()


# =============================================================================
# Request/Response Models
# =============================================================================

class AnalyzeRequest(BaseModel):
    """Request für Issue-Analyse"""
    site_url: str = Field(..., description="URL der Website")
    issues: List[Dict[str, Any]] = Field(..., description="Rohe Scanner-Issues")


class AnalyzeResponse(BaseModel):
    """Response der Issue-Analyse"""
    site_url: str
    total_issues: int
    structured_issues: List[Dict[str, Any]]
    summary: Dict[str, Any]
    by_difficulty: Dict[str, int]
    by_feature: Dict[str, int]


class GenerateFixesRequest(BaseModel):
    """Request für Fix-Generierung"""
    site_url: str = Field(..., description="URL der Website")
    issues: List[Dict[str, Any]] = Field(..., description="Strukturierte Issues")
    file_contents: Optional[Dict[str, str]] = Field(
        None, 
        description="Datei-Inhalte für Code-Patches (file_path -> content)"
    )
    include_widget: bool = Field(True, description="Widget-Fixes einschließen")
    include_code: bool = Field(True, description="Code-Patches generieren")


class GenerateFixesResponse(BaseModel):
    """Response der Fix-Generierung"""
    success: bool
    site_url: str
    fix_package: Dict[str, Any]
    generation_time_ms: int


class GenerateAltTextRequest(BaseModel):
    """Request für Alt-Text-Generierung"""
    image_src: str = Field(..., description="URL oder Pfad des Bildes")
    page_context: Optional[str] = Field("", description="Kontext der Seite")
    surrounding_text: Optional[str] = Field("", description="Umgebender Text")
    filename: Optional[str] = Field("", description="Dateiname")


class GenerateAltTextResponse(BaseModel):
    """Response der Alt-Text-Generierung"""
    success: bool
    alt_text: str
    is_decorative: bool


class DownloadBundleRequest(BaseModel):
    """Request für Bundle-Download"""
    site_url: str
    fix_package: Dict[str, Any]
    include_wordpress: bool = True


# =============================================================================
# Auth Helper
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Verify JWT token and return user data"""
    try:
        if not auth_service:
            raise HTTPException(status_code=500, detail="Auth service not initialized")
        
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Optional auth - returns None if not authenticated"""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_accessibility_module(user: Dict[str, Any]) -> bool:
    """
    Check if user has access to the accessibility module.
    Raises 403 if not granted.
    """
    if not db_service:
        logger.warning("Database service not configured for module checks")
        return True
    
    user_id = str(user.get("id") or user.get("user_id"))
    has_module = await db_service.check_user_module(user_id, 'accessibility')
    
    if not has_module:
        raise HTTPException(
            status_code=403, 
            detail="Modul 'Barrierefreiheit' nicht gebucht. Bitte upgraden Sie Ihren Plan."
        )
    
    return True


# =============================================================================
# Endpoints
# =============================================================================

@accessibility_fix_router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_issues(
    request: AnalyzeRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> AnalyzeResponse:
    """
    Kategorisiert rohe Scanner-Issues und ordnet sie Features zu.
    
    Requires 'accessibility' module to be active.
    
    Dies ist der erste Schritt im Fix-Wizard:
    1. Nimmt rohe Issues vom Scanner
    2. Ordnet sie Feature-IDs zu (ALT_TEXT, CONTRAST, etc.)
    3. Bestimmt Schwierigkeit und Fix-Typ
    4. Erstellt Zusammenfassung für Dashboard
    """
    # Modul-Check: User muss Barrierefreiheit-Modul gebucht haben
    await require_accessibility_module(user)
    
    logger.info(f"🔍 Analyzing {len(request.issues)} issues for {request.site_url}")
    
    try:
        # Kategorisiere Issues
        structured_issues = feature_engine.categorize_issues(request.issues)
        
        # Erstelle Zusammenfassung
        summary = feature_engine.get_summary(structured_issues)
        
        # Gruppierungen
        by_difficulty = feature_engine.group_by_difficulty(structured_issues)
        by_feature = feature_engine.group_by_feature(structured_issues)
        
        return AnalyzeResponse(
            site_url=request.site_url,
            total_issues=len(structured_issues),
            structured_issues=[issue.to_dict() for issue in structured_issues],
            summary=summary,
            by_difficulty={
                k.value: len(v) for k, v in by_difficulty.items()
            },
            by_feature={
                k.value: len(v) for k, v in by_feature.items()
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analyse fehlgeschlagen: {str(e)}")


@accessibility_fix_router.post("/generate-fixes", response_model=GenerateFixesResponse)
async def generate_fixes(
    request: GenerateFixesRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_current_user)
) -> GenerateFixesResponse:
    """
    Generiert Fixes für die analysierten Issues.
    
    Requires 'accessibility' module to be active.
    
    Dies ist der zweite Schritt im Fix-Wizard:
    1. Nimmt strukturierte Issues
    2. Generiert Widget-Fixes (sofort)
    3. Generiert Code-Patches via LLM
    4. Erstellt manuelle Anleitungen
    """
    # Modul-Check: User muss Barrierefreiheit-Modul gebucht haben
    await require_accessibility_module(user)
    
    import time
    start_time = time.time()
    
    logger.info(f"🔧 Generating fixes for {request.site_url}")
    
    try:
        # Generiere Fix-Paket
        fix_package = await patch_service.generate_fix_package(
            site_url=request.site_url,
            raw_issues=request.issues,
            file_contents=request.file_contents
        )
        
        generation_time = int((time.time() - start_time) * 1000)
        
        # Speichere in Datenbank (Background Task)
        if db_pool:
            background_tasks.add_task(
                save_fix_package_to_db,
                user.get('user_id'),
                request.site_url,
                fix_package.to_dict()
            )
        
        return GenerateFixesResponse(
            success=True,
            site_url=request.site_url,
            fix_package=fix_package.to_dict(),
            generation_time_ms=generation_time
        )
    
    except Exception as e:
        logger.error(f"❌ Fix generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fix-Generierung fehlgeschlagen: {str(e)}")


@accessibility_fix_router.post("/download-bundle")
async def download_bundle(
    request: DownloadBundleRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> StreamingResponse:
    """
    Generiert und liefert das Fix-Bundle als ZIP-Download.
    
    Das Bundle enthält:
    - README.md mit Anleitung
    - Code-Patches als .patch Dateien
    - HTML-Snippets
    - CSS-Fixes
    - WordPress-Plugin (optional)
    - Widget-Integration
    """
    logger.info(f"📦 Generating download bundle for {request.site_url}")
    
    try:
        # Generiere Bundle
        zip_buffer = await patch_generator.generate_enhanced_bundle(
            site_url=request.site_url,
            fix_package=request.fix_package,
            include_wordpress=request.include_wordpress
        )
        
        # Dateiname generieren
        site_slug = request.site_url.replace('https://', '').replace('http://', '')
        site_slug = site_slug.replace('/', '-').replace('.', '-')[:30]
        filename = f"complyo-fixes-{site_slug}-{datetime.now().strftime('%Y%m%d')}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Bundle generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bundle-Generierung fehlgeschlagen: {str(e)}")


@accessibility_fix_router.post("/generate-alt-text", response_model=GenerateAltTextResponse)
async def generate_alt_text(
    request: GenerateAltTextRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> GenerateAltTextResponse:
    """
    Generiert einen Alt-Text für ein einzelnes Bild.
    
    Nützlich für:
    - Einzelne Bilder im Dashboard
    - Live-Vorschau im Wizard
    """
    logger.info(f"🖼️ Generating alt text for {request.image_src[:50]}...")
    
    try:
        success, alt_text = await patch_service.generate_alt_text(
            image_src=request.image_src,
            page_context=request.page_context or "",
            surrounding_text=request.surrounding_text or "",
            filename=request.filename or ""
        )
        
        # Prüfe ob dekorativ
        is_decorative = alt_text == "" or alt_text.upper() == "DECORATIVE"
        
        return GenerateAltTextResponse(
            success=success,
            alt_text=alt_text if not is_decorative else "",
            is_decorative=is_decorative
        )
    
    except Exception as e:
        logger.error(f"❌ Alt text generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Alt-Text-Generierung fehlgeschlagen: {str(e)}")


@accessibility_fix_router.get("/feature-definitions")
async def get_feature_definitions() -> Dict[str, Any]:
    """
    Gibt alle Feature-Definitionen zurück.
    
    Nützlich für:
    - Frontend-Darstellung
    - Tooltip-Inhalte
    - WCAG-Referenzen
    """
    definitions = {}
    
    for feature_id, feature_def in feature_engine.features.items():
        definitions[feature_id.value] = {
            "id": feature_def.id.value,
            "title": feature_def.title,
            "description": feature_def.description,
            "wcag_criteria": [
                {"id": c.id, "name": c.name, "level": c.level, "url": c.url}
                for c in feature_def.wcag_criteria
            ],
            "legal_refs": feature_def.legal_refs,
            "auto_fix_level": feature_def.auto_fix_level.value,
            "difficulty": feature_def.difficulty.value,
            "fix_types": [ft.value for ft in feature_def.fix_types],
            "risk_euro_base": feature_def.risk_euro_base
        }
    
    return {"features": definitions}


@accessibility_fix_router.get("/summary/{site_id}")
async def get_fix_summary(
    site_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Gibt die Fix-Zusammenfassung für eine Website zurück.
    
    Lädt gespeicherte Fix-Pakete aus der Datenbank.
    """
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT fix_package, created_at, updated_at
                FROM accessibility_fix_packages
                WHERE site_id = $1 AND user_id = $2
                ORDER BY created_at DESC
                LIMIT 1
            """, site_id, user.get('user_id'))
            
            if not row:
                return {"found": False, "message": "Keine Fixes gefunden"}
            
            return {
                "found": True,
                "fix_package": row['fix_package'],
                "created_at": row['created_at'].isoformat(),
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
            }
    
    except Exception as e:
        logger.error(f"❌ Failed to get fix summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Background Tasks
# =============================================================================

async def save_fix_package_to_db(user_id: str, site_url: str, fix_package: Dict[str, Any]):
    """Speichert Fix-Paket in der Datenbank"""
    if not db_pool:
        logger.warning("Database not available, skipping save")
        return
    
    site_id = site_url.replace('https://', '').replace('http://', '')
    site_id = site_id.replace('/', '-').replace('.', '-')[:50]
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO accessibility_fix_packages (user_id, site_id, site_url, fix_package, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (user_id, site_id) 
                DO UPDATE SET fix_package = $4, updated_at = NOW()
            """, user_id, site_id, site_url, fix_package)
        
        logger.info(f"✅ Fix package saved for {site_url}")
    
    except Exception as e:
        logger.error(f"❌ Failed to save fix package: {e}")


# =============================================================================
# Init Functions
# =============================================================================

def init_routes(pool, auth_svc, database_service=None):
    """Initialize route dependencies"""
    global db_pool, auth_service, db_service
    db_pool = pool
    auth_service = auth_svc
    db_service = database_service
    logger.info("✅ Accessibility fix routes initialized")

