"""
Deep Cookie Scanner Engine
Comprehensive cookie and tracking detection via Playwright + Headless Chromium.

Architektur:
1. Startet Headless-Chromium, navigiert zur Ziel-URL (wait_until=networkidle)
2. Erfasst alle ausgehenden Requests (Script/XHR/Img/Font/...)
3. Liest die real gesetzten Cookies aus dem Browser-Context
4. Erfasst localStorage/sessionStorage
5. Simuliert Nutzer-Interaktion (Scroll) für lazy-geladene Tracker
6. Identifiziert Dienste über den cookie_services-Katalog (Domains + Cookie-Namen)
   → echter Dienstname, Anbieter, Kategorie und service_key statt Heuristik-Rauschen
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
    service_key: Optional[str] = None
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
    service_keys: List[str] = field(default_factory=list)
    scan_duration_seconds: int = 0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def _cookie_pattern_match(name: str, pattern: str) -> bool:
    """Cookie-Name gegen Katalog-Pattern (unterstützt Präfix/Suffix-Wildcard `*`)."""
    if not name or not pattern:
        return False
    p = pattern.strip()
    if p.endswith("*"):
        return name.startswith(p[:-1])
    if p.startswith("*"):
        return name.endswith(p[1:])
    return name == p


class CatalogMatcher:
    """
    Matcht erkannte Request-URLs und Cookie-Namen gegen den cookie_services-Katalog.
    Erwartet Service-Dicts: {service_key, name, category, provider, domains[], cookie_patterns[]}.
    """

    def __init__(self, services: Optional[List[dict]] = None):
        self.services = services or []

    def match_url(self, url: str) -> Optional[dict]:
        if not url:
            return None
        u = url.lower()
        for svc in self.services:
            for dom in svc.get("domains", []):
                # Nur echte Domains (mit Punkt) — verhindert, dass generische
                # Tokens wie "custom" jede URL fälschlich matchen.
                if dom and "." in dom and dom.lower() in u:
                    return svc
        return None

    def match_cookie(self, name: str) -> Optional[dict]:
        if not name:
            return None
        for svc in self.services:
            for pat in svc.get("cookie_patterns", []):
                if _cookie_pattern_match(name, pat):
                    return svc
        return None


# Label für Cookies/Requests, die keinem Katalog-Dienst zugeordnet werden konnten
# (typisch: First-Party-Session/CSRF). Bewusst KEIN domain.capitalize()-Rauschen.
UNMATCHED_LABEL = "Sonstige / First-Party"


class DeepCookieScanner:
    """
    Hauptscanner-Engine für umfassende Cookie-/Tracking-Erkennung.
    Optional wird ein cookie_services-Katalog (CatalogMatcher-Format) übergeben;
    ohne Katalog werden Dienste nicht klassifiziert.
    """

    def __init__(self, scan_id: int, url: str, catalog: Optional[List[dict]] = None, headless_browser=None):
        self.scan_id = scan_id
        self.url = url
        self.browser = headless_browser
        self.matcher = CatalogMatcher(catalog or [])
        self.cookies: List[Cookie] = []
        self.requests: List[Request] = []
        self.storage: Dict[str, Dict] = {"localStorage": {}, "sessionStorage": {}}
        # service_key -> {service_key, name, category, provider}
        self.detected_services: Dict[str, dict] = {}
        self.start_time = None

    def _register_service(self, svc: dict) -> None:
        key = svc.get("service_key") or svc.get("name")
        if not key:
            return
        if key not in self.detected_services:
            self.detected_services[key] = {
                "service_key": svc.get("service_key"),
                "name": svc.get("name"),
                "category": svc.get("category") or "functional",
                "provider": svc.get("provider") or "",
            }

    async def scan(self) -> ScanResult:
        """
        Echter Scan via Playwright: Browser starten, Requests + Cookies +
        Storage erfassen, Nutzer-Interaktion simulieren, Ergebnis kompilieren.
        """
        self.start_time = datetime.utcnow()

        if not PLAYWRIGHT_AVAILABLE:
            return ScanResult(scan_id=self.scan_id, url=self.url, error="Playwright nicht verfügbar")

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
                    # DOM-ready statt networkidle: Seiten mit Polling/Chat-Widgets erreichen
                    # nie Netzwerkruhe und liefen hier bei jedem Scan in den vollen Timeout.
                    # Netzwerkruhe bekommt danach eine begrenzte Chance — Tracker/Inhalte,
                    # die bis dahin nicht geladen sind, sieht der Scan eben nicht.
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    try:
                        # Tracker brauchen einen Moment zum Feuern — aber begrenzt.
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                except Exception as e:
                    logger.warning(f"Navigation langsam/teilweise für {url}: {e}")

                # Lazy-Tracker durch Interaktion triggern
                await self._simulate_user_interaction(page)

                # Cookies aus dem Browser-Context (echte gesetzte Cookies)
                try:
                    for c in await context.cookies():
                        name = c.get("name", "")
                        domain = c.get("domain", "")
                        # Dienst-Zuordnung: zuerst über den Cookie-Namen (präzise),
                        # sonst über die Cookie-Domain.
                        svc = self.matcher.match_cookie(name) \
                            or self.matcher.match_url("https://" + domain.lstrip("."))
                        cookie = Cookie(
                            name=name,
                            domain=domain,
                            path=c.get("path", "/"),
                            secure=c.get("secure", False),
                            httpOnly=c.get("httpOnly", False),
                            sameSite=c.get("sameSite", "Lax"),
                            expires=str(c.get("expires", "")),
                            service=(svc.get("name") if svc else None),
                            service_key=(svc.get("service_key") if svc else None),
                            category=(svc.get("category") if svc else "uncategorized"),
                        )
                        self.cookies.append(cookie)
                        if svc:
                            self._register_service(svc)
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
            return ScanResult(
                scan_id=self.scan_id,
                url=self.url,
                scan_duration_seconds=int((datetime.utcnow() - self.start_time).total_seconds()),
                error=str(e),
            )

    def _on_request(self, request):
        """Sync-Handler für page.on('request') — erfasst jeden Request + Dienst."""
        try:
            svc = self.matcher.match_url(request.url)
            self.requests.append(Request(
                url=request.url,
                method=request.method,
                type=request.resource_type,
                service=(svc.get("name") if svc else None),
            ))
            if svc:
                self._register_service(svc)
        except Exception:
            pass

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
        Verdichtet alle erfassten Daten in eine strukturierte ScanResult.
        categorized ist nach Dienstname gruppiert und trägt service_key/category/provider
        für die 1-Klick-Übernahme in die Banner-Config.
        """
        by_name = {m["name"]: m for m in self.detected_services.values() if m.get("name")}
        categorized: Dict[str, Dict] = {}

        def bucket(name: str) -> Dict:
            if name not in categorized:
                meta = by_name.get(name, {})
                categorized[name] = {
                    "service_key": meta.get("service_key"),
                    "category": meta.get("category"),
                    "provider": meta.get("provider"),
                    "cookies": [],
                    "requests": [],
                    "storage": {},
                }
            return categorized[name]

        for cookie in self.cookies:
            bucket(cookie.service or UNMATCHED_LABEL)["cookies"].append(asdict(cookie))

        # Nur dienst-zugeordnete Requests einsortieren — kein First-Party-Rauschen.
        for request in self.requests:
            if request.service:
                bucket(request.service)["requests"].append(asdict(request))

        service_keys = sorted({m["service_key"] for m in self.detected_services.values() if m.get("service_key")})
        services_detected = sorted({m["name"] for m in self.detected_services.values() if m.get("name")})

        return ScanResult(
            scan_id=self.scan_id,
            url=self.url,
            cookies=self.cookies,
            requests=self.requests,
            storage=self.storage,
            categorized=categorized,
            total_cookies=len(self.cookies),
            unique_services=len(self.detected_services),
            total_requests=len(self.requests),
            services_detected=services_detected,
            service_keys=service_keys,
            scan_duration_seconds=int((datetime.utcnow() - self.start_time).total_seconds()),
        )
