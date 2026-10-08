"""
Ersteinrichtung nach Grundsystem.

Der Cookie-Scan erkannte Services, aber nicht die Plattform. Danach zeigte der
Wizard immer dieselben drei Kacheln, und die fertigen Plugins fuer WordPress
und Joomla lagen unausgeliefert im Repo (die eingecheckten Zips dazu waren
veraltet). Diese Tests bewachen:

1. Erkennung: eine Quelle fuer Hauptscan und Cookie-Scan.
2. Einrichtungsweg: WordPress/Joomla -> Plugin, Rest -> Schnipsel.
3. Scan-Route: die Felder kommen beim Client an.
4. Plugin-Route: liefert das Zip, 404 fuer Unbekanntes.
5. Pakete: das ausgelieferte Zip entspricht dem Quellordner (Datei fuer Datei).
"""

import hashlib
import os
import sys
import zipfile
from unittest.mock import AsyncMock, MagicMock

import pytest
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.grundsystem import (  # noqa: E402
    PLUGIN_PAKETE,
    einrichtungsweg,
    erkenne_grundsystem,
)

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = os.path.abspath(os.path.join(BACKEND, ".."))


# ============================================================================
# 1) Erkennung
# ============================================================================

class TestErkennung:
    def test_wordpress_ueber_pfad(self):
        html = '<html><head><link href="/wp-content/themes/x/style.css"></head><body>x</body></html>'
        assert erkenne_grundsystem(html) == "WordPress"

    def test_generator_meta_in_beliebiger_attributreihenfolge(self):
        assert erkenne_grundsystem('<meta name="generator" content="Joomla! - Open Source">') == "Joomla"
        assert erkenne_grundsystem('<meta content="Joomla! - Open Source" name="generator">') == "Joomla"

    def test_joomla_ueber_medienpfad(self):
        assert erkenne_grundsystem('<script src="/media/jui/js/jquery.min.js"></script>') == "Joomla"

    def test_header_zaehlt(self):
        assert erkenne_grundsystem("<html></html>", {"X-Shopify-Stage": "production"}) == "Shopify"

    def test_statisches_html_ist_nichts(self):
        assert erkenne_grundsystem("<html><body><h1>Hallo</h1></body></html>") is None

    def test_hauptscan_nutzt_dieselbe_quelle(self):
        """ComplianceScanner._detect_cms darf keine zweite Signaturliste haben."""
        from compliance_engine.scanner import ComplianceScanner
        soup = BeautifulSoup('<meta name="generator" content="WordPress 6.5">', "html.parser")
        assert ComplianceScanner._detect_cms(soup) == "WordPress"
        import inspect
        quelle = inspect.getsource(ComplianceScanner._detect_cms)
        assert "erkenne_grundsystem" in quelle
        assert "wp-content" not in quelle, "Signaturen gehoeren nach grundsystem.py"


# ============================================================================
# 2) Einrichtungsweg
# ============================================================================

class TestEinrichtungsweg:
    def test_wordpress_bekommt_plugin(self):
        w = einrichtungsweg("WordPress")
        assert w["cms_key"] == "wordpress"
        assert w["einrichtung"] == "plugin"
        assert w["plugin_download_pfad"] == "/api/cookie-compliance/plugin/wordpress"

    def test_joomla_bekommt_plugin(self):
        w = einrichtungsweg("Joomla")
        assert w["einrichtung"] == "plugin"
        assert w["plugin_download_pfad"].endswith("/joomla")

    def test_unbekannt_ist_html_mit_schnipsel(self):
        w = einrichtungsweg(None)
        assert w == {
            "detected_cms": None,
            "cms_key": "html",
            "einrichtung": "snippet",
            "plugin_download_pfad": None,
            "anleitung": w["anleitung"],
        }
        assert "</head>" in w["anleitung"]

    def test_shopify_schnipsel_mit_eigenem_hinweis(self):
        w = einrichtungsweg("Shopify")
        assert w["einrichtung"] == "snippet"
        assert "theme.liquid" in w["anleitung"]


# ============================================================================
# 3) Scan-Route reicht das Grundsystem durch
# ============================================================================

