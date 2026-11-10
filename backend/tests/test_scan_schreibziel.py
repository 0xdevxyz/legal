"""
Der Cookie-Scan misst fuer jeden, speichert aber nur am eigenen Ziel.

Befund 10.11.2026, live gemessen: `POST /api/cookie-compliance/scan` ohne
Anmeldung, mit der site_id einer fremden Website, setzte deren `services`
neu. Davor stand nur das CSRF-Doppelcookie, das sich jeder mit einem GET
selbst holt. Die site_id steht im Einbaucode jeder Kundenseite. Ein Fremder
konnte damit die Dienstliste eines Kundenbanners leeren: der Banner zeigt
dann keine Dienste mehr und die Cookie-Richtlinie ist falsch.

Dieselbe Luecke fuer angemeldete Konten: `POST /deep-cookie-scan/{id}/apply`
nahm jede site_id aus dem Rumpf.

Bewacht wird:
1. die Zielregel selbst (scan_schreibziel),
2. die Route: ohne Ziel kein execute und keine Pruefstufe mit Anwenden,
3. der Quelltext: Speichern haengt am Schreibziel, nicht an der site_id.
"""

import inspect
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ============================================================================
# 1) Die Zielregel
# ============================================================================

def _regel(monkeypatch, eigene, primaer, zeile_vorhanden=False):
    import cookie_compliance_routes as modul
    monkeypatch.setattr(modul, "get_user_site_ids", AsyncMock(return_value=set(eigene)))
    monkeypatch.setattr(modul, "get_user_website_site_id", AsyncMock(return_value=primaer))
    pool = MagicMock()
    pool.fetchrow = AsyncMock(return_value={"id": 1} if zeile_vorhanden else None)
    return modul, pool


@pytest.mark.asyncio
async def test_ohne_anmeldung_gibt_es_kein_ziel(monkeypatch):
    modul, pool = _regel(monkeypatch, eigene={"kunde-de"}, primaer="kunde-de")
    assert await modul.scan_schreibziel(None, "kunde-de", pool) is None


@pytest.mark.asyncio
async def test_eigene_website_ist_das_ziel(monkeypatch):
    modul, pool = _regel(monkeypatch, eigene={"kunde-de"}, primaer="kunde-de")
    assert await modul.scan_schreibziel(7, "kunde-de", pool) == "kunde-de"


@pytest.mark.asyncio
async def test_agenturkonto_trifft_die_gewaehlte_website_nicht_die_primaere(monkeypatch):
    modul, pool = _regel(monkeypatch, eigene={"a-de", "b-de"}, primaer="a-de")
    assert await modul.scan_schreibziel(7, "b-de", pool) == "b-de"


@pytest.mark.asyncio
async def test_fremde_website_faellt_auf_die_eigene_primaere(monkeypatch):
    modul, pool = _regel(monkeypatch, eigene={"kunde-de"}, primaer="kunde-de")
    assert await modul.scan_schreibziel(7, "opfer-de", pool) == "kunde-de"


@pytest.mark.asyncio
async def test_konto_mit_websites_aber_ohne_primaere_schreibt_nichts_fremdes(monkeypatch):
    modul, pool = _regel(monkeypatch, eigene={"a-de", "b-de"}, primaer=None)
    assert await modul.scan_schreibziel(7, "opfer-de", pool) is None


@pytest.mark.asyncio
async def test_konto_ohne_website_darf_neu_anlegen(monkeypatch):
    modul, pool = _regel(monkeypatch, eigene=set(), primaer=None, zeile_vorhanden=False)
    assert await modul.scan_schreibziel(7, "neu-de", pool) == "neu-de"


@pytest.mark.asyncio
async def test_konto_ohne_website_fasst_keine_vorhandene_zeile_an(monkeypatch):
    """Vorhanden heisst: gehoert jemand anderem oder ist verwaist. Beides nicht meins."""
    modul, pool = _regel(monkeypatch, eigene=set(), primaer=None, zeile_vorhanden=True)
    assert await modul.scan_schreibziel(7, "opfer-de", pool) is None


# ============================================================================
# 2) Die Route
# ============================================================================

