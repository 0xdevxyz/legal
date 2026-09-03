"""Der entkoppelte Prüfweg darf nie einen Auftrag im Ungewissen lassen.

Zwei Fehlerbilder sollen diese Tests ausschliessen:

1. Ein Auftrag wird angenommen, kommt aber nie in die Schlange (Arbeiter aus,
   Schlange voll). Er stuende dann fuer immer auf `wartend`, und der Kunde
   fragt endlos nach.
2. Der Abholweg antwortet mit einem Fehlercode, wo ein Zustand hingehoert.
   Dann muss die abholende Seite raten, ob "noch nicht fertig" oder "kaputt"
   gemeint ist - genau daran ist der Betriebswaechter schon einmal blind
   geworden.
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import public_routes as pr
from compliance_engine import scan_auftraege as sa


class Anfrage:
    def __init__(self, url):
        self.url = url


def ablage(verfuegbar=True, kennung="scan-abc12345678", hole=None):
    m = AsyncMock()
    m.verfuegbar = AsyncMock(return_value=verfuegbar)
    m.anlegen = AsyncMock(return_value=kennung)
    m.hole = AsyncMock(return_value=hole)
    m.markiere_fehlgeschlagen = AsyncMock(return_value=True)
    m.WARTEND, m.LAEUFT = sa.WARTEND, sa.LAEUFT
    m.FERTIG, m.FEHLGESCHLAGEN = sa.FERTIG, sa.FEHLGESCHLAGEN
    m.ist_endzustand = sa.ist_endzustand
    return m


def arbeiter(einreihen=True):
    m = AsyncMock()
    m.einreihen = AsyncMock(return_value=einreihen)
    return m


class mit:
    """Haengt die Attrappen ans Paket, nicht in sys.modules.

    Der Endpunkt macht `from compliance_engine import scan_auftraege`. Python
    liefert dabei das Attribut des Pakets, nicht den sys.modules-Eintrag unter
    dem gepunkteten Namen — ein patch.dict(sys.modules, ...) laeuft deshalb ins
    Leere und die echten Module werden benutzt.
    """

    def __init__(self, ablage_m, arbeiter_m):
        import compliance_engine
        self.paket = compliance_engine
        self.neu = {"scan_auftraege": ablage_m, "scan_arbeiter": arbeiter_m}
        self.alt = {}

    def __enter__(self):
        for name, wert in self.neu.items():
            self.alt[name] = getattr(self.paket, name, None)
            setattr(self.paket, name, wert)
        return self

    def __exit__(self, *a):
        for name, wert in self.alt.items():
            if wert is None:
                delattr(self.paket, name)
            else:
                setattr(self.paket, name, wert)
        return False


@pytest.mark.asyncio
class TestAnnahme:
    async def test_angenommen_gibt_kennung_und_wege(self):
        a, w = ablage(), arbeiter()
        with mit(a, w):
            r = await pr.scan_auftrag_annehmen(Anfrage("https://example.com"))
        assert r["kennung"] == "scan-abc12345678"
        assert r["zustand"] == sa.WARTEND
        assert "analyze-progress" in r["fortschritt_pfad"]
        assert r["ergebnis_pfad"].endswith(r["kennung"])

    async def test_url_wird_ergaenzt(self):
        a, w = ablage(), arbeiter()
        with mit(a, w):
            await pr.scan_auftrag_annehmen(Anfrage("example.com"))
        a.anlegen.assert_awaited_once_with("https://example.com")

    async def test_ohne_ablage_503_statt_stillem_rueckfall(self):
        """Der Aufrufer soll wissen, dass er den synchronen Weg braucht."""
        a, w = ablage(verfuegbar=False), arbeiter()
        with mit(a, w):
            with pytest.raises(HTTPException) as e:
                await pr.scan_auftrag_annehmen(Anfrage("https://example.com"))
        assert e.value.status_code == 503
        assert e.value.headers.get("Retry-After")

    async def test_volle_schlange_laesst_den_auftrag_nicht_haengen(self):
        """Sonst steht er fuer immer auf `wartend`."""
        a, w = ablage(), arbeiter(einreihen=False)
        with mit(a, w):
            with pytest.raises(HTTPException) as e:
                await pr.scan_auftrag_annehmen(Anfrage("https://example.com"))
        assert e.value.status_code == 503
        a.markiere_fehlgeschlagen.assert_awaited_once()

    async def test_ablage_verweigert_anlegen(self):
        a, w = ablage(kennung=None), arbeiter()
        with mit(a, w):
            with pytest.raises(HTTPException) as e:
                await pr.scan_auftrag_annehmen(Anfrage("https://example.com"))
        assert e.value.status_code == 503


@pytest.mark.asyncio
class TestAbholen:
    async def test_wartend_meldet_nicht_fertig(self):
        a = ablage(hole={"zustand": sa.WARTEND, "url": "https://example.com"})
        with mit(a, arbeiter()):
            r = await pr.scan_auftrag_abholen("scan-abc12345678")
        assert r["zustand"] == sa.WARTEND
        assert r["fertig"] is False
        assert "ergebnis" not in r

    async def test_fertig_liefert_das_ergebnis(self):
        a = ablage(hole={"zustand": sa.FERTIG, "url": "u",
                         "ergebnis": {"score": 55, "issues_count": 13}})
        with mit(a, arbeiter()):
            r = await pr.scan_auftrag_abholen("scan-abc12345678")
        assert r["fertig"] is True
        assert r["ergebnis"]["issues_count"] == 13

    async def test_fehlschlag_traegt_den_grund_und_gilt_als_fertig(self):
        """`fertig` heisst "hoer auf zu fragen", nicht "hat geklappt"."""
        a = ablage(hole={"zustand": sa.FEHLGESCHLAGEN, "url": "u",
                         "fehler": "Website nicht erreichbar"})
        with mit(a, arbeiter()):
            r = await pr.scan_auftrag_abholen("scan-abc12345678")
        assert r["fertig"] is True
        assert "nicht erreichbar" in r["fehler"]
        assert "ergebnis" not in r

    async def test_unbekannte_kennung_ist_404(self):
        a = ablage(hole=None)
        with mit(a, arbeiter()):
            with pytest.raises(HTTPException) as e:
                await pr.scan_auftrag_abholen("scan-gibtesnicht1")
        assert e.value.status_code == 404

    async def test_laufend_ist_kein_endzustand(self):
        a = ablage(hole={"zustand": sa.LAEUFT, "url": "u"})
        with mit(a, arbeiter()):
            r = await pr.scan_auftrag_abholen("scan-abc12345678")
        assert r["fertig"] is False


class TestKeineSchrankeAufDemNeuenWeg:
    def test_annahme_traegt_keine_aufnahmeschranke(self):
        """Die Schranke schuetzt vor wartenden Anfragen im Speicher. Der
        entkoppelte Weg haelt nichts - sie waere hier nur eine Bremse."""
        route = next(r for r in pr.public_router.routes
                     if getattr(r, "path", "").endswith("/analyze-auftrag"))
        namen = [d.dependency.__name__ for d in route.dependencies]
        assert "scan_platz" not in namen

    def test_annahme_traegt_weiterhin_das_rate_limit(self):
        route = next(r for r in pr.public_router.routes
                     if getattr(r, "path", "").endswith("/analyze-auftrag"))
        assert route.dependencies, "Rate-Limit fehlt"

    def test_annahme_antwortet_202(self):
        route = next(r for r in pr.public_router.routes
                     if getattr(r, "path", "").endswith("/analyze-auftrag"))
        assert route.status_code == 202
