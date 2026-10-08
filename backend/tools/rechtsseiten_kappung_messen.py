#!/usr/bin/env python3
"""
Misst die Kappung der KI-Auszuege im Validator: Aufrufe, Kosten, Laufzeit und
Feldergebnisse je Seite und Kappung.

Der gebuendelte KI-Aufruf liest eine Seite in Auszuegen (`_BATCH_MAX_AUSSCHNITTE`).
Wie hoch die Kappung sein soll, ist eine Kostenfrage gegen eine Vollstaendigkeits-
frage und laesst sich nur mit echter KI beantworten. Dieses Werkzeug fuehrt
`validate_page` je Seite fuer mehrere Kappungen aus (Kappungen mit gleichen Auszuegen
werden nicht doppelt bezahlt) und schreibt alles in eine JSON-Datei, die sich gegen
die Etiketten auswerten laesst (siehe rechtsseiten_treffsicherheit.py).

Die Budget-Funktionen werden ersetzt: der Lauf verbraucht weder das Redis-Tagesbudget
des Betriebs noch wird er davon gebremst. Echte Kosten laufen trotzdem auf, bei 19
Seiten und vier Kappungen rund 0,20 EUR.

Aufruf im Backend-Image (Mount auf /src, Umgebung des Backend-Containers wegen
OPENROUTER_API_KEY, ohne Netz zu Redis):
    KAPPUNGEN=4,6,8,12 python tools/rechtsseiten_kappung_messen.py liste.json ergebnis.json
`liste.json`: {"domain": "https://...datenschutz-url"}
"""
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aiohttp
from compliance_engine import ai_budget
from compliance_engine.hybrid_validator import HybridValidator, zu_fliesstext

KAPPUNGEN = [int(x) for x in os.environ.get("KAPPUNGEN", "4,6,8,12").split(",")]
verbrauch = {"calls": 0, "kosten": 0.0, "tokens": 0}

async def frei(*_a, **_k):
    return True
async def buchen(user_id, kosten):
    verbrauch["calls"] += 1
    verbrauch["kosten"] += kosten
ai_budget.budget_frei = frei
ai_budget.kosten_buchen = buchen

async def hole(url):
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as s:
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True) as r:
            return await r.text()

async def main(liste, out):
    ziele = json.load(open(liste))          # {dom: url}
    ergebnis = {}
    for dom, url in ziele.items():
        html = await hole(url)
        text = zu_fliesstext(html)
        hv0 = HybridValidator()
        ergebnis[dom] = {"url": url, "zeichen": len(text), "kappung": {}}
        letzter = None
        for kap in KAPPUNGEN:
            HybridValidator._BATCH_MAX_AUSSCHNITTE = kap
            teile, voll = HybridValidator()._batch_ausschnitte(text)
            # Gleiche Auszuege wie die vorige Kappung und schon vollstaendig gelesen: Ergebnis uebernehmen.
            if letzter is not None and letzter["auszuege"] == len(teile) and letzter["voll"] == voll:
                ergebnis[dom]["kappung"][kap] = {**letzter, "uebernommen": True}
                continue
            verbrauch.update(calls=0, kosten=0.0)
            t0 = time.monotonic()
            r = await HybridValidator().validate_page("datenschutz", html, url)
            felder = {f["field"]: {"found": f["found"], "unverifiziert": bool(f.get("unverifiziert")),
                                   "methode": f["method"]} for f in r["results"]}
            letzter = {"auszuege": len(teile), "voll": voll, "calls": verbrauch["calls"],
                       "kosten": round(verbrauch["kosten"], 5), "sekunden": round(time.monotonic() - t0, 1),
                       "felder": felder}
            ergebnis[dom]["kappung"][kap] = letzter
            print(f"{dom:28} {len(text):>6} Zeichen kappung={kap:>2} auszuege={len(teile)} voll={voll} "
                  f"calls={verbrauch['calls']} {verbrauch['kosten']:.4f} EUR", flush=True)
    json.dump(ergebnis, open(out, "w"), ensure_ascii=False, indent=1)

asyncio.run(main(sys.argv[1], sys.argv[2]))
