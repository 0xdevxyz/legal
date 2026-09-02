"""
Tests für die Early-Access Waitlist-Endpoints
Deckt ab: Happy-Path, Honeypot, Zeitfalle, Turnstile, Consent-False, Duplicate,
Token-Confirm, Rate-Limit
"""

import os
import pytest
from contextlib import asynccontextmanager
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


def verbindung(mock_db, fetchrow=None, fetchval=None):
    """Baut den db_service-Mock so, wie DatabaseService wirklich aussieht.

    Vorher stand hier `mock_db.execute_query = AsyncMock(...)`. Diese Methode
    hat es auf DatabaseService nie gegeben — MagicMock erfindet jedes Attribut,
    auf das man zugreift, und so liefen alle Tests gruen, waehrend jede echte
    Anmeldung in einen AttributeError und damit in einen 500er lief. Der Mock
    hat den Fehler nicht uebersehen, er hat ihn erzeugt.

    Deshalb bildet dieser Helfer das tatsaechliche Muster nach:
    `async with db_service.get_connection() as conn` und darauf asyncpg mit
    fetchrow / fetchval / execute. TestDbServiceVertrag unten haelt fest, dass
    es diese Methoden wirklich gibt.
    """
    conn = MagicMock()
    conn.fetchrow = AsyncMock(side_effect=list(fetchrow) if fetchrow is not None else [None])
    conn.fetchval = AsyncMock(side_effect=list(fetchval) if fetchval is not None else [1])
    conn.execute = AsyncMock(return_value=None)

    @asynccontextmanager
    async def _hole_verbindung():
        yield conn

    mock_db.get_connection = _hole_verbindung
    return conn


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
        conn = verbindung(mock_db, fetchrow=[None])
        mock_email.send_waitlist_confirmation = MagicMock(return_value=True)

        response = client.post("/api/leads/waitlist", json=VALID_PAYLOAD)

        assert response.status_code == 200
        conn.execute.assert_awaited_once()
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
        mock_db.get_connection.assert_not_called()

    @patch("lead_routes.db_service")
    def test_zu_schnell_ausgefuellt_wird_verworfen(self, mock_db, client):
        payload = {**VALID_PAYLOAD, "form_ts": _form_ts(vor_sekunden=1)}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204
        mock_db.get_connection.assert_not_called()

    @patch("lead_routes.db_service")
    def test_abgestandenes_formular_wird_verworfen(self, mock_db, client):
        """Älter als 6 Stunden — vermutlich ein wiederverwendetes Formular."""
        payload = {**VALID_PAYLOAD, "form_ts": _form_ts(vor_sekunden=7 * 3600)}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204
        mock_db.get_connection.assert_not_called()

    @patch("lead_routes.db_service")
    def test_turnstile_aktiv_aber_kein_token(self, mock_db, client, monkeypatch):
        """Ist ein Secret gesetzt, wird ohne Token nicht gespeichert."""
        import lead_routes

        monkeypatch.setattr(lead_routes, "TURNSTILE_SECRET", "geheim")
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "turnstile_token"}
        response = client.post("/api/leads/waitlist", json=payload)
        assert response.status_code == 204
        mock_db.get_connection.assert_not_called()

    @patch("lead_routes.db_service")
    def test_duplicate_email_returns_already_registered(self, mock_db, client):
        verbindung(mock_db, fetchrow=[{"id": "existing-id", "confirmed_at": None}])

        response = client.post("/api/leads/waitlist", json=VALID_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_registered"

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_rate_limit_4th_request_returns_429(self, mock_db, mock_email, client):
        verbindung(mock_db, fetchrow=[None] * 10)
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
        verbindung(mock_db, fetchrow=[{
            "id": "lead-id-1", "confirm_token_expires_at": future,
            "confirmed_at": None, "angebot": None, "landing_path": None,
            "platz_nr": None,
        }])

        response = client.get(f"/api/leads/waitlist/confirm?token={CONFIRM_TOKEN}", follow_redirects=False)

        assert response.status_code == 302
        assert "confirmed=1" in response.headers.get("location", "")

    @patch("lead_routes.db_service")
    def test_expired_token_redirects_confirmed_0(self, mock_db, client):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        verbindung(mock_db, fetchrow=[{
            "id": "lead-id-2",
            "confirm_token_expires_at": past,
            "confirmed_at": None,
            "angebot": None,
            "landing_path": None,
            "platz_nr": None,
        }])

        response = client.get(f"/api/leads/waitlist/confirm?token={CONFIRM_TOKEN}", follow_redirects=False)

        assert response.status_code == 302
        assert "confirmed=0" in response.headers.get("location", "")

    @patch("lead_routes.db_service")
    def test_unknown_token_redirects_confirmed_0(self, mock_db, client):
        verbindung(mock_db, fetchrow=[None])

        response = client.get("/api/leads/waitlist/confirm?token=unknowntoken", follow_redirects=False)

        assert response.status_code == 302
        assert "confirmed=0" in response.headers.get("location", "")


class TestDbServiceVertrag:
    """Haelt fest, dass lead_routes nur Methoden aufruft, die es wirklich gibt.

    Anlass: die Waitlist rief `db_service.execute_query(...)` auf. DatabaseService
    hat diese Methode nicht, und weil MagicMock jedes Attribut erfindet, ist es
    keinem Test aufgefallen — die Anmeldestrecke war tot, die Suite gruen. Dieser
    Test vergleicht deshalb gegen die echte Klasse statt gegen einen Mock.
    """

    def test_aufgerufene_db_methoden_existieren(self):
        import re as _re
        import inspect
        from database_service import DatabaseService

        with open(
            os.path.join(os.path.dirname(__file__), "..", "lead_routes.py"),
            encoding="utf-8",
        ) as fh:
            quelltext = fh.read()

        aufgerufen = set(_re.findall(r"db_service\.([a-zA-Z_][a-zA-Z0-9_]*)", quelltext))
        vorhanden = {n for n, _ in inspect.getmembers(DatabaseService)}
        fehlend = aufgerufen - vorhanden

        assert not fehlend, (
            "lead_routes ruft auf DatabaseService nicht vorhandene Methode(n) auf: "
            + ", ".join(sorted(fehlend))
            + ". Im Betrieb ist das ein AttributeError und damit ein 500er pro Anmeldung."
        )


class TestHerkunft:
    """Die Kampagnenfelder muessen ankommen — sonst ist bezahlter Traffic blind."""

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_kampagne_und_utm_werden_gespeichert(self, mock_db, mock_email, client):
        conn = verbindung(mock_db, fetchrow=[None])
        mock_email.send_waitlist_confirmation = MagicMock(return_value=True)

        payload = {
            **VALID_PAYLOAD,
            "campaign": "ea100-bfsg",
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "bfsg-test",
            "landing_path": "/early-access",
        }
        response = client.post("/api/leads/waitlist", json=payload)

        assert response.status_code == 200
        args = conn.execute.await_args.args
        assert "ea100-bfsg" in args, "campaign kommt nicht in der Datenbank an"
        assert "google" in args, "utm_source kommt nicht in der Datenbank an"
        assert "/early-access" in args, "landing_path kommt nicht in der Datenbank an"
        # angebot ist eine Servereigenschaft und darf nicht aus dem Request stammen.
        assert lead_routes_angebot() in args, "zugesagtes Angebot wird nicht belegt"

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_ohne_kampagne_kein_angebot(self, mock_db, mock_email, client):
        """Wer ueber die normale Seite kommt, bekommt keinen Early-Access-Platz."""
        conn = verbindung(mock_db, fetchrow=[None])
        mock_email.send_waitlist_confirmation = MagicMock(return_value=True)

        response = client.post("/api/leads/waitlist", json=VALID_PAYLOAD)

        assert response.status_code == 200
        args = conn.execute.await_args.args
        assert lead_routes_angebot() not in args

    @patch("lead_routes.db_service")
    def test_fremde_domain_im_landing_path_wird_verworfen(self, mock_db, client):
        """Der Pfad steuert ein Redirect nach dem Opt-In — offene Weiterleitung waere die Folge."""
        import lead_routes

        for boese in ("//fremde.domain", "https://fremde.domain", "/pfad?weiter=x"):
            geprueft = lead_routes.WaitlistJoinRequest(
                email="a@b.de", consent=True, landing_path=boese,
            ).landing_path
            assert geprueft is None, f"{boese} haette gespeichert werden duerfen"

        assert lead_routes.WaitlistJoinRequest(
            email="a@b.de", consent=True, landing_path="/early-access",
        ).landing_path == "/early-access"


def lead_routes_angebot():
    import lead_routes
    return lead_routes.EARLY_ACCESS_ANGEBOT


class TestEchteBesucherIp:
    """Das Rate-Limit muss pro Besucher greifen, nicht pro Gateway.

    Hinter nginx ist `request.client.host` immer die Proxy-IP. Wer damit einen
    Eimer fuellt, sperrt nach drei Anmeldungen in zehn Minuten JEDEN weiteren
    Besucher aus. Auf einer beworbenen Seite bedeutet das: die Anzeigen laufen
    weiter, das Formular antwortet allen mit 429. Genau so lag am 12.08.2026
    schon der Landing-Scanner still.
    """

    def test_waitlist_nutzt_get_client_ip(self):
        with open(
            os.path.join(os.path.dirname(__file__), "..", "lead_routes.py"),
            encoding="utf-8",
        ) as fh:
            quelltext = fh.read()

        beginn = quelltext.index("async def join_waitlist")
        ende = quelltext.index("async def waitlist_plaetze")
        rumpf = quelltext[beginn:ende]

        assert "get_client_ip(" in rumpf, (
            "join_waitlist ermittelt die IP nicht ueber get_client_ip — "
            "TRUSTED_PROXIES wird damit ignoriert"
        )
        assert "http_request.client.host" not in rumpf, (
            "join_waitlist liest wieder direkt request.client.host; hinter nginx "
            "teilen sich damit alle Besucher ein Rate-Limit"
        )


LEAD_PAYLOAD = {
    "name": "Erika Musterfrau",
    "email": "erika@example.de",
    "company": "Musterfirma GmbH",
    "url": "https://example.de",
    "analysis_data": {"score": 42},
    "session_id": "sess-1",
    "language": "de",
}


class TestEinwilligungsIpImAuditTrail:
    """Der Einwilligungsnachweis braucht die IP des Besuchers, nicht die des Gateways.

    collect_lead und die Verify-Route schrieben `request.client.host` in den
    DSGVO-Audit-Trail (consent_ip_address bzw. verify_email). Hinter nginx ist
    das immer 172.22.0.x. Ein Nachweis, in dem bei jedem einzelnen Lead dieselbe
    interne Proxy-IP steht, belegt gegenueber der Aufsicht nichts: er zeigt nur,
    dass die Anfrage durch den eigenen Proxy lief.

    Die Gegenprobe gehoert dazu. X-Forwarded-For blind zu uebernehmen waere
    genauso wertlos, weil der Client den Header selbst setzt. get_client_ip
    glaubt ihm nur, wenn die Anfrage von einem Proxy aus TRUSTED_PROXIES kommt.
    Der TestClient meldet sich als "testclient", das ist hier die Proxy-IP.

    Die Header sind so geformt, wie nginx sie tatsaechlich liefert:
    `proxy_add_x_forwarded_for` HAENGT die gesehene Adresse an, statt zu
    ersetzen. Ein Besucher, der selbst `X-Forwarded-For: 9.9.9.9` schickt,
    erzeugt damit `9.9.9.9, <echte IP>`. Die echte Adresse steht rechts.
    """

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_collect_speichert_die_besucher_ip(self, mock_db, mock_email, client):
        mock_db.get_lead_by_email = AsyncMock(return_value=None)
        mock_db.create_lead = AsyncMock(return_value=("lead-1", "token-1"))

        with patch.dict(os.environ, {"TRUSTED_PROXIES": "testclient"}):
            response = client.post(
                "/api/leads/collect",
                json=LEAD_PAYLOAD,
                headers={"X-Forwarded-For": "203.0.113.7"},
            )

        assert response.status_code == 200, response.text
        gespeichert = mock_db.create_lead.await_args.args[0]
        assert gespeichert["consent_ip_address"] == "203.0.113.7", (
            "collect_lead schreibt die Gateway-IP statt der Besucher-IP in den "
            "Einwilligungsnachweis"
        )

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_selbst_gesetzter_header_wird_verworfen(self, mock_db, mock_email, client):
        """Der Besucher haengt links etwas an, nginx setzt rechts die Wahrheit."""
        mock_db.get_lead_by_email = AsyncMock(return_value=None)
        mock_db.create_lead = AsyncMock(return_value=("lead-1", "token-1"))

        with patch.dict(os.environ, {"TRUSTED_PROXIES": "testclient"}):
            response = client.post(
                "/api/leads/collect",
                json=LEAD_PAYLOAD,
                headers={"X-Forwarded-For": "9.9.9.9, 203.0.113.7"},
            )

        assert response.status_code == 200, response.text
        gespeichert = mock_db.create_lead.await_args.args[0]
        assert gespeichert["consent_ip_address"] == "203.0.113.7", (
            "der vom Besucher selbst gesetzte Teil der Kette landet im "
            "Einwilligungsnachweis"
        )

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_collect_glaubt_unbekanntem_proxy_nicht(self, mock_db, mock_email, client):
        """Gegenprobe: ohne hinterlegten Proxy zaehlt nur die direkte Adresse."""
        mock_db.get_lead_by_email = AsyncMock(return_value=None)
        mock_db.create_lead = AsyncMock(return_value=("lead-1", "token-1"))

        with patch.dict(os.environ, {"TRUSTED_PROXIES": "10.9.9.9"}):
            response = client.post(
                "/api/leads/collect",
                json=LEAD_PAYLOAD,
                headers={"X-Forwarded-For": "1.2.3.4"},
            )

        assert response.status_code == 200, response.text
        gespeichert = mock_db.create_lead.await_args.args[0]
        assert gespeichert["consent_ip_address"] != "1.2.3.4", (
            "collect_lead uebernimmt X-Forwarded-For ungeprueft; damit kann sich "
            "jeder eine beliebige IP in den Einwilligungsnachweis schreiben"
        )

    @patch("lead_routes.email_service")
    @patch("lead_routes.db_service")
    def test_verify_speichert_die_besucher_ip(self, mock_db, mock_email, client):
        mock_db.get_lead_by_verification_token = AsyncMock(
            return_value={
                "id": "lead-1",
                "email": "erika@example.de",
                "name": "Erika Musterfrau",
                "email_verified": False,
                "analysis_data": {},
            }
        )
        mock_db.verify_email = AsyncMock(return_value=True)

        with patch.dict(os.environ, {"TRUSTED_PROXIES": "testclient"}):
            response = client.get(
                "/api/leads/verify/token-1",
                headers={"X-Forwarded-For": "9.9.9.9, 203.0.113.7"},
            )

        assert response.status_code == 200, response.text
        assert mock_db.verify_email.await_args.args[1] == "203.0.113.7", (
            "die Verify-Route schreibt die Gateway-IP in den Bestaetigungsnachweis"
        )


class TestCookieConsentIpNichtFaelschbar:
    """Das Einwilligungsprotokoll des Cookie-Banners hing an einem blanken Header.

    cookie_compliance_routes hatte eine eigene get_client_ip, die
    X-Forwarded-For ohne jede Pruefung uebernahm. Der Header kommt vom Client.
    Ein Protokoll, in das sich jeder eine beliebige IP schreiben kann, ist als
    Nachweis wertlos, und die Zeile in geo-check lief ausserdem in einen
    AttributeError, sobald request.client fehlte.
    """

    def test_modul_nutzt_die_gepruefte_variante(self):
        with open(
            os.path.join(os.path.dirname(__file__), "..", "cookie_compliance_routes.py"),
            encoding="utf-8",
        ) as fh:
            quelltext = fh.read()

        assert "_client_ip_geprueft" in quelltext, (
            "cookie_compliance_routes ermittelt die IP nicht ueber "
            "dependencies.get_client_ip; TRUSTED_PROXIES wird ignoriert"
        )
        for schreibweise in ("request.headers.get('X-Forwarded-For'",
                             'request.headers.get("X-Forwarded-For"'):
            assert schreibweise not in quelltext, (
                "in cookie_compliance_routes steht wieder ein ungeprueftes "
                "X-Forwarded-For; der Header ist frei faelschbar"
            )
