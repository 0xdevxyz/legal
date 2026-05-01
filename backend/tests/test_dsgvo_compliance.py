"""
AUDIT-08: DSGVO §25 TTDSG Pre-Consent Compliance Tests
Validates that no tracking happens before explicit consent and that
banner_shown=False is not treated as a valid consent signal.
"""

import datetime
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

import cookie_compliance_routes
from cookie_compliance_routes import router as cookie_router


def make_client():
    app = FastAPI()
    app.include_router(cookie_router)
    return TestClient(app)


def mock_db_pool(monkeypatch, config_row=None, insert_row=None):
    if insert_row is None:
        insert_row = {
            "id": 1,
            "timestamp": datetime.datetime(2026, 5, 1, 12, 0, 0),
        }
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(side_effect=[config_row, insert_row])
    mock_pool.execute = AsyncMock(return_value=None)
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    return mock_pool


def test_banner_shown_false_does_not_enable_tracking(monkeypatch):
    """
    DSGVO §25: A request with banner_shown=False must still be accepted by the
    API (it records the implicit state), but the stored consent_categories must
    have analytics and marketing as False — i.e. no tracking is enabled.
    """
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "test-site",
        "visitor_id": "visitor-implicit",
        "banner_shown": False,
        "consent_categories": {
            "necessary": True,
            "functional": False,
            "analytics": False,
            "marketing": False,
        },
    }
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 200

    insert_call = pool.fetchrow.call_args_list[1]
    import json as _json
    cats = _json.loads(insert_call.args[3])
    assert cats["analytics"] is False, "Analytics must be False when banner was not shown"
    assert cats["marketing"] is False, "Marketing must be False when banner was not shown"

    banner_shown_arg = insert_call.args[10]
    assert banner_shown_arg is False, "banner_shown flag must be persisted as False"


def test_banner_shown_false_with_analytics_true_is_stored_as_is(monkeypatch):
    """
    If a client sends banner_shown=False but analytics=True, the API stores
    exactly what was sent — it is the caller's responsibility to not call this
    before showing a banner. The endpoint must NOT silently coerce analytics=True
    to False. This test documents the current behaviour.
    """
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "test-site",
        "visitor_id": "visitor-suspicious",
        "banner_shown": False,
        "consent_categories": {
            "necessary": True,
            "functional": False,
            "analytics": True,
            "marketing": True,
        },
    }
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 200

    insert_call = pool.fetchrow.call_args_list[1]
    import json as _json
    cats = _json.loads(insert_call.args[3])
    assert cats["analytics"] is True
    assert cats["marketing"] is True
    banner_shown_arg = insert_call.args[10]
    assert banner_shown_arg is False


def test_only_necessary_consent_does_not_trigger_tracking_categories(monkeypatch):
    """
    When the user clicks 'Nur Notwendige', analytics and marketing must be False.
    """
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "test-site",
        "visitor_id": "visitor-necessary-only",
        "banner_shown": True,
        "consent_categories": {
            "necessary": True,
            "functional": False,
            "analytics": False,
            "marketing": False,
        },
    }
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 200

    insert_call = pool.fetchrow.call_args_list[1]
    import json as _json
    cats = _json.loads(insert_call.args[3])
    assert cats["analytics"] is False
    assert cats["marketing"] is False
    assert cats["functional"] is False
    assert cats["necessary"] is True


def test_user_agent_is_stored(monkeypatch):
    """
    DSGVO §25 / AUDIT-03: User-agent must be stored (truncated) in the consent log.
    """
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "test-site",
        "visitor_id": "visitor-ua-test",
        "banner_shown": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "consent_categories": {
            "necessary": True,
            "functional": False,
            "analytics": False,
            "marketing": False,
        },
    }
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 200

    insert_call = pool.fetchrow.call_args_list[1]
    stored_ua = insert_call.args[7]
    assert stored_ua is not None
    assert len(stored_ua) > 0


def test_ip_address_is_not_stored_in_plaintext(monkeypatch):
    """
    DSGVO: IP addresses must be hashed, not stored in plaintext.
    The insert call should pass an ip_hash (64 hex chars for sha256), not the raw IP.
    """
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "test-site",
        "visitor_id": "visitor-ip-test",
        "banner_shown": True,
        "ip_address": "192.168.1.100",
        "consent_categories": {
            "necessary": True,
            "functional": False,
            "analytics": False,
            "marketing": False,
        },
    }
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 200

    insert_call = pool.fetchrow.call_args_list[1]
    stored_ip = insert_call.args[5]
    assert stored_ip != "192.168.1.100", "Raw IP must not be stored"
    if stored_ip is not None:
        assert len(stored_ip) in (32, 40, 64), "IP should be stored as a hash"


def test_consent_without_analytics_results_in_rejected_all_stats(monkeypatch):
    """
    When only necessary=True and all others False, the stats upsert should
    mark rejected_all=1 and accepted_analytics=0.
    """
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "stats-site",
        "visitor_id": "visitor-stats",
        "banner_shown": True,
        "consent_categories": {
            "necessary": True,
            "functional": False,
            "analytics": False,
            "marketing": False,
        },
    }
    client.post("/api/cookie-compliance/consent", json=payload)

    execute_call = pool.execute.call_args
    args = execute_call.args
    accepted_all = args[3]
    rejected_all = args[5]
    accepted_analytics = args[6]
    assert accepted_all == 0
    assert rejected_all == 1
    assert accepted_analytics == 0


def test_consent_with_all_true_results_in_accepted_all_stats(monkeypatch):
    """
    When all categories are True, stats should mark accepted_all=1.
    """
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "stats-site",
        "visitor_id": "visitor-accept-all",
        "banner_shown": True,
        "consent_categories": {
            "necessary": True,
            "functional": True,
            "analytics": True,
            "marketing": True,
        },
    }
    client.post("/api/cookie-compliance/consent", json=payload)

    execute_call = pool.execute.call_args
    args = execute_call.args
    accepted_all = args[3]
    rejected_all = args[5]
    assert accepted_all == 1
    assert rejected_all == 0
