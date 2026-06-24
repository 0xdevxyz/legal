"""
Cookie Compliance Routes
API endpoints for Cookie-Consent-Management
"""

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import asyncpg
import hashlib
import re
from datetime import datetime, date
import json
import logging
from fastapi.responses import StreamingResponse
import io
import csv
from cookie_scanner_service import cookie_scanner
from file_storage_service import file_storage
from agency_report_generator import AgencyReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)  # auto_error=False für optionale Auth

# Global database pool and auth service (set by main.py)
db_pool = None
auth_service = None  # Wird von main_production.py gesetzt
db_service = None  # Wird von main_production.py gesetzt für Modul-Checks
redis_client = None  # Wird von main_production.py gesetzt für Rate-Limiting

# ============================================================================
# Authentication Helpers
# ============================================================================

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return user data (optional - returns None if no auth)"""
    if not credentials:
        return None
    
    try:
        if not auth_service:
            logger.warning("Auth service not configured")
            return None
            
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            return None
        
        logger.info(f"User authenticated: {user_data.get('user_id') or user_data.get('id')}")
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return None

async def get_current_user_required(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user data (required - raises 401 if no auth)"""
    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_module(user: Dict[str, Any], module_id: str) -> bool:
    """
    Check if user has access to a specific module.
    Raises 403 if module not granted.
    """
    if not db_service:
        logger.warning("Database service not configured for module checks")
        return True
    
    user_id = str(user.get("id") or user.get("user_id"))
    has_module = await db_service.check_user_module(user_id, module_id)
    
    if not has_module:
        module_names = {
            'cookie': 'Cookie & DSGVO',
            'accessibility': 'Barrierefreiheit',
            'legal_texts': 'Rechtliche Texte',
            'monitoring': 'Monitoring & Scan'
        }
        module_name = module_names.get(module_id, module_id)
        raise HTTPException(
            status_code=403, 
            detail=f"Modul '{module_name}' nicht gebucht. Bitte upgraden Sie Ihren Plan."
        )
    
    return True

async def get_user_id_from_token(user: Dict[str, Any]) -> Any:
    """Extract user_id from token and verify in database"""
    user_id_from_token = user.get("id") or user.get("user_id")
    
    if not user_id_from_token:
        logger.error(f"No user_id in token: {user}")
        raise HTTPException(status_code=403, detail="User ID not found in token")
    
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        db_user = await conn.fetchrow(
            "SELECT id FROM users WHERE id::text = $1 OR email = $2 LIMIT 1",
            str(user_id_from_token),
            user.get("email", "")
        )
        
        if not db_user:
            logger.error(f"User not found in database for token: {user_id_from_token}")
            raise HTTPException(status_code=403, detail="User not found in database")
        
        return db_user["id"]

async def get_user_website_site_id(user_id: Any) -> Optional[str]:
    """Get the site_id for the user's primary website"""
    if not db_pool:
        return None
    
    async with db_pool.acquire() as conn:
        # Hole die primäre Website des Users
        website = await conn.fetchrow("""
            SELECT url FROM tracked_websites 
            WHERE user_id = $1 AND is_primary = TRUE
            LIMIT 1
        """, user_id)
        
        if website:
            # Generiere site_id aus URL
            from urllib.parse import urlparse
            parsed = urlparse(website['url'])
            hostname = parsed.netloc or parsed.path
            hostname = hostname.replace('www.', '')
            site_id = hostname.replace('.', '-').lower()
            return site_id
        
        return None

# ============================================================================
# Pydantic Models
# ============================================================================

class ConsentCategories(BaseModel):
    necessary: bool = True
    functional: bool = False
    analytics: bool = False
    marketing: bool = False

class ConsentLog(BaseModel):
    site_id: str = Field(..., min_length=1, max_length=255)
    visitor_id: str = Field(..., min_length=1, max_length=255)
    consent_categories: ConsentCategories
    services_accepted: Optional[List[str]] = []
    language: str = Field(default="de", max_length=10)
    banner_shown: bool = True
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None  # Will be hashed
    device_fingerprint: Optional[str] = None  # Privacy-friendly alternative to IP

    @validator('site_id', 'visitor_id')
    def validate_ids(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('ID cannot be empty')
        return v.strip()

class BannerTexts(BaseModel):
    # Alle Felder optional + extra erlaubt: Der Banner-Text wird je nach
    # Sprache/Scan mit unterschiedlichen Schluesseln gespeichert (z.B.
    # privacy_link/imprint_link statt privacy_policy/imprint, plus Kategorie-
    # Texte analytics/marketing/...). Ein strenges Schema fuehrte dazu, dass
    # jeder erneute Speichern-Vorgang mit HTTP 422 abgewiesen wurde und z.B.
    # Layout-/Positionsaenderungen nie persistiert wurden. Texte sind reine
    # Anzeige-Strings — sie duerfen die Speicherung niemals blockieren.
    title: Optional[str] = ""
    description: Optional[str] = ""
    accept_all: Optional[str] = ""
    reject_all: Optional[str] = ""
    accept_selected: Optional[str] = ""
    settings: Optional[str] = ""
    privacy_policy: Optional[str] = ""
    imprint: Optional[str] = ""

    class Config:
        extra = "allow"

class BannerConfig(BaseModel):
    site_id: str = Field(..., min_length=1, max_length=255)
    layout: str = Field(default="banner_bottom")
    primary_color: str = Field(default="#6366f1")
    accent_color: str = Field(default="#8b5cf6")
    text_color: str = Field(default="#333333")
    bg_color: str = Field(default="#ffffff")
    button_style: str = Field(default="rounded")
    position: str = Field(default="bottom")
    width_mode: str = Field(default="full")
    texts: Dict[str, BannerTexts]
    services: List[str] = []
    show_on_pages: Dict[str, Any] = {"all": True, "exclude": []}
    geo_restriction: Dict[str, Any] = {"enabled": False, "countries": []}
    auto_block_scripts: bool = True
    respect_dnt: bool = True
    cookie_lifetime_days: int = 365
    show_branding: bool = True
    custom_logo_url: Optional[str] = None
    consent_mode_enabled: Optional[bool] = True
    gtm_container_id: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    cookie_policy_url: Optional[str] = None
    imprint_url: Optional[str] = None

    class Config:
        extra = "allow"

class BannerConfigUpdate(BaseModel):
    layout: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    text_color: Optional[str] = None
    bg_color: Optional[str] = None
    button_style: Optional[str] = None
    position: Optional[str] = None
    width_mode: Optional[str] = None
    texts: Optional[Dict[str, Dict[str, str]]] = None
    services: Optional[List[str]] = None
    show_on_pages: Optional[Dict[str, Any]] = None
    geo_restriction: Optional[Dict[str, Any]] = None
    auto_block_scripts: Optional[bool] = None
    respect_dnt: Optional[bool] = None
    cookie_lifetime_days: Optional[int] = None
    show_branding: Optional[bool] = None
    custom_logo_url: Optional[str] = None

class ServiceTemplate(BaseModel):
    service_key: str
    name: str
    category: str
    provider: Optional[str] = None
    template: Dict[str, Any]
    plan_required: str = "ai"

class ClientAssignRequest(BaseModel):
    client_name: Optional[str] = Field(None, max_length=255)
    client_email: Optional[str] = Field(None, max_length=255)

class CustomServiceInput(BaseModel):
    """Customer-defined cookie service (Borlabs-style custom cookies)."""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="functional", max_length=50)
    provider: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    domains: List[str] = []
    cookies: List[str] = []
    legal_basis: Optional[str] = None
    privacy_url: Optional[str] = None
    cookie_lifetime: Optional[str] = Field(None, max_length=100)

    @validator('category')
    def validate_category(cls, v):
        allowed = {'necessary', 'functional', 'analytics', 'marketing'}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v

    @validator('domains', 'cookies', pre=True)
    def clean_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        return [str(x).strip() for x in v if str(x).strip()]

# ============================================================================
# Helper Functions
# ============================================================================

def _as_list(val) -> List[str]:
    """Normalize a JSONB column (str or list) into a list of strings."""
    if val is None:
        return []
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except Exception:
            return [val] if val.strip() else []
    if isinstance(val, list):
        return [str(x) for x in val]
    return []

def hash_ip_address(ip: str) -> str:
    """Hash IP address with SHA256 for privacy"""
    if not ip:
        return ""
    return hashlib.sha256(ip.encode()).hexdigest()


def truncate_user_agent(ua_string):
    """DSGVO-compliant UA truncation to browser family + major version.
    Returns 'Browser/Version' (e.g. 'Chrome/120') or 'unknown' on no match.
    Priority order: more-specific browsers (Edge/Edg, OPR, CriOS, FxiOS,
    SamsungBrowser, UCBrowser, MSIE/Trident) MUST win over Chrome/Safari
    because Chrome UAs contain 'Safari/' and Edge UAs contain 'Chrome/'.
    We collect all matches then select by priority rank.
    AUDIT-03 — Phase 1, v2.0 milestone.
    """
    if not ua_string:
        return "unknown"
    # Priority list: index 0 = highest priority
    priority = [
        "Edge", "Edg", "OPR", "CriOS", "FxiOS",
        "SamsungBrowser", "UCBrowser", "MSIE", "Trident",
        "Firefox", "Opera", "Chrome", "Safari",
    ]
    pattern = re.compile(
        r'(Edge|Edg|OPR|CriOS|FxiOS|SamsungBrowser|UCBrowser|MSIE|Trident|Chrome|Firefox|Safari|Opera)[\/ ](\d+)'
    )
    matches = pattern.findall(ua_string)
    if not matches:
        return "unknown"
    # Select the match with the highest priority rank
    best = min(matches, key=lambda m: priority.index(m[0]) if m[0] in priority else 99)
    browser = best[0]
    if browser == "Edg":
        browser = "Edge"
    elif browser in ("Trident", "MSIE"):
        browser = "IE"
    return f"{browser}/{best[1]}"


