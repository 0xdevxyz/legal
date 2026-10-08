# -*- coding: utf-8 -*-
"""Das Barrierefreiheits-Widget zeigt seinen Fokus, auch gegen die Kundenseite.

Befund vom 29.09.2026 auf panoart360.de, per Puppeteer gemessen: der Knopf
unten rechts hatte fokussiert dieselben berechneten Werte wie unfokussiert,
outline "none 3px rgb(17,24,39)". Eine :focus-visible-Regel gab es, sie
verlor aber gegen das Theme der Seite:

    button:active, button:focus { outline: none !important; }

Das ist ein gaengiger Reset, er steht auf vielen Kundenseiten. Das Widget,
das Barrierefreiheit verkauft, verstiess damit ueberall gegen WCAG 2.4.7.
Im selben Lauf: der Knopf lag ueber den Links "Fb" und "X" der Seite, und
elementFromPoint in der Mitte des fokussierten Links traf den Knopf
(WCAG 2.4.11).

Dieser Waechter misst deshalb NICHT auf einer sauberen Seite, sondern auf
einer mit genau diesen Resets, und mit echten Tab-Druecken: :focus-visible
gilt nur nach Tastatureingabe, ein element.focus() allein beweist nichts.

axe prueft weder 2.4.7 noch 2.4.11; test_eigene_widgets_barrierefrei.py
waere hier gruen geblieben. Das ist der Grund fuer diese eigene Datei.

Gegenprobe: das !important aus dem FOKUS-Block im Widget entfernen, dann
faellt test_knopf_zeigt_fokus_gegen_seitenreset.
"""

import json
import os
import tempfile

import pytest

WIDGETS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "widgets"))

# Was Kundenseiten tun. Die erste Zeile steht wortgleich im Theme von
# panoart360.de (css/main.css), die zweite in vielen Resets, die dritte
# faengt den Versuch ab, den Ring nur ueber box-shadow zu retten.
FEINDLICHES_CSS = """
button:active, button:focus { outline: none !important; }
a:focus, *:focus { outline: 0 !important; }
*:focus-visible { outline: none !important; box-shadow: none !important; }
"""

TRAEGERSEITE = """<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><title>Traegerseite</title>
<style>__CSS__</style></head>
<body style="margin:0;background:#0b0f14;color:#fff;min-height:200vh">
<main><h1>Traegerseite</h1><a href="#a" id="erster">Erster Link</a></main>
__ECKE__
__STUB__
<script data-site-id="waechter">
__WIDGET__
</script>
</body>
</html>
"""

# Wie auf panoart360.de: kleine Links unten rechts im bildschirmhohen
# Einstieg, absolut positioniert ("socials bottom-right"). Absolut, nicht
# fixiert: eine fixierte Leiste erkennt das Widget als Eck-Element und
# weicht ihr ohnehin dauerhaft aus, dann bewiese der Test nichts.
ECKE_LINKS = """
<section style="position:absolute;top:0;left:0;right:0;height:100vh">
  <div style="position:absolute;right:24px;bottom:22px;display:flex;gap:14px;font-size:14px">
    <a href="#fb" id="fb">Fb</a><a href="#x" id="x">X</a>
  </div>
</section>
"""

# Ein Scroll-to-Top-Knopf in der Ecke. Das Widget erkennt ihn seit 279bb6a,
# die Verschiebung verlor aber gegen "bottom/right: 20px !important" und
# wirkte nie; auf panoart360.de lag der complyo-Knopf mobil deshalb ueber dem
# WhatsApp-Knopf der Seite.
ECKE_NACH_OBEN = """
<a href="#top" class="back-to-top" id="nachoben"
   style="position:fixed;right:20px;bottom:20px;width:44px;height:44px;background:#2d6">oben</a>
"""


def _stub() -> str:
    """Beantwortet die Abrufe des Widgets im Dokument, ohne Produktion."""
    return (
        "<script>(function () {\n"
        "  const antwort = (k) => new Response(JSON.stringify(k), "
        "{ status: 200, headers: { 'Content-Type': 'application/json' } });\n"
        "  window.fetch = function () {\n"
        "    return Promise.resolve(antwort({ success: true, data: {}, fixes: [] }));\n"
        "  };\n"
        "})();</script>"
    )


def _seite(ecke: str = "") -> str:
    widget = open(os.path.join(WIDGETS, "accessibility-v6.js"), encoding="utf-8").read()
    return (TRAEGERSEITE.replace("__CSS__", FEINDLICHES_CSS)
            .replace("__ECKE__", ecke)
            .replace("__STUB__", _stub())
            .replace("__WIDGET__", widget))


STIL = """(e) => { const c = getComputedStyle(e);
  return { stil: c.outlineStyle, breite: parseFloat(c.outlineWidth), farbe: c.outlineColor,
           schatten: c.boxShadow, fv: e.matches(':focus-visible'),
           aktiv: document.activeElement === e }; }"""

