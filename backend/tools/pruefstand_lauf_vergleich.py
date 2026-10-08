#!/usr/bin/env python3
"""
Pruefstand-Vergleich: zwei Laeufe nebeneinander, die Haeufigkeit je Befundart.

`pruefstand.py` misst einen Bestand echter Seiten. Eine einzelne Messung ist ein
Foto; ob eine Aenderung am Scanner etwas verbessert oder verschlechtert hat,
zeigt erst der Vergleich zweier Laeufe ueber DIESELBEN Seiten. Dieses Werkzeug
stellt sie gegenueber und sagt zwei Dinge, die ein Mittelwert allein verdeckt:

1. Was hat sich je Befundart bewegt? Nicht der Einzelbefund zaehlt, sondern die
   Zahl der Seiten, auf denen er auftritt.
2. Welche Befunde feuern auf fast jeder Seite? Alle acht Phantom-Regeln, die am
   08.09.2026 aufflogen, sahen gleich aus: sie traten auf 20 von 24 Seiten auf.
   Eine Pflicht, die fast alle echten Seiten gleichzeitig verletzen, ist
   meistens ein Messfehler. Das ist ein Verdacht, kein Urteil: die Liste nennt
   Kandidaten, die ein Mensch an Quelltext und Rechtslage pruefen muss.

axe-Regeln stehen nicht auf der Verdachtsliste. axe ist die Referenz: dass
color-contrast auf drei Viertel der Seiten auftritt, ist ein Befund ueber den
Bestand, kein Fehler des Scanners (siehe Bestandsaufnahme vom 06.08.2026).
Befunde ohne Eurobetrag (Hinweise, Empfehlungen) ebenfalls nicht: sie kosten
den Kunden keine Note und behaupten kein Risiko.

Abgrenzung zu `pruefstand_vergleich.py` (PR #17): jenes stellt zwei Messungen
DESSELBEN Codes mit und ohne KI nebeneinander, um die Befunde zu finden, die am
KI-Budget haengen. Dieses stellt zwei LAEUFE ueber die Zeit nebeneinander (vor und
nach einer Aenderung, Woche gegen Woche) und fuehrt die Verdachtsliste. Beide
lesen dieselbe `pruefstand.json`.

Nur Python-Standardbibliothek, damit es auf dem Server ohne Container laeuft.

Aufruf:
    python3 tools/pruefstand_lauf_vergleich.py ALT.json NEU.json
    python3 tools/pruefstand_lauf_vergleich.py ALT.json NEU.json --streng
    python3 tools/pruefstand_lauf_vergleich.py NEU.json          # nur Verdachtsliste

`--streng` setzt den Exitcode 1, wenn gegenueber ALT eine neue Verdachtsart
auftritt oder der Score-Mittelwert um mehr als `--score-grenze` Punkte faellt.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

_ZAHL = re.compile(r"\d+")
_NICHT_WORT = re.compile(r"[^\w#]+")


def lade(pfad: str) -> Dict[str, Any]:
    with open(pfad, encoding="utf-8") as fh:
        return json.load(fh)


def anzeige(issue: Dict[str, Any]) -> str:
    """Der Titel, wie ihn der Kunde liest."""
    return f"{issue.get('category') or '?'}: {(issue.get('title') or '').strip()}"


def befundart(issue: Dict[str, Any]) -> str:
    """Schluessel einer Befundart: Kategorie und Titel, Zahlen als `#`.

    Dieselbe Linie wie `ScoreCalculator` fuer die Obergrenze je Typ: "12
    Bilder ohne Alt-Text" und "3 Bilder ohne Alt-Text" sind eine Art.

    Satzzeichen und Schreibweise zaehlen nicht. Der Pruefstand vergleicht Laeufe
    ueber Wochen, und in der Zeit werden Titel umformuliert: aus "Google Fonts
    (extern geladen) — Drittlandtransfer" wurde "Google Fonts (extern geladen):
    Drittlandtransfer". Mit dem Titel als Rohtext zeigte der Vergleich dafuer ein
    Minus von 10 und ein Plus von 10, also eine Bewegung, die es nicht gab.
    """
    titel = _ZAHL.sub("#", (issue.get("title") or "").strip())
    titel = _NICHT_WORT.sub(" ", titel.lower()).strip()
    return f"{issue.get('category') or '?'}: {titel}"


def messbare(lauf: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Die Seiten, die tatsaechlich gemessen wurden (URL -> Messung)."""
    return {s["url"]: s for s in lauf.get("seiten", []) if "issues" in s}