def get_client_ip(request: Request) -> Optional[str]:
    """Get client IP from request headers"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None

async def get_db_connection():
    """Get database connection from app state"""
    global db_pool
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_pool

# ============================================================================
# Consent Logging Endpoints
# ============================================================================

@router.post("/api/cookie-compliance/consent")
async def log_consent(
    consent: ConsentLog,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Log cookie consent decision (DSGVO-compliant)
    
    - Pseudonymizes visitor_id
    - Hashes IP address
    - Stores consent categories & services
    - Auto-expires after 3 years
    """
    try:
        # AUDIT-19: Rate-Limiting (max 100 Consent-Logs/Minute pro Site-ID)
        if not await check_rate_limit(consent.site_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded: max 100 consents per minute per site")

        # Get IP and hash it
        ip_address = consent.ip_address or get_client_ip(request)
        ip_hash = hash_ip_address(ip_address) if ip_address else None
        
        # Get user agent (AUDIT-03: DSGVO-compliant truncation)
        raw_ua = consent.user_agent or request.headers.get("User-Agent", "")
        user_agent = truncate_user_agent(raw_ua)  # AUDIT-03: DSGVO-compliant truncation
        
        # Get banner config ID (instead of revision)
        config_query = """
            SELECT id FROM cookie_banner_configs 
            WHERE site_id = $1
        """
        config_row = await db_pool.fetchrow(config_query, consent.site_id)
        revision_id = config_row['id'] if config_row else 1
        
        # Insert consent log (with optional device fingerprint as IP alternative)
        insert_query = """
            INSERT INTO cookie_consent_logs (
                site_id, visitor_id, consent_categories, services_accepted,
                ip_address_hash, device_fingerprint, user_agent, revision_id, language, banner_shown
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, timestamp
        """
        
        # Use device fingerprint if provided, otherwise fall back to IP hash
        device_fp = consent.device_fingerprint if consent.device_fingerprint else None
        
        result = await db_pool.fetchrow(
            insert_query,
            consent.site_id,
            consent.visitor_id,
            json.dumps(consent.consent_categories.dict()),
            json.dumps(consent.services_accepted) if consent.services_accepted else None,
            ip_hash,
            device_fp,
            user_agent,
            revision_id,
            consent.language,
            consent.banner_shown
        )
        
        # Update statistics (upsert)
        today = date.today()
        stats_query = """
            INSERT INTO cookie_compliance_stats (
                site_id, date, total_impressions,
                accepted_all, accepted_partial, rejected_all,
                accepted_analytics, accepted_marketing, accepted_functional
            )
            VALUES ($1, $2, 1, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (site_id, date) DO UPDATE SET
                total_impressions = cookie_compliance_stats.total_impressions + 1,
                accepted_all = cookie_compliance_stats.accepted_all + EXCLUDED.accepted_all,
                accepted_partial = cookie_compliance_stats.accepted_partial + EXCLUDED.accepted_partial,
                rejected_all = cookie_compliance_stats.rejected_all + EXCLUDED.rejected_all,
                accepted_analytics = cookie_compliance_stats.accepted_analytics + EXCLUDED.accepted_analytics,
                accepted_marketing = cookie_compliance_stats.accepted_marketing + EXCLUDED.accepted_marketing,
                accepted_functional = cookie_compliance_stats.accepted_functional + EXCLUDED.accepted_functional,
                updated_at = NOW()
        """
        
        # Determine consent type
        categories = consent.consent_categories
        all_accepted = categories.analytics and categories.marketing and categories.functional
        rejected = not (categories.analytics or categories.marketing or categories.functional)
        partial = not all_accepted and not rejected
        
        await db_pool.execute(
            stats_query,
            consent.site_id,
            today,
            1 if all_accepted else 0,
            1 if partial else 0,
            1 if rejected else 0,
            1 if categories.analytics else 0,
            1 if categories.marketing else 0,
            1 if categories.functional else 0
        )
        
        return {
            "success": True,
            "consent_id": result['id'],
            "timestamp": result['timestamp'].isoformat(),
            "message": "Consent logged successfully"
        }
        
    except Exception as e:
        print(f"Error logging consent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log consent: {str(e)}")

# ============================================================================
# Banner Configuration Endpoints
# ============================================================================

@router.get("/api/cookie-compliance/my-config")
async def get_my_config(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get the user's existing cookie banner configuration.
    
    WICHTIG: 1 Account = 1 Website!
    Jeder User kann nur EINE Website mit Cookie-Banner absichern.
    
    Returns:
    - has_config: true wenn bereits konfiguriert
    - data: bestehende Config oder null
    """
    try:
        # Authentifizierung
        user = await get_current_user_required(credentials)
        user_id = await get_user_id_from_token(user)
        
        # Hole auch die site_id der registrierten Website
        registered_site_id = await get_user_website_site_id(user_id)
        
        query = """
            SELECT 
                id, site_id, user_id,
                layout, primary_color, accent_color, text_color, bg_color,
                button_style, position, width_mode,
                texts, services, show_on_pages, geo_restriction,
                auto_block_scripts, respect_dnt, cookie_lifetime_days,
                show_branding, custom_logo_url,
                is_active, created_at, updated_at,
                scan_completed_at, last_scan_url
            FROM cookie_banner_configs
            WHERE user_id = $1 AND is_active = true
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        row = await db_pool.fetchrow(query, user_id)
        
        if not row:
            # ✅ Verwaiste Config (user_id IS NULL) beanspruchen, falls eine zur
            #    registrierten Website passende Zeile existiert (z.B. durch einen
            #    früheren Scan ohne user_id). Verhindert die Ersteinrichtungs-Schleife.
            if registered_site_id:
                claimed = await db_pool.execute("""
                    UPDATE cookie_banner_configs
                    SET user_id = $1, updated_at = NOW()
                    WHERE site_id = $2 AND user_id IS NULL
                """, user_id, registered_site_id)
                if claimed and claimed != "UPDATE 0":
                    logger.info(f"Claimed orphaned config {registered_site_id} for user {user_id}")
                    row = await db_pool.fetchrow(query, user_id)

            # ✅ Wenn registered_site_id existiert, erstelle automatisch eine Config
            if not row and registered_site_id:
                logger.info(f"Creating default config for site_id: {registered_site_id}")
                
                # Hole die Website-URL
                website_url = await db_pool.fetchval("""
                    SELECT url FROM tracked_websites 
                    WHERE user_id = $1 AND is_primary = TRUE
                    LIMIT 1
                """, user_id)
                
                default_texts = {
                    "de": {
                        "title": "Datenschutz-Präferenz",
                        "description": "Wir benötigen Ihre Einwilligung, bevor Sie unsere Website weiter besuchen können.\n\nWenn Sie unter 16 Jahre alt sind und Ihre Einwilligung zu optionalen Services geben möchten, müssen Sie Ihre Erziehungsberechtigten um Erlaubnis bitten.\n\nWir verwenden Cookies und andere Technologien auf unserer Website. Einige von ihnen sind essenziell, während andere uns helfen, diese Website und Ihre Erfahrung zu verbessern.",
                        "accept_all": "Alle akzeptieren",
                        "reject_all": "Nur essenzielle Cookies akzeptieren",
                        "accept_selected": "Speichern",
                        "settings": "Individuelle Datenschutzeinstellungen",
                        "necessary": "Essenziell",
                        "necessaryDesc": "Essenzielle Services ermöglichen grundlegende Funktionen.",
                        "functional": "Funktional",
                        "functionalDesc": "Funktionale Cookies speichern Ihre Präferenzen.",
                        "analytics": "Statistiken",
                        "analyticsDesc": "Statistik-Cookies helfen uns zu verstehen, wie Besucher interagieren.",
                        "marketing": "Externe Medien",
                        "marketingDesc": "Inhalte von Videoplattformen und Social-Media werden standardmäßig blockiert.",
                        "privacy_link": "Datenschutzerklärung",
                        "imprint_link": "Impressum"
                    }
                }
                
                # Erstelle die Config
                await db_pool.execute("""
                    INSERT INTO cookie_banner_configs (
                        site_id, user_id, layout, primary_color, accent_color,
                        text_color, bg_color, button_style, position, width_mode,
                        texts, services, show_on_pages, geo_restriction,
                        auto_block_scripts, respect_dnt, cookie_lifetime_days,
                        show_branding, is_active, last_scan_url
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ON CONFLICT (site_id) DO NOTHING
                """,
                    registered_site_id,
                    user_id,
                    'box_modal',
                    '#7c3aed',
                    '#8b5cf6',
                    '#333333',
                    '#ffffff',
                    'rounded',
                    'center',
                    'boxed',
                    json.dumps(default_texts),
                    json.dumps([]),
                    json.dumps({"all": True, "exclude": []}),
                    json.dumps({"enabled": False, "countries": []}),
                    True,
                    True,
                    365,
                    True,
                    True,
                    website_url
                )
                
                # Lade die neu erstellte Config
                row = await db_pool.fetchrow(query, user_id)
            
            if not row:
                return {
                    "success": True,
                    "has_config": False,
                    "data": None,
                    "registered_site_id": registered_site_id,
                    "message": "Keine Konfiguration gefunden - bitte zuerst eine Website registrieren"
                }
        
        config = dict(row)
        
        # Parse JSON fields
        if isinstance(config.get('texts'), str):
            config['texts'] = json.loads(config['texts'])
        if isinstance(config.get('services'), str):
            config['services'] = json.loads(config['services'])
        if isinstance(config.get('show_on_pages'), str):
            config['show_on_pages'] = json.loads(config['show_on_pages'])
        if isinstance(config.get('geo_restriction'), str):
            config['geo_restriction'] = json.loads(config['geo_restriction'])
        
        config['scan_completed'] = config.get('scan_completed_at') is not None
        
        # Convert datetime to ISO string
        for field in ['scan_completed_at', 'created_at', 'updated_at']:
            if config.get(field):
                config[field] = config[field].isoformat()
        
        return {
            "success": True,
            "has_config": True,
            "data": config,
            "registered_site_id": registered_site_id,  # Site-ID der registrierten Website
            "message": "Konfiguration gefunden - 1 Website bereits registriert"
        }
        
    except Exception as e:
        logger.error(f"Error in get_my_config (user lookup/db): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {type(e).__name__}: {str(e)[:200]}")


@router.get("/api/cookie-compliance/config/{site_id}")
async def get_banner_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get cookie banner configuration for a site
    
    Returns complete banner configuration including:
    - Design settings (colors, layout)
    - Texts (multi-language)
    - Active services
    - Advanced settings
    """
    try:
        query = """
            SELECT 
                id, site_id, user_id,
                layout, primary_color, accent_color, text_color, bg_color,
                button_style, position, width_mode,
                texts, services, show_on_pages, geo_restriction,
                auto_block_scripts, respect_dnt, cookie_lifetime_days,
                show_branding, custom_logo_url,
                is_active, created_at, updated_at,
                scan_completed_at, last_scan_url
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        
        row = await db_pool.fetchrow(query, site_id)
        
        if not row:
            # Return default configuration - OHNE scan_completed
            default_description = """Wir benötigen Ihre Einwilligung, bevor Sie unsere Website weiter besuchen können.

Wenn Sie unter 16 Jahre alt sind und Ihre Einwilligung zu optionalen Services geben möchten, müssen Sie Ihre Erziehungsberechtigten um Erlaubnis bitten.

Wir verwenden Cookies und andere Technologien auf unserer Website. Einige von ihnen sind essenziell, während andere uns helfen, diese Website und Ihre Erfahrung zu verbessern. Personenbezogene Daten können verarbeitet werden (z. B. IP-Adressen), z. B. für personalisierte Anzeigen und Inhalte oder die Messung von Anzeigen und Inhalten. Weitere Informationen über die Verwendung Ihrer Daten finden Sie in unserer Datenschutzerklärung. Es besteht keine Verpflichtung, in die Verarbeitung Ihrer Daten einzuwilligen, um dieses Angebot zu nutzen. Sie können Ihre Auswahl jederzeit unter Einstellungen widerrufen oder anpassen. Bitte beachten Sie, dass aufgrund individueller Einstellungen möglicherweise nicht alle Funktionen der Website verfügbar sind.

Einige Services verarbeiten personenbezogene Daten in den USA. Mit Ihrer Einwilligung zur Nutzung dieser Services willigen Sie auch in die Verarbeitung Ihrer Daten in den USA gemäß Art. 49 (1) lit. a DSGVO ein. Der EuGH stuft die USA als ein Land mit unzureichendem Datenschutz nach EU-Standards ein. Es besteht beispielsweise die Gefahr, dass US-Behörden personenbezogene Daten in Überwachungsprogrammen verarbeiten, ohne dass für Europäerinnen und Europäer eine Klagemöglichkeit besteht."""

            return {
                "success": True,
                "data": {
                    "site_id": site_id,
                    "layout": "banner_bottom",
                    "primary_color": "#6366f1",
                    "accent_color": "#8b5cf6",
                    "text_color": "#333333",
                    "bg_color": "#ffffff",
                    "button_style": "rounded",
                    "position": "bottom",
                    "width_mode": "full",
                    "texts": {
                        "de": {
                            "title": "Datenschutz-Präferenz",
                            "description": default_description,
                            "accept_all": "Alle akzeptieren",
                            "reject_all": "Nur essenzielle Cookies akzeptieren",
                            "accept_selected": "Speichern",
                            "settings": "Individuelle Datenschutzeinstellungen",
                            "necessary": "Essenziell",
                            "necessaryDesc": "Essenzielle Services ermöglichen grundlegende Funktionen und sind für das ordnungsgemäße Funktionieren der Website erforderlich.",
                            "functional": "Funktional",
                            "functionalDesc": "Funktionale Cookies speichern Ihre Präferenzen wie Sprache und Region für ein verbessertes Nutzungserlebnis.",
                            "analytics": "Statistiken",
                            "analyticsDesc": "Statistik-Cookies helfen Webseiten-Besitzern zu verstehen, wie Besucher mit Webseiten interagieren, indem Informationen anonym gesammelt und gemeldet werden.",
                            "marketing": "Externe Medien",
                            "marketingDesc": "Inhalte von Videoplattformen und Social-Media-Plattformen werden standardmäßig blockiert. Wenn externe Services akzeptiert werden, ist für den Zugriff auf diese Inhalte keine manuelle Einwilligung mehr erforderlich.",
                            "privacy_link": "Datenschutzerklärung",
                            "imprint_link": "Impressum"
                        }
                    },
                    "services": [],
                    "show_on_pages": {"all": True, "exclude": []},
                    "geo_restriction": {"enabled": False, "countries": []},
                    "auto_block_scripts": True,
                    "respect_dnt": True,
                    "cookie_lifetime_days": 365,
                    "show_branding": True,
                    "custom_logo_url": None,
                    "revision": 1,
                    "is_active": False,  # ✅ FIX: Default ist FALSE - Banner nur zeigen wenn im Backend konfiguriert!
                    "scan_completed": False,
                    "scan_completed_at": None,
                    "last_scan_url": None
                },
                "message": "Default configuration - no banner configured yet"
            }
        
        # Convert row to dict and parse JSON fields
        config = dict(row)
        
        # Parse JSONB fields if they are strings
        if isinstance(config.get('texts'), str):
            config['texts'] = json.loads(config['texts'])
        if isinstance(config.get('services'), str):
            config['services'] = json.loads(config['services'])
        if isinstance(config.get('show_on_pages'), str):
            config['show_on_pages'] = json.loads(config['show_on_pages'])
        if isinstance(config.get('geo_restriction'), str):
            config['geo_restriction'] = json.loads(config['geo_restriction'])
        
        # ✅ Füge scan_completed Status hinzu
        config['scan_completed'] = config.get('scan_completed_at') is not None

        # Convert datetime to ISO string
        if config.get('scan_completed_at'):
            config['scan_completed_at'] = config['scan_completed_at'].isoformat()
        if config.get('created_at'):
            config['created_at'] = config['created_at'].isoformat()
        if config.get('updated_at'):
            config['updated_at'] = config['updated_at'].isoformat()

        # 🔒 Laufzeit-Lizenzprüfung: Wurde die Website im Dashboard entfernt,
        # signalisiert license_active=false → der Banner zeigt einen Hinweis
        # statt zu funktionieren (Anti-Missbrauch gegen optimieren+löschen).
        from license_check import site_has_active_license
        config['license_active'] = await site_has_active_license(db_pool, site_id)

        return {
            "success": True,
            "data": config
        }
        
    except Exception as e:
        print(f"Error getting banner config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

@router.post("/api/cookie-compliance/config")
async def create_or_update_config(
    config: BannerConfig,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Create or update cookie banner configuration
    
    Requires authentication (user_id from session)
    Requires 'cookie' module to be active
    """
    try:
        # Authentifizierung
        user = await get_current_user_required(credentials)
        user_id = await get_user_id_from_token(user)
        
        # Modul-Check: User muss Cookie-Modul gebucht haben
        await require_module(user, 'cookie')
        
        # Prüfe, ob die site_id zur registrierten Website des Users gehört
        registered_site_id = await get_user_website_site_id(user_id)
        
        if registered_site_id and config.site_id != registered_site_id:
            logger.warning(f"User {user_id} tried to configure site_id '{config.site_id}' but registered site is '{registered_site_id}'")
            # Verwende die registrierte site_id statt der übergebenen
            config.site_id = registered_site_id
        
        # Check if config exists
        check_query = "SELECT id FROM cookie_banner_configs WHERE site_id = $1"
        existing = await db_pool.fetchrow(check_query, config.site_id)
        
        if existing:
            # Update existing
            update_query = """
                UPDATE cookie_banner_configs SET
                    layout = $2, primary_color = $3, accent_color = $4,
                    text_color = $5, bg_color = $6, button_style = $7,
                    position = $8, width_mode = $9, texts = $10,
                    services = $11, show_on_pages = $12, geo_restriction = $13,
                    auto_block_scripts = $14, respect_dnt = $15,
                    cookie_lifetime_days = $16, show_branding = $17,
                    custom_logo_url = $18, updated_at = NOW()
                WHERE site_id = $1
                RETURNING id, revision
            """

            result = await db_pool.fetchrow(
                update_query,
                config.site_id,
                config.layout,
                config.primary_color,
                config.accent_color,
                config.text_color,
                config.bg_color,
                config.button_style,
                config.position,
                config.width_mode,
                json.dumps(config.texts),
                json.dumps(config.services),
                json.dumps(config.show_on_pages),
                json.dumps(config.geo_restriction),
                config.auto_block_scripts,
                config.respect_dnt,
                config.cookie_lifetime_days,
                config.show_branding,
                config.custom_logo_url
            )

            return {
                "success": True,
                "message": "Configuration updated",
                "config_id": result['id'],
                "revision": result['revision']
            }
        else:
            # Create new
            insert_query = """
                INSERT INTO cookie_banner_configs (
                    site_id, user_id, layout, primary_color, accent_color,
                    text_color, bg_color, button_style, position, width_mode,
                    texts, services, show_on_pages, geo_restriction,
                    auto_block_scripts, respect_dnt, cookie_lifetime_days,
                    show_branding, custom_logo_url
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                RETURNING id, revision
            """
            
            result = await db_pool.fetchrow(
                insert_query,
                config.site_id,
                user_id,
                config.layout,
                config.primary_color,
                config.accent_color,
                config.text_color,
                config.bg_color,
                config.button_style,
                config.position,
                config.width_mode,
                json.dumps(config.texts),
                json.dumps(config.services),
                json.dumps(config.show_on_pages),
                json.dumps(config.geo_restriction),
                config.auto_block_scripts,
                config.respect_dnt,
                config.cookie_lifetime_days,
                config.show_branding,
                config.custom_logo_url
            )
            
            return {
                "success": True,
                "message": "Configuration created",
                "config_id": result['id'],
                "revision": result['revision']
            }
        
    except Exception as e:
        print(f"Error saving banner config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

@router.patch("/api/cookie-compliance/config/{site_id}")
async def update_config_partial(
    site_id: str,
    updates: BannerConfigUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Partially update banner configuration
    
    Requires authentication - validates that site_id belongs to user
    Requires 'cookie' module to be active
    """
    try:
        # Authentifizierung
        user = await get_current_user_required(credentials)
        user_id = await get_user_id_from_token(user)
        
        # Modul-Check: User muss Cookie-Modul gebucht haben
        await require_module(user, 'cookie')
        
        # Prüfe, ob die site_id zur registrierten Website des Users gehört
        registered_site_id = await get_user_website_site_id(user_id)
        
        if registered_site_id and site_id != registered_site_id:
            raise HTTPException(
                status_code=403, 
                detail=f"Site {site_id} does not belong to this user"
            )
        # Build dynamic update query
        update_fields = []
        values = [site_id]
        param_idx = 2
        
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                if isinstance(value, (dict, list)):
                    update_fields.append(f"{field} = ${param_idx}::jsonb")
                    values.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = ${param_idx}")
                    values.append(value)
                param_idx += 1
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_query = f"""
            UPDATE cookie_banner_configs SET
                {', '.join(update_fields)},
                updated_at = NOW()
            WHERE site_id = $1
            RETURNING id
        """
        
        result = await db_pool.fetchrow(update_query, *values)
        
        if not result:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {
            "success": True,
            "message": "Configuration updated",
            "config_id": result['id'],
            "revision": result['revision']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update: {str(e)}")

# ============================================================================
# Service Templates Endpoints
# ============================================================================

@router.get("/api/cookie-compliance/services")
async def get_available_services(
    category: Optional[str] = None,
    plan: Optional[str] = None,
    site_id: Optional[str] = None,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get available cookie service templates

    Query params:
    - category: Filter by category (analytics, marketing, functional, necessary)
    - plan: Filter by required plan (ai, expert)
    - site_id: If given, the site's custom services are appended (is_custom=true)
    """
    try:
        query = """
            SELECT 
                id, service_key, name, category, provider,
                description, cookies, template, plan_required, is_active,
                created_at, updated_at, privacy_url,
                provider_address, provider_privacy_url, provider_cookie_url, provider_description
            FROM cookie_services
            WHERE is_active = true
        """
        
        params = []
        if category:
            query += f" AND category = ${len(params) + 1}"
            params.append(category)
        
        if plan:
            # Include services for this plan and lower
            if plan == "expert":
                query += " AND plan_required IN ('ai', 'expert')"
            else:
                query += f" AND plan_required = ${len(params) + 1}"
                params.append(plan)
        
        query += " ORDER BY category, name"
        
        rows = await db_pool.fetch(query, *params)

        services = [dict(row) for row in rows]

        # Append the site's custom services (shaped like catalogue rows).
        # Wrapped defensively so a missing table never breaks the catalogue.
        if site_id:
            try:
                custom_rows = await db_pool.fetch(
                    """
                    SELECT service_key, name, category, provider, description,
                           domains, cookies, legal_basis, privacy_url, cookie_lifetime
                    FROM cookie_custom_services
                    WHERE site_id = $1 AND is_active = true
                    ORDER BY category, name
                    """,
                    site_id,
                )
                for cr in custom_rows:
                    cr = dict(cr)
                    if category and cr['category'] != category:
                        continue
                    domains = _as_list(cr.get('domains'))
                    cookies = _as_list(cr.get('cookies'))
                    services.append({
                        "id": None,
                        "service_key": cr['service_key'],
                        "name": cr['name'],
                        "category": cr['category'],
                        "provider": cr.get('provider'),
                        "description": cr.get('description'),
                        "cookies": cookies,
                        "template": {
                            "id": cr['service_key'],
                            "name": cr['name'],
                            "category": cr['category'],
                            "domains": domains,
                            "cookies": cookies,
                            "legal_basis": cr.get('legal_basis'),
                            "privacy_policy_url": cr.get('privacy_url'),
                            "cookie_lifetime": cr.get('cookie_lifetime'),
                        },
                        "plan_required": "ai",
                        "is_active": True,
                        "privacy_url": cr.get('privacy_url'),
                        "is_custom": True,
                    })
            except Exception as ce:
                logger.warning(f"Custom services unavailable for {site_id}: {ce}")

        # Group by category
        grouped = {}
        for service in services:
            cat = service['category']
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(service)

        return {
            "success": True,
            "total": len(services),
            "services": services,
            "grouped": grouped
        }

    except Exception as e:
        print(f"Error getting services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")

@router.get("/api/cookie-compliance/services/{service_key}")
async def get_service_detail(
    service_key: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get detailed information about a specific service
    """
    try:
        query = """
            SELECT 
                id, service_key, name, category, provider,
                template, plan_required, is_active,
                created_at, updated_at
            FROM cookie_services
            WHERE service_key = $1 AND is_active = true
        """
        
        row = await db_pool.fetchrow(query, service_key)
        
        if not row:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return {
            "success": True,
            "data": dict(row)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")

# ============================================================================
# Custom Services Endpoints (kundeneigene Dienst-Definitionen)
# ============================================================================

def _slugify(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '_', (name or '').lower()).strip('_')
    return slug or 'service'

@router.get("/api/cookie-compliance/custom-services/{site_id}")
async def list_custom_services(
    site_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """List the site's custom service definitions."""
    user = await get_current_user_required(credentials)
    await require_module(user, 'cookie')
    try:
        rows = await db_pool.fetch(
            """
            SELECT service_key, name, category, provider, description,
                   domains, cookies, legal_basis, privacy_url, cookie_lifetime,
                   is_active, created_at, updated_at
            FROM cookie_custom_services
            WHERE site_id = $1
            ORDER BY category, name
            """,
            site_id,
        )
        data = []
        for r in rows:
            r = dict(r)
            r['domains'] = _as_list(r.get('domains'))
            r['cookies'] = _as_list(r.get('cookies'))
            data.append(r)
        return {"success": True, "total": len(data), "data": data}
    except asyncpg.UndefinedTableError:
        return {"success": True, "total": 0, "data": []}
    except Exception as e:
        logger.error(f"Error listing custom services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list custom services: {str(e)}")

@router.post("/api/cookie-compliance/custom-services/{site_id}")
async def create_custom_service(
    site_id: str,
    payload: CustomServiceInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Create a custom service for a site. service_key is derived from the name."""
    user = await get_current_user_required(credentials)
    await require_module(user, 'cookie')
    try:
        user_id = None
        try:
            user_id = await get_user_id_from_token(user)
        except Exception:
            pass

        base_key = f"custom_{_slugify(payload.name)}"
        # Ensure uniqueness within the site
        existing = await db_pool.fetch(
            "SELECT service_key FROM cookie_custom_services WHERE site_id = $1 AND service_key LIKE $2",
            site_id, base_key + '%',
        )
        existing_keys = {r['service_key'] for r in existing}
        service_key = base_key
        i = 2
        while service_key in existing_keys:
            service_key = f"{base_key}_{i}"
            i += 1

        row = await db_pool.fetchrow(
            """
            INSERT INTO cookie_custom_services
                (site_id, user_id, service_key, name, category, provider, description,
                 domains, cookies, legal_basis, privacy_url, cookie_lifetime)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb,$9::jsonb,$10,$11,$12)
            RETURNING service_key
            """,
            site_id, user_id, service_key, payload.name, payload.category,
            payload.provider, payload.description,
            json.dumps(payload.domains), json.dumps(payload.cookies),
            payload.legal_basis, payload.privacy_url, payload.cookie_lifetime,
        )
        return {"success": True, "service_key": row['service_key']}
    except asyncpg.UndefinedTableError:
        raise HTTPException(status_code=503, detail="Custom-Services-Tabelle noch nicht eingerichtet.")
    except Exception as e:
        logger.error(f"Error creating custom service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create custom service: {str(e)}")

@router.put("/api/cookie-compliance/custom-services/{site_id}/{service_key}")
async def update_custom_service(
    site_id: str,
    service_key: str,
    payload: CustomServiceInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Update an existing custom service."""
    user = await get_current_user_required(credentials)
    await require_module(user, 'cookie')
    try:
        result = await db_pool.execute(
            """
            UPDATE cookie_custom_services
            SET name=$3, category=$4, provider=$5, description=$6,
                domains=$7::jsonb, cookies=$8::jsonb, legal_basis=$9,
                privacy_url=$10, cookie_lifetime=$11, updated_at=now()
            WHERE site_id=$1 AND service_key=$2
            """,
            site_id, service_key, payload.name, payload.category, payload.provider,
            payload.description, json.dumps(payload.domains), json.dumps(payload.cookies),
            payload.legal_basis, payload.privacy_url, payload.cookie_lifetime,
        )
        if result.endswith('0'):
            raise HTTPException(status_code=404, detail="Custom service not found")
        return {"success": True, "service_key": service_key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating custom service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update custom service: {str(e)}")

@router.delete("/api/cookie-compliance/custom-services/{site_id}/{service_key}")
async def delete_custom_service(
    site_id: str,
    service_key: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Delete a custom service."""
    user = await get_current_user_required(credentials)
    await require_module(user, 'cookie')
    try:
        result = await db_pool.execute(
            "DELETE FROM cookie_custom_services WHERE site_id=$1 AND service_key=$2",
            site_id, service_key,
        )
        if result.endswith('0'):
            raise HTTPException(status_code=404, detail="Custom service not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting custom service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete custom service: {str(e)}")

# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/api/cookie-compliance/stats/{site_id}")
async def get_site_statistics(
    site_id: str,
    days: int = 30,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get consent statistics for a site
    
    Query params:
    - days: Number of days to include (default 30)
    """
    try:
        days = max(1, min(days, 365))
        stats_query = """
            SELECT 
                date, total_impressions,
                accepted_all, accepted_partial, rejected_all,
                accepted_analytics, accepted_marketing, accepted_functional
            FROM cookie_compliance_stats
            WHERE site_id = $1 
                AND date >= CURRENT_DATE - ($2 * INTERVAL '1 day')
            ORDER BY date DESC
        """
        
        rows = await db_pool.fetch(stats_query, site_id, days)
        
        daily_stats = [dict(row) for row in rows]
        
        # Calculate totals
        total_impressions = sum(s['total_impressions'] for s in daily_stats)
        total_accepted_all = sum(s['accepted_all'] for s in daily_stats)
        total_accepted_partial = sum(s['accepted_partial'] for s in daily_stats)
        total_rejected_all = sum(s['rejected_all'] for s in daily_stats)
        
        # Calculate rates
        acceptance_rate = (total_accepted_all / total_impressions * 100) if total_impressions > 0 else 0
        partial_rate = (total_accepted_partial / total_impressions * 100) if total_impressions > 0 else 0
        rejection_rate = (total_rejected_all / total_impressions * 100) if total_impressions > 0 else 0
        
        # Category stats
        total_analytics = sum(s['accepted_analytics'] for s in daily_stats)
        total_marketing = sum(s['accepted_marketing'] for s in daily_stats)
        total_functional = sum(s['accepted_functional'] for s in daily_stats)
        
        analytics_rate = (total_analytics / total_impressions * 100) if total_impressions > 0 else 0
        marketing_rate = (total_marketing / total_impressions * 100) if total_impressions > 0 else 0
        functional_rate = (total_functional / total_impressions * 100) if total_impressions > 0 else 0
        
        return {
            "success": True,
            "site_id": site_id,
            "period_days": days,
            "summary": {
                "total_impressions": total_impressions,
                "accepted_all": total_accepted_all,
                "accepted_partial": total_accepted_partial,
                "rejected_all": total_rejected_all,
                "acceptance_rate": round(acceptance_rate, 2),
                "partial_rate": round(partial_rate, 2),
                "rejection_rate": round(rejection_rate, 2)
            },
            "categories": {
                "analytics": {
                    "total": total_analytics,
                    "rate": round(analytics_rate, 2)
                },
                "marketing": {
                    "total": total_marketing,
                    "rate": round(marketing_rate, 2)
                },
                "functional": {
                    "total": total_functional,
                    "rate": round(functional_rate, 2)
                }
            },
            "daily_stats": daily_stats
        }
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/api/cookie-compliance/consents/{site_id}")
async def get_consent_logs(
    site_id: str,
    limit: int = 100,
    offset: int = 0,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get consent logs for a site (for DSGVO documentation)
    
    Query params:
    - limit: Number of records (default 100, max 1000)
    - offset: Pagination offset
    """
    try:
        if limit > 1000:
            limit = 1000
        
        # Get logs
        query = """
            SELECT 
                id, site_id, visitor_id, consent_categories,
                services_accepted, language, banner_shown,
                revision_id, timestamp
            FROM cookie_consent_logs
            WHERE site_id = $1
            ORDER BY timestamp DESC
            LIMIT $2 OFFSET $3
        """
        
        rows = await db_pool.fetch(query, site_id, limit, offset)
        
        # Count total
        count_query = "SELECT COUNT(*) as total FROM cookie_consent_logs WHERE site_id = $1"
        count_row = await db_pool.fetchrow(count_query, site_id)
        total = count_row['total']
        
        logs = [dict(row) for row in rows]
        
        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": logs
        }
        
    except Exception as e:
        print(f"Error getting consent logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.get("/api/cookie-compliance/consents/{site_id}/export")
async def export_consent_logs_csv(
    site_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Export consent logs as CSV for DSGVO proof-of-consent documentation (Art. 7).

    Authenticated + requires the Cookie module. Excel-compatible UTF-8 (BOM),
    semicolon-separated. Contains pseudonymized data only (hashed IP, truncated UA).
    """
    user = await get_current_user_required(credentials)
    await require_module(user, 'cookie')
    try:
        query = """
            SELECT id, visitor_id, consent_categories, services_accepted,
                   ip_address_hash, user_agent, language, banner_shown,
                   revision_id, timestamp
            FROM cookie_consent_logs
            WHERE site_id = $1
            ORDER BY timestamp DESC
        """
        rows = await db_pool.fetch(query, site_id)

        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=';')
        writer.writerow([
            'ID', 'Zeitstempel (UTC)', 'Visitor-ID', 'Notwendig', 'Funktional',
            'Statistik', 'Marketing', 'Akzeptierte Services', 'IP-Hash',
            'User-Agent', 'Sprache', 'Banner angezeigt', 'Konfig-Revision'
        ])
        for r in rows:
            cats = r['consent_categories']
            if isinstance(cats, str):
                try:
                    cats = json.loads(cats)
                except Exception:
                    cats = {}
            cats = cats or {}
            services = r['services_accepted']
            if isinstance(services, str):
                try:
                    services = json.loads(services)
                except Exception:
                    services = None
            services_str = ', '.join(services) if isinstance(services, list) else ''
            writer.writerow([
                r['id'],
                r['timestamp'].isoformat() if r['timestamp'] else '',
                r['visitor_id'] or '',
                'ja' if cats.get('necessary') else 'nein',
                'ja' if cats.get('functional') else 'nein',
                'ja' if cats.get('analytics') else 'nein',
                'ja' if cats.get('marketing') else 'nein',
                services_str,
                r['ip_address_hash'] or '',
                r['user_agent'] or '',
                r['language'] or '',
                'ja' if r['banner_shown'] else 'nein',
                r['revision_id'] if r['revision_id'] is not None else ''
            ])

        # Prepend BOM so Excel renders UTF-8 (umlauts) correctly.
        csv_bytes = ('﻿' + buf.getvalue()).encode('utf-8')
        filename = f"consent-log_{site_id}_{date.today().isoformat()}.csv"
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting consent logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export: {str(e)}")

# ============================================================================
# Utility Endpoints
# ============================================================================

@router.delete("/api/cookie-compliance/consents/expired")
async def delete_expired_consents(
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Manually trigger deletion of expired consent logs (DSGVO: older than 3 years)
    
    Usually runs automatically via cron job
    """
    try:
        query = "SELECT delete_expired_consents()"
        await db_pool.execute(query)
        
        return {
            "success": True,
            "message": "Expired consents deleted"
        }
        
    except Exception as e:
        print(f"Error deleting expired consents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")

@router.post("/api/cookie-compliance/scan")
async def scan_website(
    request: Request,
    data: Dict[str, str],
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Scannt eine Website und erkennt automatisch verwendete Cookie-Services.
    Speichert die gefundenen Services automatisch in der Banner-Konfiguration.
    
    Body:
    - url: Website URL zum Scannen
    - site_id: (optional) Site-ID für die Konfiguration
    
    Returns:
    - detected_services: Liste erkannter Services
    - config_updated: Boolean ob Config aktualisiert wurde
    """
    try:
        url = data.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        
        # Site-ID aus URL generieren wenn nicht angegeben
        site_id = data.get('site_id')
        if not site_id:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url if url.startswith('http') else f'https://{url}')
                hostname = parsed.netloc.replace('www.', '')
                site_id = hostname.replace('.', '-').lower()
            except:
                site_id = 'unknown-site'

        # ✅ Authentifizierten User ermitteln (optional): Die gespeicherte Config
        #    MUSS dem User zugeordnet werden (user_id), sonst findet /my-config sie
        #    nicht (filtert auf user_id) und die Ersteinrichtung läuft in eine Schleife.
        user_id = None
        try:
            user = await get_current_user_optional(credentials)
            if user:
                user_id = await get_user_id_from_token(user)
                # An die registrierte Website binden (1 Account = 1 Website),
                # damit nicht unter einer abweichenden site_id eine Waisen-Config entsteht.
                registered_site_id = await get_user_website_site_id(user_id)
                if registered_site_id:
                    site_id = registered_site_id
        except Exception as e:
            logger.warning(f"[Scan] Could not resolve user_id (anonymous scan): {e}")

        logger.warning(f"[Scan] START url={url} site_id={site_id} user_id={user_id}")

        # Scan website
        scan_result = await cookie_scanner.scan_website(url)

        if scan_result.get('error'):
            logger.warning(f"[Scan] scanner returned error for {url}: {scan_result.get('error')}")
            return {
                "success": False,
                "error": scan_result['error'],
                "url": url
            }
        
        # Match detected services with database services
        matched_services = []
        service_keys_found = []
        
        if scan_result['detected_services']:
            service_keys = scan_result['detected_services']
            
            query = """
                SELECT service_key, name, category, description, cookies
                FROM cookie_services
                WHERE service_key = ANY($1::text[]) AND is_active = true
            """
            
            rows = await db_pool.fetch(query, service_keys)
            
            for row in rows:
                service_keys_found.append(row['service_key'])
                matched_services.append({
                    'service_key': row['service_key'],
                    'name': row['name'],
                    'category': row['category'],
                    'description': row['description'],
                    'confidence': scan_result['confidence'].get(row['service_key'], 0.5)
                })
        
        # ✅ AUTOMATISCH: Speichere gefundene Services in cookie_banner_configs
        config_updated = False
        if site_id:
            # Prüfe ob Config existiert
            existing = await db_pool.fetchrow(
                "SELECT id FROM cookie_banner_configs WHERE site_id = $1",
                site_id
            )
            
            if existing:
                # Update existierende Config mit gefundenen Services.
                # user_id heilen, falls die Zeile zuvor verwaist angelegt wurde.
                res = await db_pool.execute("""
                    UPDATE cookie_banner_configs SET
                        services = $2::jsonb,
                        scan_completed_at = NOW(),
                        last_scan_url = $3,
                        user_id = COALESCE(user_id, $4),
                        updated_at = NOW()
                    WHERE site_id = $1
                """, site_id, json.dumps(service_keys_found), url, user_id)
                config_updated = True
                logger.warning(f"[Scan] ✅ UPDATE site_id={site_id} result={res} services={len(service_keys_found)}")
            else:
                # Erstelle neue Config mit gefundenen Services (inkl. user_id,
                # damit /my-config sie zuverlässig findet).
                res = await db_pool.execute("""
                    INSERT INTO cookie_banner_configs (
                        site_id, user_id, services, scan_completed_at, last_scan_url, is_active
                    ) VALUES ($1, $2, $3::jsonb, NOW(), $4, true)
                """, site_id, user_id, json.dumps(service_keys_found), url)
                config_updated = True
                logger.warning(f"[Scan] ✅ INSERT site_id={site_id} result={res} services={len(service_keys_found)}")
        else:
            logger.warning(f"[Scan] ⚠️ persistence SKIPPED — empty site_id (url={url}, user_id={user_id})")

        # Drittlandtransfer-Findings (abmahnfähig, KEIN Cookie-Problem) durchreichen.
        # Diese erscheinen unabhängig davon, ob Banner-Cookies gefunden wurden —
        # damit der Scanner bei extern geladenen Google Fonts & Co. nicht länger
        # fälschlich "keine relevanten Cookies" meldet.
        privacy_findings = scan_result.get('privacy_findings', [])
        privacy_risk_euro = sum(f.get('risk_euro', 0) for f in privacy_findings)

        logger.warning(
            f"[Scan] DONE site_id={site_id} config_updated={config_updated} "
            f"total_found={len(matched_services)} privacy_findings={len(privacy_findings)}"
        )
        return {
            "success": True,
            "url": url,
            "site_id": site_id,
            "detected_services": matched_services,
            "total_found": len(matched_services),
            "privacy_findings": privacy_findings,
            "privacy_findings_count": len(privacy_findings),
            "privacy_risk_euro": privacy_risk_euro,
            "config_updated": config_updated,
            "scan_timestamp": scan_result.get('scan_timestamp'),
            "raw_detection": {
                'scripts_count': len(scan_result.get('scripts', [])),
                'iframes_count': len(scan_result.get('iframes', []))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error scanning website: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/api/cookie-compliance/monitor/check/{site_id}")
async def monitor_website_check(
    site_id: str,
    data: Dict[str, Any],
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Vergleicht einen frischen Scan mit der gespeicherten Baseline.
    Gibt hinzugekommene und entfernte Services zurück.
    """
    try:
        url = data.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="URL required")

        # Gespeicherte Services aus der Config laden
        config_row = await db_pool.fetchrow("""
            SELECT services, last_scan_url, scan_completed_at
            FROM cookie_banner_configs
            WHERE site_id = $1
        """, site_id)

        stored_services: list = []
        if config_row and config_row['services']:
            raw = config_row['services']
            if isinstance(raw, str):
                raw = json.loads(raw)
            if isinstance(raw, list):
                stored_services = raw

        # Frischen Scan durchführen
        scan_result = await cookie_scanner.scan_website(url)

        if scan_result.get('error'):
            return {"success": False, "error": scan_result['error']}

        # Erkannte Services mit DB abgleichen
        new_service_keys = scan_result.get('detected_services', [])
        matched_services = []
        if new_service_keys:
            rows = await db_pool.fetch("""
                SELECT service_key, name, category
                FROM cookie_services
                WHERE service_key = ANY($1::text[]) AND is_active = true
            """, new_service_keys)
            matched_services = [dict(row) for row in rows]

        current_keys = {s['service_key'] for s in matched_services}
        stored_keys = set(stored_services)

        new_services = [s for s in matched_services if s['service_key'] not in stored_keys]
        removed_services = list(stored_keys - current_keys)
        has_changes = bool(new_services or removed_services)

        return {
            "success": True,
            "site_id": site_id,
            "has_changes": has_changes,
            "new_services": new_services,
            "removed_services": removed_services,
            "current_services": matched_services,
            "baseline_services": stored_services,
            "scan_timestamp": scan_result.get('scan_timestamp'),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Monitor check error for {site_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Monitor check failed: {str(e)}")


@router.post("/api/cookie-compliance/scan/deep")
async def scan_website_deep(
    request: Request,
    data: Dict[str, Any],
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Deep Scan einer Website mit Headless Browser
    
    Erkennt:
    - Alle Cookies (First & Third Party)
    - Local Storage Eintraege
    - Session Storage Eintraege
    - Third-Party Requests
    - Dynamisch geladene Scripts
    
    Body:
    - url: Website URL zum Scannen
    - wait_time: (optional) Wartezeit in ms nach Page Load (default: 3000)
    
    Returns:
    - Umfassendes Scan-Ergebnis mit allen Tracking-Daten
    """
    try:
        url = data.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        
        wait_time = data.get('wait_time', 3000)
        
        # Check if headless scanning is available
        # Note: Deep scan requires Playwright which is not installed
        return {
            "success": False,
            "error": "Headless scanning not available. Use light scan instead.",
            "url": url,
            "fallback_available": True
        }
        
        # Deep scan disabled - use light scan via /scan endpoint
        scan_result = {"error": "Deep scan not available"}
        
        if scan_result.get('error'):
            return {
                "success": False,
                "error": scan_result['error'],
                "url": url
            }
        
        # Match detected services with database
        matched_services = []
        if scan_result.get('detected_services'):
            service_keys = list(scan_result['detected_services'])
            
            query = """
                SELECT service_key, name, category, provider, template
                FROM cookie_services
                WHERE service_key = ANY($1::text[]) AND is_active = true
            """
            
            rows = await db_pool.fetch(query, service_keys)
            
            for row in rows:
                matched_services.append({
                    'service_key': row['service_key'],
                    'name': row['name'],
                    'category': row['category'],
                    'provider': row['provider'],
                    'confidence': scan_result.get('confidence', {}).get(row['service_key'], 0.5),
                    'evidence': scan_result.get('service_details', {}).get(row['service_key'], {}).get('evidence', [])
                })
        
        return {
            "success": True,
            "url": url,
            "scan_method": "headless_browser",
            "scan_timestamp": scan_result.get('scan_timestamp'),
            
            # Detected services
            "detected_services": matched_services,
            "total_services": len(matched_services),
            
            # Cookie data
            "cookies": scan_result.get('cookies', {}),
            
            # Storage data
            "local_storage": scan_result.get('local_storage', {}),
            "session_storage": scan_result.get('session_storage', {}),
            
            # Network data
            "third_party_requests": scan_result.get('third_party_requests', {}),
            
            # Content
            "scripts": scan_result.get('scripts', []),
            "iframes": scan_result.get('iframes', []),
            
            # Summary
            "summary": scan_result.get('summary', {}),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in deep scan: {e}")
        raise HTTPException(status_code=500, detail=f"Deep scan failed: {str(e)}")


@router.get("/api/cookie-compliance/scan/capabilities")
async def get_scan_capabilities():
    """
    Gibt die verfuegbaren Scan-Capabilities zurueck
    
    Returns:
    - light_scan: Immer verfuegbar (HTTP-basiert)
    - deep_scan: Verfuegbar wenn Playwright installiert
    - features: Liste der Features pro Scan-Typ
    """
    return {
        "success": True,
        "capabilities": {
            "light_scan": {
                "available": True,
                "description": "HTTP-basierter Scan ohne Browser-Rendering",
                "features": [
                    "Script-Erkennung via HTML-Parsing",
                    "Iframe-Erkennung",
                    "Pattern-basierte Service-Erkennung",
                    "Schnell (< 5 Sekunden)"
                ]
            },
            "deep_scan": {
                "available": False,  # Playwright not installed
                "description": "Headless Browser Scan mit vollstaendiger JS-Ausfuehrung",
                "features": [
                    "Echtes Browser-Rendering",
                    "Cookie-Auslesen (First & Third Party)",
                    "Local Storage Scanning",
                    "Session Storage Scanning",
                    "Third-Party Request Tracking",
                    "Dynamisch geladene Scripts",
                    "Genauere Erkennung (10-30 Sekunden)"
                ]
            }
        }
    }


@router.get("/api/cookie-compliance/blocking-config/{site_id}")
async def get_blocking_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get blocking configuration for auto-blocking script
    Returns all services with their blocking patterns
    """
    try:
        # Get banner config to know which services are active
        config_query = """
            SELECT services, auto_block_scripts
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        config = await db_pool.fetchrow(config_query, site_id)
        
        if not config:
            # Return empty config if not set up yet
            return {
                "success": True,
                "site_id": site_id,
                "auto_block": False,
                "services": []
            }
        
        selected_services = config['services'] if config['services'] else []
        auto_block = config['auto_block_scripts'] if config['auto_block_scripts'] is not None else True
        
        # Get service details with blocking info
        if selected_services and len(selected_services) > 0:
            services_query = """
                SELECT 
                    service_key,
                    name,
                    category,
                    script_patterns,
                    iframe_patterns,
                    cookie_names,
                    local_storage_keys,
                    block_method
                FROM cookie_services
                WHERE service_key = ANY($1::text[]) AND is_active = true
            """
            rows = await db_pool.fetch(services_query, selected_services)
        else:
            rows = []
        
        services_data = []
        for row in rows:
            services_data.append({
                'service_key': row['service_key'],
                'name': row['name'],
                'category': row['category'],
                'script_patterns': row['script_patterns'] or [],
                'iframe_patterns': row['iframe_patterns'] or [],
                'cookie_names': row['cookie_names'] or [],
                'local_storage_keys': row['local_storage_keys'] or [],
                'block_method': row['block_method'] or 'script_rewrite'
            })
        
        return {
            "success": True,
            "site_id": site_id,
            "auto_block": auto_block,
            "services": services_data
        }
        
    except Exception as e:
        print(f"Error getting blocking config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get blocking configuration: {str(e)}")

@router.get("/api/cookie-compliance/health")
async def health_check(db_pool: asyncpg.Pool = Depends(get_db_connection)):
    """
    Health check endpoint
    """
    try:
        # Test database connection
        result = await db_pool.fetchval("SELECT COUNT(*) FROM cookie_services WHERE is_active = true")
        
        return {
            "success": True,
            "status": "healthy",
            "active_services": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Phase 1: Google Consent Mode v2, Jugendschutz, TCF
# ============================================================================

@router.get("/api/cookie-compliance/consent-mode-config/{site_id}")
async def get_consent_mode_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get Google Consent Mode v2 configuration
    Pflicht seit März 2024 für Google Services
    """
    try:
        query = """
            SELECT 
                consent_mode_enabled,
                consent_mode_default,
                gtm_enabled,
                gtm_container_id
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        if not row:
            return {
                "success": True,
                "data": {
                    "consent_mode_enabled": True,
                    "consent_mode_default": {
                        "ad_storage": "denied",
                        "analytics_storage": "denied",
                        "ad_user_data": "denied",
                        "ad_personalization": "denied"
                    },
                    "gtm_enabled": False,
                    "gtm_container_id": None
                }
            }
        
        return {
            "success": True,
            "data": {
                "consent_mode_enabled": row['consent_mode_enabled'],
                "consent_mode_default": row['consent_mode_default'] or {
                    "ad_storage": "denied",
                    "analytics_storage": "denied",
                    "ad_user_data": "denied",
                    "ad_personalization": "denied"
                },
                "gtm_enabled": row.get('gtm_enabled', False),
                "gtm_container_id": row.get('gtm_container_id')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cookie-compliance/consent-mode-config")
async def update_consent_mode_config(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Update Google Consent Mode v2 configuration
    """
    try:
        data = await request.json()
        site_id = data.get('site_id')
        
        if not site_id:
            raise HTTPException(status_code=400, detail="site_id required")
        
        query = """
            UPDATE cookie_banner_configs SET
                consent_mode_enabled = COALESCE($2, consent_mode_enabled),
                consent_mode_default = COALESCE($3, consent_mode_default),
                gtm_enabled = COALESCE($4, gtm_enabled),
                gtm_container_id = COALESCE($5, gtm_container_id),
                updated_at = NOW()
            WHERE site_id = $1
            RETURNING id
        """
        
        result = await db_pool.fetchrow(
            query,
            site_id,
            data.get('consent_mode_enabled'),
            json.dumps(data.get('consent_mode_default')) if data.get('consent_mode_default') else None,
            data.get('gtm_enabled'),
            data.get('gtm_container_id')
        )
        
        return {"success": True, "updated": result is not None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/cookie-compliance/age-verification/{site_id}")
async def get_age_verification_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get age verification (Jugendschutz) configuration
    Art. 8 DSGVO - Altersgrenzen für Minderjährige
    """
    try:
        query = """
            SELECT 
                age_verification_enabled,
                age_verification_min_age
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        # Länderspezifische Altersgrenzen nach DSGVO
        country_age_limits = {
            "DE": 16, "AT": 14, "BE": 13, "BG": 14, "HR": 16,
            "CY": 14, "CZ": 15, "DK": 13, "EE": 13, "FI": 13,
            "FR": 15, "GR": 15, "HU": 16, "IE": 16, "IT": 14,
            "LV": 13, "LT": 14, "LU": 16, "MT": 13, "NL": 16,
            "PL": 16, "PT": 13, "RO": 16, "SK": 16, "SI": 16,
            "ES": 14, "SE": 13, "GB": 13, "CH": 16
        }
        
        if not row:
            return {
                "success": True,
                "data": {
                    "enabled": False,
                    "min_age": 16,
                    "country_age_limits": country_age_limits
                }
            }
        
        return {
            "success": True,
            "data": {
                "enabled": row['age_verification_enabled'] or False,
                "min_age": row['age_verification_min_age'] or 16,
                "country_age_limits": country_age_limits
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cookie-compliance/age-verification")
async def update_age_verification_config(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Update age verification configuration
    """
    try:
        data = await request.json()
        site_id = data.get('site_id')
        
        if not site_id:
            raise HTTPException(status_code=400, detail="site_id required")
        
        query = """
            UPDATE cookie_banner_configs SET
                age_verification_enabled = COALESCE($2, age_verification_enabled),
                age_verification_min_age = COALESCE($3, age_verification_min_age),
                updated_at = NOW()
            WHERE site_id = $1
            RETURNING id
        """
        
        result = await db_pool.fetchrow(
            query,
            site_id,
            data.get('enabled'),
            data.get('min_age')
        )
        
        return {"success": True, "updated": result is not None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TCF 2.2 Endpoints (UI vorbereitet)
@router.get("/api/cookie-compliance/tcf/vendors")
async def get_tcf_vendors(
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get available TCF vendors
    """
    try:
        query = """
            SELECT 
                vendor_id, name, purposes, legitimate_interests,
                special_purposes, features, special_features, policy_url
            FROM tcf_vendors
            WHERE is_active = true
            ORDER BY name
        """
        rows = await db_pool.fetch(query)
        
        vendors = []
        for row in rows:
            vendors.append({
                "vendor_id": row['vendor_id'],
                "name": row['name'],
                "purposes": list(row['purposes']) if row['purposes'] else [],
                "legitimate_interests": list(row['legitimate_interests']) if row['legitimate_interests'] else [],
                "special_purposes": list(row['special_purposes']) if row['special_purposes'] else [],
                "features": list(row['features']) if row['features'] else [],
                "special_features": list(row['special_features']) if row['special_features'] else [],
                "policy_url": row['policy_url'] or ""
            })
        
        purposes = [
            {"id": 1, "name": "Speicherung von und Zugriff auf Informationen", "description": "Cookies, Geräte- oder ähnliche Online-Kennungen"},
            {"id": 2, "name": "Einfache Anzeigen", "description": "Anzeige von Werbung"},
            {"id": 3, "name": "Anzeigenauswahl, -schaltung und -berichterstattung", "description": "Personalisierte Werbung"},
            {"id": 4, "name": "Personalisierung von Inhalten", "description": "Auswahl personalisierter Inhalte"},
            {"id": 5, "name": "Messung", "description": "Messung der Anzeigen- und Inhaltsleistung"},
            {"id": 6, "name": "Anwendung von Marktforschung", "description": "Erkenntnisse über Zielgruppen"},
            {"id": 7, "name": "Entwicklung und Verbesserung von Produkten", "description": "Entwicklung neuer Produkte"},
            {"id": 8, "name": "Auswahl einfacher Anzeigen", "description": "Grundlegende Anzeigenauswahl"},
            {"id": 9, "name": "Erstellung eines personalisierten Anzeigenprofils", "description": "Profil für personalisierte Werbung"},
            {"id": 10, "name": "Auswahl personalisierter Anzeigen", "description": "Personalisierte Anzeigen basierend auf Profil"}
        ]
        
        return {
            "success": True,
            "vendors": vendors,
            "purposes": purposes,
            "tcf_version": "2.2",
            "vendor_count": len(vendors)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TCF vendor fetch failed: {str(e)}")


@router.get("/api/cookie-compliance/tcf/config/{site_id}")
async def get_tcf_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get TCF configuration for a site
    """
    try:
        query = """
            SELECT 
                tcf_enabled,
                tcf_vendors
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        if not row:
            return {
                "success": True,
                "data": {
                    "tcf_enabled": False,
                    "tcf_vendors": [],
                    "notice": "TCF erfordert Registrierung bei IAB Europe als CMP"
                }
            }
        
        tcf_vendors = row['tcf_vendors']
        if isinstance(tcf_vendors, str):
            tcf_vendors = json.loads(tcf_vendors)
        
        return {
            "success": True,
            "data": {
                "tcf_enabled": row['tcf_enabled'] or False,
                "tcf_vendors": tcf_vendors or [],
                "notice": "TCF erfordert Registrierung bei IAB Europe als CMP"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cookie-compliance/tcf/config")
async def update_tcf_config(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Update TCF configuration
    """
    try:
        data = await request.json()
        site_id = data.get('site_id')
        
        if not site_id:
            raise HTTPException(status_code=400, detail="site_id required")
        
        query = """
            UPDATE cookie_banner_configs SET
                tcf_enabled = COALESCE($2, tcf_enabled),
                tcf_vendors = COALESCE($3, tcf_vendors),
                updated_at = NOW()
            WHERE site_id = $1
            RETURNING id
        """
        
        result = await db_pool.fetchrow(
            query,
            site_id,
            data.get('tcf_enabled'),
            json.dumps(data.get('tcf_vendors')) if data.get('tcf_vendors') else None
        )
        
        return {"success": True, "updated": result is not None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 2: Geo-Restriction, Consent Forwarding
# ============================================================================

@router.get("/api/cookie-compliance/geo-check")
async def geo_check(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Detect visitor's country for geo-restriction
    Uses IP-based geolocation
    """
    try:
        # Get client IP
        client_ip = request.headers.get('X-Forwarded-For', request.client.host)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Hash IP for privacy
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
        
        # Check cache first
        cache_query = """
            SELECT country_code FROM geo_ip_cache 
            WHERE ip_hash = $1 AND cached_at > NOW() - INTERVAL '24 hours'
        """
        cached = await db_pool.fetchrow(cache_query, ip_hash)
        
        if cached:
            return {
                "success": True,
                "country_code": cached['country_code'],
                "cached": True
            }
        
        # Simple IP-based detection (can be enhanced with MaxMind)
        # For now, use a basic approach or default to EU
        country_code = "DE"  # Default
        
        # Try to detect from common headers
        cf_country = request.headers.get('CF-IPCountry')
        if cf_country:
            country_code = cf_country
        
        # Cache result
        cache_insert = """
            INSERT INTO geo_ip_cache (ip_hash, country_code)
            VALUES ($1, $2)
            ON CONFLICT (ip_hash) DO UPDATE SET 
                country_code = $2, cached_at = NOW()
        """
        await db_pool.execute(cache_insert, ip_hash, country_code)
        
        return {
            "success": True,
            "country_code": country_code,
            "cached": False
        }
    except Exception as e:
        return {
            "success": True,
            "country_code": "EU",  # Default to EU on error
            "error": str(e)
        }


@router.get("/api/cookie-compliance/geo-restriction/{site_id}")
async def get_geo_restriction_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get geo-restriction configuration
    """
    try:
        query = """
            SELECT 
                geo_restriction_enabled,
                geo_countries
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        # EU/EEA countries that require cookie consent
        eu_countries = [
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
            "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "GB", "CH", "NO", "IS", "LI"
        ]
        
        if not row:
            return {
                "success": True,
                "data": {
                    "enabled": False,
                    "countries": [],
                    "eu_countries": eu_countries,
                    "mode": "show_all"  # show_all, show_in_countries, hide_in_countries
                }
            }
        
        return {
            "success": True,
            "data": {
                "enabled": row['geo_restriction_enabled'] or False,
                "countries": row['geo_countries'] or [],
                "eu_countries": eu_countries,
                "mode": "show_in_countries"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cookie-compliance/geo-restriction")
async def update_geo_restriction(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Update geo-restriction settings
    """
    try:
        data = await request.json()
        site_id = data.get('site_id')
        
        if not site_id:
            raise HTTPException(status_code=400, detail="site_id required")
        
        query = """
            UPDATE cookie_banner_configs SET
                geo_restriction_enabled = COALESCE($2, geo_restriction_enabled),
                geo_countries = COALESCE($3, geo_countries),
                updated_at = NOW()
            WHERE site_id = $1
            RETURNING id
        """
        
        result = await db_pool.fetchrow(
            query,
            site_id,
            data.get('enabled'),
            data.get('countries')
        )
        
        return {"success": True, "updated": result is not None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Consent Forwarding
@router.get("/api/cookie-compliance/forwarding/{site_id}")
async def get_forwarding_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get consent forwarding configuration
    """
    try:
        query = """
            SELECT 
                forwarding_enabled,
                forwarding_target_sites
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        if not row:
            return {
                "success": True,
                "data": {
                    "enabled": False,
                    "target_sites": [],
                    "mode": "one_way"  # one_way, two_way
                }
            }
        
        return {
            "success": True,
            "data": {
                "enabled": row['forwarding_enabled'] or False,
                "target_sites": row['forwarding_target_sites'] or [],
                "mode": "one_way"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cookie-compliance/forwarding")
async def update_forwarding_config(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Update consent forwarding settings
    """
    try:
        data = await request.json()
        site_id = data.get('site_id')
        
        if not site_id:
            raise HTTPException(status_code=400, detail="site_id required")
        
        query = """
            UPDATE cookie_banner_configs SET
                forwarding_enabled = COALESCE($2, forwarding_enabled),
                forwarding_target_sites = COALESCE($3, forwarding_target_sites),
                updated_at = NOW()
            WHERE site_id = $1
            RETURNING id
        """
        
        result = await db_pool.fetchrow(
            query,
            site_id,
            data.get('enabled'),
            data.get('target_sites')
        )
        
        return {"success": True, "updated": result is not None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 5: Cookie Policy Generator, Revision System, Import/Export
# ============================================================================

@router.get("/api/cookie-compliance/policy/{site_id}")
async def generate_cookie_policy(
    site_id: str,
    lang: str = "de",
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Generate cookie policy document from configured services
    """
    try:
        config_query = """
            SELECT c.*,
                   array_agg(s.name ORDER BY s.name) FILTER (WHERE s.name IS NOT NULL)        AS service_names,
                   array_agg(s.category ORDER BY s.name) FILTER (WHERE s.name IS NOT NULL)    AS service_categories,
                   array_agg(s.provider ORDER BY s.name) FILTER (WHERE s.name IS NOT NULL)    AS service_providers,
                   array_agg(s.description ORDER BY s.name) FILTER (WHERE s.name IS NOT NULL) AS service_descriptions,
                   array_agg(s.cookies ORDER BY s.name) FILTER (WHERE s.name IS NOT NULL)     AS service_cookies
            FROM cookie_banner_configs c
            LEFT JOIN LATERAL jsonb_array_elements_text(c.services) AS svc_key ON true
            LEFT JOIN cookie_services s ON s.service_key = svc_key
            WHERE c.site_id = $1 AND c.is_active = true
            GROUP BY c.id
        """
        row = await db_pool.fetchrow(config_query, site_id)
        
        if not row:
            policy = {
                "title": "Cookie-Richtlinie" if lang == "de" else "Cookie Policy",
                "last_updated": datetime.now().isoformat(),
                "site_id": site_id,
                "sections": [
                    {
                        "title": "Einleitung" if lang == "de" else "Introduction",
                        "content": "Diese Website verwendet Cookies und ähnliche Technologien, um die Benutzererfahrung zu verbessern." if lang == "de" else "This website uses cookies and similar technologies to improve user experience."
                    },
                    {
                        "title": "Ihre Rechte" if lang == "de" else "Your Rights",
                        "content": "Sie können Ihre Einwilligung jederzeit widerrufen." if lang == "de" else "You can withdraw your consent at any time."
                    }
                ]
            }
            return {"success": True, "policy": policy, "format": "json", "configured": False}
        
        # Build policy document
        policy = {
            "title": "Cookie-Richtlinie" if lang == "de" else "Cookie Policy",
            "last_updated": datetime.now().isoformat(),
            "site_id": site_id,
            "sections": []
        }
        
        # Introduction
        policy["sections"].append({
            "title": "Einleitung" if lang == "de" else "Introduction",
            "content": "Diese Website verwendet Cookies und ähnliche Technologien, um die Benutzererfahrung zu verbessern und bestimmte Funktionen bereitzustellen." if lang == "de" else "This website uses cookies and similar technologies to improve user experience and provide certain features."
        })
        
        # Categorize services
        categories = {
            "necessary": {"name": "Notwendig", "services": []},
            "functional": {"name": "Funktional", "services": []},
            "analytics": {"name": "Statistik", "services": []},
            "marketing": {"name": "Marketing", "services": []}
        }
        
        if row['service_names'] and row['service_names'][0]:
            for i, name in enumerate(row['service_names']):
                if name:
                    cat = row['service_categories'][i] if row['service_categories'] else 'functional'
                    if cat in categories:
                        categories[cat]["services"].append({
                            "name": name,
                            "provider": row['service_providers'][i] if row['service_providers'] else "",
                            "description": row['service_descriptions'][i] if row['service_descriptions'] else "",
                            "cookies": row['service_cookies'][i] if row['service_cookies'] else []
                        })
        
        for cat_key, cat_data in categories.items():
            if cat_data["services"]:
                section = {
                    "title": cat_data["name"],
                    "services": cat_data["services"]
                }
                policy["sections"].append(section)
        
        # Rights section
        policy["sections"].append({
            "title": "Ihre Rechte" if lang == "de" else "Your Rights",
            "content": "Sie können Ihre Einwilligung jederzeit widerrufen, indem Sie auf den Cookie-Einstellungen-Link klicken." if lang == "de" else "You can withdraw your consent at any time by clicking the cookie settings link."
        })
        
        return {
            "success": True,
            "policy": policy,
            "format": "json",
            "configured": True
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Policy generation failed: {str(e)}")


@router.get("/api/cookie-compliance/revisions/{site_id}")
async def get_config_revisions(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get configuration revision history
    """
    try:
        query = """
            SELECT 
                revision_number, config_snapshot, changes_summary, created_at
            FROM cookie_consent_revisions
            WHERE site_id = $1
            ORDER BY revision_number DESC
            LIMIT 50
        """
        rows = await db_pool.fetch(query, site_id)
        
        revisions = []
        for row in rows:
            revisions.append({
                "revision": row['revision_number'],
                "snapshot": row['config_snapshot'],
                "changes": row['changes_summary'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            })
        
        return {
            "success": True,
            "revisions": revisions,
            "total": len(revisions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/cookie-compliance/export/{site_id}")
async def export_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Export complete configuration as JSON
    """
    try:
        query = """
            SELECT * FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        if not row:
            return {"success": False, "error": "Configuration not found"}
        
        config = dict(row)
        
        # Remove internal fields
        for field in ['id', 'user_id', 'created_at', 'updated_at', 'is_active']:
            config.pop(field, None)
        
        # Convert datetime fields
        if config.get('scan_completed_at'):
            config['scan_completed_at'] = config['scan_completed_at'].isoformat()
        
        return {
            "success": True,
            "export": {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "site_id": site_id,
                "config": config
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cookie-compliance/import")
async def import_config(
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Import configuration from JSON
    """
    try:
        data = await request.json()
        site_id = data.get('site_id')
        import_data = data.get('import')
        
        if not site_id or not import_data:
            raise HTTPException(status_code=400, detail="site_id and import data required")
        
        config = import_data.get('config', {})
        
        # Check if config exists
        existing = await db_pool.fetchrow(
            "SELECT id FROM cookie_banner_configs WHERE site_id = $1",
            site_id
        )
        
        if existing:
            # Update existing
            query = """
                UPDATE cookie_banner_configs SET
                    layout = $2,
                    primary_color = $3,
                    accent_color = $4,
                    text_color = $5,
                    bg_color = $6,
                    services = $7,
                    texts = $8,
                    consent_mode_enabled = $9,
                    consent_mode_default = $10,
                    updated_at = NOW()
                WHERE site_id = $1
                RETURNING id
            """
            result = await db_pool.fetchrow(
                query,
                site_id,
                config.get('layout', 'box_modal'),
                config.get('primary_color', '#7c3aed'),
                config.get('accent_color', '#9333ea'),
                config.get('text_color', '#333333'),
                config.get('bg_color', '#ffffff'),
                config.get('services', []),
                json.dumps(config.get('texts', {})),
                config.get('consent_mode_enabled', True),
                json.dumps(config.get('consent_mode_default', {}))
            )
        else:
            return {"success": False, "error": "Site not found. Create configuration first."}
        
        return {
            "success": True,
            "imported": True,
            "site_id": site_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 6: Auto-Reconsent, Bannerless Mode
# ============================================================================

@router.get("/api/cookie-compliance/reconsent-check/{site_id}")
async def check_reconsent_required(
    site_id: str,
    config_hash: str = None,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Check if reconsent is required due to config changes
    """
    try:
        query = """
            SELECT config_hash, requires_reconsent
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        if not row:
            return {"success": True, "requires_reconsent": False}
        
        current_hash = row['config_hash']
        requires_reconsent = row['requires_reconsent'] or False
        
        # Compare hashes if provided
        if config_hash and current_hash and config_hash != current_hash:
            requires_reconsent = True
        
        return {
            "success": True,
            "requires_reconsent": requires_reconsent,
            "current_hash": current_hash
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/cookie-compliance/bannerless/{site_id}")
async def get_bannerless_config(
    site_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get bannerless mode configuration
    Only content blockers, no cookie banner
    """
    try:
        query = """
            SELECT bannerless_mode
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        row = await db_pool.fetchrow(query, site_id)
        
        return {
            "success": True,
            "bannerless_mode": row['bannerless_mode'] if row else False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AUDIT-16/17: Consent Revocation & Revocation Analytics
# =============================================================================

class RevocationRequest(BaseModel):
    site_id: str = Field(..., min_length=1, max_length=255)
    visitor_id: str = Field(..., min_length=1, max_length=255)
    reason: Optional[str] = None

_revocation_rate_cache: Dict[str, Any] = {}

@router.post("/api/cookie-compliance/revoke")
async def revoke_consent(
    revocation: RevocationRequest,
    request: Request,
):
    """AUDIT-16: Widerruf einer erteilten Einwilligung (DSGVO Art. 7 Abs. 3)."""
    if not db_pool:
        return {"success": True, "message": "Revocation recorded (no db)"}
    try:
        await db_pool.execute(
            """INSERT INTO cookie_consent_logs
               (site_id, visitor_id, consent_categories, action, timestamp, user_agent)
               VALUES ($1, $2, $3, 'revoke', NOW(), $4)""",
            revocation.site_id,
            revocation.visitor_id,
            json.dumps({"necessary": True, "functional": False, "analytics": False, "marketing": False}),
            truncate_user_agent(request.headers.get("user-agent", ""))
        )
        return {"success": True, "action": "revoke", "site_id": revocation.site_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/cookie-compliance/revocation-stats/{site_id}")
async def get_revocation_stats(
    site_id: str,
    days: int = 30,
    current_user: Dict = Depends(get_current_user_required),
):
    """AUDIT-17: Acceptance vs. Revocation Rate der letzten N Tage."""
    if not db_pool:
        return {"site_id": site_id, "acceptance_rate": 0.0, "revocation_rate": 0.0, "total": 0, "days": days}
    try:
        rows = await db_pool.fetch(
            """SELECT action, COUNT(*) as cnt
               FROM cookie_consent_logs
               WHERE site_id = $1
                 AND timestamp >= NOW() - ($2 * INTERVAL '1 day')
               GROUP BY action""",
            site_id, days
        )
        counts = {r["action"]: r["cnt"] for r in rows}
        total = sum(counts.values())
        accept_count = counts.get("accept", 0) + counts.get(None, 0)
        revoke_count = counts.get("revoke", 0)
        return {
            "site_id": site_id,
            "days": days,
            "total": total,
            "accept_count": accept_count,
            "revoke_count": revoke_count,
            "acceptance_rate": round(accept_count / total, 4) if total else 0.0,
            "revocation_rate": round(revoke_count / total, 4) if total else 0.0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AUDIT-18: Per-Service Consent Tracking bereits im ConsentLog.services_accepted
# Zusätzlicher Endpoint: Per-Service Breakdown aus Logs
# =============================================================================

@router.get("/api/cookie-compliance/service-stats/{site_id}")
async def get_service_consent_stats(
    site_id: str,
    days: int = 30,
    current_user: Dict = Depends(get_current_user_required),
):
    """AUDIT-18: Per-Service Consent-Statistiken (welche Services wie oft akzeptiert)."""
    if not db_pool:
        return {"site_id": site_id, "services": {}, "days": days}
    try:
        rows = await db_pool.fetch(
            """SELECT services_accepted
               FROM cookie_consent_logs
               WHERE site_id = $1
                 AND action IS DISTINCT FROM 'revoke'
                 AND timestamp >= NOW() - ($2 * INTERVAL '1 day')
                 AND services_accepted IS NOT NULL""",
            site_id, days
        )
        service_counts: Dict[str, int] = {}
        for row in rows:
            services = row["services_accepted"]
            if isinstance(services, str):
                try:
                    services = json.loads(services)
                except Exception:
                    continue
            if isinstance(services, list):
                for svc in services:
                    service_counts[svc] = service_counts.get(svc, 0) + 1
        return {"site_id": site_id, "days": days, "services": service_counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AUDIT-19: Rate-Limiting (max 100 Consent-Logs/Minute pro Site-ID)
# Redis Sliding Window (ZADD/ZREMRANGEBYSCORE)
# =============================================================================

import time as _time

_RATE_LIMIT_MAX = 100
_RATE_LIMIT_WINDOW_SECONDS = 60


async def check_rate_limit(site_id: str) -> bool:
    """Returns True if within rate limit, False if exceeded. Uses Redis ZADD sliding window."""
    if not redis_client:
        return True
    now = _time.time()
    key = f"rate_limit:consent:{site_id}"
    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, now - _RATE_LIMIT_WINDOW_SECONDS)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, _RATE_LIMIT_WINDOW_SECONDS * 2)
    results = await pipe.execute()
    count = results[2]
    if count > _RATE_LIMIT_MAX:
        await redis_client.zrem(key, str(now))
        return False
    return True


# =============================================================================
# AUDIT-24: Agency-Dashboard — Aggregierte Consent-Statistiken
# =============================================================================

@router.get("/api/cookie-compliance/agency/stats")
async def get_agency_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """AUDIT-24: Aggregierte Consent-Statistiken über alle verwalteten Sites."""
    user = await get_current_user_required(credentials)
    if not db_pool:
        return {"sites": [], "totals": {"total_impressions": 0, "acceptance_rate": 0.0}}
    user_id = int(user.get("id") or user.get("user_id"))
    try:
        rows = await db_pool.fetch(
            """SELECT
                 s.site_id,
                 s.total_impressions,
                 s.accepted_all,
                 s.rejected_all,
                 s.accepted_partial,
                 s.date
               FROM cookie_compliance_stats s
               INNER JOIN cookie_banner_configs c ON c.site_id = s.site_id AND c.user_id = $1
               WHERE s.date >= CURRENT_DATE - INTERVAL '30 days'
               ORDER BY s.date DESC""",
            user_id
        )
        site_map: Dict[str, Any] = {}
        for r in rows:
            sid = r["site_id"]
            if sid not in site_map:
                site_map[sid] = {"site_id": sid, "total_impressions": 0, "accepted_all": 0, "rejected_all": 0, "accepted_partial": 0}
            site_map[sid]["total_impressions"] += r["total_impressions"] or 0
            site_map[sid]["accepted_all"] += r["accepted_all"] or 0
            site_map[sid]["rejected_all"] += r["rejected_all"] or 0
            site_map[sid]["accepted_partial"] += r["accepted_partial"] or 0
        sites = list(site_map.values())
        for s in sites:
            total = s["total_impressions"]
            s["acceptance_rate"] = round((s["accepted_all"] + s["accepted_partial"]) / total, 4) if total else 0.0
        total_impressions = sum(s["total_impressions"] for s in sites)
        accepted = sum(s["accepted_all"] + s["accepted_partial"] for s in sites)
        return {
            "sites": sites,
            "totals": {
                "total_impressions": total_impressions,
                "acceptance_rate": round(accepted / total_impressions, 4) if total_impressions else 0.0,
                "site_count": len(sites),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AGENCY-01: Client attribution per site (Phase 10)
# =============================================================================

@router.patch("/api/cookie-compliance/agency/sites/{site_id}/client")
async def assign_client_to_site(
    site_id: str,
    body: ClientAssignRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """AGENCY-01: Assign client_name + client_email to a site owned by this agency."""
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    if not db_pool:
        raise HTTPException(status_code=503, detail="Datenbank nicht verfügbar.")
    result = await db_pool.execute(
        """UPDATE cookie_banner_configs
           SET client_name = $1,
               client_email = $2,
               updated_at = NOW()
           WHERE site_id = $3 AND user_id = $4""",
        body.client_name, body.client_email, site_id, user_id,
    )
    # asyncpg returns 'UPDATE N' string — 0 means site not owned by user
    if isinstance(result, str) and result.strip().upper().endswith(" 0"):
        raise HTTPException(status_code=404, detail="Site nicht gefunden oder nicht zugewiesen.")
    return {"ok": True, "site_id": site_id, "client_name": body.client_name, "client_email": body.client_email}


# =============================================================================
# AGENCY-02: Per-client grouping endpoint (Phase 10)
# Companion to /agency/stats — adds grouped view; existing endpoint untouched.
# =============================================================================

@router.get("/api/cookie-compliance/agency/clients")
async def get_agency_clients(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """AGENCY-02: Aggregated stats grouped by client_name for the current agency."""
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    if not db_pool:
        return {"clients": []}
    rows = await db_pool.fetch(
        """SELECT
             c.client_name,
             c.client_email,
             COUNT(DISTINCT c.site_id)                                          AS site_count,
             COALESCE(SUM(s.total_impressions), 0)                              AS total_impressions,
             COALESCE(SUM(s.accepted_all + s.accepted_partial), 0)              AS total_accepted
           FROM cookie_banner_configs c
           LEFT JOIN cookie_compliance_stats s
                  ON s.site_id = c.site_id
                 AND s.date >= CURRENT_DATE - INTERVAL '30 days'
           WHERE c.user_id = $1 AND c.client_name IS NOT NULL
           GROUP BY c.client_name, c.client_email
           ORDER BY c.client_name""",
        user_id,
    )
    clients = []
    for r in rows:
        total = r["total_impressions"] or 0
        accepted = r["total_accepted"] or 0
        clients.append({
            "client_name": r["client_name"],
            "client_email": r["client_email"],
            "site_count": r["site_count"],
            "total_impressions": total,
            "total_accepted": accepted,
            "acceptance_rate": round(accepted / total, 4) if total else 0.0,
        })
    return {"clients": clients}


# =============================================================================
# AGENCY-03: Logo upload (Phase 10) — PNG only, 2 MB max
# =============================================================================

@router.post("/api/cookie-compliance/agency/logo")
async def upload_agency_logo(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """AGENCY-03: Upload agency logo (PNG only, max 2 MB) and store path on users row."""
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    content = await file.read()
    if file.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Nur PNG-Logos werden unterstützt (kein SVG/JPEG).")
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Logo zu groß (max 2 MB).")
    if not db_pool:
        raise HTTPException(status_code=503, detail="Datenbank nicht verfügbar.")
    info = await file_storage.save_file(
        user_id=user_id,
        file_content=content,
        original_filename=file.filename or "logo.png",
        system_id="logos",
    )
    await db_pool.execute(
        "UPDATE users SET agency_logo_path = $1 WHERE id = $2",
        info["relative_path"], user_id,
    )
    return {"relative_path": info["relative_path"], "filename": info["filename"]}


@router.get("/api/cookie-compliance/agency/logo")
async def get_agency_logo(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """AGENCY-03: Return the logo URL if the agency has uploaded one."""
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    if not db_pool:
        return {"logo_url": None}
    row = await db_pool.fetchrow(
        "SELECT agency_logo_path FROM users WHERE id = $1", user_id
    )
    if not row or not row["agency_logo_path"]:
        return {"logo_url": None}
    return {"logo_url": "/api/cookie-compliance/agency/logo/file"}


@router.get("/api/cookie-compliance/agency/logo/file")
async def serve_agency_logo_file(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """AGENCY-03: Serve the stored agency logo PNG via FileStorageService."""
    from fastapi.responses import Response as FastAPIResponse
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    if not db_pool:
        raise HTTPException(status_code=503, detail="Datenbank nicht verfügbar.")
    row = await db_pool.fetchrow(
        "SELECT agency_logo_path FROM users WHERE id = $1", user_id
    )
    if not row or not row["agency_logo_path"]:
        raise HTTPException(status_code=404, detail="Kein Logo hochgeladen.")
    logo_bytes = await file_storage.get_file(row["agency_logo_path"])
    if logo_bytes is None:
        raise HTTPException(status_code=404, detail="Logo-Datei nicht gefunden.")
    return FastAPIResponse(content=logo_bytes, media_type="image/png")


# =============================================================================
# AGENCY-02 + AGENCY-03: PDF report download per client (Phase 10)
# =============================================================================

_agency_pdf_generator = AgencyReportGenerator()


@router.get("/api/cookie-compliance/agency/client-report/{client_name}")
async def download_client_report(
    client_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """AGENCY-02 + AGENCY-03: Stream a branded PDF report for one client."""
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    if not db_pool:
        raise HTTPException(status_code=503, detail="Datenbank nicht verfuegbar.")

    # 1. Fetch per-site rows for this client. last_scan_url is on cookie_banner_configs.
    #    Latest compliance_score per site via scan_history LEFT JOIN LATERAL.
    rows = await db_pool.fetch(
        """SELECT
             c.site_id,
             c.last_scan_url,
             sh.compliance_score,
             sh.scan_data
           FROM cookie_banner_configs c
           LEFT JOIN LATERAL (
               SELECT compliance_score, scan_data
               FROM scan_history
               WHERE user_id = c.user_id
                 AND url = c.last_scan_url
               ORDER BY scan_timestamp DESC
               LIMIT 1
           ) sh ON true
           WHERE c.user_id = $1 AND c.client_name = $2""",
        user_id, client_name,
    )

    # 2. Build the sites list for the generator.
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "warning": 2, "low": 3, "info": 4}
    sites = []
    for r in rows:
        scan_data = r["scan_data"] or {}
        detected = scan_data.get("detected_issues", []) if isinstance(scan_data, dict) else []
        sorted_issues = sorted(
            detected,
            key=lambda i: severity_rank.get((i.get("severity") or "low").lower(), 9),
        )
        top_3 = [
            (i.get("title") or i.get("description") or "Unbekanntes Issue")
            for i in sorted_issues[:3]
        ]
        sites.append({
            "url": r["last_scan_url"] or r["site_id"],
            "compliance_score": r["compliance_score"],
            "top_issues": top_3,
        })

    # 3. Fetch agency logo bytes (if uploaded).
    logo_row = await db_pool.fetchrow(
        "SELECT agency_logo_path FROM users WHERE id = $1", user_id,
    )
    logo_bytes = None
    if logo_row and logo_row["agency_logo_path"]:
        logo_bytes = await file_storage.get_file(logo_row["agency_logo_path"])

    # 4. Generate the PDF.
    pdf_bytes = _agency_pdf_generator.generate(
        client_name=client_name,
        sites=sites,
        agency_logo_bytes=logo_bytes,
    )

    # 5. Stream it.
    safe_name = "".join(c for c in client_name if c.isalnum() or c in "-_") or "report"
    headers = {
        "Content-Disposition": f'attachment; filename="complyo_report_{safe_name}.pdf"',
    }
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
