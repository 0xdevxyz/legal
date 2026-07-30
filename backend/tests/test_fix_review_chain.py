"""
Review-Kette der KI-Fix-Engine
==============================

Befund (30.07.2026): Das Quality-Gate-Ergebnis lag nur in fix_jobs.result;
die Admin-Review-Queue las nie beschriebene Spalten (500), und es gab de facto
keine menschliche Freigabe fuer KI-Fixes. Seit Revision 0009 wird das
Gate-Ergebnis im Audit persistiert, die Kunden-Endpunkte gaten die Auslieferung
(pending_review/rejected -> Inhalt zurueckgehalten), und Admin-Approve/Reject
spiegelt die Entscheidung zurueck nach fix_jobs.result.

Statische Waechter + Unit-Tests fuer die Redaktionslogik.
"""
import os
import re

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(name: str) -> str:
    with open(os.path.join(_BACKEND, name), encoding="utf-8") as fh:
        return fh.read()


class TestGatingLogik:
    """_gate_fix_result: was der Kunde wann sehen darf."""

    @staticmethod
    def _fn():
        try:
            from main_production import _gate_fix_result
        except Exception:  # pragma: no cover — laeuft nur im Backend-Container
            pytest.skip("main_production nicht importierbar")
        return _gate_fix_result

    def test_pending_review_haelt_inhalt_zurueck(self):
        gate = self._fn()
        result = {"data": {"code": "<x>", "steps": ["a"], "quality_gate_status": "pending_review"}}
        out = gate(result)
        assert "code" not in out["data"] and "steps" not in out["data"]
        assert out["data"]["under_review"] is True
        assert out["data"]["review_status"] == "pending_review"

    def test_rejected_haelt_inhalt_zurueck(self):
        gate = self._fn()
        out = gate({"data": {"code": "<x>", "quality_gate_status": "rejected"}})
        assert "code" not in out["data"]
        assert out["data"]["under_review"] is False

    def test_validated_wird_voll_ausgeliefert(self):
        gate = self._fn()
        result = {"data": {"code": "<x>", "quality_gate_status": "validated"}}
        assert gate(result) == result

    def test_altbestand_ohne_status_bleibt_sichtbar(self):
        """Fixes von vor Revision 0009 wurden bereits ausgeliefert."""
        gate = self._fn()
        result = {"data": {"code": "<x>"}}
        assert gate(result) == result

    def test_original_wird_nicht_mutiert(self):
        gate = self._fn()
        result = {"data": {"code": "<x>", "quality_gate_status": "pending_review"}}
        gate(result)
        assert "code" in result["data"]


class TestStatischeVerdrahtung:
    """Die Kette darf nicht stillschweigend wieder auseinanderfallen."""

    def test_beide_kundenendpunkte_gaten(self):
        src = _lese("main_production.py")
        assert src.count("_gate_fix_result(") >= 3, (
            "Status- und active-Endpunkt muessen _gate_fix_result aufrufen"
        )

    def test_worker_persistiert_gate_ergebnis(self):
        src = _lese("background_worker.py")
        assert "_log_fix_audit(" in src, "Worker schreibt das Audit nicht mehr"
        assert "quality_gate_status" in src

    def test_audit_insert_fuehrt_review_spalten(self):
        src = _lese("audit_service.py")
        for spalte in ("website_id", "issue_title", "quality_gate_status", "quality_gate_log"):
            assert spalte in src, f"log_fix_generation schreibt {spalte} nicht mehr"

    def test_admin_entscheidung_wird_gespiegelt(self):
        src = _lese("admin_routes.py")
        assert src.count("_propagate_review_status(db, fix_id") == 2, (
            "Approve UND Reject muessen die Entscheidung nach fix_jobs spiegeln"
        )

    def test_audit_ids_sind_strings(self):
        """fix_application_audit.id ist VARCHAR(UUID) — int-Pfadparameter
        wiesen frueher jede echte ID mit 422 ab."""
        src = _lese("admin_routes.py")
        assert "fix_id: int" not in src
