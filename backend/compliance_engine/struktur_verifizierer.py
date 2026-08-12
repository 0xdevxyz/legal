"""
Struktur-Fixes, die sich im Browser selbst prüfen — wie beim Kontrast.

Dieselbe Zusage, dieselbe Mechanik: einspielen, nachmessen, und nur ausliefern,
was die Nachmessung bestanden hat. Bei Struktur ist sie noch wichtiger als bei
Farbe, weil ein `role="main"` an der falschen Stelle nicht auffällt — es sieht
aus wie vorher und behauptet trotzdem eine Struktur, die nicht stimmt. Die
Messung ist das Einzige, was den Unterschied zeigt.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional

from compliance_engine.axe_scanner import AXE_CORE_JS, axe_tags_fuer
from compliance_engine.formular_fixes import (
    FORMULARFELDER_JS, beschriftung_fuer_feld, titel_aus_seite,
)
from compliance_engine.struktur_fixes import (
    ALTERNATIVEN_JS, HAUPTINHALT_JS, STRUKTUR_ANWENDEN_JS, baue_struktur_css, baue_struktur_fixes,
)

logger = logging.getLogger(__name__)

# Die Regeln, um die es geht. Bewusst eng: alles andere braucht ein Urteil.
BETROFFENE_REGELN = [
    "region", "landmark-one-main", "meta-viewport", "frame-title",
    "scrollable-region-focusable", "link-in-text-block",
    # Formularseite: Beschriftungen, Seitentitel, ARIA-Elternrollen.
    "label", "select-name", "document-title",
]

SETZZEIT_MS = 300


async def _axe(page, regeln: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    if not await page.evaluate("typeof axe !== 'undefined'"):
        await page.add_script_tag(content=AXE_CORE_JS)
        await page.wait_for_function("typeof axe !== 'undefined'", timeout=8000)
    cfg = ({"runOnly": {"type": "rule", "values": regeln}} if regeln
           else {"runOnly": {"type": "tag", "values": axe_tags_fuer("wcag21aa")}})
    ergebnis = await page.evaluate(
        "async () => await axe.run(document, %s)" % json.dumps(cfg)
    )
    return {v["id"]: v["nodes"] for v in ergebnis.get("violations", [])}


async def verifizierte_struktur_fixes(page) -> Dict[str, Any]:
    """
    Bestimmt Struktur-Fixes an der geöffneten Seite und misst ihre Wirkung.

    Erwartet eine geladene Playwright-Seite; sie wird dabei verändert und
    sollte danach nicht mehr für andere Messungen dienen.

    Returns:
        {"fixes": [...], "css_rules": [...], "vorher": int, "nachher": int,
         "je_regel": {regel: (vorher, nachher)}, "haupt_selektor": str|None}
    """
    vorher = await _axe(page, BETROFFENE_REGELN)
    if not vorher:
        return {"fixes": [], "css_rules": [], "vorher": 0, "nachher": 0,
                "je_regel": {}, "haupt_selektor": None}

    # Die bemaengelten `region`-Knoten in den Browser reichen — aus ihnen
    # bestimmt HAUPTINHALT_JS den gemeinsamen Vorfahr.
    region_selektoren = [
        (n.get("target") or [None])[0] for n in vorher.get("region", [])
    ]
    region_selektoren = [s for s in region_selektoren if s]
    haupt_selektor = None
    haupt_alternativen: list = []
    if region_selektoren:
        await page.evaluate(
            "(sel) => { window.__complyoRegionKnoten = sel; }", region_selektoren
        )
        try:
            haupt_selektor = await page.evaluate(HAUPTINHALT_JS)
        except Exception as e:
            logger.warning(f"Hauptinhalt nicht bestimmbar: {e}")
        if haupt_selektor:
            # Seitenstabile Alternativen desselben Containers mitmessen —
            # der exakte Selektor traegt sonst die Post-ID der Startseite
            # und trifft auf Unterseiten nichts (Audit 11.08.).
            try:
                haupt_alternativen = await page.evaluate(ALTERNATIVEN_JS, haupt_selektor) or []
            except Exception as e:
                logger.warning(f"Selektor-Alternativen nicht bestimmbar: {e}")

    fixes = baue_struktur_fixes(vorher, haupt_selektor, haupt_alternativen)
    css_rules = baue_struktur_css(vorher)
    fixes.extend(await _formular_fixes(page, vorher))
    fixes.extend(await _titel_fix(page, vorher))

    if not fixes and not css_rules:
        anzahl = sum(len(v) for v in vorher.values())
        return {"fixes": [], "css_rules": [], "vorher": anzahl, "nachher": anzahl,
                "je_regel": {}, "haupt_selektor": None}

    if fixes:
        gesetzt = await page.evaluate(STRUKTUR_ANWENDEN_JS, fixes)
        logger.info(f"Struktur: {gesetzt} Attribut(e) gesetzt")
    if css_rules:
        await page.add_style_tag(content="\n".join(
            f"{r['selector']} {{ {r['declarations']} }}" for r in css_rules
        ))
    await page.wait_for_timeout(SETZZEIT_MS)

    nachher = await _axe(page, BETROFFENE_REGELN)

    je_regel = {
        regel: (len(vorher.get(regel, [])), len(nachher.get(regel, [])))
        for regel in set(vorher) | set(nachher)
    }
    v_gesamt = sum(len(v) for v in vorher.values())
    n_gesamt = sum(len(v) for v in nachher.values())

    # Nur ausliefern, was auch gewirkt hat. Ein `role="main"`, das die
    # region-Befunde nicht senkt, sass an der falschen Stelle — dann lieber
    # nichts setzen als etwas Falsches behaupten.
    region_vorher, region_nachher = je_regel.get("region", (0, 0))
    # Nicht nur "besser als nichts", sondern deutlich besser: raeumt das
    # gesetzte main weniger als die Haelfte der Befunde ab, sass es an einem
    # Abschnitt statt am Hauptinhalt. Dann lieber keins.
    genug = region_vorher > 0 and (region_vorher - region_nachher) * 2 >= region_vorher
    if haupt_selektor and region_vorher > 0 and not genug:
        logger.info(
            f"role=main auf {haupt_selektor} raeumt nur "
            f"{region_vorher - region_nachher} von {region_vorher} Befunden ab — "
            f"das ist ein Abschnitt, nicht der Hauptinhalt; wird nicht ausgeliefert"
        )
        fixes = [f for f in fixes if f["regel"] != "region"]
        haupt_selektor = None

    logger.info(f"Struktur verifiziert: {v_gesamt} -> {n_gesamt} Fundstellen")
    return {
        "fixes": fixes,
        "css_rules": css_rules,
        "vorher": v_gesamt,
        "nachher": n_gesamt,
        "je_regel": je_regel,
        "haupt_selektor": haupt_selektor,
    }


# =============================================================================
# Formularseite
# =============================================================================

async def _formular_fixes(page, befunde) -> List[Dict[str, Any]]:
    """Beschriftungen fuer Felder ohne Label — oder aria-hidden fuer Koeder."""
    knoten = befunde.get("label", []) + befunde.get("select-name", [])
    selektoren = [(n.get("target") or [None])[0] for n in knoten]
    selektoren = [s for s in selektoren if s]
    if not selektoren:
        return []

    await page.evaluate("(s) => { window.__complyoFeldSelektoren = s; }", selektoren)
    try:
        felder = await page.evaluate(FORMULARFELDER_JS)
    except Exception as e:
        logger.warning(f"Formularfelder nicht lesbar: {e}")
        return []

    fixes: List[Dict[str, Any]] = []
    for feld in felder:
        vorschlag = beschriftung_fuer_feld(feld["attribute"], feld["umgebungstext"])
        if not vorschlag:
            continue
        if vorschlag.get("honeypot"):
            # Ein Spam-Koeder braucht kein Label, sondern Unsichtbarkeit fuer
            # alle. Ihn zu beschriften waere formal richtig und praktisch
            # falsch: der Screenreader saegte ein Feld an, das niemand
            # ausfuellen darf.
            fixes.append({
                "selector": feld["selector"], "attribut": "aria-hidden",
                "wert": "true", "regel": "label",
                "begruendung": "Spam-Koeder — fuer alle unsichtbar statt beschriftet.",
            })
            continue
        fixes.append({
            "selector": feld["selector"], "attribut": "aria-label",
            "wert": vorschlag["label"], "regel": "label",
            "begruendung": f"Beschriftung abgeleitet aus: {vorschlag['quelle']}.",
        })
    return fixes



async def _titel_fix(page, befunde) -> List[Dict[str, Any]]:
    """Fehlender `<title>` — WCAG 2.4.2, der erste Text, den ein Screenreader ansagt."""
    if not befunde.get("document-title"):
        return []
    daten = await page.evaluate("""() => ({
        h1: (document.querySelector('h1') || {}).innerText || '',
        og: (document.querySelector('meta[property="og:title"]') || {}).content || '',
        host: location.hostname,
    })""")
    titel = titel_aus_seite(daten["h1"], daten["og"], daten["host"])
    if not titel:
        return []
    return [{
        "selector": "title", "attribut": "__text__", "wert": titel,
        "regel": "document-title",
        "begruendung": "Seite ohne Titel — abgeleitet aus der Hauptueberschrift.",
    }]
