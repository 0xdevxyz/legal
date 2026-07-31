"""
Regel-SSOT fuer auto-generierte deklarative Compliance-Checks.

Von ZWEI Konsumenten genutzt (Defense in Depth):
- check_generator._validate_spec: lehnt fehlerhafte Specs bei der GENERIERUNG ab
- declarative_check_runner: skippt fehlerhafte Bestands-Checks zur LAUFZEIT

Hintergrund (Audit 2026-07): 15 aktive Checks waren "neutralisiert" (generische
Datenschutz-Link-Keywords ohne content_requirements -> jede Seite mit DS-Link
"besteht", obwohl der Titel Inhaltstiefe verspricht), 1 Check hatte invertierte
Logik (fonts.googleapis.com als PFLICHT-Element -> feuerte genau bei Seiten OHNE
den Verstoss), und drei Cookie-Checks trugen 300.000 EUR risk_euro.
"""

from typing import Any, Dict, Optional

# Generische Rechtsseiten-Signale: als Link-Keyword matchen sie auf praktisch
# jeder Website (Runner-Schritt 2 macht sie zum Universalschluessel). Ein Check,
# der NUR darueber findet, prueft nichts — er braucht content_requirements.
GENERIC_LINK_KEYWORDS = frozenset({
    "datenschutz", "datenschutzerklaerung", "datenschutzerklärung", "privacy",
    "privacy-policy", "dsgvo", "gdpr", "data-protection",
    "impressum", "imprint", "legal", "rechtliches",
    "agb", "terms",
    "cookie", "cookies", "consent", "einwilligung",
})

# Anwesenheit dieser Muster IST der Verstoss — sie duerfen nie als
# required_element (Pflicht-Element) verlangt werden (invertierte Logik).
VIOLATION_INDICATOR_PATTERNS = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "google-analytics.com",
    "googletagmanager.com",
    "connect.facebook.net",
    "facebook.com/tr",
    "doubleclick.net",
    "googlesyndication.com",
    "static.hotjar.com",
    "analytics.tiktok.com",
)

# KMU-Deckel fuer auto-generierte Checks. Die drei 300.000-EUR-Cookie-Checks
# des Altbestands waren fuer KMU-Reports absurd; zur Laufzeit wird zusaetzlich
# hart gekappt (declarative_check_runner._issue_dict).
AUTO_CHECK_RISK_CAP = 25000


def _keywords(detection: Dict[str, Any]) -> "list[str]":
    kws = list(detection.get("link_href_keywords") or [])
    kws += list(detection.get("link_text_keywords") or [])
    return [str(k).lower().strip() for k in kws if str(k).strip()]


def detection_is_weak(detection: Dict[str, Any]) -> bool:
    """
    True, wenn die Detection ueber generische Rechtsseiten-Link-Keywords
    "findet", ohne den Zielinhalt zu pruefen (kein content_requirements).
    Solche Checks bestehen auf jeder Seite mit DS-/Impressum-Link und sind
    damit wirkungslos (oder taeuschen Tiefenpruefung vor). Reine
    Existenz-Pruefungen deckt bereits der hartcodierte Check-Satz ab.
    """
    if not isinstance(detection, dict):
        return True
    if detection.get("content_requirements"):
        return False
    for kw in _keywords(detection):
        if any(generic in kw for generic in GENERIC_LINK_KEYWORDS):
            return True
    return False


def detection_is_inverted(detection: Dict[str, Any]) -> Optional[str]:
    """
    Gibt den Verstoss-Indikator zurueck, wenn die Detection ein Element als
    Pflicht verlangt, dessen ANWESENHEIT selbst der Verstoss ist — sonst None.
    (required_element-Semantik: Issue wenn NICHT gefunden -> ein solcher Check
    feuert genau bei konformen Seiten und schweigt beim Verstoss.)
    """
    if not isinstance(detection, dict):
        return None
    blobs = list(detection.get("html_patterns") or []) + _keywords(detection)
    for blob in blobs:
        low = str(blob).lower()
        for indicator in VIOLATION_INDICATOR_PATTERNS:
            if indicator in low:
                return indicator
    return None
