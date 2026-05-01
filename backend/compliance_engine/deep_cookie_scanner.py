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
from typing import Dict, List, Optional, Set, Any
import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

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
        Execute full scan: navigate, intercept, simulate, collect
        """
        self.start_time = datetime.utcnow()
        
        try:
            # 1. Navigate to URL and set up interception
            await self._setup_interception()
            
            # 2. Navigate to page (triggers all initial scripts)
            await self._navigate_page()
            
            # 3. Simulate user interactions to trigger lazy tracking
            await self._simulate_user_interaction()
            
            # 4. Compile and categorize results
            result = await self._compile_results()
            
            return result
        except Exception as e:
            # Return failed result
            result = ScanResult(
                scan_id=self.scan_id,
                url=self.url,
                scan_duration_seconds=int((datetime.utcnow() - self.start_time).total_seconds())
            )
            result.error = str(e)
            return result

    async def _setup_interception(self):
        """
        Set up browser-level interception for:
        - HTTP response headers (Set-Cookie)
        - Network requests (XHR, Fetch, Img, etc.)
        - Storage APIs (localStorage, sessionStorage)
        """
        # In production, use pyppeteer.Browser.setRequestInterception()
        # Example pseudocode:
        # await self.browser.client.send("Network.enable")
        # await self.browser.client.send("Network.setUserAgentOverride", ...)
        # self.browser.on('response', self._intercept_response)
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

    async def _simulate_user_interaction(self):
        """
        Simulate user interactions to trigger lazy-loaded trackers:
        - Scroll to bottom
        - Hover over elements
        - Click buttons
        - Wait for AJAX requests
        """
        # Pseudocode:
        # await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        # await page.hover("body > *")
        # await page.click("button")
        # await page.waitForNavigation({waitUntil: "networkidle2", timeout: 5000})
        pass

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
