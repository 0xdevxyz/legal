"""
Grundsystem (CMS) einer Website erkennen und den passenden Einrichtungsweg
dazu nennen.

Die Signaturen standen bisher nur in ComplianceScanner._detect_cms und
erreichten damit nur den Hauptscan. Der Cookie-Scan, mit dem die
Ersteinrichtung beginnt, wusste nichts davon und zeigte danach immer dieselben
drei Kacheln (WordPress, Webflow, HTML), egal was die Seite ist. Dabei liegen
fuer WordPress und Joomla fertige Plugins im Repo, die der Kunde nie zu sehen
bekam.

Eine Quelle fuer beide Scans: der Hauptscan ruft weiter
ComplianceScanner._detect_cms, das jetzt hierher delegiert.
"""

import re
from typing import Dict, Optional

# Reihenfolge ist Rangfolge: der erste Treffer gewinnt. "wordpress" steht vor
# "joomla", weil WordPress-Seiten mit einem Joomla-Migrationsrest sonst falsch
# landen; "drupal" nach "joomla", weil "/sites/default/files" auch in fremden
# Themes vorkommt.
SIGNATUREN = [
    ("WordPress",   ["wp-content", "wp-includes", "/wp-json", "wp-emoji", "wordpress"]),
    ("Shopify",     ["cdn.shopify.com", "shopify.theme", "x-shopify"]),
    ("Wix",         ["static.wixstatic.com", "wix.com", "_wix"]),
    ("Jimdo",       ["jimdo", "jimstatic.com"]),
    ("Typo3",       ["typo3", "/typo3conf/"]),
    ("Joomla",      ["/media/jui/", "joomla", "com_content"]),
    ("Drupal",      ["drupal-settings-json", "/sites/default/files", "drupal"]),
    ("Webflow",     ["webflow", "assets.website-files.com"]),
    ("Squarespace", ["squarespace", "static1.squarespace.com"]),
]

# Welcher Einrichtungsweg zu welchem Grundsystem gehoert. "plugin" heisst: es
# gibt ein fertiges Paket im Repo (backend/plugins), das der Kunde hochlaedt.
# Alles andere bekommt den Script-Schnipsel in den <head>.
PLUGIN_PAKETE: Dict[str, Dict[str, str]] = {
    "wordpress": {
        "datei": "complyo-compliance.zip",
        "anleitung": "WordPress-Backend: Plugins, Installieren, Plugin hochladen. "
                     "Danach aktivieren und unter Einstellungen, Complyo die Site-ID pruefen.",
    },
    "joomla": {
        "datei": "plg_system_complyo.zip",
        "anleitung": "Joomla-Backend: System, Installieren, Erweiterungen. "
                     "Danach unter Plugins das System-Plugin Complyo aktivieren und die Site-ID eintragen.",
    },
}

# Hinweis, wo der Schnipsel hingehoert, wenn es kein Plugin gibt.
SCHNIPSEL_HINWEISE: Dict[str, str] = {
    "shopify":     "Onlineshop, Themes, Code bearbeiten, theme.liquid: direkt nach <head> einfuegen.",
    "wix":         "Einstellungen, Benutzerdefinierter Code: als Head-Code auf allen Seiten einfuegen.",
    "jimdo":       "Einstellungen, Head bearbeiten: Schnipsel einfuegen.",
    "typo3":       "Im Seitentemplate (Fluid-Layout oder TypoScript page.headerData) einfuegen.",
    "drupal":      "Im Theme-Template html.html.twig im <head> einfuegen oder per Asset Injector.",
    "webflow":     "Site Settings, Custom Code, Head Code: Schnipsel einfuegen.",
    "squarespace": "Einstellungen, Erweitert, Code-Injektion, Header: Schnipsel einfuegen.",
    "html":        "In jeder HTML-Datei direkt vor </head> einfuegen, am besten im Template.",
}


def erkenne_grundsystem(html: str, headers: Optional[dict] = None) -> Optional[str]:
    """
    Gibt den Anzeigenamen des Grundsystems zurueck (z.B. "WordPress") oder None.
    Liest HTML-Signaturen, den Generator-Meta-Tag und HTTP-Header.
    """
    text = (html or "").lower()
    # Name und Wert: die Signatur "x-shopify" steckt im Header-Namen, nicht im Wert.
    kopf = {str(k).lower(): str(v).lower() for k, v in (headers or {}).items()}

    # Generator-Meta: Attributreihenfolge ist nicht festgelegt, deshalb erst
    # das Tag suchen, dann darin das content-Attribut.
    generator = ""
    for tag in re.finditer(r"<meta\b[^>]*>", text):
        t = tag.group(0)
        if re.search(r"""name\s*=\s*["']?generator""", t):
            c = re.search(r"""content\s*=\s*["']([^"']*)["']""", t)
            if c:
                generator = c.group(1).lower()
                break

    haystack = text + " " + generator + " " + " ".join(f"{k}: {v}" for k, v in kopf.items())
    for name, marker in SIGNATUREN:
        if any(s in haystack for s in marker):
            return name
    return None


def grundsystem_schluessel(name: Optional[str]) -> str:
    """"WordPress" -> "wordpress", None -> "html"."""
    return (name or "html").lower()


def einrichtungsweg(name: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Beschreibt, wie der Kunde complyo auf diesem Grundsystem einbindet.

    Rueckgabe:
      detected_cms:        Anzeigename oder None
      cms_key:             Kleinschreibung, "html" wenn nichts erkannt
      einrichtung:         "plugin" oder "snippet"
      plugin_download_pfad: Pfad unter der API, nur bei "plugin"
      anleitung:           ein Satz, wo das Paket bzw. der Schnipsel hingehoert
    """
    key = grundsystem_schluessel(name)
    paket = PLUGIN_PAKETE.get(key)
    if paket:
        return {
            "detected_cms": name,
            "cms_key": key,
            "einrichtung": "plugin",
            "plugin_download_pfad": f"/api/cookie-compliance/plugin/{key}",
            "anleitung": paket["anleitung"],
        }
    return {
        "detected_cms": name,
        "cms_key": key,
        "einrichtung": "snippet",
        "plugin_download_pfad": None,
        "anleitung": SCHNIPSEL_HINWEISE.get(key, SCHNIPSEL_HINWEISE["html"]),
    }
