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
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from compliance_engine.checks.shop_check import detect_shop
from compliance_engine.sicherer_abruf import hole

logger = logging.getLogger(__name__)

from compliance_engine.check_spec_rules import (
    detection_is_weak,
    gate_entscheidet_nichts,
    gate_keyword_too_short,
    MIN_GATE_KEYWORD_LEN,
    SUCHRAEUME,
    AUTO_CHECK_RISK_CAP as _RISK_CAP,
)
from compliance_engine.scan_kontext import erfuellt as _kontext_erfuellt


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
def _sichtbarer_text(soup: BeautifulSoup, html_lower: str) -> str:
    """
    Sichtbarer Seitentext in Kleinschreibung — ohne Skripte, Stile und Attribute.

    Das Gate fragt "geht es auf dieser Seite fachlich um X?". Ein Klassenname
    wie "partner-logo" oder eine JS-Variable "review" beantwortet das nicht.
    """
    try:
        kopie = soup
        text = kopie.get_text(separator=" ")
    except Exception:
        return html_lower
    return " ".join(text.split()).lower()


# Bis zu dieser Laenge matcht ein Keyword nur als GANZES Wort. Grund (Audit
# 2026-08): die Wortanfang-Regel machte aus dem Gate-Keyword "ki" einen Treffer
# auf "Kindermobiliar", "Kino", "Kiefer" — eine Ferienpark-Seite ohne jede KI
# bekam einen AI-Act-Befund ueber 15.000 EUR, eine Zahnarztseite 20.000 EUR.
KURZ_KEYWORD_MAX_LEN = 3


def _keyword_trifft(keyword: str, text: str) -> bool:
    """
    Trifft das Keyword als eigenes Wort — oder als Anfang eines Kompositums?

    Ab 4 Zeichen gilt der Wortanfang, weil deutsche Komposita sonst
    durchrutschen: "Grünstrom" und "Kündigungsbutton" SOLLEN treffen. Am
    Wortende wird nicht geschnitten, dafuer aber am Anfang — so trifft "grün"
    nicht mehr "Hintergrund".

    Bis KURZ_KEYWORD_MAX_LEN Zeichen wird beidseitig geschnitten: ein Fragment
    aus zwei bis drei Buchstaben trifft als Wortanfang zu viel ("ki" ->
    Kindermobiliar, "bot" -> Botschaft). Der Preis ist, dass ein kurzes
    Keyword sein Kompositum nicht mehr findet ("abo" trifft "Abo", nicht
    "Abomodell") — ein verpasster Fund ist hier billiger als ein erfundener.
    """
    k = (keyword or "").strip().lower()
    if not k:
        return False
    if len(k) <= KURZ_KEYWORD_MAX_LEN:
        return re.search(r"(?<![\w])" + re.escape(k) + r"(?![\w])", text) is not None
    return re.search(r"(?<![\w])" + re.escape(k), text) is not None


def _gate_passes(applies_when: Dict[str, Any], soup: BeautifulSoup, html_lower: str) -> bool:
    if not applies_when or applies_when.get("always") is True:
        return True

    # AND über alle gesetzten Bedingungen
    if applies_when.get("site_type") == "shop":
        if not detect_shop(soup):
            return False

    kw_any = applies_when.get("keywords_any")
    kw_all = applies_when.get("keywords_all")
    if not kw_any and not kw_all:
        return True

    text = _sichtbarer_text(soup, html_lower)

    if kw_any and not any(_keyword_trifft(k, text) for k in kw_any):
        return False

    if kw_all and not all(_keyword_trifft(k, text) for k in kw_all):
        return False

    return True


# ---------------------------------------------------------------------------
# Detektion eines Pflicht-Elements
# ---------------------------------------------------------------------------
async def _url_exists(url: str, session=None) -> bool:
    """Antwortet die Kandidatenseite mit 200? Abruf über die SSRF-Schranke."""
    abruf = await hole(session, url, timeout=8)
    return abruf is not None and abruf.status == 200


async def _fetch_text(url: str, session=None) -> Optional[str]:
    """Inhalt der Kandidatenseite, oder None. Abruf über die SSRF-Schranke."""
    abruf = await hole(session, url, timeout=10)
    return abruf.text() if abruf is not None and abruf.status == 200 else None


