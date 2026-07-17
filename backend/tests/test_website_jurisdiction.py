"""
Regressionstests für den Jurisdiction-Override in website_routes.save_website().

Bugs:
1) Der INSERT-Zweig schrieb 'jurisdiction' nicht — ein beim Anlegen
   mitgesendeter Override wurde validiert und dann weggeworfen.
2) Der UPDATE nutzte COALESCE($4, jurisdiction) — damit war das Zurücksetzen
   des Overrides (explizit null) unmöglich.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

import website_routes
from website_routes import WebsiteCreate, save_website


class FakeConn:
    """Protokolliert fetchrow/fetchval/execute-Aufrufe."""

    def __init__(self, existing=None, inserted_jurisdiction=None):
        self.existing = existing
        self.calls = []
        self.inserted_jurisdiction = inserted_jurisdiction

    async def fetchrow(self, query, *args):
        self.calls.append((query, args))
        q = " ".join(query.split())
        if q.startswith("SELECT id, scan_count, is_primary"):
            return self.existing
        if "SELECT websites_max" in q:
            return {"websites_max": 10, "websites_count": 1}
        if q.startswith("INSERT INTO tracked_websites"):
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "url": args[1],
                "last_score": args[2],
                "last_scan_date": args[3],
                "scan_count": 1,
                "is_primary": args[4],
                "jurisdiction": args[5],
            }
        if q.startswith("UPDATE tracked_websites"):
            # CASE WHEN $5 THEN $4 ELSE jurisdiction END nachbilden
            new_j = args[3] if args[4] else "de"  # "de" = bestehender Wert
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "url": "https://example.com",
                "last_score": args[0],
                "last_scan_date": args[1],
                "scan_count": 2,
                "is_primary": True,
                "jurisdiction": new_j,
            }
        return None

    async def fetchval(self, query, *args):
        self.calls.append((query, args))
        q = " ".join(query.split())
        if "COUNT(*)" in q:
            return 1
        if "SELECT jurisdiction FROM user_limits" in q:
            return "de"
        return None

    async def execute(self, query, *args):
        self.calls.append((query, args))
        return None


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        conn = self._conn

        class _Ctx:
            async def __aenter__(self):
                return conn

            async def __aexit__(self, *a):
                return False

        return _Ctx()


@pytest.fixture
def user():
    return {"id": 1, "user_id": 1}


def _find_call(conn, prefix):
    for query, args in conn.calls:
        if " ".join(query.split()).startswith(prefix):
            return args
    return None


# ============================================================================
# INSERT-Zweig
# ============================================================================

@pytest.mark.asyncio
async def test_insert_persists_jurisdiction_override(monkeypatch, user):
    """Anlegen mit Override -> Override landet im INSERT."""
    conn = FakeConn(existing=None)
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    result = await save_website(
        WebsiteCreate(url="https://example.com", score=80, jurisdiction="eu"),
        user=user,
    )

    args = _find_call(conn, "INSERT INTO tracked_websites")
    assert args is not None, "Kein INSERT abgesetzt"
    assert args[5] == "eu", f"jurisdiction wurde nicht in den INSERT übernommen: {args}"
    assert result["website"]["jurisdiction"] == "eu"
    assert result["website"]["effective_jurisdiction"] == "eu"


@pytest.mark.asyncio
async def test_insert_without_jurisdiction_stores_null(monkeypatch, user):
    """Ohne Override -> NULL (Account-Default erben)."""
    conn = FakeConn(existing=None)
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    result = await save_website(
        WebsiteCreate(url="https://example.com", score=80), user=user
    )

    args = _find_call(conn, "INSERT INTO tracked_websites")
    assert args[5] is None
    assert result["website"]["jurisdiction"] is None
    # Account-Default ("de") schlägt durch
    assert result["website"]["effective_jurisdiction"] == "de"


@pytest.mark.asyncio
async def test_insert_rejects_unknown_jurisdiction(monkeypatch, user):
    from fastapi import HTTPException

    conn = FakeConn(existing=None)
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    with pytest.raises(HTTPException) as exc:
        await save_website(
            WebsiteCreate(url="https://example.com", score=80, jurisdiction="us"),
            user=user,
        )
    assert exc.value.status_code == 400


# ============================================================================
# UPDATE-Zweig
# ============================================================================

EXISTING = {"id": "11111111-1111-1111-1111-111111111111", "scan_count": 1, "is_primary": True}


@pytest.mark.asyncio
async def test_update_sets_override(monkeypatch, user):
    conn = FakeConn(existing=EXISTING)
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    await save_website(
        WebsiteCreate(url="https://example.com", score=90, jurisdiction="eu"), user=user
    )

    args = _find_call(conn, "UPDATE tracked_websites")
    assert args[3] == "eu"
    assert args[4] is True, "jurisdiction_sent muss True sein"


@pytest.mark.asyncio
async def test_update_with_explicit_null_clears_override(monkeypatch, user):
    """
    Explizites null MUSS den Override löschen.
    Vor dem Fix verhinderte COALESCE($4, jurisdiction) genau das.
    """
    conn = FakeConn(existing=EXISTING)
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    payload = WebsiteCreate(**{"url": "https://example.com", "score": 90, "jurisdiction": None})
    result = await save_website(payload, user=user)

    args = _find_call(conn, "UPDATE tracked_websites")
    assert args[3] is None
    assert args[4] is True, "explizit gesendetes null muss als 'gesendet' gelten"
    assert result["website"]["jurisdiction"] is None, "Override wurde nicht gelöscht"


@pytest.mark.asyncio
async def test_update_without_jurisdiction_leaves_value_untouched(monkeypatch, user):
    """'Feld nicht mitgesendet' darf den Override NICHT löschen."""
    conn = FakeConn(existing=EXISTING)
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    payload = WebsiteCreate(url="https://example.com", score=90)
    result = await save_website(payload, user=user)

    args = _find_call(conn, "UPDATE tracked_websites")
    assert args[4] is False, "nicht gesendetes Feld darf jurisdiction nicht anfassen"
    # FakeConn liefert bei jurisdiction_sent=False den bestehenden Wert "de"
    assert result["website"]["jurisdiction"] == "de"


def test_model_fields_set_distinguishes_absent_from_explicit_null():
    """Die Grundlage des Fixes: Pydantic unterscheidet beide Fälle."""
    absent = WebsiteCreate(url="https://example.com", score=1)
    explicit = WebsiteCreate(**{"url": "https://example.com", "score": 1, "jurisdiction": None})

    assert "jurisdiction" not in absent.model_fields_set
    assert "jurisdiction" in explicit.model_fields_set
    assert absent.jurisdiction is None and explicit.jurisdiction is None


def test_dead_jurisdiction_update_model_is_gone():
    """WebsiteJurisdictionUpdate war toter Code ohne Endpunkt -> entfernt."""
    assert not hasattr(website_routes, "WebsiteJurisdictionUpdate")
