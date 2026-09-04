"""Ein einzelnes unerwartetes Feld darf keinen ganzen Auftrag verschlucken.

Beim ersten Live-Versuch des entkoppelten Vollscans (04.09.2026) legte der
Endpunkt das komplette Nutzerobjekt in den Auftrag. Darin steckt ein
`created_at` vom Typ datetime — `json.dumps` warf, `anlegen` gab None zurueck,
und der Kunde bekam ein 503 "Auftrag konnte nicht angelegt werden" ohne jeden
Hinweis. Im Log stand die Ursache, in der Antwort nicht.

Zwei Lehren, beide hier festgehalten:
1. In den Auftrag gehoert nur, was der Arbeiter wirklich braucht.
2. Trotzdem ein Netz: ein unerwartetes Feld soll zur Zeichenkette werden,
   nicht den Auftrag kosten.
"""

import datetime as dt
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import scan_auftraege as sa


class FakeRedis:
    def __init__(self):
        self.daten = {}

    async def set(self, key, value, ex=None):
        # Muss echtes JSON sein — sonst faellt es erst beim Lesen auf.
        json.loads(value)
        self.daten[key] = value

    async def get(self, key):
        return self.daten.get(key)


async def _fertig(w):
    return w


@pytest.fixture
def redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(sa, "_redis", lambda: _fertig(r))
    return r


@pytest.mark.asyncio
class TestNetz:
    async def test_datetime_im_zusatz_kostet_keinen_auftrag(self, redis):
        """Genau der Fall, der den ersten Live-Versuch scheitern liess."""
        k = await sa.anlegen(
            "https://example.com",
            art=sa.ART_V2,
            zusatz={"angelegt": dt.datetime(2026, 9, 4, 12, 0)},
        )
        assert k is not None, "Auftrag verschluckt"
        a = await sa.hole(k)
        assert a["zustand"] == sa.WARTEND
        assert isinstance(a["angelegt"], str)

    async def test_normale_felder_bleiben_ihr_typ(self):
        """Gegenprobe: default=str darf nicht alles zu Text machen."""
        r = FakeRedis()
        import unittest.mock as m
        with m.patch.object(sa, "_redis", lambda: _fertig(r)):
            k = await sa.anlegen("https://example.com", art=sa.ART_V2,
                                 zusatz={"seitenbudget": 40})
            a = await sa.hole(k)
        assert a["seitenbudget"] == 40
        assert isinstance(a["seitenbudget"], int)

    async def test_auch_beim_aendern(self, redis):
        """markiere_fertig legt das Ergebnis ab — dort kann genauso etwas
        Unerwartetes stecken."""
        k = await sa.anlegen("https://example.com")
        ok = await sa.markiere_fertig(k, {"wann": dt.datetime(2026, 9, 4)})
        assert ok is True
        a = await sa.hole(k)
        assert a["zustand"] == sa.FERTIG
