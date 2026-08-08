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
# Gemeinsame Ownership-Prüfung (definiert in alt_text_routes, Quelle:
# cookie_compliance_routes.get_user_site_ids). Kein Zyklus: alt_text_routes
# importiert widget_routes nicht.
from alt_text_routes import require_site_ownership

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


# Hinweis: Die frühere Route GET /api/widgets/cookie-consent.js (Legacy v1) wurde
# entfernt. Sie las die Datei backend/widgets/cookie_consent.js, die nicht (mehr)
# existiert → jeder Abruf lieferte 404. Kein Konsument nutzte diese URL (belegt per
# grep über backend/, dashboard-react/src, wordpress-plugin/, joomla-plugin/,
# channels/ – 0 Treffer außer der Route selbst). Der aktuelle Banner wird über
# /api/widgets/cookie-compliance.js bzw. /privacy-manager.js ausgeliefert (siehe unten).

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
        # i18n: 17-Sprachen-Übersetzungen, die window.COMPLYO_TRANSLATIONS setzen.
        # Der Banner liest window.COMPLYO_TRANSLATIONS (cookie_banner_v2.js), das ohne
        # diese Datei nie gesetzt wurde → Mehrsprachigkeit war tot. Muss VOR dem Banner
        # ausgeliefert werden, damit die globale Variable beim Init bereitsteht.
        translations_path = os.path.join(WIDGET_DIR, 'locales', 'translations.js')

        if not os.path.exists(banner_path) or not os.path.exists(blocker_path):
            raise HTTPException(status_code=404, detail="Widget files not found")

        # Read widgets
        with open(banner_path, 'r', encoding='utf-8') as f:
            banner_code = f.read()

        with open(blocker_path, 'r', encoding='utf-8') as f:
            blocker_code = f.read()

        # Übersetzungen optional laden (fehlende Datei darf das Widget nicht brechen)
        translations_code = ''
        if os.path.exists(translations_path):
            with open(translations_path, 'r', encoding='utf-8') as f:
                translations_code = f.read()

        # Combine widgets
        combined_code = f"""/**
 * Complyo Cookie Compliance Widget - Combined Bundle
 * Version: 2.0.0
 * © 2025 Complyo - All rights reserved
 */

/* ========== i18n Translations (sets window.COMPLYO_TRANSLATIONS before banner init) ========== */
{translations_code}

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
        raise HTTPException(status_code=500, detail="Failed to serve widget")


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

    # Die Remediation anhaengen — der Grund ist eine Luecke, die beim Ausrollen
    # aufgefallen ist:
    #
    # accessibility-v6.js holt ausschliesslich Alt-Texte, ueber einen eigenen
    # Endpunkt. Kontrast-, Struktur- und Linkname-Reparaturen laufen dagegen
    # ueber das Fix-Manifest, das nur a11y_remediation.js liest — und die Datei
    # wird unter einer ANDEREN Adresse ausgeliefert (/api/widgets/a11y-fixes.js).
    # Auf den Kundenseiten steht aber ueberall dieses Skript hier. Ergebnis:
    # alles ausser Alt-Texten erreichte niemanden, ohne dass es auffiel.
    #
    # Statt 25 Kunden ein zweites Skript einbauen zu lassen, kommen beide
    # Teile aus derselben Adresse. Die Remediation ist eine eigenstaendige
    # IIFE und liest ihre Konfiguration aus `script[data-site-id]` — also aus
    # genau dem Tag, mit dem dieses Skript geladen wurde.
    #
    # Doppelt gesetzte Alt-Texte sind kein Problem: beide Wege ueberschreiben
    # ein vorhandenes `alt` nie, wer zuerst kommt gewinnt.
    remediation_path = os.path.join(WIDGET_DIR, 'a11y_remediation.js')
    if os.path.exists(remediation_path):
        with open(remediation_path, 'r', encoding='utf-8') as f:
            content += "\n;/* --- complyo a11y remediation (Fix-Manifest) --- */\n" + f.read()
    else:
        logging.getLogger(__name__).warning(
            "a11y_remediation.js fehlt — Kontrast-, Struktur- und "
            "Linkname-Reparaturen werden nicht ausgeliefert"
        )
    
    # Return as JavaScript with correct MIME type
    etag = f'"{hashlib.md5(content.encode()).hexdigest()}"'
    headers = {
        # no-cache = darf gecacht werden, MUSS aber bei jedem Load per ETag
        # revalidiert werden. So erscheinen Widget-Updates sofort, während
        # unveraenderte Inhalte als 304 (ohne Body) kommen → kaum Mehr-Traffic.
        # (Vorher: max-age=86400 → bis zu 24h alter Stand beim Kunden.)
        'Cache-Control': 'no-cache, must-revalidate',
        'Access-Control-Allow-Origin': '*',
        'X-Complyo-Widget-Version': '6.1.0',
        'ETag': etag,
        'Vary': 'Accept-Encoding',
    }

    # Conditional GET: unveraenderte Datei → 304 Not Modified ohne Body
    if request.headers.get('if-none-match') == etag:
        return Response(status_code=304, headers=headers)

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


@router.get("/api/widgets/a11y-fixes.js")
async def serve_a11y_remediation_widget(request: Request):
    """
    Runtime-Alt-Text-Remediation für React/Vue/Angular/SPAs (Channel #3).
    Wendet freigegebene KI-Alt-Texte ins Live-DOM an + MutationObserver.
    """
    widget_path = os.path.join(WIDGET_DIR, 'a11y_remediation.js')
    if not os.path.exists(widget_path):
        raise HTTPException(status_code=404, detail="Widget not found")

    with open(widget_path, 'r', encoding='utf-8') as f:
        content = f.read()

    etag = f'"{hashlib.md5(content.encode()).hexdigest()}"'
    headers = {
        # Wie accessibility.js: per ETag revalidieren statt lange cachen.
        'Cache-Control': 'no-cache, must-revalidate',
        'Access-Control-Allow-Origin': '*',
        'ETag': etag,
        'Vary': 'Accept-Encoding',
    }
    if request.headers.get('if-none-match') == etag:
        return Response(status_code=304, headers=headers)

    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' in accept_encoding:
        compressed = gzip.compress(content.encode('utf-8'))
        headers['Content-Encoding'] = 'gzip'
        return Response(content=compressed, media_type='application/javascript', headers=headers)

    return Response(content=content, media_type='application/javascript', headers=headers)


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
async def get_widget_config(site_id: str, request: Request):
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
    license_state = {"status": "active", "enforced": False, "active": True, "message": None}
    if db_pool:
        try:
            from license_check import evaluate_license
            license_state = await evaluate_license(db_pool, site_id, request)
        except Exception as e:
            _logger.warning(f"[Widget Config] License check failed for {site_id}: {e}")

    return {
        "success": True,
        "license_active": license_state["active"],
        "license": license_state,
        "config": default_config,
    }


@router.get("/api/widgets/snippet/{widget_type}")
async def get_widget_snippet(
    widget_type: str,
    site_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Liefert den HTML-Einbettungscode fuer ein Widget.

    Der Einbettungscode ist das eigentliche Produkt: Er schaltet Banner und
    Widget auf der Kundenseite scharf. Im Free-Tarif ist er deshalb nicht
    enthalten — dort bleibt es bei Scan, Konfiguration und Vorschau. Der
    Endpunkt war bis dahin voellig ungeschuetzt: ohne Anmeldung, ohne
    Tarifpruefung, mit beliebiger site_id aufrufbar.
    """
    plan = (current_user.get('plan_type') or 'free').lower()
    if plan in ('', 'free'):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "plan_upgrade_required",
                "plan": plan or "free",
                "message": (
                    "Der Einbettungscode ist im Free-Tarif nicht enthalten. "
                    "Scan, Konfiguration und Vorschau bleiben kostenlos — zum "
                    "Ausspielen auf deiner Website braucht es einen bezahlten Tarif."
                ),
            },
        )

    # Fremde site_id ist ein Missbrauchssignal, aber kein harter Blocker:
    # Legacy-Konten haben nicht zwingend eine passende tracked_websites-Zeile.
    try:
        if db_pool:
            from license_check import url_to_site_id
            rows = await db_pool.fetch(
                "SELECT url FROM tracked_websites WHERE user_id = $1",
                current_user.get('id') or current_user.get('user_id'),
            )
            own = {url_to_site_id(r["url"]) for r in rows if r["url"]}
            if own and site_id not in own:
                logging.getLogger(__name__).warning(
                    "[Widget Snippet] User %s fordert Snippet fuer fremde site_id %s an",
                    current_user.get('id'), site_id,
                )
    except Exception as e:
        logging.getLogger(__name__).warning(f"[Widget Snippet] Ownership-Check fehlgeschlagen: {e}")

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
            # Kein Demo-Fallback: erfundene Alt-Texte ("Firmenlogo Mustermann
            # GmbH") duerfen nie in einem Kundenprojekt landen.
            raise HTTPException(
                status_code=503,
                detail="Datenbank nicht verfügbar — Fixes können nicht geladen werden."
            )
        
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


