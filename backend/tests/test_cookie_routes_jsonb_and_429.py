"""
Regressionstests für cookie_compliance_routes:

1) asyncpg-JSONB: Der Pool hat KEINEN json-Codec. JSONB-Spalten müssen mit
   json.dumps() geschrieben werden — eine rohe Liste/ein rohes dict führt in
   Produktion zu DataError/500. POST /import schrieb 'services' als rohe Liste.

2) POST /consent verschluckte die eigene HTTPException(429) im generischen
   'except Exception' und lieferte 500 statt 429 an das Widget.
"""

import datetime
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

import cookie_compliance_routes
from cookie_compliance_routes import router as cookie_router


def make_client():
    app = FastAPI()
    app.include_router(cookie_router)
    return TestClient(app, raise_server_exceptions=False)


# ============================================================================
# 1) JSONB-Writes
# ============================================================================

CONSENT_PAYLOAD = {
    "site_id": "test-site",
    "visitor_id": "visitor-abc",
    "consent_categories": {
        "necessary": True,
        "functional": False,
        "analytics": False,
        "marketing": False,
    },
}


def test_import_writes_services_as_json_string(monkeypatch):
    """
    POST /import muss 'services' als JSON-String übergeben.
    Vor dem Fix wurde die rohe Liste durchgereicht -> asyncpg DataError.
    """
    mock_pool = MagicMock()
    # fetchrow #1: existing config lookup, #2: UPDATE ... RETURNING id
    mock_pool.fetchrow = AsyncMock(side_effect=[{"id": 1}, {"id": 1}])
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    monkeypatch.setattr(
        cookie_compliance_routes, "require_site_access", AsyncMock(return_value=None)
    )

    client = make_client()
    services = [{"key": "ga4", "enabled": True}]
    resp = client.post(
        "/api/cookie-compliance/import",
        json={
            "site_id": "test-site",
            "import": {"config": {"services": services, "texts": {"de": {}}}},
        },
        headers={"Authorization": "Bearer x"},
    )

    assert resp.status_code == 200, resp.text
    update_call = mock_pool.fetchrow.call_args_list[1]
    # args[0] ist die Query selbst -> args[N] entspricht $N
    services_arg = update_call.args[7]  # $7 = services

    assert isinstance(services_arg, str), (
        f"services muss ein JSON-String sein (json.dumps), war {type(services_arg)}"
    )
    assert json.loads(services_arg) == services


def test_import_all_jsonb_args_are_strings(monkeypatch):
    """Alle JSONB-Spalten der Import-Route (services, texts, consent_mode_default)."""
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(side_effect=[{"id": 1}, {"id": 1}])
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    monkeypatch.setattr(
        cookie_compliance_routes, "require_site_access", AsyncMock(return_value=None)
    )

    client = make_client()
    client.post(
        "/api/cookie-compliance/import",
        json={
            "site_id": "test-site",
            "import": {
                "config": {
                    "services": [{"key": "ga4"}],
                    "texts": {"de": {"title": "Hi"}},
                    "consent_mode_default": {"ad_storage": "denied"},
                }
            },
        },
        headers={"Authorization": "Bearer x"},
    )

    args = mock_pool.fetchrow.call_args_list[1].args
    # args[0] ist die Query selbst -> args[N] entspricht $N
    for idx, name in ((7, "services"), (8, "texts"), (10, "consent_mode_default")):
        assert isinstance(args[idx], str), f"{name} muss json.dumps()-String sein"
        json.loads(args[idx])  # muss parsebar sein


def test_import_source_has_no_raw_services_write():
    """Negativ-Wächter direkt auf der Quelle."""
    import inspect

    src = inspect.getsource(cookie_compliance_routes)
    assert "config.get('services', [])," not in src, (
        "services wird roh (ohne json.dumps) in eine JSONB-Spalte geschrieben"
    )


# ============================================================================
# 2) 429 darf nicht zu 500 werden
# ============================================================================

def test_consent_rate_limit_returns_429_not_500(monkeypatch):
    """Die eigene HTTPException(429) muss durchgereicht werden."""
    monkeypatch.setattr(
        cookie_compliance_routes, "check_rate_limit", AsyncMock(return_value=False)
    )
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)
    mock_pool.execute = AsyncMock(return_value=None)
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)

    client = make_client()
    resp = client.post("/api/cookie-compliance/consent", json=CONSENT_PAYLOAD)

    assert resp.status_code == 429, (
        f"Rate-Limit muss 429 liefern, war {resp.status_code}: {resp.text}"
    )
    assert "Rate limit" in resp.json()["detail"]


def test_consent_within_rate_limit_still_returns_200(monkeypatch):
    """Negativkontrolle: der Happy-Path bleibt unberührt."""
    monkeypatch.setattr(
        cookie_compliance_routes, "check_rate_limit", AsyncMock(return_value=True)
    )
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(
        side_effect=[
            None,
            {"id": 42, "timestamp": datetime.datetime(2026, 5, 1, 12, 0, 0)},
        ]
    )
    mock_pool.execute = AsyncMock(return_value=None)
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)

    client = make_client()
    resp = client.post("/api/cookie-compliance/consent", json=CONSENT_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["consent_id"] == 42


def test_consent_real_error_still_returns_500(monkeypatch):
    """Echte Fehler müssen weiterhin 500 liefern — der Fix darf das nicht aufweichen."""
    monkeypatch.setattr(
        cookie_compliance_routes, "check_rate_limit", AsyncMock(return_value=True)
    )
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(side_effect=RuntimeError("db kaputt"))
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)

    client = make_client()
    resp = client.post("/api/cookie-compliance/consent", json=CONSENT_PAYLOAD)
    assert resp.status_code == 500
