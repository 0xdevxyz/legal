"""Die Aufnahmeschranke schuetzt das Messergebnis, nicht den Server.

Gemessen am 03.09.2026: bei 22 gleichzeitigen Scans und Browser-Semaphor 6
raeumte der Kernel acht Chrome-Prozesse ab, und vier der 22 Scans lieferten
14 statt 13 Befunde. Der Befund haing dann von der Serverlast ab.

Ein Ausfall faellt auf, ein leise veraendertes Ergebnis nicht. Deshalb lieber
503 als eine Antwort, die eine Minute spaeter anders aussieht.
"""

import asyncio
import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import public_routes as pr


async def _platz_nehmen():
    """Durchlaeuft die Dependency einmal und gibt den Generator zurueck."""
    gen = pr.scan_platz()
    await gen.__anext__()
    return gen


async def _platz_zurueck(gen):
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()


@pytest.fixture(autouse=True)
def frische_plaetze():
    """Jeder Test startet mit vollem Kontingent."""
    original = pr._scan_plaetze
    pr._scan_plaetze = asyncio.Semaphore(pr.SCAN_GLEICHZEITIG_MAX)
    yield
    pr._scan_plaetze = original


@pytest.mark.asyncio
class TestSchranke:
    async def test_unter_der_grenze_wird_durchgelassen(self):
        gen = await _platz_nehmen()
        await _platz_zurueck(gen)   # kein Fehler = durchgelassen

    async def test_volle_belegung_wird_abgelehnt(self):
        offen = [await _platz_nehmen() for _ in range(pr.SCAN_GLEICHZEITIG_MAX)]
        with pytest.raises(HTTPException) as e:
            await _platz_nehmen()
        assert e.value.status_code == 503
        for g in offen:
            await _platz_zurueck(g)

    async def test_ablehnung_nennt_retry_after(self):
        """Ohne Retry-After weiss weder Mensch noch Client, wann es Sinn hat."""
        offen = [await _platz_nehmen() for _ in range(pr.SCAN_GLEICHZEITIG_MAX)]
        with pytest.raises(HTTPException) as e:
            await _platz_nehmen()
        assert e.value.headers.get("Retry-After") == "30"
        for g in offen:
            await _platz_zurueck(g)

    async def test_platz_wird_wieder_frei(self):
        offen = [await _platz_nehmen() for _ in range(pr.SCAN_GLEICHZEITIG_MAX)]
        await _platz_zurueck(offen.pop())
        neu = await _platz_nehmen()          # muss jetzt wieder gehen
        await _platz_zurueck(neu)
        for g in offen:
            await _platz_zurueck(g)

    async def test_platz_wird_auch_nach_fehler_frei(self):
        """Sonst verstopft ein einziger fehlgeschlagener Scan die Schranke."""
        gen = pr.scan_platz()
        await gen.__anext__()
        vorher = pr._scan_plaetze._value
        with pytest.raises(RuntimeError):
            await gen.athrow(RuntimeError("Scan geplatzt"))
        assert pr._scan_plaetze._value == vorher + 1


class TestEinstellbarkeit:
    def test_grenze_ist_positiv(self):
        assert pr.SCAN_GLEICHZEITIG_MAX >= 1

    def test_grenze_liegt_unter_der_gemessenen_kante(self):
        """Bei 16 gleichzeitigen waren die Ergebnisse noch identisch,
        bei 22 kippten vier davon. 12 haelt Abstand."""
        assert pr.SCAN_GLEICHZEITIG_MAX <= 16
