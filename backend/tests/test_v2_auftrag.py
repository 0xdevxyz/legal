"""Ein fremder Vollscan darf nicht abholbar sein.

Der oeffentliche Vorschau-Scan hat keinen Besitzer — sein Ergebnis ist eine
oeffentliche Website-Bewertung. Der angemeldete Vollscan hat einen: er
speichert Verlauf unter einem Konto, nutzt dessen Tarif-Seitenbudget und kann
Befunde zu einer Kundenwebsite enthalten.

Die Kennung ist 128 Bit lang und praktisch nicht zu raten. "Praktisch nicht zu
raten" ist trotzdem keine Zugriffskontrolle.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import scan_auftraege as sa


def auftrag(user_id=None, zustand=sa.WARTEND, **rest):
    d = {"kennung": "scan-abc", "url": "https://example.com",
         "zustand": zustand, "user_id": user_id}
    d.update(rest)
    return d


class TestBesitz:
    def test_eigener_auftrag_ist_abholbar(self):
        assert sa.gehoert_zu(auftrag(user_id="7"), "7") is True

    def test_fremder_auftrag_ist_gesperrt(self):
        assert sa.gehoert_zu(auftrag(user_id="7"), "8") is False

    def test_besitzerloser_auftrag_ist_fuer_jeden_da(self):
        """Der oeffentliche Vorschau-Scan hat keinen Besitzer."""
        assert sa.gehoert_zu(auftrag(user_id=None), "7") is True
        assert sa.gehoert_zu(auftrag(user_id=None), None) is True

    def test_ohne_anmeldung_kein_fremder_auftrag(self):
        """Gegenprobe: kein Konto darf nicht wie jedes Konto wirken."""
        assert sa.gehoert_zu(auftrag(user_id="7"), None) is False

    def test_zahl_und_zeichenkette_gelten_als_dasselbe_konto(self):
        """user_id kommt je nach Weg als int oder str herein."""
        assert sa.gehoert_zu(auftrag(user_id="7"), 7) is True


@pytest.mark.asyncio
class TestAnlegen:
    async def test_art_und_besitzer_landen_im_auftrag(self, monkeypatch):
        gespeichert = {}

        class R:
            async def set(self, key, value, ex=None):
                import json
                gespeichert.update(json.loads(value))

            async def get(self, key):
                return None

        monkeypatch.setattr(sa, "_redis", lambda: _fertig(R()))
        await sa.anlegen("https://example.com", user_id=7, art=sa.ART_V2,
                         zusatz={"seitenbudget": 40})
        assert gespeichert["art"] == sa.ART_V2
        assert gespeichert["user_id"] == "7"
        assert gespeichert["seitenbudget"] == 40

    async def test_vorschau_bleibt_ohne_besitzer(self, monkeypatch):
        gespeichert = {}

        class R:
            async def set(self, key, value, ex=None):
                import json
                gespeichert.update(json.loads(value))

            async def get(self, key):
                return None

        monkeypatch.setattr(sa, "_redis", lambda: _fertig(R()))
        await sa.anlegen("https://example.com")
        assert gespeichert["user_id"] is None
        assert gespeichert["art"] == sa.ART_PREVIEW


async def _fertig(wert):
    return wert


class TestArten:
    def test_beide_arten_sind_verschieden(self):
        assert sa.ART_PREVIEW != sa.ART_V2

    def test_arten_sind_zeichenketten(self):
        """Sie wandern durch JSON — Enum-Werte ueberlebten das nicht."""
        assert isinstance(sa.ART_PREVIEW, str)
        assert isinstance(sa.ART_V2, str)


class TestCsrfAusnahme:
    def test_neuer_weg_ist_ausgenommen(self):
        """Beim oeffentlichen Pendant uebersehen: 13 gruene Tests, und der
        erste Live-Aufruf antwortete 'CSRF token missing or invalid'."""
        from csrf_middleware import EXEMPT_PATHS
        assert "/api/v2/analyze-auftrag" in EXEMPT_PATHS

    def test_alter_weg_bleibt_ausgenommen(self):
        from csrf_middleware import EXEMPT_PATHS
        assert "/api/v2/analyze" in EXEMPT_PATHS
