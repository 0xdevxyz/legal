"""
Cookie Compliance Routes
API endpoints for Cookie-Consent-Management
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import asyncpg
import hashlib
import uuid
from datetime import datetime, date, timedelta
import json
import logging
from cookie_scanner_service import cookie_scanner
from functools import wraps

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)  # auto_error=False für optionale Auth

# Global database pool and auth service (set by main.py)
db_pool = None
auth_service = None  # Wird von main_production.py gesetzt
db_service = None  # Wird von main_production.py gesetzt für Modul-Checks

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
    title: str
    description: str
    accept_all: str
    reject_all: str
    accept_selected: str
    settings: str
    privacy_policy: str
    imprint: str

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

# ============================================================================
# Helper Functions
# ============================================================================

def hash_ip_address(ip: str) -> str:
    """Hash IP address with SHA256 for privacy"""
    if not ip:
        return ""
    return hashlib.sha256(ip.encode()).hexdigest()

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
        # Get IP and hash it
        ip_address = consent.ip_address or get_client_ip(request)
        ip_hash = hash_ip_address(ip_address) if ip_address else None
        
        # Get user agent
        user_agent = consent.user_agent or request.headers.get("User-Agent", "")[:500]
        
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
            # ✅ Wenn registered_site_id existiert, erstelle automatisch eine Config
            if registered_site_id:
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
        print(f"Error getting user config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


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
                RETURNING id
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
                RETURNING id
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
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get available cookie service templates
    
    Query params:
    - category: Filter by category (analytics, marketing, functional, necessary)
    - plan: Filter by required plan (ai, expert)
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
        # Get daily stats
        stats_query = """
            SELECT 
                date, total_impressions,
                accepted_all, accepted_partial, rejected_all,
                accepted_analytics, accepted_marketing, accepted_functional,
                service_stats
            FROM cookie_compliance_stats
            WHERE site_id = $1 
                AND date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY date DESC
        """ % days
        
        rows = await db_pool.fetch(stats_query, site_id)
        
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
        
        print(f"[Scan] Scanning {url} for site_id: {site_id}")
        
        # Scan website
        scan_result = await cookie_scanner.scan_website(url)
        
        if scan_result.get('error'):
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
                # Update existierende Config mit gefundenen Services
                await db_pool.execute("""
                    UPDATE cookie_banner_configs SET
                        services = $2::text[],
                        scan_completed_at = NOW(),
                        last_scan_url = $3,
                        updated_at = NOW()
                    WHERE site_id = $1
                """, site_id, service_keys_found, url)
                config_updated = True
                print(f"[Scan] ✅ Config updated for {site_id} with {len(service_keys_found)} services")
            else:
                # Erstelle neue Config mit gefundenen Services
                await db_pool.execute("""
                    INSERT INTO cookie_banner_configs (
                        site_id, services, scan_completed_at, last_scan_url, is_active
                    ) VALUES ($1, $2::text[], NOW(), $3, true)
                """, site_id, service_keys_found, url)
                config_updated = True
                print(f"[Scan] ✅ New config created for {site_id} with {len(service_keys_found)} services")
        
        return {
            "success": True,
            "url": url,
            "site_id": site_id,
            "detected_services": matched_services,
            "total_found": len(matched_services),
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
                "purposes": row['purposes'] or [],
                "legitimate_interests": row['legitimate_interests'] or [],
                "special_purposes": row['special_purposes'] or [],
                "features": row['features'] or [],
                "special_features": row['special_features'] or [],
                "policy_url": row['policy_url']
            })
        
        # TCF 2.2 Purposes
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
            "tcf_version": "2.2"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        # Get config and services
        config_query = """
            SELECT c.*, 
                   array_agg(s.name) as service_names,
                   array_agg(s.category) as service_categories,
                   array_agg(s.provider) as service_providers,
                   array_agg(s.description) as service_descriptions,
                   array_agg(s.cookies) as service_cookies
            FROM cookie_banner_configs c
            LEFT JOIN cookie_services s ON s.service_key = ANY(c.services)
            WHERE c.site_id = $1 AND c.is_active = true
            GROUP BY c.id
        """
        row = await db_pool.fetchrow(config_query, site_id)
        
        if not row:
            return {"success": False, "error": "Site not configured"}
        
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
            "format": "json"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

