"""
Logo der Website im Einstellungsfenster des Banners, im echten Browser.

Zwei Dinge lassen sich nur dort pruefen: was die Erkennung auf einer
gerenderten Seite einsammelt (Sichtbarkeit, Lage, Farbe hinter dem Logo), und
ob das Widget das Logo wirklich zeigt, begrenzt, bei einem hellen Logo eine
dunkle Unterlage setzt und bei einer toten Adresse auf den Buchstaben
zurueckfaellt.

Chromium muss installiert sein. Lokal: COMPLYO_TEST_CHROMIUM auf die Programmdatei.
"""
import json
import os
import struct
import threading
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lies(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


def _png(breite, hoehe, farbe, rand_durchsichtig=True):
    """Kleines RGBA-PNG: farbiges Rechteck, auf Wunsch mit durchsichtigem Rand."""
    zeilen = b""
    for y in range(hoehe):
        zeile = b"\x00"
        for x in range(breite):
            innen = 4 <= x < breite - 4 and 4 <= y < hoehe - 4
            if innen or not rand_durchsichtig:
                zeile += bytes(farbe) + b"\xff"
            else:
                zeile += b"\x00\x00\x00\x00"
        zeilen += zeile

    def stueck(typ, daten):
        return (struct.pack(">I", len(daten)) + typ + daten +
                struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n" + stueck(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 6, 0, 0, 0)) +
            stueck(b"IDAT", zlib.compress(zeilen)) + stueck(b"IEND", b""))


BILDER = {
    "/logo-dunkel.png": _png(240, 60, (20, 30, 60)),
    "/logo-weiss.png": _png(240, 60, (255, 255, 255)),
    "/logo-weisse-flaeche.png": _png(240, 60, (255, 255, 255), rand_durchsichtig=False),
    "/apple-180.png": _png(180, 180, (200, 30, 30), rand_durchsichtig=False),
    "/team.png": _png(400, 200, (90, 90, 90), rand_durchsichtig=False),
    "/fb.png": _png(32, 32, (0, 0, 200), rand_durchsichtig=False),
}

SEITEN = {
    # Heller Kopf mit Logo, dazu Dinge, die kein Logo sind.
    "hell": ('<link rel="apple-touch-icon" sizes="180x180" href="/apple-180.png">',
             '<header style="background:#fff;padding:12px"><a href="/"><img class="site-logo" src="/logo-dunkel.png" '
             'alt="Kunde GmbH" width="160" height="40"></a><img src="/fb.png" alt="facebook" width="24" height="24"></header>'
             '<main><img src="/team.png" alt="Team" width="400" height="200"></main>'),
    # Dunkler Kopf mit weissem Logo.
    "dunkel": ('', '<header style="background:#0b1020;padding:12px"><a href="/"><img src="/logo-weiss.png" '
                   'alt="Logo" width="160" height="40"></a></header><p>Inhalt</p>'),
    # Kein Bild im Kopf: nur das Icon bleibt.
    "nur_icon": ('<link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" sizes="180x180" href="/apple-180.png">',
                 '<header><a href="/">Kunde GmbH</a></header><main><img src="/team.png" alt="Team" width="400" height="200"></main>'),
    # Logo steckt in einem fremden Einwilligungsfenster: zaehlt nicht.
    "consent": ('', '<div id="cookie-banner"><img class="logo" src="/logo-dunkel.png" alt="logo" width="160" height="40"></div>'
                    '<p>Inhalt</p>'),
    "leer": ('', '<p>nichts</p>'),
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
            elif p in BILDER:
                self._s(200, "image/png", BILDER[p])
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


def _seite(umgebung, name, logo=None, breite=1280):
    basis, browser = umgebung
    ctx = browser.new_context(viewport={"width": breite, "height": 900})
    page = ctx.new_page()
    fehler = []

    def abfangen(route):
        u = route.request.url
        if u.startswith(basis):
            return route.continue_()
        if "api.complyo.de/api/cookie-compliance/config/" in u:
            daten = {"site_id": "test-de", "layout": "box_modal", "is_active": True, "services": [],
                     "license_active": True, "scan_completed": True, "revision": 1,
                     "primary_color": "#3c7f1a", "accent_color": "#336c16", "custom_logo_url": logo}
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
    return page, ctx, fehler


def _fenster(page):
    page.evaluate("() => window.complyo.openPreferences()")
    page.wait_for_selector("#complyo-settings-modal .cps-header", timeout=5000)
    page.wait_for_timeout(700)
    return page.evaluate("""() => {
      const kopf = document.querySelector('#complyo-settings-modal .cps-header-left');
      const huelle = kopf.querySelector('.cps-logo-bild');
      const img = kopf.querySelector('img');
      const kreis = kopf.querySelector('.cps-logo');
      const r = img ? img.getBoundingClientRect() : null;
      return {
        bild: !!img, src: img ? img.getAttribute('src') : null,
        breite: r ? r.width : 0, hoehe: r ? r.height : 0,
        dunkel: !!(huelle && huelle.classList.contains('cps-logo-bild--dunkel')),
        unterlage: huelle ? getComputedStyle(huelle).backgroundColor : null,
        kreis: kreis ? kreis.textContent.trim() : null,
        titelLinks: kopf.querySelector('.cps-title').getBoundingClientRect().left,
        ueberlauf: document.documentElement.scrollWidth > window.innerWidth,
      };
    }""")


# ============================================================================
# 1) Anzeige im Widget
# ============================================================================

class TestAnzeige:
    def test_logo_steht_an_der_stelle_des_c(self, umgebung):
        basis, _ = umgebung
        page, ctx, fehler = _seite(umgebung, "leer", logo=f"{basis}/logo-dunkel.png#complyo-auto")
        try:
            z = _fenster(page)
            assert z["bild"] and z["kreis"] is None
            assert z["src"] == f"{basis}/logo-dunkel.png", "Das Fragment gehoert nicht in die Adresse."
            assert 0 < z["hoehe"] <= 36.5 and 0 < z["breite"] <= 160.5
            assert not z["dunkel"]
            assert fehler == [], fehler
        finally:
            ctx.close()

    def test_helles_logo_bekommt_eine_dunkle_unterlage(self, umgebung):
        """Vom Scan nicht als dunkel vermerkt (etwa Kopf ueber einem Foto): das Widget misst nach."""
        basis, _ = umgebung
        page, ctx, _ = _seite(umgebung, "leer", logo=f"{basis}/logo-weiss.png#complyo-auto")
        try:
            z = _fenster(page)
            assert z["bild"] and z["dunkel"]
            assert z["unterlage"] == "rgb(17, 24, 39)"
        finally:
            ctx.close()

    def test_logo_mit_eigener_weisser_flaeche_bleibt_ohne_unterlage(self, umgebung):
        basis, _ = umgebung
        page, ctx, _ = _seite(umgebung, "leer", logo=f"{basis}/logo-weisse-flaeche.png")
        try:
            assert not _fenster(page)["dunkel"]
        finally:
            ctx.close()

    def test_vermerk_des_scans_setzt_die_unterlage_sofort(self, umgebung):
        basis, _ = umgebung
        page, ctx, _ = _seite(umgebung, "leer", logo=f"{basis}/logo-dunkel.png#complyo-auto-dunkel")
        try:
            z = _fenster(page)
            assert z["dunkel"] and z["hoehe"] <= 26.5
        finally:
            ctx.close()

    def test_tote_adresse_faellt_auf_den_buchstaben_der_website_zurueck(self, umgebung):
        basis, _ = umgebung
        page, ctx, fehler = _seite(umgebung, "leer", logo=f"{basis}/gibt-es-nicht.png#complyo-auto")
        try:
            z = _fenster(page)
            assert not z["bild"] and z["kreis"] == "1", "127.0.0.1 beginnt mit 1; ein festes C waere falsch."
            assert fehler == [], fehler
        finally:
            ctx.close()

    @pytest.mark.parametrize("logo", [None, "", "javascript:alert(1)", "/relativ.png", 7])
    def test_ohne_brauchbare_adresse_bleibt_der_kreis(self, umgebung, logo):
        page, ctx, fehler = _seite(umgebung, "leer", logo=logo)
        try:
            z = _fenster(page)
            assert not z["bild"] and z["kreis"] == "1"
            assert fehler == [], fehler
        finally:
            ctx.close()

    def test_handybreite_ohne_ueberlauf(self, umgebung):
        basis, _ = umgebung
        page, ctx, _ = _seite(umgebung, "leer", logo=f"{basis}/logo-dunkel.png#complyo-auto", breite=375)
        try:
            z = _fenster(page)
            assert z["bild"] and z["breite"] <= 110.5
            assert not z["ueberlauf"]
        finally:
            ctx.close()


# ============================================================================
# 2) Erkennung auf der gerenderten Seite
# ============================================================================

def _erkenne(umgebung, name):
    from compliance_engine.logo_erkennung import LOGO_JS, bewerte_logokandidaten
    from compliance_engine.markenfarben_gerendert import CONSENT_SELEKTOR
    basis, _ = umgebung
    page, ctx, _ = _seite(umgebung, name)
    try:
        kandidaten = page.evaluate(LOGO_JS, CONSENT_SELEKTOR)
        return bewerte_logokandidaten(kandidaten, page.url), kandidaten
    finally:
        ctx.close()


class TestErkennung:
    def test_logo_im_hellen_kopf(self, umgebung):
        basis, _ = umgebung
        e, _ = _erkenne(umgebung, "hell")
        assert e["url"] == f"{basis}/logo-dunkel.png" and e["quelle"] == "kopfbild" and e["grund"] == "hell"

    def test_weisses_logo_auf_dunklem_kopf_wird_als_dunkel_vermerkt(self, umgebung):
        basis, _ = umgebung
        e, _ = _erkenne(umgebung, "dunkel")
        assert e["url"] == f"{basis}/logo-weiss.png" and e["grund"] == "dunkel"
        assert e["gespeichert"].endswith("#complyo-auto-dunkel")

    def test_ohne_bild_im_kopf_bleibt_das_apple_touch_icon(self, umgebung):
        basis, _ = umgebung
        e, _ = _erkenne(umgebung, "nur_icon")
        assert e["url"] == f"{basis}/apple-180.png" and e["quelle"] == "apple-touch-icon"

    def test_logo_eines_fremden_einwilligungsfensters_zaehlt_nicht(self, umgebung):
        e, kandidaten = _erkenne(umgebung, "consent")
        assert kandidaten["bilder"] == [] and e is None

    def test_seite_ohne_alles_hat_kein_logo(self, umgebung):
        e, _ = _erkenne(umgebung, "leer")
        assert e is None
