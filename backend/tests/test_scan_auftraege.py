"""Die Auftragsablage muss ohne Redis den Weg freigeben, nicht blockieren.

Der Scan hielt bis 03.09.2026 seine HTTP-Verbindung 16-18 s offen. Der Speicher
wuchs dabei mit den WARTENDEN Anfragen: bei Browser-Semaphor 6 war das Backend
schon bei 16 gleichzeitigen Anfragen am 2-GiB-Anschlag, und bei 22 lieferten
vier Scans 14 statt 13 Befunde.

Die Ablage entkoppelt Annahme und Ausführung. Der wichtigste Test ist dabei
nicht der gute Fall, sondern der Ausfall: faellt Redis aus, muss der alte
synchrone Weg weiterlaufen. Ein Scanner, der ohne Redis gar nicht mehr scannt,
waere schlechter als der Zustand vorher.
"""

import json
import os
import sys
import time
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import scan_auftraege as sa
from compliance_engine.scan_progress import token_gueltig


class FakeRedis:
    """Minimale Redis-Attrappe: set/get mit Ablauf, optional mit Stoerung."""

    def __init__(self, stoerung=None):
        self.daten = {}
        self.stoerung = stoerung
        self.ex_werte = []

    async def set(self, key, value, ex=None):
        if self.stoerung:
            raise self.stoerung
        self.daten[key] = value
        self.ex_werte.append(ex)

    async def get(self, key):
        if self.stoerung:
            raise self.stoerung
        return self.daten.get(key)


def mit_redis(r):
    return patch.object(sa, "_redis", AsyncMock(return_value=r))


@pytest.mark.asyncio
class TestOhneRedis:
    """Der Ausfall ist der wichtige Fall."""

    async def test_verfuegbar_meldet_nein(self):
        with mit_redis(None):
            assert await sa.verfuegbar() is False

    async def test_anlegen_gibt_none_statt_zu_werfen(self):
        with mit_redis(None):
            assert await sa.anlegen("https://example.com") is None

    async def test_hole_gibt_none_statt_zu_werfen(self):
        with mit_redis(None):
            assert await sa.hole("scan-abc12345") is None

    async def test_markieren_faellt_nicht_um(self):
        with mit_redis(None):
            assert await sa.markiere_laufend("scan-abc12345") is False
            assert await sa.markiere_fertig("scan-abc12345", {}) is False
            assert await sa.markiere_fehlgeschlagen("scan-abc12345", "x") is False

    async def test_kaputtes_redis_wirft_nicht_durch(self):
        """set/get werfen — die Ablage muss das schlucken."""
        with mit_redis(FakeRedis(stoerung=ConnectionError("Redis weg"))):
            assert await sa.anlegen("https://example.com") is None
            assert await sa.hole("scan-abc12345") is None


@pytest.mark.asyncio
class TestLebenslauf:
    async def test_anlegen_lesen_fertig(self):
        r = FakeRedis()
        with mit_redis(r):
            k = await sa.anlegen("https://example.com")
            assert k
            a = await sa.hole(k)
            assert a["zustand"] == sa.WARTEND
            assert a["url"] == "https://example.com"

            assert await sa.markiere_laufend(k)
            assert (await sa.hole(k))["zustand"] == sa.LAEUFT

            assert await sa.markiere_fertig(k, {"score": 55, "issues_count": 13})
            a = await sa.hole(k)
            assert a["zustand"] == sa.FERTIG
            assert a["ergebnis"]["issues_count"] == 13

    async def test_fehlschlag_traegt_den_grund(self):
        r = FakeRedis()
        with mit_redis(r):
            k = await sa.anlegen("https://example.com")
            await sa.markiere_fehlgeschlagen(k, "Website nicht erreichbar")
            a = await sa.hole(k)
            assert a["zustand"] == sa.FEHLGESCHLAGEN
            assert "nicht erreichbar" in a["fehler"]

    async def test_unbekannte_kennung_ist_none(self):
        with mit_redis(FakeRedis()):
            assert await sa.hole("scan-gibtesnicht123") is None

    async def test_schreiben_legt_nichts_an(self):
        """Sonst entstehen Auftraege, die nie jemand angenommen hat."""
        r = FakeRedis()
        with mit_redis(r):
            assert await sa.markiere_fertig("scan-erfunden1234", {}) is False
            assert r.daten == {}


@pytest.mark.asyncio
class TestHaengendeAuftraege:
    async def test_zu_lange_laufend_gilt_als_gescheitert(self):
        """Sonst wartet die Anzeige auf einen Arbeiter, den es nicht mehr gibt."""
        r = FakeRedis()
        with mit_redis(r):
            k = await sa.anlegen("https://example.com")
            await sa.markiere_laufend(k)
            # Beginn kuenstlich in die Vergangenheit schieben
            roh = json.loads(r.daten[sa.PRAEFIX + k])
            roh["begonnen"] = time.time() - sa.LAUFZEIT_GRENZE_SEKUNDEN - 1
            r.daten[sa.PRAEFIX + k] = json.dumps(roh)

            a = await sa.hole(k)
            assert a["zustand"] == sa.FEHLGESCHLAGEN
            assert "abgebrochen" in a["fehler"]

    async def test_frisch_laufend_bleibt_laufend(self):
        """Gegenprobe: ein normaler Scan darf nicht als gescheitert gelten."""
        r = FakeRedis()
        with mit_redis(r):
            k = await sa.anlegen("https://example.com")
            await sa.markiere_laufend(k)
            assert (await sa.hole(k))["zustand"] == sa.LAEUFT


class TestKennung:
    def test_passt_zur_fortschrittsanzeige(self):
        """Eine Kennung, die scan_progress ablehnt, laesst den Balken stumm."""
        for _ in range(20):
            assert token_gueltig(sa.neue_kennung())

    def test_kennungen_sind_verschieden(self):
        assert len({sa.neue_kennung() for _ in range(200)}) == 200


class TestZustandslogik:
    def test_endzustaende(self):
        assert sa.ist_endzustand(sa.FERTIG)
        assert sa.ist_endzustand(sa.FEHLGESCHLAGEN)

    def test_zwischenzustaende_sind_keine_endzustaende(self):
        assert not sa.ist_endzustand(sa.WARTEND)
        assert not sa.ist_endzustand(sa.LAEUFT)
        assert not sa.ist_endzustand(None)


@pytest.mark.asyncio
class TestAblauf:
    async def test_ttl_wird_gesetzt(self):
        """Ohne TTL wuechse die Ablage unbegrenzt."""
        r = FakeRedis()
        with mit_redis(r):
            await sa.anlegen("https://example.com")
        assert r.ex_werte == [sa.TTL_SEKUNDEN]

    async def test_ttl_wird_bei_jeder_aenderung_erneuert(self):
        r = FakeRedis()
        with mit_redis(r):
            k = await sa.anlegen("https://example.com")
            await sa.markiere_fertig(k, {})
        assert all(e == sa.TTL_SEKUNDEN for e in r.ex_werte)
