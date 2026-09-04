"""Eine Ablehnung ohne Grund ist ein verlorener Datenpunkt.

`ai_alt_text_generator.py` legt dem Modell freigegebene Beispiele UND
Ablehnungsgruende vor, bevor es den naechsten Vorschlag macht — und filtert
dabei auf `rejected_reason IS NOT NULL AND rejected_reason != ''`.

Die Spalte existierte seit Wochen, der Leseweg auch. Geschrieben hat sie nie
jemand: weder der Endpunkt noch der Speicherer nahmen einen Grund entgegen,
und die Oberflaeche fragte nicht danach. Stand 04.09.2026: 42 Entscheidungen
in der Datenbank, davon 42 Zustimmungen, 0 Ablehnungsgruende.

Aus lauter Zustimmung laesst sich nichts lernen. Erst die Ablehnung sagt, wo
ein Verfahren danebenliegt.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from accessibility_fix_saver import AccessibilityFixSaver
from alt_text_routes import ApproveAltTextRequest


class FakeConn:
    """Merkt sich die ausgefuehrten UPDATEs samt Parametern."""

    def __init__(self, zeile=None):
        self.zeile = zeile if zeile is not None else {
            "id": 1, "user_id": "u1", "site_id": "s1"
        }
        self.aufrufe = []

    async def fetchrow(self, *a):
        return self.zeile

    async def execute(self, sql, *params):
        self.aufrufe.append((" ".join(sql.split()), params))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return self._conn


@pytest.fixture
def conn():
    return FakeConn()


@pytest.fixture
def saver(conn):
    return AccessibilityFixSaver(FakePool(conn))


@pytest.mark.asyncio
class TestGrundWirdGeschrieben:
    async def test_ablehnung_speichert_den_grund(self, saver, conn):
        await saver.set_status(
            fix_id=1, status="rejected",
            erlaubte_sites={"s1"},
            rejected_reason="Zu allgemein, sagt nichts aus",
        )
        sql, params = conn.aufrufe[-1]
        assert "rejected_reason" in sql
        assert "Zu allgemein, sagt nichts aus" in params

    async def test_ablehnung_mit_eigenem_text_speichert_beides(self, saver, conn):
        await saver.set_status(
            fix_id=1, status="rejected", custom_alt="Neuer Text",
            erlaubte_sites={"s1"}, rejected_reason="Zu lang",
        )
        sql, params = conn.aufrufe[-1]
        assert "rejected_reason" in sql
        assert "Zu lang" in params
        assert "Neuer Text" in params


@pytest.mark.asyncio
class TestGegenprobe:
    async def test_freigabe_schreibt_keinen_grund(self, saver, conn):
        """Sonst stuende an einem freigegebenen Fix noch die alte Begruendung."""
        await saver.set_status(fix_id=1, status="approved", erlaubte_sites={"s1"})
        _, params = conn.aufrufe[-1]
        assert None in params

    async def test_freigabe_loescht_einen_alten_grund(self, saver, conn):
        """Wer erst ablehnt und dann doch freigibt, darf keinen Grund hinterlassen —
        er wuerde die Auswertung verfaelschen."""
        await saver.set_status(
            fix_id=1, status="approved", erlaubte_sites={"s1"},
            rejected_reason="Zu lang",
        )
        _, params = conn.aufrufe[-1]
        assert "Zu lang" not in params
        assert None in params

    async def test_ablehnung_ohne_grund_bleibt_moeglich(self, saver, conn):
        """Der Grund darf nichts blockieren — eine Ablehnung ohne Begruendung
        ist besser als gar keine Ablehnung."""
        ok = await saver.set_status(fix_id=1, status="rejected", erlaubte_sites={"s1"})
        assert ok is True


class TestEndpunktNimmtDenGrundAn:
    def test_modell_kennt_das_feld(self):
        r = ApproveAltTextRequest(fix_id=1, approved=False,
                                  rejected_reason="Bildinhalt falsch beschrieben")
        assert r.rejected_reason == "Bildinhalt falsch beschrieben"

    def test_feld_ist_freiwillig(self):
        r = ApproveAltTextRequest(fix_id=1, approved=True)
        assert r.rejected_reason is None


class TestDerLesewegPasstZumSchreibweg:
    def test_generator_filtert_auf_nicht_leer(self):
        """Ein leerer String wuerde vom Generator verworfen — die Oberflaeche
        darf also nie '' statt None schicken."""
        quelle = open(
            os.path.join(os.path.dirname(__file__), "..",
                         "compliance_engine", "ai_alt_text_generator.py"),
            encoding="utf-8",
        ).read()
        assert "rejected_reason IS NOT NULL" in quelle
        assert "rejected_reason != ''" in quelle