AKTIV = """() => { const a = document.activeElement;
  if (!a || a === document.body) return null;
  const c = getComputedStyle(a);
  return { name: (a.className || a.tagName).toString() + (a.dataset.feature ? '[' + a.dataset.feature + ']' : ''),
           imPanel: !!a.closest('#complyo-panel'), imDialog: !!a.closest('#complyo-text-settings-modal'),
           stil: c.outlineStyle, breite: parseFloat(c.outlineWidth), schatten: c.boxShadow }; }"""


class _Browser:
    """Eine Seite in Chromium, Viewport wie am Desktop."""

    def __init__(self, html: str, breite: int = 1440, hoehe: int = 900):
        self.html, self.breite, self.hoehe = html, breite, hoehe

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
        f.write(self.html)
        f.close()
        self.pfad = f.name
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(args=["--no-sandbox"])
        self.seite = self._browser.new_page(viewport={"width": self.breite, "height": self.hoehe})
        self.seite.goto(f"file://{self.pfad}", wait_until="load")
        self.seite.wait_for_selector("#complyo-a11y-widget .complyo-toggle-btn", timeout=15000)
        self.seite.wait_for_timeout(300)
        return self.seite

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        os.unlink(self.pfad)


def _tab_nach(seite, vorgaenger_js: str):
    """Fokus auf den Vorgaenger per Skript, dann ein echter Tab-Druck."""
    seite.evaluate(f"() => {{ const e = {vorgaenger_js}; e.focus({{preventScroll: true}}); }}")
    seite.keyboard.press("Tab")
    seite.wait_for_timeout(350)


def _zum_knopf(seite):
    # Das Widget haengt an <html> hinter <body>: nach dem letzten Link der
    # Seite ist der Knopf der naechste Tab-Halt.
    _tab_nach(seite, "[...document.body.querySelectorAll('a[href]')].pop()")


def _ist_ring(werte: dict) -> bool:
    return werte["stil"] not in ("none", "hidden") and werte["breite"] >= 2


class TestFokusSichtbar:
    def test_knopf_zeigt_fokus_gegen_seitenreset(self):
        with _Browser(_seite()) as seite:
            knopf = seite.locator(".complyo-toggle-btn")
            ohne = knopf.evaluate(STIL)
            _zum_knopf(seite)
            mit = knopf.evaluate(STIL)

        assert mit["aktiv"] and mit["fv"], (
            f"Der Tab-Druck hat den Knopf nicht erreicht ({mit}); gemessen waere "
            "ein anderer Zustand."
        )
        assert _ist_ring(mit), (
            f"Knopf fokussiert ohne sichtbaren Rahmen: outline {mit['stil']} "
            f"{mit['breite']}px. Das Seiten-CSS hat die Fokusregel ueberstimmt."
        )
        assert mit["stil"] != ohne["stil"] or mit["schatten"] != ohne["schatten"], (
            "Fokussiert und unfokussiert sind gleich."
        )

    def test_ring_ist_zweifarbig(self):
        """Dunkler Ring fuer hellen Grund, heller Saum fuer dunklen."""
        with _Browser(_seite()) as seite:
            _zum_knopf(seite)
            mit = seite.locator(".complyo-toggle-btn").evaluate(STIL)
        assert mit["farbe"] == "rgb(17, 24, 39)", mit
        assert "rgb(255, 255, 255)" in mit["schatten"], (
            f"Heller Saum fehlt, auf dunklem Grund verschwaende der Ring: {mit['schatten']}"
        )

    def test_alle_bedienelemente_im_panel_zeigen_fokus(self):
        with _Browser(_seite()) as seite:
            _zum_knopf(seite)
            seite.keyboard.press("Enter")
            seite.wait_for_timeout(300)
            erstes = seite.evaluate(AKTIV)
            gesehen = []
            for _ in range(60):
                a = seite.evaluate(AKTIV)
                if not a or not a["imPanel"]:
                    break
                gesehen.append(a)
                seite.keyboard.press("Tab")
                # Kacheln haben einen box-shadow-Uebergang; outline nicht,
                # gemessen wird die outline.
                seite.wait_for_timeout(30)

        assert erstes and erstes["imPanel"] and "complyo-close-btn" in erstes["name"], (
            f"Nach dem Oeffnen per Tastatur steht der Fokus nicht im Bedienfeld: {erstes}. "
            "Der Knopf verschwindet beim Oeffnen, der Fokus fiele sonst ins Leere."
        )
        # 1 Schliessen + 2 Sprachen + 19 Kacheln + Zuruecksetzen + summary
        assert len(gesehen) >= 24, (
            f"Nur {len(gesehen)} Tab-Halte im Bedienfeld, erwartet mindestens 24: "
            + ", ".join(g["name"] for g in gesehen)
        )
        ohne_ring = [g["name"] for g in gesehen if not _ist_ring(g)]
        assert not ohne_ring, f"Ohne sichtbaren Fokus: {ohne_ring}"

    def test_regler_im_textdialog_zeigen_fokus(self):
        """Die Regler setzen selbst outline: none."""
        with _Browser(_seite()) as seite:
            _zum_knopf(seite)
            seite.keyboard.press("Enter")
            seite.wait_for_timeout(300)
            seite.focus('#complyo-a11y-widget [data-feature="fontSize"]')
            seite.keyboard.press("Enter")
            seite.wait_for_timeout(300)
            seite.evaluate("() => document.querySelector('#complyo-text-settings-modal .complyo-modal-close').focus()")
            gesehen = []
            for _ in range(12):
                seite.keyboard.press("Tab")
                seite.wait_for_timeout(30)
                a = seite.evaluate(AKTIV)
                if not a or not a["imDialog"]:
                    break
                gesehen.append(a)
        regler = [g for g in gesehen if "complyo-slider" in g["name"]]
        assert len(regler) >= 2, f"Regler nicht per Tab erreicht: {[g['name'] for g in gesehen]}"
        ohne_ring = [g["name"] for g in gesehen if not _ist_ring(g)]
        assert not ohne_ring, f"Ohne sichtbaren Fokus im Textdialog: {ohne_ring}"

    def test_escape_gibt_fokus_an_den_knopf_zurueck(self):
        with _Browser(_seite()) as seite:
            _zum_knopf(seite)
            seite.keyboard.press("Enter")
            seite.wait_for_timeout(300)
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(200)
            zurueck = seite.locator(".complyo-toggle-btn").evaluate(STIL)
        assert zurueck["aktiv"], "Nach Escape steht der Fokus nicht wieder auf dem Knopf."
        assert _ist_ring(zurueck)


