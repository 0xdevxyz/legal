"""Ablehnungsgründe für Linktexte und Kontraste.

Der Lernstand wies am 04.09. fünf von sechs Befundtypen als „Gründe nicht
erfassbar" aus. Beim Nachsehen zerfiel das in zwei sehr verschiedene Gruppen:

- **Linktexte und kontrast-css** haben eine echte Entscheidung in der
  Oberfläche. Ihnen fehlte nur die Erfassung. Diese Tests halten sie fest.
- **skip-link, landmark-main, struktur, css-rule** werden beim Anlegen direkt
  auf `approved` gesetzt — es fragt nie jemand. Eine Grundspalte wäre dort
  eine Spalte ohne Schreiber, derselbe Fehler wie bei
  `fix_acceptance_metrics`, nur spiegelverkehrt. Sie bekommen keine.
"""

import os
import sys
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from accessibility_fix_saver import AccessibilityFixSaver
from alt_text_routes import ApproveLinkRequest, KontrastFreigabeRequest


class FakeConn:
    def __init__(self, zeile=None):
        self.zeile = zeile if zeile is not None else {
            "id": 1, "user_id": "u1", "site_id": "s1"}
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
class TestLinktexte:
    async def test_ablehnung_speichert_den_grund(self, saver, conn):
        await saver.set_link_status(
            fix_id=1, status="rejected", erlaubte_sites={"s1"},
            rejected_reason="Beschreibt das Ziel falsch")
        sql, params = conn.aufrufe[-1]
        assert "rejected_reason" in sql
        assert "Beschreibt das Ziel falsch" in params

    async def test_mit_eigenem_text_beides(self, saver, conn):
        await saver.set_link_status(
            fix_id=1, status="rejected", custom_label="Neuer Text",
            erlaubte_sites={"s1"}, rejected_reason="Zu lang")
        sql, params = conn.aufrufe[-1]
        assert "rejected_reason" in sql
        assert "Zu lang" in params and "Neuer Text" in params

    async def test_freigabe_loescht_einen_alten_grund(self, saver, conn):
        """Wer erst ablehnt und dann doch freigibt, darf keine Begründung an
        einem freigegebenen Fix hinterlassen."""
        await saver.set_link_status(
            fix_id=1, status="approved", erlaubte_sites={"s1"},
            rejected_reason="Zu lang")
        _, params = conn.aufrufe[-1]
        assert "Zu lang" not in params
        assert None in params

    async def test_ablehnung_ohne_grund_bleibt_moeglich(self, saver, conn):
        ok = await saver.set_link_status(
            fix_id=1, status="rejected", erlaubte_sites={"s1"})
        assert ok is True


class TestModelle:
    def test_link_modell_kennt_den_grund(self):
        r = ApproveLinkRequest(fix_id=1, approved=False,
                               rejected_reason="Zu allgemein, sagt nichts aus")
        assert r.rejected_reason == "Zu allgemein, sagt nichts aus"

    def test_kontrast_modell_kennt_den_grund(self):
        r = KontrastFreigabeRequest(site_id="s1", index=0, approved=False,
                                    ablehngrund="Passt nicht zur Marke")
        assert r.ablehngrund == "Passt nicht zur Marke"

    def test_beide_felder_sind_freiwillig(self):
        assert ApproveLinkRequest(fix_id=1, approved=True).rejected_reason is None
        assert KontrastFreigabeRequest(
            site_id="s1", index=0, approved=True).ablehngrund is None


class TestOberflaeche:
    """Der Grund muss auch gefragt werden, sonst bleibt die Spalte leer —
    genau der Fehler, der den Lernkreislauf sechs Wochen leer laufen liess."""

    def _datei(self, name):
        pfad = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "dashboard-react", "src", "components", "accessibility", name)
        return open(pfad, encoding="utf-8").read()

    def test_worklist_fragt_bei_linktexten_nach(self):
        s = self._datei("AccessibilityWorklist.tsx")
        assert "LINK_ABLEHNGRUENDE" in s
        assert "decideLink(item, false, grund)" in s
        assert "rejected_reason: approved ? undefined : grund" in s

    def test_kontrast_fragt_nach(self):
        s = self._datei("KontrastFreigabe.tsx")
        assert "KONTRAST_ABLEHNGRUENDE" in s
        assert "entscheiden(e.index, false, grund)" in s
        assert "ablehngrund: approved ? undefined : grund" in s

    def test_gruende_sind_je_befundtyp_verschieden(self):
        """Eine gemeinsame Liste haette bei jedem Typ die Haelfte der Auswahl
        unbrauchbar gemacht."""
        w = self._datei("AccessibilityWorklist.tsx")
        k = self._datei("KontrastFreigabe.tsx")
        assert "Bildinhalt falsch beschrieben" in w     # nur Alt-Texte
        assert "Beschreibt das Ziel falsch" in w        # nur Linktexte
        assert "Passt nicht zur Marke" in k             # nur Farben
        assert "Passt nicht zur Marke" not in w
