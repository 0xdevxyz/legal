"""
Privacy Transfer Findings — SSOT für "Drittlandtransfer ohne Einwilligung"

Erkennt Drittanbieter-Ressourcen, die beim Laden die IP-Adresse des Nutzers
(personenbezogenes Datum) OHNE vorherige Einwilligung an Server außerhalb der
EU/des EWR übertragen. Das ist KEIN Cookie-Problem — diese Dienste setzen
typischerweise gar keine Cookies — sondern ein Drittlandtransfer nach
DSGVO Art. 44 ff. i.V.m. Art. 6 Abs. 1.

Leitfall: Google Fonts, extern geladen → LG München I, Urt. v. 20.01.2022,
Az. 3 O 17493/20 (100 € Schadensersatz pro betroffenem Nutzer). Dieselbe
juristische Logik greift bei reCAPTCHA, Google Maps, YouTube (nicht
-nocookie) und Adobe/Monotype-Webfonts.

WICHTIG — Genauigkeit:
- Erkennung läuft primär gegen die ECHTEN Netzwerk-Requests des Headless-
  Scanners (fängt auch Fonts via CSS @import / JS-Injection), HTML dient als
  Fallback.
- Die KONFORMEN Varianten dürfen NICHT abgestraft werden:
    * youtube-nocookie.com (datenschutzfreundlicher Embed)
    * self-hosted Fonts (kein Request an einen Drittanbieter)
  Die Muster sind so gewählt, dass diese Fälle nicht matchen; zusätzlich
  greifen explizite Negativ-Guards.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

# ---------------------------------------------------------------------------
# Registry: Drittanbieter-Ressourcen mit IP-Transfer in Drittländer ohne Consent
# ---------------------------------------------------------------------------
# Felder pro Eintrag:
#   key            stabiler Schlüssel
#   name           Anzeigename
#   provider       Anbieter inkl. Sitz (Drittland)
#   category       fonts | maps | captcha | video
#   transmits      welches personenbezogene Datum übertragen wird
#   severity       critical (klares Abmahn-Risiko)
#   risk_euro      konservativ geschätztes Risiko (Schadensersatz + Abmahnkosten)
#   match          Liste von Regex, die gegen Request-URLs UND HTML geprüft werden
#   exclude        Regex, die einen Treffer entwerten (konforme Varianten)
#   court_ref      einschlägige Rechtsprechung (falls vorhanden)
#   legal_basis    Rechtsgrundlage
#   recommendation Handlungsempfehlung
TRANSFER_SERVICES: List[Dict] = [
    {
        "key": "google_fonts",
        "name": "Google Fonts (extern geladen)",
        "provider": "Google LLC, USA",
        "category": "fonts",
        "transmits": "IP-Adresse",
        "severity": "critical",
        "risk_euro": 5000,
        "match": [
            r"fonts\.googleapis\.com",
            r"fonts\.gstatic\.com",
        ],
        "exclude": [],
        "court_ref": "LG München I, Urt. v. 20.01.2022, Az. 3 O 17493/20 (100 €/Nutzer)",
        "legal_basis": "DSGVO Art. 6 Abs. 1, Art. 44 ff. (Drittlandtransfer)",
        "recommendation": (
            "Google Fonts lokal (self-hosted) einbinden statt von Google-Servern. "
            "Schriften herunterladen (z. B. google-webfonts-helper) und vom eigenen "
            "Server ausliefern — dann findet kein Request an Google statt."
        ),
    },
    {
        "key": "google_recaptcha",
        "name": "Google reCAPTCHA",
        "provider": "Google LLC, USA",
        "category": "captcha",
        "transmits": "IP-Adresse + Interaktions-/Gerätedaten",
        "severity": "critical",
        "risk_euro": 5000,
        "match": [
            r"google\.com/recaptcha",
            r"recaptcha\.net",
            r"gstatic\.com/recaptcha",
        ],
        "exclude": [],
        "court_ref": None,
        "legal_basis": "DSGVO Art. 6 Abs. 1, Art. 44 ff. (Drittlandtransfer)",
        "recommendation": (
            "reCAPTCHA nur nach aktiver Einwilligung laden (Consent-Gate) oder durch "
            "eine datenschutzfreundliche Alternative ersetzen (z. B. Friendly Captcha, "
            "hCaptcha mit AV-Vertrag/EU-Hosting, Honeypot)."
        ),
    },
    {
        "key": "google_maps",
        "name": "Google Maps (extern eingebunden)",
        "provider": "Google LLC, USA",
        "category": "maps",
        "transmits": "IP-Adresse",
        "severity": "critical",
        "risk_euro": 4000,
        "match": [
            r"maps\.googleapis\.com",
            r"maps\.gstatic\.com",
            r"maps\.google\.com/maps",
            r"google\.com/maps/embed",
        ],
        "exclude": [],
        "court_ref": None,
        "legal_basis": "DSGVO Art. 6 Abs. 1, Art. 44 ff. (Drittlandtransfer)",
        "recommendation": (
            "Karte erst nach aktiver Einwilligung laden (2-Klick-/Consent-Lösung) "
            "oder eine EU-gehostete Alternative (z. B. OpenStreetMap) verwenden."
        ),
    },
    {
        "key": "youtube_embed",
        "name": "YouTube-Video (ohne erweiterten Datenschutzmodus)",
        "provider": "Google LLC, USA",
        "category": "video",
        "transmits": "IP-Adresse",
        "severity": "critical",
        "risk_euro": 4000,
        "match": [
            r"youtube\.com/embed",
            r"//youtube\.com",
            r"www\.youtube\.com",
            r"i\.ytimg\.com",
        ],
        # youtube-nocookie.com ist die KONFORME Variante → niemals abstrafen
        "exclude": [r"youtube-nocookie\.com"],
        "court_ref": None,
        "legal_basis": "DSGVO Art. 6 Abs. 1, Art. 44 ff. (Drittlandtransfer)",
        "recommendation": (
            "Erweiterten Datenschutzmodus nutzen (youtube-nocookie.com) UND das Video "
            "erst nach aktiver Einwilligung laden (2-Klick-Lösung)."
        ),
    },
    {
        "key": "adobe_typekit_fonts",
        "name": "Adobe Fonts / Typekit / Fonts.com (extern geladen)",
        "provider": "Adobe Inc. / Monotype, USA",
        "category": "fonts",
        "transmits": "IP-Adresse",
        "severity": "critical",
        "risk_euro": 5000,
        "match": [
            r"use\.typekit\.net",
            r"p\.typekit\.net",
            r"use\.fontawesome\.com",
            r"fast\.fonts\.net",
            r"\bfonts\.com\b",
        ],
        "exclude": [],
        "court_ref": None,
        "legal_basis": "DSGVO Art. 6 Abs. 1, Art. 44 ff. (Drittlandtransfer)",
        "recommendation": (
            "Webfonts lokal (self-hosted) einbinden, sofern die Lizenz dies erlaubt, "
            "oder den Dienst erst nach aktiver Einwilligung laden."
        ),
    },
]

# Vorkompilierte Muster für Performance/Korrektheit
for _svc in TRANSFER_SERVICES:
    _svc["_match_re"] = [re.compile(p, re.IGNORECASE) for p in _svc["match"]]
    _svc["_exclude_re"] = [re.compile(p, re.IGNORECASE) for p in _svc.get("exclude", [])]


# Trennt HTML/CSS an allen Zeichen, die URLs typischerweise begrenzen
# (Whitespace, Quotes, Klammern, spitze Klammern). Ergebnis: pro Verweis ein Token.
_URL_DELIMITERS = re.compile(r"""[\s"'()<>,;]+""")


