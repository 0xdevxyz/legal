"""
Declarative Check Runner
========================
Generischer Interpreter für datengetriebene Compliance-Prüfungen aus der
Tabelle `compliance_checks`.

Bisher waren Website-Prüfungen hartcodierte Python-Funktionen. Eine neue
gesetzliche Pflicht erforderte handgeschriebenen Code + Deploy. Hier werden
Prüfungen als DATEN beschrieben (applies_when + detection) und zur Scan-Zeit
interpretiert — so kann der Legal-Change-Monitor neue Prüfungen automatisch
anlegen (siehe check_generator.py), ohne Code zu ändern.

Aktuell unterstütztes Detektions-Muster: "required_element" — für einen
gegebenen Seitentyp muss ein Pflicht-Element (Link / Pfad / Button / Text)
existieren; fehlt es, wird ein Issue erzeugt. Dieses Muster deckt den Großteil
der Compliance-Pflichten ab (Widerrufsbutton, Kündigungsbutton, AGB-Link,
Pflicht-Seiten, ...).
"""

import re
import ssl
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin

import aiohttp
import certifi
from bs4 import BeautifulSoup

from compliance_engine.checks.shop_check import detect_shop

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registry: lädt aktive Checks aus der DB, gecached mit TTL (analog rule_engine)
# ---------------------------------------------------------------------------
class DeclarativeCheckRegistry:
    """Hält die aktiven deklarativen Checks im Speicher (TTL-Cache)."""

    def __init__(self, db_pool, ttl_seconds: int = 300):
        self.db_pool = db_pool
        self.ttl_seconds = ttl_seconds
        self._cache: List[Dict[str, Any]] = []
        self._loaded_at: Optional[datetime] = None

    async def get_active_checks(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        if (
            not force_refresh
            and self._loaded_at
            and (datetime.now() - self._loaded_at).total_seconds() < self.ttl_seconds
        ):
            return self._cache

        if not self.db_pool:
            return self._cache

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, slug, category, title, description, recommendation,
                           legal_basis, severity, risk_euro, applies_when, detection,
                           effective_date
                    FROM compliance_checks
                    WHERE status = 'active'
                    ORDER BY severity DESC, risk_euro DESC
                    """
                )
                self._cache = [self._row_to_check(r) for r in rows]
                self._loaded_at = datetime.now()
                logger.info(f"✅ Loaded {len(self._cache)} declarative compliance checks")
                return self._cache
        except Exception as e:
            logger.error(f"DeclarativeCheckRegistry load failed: {e}", exc_info=True)
            return self._cache

    @staticmethod
    def _row_to_check(row) -> Dict[str, Any]:
        import json as _json

        def _as_dict(v):
            if isinstance(v, str):
                try:
                    return _json.loads(v)
                except Exception:
                    return {}
            return v or {}

        d = dict(row)
        d["applies_when"] = _as_dict(d.get("applies_when"))
        d["detection"] = _as_dict(d.get("detection"))
        return d


# Global instance (initialisiert in main_production.startup, analog legal_update_integration)
declarative_check_registry: Optional[DeclarativeCheckRegistry] = None


def init_declarative_check_registry(db_pool) -> DeclarativeCheckRegistry:
    global declarative_check_registry
    declarative_check_registry = DeclarativeCheckRegistry(db_pool)
    return declarative_check_registry


# ---------------------------------------------------------------------------
# Gate-Auswertung: ist die Prüfung für diese Seite relevant?
# ---------------------------------------------------------------------------
def _gate_passes(applies_when: Dict[str, Any], soup: BeautifulSoup, html_lower: str) -> bool:
    if not applies_when or applies_when.get("always") is True:
        return True

    # AND über alle gesetzten Bedingungen
    if applies_when.get("site_type") == "shop":
        if not detect_shop(soup):
            return False

    kw_any = applies_when.get("keywords_any")
    if kw_any and not any(k.lower() in html_lower for k in kw_any):
        return False

    kw_all = applies_when.get("keywords_all")
    if kw_all and not all(k.lower() in html_lower for k in kw_all):
        return False

    return True


# ---------------------------------------------------------------------------
# Detektion eines Pflicht-Elements
# ---------------------------------------------------------------------------
async def _url_exists(url: str, session=None) -> bool:
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        if session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as r:
                return r.status == 200
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as tmp:
            async with tmp.get(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as r:
                return r.status == 200
    except Exception:
        return False


async def _fetch_text(url: str, session=None) -> Optional[str]:
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        if session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as r:
                if r.status == 200:
                    return await r.text()
        else:
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            async with aiohttp.ClientSession(connector=connector) as tmp:
                async with tmp.get(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as r:
                    if r.status == 200:
                        return await r.text()
    except Exception:
        pass
    return None


async def _detect_required_element(
    detection: Dict[str, Any],
    base_url: str,
    soup: BeautifulSoup,
    html_lower: str,
    session=None,
) -> Dict[str, Any]:
    """
    Sucht das Pflicht-Element. Reihenfolge: Inline-HTML-Patterns -> Links ->
    Kandidaten-Pfade. Gibt {found: bool, found_url: Optional[str]} zurück.
    """
    link_href_kw = [k.lower() for k in detection.get("link_href_keywords", [])]
    link_text_kw = [k.lower() for k in detection.get("link_text_keywords", [])]
    html_patterns = detection.get("html_patterns", [])
    url_paths = detection.get("url_paths", [])

    # 1. Inline-Patterns (z.B. ein <button>Vertrag widerrufen</button>)
    for pat in html_patterns:
        try:
            if re.search(pat, html_lower, re.IGNORECASE):
                return {"found": True, "found_url": None}
        except re.error as e:
            logger.warning(f"Invalid html_pattern '{pat}': {e}")

    # 2. Links per href / Text / aria-label / title
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").lower()
        text = a.get_text(strip=True).lower()
        aria = (a.get("aria-label") or "").lower()
        title = (a.get("title") or "").lower()
        if any(k in href for k in link_href_kw):
            return {"found": True, "found_url": urljoin(base_url, a.get("href", ""))}
        if any(k in text or k in aria or k in title for k in link_text_kw):
            return {"found": True, "found_url": urljoin(base_url, a.get("href", ""))}

    # 3. Kandidaten-Pfade direkt proben
    if url_paths:
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in url_paths:
            candidate = base + path
            if await _url_exists(candidate, session):
                return {"found": True, "found_url": candidate}

    return {"found": False, "found_url": None}


def _issue_dict(check: Dict[str, Any], *, title: str, description: str,
                severity: str, risk_euro: int, is_missing: bool) -> Dict[str, Any]:
    return {
        "category": check["category"],
        "severity": severity,
        "title": title,
        "description": description,
        "risk_euro": int(risk_euro),
        "recommendation": check["recommendation"],
        "legal_basis": check["legal_basis"],
        "auto_fixable": False,
        "is_missing": is_missing,
        "metadata": {
            "declarative_check_slug": check["slug"],
            "declarative_check_id": check["id"],
        },
    }


async def _run_single_check(
    check: Dict[str, Any],
    url: str,
    soup: BeautifulSoup,
    html_lower: str,
    session=None,
) -> List[Dict[str, Any]]:
    detection = check.get("detection", {})
    dtype = detection.get("type", "required_element")

    if dtype != "required_element":
        logger.warning(f"Declarative check '{check['slug']}': unsupported detection.type '{dtype}' — skipped")
        return []

    result = await _detect_required_element(detection, url, soup, html_lower, session)

    if not result["found"]:
        return [_issue_dict(
            check,
            title=check["title"],
            description=check["description"],
            severity=check["severity"],
            risk_euro=check["risk_euro"],
            is_missing=True,
        )]

    # Element vorhanden -> optional Inhaltsanforderungen auf der Zielseite prüfen
    content_req = detection.get("content_requirements") or {}
    found_url = result.get("found_url")
    if content_req and found_url:
        text = await _fetch_text(found_url, session)
        if text:
            t = BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True).lower()
            missing = [label for label, pat in content_req.items()
                       if not _safe_search(pat, t)]
            if missing:
                return [_issue_dict(
                    check,
                    title=f"{check['title']} — unvollständig",
                    description=(
                        f"{check['title']} gefunden, aber ohne erkennbare Angaben zu: "
                        f"{', '.join(missing)}."
                    ),
                    severity="warning",
                    risk_euro=max(1, int(check["risk_euro"] * 0.6)),
                    is_missing=False,
                )]
    return []


def _safe_search(pattern: str, text: str) -> bool:
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return pattern.lower() in text


async def run_declarative_checks(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Einstiegspunkt für den Scanner. Lädt aktive deklarative Checks aus der
    Registry, wertet Gate + Detektion aus und liefert Issue-Dicts im selben
    Format wie die hartcodierten Checks.
    """
    if declarative_check_registry is None:
        return []

    checks = await declarative_check_registry.get_active_checks()
    if not checks:
        return []

    html_lower = str(soup).lower()
    issues: List[Dict[str, Any]] = []

    for check in checks:
        try:
            if not _gate_passes(check.get("applies_when", {}), soup, html_lower):
                continue
            issues.extend(await _run_single_check(check, url, soup, html_lower, session))
        except Exception as e:
            logger.warning(f"Declarative check '{check.get('slug')}' failed (non-critical): {e}")

    logger.info(f"Declarative checks: {len(issues)} Issues aus {len(checks)} aktiven Checks")
    return issues
