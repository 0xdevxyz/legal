"""
Kontrast-Reparatur: aus gemessenen Farbpaaren wird eine kurze Entscheidungsliste.

Warum das der wichtigste Fix ist
--------------------------------
Auf 24 echten deutschen KMU-Websites (Messung 06.08.2026) ist `color-contrast`
der mit Abstand haeufigste **Pflicht**-Verstoss: 192 Fundstellen auf 18 von 24
Seiten, Schwere "serious". Alles andere zusammen kommt auf 97. Wer BFSG ernst
meint, muss Kontrast koennen — und niemand am Markt repariert ihn, alle zeigen
ihn nur an.

Der Trick liegt in der Gruppierung
----------------------------------
192 Fundstellen sind nicht 192 Entscheidungen. axe misst je Element, aber
dieselbe Farbkombination wiederholt sich: auf konditorei-limbach.de sind 11
Fundstellen in Wahrheit eine Handvoll Farbpaare. Gruppiert man nach
(Vordergrund, Hintergrund, geforderte Ratio), bleibt eine Liste, die ein
Mensch in zwei Minuten durchsieht — und eine Freigabe repariert dutzende
Stellen. Genau das ist der Unterschied zwischen einem Report und einer Loesung.

Warum nicht CSS parsen
----------------------
`contrast_analyzer.py` kann die Mathematik, arbeitet aber auf CSS-Text. Was
ein Element wirklich anzeigt, steht dort nicht: Kaskade, Spezifitaet, vererbte
Farben und JS-gesetzte Styles entscheiden mit. axe misst am gerenderten
Element — das ist die einzige Quelle, der man einen Fix anvertrauen kann.

Warum die Helligkeit und nicht der Farbton
------------------------------------------
Der Vorschlag behaelt Farbton und Saettigung und verschiebt nur die
Helligkeit, bis die geforderte Ratio erreicht ist — in der Richtung, die
weniger Aenderung kostet. Das Ergebnis bleibt erkennbar dieselbe Farbe; ein
Kunde, der seine Markenfarbe verteidigt, sieht einen Nachbarton, keinen
Fremdkoerper. Und die Freigabe bleibt beim Menschen: Farbe ist Gestaltung.
"""
import colorsys
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Feinheit der Helligkeitssuche. 0.002 entspricht rund 0,2 % Helligkeit —
# feiner als das Auge unterscheidet, grob genug fuer eine schnelle Suche.
_SCHRITT = 0.002


