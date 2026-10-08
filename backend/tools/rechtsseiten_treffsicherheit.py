#!/usr/bin/env python3
"""
Treffsicherheit der Rechtsseiten-Befunde gegen einen von Hand etikettierten Bestand.

Der Pruefstand (`pruefstand.py`, `pruefstand_lauf_vergleich.py`) misst Haeufigkeiten:
wie oft ein Befund auftritt. Ob er zu Recht auftritt, sagt er nicht. Dieses
Werkzeug legt einen Lauf neben die Etiketten (wo steht das Impressum, wo die
Datenschutzerklaerung, welche Pflichtangaben stehen darin) und zaehlt:

Seitenebene   Fand der Check die Rechtsseite, die es gibt? Ein "nicht gefunden"
              bei vorhandener Seite (falscher Alarm) ist der teure Fehler: er
              loest sechs Folgebefunde aus. Ein "gefunden" bei fehlender Seite
              (verpasster Mangel) ist der gefaehrliche.

Feldebene     Auf Seiten, die Etikett UND Check gefunden haben: wie oft stimmt
              ein "X fehlt"? Genauigkeit = richtige Behauptungen je Behauptung,
              Trefferquote = gefundene Luecken je tatsaechlicher Luecke. Dazu die
              Summe der Eurobetraege, die an falschen Behauptungen haengen.

Ein Feld ohne Befund gilt als "nicht beanstandet", auch wenn die Pruefung wegen
fehlender KI-Zweitmeinung nur "nicht abschliessend geprueft" meldet: aus Sicht
des Kunden ist beides kein Mangel. Etiketten mit `unsicher` (grenzwertige Faelle,
etwa Dauer nur fuer Cookies) werden auf Wunsch getrennt ausgewertet.

Die Etiketten und die Laeufe enthalten Kundendomains und gehoeren nicht ins Repo.
Nur Python-Standardbibliothek.

Aufruf:
    python3 tools/rechtsseiten_treffsicherheit.py --wahrheit wahrheit.json \
        --lauf live=laeufe/a/pruefstand.json --lauf neu=laeufe/b/pruefstand.json
        [--streng] [--details]
"""
import argparse
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

# Befunde, die sagen: die Rechtsseite wurde nicht gefunden oder ist keine.
NICHT_GEFUNDEN = {
    "impressum": {"Kein Impressum-Link gefunden", "Impressum-Link führt zu keiner Impressumsseite",
                  "Impressum-Seite nicht erreichbar"},
    "datenschutz": {"Keine Datenschutzerklärung gefunden",
                    "Datenschutz-Link führt zu keiner Datenschutzerklärung",
                    "Datenschutzerklärung nicht erreichbar"},
}

# "Inhaltspruefung nicht moeglich": gefunden, aber nicht gelesen.
UNBESTAETIGT = {
    "impressum": {"Inhaltsprüfung des Impressums nicht möglich"},
    "datenschutz": {"Inhaltsprüfung der Datenschutzerklärung nicht möglich"},
}

# Befundtitel je Feld (Feldebene, nur auf gefundenen Seiten).
FELD_TITEL = {
    "impressum": {
        "Firmenname/Name fehlt im Impressum": "name",
        "Anschrift fehlt im Impressum": "adresse",
        "PLZ/Ort fehlen im Impressum": "plz_ort",
        "E-Mail-Adresse fehlt im Impressum": "email",
        "Telefonnummer fehlt im Impressum": "telefon",
        "Handelsregister-Angabe nicht gefunden": "register",
        "Handelsregisternummer fehlt (GmbH/UG erkannt)": "register",
        "Handelsregisternummer fehlt (AG/SE erkannt)": "register",
        "Geschäftsführer nicht angegeben (GmbH/UG erkannt)": "vertretung",
        "Vorstand nicht angegeben (e.V. erkannt)": "vertretung",
    },
    "datenschutz": {
        "Verantwortlicher fehlt": "verantwortlicher",
        "Zwecke der Datenverarbeitung fehlen": "zwecke",
        "Rechtsgrundlagen fehlen": "rechtsgrundlage",
        "Speicherdauer fehlt": "speicherdauer",
        "Betroffenenrechte fehlen": "betroffenenrechte",
        "Beschwerderecht fehlt": "beschwerderecht",
    },
}


