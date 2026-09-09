#!/usr/bin/env python3
"""
Alt gegen neu: raeumt die Struktur-Reparatur mit weiteren Landmarken mehr ab?

Misst je Seite zweimal auf frisch geladenen Instanzen — einmal nur mit dem
einen role="main" (bisheriger Weg), einmal zusaetzlich mit benannten
Geschwister-Landmarken. Das complyo-Widget wird dabei blockiert, sonst misst
der Lauf die eigene Laufzeit-Reparatur mit.
"""
import argparse, asyncio, json, os, re, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from compliance_engine.struktur_verifizierer import _axe, BETROFFENE_REGELN
from compliance_engine.struktur_fixes import (
    ALTERNATIVEN_JS, GESCHWISTER_LANDMARKS_JS, HAUPTINHALT_JS, STRUKTUR_ANWENDEN_JS,
    baue_geschwister_landmarks, baue_struktur_fixes,
)

WIDGET = re.compile(r"https?://api\.complyo\.(de|tech)/")


async def _seite(browser, url):
    pg = await browser.new_page()
    await pg.route(WIDGET, lambda route: asyncio.ensure_future(route.abort()))
    await pg.goto(url, wait_until="domcontentloaded", timeout=45000)
    try:
        await pg.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    return pg


async def _lauf(browser, url, mit_geschwistern):
    pg = await _seite(browser, url)
    try:
        vorher = await _axe(pg, BETROFFENE_REGELN)
        sel = [(n.get("target") or [None])[0] for n in vorher.get("region", [])]
        sel = [s for s in sel if s]
        haupt, alternativen = None, []
        if sel:
            await pg.evaluate("(s) => { window.__complyoRegionKnoten = s; }", sel)
            haupt = await pg.evaluate(HAUPTINHALT_JS)
            if haupt:
                alternativen = await pg.evaluate(ALTERNATIVEN_JS, haupt) or []
        fixes = baue_struktur_fixes(vorher, haupt, alternativen)
        weitere = []
        if mit_geschwistern and sel:
            weitere = baue_geschwister_landmarks(
                await pg.evaluate(GESCHWISTER_LANDMARKS_JS, haupt))
            fixes = fixes + weitere
        gesetzt = await pg.evaluate(STRUKTUR_ANWENDEN_JS, fixes) if fixes else 0
        await pg.wait_for_timeout(300)
        nachher = await _axe(pg, BETROFFENE_REGELN)
        return {
            "haupt": haupt,
            "weitere": len(weitere) // 2,
            "namen": [f["wert"] for f in weitere if f["attribut"] == "aria-label"],
            "gesetzt": gesetzt,
            "region_vorher": len(vorher.get("region", [])),
            "region_nachher": len(nachher.get("region", [])),
            "gesamt_vorher": sum(len(v) for v in vorher.values()),
            "gesamt_nachher": sum(len(v) for v in nachher.values()),
        }
    finally:
        await pg.close()


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    args = ap.parse_args()
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        summe = {"alt": 0, "neu": 0, "vorher": 0}
        for url in args.urls:
            try:
                alt = await _lauf(b, url, False)
                neu = await _lauf(b, url, True)
            except Exception as e:
                print(url + ": Fehler " + str(e), flush=True)
                continue
            summe["vorher"] += alt["region_vorher"]
            summe["alt"] += alt["region_nachher"]
            summe["neu"] += neu["region_nachher"]
            print("\n=== " + url)
            print("  alt: region {} -> {}   main={}".format(
                alt["region_vorher"], alt["region_nachher"], alt["haupt"]))
            print("  neu: region {} -> {}   +{} weitere Landmarken".format(
                neu["region_vorher"], neu["region_nachher"], neu["weitere"]))
            for n in neu["namen"]:
                print("       Name: " + n[:70])
        print("\n=== Summe region ueber {} Seiten: vorher {}, alt {}, neu {}".format(
            len(args.urls), summe["vorher"], summe["alt"], summe["neu"]))
        await b.close()

asyncio.run(main())
