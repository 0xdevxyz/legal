# -*- coding: utf-8 -*-
"""Was complyo in fremde Seiten schreibt, darf dort keine Verstoesse erzeugen.

Am 09.09.2026 brachte der eigene Cookie-Banner fuenf Kontrastverstoesse auf
jede Seite mit, auf der er lief. Gefunden wurde das nur zufaellig, weil ein
Scan zum ersten Mal MIT eigenem Widget gemessen hat — der regulaere Scan blockt
api.complyo.de und ist fuer die eigenen Fehler blind.

complyo verkauft Barrierefreiheit. Ein Werkzeug dieses Anbieters, das selbst
Verstoesse einschleppt, ist der teuerste denkbare Schaden: er trifft jede
Kundenseite gleichzeitig und faellt beim Kunden auf, nicht bei uns.

Dieser Waechter misst deshalb VOR der Auslieferung, aus dem Arbeitsbaum:

    1. Eine leere, saubere Traegerseite wird gemessen. Findet axe dort etwas,
       taugt der Vergleich nicht und der Test sagt das.
    2. Dieselbe Seite mit den ausgelieferten Widgets wird gemessen.
    3. Jeder Befund, der erst durch complyo dazukommt, laesst den Test fallen.

Zwei Fallen, in die der erste Anlauf hineingelaufen ist — beide stehen hier,
weil sie sich sonst wiederholen:

* Der Konfigurations-Stub antwortete mit `{config: ...}`, gelesen wird aber
  `data.data`. Ohne Konfiguration sind keine Services gesetzt, und ohne
  Services haelt sich der Banner absichtlich zurueck. Der Test mass eine leere
  Seite und war gruen. Deshalb prueft er jetzt die SICHTBARKEIT, bevor er
  misst — und faellt, statt zu ueberspringen.
* Eine erste Probe suchte die Marker per Zeichenkette im Seitenquelltext. Die
  stehen aber schon im Widget-Quelltext selbst, den die Seite ja enthaelt.
  Alles "gefunden", nichts gerendert. Gemessen wird nur ueber das DOM.

Gemessen wird in ZWEI Zustaenden. Der geschlossene Zustand ist der, den
jeder Besucher sieht; der aufgeklappte ist der, in dem ein Fehler am
laengsten unentdeckt bleibt, weil ihn nur sieht, wer den Dialog oeffnet.
Aufgeklappt heisst hier: Einstellungsdialog des Banners, Bedienfeld des
Barrierefreiheits-Widgets, dessen Text-Dialog und die Seitenstruktur-Flaeche.

Gegenprobe: baut man den behobenen Fehler wieder ein, faellt
`test_widgets_bringen_nichts_mit`.
"""

import asyncio
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WIDGETS = os.path.join(BACKEND, "widgets")

# Was complyo in Kundenseiten injiziert und was dabei sichtbare Oberflaeche
# erzeugt. content_blocker.js und a11y_remediation.js stehen bewusst nicht
# hier: sie zeichnen nichts Eigenes, sie veraendern Fremdinhalt.
OBERFLAECHEN = [
    ("cookie_banner_v2.js", {"data-site-id": "waechter"}),
    ("accessibility-v6.js", {"data-site-id": "waechter", "data-complyo-a11y": "1"}),
]

# Muss nach dem Laden sichtbar sein. Ist es das nicht, hat der Test nichts
# gemessen und darf nicht gruen sein.
PFLICHT_SICHTBAR = [".complyo-banner-layout, .complyo-box-layout", "#complyo-settings",
                    ".complyo-footer a", ".complyo-branding-prefix",
                    ".complyo-toggle-btn"]

# Zwei Paletten: die Voreinstellung und die, an der es wirklich gescheitert
# ist. Eine einzige Palette zu pruefen hiesse, den naechsten Kunden mit
# anderer Markenfarbe wieder dem Zufall zu ueberlassen.
PALETTEN = {
    "voreinstellung": {},
    "complyo-de": {"primary_color": "#25bac8", "accent_color": "#00fff7",
                   "text_color": "#134e4a", "bg_color": "#f0fdfa"},
}

# Die Flaechen, die erst auf Klick entstehen. Je Eintrag: worauf geklickt
# wird und was danach sichtbar sein MUSS. Ist es das nicht, hat der Test den
# Dialog nicht geoeffnet und misst die Seite darunter, also nichts.
#
# Je Zustand hoechstens EIN Dialog. Gestapelt scheitert der zweite Klick am
# Hintergrund des ersten: der faengt ihn ab, und Playwright wartet, bis die
# Zeit ablaeuft. Das war der erste Anlauf, und er sah aus wie ein Fehler im
# Widget, war aber einer im Waechter.
ZUSTAENDE = {
    "geschlossen": [],
    "banner-einstellungen": [
        ("#complyo-settings", "#complyo-settings-modal"),
    ],
    "a11y-bedienfeld": [
        (".complyo-toggle-btn", "#complyo-panel"),
    ],
    "a11y-textdialog": [
        (".complyo-toggle-btn", "#complyo-panel"),
        ('#complyo-a11y-widget [data-feature="fontSize"]',
         "#complyo-text-settings-modal"),
    ],
    "a11y-seitenstruktur": [
        (".complyo-toggle-btn", "#complyo-panel"),
        ('#complyo-a11y-widget [data-feature="pageStructure"]',
         "#complyo-page-structure-overlay"),
    ],
}