def haeufigkeit(seiten: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Je Befundart: auf wie vielen Seiten, wie viele Treffer, welches Risiko."""
    arten: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"seiten": set(), "treffer": 0, "risiko_euro": 0,
                 "axe": False, "severity": set(), "titel": ""})
    for url, s in seiten.items():
        for i in s["issues"]:
            a = arten[befundart(i)]
            a["titel"] = a["titel"] or anzeige(i)
            a["seiten"].add(url)
            a["treffer"] += 1
            a["risiko_euro"] += int(i.get("risk_euro") or 0)
            a["axe"] = a["axe"] or bool(i.get("axe_rule"))
            a["severity"].add(i.get("severity"))
    return arten


def kennzahlen(seiten: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    scores = [s["score"] for s in seiten.values() if s.get("score") is not None]
    issues = [i for s in seiten.values() for i in s["issues"]]
    return {
        "seiten": len(seiten),
        "score_mittel": round(sum(scores) / len(scores), 1) if scores else None,
        "befunde": len(issues),
        "kritisch": sum(1 for i in issues if i.get("severity") == "critical"),
        "risiko_euro": sum(int(i.get("risk_euro") or 0) for i in issues),
    }


def _verdacht(seiten: Dict[str, Dict[str, Any]], schwelle: float,
              mindestens: int) -> List[Tuple[str, str, int, float, int]]:
    n = len(seiten)
    if n < mindestens:
        return []
    treffer = []
    for schluessel, a in haeufigkeit(seiten).items():
        if a["axe"] or a["risiko_euro"] <= 0:
            continue
        quote = len(a["seiten"]) / n
        if quote >= schwelle:
            treffer.append((schluessel, a["titel"], len(a["seiten"]), quote,
                            a["risiko_euro"]))
    return sorted(treffer, key=lambda t: (-t[2], t[1]))


def verdacht(seiten: Dict[str, Dict[str, Any]], schwelle: float = 0.75,
             mindestens: int = 8) -> List[Tuple[str, int, float, int]]:
    """Befundarten, die auf fast jeder Seite feuern, aber Geld kosten.

    Eine Art steht darauf, wenn sie auf mindestens `schwelle` der gemessenen
    Seiten auftritt, mindestens einmal einen Eurobetrag traegt und nicht aus
    axe stammt. Unter `mindestens` Seiten sagt eine Quote nichts.

    Liefert (Titel, Seiten, Quote, Euro).
    """
    return [(titel, n, q, e)
            for _, titel, n, q, e in _verdacht(seiten, schwelle, mindestens)]


def vergleiche(alt: Dict[str, Any], neu: Dict[str, Any],
               schwelle: float = 0.75, mindestens: int = 8) -> Dict[str, Any]:
    """Stellt zwei Laeufe gegenueber, nur ueber die gemeinsam gemessenen Seiten.

    Ohne diese Einschraenkung veraendert schon eine Seite, die in einem Lauf
    nicht erreichbar war, jeden Mittelwert.
    """
    s_alt, s_neu = messbare(alt), messbare(neu)
    gemeinsam = sorted(set(s_alt) & set(s_neu))
    a = {u: s_alt[u] for u in gemeinsam}
    b = {u: s_neu[u] for u in gemeinsam}

    h_alt, h_neu = haeufigkeit(a), haeufigkeit(b)
    zeilen = []
    for schluessel in sorted(set(h_alt) | set(h_neu)):
        v = len(h_alt[schluessel]["seiten"]) if schluessel in h_alt else 0
        n = len(h_neu[schluessel]["seiten"]) if schluessel in h_neu else 0
        titel = (h_neu.get(schluessel) or h_alt[schluessel])["titel"]
        zeilen.append({"art": titel, "alt": v, "neu": n, "diff": n - v})

    k_alt = {t[0]: t[1] for t in _verdacht(a, schwelle, mindestens)}
    k_neu = {t[0]: t[1] for t in _verdacht(b, schwelle, mindestens)}
    return {
        "gemeinsam": len(gemeinsam),
        "nur_alt": sorted(set(s_alt) - set(s_neu)),
        "nur_neu": sorted(set(s_neu) - set(s_alt)),
        "kennzahlen_alt": kennzahlen(a),
        "kennzahlen_neu": kennzahlen(b),
        "arten": zeilen,
        "verdacht_neu": sorted(k_neu[k] for k in set(k_neu) - set(k_alt)),
        "verdacht_weg": sorted(k_alt[k] for k in set(k_alt) - set(k_neu)),
        "verdacht": verdacht(b, schwelle, mindestens),
    }


def _euro(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _kz(z: Dict[str, Any]) -> str:
    return (f"Score {z['score_mittel']}, {z['befunde']} Befunde "
            f"({z['kritisch']} kritisch), {_euro(z['risiko_euro'])} EUR Risiko")


def bericht(v: Dict[str, Any], alt_name: str = "alt", neu_name: str = "neu") -> str:
    zeilen: List[str] = []
    zeilen.append(f"Vergleich ueber {v['gemeinsam']} gemeinsam gemessene Seiten")
    for was, urls in (("nur im alten Lauf", v["nur_alt"]),
                      ("nur im neuen Lauf", v["nur_neu"])):
        if urls:
            zeilen.append(f"  {was} gemessen ({len(urls)}), nicht verglichen")
    zeilen.append(f"  {alt_name:>5}: {_kz(v['kennzahlen_alt'])}")
    zeilen.append(f"  {neu_name:>5}: {_kz(v['kennzahlen_neu'])}")

    bewegt = [z for z in v["arten"] if z["diff"] != 0]
    zeilen.append("")
    zeilen.append(f"Befundarten, die sich bewegt haben ({len(bewegt)}), "
                  "Seiten mit Befund alt -> neu:")
    for z in sorted(bewegt, key=lambda z: (z["diff"], z["art"])):
        zeilen.append(f"  {z['alt']:>3} -> {z['neu']:>3}  ({z['diff']:+d})  {z['art']}")
    if not bewegt:
        zeilen.append("  keine")

    zeilen.append("")
    n = v["kennzahlen_neu"]["seiten"]
    zeilen.append("Verdacht auf Messfehler im neuen Lauf (complyo-eigene Befunde "
                  "mit Eurobetrag, die auf fast jeder Seite stehen):")
    for art, seiten, quote, risiko in v["verdacht"]:
        neu = "  NEU" if art in v["verdacht_neu"] else ""
        zeilen.append(f"  {seiten:>3}/{n}  {quote:>4.0%}  {_euro(risiko):>7} EUR  {art}{neu}")
    if not v["verdacht"]:
        zeilen.append("  keine")
    for art in v["verdacht_weg"]:
        zeilen.append(f"  weg gegenueber dem alten Lauf: {art}")
    zeilen.append("")
    zeilen.append("Die Liste nennt Kandidaten. Jeder Eintrag ist an Quelltext und "
                  "Rechtslage zu pruefen, bevor man ihn aendert (Breitenprobe: "
                  "eine Seite OHNE die Angabe darf nicht als vorhanden gemeldet "
                  "werden).")
    return "\n".join(zeilen)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dateien", nargs="+", help="ALT.json NEU.json oder nur NEU.json")
    ap.add_argument("--schwelle", type=float, default=0.75,
                    help="Anteil der Seiten, ab dem eine Art verdaechtig ist")
    ap.add_argument("--streng", action="store_true",
                    help="Exitcode 1 bei neuer Verdachtsart oder Score-Absturz")
    ap.add_argument("--score-grenze", type=float, default=5.0,
                    help="Punkte, um die der Mittelwert fallen darf")
    args = ap.parse_args(argv)

    if len(args.dateien) == 1:
        neu = lade(args.dateien[0])
        seiten = messbare(neu)
        print(f"{len(seiten)} Seiten gemessen: {_kz(kennzahlen(seiten))}\n")
        print("Verdacht auf Messfehler (complyo-eigene Befunde mit Eurobetrag "
              "auf fast jeder Seite):")
        liste = verdacht(seiten, args.schwelle)
        for art, n, quote, risiko in liste:
            print(f"  {n:>3}/{len(seiten)}  {quote:>4.0%}  {_euro(risiko):>7} EUR  {art}")
        if not liste:
            print("  keine")
        return 0

    if len(args.dateien) != 2:
        ap.error("entweder eine Datei (nur Verdachtsliste) oder zwei (Vergleich)")
    alt, neu = lade(args.dateien[0]), lade(args.dateien[1])
    v = vergleiche(alt, neu, args.schwelle)
    print(bericht(v))

    if args.streng:
        a, b = v["kennzahlen_alt"]["score_mittel"], v["kennzahlen_neu"]["score_mittel"]
        fehler = []
        if v["verdacht_neu"]:
            fehler.append(f"{len(v['verdacht_neu'])} neue Verdachtsart(en)")
        if a is not None and b is not None and a - b > args.score_grenze:
            fehler.append(f"Score-Mittel faellt von {a} auf {b}")
        if v["gemeinsam"] == 0:
            fehler.append("keine gemeinsam gemessene Seite, nichts verglichen")
        if fehler:
            print("\nSTRENG: " + "; ".join(fehler), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
