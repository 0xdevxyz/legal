"""
Deep Cookie Scanner API Routes
Premium feature endpoints for cookie and tracking detection

Endpoints:
POST   /api/v2/deep-cookie-scan/start         - Start a new scan
GET    /api/v2/deep-cookie-scan/{scan_id}     - Poll scan status & results
GET    /api/v2/deep-cookie-scan/{scan_id}/export - Export for Cookie Configurator
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncpg
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from dependencies import get_current_user
from database_service import db_service
from compliance_engine.privacy_transfer_findings import detect_transfers
from compliance_engine.deep_cookie_scanner import DeepCookieScanner

import json
import logging
from dataclasses import asdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["deep-cookie-scanner"])


def _as_obj(val, default):
    """
    JSONB-Felder kommen ohne registrierten Codec als String aus asyncpg zurück.
    Parst Strings defensiv zu Python-Objekten; lässt bereits geparste Werte durch.
    """
    if val is None:
        return default
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (ValueError, TypeError):
            return default
    return val

db_pool = None


async def get_db_connection():
    if db_pool:
        async with db_pool.acquire() as conn:
            yield conn
    else:
        raise HTTPException(status_code=503, detail="Database not available")


async def check_premium_plan(user_id: int, connection) -> bool:
    result = await connection.fetchval(
        "SELECT plan_type FROM subscriptions WHERE user_id = $1 AND status = 'active'",
        user_id
    )
    return result in ["pro", "premium", "agency", "enterprise", "complete"]


# Das monatliche Deep-Scan-Kontingent entspricht der Anzahl freigeschalteter
# Websites (user_limits.websites_max). Daraus ergibt sich automatisch:
#   pro = 1, agency = 25, agency2 = 50 (Agency + Add-on, additiv).
# Add-ons (agency_extra/agency2) erhöhen websites_max, plan_type bleibt 'agency'
# — deshalb wird hier websites_max statt plan_type ausgewertet.
DEFAULT_SCAN_LIMIT = 1
UNLIMITED_SCAN_LIMIT = 999999


async def resolve_scan_limit(user_id: int, connection) -> int:
    """Ermittelt das monatliche Scan-Limit aus dem freigeschalteten Website-Kontingent."""
    websites_max = await connection.fetchval(
        "SELECT websites_max FROM user_limits WHERE user_id = $1",
        user_id
    )
    if websites_max is None:
        return DEFAULT_SCAN_LIMIT
    if websites_max < 0:  # -1 = unbegrenzt (Master-Account)
        return UNLIMITED_SCAN_LIMIT
    return websites_max


async def check_scan_limit(user_id: int, connection) -> Dict[str, int]:
    current_month = datetime.utcnow().strftime("%Y-%m")
    scans_limit = await resolve_scan_limit(user_id, connection)

    usage = await connection.fetchrow(
        "SELECT scans_used, scans_limit FROM deep_scan_usage "
        "WHERE user_id = $1 AND current_month = $2",
        user_id,
        current_month
    )

    if not usage:
        await connection.execute(
            "INSERT INTO deep_scan_usage (user_id, current_month, scans_used, scans_limit) "
            "VALUES ($1, $2, 0, $3)",
            user_id,
            current_month,
            scans_limit
        )
        return {"scans_used": 0, "scans_limit": scans_limit, "can_scan": True}

    scans_used = usage["scans_used"]
    # Limit an den aktuellen Plan angleichen (z. B. nach Upgrade auf Agency),
    # ohne den bereits verbrauchten Zähler zurückzusetzen.
    if usage["scans_limit"] != scans_limit:
        await connection.execute(
            "UPDATE deep_scan_usage SET scans_limit = $3 "
            "WHERE user_id = $1 AND current_month = $2",
            user_id,
            current_month,
            scans_limit
        )

    can_scan = scans_used < scans_limit

    return {"scans_used": scans_used, "scans_limit": scans_limit, "can_scan": can_scan}


class StartScanRequest(BaseModel):
    url: str
    website_id: Optional[str] = None


@router.post("/deep-cookie-scan/start")
async def start_deep_scan(
    body: StartScanRequest,
    current_user: Dict = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(get_db_connection),
):
    """
    Start a new deep cookie scan

    Request body (JSON):
        url: str - Website URL to scan
        website_id: Optional[str] - Tracked website ID for linking

    Response:
        {
            "scan_id": 123,
            "status": "pending",
            "message": "Scan queued, check progress with GET /api/v2/deep-cookie-scan/123",
            "estimated_duration_seconds": 180
        }
    """
    url = body.url
    website_id = body.website_id
    user_id = current_user["id"]
    
    # 1. Check if user has premium plan
    has_premium = await check_premium_plan(user_id, connection)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail="Deep Cookie Scanner is a Premium feature. Upgrade your plan to access."
        )
    
    # 2. Check scan limits
    usage = await check_scan_limit(user_id, connection)
    if not usage["can_scan"]:
        raise HTTPException(
            status_code=429,
            detail=f"Scan limit reached ({usage['scans_used']}/{usage['scans_limit']} this month). "
                   "Your limit resets on the 1st of next month."
        )
    
    # 3. Validate URL
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    # 4. Create scan record
    try:
        scan_id = await connection.fetchval(
            """
            INSERT INTO deep_cookie_scans (user_id, website_id, url, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING id
            """,
            int(user_id),
            website_id,
            url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scan: {str(e)}")
    
    # 5. Increment usage counter
    current_month = datetime.utcnow().strftime("%Y-%m")
    await connection.execute(
        "UPDATE deep_scan_usage SET scans_used = scans_used + 1 WHERE user_id = $1 AND current_month = $2",
        int(user_id),
        current_month
    )
    
    # 6. Background-Job starten (asyncio Task) — führt den echten Playwright-Scan aus
    asyncio.create_task(background_scan_job(scan_id, url))
    
    # 7. Log event
    await connection.execute(
        "INSERT INTO deep_scan_history (scan_id, event_type, event_data) "
        "VALUES ($1, 'started', $2)",
        scan_id,
        {"url": url, "initiated_at": datetime.utcnow().isoformat()}
    )
    
    return {
        "scan_id": scan_id,
        "status": "pending",
        "message": f"Scan queued. Check progress with GET /api/v2/deep-cookie-scan/{scan_id}",
        "estimated_duration_seconds": 180,
        "usage": {
            "scans_used": usage["scans_used"] + 1,
            "scans_limit": usage["scans_limit"]
        }
    }


@router.get("/deep-cookie-scan/usage")
async def get_scan_usage(
    current_user: Dict = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(get_db_connection),
):
    """
    Aktuelles monatliches Scan-Kontingent des Nutzers (plan-abhängig).
    Dient dem Frontend dazu, den korrekten Zähler/Limit schon vor dem
    ersten Scan anzuzeigen.
    """
    user_id = current_user["id"]
    usage = await check_scan_limit(int(user_id), connection)
    return {
        "scans_used": usage["scans_used"],
        "scans_limit": usage["scans_limit"],
        "can_scan": usage["can_scan"],
    }


@router.get("/deep-cookie-scan/{scan_id}")
async def get_scan_status(
    scan_id: int,
    current_user: Dict = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(get_db_connection),
):
    """
    Poll scan status and get results when complete
    
    Response:
        Pending:
            {
                "scan_id": 123,
                "status": "pending|running|completed|failed",
                "progress_percent": 35,
                "message": "Collecting cookies from page..."
            }
        
        Completed:
            {
                "scan_id": 123,
                "status": "completed",
                "url": "https://example.com",
                "total_cookies": 47,
                "unique_services": 12,
                "total_requests": 284,
                "services_detected": ["Google Analytics", "Facebook", "Hotjar", ...],
                "cookies": [...],
                "requests": [...],
                "categorized": {
                    "Google Analytics": {
                        "cookies": [...],
                        "requests": [...]
                    },
                    ...
                },
                "scan_duration_seconds": 127
            }
    """
    user_id = current_user["id"]
    
    # Fetch scan
    scan = await connection.fetchrow(
        "SELECT * FROM deep_cookie_scans WHERE id = $1 AND user_id = $2",
        scan_id,
        int(user_id)
    )
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Build response based on status
    response = {
        "scan_id": scan["id"],
        "status": scan["status"],
        "url": scan["url"],
        "created_at": scan["created_at"].isoformat(),
    }
    
    if scan["status"] == "pending":
        response["progress_percent"] = 0
        response["message"] = "Scan queued..."
    elif scan["status"] == "running":
        response["progress_percent"] = 50  # In production, track actual progress
        response["message"] = "Scanning for cookies and tracking..."
    elif scan["status"] == "failed":
        response["error"] = scan["error_message"]
    elif scan["status"] == "completed":
        # Drittlandtransfer-Findings aus den ECHTEN beobachteten Requests ableiten
        # (Google Fonts, reCAPTCHA, Maps, YouTube, Adobe-Fonts) — abmahnfähig.
        privacy_findings = _privacy_findings_from_requests(scan["requests"])

        # Return full results (JSONB-Felder defensiv parsen)
        response.update({
            "total_cookies": scan["total_cookies"],
            "unique_services": scan["unique_services"],
            "total_requests": scan["total_requests"],
            "services_detected": _as_obj(scan["services_detected"], []),
            "cookies": _as_obj(scan["cookies"], []),
            "requests": _as_obj(scan["requests"], []),
            "categorized": _as_obj(scan["categorized"], {}),
            "scan_duration_seconds": scan["scan_duration_seconds"],
            "privacy_findings": privacy_findings,
            "privacy_findings_count": len(privacy_findings),
            "privacy_risk_euro": sum(f.get("risk_euro", 0) for f in privacy_findings),
        })

    return response


def _privacy_findings_from_requests(requests_raw) -> list:
    """
    Extrahiert Request-URLs aus dem gespeicherten requests-Feld (JSON-String oder
    bereits geparste Liste) und ermittelt die Drittlandtransfer-Findings.
    """
    if not requests_raw:
        return []
    requests = requests_raw
    if isinstance(requests, str):
        try:
            requests = json.loads(requests)
        except (ValueError, TypeError):
            return []
    if not isinstance(requests, list):
        return []
    urls = [r.get("url", "") for r in requests if isinstance(r, dict)]
    return detect_transfers(request_urls=urls)


@router.get("/deep-cookie-scan/{scan_id}/export")
async def export_scan_for_configurator(
    scan_id: int,
    current_user: Dict = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(get_db_connection),
):
    """
    Export scan results in format compatible with Cookie Configurator
    For 1-click import into banner configuration
    
    Response:
        {
            "scan_id": 123,
            "services": [
                {
                    "name": "Google Analytics",
                    "category": "analytics",
                    "cookies": ["_ga", "_gid", "_gat", ...],
                    "total_requests": 24,
                    "can_block": false,
                    "description": "Sends analytics data to Google..."
                },
                {
                    "name": "Facebook",
                    "category": "marketing",
                    "cookies": ["_fbp", "fr", ...],
                    "total_requests": 8,
                    "can_block": true,
                    "description": "Facebook conversion tracking..."
                },
                ...
            ],
            "import_ready": true
        }
    """
    user_id = current_user["id"]
    
    scan = await connection.fetchrow(
        "SELECT categorized, services_detected FROM deep_cookie_scans WHERE id = $1 AND user_id = $2 AND status = 'completed'",
        scan_id,
        int(user_id)
    )
    
    if not scan:
        raise HTTPException(status_code=404, detail="Completed scan not found")
    
    categorized = _as_obj(scan["categorized"], {})

    # Transform to service-centric format for configurator
    services = []
    
    for service_name, data in categorized.items():
        cookies = data.get("cookies", [])
        requests = data.get("requests", [])
        
        # Extract unique cookie names
        cookie_names = list(set([c.get("name", "") for c in cookies if c.get("name")]))
        
        # Determine category based on service name and patterns
        category = _determine_category(service_name, cookie_names)
        
        services.append({
            "name": service_name,
            "category": category,
            "cookies": cookie_names,
            "total_cookies": len(cookies),
            "total_requests": len(requests),
            "can_block": category != "necessary",
            "description": _get_service_description(service_name),
        })
    
    # Sort by category priority (necessary first)
    category_priority = {"necessary": 0, "functional": 1, "analytics": 2, "marketing": 3}
    services.sort(key=lambda s: (category_priority.get(s["category"], 99), s["name"]))
    
    return {
        "scan_id": scan_id,
        "services": services,
        "import_ready": True,
        "message": "Ready to import into Cookie Configurator. Click '➜ Hinzufügen' to add each service."
    }


def _determine_category(service_name: str, cookie_names: list) -> str:
    """
    Determine cookie category based on service name and cookie names
    """
    service_lower = service_name.lower()
    
    necessary_keywords = ["cloudflare", "cdn", "csrf", "_session", "sid"]
    functional_keywords = ["typekit", "font", "intercom", "zendesk"]
    analytics_keywords = ["google analytics", "matomo", "hotjar", "amplitude", "_ga", "_gid"]
    marketing_keywords = ["facebook", "google ads", "linkedin", "twitter", "tiktok", "pinterest"]
    
    if any(kw in service_lower for kw in necessary_keywords):
        return "necessary"
    elif any(kw in service_lower for kw in functional_keywords):
        return "functional"
    elif any(kw in service_lower for kw in analytics_keywords) or any(
        pattern in "".join(cookie_names).lower()
        for pattern in ["_ga", "_gid", "_pk", "_hjid"]
    ):
        return "analytics"
    elif any(kw in service_lower for kw in marketing_keywords):
        return "marketing"
    else:
        return "functional"  # Default


def _get_service_description(service_name: str) -> str:
    """
    Get human-readable description for service
    """
    descriptions = {
        "Google Analytics": "Sends analytics data to Google Analytics for website traffic analysis",
        "Google Ads": "Google Ads conversion tracking and remarketing",
        "Facebook": "Facebook conversion tracking and audience tracking",
        "Hotjar": "Session recording and user feedback collection",
        "Matomo": "Privacy-friendly analytics alternative to Google Analytics",
        "LinkedIn": "LinkedIn conversion tracking and audience targeting",
        "Intercom": "Live chat and customer support widget",
        "Stripe": "Payment processing and fraud detection",
        "Cloudflare": "CDN and DDoS protection (required for functionality)",
    }
    return descriptions.get(service_name, f"External service: {service_name}")


async def background_scan_job(scan_id: int, url: str):
    """
    Führt den echten Deep-Scan (Playwright) aus und persistiert das Ergebnis.
    Läuft als asyncio-Task NACH dem Request → nutzt den Modul-DB-Pool
    (in main_production via `_deep_cookie_scanner_routes.db_pool = db_pool` gesetzt),
    nicht die request-gebundene Dependency.
    """
    if not db_pool:
        logger.error(f"[DeepScan {scan_id}] Kein DB-Pool verfügbar — Abbruch")
        return

    try:
        async with db_pool.acquire() as connection:
            await connection.execute(
                "UPDATE deep_cookie_scans SET status = 'running' WHERE id = $1",
                scan_id,
            )

        # Echter Scan (DeepCookieScanner startet Playwright selbst)
        scanner = DeepCookieScanner(scan_id, url)
        result = await scanner.scan()

        if getattr(result, "error", None):
            raise RuntimeError(result.error)

        async with db_pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE deep_cookie_scans SET
                    status = 'completed',
                    cookies = $2,
                    requests = $3,
                    storage = $4,
                    categorized = $5,
                    total_cookies = $6,
                    unique_services = $7,
                    total_requests = $8,
                    services_detected = $9,
                    scan_duration_seconds = $10,
                    last_updated = NOW()
                WHERE id = $1
                """,
                scan_id,
                json.dumps([asdict(c) for c in result.cookies]),
                json.dumps([asdict(r) for r in result.requests]),
                json.dumps(result.storage),
                json.dumps(result.categorized),
                result.total_cookies,
                result.unique_services,
                result.total_requests,
                json.dumps(result.services_detected),  # JSONB-Spalte → dumpen
                result.scan_duration_seconds,
            )
            await connection.execute(
                "INSERT INTO deep_scan_history (scan_id, event_type) VALUES ($1, 'completed')",
                scan_id,
            )
        logger.info(f"[DeepScan {scan_id}] ✅ completed — {result.total_requests} requests, "
                    f"{result.total_cookies} cookies, {result.unique_services} services")

    except Exception as e:
        logger.error(f"[DeepScan {scan_id}] ❌ failed: {e}")
        try:
            async with db_pool.acquire() as connection:
                await connection.execute(
                    "UPDATE deep_cookie_scans SET status = 'failed', error_message = $2 WHERE id = $1",
                    scan_id, str(e),
                )
                await connection.execute(
                    "INSERT INTO deep_scan_history (scan_id, event_type, event_data) VALUES ($1, 'failed', $2)",
                    scan_id, json.dumps({"error": str(e)}),
                )
        except Exception as inner:
            logger.error(f"[DeepScan {scan_id}] konnte Fehlerstatus nicht speichern: {inner}")
