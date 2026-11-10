"""
Blocker gegen Vorladen, im echten Browser.

Anlass (09./10.11.2026, reinhardt.coffee, Netlog mit frischem Chrome-Profil): Mit Plugin,
Blocker, Banner und Inline-Blocker gingen ohne Einwilligung 7 Anfragen an Google:
gtag.js, drei Google-Fonts-Stylesheets, YouTube iframe_api (2x), widgetapi.js.
Ursachen: (a) der Vorlade-Scanner holt statisches Markup vor jedem Skript, (b) vorab
neutralisierte Skripte wurden nach "Alle akzeptieren" nie freigegeben, (c) dynamisch
erzeugte Skripte (Slider) kannten kein Muster, (d) replaceChild auf null,
(e) das Einstellungsfenster blieb nach "Alle akzeptieren" offen, (f) Dienstdetails leer.

Gemessen wird, was der Browser wirklich anfragt (page.on('request') sieht auch Anfragen
des Vorlade-Scanners). Das Markup der Seiten ist das, was das WordPress-Plugin 2.7.0
ausliefert (neutralisiert); die unbehandelte Fassung kann kein Skript im Browser retten,
das ist die Grenze, die das Plugin schliesst.

Chromium muss installiert sein. Lokal: COMPLYO_TEST_CHROMIUM auf die Programmdatei.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIF = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")

DRITTE = ("googletagmanager.com", "youtube.com", "youtube-nocookie.com", "fonts.googleapis.com",
          "fonts.gstatic.com", "ytimg.com", "vimeo.com", "facebook.net")


def _lies(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


KOPF = """<!doctype html><html lang="de"><head><meta charset="utf-8"><title>{n}</title>
<script src="/blocker.js" data-site-id="test-de" data-cfasync="false"></script>
<script src="/bundle.js" data-site-id="test-de"></script>
{kopf}</head><body><h1>{n}</h1>{koerper}</body></html>"""

# Markup, wie es das Plugin ausliefert: nichts Externes mit src/href.
PLUGIN_KOPF = """
<script type="text/plain" data-complyo-consent="analytics" data-complyo-src="https://www.googletagmanager.com/gtag/js?id=G-TEST" data-complyo-blocked="true" async></script>
<script type="text/plain" data-complyo-consent="analytics" data-complyo-inline="1">window.__gtag_inline = (window.__gtag_inline || 0) + 1;</script>
<link data-complyo-consent="functional" data-complyo-href="https://fonts.googleapis.com/css?family=Oswald" data-complyo-rel="stylesheet" data-complyo-blocked="true" rel="stylesheet" media="not all">
"""
PLUGIN_KOERPER = """
<iframe data-complyo-consent="marketing" data-complyo-src="https://www.youtube.com/embed/abc123" data-complyo-blocked="true" width="560" height="315"></iframe>
"""

SEITEN = {
    "plugin_markup": (PLUGIN_KOPF, PLUGIN_KOERPER),
    "dynamisch": ("<script>"
                  "var s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';document.head.appendChild(s);"
                  "var t=document.createElement('script');t.setAttribute('src','https://www.googletagmanager.com/gtag/js?id=G-X');document.head.appendChild(t);"
                  "var f=document.createElement('iframe');f.src='https://www.youtube.com/embed/zzz';"
                  "document.addEventListener('DOMContentLoaded',function(){document.body.appendChild(f);});"
                  "</script>", ""),
    "slider": ("<script>var s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';"
               "document.head.appendChild(s);</script>",
               '<rs-module-wrap id="rev_slider_4_1_wrapper" style="display:block;height:300px;position:relative">'
                   '<rs-bgvideo data-video="w:100%" data-ytid="F8jCDH6z4kY"></rs-bgvideo></rs-module-wrap>'
                   '<div id="band" data-vc-parallax-image="https://www.youtube.com/watch?v=_NzrEUNis1c" style="height:200px"></div>'),
    "sauber": ("", "<p>nichts Externes</p>"),
}

TEMPLATE_YT = {
    "id": "youtube", "name": "YouTube", "cookies": ["VISITOR_INFO1_LIVE", "YSC", "PREF"],
    "domains": ["youtube.com"], "category": "marketing", "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "description_de": "Video-Plattform von Google für eingebettete Videos",
    "cookie_lifetime": "6 Monate", "privacy_policy_url": "https://policies.google.com/privacy",
    "data_processing_countries": ["USA"],
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


def _seite(umgebung, name, consent=None, dienste=("youtube",)):
    """Öffnet die Seite; liefert (page, ctx, anfragen). Anfragen an Dritte werden gezählt,
    aber mit harmlosen Dummys beantwortet (kein echtes Netz)."""
    basis, browser = umgebung
    ctx = browser.new_context()
    page = ctx.new_page()
    anfragen = []
    fehler = []

    def abfangen(route):
        u = route.request.url
        if u.startswith(basis):
            return route.continue_()
        if any(d in u for d in DRITTE):
            anfragen.append(u)
            if u.endswith("iframe_api"):
                return route.fulfill(status=200, content_type="application/javascript",
                                     body="window.__yt_api=(window.__yt_api||0)+1;")
            if "gtag/js" in u:
                return route.fulfill(status=200, content_type="application/javascript",
                                     body="window.__gtag_js=(window.__gtag_js||0)+1;")
            if "fonts.googleapis.com" in u:
                return route.fulfill(status=200, content_type="text/css", body="")
            return route.fulfill(status=200, content_type="text/html", body="<html></html>")
        if "api.complyo.de/api/cookie-compliance/config/" in u:
            daten = {"site_id": "test-de", "layout": "box_modal", "is_active": True,
                     "services": list(dienste), "license_active": True, "scan_completed": True,
                     "revision": 1, "primary_color": "#3c7f1a", "accent_color": "#336c16"}
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"success": True, "data": daten}))
        if "api.complyo.de/api/cookie-compliance/services" in u:
            svc = [{"service_key": "youtube", "name": "YouTube", "category": "marketing",
                    "provider": "Google LLC", "description": None, "cookies": "[]",
                    "template": json.dumps(TEMPLATE_YT), "requires_third_country_consent": True,
                    "data_processing_countries": [{"code": "US", "name": "Vereinigte Staaten"}]}]
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"success": True, "services": svc, "total": 1}))
        if "api.complyo.de" in u or "complyo.de/" in u:
            return route.fulfill(status=200, content_type="application/json", body='{"success":true}')
        return route.fulfill(status=200, content_type="image/gif", body=GIF)

    page.route("**/*", abfangen)
    if consent is not None:
        page.add_init_script(
            "try{localStorage.setItem('complyo_cookie_consent',JSON.stringify(Object.assign("
            "{necessary:true,services:[],timestamp:new Date().toISOString(),version:'t'},%s)));"
            "localStorage.setItem('complyo_consent_date',new Date().toISOString());}catch(e){}" % json.dumps(consent))
    page.on("pageerror", lambda e: fehler.append(str(e)[:200]))
    page.goto(f"{umgebung[0]}/seite/{name}.html")
    page.wait_for_timeout(1500)
    return page, ctx, anfragen, fehler


def _warte_banner(page):
    page.wait_for_function("() => window.complyo && window.complyo.acceptAll", timeout=8000)


class TestNichtsVorEinwilligung:
    @pytest.mark.parametrize("name", ["plugin_markup", "dynamisch", "slider"])
    def test_null_anfragen_an_dritte(self, umgebung, name):
        page, ctx, anfragen, fehler = _seite(umgebung, name)
        try:
            assert anfragen == [], f"vor der Einwilligung angefragt: {anfragen}"
            assert fehler == [], fehler
        finally:
            ctx.close()

    def test_dynamische_skripte_werden_neutralisiert_nicht_ausgefuehrt(self, umgebung):
        page, ctx, anfragen, _ = _seite(umgebung, "dynamisch")
        try:
            r = page.evaluate("""() => ({
              yt: window.__yt_api || 0, gtag: window.__gtag_js || 0,
              neutral: document.querySelectorAll('script[data-complyo-src]').length })""")
            assert r["yt"] == 0 and r["gtag"] == 0, r
            assert r["neutral"] >= 2, r
        finally:
            ctx.close()


class TestFreigabeNachEinwilligung:
    def test_alle_akzeptieren_gibt_alles_frei(self, umgebung):
        """Das war die Luecke: vorab neutralisierte Skripte (gtag.js, Inline, Fonts, iframe)
        blieben nach 'Alle akzeptieren' tot."""
        page, ctx, anfragen, fehler = _seite(umgebung, "plugin_markup")
        try:
            _warte_banner(page)
            page.evaluate("() => window.complyo.acceptAll()")
            page.wait_for_timeout(1500)
            r = page.evaluate("""() => ({
              gtag: window.__gtag_js || 0, inline: window.__gtag_inline || 0,
              iframeSrc: (document.querySelector('iframe') || {}).src || '',
              fonts: !!document.querySelector('link[href*="fonts.googleapis.com"]'),
              placeholder: document.querySelectorAll('.complyo-content-placeholder').length })""")
            assert r["gtag"] == 1, ("gtag.js nach Einwilligung nicht geladen", r, anfragen)
            assert r["inline"] == 1, ("Inline-Tracker nicht ausgefuehrt", r)
            assert "youtube.com/embed/abc123" in r["iframeSrc"], r
            assert r["fonts"] is True, r
            assert r["placeholder"] == 0, r
            assert fehler == [], fehler
        finally:
            ctx.close()

    def test_dynamische_skripte_laufen_nach_einwilligung(self, umgebung):
        page, ctx, anfragen, fehler = _seite(umgebung, "dynamisch")
        try:
            _warte_banner(page)
            page.evaluate("() => window.complyo.acceptAll()")
            page.wait_for_timeout(1500)
            r = page.evaluate("() => ({yt: window.__yt_api || 0, gtag: window.__gtag_js || 0})")
            assert r == {"yt": 1, "gtag": 1}, (r, anfragen)
        finally:
            ctx.close()

    def test_wiederkehrender_besucher_wird_nie_blockiert(self, umgebung):
        """Einwilligung liegt schon im localStorage: gtag.js und die Inline-Skripte laufen
        ohne Banner-Klick, die API wird nicht ueber einen Platzhalter ausgebremst."""
        alles = {"functional": True, "analytics": True, "marketing": True, "third_country": True}
        page, ctx, anfragen, fehler = _seite(umgebung, "plugin_markup", consent=alles)
        try:
            r = page.evaluate("""() => ({gtag: window.__gtag_js || 0, inline: window.__gtag_inline || 0,
              iframeSrc: (document.querySelector('iframe') || {}).src || '',
              placeholder: document.querySelectorAll('.complyo-content-placeholder').length})""")
            assert r["gtag"] == 1 and r["inline"] == 1, (r, anfragen)
            assert "youtube.com/embed/abc123" in r["iframeSrc"], r
            assert r["placeholder"] == 0, r
        finally:
            ctx.close()

    def test_teil_einwilligung_laesst_youtube_gesperrt(self, umgebung):
        """Nur 'funktional' erlaubt: Analytics-Skript bleibt tot, YouTube bekommt den Platzhalter."""
        teil = {"functional": True, "analytics": False, "marketing": False, "third_country": True}
        page, ctx, anfragen, _ = _seite(umgebung, "plugin_markup", consent=teil)
        try:
            r = page.evaluate("""() => ({gtag: window.__gtag_js || 0,
              placeholder: document.querySelectorAll('.complyo-content-placeholder').length})""")
            assert r["gtag"] == 0, r
            assert r["placeholder"] == 1, r
            assert not [a for a in anfragen if "youtube" in a or "googletagmanager" in a], anfragen
        finally:
            ctx.close()


class TestSperrbildschirmeImBannerDesign:
    def test_video_hintergruende_bekommen_den_platzhalter(self, umgebung):
        page, ctx, anfragen, _ = _seite(umgebung, "slider")
        try:
            r = page.evaluate("""() => Array.from(document.querySelectorAll('.complyo-video-overlay')).map(o => {
              const cs = getComputedStyle(o); const btn = o.querySelector('.complyo-placeholder-btn');
              return {pos: cs.position, bg: cs.backgroundColor, radius: cs.borderRadius,
                      btn: btn ? getComputedStyle(btn).backgroundColor : null,
                      w: o.getBoundingClientRect().width, h: o.getBoundingClientRect().height}})""")
            assert len(r) == 2, r  # Hero und Videoband
            for o in r:
                assert o["pos"] == "absolute", o
                assert o["w"] > 100 and o["h"] > 100, o
            assert anfragen == []
        finally:
            ctx.close()

    def test_platzhalter_nutzt_die_farben_des_banners(self, umgebung):
        page, ctx, anfragen, _ = _seite(umgebung, "slider")
        try:
            _warte_banner(page)
            page.wait_for_timeout(500)
            btn = page.evaluate("""() => { const b = document.querySelector('.complyo-video-overlay .complyo-placeholder-btn');
                return b ? getComputedStyle(b).backgroundColor : null }""")
            assert btn == "rgb(60, 127, 26)", f"Knopf nicht in der Bannerfarbe: {btn}"
        finally:
            ctx.close()

    def test_inhalt_laden_gibt_nur_diesen_dienst_frei(self, umgebung):
        page, ctx, anfragen, _ = _seite(umgebung, "slider")
        try:
            _warte_banner(page)
            # Der Banner liegt ueber der Seite; der Besucher koennte den Knopf nach dem Banner klicken.
            page.evaluate("() => document.querySelector('#rev_slider_4_1_wrapper .complyo-placeholder-btn').click()")
            # Revolution Slider: nach der Freigabe laedt die Seite einmal neu (1,5 s), damit sich das
            # Hero-Video mit bereits gespeicherter Einwilligung richtig aufbaut.
            page.wait_for_timeout(4000)
            c = page.evaluate("() => JSON.parse(localStorage.getItem('complyo_cookie_consent'))")
            assert c["marketing"] is True and c["analytics"] is False, c
            assert page.evaluate("() => window.__yt_api || 0") == 1
            assert page.evaluate("() => document.querySelectorAll('.complyo-video-overlay').length") == 0
        finally:
            ctx.close()


class TestEinstellungsfenster:
    def test_alle_akzeptieren_im_fenster_schliesst_das_fenster(self, umgebung):
        page, ctx, _, _ = _seite(umgebung, "sauber")
        try:
            _warte_banner(page)
            page.evaluate("() => window.complyo.openPreferences()")
            page.wait_for_selector("#complyo-settings-modal", timeout=4000)
            page.evaluate("() => window.complyo.acceptAll()")
            page.wait_for_timeout(700)
            assert page.evaluate("() => !!document.getElementById('complyo-settings-modal')") is False
            assert page.evaluate("() => !!document.getElementById('complyo-settings-backdrop')") is False
        finally:
            ctx.close()

    def test_dienstdetails_zeigen_cookie_namen_dauer_zweck(self, umgebung):
        page, ctx, _, _ = _seite(umgebung, "sauber")
        try:
            _warte_banner(page)
            page.evaluate("() => window.complyo.openPreferences()")
            page.wait_for_selector("#complyo-settings-modal", timeout=4000)
            page.click('.cps-tab[data-tab="services"]')
            page.wait_for_timeout(300)
            text = page.inner_text("#cps-services-list")
            for erwartet in ("VISITOR_INFO1_LIVE", "6 Monate", "Video-Plattform", "Art. 6 Abs. 1 lit. a", "Vereinigte Staaten"):
                assert erwartet in text or erwartet in page.evaluate(
                    "() => document.getElementById('cps-services-list').textContent"), (erwartet, text)
        finally:
            ctx.close()


class TestEinzelnEntsperren:
    def test_inhalt_laden_beim_iframe_gibt_nur_youtube_frei(self, umgebung):
        """Rueckmeldung Daniel 10.11.2026: 'Ich kann die Inhalte nicht einzeln entsperren.'
        Ursache: der Klick setzte die Kategorie, nicht die Drittland-Einwilligung, die der
        Blocker fuer Google/YouTube verlangt. Danach lud nichts."""
        page, ctx, anfragen, fehler = _seite(umgebung, "plugin_markup")
        try:
            _warte_banner(page)
            page.evaluate("() => document.querySelector('.complyo-placeholder-btn').click()")
            page.wait_for_timeout(1200)
            r = page.evaluate("""() => ({
              c: JSON.parse(localStorage.getItem('complyo_cookie_consent')),
              src: (document.querySelector('iframe') || {}).src || '',
              ph: document.querySelectorAll('.complyo-content-placeholder').length,
              gtag: window.__gtag_js || 0 })""")
            assert "youtube.com/embed/abc123" in r["src"], r
            assert r["ph"] == 0, r
            assert r["c"]["marketing"] is True and r["c"]["third_country"] is True, r
            assert r["c"]["analytics"] is False and r["gtag"] == 0, ("Analytics muss gesperrt bleiben", r)
            assert fehler == [], fehler
        finally:
            ctx.close()


class TestKeinEmojiImPlatzhalter:
    def test_symbol_ist_vektorgrafik_kein_emoji(self, umgebung):
        """WordPress ersetzt Emoji durch Bilder von s.w.org und fragt sie vor der Einwilligung ab
        (Netlog reinhardt.coffee 10.11.2026: 25b6.svg zu dem Play-Symbol des Platzhalters)."""
        page, ctx, anfragen, _ = _seite(umgebung, "plugin_markup")
        try:
            r = page.evaluate("""() => Array.from(document.querySelectorAll('.complyo-placeholder-icon')).map(
              e => ({text: e.textContent.trim(), svg: !!e.querySelector('svg')}))""")
            assert r and all(x["text"] == "" and x["svg"] for x in r), r
        finally:
            ctx.close()
