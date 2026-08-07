#!/usr/bin/env python3
"""
Gesamtwirkung: alles, was complyo reparieren kann, in EINEM Lauf gemessen.

Zahlen aus drei getrennten Laeufen zu addieren waere unsauber — Fixes
beeinflussen einander (ein role="main" veraendert die region-Zaehlung, ein
Alt-Text loest zugleich link-name). Deshalb hier: dieselbe Seite, alle
Reparaturen nacheinander, axe davor und danach ueber den vollen Regelsatz.
"""
import argparse, asyncio, json, os, sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.axe_scanner import AXE_CORE_JS, axe_tags_fuer, ist_rechtspflicht
from compliance_engine.struktur_verifizierer import verifizierte_struktur_fixes
from compliance_engine.kontrast_verifizierer import verifizierte_kontrast_fixes
from compliance_engine.linkname_fixes import baue_linkname_vorschlaege

VOLL = json.dumps({"runOnly": {"type": "tag", "values": axe_tags_fuer("wcag21aa")}})


async def _axe_voll(page):
    if not await page.evaluate("typeof axe !== 'undefined'"):
        await page.add_script_tag(content=AXE_CORE_JS)
        await page.wait_for_function("typeof axe !== 'undefined'", timeout=8000)
    r = await page.evaluate("async () => await axe.run(document, %s)" % VOLL)
    return r.get("violations", [])


def _zaehle(violations):
    pflicht = sum(len(v["nodes"]) for v in violations if ist_rechtspflicht(v["tags"]))
    empfehlung = sum(len(v["nodes"]) for v in violations if not ist_rechtspflicht(v["tags"]))
    je_regel = Counter({v["id"]: len(v["nodes"]) for v in violations})
    return pflicht, empfehlung, je_regel


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

            vor = await _axe_voll(pg)
            v_pflicht, v_empf, v_regel = _zaehle(vor)

            # Link-Beschriftungen: Vorschlaege bestimmen und wie im Betrieb
            # als aria-label setzen.
            ln_knoten = [n for v in vor if v["id"] in ("link-name", "button-name")
                         for n in v["nodes"]]
            vorschlaege = baue_linkname_vorschlaege(ln_knoten)
            if vorschlaege:
                await pg.evaluate("""(v) => {
                  for (const e of v) for (const s of (e.selektoren || [])) {
                    try { const el = document.querySelector(s);
                          if (el && !el.getAttribute('aria-label'))
                            el.setAttribute('aria-label', e.label); } catch (x) {}
                  }
                }""", vorschlaege)

            await verifizierte_struktur_fixes(pg)
            await verifizierte_kontrast_fixes(pg)
            await pg.wait_for_timeout(400)

            nach = await _axe_voll(pg)
            n_pflicht, n_empf, n_regel = _zaehle(nach)
            return {"datei": os.path.basename(pfad),
                    "vorher": {"pflicht": v_pflicht, "empfehlung": v_empf, "regeln": dict(v_regel)},
                    "nachher": {"pflicht": n_pflicht, "empfehlung": n_empf, "regeln": dict(n_regel)}}
        finally:
            await b.close()


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", required=True)
    args = ap.parse_args()
    dateien = sorted(os.path.join(args.ordner, f) for f in os.listdir(args.ordner)
                     if f.endswith(".html"))
    erg, vr, nr = [], Counter(), Counter()
    for i, pfad in enumerate(dateien, 1):
        try:
            r = await pruefe(pfad)
        except Exception as e:
            print(f"[{i}/{len(dateien)}] {os.path.basename(pfad)}: Fehler {e}", flush=True)
            continue
        erg.append(r)
        vr.update(r["vorher"]["regeln"]); nr.update(r["nachher"]["regeln"])
        print(f"[{i}/{len(dateien)}] {r['datei']:<38} "
              f"Pflicht {r['vorher']['pflicht']:>3} -> {r['nachher']['pflicht']:<3} "
              f"Empfehlung {r['vorher']['empfehlung']:>3} -> {r['nachher']['empfehlung']}",
              flush=True)

    vp = sum(r["vorher"]["pflicht"] for r in erg); np_ = sum(r["nachher"]["pflicht"] for r in erg)
    ve = sum(r["vorher"]["empfehlung"] for r in erg); ne = sum(r["nachher"]["empfehlung"] for r in erg)
    print("\n" + "=" * 68)
    print(f"{'Regel':<34}{'vorher':>8}{'nachher':>9}{'behoben':>9}")
    for regel in sorted(vr, key=lambda r: -vr[r]):
        if vr[regel] - nr[regel] == 0 and vr[regel] < 3:
            continue
        print(f"{regel:<34}{vr[regel]:>8}{nr[regel]:>9}{vr[regel] - nr[regel]:>9}")
    print("-" * 68)
    print(f"{'PFLICHT (WCAG 2.1 AA)':<34}{vp:>8}{np_:>9}{vp - np_:>9}"
          f"   ({round(100 * (vp - np_) / vp) if vp else 0} %)")
    print(f"{'Empfehlung (best-practice)':<34}{ve:>8}{ne:>9}{ve - ne:>9}"
          f"   ({round(100 * (ve - ne) / ve) if ve else 0} %)")
    print("=" * 68)
    with open(os.path.join(args.ordner, "gesamtwirkung.json"), "w", encoding="utf-8") as fh:
        json.dump(erg, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
