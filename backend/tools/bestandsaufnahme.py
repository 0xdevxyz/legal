#!/usr/bin/env python3
"""
Bestandsaufnahme: was ist auf echten deutschen KMU-Websites tatsaechlich kaputt?

Zweck ist nicht der Bericht, sondern die Bauentscheidung. Welche Fixes complyo
als naechstes mechanisch koennen muss, ergibt sich aus der Haeufigkeit im
echten Bestand — nicht aus der WCAG-Gliederung und nicht aus dem Bauchgefuehl.
Eine Regel, die auf 24 von 26 Seiten auftritt, ist mehr wert als drei, die je
einmal vorkommen.

Gemessen wird mit blockiertem complyo-Widget (sonst misst man den eigenen
Laufzeit-Fix mit) und zusaetzlich zu axe eine Reihe eigener Zaehlungen fuer
Luecken, die axe nicht als Verstoss fuehrt — allen voran `alt=""`, das
WordPress an jedes Bild ohne Mediathek-Alt-Text schreibt.

Aufruf im Backend-Container (Mount auf /src, nicht /app):
    python tools/bestandsaufnahme.py --datei sites.txt --out /out
"""
import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_IMG = re.compile(r"<img\b[^>]*>", re.I)
_ALT = re.compile(r"""(?<![\w-])alt\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_A_TAG = re.compile(r"<a\b[^>]*>(.*?)</a>", re.I | re.S)
_HREF = re.compile(r"""(?<![\w-])href\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_ARIA_LABEL = re.compile(r"""(?<![\w-])aria-label\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_TAGS_WEG = re.compile(r"<[^>]+>")

# Linktexte, die ueberall stehen und nirgends erklaeren, wohin sie fuehren.
_NICHTSSAGENDE_LINKS = {
    "hier", "hier klicken", "mehr", "mehr erfahren", "weiterlesen", "weiter",
    "read more", "click here", "link", "details", "info", "mehr lesen",
    "zum artikel", "artikel lesen", "jetzt", "los", "ansehen",
}


def eigene_zaehlung(html: str) -> Dict[str, int]:
    """Luecken, die axe nicht als Verstoss fuehrt, die BFSG aber betreffen."""
    bilder = _IMG.findall(html)
    stumm = 0
    for tag in bilder:
        m = _ALT.search(tag)
        if not m or not (m.group(1) or m.group(2) or "").strip():
            stumm += 1

    leere_links, vage_links, links = 0, 0, 0
    for treffer in _A_TAG.finditer(html):
        ganzer = treffer.group(0)
        if not _HREF.search(ganzer):
            continue
        links += 1
        text = _TAGS_WEG.sub(" ", treffer.group(1))
        text = re.sub(r"\s+", " ", text).strip().lower()
        aria = _ARIA_LABEL.search(ganzer)
        beschriftung = text or (aria.group(1) or aria.group(2) if aria else "") or ""
        if not beschriftung.strip():
            leere_links += 1
        elif beschriftung.strip(" .:!»›→>") in _NICHTSSAGENDE_LINKS:
            vage_links += 1

    return {
        "bilder": len(bilder),
        "bilder_stumm": stumm,
        "links": links,
        "links_ohne_text": leere_links,
        "links_vage": vage_links,
        "hat_lang": 1 if re.search(r"<html[^>]*\slang\s*=", html, re.I) else 0,
        "hat_main": 1 if re.search(r"<main\b|role\s*=\s*[\"']main[\"']", html, re.I) else 0,
        "hat_skiplink": 1 if re.search(r"skip[-_]?link|zum inhalt springen", html, re.I) else 0,
        "hat_title": 1 if re.search(r"<title[^>]*>\s*\S", html, re.I) else 0,
    }


async def hole_seite(url: str) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.route(
            re.compile(r"https?://api\.complyo\.(de|tech)/"),
            lambda route: asyncio.ensure_future(route.abort()),
        )
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            return await page.content()
        finally:
            await browser.close()


async def axe_auf_datei(pfad: str) -> Dict[str, Any]:
    from compliance_engine.axe_scanner import AxeScanner

    from compliance_engine.axe_scanner import ist_rechtspflicht

    ergebnis = await AxeScanner().scan_page(f"file://{os.path.abspath(pfad)}")
    regeln: Dict[str, Dict[str, Any]] = {}
    for v in ergebnis.violations:
        regeln[v.id] = {
            "knoten": len(v.nodes),
            "impact": v.impact,
            "pflicht": ist_rechtspflicht(v.tags),
            "wcag": [t for t in v.tags if t.startswith(("wcag", "best-practice"))],
        }
    return regeln


async def pruefe(url: str, ordner: str) -> Dict[str, Any]:
    html = await hole_seite(url)
    name = re.sub(r"[^a-z0-9.-]", "_", url.replace("https://", "").replace("http://", ""))
    datei = os.path.join(ordner, f"{name}.html")
    basis = re.match(r"(https?://[^/]+)", url).group(1) + "/"
    if "<base " not in html.lower():
        html = re.sub(r"(<head[^>]*>)", rf'\1<base href="{basis}">', html, count=1, flags=re.I)
    with open(datei, "w", encoding="utf-8") as fh:
        fh.write(html)

    return {"url": url, "axe": await axe_auf_datei(datei), "eigen": eigene_zaehlung(html)}


def bericht(seiten: List[Dict[str, Any]]) -> str:
    gueltig = [s for s in seiten if s.get("axe") is not None]
    n = len(gueltig)

    seiten_je_regel = Counter()
    knoten_je_regel = Counter()
    impact_je_regel = {}
    wcag_je_regel = {}
    for s in gueltig:
        for regel, d in s["axe"].items():
            seiten_je_regel[regel] += 1
            knoten_je_regel[regel] += d["knoten"]
            impact_je_regel[regel] = d["impact"]
            wcag_je_regel[regel] = "**Pflicht**" if d.get("pflicht") else "Empfehlung"

    z = [f"# Bestandsaufnahme — {n} echte deutsche KMU-Websites", "",
         f"Gemessen {datetime.now().strftime('%d.%m.%Y')} · axe-core 4.11.4 "
         f"(WCAG 2.1 AA + best-practice) · Startseite · complyo-Widget blockiert",
         "",
         "Zweck: entscheiden, welche Fixes complyo als naechstes mechanisch koennen",
         "muss. Sortiert nach Verbreitung, nicht nach WCAG-Nummer.", ""]

    pflicht_regeln = [r for r in seiten_je_regel if wcag_je_regel[r] == "**Pflicht**"]
    pflicht_knoten = sum(knoten_je_regel[r] for r in pflicht_regeln)
    empf_knoten = sum(knoten_je_regel[r] for r in seiten_je_regel) - pflicht_knoten

    z += [f"**{pflicht_knoten} Fundstellen sind WCAG-2.1-AA-Pflicht, "
          f"{empf_knoten} sind Empfehlungen.** Die Trennung ist wichtig: "
          f"`region` und `heading-order` sind keine BFSG-Verstoesse.", "",
          "## Was axe findet", "",
          "| axe-Regel | Seiten | Anteil | Fundstellen | Schwere | Rang |",
          "|---|---:|---:|---:|---|---|"]
    for regel, seitenzahl in seiten_je_regel.most_common():
        z.append(f"| `{regel}` | {seitenzahl} | {round(100*seitenzahl/n)} % | "
                 f"{knoten_je_regel[regel]} | {impact_je_regel[regel]} | "
                 f"{wcag_je_regel[regel]} |")

    e = defaultdict(int)
    for s in gueltig:
        for k, v in s["eigen"].items():
            e[k] += v
    ohne_lang = sum(1 for s in gueltig if not s["eigen"]["hat_lang"])
    ohne_main = sum(1 for s in gueltig if not s["eigen"]["hat_main"])
    ohne_skip = sum(1 for s in gueltig if not s["eigen"]["hat_skiplink"])
    ohne_titel = sum(1 for s in gueltig if not s["eigen"]["hat_title"])
    mit_stummen = sum(1 for s in gueltig if s["eigen"]["bilder_stumm"] > 0)
    mit_vagen = sum(1 for s in gueltig if s["eigen"]["links_vage"] > 0)
    mit_leeren = sum(1 for s in gueltig if s["eigen"]["links_ohne_text"] > 0)

    z += ["", "## Was axe nicht findet", "",
          "Diese Luecken bestehen jede axe-Pruefung und betreffen Nutzer trotzdem.",
          "`alt=\"\"` gilt fuer axe als bewusste Dekorativ-Markierung — WordPress",
          "schreibt es aber an jedes Bild ohne Mediathek-Alt-Text.", "",
          "| Luecke | betroffene Seiten | Anteil | Fundstellen gesamt |",
          "|---|---:|---:|---:|",
          f"| Bilder ohne Textalternative | {mit_stummen} | {round(100*mit_stummen/n)} % | {e['bilder_stumm']} von {e['bilder']} Bildern |",
          f"| Links ohne erkennbaren Text | {mit_leeren} | {round(100*mit_leeren/n)} % | {e['links_ohne_text']} |",
          f"| Links mit nichtssagendem Text | {mit_vagen} | {round(100*mit_vagen/n)} % | {e['links_vage']} |",
          f"| kein `lang` am `<html>` | {ohne_lang} | {round(100*ohne_lang/n)} % | — |",
          f"| kein `<main>`-Landmark | {ohne_main} | {round(100*ohne_main/n)} % | — |",
          f"| kein Sprunglink | {ohne_skip} | {round(100*ohne_skip/n)} % | — |",
          f"| kein Seitentitel | {ohne_titel} | {round(100*ohne_titel/n)} % | — |",
          ""]

    def pflicht_von(seite):
        return sum(d["knoten"] for d in seite["axe"].values() if d.get("pflicht"))

    z += ["## Je Seite", "",
          "| Seite | Pflicht-Verstoesse | Empfehlungen | stumme Bilder |",
          "|---|---:|---:|---:|"]
    for s in sorted(gueltig, key=lambda x: -pflicht_von(x)):
        gesamt = sum(d["knoten"] for d in s["axe"].values())
        z.append(f"| {s['url'].replace('https://','')} | {pflicht_von(s)} | "
                 f"{gesamt - pflicht_von(s)} | {s['eigen']['bilder_stumm']} |")

    fehler = [s for s in seiten if s.get("axe") is None]
    if fehler:
        z += ["", "## Nicht erreichbar", ""]
        z += [f"- {s['url']} — {s.get('fehler')}" for s in fehler]
    return "\n".join(z)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", required=True, help="Datei mit einer URL je Zeile")
    ap.add_argument("--out", default="/out")
    args = ap.parse_args()

    with open(args.datei, encoding="utf-8") as fh:
        urls = [z.strip() for z in fh if z.strip() and not z.startswith("#")]

    os.makedirs(args.out, exist_ok=True)
    seiten = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}", flush=True)
        try:
            seiten.append(await pruefe(url, args.out))
        except Exception as e:
            print(f"    Fehler: {e}", flush=True)
            seiten.append({"url": url, "axe": None, "fehler": str(e)[:150]})

    with open(os.path.join(args.out, "bestand.json"), "w", encoding="utf-8") as fh:
        json.dump(seiten, fh, ensure_ascii=False, indent=2)
    ziel = os.path.join(args.out, "BESTANDSAUFNAHME.md")
    with open(ziel, "w", encoding="utf-8") as fh:
        fh.write(bericht(seiten))
    print(f"\nBericht: {ziel}")


if __name__ == "__main__":
    asyncio.run(main())
