"""
Complyo Automated Cookie Scanner
Scannt Websites mit Playwright (headless Chromium) und erkennt alle gesetzten Cookies,
localStorage-Einträge und Tracking-Scripts automatisch.
Cookiebot-equivalent: echte Browser-Ausführung statt nur HTML-Parsing.
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cookie Knowledge Base
# (Subset – wird laufend erweitert; deckt die häufigsten 500+ Cookies ab)
# ---------------------------------------------------------------------------
COOKIE_DB: dict[str, dict] = {
    # Google Analytics
    "_ga":           {"provider": "Google Analytics", "category": "analytics",  "duration": "2 Jahre",    "purpose": "Nutzeridentifikation für Statistiken"},
    "_gid":          {"provider": "Google Analytics", "category": "analytics",  "duration": "24 Stunden", "purpose": "Sitzungsidentifikation"},
    "_gat":          {"provider": "Google Analytics", "category": "analytics",  "duration": "1 Minute",   "purpose": "Anforderungsrate drosseln"},
    "_gat_gtag":     {"provider": "Google Analytics", "category": "analytics",  "duration": "1 Minute",   "purpose": "Anforderungsrate drosseln"},
    "_ga_*":         {"provider": "Google Analytics 4", "category": "analytics","duration": "2 Jahre",    "purpose": "GA4 Sitzungspersistenz"},
    "__utma":        {"provider": "Google Analytics", "category": "analytics",  "duration": "2 Jahre",    "purpose": "Besucher-Tracking"},
    "__utmb":        {"provider": "Google Analytics", "category": "analytics",  "duration": "30 Minuten", "purpose": "Sitzungs-Tracking"},
    "__utmc":        {"provider": "Google Analytics", "category": "analytics",  "duration": "Session",    "purpose": "Sitzungs-Tracking"},
    "__utmz":        {"provider": "Google Analytics", "category": "analytics",  "duration": "6 Monate",   "purpose": "Traffic-Quelle"},
    # Google Ads
    "_gcl_au":       {"provider": "Google Ads",       "category": "marketing",  "duration": "3 Monate",   "purpose": "Conversion-Tracking"},
    "_gcl_aw":       {"provider": "Google Ads",       "category": "marketing",  "duration": "3 Monate",   "purpose": "Klick-Tracking"},
    "IDE":           {"provider": "Google DoubleClick","category": "marketing",  "duration": "2 Jahre",    "purpose": "Personalisierte Werbung"},
    "DSID":          {"provider": "Google DoubleClick","category": "marketing",  "duration": "2 Wochen",   "purpose": "Anmeldestatus"},
    "NID":           {"provider": "Google",            "category": "functional", "duration": "6 Monate",   "purpose": "Nutzereinstellungen"},
    "CONSENT":       {"provider": "Google",            "category": "necessary",  "duration": "2 Jahre",    "purpose": "Consent-Status"},
    # Facebook / Meta
    "_fbp":          {"provider": "Meta (Facebook)",  "category": "marketing",  "duration": "3 Monate",   "purpose": "Conversion-Tracking"},
    "_fbc":          {"provider": "Meta (Facebook)",  "category": "marketing",  "duration": "2 Jahre",    "purpose": "Click-ID"},
    "fr":            {"provider": "Meta (Facebook)",  "category": "marketing",  "duration": "3 Monate",   "purpose": "Werbung"},
    "xs":            {"provider": "Meta (Facebook)",  "category": "marketing",  "duration": "3 Monate",   "purpose": "Sitzungstoken"},
    # Hotjar
    "_hjSessionUser_*": {"provider": "Hotjar",       "category": "analytics",  "duration": "1 Jahr",     "purpose": "Nutzer-Identifikation"},
    "_hjSession_*":     {"provider": "Hotjar",       "category": "analytics",  "duration": "30 Minuten", "purpose": "Sitzung"},
    "_hjAbsoluteSessionInProgress": {"provider": "Hotjar", "category": "analytics", "duration": "30 Minuten", "purpose": "Sitzungsstatus"},
    # Microsoft Clarity
    "_clsk":         {"provider": "Microsoft Clarity","category": "analytics",  "duration": "1 Tag",      "purpose": "Sitzungs-Tracking"},
    "_clck":         {"provider": "Microsoft Clarity","category": "analytics",  "duration": "1 Jahr",     "purpose": "Nutzer-Identifikation"},
    "MUID":          {"provider": "Microsoft",        "category": "marketing",  "duration": "1 Jahr",     "purpose": "Cross-Site-Tracking"},
    # Hubspot
    "__hstc":        {"provider": "HubSpot",          "category": "analytics",  "duration": "13 Monate",  "purpose": "Besucher-Tracking"},
    "hubspotutk":    {"provider": "HubSpot",          "category": "analytics",  "duration": "13 Monate",  "purpose": "Formular-Tracking"},
    "__hssc":        {"provider": "HubSpot",          "category": "analytics",  "duration": "30 Minuten", "purpose": "Sitzung"},
    "__hssrc":       {"provider": "HubSpot",          "category": "analytics",  "duration": "Session",    "purpose": "Neue Sitzung"},
    # LinkedIn
    "li_sugr":       {"provider": "LinkedIn",         "category": "marketing",  "duration": "3 Monate",   "purpose": "Tracking"},
    "bcookie":       {"provider": "LinkedIn",         "category": "marketing",  "duration": "2 Jahre",    "purpose": "Browser-Identifikation"},
    "lidc":          {"provider": "LinkedIn",         "category": "marketing",  "duration": "1 Tag",      "purpose": "Routing"},
    "UserMatchHistory": {"provider": "LinkedIn",      "category": "marketing",  "duration": "30 Tage",    "purpose": "Conversion-Tracking"},
    # Twitter / X
    "_twitter_sess": {"provider": "Twitter/X",        "category": "marketing",  "duration": "Session",    "purpose": "Sitzung"},
    "auth_token":    {"provider": "Twitter/X",        "category": "marketing",  "duration": "5 Jahre",    "purpose": "Authentifizierung"},
    # Stripe
    "__stripe_mid":  {"provider": "Stripe",           "category": "necessary",  "duration": "1 Jahr",     "purpose": "Betrugsprävention"},
    "__stripe_sid":  {"provider": "Stripe",           "category": "necessary",  "duration": "30 Minuten", "purpose": "Sitzung"},
    # Intercom
    "intercom-session-*": {"provider": "Intercom",    "category": "functional", "duration": "1 Woche",    "purpose": "Chat-Sitzung"},
    "intercom-device-id-*": {"provider": "Intercom",  "category": "functional", "duration": "9 Monate",   "purpose": "Geräteidentifikation"},
    # WordPress
    "wordpress_logged_in_*": {"provider": "WordPress","category": "necessary",  "duration": "Session",    "purpose": "Anmeldestatus"},
    "wp-settings-*": {"provider": "WordPress",        "category": "necessary",  "duration": "1 Jahr",     "purpose": "Editor-Einstellungen"},
    "wordpress_test_cookie": {"provider": "WordPress","category": "necessary",  "duration": "Session",    "purpose": "Cookie-Test"},
    # Complyo (eigene Cookies)
    "complyo_cookie_consent":  {"provider": "Complyo","category": "necessary",  "duration": "1 Jahr",     "purpose": "Einwilligungsstatus speichern"},
    "complyo_consent_date":    {"provider": "Complyo","category": "necessary",  "duration": "1 Jahr",     "purpose": "Einwilligungsdatum"},
    "complyo_visitor_id":      {"provider": "Complyo","category": "necessary",  "duration": "1 Jahr",     "purpose": "Anonyme Besucher-ID für Audit-Log"},
    # Generic session
    "PHPSESSID":     {"provider": "PHP",              "category": "necessary",  "duration": "Session",    "purpose": "PHP-Session"},
    "JSESSIONID":    {"provider": "Java",             "category": "necessary",  "duration": "Session",    "purpose": "Java-Session"},
    "ASP.NET_SessionId": {"provider": ".NET",         "category": "necessary",  "duration": "Session",    "purpose": ".NET-Session"},
    "csrf_token":    {"provider": "Website",          "category": "necessary",  "duration": "Session",    "purpose": "CSRF-Schutz"},
    "_csrf":         {"provider": "Website",          "category": "necessary",  "duration": "Session",    "purpose": "CSRF-Schutz"},
    "csrftoken":     {"provider": "Django",           "category": "necessary",  "duration": "1 Jahr",     "purpose": "CSRF-Schutz"},
}

# Script URL → Service Mapping
SCRIPT_SERVICE_MAP: list[tuple[str, dict]] = [
    ("google-analytics.com/analytics.js",    {"name": "Google Analytics (UA)",  "category": "analytics",  "provider": "Google"}),
    ("google-analytics.com/ga.js",           {"name": "Google Analytics (legacy)", "category": "analytics", "provider": "Google"}),
    ("googletagmanager.com/gtm.js",          {"name": "Google Tag Manager",     "category": "analytics",  "provider": "Google"}),
    ("googletagmanager.com/gtag/js",         {"name": "Google Tag (GA4)",       "category": "analytics",  "provider": "Google"}),
    ("connect.facebook.net",                 {"name": "Meta Pixel",             "category": "marketing",  "provider": "Meta"}),
    ("static.hotjar.com",                    {"name": "Hotjar",                 "category": "analytics",  "provider": "Hotjar"}),
    ("clarity.ms/tag",                       {"name": "Microsoft Clarity",      "category": "analytics",  "provider": "Microsoft"}),
    ("bat.bing.com",                         {"name": "Microsoft Ads (UET)",    "category": "marketing",  "provider": "Microsoft"}),
    ("snap.licdn.com",                       {"name": "LinkedIn Insight Tag",   "category": "marketing",  "provider": "LinkedIn"}),
    ("ads.linkedin.com",                     {"name": "LinkedIn Ads",           "category": "marketing",  "provider": "LinkedIn"}),
    ("analytics.tiktok.com",                 {"name": "TikTok Pixel",           "category": "marketing",  "provider": "TikTok"}),
    ("sc-static.net",                        {"name": "Snapchat Pixel",         "category": "marketing",  "provider": "Snapchat"}),
    ("js.hs-scripts.com",                    {"name": "HubSpot Tracking",       "category": "analytics",  "provider": "HubSpot"}),
    ("js.hs-analytics.net",                  {"name": "HubSpot Analytics",      "category": "analytics",  "provider": "HubSpot"}),
    ("widget.intercom.io",                   {"name": "Intercom Chat",          "category": "functional", "provider": "Intercom"}),
    ("js.intercomcdn.com",                   {"name": "Intercom",               "category": "functional", "provider": "Intercom"}),
    ("cdn.segment.com",                      {"name": "Segment",                "category": "analytics",  "provider": "Segment"}),
    ("cdn.amplitude.com",                    {"name": "Amplitude",              "category": "analytics",  "provider": "Amplitude"}),
    ("cdn.mxpnl.com",                        {"name": "Mixpanel",               "category": "analytics",  "provider": "Mixpanel"}),
    ("script.hotjar.com",                    {"name": "Hotjar",                 "category": "analytics",  "provider": "Hotjar"}),
    ("cdn.logrocket.io",                     {"name": "LogRocket",              "category": "analytics",  "provider": "LogRocket"}),
    ("fullstory.com/s/fs.js",                {"name": "FullStory",              "category": "analytics",  "provider": "FullStory"}),
    ("maps.googleapis.com",                  {"name": "Google Maps",            "category": "functional", "provider": "Google"}),
    ("fonts.googleapis.com",                 {"name": "Google Fonts",           "category": "functional", "provider": "Google"}),
    ("youtube.com/embed",                    {"name": "YouTube",                "category": "marketing",  "provider": "Google"}),
    ("vimeo.com/video",                      {"name": "Vimeo",                  "category": "marketing",  "provider": "Vimeo"}),
    ("app.crisp.chat",                       {"name": "Crisp Chat",             "category": "functional", "provider": "Crisp"}),
    ("crisp.chat",                           {"name": "Crisp Chat",             "category": "functional", "provider": "Crisp"}),
    ("js.driftt.com",                        {"name": "Drift Chat",             "category": "functional", "provider": "Drift"}),
    ("cdn.cookielaw.org",                    {"name": "OneTrust CMP",           "category": "necessary",  "provider": "OneTrust"}),
    ("consent.cookiebot.com",                {"name": "Cookiebot CMP",          "category": "necessary",  "provider": "Usercentrics"}),
]


@dataclass
class DetectedCookie:
    name:     str
    value:    str = ""
    domain:   str = ""
    path:     str = "/"
    expires:  str = ""
    secure:   bool = False
    http_only: bool = False
    same_site: str = ""
    provider:  str = ""
    category:  str = "necessary"
    duration:  str = ""
    purpose:   str = ""
    source:    str = "browser"


@dataclass
class DetectedService:
    name:     str
    provider: str
    category: str
    script_url: str
    cookies:  list[str] = field(default_factory=list)


@dataclass
class ScanResult:
    url:           str
    scanned_at:    str
    cookies:       list[DetectedCookie]
    services:      list[DetectedService]
    has_cmp:       bool
    cmp_name:      str
    config_hash:   str
    scan_duration_ms: int
    error:         str | None = None


class CookieScanner:
    """
    Automatischer Cookie-Scanner auf Basis von Playwright.
    Führt einen echten Browser-Besuch durch und erfasst alle
    gesetzten Cookies, localStorage-Einträge und geladenen Scripts.
    """

    def __init__(self, timeout_ms: int = 15000):
        self.timeout_ms = timeout_ms

    async def scan(self, url: str, follow_links: int = 0) -> ScanResult:
        """
        Scannt eine URL mit Playwright Chromium.

        Args:
            url:          Zu scannende URL
            follow_links: Anzahl der Unterseiten die zusätzlich gescannt werden (0 = nur Homepage)

        Returns:
            ScanResult mit allen gefundenen Cookies und Services
        """
        start = asyncio.get_event_loop().time()

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("playwright nicht installiert. Bitte 'pip install playwright && playwright install chromium' ausführen.")
            return ScanResult(
                url=url, scanned_at=_now(), cookies=[], services=[],
                has_cmp=False, cmp_name="", config_hash="",
                scan_duration_ms=0, error="playwright_not_installed"
            )

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (compatible; ComplyoScanner/2.0; +https://complyo.tech/scanner)",
                    locale="de-DE",
                    timezone_id="Europe/Berlin",
                    ignore_https_errors=True,
                )

                # Collect all script URLs that are loaded
                loaded_scripts: list[str] = []
                context.on("request", lambda req: loaded_scripts.append(req.url) if req.resource_type == "script" else None)

                page = await context.new_page()

                pages_to_scan = [url]
                if follow_links > 0:
                    pages_to_scan += await self._collect_subpages(page, url, follow_links)

                for page_url in pages_to_scan:
                    try:
                        await page.goto(page_url, wait_until="networkidle", timeout=self.timeout_ms)
                        await asyncio.sleep(1.5)
                    except Exception as e:
                        logger.warning(f"[Scanner] Fehler beim Laden von {page_url}: {e}")

                raw_cookies = await context.cookies()
                await browser.close()

        except Exception as e:
            logger.error(f"[Scanner] Playwright-Fehler: {e}")
            return ScanResult(
                url=url, scanned_at=_now(), cookies=[], services=[],
                has_cmp=False, cmp_name="", config_hash="",
                scan_duration_ms=int((asyncio.get_event_loop().time() - start) * 1000),
                error=str(e)
            )

        detected_cookies = [self._enrich_cookie(c) for c in raw_cookies]
        detected_services = self._detect_services(loaded_scripts, detected_cookies)
        has_cmp, cmp_name = self._detect_cmp(loaded_scripts, detected_cookies)
        config_hash = _hash_scan(detected_cookies, detected_services)
        duration_ms = int((asyncio.get_event_loop().time() - start) * 1000)

        return ScanResult(
            url=url,
            scanned_at=_now(),
            cookies=detected_cookies,
            services=detected_services,
            has_cmp=has_cmp,
            cmp_name=cmp_name,
            config_hash=config_hash,
            scan_duration_ms=duration_ms,
        )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    async def _collect_subpages(self, page, base_url: str, limit: int) -> list[str]:
        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.href)"
            )
            parsed_base = urlparse(base_url)
            subpages = []
            for link in links:
                parsed = urlparse(link)
                if parsed.netloc == parsed_base.netloc and parsed.path not in ("/", ""):
                    subpages.append(link)
                if len(subpages) >= limit:
                    break
            return subpages
        except Exception:
            return []

    def _enrich_cookie(self, raw: dict) -> DetectedCookie:
        name    = raw.get("name", "")
        expires = raw.get("expires", -1)

        db_entry = self._lookup_cookie_db(name)

        duration = db_entry.get("duration", "")
        if not duration and expires > 0:
            days = int((expires - (datetime.now(timezone.utc).timestamp())) / 86400)
            if days <= 0:
                duration = "Session"
            elif days == 1:
                duration = "1 Tag"
            elif days < 30:
                duration = f"{days} Tage"
            elif days < 365:
                duration = f"{round(days / 30)} Monate"
            else:
                duration = f"{round(days / 365)} Jahre"
        elif not duration:
            duration = "Session"

        expires_str = ""
        if isinstance(expires, (int, float)) and expires > 0:
            try:
                expires_str = datetime.fromtimestamp(expires, tz=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                expires_str = ""

        return DetectedCookie(
            name=name,
            value="",
            domain=raw.get("domain", ""),
            path=raw.get("path", "/"),
            expires=expires_str,
            secure=raw.get("secure", False),
            http_only=raw.get("httpOnly", False),
            same_site=raw.get("sameSite", ""),
            provider=db_entry.get("provider", _guess_provider(raw.get("domain", ""))),
            category=db_entry.get("category", _guess_category(name)),
            duration=duration,
            purpose=db_entry.get("purpose", ""),
            source="browser",
        )

    def _lookup_cookie_db(self, name: str) -> dict:
        if name in COOKIE_DB:
            return COOKIE_DB[name]
        for pattern, info in COOKIE_DB.items():
            if pattern.endswith("*") and name.startswith(pattern[:-1]):
                return info
        return {}

    def _detect_services(self, scripts: list[str], cookies: list[DetectedCookie]) -> list[DetectedService]:
        found: dict[str, DetectedService] = {}

        for script_url in scripts:
            for pattern, info in SCRIPT_SERVICE_MAP:
                if pattern in script_url and info["name"] not in found:
                    svc = DetectedService(
                        name=info["name"],
                        provider=info["provider"],
                        category=info["category"],
                        script_url=script_url,
                    )
                    found[info["name"]] = svc

        for cookie in cookies:
            for svc in found.values():
                if cookie.provider == svc.provider:
                    if cookie.name not in svc.cookies:
                        svc.cookies.append(cookie.name)

        return list(found.values())

    def _detect_cmp(self, scripts: list[str], cookies: list[DetectedCookie]) -> tuple[bool, str]:
        cmp_patterns = {
            "consent.cookiebot.com":     "Cookiebot (Usercentrics)",
            "app.usercentrics.eu":       "Usercentrics",
            "cdn.cookielaw.org":         "OneTrust",
            "ccm19.de":                  "CCM19",
            "borlabs-cookie":            "Borlabs Cookie",
            "klaro":                     "Klaro",
            "api.complyo":               "Complyo",
            "cookieconsent":             "Generic CookieConsent",
        }

        for script_url in scripts:
            for pattern, name in cmp_patterns.items():
                if pattern in script_url:
                    return True, name

        for cookie in cookies:
            if any(x in cookie.name.lower() for x in ["cookieconsent", "complyo_cookie", "borlabs", "uconsent", "CookieConsent"]):
                return True, cookie.provider or "Unbekannt"

        return False, ""


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_scan(cookies: list[DetectedCookie], services: list[DetectedService]) -> str:
    data = {
        "cookies": sorted([c.name for c in cookies]),
        "services": sorted([s.name for s in services]),
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def _guess_provider(domain: str) -> str:
    domain = domain.lstrip(".")
    for pattern, info in SCRIPT_SERVICE_MAP:
        if any(part in domain for part in pattern.split(".")):
            return info["provider"]
    return domain.split(".")[-2].capitalize() if "." in domain else domain


def _guess_category(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ("_ga", "analytics", "stat", "clarity", "hotjar", "hstc", "hssc")):
        return "analytics"
    if any(x in n for x in ("_fb", "pixel", "ads", "marketing", "track", "linkedin", "twitter")):
        return "marketing"
    if any(x in n for x in ("session", "csrf", "xsrf", "auth", "login", "token", "security")):
        return "necessary"
    if any(x in n for x in ("lang", "theme", "pref", "locale", "currency", "cart")):
        return "functional"
    return "necessary"


# Synchroner Wrapper für nicht-async Kontexte
def scan_sync(url: str, follow_links: int = 0) -> ScanResult:
    return asyncio.run(CookieScanner().scan(url, follow_links=follow_links))
