"""
Markenfarben der Kundenwebsite als Startwerte fuer das Cookie-Banner.

Die Extraktion (WebsiteCrawler.extract_brand_colors) gab es schon, aber nur
hinter einem Knopf im Banner-Designer. Beim ersten Cookie-Scan laeuft sie
jetzt mit, und eine neue Konfiguration startet mit den Farben der Website
statt mit dem Standard-Violett.

Was dieses Modul dazutut: die Lesbarkeitspruefung. Der Banner setzt weisse
Schrift auf die Primaerfarbe (Knoepfe), vgl. AccessibilityScore.tsx. Eine
helle Markenfarbe (Cyan, Gelb, Hellgruen) wuerde ungeprueft einen Banner
erzeugen, der die eigene Kontrastregel reisst. Deshalb wird eine zu helle
Primaer- oder Akzentfarbe im selben Farbton abgedunkelt, bis 4,5:1 gegen
Weiss erreicht sind, und die Anpassung wird ausgewiesen.
"""

import colorsys
from typing import Any, Dict, List, Optional

MINDESTKONTRAST = 4.5
STANDARD = {
    "primary_color": "#7c3aed",
    "accent_color": "#8b5cf6",
    "text_color": "#333333",
    "bg_color": "#ffffff",
}


def _hex_zu_rgb(farbe: str):
    h = (farbe or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"keine Hex-Farbe: {farbe!r}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_zu_hex(r: int, g: int, b: int) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(round(r)))),
        max(0, min(255, int(round(g)))),
        max(0, min(255, int(round(b)))),
    )


def relative_leuchtdichte(farbe: str) -> float:
    """WCAG 2.x, dieselbe Formel wie getLuminance im Dashboard."""
    def kanal(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = _hex_zu_rgb(farbe)
    return 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b)


def kontrast(farbe_a: str, farbe_b: str) -> float:
    l1 = relative_leuchtdichte(farbe_a)
    l2 = relative_leuchtdichte(farbe_b)
    hell, dunkel = max(l1, l2), min(l1, l2)
    return (hell + 0.05) / (dunkel + 0.05)


def abdunkeln_bis_lesbar(farbe: str, gegen: str = "#ffffff", ziel: float = MINDESTKONTRAST) -> str:
    """
    Senkt die Helligkeit im selben Farbton, bis der Kontrast gegen `gegen`
    mindestens `ziel` erreicht. Erfuellt die Farbe das schon, kommt sie
    unveraendert zurueck. Ergebnis ist eine dunklere Stufe der Markenfarbe,
    nicht eine fremde Farbe.
    """
    if kontrast(farbe, gegen) >= ziel:
        return farbe.lower()
    r, g, b = _hex_zu_rgb(farbe)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    for _ in range(60):
        l *= 0.93
        rr, gg, bb = colorsys.hls_to_rgb(h, l, s)
        kandidat = _rgb_zu_hex(rr * 255, gg * 255, bb * 255)
        if kontrast(kandidat, gegen) >= ziel:
            return kandidat
    return "#1f2937"


def farbvorschlag(brand_colors: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Macht aus dem Extraktionsergebnis einen pruefbaren Vorschlag.

    Rueckgabe:
      farben:    primary_color, accent_color, text_color, bg_color
      quelle:    "website" wenn die Seite eigene Farben hatte, sonst "standard"
      angepasst: Liste von {feld, von, zu, grund} fuer jede Abdunklung
    """
    if not brand_colors or not brand_colors.get("scraped"):
        return {"farben": dict(STANDARD), "quelle": "standard", "angepasst": []}

    farben = {}
    angepasst: List[Dict[str, str]] = []
    for feld in ("primary_color", "accent_color", "text_color", "bg_color"):
        wert = str(brand_colors.get(feld) or STANDARD[feld]).lower()
        try:
            _hex_zu_rgb(wert)
        except ValueError:
            wert = STANDARD[feld]
        farben[feld] = wert

    # Knoepfe: weisse Schrift auf Primaer- und Akzentfarbe.
    for feld in ("primary_color", "accent_color"):
        vorher = farben[feld]
        nachher = abdunkeln_bis_lesbar(vorher, "#ffffff")
        if nachher != vorher:
            farben[feld] = nachher
            angepasst.append({
                "feld": feld,
                "von": vorher,
                "zu": nachher,
                "grund": f"Kontrast zu weisser Schrift war {kontrast(vorher, '#ffffff'):.2f}:1, "
                         f"Mindestwert {MINDESTKONTRAST}:1",
            })

    # Fliesstext auf Bannerhintergrund.
    if kontrast(farben["text_color"], farben["bg_color"]) < MINDESTKONTRAST:
        vorher = farben["text_color"]
        farben["text_color"] = abdunkeln_bis_lesbar(vorher, farben["bg_color"])
        if farben["text_color"] != vorher:
            angepasst.append({
                "feld": "text_color", "von": vorher, "zu": farben["text_color"],
                "grund": f"Kontrast zum Bannerhintergrund war {kontrast(vorher, farben['bg_color']):.2f}:1",
            })

    return {"farben": farben, "quelle": "website", "angepasst": angepasst}
