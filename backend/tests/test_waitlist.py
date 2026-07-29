"""
Tests für die Early-Access Waitlist-Endpoints
Deckt ab: Happy-Path, Honeypot, Zeitfalle, Turnstile, Consent-False, Duplicate,
Token-Confirm, Rate-Limit
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI


def build_app():
    app = FastAPI()
    from lead_routes import lead_router
    app.include_router(lead_router)
    return app


def _form_ts(vor_sekunden: float = 10) -> int:
    """form_ts wie das Formular es setzt: Renderzeitpunkt in Millisekunden.

    10 Sekunden zurück liegt sicher im erlaubten Fenster der Zeitfalle
    (_MIN_FILL_SECONDS = 4 bis _MAX_FORM_AGE_SECONDS = 6 h). Der Wert wird beim
    Import berechnet; die verstrichene Zeit wächst danach nur, bleibt also gültig.
    """
    return int((datetime.now(timezone.utc).timestamp() - vor_sekunden) * 1000)


VALID_PAYLOAD = {
    "email": "test@example.de",
    "name": "Max Mustermann",
    "phone": "+49 123 456789",
    "consent": True,
    "website": "",
    "source": "early-access",
    # Ohne form_ts greift die Zeitfalle und der Endpunkt antwortet still mit 204,
    # bevor Rate-Limit oder Speicherung überhaupt erreicht werden.
    "form_ts": _form_ts(),
}

CONFIRM_TOKEN = "valid_token_abc123"


@pytest.fixture()
def client():
    app = build_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_rate_limit():
    import lead_routes
    lead_routes._rate_limit_store.clear()
    yield
    lead_routes._rate_limit_store.clear()


class TestWaitlistJoin:
    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_happy_path(self, mock_db, mock_email, client):
        mock_db.execute_query = AsyncMock(side_effect=[None, None])
        mock_email.send_waitlist_confirmation = MagicMock(return_value=True)

        response = client.post("/api/leads/waitlist", json=VALID_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_confirmation"
        assert "Bestätigungsmail" in data["message"]

    @patch("lead_routes.db_service")
    def test_consent_false_returns_422(self, mock_db, client):
        payload = {**VALID_PAYLOAD, "consent": False}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 422

    def test_honeypot_filled_returns_204(self, client):
        payload = {**VALID_PAYLOAD, "website": "http://spam.bot"}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204

    @patch("lead_routes.db_service")
    def test_ohne_form_ts_greift_die_zeitfalle(self, mock_db, client):
        """Wer direkt auf den Endpunkt POSTet, hat kein Formular gerendert."""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "form_ts"}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204
        mock_db.execute_query.assert_not_called()

    @patch("lead_routes.db_service")
    def test_zu_schnell_ausgefuellt_wird_verworfen(self, mock_db, client):
        payload = {**VALID_PAYLOAD, "form_ts": _form_ts(vor_sekunden=1)}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204
        mock_db.execute_query.assert_not_called()

    @patch("lead_routes.db_service")
    def test_abgestandenes_formular_wird_verworfen(self, mock_db, client):
        """Älter als 6 Stunden — vermutlich ein wiederverwendetes Formular."""
        payload = {**VALID_PAYLOAD, "form_ts": _form_ts(vor_sekunden=7 * 3600)}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204
        mock_db.execute_query.assert_not_called()

    @patch("lead_routes.db_service")
    def test_turnstile_aktiv_aber_kein_token(self, mock_db, client, monkeypatch):
        """Ist ein Secret gesetzt, wird ohne Token nicht gespeichert."""
        import lead_routes

        monkeypatch.setattr(lead_routes, "TURNSTILE_SECRET", "geheim")
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "turnstile_token"}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204
        mock_db.execute_query.assert_not_called()

    @patch("lead_routes.db_service")
    def test_duplicate_email_returns_already_registered(self, mock_db, client):
        mock_db.execute_query = AsyncMock(return_value={"id": "existing-id", "confirmed_at": None})

        response = client.post("/api/leads/waitlist", json=VALID_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_registered"

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_rate_limit_4th_request_returns_429(self, mock_db, mock_email, client):
        mock_db.execute_query = AsyncMock(side_effect=[None, None] * 10)
        mock_email.send_waitlist_confirmation = MagicMock(return_value=True)

        for _ in range(3):
            r = client.post("/api/leads/waitlist", json=VALID_PAYLOAD)
            assert r.status_code in (200, 204)

        fourth = client.post("/api/leads/waitlist", json=VALID_PAYLOAD)
        assert fourth.status_code == 429

    @patch("lead_routes.db_service")
    def test_invalid_email_returns_422(self, mock_db, client):
        payload = {**VALID_PAYLOAD, "email": "not-an-email"}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 422

    @patch("lead_routes.db_service")
    def test_invalid_phone_returns_422(self, mock_db, client):
        payload = {**VALID_PAYLOAD, "phone": "<script>alert(1)</script>"}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 422


class TestWaitlistConfirm:
    @patch("lead_routes.db_service")
    def test_valid_token_redirects_confirmed_1(self, mock_db, client):
        future = datetime.now(timezone.utc) + timedelta(days=6)
        mock_db.execute_query = AsyncMock(side_effect=[
            {"id": "lead-id-1", "confirm_token_expires_at": future, "confirmed_at": None},
            None,
        ])

        response = client.get(f"/api/leads/waitlist/confirm?token={CONFIRM_TOKEN}", follow_redirects=False)

        assert response.status_code == 302
        assert "confirmed=1" in response.headers.get("location", "")

    @patch("lead_routes.db_service")
    def test_expired_token_redirects_confirmed_0(self, mock_db, client):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        mock_db.execute_query = AsyncMock(return_value={
            "id": "lead-id-2",
            "confirm_token_expires_at": past,
            "confirmed_at": None,
        })

        response = client.get(f"/api/leads/waitlist/confirm?token={CONFIRM_TOKEN}", follow_redirects=False)

        assert response.status_code == 302
        assert "confirmed=0" in response.headers.get("location", "")

    @patch("lead_routes.db_service")
    def test_unknown_token_redirects_confirmed_0(self, mock_db, client):
        mock_db.execute_query = AsyncMock(return_value=None)

        response = client.get("/api/leads/waitlist/confirm?token=unknowntoken", follow_redirects=False)

        assert response.status_code == 302
        assert "confirmed=0" in response.headers.get("location", "")
