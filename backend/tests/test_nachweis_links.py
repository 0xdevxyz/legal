"""
Die Nachweis-Adressen im Dashboard.

Der oeffentliche Nachweis lag seit August bereit und kein Kunde hat ihn
gesehen: kein Link, kein Einbettungscode. Dieser Router liefert beides. Er
gibt den Zugriffsschluessel aus, deshalb angemeldet, und er sagt "vorhanden"
nur, wenn der oeffentliche Endpunkt auch wirklich eine Seite liefert.
"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import nachweis_links_routes as nl  # noqa: E402
import nachweis_routes as nw  # noqa: E402
from compliance_engine.nachweis_generator import nachweis_token  # noqa: E402
from dependencies import get_current_user, get_db  # noqa: E402

GEHEIM = "test-geheimnis"
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pool(zeilen):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=zeilen)
    pool = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return pool, conn


def _client(monkeypatch, zeilen, user=None, geheim=GEHEIM):
    if geheim:
        monkeypatch.setenv("COMPLYO_NACHWEIS_SECRET", geheim)
    else:
        monkeypatch.delenv("COMPLYO_NACHWEIS_SECRET", raising=False)
    pool, conn = _pool(zeilen)
    app = FastAPI()
    app.include_router(nl.router)
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: pool
    return TestClient(app), conn


NUTZER = {"id": 7, "user_id": 7, "email": "k@example.de"}
ZEILEN = [
    {"id": 1, "url": "https://www.beispiel.de/"},
    {"id": 2, "url": "https://ohne-messung.de"},
]


async def _daten(site_id):
    if site_id == "beispiel-de":
        return {"gemessen_am": "2026-09-11 08:00", "site_url": "https://www.beispiel.de/"}
    return None


class TestAdressen:
    def test_ohne_anmeldung_kein_schluessel(self, monkeypatch):
        client, _ = _client(monkeypatch, ZEILEN)
        r = client.get("/api/nachweis-links")
        assert r.status_code in (401, 403)

    def test_ohne_geheimnis_nicht_verfuegbar_mit_grund(self, monkeypatch):
        client, conn = _client(monkeypatch, ZEILEN, NUTZER, geheim="")
        r = client.get("/api/nachweis-links")
        assert r.status_code == 200
        assert r.json()["verfuegbar"] is False
        assert "COMPLYO_NACHWEIS_SECRET" in r.json()["grund"]
        assert r.json()["websites"] == []
        conn.fetch.assert_not_called()

    def test_je_website_adressen_und_stand(self, monkeypatch):
        monkeypatch.setattr(nw, "_daten_fuer", _daten)
        monkeypatch.setenv("COMPLYO_PUBLIC_URL", "https://complyo.de/")
        monkeypatch.setenv("PUBLIC_API_BASE", "https://api.complyo.de")
        client, conn = _client(monkeypatch, ZEILEN, NUTZER)
        r = client.get("/api/nachweis-links")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["verfuegbar"] is True
        assert [w["site_id"] for w in body["websites"]] == ["beispiel-de", "ohne-messung-de"]

        # Nur die Websites DIESES Nutzers.
        assert conn.fetch.call_args.args[-1] == 7

        mit, ohne = body["websites"]
        token = nachweis_token("beispiel-de", GEHEIM)
        assert mit["nachweis_vorhanden"] is True
        assert mit["gemessen_am"] == "2026-09-11 08:00"
        assert mit["urls"] == {
            "nachweis_seite": f"https://complyo.de/nachweis/beispiel-de/{token}",
            "erklaerung_seite": f"https://complyo.de/nachweis/beispiel-de/{token}/erklaerung",
            "nachweis_json": f"https://api.complyo.de/api/nachweis/beispiel-de/{token}",
            "erklaerung_markdown": f"https://api.complyo.de/api/nachweis/beispiel-de/{token}/erklaerung",
        }
        assert mit["einbettung"] == (
            f'<a href="https://complyo.de/nachweis/beispiel-de/{token}">'
            "Prüfnachweis zur Barrierefreiheit</a>"
        )
        assert ohne["nachweis_vorhanden"] is False
        assert ohne["gemessen_am"] is None
        # Die Adressen gibt es trotzdem: sobald gemessen wurde, stimmen sie.
        assert ohne["urls"]["nachweis_seite"].endswith(nachweis_token("ohne-messung-de", GEHEIM))

    def test_schluessel_ist_derselbe_wie_am_oeffentlichen_endpunkt(self):
        """Sonst zeigt das Dashboard einen Link, der auf 404 laeuft."""
        adressen = nl.adressen_fuer("beispiel-de", nachweis_token("beispiel-de", GEHEIM))
        assert adressen["nachweis_json"].endswith(
            "/api/nachweis/beispiel-de/" + nachweis_token("beispiel-de", GEHEIM))

    def test_einbettung_escaped(self):
        assert '&quot;' in nl.einbettung_fuer('https://x.de/"')


class TestRegistrierung:
    def test_router_haengt_in_der_anwendung(self):
        src = open(os.path.join(_BACKEND, "main_production.py"), encoding="utf-8").read()
        assert "app.include_router(nachweis_links_router)" in src

    def test_keine_csrf_ausnahme(self):
        """Angemeldet, gibt den Schluessel aus: keine Ausnahme noetig, keine erwuenscht."""
        from csrf_middleware import EXEMPT_PATHS, EXEMPT_PREFIXES
        assert "/api/nachweis-links" not in EXEMPT_PATHS
        assert not "/api/nachweis-links".startswith(EXEMPT_PREFIXES)
