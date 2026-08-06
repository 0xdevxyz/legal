#!/usr/bin/env python3
"""
Wirkungsnachweis fuer die Kontrast-Reparatur.

Unit-Tests belegen, dass die Mathematik stimmt. Sie belegen nicht, dass der
Fix auf einer echten Seite ankommt — dazwischen liegen Kaskade, Spezifitaet
und Selektoren, die axe geliefert hat. Deshalb wird hier gemessen statt
gerechnet: dieselbe Seite, axe davor, CSS eingespielt, axe danach.

Aufruf im Backend-Container (Mount auf /src):
    python tools/kontrast_wirkung.py --ordner /out
"""
import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.axe_scanner import AXE_CORE_JS, axe_tags_fuer  # noqa: E402
from compliance_engine.kontrast_verifizierer import (  # noqa: E402
    verifizierte_kontrast_fixes,
)


async def _axe(page) -> Dict[str, Any]:
    await page.add_script_tag(content=AXE_CORE_JS)
    await page.wait_for_function("typeof axe !== 'undefined'", timeout=8000)
    cfg = {"runOnly": {"type": "tag", "values": axe_tags_fuer("wcag21aa")}}
    return await page.evaluate(
        "async () => await axe.run(document, %s)" % json.dumps(cfg)
    )


def _kontrast_knoten(ergebnis: Dict[str, Any]) -> List[Dict[str, Any]]:
    for v in ergebnis.get("violations", []):
        if v["id"] == "color-contrast":
            return v["nodes"]
    return []


async def pruefe_seite(pfad: str) -> Dict[str, Any]:
    from playwright.async_api import async_playwright

    datei_url = f"file://{os.path.abspath(pfad)}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(datei_url, wait_until="domcontentloaded", timeout=45000)
            try:
                await page.wait_for_load_state("networkidle", timeout=6000)
            except Exception:
                pass

            r = await verifizierte_kontrast_fixes(page)
            return {
                "datei": os.path.basename(pfad),
                "vorher": r["vorher"],
                "nachher": r["nachher"],
                "entscheidungen": len(r["entscheidungen"]),
                "bestaetigt": sum(1 for e in r["entscheidungen"] if e.get("bestaetigt")),
                "runden": r["runden"],
                "css_zeichen": len(r["css"]),
            }
        finally:
            await browser.close()


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", required=True, help="Ordner mit den .html-Kopien")
    args = ap.parse_args()

    dateien = sorted(
        os.path.join(args.ordner, f)
        for f in os.listdir(args.ordner)
        if f.endswith(".html")
    )

    ergebnisse = []
    for i, pfad in enumerate(dateien, 1):
        name = os.path.basename(pfad)
        try:
            r = await pruefe_seite(pfad)
        except Exception as e:
            print(f"[{i}/{len(dateien)}] {name}: Fehler {e}", flush=True)
            continue
        ergebnisse.append(r)
        if r["vorher"]:
            print(f"[{i}/{len(dateien)}] {name}: {r['vorher']} -> {r['nachher']} "
                  f"({r['entscheidungen']} Entscheidungen, {r.get('runden',0)} Runden)",
                  flush=True)
        else:
            print(f"[{i}/{len(dateien)}] {name}: kein Kontrastproblem", flush=True)

    v = sum(r["vorher"] for r in ergebnisse)
    n = sum(r["nachher"] for r in ergebnisse)
    ent = sum(r["entscheidungen"] for r in ergebnisse)
    betroffen = [r for r in ergebnisse if r["vorher"]]
    print()
    print("=" * 62)
    print(f"Seiten mit Kontrastproblem : {len(betroffen)} von {len(ergebnisse)}")
    print(f"Fundstellen                : {v} -> {n}  (behoben: {v - n}, "
          f"{round(100 * (v - n) / v) if v else 0} %)")
    print(f"Menschliche Entscheidungen : {ent}  "
          f"(= {round(v / ent, 1) if ent else 0} Fundstellen je Freigabe)")
    print("=" * 62)

    with open(os.path.join(args.ordner, "kontrast-wirkung.json"), "w",
              encoding="utf-8") as fh:
        json.dump(ergebnisse, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
