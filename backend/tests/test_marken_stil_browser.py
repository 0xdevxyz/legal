"""
Schrift und Ecken der Website im Cookie-Banner, im echten Browser.

Zwei Dinge lassen sich nur dort pruefen: was die Messung auf einer gerenderten
Seite einsammelt (Sichtbarkeit, fremdes Einwilligungsfenster, Browserkennung auf
<html>), und ob das Widget Schrift und Ecken wirklich auf den Banner legt, eine
ausdrueckliche Wahl des Kunden gewinnen laesst und Boeses verwirft.

Chromium muss installiert sein. Lokal: COMPLYO_TEST_CHROMIUM auf die Programmdatei.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lies(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


LANG = "Das ist ein langer Absatz mit genug Text, damit er als Fliesstext der Seite zaehlt und gemessen wird."

SEITEN = {
    # Serifenschrift, eckige Knoepfe.
    "serife": ('<style>body{font-family:Georgia,"Times New Roman",serif}'
               '.btn{display:inline-block;background:#1d4ed8;color:#fff;padding:12px 24px;border-radius:0;border:0}</style>',
               f'<main><p>{LANG}</p><a class="btn" href="/a">Anfragen</a><a class="btn" href="/b">Termin</a></main>'),
    # Pillenknoepfe, serifenlose Webschrift mit Namen aus zwei Woertern.
    "pille": ('<style>body{font-family:"Open Sans",Arial,sans-serif}'
              '.btn{display:inline-block;background:#c2410c;color:#fff;padding:12px 28px;border-radius:999px;border:0}</style>',
              f'<main><p>{LANG}</p><a class="btn" href="/a">Anfragen</a></main>'),
    # Ein fremdes Einwilligungsfenster mit eigenen Pillenknoepfen zaehlt nicht.
    "consent": ('<style>body{font-family:Georgia,serif}'
                '.btn{display:inline-block;background:#1d4ed8;color:#fff;padding:12px 24px;border-radius:6px;border:0}'
                '.c.btn{display:inline-block;background:#111;color:#fff;padding:12px 24px;border-radius:999px;border:0}</style>',
                f'<main><p>{LANG}</p><a class="btn" href="/a">Anfragen</a></main>'
                '<div id="cookie-banner"><a class="btn c" href="#">Alle akzeptieren</a><a class="btn c" href="#">Ablehnen</a>'
                '<a class="btn c" href="#">Einstellungen</a></div>'),
    # Browserkennung als Klasse auf <html> (Avada): darf die Messung nicht ausblenden.
    "avada": ('<script>document.documentElement.className += " ua-complyo-scanner";</script>'
              '<style>body{font-family:Georgia,serif}'
              '.btn{display:inline-block;background:#c2410c;color:#fff;padding:12px 24px;border-radius:6px;border:0}</style>',
              f'<main><p>{LANG}</p><a class="btn" href="/a">Anfragen</a></main>'),
    # Symbolschrift auf dem Fliesstext (fehlerhaft vererbt): nie als Textschrift.
    "symbol": ('<style>body{font-family:"Font Awesome 6 Free"}.btn{display:inline-block;background:#1d4ed8;color:#fff;'
               'padding:12px 24px;border-radius:4px;border:0}</style>',
               f'<main><p>{LANG}</p><a class="btn" href="/a">Anfragen</a></main>'),
    # Keine Knoepfe, keine Fliesstexte.
    "leer": ('', '<h1>Hallo</h1>'),
    "banner": ('', '<p>Inhalt</p>'),
}

KOPF = """<!doctype html><html lang="de"><head><meta charset="utf-8"><title>{n}</title>{kopf}
<script src="/bundle.js" data-site-id="test-de"></script></head><body>{koerper}</body></html>"""


@pytest.fixture(scope="module")
def umgebung():
    bundle = (_lies("widgets", "locales", "translations.js") + "\n" +
              _lies("widgets", "content_blocker.js") + "\n" +
              _lies("widgets", "cookie_banner_v2.js"))

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _s(self, code, typ, body=b""):
            self.send_response(code)
            self.send_header("Content-Type", typ)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            p = self.path.split("?")[0]
            if p == "/bundle.js":
                self._s(200, "application/javascript", bundle.encode())
            elif p.startswith("/seite/"):
                name = p.split("/")[2].replace(".html", "")
                kopf, koerper = SEITEN[name]
                self._s(200, "text/html; charset=utf-8", KOPF.format(n=name, kopf=kopf, koerper=koerper).encode())
            else:
                self._s(404, "text/plain", b"nein")

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        args=["--no-sandbox"], executable_path=os.environ.get("COMPLYO_TEST_CHROMIUM") or None)
    yield f"http://127.0.0.1:{srv.server_address[1]}", browser
    browser.close()
    pw.stop()
    srv.shutdown()


def _messe(umgebung, name):
    """Messung wie im Scan: dieselben Proben, dieselbe Bewertung."""
    from compliance_engine.marken_stil import STIL_JS, bewerte_stilproben
    from compliance_engine.markenfarben_gerendert import CONSENT_SELEKTOR
    basis, browser = umgebung
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              user_agent="Mozilla/5.0 Chrome/120 Complyo-Scanner/2.0")
    try:
        page = ctx.new_page()
        page.route("**/bundle.js", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
        page.goto(f"{basis}/seite/{name}.html")
        proben = page.evaluate(STIL_JS, CONSENT_SELEKTOR)
        return bewerte_stilproben(proben), proben
    finally:
        ctx.close()


def _banner(umgebung, name="banner", **konfig):
    basis, browser = umgebung
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    fehler = []

    def abfangen(route):
        u = route.request.url
        if u.startswith(basis):
            return route.continue_()
        if "api.complyo.de/api/cookie-compliance/config/" in u:
            daten = {"site_id": "test-de", "layout": "box_modal", "is_active": True, "services": [],
                     "license_active": True, "scan_completed": True, "revision": 1,
                     "primary_color": "#3c7f1a", "accent_color": "#336c16"}
            daten.update(konfig)
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"success": True, "data": daten}))
        if "api.complyo.de/api/cookie-compliance/services" in u:
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"success": True, "services": [], "total": 0}))
        if "complyo.de" in u:
            return route.fulfill(status=200, content_type="application/json", body='{"success":true}')
        return route.fulfill(status=404, content_type="text/plain", body="nein")

    page.route("**/*", abfangen)
    page.on("pageerror", lambda e: fehler.append(str(e)[:200]))
    page.goto(f"{basis}/seite/{name}.html")
    page.wait_for_function("() => window.complyo && window.complyo.openPreferences", timeout=8000)
    page.wait_for_selector(".complyo-cookie-banner .complyo-btn-primary", timeout=8000, state="attached")
    page.wait_for_timeout(500)
    return page, ctx, fehler


def _stil(page):
    return page.evaluate("""() => {
      const w = document.querySelector('.complyo-cookie-banner');
      const k = document.querySelector('.complyo-cookie-banner .complyo-btn-primary');
      const b = document.querySelector('.complyo-box-layout');
      const wurzel = getComputedStyle(document.documentElement);
      return {
        schrift: w ? getComputedStyle(w).fontFamily : null,
        knopf: k ? getComputedStyle(k).borderTopLeftRadius : null,
        karte: b ? getComputedStyle(b).borderTopLeftRadius : null,
        variable: wurzel.getPropertyValue('--complyo-font').trim(),
        knopfKlasse: k ? k.className : null,
      };
    }""")


STANDARD_SCHRIFT = "-apple-system"


# ============================================================================
# 1) Messung auf der gerenderten Seite
# ============================================================================

class TestMessung:
    def test_serifenschrift_und_eckige_knoepfe(self, umgebung):
        e, _ = _messe(umgebung, "serife")
        assert e["radius"] == 0
        assert e["schrift"] == 'Georgia, "Times New Roman", serif'

    def test_webschrift_mit_zwei_woertern_und_pille(self, umgebung):
        e, _ = _messe(umgebung, "pille")
        assert e["radius"] == 100
        assert e["schrift"] == '"Open Sans", Arial, sans-serif'

    def test_knoepfe_eines_fremden_einwilligungsfensters_zaehlen_nicht(self, umgebung):
        e, proben = _messe(umgebung, "consent")
        assert e["radius"] == 6, proben

    def test_browserkennung_als_klasse_auf_html_blendet_die_seite_nicht_aus(self, umgebung):
        e, proben = _messe(umgebung, "avada")
        assert e is not None and e["radius"] == 6 and e["schrift"].startswith("Georgia"), proben

    def test_symbolschrift_wird_nicht_uebernommen(self, umgebung):
        e, _ = _messe(umgebung, "symbol")
        assert e["schrift"] is None and e["radius"] == 4

    def test_seite_ohne_knoepfe_hat_keine_ecken(self, umgebung):
        e, _ = _messe(umgebung, "leer")
        assert e is None or e["radius"] is None


# ============================================================================
# 2) Anzeige im Widget
# ============================================================================

class TestAnzeige:
    def test_schrift_und_ecken_liegen_auf_dem_banner(self, umgebung):
        page, ctx, fehler = _banner(umgebung, marken_schrift='Georgia, "Times New Roman", serif', marken_radius=0)
        try:
            s = _stil(page)
            assert s["schrift"].startswith("Georgia"), s
            assert s["knopf"] == "0px", s
            assert s["karte"] == "0px", s
            assert fehler == [], fehler
        finally:
            ctx.close()

    def test_pille_und_kartenrundung(self, umgebung):
        page, ctx, _ = _banner(umgebung, marken_schrift='"Open Sans", sans-serif', marken_radius=100)
        try:
            s = _stil(page)
            assert s["knopf"] != "10px" and float(s["knopf"].replace("px", "")) >= 100, s
            assert s["karte"] == "16px", s
        finally:
            ctx.close()

    def test_ohne_felder_bleibt_alles_wie_vorher(self, umgebung):
        page, ctx, _ = _banner(umgebung)
        try:
            s = _stil(page)
            assert s["schrift"].startswith(STANDARD_SCHRIFT), s
            assert s["knopf"] == "10px" and s["karte"] == "12px", s
        finally:
            ctx.close()

    def test_ausdrueckliche_wahl_des_kunden_gewinnt(self, umgebung):
        page, ctx, _ = _banner(umgebung, button_style="square", marken_radius=100)
        try:
            assert _stil(page)["knopf"] == "6px"
        finally:
            ctx.close()
        page, ctx, _ = _banner(umgebung, button_style="pill", marken_radius=0)
        try:
            assert float(_stil(page)["knopf"].replace("px", "")) >= 100
        finally:
            ctx.close()

    @pytest.mark.parametrize("boese", [
        'Arial; } body { display:none',
        'x"; background:url(//boese.de/a)',
        '</style><script>window.boese=1</script>',
        'a' * 300,
    ])
    def test_boese_schrift_vom_server_wird_verworfen(self, umgebung, boese):
        page, ctx, fehler = _banner(umgebung, marken_schrift=boese)
        try:
            s = _stil(page)
            assert s["schrift"].startswith(STANDARD_SCHRIFT), s
            assert page.evaluate("() => window.boese === undefined")
            assert page.evaluate("() => getComputedStyle(document.body).display") != "none"
            assert fehler == [], fehler
        finally:
            ctx.close()

    @pytest.mark.parametrize("radius", [-5, 25, 1000, "6", None, 1.5e300])
    def test_unsinniger_radius_wird_verworfen(self, umgebung, radius):
        page, ctx, _ = _banner(umgebung, marken_radius=radius)
        try:
            s = _stil(page)
            assert s["knopf"] == "10px" and s["karte"] == "12px", s
        finally:
            ctx.close()
