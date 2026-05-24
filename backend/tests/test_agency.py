"""
Unit tests for Phase 10 Agency Channel endpoints (AGENCY-01 + AGENCY-03).

Covers:
- PATCH /api/cookie-compliance/agency/sites/{site_id}/client  (assign client attribution)
- GET  /api/cookie-compliance/agency/clients                  (grouped client list)
- POST /api/cookie-compliance/agency/logo                     (PNG logo upload)

All tests use FastAPI TestClient + monkeypatch — zero live DB or file system deps.
RED stage: tests fail with 404 until Task 3 implements the endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
import os

# Parent directory already on path via conftest.py, but be explicit for clarity
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cookie_compliance_routes


# =============================================================================
# Helpers
# =============================================================================

def make_app() -> TestClient:
    """Create a fresh FastAPI app with the cookie_compliance_routes router mounted."""
    app = FastAPI()
    app.include_router(cookie_compliance_routes.router)
    return TestClient(app)


def auth_headers() -> dict:
    return {"Authorization": "Bearer test-token"}


def mock_user() -> dict:
    return {"id": 1, "user_id": 1, "modules": ["cookie"]}


def _patch_auth(monkeypatch):
    """Patch get_current_user_required and require_module so they always succeed."""
    async def _fake_get_current_user_required(credentials):
        return mock_user()

    async def _fake_require_module(user, module_id):
        return True

    monkeypatch.setattr(
        cookie_compliance_routes,
        "get_current_user_required",
        _fake_get_current_user_required,
    )
    monkeypatch.setattr(
        cookie_compliance_routes,
        "require_module",
        _fake_require_module,
    )


def _patch_db_pool(monkeypatch, fetch_return=None, execute_return="UPDATE 1"):
    """Replace module-level db_pool with a MagicMock with async methods."""
    mock_pool = MagicMock()
    mock_pool.fetch = AsyncMock(return_value=fetch_return or [])
    mock_pool.execute = AsyncMock(return_value=execute_return)
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    return mock_pool


# =============================================================================
# AGENCY-01: PATCH /api/cookie-compliance/agency/sites/{site_id}/client
# =============================================================================

def test_assign_client(monkeypatch):
    """PATCH with valid body returns 200 and confirms db_pool.execute called with UPDATE."""
    _patch_auth(monkeypatch)
    mock_pool = _patch_db_pool(monkeypatch, execute_return="UPDATE 1")
    client = make_app()

    response = client.patch(
        "/api/cookie-compliance/agency/sites/site-abc/client",
        json={"client_name": "Musterfirma GmbH", "client_email": "kontakt@musterfirma.de"},
        headers=auth_headers(),
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["ok"] is True
    assert data["site_id"] == "site-abc"
    assert data["client_name"] == "Musterfirma GmbH"

    # db_pool.execute must have been called (the UPDATE)
    mock_pool.execute.assert_called_once()
    call_sql = mock_pool.execute.call_args[0][0]
    assert "UPDATE" in call_sql.upper(), "execute call must contain UPDATE statement"


def test_assign_client_not_found(monkeypatch):
    """PATCH where site does not belong to user (UPDATE affects 0 rows) returns 404."""
    _patch_auth(monkeypatch)
    # asyncpg returns the string 'UPDATE 0' when no rows matched
    _patch_db_pool(monkeypatch, execute_return="UPDATE 0")
    client = make_app()

    response = client.patch(
        "/api/cookie-compliance/agency/sites/unknown-site/client",
        json={"client_name": "Nobody", "client_email": "nobody@example.com"},
        headers=auth_headers(),
    )

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


# =============================================================================
# AGENCY-02: GET /api/cookie-compliance/agency/clients
# =============================================================================

def test_get_agency_clients(monkeypatch):
    """GET returns {'clients': [...]} with site_count and acceptance_rate per group."""
    _patch_auth(monkeypatch)

    # Two fake grouped rows (one per client)
    fake_rows = [
        {
            "client_name": "Firma Alpha",
            "client_email": "alpha@example.de",
            "site_count": 3,
            "total_impressions": 1000,
            "total_accepted": 750,
        },
        {
            "client_name": "Firma Beta",
            "client_email": "beta@example.de",
            "site_count": 1,
            "total_impressions": 200,
            "total_accepted": 100,
        },
    ]
    _patch_db_pool(monkeypatch, fetch_return=fake_rows)
    client = make_app()

    response = client.get(
        "/api/cookie-compliance/agency/clients",
        headers=auth_headers(),
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "clients" in data, "Response must have 'clients' key"
    assert len(data["clients"]) == 2

    alpha = data["clients"][0]
    assert alpha["client_name"] == "Firma Alpha"
    assert alpha["site_count"] == 3
    assert "acceptance_rate" in alpha
    assert alpha["acceptance_rate"] == round(750 / 1000, 4)


def test_clients_excludes_null(monkeypatch):
    """SQL query passed to db_pool.fetch must filter by 'c.client_name IS NOT NULL'."""
    _patch_auth(monkeypatch)
    mock_pool = _patch_db_pool(monkeypatch, fetch_return=[])
    client = make_app()

    client.get(
        "/api/cookie-compliance/agency/clients",
        headers=auth_headers(),
    )

    # Verify the SQL string passed to fetch contains the NULL filter
    mock_pool.fetch.assert_called_once()
    call_sql = mock_pool.fetch.call_args[0][0]
    assert "c.client_name IS NOT NULL" in call_sql, (
        "SQL passed to db_pool.fetch must contain 'c.client_name IS NOT NULL'"
    )


# =============================================================================
# AGENCY-03: POST /api/cookie-compliance/agency/logo
# =============================================================================

# Minimal valid 1×1 PNG header bytes (the actual image is tiny but PNG-magic is correct)
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"x" * 100


def test_logo_upload_png_ok(monkeypatch):
    """Valid PNG under 2 MB returns 200 and db_pool.execute updates agency_logo_path."""
    _patch_auth(monkeypatch)
    mock_pool = _patch_db_pool(monkeypatch, execute_return="UPDATE 1")

    # Patch file_storage.save_file to avoid actual filesystem writes
    mock_storage = AsyncMock(return_value={"relative_path": "logos/logo.png", "filename": "logo.png"})
    monkeypatch.setattr(cookie_compliance_routes.file_storage, "save_file", mock_storage)

    client = make_app()
    response = client.post(
        "/api/cookie-compliance/agency/logo",
        files={"file": ("logo.png", _PNG_MAGIC, "image/png")},
        headers=auth_headers(),
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "relative_path" in data, "Response must contain 'relative_path'"

    # UPDATE users SET agency_logo_path must have been called
    mock_pool.execute.assert_called_once()
    call_sql = mock_pool.execute.call_args[0][0]
    assert "agency_logo_path" in call_sql.lower(), "execute must update agency_logo_path"


def test_logo_upload_svg_rejected(monkeypatch):
    """SVG content type returns 400 with detail containing 'PNG'."""
    _patch_auth(monkeypatch)
    _patch_db_pool(monkeypatch)
    client = make_app()

    response = client.post(
        "/api/cookie-compliance/agency/logo",
        files={"file": ("logo.svg", b"<svg/>", "image/svg+xml")},
        headers=auth_headers(),
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    assert "PNG" in response.json().get("detail", ""), "Error detail must mention 'PNG'"


def test_logo_upload_jpeg_rejected(monkeypatch):
    """JPEG content type returns 400."""
    _patch_auth(monkeypatch)
    _patch_db_pool(monkeypatch)
    client = make_app()

    response = client.post(
        "/api/cookie-compliance/agency/logo",
        files={"file": ("logo.jpg", b"\xff\xd8\xff" + b"x" * 50, "image/jpeg")},
        headers=auth_headers(),
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


def test_logo_upload_too_large(monkeypatch):
    """File > 2 MB returns 400 with detail mentioning size limit."""
    _patch_auth(monkeypatch)
    _patch_db_pool(monkeypatch)
    client = make_app()

    oversized_content = b"x" * (2 * 1024 * 1024 + 1024)  # 2 MB + 1 KB
    response = client.post(
        "/api/cookie-compliance/agency/logo",
        files={"file": ("logo.png", oversized_content, "image/png")},
        headers=auth_headers(),
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    detail = response.json().get("detail", "").lower()
    assert "2 mb" in detail or "zu groß" in detail, (
        f"Error detail must mention size limit, got: {detail!r}"
    )
