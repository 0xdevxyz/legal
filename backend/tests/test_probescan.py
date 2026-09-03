"""Der Waechter muss den Scanpfad selbst pruefen, nicht seine Umgebung.

Lasttest 03.09.2026: nach acht gleichzeitigen Scans lieferte
/api/analyze-preview nichts mehr, waehrend /api/health und /api/stripe/plans
60 von 60 Mal mit 200 antworteten. Der Waechter haette "alles ruhig" gemeldet.

Die zweite Falle steckt in _preview_scan_fehler(): die gibt ein gewoehnliches
dict zurueck, FastAPI macht daraus HTTP 200 mit success:false. Wer nur den
Statuscode prueft, sieht gruen, waehrend jeder Kundenscan scheitert.
"""

import asyncio
import os
import sys
import time
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cronjobs')))

import betriebswaechter as bw


class FakeAntwort:
    def __init__(self, status, daten):
        self.status = status
        self._daten = daten

    async def json(self):
        if self._daten is None:
            raise ValueError("kein JSON")
        return self._daten

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class FakeSitzung:
    def __init__(self, antwort=None, ausnahme=None, verzoegerung=0.0):
        self._antwort = antwort
        self._ausnahme = ausnahme
        self._verzoegerung = verzoegerung

    def post(self, *a, **k):
        if self._ausnahme:
            raise self._ausnahme
        if self._verzoegerung:
            # monotonic wird im Test gefaelscht, hier nicht wirklich warten
            pass
        return self._antwort

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def laufe(antwort=None, ausnahme=None):
    import aiohttp  # noqa: F401  - Verfuegbarkeit ist Voraussetzung

    class FakeAiohttp:
        ClientTimeout = staticmethod(lambda **k: None)

        @staticmethod
        def ClientSession(*a, **k):
            return FakeSitzung(antwort=antwort, ausnahme=ausnahme)

    with patch.dict(sys.modules, {"aiohttp": FakeAiohttp}):
        return asyncio.run(bw.pruefe_scanpfad())


GUTE_ANTWORT = {
    "success": True,
    "score": 32,
    "risk_categories": [{"id": "dsgvo", "detected": True}],
    "total_risk_range": "1.600€ - 12.800€",
}


class TestGruenerFall:
    def test_gesunder_scan_meldet_nichts(self):
        assert laufe(FakeAntwort(200, GUTE_ANTWORT)) == []


class TestDieFalleMitHttp200:
    def test_success_false_bei_status_200_wird_erkannt(self):
        """Genau das liefert _preview_scan_fehler bei jedem Scannerfehler."""
        befunde = laufe(FakeAntwort(200, {
            "success": False,
            "error": "scan_failed",
            "message": "Die Website konnte nicht automatisch gescannt werden.",
        }))
        assert befunde, "HTTP 200 mit success:false muss auffallen"
        assert befunde[0][0] == "probescan-erfolglos"

    def test_scan_ohne_kategorien_faellt_auf(self):
        befunde = laufe(FakeAntwort(200, {"success": True, "score": 50,
                                          "risk_categories": []}))
        assert any(k == "probescan-leer" for k, _ in befunde)

    def test_scan_ohne_score_faellt_auf(self):
        befunde = laufe(FakeAntwort(200, {"success": True,
                                          "risk_categories": [{"id": "a"}]}))
        assert any(k == "probescan-ohne-score" for k, _ in befunde)

    def test_kein_json_faellt_auf(self):
        befunde = laufe(FakeAntwort(200, None))
        assert befunde[0][0] == "probescan-antwortform"


class TestAusfall:
    def test_zeitlimit_wird_als_stehender_scanpfad_gemeldet(self):
        befunde = laufe(ausnahme=asyncio.TimeoutError())
        assert befunde[0][0] == "probescan-zeitlimit"
        assert "Scanpfad" in befunde[0][1]

    def test_fehlerstatus_wird_gemeldet(self):
        befunde = laufe(FakeAntwort(502, {}))
        assert befunde[0][0] == "probescan-status"

    def test_ohne_aiohttp_genau_ein_befund_statt_absturz(self):
        with patch.dict(sys.modules, {"aiohttp": None}):
            befunde = asyncio.run(bw.pruefe_scanpfad())
        assert len(befunde) == 1
        assert befunde[0][0] == "probescan-unmoeglich"


class TestNeustartMeldung:
    def test_ohne_journal_keine_meldung(self, tmp_path, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        assert bw.pruefe_neustarts() == []

    def test_neustarts_werden_gemeldet(self, tmp_path, monkeypatch):
        journal = tmp_path / "neustarts.log"
        jetzt = int(time.time())
        journal.write_text(
            f"{jetzt - 100} complyo-backend neugestartet\n"
            f"{jetzt - 200} complyo-backend neugestartet\n"
        )
        monkeypatch.setattr(bw.os.path, "exists", lambda p: True)
        with patch("builtins.open", lambda *a, **k: journal.open(encoding="utf-8")):
            befunde = bw.pruefe_neustarts()
        assert befunde
        assert "2x" in befunde[0][1]

    def test_alte_eintraege_zaehlen_nicht(self, tmp_path, monkeypatch):
        """Sonst meldet der Waechter monatelang einen Neustart von gestern."""
        journal = tmp_path / "neustarts.log"
        journal.write_text(f"{int(time.time()) - 200000} complyo-backend neugestartet\n")
        monkeypatch.setattr(bw.os.path, "exists", lambda p: True)
        with patch("builtins.open", lambda *a, **k: journal.open(encoding="utf-8")):
            assert bw.pruefe_neustarts() == []

    def test_aufgeben_wiegt_schwerer_als_neustart(self, tmp_path, monkeypatch):
        journal = tmp_path / "neustarts.log"
        jetzt = int(time.time())
        journal.write_text(
            f"{jetzt - 100} complyo-backend neugestartet\n"
            f"{jetzt - 50} complyo-backend aufgegeben\n"
        )
        monkeypatch.setattr(bw.os.path, "exists", lambda p: True)
        with patch("builtins.open", lambda *a, **k: journal.open(encoding="utf-8")):
            befunde = bw.pruefe_neustarts()
        assert befunde[0][0].startswith("neustart-aufgegeben")
        assert "braucht einen Menschen" in befunde[0][1]
