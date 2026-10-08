#!/usr/bin/env python3
"""
Zwei Pruefstandslaeufe vergleichen: was haengt am Code, was am KI-Budget?

Der Pruefstand (tools/pruefstand.py) schreibt je Lauf eine pruefstand.json.
Dieses Werkzeug stellt zwei davon nebeneinander, nach HAEUFIGKEIT je
Befundtitel und nicht nach Einzelbefund: ein Titel, der in Lauf A auf 20 von
24 Seiten steht und in Lauf B auf 3, ist entweder eine Reparatur oder ein
Messfehler, und beides will man sehen.

Der wichtigste Fall ist derselbe Code mit --ki an gegen --ki aus. Jede Zeile
mit Differenz ist dann ein Befund, dessen Existenz nicht an der Website
haengt, sondern daran, ob ein fremder Dienst gerade antwortet. Am 09.09.2026
lag der Score-Mittelwert ohne KI bei 34, mit KI bei 43, und nur 0 von 24
Seiten hatten in beiden Laeufen dieselbe Note. Ziel ist 24 von 24.

Aufruf:
    python tools/pruefstand_vergleich.py /out/mit-ki/pruefstand.json /out/ohne-ki/pruefstand.json
    python tools/pruefstand_vergleich.py a.json b.json --seiten   # je Seite statt je Titel
"""
import argparse
import json
from collections import Counter
from statistics import mean


def lade(pfad: str) -> dict:
    with open(pfad, encoding="utf-8") as f:
        daten = json.load(f)
    seiten = {s["url"]: s for s in daten.get("seiten", []) if "issues" in s}
    return {"ki": daten.get("ki", "?"), "gemessen": daten.get("gemessen", "?"),
            "seiten": seiten}


def titel_haeufigkeit(seiten: dict) -> Counter:
    """Auf wie vielen Seiten kommt ein Befundtitel vor (je Seite hoechstens einmal)."""
    zaehler = Counter()
    for s in seiten.values():
        for titel in {i.get("title") for i in s["issues"]}:
            zaehler[titel] += 1
    return zaehler


def vergleich_je_titel(a: dict, b: dict) -> list:
    gemeinsam = sorted(set(a["seiten"]) & set(b["seiten"]))
    ha = titel_haeufigkeit({u: a["seiten"][u] for u in gemeinsam})
    hb = titel_haeufigkeit({u: b["seiten"][u] for u in gemeinsam})
    zeilen = []
    for titel in set(ha) | set(hb):
        zeilen.append((titel, ha.get(titel, 0), hb.get(titel, 0)))
    zeilen.sort(key=lambda z: (-abs(z[1] - z[2]), -max(z[1], z[2]), z[0] or ""))
    return zeilen


def vergleich_je_seite(a: dict, b: dict) -> list:
    zeilen = []
    for url in sorted(set(a["seiten"]) & set(b["seiten"])):
        sa, sb = a["seiten"][url], b["seiten"][url]
        ta = {i.get("title") for i in sa["issues"]}
        tb = {i.get("title") for i in sb["issues"]}
        zeilen.append({
            "url": url,
            "score_a": sa.get("score"), "score_b": sb.get("score"),
            "nur_a": sorted(t for t in ta - tb if t),
            "nur_b": sorted(t for t in tb - ta if t),
        })
    return zeilen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--seiten", action="store_true", help="Unterschiede je Seite statt je Titel")
    ap.add_argument("--alle", action="store_true", help="auch Titel ohne Differenz zeigen")
    args = ap.parse_args()

    a, b = lade(args.a), lade(args.b)
    gemeinsam = sorted(set(a["seiten"]) & set(b["seiten"]))
    print(f"A: {args.a}  (ki={a['ki']}, {a['gemessen'][:16]})")
    print(f"B: {args.b}  (ki={b['ki']}, {b['gemessen'][:16]})")
    print(f"{len(gemeinsam)} Seiten in beiden Laeufen "
          f"(nur A: {len(set(a['seiten']) - set(b['seiten']))}, "
          f"nur B: {len(set(b['seiten']) - set(a['seiten']))})")
    if not gemeinsam:
        return

    scores_a = [a["seiten"][u].get("score") for u in gemeinsam]
    scores_b = [b["seiten"][u].get("score") for u in gemeinsam]
    paare = [(x, y) for x, y in zip(scores_a, scores_b) if x is not None and y is not None]
    if paare:
        gleich = sum(1 for x, y in paare if x == y)
        print(f"Score-Mittel A {mean(x for x, _ in paare):.1f}, "
              f"B {mean(y for _, y in paare):.1f}; "
              f"identischer Score auf {gleich}/{len(paare)} Seiten")
    befunde_a = sum(len(a["seiten"][u]["issues"]) for u in gemeinsam)
    befunde_b = sum(len(b["seiten"][u]["issues"]) for u in gemeinsam)
    print(f"Befunde gesamt A {befunde_a}, B {befunde_b}\n")

    if args.seiten:
        for z in vergleich_je_seite(a, b):
            if not z["nur_a"] and not z["nur_b"] and z["score_a"] == z["score_b"] and not args.alle:
                continue
            print(f"{z['url']}  Score A {z['score_a']} / B {z['score_b']}")
            for t in z["nur_a"]:
                print(f"    nur A: {t}")
            for t in z["nur_b"]:
                print(f"    nur B: {t}")
        return

    print(f"{'Befundtitel':70} {'A':>4} {'B':>4} {'Diff':>5}")
    for titel, na, nb in vergleich_je_titel(a, b):
        if na == nb and not args.alle:
            continue
        print(f"{(titel or '(ohne Titel)')[:70]:70} {na:4d} {nb:4d} {nb - na:+5d}")


if __name__ == "__main__":
    main()