def _tokenize_html(html: str) -> List[str]:
    """
    Zerlegt HTML/CSS in URL-artige Tokens. Erfasst auch CSS `@import url(...)`
    und `src:url(...)`, da die Klammern als Delimiter wirken.
    """
    return [t for t in _URL_DELIMITERS.split(html) if t]


def _matches(service: Dict, haystacks: List[str]) -> List[str]:
    """
    Liefert die Liste der Belege (gekürzte URLs/Snippets), die für diesen Dienst
    matchen. Negativ-Guards (konforme Varianten) entwerten den jeweiligen Beleg.
    """
    evidence: List[str] = []
    for hay in haystacks:
        if not hay:
            continue
        # konforme Variante? → diesen Beleg überspringen
        if any(ex.search(hay) for ex in service["_exclude_re"]):
            continue
        if any(m.search(hay) for m in service["_match_re"]):
            snippet = hay.strip()[:300]
            if snippet not in evidence:
                evidence.append(snippet)
    return evidence


def detect_transfers(
    *,
    html: str = "",
    request_urls: Optional[Iterable[str]] = None,
) -> List[Dict]:
    """
    Erkennt Drittlandtransfer-Dienste anhand echter Request-URLs (bevorzugt) und
    HTML (Fallback).

    Args:
        html:         roher HTML-Quelltext der Seite (Fallback-Erkennung)
        request_urls: tatsächlich beobachtete ausgehende Request-URLs aus dem
                      Headless-/Deep-Scan (zuverlässigste Quelle)

    Returns:
        Liste von Finding-Dicts (siehe `_build_finding`). Pro Dienst max. ein
        Finding; `evidence` enthält die belegenden URLs/Snippets, `source` zeigt
        ob der Beleg aus echten Requests ("request") und/oder HTML ("html") stammt.
    """
    req_list = [u for u in (request_urls or []) if u]
    # HTML in URL-Tokens zerlegen, damit jeder Verweis EINZELN bewertet wird.
    # Sonst könnte eine konforme Variante (z. B. youtube-nocookie.com irgendwo
    # auf der Seite) ein echtes, nicht-konformes Embed an anderer Stelle
    # fälschlich mit-unterdrücken (False Negative).
    html_haystacks = _tokenize_html(html) if html else []

    findings: List[Dict] = []
    for svc in TRANSFER_SERVICES:
        req_evidence = _matches(svc, req_list)
        html_evidence = _matches(svc, html_haystacks)
        if not req_evidence and not html_evidence:
            continue

        sources = []
        if req_evidence:
            sources.append("request")
        if html_evidence:
            sources.append("html")

        # Requests sind aussagekräftiger; davon zeigen wir bevorzugt Belege
        evidence = (req_evidence or html_evidence)[:5]
        findings.append(_build_finding(svc, evidence=evidence, sources=sources))

    return findings


