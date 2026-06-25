"""
Complyo Widget API Routes
Endpoints for serving and managing widgets
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import time
import gzip
import hashlib
import asyncpg
import json
import logging
from accessibility_templates import AccessibilityTemplates
from accessibility_patch_generator import AccessibilityPatchGenerator
import aiohttp
from accessibility_fix_saver import AccessibilityFixSaver
from dependencies import get_current_user, get_db

router = APIRouter()

# Database pool (wird von main.py gesetzt)
db_pool = None

def set_db_pool(pool):
    """Setzt den Database Pool (called from main.py)"""
    global db_pool
    return pool

# Widget directory
WIDGET_DIR = os.path.join(os.path.dirname(__file__), 'widgets')


class WidgetTrackingEvent(BaseModel):
    siteId: str
    event: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class WidgetAnalyticsRequest(BaseModel):
    site_id: str
    feature: str
    value: Any
    timestamp: int
    session_id: str


@router.get("/api/widgets/cookie-consent.js")
async def serve_cookie_consent_widget(request: Request):
    """
    Serve the Cookie Consent Widget JavaScript (Legacy v1)
    """
    widget_path = os.path.join(WIDGET_DIR, 'cookie_consent.js')
    
    if not os.path.exists(widget_path):
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Read widget content
    with open(widget_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    headers = {
        'Cache-Control': 'public, max-age=86400, stale-while-revalidate=3600',
        'Access-Control-Allow-Origin': '*',
        'ETag': f'"{hashlib.md5(content.encode()).hexdigest()}"',
        'Vary': 'Accept-Encoding',
    }

    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' in accept_encoding:
        compressed = gzip.compress(content.encode('utf-8'))
        headers['Content-Encoding'] = 'gzip'
        return Response(
            content=compressed,
            media_type='application/javascript',
            headers=headers,
        )

    return Response(
        content=content,
        media_type='application/javascript',
        headers=headers,
    )

@router.get("/api/widgets/privacy-manager.js")
@router.get("/api/widgets/cookie-compliance.js")  # Legacy support
async def serve_cookie_compliance_widget(request: Request, site_id: Optional[str] = None):
    """
    Serve the complete Cookie Compliance Widget (v2)
    
    Includes:
    - Cookie Banner v2
    - Content Blocker
    - Config injection from database
    
    Query params:
    - site_id: Optional site identifier for custom configuration
    
    Note: Also available at /privacy-manager.js to avoid ad-blocker issues
    """
    try:
        # Load both widgets
        banner_path = os.path.join(WIDGET_DIR, 'cookie_banner_v2.js')
        blocker_path = os.path.join(WIDGET_DIR, 'content_blocker.js')
        
        if not os.path.exists(banner_path) or not os.path.exists(blocker_path):
            raise HTTPException(status_code=404, detail="Widget files not found")
        
        # Read widgets
        with open(banner_path, 'r', encoding='utf-8') as f:
            banner_code = f.read()
        
        with open(blocker_path, 'r', encoding='utf-8') as f:
            blocker_code = f.read()
        
        # Combine widgets
        combined_code = f"""/**
 * Complyo Cookie Compliance Widget - Combined Bundle
 * Version: 2.0.0
 * © 2025 Complyo - All rights reserved
 */

/* ========== Content Blocker (loads first to block before page renders) ========== */
{blocker_code}

