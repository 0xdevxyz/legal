"""Selbstüberwachung darf weder das Log noch die Kundenkasse belasten (15.09.2026).

Zwei Befunde aus der Kosten/Nutzen-Messung vom 15.09.2026, beide nicht am Betrag,
sondern am Verhältnis:

1. Von rund 2.500 Zeilen Backend-Log in 13 Stunden waren 1.558 ein erfolgreiches
   `GET /health`. Der echte Befund fällt in so einem Log nicht mehr auf.
2. Alle 13 Vorschau-Scans derselben 13 Stunden kamen vom Betriebswächter selbst,
   keiner von außen. Sie buchten auf `ki:kosten:vorschau`, den Tagestopf, der
   Interessenten gehört. Sobald Besucher kommen, greift der Deckel zuerst bei
   ihnen, nicht beim Wächter.

Beides wird hier festgenagelt, inklusive der Grenzfälle, an denen ein zu grober
Filter oder eine zu großzügige Erkennung Schaden anrichten würde.
"""
import ast
import asyncio
import importlib
import logging
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def zugriffssatz(pfad: str, status: int) -> logging.LogRecord:
    """Ein Satz in der Form, die uvicorn.access erzeugt."""
    return logging.LogRecord(
        name="uvicorn.access", level=logging.INFO, pathname=__file__, lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:1234", "GET", pfad, "1.1", status),
        exc_info=None,
    )


@pytest.fixture(scope="module")
def filter_klasse():
    import betriebslog
    return betriebslog.GesundheitsabrufeStumm()


class TestGesundheitsabrufeStumm:
    def test_erfolgreicher_health_abruf_wird_unterdrueckt(self, filter_klasse):
        assert filter_klasse.filter(zugriffssatz("/health", 200)) is False

    def test_api_health_ebenfalls(self, filter_klasse):
        assert filter_klasse.filter(zugriffssatz("/api/health", 200)) is False

    def test_abfrageteil_wird_abgeschnitten(self, filter_klasse):
        assert filter_klasse.filter(zugriffssatz("/health?probe=1", 200)) is False

    @pytest.mark.parametrize("status", [400, 404, 500, 503])
    def test_kaputter_health_abruf_bleibt_sichtbar(self, filter_klasse, status):
        # Der eigentliche Punkt: genau dieser Fall ist das Signal. Ein Filter,
        # der ihn mitnimmt, waere ein Waechter, der schweigt.
        assert filter_klasse.filter(zugriffssatz("/health", status)) is True

    def test_andere_pfade_bleiben(self, filter_klasse):
        assert filter_klasse.filter(zugriffssatz("/api/analyze-preview", 200)) is True

    def test_kein_praefix_treffer(self, filter_klasse):
        # /healthcheck und /health-report sind andere Routen und duerfen nicht
        # mitverschwinden, nur weil sie mit /health anfangen.
        assert filter_klasse.filter(zugriffssatz("/healthcheck", 200)) is True
        assert filter_klasse.filter(zugriffssatz("/api/health/detail", 200)) is True

    def test_unerwartete_form_wird_nicht_gefiltert(self, filter_klasse):
        for args in [(), ("a", "b"), None, {"pfad": "/health"}]:
            satz = zugriffssatz("/health", 200)
            satz.args = args
            assert filter_klasse.filter(satz) is True, f"Form {args!r} wurde gefiltert"

    def test_unlesbarer_status_wird_nicht_gefiltert(self, filter_klasse):
        satz = zugriffssatz("/health", 200)
        satz.args = ("127.0.0.1:1", "GET", "/health", "1.1", "grün")
        assert filter_klasse.filter(satz) is True

    def test_installieren_haengt_an_und_zwar_einmal(self):
        import betriebslog
        zugriffslogger = logging.getLogger("uvicorn.access")
        vorher = list(zugriffslogger.filters)
        try:
            betriebslog.installieren()
            betriebslog.installieren()
            angehaengt = [
                f for f in zugriffslogger.filters
                if isinstance(f, betriebslog.GesundheitsabrufeStumm)
            ]
            assert len(angehaengt) == 1, f"{len(angehaengt)} Filter angehaengt"
        finally:
            zugriffslogger.filters = vorher

    def test_main_production_haengt_den_filter_ein(self):
        # Verdrahtungstest wie in test_verdrahtung.py: das Modul selbst zu
        # importieren wuerde die halbe Anwendung hochfahren, die Bindung muss
        # aber trotzdem bewacht sein - ohne sie ist der Filter wirkungslos.
        #
        # Ueber den Syntaxbaum und nicht per Textsuche: beim ersten Entwurf war
        # es eine Textsuche, und die Gegenprobe (Zeile auskommentieren) blieb
        # gruen, weil der Text im Kommentar stehenblieb. Ein Waechter, der
        # einen Kommentar fuer Code haelt, bewacht nichts.
        quelle = (Path(__file__).resolve().parent.parent / "main_production.py").read_text()
        baum = ast.parse(quelle)

        importiert = any(
            isinstance(k, ast.Import) and any(n.name == "betriebslog" for n in k.names)
            for k in ast.walk(baum)
        )
        assert importiert, "main_production importiert betriebslog nicht"

        gerufen = any(
            isinstance(k, ast.Expr)
            and isinstance(k.value, ast.Call)
            and isinstance(k.value.func, ast.Attribute)
            and k.value.func.attr == "installieren"
            and isinstance(k.value.func.value, ast.Name)
            and k.value.func.value.id == "betriebslog"
            for k in baum.body
        )
        assert gerufen, "betriebslog.installieren() wird auf Modulebene nicht gerufen"


