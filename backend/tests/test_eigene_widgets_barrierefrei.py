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


async def _messen(html: str) -> dict:
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

            sichtbar = await seite.evaluate(
                """(auswahl) => Object.fromEntries(auswahl.map((s) => {
                    const e = document.querySelector(s);
                    if (!e) return [s, false];
                    const cs = getComputedStyle(e);
                    const r = e.getBoundingClientRect();
                    return [s, cs.display !== 'none' && cs.visibility !== 'hidden'
                               && r.width > 0 && r.height > 0];
                }))""",
                PFLICHT_SICHTBAR,
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


def _lauf(mit_widgets: bool, palette: dict) -> dict:
    return asyncio.new_event_loop().run_until_complete(
        _messen(_seite(mit_widgets, palette))
    )


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

    @pytest.mark.parametrize("name", sorted(PALETTEN))
    def test_widgets_bringen_nichts_mit(self, name):
        palette = PALETTEN[name]
        mit = _lauf(True, palette)

        fehlend = [s for s, ok in mit["sichtbar"].items() if not ok]
        assert not fehlend, (
            f"[{name}] Nichts gemessen — diese Elemente sind nicht sichtbar: {fehlend}. "
            "Ein Waechter, der eine leere Seite misst, ist schlimmer als keiner."
        )

        leer = _lauf(False, {})["befunde"]
        neu = {r: n - leer.get(r, 0) for r, n in mit["befunde"].items()
               if n > leer.get(r, 0)}
        assert not neu, (
            f"[{name}] complyo bringt Verstoesse in die Seite ein: "
            + ", ".join(f"{r} (+{n})" for r, n in sorted(neu.items()))
        )
