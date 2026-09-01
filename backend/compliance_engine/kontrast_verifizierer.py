"""
Kontrast-Fixes, die sich selbst pruefen.

Der Unterschied zum Rest des Marktes steckt in diesem Modul. Ein Werkzeug, das
Kontrastfehler *anzeigt*, braucht nur zu messen. Eines, das sie *repariert*,
muss beweisen, dass die Reparatur haelt — und das geht bei Farbe nicht durch
Rechnen allein:

  - Deckkraft: axe meldet die effektive Farbe nach Mischung. Auf
    naturheilzentrum-freitag.de meldet axe `#888888` fuer einen Link, dessen
    berechnete Farbe `rgb(255,255,255)` ist. Eine gesetzte Farbe wird ebenso
    gemischt — der erste Vorschlag landete als `rgb(164,164,164)` statt
    `#6a6a6a` und verfehlte die Vorgabe.
  - Verlaeufe und Hintergrundbilder: axe schaetzt eine Ersatzfarbe.
  - Kaskade und Spezifitaet fremder Themes.

Deshalb wird hier nicht vorhergesagt, sondern nachgemessen: Vorschlag
einspielen, axe erneut laufen lassen, und was noch scheitert, bekommt eine
schaerfere Runde. Was am Ende ausgeliefert wird, hat die Pruefung im echten
Browser bestanden — nicht in einer Formel.

Das ist die Zusage, die sich kein Report-Werkzeug leisten kann: **Was complyo
als behoben ausweist, ist im Browser nachgemessen.**
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from compliance_engine.axe_scanner import AXE_CORE_JS, axe_tags_fuer
from compliance_engine.kontrast_fixes import (
    als_css, baue_kontrast_entscheidungen, verschaerfe,
)

logger = logging.getLogger(__name__)

MAX_RUNDEN = 4  # danach ist die Farbe ausgereizt, nicht die Geduld

# Wartezeit nach dem Einspielen, bevor gemessen wird.
#
# Nicht willkuerlich: viele Themes legen `transition: color` auf Links und
# Ueberschriften. Die eingespielte Farbe wandert dann ueber mehrere hundert
# Millisekunden dorthin, und axe misst mittendrin einen Zwischenwert. Gemessen
# auf naturheilzentrum-freitag.de: nach 0 ms und 120 ms meldet axe noch 17
# Verstoesse, ab 300 ms null. Mit 120 ms haette die Nachschaerfung auf einem
# Zwischenstand aufgesetzt und die Farben grundlos weiter abgedunkelt —
# schlimmer als kein Fix, weil es die Gestaltung ohne Not veraendert.
SETZZEIT_MS = 500


async def _axe_kontrast(page) -> List[Dict[str, Any]]:
    """Nur die Regel `color-contrast` — schneller als der volle Satz."""
    await page.evaluate("""() => {
        if (!window.__complyo_axe_geladen) { window.__complyo_axe_geladen = false; }
    }""")
    if not await page.evaluate("typeof axe !== 'undefined'"):
        await page.add_script_tag(content=AXE_CORE_JS)
        await page.wait_for_function("typeof axe !== 'undefined'", timeout=8000)

    cfg = {"runOnly": {"type": "rule", "values": ["color-contrast"]}}
    ergebnis = await page.evaluate(
        "async () => await axe.run(document, %s)" % json.dumps(cfg)
    )
    for v in ergebnis.get("violations", []):
        if v["id"] == "color-contrast":
            return v["nodes"]
    return []


def _gemessen_je_paar(nodes: List[Dict[str, Any]]) -> Dict[Tuple[str, str], float]:
    """Schlechteste gemessene Ratio je Farbpaar nach dem Einspielen."""
    schlechteste: Dict[Tuple[str, str], float] = {}
    for node in nodes:
        for pruefung in node.get("any", []) or []:
            d = pruefung.get("data") or {}
            fg, bg, ratio = d.get("fgColor"), d.get("bgColor"), d.get("contrastRatio")
            if fg and bg and ratio:
                schluessel = (fg.lower(), bg.lower())
                schlechteste[schluessel] = min(
                    schlechteste.get(schluessel, 99.0), float(ratio)
                )
    return schlechteste


async def verifizierte_kontrast_fixes(
    page,
    max_runden: int = MAX_RUNDEN,
) -> Dict[str, Any]:
    """
    Erzeugt Kontrast-Entscheidungen und misst nach, ob sie wirken.

    Erwartet eine bereits geladene Playwright-Seite. Die Seite wird dabei
    veraendert (Stylesheets werden eingespielt) — sie sollte danach nicht mehr
    fuer andere Messungen dienen.

    Returns:
        {
          "entscheidungen": [...],   # mit "bestaetigt": True/False je Eintrag
          "vorher": int, "nachher": int,
          "css": str,               # was ausgeliefert werden kann
          "runden": int,
        }
    """
    start_knoten = await _axe_kontrast(page)
    if not start_knoten:
        return {"entscheidungen": [], "vorher": 0, "nachher": 0, "css": "", "runden": 0}

    entscheidungen = baue_kontrast_entscheidungen(start_knoten)
    vorher = len(start_knoten)
    stil_handle = None
    runde = 0

    for runde in range(1, max_runden + 1):
        css = als_css(entscheidungen)
        if not css.strip().splitlines()[1:]:
            break  # nichts Loesbares uebrig

        # Alten Fix entfernen, damit sich die Runden nicht stapeln und die
        # letzte Messung wirklich den aktuellen Vorschlag zeigt.
        if stil_handle is not None:
            await page.evaluate("(el) => el.remove()", stil_handle)
        stil_handle = await page.add_style_tag(content=css)
        await page.wait_for_timeout(SETZZEIT_MS)

        rest = await _axe_kontrast(page)
        if not rest:
            break

        gemessen = _gemessen_je_paar(rest)
        etwas_verschaerft = False
        for e in entscheidungen:
            if not e.get("loesbar"):
                continue
            # Nach dem Einspielen meldet axe die NEUE effektive Farbe. Der
            # Abgleich laeuft deshalb ueber den Hintergrund plus den aktuellen
            # Vorschlag, nicht ueber die Ursprungsfarbe.
            schluessel = ((e.get("vorschlag") or "").lower(), e["hintergrund"].lower())
            ratio = gemessen.get(schluessel)
            if ratio is None:
                continue  # dieses Paar taucht nicht mehr auf -> behoben
            if verschaerfe(e, ratio):
                etwas_verschaerft = True

        if not etwas_verschaerft:
            break

    await page.wait_for_timeout(SETZZEIT_MS)
    rest = await _axe_kontrast(page)
    offene = _gemessen_je_paar(rest)
    for e in entscheidungen:
        schluessel = ((e.get("vorschlag") or "").lower(), e["hintergrund"].lower())
        e["bestaetigt"] = bool(e.get("loesbar")) and schluessel not in offene

    logger.info(
        f"Kontrast verifiziert: {vorher} -> {len(rest)} Fundstellen in {runde} Runde(n), "
        f"{sum(1 for e in entscheidungen if e['bestaetigt'])} von "
        f"{len(entscheidungen)} Entscheidungen im Browser bestaetigt"
    )
    return {
        "entscheidungen": entscheidungen,
        "vorher": vorher,
        "nachher": len(rest),
        "css": als_css([e for e in entscheidungen if e.get("bestaetigt")]),
        "runden": runde,
    }


async def kontrast_fixes_fuer_url(url: str, timeout: int = 45000) -> Optional[Dict[str, Any]]:
    """Bequemer Einstieg: oeffnet die Seite selbst und liefert verifizierte Fixes."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright fehlt — Kontrast-Fixes uebersprungen")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            try:
                await page.wait_for_load_state("networkidle", timeout=6000)
                from .axe_scanner import warte_auf_ruhige_darstellung
                await warte_auf_ruhige_darstellung(page)
            except Exception:
                pass
            return await verifizierte_kontrast_fixes(page)
        except Exception as e:
            logger.warning(f"Kontrast-Fixes fuer {url} fehlgeschlagen: {e}")
            return None
        finally:
            await browser.close()