class FakeKopf:
    def __init__(self, werte):
        self._w = werte

    def get(self, name, standard=None):
        return self._w.get(name, standard)


class FakeAnfrage:
    def __init__(self, **kopfzeilen):
        self.headers = FakeKopf(kopfzeilen)


class TestProbescanErkennung:
    def test_ohne_geheimnis_niemals(self, monkeypatch):
        # Der wichtigste Fall: ein leeres Geheimnis darf nicht auf einen leeren
        # oder beliebigen Kopf passen, sonst bucht jeder Besucher auf den
        # Systemtopf.
        import public_routes as pr
        monkeypatch.delenv("COMPLYO_PROBESCAN_TOKEN", raising=False)
        assert pr._ist_probescan(FakeAnfrage()) is False
        assert pr._ist_probescan(FakeAnfrage(**{pr.PROBESCAN_KOPF: ""})) is False
        assert pr._ist_probescan(FakeAnfrage(**{pr.PROBESCAN_KOPF: "irgendwas"})) is False

    def test_geheimnis_gesetzt_aber_kein_kopf(self, monkeypatch):
        import public_routes as pr
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        assert pr._ist_probescan(FakeAnfrage()) is False

    def test_falscher_kopf(self, monkeypatch):
        import public_routes as pr
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        assert pr._ist_probescan(FakeAnfrage(**{pr.PROBESCAN_KOPF: "abc124"})) is False

    def test_richtiger_kopf(self, monkeypatch):
        import public_routes as pr
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        assert pr._ist_probescan(FakeAnfrage(**{pr.PROBESCAN_KOPF: "abc123"})) is True

    def test_leerraum_wird_abgeschnitten(self, monkeypatch):
        import public_routes as pr
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        assert pr._ist_probescan(FakeAnfrage(**{pr.PROBESCAN_KOPF: " abc123 "})) is True


class FakeZiel:
    url = "https://complyo.de"


class TestKostenstelleDesEndpunkts:
    """Das eigentliche Ziel: auf welches Konto bucht der Scan?"""

    def _konto_beim_scan(self, monkeypatch, kopfzeilen):
        import public_routes as pr
        from compliance_engine import ai_budget

        gesehen = {}

        async def fake_scan(url):
            gesehen["konto"] = ai_budget._konto.get()
            return {"success": True}

        monkeypatch.setattr(pr, "fuehre_preview_scan_aus", fake_scan)
        asyncio.get_event_loop_policy().new_event_loop()
        asyncio.run(pr.analyze_website_preview(FakeZiel(), FakeAnfrage(**kopfzeilen)))
        return gesehen["konto"]

    def test_gewoehnlicher_besucher_bucht_auf_vorschau(self, monkeypatch):
        import public_routes as pr
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        user, _plan = self._konto_beim_scan(monkeypatch, {})
        assert user is None, "Besucher darf nicht auf den Systemtopf buchen"

    def test_probescan_bucht_auf_system(self, monkeypatch):
        import public_routes as pr
        from compliance_engine import ai_budget
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        user, _plan = self._konto_beim_scan(
            monkeypatch, {pr.PROBESCAN_KOPF: "abc123"}
        )
        assert user == ai_budget.SYSTEM

    def test_konto_klebt_nicht_am_naechsten_scan(self, monkeypatch):
        # konto_setzen ist Kontextmanager, nicht set(). Ohne reset() wuerde der
        # naechste Besucherscan auf dem Systemtopf landen.
        import public_routes as pr
        from compliance_engine import ai_budget
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        self._konto_beim_scan(monkeypatch, {pr.PROBESCAN_KOPF: "abc123"})
        user, _plan = self._konto_beim_scan(monkeypatch, {})
        assert user is None


class TestWaechterSendetKopf:
    def test_kopf_wird_mitgeschickt_wenn_geheimnis_gesetzt(self, monkeypatch, tmp_path):
        monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "s.json"))
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "geheim42")
        import cronjobs.betriebswaechter as m
        importlib.reload(m)
        assert m.PROBESCAN_TOKEN == "geheim42"
        gesendet = _probescan_mit_falscher_sitzung(monkeypatch, m)
        assert gesendet.get(m.PROBESCAN_KOPF) == "geheim42"

    def test_ohne_geheimnis_kein_leerer_kopf(self, monkeypatch, tmp_path):
        # Ein leerer Kopf wuerde auf der Gegenseite nie passen, waere aber ein
        # stiller Hinweis, dass hier etwas fehlt. Lieber gar keinen senden.
        monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "s.json"))
        monkeypatch.delenv("COMPLYO_PROBESCAN_TOKEN", raising=False)
        import cronjobs.betriebswaechter as m
        importlib.reload(m)
        gesendet = _probescan_mit_falscher_sitzung(monkeypatch, m)
        assert m.PROBESCAN_KOPF not in gesendet


def _probescan_mit_falscher_sitzung(monkeypatch, modul):
    """Faehrt pruefe_scanpfad gegen eine gefaelschte aiohttp-Sitzung."""
    import aiohttp

    aufgezeichnet = {}

    class FakeAntwort:
        status = 200

        async def json(self):
            return {"success": True, "risk_categories": [{"a": 1}], "score": 80}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    class FakeSitzung:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def post(self, url, json=None, headers=None):
            aufgezeichnet.update(headers or {})
            return FakeAntwort()

    monkeypatch.setattr(aiohttp, "ClientSession", FakeSitzung)
    befunde = asyncio.run(modul.pruefe_scanpfad())
    assert befunde == [], f"Probescan meldete unerwartet: {befunde}"
    return aufgezeichnet
