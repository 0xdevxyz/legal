"""
Drittländer-SSOT — sichere vs. unsichere Drittländer + Verarbeitungsländer pro Anbieter.

Logik wie Real Cookie Banner:
- EU/EWR-Mitgliedstaaten           → sicher (kein Drittland)
- Länder mit EU-Angemessenheits-
  beschluss (Art. 45 DSGVO)        → sicher
- alle übrigen Länder              → UNSICHERES Drittland → es ist eine
  Spezial-Einwilligung nach Art. 49 Abs. 1 lit. a DSGVO einzuholen, sofern für
  die Datenverarbeitung keine geeigneten Garantien (Art. 46) bestehen.

Dieses Modul ist die Single Source of Truth dafür, welche Länder als sicher
gelten und in welchen Ländern die bekannten Drittanbieter Daten verarbeiten.
`privacy_transfer_findings` und das Cookie-Banner-Widget greifen darauf zu, um
pro Service auszuweisen, ob eine besondere Einwilligung erforderlich ist.

Quelle der Anbieter-Länderlisten: öffentliche Service-Vorlagen (u. a. Real
Cookie Banner), Datenschutzerklärungen der Anbieter. Bewusst konservativ — im
Zweifel "unsicher".
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

# ---------------------------------------------------------------------------
# Sichere Länder
# ---------------------------------------------------------------------------
# EU + EWR (Island, Liechtenstein, Norwegen). Innerhalb dieser Länder ist kein
# Drittlandtransfer gegeben.
EU_EEA: frozenset[str] = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",                      # 27 EU
    "IS", "LI", "NO",                      # EWR
})

# Länder mit EU-Angemessenheitsbeschluss (Art. 45 DSGVO). Stand 2026.
# USA gilt seit dem EU-US Data Privacy Framework (10.07.2023) als sicher —
# ABER nur für Unternehmen, die unter dem DPF zertifiziert sind. Wir führen US
# konservativ NICHT pauschal als sicher (siehe US_IS_SAFE).
ADEQUACY: frozenset[str] = frozenset({
    "AD",  # Andorra
    "AR",  # Argentinien
    "CA",  # Kanada (nur kommerzielle Organisationen unter PIPEDA)
    "FO",  # Färöer
    "GG",  # Guernsey
    "IL",  # Israel
    "IM",  # Isle of Man
    "JP",  # Japan
    "JE",  # Jersey
    "NZ",  # Neuseeland
    "KR",  # Südkorea
    "CH",  # Schweiz
    "GB",  # Vereinigtes Königreich
    "UY",  # Uruguay
})

# Politische/juristische Stellschraube: Soll USA pauschal als sicher gelten?
# Default False — die meisten Tracking-Anbieter sind NICHT DPF-zertifiziert für
# alle relevanten Verarbeitungen, und die Rechtslage ist angreifbar (vgl.
# anhängige Klagen gegen das DPF). So bleibt die Abmahn-Sicht konservativ.
US_IS_SAFE: bool = False

SAFE_COUNTRIES: frozenset[str] = EU_EEA | ADEQUACY | ({"US"} if US_IS_SAFE else frozenset())


# ---------------------------------------------------------------------------
# Deutsche Länder-Namen (für die Anzeige im Banner / in Findings)
# ---------------------------------------------------------------------------
COUNTRY_NAMES_DE: Dict[str, str] = {
    # EU / EWR
    "AT": "Österreich", "BE": "Belgien", "BG": "Bulgarien", "HR": "Kroatien",
    "CY": "Zypern", "CZ": "Tschechien", "DK": "Dänemark", "EE": "Estland",
    "FI": "Finnland", "FR": "Frankreich", "DE": "Deutschland", "GR": "Griechenland",
    "HU": "Ungarn", "IE": "Irland", "IT": "Italien", "LV": "Lettland",
    "LT": "Litauen", "LU": "Luxemburg", "MT": "Malta", "NL": "Niederlande",
    "PL": "Polen", "PT": "Portugal", "RO": "Rumänien", "SK": "Slowakei",
    "SI": "Slowenien", "ES": "Spanien", "SE": "Schweden",
    "IS": "Island", "LI": "Liechtenstein", "NO": "Norwegen",
    # Angemessenheit
    "AD": "Andorra", "AR": "Argentinien", "CA": "Kanada", "FO": "Färöer",
    "GG": "Guernsey", "IL": "Israel", "IM": "Isle of Man", "JP": "Japan",
    "JE": "Jersey", "NZ": "Neuseeland", "KR": "Südkorea", "CH": "Schweiz",
    "GB": "Vereinigtes Königreich", "UY": "Uruguay",
    # Unsichere Drittländer (Anbieter-Listen)
    "US": "Vereinigte Staaten", "AF": "Afghanistan", "AL": "Albanien",
    "DZ": "Algerien", "AO": "Angola", "AM": "Armenien", "AU": "Australien",
    "AZ": "Aserbaidschan", "BH": "Bahrain", "BD": "Bangladesch", "BB": "Barbados",
    "BY": "Belarus", "BJ": "Benin", "BM": "Bermuda", "BT": "Bhutan",
    "BO": "Bolivien", "BA": "Bosnien und Herzegowina", "BR": "Brasilien",
    "VG": "Jungferninseln, Britisch", "BN": "Brunei Darussalam", "BF": "Burkina Faso",
    "KH": "Kambodscha", "CM": "Kamerun", "KY": "Kaimaninseln", "CL": "Chile",
    "CN": "China", "CO": "Kolumbien", "CR": "Costa Rica", "CU": "Kuba",
    "CI": "Republik Côte d'Ivoire", "CD": "Kongo, Demokratische Republik",
    "DO": "Dominikanische Republik", "EC": "Ecuador", "EG": "Ägypten",
    "ET": "Äthiopien", "FJ": "Fidschi", "GA": "Gabun", "GE": "Georgien",
    "GH": "Ghana", "GT": "Guatemala", "HN": "Honduras", "IN": "Indien",
    "ID": "Indonesien", "IQ": "Irak", "JM": "Jamaika", "JO": "Jordanien",
    "KZ": "Kasachstan", "KE": "Kenia", "KW": "Kuwait", "KG": "Kirgisistan",
    "LB": "Libanon", "MG": "Madagaskar", "MY": "Malaysia", "MV": "Malediven",
    "ML": "Mali", "MU": "Mauritius", "MX": "Mexiko", "MD": "Moldawien",
    "MN": "Mongolei", "ME": "Montenegro", "MA": "Marokko", "MZ": "Mosambik",
    "MM": "Myanmar", "NA": "Namibia", "NP": "Nepal", "NI": "Nicaragua",
    "NE": "Niger", "NG": "Nigeria", "MK": "Mazedonien", "OM": "Oman",
    "PK": "Pakistan", "PS": "Palästinensisches Gebiet, besetzt", "PA": "Panama",
    "PE": "Peru", "PH": "Philippinen", "QA": "Katar", "RU": "Russische Föderation",
    "RW": "Ruanda", "KN": "St. Kitts und Nevis", "VC": "St. Vincent und Grenadinen",
    "WS": "Samoa", "SA": "Saudi-Arabien", "SN": "Senegal", "RS": "Serbien",
    "SG": "Singapur", "SB": "Salomonen", "SO": "Somalia", "ZA": "Südafrika",
    "LK": "Sri Lanka", "SD": "Sudan", "SY": "Syrische Arabische Republik",
    "ST": "São Tomé und Príncipe", "TW": "Taiwan", "TZ": "Tansania",
    "TH": "Thailand", "GM": "Gambia", "TG": "Togo", "TN": "Tunesien",
    "TR": "Türkei", "TC": "Turks- und Caicosinseln", "UG": "Uganda",
    "UA": "Ukraine", "AE": "Vereinigte Arabische Emirate", "UZ": "Usbekistan",
    "VU": "Vanuatu", "VE": "Venezuela", "VN": "Vietnam", "ZM": "Sambia",
    "ZW": "Simbabwe",
}


# ---------------------------------------------------------------------------
# Verarbeitungsländer pro Anbieter-Unternehmen
# ---------------------------------------------------------------------------
# Die "globale" Automattic-Liste (Gravatar, WordPress Emojis, Jetpack, …) — exakt
# wie in den verbreiteten Service-Vorlagen (Real Cookie Banner) ausgewiesen.
_AUTOMATTIC_GLOBAL: List[str] = [
    "US", "AF", "AL", "DZ", "AO", "AM", "AU", "AZ", "BH", "BD", "BB", "BY",
    "BJ", "BM", "BT", "BO", "BA", "BR", "VG", "BN", "BF", "KH", "CM", "KY",
    "CL", "CN", "CO", "CR", "CU", "CI", "CD", "DO", "EC", "EG", "ET", "FJ",
    "GA", "GE", "GH", "GT", "HN", "IN", "ID", "IQ", "JM", "JO", "KZ", "KE",
    "KW", "KG", "LB", "MG", "MY", "MV", "ML", "MU", "MX", "MD", "MN", "ME",
    "MA", "MZ", "MM", "NA", "NP", "NI", "NE", "NG", "MK", "OM", "PK", "PS",
    "PA", "PE", "PH", "QA", "RU", "RW", "KN", "VC", "WS", "SA", "SN", "RS",
    "SG", "SB", "SO", "ZA", "LK", "SD", "SY", "ST", "TW", "TZ", "TH", "GM",
    "TG", "TN", "TR", "TC", "UG", "UA", "AE", "UZ", "VU", "VE", "VN", "ZM",
    "ZW",
]

# Anbieter-Unternehmen → Liste der Verarbeitungsländer (ISO-3166 alpha-2).
PROVIDER_COUNTRIES: Dict[str, List[str]] = {
    "google":     ["US"],
    "meta":       ["US"],
    "microsoft":  ["US"],
    "adobe":      ["US"],
    "monotype":   ["US"],
    "hotjar":     ["MT", "IE", "US"],   # Hotjar Ltd (Malta), Sub-Prozessoren in USA
    "linkedin":   ["US"],
    "tiktok":     ["US", "SG", "CN"],   # ByteDance — u. a. Singapur, USA, China
    "snapchat":   ["US"],
    "hubspot":    ["US"],
    "intercom":   ["US"],
    "segment":    ["US"],
    "amplitude":  ["US"],
    "mixpanel":   ["US"],
    "logrocket":  ["US"],
    "fullstory":  ["US"],
    "vimeo":      ["US"],
    "crisp":      ["FR"],               # Crisp — EU-gehostet (Frankreich)
    "drift":      ["US"],
    "automattic": _AUTOMATTIC_GLOBAL,
}

# Anbieter-Namen (Freitext aus DB/Scan) → Unternehmens-Schlüssel. Wird genutzt,
# wenn der service_key unbekannt ist; Matching per Teilstring (case-insensitive).
PROVIDER_ALIASES: Dict[str, str] = {
    "google": "google", "youtube": "google", "doubleclick": "google",
    "meta": "meta", "facebook": "meta", "instagram": "meta", "whatsapp": "meta",
    "microsoft": "microsoft", "bing": "microsoft", "clarity": "microsoft", "linkedin": "linkedin",
    "adobe": "adobe", "typekit": "adobe", "monotype": "monotype", "fonts.com": "monotype",
    "hotjar": "hotjar", "tiktok": "tiktok", "bytedance": "tiktok", "snap": "snapchat",
    "hubspot": "hubspot", "intercom": "intercom", "segment": "segment",
    "amplitude": "amplitude", "mixpanel": "mixpanel", "logrocket": "logrocket",
    "fullstory": "fullstory", "vimeo": "vimeo", "crisp": "crisp", "drift": "drift",
    "automattic": "automattic", "gravatar": "automattic", "jetpack": "automattic",
    "wordpress.com": "automattic", "wordpress.org": "automattic", "wp.com": "automattic",
}

# Bekannte Drittanbieter-Dienst-Schlüssel (aus privacy_transfer_findings /
# automated_cookie_scanner) → Anbieter-Unternehmen in PROVIDER_COUNTRIES.
SERVICE_PROVIDER: Dict[str, str] = {
    # privacy_transfer_findings Keys
    "google_fonts":        "google",
    "google_recaptcha":    "google",
    "google_maps":         "google",
    "youtube_embed":       "google",
    "adobe_typekit_fonts": "adobe",
    # WordPress-Standard-Dienste (RCB-typische Drittland-Kandidaten)
    "wordpress_emojis":    "automattic",
    "gravatar":            "automattic",
    "jetpack":             "automattic",
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def is_safe_country(code: str) -> bool:
    """True, wenn das Land kein unsicheres Drittland ist (EU/EWR oder Angemessenheit)."""
    return code.upper() in SAFE_COUNTRIES


def country_name(code: str) -> str:
    """Deutscher Anzeigename; fällt auf den Code zurück, wenn unbekannt."""
    return COUNTRY_NAMES_DE.get(code.upper(), code.upper())


def split_countries(codes: Iterable[str]) -> Dict[str, List[str]]:
    """Teilt eine Länderliste in sichere und unsichere Drittländer (Codes)."""
    safe, unsafe = [], []
    for raw in codes:
        c = raw.upper()
        (safe if c in SAFE_COUNTRIES else unsafe).append(c)
    return {"safe": safe, "unsafe": unsafe}


def resolve_company(*, service_key: str = "", provider: str = "") -> str:
    """
    Ermittelt den Unternehmens-Schlüssel aus service_key (bevorzugt) oder dem
    Freitext-Anbieternamen. Leerer String, wenn nichts passt.
    """
    if service_key and service_key in SERVICE_PROVIDER:
        return SERVICE_PROVIDER[service_key]
    p = (provider or "").lower()
    if not p:
        return ""
    # exakter Unternehmens-Token zuerst, dann Aliase (jeweils Teilstring-Match)
    for company in PROVIDER_COUNTRIES:
        if company in p:
            return company
    for alias, company in PROVIDER_ALIASES.items():
        if alias in p:
            return company
    return ""


def countries_for(
    *, service_key: str = "", provider_company: str = "", provider: str = ""
) -> List[str]:
    """
    Verarbeitungsländer für einen Dienst-Schlüssel, ein Anbieter-Unternehmen
    ODER einen Freitext-Anbieternamen. Leere Liste, wenn nichts hinterlegt ist.
    """
    company = (
        provider_company.lower()
        or resolve_company(service_key=service_key, provider=provider)
    )
    return list(PROVIDER_COUNTRIES.get(company, []))


def third_country_breakdown(service_names: Iterable[str]) -> List[Dict]:
    """
    Für eine Liste von Service-Anzeigenamen (z. B. ["Google Analytics 4",
    "Hotjar", "Crisp"]) die Teilmenge, die in unsicheren Drittländern verarbeitet:

        [{"name": "Google Analytics 4", "unsafe_country_names": ["Vereinigte Staaten"]}, ...]

    Auflösung über den Anbieternamen (Teilstring-Match gegen PROVIDER_ALIASES).
    Dedupliziert nach Name. Genutzt vom Datenschutzerklärungs-Generator, um den
    Art.-49-Abschnitt deterministisch zu erzeugen.
    """
    seen: set[str] = set()
    out: List[Dict] = []
    for name in service_names:
        if not name or name in seen:
            continue
        seen.add(name)
        info = country_processing_info(provider=name)
        if info and info["requires_special_consent"]:
            out.append({
                "name": name,
                "unsafe_country_names": info["unsafe_country_names"],
            })
    return out


def country_processing_info(
    *, service_key: str = "", provider_company: str = "", provider: str = ""
) -> Optional[Dict]:
    """
    Liefert die aufbereitete Drittland-Information für einen Dienst:

        {
          "countries":            ["US", ...],                # alle Verarbeitungsländer
          "countries_named":      [{"code","name","safe"}],   # für die Anzeige
          "unsafe_countries":     ["US", ...],                # nur unsichere Drittländer
          "unsafe_country_names": ["Vereinigte Staaten", ...],
          "requires_special_consent": True,                   # Art. 49 Abs. 1 lit. a
          "legal_basis": "DSGVO Art. 49 Abs. 1 lit. a",
        }

    None, wenn für den Dienst/Anbieter keine Länder hinterlegt sind.
    """
    codes = countries_for(
        service_key=service_key, provider_company=provider_company, provider=provider
    )
    if not codes:
        return None

    split = split_countries(codes)
    unsafe = split["unsafe"]
    return {
        "countries": codes,
        "countries_named": [
            {"code": c, "name": country_name(c), "safe": c in SAFE_COUNTRIES}
            for c in codes
        ],
        "unsafe_countries": unsafe,
        "unsafe_country_names": [country_name(c) for c in unsafe],
        "requires_special_consent": bool(unsafe),
        "legal_basis": "DSGVO Art. 49 Abs. 1 lit. a",
    }