def _aufbau(monkeypatch, *, nutzer, eigene=(), primaer=None, zeile_vorhanden=True):
    import cookie_compliance_routes as modul
    app = FastAPI()
    app.include_router(modul.router)
    client = TestClient(app, raise_server_exceptions=False)

    pool = MagicMock()
    pool.fetch = AsyncMock(return_value=[
        {"service_key": "google_analytics_ga4", "name": "Google Analytics 4",
         "category": "analytics", "description": "", "cookies": []},
    ])
    pool.fetchrow = AsyncMock(return_value={"id": 1} if zeile_vorhanden else None)
    pool.execute = AsyncMock(return_value="UPDATE 1")
    monkeypatch.setattr(modul, "db_pool", pool)

    monkeypatch.setattr(modul, "get_current_user_optional", AsyncMock(return_value=nutzer))
    monkeypatch.setattr(modul, "get_user_id_from_token", AsyncMock(return_value=7))
    monkeypatch.setattr(modul, "get_user_site_ids", AsyncMock(return_value=set(eigene)))
    monkeypatch.setattr(modul, "get_user_website_site_id", AsyncMock(return_value=primaer))

    scanner = MagicMock()
    scanner.scan_website = AsyncMock(return_value={
        "url": "https://opfer.de",
        "detected_services": ["google_analytics_ga4"],
        "confidence": {"google_analytics_ga4": 0.9},
        "privacy_findings": [],
        "detected_cms": None,
    })
    monkeypatch.setattr(modul, "cookie_scanner", scanner)

    # Kein Browser im Test: Farben und Pruefstufe sind hier nur Zeugen.
    import compliance_engine.markenfarben_gerendert as farben
    monkeypatch.setattr(farben, "markenfarben_gerendert", AsyncMock(return_value=None))
    from compliance_engine import cookie_pruefstufe
    einreihen = AsyncMock(return_value={"zustand": "wartend"})
    monkeypatch.setattr(cookie_pruefstufe, "einreihen", einreihen)

    return client, pool, einreihen


def _schreibaufrufe(pool):
    return [a for a in pool.execute.await_args_list
            if "cookie_banner_configs" in str(a.args[0])]


def test_ohne_anmeldung_wird_gemessen_aber_nichts_geschrieben(monkeypatch):
    client, pool, einreihen = _aufbau(monkeypatch, nutzer=None)

    resp = client.post("/api/cookie-compliance/scan",
                       json={"url": "https://opfer.de", "site_id": "opfer-de"})

    assert resp.status_code == 200, resp.text
    daten = resp.json()
    assert daten["success"] is True
    assert daten["total_found"] == 1, "Die Messung selbst muss weiter ankommen."
    assert daten["config_updated"] is False
    assert daten["speicherung"] == "ohne_anmeldung"
    assert _schreibaufrufe(pool) == [], (
        "Ohne Anmeldung darf der Scan keine Bannerkonfiguration anfassen."
    )
    # Die Browser-Pruefung misst weiter, ergaenzt aber nichts.
    assert einreihen.await_args.kwargs["anwenden_ja"] is False


def test_ohne_anmeldung_zaehlt_die_gemessene_adresse_nicht_die_site_id(monkeypatch):
    """Sonst stuende unter der Kennung des Kunden der Pruefstand einer anderen Seite."""
    client, pool, einreihen = _aufbau(monkeypatch, nutzer=None)

    daten = client.post("/api/cookie-compliance/scan",
                        json={"url": "https://anders.de", "site_id": "kunde-de"}).json()

    assert daten["site_id"] == "anders-de"
    assert einreihen.await_args.args[0] == "anders-de"


def test_angemeldet_an_der_eigenen_website_wird_gespeichert(monkeypatch):
    client, pool, einreihen = _aufbau(
        monkeypatch, nutzer={"id": 7}, eigene={"kunde-de"}, primaer="kunde-de")

    daten = client.post("/api/cookie-compliance/scan",
                        json={"url": "https://kunde.de", "site_id": "kunde-de"}).json()

    assert daten["config_updated"] is True
    assert daten["speicherung"] == "gespeichert"
    schreiben = _schreibaufrufe(pool)
    assert len(schreiben) == 1
    assert schreiben[0].args[1] == "kunde-de"
    einreihen.assert_awaited_once()