def _hex_zu_rgb(farbe: str) -> Optional[Tuple[int, int, int]]:
    """`#a86100`, `#abc` oder `rgb(168, 97, 0)` -> (168, 97, 0)."""
    if not farbe:
        return None
    farbe = farbe.strip()

    m = re.match(r"^#?([0-9a-f]{3}|[0-9a-f]{6})$", farbe, re.I)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    m = re.match(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", farbe, re.I)
    if m:
        return tuple(min(255, int(m.group(i))) for i in (1, 2, 3))
    return None


def _rgb_zu_hex(rgb: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _leuchtdichte(rgb: Tuple[int, int, int]) -> float:
    """Relative Leuchtdichte nach WCAG 2.1."""
    def kanal(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (kanal(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    """Kontrastverhaeltnis zweier Farben, 1.0 bis 21.0."""
    la, lb = _leuchtdichte(a), _leuchtdichte(b)
    hell, dunkel = max(la, lb), min(la, lb)
    return (hell + 0.05) / (dunkel + 0.05)


def geforderte_ratio(font_size: str = "", font_weight: str = "",
                     erwartet: str = "") -> float:
    """
    Welche Ratio verlangt WCAG hier — 4.5:1 oder 3:1 fuer grossen Text?

    axe liefert die Antwort in `expectedContrastRatio` bereits mit; sie wird
    bevorzugt, weil axe Schriftgroesse und -gewicht am gerenderten Element
    misst. Der Rest ist Rueckfallebene.
    """
    if erwartet:
        m = re.match(r"([\d.]+)", erwartet.strip())
        if m:
            return float(m.group(1))

    pt = 0.0
    m = re.search(r"([\d.]+)\s*pt", font_size or "")
    if m:
        pt = float(m.group(1))
    fett = str(font_weight).lower() in ("bold", "bolder", "600", "700", "800", "900")
    if pt >= 18 or (fett and pt >= 14):
        return 3.0
    return 4.5


def _mit_helligkeit(rgb: Tuple[int, int, int], neue_l: float) -> Tuple[int, int, int]:
    h, _l, s = colorsys.rgb_to_hls(*(c / 255.0 for c in rgb))
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, neue_l)), s)
    return (round(r * 255), round(g * 255), round(b * 255))


def finde_ersatzfarbe(
    vordergrund: Tuple[int, int, int],
    hintergrund: Tuple[int, int, int],
    ziel: float,
) -> Optional[Tuple[Tuple[int, int, int], float]]:
    """
    Naechstliegende Variante des Vordergrunds, die `ziel` erreicht.

    Farbton und Saettigung bleiben, nur die Helligkeit wandert — und zwar in
    beide Richtungen, wobei die mit dem kleineren Abstand gewinnt. Ein
    dunkelblaues Markenblau wird so dunkler statt willkuerlich schwarz.

    Returns:
        (rgb, erreichte_ratio) oder None, wenn selbst Schwarz und Weiss die
        Vorgabe nicht schaffen — dann muss der Hintergrund ran.
    """
    _h, l_start, _s = colorsys.rgb_to_hls(*(c / 255.0 for c in vordergrund))

    bester: Optional[Tuple[Tuple[int, int, int], float, float]] = None
    for richtung in (-1, +1):
        schritte = int(1.0 / _SCHRITT) + 1
        for i in range(1, schritte):
            l = l_start + richtung * i * _SCHRITT
            if not (0.0 <= l <= 1.0):
                break
            kandidat = _mit_helligkeit(vordergrund, l)
            ratio = kontrast(kandidat, hintergrund)
            if ratio >= ziel:
                abstand = abs(l - l_start)
                if bester is None or abstand < bester[2]:
                    bester = (kandidat, ratio, abstand)
                break

    return (bester[0], round(bester[1], 2)) if bester else None


def _sammle(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Zieht die Messwerte aus einem axe-Knoten der Regel `color-contrast`."""
    for pruefung in node.get("any", []) or []:
        daten = pruefung.get("data") or {}
        if daten.get("fgColor") and daten.get("bgColor"):
            return daten
    return None


def baue_kontrast_entscheidungen(
    nodes: List[Dict[str, Any]],
    max_gruppen: int = 25,
) -> List[Dict[str, Any]]:
    """
    Aus axe-Fundstellen wird eine Liste menschlicher Entscheidungen.

    Args:
        nodes: `violation["nodes"]` der Regel `color-contrast`.
        max_gruppen: Deckel, damit eine kaputte Seite die Worklist nicht flutet.

    Returns:
        Je Farbpaar ein Eintrag mit alter und vorgeschlagener Farbe, erreichter
        Ratio, Anzahl betroffener Stellen und Selektoren. Absteigend nach
        Wirkung sortiert — die Entscheidung, die am meisten repariert, steht oben.
    """
    gruppen: Dict[Tuple[str, str, float], Dict[str, Any]] = {}

    for node in nodes:
        daten = _sammle(node)
        if not daten:
            continue
        vg = _hex_zu_rgb(daten["fgColor"])
        hg = _hex_zu_rgb(daten["bgColor"])
        if not vg or not hg:
            continue
        ziel = geforderte_ratio(
            daten.get("fontSize", ""), daten.get("fontWeight", ""),
            daten.get("expectedContrastRatio", ""),
        )
        schluessel = (_rgb_zu_hex(vg), _rgb_zu_hex(hg), ziel)
        eintrag = gruppen.setdefault(schluessel, {
            "vordergrund": _rgb_zu_hex(vg),
            "hintergrund": _rgb_zu_hex(hg),
            "ziel_ratio": ziel,
            "ist_ratio": round(float(daten.get("contrastRatio") or kontrast(vg, hg)), 2),
            "stellen": 0,
            "selektoren": [],
            "beispiel_html": "",
        })
        eintrag["stellen"] += 1
        ziel_sel = node.get("target") or []
        if ziel_sel and len(eintrag["selektoren"]) < 50:
            eintrag["selektoren"].append(ziel_sel[0])
        if not eintrag["beispiel_html"]:
            eintrag["beispiel_html"] = (node.get("html") or "")[:200]

    entscheidungen = []
    for (vg_hex, hg_hex, ziel), eintrag in gruppen.items():
        vg, hg = _hex_zu_rgb(vg_hex), _hex_zu_rgb(hg_hex)
        ersatz = finde_ersatzfarbe(vg, hg, ziel)
        if ersatz:
            eintrag["vorschlag"] = _rgb_zu_hex(ersatz[0])
            eintrag["neue_ratio"] = ersatz[1]
            eintrag["loesbar"] = True
        else:
            # Kein Ton dieser Farbe schafft es. Ehrlich benennen statt einen
            # Vorschlag zu erfinden, der die Vorgabe verfehlt.
            eintrag["vorschlag"] = None
            eintrag["neue_ratio"] = None
            eintrag["loesbar"] = False
            eintrag["hinweis"] = (
                "Mit dieser Vordergrundfarbe nicht erreichbar — der Hintergrund "
                "müsste angepasst werden."
            )
        entscheidungen.append(eintrag)

    entscheidungen.sort(key=lambda e: (not e["loesbar"], -e["stellen"]))
    if len(entscheidungen) > max_gruppen:
        logger.info(
            f"Kontrast: {len(entscheidungen)} Farbpaare gefunden, "
            f"{max_gruppen} werden vorgelegt"
        )
    return entscheidungen[:max_gruppen]


def verschaerfe(entscheidung: Dict[str, Any], gemessene_ratio: float) -> bool:
    """
    Zweiter Anlauf, wenn die Messung hinter der Rechnung zurueckbleibt.

    Der Anlass ist real: auf naturheilzentrum-freitag.de meldet axe fuer einen
    Link `fgColor: #888888`, die berechnete Farbe des Elements ist aber
    `rgb(255,255,255)`. Aufgeloest: ueber dem Element liegt eine Deckkraft, und
    axe meldet die EFFEKTIVE Farbe nach der Mischung. Wer daraufhin `color`
    setzt, bekommt sie ebenfalls durchgemischt — aus `#6a6a6a` wurde gemessene
    `rgb(164,164,164)`, und der Verstoss blieb.

    Aus der Ferne ist das nicht auszurechnen: Deckkraft, Verlaufshintergruende
    und Hintergrundbilder liegen ausserhalb dessen, was axe an Daten liefert.
    Also wird nicht geraten, sondern nachgemessen und nachgelegt — die
    Zielvorgabe steigt um den gemessenen Fehlbetrag, mit Zuschlag.

    Args:
        entscheidung: Eintrag aus `baue_kontrast_entscheidungen`, wird veraendert.
        gemessene_ratio: was axe nach dem Einspielen tatsaechlich gemessen hat.

    Returns:
        True, wenn ein schaerferer Vorschlag gefunden wurde; False, wenn die
        Farbe ausgereizt ist (dann bleibt nur der Hintergrund).
    """
    ziel = entscheidung["ziel_ratio"]
    if gemessene_ratio <= 0:
        return False

    # Der Fehlbetrag zeigt, wie stark die Mischung daempft. 1.15 als Zuschlag,
    # damit die naechste Runde nicht wieder knapp scheitert.
    faktor = min(6.0, (ziel / gemessene_ratio) * 1.15)
    neues_ziel = min(21.0, entscheidung.get("internes_ziel", ziel) * faktor)
    if neues_ziel <= entscheidung.get("internes_ziel", ziel) + 0.01:
        return False

    vg = _hex_zu_rgb(entscheidung["vordergrund"])
    hg = _hex_zu_rgb(entscheidung["hintergrund"])
    ersatz = finde_ersatzfarbe(vg, hg, neues_ziel)
    if not ersatz:
        return False

    entscheidung["internes_ziel"] = neues_ziel
    entscheidung["vorschlag"] = _rgb_zu_hex(ersatz[0])
    entscheidung["neue_ratio"] = ersatz[1]
    entscheidung["loesbar"] = True
    entscheidung["runden"] = entscheidung.get("runden", 1) + 1
    return True


def als_css(entscheidungen: List[Dict[str, Any]]) -> str:
    """
    Die freigegebenen Entscheidungen als CSS.

    Selektoren kommen von axe und sind auf das gemessene Element gemuenzt.
    `!important` ist hier kein Pfusch, sondern noetig: der Fix wird nach dem
    Theme-CSS geladen und muss dessen Spezifitaet ueberstimmen, ohne dass
    jemand die Theme-Dateien anfasst.
    """
    zeilen = ["/* complyo — Kontrast nach WCAG 2.1 AA (1.4.3) */"]
    for e in entscheidungen:
        if not e.get("loesbar") or not e.get("vorschlag"):
            continue
        selektoren = sorted(set(e["selektoren"]))
        if not selektoren:
            continue
        zeilen.append(
            f"/* {e['vordergrund']} auf {e['hintergrund']}: "
            f"{e['ist_ratio']}:1 -> {e['neue_ratio']}:1 "
            f"({e['stellen']} Stelle(n)) */"
        )
        # Bewusst eine Regel je Selektor statt einer Gruppe: bei
        # kommagetrennten Selektoren verwirft der Browser die GANZE Regel,
        # sobald einer davon ungueltig ist. axe-Selektoren kommen aus fremden
        # Seiten — ein einziger Ausreisser duerfte nicht alle anderen Fixes
        # mitreissen. Die paar Kilobyte mehr sind der Preis dafuer.
        for selektor in selektoren:
            zeilen.append(f"{selektor} {{ color: {e['vorschlag']} !important; }}")
    return "\n".join(zeilen) + "\n"


def als_css_regeln(entscheidungen: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Dieselben Fixes im Format des Fix-Manifests: [{selector, declarations}].

    Der Auslieferungsweg existiert bereits — `a11y_remediation.js` baut aus
    `css_rules` ein `<style>` und haengt es an den Kopf, genau so, wie die
    Verifikation es im Browser nachgemessen hat. Deshalb hier kein neuer Kanal,
    nur das passende Format.

    Eine Regel je Selektor statt einer kommagetrennten Gruppe: ein einzelner
    ungueltiger Selektor aus fremdem Markup wuerde sonst die ganze Regel und
    damit alle uebrigen Fixes derselben Entscheidung mitreissen.
    """
    regeln: List[Dict[str, str]] = []
    for e in entscheidungen:
        if not e.get("bestaetigt", e.get("loesbar")) or not e.get("vorschlag"):
            continue
        for selektor in sorted(set(e.get("selektoren") or [])):
            regeln.append({
                "selector": selektor,
                "declarations": f"color: {e['vorschlag']} !important;",
            })
    return regeln
