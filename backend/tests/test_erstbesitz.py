"""
Erstbesitz: hat die Bannerkonfiguration einer Website einen Besitzer, zaehlt
die Website nur fuer ihn.

Befund 10./11.11.2026: Besitz entstand allein dadurch, dass ein Konto die
Adresse anlegt (`tracked_websites`, kein Domainnachweis). `get_user_site_ids`
nahm jede so angelegte Adresse als eigene. Ein Konto konnte damit die Adresse
eines fremden Kunden anlegen und danach dessen Banner, Alt-Texte und
Widget-Einstellungen aendern. `POST /api/cookie-compliance/config` liess ein
Konto ganz ohne Website sogar ungeprueft durch.

Gemessen vor dem Einbau auf der Produktionsdatenbank: 11 Konfigurationen, alle
mit Besitzer; 12 Adressen in 2 Konten; keine Adresse in zwei Konten. Die Regel
aendert also fuer niemanden im Bestand etwas.

Ein gewollter Besitzerwechsel ist Handarbeit des Betreibers (user_id der Zeile
umsetzen). Ein echter Domainnachweis ersetzt diese Regel nicht, er kaeme dazu.
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
# 1) get_user_site_ids gegen eine kleine Datenbank-Attrappe
# ============================================================================

class _Verbindung:
    def __init__(self, adressen, konfigurationen):
        self.adressen = adressen                # {user_id: [url, ...]}
        self.konfigurationen = konfigurationen  # {site_id: besitzer oder None}
        self.abfragen = []

    async def fetch(self, sql, *args):
        self.abfragen.append(sql)
        if "FROM tracked_websites" in sql:
            return [{"url": u} for u in self.adressen.get(args[0], [])]
        if "user_id <> $2" in sql:
            kandidaten, konto = args
            return [{"site_id": s} for s, b in self.konfigurationen.items()
                    if s in kandidaten and b is not None and b != konto]
        if "FROM cookie_banner_configs WHERE user_id = $1" in sql:
            return [{"site_id": s} for s, b in self.konfigurationen.items() if b == args[0]]
        raise AssertionError(f"unerwartete Abfrage: {sql}")


class _Pool:
    def __init__(self, verbindung):
        self.verbindung = verbindung

    def acquire(self):
        verbindung = self.verbindung

        class _Kontext:
            async def __aenter__(self):
                return verbindung

            async def __aexit__(self, *a):
                return False
        return _Kontext()


def _mit_datenbank(monkeypatch, adressen, konfigurationen):
    import cookie_compliance_routes as modul
    verbindung = _Verbindung(adressen, konfigurationen)
    monkeypatch.setattr(modul, "db_pool", _Pool(verbindung))
    return modul, verbindung


@pytest.mark.asyncio
async def test_adresse_eines_fremden_kunden_anlegen_macht_sie_nicht_zur_eigenen(monkeypatch):
    modul, _ = _mit_datenbank(
        monkeypatch,
        adressen={1: ["https://kunde.de"], 2: ["https://www.kunde.de/", "https://eigene.de"]},
        konfigurationen={"kunde-de": 1},
    )
    assert await modul.get_user_site_ids(1) == {"kunde-de"}
    assert await modul.get_user_site_ids(2) == {"eigene-de"}, (
        "Konto 2 hat die Adresse von Konto 1 nur angelegt. Das darf kein Besitz sein."
    )


@pytest.mark.asyncio
async def test_wer_zuerst_die_konfiguration_hat_behaelt_die_website(monkeypatch):
    """Auch wenn der Besitzer die Adresse gar nicht (mehr) im Konto fuehrt."""
    modul, _ = _mit_datenbank(
        monkeypatch,
        adressen={2: ["https://kunde.de"]},
        konfigurationen={"kunde-de": 1},
    )
    assert await modul.get_user_site_ids(1) == {"kunde-de"}
    assert await modul.get_user_site_ids(2) == set()


@pytest.mark.asyncio
async def test_website_ohne_konfiguration_und_verwaiste_zeile_bleiben_zugaenglich(monkeypatch):
    """Sonst kaeme niemand mehr an eine neue oder herrenlose Website."""
    modul, _ = _mit_datenbank(
        monkeypatch,
        adressen={2: ["https://neu.de", "https://verwaist.de"]},
        konfigurationen={"verwaist-de": None},
    )
    assert await modul.get_user_site_ids(2) == {"neu-de", "verwaist-de"}


@pytest.mark.asyncio
async def test_agenturkonto_behaelt_alle_eigenen_websites(monkeypatch):
    modul, _ = _mit_datenbank(
        monkeypatch,
        adressen={5: ["https://a.de", "https://b.de", "https://c.de"]},
        konfigurationen={"a-de": 5, "b-de": 5, "fremd-de": 9},
    )
    assert await modul.get_user_site_ids(5) == {"a-de", "b-de", "c-de"}


# ============================================================================
# 2) POST /config
# ============================================================================

def _client(monkeypatch, *, eigene, primaer=None, zeilen):
    """zeilen: Antworten von fetchrow in Aufrufreihenfolge."""
    import cookie_compliance_routes as modul
    app = FastAPI()
    app.include_router(modul.router)
    pool = MagicMock()
    pool.fetchrow = AsyncMock(side_effect=list(zeilen))
    pool.execute = AsyncMock(return_value="UPDATE 1")
    monkeypatch.setattr(modul, "db_pool", pool)
    monkeypatch.setattr(modul, "get_current_user_required", AsyncMock(return_value={"id": 7}))
    monkeypatch.setattr(modul, "get_user_id_from_token", AsyncMock(return_value=7))
    monkeypatch.setattr(modul, "require_module", AsyncMock(return_value=True))
    monkeypatch.setattr(modul, "get_user_site_ids", AsyncMock(return_value=set(eigene)))
    monkeypatch.setattr(modul, "get_user_website_site_id", AsyncMock(return_value=primaer))
    return TestClient(app, raise_server_exceptions=False), pool


def _speichern(client, site_id):
    return client.post(
        "/api/cookie-compliance/config",
        json={"site_id": site_id, "texts": {"de": {}}, "services": ["google_analytics_ga4"]},
        headers={"Authorization": "Bearer x"},
    )


def _schreibende(pool):
    alle = [c.args[0] for c in pool.fetchrow.await_args_list] + [c.args[0] for c in pool.execute.await_args_list]
    return [sql for sql in alle if sql.lstrip().upper().startswith(("UPDATE", "INSERT"))]


def test_konto_ohne_website_kann_keine_fremde_konfiguration_ueberschreiben(monkeypatch):
    """Der Weg, der bis zum 11.11.2026 offen stand (`owned_site_ids and ...`)."""
    client, pool = _client(monkeypatch, eigene=set(), zeilen=[{"user_id": 99}])
    resp = _speichern(client, "opfer-de")
    assert resp.status_code == 403, resp.text
    assert _schreibende(pool) == []


def test_konto_ohne_website_uebernimmt_keine_verwaiste_konfiguration(monkeypatch):
    client, pool = _client(monkeypatch, eigene=set(), zeilen=[{"user_id": None}])
    resp = _speichern(client, "verwaist-de")
    assert resp.status_code == 403, resp.text
    assert _schreibende(pool) == []


def test_fremde_konfiguration_wird_nicht_ersatzweise_an_der_eigenen_gespeichert(monkeypatch):
    """Vorher fiel der Speicherweg still auf die eigene Website zurueck und
    ueberschrieb deren Banner mit Einstellungen, die fuer eine andere gedacht waren."""
    client, pool = _client(monkeypatch, eigene={"kunde-de"}, primaer="kunde-de",
                           zeilen=[{"user_id": 99}])
    resp = _speichern(client, "opfer-de")
    assert resp.status_code == 403, resp.text
    assert _schreibende(pool) == []


def test_unbekannte_kennung_faellt_wie_bisher_auf_die_eigene_website(monkeypatch):
    """Platzhalter oder abweichende Schreibweise aus einem alten Frontend."""
    client, pool = _client(monkeypatch, eigene={"kunde-de"}, primaer="kunde-de",
                           zeilen=[None, {"id": 1}, {"id": 1, "revision": 4}])
    resp = _speichern(client, "kunde")
    assert resp.status_code == 200, resp.text
    update = [c for c in pool.fetchrow.await_args_list if "UPDATE cookie_banner_configs" in c.args[0]]
    assert len(update) == 1 and update[0].args[1] == "kunde-de"


def test_konto_ohne_website_darf_eine_neue_konfiguration_anlegen(monkeypatch):
    client, pool = _client(monkeypatch, eigene=set(),
                           zeilen=[None, None, {"id": 5, "revision": 1}])
    resp = _speichern(client, "neu-de")
    assert resp.status_code == 200, resp.text
    insert = [c for c in pool.fetchrow.await_args_list if "INSERT INTO cookie_banner_configs" in c.args[0]]
    assert len(insert) == 1 and insert[0].args[1] == "neu-de" and insert[0].args[2] == 7


def test_eigene_website_speichert_ohne_zusaetzliche_pruefung(monkeypatch):
    client, pool = _client(monkeypatch, eigene={"kunde-de"}, primaer="kunde-de",
                           zeilen=[{"id": 1}, {"id": 1, "revision": 2}])
    resp = _speichern(client, "kunde-de")
    assert resp.status_code == 200, resp.text


def test_ablehnung_ist_keine_stoerung(monkeypatch):
    """Ohne `except HTTPException: raise` wurde aus 401 und 403 ein 500."""
    import cookie_compliance_routes as modul
    app = FastAPI()
    app.include_router(modul.router)
    monkeypatch.setattr(modul, "db_pool", MagicMock())
    monkeypatch.setattr(modul, "auth_service", None)
    resp = TestClient(app, raise_server_exceptions=False).post(
        "/api/cookie-compliance/config",
        json={"site_id": "kunde-de", "texts": {"de": {}}, "services": []},
    )
    assert resp.status_code == 401, resp.text


# ============================================================================
# 3) Quelltext: die Regel sitzt an der einen Stelle, durch die alle gehen
# ============================================================================

def test_die_regel_steht_in_get_user_site_ids():
    import cookie_compliance_routes as modul
    quelle = inspect.getsource(modul.get_user_site_ids)
    assert "user_id IS NOT NULL AND user_id <> $2" in quelle, (
        "get_user_site_ids nimmt wieder jede im Konto angelegte Adresse als eigene."
    )


def test_alle_besitzpruefungen_gehen_durch_get_user_site_ids():
    """Wer eine eigene Besitzlogik baut, umgeht die Erstbesitz-Regel."""
    gezaehlt = 0
    for datei, funktionen in {
        "cookie_compliance_routes.py": ["require_site_access", "require_site_access_user", "scan_schreibziel"],
        "alt_text_routes.py": ["require_site_ownership"],
    }.items():
        with open(os.path.join(BACKEND, datei), encoding="utf-8") as fh:
            quelle = fh.read()
        for name in funktionen:
            start = quelle.index(f"async def {name}(")
            ende = quelle.find("\nasync def ", start + 1)
            rumpf = quelle[start:ende if ende > 0 else len(quelle)]
            gezaehlt += 1
            assert "get_user_site_ids(" in rumpf, (
                f"{datei}:{name} prueft die Zugehoerigkeit nicht mehr ueber get_user_site_ids."
            )
    assert gezaehlt == 4

    with open(os.path.join(BACKEND, "tests", "test_mandantentrennung.py"), encoding="utf-8") as fh:
        assert "get_user_site_ids" in fh.read(), "Der Mandantenwaechter kennt die Besitzfunktion nicht mehr."