def test_agenturkonto_speichert_an_der_gewaehlten_website(monkeypatch):
    client, pool, _ = _aufbau(
        monkeypatch, nutzer={"id": 7}, eigene={"a-de", "b-de"}, primaer="a-de")

    daten = client.post("/api/cookie-compliance/scan",
                        json={"url": "https://b.de", "site_id": "b-de"}).json()

    assert daten["site_id"] == "b-de"
    assert _schreibaufrufe(pool)[0].args[1] == "b-de", (
        "Der Scan von Website B darf nicht die Dienstliste der primaeren Website A setzen."
    )


def test_angemeldet_an_fremder_website_trifft_die_fremde_nie(monkeypatch):
    client, pool, _ = _aufbau(
        monkeypatch, nutzer={"id": 7}, eigene={"kunde-de"}, primaer="kunde-de")

    client.post("/api/cookie-compliance/scan",
                json={"url": "https://opfer.de", "site_id": "opfer-de"})

    ziele = {a.args[1] for a in _schreibaufrufe(pool)}
    assert "opfer-de" not in ziele
    assert ziele <= {"kunde-de"}


def test_konto_ohne_website_ueberschreibt_keine_vorhandene_konfiguration(monkeypatch):
    client, pool, einreihen = _aufbau(
        monkeypatch, nutzer={"id": 7}, eigene=set(), primaer=None, zeile_vorhanden=True)

    daten = client.post("/api/cookie-compliance/scan",
                        json={"url": "https://opfer.de", "site_id": "opfer-de"}).json()

    assert daten["config_updated"] is False
    assert daten["speicherung"] == "fremde_website"
    assert _schreibaufrufe(pool) == []
    assert einreihen.await_args.kwargs["anwenden_ja"] is False


def test_fehler_beim_ermitteln_des_kontos_heisst_nicht_speichern(monkeypatch):
    client, pool, _ = _aufbau(
        monkeypatch, nutzer={"id": 7}, eigene={"opfer-de"}, primaer="opfer-de")
    import cookie_compliance_routes as modul
    monkeypatch.setattr(modul, "get_user_id_from_token",
                        AsyncMock(side_effect=RuntimeError("db weg")))

    daten = client.post("/api/cookie-compliance/scan",
                        json={"url": "https://opfer.de", "site_id": "opfer-de"}).json()

    assert daten["config_updated"] is False
    assert _schreibaufrufe(pool) == []


# ============================================================================
# 3) Quelltext: der Schreibweg haengt am Schreibziel
# ============================================================================

def test_scan_route_speichert_nur_ueber_das_schreibziel():
    import cookie_compliance_routes as modul
    quelle = inspect.getsource(modul.scan_website)
    assert quelle.count("cookie_banner_configs") >= 3, (
        "Die Schreibstellen der Scan-Route wurden nicht gefunden. Dann liest "
        "dieser Waechter die falsche Funktion und prueft nichts."
    )
    i_ziel = quelle.index("if schreibziel:")
    for stelle in ("UPDATE cookie_banner_configs", "INSERT INTO cookie_banner_configs"):
        assert quelle.index(stelle) > i_ziel, (
            f"'{stelle}' steht vor der Pruefung des Schreibziels."
        )
    assert "if site_id:\n            # Prüfe ob Config existiert" not in quelle, (
        "Die Scan-Route speichert wieder fuer jede uebergebene site_id."
    )


def test_tiefenscan_uebernahme_prueft_die_zugehoerigkeit():
    pfad = os.path.join(BACKEND, "deep_cookie_scanner_routes.py")
    with open(pfad, encoding="utf-8") as fh:
        quelle = fh.read()
    start = quelle.index("async def apply_scan_to_banner")
    rumpf = quelle[start:start + 4000]
    assert "UPDATE cookie_banner_configs" in rumpf, "Schreibstelle nicht gefunden."
    assert rumpf.index("get_user_site_ids") < rumpf.index("UPDATE cookie_banner_configs"), (
        "Die Uebernahme des Tiefenscans schreibt in eine site_id aus dem Rumpf, "
        "ohne zu pruefen, ob sie dem Konto gehoert."
    )
