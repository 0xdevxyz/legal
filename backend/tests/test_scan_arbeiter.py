"""Der Arbeiter darf keinen Auftrag haengen lassen.

Ein Auftrag, der fuer immer auf `wartend` oder `laeuft` steht, ist schlimmer
als ein Fehlschlag: die Anzeige beim Kunden dreht sich endlos, und niemand
erfaehrt, dass etwas schiefging. Deshalb pruefen diese Tests vor allem die
unschoenen Wege — Absturz, Abbruch, volle Schlange, Neustart.

Zweite Falle, die hier festgehalten wird: fuehre_preview_scan_aus() wirft bei
Scannerfehlern nicht, sondern liefert ein dict mit success=False. Wer nur auf
Ausnahmen achtet, legt einen gescheiterten Scan als `fertig` ab.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import scan_arbeiter as ar
from compliance_engine import scan_auftraege as sa


class Ablage:
    """Merkt sich, in welchem Zustand ein Auftrag zuletzt abgelegt wurde."""

    def __init__(self):
        self.zustand = {}
        self.fehler = {}
        self.ergebnis = {}

    async def laufend(self, k):
        self.zustand[k] = sa.LAEUFT
        return True

    async def fertig(self, k, e):
        self.zustand[k] = sa.FERTIG
        self.ergebnis[k] = e
        return True

    async def gescheitert(self, k, f):
        self.zustand[k] = sa.FEHLGESCHLAGEN
        self.fehler[k] = f
        return True


@pytest.fixture
def ablage():
    a = Ablage()
    with patch.object(ar.sa, "markiere_laufend", a.laufend), \
         patch.object(ar.sa, "markiere_fertig", a.fertig), \
         patch.object(ar.sa, "markiere_fehlgeschlagen", a.gescheitert):
        yield a


@pytest_asyncio.fixture
async def gestartet(ablage):
    await ar.starte()
    yield ablage
    await ar.beende()


@pytest.mark.asyncio
class TestGuterFall:
    async def test_erfolgreicher_scan_wird_fertig(self, gestartet):
        gut = {"success": True, "score": 55, "issues_count": 13}
        with patch("public_routes.fuehre_preview_scan_aus", AsyncMock(return_value=gut)):
            await ar.einreihen("scan-a1234567", "https://example.com")
            await asyncio.sleep(0.2)
        assert gestartet.zustand["scan-a1234567"] == sa.FERTIG
        assert gestartet.ergebnis["scan-a1234567"]["issues_count"] == 13


@pytest.mark.asyncio
class TestStilleFehlschlaege:
    async def test_success_false_gilt_als_fehlschlag(self, gestartet):
        """Der Scanner wirft nicht, er meldet success=False. Wer nur auf
        Ausnahmen achtet, legt einen gescheiterten Scan als fertig ab."""
        schlecht = {"success": False, "message": "Website nicht erreichbar"}
        with patch("public_routes.fuehre_preview_scan_aus", AsyncMock(return_value=schlecht)):
            await ar.einreihen("scan-b1234567", "https://example.com")
            await asyncio.sleep(0.2)
        assert gestartet.zustand["scan-b1234567"] == sa.FEHLGESCHLAGEN
        assert "nicht erreichbar" in gestartet.fehler["scan-b1234567"]

    async def test_leere_antwort_gilt_als_fehlschlag(self, gestartet):
        with patch("public_routes.fuehre_preview_scan_aus", AsyncMock(return_value=None)):
            await ar.einreihen("scan-c1234567", "https://example.com")
            await asyncio.sleep(0.2)
        assert gestartet.zustand["scan-c1234567"] == sa.FEHLGESCHLAGEN

    async def test_ausnahme_haengt_den_auftrag_nicht(self, gestartet):
        with patch("public_routes.fuehre_preview_scan_aus",
                   AsyncMock(side_effect=RuntimeError("Browser weg"))):
            await ar.einreihen("scan-d1234567", "https://example.com")
            await asyncio.sleep(0.2)
        assert gestartet.zustand["scan-d1234567"] == sa.FEHLGESCHLAGEN

    async def test_arbeiter_lebt_nach_einer_ausnahme_weiter(self, gestartet):
        """Sonst reisst ein kaputter Scan alle folgenden mit."""
        with patch("public_routes.fuehre_preview_scan_aus",
                   AsyncMock(side_effect=RuntimeError("Browser weg"))):
            await ar.einreihen("scan-e1234567", "https://example.com")
            await asyncio.sleep(0.2)
        gut = {"success": True, "score": 55}
        with patch("public_routes.fuehre_preview_scan_aus", AsyncMock(return_value=gut)):
            await ar.einreihen("scan-f1234567", "https://example.com")
            await asyncio.sleep(0.2)
        assert gestartet.zustand["scan-f1234567"] == sa.FERTIG


@pytest.mark.asyncio
class TestSchlange:
    async def test_volle_schlange_lehnt_ab_statt_zu_warten(self, ablage):
        """Ein Dienst, der unbegrenzt annimmt, verspricht Ergebnisse fuer
        naechste Woche."""
        alt = ar.WARTESCHLANGE_MAX
        ar.WARTESCHLANGE_MAX = 2
        try:
            ar._warteschlange = asyncio.Queue(maxsize=2)
            assert await ar.einreihen("scan-g1234567", "u") is True
            assert await ar.einreihen("scan-h1234567", "u") is True
            assert await ar.einreihen("scan-i1234567", "u") is False
        finally:
            ar.WARTESCHLANGE_MAX = alt
            ar._warteschlange = None

    async def test_ohne_laufende_arbeiter_wird_abgelehnt(self, ablage):
        ar._warteschlange = None
        assert await ar.einreihen("scan-j1234567", "u") is False


@pytest.mark.asyncio
class TestHerunterfahren:
    async def test_wartende_auftraege_werden_als_gescheitert_abgelegt(self, ablage):
        """Sonst stehen sie nach einem Neustart fuer immer auf `wartend`."""
        await ar.starte()
        # Arbeiter blockieren, damit nichts abgearbeitet wird
        with patch("public_routes.fuehre_preview_scan_aus",
                   AsyncMock(side_effect=lambda u: asyncio.sleep(30))):
            for i in range(3):
                await ar.einreihen(f"scan-k123456{i}", "https://example.com")
            await asyncio.sleep(0.05)
            await ar.beende()
        # Mindestens die nie begonnenen muessen als gescheitert dastehen
        assert any(z == sa.FEHLGESCHLAGEN for z in ablage.zustand.values())

    async def test_beenden_ist_mehrfach_harmlos(self, ablage):
        await ar.starte()
        await ar.beende()
        await ar.beende()
        assert not ar.laeuft()

    async def test_starten_ist_mehrfach_harmlos(self, ablage):
        await ar.starte()
        anzahl = len(ar._arbeiter)
        await ar.starte()
        assert len(ar._arbeiter) == anzahl
        await ar.beende()


class TestEinstellbarkeit:
    def test_werte_sind_positiv(self):
        assert ar.ARBEITER_ANZAHL >= 1
        assert ar.WARTESCHLANGE_MAX >= 1

    def test_arbeiterzahl_passt_zur_gemessenen_kapazitaet(self):
        """Bei sechs gleichzeitigen Scans lag die Spitze bei 973 MiB von 2 GiB."""
        assert ar.ARBEITER_ANZAHL <= 8