# ---------------------------------------------------------------------------
# Suchraum: WO die Pruefung nachsehen darf
# ---------------------------------------------------------------------------
# Eine Pruefung behauptet etwas ueber eine Stelle der Website. Bis zum
# 09.09.2026 durchsuchte jede von ihnen den gesamten Seitenquelltext, egal was
# ihr Titel sagte. Das ging in beide Richtungen schief, und zwar an derselben
# Pruefung an einem Tag:
#
#   "Das Cookie-Consent-Banner informiert nicht ueber die Gueltigkeitsdauer"
#   verlangte woertlich "6 Monate" irgendwo auf der Seite. Ein Banner, das
#   "12 Monate" sagt, fiel durch (Fehlalarm). Nach dem Aufweichen des Musters
#   traf es den Satz "...16 Jahre alt sind und Ihre Einwilligung..." aus dem
#   Fliesstext, und die Pruefung sprach frei, ohne je im Banner gewesen zu sein
#   (Fehl-Freispruch).
#
# Beides verschwindet, sobald die Pruefung sagen kann, wo sie nachsieht.
#
# Grundsatz wie bei `requires`: laesst sich der Raum auf dieser Seite nicht
# bestimmen, wird NICHT geprueft. Ein fehlender Suchraum ist kein fehlendes
# Element — wer keinen Banner hat, verletzt keine Bannerpflicht.
#
# Die Namen stehen in der Regel-SSOT (check_spec_rules), weil der Generator sie
# genauso braucht; aufgeloest werden sie hier.

# Wie die Rechtsseiten gefunden werden. Bewusst knapp und ohne die generischen
# Faelle, die check_spec_rules als Universalschluessel kennt — hier ist der
# Link NICHT der Nachweis, sondern nur der Weg zum Suchraum.
_SEITEN_LINKS = {
    "agb": (["agb", "allgemeine-geschaeftsbedingungen", "terms", "nutzungsbedingungen",
             "geschaeftsbedingungen", "tos", "gtc"],
            ["agb", "allgemeine geschäftsbedingungen", "nutzungsbedingungen",
             "terms of service", "geschäftsbedingungen"]),
    "datenschutz": (["datenschutz", "privacy", "dsgvo", "gdpr", "data-protection"],
                    ["datenschutz", "datenschutzerklärung", "privacy policy"]),
    "impressum": (["impressum", "imprint", "legal-notice"],
                  ["impressum", "imprint"]),
}


class Suchraum:
    """Ein aufgeloester Suchraum: Markup plus Herkunftsangabe fuer den Befund."""

    __slots__ = ("name", "soup", "html_lower", "quelle")

    def __init__(self, name: str, soup: BeautifulSoup, quelle: Optional[str] = None):
        self.name = name
        self.soup = soup
        self.html_lower = str(soup).lower()
        self.quelle = quelle