def _client():
    import cookie_compliance_routes
    from cookie_compliance_routes import router
    app = FastAPI()
    app.include_router(router)
    return cookie_compliance_routes, TestClient(app, raise_server_exceptions=False)


def test_scan_route_liefert_grundsystem_und_weg(monkeypatch):
    modul, client = _client()

    pool = MagicMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value={"id": 1})
    pool.execute = AsyncMock(return_value="UPDATE 1")
    monkeypatch.setattr(modul, "db_pool", pool)
    monkeypatch.setattr(modul, "get_current_user_optional", AsyncMock(return_value=None))

    scanner = MagicMock()
    scanner.scan_website = AsyncMock(return_value={
        "url": "https://kunde.de",
        "detected_services": [],
        "confidence": {},
        "privacy_findings": [],
        "detected_cms": "WordPress",
        "scan_timestamp": "2026-10-08T00:00:00",
    })
    monkeypatch.setattr(modul, "cookie_scanner", scanner)

    resp = client.post("/api/cookie-compliance/scan", json={"url": "https://kunde.de"})
    assert resp.status_code == 200, resp.text
    daten = resp.json()
    assert daten["success"] is True
    assert daten["detected_cms"] == "WordPress"
    assert daten["cms_key"] == "wordpress"
    assert daten["einrichtung"] == "plugin"
    assert daten["plugin_download_pfad"] == "/api/cookie-compliance/plugin/wordpress"
    assert daten["anleitung"]


def test_scan_route_ohne_grundsystem_ist_html(monkeypatch):
    modul, client = _client()
    pool = MagicMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.execute = AsyncMock(return_value="INSERT 0 1")
    monkeypatch.setattr(modul, "db_pool", pool)
    monkeypatch.setattr(modul, "get_current_user_optional", AsyncMock(return_value=None))
    scanner = MagicMock()
    scanner.scan_website = AsyncMock(return_value={
        "url": "https://statisch.de", "detected_services": [], "confidence": {},
        "privacy_findings": [], "detected_cms": None,
    })
    monkeypatch.setattr(modul, "cookie_scanner", scanner)

    daten = client.post("/api/cookie-compliance/scan", json={"url": "https://statisch.de"}).json()
    assert daten["cms_key"] == "html"
    assert daten["einrichtung"] == "snippet"
    assert daten["plugin_download_pfad"] is None


# ============================================================================
# 4) Plugin-Route
# ============================================================================

def test_plugin_route_liefert_zip():
    _, client = _client()
    resp = client.get("/api/cookie-compliance/plugin/wordpress")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/zip")
    assert 'filename="complyo-compliance.zip"' in resp.headers["content-disposition"]
    assert resp.content[:2] == b"PK"


def test_plugin_route_joomla_und_grossschreibung():
    _, client = _client()
    assert client.get("/api/cookie-compliance/plugin/Joomla").status_code == 200


def test_plugin_route_unbekanntes_cms_404():
    _, client = _client()
    assert client.get("/api/cookie-compliance/plugin/typo3").status_code == 404
    assert client.get("/api/cookie-compliance/plugin/html").status_code == 404


def test_plugin_route_ist_get_und_braucht_keine_csrf_ausnahme():
    """GET laeuft an der CSRF-Schranke vorbei; eine Ausnahme waere nur
    Angriffsflaeche (vgl. test_csrf_scanwege)."""
    from csrf_middleware import EXEMPT_PATHS
    assert not any(p.startswith("/api/cookie-compliance/plugin") for p in EXEMPT_PATHS)


# ============================================================================
# 5) Ausgeliefertes Paket == Quellordner
# ============================================================================

QUELLEN = {
    "wordpress": ("wordpress-plugin/complyo-compliance", "complyo-compliance"),
    "joomla": ("joomla-plugin/plg_system_complyo", "plg_system_complyo"),
}


def _dateien(ordner):
    aus = {}
    for wurzel, _, namen in os.walk(ordner):
        for n in namen:
            if n.startswith(".") or n.endswith((".zip", ".pyc")):
                continue
            voll = os.path.join(wurzel, n)
            rel = os.path.relpath(voll, ordner).replace(os.sep, "/")
            with open(voll, "rb") as fh:
                aus[rel] = hashlib.sha256(fh.read()).hexdigest()
    return aus


