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

# Mindestlaenge fuer Gate-Keywords (applies_when.keywords_any/_all).
# Hintergrund (Audit 2026-08): Check #278 trug "ki" und "ai" als Gate-Keywords.
# Der Runner matcht am Wortanfang, damit deutsche Komposita treffen — "ki" traf
# damit "Kindermobiliar", "Kino", "Kiefer". Eine Ferienpark-Seite ohne jede KI
# bekam so einen AI-Act-Befund ueber 15.000 EUR. Zwei Zeichen tragen keine
# Aussage; wer KI-Bezug meint, schreibt "ki-assistent" oder "chatbot".
MIN_GATE_KEYWORD_LEN = 3


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


def gate_keyword_too_short(applies_when: Dict[str, Any]) -> Optional[str]:
    """
    Gibt das erste zu kurze Gate-Keyword zurueck, sonst None.

    Gate-Keywords unter MIN_GATE_KEYWORD_LEN Zeichen sind keine Bedingung,
    sondern ein Zufallsgenerator: sie treffen ueber die Wortanfang-Regel des
    Runners beliebige Woerter und erzeugen Befunde auf Seiten, die mit dem
    Thema nichts zu tun haben.
    """
    if not isinstance(applies_when, dict):
        return None
    for field in ("keywords_any", "keywords_all"):
        for kw in applies_when.get(field) or []:
            k = str(kw).strip().lower()
            if 0 < len(k) < MIN_GATE_KEYWORD_LEN:
                return k
    return None


# ---------------------------------------------------------------------------
# Gate-Staerke: entscheidet die Bedingung ueberhaupt etwas?
# ---------------------------------------------------------------------------
# Hintergrund (Selbstscan 08.09.2026): complyo.de bekam im eigenen Scanner 13
# Befunde, davon 9 aus deklarativen Checks — ueber einen Cookie-Banner, den es
# auf der Seite nicht gibt, und ueber Drittlandtransfers, die nicht
# stattfinden. Ursache waren zwei Gate-Formen, die keine Bedingung sind:
#
#   {"always": true}                     laeuft auf jeder Website
#   {"keywords_any": ["cookie", ...]}    trifft jede Seite, die ueber Cookies
#                                        SCHREIBT (Footer-Link genuegt)
#
# Beide erzeugen den Befund unabhaengig davon, ob die Pflicht besteht. Fast
# jede Pflicht ist aber bedingt: der Ablehnen-Knopf setzt einen Banner voraus,
# der USA-Hinweis einen USA-Transfer. Die Bedingung gehoert deshalb in
# `applies_when.requires` und wird gegen belegte Tatsachen geprueft
# (compliance_engine.scan_kontext), nicht gegen Werbetexte.
#
# Diese Woerter kommen in gewoehnlichen Geschaeftstexten vor und grenzen darum
# nichts ein. Ein Gate, das NUR aus solchen Woertern besteht, ist keines.
GENERISCHE_GATE_KEYWORDS = frozenset({
    "cookie", "cookies", "consent", "einwilligung", "zustimmung", "zustimm",
    "tracking", "analytics", "pixel", "daten", "datenschutz",
    "shop", "plattform", "marktplatz", "marketplace", "online-plattform",
    "anzeigen", "anzeige", "werbung", "bewertung", "bewertungen",
    "anmelden", "abonnieren", "subscribe", "kunden", "service", "angebot",
    "produkte", "online", "digital", "software", "website", "webseite",
})


def gate_entscheidet_nichts(applies_when: Dict[str, Any]) -> Optional[str]:
    """
    Gibt den Grund zurueck, wenn das Gate die Pflicht nicht eingrenzt — sonst None.

    Als Eingrenzung zaehlen:
      * `requires`  — belegte Tatsachen (der belastbare Weg, siehe scan_kontext)
      * `site_type` — struktureller Seitentyp (z.B. Shop-Erkennung)
      * mindestens EIN Gate-Keyword, das kein Allerweltswort ist

    Alles andere laeuft praktisch auf jeder Kundenseite und erzeugt dort den
    Befund einer Pflicht, die es nicht gibt.
    """
    if not isinstance(applies_when, dict):
        return "applies_when fehlt"

    if [str(r).strip() for r in (applies_when.get("requires") or []) if str(r).strip()]:
        return None
    if applies_when.get("site_type"):
        return None
    # Ausdrueckliche Universalpflicht. Es gibt sie wirklich — Impressum und
    # Datenschutzerklaerung schuldet jede geschaeftsmaessige Website. Sie
    # braucht aber ein eigenes Wort, damit sie eine Entscheidung ist und kein
    # Vorgabewert: `always: true` stand in acht Pruefungen, weil niemand eine
    # Bedingung eingetragen hatte, nicht weil die Pflicht universal waere.
    if applies_when.get("jede_website") is True:
        return None

    keywords = [
        str(k).strip().lower()
        for feld in ("keywords_any", "keywords_all")
        for k in (applies_when.get(feld) or [])
        if str(k).strip()
    ]
    if not keywords:
        return (
            "bedingungslos (always/leer) ohne applies_when.requires — die "
            "Pflicht wuerde auf jeder Kundenseite behauptet"
        )
    if all(k in GENERISCHE_GATE_KEYWORDS for k in keywords):
        return (
            f"nur generische Gate-Stichwoerter ({', '.join(sorted(set(keywords)))}) "
            f"ohne applies_when.requires — sie treffen jede Seite, die ueber das "
            f"Thema schreibt, nicht die, fuer die die Pflicht gilt"
        )
    return None