def _dom(url: str) -> str:
    d = url.split("//", 1)[-1].split("/", 1)[0].lower()
    return d[4:] if d.startswith("www.") else d


def lade(pfad: str) -> Dict[str, Any]:
    with open(pfad, encoding="utf-8") as fh:
        return json.load(fh)


def messbare(lauf: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    return {_dom(s["url"]): s["issues"] for s in lauf.get("seiten", []) if "issues" in s}


def seitenebene(wahrheit: Dict[str, Any], issues_je_seite: Dict[str, List[Dict[str, Any]]],
                art: str) -> Dict[str, Any]:
    """Auffindbarkeit: Etikett gegen Befund."""
    res = {"richtig_gefunden": [], "falscher_alarm": [], "verpasst": [], "richtig_nicht_gefunden": [],
           "unbestaetigt": []}
    for dom, w in wahrheit["seiten"].items():
        if dom not in issues_je_seite:
            continue
        titel = {i["title"] for i in issues_je_seite[dom]}
        gefunden_laut_check = not (titel & NICHT_GEFUNDEN[art])
        existiert = w[art]["ort"] != "keine"
        if existiert and gefunden_laut_check:
            res["richtig_gefunden"].append(dom)
            if titel & UNBESTAETIGT[art]:
                res["unbestaetigt"].append(dom)
        elif existiert and not gefunden_laut_check:
            res["falscher_alarm"].append(dom)
        elif not existiert and gefunden_laut_check:
            res["verpasst"].append(dom)
        else:
            res["richtig_nicht_gefunden"].append(dom)
    return res


def feldebene(wahrheit: Dict[str, Any], issues_je_seite: Dict[str, List[Dict[str, Any]]],
              art: str, nur_sichere: bool = False) -> Dict[str, Dict[str, Any]]:
    """Behauptungen "X fehlt" gegen Etikett, nur auf Seiten, die beide gefunden haben."""
    seiten = seitenebene(wahrheit, issues_je_seite, art)["richtig_gefunden"]
    je_feld: Dict[str, Dict[str, Any]] = {}
    for dom in seiten:
        w = wahrheit["seiten"][dom][art]
        titel_zu_feld = FELD_TITEL[art]
        behauptet: Dict[str, int] = {}
        for i in issues_je_seite[dom]:
            f = titel_zu_feld.get(i["title"])
            if f:
                behauptet[f] = behauptet.get(f, 0) + int(i.get("risk_euro") or 0)
        for feld, vorhanden in w["felder"].items():
            if nur_sichere and feld in w.get("unsicher", []):
                continue
            z = je_feld.setdefault(feld, {"luecken": 0, "behauptet": 0, "richtig": 0, "falsch": 0,
                                          "falsch_euro": 0, "richtig_euro": 0, "falsch_seiten": [],
                                          "verpasst_seiten": []})
            luecke = not vorhanden
            if luecke:
                z["luecken"] += 1
            if feld in behauptet:
                z["behauptet"] += 1
                if luecke:
                    z["richtig"] += 1
                    z["richtig_euro"] += behauptet[feld]
                else:
                    z["falsch"] += 1
                    z["falsch_euro"] += behauptet[feld]
                    z["falsch_seiten"].append(dom)
            elif luecke:
                z["verpasst_seiten"].append(dom)
        # Behauptungen zu Feldern ohne Etikett (z. B. register bei Einzelunternehmen) zaehlen
        # als falsch: es gibt keine Pflicht, die fehlen koennte.
        for feld, euro in behauptet.items():
            if feld not in w["felder"]:
                z = je_feld.setdefault(feld, {"luecken": 0, "behauptet": 0, "richtig": 0, "falsch": 0,
                                              "falsch_euro": 0, "richtig_euro": 0, "falsch_seiten": [],
                                              "verpasst_seiten": []})
                z["behauptet"] += 1
                z["falsch"] += 1
                z["falsch_euro"] += euro
                z["falsch_seiten"].append(dom)
    return je_feld


def summe(je_feld: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    s = {"luecken": 0, "behauptet": 0, "richtig": 0, "falsch": 0, "falsch_euro": 0, "richtig_euro": 0}
    for z in je_feld.values():
        for k in s:
            s[k] += z[k]
    s["genauigkeit"] = round(100 * s["richtig"] / s["behauptet"]) if s["behauptet"] else None
    s["trefferquote"] = round(100 * s["richtig"] / s["luecken"]) if s["luecken"] else None
    return s


def auswerten(wahrheit: Dict[str, Any], lauf: Dict[str, Any], nur_sichere: bool = False) -> Dict[str, Any]:
    issues = messbare(lauf)
    out: Dict[str, Any] = {"seiten": sorted(set(issues) & set(wahrheit["seiten"]))}
    for art in ("impressum", "datenschutz"):
        out[art] = {
            "seite": seitenebene(wahrheit, issues, art),
            "feld": feldebene(wahrheit, issues, art, nur_sichere),
        }
        out[art]["summe"] = summe(out[art]["feld"])
    return out


def _quote(x: Optional[int]) -> str:
    return "  -" if x is None else f"{x:>3} %"


def bericht(ergebnisse: List[Tuple[str, Dict[str, Any]]], details: bool = False) -> str:
    z: List[str] = []
    n = len(ergebnisse[0][1]["seiten"]) if ergebnisse else 0
    z.append(f"Treffsicherheit gegen Etiketten, {n} Seiten")
    for art in ("impressum", "datenschutz"):
        z.append("")
        z.append(f"== {art.capitalize()}")
        z.append("Seitenebene (Rechtsseite gefunden?)")
        z.append(f"  {'Lauf':16}{'richtig':>9}{'falscher Alarm':>16}{'verpasst':>10}{'richtig fehlend':>17}{'unbestaetigt':>14}")
        for name, e in ergebnisse:
            s = e[art]["seite"]
            z.append(f"  {name:16}{len(s['richtig_gefunden']):>9}{len(s['falscher_alarm']):>16}"
                     f"{len(s['verpasst']):>10}{len(s['richtig_nicht_gefunden']):>17}{len(s['unbestaetigt']):>14}")
            if details:
                for k, label in (("falscher_alarm", "falscher Alarm"), ("verpasst", "verpasst")):
                    if s[k]:
                        z.append(f"      {label}: {', '.join(sorted(s[k]))}")
        z.append("Feldebene (stimmt ein \"X fehlt\"?), nur auf Seiten, die Etikett und Check gefunden haben")
        z.append(f"  {'Lauf':16}{'Luecken':>9}{'behauptet':>11}{'richtig':>9}{'falsch':>8}{'Genauigkeit':>13}{'Trefferquote':>14}{'falsch in EUR':>15}")
        for name, e in ergebnisse:
            s = e[art]["summe"]
            z.append(f"  {name:16}{s['luecken']:>9}{s['behauptet']:>11}{s['richtig']:>9}{s['falsch']:>8}"
                     f"{_quote(s['genauigkeit']):>13}{_quote(s['trefferquote']):>14}{s['falsch_euro']:>15,}".replace(",", "."))
        if details:
            for name, e in ergebnisse:
                for feld, f in sorted(e[art]["feld"].items()):
                    if f["falsch_seiten"] or f["verpasst_seiten"]:
                        z.append(f"      {name} {feld}: falsch auf {', '.join(sorted(f['falsch_seiten'])) or '-'}"
                                 f"; verpasst auf {', '.join(sorted(f['verpasst_seiten'])) or '-'}")
    return "\n".join(z)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--wahrheit", required=True)
    ap.add_argument("--lauf", action="append", required=True, metavar="NAME=PFAD")
    ap.add_argument("--streng", action="store_true", help="nur Felder ohne `unsicher`-Etikett")
    ap.add_argument("--details", action="store_true", help="Seiten je Fehler nennen")
    ap.add_argument("--json", action="store_true", help="Rohzahlen als JSON")
    args = ap.parse_args(argv)

    wahrheit = lade(args.wahrheit)
    ergebnisse = []
    for eintrag in args.lauf:
        name, _, pfad = eintrag.partition("=")
        ergebnisse.append((name, auswerten(wahrheit, lade(pfad), args.streng)))
    if args.json:
        print(json.dumps({n: e for n, e in ergebnisse}, ensure_ascii=False, indent=1))
    else:
        print(bericht(ergebnisse, args.details))
    return 0


if __name__ == "__main__":
    sys.exit(main())
