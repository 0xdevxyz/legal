#!/usr/bin/env python3
"""
Vorher/Nachher-Fälle: gemessener Beleg, dass complyo repariert statt anzuzeigen.

Warum dieses Werkzeug
---------------------
Der Satz "andere sagen dir, was falsch ist — complyo repariert es" ist die
einzige Aussage, die complyo von Cookiebot, Usercentrics und Hugo trennt.
Solange sie nur behauptet wird, ist sie im Verkaufsgespraech nichts wert.
Dieses Skript belegt sie mit gemessenen Zahlen: dieselbe Seite, derselbe
Pruefer, einmal vor und einmal nach dem mechanischen Fix.

Fairness der Messung
--------------------
Vorher und Nachher werden unter IDENTISCHEN Bedingungen gemessen: beide aus
einer lokalen Datei, beide mit <base href> auf die Originaldomain, damit CSS,
Schriften und Bilder in beiden Laeufen gleich laden. Ein Vergleich "Live-URL
vorher gegen Datei nachher" waere geschoent — Kontrastregeln haetten im
Nachher-Lauf schlicht kein CSS zu pruefen.

Der Fix-Schritt ist derselbe Produktionscode, den auch der PR-Knopf benutzt
(fix_patch_builder.baue_patches). Kein Sonderweg fuer die Demo.

Aufruf (im Backend-Container):
    python tools/vorher_nachher.py --site-id spedition-mahn-de \\
        --url https://spedition-mahn.de --status pending
    python tools/vorher_nachher.py --alle --out /tmp/faelle
"""
import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Derselbe Filter, den auch der PR-Weg benutzt — der Bericht darf keine
# Vorschlaege zaehlen, die der Builder anschliessend verwirft.
from fix_patch_builder import baue_patches, ist_nichtssagend  # noqa: E402