async def _hole_suchraum(
    name: str,
    url: str,
    soup: BeautifulSoup,
    html_lower: str,
    session=None,
    zwischenspeicher: Optional[Dict[str, Any]] = None,
) -> Optional[Suchraum]:
    """Loest einen Suchraum auf. None heisst: auf dieser Seite nicht vorhanden.

    Der Zwischenspeicher gilt fuer EINEN Seitenlauf: mehrere Pruefungen mit
    demselben Raum holen die Unterseite sonst mehrfach.
    """
    if zwischenspeicher is not None and name in zwischenspeicher:
        return zwischenspeicher[name]

    raum: Optional[Suchraum] = None

    if name == "seite":
        raum = Suchraum(name, soup, url)

    elif name == "consent_banner":
        from compliance_engine.checks.cookie_check import _find_consent_container
        behaelter = _find_consent_container(soup)
        if behaelter is not None:
            raum = Suchraum(name, behaelter, url)

    elif name in _SEITEN_LINKS:
        href_kw, text_kw = _SEITEN_LINKS[name]
        ziel = None
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").lower()
            text = a.get_text(strip=True).lower()
            if any(k in href for k in href_kw) or any(k == text for k in text_kw):
                ziel = urljoin(url, a.get("href", ""))
                break
        if ziel:
            roh = await _fetch_text(ziel, session)
            if roh:
                raum = Suchraum(name, BeautifulSoup(roh, "html.parser"), ziel)

    if zwischenspeicher is not None:
        zwischenspeicher[name] = raum
    return raum


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
        # Laufzeit-Deckel: schutz vor DB-Altlasten (bis 300.000 EUR risk_euro
        # in Kundenreports), unabhaengig vom Timing des DB-Cleanups.
        "risk_euro": min(int(risk_euro), _RISK_CAP),
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
    raeume: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    detection = check.get("detection", {})
    dtype = detection.get("type", "required_element")

    # Defense in Depth: neutralisierte Detections (generische Rechtsseiten-
    # Link-Keywords ohne content_requirements) erzeugen weder Schein-Pass
    # noch False Positives — sie werden uebersprungen, selbst wenn eine
    # solche Spec (Altbestand/Migration) noch in der DB liegt.
    if detection_is_weak(detection):
        logger.warning(
            f"Declarative check '{check['slug']}': weak detection "
            f"(generische Link-Keywords ohne content_requirements) — skipped"
        )
        return []

    if dtype != "required_element":
        logger.warning(f"Declarative check '{check['slug']}': unsupported detection.type '{dtype}' — skipped")
        return []

    # Suchraum bestimmen. Unbekannter Name oder auf dieser Seite nicht
    # vorhanden: nicht pruefen. Beides ist die sichere Richtung — ein fehlender
    # Suchraum belegt kein fehlendes Element.
    raum_name = detection.get("scope") or "seite"
    if raum_name not in SUCHRAEUME:
        logger.warning(
            f"Declarative check '{check['slug']}': unbekannter Suchraum "
            f"'{raum_name}' — skipped"
        )
        return []

    raum = await _hole_suchraum(raum_name, url, soup, html_lower, session, raeume)
    if raum is None:
        logger.debug(
            f"Declarative check '{check['slug']}': Suchraum "
            f"'{raum_name}' auf dieser Seite nicht vorhanden — nicht anwendbar"
        )
        return []

    # Kandidaten-Pfade probt nur der Seitenraum: in einem Bannerausschnitt oder
    # auf einer Rechtsseite nach /transparenzbericht zu suchen, ergibt keinen Sinn.
    if raum_name != "seite" and detection.get("url_paths"):
        detection = {**detection, "url_paths": []}

    result = await _detect_required_element(
        detection, raum.quelle or url, raum.soup, raum.html_lower, session
    )

    if not result["found"]:
        beschreibung = check["description"]
        if raum_name != "seite":
            # Ohne diese Angabe ist der Befund nicht nachpruefbar: der Leser
            # weiss sonst nicht, wo der Scanner ueberhaupt nachgesehen hat.
            beschreibung += f" Geprüft wurde {SUCHRAEUME[raum_name]}"
            beschreibung += f" ({raum.quelle})." if raum.quelle and raum_name != "consent_banner" else "."
        return [_issue_dict(
            check,
            title=check["title"],
            description=beschreibung,
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


async def run_declarative_checks(
    url: str,
    soup: BeautifulSoup,
    session=None,
    kontext: Optional[Dict[str, bool]] = None,
) -> List[Dict[str, Any]]:
    """
    Einstiegspunkt für den Scanner. Lädt aktive deklarative Checks aus der
    Registry, wertet Gate + Detektion aus und liefert Issue-Dicts im selben
    Format wie die hartcodierten Checks.

    `kontext` sind die für diese Seite belegten Tatsachen
    (compliance_engine.scan_kontext.ermittle). Eine Prüfung, deren
    `applies_when.requires` darin keine Deckung findet, läuft nicht — die
    Pflicht, die sie prüft, besteht für diese Seite nicht.

    Ohne Kontext (Altpfad, Test) laufen nur Prüfungen ohne `requires`; bedingte
    Pflichten werden übersprungen statt auf Verdacht behauptet.
    """
    if declarative_check_registry is None:
        return []

    checks = await declarative_check_registry.get_active_checks()
    if not checks:
        return []

    html_lower = str(soup).lower()
    issues: List[Dict[str, Any]] = []
    # Ein Zwischenspeicher je Seitenlauf: zwoelf Pruefungen mit dem Suchraum
    # "datenschutz" holen die Unterseite sonst zwoelfmal.
    raeume: Dict[str, Any] = {}

    for check in checks:
        try:
            # Defense in Depth (analog weak detection): ein Gate-Keyword unter
            # MIN_GATE_KEYWORD_LEN Zeichen trifft beliebige Woerter. Solche
            # Specs lehnt der Generator ab; liegt noch eine im Altbestand,
            # wird sie hier uebersprungen statt Befunde zu erfinden.
            kurz = gate_keyword_too_short(check.get("applies_when") or {})
            if kurz:
                logger.warning(
                    f"Declarative check '{check.get('slug')}': Gate-Keyword "
                    f"'{kurz}' unter {MIN_GATE_KEYWORD_LEN} Zeichen — skipped"
                )
                continue
            # Gate-Staerke (Regel-SSOT): ein bedingungsloses oder rein
            # generisches Gate behauptet die Pflicht auf jeder Kundenseite.
            schwach = gate_entscheidet_nichts(check.get("applies_when") or {})
            if schwach:
                logger.warning(
                    f"Declarative check '{check.get('slug')}': {schwach} — skipped"
                )
                continue
            # Bedingte Pflicht: nur pruefen, wenn ihre Voraussetzung belegt ist.
            trifft_zu, grund = _kontext_erfuellt(
                (check.get("applies_when") or {}).get("requires"), kontext
            )
            if not trifft_zu:
                if grund.startswith("unbekannt:"):
                    logger.warning(
                        f"Declarative check '{check.get('slug')}': "
                        f"Voraussetzung {grund} — skipped"
                    )
                else:
                    logger.debug(
                        f"Declarative check '{check.get('slug')}': Voraussetzung "
                        f"'{grund}' auf dieser Seite nicht belegt — nicht anwendbar"
                    )
                continue
            if not _gate_passes(check.get("applies_when", {}), soup, html_lower):
                continue
            issues.extend(await _run_single_check(
                check, url, soup, html_lower, session, raeume=raeume
            ))
        except Exception as e:
            logger.warning(f"Declarative check '{check.get('slug')}' failed (non-critical): {e}")

    logger.info(f"Declarative checks: {len(issues)} Issues aus {len(checks)} aktiven Checks")
    return issues