/* ========== Cookie Banner ========== */
{banner_code}
"""
        
        # Return combined widget
        headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Access-Control-Allow-Origin': '*',
            'X-Complyo-Version': '2.0.0',
            'ETag': f'"{hashlib.md5(combined_code.encode()).hexdigest()}"',
            'Vary': 'Accept-Encoding',
        }

        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' in accept_encoding:
            compressed = gzip.compress(combined_code.encode('utf-8'))
            headers['Content-Encoding'] = 'gzip'
            return Response(
                content=compressed,
                media_type='application/javascript',
                headers=headers,
            )

        return Response(
            content=combined_code,
            media_type='application/javascript',
            headers=headers,
        )
        
    except Exception as e:
        print(f"Error serving cookie compliance widget: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve widget: {str(e)}")


@router.get("/api/widgets/accessibility.js")
async def serve_accessibility_widget(request: Request, version: str = "6"):
    """
    Serve the Accessibility Widget JavaScript (v6 only)
    """
    widget_filename = 'accessibility-v6.js'
    
    widget_path = os.path.join(WIDGET_DIR, widget_filename)
    
    if not os.path.exists(widget_path):
        raise HTTPException(status_code=404, detail=f"Widget {widget_filename} not found")
    
    # Read widget content
    with open(widget_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Return as JavaScript with correct MIME type
    headers = {
        'Cache-Control': 'public, max-age=86400, stale-while-revalidate=3600',
        'Access-Control-Allow-Origin': '*',
        'X-Complyo-Widget-Version': '6.1.0',
        'ETag': f'"{hashlib.md5(content.encode()).hexdigest()}"',
        'Vary': 'Accept-Encoding',
    }

    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' in accept_encoding:
        compressed = gzip.compress(content.encode('utf-8'))
        headers['Content-Encoding'] = 'gzip'
        return Response(
            content=compressed,
            media_type='application/javascript',
            headers=headers,
        )

    return Response(
        content=content,
        media_type='application/javascript',
        headers=headers,
    )


@router.post("/api/widgets/track")
async def track_widget_event(event: WidgetTrackingEvent):
    """
    Track widget events (consent decisions, accessibility usage, etc.)
    """
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO widget_events
                       (site_id, widget_type, event_name, event_data)
                       VALUES ($1, $2, $3, $4)""",
                    event.siteId,
                    "tracking",
                    event.event,
                    json.dumps(event.metadata) if event.metadata else "{}",
                )
        else:
            logger = logging.getLogger(__name__)
            logger.warning(f"[Widget Tracking] DB not available - {event.siteId}: {event.event}")

        return {
            "success": True,
            "message": "Event tracked"
        }

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error tracking widget event: {e}")
        return {
            "success": False,
            "message": "Tracking failed"
        }


@router.post("/api/widgets/analytics")
async def track_widget_analytics(
    data: WidgetAnalyticsRequest,
    background_tasks: BackgroundTasks
):
    """
    Track widget usage analytics for Upsell-Insights
    
    Tracks feature usage patterns to identify:
    - Most used features
    - User preferences
    - Potential for permanent deployment
    
    Args:
        data: Analytics data (feature, value, session_id, etc.)
        background_tasks: Background task queue
        
    Returns:
        Success response
    """
    try:
        # ✅ Save to database
        if db_pool:
            async with db_pool.acquire() as conn:
                # Use the stored procedure for efficient tracking
                await conn.execute(
                    "SELECT track_widget_feature($1, $2, $3, $4)",
                    data.site_id,
                    data.session_id,
                    data.feature,
                    json.dumps({"value": data.value, "timestamp": data.timestamp}) if data.value else None
                )
            
            logger.info(f"📊 Widget Analytics: Site={data.site_id}, Feature={data.feature}, Session={data.session_id[:8]}...")
        else:
            # Fallback: Log wenn DB nicht verfügbar
            logger.warning(f"[Widget Analytics] DB not available - Site: {data.site_id}, Feature: {data.feature}")
        
        return {
            "success": True,
            "message": "Analytics tracked"
        }
    
    except Exception as e:
        print(f"Error tracking widget analytics: {e}")
        # Don't fail the request - analytics shouldn't break the widget
        return {
            "success": True,  # Return success even on error
            "message": "Analytics tracking failed silently"
        }


async def _check_upsell_opportunity(site_id: str):
    """
    Background task to check if user should see upsell notification

    Checks:
    - Total usage count > 100 (widget is heavily used)
    - Specific features used frequently (font-size > 50x)

    If threshold met: Send notification to dashboard
    """
    _logger = logging.getLogger(__name__)
    try:
        if not db_pool:
            return

        async with db_pool.acquire() as conn:
            usage_count = await conn.fetchval(
                """SELECT COUNT(*) FROM widget_usage_stats
                   WHERE site_id = $1
                   AND date > CURRENT_DATE - INTERVAL '30 days'""",
                site_id,
            )

        if usage_count and usage_count > 100:
            _logger.info(
                f"[Upsell] Site {site_id} hit upsell threshold: {usage_count} events in 30 days"
            )

    except Exception as e:
        _logger = logging.getLogger(__name__)
        _logger.error(f"Error checking upsell opportunity: {e}")