AUFGEKLAPPT = [z for z in ZUSTAENDE if z != "geschlossen"]

# `optout_center.js` ist seit mindestens Juli 2026 tot: keine Backend-Route
# liefert es aus, kein Konsument laedt es, die Opt-out-Funktion steckt im
# Banner. Es hier trotzdem zu messen waere Theater. Ein Waechter, der toten
# Code prueft, faerbt die Suite rot, wenn jemand an einer Datei etwas findet,
# die niemand ausliefert.
#
# Was stattdessen bewacht wird: die Annahme selbst. Sobald die Datei wieder
# irgendwo referenziert wird, MUSS sie in OBERFLAECHEN stehen. Das ist der
# Moment, in dem die Messung faellig wird, und genau dann faellt der Test.
UNAUSGELIEFERT = "optout_center.js"

TRAEGERSEITE = """<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><title>Traegerseite</title></head>
<body>
<main>
<h1>Traegerseite</h1>
<p>Diese Seite ist absichtlich leer und barrierefrei. Alles, was axe hier
findet, stammt von complyo.</p>
</main>
__EINBAU__
</body>
</html>
"""


def _stub(palette: dict) -> str:
    """Beantwortet Konfigurationsabrufe im Dokument selbst.

    Der Waechter soll den Quelltext pruefen, nicht die Erreichbarkeit der
    Produktion. `is_active` und ein Service sind noetig, sonst zeigt der Banner
    sich zu Recht gar nicht.
    """
    daten = {"is_active": True, "services": ["google-analytics"],
             "show_branding": True, **palette}
    return (
        "<script>(function () {\n"
        f"  const daten = {json.dumps(daten)};\n"
        "  const antwort = (k) => new Response(JSON.stringify(k), "
        "{ status: 200, headers: { 'Content-Type': 'application/json' } });\n"
        "  window.fetch = function (eingabe) {\n"
        "    const url = String((eingabe && eingabe.url) || eingabe || '');\n"
        "    if (url.includes('/config/')) return Promise.resolve(antwort({ success: true, data: daten }));\n"
        "    return Promise.resolve(antwort({ success: true, data: {}, services: [] }));\n"
        "  };\n"
        "})();</script>"
    )


def _seite(mit_widgets: bool, palette: dict) -> str:
    if not mit_widgets:
        return TRAEGERSEITE.replace("__EINBAU__", "")
    teile = [_stub(palette)]
    for datei, attrs in OBERFLAECHEN:
        quelle = open(os.path.join(WIDGETS, datei), encoding="utf-8").read()
        merkmale = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        teile.append(f"<script {merkmale}>\n{quelle}\n</script>")
    return TRAEGERSEITE.replace("__EINBAU__", "\n".join(teile))


async def _messen(html: str, aufklappen=()) -> dict:
    from playwright.async_api import async_playwright
    from compliance_engine.axe_scanner import AXE_CORE_JS

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as f:
        f.write(html)
        pfad = f.name
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(args=["--no-sandbox"])
            seite = await (await browser.new_context()).new_page()
            await seite.goto(f"file://{pfad}", wait_until="domcontentloaded")
            await seite.wait_for_timeout(3500)

            # Erst die Pflichtflaechen des geschlossenen Zustands pruefen,
            # dann aufklappen: wer auf einen Knopf klickt, den es nicht gibt,
            # soll das hier lesen und nicht in einer leeren Messung enden.
            geoeffnet = []
            for klick, erwartet in aufklappen:
                knopf = await seite.query_selector(klick)
                if knopf is None:
                    raise AssertionError(
                        f"Bedienelement {klick} fehlt — der Dialog konnte nicht "
                        "geoeffnet werden, gemessen waere die Seite darunter."
                    )
                await knopf.click()
                await seite.wait_for_timeout(600)
                geoeffnet.append(erwartet)

            sichtbar = await seite.evaluate(
                """(auswahl) => Object.fromEntries(auswahl.map((s) => {
                    const e = document.querySelector(s);
                    if (!e) return [s, false];
                    const cs = getComputedStyle(e);
                    const r = e.getBoundingClientRect();
                    return [s, cs.display !== 'none' && cs.visibility !== 'hidden'
                               && r.width > 0 && r.height > 0];
                }))""",
                (PFLICHT_SICHTBAR if not geoeffnet else geoeffnet),
            )

            await seite.evaluate(AXE_CORE_JS)
            roh = await seite.evaluate(
                "async () => (await axe.run(document, { runOnly: { type: 'tag',"
                " values: ['wcag2a','wcag2aa','wcag21a','wcag21aa'] } })).violations"
            )
            await browser.close()

        zaehlung = {}
        for v in roh or []:
            zaehlung[v["id"]] = zaehlung.get(v["id"], 0) + max(1, len(v.get("nodes") or []))
        return {"befunde": zaehlung, "sichtbar": sichtbar}
    finally:
        os.unlink(pfad)


