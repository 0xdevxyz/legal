"""
Im Einstellungsfenster des Banners steht das Logo der Website, kein festes "C".

Anlass (Daniel, 12.11.2026): "Das Logo des Nutzers muss noch dahin, wo das C im
Cookiebanner steht." Das Feld `custom_logo_url` gab es, aber niemand fuellte es
und das Widget las es nicht.

Bewacht wird hier ohne Browser:
1. die Auswahl des Logos aus den eingesammelten Kandidaten (bewerte_logokandidaten),
2. die Kennzeichnung und die Eingabepruefung,
3. der Schreibweg (Scan und Speichern der Konfiguration),
4. der Quelltext des Widgets.
Das Verhalten im Browser prueft tests/test_banner_logo_browser.py.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.logo_erkennung import (  # noqa: E402
    MARKE_AUTO,
    MARKE_DUNKEL,
    bereinige_eingabe,
    bewerte_logokandidaten,
    ist_automatisch,
)

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASIS = "https://kunde.de/"


def _bild(src, **kw):
    k = {"src": src, "b": 180, "h": 48, "x": 40, "y": 20, "logoWort": False, "kennung": src,
         "imKopf": False, "zurStartseite": False, "grund": [255, 255, 255]}
    k.update(kw)
    return k


# ============================================================================
# 1) Auswahl
# ============================================================================

class TestAuswahl:
    def test_logo_im_kopf_gewinnt(self):
        e = bewerte_logokandidaten({"breite": 1280, "bilder": [
            _bild("/bilder/hero.jpg", b=500, h=250, y=200),
            _bild("/wp-content/uploads/logo.png", logoWort=True, imKopf=True, zurStartseite=True),
        ], "icons": [{"href": "/favicon.png", "apple": False, "groesse": 32, "typ": "image/png"}]}, BASIS)
        assert e["url"] == "https://kunde.de/wp-content/uploads/logo.png"
        assert e["quelle"] == "kopfbild" and e["grund"] == "hell"
        assert e["gespeichert"] == e["url"] + MARKE_AUTO

    def test_dunkler_kopfbereich_wird_vermerkt(self):
        """Ein weisses Logo waere auf dem weissen Einstellungsfenster unsichtbar."""
        e = bewerte_logokandidaten({"bilder": [
            _bild("/logo-weiss.svg", logoWort=True, imKopf=True, grund=[17, 24, 39]),
        ]}, BASIS)
        assert e["grund"] == "dunkel"
        assert e["gespeichert"].endswith(MARKE_DUNKEL)

    def test_bild_ohne_hinweis_ist_kein_logo(self):
        """Irgendein Bild oben auf der Seite reicht nicht: lieber keins als ein falsches."""
        assert bewerte_logokandidaten({"bilder": [_bild("/bilder/team.jpg", y=300, x=900)]}, BASIS) is None

    @pytest.mark.parametrize("src", ["/img/facebook-icon.png", "/flags/de.png", "/img/hero-banner.jpg",
                                     "/siegel/trustpilot.png"])
    def test_symbole_im_kopf_sind_kein_logo(self, src):
        e = bewerte_logokandidaten({"bilder": [_bild(src, b=32, h=32, imKopf=True, kennung=src)]}, BASIS)
        assert e is None

    def test_zu_kleine_und_zu_grosse_bilder_fallen_raus(self):
        assert bewerte_logokandidaten({"bilder": [
            _bild("/logo-pixel.png", b=10, h=10, logoWort=True, imKopf=True),
            _bild("/logo-plakat.png", b=1200, h=600, logoWort=True, imKopf=True),
        ]}, BASIS) is None

    def test_bei_gleichstand_gewinnt_das_erste_im_dokument(self):
        e = bewerte_logokandidaten({"bilder": [
            _bild("/logo-eigen.png", logoWort=True, imKopf=True, zurStartseite=True),
            _bild("/partner-logo.png", logoWort=True, imKopf=True, zurStartseite=True),
        ]}, BASIS)
        assert e["url"].endswith("/logo-eigen.png")

    def test_ohne_kopfbild_zaehlt_die_angabe_in_schema_org(self):
        e = bewerte_logokandidaten({"bilder": [], "jsonld": ["https://cdn.kunde.de/marke.svg"],
                                    "icons": [{"href": "/apple.png", "apple": True, "groesse": 180}]}, BASIS)
        assert e["url"] == "https://cdn.kunde.de/marke.svg" and e["quelle"] == "jsonld"

    def test_danach_das_groesste_apple_touch_icon(self):
        e = bewerte_logokandidaten({"icons": [
            {"href": "/apple-76.png", "apple": True, "groesse": 76},
            {"href": "/apple-180.png", "apple": True, "groesse": 180},
            {"href": "/favicon.svg", "apple": False, "groesse": 0, "typ": "image/svg+xml"},
        ]}, BASIS)
        assert e["url"].endswith("/apple-180.png") and e["quelle"] == "apple-touch-icon"

    def test_favicon_nur_als_svg_oder_png(self):
        e = bewerte_logokandidaten({"icons": [
            {"href": "/favicon.ico", "apple": False, "groesse": 16, "typ": "image/x-icon"},
            {"href": "/icon.png", "apple": False, "groesse": 192, "typ": "image/png"},
        ]}, BASIS)
        assert e["url"].endswith("/icon.png") and e["quelle"] == "favicon"
        assert bewerte_logokandidaten({"icons": [
            {"href": "/favicon.ico", "apple": False, "groesse": 16, "typ": "image/x-icon"}]}, BASIS) is None

    @pytest.mark.parametrize("src", ["data:image/png;base64,AAAA", "javascript:alert(1)", "",
                                     "https://kunde.de/a\"onerror=\"x.png", "https://kunde.de/" + "a" * 600])
    def test_unbrauchbare_adressen_werden_nie_genommen(self, src):
        e = bewerte_logokandidaten({"bilder": [_bild(src, logoWort=True, imKopf=True)], "jsonld": [src]}, BASIS)
        assert e is None

    def test_relative_adresse_wird_absolut_und_verliert_ihr_fragment(self):
        e = bewerte_logokandidaten({"bilder": [
            _bild("img/logo.svg#teil", logoWort=True, imKopf=True)]}, "https://kunde.de/unterseite/")
        assert e["url"] == "https://kunde.de/unterseite/img/logo.svg"

    @pytest.mark.parametrize("muell", [None, [], "x", {}, {"bilder": "nein"}, {"bilder": [None, 7]},
                                       {"icons": [None, {"href": 5}], "jsonld": [None, 3]}])
    def test_muell_wirft_nicht(self, muell):
        assert bewerte_logokandidaten(muell, BASIS) is None


# ============================================================================
# 2) Kennzeichnung und Eingabe
# ============================================================================

def test_nur_leere_oder_selbst_erkannte_adressen_darf_der_scan_erneuern():
    assert ist_automatisch(None) and ist_automatisch("")
    assert ist_automatisch("https://kunde.de/logo.png" + MARKE_AUTO)
    assert ist_automatisch("https://kunde.de/logo.png" + MARKE_DUNKEL)
    assert not ist_automatisch("https://kunde.de/mein-logo.png")


def test_eingabe_aus_dem_dashboard():
    assert bereinige_eingabe(None) is None, "nicht mitgeschickt heisst: nichts aendern"
    assert bereinige_eingabe("") == "", "leer heisst: entfernen"
    assert bereinige_eingabe(" https://kunde.de/logo.png ") == "https://kunde.de/logo.png"
    assert bereinige_eingabe("https://kunde.de/l.png" + MARKE_DUNKEL) == "https://kunde.de/l.png" + MARKE_DUNKEL
    for muell in ("javascript:alert(1)", "data:image/png;base64,AA", "logo.png", 7, "https://kunde.de/a b.png"):
        assert bereinige_eingabe(muell) is None, f"{muell!r} darf nichts aendern"


# ============================================================================
# 3) Schreibweg
# ============================================================================

@pytest.mark.asyncio
async def test_logo_ueberschreibt_nur_leere_oder_selbst_erkannte_werte():
    import cookie_compliance_routes as modul
    pool = MagicMock()
    pool.execute = AsyncMock(return_value="UPDATE 1")
    ok = await modul._speichere_logo(pool, "kunde-de", {"gespeichert": "https://kunde.de/logo.png" + MARKE_AUTO})
    assert ok is True
    sql, site, wert = pool.execute.await_args.args
    assert site == "kunde-de" and wert.endswith(MARKE_AUTO)
    assert "custom_logo_url IS NULL" in sql and "LIKE '%#complyo-auto%'" in sql, (
        "Ohne diese Bedingung ueberschreibt jeder Scan ein von Hand gesetztes Logo."
    )


@pytest.mark.asyncio
async def test_ohne_logo_und_bei_fehler_passiert_nichts():
    import cookie_compliance_routes as modul
    pool = MagicMock()
    pool.execute = AsyncMock(side_effect=RuntimeError("Spalte fehlt"))
    assert await modul._speichere_logo(pool, "kunde-de", {}) is False
    pool.execute.assert_not_awaited()
    assert await modul._speichere_logo(pool, "kunde-de", {"gespeichert": "https://kunde.de/l.png#complyo-auto"}) is False


def _scan_client(monkeypatch, *, angemeldet, logo):
    import cookie_compliance_routes as modul
    app = FastAPI()
    app.include_router(modul.router)
    pool = MagicMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value={"id": 1, "user_id": 7})
    pool.execute = AsyncMock(return_value="UPDATE 1")
    monkeypatch.setattr(modul, "db_pool", pool)
    monkeypatch.setattr(modul, "get_current_user_optional", AsyncMock(return_value={"id": 7} if angemeldet else None))
    monkeypatch.setattr(modul, "get_user_id_from_token", AsyncMock(return_value=7))
    monkeypatch.setattr(modul, "get_user_site_ids", AsyncMock(return_value={"kunde-de"}))
    monkeypatch.setattr(modul, "get_user_website_site_id", AsyncMock(return_value="kunde-de"))
    scanner = MagicMock()
    scanner.scan_website = AsyncMock(return_value={
        "url": "https://kunde.de", "detected_services": [], "confidence": {},
        "privacy_findings": [], "detected_cms": None})
    monkeypatch.setattr(modul, "cookie_scanner", scanner)

    async def gerendert(url, timeout_s=20.0, logo_ziel=None, stil_ziel=None):
        if logo_ziel is not None and logo:
            logo_ziel.update(logo)
        return None
    import compliance_engine.markenfarben_gerendert as farben
    monkeypatch.setattr(farben, "markenfarben_gerendert", gerendert)
    from compliance_engine import cookie_pruefstufe
    monkeypatch.setattr(cookie_pruefstufe, "einreihen", AsyncMock(return_value={"zustand": "aus"}))
    return TestClient(app, raise_server_exceptions=False), pool


LOGO = {"url": "https://kunde.de/logo.png", "quelle": "kopfbild", "grund": "hell",
        "gespeichert": "https://kunde.de/logo.png" + MARKE_AUTO}


def test_scan_legt_das_erkannte_logo_ab(monkeypatch):
    client, pool = _scan_client(monkeypatch, angemeldet=True, logo=LOGO)
    daten = client.post("/api/cookie-compliance/scan",
                        json={"url": "https://kunde.de", "site_id": "kunde-de"}).json()
    assert daten["logo"] == {"url": "https://kunde.de/logo.png", "quelle": "kopfbild", "grund": "hell"}
    assert daten["logo_gespeichert"] is True
    logo_sql = [c for c in pool.execute.await_args_list if "custom_logo_url" in c.args[0]]
    assert len(logo_sql) == 1 and logo_sql[0].args[1] == "kunde-de"


def test_scan_ohne_anmeldung_zeigt_das_logo_speichert_es_aber_nicht(monkeypatch):
    client, pool = _scan_client(monkeypatch, angemeldet=False, logo=LOGO)
    daten = client.post("/api/cookie-compliance/scan", json={"url": "https://kunde.de"}).json()
    assert daten["logo"]["url"] == "https://kunde.de/logo.png"
    assert daten["logo_gespeichert"] is False
    assert [c for c in pool.execute.await_args_list if "custom_logo_url" in c.args[0]] == []


def test_scan_ohne_logo_schreibt_nichts_und_scheitert_nicht(monkeypatch):
    client, pool = _scan_client(monkeypatch, angemeldet=True, logo=None)
    daten = client.post("/api/cookie-compliance/scan",
                        json={"url": "https://kunde.de", "site_id": "kunde-de"}).json()
    assert daten["success"] is True and daten["logo"] is None
    assert [c for c in pool.execute.await_args_list if "custom_logo_url" in c.args[0]] == []


def _speicher_client(monkeypatch, vorhanden):
    import cookie_compliance_routes as modul
    app = FastAPI()
    app.include_router(modul.router)
    pool = MagicMock()
    pool.fetchrow = AsyncMock(side_effect=[vorhanden, {"id": 1, "revision": 2}])
    pool.execute = AsyncMock(return_value="UPDATE 1")
    monkeypatch.setattr(modul, "db_pool", pool)
    monkeypatch.setattr(modul, "get_current_user_required", AsyncMock(return_value={"id": 7}))
    monkeypatch.setattr(modul, "get_user_id_from_token", AsyncMock(return_value=7))
    monkeypatch.setattr(modul, "require_module", AsyncMock(return_value=True))
    monkeypatch.setattr(modul, "get_user_site_ids", AsyncMock(return_value={"kunde-de"}))
    return TestClient(app, raise_server_exceptions=False), pool


def _gespeichertes_logo(pool):
    update = [c for c in pool.fetchrow.await_args_list if "UPDATE cookie_banner_configs" in c.args[0]]
    assert len(update) == 1
    sql, args = update[0].args[0], update[0].args[1:]
    stelle = int(sql.split("custom_logo_url = $")[1].split(",")[0])
    return args[stelle - 1]


@pytest.mark.parametrize("eingabe, erwartet", [
    ({}, "https://kunde.de/logo.png#complyo-auto"),                       # Feld nicht mitgeschickt
    ({"custom_logo_url": None}, "https://kunde.de/logo.png#complyo-auto"),
    ({"custom_logo_url": ""}, None),                                       # bewusst entfernt
    ({"custom_logo_url": "https://kunde.de/neu.svg"}, "https://kunde.de/neu.svg"),
    ({"custom_logo_url": "javascript:alert(1)"}, "https://kunde.de/logo.png#complyo-auto"),
])
def test_speichern_der_konfiguration_loescht_das_logo_nicht_versehentlich(monkeypatch, eingabe, erwartet):
    """Das Dashboard schickt das Feld nicht immer mit. Vorher setzte jedes
    Speichern custom_logo_url auf NULL."""
    client, pool = _speicher_client(
        monkeypatch, {"id": 1, "custom_logo_url": "https://kunde.de/logo.png#complyo-auto"})
    rumpf = {"site_id": "kunde-de", "texts": {"de": {}}, "services": []}
    rumpf.update(eingabe)
    resp = client.post("/api/cookie-compliance/config", json=rumpf, headers={"Authorization": "Bearer x"})
    assert resp.status_code == 200, resp.text
    assert _gespeichertes_logo(pool) == erwartet


# ============================================================================
# 4) Quelltext des Widgets
# ============================================================================

def _widget():
    with open(os.path.join(BACKEND, "widgets", "cookie_banner_v2.js"), encoding="utf-8") as fh:
        return fh.read()


def test_kein_festes_c_mehr_im_einstellungsfenster():
    quelle = _widget()
    assert '<div class="cps-logo">C</div>' not in quelle
    rumpf = quelle[quelle.index("renderSettingsHTML() {"):]
    rumpf = rumpf[:rumpf.index("<!-- Description -->")]
    assert "${this.logoHTML()}" in rumpf


def test_widget_liest_das_logo_aus_der_konfiguration_und_bindet_den_rueckfall():
    quelle = _widget()
    assert "serverConfig.custom_logo_url" in quelle
    assert "this.bindeLogo(modal)" in quelle
    logo = quelle[quelle.index("logoHTML() {"):quelle.index("renderSettingsHTML() {")]
    assert "sanitizeUrl(" in logo, "Die Adresse geht ungeprueft ins Markup."
    assert "onerror=" not in logo and "onload=" not in logo, (
        "Inline-Handler blockiert eine strenge Content-Security-Policy der Kundenseite."
    )
    assert "addEventListener('error'" in logo


def test_konfigurationsroute_liefert_das_feld_aus():
    with open(os.path.join(BACKEND, "cookie_compliance_routes.py"), encoding="utf-8") as fh:
        quelle = fh.read()
    start = quelle.index('@router.get("/api/cookie-compliance/config/{site_id}")')
    rumpf = quelle[start:start + 9000]
    assert "custom_logo_url" in rumpf, "Die oeffentliche Konfiguration liefert das Logo nicht mehr aus."
