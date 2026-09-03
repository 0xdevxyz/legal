"""
Unit tests for POST /api/v2/accessibility/generate-statement endpoint.

Covers AUDIT-05 verification criteria:
- SC1: Returns {html, markdown, filename} JSON
- SC2: Populates conformance status + known issues from scan data
- SC2 fallback: "Nicht bewertet" when no scan exists
- SC4: All 6 BFSG required fields present + BMAS URL
- Security: Jinja2 autoescape prevents XSS
"""

from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest
import sys
import os

# Add parent directory to path so module imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import accessibility_fix_routes
from accessibility_fix_routes import accessibility_fix_router
from dependencies import get_current_user


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


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def disable_rate_limit():
    """Deaktiviert das Redis-Rate-Limit (5/60s) für alle Tests dieser Datei.

    Die Route hängt an `Depends(rate_limit("a11y_statement", 5, 60))`. Das Limit
    zählt in einem echten Redis pro Client-IP — im TestClient ist die IP für ALLE
    Tests identisch ("testclient"), das Sliding Window (60s) überlebt also
    Testgrenzen. Ab dem 6. Request im Gesamtlauf antwortete die Route mit 429,
    bevor Auth-/Payload-Logik überhaupt lief.

    `rate_limit._check` ist fail-open: ohne Redis wird das Limit nicht
    durchgesetzt. Wir patchen daher `dependencies.get_redis` auf None — das
    Limit ist damit pro Test deterministisch aus, ohne die eigentlichen
    Aussagen der Tests (Auth, Response-Shape, Escaping) zu berühren.
    Das Rate-Limit selbst ist nicht Gegenstand dieser Datei.
    """
    with patch("dependencies.get_redis", AsyncMock(return_value=None)):
        yield


def auth_headers():
    return {"Authorization": "Bearer fake-jwt-token"}


def make_app(user=None):
    """Baut die Test-App.

    Ohne `user` bleibt die echte Auth-Dependency aktiv (für den Auth-Test).
    Mit `user` wird `get_current_user` per dependency_overrides ersetzt.
    """
    app = FastAPI()
    app.include_router(accessibility_fix_router)
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def setup_mocks(monkeypatch, db_row=None, user=None):
    """Konfiguriert db_pool + Modul-Gate und liefert den Test-User zurück.

    Auth wird NICHT mehr hier gemockt: Die Route hängt seit der Auth-Härtung an
    der kanonischen Dependency `dependencies.get_current_user` (JWT-Decode +
    DB-Lookup) und nutzt das modul-lokale `accessibility_fix_routes.auth_service`
    nicht mehr. Der alte `auth_service.verify_token`-Mock lief deshalb ins Leere
    (→ 401); sichtbar wurde das erst, nachdem das Rate-Limit-429 weg war.
    Der zurückgegebene User geht an `make_app()` und wird dort per
    dependency_overrides injiziert — der eigentliche Auth-Test bleibt davon
    unberührt und prüft weiter gegen die echte Dependency.
    """
    resolved_user = user or mock_user()

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

    return resolved_user


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
    user = setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app(user)
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
    user = setup_mocks(monkeypatch, db_row=None)
    client = make_app(user)
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
    """Bei total_issues == 0 werden die Scan-Daten genutzt — aber OHNE Konformitätsversprechen.

    Der Test erwartete früher 'vollständig konform mit WCAG 2.1 Level AA'. Die
    Route formuliert bewusst anders: Ein automatisierter Scan deckt nur einen
    Teil der WCAG-Kriterien ab und darf deshalb keine vollständige Konformität
    bescheinigen — eine solche Aussage wäre in einer BFSG-Erklärung eine
    Falschangabe. Das Produkt hat recht, die alte Erwartung war überholt.

    Geprüft wird daher der eigentliche Kern von SC2: Scan-Daten (0 Issues)
    werden verwendet (Abgrenzung zum 'Nicht bewertet'-Fallback), und es wird
    KEINE vollständige Konformität behauptet.
    """
    user = setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app(user)
    response = client.post(
        "/api/v2/accessibility/generate-statement",
        json=VALID_PAYLOAD,
        headers=auth_headers(),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    html = response.json()["html"]
    assert "keine Abweichungen von WCAG 2.1 Level AA" in html, (
        "Bei total_issues == 0 muss das Ergebnis des Scans ausgewiesen werden"
    )
    assert "Nicht bewertet" not in html, (
        "Mit vorhandenen Scan-Daten darf NICHT der 'Nicht bewertet'-Fallback greifen"
    )
    assert "vollständig konform" not in html, (
        "Ein automatisierter Scan darf keine vollständige WCAG-Konformität bescheinigen"
    )


def test_generate_statement_uses_scan_data_with_issues(monkeypatch):
    """When total_issues > 0, html must contain 'teilweise konform' AND issue descriptions."""
    user = setup_mocks(monkeypatch, db_row=SAMPLE_ROW_WITH_ISSUES)
    client = make_app(user)
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
    user = setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app(user)
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
    user = setup_mocks(monkeypatch, db_row=SAMPLE_ROW_NO_ISSUES)
    client = make_app(user)
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
    user = setup_mocks(monkeypatch, db_row=None)
    client = make_app(user)
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
