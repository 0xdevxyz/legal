"""
Regressionstests für ai_compliance_worker.process_scheduled_scans().

Bug: Der Worker rief ai_act_analyzer.classify_system() auf — diese Methode
existiert nicht (korrekt: classify_risk_category). Zusätzlich wurde
check_compliance() mit dem Klassifikations-Objekt statt der Risikokategorie
(str) aufgerufen. Der resultierende AttributeError wurde still verschluckt,
geplante Scans starben unbemerkt.
"""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import ai_compliance_worker
from ai_act_analyzer import AIActAnalyzer, AISystem, RiskClassification, ComplianceResult


# --- Contract-Tests gegen den Analyzer ---------------------------------------

def test_analyzer_has_no_classify_system_method():
    """Der Name, den der Worker früher aufrief, existiert nicht — Bug festnageln."""
    assert not hasattr(AIActAnalyzer, "classify_system")


def test_analyzer_exposes_classify_risk_category():
    assert callable(getattr(AIActAnalyzer, "classify_risk_category"))


def test_check_compliance_signature_takes_risk_category_str():
    """check_compliance(ai_system, risk_category: str) — nicht das Objekt."""
    sig = inspect.signature(AIActAnalyzer.check_compliance)
    params = list(sig.parameters)
    assert params == ["self", "ai_system", "risk_category"]
    assert sig.parameters["risk_category"].annotation is str


def test_worker_source_does_not_call_classify_system():
    src = inspect.getsource(ai_compliance_worker.AIComplianceWorker.process_scheduled_scans)
    assert "classify_system(" not in src
    assert "classify_risk_category(" in src


# --- Verhaltenstest: der Worker ruft den Analyzer korrekt auf ----------------

def _scan_row():
    return {
        "id": 1,
        "ai_system_id": 99,
        "user_id": 7,
        "system_name": "Test-System",
        "description": "Ein harmloses Empfehlungssystem",
        "vendor": "ACME",
        "purpose": "Produktempfehlungen",
        "domain": "marketing",
        "old_risk": "limited",
        "old_score": 50,
        "email": "a@b.de",
        "full_name": "A B",
        "schedule_type": "weekly",
        "schedule_day": 1,
        "schedule_hour": 3,
    }


@pytest.mark.asyncio
async def test_worker_calls_analyzer_with_correct_methods_and_types():
    worker = ai_compliance_worker.AIComplianceWorker()

    classification = RiskClassification(
        risk_category="limited",
        reasoning="ok",
        confidence=0.9,
        relevant_articles=["Art. 52"],
        key_concerns=[],
    )
    compliance = ComplianceResult(
        compliance_score=80,
        overall_risk_score=2.0,
        requirements_met=[{"r": "1"}],
        requirements_failed=[],
        findings=[],
        recommendations="passt",
    )

    mock_db = MagicMock()
    mock_db.pool = MagicMock()
    mock_db.pool.fetch = AsyncMock(return_value=[_scan_row()])
    mock_db.pool.execute = AsyncMock(return_value=None)

    mock_analyzer = MagicMock()
    mock_analyzer.classify_risk_category = AsyncMock(return_value=classification)
    mock_analyzer.check_compliance = AsyncMock(return_value=compliance)

    with patch.dict("sys.modules", {}), \
         patch("database_service.db_service", mock_db), \
         patch("ai_act_analyzer.ai_act_analyzer", mock_analyzer), \
         patch.object(worker, "_save_scan_result", AsyncMock(return_value="scan-1")), \
         patch.object(worker, "_update_next_run", AsyncMock(return_value=None)), \
         patch.object(worker, "_get_user_settings", AsyncMock(return_value={})), \
         patch.object(worker, "_create_notification", AsyncMock(return_value=None)):
        await worker.process_scheduled_scans()

    # classify_risk_category wurde mit einem AISystem-Modell aufgerufen
    mock_analyzer.classify_risk_category.assert_awaited_once()
    passed_system = mock_analyzer.classify_risk_category.await_args.args[0]
    assert isinstance(passed_system, AISystem), (
        f"Analyzer erwartet AISystem, bekam {type(passed_system)}"
    )
    assert passed_system.name == "Test-System"

    # check_compliance wurde mit (AISystem, risk_category: str) aufgerufen
    mock_analyzer.check_compliance.assert_awaited_once()
    args = mock_analyzer.check_compliance.await_args.args
    assert isinstance(args[0], AISystem)
    assert args[1] == "limited", "risk_category muss der str sein, nicht das Objekt"
    assert isinstance(args[1], str)


@pytest.mark.asyncio
async def test_worker_logs_exception_with_stacktrace(caplog):
    """Ein Fehler im Scan darf nicht still verschluckt werden."""
    worker = ai_compliance_worker.AIComplianceWorker()

    mock_db = MagicMock()
    mock_db.pool = MagicMock()
    mock_db.pool.fetch = AsyncMock(return_value=[_scan_row()])
    mock_db.pool.execute = AsyncMock(return_value=None)

    mock_analyzer = MagicMock()
    mock_analyzer.classify_risk_category = AsyncMock(
        side_effect=AttributeError("boom")
    )

    with patch("database_service.db_service", mock_db), \
         patch("ai_act_analyzer.ai_act_analyzer", mock_analyzer), \
         caplog.at_level("ERROR"):
        await worker.process_scheduled_scans()

    assert "boom" in caplog.text
    # logger.exception() hängt den Stacktrace an
    assert "Traceback" in caplog.text, "Fehler muss mit Stacktrace geloggt werden"
