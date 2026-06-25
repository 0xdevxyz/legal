"""
Unit tests for POST /api/v2/accessibility/generate-statement endpoint.

Covers AUDIT-05 verification criteria:
- SC1: Returns {html, markdown, filename} JSON
- SC2: Populates conformance status + known issues from scan data
- SC2 fallback: "Nicht bewertet" when no scan exists
- SC4: All 6 BFSG required fields present + BMAS URL
- Security: Jinja2 autoescape prevents XSS
"""

from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
import os

# Add parent directory to path so module imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import accessibility_fix_routes
from accessibility_fix_routes import accessibility_fix_router


# =============================================================================
# Constants
# =============================================================================

SAMPLE_ROW_NO_ISSUES = {
    "fix_package": {
        "summary": {"total_issues": 0},
        "widget_fixes": [],
        "code_patches": [],
        "manual_guides": [],
    },
    "site_url": "https://example.de",
    "created_at": "2026-04-30T12:00:00",
}

SAMPLE_ROW_WITH_ISSUES = {
    "fix_package": {
        "summary": {"total_issues": 5},
        "widget_fixes": [{"description": "Alt-Texte für 12 Bilder fehlen"}],
        "code_patches": [{"description": "Kontrastverhältnis 4 Buttons zu niedrig"}],
        "manual_guides": [{"description": "Tastaturnavigation Menü prüfen"}],
    },
    "site_url": "https://example.de",
    "created_at": "2026-04-30T12:00:00",
}

VALID_PAYLOAD = {
    "site_id": "example-de",
    "site_url": "https://example.de",
    "contact_email": "kontakt@example.de",
    "review_date": "2026-04-30",
}


# =============================================================================
# Helpers
# =============================================================================

def mock_user():
    return {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "is_premium": True,
        "modules": ["accessibility"],
    }


def auth_headers():
    return {"Authorization": "Bearer fake-jwt-token"}


def make_app():
    app = FastAPI()
    app.include_router(accessibility_fix_router)
    return TestClient(app)


def setup_mocks(monkeypatch, db_row=None, user=None):
    """Configure mocks for auth_service, db_pool, and require_accessibility_module."""
    # Mock auth_service so get_current_user accepts the fake Bearer token
    mock_auth = MagicMock()
    mock_auth.verify_token = MagicMock(return_value=user or mock_user())
    monkeypatch.setattr(accessibility_fix_routes, "auth_service", mock_auth)

    # Mock db_pool with a connection whose fetchrow returns db_row
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=db_row)
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr(accessibility_fix_routes, "db_pool", mock_pool)

    # Bypass the module-gate check (avoids DB lookup for subscription status)
    async def _noop(user):
        return None
    monkeypatch.setattr(accessibility_fix_routes, "require_accessibility_module", _noop)


# =============================================================================
# Tests
# =============================================================================

def test_generate_statement_requires_auth():
    """POST without Bearer token must return 401 or 403 (FastAPI HTTPBearer rejects)."""
    client = make_app()
    response = client.post("/api/v2/accessibility/generate-statement", json=VALID_PAYLOAD)
    assert response.status_code in (401, 403), (
        f"Expected 401 or 403 without auth, got {response.status_code}"
    )


def test_generate_statement_returns_correct_shape(monkeypatch):
    """Valid request returns JSON with keys 'html', 'markdown', 'filename'."""
    setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app()
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=VALID_PAYLOAD,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "html" in data, "Response must contain 'html' key"
    assert "markdown" in data, "Response must contain 'markdown' key"
    assert "filename" in data, "Response must contain 'filename' key"
    assert isinstance(data["html"], str) and len(data["html"]) > 0, "html must be non-empty string"
    assert isinstance(data["markdown"], str) and len(data["markdown"]) > 0, "markdown must be non-empty string"
    assert data["filename"] == "barrierefreiheitserklaerung.html", (
        f"filename must be 'barrierefreiheitserklaerung.html', got {data['filename']!r}"
    )


def test_generate_statement_no_scan_fallback(monkeypatch):
    """When fetchrow returns None (no scan data), response html must contain 'Nicht bewertet'."""
    setup_mocks(monkeypatch, db_row=None)
    client = make_app()
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=VALID_PAYLOAD,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    html = response.json()["html"]
    assert "Nicht bewertet" in html, (
        "When no scan data exists, html must contain 'Nicht bewertet'"
    )


def test_generate_statement_uses_scan_data_zero_issues(monkeypatch):
    """When total_issues == 0, html must contain 'vollständig konform mit WCAG 2.1 Level AA'."""
    setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app()
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=VALID_PAYLOAD,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    html = response.json()["html"]
    assert "vollständig konform mit WCAG 2.1 Level AA" in html, (
        "When total_issues == 0, html must contain 'vollständig konform mit WCAG 2.1 Level AA'"
    )


def test_generate_statement_uses_scan_data_with_issues(monkeypatch):
    """When total_issues > 0, html must contain 'teilweise konform' AND issue descriptions."""
    setup_mocks(monkeypatch, db_row=SAMPLE_ROW_WITH_ISSUES)
    client = make_app()
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=VALID_PAYLOAD,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    html = response.json()["html"]
    assert "teilweise konform" in html, (
        "When total_issues > 0, html must contain 'teilweise konform'"
    )
    # Issue descriptions from widget_fixes, code_patches, manual_guides must appear
    assert "Alt-Texte für 12 Bilder fehlen" in html, (
        "Issue descriptions from widget_fixes must be listed in the html"
    )
    assert "Kontrastverhältnis 4 Buttons zu niedrig" in html, (
        "Issue descriptions from code_patches must be listed in the html"
    )


def test_statement_contains_bfsg_required_fields(monkeypatch):
    """Generated html must contain all 6 BFSG required section markers."""
    setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app()
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=VALID_PAYLOAD,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    html = response.json()["html"]

    required_fields = [
        "Geltungsbereich",
        "Stand der Vereinbarkeit",
        "Nicht barrierefreie Inhalte",
        "Kontakt",
        "Durchsetzungsverfahren",
    ]
    for field in required_fields:
        assert field in html, f"BFSG required field '{field}' missing from generated html"

    # Datum must be present (any date-like string — check for "2026" or day format)
    import re
    assert re.search(r"\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2}", html), (
        "Generated html must contain a date (Datum field)"
    )


def test_statement_contains_bmas_url(monkeypatch):
    """Generated html must contain the BMAS Schlichtungsstelle URL."""
    setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app()
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=VALID_PAYLOAD,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    html = response.json()["html"]
    assert "https://www.schlichtungsstelle-bfsg.de/" in html, (
        "Generated html must contain BMAS Schlichtungsstelle URL"
    )


def test_generate_statement_escapes_html(monkeypatch):
    """XSS vector in contact_email must be escaped — literal '<script>' must NOT appear in html."""
    setup_mocks(monkeypatch, db_row=None)
    client = make_app()
    xss_payload = dict(VALID_PAYLOAD)
    xss_payload["contact_email"] = "evil<script>alert(1)</script>@x.de"
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=xss_payload,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    html = response.json()["html"]
    assert "<script>" not in html, (
        "Jinja2 autoescape must prevent raw '<script>' appearing in html output"
    )
