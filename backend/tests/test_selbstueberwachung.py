"""Selbstüberwachung darf weder das Log noch die Kundenkasse belasten (15.09.2026).

Zwei Befunde aus der Kosten/Nutzen-Messung vom 15.09.2026, beide nicht am Betrag,
sondern am Verhältnis:

1. Von rund 2.750 protokollierten HTTP-Abrufen in 13 Stunden waren 1.558 ein
   erfolgreiches `GET /health`, knapp 57 %. Der echte Befund fällt in so einem
   Log nicht mehr auf.
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
        #
        # Beide Scans MUESSEN in einem Ereignisprozess laufen: asyncio.run()
        # baut je Aufruf einen frischen Kontext, ein Kleber waere zwischen zwei
        # run()-Aufrufen gar nicht sichtbar. Beim ersten Entwurf war der Test
        # genau so gebaut und blieb in der Gegenprobe (reset() entfernt) gruen.
        import public_routes as pr
        from compliance_engine import ai_budget
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")

        gesehen = []

        async def fake_scan(url):
            gesehen.append(ai_budget._konto.get())
            return {"success": True}

        monkeypatch.setattr(pr, "fuehre_preview_scan_aus", fake_scan)

        async def nacheinander():
            await pr.analyze_website_preview(
                FakeZiel(), FakeAnfrage(**{pr.PROBESCAN_KOPF: "abc123"}))
            await pr.analyze_website_preview(FakeZiel(), FakeAnfrage())

        asyncio.run(nacheinander())
        assert gesehen[0][0] == ai_budget.SYSTEM
        assert gesehen[1][0] is None, "Konto des Probescans klebt am naechsten Scan"


class TestSparsamerProbescan:
    """Stuendlich ohne KI, einmal taeglich mit.

    Der Probescan bewertet, ob der Scanpfad laeuft: success, risk_categories,
    score, Dauer. Die KI-Pruefung von Impressum und Datenschutz braucht er
    dafuer nicht, sie kostete aber 0,167 USD am Tag und damit 76 % der
    gesamten Tagesrechnung (gemessen 15.09.2026).
    """

    def test_ki_stunde_ist_vollstaendig_der_rest_sparsam(self, monkeypatch, tmp_path):
        monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "s.json"))
        monkeypatch.setenv("WAECHTER_PROBESCAN_KI_STUNDE", "3")
        import cronjobs.betriebswaechter as m
        importlib.reload(m)
        assert m.probescan_modus(3) == "vollstaendig"
        vollstaendige = [h for h in range(24) if m.probescan_modus(h) == "vollstaendig"]
        assert vollstaendige == [3], f"genau eine Stunde am Tag, nicht {vollstaendige}"

    def test_kopf_steuert_den_modus(self):
        import public_routes as pr
        assert pr._probescan_ohne_ki(FakeAnfrage(**{pr.PROBESCAN_MODUS_KOPF: "sparsam"})) is True
        assert pr._probescan_ohne_ki(FakeAnfrage(**{pr.PROBESCAN_MODUS_KOPF: "SPARSAM"})) is True
        assert pr._probescan_ohne_ki(FakeAnfrage(**{pr.PROBESCAN_MODUS_KOPF: "vollstaendig"})) is False

    def test_ohne_kopf_bleibt_die_ki_an(self):
        # Ein unbekannter Aufrufer darf nicht versehentlich die halbe Pruefung
        # bekommen. Fehlender Kopf heisst vollstaendig, nicht sparsam.
        import public_routes as pr
        assert pr._probescan_ohne_ki(FakeAnfrage()) is False

    def _ki_zustand_beim_scan(self, monkeypatch, kopfzeilen):
        import public_routes as pr
        from compliance_engine import ai_budget

        gesehen = {}

        async def fake_scan(url):
            gesehen["ki_aus"] = ai_budget.ki_ist_aus()
            gesehen["konto"] = ai_budget._konto.get()
            return {"success": True}

        monkeypatch.setattr(pr, "fuehre_preview_scan_aus", fake_scan)
        asyncio.run(pr.analyze_website_preview(FakeZiel(), FakeAnfrage(**kopfzeilen)))
        return gesehen

    def test_sparsamer_probescan_schaltet_die_ki_ab(self, monkeypatch):
        import public_routes as pr
        from compliance_engine import ai_budget
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        gesehen = self._ki_zustand_beim_scan(monkeypatch, {
            pr.PROBESCAN_KOPF: "abc123",
            pr.PROBESCAN_MODUS_KOPF: "sparsam",
        })
        assert gesehen["ki_aus"] is True
        assert gesehen["konto"][0] == ai_budget.SYSTEM, "Konto muss trotzdem stimmen"

    def test_vollstaendiger_probescan_laesst_die_ki_an(self, monkeypatch):
        import public_routes as pr
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        gesehen = self._ki_zustand_beim_scan(monkeypatch, {
            pr.PROBESCAN_KOPF: "abc123",
            pr.PROBESCAN_MODUS_KOPF: "vollstaendig",
        })
        assert gesehen["ki_aus"] is False

    def test_besucher_kann_die_ki_nicht_abschalten(self, monkeypatch):
        # Ohne gueltiges Geheimnis darf der Modus-Kopf nichts bewirken, sonst
        # kann jeder Besucher sich selbst eine halbe Pruefung bestellen.
        import public_routes as pr
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")
        gesehen = self._ki_zustand_beim_scan(monkeypatch, {
            pr.PROBESCAN_MODUS_KOPF: "sparsam",
        })
        assert gesehen["ki_aus"] is False
        assert gesehen["konto"][0] is None

    def test_schalter_klebt_nicht_am_naechsten_scan(self, monkeypatch):
        # Beide Scans in EINEM Ereignisprozess, siehe die Begruendung bei
        # test_konto_klebt_nicht_am_naechsten_scan: ueber zwei asyncio.run()
        # hinweg kann ein haengengebliebener ContextVar gar nicht auffallen.
        import public_routes as pr
        from compliance_engine import ai_budget
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "abc123")

        gesehen = []

        async def fake_scan(url):
            gesehen.append(ai_budget.ki_ist_aus())
            return {"success": True}

        monkeypatch.setattr(pr, "fuehre_preview_scan_aus", fake_scan)

        async def nacheinander():
            await pr.analyze_website_preview(FakeZiel(), FakeAnfrage(**{
                pr.PROBESCAN_KOPF: "abc123",
                pr.PROBESCAN_MODUS_KOPF: "sparsam",
            }))
            await pr.analyze_website_preview(FakeZiel(), FakeAnfrage())

        asyncio.run(nacheinander())
        assert gesehen == [True, False], f"Schalter klebt: {gesehen}"

    def test_budget_sperrt_ohne_redis_zu_fragen(self, monkeypatch):
        from compliance_engine import ai_budget

        async def redis_verboten():
            raise AssertionError("Bei abgeschalteter KI darf Redis nicht gefragt werden")

        monkeypatch.setattr(ai_budget, "_redis", redis_verboten)

        async def lauf():
            with ai_budget.ki_aus():
                return await ai_budget.budget_frei(None, "free", 0.001)

        assert asyncio.run(lauf()) is False


class TestWaechterSendetKopf:
    def test_kopf_wird_mitgeschickt_wenn_geheimnis_gesetzt(self, monkeypatch, tmp_path):
        monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "s.json"))
        monkeypatch.setenv("COMPLYO_PROBESCAN_TOKEN", "geheim42")
        import cronjobs.betriebswaechter as m
        importlib.reload(m)
        assert m.PROBESCAN_TOKEN == "geheim42"
        gesendet = _probescan_mit_falscher_sitzung(monkeypatch, m)
        assert gesendet.get(m.PROBESCAN_KOPF) == "geheim42"
        assert gesendet.get(m.PROBESCAN_MODUS_KOPF) in ("sparsam", "vollstaendig")

    def test_ohne_geheimnis_kein_leerer_kopf(self, monkeypatch, tmp_path):
        # Ein leerer Kopf wuerde auf der Gegenseite nie passen, waere aber ein
        # stiller Hinweis, dass hier etwas fehlt. Lieber gar keinen senden.
        monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "s.json"))
        monkeypatch.delenv("COMPLYO_PROBESCAN_TOKEN", raising=False)
        import cronjobs.betriebswaechter as m
        importlib.reload(m)
        gesendet = _probescan_mit_falscher_sitzung(monkeypatch, m)
        assert m.PROBESCAN_KOPF not in gesendet
        # Ohne Geheimnis nimmt das Backend den Modus ohnehin nicht an. Ein
        # wirkungsloser Kopf sieht im Mitschnitt aus, als wuerde er wirken.
        assert m.PROBESCAN_MODUS_KOPF not in gesendet


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


@pytest.fixture(scope="module")
def monitor():
    import cronjobs.website_monitor as m
    return m


class TestBeispieldomainenWerdenNichtGeprueft:
    """example.com stand seit dem 24.05.2026 aktiv in der Überwachung.

    27 Vollscans über Unterseiten, Konto smoketest@complyo.dev. Reservierte
    Namen aus RFC 2606 / RFC 6761 gehören niemandem und lösen teils gar nicht
    auf, eine Compliance-Prüfung misst an ihnen nichts.
    """

    @pytest.mark.parametrize("url", [
        "https://example.com",
        "http://example.com/",
        "https://www.example.com",
        "https://EXAMPLE.COM",
        "https://example.net",
        "https://example.org",
        "https://irgendwas.test",
        "https://kunde.example",
        "https://foo.invalid",
        "http://localhost:3000",
        "https://app.localhost",
    ])
    def test_reservierte_namen_werden_erkannt(self, monitor, url):
        assert monitor.ist_beispieldomain(url) is True, url

    @pytest.mark.parametrize("url", [
        "https://complyo.de",
        "https://loqal.io",
        "https://zua-zwickau.de",
        "https://ferienpark-waldenburg.de",
        # Kein Praefixtreffer: die gehoeren echten Leuten.
        "https://example.company",
        "https://myexample.com",
        "https://example.com.de",
        "https://testsieger.de",
    ])
    def test_echte_kundenseiten_bleiben_drin(self, monitor, url):
        assert monitor.ist_beispieldomain(url) is False, url

    def test_leere_eingabe_sperrt_nichts(self, monitor):
        assert monitor.ist_beispieldomain("") is False
        assert monitor.ist_beispieldomain(None) is False

    def test_sperre_ist_in_der_schleife_verdrahtet(self):
        """Die Sperre muss die Bedingung eines if sein, nicht irgendwo stehen.

        Erster Entwurf suchte nur, ob der Aufruf im Syntaxbaum vorkommt. Die
        Gegenprobe `if False and ist_beispieldomain(url):` blieb damit gruen,
        weil der Aufruf ja noch dasteht. Geprueft wird deshalb die Form: der
        Aufruf IST die Bedingung, und im Rumpf wird abgebrochen.
        """
        quelle = (Path(__file__).resolve().parent.parent
                  / "cronjobs" / "website_monitor.py").read_text()
        baum = ast.parse(quelle)

        passende = [
            k for k in ast.walk(baum)
            if isinstance(k, ast.If)
            and isinstance(k.test, ast.Call)
            and isinstance(k.test.func, ast.Name)
            and k.test.func.id == "ist_beispieldomain"
        ]
        assert passende, (
            "ist_beispieldomain steht nicht als unmittelbare Bedingung eines if "
            "(eine mit False verundete Bedingung zaehlt nicht)"
        )
        assert any(
            any(isinstance(r, ast.Return) for r in ast.walk(zweig))
            for k in passende for zweig in k.body
        ), "Die Sperre greift, bricht den Durchlauf aber nicht ab"


class TestRescanMarkierung:
    """Ein Duplikat darf keinen Vollscan aller Sites ausloesen.

    Gemessen am 15.09.2026: alle sieben überwachten Sites trugen
    `rescan_required` dauerhaft, `scan_frequency = weekly` war dadurch
    wirkungslos, jede Site wurde täglich über 46 Seiten voll gescannt. Der
    Duplikat-Guard existierte für die Benachrichtigungen, aber nicht für die
    Markierung.
    """

    def test_markierung_haengt_am_duplikat_guard(self):
        """Der Markierungsaufruf muss im else-Zweig der Duplikatpruefung stehen.

        Erster Entwurf suchte die Zeichenketten `if ist_duplikat:` und
        `websites_flagged = 0` im Quelltext. Die Gegenprobe (Guard durch
        `if False:` ersetzt) blieb gruen, weil `if ist_duplikat:` an einer
        ZWEITEN Stelle steht, naemlich beim Benachrichtigen. Eine Textsuche
        kann nicht unterscheiden, wo ein Treffer liegt.
        """
        quelle = (Path(__file__).resolve().parent.parent / "compliance_engine"
                  / "legal_update_integration.py").read_text()
        baum = ast.parse(quelle)

        def ruft_markierung(knoten) -> bool:
            return any(
                isinstance(k, ast.Call) and isinstance(k.func, ast.Attribute)
                and k.func.attr == "_flag_websites_for_rescan"
                for k in ast.walk(knoten)
            )

        alle = [k for k in ast.walk(baum) if ruft_markierung(k) and isinstance(k, ast.Call)]
        assert alle, "Markierung wird nirgends gerufen"

        guards = [
            k for k in ast.walk(baum)
            if isinstance(k, ast.If)
            and isinstance(k.test, ast.Name) and k.test.id == "ist_duplikat"
            and any(ruft_markierung(z) for z in k.orelse)
            and not any(ruft_markierung(z) for z in k.body)
        ]
        assert guards, (
            "Die Rescan-Markierung steht nicht im else-Zweig von `if ist_duplikat:` "
            "— ein wiederholter Titel loest damit wieder Vollscans aller Sites aus"
        )

        # Und der Guard muss seinen Wert wirklich aus der Duplikatpruefung ziehen.
        zuweisungen = [
            k for k in ast.walk(baum)
            if isinstance(k, ast.Assign)
            and any(isinstance(z, ast.Name) and z.id == "ist_duplikat" for z in k.targets)
        ]
        assert zuweisungen, "ist_duplikat wird nirgends gesetzt"
        quelltexte = [ast.unparse(z.value) for z in zuweisungen]
        assert any("_is_duplicate_update" in q for q in quelltexte), quelltexte

    def test_toter_parameter_ist_weg(self):
        # affected_categories wurde vom Aufrufer ausgerechnet und von der
        # Funktion weggeworfen. Ein Argument, das nichts bewirkt, liest sich
        # wie eine Auswahl, die es nicht gibt.
        import inspect
        from compliance_engine.legal_update_integration import LegalUpdateIntegration
        unterschrift = inspect.signature(
            LegalUpdateIntegration._flag_websites_for_rescan)
        assert "affected_categories" not in unterschrift.parameters
