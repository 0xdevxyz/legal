"""
AUDIT-06: Cookie Consent Flow E2E Tests
Tests the POST /api/cookie-compliance/consent endpoint using FastAPI TestClient + monkeypatch.
No real DB connection required.
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
    """
    Patch cookie_compliance_routes.db_pool with an AsyncMock that handles:
    - fetchrow #1: SELECT from cookie_banner_configs
    - fetchrow #2: INSERT INTO cookie_consent_logs RETURNING id, timestamp
    - execute: UPDATE cookie_compliance_stats (mocked to avoid schema bug)
    """
    if config_row is None:
        config_row = None  # no config found → revision_id defaults to 1

    if insert_row is None:
        insert_row = {
            "id": 42,
            "timestamp": datetime.datetime(2026, 5, 1, 12, 0, 0),
        }

    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(side_effect=[config_row, insert_row])
    mock_pool.execute = AsyncMock(return_value=None)
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    return mock_pool


REJECT_PAYLOAD = {
    "site_id": "test-site",
    "visitor_id": "visitor-abc",
    "consent_categories": {
        "necessary": True,
        "functional": False,
        "analytics": False,
        "marketing": False,
    },
}

ACCEPT_ALL_PAYLOAD = {
    "site_id": "test-site",
    "visitor_id": "visitor-abc",
    "consent_categories": {
        "necessary": True,
        "functional": True,
        "analytics": True,
        "marketing": True,
    },
}


def test_reject_all_returns_200_with_consent_id(monkeypatch):
    mock_db_pool(monkeypatch)
    client = make_client()
    response = client.post("/api/cookie-compliance/consent", json=REJECT_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["consent_id"] == 42


def test_reject_all_returns_timestamp(monkeypatch):
    mock_db_pool(monkeypatch)
    client = make_client()
    response = client.post("/api/cookie-compliance/consent", json=REJECT_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "2026" in data["timestamp"]


def test_reject_all_passes_only_necessary_to_db(monkeypatch):
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    client.post("/api/cookie-compliance/consent", json=REJECT_PAYLOAD)

    insert_call = pool.fetchrow.call_args_list[1]
    categories_json = insert_call.args[3]
    import json as _json
    cats = _json.loads(categories_json)
    assert cats["necessary"] is True
    assert cats["analytics"] is False
    assert cats["marketing"] is False
    assert cats["functional"] is False


def test_accept_all_returns_200_with_consent_id(monkeypatch):
    mock_db_pool(monkeypatch)
    client = make_client()
    response = client.post("/api/cookie-compliance/consent", json=ACCEPT_ALL_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["consent_id"] == 42


def test_accept_all_passes_all_four_categories_as_true(monkeypatch):
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    client.post("/api/cookie-compliance/consent", json=ACCEPT_ALL_PAYLOAD)

    insert_call = pool.fetchrow.call_args_list[1]
    import json as _json
    cats = _json.loads(insert_call.args[3])
    assert cats["necessary"] is True
    assert cats["functional"] is True
    assert cats["analytics"] is True
    assert cats["marketing"] is True


def test_consent_uses_config_revision_when_found(monkeypatch):
    config_row = {"id": 99}
    insert_row = {"id": 7, "timestamp": datetime.datetime(2026, 5, 1, 12, 0, 0)}
    pool = mock_db_pool(monkeypatch, config_row=config_row, insert_row=insert_row)
    client = make_client()
    response = client.post("/api/cookie-compliance/consent", json=REJECT_PAYLOAD)
    assert response.status_code == 200
    insert_call = pool.fetchrow.call_args_list[1]
    revision_id = insert_call.args[8]
    assert revision_id == 99


def test_consent_defaults_to_revision_1_when_no_config(monkeypatch):
    pool = mock_db_pool(monkeypatch, config_row=None)
    client = make_client()
    client.post("/api/cookie-compliance/consent", json=REJECT_PAYLOAD)
    insert_call = pool.fetchrow.call_args_list[1]
    revision_id = insert_call.args[8]
    assert revision_id == 1


def test_stats_upsert_is_called_once(monkeypatch):
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    client.post("/api/cookie-compliance/consent", json=REJECT_PAYLOAD)
    pool.execute.assert_awaited_once()


def test_missing_site_id_returns_422(monkeypatch):
    mock_db_pool(monkeypatch)
    client = make_client()
    payload = dict(REJECT_PAYLOAD)
    del payload["site_id"]
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 422


def test_missing_visitor_id_returns_422(monkeypatch):
    mock_db_pool(monkeypatch)
    client = make_client()
    payload = dict(REJECT_PAYLOAD)
    del payload["visitor_id"]
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 422


def test_partial_consent_analytics_only(monkeypatch):
    pool = mock_db_pool(monkeypatch)
    client = make_client()
    payload = {
        "site_id": "test-site",
        "visitor_id": "visitor-xyz",
        "consent_categories": {
            "necessary": True,
            "functional": False,
            "analytics": True,
            "marketing": False,
        },
    }
    response = client.post("/api/cookie-compliance/consent", json=payload)
    assert response.status_code == 200
    insert_call = pool.fetchrow.call_args_list[1]
    import json as _json
    cats = _json.loads(insert_call.args[3])
    assert cats["analytics"] is True
    assert cats["marketing"] is False