@pytest.mark.parametrize("cms", sorted(QUELLEN))
def test_paket_entspricht_quellordner(cms):
    quelle_rel, praefix = QUELLEN[cms]
    quelle = os.path.join(REPO, quelle_rel)
    if not os.path.isdir(quelle):
        pytest.skip(f"Quellordner {quelle_rel} nicht gemountet (Test braucht das ganze Repo, siehe scripts/tests-lokal.sh)")
    zip_pfad = os.path.join(BACKEND, "plugins", PLUGIN_PAKETE[cms]["datei"])
    assert os.path.isfile(zip_pfad), "Zip fehlt: scripts/plugins-paketieren.py laufen lassen"

    erwartet = _dateien(quelle)
    assert erwartet, "Quellordner ist leer"
    with zipfile.ZipFile(zip_pfad) as zf:
        im_zip = {}
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            assert name.startswith(praefix + "/"), f"{name} liegt nicht unter {praefix}/"
            im_zip[name[len(praefix) + 1:]] = hashlib.sha256(zf.read(name)).hexdigest()

    assert set(im_zip) == set(erwartet), (
        f"Dateiliste weicht ab. Nur im Zip: {set(im_zip) - set(erwartet)}, "
        f"nur im Ordner: {set(erwartet) - set(im_zip)}. scripts/plugins-paketieren.py laufen lassen."
    )
    abweichend = [n for n in erwartet if erwartet[n] != im_zip[n]]
    assert not abweichend, f"Inhalt veraltet: {abweichend}. scripts/plugins-paketieren.py laufen lassen."


def test_wordpress_paket_traegt_die_version_der_quelle():
    quelle = os.path.join(REPO, "wordpress-plugin/complyo-compliance/complyo-compliance.php")
    if not os.path.isfile(quelle):
        pytest.skip("Quellordner nicht gemountet")
    with open(quelle, encoding="utf-8") as fh:
        version_quelle = next(l for l in fh if "Version:" in l).strip()
    with zipfile.ZipFile(os.path.join(BACKEND, "plugins", "complyo-compliance.zip")) as zf:
        php = zf.read("complyo-compliance/complyo-compliance.php").decode("utf-8")
    assert version_quelle in php


# ============================================================================
# 6) Grundsystem der eigenen Website aus dem letzten Hauptscan
# ============================================================================

def test_grundsystem_route_liest_letzten_hauptscan(monkeypatch):
    modul, client = _client()
    pool = MagicMock()
    pool.fetchrow = AsyncMock(return_value={"scan_data": '{"detected_cms": "Joomla", "issues": []}'})
    monkeypatch.setattr(modul, "db_pool", pool)
    monkeypatch.setattr(modul, "get_current_user_required", AsyncMock(return_value={"id": 7}))
    monkeypatch.setattr(modul, "get_user_id_from_token", AsyncMock(return_value=7))

    daten = client.get("/api/cookie-compliance/grundsystem", headers={"Authorization": "Bearer x"}).json()
    assert daten["success"] is True
    assert daten["detected_cms"] == "Joomla"
    assert daten["einrichtung"] == "plugin"
    assert daten["plugin_download_pfad"] == "/api/cookie-compliance/plugin/joomla"


def test_grundsystem_route_ohne_scan_ist_html(monkeypatch):
    modul, client = _client()
    pool = MagicMock()
    pool.fetchrow = AsyncMock(return_value=None)
    monkeypatch.setattr(modul, "db_pool", pool)
    monkeypatch.setattr(modul, "get_current_user_required", AsyncMock(return_value={"id": 7}))
    monkeypatch.setattr(modul, "get_user_id_from_token", AsyncMock(return_value=7))

    daten = client.get("/api/cookie-compliance/grundsystem", headers={"Authorization": "Bearer x"}).json()
    assert daten["cms_key"] == "html"
    assert daten["einrichtung"] == "snippet"


def test_grundsystem_route_braucht_anmeldung(monkeypatch):
    from fastapi import HTTPException
    modul, client = _client()
    monkeypatch.setattr(modul, "db_pool", MagicMock())
    monkeypatch.setattr(modul, "get_current_user_required", AsyncMock(side_effect=HTTPException(status_code=401)))
    assert client.get("/api/cookie-compliance/grundsystem").status_code == 401