def _lauf(mit_widgets: bool, palette: dict, aufklappen=()) -> dict:
    return asyncio.new_event_loop().run_until_complete(
        _messen(_seite(mit_widgets, palette), aufklappen)
    )


_LEER: dict = {}


def _leermessung() -> dict:
    """Die leere Traegerseite aendert sich zwischen den Faellen nicht.

    Sie je Fall neu zu messen kostete einen Browserstart pro Zustand und
    Palette, bei zehn Faellen also neun umsonst.
    """
    if not _LEER:
        _LEER.update(_lauf(False, {})["befunde"])
    return _LEER


axe_da = pytest.mark.skipif(
    not os.path.isfile(os.path.join(BACKEND, "compliance_engine", "vendor", "axe.min.js")),
    reason="axe-core Bundle fehlt",
)


@axe_da
class TestEigeneOberflaechen:
    def test_traegerseite_ist_sauber(self):
        """Ohne das ist jeder Vergleich wertlos."""
        leer = _lauf(False, {})
        assert leer["befunde"] == {}, f"Traegerseite nicht sauber: {leer['befunde']}"

    @pytest.mark.parametrize("zustand", sorted(ZUSTAENDE))
    @pytest.mark.parametrize("name", sorted(PALETTEN))
    def test_widgets_bringen_nichts_mit(self, name, zustand):
        palette = PALETTEN[name]
        mit = _lauf(True, palette, ZUSTAENDE[zustand])

        fehlend = [s for s, ok in mit["sichtbar"].items() if not ok]
        assert not fehlend, (
            f"[{name}/{zustand}] Nichts gemessen — diese Elemente sind nicht "
            f"sichtbar: {fehlend}. Ein Waechter, der eine leere Seite misst, "
            "ist schlimmer als keiner."
        )

        leer = _leermessung()
        neu = {r: n - leer.get(r, 0) for r, n in mit["befunde"].items()
               if n > leer.get(r, 0)}
        assert not neu, (
            f"[{name}/{zustand}] complyo bringt Verstoesse in die Seite ein: "
            + ", ".join(f"{r} (+{n})" for r, n in sorted(neu.items()))
        )

    @pytest.mark.parametrize("zustand", AUFGEKLAPPT)
    def test_dialog_ist_wirklich_offen(self, zustand):
        """Ohne das koennte das Aufklappen still ausfallen.

        Klickt der Waechter ins Leere oder schliesst ein Dialog sich sofort
        wieder, sieht die Messung aus wie der geschlossene Zustand und meldet
        trotzdem gruen: ein Zustand, den niemand geprueft hat, sieht dann
        genauso gruen aus wie einer, der sauber ist.
        """
        auf = _lauf(True, PALETTEN["complyo-de"], ZUSTAENDE[zustand])
        erwartet = [s for _, s in ZUSTAENDE[zustand]]
        fehlend = [s for s in erwartet if not auf["sichtbar"].get(s)]
        assert not fehlend, (
            f"[{zustand}] geklickt, aber nicht sichtbar: {fehlend}"
        )


class TestUnausgelieferteOberflaeche:
    """Tote Widget-Dateien werden nicht gemessen, aber ihr Tod wird bewacht."""

    def test_optout_center_bleibt_unausgeliefert_oder_wird_gemessen(self):
        wurzel = os.path.abspath(os.path.join(BACKEND, ".."))
        treffer = []
        for ordner, unter, dateien in os.walk(wurzel):
            unter[:] = [u for u in unter if u not in {
                ".git", "node_modules", ".next", "__pycache__", "venv",
                ".venv", "dist", "build", "vendor", "tests"}]
            for datei in dateien:
                if not datei.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".php")):
                    continue
                voll = os.path.join(ordner, datei)
                if os.path.samefile(os.path.dirname(voll), WIDGETS) and datei == UNAUSGELIEFERT:
                    continue  # die Datei selbst darf sich nennen
                try:
                    inhalt = open(voll, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                if "optout_center" in inhalt or "optout-center" in inhalt:
                    treffer.append(os.path.relpath(voll, wurzel))

        if not treffer:
            return  # tot wie dokumentiert, nichts zu messen

        assert any(d == UNAUSGELIEFERT for d, _ in OBERFLAECHEN), (
            f"{UNAUSGELIEFERT} wird wieder referenziert ({', '.join(sorted(treffer))}), "
            "steht aber nicht in OBERFLAECHEN. Was complyo in fremde Seiten "
            "zeichnet, wird vor der Auslieferung gemessen — sonst ist der "
            "Waechter ab jetzt blind fuer genau diese Flaeche."
        )
