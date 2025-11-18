"""
Cookie Compliance Routes
API endpoints for Cookie-Consent-Management
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import asyncpg
import hashlib
import uuid
from datetime import datetime, date, timedelta
import json
from cookie_scanner_service import cookie_scanner

router = APIRouter()

# Global database pool (set by main.py)
db_pool = None

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
        
        # Insert consent log
        insert_query = """
            INSERT INTO cookie_consent_logs (
                site_id, visitor_id, consent_categories, services_accepted,
                ip_address_hash, user_agent, revision_id, language, banner_shown
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, timestamp
        """
        
        result = await db_pool.fetchrow(
            insert_query,
            consent.site_id,
            consent.visitor_id,
            json.dumps(consent.consent_categories.dict()),
            json.dumps(consent.services_accepted) if consent.services_accepted else None,
            ip_hash,
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
                is_active, created_at, updated_at
            FROM cookie_banner_configs
            WHERE site_id = $1 AND is_active = true
        """
        
        row = await db_pool.fetchrow(query, site_id)
        
        if not row:
            # Return default configuration
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
                            "title": "🍪 Wir respektieren Ihre Privatsphäre",
                            "description": "Wir verwenden Cookies, um Ihre Erfahrung zu verbessern. Weitere Informationen finden Sie in unserer Datenschutzerklärung.",
                            "accept_all": "Alle akzeptieren",
                            "reject_all": "Ablehnen",
                            "accept_selected": "Auswahl akzeptieren",
                            "settings": "Einstellungen",
                            "privacy_policy": "Datenschutzerklärung",
                            "imprint": "Impressum"
                        },
                        "en": {
                            "title": "🍪 We respect your privacy",
                            "description": "We use cookies to enhance your experience. More information in our privacy policy.",
                            "accept_all": "Accept all",
                            "reject_all": "Reject",
                            "accept_selected": "Accept selection",
                            "settings": "Settings",
                            "privacy_policy": "Privacy Policy",
                            "imprint": "Imprint"
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
                    "is_active": True
                },
                "message": "Default configuration (not yet customized)"
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
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Create or update cookie banner configuration
    
    Requires authentication (user_id from session)
    """
    try:
        # TODO: Get user_id from session/auth
        # For now, use placeholder
        user_id = 1  # Replace with actual user from session
        
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
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Partially update banner configuration
    """
    try:
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
                template, plan_required, is_active,
                created_at, updated_at
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
    Scannt eine Website und erkennt automatisch verwendete Cookie-Services
    
    Body:
    - url: Website URL zum Scannen
    
    Returns:
    - detected_services: Liste erkannter Services
    - confidence: Konfidenz-Score pro Service
    """
    try:
        url = data.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        
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
        if scan_result['detected_services']:
            service_keys = scan_result['detected_services']
            placeholders = ','.join([f'${i+1}' for i in range(len(service_keys))])
            
            query = f"""
                SELECT service_key, name, category
                FROM cookie_services
                WHERE service_key = ANY($1::text[]) AND is_active = true
            """
            
            rows = await db_pool.fetch(query, service_keys)
            
            for row in rows:
                matched_services.append({
                    'service_key': row['service_key'],
                    'name': row['name'],
                    'category': row['category'],
                    'confidence': scan_result['confidence'].get(row['service_key'], 0.5)
                })
        
        return {
            "success": True,
            "url": url,
            "detected_services": matched_services,
            "total_found": len(matched_services),
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

