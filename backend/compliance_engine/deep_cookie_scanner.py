"""
Deep Cookie Scanner Engine
Comprehensive cookie and tracking detection via Puppeteer + Headless Chrome

Architecture:
1. Intercepts all HTTP responses (cookie headers)
2. Overrides document.cookie getter/setter to log all cookie operations
3. Injects JS to capture localStorage/sessionStorage
4. Simulates user interactions (scroll, hover, click) to trigger lazy tracking
5. Identifies services via URL pattern matching
6. Returns structured results with per-service breakdown
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright nicht verfügbar — DeepCookieScanner kann nicht scannen.")

# Note: Would use pyppeteer or async-driver in production
# For MVP, showing the architecture


@dataclass
class Cookie:
    name: str
    domain: str
    path: str = "/"
    secure: bool = False
    httpOnly: bool = False
    sameSite: str = "Lax"
    expires: Optional[str] = None
    service: Optional[str] = None
    category: str = "uncategorized"  # necessary, functional, analytics, marketing


@dataclass
class Request:
    url: str
    method: str
    type: str  # xhr, fetch, img, script, etc.
    service: Optional[str] = None
    payload_size: int = 0


@dataclass
class ScanResult:
    scan_id: int
    url: str
    cookies: List[Cookie] = field(default_factory=list)
    requests: List[Request] = field(default_factory=list)
    storage: Dict[str, Dict] = field(default_factory=lambda: {"localStorage": {}, "sessionStorage": {}})
    categorized: Dict[str, Dict] = field(default_factory=dict)
    total_cookies: int = 0
    unique_services: int = 0
    total_requests: int = 0
    services_detected: List[str] = field(default_factory=list)
    scan_duration_seconds: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# Service Identification Patterns
SERVICE_PATTERNS = {
    "Google Analytics": [
        r"google-analytics\.com",
        r"ga\.js",
        r"_gid",
        r"_ga_",
    ],
    "Google Ads": [
        r"google\.com/ads",
        r"doubleclick\.net",
        r"_gac_",
    ],
    "Facebook": [
        r"facebook\.com",
        r"facebook\.net",
        r"fbcdn\.net",
        r"_fbp",
    ],
    "Hotjar": [
        r"hotjar\.com",
        r"_hjid",
    ],
    "Matomo": [
        r"matomo\.js",
        r"piwik",
        r"_pk_",
    ],
    "LinkedIn": [
        r"linkedin\.com",
        r"licdn\.com",
        r"_li_",
    ],
    "Intercom": [
        r"intercom\.io",
        r"intercom-analytics",
    ],
    "Typekit": [
        r"typekit\.net",
        r"fonts\.com",
    ],
    "Cloudflare": [
        r"cloudflare\.com",
        r"__cfruid",
    ],
    "Stripe": [
        r"stripe\.com",
        r"__stripe",
    ],
}


class DeepCookieScanner:
    """
    Main scanner engine for comprehensive cookie detection
    """

    def __init__(self, scan_id: int, url: str, headless_browser=None):
        self.scan_id = scan_id
        self.url = url
        self.browser = headless_browser
        self.cookies: List[Cookie] = []
        self.requests: List[Request] = []
        self.storage: Dict[str, Dict] = {"localStorage": {}, "sessionStorage": {}}
        self.services_detected: Set[str] = set()
        self.start_time = None

    async def scan(self) -> ScanResult:
        """
        Echter Scan via Playwright: Browser starten, Requests + Cookies +
        Storage erfassen, Nutzer-Interaktion simulieren, Ergebnis kompilieren.
        """
        self.start_time = datetime.utcnow()

        if not PLAYWRIGHT_AVAILABLE:
            result = ScanResult(scan_id=self.scan_id, url=self.url)
            result.error = "Playwright nicht verfügbar"
            return result

        url = self.url if self.url.startswith(("http://", "https://")) else f"https://{self.url}"

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage",
                          "--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                    locale="de-DE",
                )
                page = await context.new_page()

                # Alle ausgehenden Requests erfassen (XHR, Script, Img, Font, ...)
                page.on("request", self._on_request)

                # Navigieren (löst initiale Skripte/Tracker aus)
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                except Exception as e:
                    logger.warning(f"Navigation langsam/teilweise für {url}: {e}")

                # Lazy-Tracker durch Interaktion triggern
                await self._simulate_user_interaction(page)

                # Cookies aus dem Browser-Context (echte gesetzte Cookies)
                try:
                    for c in await context.cookies():
                        cookie = Cookie(
                            name=c.get("name", ""),
                            domain=c.get("domain", ""),
                            path=c.get("path", "/"),
                            secure=c.get("secure", False),
                            httpOnly=c.get("httpOnly", False),
                            sameSite=c.get("sameSite", "Lax"),
                            expires=str(c.get("expires", "")),
                            service=self._identify_service("https://" + c.get("domain", "").lstrip(".")),
                        )
                        self.cookies.append(cookie)
                        if cookie.service:
                            self.services_detected.add(cookie.service)
                except Exception as e:
                    logger.warning(f"Cookie-Erfassung fehlgeschlagen: {e}")

                # Storage erfassen
                try:
                    self.storage["localStorage"] = await page.evaluate(
                        "() => Object.fromEntries(Object.entries(localStorage))"
                    ) or {}
                    self.storage["sessionStorage"] = await page.evaluate(
                        "() => Object.fromEntries(Object.entries(sessionStorage))"
                    ) or {}
                except Exception as e:
                    logger.debug(f"Storage-Erfassung fehlgeschlagen: {e}")

                await context.close()
                await browser.close()

            return await self._compile_results()

        except Exception as e:
            logger.error(f"Deep-Scan fehlgeschlagen für {url}: {e}")
            result = ScanResult(
                scan_id=self.scan_id,
                url=self.url,
                scan_duration_seconds=int((datetime.utcnow() - self.start_time).total_seconds()),
            )
            result.error = str(e)
            return result

    def _on_request(self, request):
        """Sync-Handler für page.on('request') — erfasst jeden Request."""
        try:
            service = self._identify_service(request.url)
            self.requests.append(Request(
                url=request.url,
                method=request.method,
                type=request.resource_type,
                service=service,
            ))
            if service:
                self.services_detected.add(service)
        except Exception:
            pass

    async def _intercept_response(self, response):
        """
        Intercept HTTP responses to extract Set-Cookie headers
        """
        # Get Set-Cookie headers from response
        set_cookie_headers = response.headers.get("set-cookie", [])
        
        for cookie_str in set_cookie_headers:
            cookie = self._parse_set_cookie(cookie_str)
            if cookie:
                cookie.service = self._identify_service(response.url)
                self.cookies.append(cookie)
                self.services_detected.add(cookie.service)

    async def _intercept_request(self, request):
        """
        Intercept network requests to identify trackers/analytics
        """
        req = Request(
            url=request.url,
            method=request.method,
            type=self._get_request_type(request),
            service=self._identify_service(request.url),
            payload_size=len(request.postData or b""),
        )
        self.requests.append(req)
        
        if req.service:
            self.services_detected.add(req.service)

    def _parse_set_cookie(self, cookie_str: str) -> Optional[Cookie]:
        """
        Parse Set-Cookie header into Cookie object
        Format: name=value; Domain=...; Path=...; Secure; HttpOnly; SameSite=...
        """
        try:
            parts = cookie_str.split(";")
            name_val = parts[0].strip().split("=", 1)
            
            if len(name_val) != 2:
                return None
            
            cookie = Cookie(name=name_val[0].strip(), domain="")
            
            for part in parts[1:]:
                key_val = part.strip().split("=", 1)
                key = key_val[0].strip().lower()
                val = key_val[1].strip() if len(key_val) > 1 else ""
                
                if key == "domain":
                    cookie.domain = val
                elif key == "path":
                    cookie.path = val
                elif key == "secure":
                    cookie.secure = True
                elif key == "httponly":
                    cookie.httpOnly = True
                elif key == "samesite":
                    cookie.sameSite = val
                elif key == "expires":
                    cookie.expires = val
            
            return cookie
        except Exception:
            return None

    def _inject_storage_logger(self) -> str:
        """
        Generate JavaScript to inject into page to capture storage operations
        Overrides localStorage/sessionStorage setters
        """
        return """
        (function() {
            const originalSetItem = Storage.prototype.setItem;
            const storageEvents = [];
            
            Storage.prototype.setItem = function(key, value) {
                storageEvents.push({
                    type: this === localStorage ? 'localStorage' : 'sessionStorage',
                    key: key,
                    value: value,
                    timestamp: new Date().toISOString()
                });
                return originalSetItem.call(this, key, value);
            };
            
            window.__capturedStorage = storageEvents;
            
            // Also capture all current storage
            window.__allLocalStorage = {};
            window.__allSessionStorage = {};
            
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                window.__allLocalStorage[key] = localStorage.getItem(key);
            }
            
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                window.__allSessionStorage[key] = sessionStorage.getItem(key);
            }
        })();
        """

    async def _simulate_user_interaction(self, page):
        """
        Simuliert Nutzer-Interaktion, um lazy geladene Tracker auszulösen:
        Scrollen + kurze Wartezeit für nachladende AJAX-/Consent-Skripte.
        """
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
        except Exception as e:
            logger.debug(f"User-Interaktion-Simulation übersprungen: {e}")

    async def _compile_results(self) -> ScanResult:
        """
        Compile all intercepted data into structured ScanResult
        """
        # Categorize cookies by service
        categorized = {}
        for cookie in self.cookies:
            service = cookie.service or "Unknown"
            if service not in categorized:
                categorized[service] = {
                    "cookies": [],
                    "requests": [],
                    "storage": {}
                }
            categorized[service]["cookies"].append(asdict(cookie))
        
        # Categorize requests by service
        for request in self.requests:
            service = request.service or "Unknown"
            if service not in categorized:
                categorized[service] = {
                    "cookies": [],
                    "requests": [],
                    "storage": {}
                }
            categorized[service]["requests"].append(asdict(request))
        
        return ScanResult(
            scan_id=self.scan_id,
            url=self.url,
            cookies=self.cookies,
            requests=self.requests,
            storage=self.storage,
            categorized=categorized,
            total_cookies=len(self.cookies),
            unique_services=len(self.services_detected),
            total_requests=len(self.requests),
            services_detected=sorted(list(self.services_detected)),
            scan_duration_seconds=int((datetime.utcnow() - self.start_time).total_seconds()),
        )

    def _identify_service(self, url: str) -> Optional[str]:
        """
        Identify service/vendor from URL using pattern matching
        """
        url_lower = url.lower()
        
        for service, patterns in SERVICE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return service
        
        # Check domain for brand name
        domain = urlparse(url).netloc.lower()
        domain_parts = domain.split(".")
        
        if domain_parts:
            main_domain = domain_parts[-2]  # Get main domain (e.g., "google" from "analytics.google.com")
            # This is a simple heuristic; real implementation would need better logic
            return main_domain.capitalize()
        
        return None

    def _get_request_type(self, request) -> str:
        """
        Determine request type from request object
        """
        # In production, inspect request.resourceType or Content-Type header
        url_lower = request.url.lower()
        
        if ".js" in url_lower:
            return "script"
        elif ".css" in url_lower:
            return "stylesheet"
        elif any(img in url_lower for img in [".png", ".jpg", ".gif", ".webp"]):
            return "image"
        elif "api" in url_lower or "endpoint" in url_lower:
            return "xhr"
        else:
            return "other"
