"""Unit tests for GET /api/cookie-compliance/agency/client-report/{client_name}."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import cookie_compliance_routes
from cookie_compliance_routes import router as cc_router


# 1x1 transparent PNG (smallest valid PNG)
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f"
    b"\x00\x00\x01\x01\x00\x05\xdb\x9eN\xa9\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(cc_router)
    monkeypatch.setattr(
        cookie_compliance_routes, "get_current_user_required",
        AsyncMock(return_value={"id": 1, "user_id": 1, "modules": ["cookie"]}),
    )
    monkeypatch.setattr(cookie_compliance_routes, "require_module", AsyncMock(return_value=True))
    return TestClient(app)


def _mock_db_pool(monkeypatch, fetch_rows=None, fetchrow_row=None):
    pool = MagicMock()
    pool.fetch = AsyncMock(return_value=fetch_rows or [])
    pool.fetchrow = AsyncMock(return_value=fetchrow_row)
    pool.execute = AsyncMock(return_value="UPDATE 1")
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", pool)
    return pool


def test_client_report_returns_pdf(client, monkeypatch):
    _mock_db_pool(
        monkeypatch,
        fetch_rows=[
            {"site_id": "kunde-a-de", "last_scan_url": "https://kunde-a.de",
             "compliance_score": 80, "scan_data": {"detected_issues": [
                 {"title": "A", "severity": "high"},
                 {"title": "B", "severity": "high"},
                 {"title": "C", "severity": "medium"},
             ]}},
        ],
        fetchrow_row={"agency_logo_path": None},
    )
    r = client.get("/api/cookie-compliance/agency/client-report/Mustermann%20GmbH",
                   headers={"Authorization": "Bearer test"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:5] == b"%PDF-"


def test_client_report_with_logo(client, monkeypatch):
    _mock_db_pool(
        monkeypatch,
        fetch_rows=[{"site_id": "x", "last_scan_url": "https://x.de",
                     "compliance_score": 75, "scan_data": {"detected_issues": []}}],
        fetchrow_row={"agency_logo_path": "ai_documentation/1/logos/logo.png"},
    )
    get_file_mock = AsyncMock(return_value=TINY_PNG)
    monkeypatch.setattr(cookie_compliance_routes.file_storage, "get_file", get_file_mock)
    r = client.get("/api/cookie-compliance/agency/client-report/Acme",
                   headers={"Authorization": "Bearer test"})
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"
    get_file_mock.assert_awaited_once_with("ai_documentation/1/logos/logo.png")


def test_client_report_no_sites_assigned(client, monkeypatch):
    _mock_db_pool(monkeypatch, fetch_rows=[], fetchrow_row={"agency_logo_path": None})
    r = client.get("/api/cookie-compliance/agency/client-report/NoSites",
                   headers={"Authorization": "Bearer test"})
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"


def test_client_report_db_pool_none_returns_503(client, monkeypatch):
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", None)
    r = client.get("/api/cookie-compliance/agency/client-report/X",
                   headers={"Authorization": "Bearer test"})
    assert r.status_code == 503
