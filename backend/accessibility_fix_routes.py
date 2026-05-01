"""
BFSG Accessibility Fix API Routes
Anfängerfreundliche Fix-Pipeline für Barrierefreiheit

Endpoints:
- POST /api/v2/accessibility/analyze - Issues kategorisieren
- POST /api/v2/accessibility/generate-fixes - Fixes generieren
- GET /api/v2/accessibility/download-bundle - Fix-Bundle herunterladen
- POST /api/v2/accessibility/generate-alt-text - Einzelnen Alt-Text generieren
- POST /api/v2/accessibility/generate-statement - BFSG Barrierefreiheitserklärung generieren (AUDIT-05)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import io
from datetime import datetime
from jinja2 import Environment, select_autoescape

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
# BFSG Accessibility Statement Generator (AUDIT-05)
# =============================================================================

_statement_jinja_env = Environment(autoescape=select_autoescape(['html']))

STATEMENT_TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Barrierefreiheitserklärung - {{ site_url }}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.6; padding: 0 1rem; }
    h1 { border-bottom: 2px solid #1e40af; padding-bottom: 0.5rem; color: #1e40af; }
    h2 { color: #1e3a8a; margin-top: 1.5rem; }
    ul { padding-left: 1.5rem; }
    a { color: #1e40af; }
    @media print { body { margin: 1rem; max-width: none; } a { color: #000; } }
  </style>
</head>
<body>
  <h1>Barrierefreiheitserklärung</h1>

  <h2>Geltungsbereich</h2>
  <p>Diese Erklärung gilt für die Website <strong>{{ site_url }}</strong>.</p>

  <h2>Stand der Vereinbarkeit mit den Anforderungen</h2>
  <p>{{ conformity_text }}</p>

  <h2>Nicht barrierefreie Inhalte</h2>
  {% if known_issues %}
  <p>Die folgenden Inhalte sind aus den nachstehenden Gründen nicht barrierefrei:</p>
  <ul>
    {% for issue in known_issues %}<li>{{ issue }}</li>{% endfor %}
  </ul>
  {% else %}
  <p>Es sind aktuell keine nicht barrierefreien Inhalte bekannt.</p>
  {% endif %}

  <h2>Kontakt und Feedback-Mechanismus</h2>
  <p>Sollten Ihnen Mängel beim barrierefreien Zugang zu Inhalten auffallen, kontaktieren Sie uns bitte:</p>
  <p>E-Mail: <a href="mailto:{{ contact_email }}">{{ contact_email }}</a></p>

  <h2>Durchsetzungsverfahren</h2>
  <p>Sollten auch nach Ihrem Feedback an uns keine zufriedenstellende Lösung gefunden worden sein, können Sie sich an die Schlichtungsstelle nach dem Behindertengleichstellungsgesetz wenden:</p>
  <p><a href="https://www.schlichtungsstelle-bfsg.de/">https://www.schlichtungsstelle-bfsg.de/</a></p>

  <p><small>Diese Erklärung wurde am {{ generated_date }} erstellt. Letzte Überprüfung: {{ review_date }}.</small></p>
</body>
</html>"""


class GenerateStatementRequest(BaseModel):
    """Request für BFSG Barrierefreiheitserklärung-Generator"""
    site_id: str = Field(..., description="Site-ID des Scans (z.B. 'example-de')")
    site_url: Optional[str] = Field(None, description="URL der Website (Anzeige)")
    contact_email: Optional[str] = Field(None, description="Kontakt-Email für Feedback")
    review_date: Optional[str] = Field(None, description="Datum der Überprüfung (DD.MM.YYYY oder YYYY-MM-DD)")


class GenerateStatementResponse(BaseModel):
    """Response des Barrierefreiheitserklärung-Generators"""
    html: str
    markdown: str
    filename: str = "barrierefreiheitserklaerung.html"


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


@accessibility_fix_router.post("/generate-statement", response_model=GenerateStatementResponse)
async def generate_statement(
    request: GenerateStatementRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> GenerateStatementResponse:
    """Generate BFSG-compliant Barrierefreiheitserklärung (AUDIT-05).

    Pulls scan results from accessibility_fix_packages (column: fix_package, key: site_id),
    renders Jinja2 HTML template with all 6 BFSG required fields, and returns html + markdown.
    """
    await require_accessibility_module(user)
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")

    # Defaults (used when no scan data exists)
    conformity_text = "Konformitätsstatus: Nicht bewertet — bisher wurde keine Barrierefreiheits-Prüfung durchgeführt."
    known_issues: List[str] = []
    display_url = request.site_url or request.site_id

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT fix_package, site_url, created_at
            FROM accessibility_fix_packages
            WHERE site_id = $1 AND user_id = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            request.site_id,
            str(user.get("user_id")),
        )

    if row:
        display_url = row.get("site_url") or display_url
        package = row.get("fix_package") or {}
        summary = package.get("summary", {}) if isinstance(package, dict) else {}
        total = int(summary.get("total_issues", 0) or 0)
        if total == 0:
            conformity_text = "Diese Website ist vollständig konform mit WCAG 2.1 Level AA / EN 301 549."
        else:
            conformity_text = (
                f"Diese Website ist teilweise konform mit WCAG 2.1 Level AA / EN 301 549. "
                f"Es sind {total} bekannte Abweichungen dokumentiert."
            )

        # Collect up to 10 issue descriptions from widget_fixes + code_patches + manual_guides
        collected: List[str] = []
        for bucket in ("widget_fixes", "code_patches", "manual_guides"):
            for entry in (package.get(bucket) or []):
                desc = (entry or {}).get("description")
                if desc:
                    collected.append(desc)
                if len(collected) >= 10:
                    break
            if len(collected) >= 10:
                break
        known_issues = collected[:10]

    template = _statement_jinja_env.from_string(STATEMENT_TEMPLATE_HTML)
    html_out = template.render(
        site_url=display_url,
        conformity_text=conformity_text,
        known_issues=known_issues,
        contact_email=request.contact_email or "info@ihre-domain.de",
        review_date=request.review_date or datetime.now().strftime("%d.%m.%Y"),
        generated_date=datetime.now().strftime("%d.%m.%Y"),
    )

    # Markdown variant (simple, no library)
    md_lines = [
        "# Barrierefreiheitserklärung",
        "",
        "## Geltungsbereich",
        f"Diese Erklärung gilt für die Website **{display_url}**.",
        "",
        "## Stand der Vereinbarkeit",
        conformity_text,
        "",
        "## Nicht barrierefreie Inhalte",
    ]
    if known_issues:
        md_lines.extend(f"- {i}" for i in known_issues)
    else:
        md_lines.append("Es sind aktuell keine nicht barrierefreien Inhalte bekannt.")
    md_lines.extend([
        "",
        "## Kontakt und Feedback",
        f"E-Mail: {request.contact_email or 'info@ihre-domain.de'}",
        "",
        "## Durchsetzungsverfahren",
        "Schlichtungsstelle BFSG: https://www.schlichtungsstelle-bfsg.de/",
        "",
        f"_Erstellt am {datetime.now().strftime('%d.%m.%Y')}. Letzte Überprüfung: {request.review_date or datetime.now().strftime('%d.%m.%Y')}._",
    ])
    markdown_out = "\n".join(md_lines)

    return GenerateStatementResponse(
        html=html_out,
        markdown=markdown_out,
        filename="barrierefreiheitserklaerung.html",
    )


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

