#!/usr/bin/env python3
"""Wirkungsnachweis der Struktur-Reparatur über den echten Bestand."""
import argparse, asyncio, json, os, sys
from collections import Counter
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from compliance_engine.struktur_verifizierer import verifizierte_struktur_fixes


async def pruefe(pfad):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        pg = await b.new_page()
        try:
            await pg.goto(f"file://{os.path.abspath(pfad)}", wait_until="domcontentloaded",
                          timeout=45000)
            try:
                await pg.wait_for_load_state("networkidle", timeout=6000)
            except Exception:
                pass
            return await verifizierte_struktur_fixes(pg)
        finally:
            await b.close()


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", required=True)
    args = ap.parse_args()
    dateien = sorted(os.path.join(args.ordner, f) for f in os.listdir(args.ordner)
                     if f.endswith(".html"))
    v_regel, n_regel = Counter(), Counter()
    mit_main = 0
    ergebnisse = []
    for i, pfad in enumerate(dateien, 1):
        name = os.path.basename(pfad)
        try:
            r = await pruefe(pfad)
        except Exception as e:
            print(f"[{i}/{len(dateien)}] {name}: Fehler {e}", flush=True)
            continue
        ergebnisse.append({**r, "datei": name})
        for regel, (v, n) in r["je_regel"].items():
            v_regel[regel] += v
            n_regel[regel] += n
        if r["haupt_selektor"]:
            mit_main += 1
        if r["vorher"]:
            print(f"[{i}/{len(dateien)}] {name}: {r['vorher']} -> {r['nachher']}"
                  f"{'  main=' + r['haupt_selektor'] if r['haupt_selektor'] else ''}",
                  flush=True)
    print()
    print("=" * 64)
    print(f"{'Regel':<32}{'vorher':>8}{'nachher':>9}{'behoben':>9}")
    for regel in sorted(v_regel, key=lambda r: -v_regel[r]):
        v, n = v_regel[regel], n_regel[regel]
        print(f"{regel:<32}{v:>8}{n:>9}{v - n:>9}")
    v, n = sum(v_regel.values()), sum(n_regel.values())
    print("-" * 64)
    print(f"{'SUMME':<32}{v:>8}{n:>9}{v - n:>9}"
          f"   ({round(100 * (v - n) / v) if v else 0} %)")
    print(f"role=main gemessen bestimmt auf {mit_main} von {len(ergebnisse)} Seiten")
    print("=" * 64)
    with open(os.path.join(args.ordner, "struktur-wirkung.json"), "w",
              encoding="utf-8") as fh:
        json.dump(ergebnisse, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
