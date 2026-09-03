"""
Post-Deploy-Verifikation: bestaetigt nach einem echten Fix-Deploy, dass der Fix
auf der Live-Seite tatsaechlich angekommen ist UND der zugehoerige Befund dort
nicht mehr auftritt.

Vorher gab es nach dem Deploy ueber die Auslieferungskanaele keinen Nachweis
"Issue weg" — nur einen Offline-Fixture-Test. Dieses Modul schliesst die Luecke
mit einem leichten HTTP-Re-Fetch (kein Playwright) und einer kategorie-
spezifischen Praesenz-/Abwesenheits-Pruefung.

Die Kernfunktion verify_fix(...) ist rein und deterministisch (ohne Netz),
damit sie testbar bleibt. fetch_html_for_verification(...) kapselt den Netz-Zugriff.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Semantische Attribute, deren Werte als "distinktive Marker" eines Fixes gelten.
_MARKER_ATTRS = ("alt", "aria-label", "aria-describedby", "lang", "title", "for")


def _extract_markers(fix_code: str) -> list:
    """Zieht distinktive Marker aus dem Fix (Attributwerte + sichtbarer Text)."""
    markers: list = []
    if not fix_code:
        return markers
    for attr in _MARKER_ATTRS:
        for m in re.findall(rf'{attr}\s*=\s*"([^"]+)"', fix_code, re.IGNORECASE):
            val = m.strip()
            if len(val) >= 4:
                markers.append(val)
    # sichtbarer Textinhalt zwischen Tags
    for text in re.findall(r">([^<>]{4,})<", fix_code):
        t = text.strip()
        if t and not t.startswith("<!--"):
            markers.append(t)
    # Dedupe, Reihenfolge erhalten
    seen = set()
    out = []
    for mk in markers:
        if mk not in seen:
            seen.add(mk)
            out.append(mk)
    return out


def _deploy_present(html: str, fix_code: str) -> Tuple[bool, str]:
    """True, wenn mind. ein distinktiver Marker des Fixes in der Live-Seite steht."""
    markers = _extract_markers(fix_code)
    if not markers:
        return False, "kein distinktiver Marker im Fix gefunden"
    hay = html or ""
    for mk in markers:
        if mk in hay:
            return True, f"Marker gefunden: {mk[:60]!r}"
    return False, "kein Marker des Fixes auf der Live-Seite gefunden"


def _imgs_without_alt(html: str) -> int:
    imgs = re.findall(r"<img\b[^>]*>", html or "", re.IGNORECASE)
    return sum(1 for img in imgs if "alt=" not in img.lower())


def _category_clean(html: str, category: str) -> Tuple[Optional[bool], str]:
    """
    Kategorie-spezifische Abwesenheits-/Praesenz-Pruefung.
    Rueckgabe True/False, oder None wenn fuer die Kategorie keine leichte
    Live-Pruefung existiert (dann darf sie die Verifikation nicht scheitern lassen).
    """
    cat = (category or "").lower()
    h = (html or "").lower()

    if any(k in cat for k in ("barriere", "accessibility", "a11y", "wcag", "alt")):
        missing = _imgs_without_alt(html)
        return (missing == 0), f"{missing} Bild(er) ohne alt"

    if "impressum" in cat:
        return ("impressum" in h), "Impressum-Bezug auf Seite" if "impressum" in h else "kein Impressum-Bezug"

    if "datenschutz" in cat or "dsgvo" in cat:
        return ("datenschutz" in h), "Datenschutz-Bezug auf Seite" if "datenschutz" in h else "kein Datenschutz-Bezug"

    return None, "keine leichte Live-Pruefung fuer diese Kategorie"


def verify_fix(html: str, category: str, fix_code: str) -> Dict[str, Any]:
    """
    Rein & deterministisch. Verifiziert anhand des gelieferten Live-HTML, ob der
    Fix angekommen ist und der Befund der Kategorie nicht mehr auftritt.
    """
    present, present_reason = _deploy_present(html, fix_code)
    clean, clean_reason = _category_clean(html, category)

    verified = bool(present and clean is not False)
    return {
        "verified": verified,
        "deploy_present": present,
        "category_clean": clean,  # True | False | None
        "reason": f"deploy_present={present} ({present_reason}); "
                  f"category_clean={clean} ({clean_reason})",
    }


async def fetch_html_for_verification(url: str, timeout: int = 12) -> Optional[str]:
    """Leichter HTTP-GET der Live-Seite (kein Playwright)."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        import aiohttp
        import ssl
        import certifi

        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True
            ) as r:
                if r.status == 200:
                    return await r.text()
                logger.warning(f"Post-Deploy-Verifikation: {url} -> HTTP {r.status}")
                return None
    except Exception as e:
        logger.warning(f"Post-Deploy-Verifikation: Fetch fehlgeschlagen ({url}): {e}")
        return None


async def verify_live_url(url: str, category: str, fix_code: str) -> Dict[str, Any]:
    """Holt die Live-Seite und verifiziert. Bei Fetch-Fehler: verified=False, fetched=False."""
    html = await fetch_html_for_verification(url)
    if html is None:
        return {"verified": False, "fetched": False, "reason": "Live-Seite nicht abrufbar"}
    result = verify_fix(html, category, fix_code)
    result["fetched"] = True
    return result
