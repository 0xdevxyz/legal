"""Vergleich HTML-Scan gegen Browser-Prüfstufe an echten Seiten.

Beantwortet die Frage, die vor jedem Einschalten gestellt werden muss: Was fügt
der Browser hinzu, und stimmt es? Je Seite stehen nebeneinander

  * was der HTML-Scan findet (nur Katalogtreffer, wie im Banner),
  * was der Browser eindeutig zuordnet, mit den Hosts als Beleg,
  * was nur im Browser auftaucht (`neu`: würde den Banner ergänzen),
  * was nur im HTML steht (`nur_html`),
  * die Prüfliste: mehrdeutige, breite und unbekannte Fremdhosts.

Jedes `neu` ist von Hand gegen den Beleg zu lesen. Kommt ein Dienst ohne
einleuchtenden Host, ist das ein Fehler der Zuordnung, nicht der Seite.

Seiten laufen nacheinander (eine pro Browser), wie im Betrieb bei einem Arbeiter.
Gemessen werden Dauer und Spitzen-Speicher der Chromium-Prozesse.

Aufruf (Backend-Verzeichnis, Netzwerk nötig):

    python tools/pruefstufe_vergleich.py --seiten sites.txt --ausgabe vergleich.json

`sites.txt`: eine Domain oder URL je Zeile (Kundenliste nie ins Repo).
Katalog: live von api.complyo.de (öffentlich), oder `--katalog datei.json`.
"""

import argparse
import asyncio
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(__file__))

from compliance_engine import cookie_pruefstufe as ps  # noqa: E402
from compliance_engine.deep_cookie_scanner import DeepCookieScanner  # noqa: E402
from cookie_scanner_service import cookie_scanner  # noqa: E402
from pruefstufe_lasttest import chromium_messung  # noqa: E402


def katalog_laden(pfad):
    if pfad:
        raw = json.load(open(pfad, encoding="utf-8"))
    else:
        with urllib.request.urlopen("https://api.complyo.de/api/cookie-compliance/services", timeout=30) as r:
            raw = json.loads(r.read())
    items = raw.get("services") or raw.get("data") or raw
    katalog = []
    for s in items:
        if s.get("is_active") is False:
            continue
        t = ps._als_objekt(s.get("template"), {}) or {}
        domains = t.get("domains") if isinstance(t, dict) and isinstance(t.get("domains"), list) else []
        katalog.append({"service_key": s["service_key"], "name": s.get("name"), "category": s.get("category"),
                        "provider": s.get("provider") or "", "domains": [d for d in domains if isinstance(d, str)],
                        "cookie_patterns": []})
    return katalog


async def eine_seite(url, katalog, index, aktive_keys):
    t0 = time.time()
    html = await cookie_scanner.scan_website(url)
    html_keys = sorted(k for k in (html.get("detected_services") or []) if k in aktive_keys)
    t_html = time.time() - t0

    spitze = {"mib": 0.0}

    async def messen(stopp):
        while not stopp.is_set():
            spitze["mib"] = max(spitze["mib"], chromium_messung()[1])
            await asyncio.sleep(0.5)

    stopp = asyncio.Event()
    messer = asyncio.create_task(messen(stopp))
    t1 = time.time()
    try:
        erg = await asyncio.wait_for(DeepCookieScanner(0, url, catalog=katalog).scan(), timeout=ps.JOB_ZEIT_S)
        fehler = erg.error
    except asyncio.TimeoutError:
        erg, fehler = None, f"Zeitbudget {ps.JOB_ZEIT_S} s"
    finally:
        stopp.set()
        await messer
    t_browser = time.time() - t1

    zeile = {"url": url, "html_keys": html_keys, "html_fehler": html.get("error"),
             "dauer_html_s": round(t_html, 1), "dauer_browser_s": round(t_browser, 1),
             "spitze_mib": round(spitze["mib"]), "browser_fehler": fehler}
    if erg is not None and not fehler:
        zeile["bewertung"] = ps.bewerte(
            [{"url": r.url} for r in erg.requests], [{"name": c.name} for c in erg.cookies],
            html.get("url") or url, index, html_keys,
        )
    return zeile


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seiten", required=True)
    ap.add_argument("--ausgabe", default="pruefstufe-vergleich.json")
    ap.add_argument("--katalog")
    args = ap.parse_args()

    katalog = katalog_laden(args.katalog)
    index = ps.baue_index(katalog)
    aktive = {s["service_key"] for s in katalog}
    seiten = [z.strip() for z in open(args.seiten, encoding="utf-8") if z.strip() and not z.startswith("#")]
    print(f"{len(seiten)} Seiten, Katalog {len(katalog)} Dienste, {len(index)} Domains")

    ergebnisse = []
    for i, s in enumerate(seiten, 1):
        url = s if s.startswith("http") else f"https://{s}"
        try:
            z = await eine_seite(url, katalog, index, aktive)
        except Exception as e:  # eine Seite darf den Lauf nicht beenden
            z = {"url": url, "fehler": str(e)[:200]}
        ergebnisse.append(z)
        b = z.get("bewertung") or {}
        print(f"[{i}/{len(seiten)}] {url}  html={len(z.get('html_keys', []))} browser={len(b.get('browser_keys', []))} "
              f"neu={b.get('neu')} nur_html={len(b.get('nur_html', []))} "
              f"{z.get('dauer_browser_s')}s {z.get('spitze_mib')}MiB {z.get('browser_fehler') or z.get('fehler') or ''}")

    json.dump(ergebnisse, open(args.ausgabe, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = [z for z in ergebnisse if z.get("bewertung")]
    dauern = sorted(z["dauer_browser_s"] for z in ok)
    print("\n=== Zusammenfassung ===")
    print(f"Messbar: {len(ok)} von {len(ergebnisse)}")
    if dauern:
        print(f"Browser-Dauer: Median {dauern[len(dauern)//2]} s, max {dauern[-1]} s")
        print(f"Spitzen-Speicher je Seite: max {max(z['spitze_mib'] for z in ok)} MiB")
    mit_neu = [z for z in ok if z["bewertung"]["neu"]]
    print(f"Seiten, bei denen der Browser etwas ergaenzen wuerde: {len(mit_neu)}")
    for z in mit_neu:
        b = z["bewertung"]
        for k in b["neu"]:
            print(f"  NEU {z['url']}: {k}  Beleg {b['belege'][k]['hosts']}")
    print("Von Hand lesen: jeder NEU-Eintrag braucht einen einleuchtenden Host.")


if __name__ == "__main__":
    asyncio.run(main())
