"""
Selbstabschaltung des Banners, im echten Browser.

test_banner_anlass.py hält Regel und Verdrahtung fest. Hier steht, was ein
Besucher sieht. Gebaut wird derselbe Bundle wie in
widget_routes.serve_cookie_compliance_widget (Übersetzungen, Content-Blocker,
Banner) und geladen wie bei einem Kunden: erst public/cookie-blocker.js, dann der
Bundle, beide mit data-site-id. Die API von complyo wird abgefangen.

Gemessen am 08.10.2026 (Chromium, dieselben Seiten gegen den Stand ohne die
Selbstabschaltung): dort zeigte JEDE Seite den Banner. Jetzt verschwindet er nur
auf der sauberen Seite, und bei jedem Anlass, früh wie spät, erscheint er.

Chromium muss installiert sein (wie bei test_widget_fokus.py). Lokal ohne
`playwright install`: Umgebungsvariable COMPLYO_TEST_CHROMIUM auf die Programmdatei.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIF = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")


def _lies(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


KOPF = """<!doctype html><html lang="de"><head><meta charset="utf-8"><title>{n}</title>
<script src="/blocker.js" data-site-id="test-de"></script>
<script src="/bundle.js" data-site-id="test-de"></script>
{kopf}</head><body><h1>{n}</h1>{koerper}</body></html>"""

SEITEN = {
    "sauber": ("", '<img src="/bild.gif" width="8" height="8">'),
    "wp_emoji_und_complyo": (
        "<script>sessionStorage.setItem('wpEmojiSettingsSupports','{}');"
        "sessionStorage.setItem('complyo_wirkung_test-de/','1');</script>", ""),
    "fremder_host": ("", '<img src="http://pixel.fremd.test/p.gif" width="1" height="1">'),
    "cookie": ("<script>document.cookie='sitzung=abc; path=/';</script>", ""),
    "localstorage": ("<script>localStorage.setItem('merk','1');</script>", ""),
    "blocker_dienst": ("", '<script src="https://www.google-analytics.com/analytics.js"></script>'),
    "puffer_voll": ("", "".join(f'<img src="/b{i}.gif" width="1" height="1">' for i in range(270))),
    "spaeter_host": ("", "<script>setTimeout(()=>{const i=new Image();"
                         "i.src='http://spaet.fremd.test/x.gif';document.body.appendChild(i);},3500);</script>"),
}


@pytest.fixture(scope="module")
def umgebung():
    bundle = (_lies("widgets", "locales", "translations.js") + "\n" +
              _lies("widgets", "content_blocker.js") + "\n" +
              _lies("widgets", "cookie_banner_v2.js"))
    blocker = _lies("public", "cookie-blocker.js")

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
            if p == "/blocker.js":
                self._s(200, "application/javascript", blocker.encode())
            elif p == "/bundle.js":
                self._s(200, "application/javascript", bundle.encode())
            elif p.endswith(".gif"):
                self._s(200, "image/gif", GIF)
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


ABRUF = """() => {
  const b = document.querySelector('#complyo-banner, .complyo-cookie-banner');
  const inst = window.complyoCookieBanner || {};
  const lese = (s) => { try { return Object.keys(window[s]); } catch (e) { return 'gesperrt'; } };
  return { sichtbar: !!b && b.offsetParent !== null,
           anlass: inst.bannerAnlass || null,
           consentAuto: !!(window.complyoConsent && window.complyoConsent.auto),
           cookie: document.cookie, local: lese('localStorage'), session: lese('sessionStorage') };
}"""


def _lauf(umgebung, seite, auto_aus=True, feld_fehlt=False, dienste=None, vorher_consent=False,
          warte_ms=4200):
    basis, browser = umgebung
    ctx = browser.new_context()
    page = ctx.new_page()

    def abfangen(route):
        u = route.request.url
        if u.startswith(basis):
            return route.continue_()
        if "api.complyo.de/api/cookie-compliance/config/" in u:
            daten = {"site_id": "test-de", "layout": "box_modal", "is_active": True,
                     "services": dienste or [], "license_active": True, "scan_completed": True,
                     "revision": 1}
            if not feld_fehlt:
                daten["banner_auto_aus_erlaubt"] = auto_aus
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"success": True, "data": daten}))
        if "api.complyo.de/api/cookie-compliance/services" in u:
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"success": True, "services": [], "total": 0}))
        if "api.complyo.de" in u or "complyo.de/" in u:
            return route.fulfill(status=200, content_type="application/json", body='{"success":true}')
        typ = "application/javascript" if u.endswith(".js") else "image/gif"
        return route.fulfill(status=200, content_type=typ, body=b"" if typ != "image/gif" else GIF)

    page.route("**/*", abfangen)
    if vorher_consent:
        page.add_init_script(
            "try{localStorage.setItem('complyo_cookie_consent',JSON.stringify({necessary:true,functional:false,"
            "analytics:false,marketing:false,services:[],timestamp:new Date().toISOString(),version:'t'}));"
            "localStorage.setItem('complyo_consent_date',new Date().toISOString());}catch(e){}")
    fehler = []
    page.on("pageerror", lambda e: fehler.append(str(e)[:150]))
    page.goto(f"{basis}/seite/{seite}.html")
    page.wait_for_timeout(warte_ms)
    erg = page.evaluate(ABRUF)
    erg["seitenfehler"] = fehler
    ctx.close()
    return erg


class TestBannerBleibtWeg:
    def test_saubere_seite_ohne_anlass(self, umgebung):
        r = _lauf(umgebung, "sauber")
        assert r["sichtbar"] is False, r
        assert r["anlass"] and r["anlass"]["anlass"] is False, r
        assert r["consentAuto"] is True, "Die Einwilligung 'nur notwendig' muss gesetzt sein."
        assert r["seitenfehler"] == []
        # Die Pruefung selbst schreibt nichts in den Browser des Besuchers.
        assert r["cookie"] == "" and r["local"] == [] and r["session"] == [], r

    def test_wp_emoji_und_complyo_eigene_eintraege_zaehlen_nicht(self, umgebung):
        r = _lauf(umgebung, "wp_emoji_und_complyo")
        assert r["sichtbar"] is False, r
        assert r["anlass"]["anlass"] is False


class TestBannerErscheint:
    @pytest.mark.parametrize("seite,grund", [
        ("fremder_host", "host:pixel.fremd.test"),
        ("cookie", "cookie:sitzung"),
        ("localstorage", "localStorage:merk"),
        ("blocker_dienst", "blocker:"),
        ("puffer_voll", "unsicher:timing-voll"),
    ])
    def test_jeder_anlass_zeigt_den_banner(self, umgebung, seite, grund):
        r = _lauf(umgebung, seite)
        assert r["sichtbar"] is True, r
        assert any(g.startswith(grund) for g in r["anlass"]["gruende"]), r["anlass"]
        assert r["seitenfehler"] == []

    def test_anlass_der_erst_nach_dem_laden_entsteht(self, umgebung):
        """Ein Pixel, das 3,5 s nach dem Laden nachgeladen wird: erst weg, dann da."""
        r = _lauf(umgebung, "spaeter_host", warte_ms=7000)
        assert r["sichtbar"] is True, r
        assert r["anlass"].get("nachtraeglich") is True, r["anlass"]
        assert any(g.startswith("host:spaet.fremd.test") for g in r["anlass"]["gruende"])


class TestBannerWieBisher:
    def test_server_erlaubt_nicht(self, umgebung):
        r = _lauf(umgebung, "sauber", auto_aus=False)
        assert r["sichtbar"] is True, r

    def test_feld_fehlt_aelterer_server(self, umgebung):
        r = _lauf(umgebung, "sauber", feld_fehlt=True)
        assert r["sichtbar"] is True, r

    def test_dienste_in_der_konfiguration(self, umgebung):
        r = _lauf(umgebung, "sauber", dienste=["google_analytics_ga4"])
        assert r["sichtbar"] is True, r

    def test_wer_schon_eingewilligt_hat_bleibt_auf_dem_normalen_weg(self, umgebung):
        r = _lauf(umgebung, "sauber", vorher_consent=True)
        assert r["sichtbar"] is False, r
        assert r["consentAuto"] is False, "Eine gespeicherte Einwilligung darf nicht durch die Automatik ersetzt werden."
