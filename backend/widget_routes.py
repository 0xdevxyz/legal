"""
Complyo Widget API Routes
Endpoints for serving and managing widgets
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import FileResponse, Response, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from datetime import datetime
import time
import asyncpg
from accessibility_templates import AccessibilityTemplates
from accessibility_patch_generator import AccessibilityPatchGenerator
import aiohttp
from accessibility_fix_saver import AccessibilityFixSaver

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
async def serve_cookie_consent_widget():
    """
    Serve the Cookie Consent Widget JavaScript (Legacy v1)
    """
    widget_path = os.path.join(WIDGET_DIR, 'cookie_consent.js')
    
    if not os.path.exists(widget_path):
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Read widget content
    with open(widget_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Return as JavaScript with correct MIME type
    return Response(
        content=content,
        media_type='application/javascript',
        headers={
            'Cache-Control': 'public, max-age=3600',
            'Access-Control-Allow-Origin': '*'
        }
    )

@router.get("/api/widgets/privacy-manager.js")
@router.get("/api/widgets/cookie-compliance.js")  # Legacy support
async def serve_cookie_compliance_widget(site_id: Optional[str] = None):
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
        return Response(
            content=combined_code,
            media_type='application/javascript',
            headers={
                'Cache-Control': 'public, max-age=300',  # 5 Minuten Cache
                'Access-Control-Allow-Origin': '*',
                'X-Complyo-Version': '2.0.0',
                'ETag': '2.0.0-service-selection'  # Cache-Busting
            }
        )
        
    except Exception as e:
        print(f"Error serving cookie compliance widget: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve widget: {str(e)}")


@router.get("/api/widgets/accessibility.js")
async def serve_accessibility_widget(version: str = "6"):
    """
    Serve the Accessibility Widget JavaScript
    
    Args:
        version: Widget version (4, 5 or 6, default 6)
    """
    # V6 ist jetzt default - Next Level Edition mit Grid-Layout
    if version == "6":
        widget_filename = 'accessibility-v6.js'
    elif version == "5":
        widget_filename = 'accessibility-v5.js'
    else:
        widget_filename = 'accessibility.js'
    
    widget_path = os.path.join(WIDGET_DIR, widget_filename)
    
    if not os.path.exists(widget_path):
        raise HTTPException(status_code=404, detail=f"Widget {widget_filename} not found")
    
    # Read widget content
    with open(widget_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Return as JavaScript with correct MIME type
    return Response(
        content=content,
        media_type='application/javascript',
        headers={
            'Cache-Control': 'public, max-age=60',  # 60 Sekunden Cache für schnelle Updates
            'Access-Control-Allow-Origin': '*',
            'X-Complyo-Widget-Version': '6.1.0'
        }
    )


@router.post("/api/widgets/track")
async def track_widget_event(event: WidgetTrackingEvent):
    """
    Track widget events (consent decisions, accessibility usage, etc.)
    """
    try:
        # Log event (in production, save to database)
        print(f"[Widget Tracking] {event.siteId} - {event.event} at {event.timestamp}")
        
        # TODO: Save to database for analytics
        # await db_pool.execute(
        #     "INSERT INTO widget_events (site_id, event_type, timestamp, metadata) VALUES ($1, $2, $3, $4)",
        #     event.siteId, event.event, event.timestamp, event.metadata
        # )
        
        return {
            "success": True,
            "message": "Event tracked"
        }
    
    except Exception as e:
        print(f"Error tracking widget event: {e}")
        # Don't fail the request
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
    try:
        # TODO: Implement with database
        # usage_count = await db_service.fetchval(
        #     """SELECT COUNT(*) FROM widget_usage_stats
        #     WHERE site_id = $1 AND timestamp > NOW() - INTERVAL '30 days'""",
        #     site_id
        # )
        # 
        # if usage_count > 100:
        #     await _send_upsell_notification(site_id, usage_count)
        
        pass
    except Exception as e:
        print(f"Error checking upsell opportunity: {e}")


@router.get("/api/widgets/config/{site_id}")
async def get_widget_config(site_id: str):
    """
    Get widget configuration for a specific site
    """
    # TODO: Fetch from database
    # For now, return default config
    
    return {
        "success": True,
        "config": {
            "cookie_consent": {
                "enabled": True,
                "position": "bottom",
                "primaryColor": "#6366f1",
                "accentColor": "#8b5cf6",
                "language": "de"
            },
            "accessibility": {
                "enabled": True,
                "features": ["contrast", "font-size", "keyboard-nav", "skip-links", "alt-text-fallback"],
                "showToolbar": True
            }
        }
    }


@router.get("/api/widgets/snippet/{widget_type}")
async def get_widget_snippet(widget_type: str, site_id: str):
    """
    Get HTML snippet to embed widget
    """
    base_url = "https://api.complyo.tech"
    
    snippets = {
        "cookie-consent": f'<script src="{base_url}/api/widgets/cookie-consent.js" data-site-id="{site_id}"></script>',
        "accessibility": f'<script src="{base_url}/api/widgets/accessibility.js" data-site-id="{site_id}" data-complyo-a11y></script>',
        "all": f'''<!-- Complyo Widgets -->
<script src="{base_url}/api/widgets/cookie-consent.js" data-site-id="{site_id}"></script>
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
    db_pool: asyncpg.Pool = Depends(lambda: None),  # TODO: Proper dependency injection
    # user_id: int = Depends(get_current_user_id)  # TODO: Add auth
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
            user_id=1,  # TODO: Real user_id
            fixes=fixes
        )
        
        # Create download ID (timestamp-based)
        download_id = f"{site_id}_{int(time.time())}"
        
        # TODO: Store in temporary storage (Redis/file)
        # For now: Return immediately
        
        # Store ZIP in memory for this session (simplified)
        # In production: Use Redis or filesystem
        if not hasattr(generate_accessibility_patches, '_temp_storage'):
            generate_accessibility_patches._temp_storage = {}
        
        generate_accessibility_patches._temp_storage[download_id] = zip_buffer.getvalue()
        
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
        # Retrieve from temporary storage
        if not hasattr(generate_accessibility_patches, '_temp_storage'):
            raise HTTPException(status_code=404, detail="Download nicht gefunden oder abgelaufen")
        
        zip_content = generate_accessibility_patches._temp_storage.get(download_id)
        
        if not zip_content:
            raise HTTPException(status_code=404, detail="Download nicht gefunden oder abgelaufen")
        
        # Return as streaming response
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
