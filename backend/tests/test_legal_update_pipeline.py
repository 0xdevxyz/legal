"""
Tests: Legal Update Pipeline + Fix Quality Gate
Task 6 — Quality Process Implementation

Abgedeckte Szenarien:
- Rule Versioning (bump, deprecate, history, snapshot)
- Process_new_legal_update Pipeline (rules, sites, notifications)
- Fix Quality Gate (Stufe 1–3, Approval/Reject)
- Rescan Notification
- Admin Approve/Reject
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_db_pool(fetch=None, fetchval=None, execute=None, fetchrow=None, acquire=None):
    """Erstellt einen Mock asyncpg-Pool."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=fetch or [])
    conn.fetchval = AsyncMock(return_value=fetchval)
    conn.execute = AsyncMock(return_value=execute or "UPDATE 0")
    conn.fetchrow = AsyncMock(return_value=fetchrow)

    pool = MagicMock()
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool, conn


@pytest.fixture
def mock_legal_update():
    return {
        "id": 42,
        "title": "WCAG 2.2 Neue Anforderungen für Touch-Targets",
        "description": "Neue Accessibility-Anforderungen für interaktive Elemente",
        "update_type": "regulation_change",
        "severity": "high",
    }


@pytest.fixture
def mock_fix_valid():
    return {
        "fix_id": "fix-001",
        "fix_type": "code",
        "data": {
            "fix_code": '<button aria-label="Menü öffnen" type="button">Menu</button>',
            "description": "Fehlender aria-label ergänzt",
        },
    }


@pytest.fixture
def mock_fix_dangerous():
    return {
        "fix_id": "fix-002",
        "fix_type": "code",
        "data": {
            "fix_code": '<div onclick="alert(1)">click me</div>',
        },
    }


@pytest.fixture
def mock_fix_placeholder():
    return {
        "fix_id": "fix-003",
        "fix_type": "text",
        "data": {
            "fix_code": "<p>Impressum: [PLACEHOLDER] GmbH</p>",
        },
    }


# ---------------------------------------------------------------------------
# Test 1: Rule Versioning — bump_rule_version
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rule_versioning_bump():
    """bump_rule_version erhöht Regel-Version und schreibt Changelog-Eintrag."""
    from compliance_engine.rule_versioning_service import RuleVersioningService

    pool, conn = make_db_pool(fetchval=2)
    svc = RuleVersioningService(pool)

    result = await svc.bump_rule_version(
        rule_id=1,
        change_description="WCAG 2.2 Update",
        legal_update_id=42,
    )

    assert result is True
    conn.execute.assert_called_once()
    # Changelog INSERT sollte aufgerufen worden sein
    assert conn.execute.call_count >= 1 or conn.fetchval.call_count >= 1


@pytest.mark.asyncio
async def test_rule_versioning_bump_missing_rule():
    """bump_rule_version gibt False zurück wenn Regel nicht existiert."""
    from compliance_engine.rule_versioning_service import RuleVersioningService

    pool, conn = make_db_pool(fetchval=None)
    svc = RuleVersioningService(pool)

    result = await svc.bump_rule_version(rule_id=999, change_description="x")
    assert result is False


# ---------------------------------------------------------------------------
# Test 2: Rule Versioning — deprecate_rule
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rule_versioning_deprecate():
    """deprecate_rule setzt is_active=FALSE und loggt Changelog."""
    from compliance_engine.rule_versioning_service import RuleVersioningService

    pool, conn = make_db_pool(fetchval=1)
    svc = RuleVersioningService(pool)

    result = await svc.deprecate_rule(rule_id=1, reason="Regel überholt durch WCAG 2.2")
    assert result is True


# ---------------------------------------------------------------------------
# Test 3: Legal Pipeline — process_new_legal_update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_new_legal_update_returns_counts(mock_legal_update):
    """
    process_new_legal_update gibt rules_updated, websites_flagged, notifications_queued zurück.
    """
    from compliance_engine.legal_update_integration import LegalUpdateIntegration

    affected_rules = [
        {"id": 1, "issue_category": "barrierefreiheit", "legal_basis": "WCAG", "description": ""},
    ]

    pool, conn = make_db_pool(execute="UPDATE 5")

    with patch(
        "compliance_engine.rule_versioning_service.RuleVersioningService.find_rules_affected_by_legal_update",
        new=AsyncMock(return_value=affected_rules),
    ), patch(
        "compliance_engine.rule_versioning_service.RuleVersioningService.bump_rule_version",
        new=AsyncMock(return_value=True),
    ):
        integration = LegalUpdateIntegration(pool)
        result = await integration.process_new_legal_update(mock_legal_update)

    assert "rules_updated" in result
    assert "websites_flagged" in result
    assert "notifications_queued" in result
    assert isinstance(result["rules_updated"], int)