async def seite_als_datei(url: str, ziel: str, ohne_widget: bool = True) -> str:
    """Rendert die Live-Seite und legt sie als eigenstaendige HTML-Datei ab.

    <base href> wird eingefuegt, damit relative Pfade weiterhin auf die
    Originaldomain zeigen — sonst waere der Nachher-Lauf ohne CSS und die
    Kontrastregeln wuerden grundlos "besser" aussehen.

    `ohne_widget` blockiert das complyo-Laufzeit-Widget. Ohne diese Sperre ist
    die Messung auf jeder Seite wertlos, auf der complyo schon laeuft: das
    Widget repariert mit `data-auto-fix` im Browser, das "Vorher" waere also
    bereits ein "Nachher" und der Fall zeigte null Verbesserung. Genau das ist
    beim ersten Lauf auf zua-zwickau.de passiert.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        if ohne_widget:
            await page.route(
                re.compile(r"https?://api\.complyo\.(de|tech)/"),
                lambda route: asyncio.ensure_future(route.abort()),
            )
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            try:
                await page.wait_for_load_state("networkidle", timeout=6000)
            except Exception:
                pass
            html = await page.content()
        finally:
            await browser.close()

    basis = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
    if "<base " not in html.lower():
        html = re.sub(r"(<head[^>]*>)", rf'\1<base href="{basis}">', html, count=1, flags=re.I)

    with open(ziel, "w", encoding="utf-8") as fh:
        fh.write(html)
    return html


_IMG = re.compile(r"<img\b[^>]*>", re.I)
_SRC = re.compile(r"""(?<![\w-])src\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_ALT = re.compile(r"""(?<![\w-])alt\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)


def bildlage(html: str) -> Dict[str, int]:
    """
    Zaehlt Bilder ohne nutzbare Textalternative.

    Diese Kennzahl braucht es, weil axe die eigentliche Arbeit nicht sieht:
    `alt=""` ist fuer axe ein gueltiges Ergebnis (dekoratives Bild), und
    WordPress setzt es an jedes Bild ohne hinterlegten Alt-Text. Auf
    spedition-mahn.de standen so 20 von 37 Bildern stumm da, ohne dass axe
    einen einzigen Verstoss meldete. Wer nur axe-Zahlen vergleicht, misst
    ausgerechnet den Teil nicht, der Nutzern am meisten bringt — und
    unterschaetzt die eigene Leistung.
    """
    bilder = _IMG.findall(html)
    ohne, leer, echt = 0, 0, 0
    for tag in bilder:
        m = _ALT.search(tag)
        if not m:
            ohne += 1
        elif not (m.group(1) or m.group(2) or "").strip():
            leer += 1
        else:
            echt += 1
    return {"bilder": len(bilder), "ohne_alt": ohne, "leeres_alt": leer,
            "mit_alt_text": echt, "stumm": ohne + leer}


async def scanne_datei(pfad: str) -> Dict[str, Any]:
    """axe-core auf eine lokale Datei — derselbe Scanner wie im Produkt."""
    from compliance_engine.axe_scanner import AxeScanner

    scanner = AxeScanner()
    ergebnis = await scanner.scan_page(f"file://{os.path.abspath(pfad)}")

    nach_regel: Dict[str, int] = {}
    for v in ergebnis.violations:
        nach_regel[v.id] = nach_regel.get(v.id, 0) + len(v.nodes)
    return {
        "verstoesse_gesamt": sum(nach_regel.values()),
        "regeln": nach_regel,
        "kritisch": sum(
            len(v.nodes) for v in ergebnis.violations if v.impact in ("critical", "serious")
        ),
    }


async def lade_manifest(site_id: str, status: str) -> Dict[str, List[Dict[str, Any]]]:
    """Freigegebene (bzw. vorgeschlagene) Fixes aus der echten Datenbank."""
    import asyncpg

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL fehlt — im Backend-Container ausfuehren.")
    conn = await asyncpg.connect(dsn)
    try:
        alt = await conn.fetch(
            "SELECT image_src, image_filename, suggested_alt, confidence "
            "FROM accessibility_alt_text_fixes WHERE site_id = $1 AND status = $2",
            site_id, status,
        )
        doc = await conn.fetch(
            "SELECT fix_type, payload, wcag_criterion FROM accessibility_document_fixes "
            "WHERE site_id = $1 AND status = 'approved'",
            site_id,
        )
    finally:
        await conn.close()

    def entpacke(p):
        return json.loads(p) if isinstance(p, str) else (p or {})

    return {
        "alt_texts": [dict(r) for r in alt],
        "document_fixes": [
            {"fix_type": r["fix_type"], "payload": entpacke(r["payload"]),
             "wcag_criterion": r["wcag_criterion"]}
            for r in doc
        ],
    }


async def erzeuge_vorschlaege(html: str, seiten_url: str, grenze: int) -> List[Dict[str, Any]]:
    """
    Erzeugt Alt-Text-Vorschlaege fuer stumme Bilder — echte Claude Vision,
    derselbe Generator wie im Produkt.

    Damit laesst sich fuer jede Kundenseite ein Fall bauen, auch wenn noch kein
    Scan gelaufen ist. Die Vorschlaege bleiben im Arbeitsspeicher: ein Bericht
    darf keine Eintraege in der Fix-Tabelle hinterlassen, die niemand
    freigegeben hat.
    """
    from compliance_engine.ai_alt_text_generator import AIAltTextGenerator

    generator = AIAltTextGenerator()
    stumm = []
    for tag in _IMG.findall(html):
        m = _ALT.search(tag)
        if m and (m.group(1) or m.group(2) or "").strip():
            continue
        src = _SRC.search(tag)
        if not src:
            continue
        absolut = urljoin(seiten_url, src.group(1) or src.group(2) or "")
        if absolut.startswith(("http://", "https://")) and absolut not in stumm:
            stumm.append(absolut)

    stumm = stumm[:grenze]
    print(f"  {len(stumm)} stumme Bilder -> Claude Vision")

    vorschlaege = []
    for i, bild_url in enumerate(stumm, 1):
        try:
            res = await generator.generate_alt_text(image_url=bild_url, language="de")
        except Exception as e:
            print(f"    [{i}/{len(stumm)}] Fehler: {e}")
            continue
        if res and res.get("source") == "claude_vision" and res.get("alt_text"):
            vorschlaege.append({
                "image_src": bild_url,
                "image_filename": bild_url.rsplit("/", 1)[-1],
                "suggested_alt": res["alt_text"],
                "confidence": float(res.get("confidence", 0.9)),
            })
        else:
            print(f"    [{i}/{len(stumm)}] kein Vision-Ergebnis ({res.get('source')})")
    return vorschlaege


async def erzeuge_fall(site_id: str, url: str, status: str, ordner: str,
                       generiere: int = 0) -> Dict[str, Any]:
    os.makedirs(ordner, exist_ok=True)
    name = site_id.replace("/", "-")
    vorher_datei = os.path.join(ordner, f"{name}.vorher.html")
    nachher_datei = os.path.join(ordner, f"{name}.nachher.html")

    print(f"  Seite holen … {url} (complyo-Widget blockiert)")
    html = await seite_als_datei(url, vorher_datei, ohne_widget=True)

    if generiere:
        manifest = {"alt_texts": await erzeuge_vorschlaege(html, url, generiere),
                    "document_fixes": []}
    else:
        manifest = await lade_manifest(site_id, status)

    # Nichtssagende Vorschlaege aussortieren UND ausweisen — sie zu verschweigen
    # waere genau die Art von Schoenrechnerei, die dieser Bericht widerlegen soll.
    brauchbar, verworfen = [], []
    for fix in manifest["alt_texts"]:
        (verworfen if ist_nichtssagend(fix.get("suggested_alt")) else brauchbar).append(fix)
    manifest["alt_texts"] = brauchbar

    print(f"  Manifest: {len(brauchbar)} brauchbare Alt-Texte, "
          f"{len(verworfen)} nichtssagend verworfen, "
          f"{len(manifest['document_fixes'])} dokumentweite Fixes")

    print("  Vorher messen …")
    vorher = await scanne_datei(vorher_datei)
    vorher["bilder"] = bildlage(html)

    patches = baue_patches(manifest, {os.path.basename(vorher_datei): html})
    neu_html = patches[0]["new_content"] if patches else html
    beschreibung = patches[0]["description"] if patches else "keine Aenderung"
    with open(nachher_datei, "w", encoding="utf-8") as fh:
        fh.write(neu_html)

    print("  Nachher messen …")
    nachher = await scanne_datei(nachher_datei)
    nachher["bilder"] = bildlage(neu_html)

    behoben = {
        regel: vorher["regeln"].get(regel, 0) - nachher["regeln"].get(regel, 0)
        for regel in sorted(set(vorher["regeln"]) | set(nachher["regeln"]))
        if vorher["regeln"].get(regel, 0) != nachher["regeln"].get(regel, 0)
    }

    return {
        "site_id": site_id,
        "url": url,
        "gemessen_am": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "manifest_status": status,
        "alt_texte_brauchbar": len(brauchbar),
        "alt_texte_verworfen": [
            {"datei": f.get("image_filename"), "vorschlag": f.get("suggested_alt"),
             "confidence": float(f.get("confidence") or 0)}
            for f in verworfen
        ],
        "aenderung": beschreibung,
        "vorher": vorher,
        "nachher": nachher,
        "differenz_je_regel": behoben,
        "dateien": {"vorher": vorher_datei, "nachher": nachher_datei},
    }


def als_markdown(faelle: List[Dict[str, Any]]) -> str:
    z = ["# Vorher / Nachher — gemessene Fixes", "",
         f"Erzeugt {datetime.now().strftime('%d.%m.%Y')} · Pruefer: axe-core 4.11.4 (WCAG 2.1 AA + best-practice)",
         "", "Beide Messungen laufen unter identischen Bedingungen (lokale Kopie der",
         "gerenderten Seite, `<base href>` auf die Originaldomain). Der Fix-Schritt ist",
         "derselbe Produktionscode wie hinter dem PR-Knopf.",
         "",
         "Das complyo-Laufzeit-Widget ist bei der Aufnahme **blockiert**. Sonst haette",
         "es die Seite im Browser bereits repariert und das \"Vorher\" waere geschoent —",
         "gemessen wird der Zustand, den ein Besucher ohne complyo vorfindet.", "",
         "## Bilder ohne Textalternative",
         "",
         "Die Kennzahl, um die es beim BFSG geht: wie viele Bilder ein",
         "Screenreader stumm uebergeht. `alt=\"\"` zaehlt hier als stumm — axe",
         "wertet es als gueltig, WordPress setzt es aber an jedes Bild ohne",
         "hinterlegten Alt-Text.",
         "",
         "| Seite | Bilder | stumm vorher | stumm nachher | beschrieben |",
         "|---|---:|---:|---:|---:|"]
    for f in faelle:
        vb, nb = f["vorher"].get("bilder", {}), f["nachher"].get("bilder", {})
        z.append(f"| {f['site_id']} | {vb.get('bilder', 0)} | {vb.get('stumm', 0)} | "
                 f"{nb.get('stumm', 0)} | {vb.get('stumm', 0) - nb.get('stumm', 0)} |")
    z += ["", "## axe-core-Verstoesse", "",
          "Zum Vergleich das Standardmass. Es bewegt sich durch Alt-Texte kaum —",
          "axe prueft die Existenz des Attributs, nicht ob der Text etwas sagt.",
          "",
          "| Seite | Verstoesse vorher | nachher | behoben | davon kritisch/ernst |",
          "|---|---:|---:|---:|---:|"]
    for f in faelle:
        v, n = f["vorher"], f["nachher"]
        z.append(f"| {f['site_id']} | {v['verstoesse_gesamt']} | {n['verstoesse_gesamt']} | "
                 f"{v['verstoesse_gesamt'] - n['verstoesse_gesamt']} | "
                 f"{v['kritisch'] - n['kritisch']} |")
    z += ["", "## Je Fall", ""]
    for f in faelle:
        vb, nb = f["vorher"].get("bilder", {}), f["nachher"].get("bilder", {})
        z += [f"### {f['site_id']} — {f['url']}", "",
              f"- gemessen: {f['gemessen_am']} · Manifest-Status: `{f['manifest_status']}`",
              f"- angewendet: {f['aenderung']}",
              f"- Bilder: {vb.get('bilder', 0)} gesamt · stumm {vb.get('stumm', 0)} → "
              f"{nb.get('stumm', 0)} (davon leeres `alt` vorher: {vb.get('leeres_alt', 0)})",
              f"- brauchbare Alt-Text-Vorschlaege: {f['alt_texte_brauchbar']}"]
        if f["alt_texte_verworfen"]:
            z.append(f"- **verworfen (nichtssagend): {len(f['alt_texte_verworfen'])}** — "
                     + ", ".join(f'`{v["vorschlag"]}`' for v in f["alt_texte_verworfen"][:5]))
        if f["differenz_je_regel"]:
            z += ["", "| axe-Regel | vorher | nachher |", "|---|---:|---:|"]
            for regel, _ in f["differenz_je_regel"].items():
                z.append(f"| `{regel}` | {f['vorher']['regeln'].get(regel, 0)} "
                         f"| {f['nachher']['regeln'].get(regel, 0)} |")
        elif vb.get("stumm", 0) > nb.get("stumm", 0):
            z.append("- axe-Regeln unveraendert — die Verbesserung liegt in den "
                     "Alt-Texten, die axe nicht bewertet")
        else:
            z.append("- keine Aenderung")
        z.append("")
    return "\n".join(z)


# Die Standard-Fallsammlung. Reihenfolge ist Absicht: erst der eigene Auftritt
# (frei verwendbar, keine Kundenfreigabe noetig), dann die Kundenseiten.
# `status` liest geprueft Freigegebenes aus der Datenbank, `generiere` erzeugt
# Vorschlaege frisch — noetig fuer Seiten, fuer die noch kein Scan lief.
ALLE = [
    {"site_id": "panoart360-de", "url": "https://panoart360.de", "generiere": 20},
    {"site_id": "spedition-mahn-de", "url": "https://spedition-mahn.de", "status": "pending"},
    {"site_id": "ferienpark-waldenburg-de", "url": "https://ferienpark-waldenburg.de", "generiere": 20},
    {"site_id": "zua-zwickau-de", "url": "https://zua-zwickau.de", "status": "approved"},
]


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-id")
    ap.add_argument("--url")
    ap.add_argument("--status", default="approved",
                    help="Manifest-Status: approved (echt) oder pending (Vorschau)")
    ap.add_argument("--alle", action="store_true")
    ap.add_argument("--generiere", type=int, default=0,
                    help="Alt-Texte fuer bis zu N stumme Bilder frisch erzeugen "
                         "(Claude Vision) statt aus der Datenbank zu lesen")
    ap.add_argument("--out", default="/tmp/vorher-nachher")
    ap.add_argument("--nur-bericht", action="store_true",
                    help="Bericht aus vorhandener faelle.json neu schreiben, "
                         "ohne erneut zu scannen oder zu generieren")
    args = ap.parse_args()

    if args.nur_bericht:
        with open(os.path.join(args.out, "faelle.json"), encoding="utf-8") as fh:
            faelle = json.load(fh)
        ziel = os.path.join(args.out, "VORHER-NACHHER.md")
        with open(ziel, "w", encoding="utf-8") as fh:
            fh.write(als_markdown(faelle))
        print(f"Bericht: {ziel}")
        return

    if args.alle:
        ziele = ALLE
    else:
        if not (args.site_id and args.url):
            raise SystemExit("--site-id und --url noetig, oder --alle")
        ziele = [{"site_id": args.site_id, "url": args.url,
                  "status": args.status, "generiere": args.generiere}]

    faelle = []
    for ziel in ziele:
        print(f"\n{ziel['site_id']}")
        try:
            faelle.append(await erzeuge_fall(
                ziel["site_id"], ziel["url"],
                ziel.get("status", "approved"), args.out,
                generiere=ziel.get("generiere", 0),
            ))
        except Exception as e:
            print(f"  uebersprungen: {e}")

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "faelle.json"), "w", encoding="utf-8") as fh:
        json.dump(faelle, fh, ensure_ascii=False, indent=2)
    bericht = os.path.join(args.out, "VORHER-NACHHER.md")
    with open(bericht, "w", encoding="utf-8") as fh:
        fh.write(als_markdown(faelle))
    print(f"\nBericht: {bericht}")


if __name__ == "__main__":
    asyncio.run(main())