@router.get("/api/widgets/config/{site_id}")
async def get_widget_config(site_id: str):
    """
    Get widget configuration for a specific site
    """
    _logger = logging.getLogger(__name__)
    default_config = {
        "cookie_consent": {
            "enabled": True,
            "position": "bottom",
            "primaryColor": "#6366f1",
            "accentColor": "#8b5cf6",
            "language": "de",
        },
        "accessibility": {
            "enabled": True,
            "features": ["contrast", "font-size", "keyboard-nav", "skip-links", "alt-text-fallback"],
            "showToolbar": True,
        },
    }

    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT layout, primary_color, accent_color, position, language
                       FROM cookie_banner_configs
                       WHERE site_id = $1 AND is_active = TRUE
                       LIMIT 1""",
                    site_id,
                )
            if row:
                default_config["cookie_consent"].update({
                    "position": row["position"] or "bottom",
                    "primaryColor": row["primary_color"] or "#6366f1",
                    "accentColor": row["accent_color"] or "#8b5cf6",
                    "language": row.get("language") or "de",
                })
        except Exception as e:
            _logger.warning(f"[Widget Config] Could not load config for {site_id}: {e}")

    # 🔒 Laufzeit-Lizenzprüfung: Wurde die Website im Dashboard entfernt, ist die
    # Lizenz entzogen → das Barrierefreiheits-Widget rendert dann nicht mehr.
    license_active = True
    if db_pool:
        try:
            from license_check import site_has_active_license
            license_active = await site_has_active_license(db_pool, site_id)
        except Exception as e:
            _logger.warning(f"[Widget Config] License check failed for {site_id}: {e}")

    return {
        "success": True,
        "license_active": license_active,
        "config": default_config,
    }


@router.get("/api/widgets/snippet/{widget_type}")
async def get_widget_snippet(widget_type: str, site_id: str):
    """
    Get HTML snippet to embed widget
    """
    base_url = "https://api.complyo.de"
    
    snippets = {
        "cookie-consent": f'<script src="{base_url}/api/widgets/cookie-compliance.js" data-site-id="{site_id}"></script>',
        "accessibility": f'<script src="{base_url}/api/widgets/accessibility.js" data-site-id="{site_id}" data-complyo-a11y></script>',
        "all": f'''<!-- Complyo Widgets -->
<script src="{base_url}/api/widgets/cookie-compliance.js" data-site-id="{site_id}"></script>
<script src="{base_url}/api/widgets/accessibility.js" data-site-id="{site_id}" data-complyo-a11y></script>'''
    }
    
    snippet = snippets.get(widget_type)
    
    if not snippet:
        raise HTTPException(status_code=404, detail="Widget type not found")
    
    return {
        "success": True,
        "widget_type": widget_type,
        "snippet": snippet,
        "instructions": "Fügen Sie diesen Code in den <head>-Bereich Ihrer Website ein."
    }


@router.get("/api/widgets/accessibility-templates")
async def get_accessibility_templates():
    """
    Get all accessibility code templates
    Returns different WCAG compliance levels with actual code
    """
    templates = AccessibilityTemplates.get_all_templates()
    
    return JSONResponse(
        content={
            "success": True,
            "templates": templates,
            "version": "3.0.0"
        },
        headers={
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=1800'
        }
    )


@router.get("/api/widgets/accessibility-templates/{template_id}")
async def get_accessibility_template(template_id: str):
    """
    Get a specific accessibility template by ID
    """
    template = AccessibilityTemplates.get_template_by_id(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return JSONResponse(
        content={
            "success": True,
            "template": template
        },
        headers={
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=1800'
        }
    )


@router.get("/api/accessibility/alt-text-fixes")
async def get_alt_text_fixes_for_widget(site_id: str):
    """
    Gibt AI-generierte Alt-Texte für Widget-Runtime-Injection zurück
    
    Dies ist der Hybrid-Ansatz:
    - Widget lädt diese Alt-Texte und fügt sie runtime ins DOM ein
    - Für sofortige Barrierefreiheit ohne Code-Änderungen
    - Später können Patches für permanente SEO-Optimierung heruntergeladen werden
    
    Args:
        site_id: Site-Identifier
        
    Returns:
        JSON mit Alt-Text-Fixes
    """
    try:
        # Lade Fixes aus Datenbank
        fixes = []
        
        if db_pool:
            fix_saver = AccessibilityFixSaver(db_pool)
            fixes = await fix_saver.get_fixes_for_site(site_id, status='approved')
        else:
            # Fallback: Demo-Daten wenn DB nicht verfügbar
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"DB pool not available, using demo data for site_id={site_id}")
            
            fixes = [
                {
                    "image_src": "/images/logo.png",
                    "image_filename": "logo.png",
                    "suggested_alt": "Firmenlogo Mustermann GmbH",
                    "page_url": "/",
                    "confidence": 0.95
                },
                {
                    "image_src": "/images/team.jpg",
                    "image_filename": "team.jpg",
                    "suggested_alt": "Team-Foto der Mitarbeiter",
                    "page_url": "/about",
                    "confidence": 0.89
                },
                {
                    "image_src": "/images/product.png",
                    "image_filename": "product.png",
                    "suggested_alt": "Produktabbildung Premium-Modell",
                    "page_url": "/products",
                    "confidence": 0.92
                }
            ]
        
        return JSONResponse(
            content={
                "success": True,
                "fixes": fixes,
                "count": len(fixes),
                "mode": "runtime",
                "version": "4.0.0"
            },
            headers={
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=600'  # 10 Minuten Cache
            }
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading alt-text fixes: {e}")
        
        return JSONResponse(
            content={
                "success": False,
                "fixes": [],
                "error": str(e)
            },
            headers={
                'Access-Control-Allow-Origin': '*'
            }
        )


@router.post("/api/accessibility/patches/generate")
async def generate_accessibility_patches(
    site_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db),
):
    """
    Generiert Barrierefreiheits-Patches als ZIP-Download
    
    Teil des Hybrid-Modells:
    - Widget liefert sofortige Runtime-Fixes
    - Diese Patches liefern permanente SEO-optimierte Lösung
    
    Args:
        site_id: Site-Identifier
        background_tasks: Background task queue
        
    Returns:
        Download-URL für ZIP-Datei
    """
    try:
        # ✅ FIX: Load real fixes from database
        fixes = []
        
        try:
            from main import get_db_pool
            db_pool = await get_db_pool()
            
            # Query Alt-Text Fixes
            alt_text_query = """
                SELECT 
                    'alt_text' as type,
                    page_url,
                    image_src,
                    image_filename,
                    suggested_alt,
                    confidence
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1
                  AND status = 'approved'
                ORDER BY created_at DESC
            """
            
            alt_text_fixes = await db_pool.fetch(alt_text_query, site_id)
            fixes.extend([dict(fix) for fix in alt_text_fixes])
            
            logger.info(f"✅ Loaded {len(fixes)} real fixes from database for site {site_id}")
            
        except Exception as db_error:
            logger.warning(f"⚠️ Could not load fixes from DB: {db_error}. Using demo data.")
            # Fallback to demo data if DB not available
            fixes = [
                {
                    "type": "alt_text",
                    "page_url": "/",
                    "image_src": "/images/logo.png",
                    "image_filename": "logo.png",
                    "suggested_alt": "Firmenlogo",
                    "confidence": 0.95
                },
                {
                    "type": "alt_text",
                    "page_url": "/",
                    "image_src": "/images/hero.jpg",
                    "image_filename": "hero.jpg",
                    "suggested_alt": "Hero-Bild der Website",
                    "confidence": 0.89
                }
            ]
        
        # Generate patches
        generator = AccessibilityPatchGenerator()
        zip_buffer = await generator.generate_patch_bundle(
            site_id=site_id,
            user_id=current_user["id"],
            fixes=fixes
        )
        
        # Create download ID (timestamp-based)
        download_id = f"{site_id}_{int(time.time())}"
        
        import tempfile
        import os as _os
        tmp_dir = tempfile.gettempdir()
        tmp_path = _os.path.join(tmp_dir, f"complyo_patches_{download_id}.zip")
        with open(tmp_path, "wb") as f:
            f.write(zip_buffer.getvalue())
        
        return {
            "success": True,
            "download_id": download_id,
            "download_url": f"/api/accessibility/patches/download/{download_id}",
            "file_size": len(zip_buffer.getvalue()),
            "expires_in": "1 Stunde",
            "patches_count": len(demo_fixes)
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating patches: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Generieren der Patches: {str(e)}"
        )


@router.get("/api/accessibility/patches/download/{download_id}")
async def download_accessibility_patches(download_id: str):
    """
    Lädt generierte Barrierefreiheits-Patches herunter
    
    Args:
        download_id: Download-Identifier (von generate-Endpoint)
        
    Returns:
        ZIP-Datei mit Patches
    """
    try:
        import tempfile
        import os as _os
        tmp_path = _os.path.join(tempfile.gettempdir(), f"complyo_patches_{download_id}.zip")
        
        if not _os.path.exists(tmp_path):
            raise HTTPException(status_code=404, detail="Download nicht gefunden oder abgelaufen")
        
        with open(tmp_path, "rb") as f:
            zip_content = f.read()
        
        _os.unlink(tmp_path)
        
        return StreamingResponse(
            iter([zip_content]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=complyo-barrierefreiheit-patches-{download_id}.zip",
                "Content-Length": str(len(zip_content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error downloading patches: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Download: {str(e)}"
        )



@router.get("/api/widgets/analytics/{site_id}")
async def get_widget_analytics(site_id: str, days: int = 30):
    """
    Holt Widget-Analytics für Dashboard
    
    Args:
        site_id: Site-Identifier
        days: Anzahl Tage zurück (default 30)
        
    Returns:
        Analytics-Statistiken
    """
    try:
        if not db_pool:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Database not available"
                },
                headers={'Access-Control-Allow-Origin': '*'}
            )
        
        async with db_pool.acquire() as conn:
            # 1. Feature-Popularität
            feature_stats = await conn.fetch(
                f"""
                SELECT 
                    feature,
                    COUNT(*) as usage_count,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM widget_analytics
                WHERE site_id = $1 
                  AND timestamp > NOW() - INTERVAL '{days} days'
                  AND event_type = 'feature_toggle'
                  AND feature IS NOT NULL
                GROUP BY feature
                ORDER BY usage_count DESC
                """,
                site_id
            )
            
            # 2. Tägliche Nutzung
            daily_stats = await conn.fetch(
                f"""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as events,
                    COUNT(DISTINCT session_id) as sessions
                FROM widget_analytics
                WHERE site_id = $1 
                  AND timestamp > NOW() - INTERVAL '{days} days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 30
                """,
                site_id
            )
            
            # 3. Gesamt-Statistiken
            total_stats = await conn.fetchrow(
                f"""
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(DISTINCT DATE(timestamp)) as active_days
                FROM widget_analytics
                WHERE site_id = $1 
                  AND timestamp > NOW() - INTERVAL '{days} days'
                """,
                site_id
            )
        
        return JSONResponse(
            content={
                "success": True,
                "site_id": site_id,
                "period_days": days,
                "features": [
                    {
                        "feature": row['feature'],
                        "usage_count": row['usage_count'],
                        "unique_sessions": row['unique_sessions']
                    }
                    for row in feature_stats
                ],
                "daily_usage": [
                    {
                        "date": row['date'].isoformat(),
                        "events": row['events'],
                        "sessions": row['sessions']
                    }
                    for row in daily_stats
                ],
                "totals": {
                    "total_events": total_stats['total_events'],
                    "total_sessions": total_stats['total_sessions'],
                    "active_days": total_stats['active_days']
                } if total_stats else {}
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading widget analytics: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e)
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )


@router.get("/api/accessibility/widget/status")
async def check_widget_status(website_url: str, site_id: str):
    """
    ✅ Prüft ob das Complyo Widget auf einer Website eingebunden ist
    
    Args:
        website_url: URL der zu prüfenden Website
        site_id: Site-Identifier
        
    Returns:
        Status mit Details zur Widget-Integration
    """
    try:
        # Normalisiere URL
        if not website_url.startswith('http'):
            website_url = f'https://{website_url}'
        
        # Lade HTML von Website
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(website_url, allow_redirects=True) as response:
                if response.status != 200:
                    return JSONResponse(
                        content={
                            "success": True,
                            "is_installed": False,
                            "status": "website_not_reachable",
                            "message": f"Website nicht erreichbar (HTTP {response.status})",
                            "checked_url": website_url
                        },
                        headers={'Access-Control-Allow-Origin': '*'}
                    )
                
                html_content = await response.text()
                
                # Prüfe auf Widget-Script
                widget_patterns = [
                    'accessibility.js',
                    'accessibility-v',
                    'data-site-id',
                    'complyo',
                    'ComplyoAccessibilityWidget'
                ]
                
                found_patterns = []
                for pattern in widget_patterns:
                    if pattern.lower() in html_content.lower():
                        found_patterns.append(pattern)
                
                # Prüfe speziell auf site-id
                has_site_id = f'data-site-id="{site_id}"' in html_content or f"data-site-id='{site_id}'" in html_content
                has_any_site_id = 'data-site-id=' in html_content
                
                is_installed = len(found_patterns) >= 2  # Mindestens 2 Patterns gefunden
                
                return JSONResponse(
                    content={
                        "success": True,
                        "is_installed": is_installed,
                        "has_correct_site_id": has_site_id,
                        "has_any_site_id": has_any_site_id,
                        "found_patterns": found_patterns,
                        "status": "installed" if is_installed else "not_installed",
                        "message": "Widget ist korrekt eingebunden ✅" if is_installed and has_site_id else 
                                   "Widget gefunden, aber Site-ID fehlt oder ist falsch" if is_installed and not has_site_id else
                                   "Widget nicht gefunden",
                        "checked_url": website_url,
                        "expected_site_id": site_id
                    },
                    headers={'Access-Control-Allow-Origin': '*'}
                )
    
    except aiohttp.ClientError as e:
        return JSONResponse(
            content={
                "success": True,
                "is_installed": False,
                "status": "connection_error",
                "message": f"Verbindungsfehler: {str(e)}",
                "checked_url": website_url
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking widget status: {e}", exc_info=True)
        
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "message": "Fehler beim Prüfen des Widget-Status"
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )


# =============================================================================
# Cookie Scanner Endpoints
# =============================================================================

class ScanRequest(BaseModel):
    url: str
    follow_links: int = 0


# NOTE: Pfad umbenannt von "/api/cookie-compliance/scan", um die Routen-Kollision
# mit cookie_compliance_routes.scan_website aufzulösen. Dieser Background-Handler
# beschattete den Wizard-Endpoint (schreibt in die nicht existente Tabelle
# cookie_scan_results und persistiert NICHTS in cookie_banner_configs) und führte
# zur Endlosschleife der Cookie-Ersteinrichtung.
@router.post("/api/cookie-compliance/scan-background")
async def trigger_cookie_scan(
    body: ScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Startet einen automatischen Cookie-Scan für eine URL.
    Der Scan läuft im Hintergrund; Ergebnis wird in der DB gespeichert.
    """
    from compliance_engine.automated_cookie_scanner import CookieScanner

    url = body.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    site_id = current_user.get("site_id") or url

    async def run_scan():
        try:
            scanner = CookieScanner(timeout_ms=20000)
            result  = await scanner.scan(url, follow_links=body.follow_links)

            cookies_json   = json.dumps([c.__dict__ for c in result.cookies])
            services_json  = json.dumps([s.__dict__ for s in result.services])

            await db.execute(
                """
                INSERT INTO cookie_scan_results
                    (site_id, url, scanned_at, cookies, services,
                     has_cmp, cmp_name, config_hash, scan_duration_ms, error)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                ON CONFLICT (site_id) DO UPDATE SET
                    url              = EXCLUDED.url,
                    scanned_at       = EXCLUDED.scanned_at,
                    cookies          = EXCLUDED.cookies,
                    services         = EXCLUDED.services,
                    has_cmp          = EXCLUDED.has_cmp,
                    cmp_name         = EXCLUDED.cmp_name,
                    config_hash      = EXCLUDED.config_hash,
                    scan_duration_ms = EXCLUDED.scan_duration_ms,
                    error            = EXCLUDED.error
                """,
                site_id, url, result.scanned_at,
                cookies_json, services_json,
                result.has_cmp, result.cmp_name,
                result.config_hash, result.scan_duration_ms,
                result.error
            )
            logging.getLogger(__name__).info(
                f"[Scanner] {url} – {len(result.cookies)} Cookies, "
                f"{len(result.services)} Services, {result.scan_duration_ms}ms"
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"[Scanner] Background-Fehler: {e}", exc_info=True)

    background_tasks.add_task(run_scan)

    return JSONResponse(
        content={"success": True, "message": "Scan gestartet", "url": url},
        headers={"Access-Control-Allow-Origin": "*"}
    )


@router.get("/api/cookie-compliance/scan/{site_id}")
async def get_scan_result(
    site_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Gibt das letzte Scan-Ergebnis für eine Site zurück.
    """
    row = await db.fetchrow(
        """
        SELECT site_id, url, scanned_at, cookies, services,
               has_cmp, cmp_name, config_hash, scan_duration_ms, error
        FROM cookie_scan_results
        WHERE site_id = $1
        ORDER BY scanned_at DESC
        LIMIT 1
        """,
        site_id
    )

    if not row:
        return JSONResponse(
            content={"success": False, "message": "Kein Scan-Ergebnis gefunden"},
            status_code=404,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    return JSONResponse(
        content={
            "success":        True,
            "site_id":        row["site_id"],
            "url":            row["url"],
            "scanned_at":     str(row["scanned_at"]),
            "cookies":        json.loads(row["cookies"]),
            "services":       json.loads(row["services"]),
            "has_cmp":        row["has_cmp"],
            "cmp_name":       row["cmp_name"],
            "config_hash":    row["config_hash"],
            "scan_duration_ms": row["scan_duration_ms"],
            "error":          row["error"],
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )
