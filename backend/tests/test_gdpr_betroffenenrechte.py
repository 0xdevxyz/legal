"""
Wächtertests Betroffenenrechte (DSGVO Art. 15/17/20)
====================================================

Befunde vom 2026-08-11:

1. Export und Löschantrag erfassten nur die leere leads-Tabelle — die echten
   Kundenkonten in `users` waren für Art. 15/17/20 unerreichbar.
2. `db_service.use_fallback` existierte nicht; jeder Aufruf warf einen
   AttributeError, den die except-Blöcke still verschluckten.
3. Die Admin-Endpunkte hingen an einem nie gesetzten ADMIN_API_KEY und
   antworteten dauerhaft 503 — jetzt reguläre require_admin-Dependency.
4. Der E-Mail-Demo-Modus gab in Produktion True zurück ("verschickt"),
   obwohl nichts verschickt wurde.

Diese Tests brauchen keine Datenbank: DB-Zugriffe laufen über einen
Fake-Connection-Stub, die Auth-Fälle über TestClient ohne bzw. mit
überschriebener Dependency.
"""

import asyncio
import os
import re
from datetime import datetime
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _quelltext(dateiname: str) -> str:
    with open(os.path.join(_BACKEND, dateiname), encoding="utf-8") as fh:
        return fh.read()


def _code_ohne_kommentare(quelltext: str) -> str:
    return "\n".join(re.sub(r"#.*$", "", zeile) for zeile in quelltext.splitlines())


# ---------------------------------------------------------------------------
# Befund 2: use_fallback darf nirgends mehr referenziert werden
# ---------------------------------------------------------------------------

class TestKeinUseFallback:
    def test_use_fallback_ist_ueberall_entfernt(self):
        """`db_service.use_fallback` gab es nie — jede Referenz ist ein stiller
        AttributeError im except-Block. Phase-E-Muster: Fallback-Zweige raus."""
        treffer = []
        for name in sorted(os.listdir(_BACKEND)):
            if not name.endswith(".py") or name.endswith(".bak"):
                continue
            pfad = os.path.join(_BACKEND, name)
            if not os.path.isfile(pfad):
                continue
            code = _code_ohne_kommentare(_quelltext(name))
            if "use_fallback" in code:
                treffer.append(name)
        assert not treffer, (
            "use_fallback ist zurück in: " + ", ".join(treffer)
            + " — das Attribut existiert auf DatabaseService nicht"
        )


# ---------------------------------------------------------------------------
# Befund 4: Demo-Modus in Produktion → False + Fehlerlog
# ---------------------------------------------------------------------------

def _smtp_leer(monkeypatch):
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)


class TestDemoModusInProduktion:
    def test_email_service_sendet_nicht(self, monkeypatch):
        _smtp_leer(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        from email_service import EmailService
        service = EmailService()
        assert service.demo_mode is True
        assert service._send_email("kunde@example.com", "Test", "<p>x</p>", "x") is False

    def test_ai_notification_service_sendet_nicht(self, monkeypatch):
        _smtp_leer(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        from ai_compliance_notification_service import AIComplianceNotificationService
        service = AIComplianceNotificationService()
        assert service._send_email("kunde@example.com", "Test", "<p>x</p>", "x") is False

    def test_legal_notification_service_sendet_nicht(self, monkeypatch):
        _smtp_leer(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        from legal_notification_service import LegalNewsNotificationService
        service = LegalNewsNotificationService(db_pool=MagicMock())
        assert asyncio.run(
            service._send_email("kunde@example.com", "Test", "<p>x</p>", "x")
        ) is False

    def test_entwicklung_behaelt_demo_verhalten(self, monkeypatch):
        """Lokal/CI bleibt der Demo-Modus nutzbar (True + Konsolenausgabe)."""
        _smtp_leer(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")
        from email_service import EmailService
        service = EmailService()
        assert service._send_email("dev@example.com", "Test", "<p>x</p>", "x") is True


# ---------------------------------------------------------------------------
# Befund 3: Admin-Endpunkte antworten 401/403, nie wieder 503
# ---------------------------------------------------------------------------

def _gdpr_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from gdpr_api import gdpr_router

    app = FastAPI()
    app.include_router(gdpr_router)
    return app, TestClient(app)


_ADMIN_AUFRUFE = [
    ("post", "/api/gdpr/admin/run-cleanup", None),
    ("get", "/api/gdpr/admin/cleanup-status", None),
    ("post", "/api/gdpr/admin/update-retention", {"lead_id": "x", "retention_days": 30}),
    ("post", "/api/gdpr/admin/confirm-deletion", {"user_id": 1}),
]


class TestAdminAuth:
    @staticmethod
    def _aufruf(client, methode, pfad, body):
        # Ältere TestClient-Versionen (requests-basiert) kennen json= bei GET nicht.
        if body is None:
            return getattr(client, methode)(pfad)
        return getattr(client, methode)(pfad, json=body)

    def test_ohne_token_401_statt_503(self):
        _, client = _gdpr_client()
        for methode, pfad, body in _ADMIN_AUFRUFE:
            antwort = self._aufruf(client, methode, pfad, body)
            assert antwort.status_code == 401, (
                f"{methode.upper()} {pfad}: erwartet 401, bekam {antwort.status_code}"
            )

    def test_kunde_ohne_adminrolle_403(self):
        from dependencies import get_current_user

        app, client = _gdpr_client()

        async def _kunde():
            return {"id": 2, "user_id": 2, "email": "kunde@example.com", "role": "customer"}

        app.dependency_overrides[get_current_user] = _kunde
        for methode, pfad, body in _ADMIN_AUFRUFE:
            antwort = self._aufruf(client, methode, pfad, body)
            assert antwort.status_code == 403, (
                f"{methode.upper()} {pfad}: erwartet 403, bekam {antwort.status_code}"
            )

    def test_kein_admin_api_key_mehr_im_quelltext(self):
        # Der Name darf in Docstrings/Kommentaren als Begründung stehen —
        # verboten ist die FUNKTIONALE Rückkehr des geteilten Schlüssels.
        code = _code_ohne_kommentare(_quelltext("gdpr_api.py"))
        for verboten in ('os.getenv("ADMIN_API_KEY', "_ADMIN_API_KEY",
                         "_verify_admin", 'alias="admin_api_key"'):
            assert verboten not in code, (
                f"{verboten} ist zurück in gdpr_api.py — Admin läuft über require_admin"
            )
        assert "require_admin" in code

    def test_jede_admin_route_verlangt_require_admin(self):
        quelle = _quelltext("gdpr_api.py")
        muster = re.compile(
            r'@gdpr_router\.(get|post|patch|delete|put)\("(/admin/[^"]*)"\)\s*\n'
            r'async def (\w+)\(((?:[^()]|\([^()]*\))*)\)\s*:',
            re.S,
        )
        routen = list(muster.finditer(quelle))
        assert len(routen) >= 4, "Admin-Routen nicht gefunden — Regex prüfen"
        offen = [
            f"{m.group(1).upper()} {m.group(2)}"
            for m in routen
            if "require_admin" not in m.group(4)
        ]
        assert not offen, "Admin-Route(n) ohne require_admin: " + ", ".join(offen)


# ---------------------------------------------------------------------------
# Befund 1: Export erfasst users + zugehörige Tabellen, Löschung ist zweistufig
# ---------------------------------------------------------------------------

class _FakeTransaktion:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class _FakeConn:
    """Minimaler asyncpg-Ersatz: protokolliert Queries, liefert Drehbuch-Zeilen."""

    def __init__(self, fetchrow_drehbuch=None, fetch_drehbuch=None):
        self.queries = []
        self._fetchrow = fetchrow_drehbuch or []
        self._fetch = fetch_drehbuch or []

    async def fetchrow(self, query, *args):
        self.queries.append(query)
        for muster, zeile in self._fetchrow:
            if muster in query:
                return zeile
        return None

    async def fetch(self, query, *args):
        self.queries.append(query)
        for muster, zeilen in self._fetch:
            if muster in query:
                return zeilen
        return []

    async def execute(self, query, *args):
        self.queries.append(query)
        return "UPDATE 1"

    def transaction(self):
        return _FakeTransaktion()


def _mit_fake_conn(monkeypatch, conn):
    import gdpr_retention_service as grs

    @asynccontextmanager
    async def _verbindung():
        yield conn

    monkeypatch.setattr(grs.db_service, "get_connection", _verbindung)
    return grs


class TestExportUmfasstUsers:
    def test_export_liefert_kontodaten_und_kategorien(self, monkeypatch):
        konto = {
            "id": 1, "email": "kunde@example.com", "full_name": "Klara Kunde",
            "company": "Kunde GmbH", "is_active": True, "is_verified": True,
            "onboarding_completed": True, "plan_type": "pro", "role": "customer",
            "created_at": datetime(2026, 1, 5, 9, 0, 0), "updated_at": None,
        }
        conn = _FakeConn(
            fetchrow_drehbuch=[("FROM users", konto)],
            fetch_drehbuch=[(
                "FROM user_company_data",
                [{"company_name": "Kunde GmbH", "tax_id": "DE123",
                  "company_address": "Weg 1", "created_at": None, "updated_at": None}],
            )],
        )
        grs = _mit_fake_conn(monkeypatch, conn)

        async def _kein_lead(email):
            return None

        monkeypatch.setattr(grs.db_service, "get_lead_by_email", _kein_lead)

        export = asyncio.run(grs.gdpr_service.export_user_data(1, "kunde@example.com"))

        assert export is not None, "Export darf für ein existierendes Konto nicht leer sein"
        assert export["konto"]["email"] == "kunde@example.com"
        assert export["konto"]["full_name"] == "Klara Kunde"
        # datetime muss JSON-tauglich geworden sein (JSONResponse + Mailversand)
        assert export["konto"]["created_at"] == "2026-01-05T09:00:00"
        assert export["rechnungsdaten"][0]["tax_id"] == "DE123"
        # Die zugehörigen Tabellen müssen als Kategorien auftauchen
        for kategorie in ("tarif_und_limits", "scans", "generierte_dokumente",
                          "websites", "loeschantraege"):
            assert kategorie in export, f"Export-Kategorie {kategorie} fehlt"
        # Kein Passwort-Hash im Export
        assert "password_hash" not in export["konto"]

    def test_export_fragt_users_ab(self, monkeypatch):
        conn = _FakeConn(fetchrow_drehbuch=[("FROM users", {"id": 1, "email": "k@e.de"})])
        grs = _mit_fake_conn(monkeypatch, conn)

        async def _kein_lead(email):
            return None

        monkeypatch.setattr(grs.db_service, "get_lead_by_email", _kein_lead)
        asyncio.run(grs.gdpr_service.export_user_data(1, "k@e.de"))
        assert any("FROM users" in q for q in conn.queries), (
            "Export fragt die users-Tabelle nicht ab — Rückfall auf leads-only?"
        )

    def test_export_unbekanntes_konto_none(self, monkeypatch):
        conn = _FakeConn()
        grs = _mit_fake_conn(monkeypatch, conn)
        export = asyncio.run(grs.gdpr_service.export_user_data(999, "gibtsnicht@example.com"))
        assert export is None


class TestLoeschungZweistufig:
    def test_antrag_loescht_nicht_sofort(self, monkeypatch):
        """Stufe 1 registriert NUR den Antrag — kein DELETE auf users & Co."""
        conn = _FakeConn(fetchrow_drehbuch=[
            ("INSERT INTO gdpr_deletion_requests",
             {"id": 7, "requested_at": datetime(2026, 8, 11, 12, 0, 0)}),
        ])
        grs = _mit_fake_conn(monkeypatch, conn)

        async def _kein_lead(email):
            return None

        monkeypatch.setattr(grs.db_service, "get_lead_by_email", _kein_lead)
        monkeypatch.setattr(
            grs.gdpr_service, "_send_user_deletion_received", lambda *a, **kw: True
        )

        ergebnis = asyncio.run(
            grs.gdpr_service.request_user_deletion(1, "kunde@example.com", "user_request")
        )

        assert ergebnis["success"] is True
        assert ergebnis["reference_id"] == 7
        assert any("INSERT INTO gdpr_deletion_requests" in q for q in conn.queries), (
            "Löschantrag wird nicht in gdpr_deletion_requests registriert"
        )
        geloescht = [q for q in conn.queries if q.strip().upper().startswith("DELETE")]
        assert not geloescht, (
            "Stufe 1 darf nichts löschen, führte aber aus: " + "; ".join(geloescht)
        )

    def test_api_request_deletion_nutzt_zweistufigen_weg(self):
        """Der Endpunkt darf nicht mehr auf die Sofort-Hard-Delete-Kette zeigen."""
        quelle = _quelltext("gdpr_api.py")
        anfang = quelle.find('@gdpr_router.post("/request-deletion")')
        ende = quelle.find("@gdpr_router", anfang + 1)
        endpunkt = quelle[anfang:ende]
        assert "request_user_deletion" in endpunkt, (
            "POST /request-deletion registriert keinen zweistufigen Kontolöschantrag mehr"
        )
        assert "delete_lead_permanently" not in endpunkt

    def test_loesch_statements_decken_users_ab(self):
        """Der Bestätigungslauf muss users UND die FK-losen Tabellen räumen."""
        import gdpr_retention_service as grs
        statements = " ".join(grs.GDPRRetentionService._LOESCH_STATEMENTS)
        for tabelle in ("users", "user_company_data", "scan_history",
                        "generated_documents", "user_limits", "stripe_customers"):
            assert tabelle in statements, (
                f"Löschlauf lässt Tabelle {tabelle} stehen"
            )


# ---------------------------------------------------------------------------
# Befund 5/7: keine localhost-Links / toter Tarif in Mails, Dashboard-Endpunkte
# ---------------------------------------------------------------------------

class TestOberflaechenUndMails:
    def test_email_service_ohne_localhost_und_ohne_39_euro(self):
        code = _code_ohne_kommentare(_quelltext("email_service.py"))
        assert "localhost:3000" not in code, (
            "localhost:3000 ist zurück in email_service.py — FRONTEND_URL nutzen"
        )
        assert "39€" not in code and "39 €" not in code, (
            "Der tote Tarif '39€/Monat KI-Automatisierung' ist zurück im Mailtext"
        )

    def test_dashboard_passwort_endpunkt(self):
        pfad = os.path.join(
            _BACKEND, "..", "dashboard-react", "src", "app", "settings", "page.tsx"
        )
        if not os.path.isfile(pfad):
            pytest.skip("dashboard-react nicht im Testcontainer gemountet")
        with open(pfad, encoding="utf-8") as fh:
            quelle = fh.read()
        assert "/api/user/change-password" not in quelle, (
            "Dashboard ruft wieder den nie existenten POST /api/user/change-password auf"
        )
        assert "/api/user/password" in quelle
        assert "/api/user/export-data" in quelle

    def test_landing_gdpr_seite_ohne_totes_formular(self):
        pfad = os.path.join(
            _BACKEND, "..", "landing-react", "src", "app", "gdpr", "page.tsx"
        )
        if not os.path.isfile(pfad):
            pytest.skip("landing-react nicht im Testcontainer gemountet")
        with open(pfad, encoding="utf-8") as fh:
            quelle = fh.read()
        assert "fetch(" not in quelle, (
            "Die Landing-GDPR-Seite postet wieder auf eine (nicht existente) Route"
        )
        assert "datenschutz@complyo.de" in quelle
        assert "app.complyo.de" in quelle

    def test_user_routes_hat_export_endpunkt(self):
        code = _quelltext("user_routes.py")
        assert '"/export-data"' in code, (
            "GET /api/user/export-data fehlt — der Dashboard-Export-Button läuft ins Leere"
        )