MITTE_TRIFFT = """(id) => { const a = document.getElementById(id); const r = a.getBoundingClientRect();
  const oben = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
  return { fokus: document.activeElement === a,
           trifft: oben === a || a.contains(oben) ? 'selbst'
                 : (oben && oben.closest('#complyo-a11y-widget') ? 'complyo' : String(oben && oben.tagName)) }; }"""


class TestFokusNichtVerdeckt:
    @pytest.mark.parametrize("ziel", ["fb", "x"])
    def test_fokussierter_link_in_der_ecke_bleibt_sichtbar(self, ziel):
        with _Browser(_seite(ECKE_LINKS)) as seite:
            vor = seite.evaluate(MITTE_TRIFFT, ziel)
            vorgaenger = "document.getElementById('erster')" if ziel == "fb" else "document.getElementById('fb')"
            _tab_nach(seite, vorgaenger)
            seite.wait_for_timeout(400)  # bottom gleitet 0.2s
            nach = seite.evaluate(MITTE_TRIFFT, ziel)

        assert vor["trifft"] == "complyo", (
            f"Aufbau taugt nicht: ohne Fokus deckt der Knopf #{ziel} gar nicht ab ({vor}). "
            "Dann bewiese der Test nichts."
        )
        assert nach["fokus"], f"#{ziel} hat den Fokus nicht bekommen."
        assert nach["trifft"] == "selbst", (
            f"Fokussierter Link #{ziel} liegt unter dem Widget ({nach['trifft']}), WCAG 2.4.11."
        )

    def test_knopf_kehrt_zurueck(self):
        with _Browser(_seite(ECKE_LINKS)) as seite:
            unten = seite.locator(".complyo-toggle-btn").bounding_box()["y"]
            _tab_nach(seite, "document.getElementById('erster')")
            seite.wait_for_timeout(400)
            ausgewichen = seite.locator(".complyo-toggle-btn").bounding_box()["y"]
            seite.evaluate("() => document.getElementById('erster').focus()")
            seite.wait_for_timeout(400)
            zurueck = seite.locator(".complyo-toggle-btn").bounding_box()["y"]
        assert ausgewichen < unten, "Knopf ist nicht ausgewichen."
        assert abs(zurueck - unten) < 1, f"Knopf steht nicht wieder am Platz ({zurueck} statt {unten})."

    def test_scroll_nach_oben_knopf_wird_nicht_verdeckt(self):
        with _Browser(_seite(ECKE_NACH_OBEN)) as seite:
            seite.wait_for_timeout(900)
            lage = seite.evaluate("""() => {
              const k = document.querySelector('.complyo-toggle-btn').getBoundingClientRect();
              const n = document.getElementById('nachoben').getBoundingClientRect();
              return { ueberlappt: n.right > k.left && n.left < k.right && n.bottom > k.top && n.top < k.bottom,
                       ausweichen: document.getElementById('complyo-a11y-widget').dataset.complyoDodge }; }""")
        assert lage["ausweichen"] == "1", f"Scroll-to-Top-Knopf nicht erkannt: {lage}"
        assert not lage["ueberlappt"], (
            "Das Widget liegt ueber dem Scroll-to-Top-Knopf der Seite, obwohl es ihn "
            "erkannt hat. Die berechnete Position verliert gegen ein !important."
        )