"""
Additional API endpoint for Scanner Import Panel

Add this endpoint to 03_deep_cookie_scanner_routes.py after the existing endpoints
"""

@router.get("/deep-cookie-scan/my-scans")
async def get_my_scans(
    limit: int = Query(10, ge=1, le=50),
    current_user: Dict = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(get_db_connection),
):
    """
    Get user's recent completed scans for import into Cookie Configurator
    
    Query Parameters:
        limit: Maximum number of scans to return (default: 10, max: 50)
    
    Response:
        {
            "scans": [
                {
                    "scan_id": 123,
                    "url": "https://example.com",
                    "created_at": "2026-04-20T14:30:00Z",
                    "total_cookies": 47,
                    "unique_services": 12
                },
                ...
            ]
        }
    """
    user_id = current_user["id"]
    
    try:
        scans = await connection.fetch(
            """
            SELECT 
                id as scan_id,
                url,
                created_at,
                total_cookies,
                unique_services
            FROM deep_cookie_scans
            WHERE user_id = $1 AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT $2
            """,
            int(user_id),
            limit
        )
        
        return {
            "scans": [
                {
                    "scan_id": scan["scan_id"],
                    "url": scan["url"],
                    "created_at": scan["created_at"].isoformat(),
                    "total_cookies": scan["total_cookies"],
                    "unique_services": scan["unique_services"],
                }
                for scan in scans
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scans: {str(e)}")


@router.delete("/deep-cookie-scan/{scan_id}")
async def delete_scan(
    scan_id: int,
    current_user: Dict = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(get_db_connection),
):
    """
    Delete a scan and its associated data
    
    Response:
        {
            "scan_id": 123,
            "deleted": true,
            "message": "Scan deleted successfully"
        }
    """
    user_id = current_user["id"]
    
    # Verify ownership
    scan = await connection.fetchval(
        "SELECT id FROM deep_cookie_scans WHERE id = $1 AND user_id = $2",
        scan_id,
        int(user_id)
    )
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Delete scan and associated history
    await connection.execute(
        "DELETE FROM deep_scan_history WHERE scan_id = $1",
        scan_id
    )
    
    await connection.execute(
        "DELETE FROM deep_cookie_scans WHERE id = $1",
        scan_id
    )
    
    return {
        "scan_id": scan_id,
        "deleted": True,
        "message": "Scan deleted successfully"
    }


@router.get("/deep-cookie-scan/{scan_id}/stats")
async def get_scan_statistics(
    scan_id: int,
    current_user: Dict = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(get_db_connection),
):
    """
    Get detailed statistics about a completed scan
    
    Response:
        {
            "scan_id": 123,
            "total_cookies": 47,
            "cookies_by_category": {
                "necessary": 5,
                "functional": 8,
                "analytics": 18,
                "marketing": 16
            },
            "services_by_category": {
                "necessary": ["Cloudflare"],
                "analytics": ["Google Analytics", "Matomo"],
                "marketing": ["Facebook", "Google Ads", ...]
            },
            "top_cookies": [
                {"name": "_ga", "count": 5, "services": ["Google Analytics"]},
                ...
            ],
            "scan_duration_seconds": 127,
            "created_at": "2026-04-20T14:30:00Z"
        }
    """
    user_id = current_user["id"]
    
    scan = await connection.fetchrow(
        """
        SELECT 
            id,
            cookies,
            categorized,
            services_detected,
            scan_duration_seconds,
            created_at
        FROM deep_cookie_scans
        WHERE id = $1 AND user_id = $2 AND status = 'completed'
        """,
        scan_id,
        int(user_id)
    )
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Analyze cookies by category
    cookies_by_category = {
        "necessary": 0,
        "functional": 0,
        "analytics": 0,
        "marketing": 0,
    }
    
    categorized = _as_obj(scan["categorized"], {})

    for service, data in categorized.items():
        # Get category from categorization logic
        category = _determine_category(
            service,
            [c.get("name", "") for c in data.get("cookies", [])]
        )
        cookies_by_category[category] += len(data.get("cookies", []))
    
    # Group services by category
    services_by_category = {
        "necessary": [],
        "functional": [],
        "analytics": [],
        "marketing": [],
    }
    
    for service in (scan["services_detected"] or []):
        category = _determine_category(service, [])
        services_by_category[category].append(service)
    
    # Analyze top cookies
    cookie_counts = {}
    for service, data in categorized.items():
        for cookie in data.get("cookies", []):
            name = cookie.get("name", "")
            if name:
                if name not in cookie_counts:
                    cookie_counts[name] = {"count": 0, "services": []}
                cookie_counts[name]["count"] += 1
                if service not in cookie_counts[name]["services"]:
                    cookie_counts[name]["services"].append(service)
    
    top_cookies = sorted(
        [{"name": name, **data} for name, data in cookie_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]
    
    return {
        "scan_id": scan_id,
        "total_cookies": sum(cookies_by_category.values()),
        "cookies_by_category": cookies_by_category,
        "services_by_category": services_by_category,
        "top_cookies": top_cookies,
        "scan_duration_seconds": scan["scan_duration_seconds"],
        "created_at": scan["created_at"].isoformat(),
    }