@router.get("/api/accessibility/fix-manifest/{site_id}")
async def get_fix_manifest(site_id: str, request: Request):
    """
    Vereinheitlichtes Fix-Manifest für ALLE Auslieferungskanäle
    (WordPress-Plugin / HTML-CLI / SPA-Runtime).

    Bündelt content-adressiert die freigegebenen, auto-sicheren Fixes einer Site:
      - alt_texts:      KI-Alt-Texte je Bild (image_url_hash / filename / src)
      - document_fixes: dokumentweite Fixes (html-lang, skip-link, landmarks, css)

    Nur Status 'approved' wird ausgeliefert. Die Channels wenden die Fixes guarded
    an (nur setzen, wenn am Ziel noch nicht vorhanden) — nie etwas überschreiben.
    """
    _logger = logging.getLogger(__name__)
    alt_texts = []
    document_fixes = []
    link_fixes = []

    if db_pool:
        try:
            fix_saver = AccessibilityFixSaver(db_pool)
            alt_texts = await fix_saver.get_fixes_for_site(site_id, status='approved')
            document_fixes = await fix_saver.get_document_fixes_for_site(site_id, status='approved')
            link_fixes = await fix_saver.get_link_fixes_for_site(site_id, status='approved')
        except Exception as e:
            _logger.error(f"[Fix-Manifest] Fehler beim Laden für {site_id}: {e}")
            return JSONResponse(
                content={"success": False, "site_id": site_id, "error": str(e),
                         "alt_texts": [], "document_fixes": [], "link_fixes": []},
                headers={'Access-Control-Allow-Origin': '*'}
            )
    else:
        _logger.warning(f"[Fix-Manifest] DB-Pool nicht verfügbar für {site_id}")

    # CSS-Regeln aus document_fixes herausziehen (Channels mögen es getrennt).
    # `css-rule` traegt genau eine Regel, `kontrast-css` buendelt viele: die
    # Tabelle laesst nur eine Zeile je (site_id, fix_type) zu, und eine
    # Kontrast-Reparatur besteht aus einer Regel je Selektor.
    css_rules = [
        f["payload"] for f in document_fixes
        if f.get("fix_type") == "css-rule" and isinstance(f.get("payload"), dict)
    ]
    for f in document_fixes:
        if f.get("fix_type") == "struktur" and isinstance(f.get("payload"), dict):
            css_rules.extend([
                r for r in (f["payload"].get("css_rules") or [])
                if isinstance(r, dict) and r.get("selector") and r.get("declarations")
            ])
        if f.get("fix_type") == "kontrast-css" and isinstance(f.get("payload"), dict):
            css_rules.extend([
                r for r in (f["payload"].get("rules") or [])
                if isinstance(r, dict) and r.get("selector") and r.get("declarations")
            ])

    # Kennt complyo diese site_id ueberhaupt?
    #
    # Der Anlass ist ein echter Fund: auf loqal.io laedt das Cookie-Widget mit
    # `data-site-id="loqal-io"`, das Barrierefreiheits-Widget daneben mit
    # `data-site-id="scan_5_1783852724"` — einer Scan-Kennung. Das Manifest
    # antwortete mit 200 und einem leeren Koerper, das Widget wendete brav
    # nichts an, und niemand konnte es merken. Die Seite haette auch nach jeder
    # Freigabe nie eine Reparatur bekommen.
    #
    # Ein leeres Manifest hat zwei voellig verschiedene Bedeutungen: "hier gibt
    # es nichts zu tun" und "du fragst unter der falschen Kennung". Beide mit
    # derselben Antwort zu beantworten, ist der Fehler. Deshalb dieses Feld —
    # das Widget meldet es zurueck, und der Betreiber erfaehrt, dass sein
    # Einbau ins Leere laeuft.
    bekannt = bool(alt_texts or document_fixes or link_fixes)
    if not bekannt and db_pool:
        try:
            async with db_pool.acquire() as conn:
                bekannt = bool(await conn.fetchval(
                    """SELECT 1 FROM tracked_websites
                       WHERE replace(
                               regexp_replace(
                                 regexp_replace(lower(url), '^https?://(www\\.)?', ''),
                                 '[/?#:].*$', ''),
                               '.', '-') = $1
                       LIMIT 1""",
                    site_id))
        except Exception as e:
            _logger.warning(f"[Fix-Manifest] Bekanntheitspruefung fuer {site_id}: {e}")
            bekannt = True   # im Zweifel nicht warnen

    manifest = {
        "success": True,
        "version": "1.1.0",
        "site_id": site_id,
        "bekannt": bekannt,
        "alt_texts": alt_texts,
        "document_fixes": [f for f in document_fixes
                           if f.get("fix_type") not in ("css-rule", "kontrast-css")],
        # Attribut-Setzungen aus der Struktur-Reparatur — die Channels wenden
        # sie guarded an (nur wo nichts steht). Getrennt von css_rules, weil es
        # Markup betrifft und nicht Darstellung.
        "struktur_fixes": next(
            (f["payload"].get("fixes") or [] for f in document_fixes
             if f.get("fix_type") == "struktur" and isinstance(f.get("payload"), dict)),
            [],
        ),
        "link_fixes": link_fixes,
        "css_rules": css_rules,
        "counts": {
            "alt_texts": len(alt_texts),
            "document_fixes": len(document_fixes),
            "link_fixes": len(link_fixes),
        },
    }

    # ETag für effiziente Revalidierung (Channels cachen per If-None-Match).
    etag = '"' + hashlib.md5(json.dumps(manifest, sort_keys=True, default=str).encode()).hexdigest() + '"'
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-cache, must-revalidate',
        'ETag': etag,
    }
    if request.headers.get('if-none-match') == etag:
        return Response(status_code=304, headers=headers)

    return JSONResponse(content=manifest, headers=headers)


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
        # Freigegebene Fixes aus der Datenbank laden.
        # Kein Demo-Fallback: hier wurden frueher Beispieldaten
        # ("Firmenlogo", "/images/logo.png") ins Kundenpaket geschrieben, weil
        # ein falscher Import (`from main import ...` — es gibt nur
        # main_production) den except-Zweig bei JEDEM Aufruf ausloeste.
        if not db_pool:
            raise HTTPException(
                status_code=503,
                detail="Datenbank nicht verfügbar — Patch-Paket kann nicht erstellt werden."
            )

        async with db_pool.acquire() as conn:
            alt_text_fixes = await conn.fetch(
                """
                SELECT 'alt_text' AS type, page_url, image_src, image_filename,
                       suggested_alt, confidence
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1 AND status = 'approved'
                ORDER BY created_at DESC
                """,
                site_id,
            )

        fixes = [dict(f) for f in alt_text_fixes]
        logger.info(f"Patch-Paket für {site_id}: {len(fixes)} freigegebene Fixes geladen")

        if not fixes:
            # Ehrlich bleiben: ohne freigegebene Fixes gibt es nichts zu patchen.
            raise HTTPException(
                status_code=409,
                detail=(
                    "Noch keine freigegebenen Fixes vorhanden. Prüfen und bestätigen "
                    "Sie die Vorschläge zuerst in der Barrierefreiheits-Worklist."
                ),
            )

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
            detail="Fehler beim Generieren der Patches"
        )


@router.get("/api/accessibility/patches/download/{download_id}")
async def download_accessibility_patches(
    download_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Lädt generierte Barrierefreiheits-Patches herunter

    Bis 2026-07-17 ohne jede Auth erreichbar, bei erratbarer download_id
    ("{site_id}_{unix_ts}") — fremde Patch-ZIPs waren damit abrufbar. Jetzt:
    Login + Ownership auf der im download_id enthaltenen site_id.

    Args:
        download_id: Download-Identifier (von generate-Endpoint)

    Returns:
        ZIP-Datei mit Patches
    """
    import re as _re

    # download_id landet in einem Dateinamen — strikt validieren, sonst ist
    # "../../.." ein Path-Traversal.
    if not _re.fullmatch(r"[A-Za-z0-9-]+_\d+", download_id):
        raise HTTPException(status_code=404, detail="Download nicht gefunden oder abgelaufen")

    # Ownership: site_id ist der Teil vor dem letzten "_" (site_ids sind
    # hostname-basiert und enthalten keine Unterstriche).
    site_id = download_id.rsplit("_", 1)[0]
    await require_site_ownership(site_id, current_user)

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
            detail="Fehler beim Download"
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
