"""
Complyo Widget API Routes
Endpoints for serving and managing widgets
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from accessibility_templates import AccessibilityTemplates

router = APIRouter()

# Widget directory
WIDGET_DIR = os.path.join(os.path.dirname(__file__), 'widgets')


class WidgetTrackingEvent(BaseModel):
    siteId: str
    event: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


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
async def serve_accessibility_widget():
    """
    Serve the Accessibility Widget JavaScript
    """
    widget_path = os.path.join(WIDGET_DIR, 'accessibility.js')
    
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

