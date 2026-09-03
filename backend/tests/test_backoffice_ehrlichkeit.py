"""
Backoffice-Ehrlichkeit
======================

Drei stille Stellen aus dem Backoffice-Audit 2026-08:

1. license_check: Eine site_id, die in keiner Config-Tabelle vorkommt, lief
   fail-open OHNE Log — damit fehlte jede Datengrundlage fuer die
   Entscheidung, COMPLYO_LICENSE_ENFORCEMENT auf 'block' zu stellen.
   Jetzt: WARN-Log '[Lizenz] unbekannte site_id ...', weiterhin fail-open.

2. /api/admin/leads lieferte hartkodiert `leads = []` und sah dabei fertig
   aus. Jetzt echte Query ueber den Pool (hier gemockt).

3. /api/admin/system/health und /dashboard/overview behaupteten
   'uptime 99.9%', email_service 'active' u. a. — erfundene Werte sind
   gestrichen, der email_service-Status kommt aus dem echten demo_mode.

Die Tests mocken den Pool per dependency_overrides — die Queries selbst
laufen erst nach dem Deploy gegen die echte DB.
"""
import logging
import os
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import admin_routes
from dependencies import get_db, require_admin
from license_check import evaluate_license

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# 1) Lizenzpruefung: unbekannte site_id muss WARNen, aber fail-open bleiben
# ---------------------------------------------------------------------------

class PoolOhneConfig:
    """fetchrow -> None: die site_id existiert in keiner Config-Tabelle."""

    async def fetchrow(self, *args, **kwargs):
        return None

    async def fetch(self, *args, **kwargs):
        return []


@pytest.mark.asyncio
async def test_unbekannte_site_id_warnt_und_bleibt_fail_open(caplog):
    with caplog.at_level(logging.WARNING, logger="license_check"):
        result = await evaluate_license(PoolOhneConfig(), "voellig-unbekannt-de")

    # Weiterhin fail-open — kein Block, das Widget arbeitet normal weiter.
    assert result["status"] == "active"
    assert result["active"] is True
    assert result["enforced"] is False

    # Aber nicht mehr still: der Log liefert die Entscheidungsgrundlage
    # fuer enforcement=block.
    meldungen = [r.getMessage() for r in caplog.records]
    assert any(
        "[Lizenz] unbekannte site_id" in m and "voellig-unbekannt-de" in m
        for m in meldungen
    ), f"WARN-Log fuer unbekannte site_id fehlt. Logs: {meldungen}"


# ---------------------------------------------------------------------------
# Testaufbau fuer die Admin-Endpunkte: Pool gemockt, Admin-Auth ueberbrueckt
# ---------------------------------------------------------------------------

def _client(pool):
    app = FastAPI()
    app.include_router(admin_routes.admin_router)
    app.dependency_overrides[require_admin] = lambda: {
        "id": 1, "email": "admin@test.de", "role": "admin",
    }
    app.dependency_overrides[get_db] = lambda: pool
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 2) /api/admin/leads: gemockte DB-Zeilen kommen an, kein Hardcode mehr
# ---------------------------------------------------------------------------

def test_admin_leads_liefert_db_zeilen_statt_hardcode():
    zeilen = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "email": "kunde@beispiel.de",
            "name": "Kunde Eins",
            "company": "Beispiel GmbH",
            "source": "landing_page",
            "status": "new",
            "email_verified": False,
            "created_at": datetime(2026, 8, 10, 12, 0, 0),
            "verified_at": None,
            "url_analyzed": "https://beispiel.de",
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "email": "zwei@beispiel.de",
            "name": "Kunde Zwei",
            "company": None,
            "source": "landing_page",
            "status": "converted",
            "email_verified": True,
            "created_at": datetime(2026, 8, 9, 9, 30, 0),
            "verified_at": datetime(2026, 8, 9, 10, 0, 0),
            "url_analyzed": "https://zwei.de",
        },
    ]
    pool = MagicMock()
    pool.fetchval = AsyncMock(return_value=2)
    pool.fetch = AsyncMock(return_value=zeilen)

    resp = _client(pool).get("/api/admin/leads")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Die gemockten Zeilen muessen ankommen — vor dem Fix kam immer [].
    assert [l["email"] for l in body["leads"]] == [
        "kunde@beispiel.de", "zwei@beispiel.de",
    ]
    assert body["pagination"]["total_count"] == 2
    assert pool.fetch.await_count == 1, "Der Endpunkt muss die DB fragen"

    # Sensible Felder gehoeren nicht in die Listenansicht.
    for lead in body["leads"]:
        assert "verification_token" not in lead
        assert "consent_ip_address" not in lead


def test_admin_leads_filter_landen_in_der_query():
    pool = MagicMock()
    pool.fetchval = AsyncMock(return_value=0)
    pool.fetch = AsyncMock(return_value=[])

    resp = _client(pool).get("/api/admin/leads?status=new&verified=false")
    assert resp.status_code == 200, resp.text

    query = pool.fetch.await_args.args[0]
    assert "status = $1" in query
    assert "email_verified = $2" in query
    # Parametrisiert, nicht interpoliert:
    assert "new" not in query


# ---------------------------------------------------------------------------
# 3) /system/health und /dashboard/overview: keine erfundenen Werte mehr
# ---------------------------------------------------------------------------

def test_system_health_ohne_fantasiewerte():
    pool = MagicMock()
    pool.fetchval = AsyncMock(return_value=1)

    resp = _client(pool).get("/api/admin/system/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert "99.9" not in resp.text, "hartkodierte uptime ist zurueck"
    assert "uptime" not in resp.text
    assert "performance" not in body

    # DB-Status kommt aus einem echten SELECT 1 (hier gemockt beantwortet).
    assert body["database"]["status"] == "connected"
    assert pool.fetchval.await_count >= 1

    # email_service-Status spiegelt den echten demo_mode des Singletons.
    from email_service import email_service
    erwartet = "demo" if email_service.demo_mode else "active"
    assert body["email_service"]["status"] == erwartet


def test_system_health_meldet_db_fehler_statt_connected():
    pool = MagicMock()
    pool.fetchval = AsyncMock(side_effect=RuntimeError("DB weg"))

    resp = _client(pool).get("/api/admin/system/health")
    assert resp.status_code == 200, resp.text
    assert resp.json()["database"]["status"] == "error"


def test_keine_hartkodierten_kennzahlen_im_quelltext():
    """Statischer Waechter: die alten Fantasiewerte duerfen nicht zurueckkehren."""
    with open(os.path.join(_BACKEND, "admin_routes.py"), encoding="utf-8") as fh:
        src = fh.read()
    for verboten in ('"99.9%"', '"uptime"', '"< 200ms"', '"< 5 minutes"',
                     '"< 30 seconds"', '"email_service": "active"'):
        assert verboten not in src, (
            f"{verboten} steht wieder hartkodiert in admin_routes.py"
        )


def test_analytics_trends_aggregiert_scan_history():
    pool = MagicMock()
    pool.fetchval = AsyncMock(return_value=0)
    pool.fetch = AsyncMock(return_value=[
        {"tag": date(2026, 8, 9), "scans": 3},
        {"tag": date(2026, 8, 10), "scans": 5},
    ])

    resp = _client(pool).get("/api/admin/analytics/trends?days=30")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["trends"] == [
        {"date": "2026-08-09", "scans": 3},
        {"date": "2026-08-10", "scans": 5},
    ]
    assert body["summary"]["total_scans"] == 8
    assert body["summary"]["peak_day"] == "2026-08-10"
    assert "scan_history" in pool.fetch.await_args.args[0]
