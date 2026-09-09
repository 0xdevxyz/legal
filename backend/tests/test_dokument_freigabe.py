"""Dokumentweite Fixes kommen jetzt zur Freigabe — ohne die alten abzuschalten.

Bis 04.09.2026 gingen skip-link, landmark-main, struktur und css-rule beim
Anlegen direkt live. Der Lernstand wies sie mit 100 % Zustimmung aus: nicht
weil sie gut waren, sondern weil niemand gefragt wurde.

Die Umstellung des Vorgabestatus auf `pending` hat genau eine gefährliche
Nebenwirkung, und die schließen diese Tests aus: **bereits freigegebene Fixes
dürfen nicht zurückfallen.** Täten sie es, verschwänden über Nacht
Reparaturen von Kundenwebsites — still, weil niemand hinsieht.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import accessibility_fix_saver as afs
from accessibility_fix_saver import AccessibilityFixSaver
from alt_text_routes import ApproveDokumentRequest


class FakeConn:
    def __init__(self, zeile=None):
        self.zeile = zeile
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


def zeile(fix_type="skip-link"):
    return {"id": 1, "user_id": "u1", "site_id": "s1", "fix_type": fix_type}


class TestVorgabestatus:
    def test_neue_fixes_warten_auf_freigabe(self):
        """Der Kern der Produktentscheidung: mehr sinnvolle Freigabeklicks."""
        import inspect
        sig = inspect.signature(AccessibilityFixSaver.save_document_fixes)
        assert sig.parameters["status"].default == "pending"

    def test_bestehende_freigaben_ueberleben(self):
        """Das ON CONFLICT haelt einen erteilten `approved`-Status fest.

        Ohne diese Klausel haette die Umstellung auf `pending` beim naechsten
        Scan jede live stehende Reparatur zurueckgesetzt — die Kundenwebsite
        waere still wieder kaputt gewesen.
        """
        quelle = inspect_quelle()
        assert "WHEN accessibility_document_fixes.status = 'approved'" in quelle
        assert "THEN 'approved'" in quelle


def inspect_quelle() -> str:
    pfad = os.path.join(os.path.dirname(__file__), "..",
                        "accessibility_fix_saver.py")
    return open(pfad, encoding="utf-8").read()


@pytest.mark.asyncio
class TestFreigabeweg:
    async def test_freigabe_setzt_approved(self):
        conn = FakeConn(zeile())
        saver = AccessibilityFixSaver(FakePool(conn))
        ok = await saver.set_dokument_status(
            fix_id=1, status="approved", erlaubte_sites={"s1"})
        assert ok is True
        sql, params = conn.aufrufe[-1]
        assert "status = $1" in sql
        assert "approved" in params

    async def test_ablehnung_speichert_den_grund(self, ):
        conn = FakeConn(zeile())
        saver = AccessibilityFixSaver(FakePool(conn))
        await saver.set_dokument_status(
            fix_id=1, status="rejected", erlaubte_sites={"s1"},
            rejected_reason="An der falschen Stelle eingefügt")
        sql, params = conn.aufrufe[-1]
        assert "rejected_reason" in sql
        assert "An der falschen Stelle eingefügt" in params

    async def test_freigabe_loescht_einen_alten_grund(self):
        conn = FakeConn(zeile())
        saver = AccessibilityFixSaver(FakePool(conn))
        await saver.set_dokument_status(
            fix_id=1, status="approved", erlaubte_sites={"s1"},
            rejected_reason="Bricht das Layout")
        _, params = conn.aufrufe[-1]
        assert "Bricht das Layout" not in params
        assert None in params

    async def test_kontrast_gehoert_nicht_hierher(self):
        """Eine Zeilenfreigabe wuerde alle Farbpaare auf einmal entscheiden —
        genau das, was set_kontrast_freigabe vermeidet."""
        conn = FakeConn(zeile(fix_type="kontrast-css"))
        saver = AccessibilityFixSaver(FakePool(conn))
        ok = await saver.set_dokument_status(
            fix_id=1, status="approved", erlaubte_sites={"s1"})
        assert ok is False
        assert conn.aufrufe == [], "kontrast-css darf nicht geschrieben werden"

    async def test_unbekannte_id_ist_kein_erfolg(self):
        conn = FakeConn(None)
        saver = AccessibilityFixSaver(FakePool(conn))
        assert await saver.set_dokument_status(
            fix_id=99, status="approved", erlaubte_sites={"s1"}) is False

    async def test_unbekannter_status_wird_abgelehnt(self):
        conn = FakeConn(zeile())
        saver = AccessibilityFixSaver(FakePool(conn))
        assert await saver.set_dokument_status(
            fix_id=1, status="halbwegs", erlaubte_sites={"s1"}) is False


class TestModell:
    def test_kennt_den_grund(self):
        r = ApproveDokumentRequest(fix_id=1, approved=False,
                                   rejected_reason="Ist schon vorhanden")
        assert r.rejected_reason == "Ist schon vorhanden"

    def test_grund_ist_freiwillig(self):
        assert ApproveDokumentRequest(fix_id=1, approved=True).rejected_reason is None


# Diese Klasse liest Frontend-Quelltext, der im Repo neben backend/ liegt. Im
# Backend-Container ist nur backend/ nach /app kopiert, dort gibt es ihn nicht —
# das ist kein Fehlschlag, sondern eine andere Umgebung. CI checkt das ganze
# Repo aus und fuehrt die Klasse aus.
_FRONTEND_QUELLEN = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard-react")
ohne_frontend = pytest.mark.skipif(
    not os.path.isdir(_FRONTEND_QUELLEN),
    reason="Frontend-Quelltext liegt nicht neben backend/ (z. B. im Container) — laeuft in CI",
)


@ohne_frontend
class TestOberflaeche:
    def test_worklist_fragt_nach_einem_grund(self):
        pfad = os.path.join(
            os.path.dirname(__file__), "..", "..", "dashboard-react", "src",
            "components", "accessibility", "AccessibilityWorklist.tsx")
        s = open(pfad, encoding="utf-8").read()
        assert "DOK_ABLEHNGRUENDE" in s
        assert "decideDok(d, false, grund)" in s
        assert "approve-dokument" in s

    def test_offene_werden_getrennt_angezeigt(self):
        pfad = os.path.join(
            os.path.dirname(__file__), "..", "..", "dashboard-react", "src",
            "components", "accessibility", "AccessibilityWorklist.tsx")
        s = open(pfad, encoding="utf-8").read()
        assert "document_fixes.pending" in s
        assert "pending_count} offen" in s


class TestWartenderVorschlag:
    """
    Der Ausgang aus der Warteschlange.

    Ein freigegebener Fix wird beim naechsten Scan nicht ueberschrieben; der
    neue Vorschlag wartet unter `neuer_vorschlag` im Payload. Bis zum
    09.09.2026 wurde das Feld nirgends gelesen — nicht im Dashboard, nicht im
    Widget, nicht im Backend. Fuenf Vorschlaege lagen darin, der aelteste seit
    dem 12.08.2026. Auf panoart360.de raeumte die laufende Reparatur 51 auf 16
    Fundstellen ab, waehrend im selben Datensatz eine auf 4 wartete.
    """

    @staticmethod
    def _zeile(fix_type="struktur", mit_vorschlag=True):
        payload = {"fixes": [{"selector": "#works"}], "vorher": 51, "nachher": 16}
        if mit_vorschlag:
            payload["neuer_vorschlag"] = {
                "fixes": [{"selector": "#works"}, {"selector": "#about"}],
                "vorher": 51, "nachher": 4,
            }
            payload["bemerkt_am"] = "2026-09-09 21:33:33+00"
        return {"id": 7, "user_id": "u1", "site_id": "s1",
                "fix_type": fix_type, "payload": payload}

    @pytest.mark.asyncio
    async def test_uebernehmen_macht_den_vorschlag_zum_payload(self):
        conn = FakeConn(self._zeile())
        ok = await AccessibilityFixSaver(FakePool(conn)).entscheide_neuen_vorschlag(
            fix_id=7, uebernehmen=True, erlaubte_sites={"s1"})
        assert ok
        import json
        neu = json.loads(conn.aufrufe[0][1][0])
        assert neu["nachher"] == 4, "die bessere Fassung muss aktiv werden"
        assert len(neu["fixes"]) == 2

    @pytest.mark.asyncio
    async def test_uebernahme_traegt_die_warteschlangen_merker_nicht_mit(self):
        """`neuer_vorschlag` und `bemerkt_am` gehoeren zur Warteschlange."""
        conn = FakeConn(self._zeile())
        await AccessibilityFixSaver(FakePool(conn)).entscheide_neuen_vorschlag(
            fix_id=7, uebernehmen=True, erlaubte_sites={"s1"})
        import json
        neu = json.loads(conn.aufrufe[0][1][0])
        assert "neuer_vorschlag" not in neu
        assert "bemerkt_am" not in neu

    @pytest.mark.asyncio
    async def test_behalten_raeumt_den_vorschlag_weg(self):
        """Sonst stuende dieselbe Frage beim naechsten Laden wieder da."""
        conn = FakeConn(self._zeile())
        ok = await AccessibilityFixSaver(FakePool(conn)).entscheide_neuen_vorschlag(
            fix_id=7, uebernehmen=False, erlaubte_sites={"s1"})
        assert ok
        import json
        neu = json.loads(conn.aufrufe[0][1][0])
        assert neu["nachher"] == 16, "die laufende Fassung bleibt unangetastet"
        assert "neuer_vorschlag" not in neu

    @pytest.mark.asyncio
    async def test_beide_wege_zaehlen_als_menschliche_entscheidung(self):
        """Auch das Behalten ist eine Entscheidung — sonst faellt sie im
        Lernstand unter den Tisch."""
        for uebernehmen in (True, False):
            conn = FakeConn(self._zeile())
            await AccessibilityFixSaver(FakePool(conn)).entscheide_neuen_vorschlag(
                fix_id=7, uebernehmen=uebernehmen, erlaubte_sites={"s1"})
            assert "entscheidung_quelle = 'mensch'" in conn.aufrufe[0][0]

    @pytest.mark.asyncio
    async def test_ohne_wartenden_vorschlag_passiert_nichts(self):
        conn = FakeConn(self._zeile(mit_vorschlag=False))
        ok = await AccessibilityFixSaver(FakePool(conn)).entscheide_neuen_vorschlag(
            fix_id=7, uebernehmen=True, erlaubte_sites={"s1"})
        assert ok is False
        assert conn.aufrufe == []

    @pytest.mark.asyncio
    async def test_kontrast_bleibt_aussen_vor(self):
        """
        Dort steckt in `entscheidungen` eine Freigabe je Farbpaar. Eine
        Uebernahme im Ganzen wuerde genau die erteilten Farbfreigaben
        ueberschreiben, die der Mechanismus schuetzen soll.
        """
        conn = FakeConn(self._zeile(fix_type="kontrast-css"))
        ok = await AccessibilityFixSaver(FakePool(conn)).entscheide_neuen_vorschlag(
            fix_id=7, uebernehmen=True, erlaubte_sites={"s1"})
        assert ok is False
        assert conn.aufrufe == []

    @pytest.mark.asyncio
    async def test_fremde_site_wird_abgewiesen(self):
        conn = FakeConn(self._zeile())
        with pytest.raises(PermissionError):
            await AccessibilityFixSaver(FakePool(conn)).entscheide_neuen_vorschlag(
                fix_id=7, uebernehmen=True, erlaubte_sites={"andere-site"})
        assert conn.aufrufe == []
