"""
AVV-Zustimmung fuer Bestandskonten.

Seit dem 10.09.2026 nimmt die Registrierung AGB und AVV an. Die Konten von
davor haben nie zugestimmt (am 11.09.2026: 16 Konten, 0 Zeilen mit
avv_version). Das Dashboard sperrt sie, bis die Zustimmung nachgeholt ist.

Zwei Waechter und die Routen:
  * Backend, Dashboard und Landing nennen dieselbe Fassung. Sonst
    protokolliert das Backend eine Annahme fuer eine Fassung, die nie
    angezeigt wurde, und das ist kein Nachweis.
  * Die Annahme validiert die Fassungen und die Unternehmereigenschaft und
    schreibt ueber denselben Weg wie die Registrierung.
"""
import os
import re
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import auth_routes  # noqa: E402
import vertrag_routes  # noqa: E402
from dependencies import get_current_user, get_db  # noqa: E402
from vertragsstand import AGB_VERSION, AVV_VERSION  # noqa: E402

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(BACKEND)
DASHBOARD_STAND = os.path.join(WURZEL, "dashboard-react", "src", "lib", "vertragsstand.ts")
LANDING_STAND = os.path.join(WURZEL, "landing-react", "src", "lib", "vertragsstand.ts")
REGISTRIERUNG = os.path.join(WURZEL, "dashboard-react", "src", "app", "register", "page.tsx")
GATE = os.path.join(WURZEL, "dashboard-react", "src", "components", "auth", "VertragsGate.tsx")

frontend_da = pytest.mark.skipif(
    not os.path.exists(DASHBOARD_STAND), reason="dashboard-react nicht eingehaengt")


def _fassungen(pfad):
    text = open(pfad, encoding="utf-8").read()
    agb = re.search(r"const AGB_VERSION = '([\d-]+)'", text)
    avv = re.search(r"const AVV_VERSION = '([\d-]+)'", text)
    assert agb and avv, f"Fassungen fehlen in {pfad}"
    return agb.group(1), avv.group(1)


class TestEineQuelle:
    def test_fassungen_sind_datumsfoermig(self):
        for f in (AGB_VERSION, AVV_VERSION):
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", f)

    @frontend_da
    def test_dashboard_nennt_dieselbe_fassung(self):
        assert _fassungen(DASHBOARD_STAND) == (AGB_VERSION, AVV_VERSION)

    @pytest.mark.skipif(not os.path.exists(LANDING_STAND), reason="landing-react nicht eingehaengt")
    def test_landing_nennt_dieselbe_fassung(self):
        assert _fassungen(LANDING_STAND) == (AGB_VERSION, AVV_VERSION)

    @frontend_da
    def test_registrierung_und_gate_importieren_statt_zu_kopieren(self):
        for pfad in (REGISTRIERUNG, GATE):
            text = open(pfad, encoding="utf-8").read()
            assert "from '@/lib/vertragsstand'" in text, pfad
            assert not re.search(r"const (AGB|AVV)_VERSION = '", text), (
                f"{pfad} fuehrt eine eigene Fassung; die gehoert nach lib/vertragsstand.ts")

    @frontend_da
    def test_gate_liegt_hinter_der_anmeldung(self):
        layout = open(os.path.join(WURZEL, "dashboard-react", "src", "components",
                                   "dashboard", "SidebarLayout.tsx"), encoding="utf-8").read()
        innen = layout[layout.index("<AuthGuard>"):layout.index("</AuthGuard>")]
        assert "<VertragsGate>" in innen

    @frontend_da
    def test_gate_nennt_denselben_wortlaut_wie_die_registrierung(self):
        gate = open(GATE, encoding="utf-8").read()
        for stueck in ("§ 14 BGB", "https://complyo.de/avv", "https://complyo.de/agb",
                       "Art. 28 DSGVO", 'role="dialog"', "aria-modal"):
            assert stueck in gate, stueck


# ---------------------------------------------------------------------------
# Routen
# ---------------------------------------------------------------------------

NUTZER = {"id": 5, "user_id": 5, "email": "alt@example.de"}


def _pool(zeile):
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=zeile)
    conn.execute = AsyncMock()
    pool = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return pool, conn


@pytest.fixture(autouse=True)
def _ohne_redis(monkeypatch):
    monkeypatch.setattr("dependencies.get_redis", AsyncMock(return_value=None))


def _client(monkeypatch, zeile, user=NUTZER):
    pool, conn = _pool(zeile)
    monkeypatch.setattr(auth_routes, "db_pool", pool)
    app = FastAPI()
    app.include_router(vertrag_routes.router)
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: pool
    return TestClient(app), conn