def _build_finding(service: Dict, *, evidence: List[str], sources: List[str]) -> Dict:
    """Baut ein normalisiertes Finding-Dict aus einem Registry-Eintrag."""
    court = service.get("court_ref")
    description = (
        f"{service['name']} wird von externen Servern des Anbieters "
        f"({service['provider']}) geladen. Dabei wird die {service['transmits']} "
        f"des Website-Besuchers OHNE vorherige Einwilligung in ein Drittland (USA) "
        f"übertragen. Das ist ein abmahnfähiger Verstoß gegen die DSGVO."
    )
    if court:
        description += f" Einschlägige Rechtsprechung: {court}."

    return {
        "key": service["key"],
        "name": service["name"],
        "provider": service["provider"],
        "category": service["category"],
        "transmits": service["transmits"],
        "severity": service["severity"],
        "risk_euro": service["risk_euro"],
        "requires_consent": True,
        "is_third_country_transfer": True,
        "title": f"{service['name']} — Drittlandtransfer ohne Einwilligung",
        "description": description,
        "recommendation": service["recommendation"],
        "legal_basis": service["legal_basis"]
        + (f", {court}" if court else ""),
        "court_ref": court,
        "evidence": evidence,
        "source": "+".join(sources),
        "auto_fixable": False,
    }


def detected_service_keys(
    *, html: str = "", request_urls: Optional[Iterable[str]] = None
) -> List[str]:
    """Bequemer Helper: nur die Schlüssel der erkannten Transfer-Dienste."""
    return [f["key"] for f in detect_transfers(html=html, request_urls=request_urls)]