# ---------------------------------------------------------------------------
# Test 4: Websites werden als rescan_required markiert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_websites_flagged_after_legal_update(mock_legal_update):
    """
    Nach process_new_legal_update soll _flag_websites_for_rescan aufgerufen worden sein.
    """
    from compliance_engine.legal_update_integration import LegalUpdateIntegration

    pool, conn = make_db_pool(execute="UPDATE 7")

    with patch(
        "compliance_engine.rule_versioning_service.RuleVersioningService.find_rules_affected_by_legal_update",
        new=AsyncMock(return_value=[]),
    ):
        integration = LegalUpdateIntegration(pool)
        result = await integration.process_new_legal_update(mock_legal_update)

    # execute() für UPDATE tracked_websites muss aufgerufen worden sein
    conn.execute.assert_called()


# ---------------------------------------------------------------------------
# Test 5: Fix Quality Gate — valider Fix besteht
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fix_quality_gate_passes_valid_fix(mock_fix_valid):
    """Valider Fix (kein gefährlicher Code, kein Placeholder) → validated."""
    from ai_fix_engine.fix_quality_gate import FixQualityGate

    gate = FixQualityGate()
    result = await gate.run(mock_fix_valid, original_html="<html><body></body></html>")

    assert result.final_status == "validated"
    assert all(s.passed for s in result.stage_results if s.stage == 1)


# ---------------------------------------------------------------------------
# Test 6: Fix Quality Gate — gefährlicher Code wird blockiert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fix_quality_gate_blocks_dangerous_fix(mock_fix_dangerous):
    """Fix mit onclick-Handler → pending_review (Stage 1 schlägt fehl)."""
    from ai_fix_engine.fix_quality_gate import FixQualityGate

    gate = FixQualityGate()
    result = await gate.run(mock_fix_dangerous)

    assert result.final_status == "pending_review"
    stage1 = next(s for s in result.stage_results if s.stage == 1)
    assert not stage1.passed
    assert len(stage1.errors) > 0


# ---------------------------------------------------------------------------
# Test 7: Fix Quality Gate — Placeholder wird blockiert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fix_quality_gate_blocks_placeholder(mock_fix_placeholder):
    """Fix mit [PLACEHOLDER] → pending_review (Stage 3 schlägt fehl)."""
    from ai_fix_engine.fix_quality_gate import FixQualityGate

    gate = FixQualityGate()
    result = await gate.run(mock_fix_placeholder)

    assert result.final_status == "pending_review"
    stage3 = next((s for s in result.stage_results if s.stage == 3), None)
    if stage3:
        assert not stage3.passed


# ---------------------------------------------------------------------------
# Test 8: Rescan Notification wird erstellt
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rescan_notification_triggered():
    """
    notify_rescan_required erstellt einen user_legal_notifications-Eintrag.
    """
    from legal_notification_service import LegalNewsNotificationService

    pool, conn = make_db_pool(
        fetchrow={"user_id": "user-1", "email": "test@example.com"}
    )

    svc = LegalNewsNotificationService(pool)
    svc.frontend_url = "https://app.complyo.tech"

    await svc.notify_rescan_required(
        website_id="site-1",
        legal_update={"id": 42, "title": "WCAG 2.2"},
        severity="medium",
    )

    # INSERT INTO user_legal_notifications muss aufgerufen worden sein
    conn.execute.assert_called()
    call_sql = conn.execute.call_args[0][0].lower()
    assert "user_legal_notifications" in call_sql or "insert" in call_sql


# ---------------------------------------------------------------------------
# Test 9: Admin Approve Fix (via mock DB)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_approve_fix():
    """
    approve_fix setzt quality_gate_status='validated' und returned success=True.
    """
    from admin_routes import approve_fix

    pool, conn = make_db_pool(fetchval=99)

    with patch("admin_routes.get_db_pool", return_value=pool):
        result = await approve_fix(fix_id=99, admin=True, db=conn)

    assert result["success"] is True
    assert result["new_status"] == "validated"


# ---------------------------------------------------------------------------
# Test 10: Admin Reject Fix — fehlende Begründung abgelehnt
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_reject_fix_requires_reason():
    """reject_fix mit zu kurzer Begründung → 422."""
    from admin_routes import reject_fix
    from fastapi import HTTPException

    pool, conn = make_db_pool(fetchval=99)

    with pytest.raises(HTTPException) as exc_info:
        await reject_fix(fix_id=99, reason="ab", admin=True, db=conn)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_admin_reject_fix_valid():
    """reject_fix mit valider Begründung → success=True."""
    from admin_routes import reject_fix

    pool, conn = make_db_pool(fetchval=99)

    result = await reject_fix(
        fix_id=99,
        reason="Fix enthält falschen ARIA-Role-Wert",
        admin=True,
        db=conn,
    )

    assert result["success"] is True
    assert result["new_status"] == "rejected"