class TestVertragsstand:
    def test_ohne_anmeldung(self, monkeypatch):
        client, _ = _client(monkeypatch, None, user=None)
        assert client.get("/api/auth/vertragsstand").status_code in (401, 403)

    def test_bestandskonto_ohne_zeile(self, monkeypatch):
        client, conn = _client(monkeypatch, None)
        r = client.get("/api/auth/vertragsstand")
        assert r.status_code == 200
        b = r.json()
        assert b["agb_fehlt"] is True and b["avv_fehlt"] is True
        assert b["agb_version_aktuell"] == AGB_VERSION
        assert b["avv_version_aktuell"] == AVV_VERSION
        assert b["agb_angenommen"] is None and b["avv_angenommen"] is None
        assert conn.fetchrow.call_args.args[-1] == 5

    def test_agb_ja_avv_nein(self, monkeypatch):
        """Der Fall der 16 Konten: AGB bei der Registrierung, AVV nie."""
        client, _ = _client(monkeypatch, {"agb_version": AGB_VERSION, "avv_version": None,
                                          "unternehmer_bestaetigt": True, "angenommen_am": None})
        b = client.get("/api/auth/vertragsstand").json()
        assert b["agb_fehlt"] is False
        assert b["avv_fehlt"] is True

    def test_alles_angenommen(self, monkeypatch):
        client, _ = _client(monkeypatch, {"agb_version": AGB_VERSION, "avv_version": AVV_VERSION,
                                          "unternehmer_bestaetigt": True, "angenommen_am": None})
        b = client.get("/api/auth/vertragsstand").json()
        assert b["agb_fehlt"] is False and b["avv_fehlt"] is False

    def test_veraltete_fassung_fehlt(self, monkeypatch):
        client, _ = _client(monkeypatch, {"agb_version": "2020-01-01", "avv_version": AVV_VERSION,
                                          "unternehmer_bestaetigt": True, "angenommen_am": None})
        b = client.get("/api/auth/vertragsstand").json()
        assert b["agb_fehlt"] is True and b["avv_fehlt"] is False

    def test_datenbankfehler_ist_503_nicht_fehlt(self, monkeypatch):
        """Das Gate sperrt nur bei klarer Antwort; ein Tabellenproblem darf
        nicht jeden Kunden aussperren."""
        client, conn = _client(monkeypatch, None)
        conn.fetchrow = AsyncMock(side_effect=RuntimeError("relation does not exist"))
        assert client.get("/api/auth/vertragsstand").status_code == 503


class TestAnnahme:
    def _angenommen(self):
        return {"agb_version": AGB_VERSION, "avv_version": AVV_VERSION,
                "unternehmer_bestaetigt": True, "angenommen_am": None}

    def test_ohne_unternehmer_bestaetigung_400(self, monkeypatch):
        client, conn = _client(monkeypatch, self._angenommen())
        r = client.post("/api/auth/vertrag-annehmen", json={
            "unternehmer_bestaetigt": False,
            "agb_version": AGB_VERSION, "avv_version": AVV_VERSION})
        assert r.status_code == 400
        assert "Unternehmer" in r.json()["detail"]
        conn.execute.assert_not_called()

    def test_veraltete_fassung_400(self, monkeypatch):
        client, conn = _client(monkeypatch, self._angenommen())
        r = client.post("/api/auth/vertrag-annehmen", json={
            "unternehmer_bestaetigt": True,
            "agb_version": AGB_VERSION, "avv_version": "2020-01-01"})
        assert r.status_code == 400
        assert AVV_VERSION in r.json()["detail"]
        conn.execute.assert_not_called()

    def test_annahme_wird_wie_bei_der_registrierung_protokolliert(self, monkeypatch):
        client, conn = _client(monkeypatch, self._angenommen())
        r = client.post("/api/auth/vertrag-annehmen", json={
            "unternehmer_bestaetigt": True,
            "agb_version": AGB_VERSION, "avv_version": AVV_VERSION},
            headers={"User-Agent": "Testbrowser/1.0"})
        assert r.status_code == 200, r.text
        assert r.json()["avv_fehlt"] is False and r.json()["agb_fehlt"] is False

        conn.execute.assert_awaited_once()
        sql, *werte = conn.execute.call_args.args
        assert "INSERT INTO vertragsannahmen" in sql
        # user_id, email, agb, avv, unternehmer, ip, user-agent
        assert werte[0] == 5
        assert werte[1] == "alt@example.de"
        assert werte[2] == AGB_VERSION
        assert werte[3] == AVV_VERSION
        assert werte[4] is True
        assert werte[5]  # IP-Adresse
        assert werte[6] == "Testbrowser/1.0"

    def test_nicht_gespeicherte_annahme_ist_503(self, monkeypatch):
        """protokolliere_vertragsannahme ist best effort; hier ist der Nachweis
        der Zweck, also wird nachgelesen."""
        client, conn = _client(monkeypatch, None)
        conn.execute = AsyncMock(side_effect=RuntimeError("kaputt"))
        r = client.post("/api/auth/vertrag-annehmen", json={
            "unternehmer_bestaetigt": True,
            "agb_version": AGB_VERSION, "avv_version": AVV_VERSION})
        assert r.status_code == 503

    def test_ohne_anmeldung(self, monkeypatch):
        client, _ = _client(monkeypatch, None, user=None)
        r = client.post("/api/auth/vertrag-annehmen", json={
            "unternehmer_bestaetigt": True,
            "agb_version": AGB_VERSION, "avv_version": AVV_VERSION})
        assert r.status_code in (401, 403)


class TestRegistrierung:
    def test_router_haengt_in_der_anwendung(self):
        src = open(os.path.join(BACKEND, "main_production.py"), encoding="utf-8").read()
        assert "app.include_router(vertrag_router)" in src

    def test_keine_csrf_ausnahme(self):
        from csrf_middleware import EXEMPT_PATHS
        assert "/api/auth/vertrag-annehmen" not in EXEMPT_PATHS
        assert "/api/auth/vertragsstand" not in EXEMPT_PATHS
