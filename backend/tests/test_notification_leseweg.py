"""
Wächtertests für den Benachrichtigungs-Leseweg (notification_routes.py)
=======================================================================

Die Tabelle user_legal_notifications hatte bis 08/2026 keinen einzigen Leser
(1.208 Zeilen, alle ungelesen). Mit dem neuen Leseweg gilt:

1. Ohne Token: 401 — beide Routen hängen an der kanonischen Auth-Dependency.
2. GET liefert ausschließlich EIGENE Benachrichtigungen; die user_id kommt
   allein aus dem JWT, ein user_id-Query-Parameter wird ignoriert (kein IDOR).
3. Die Gelesen-Markierung greift nur auf eigene Zeilen; fremde IDs → 404.

Aufbau analog test_statement_generator.py / test_ab_test_auth.py:
- statischer Wächter über den Quelltext (jede Route braucht current_user)
- FastAPI-App nur mit dem Router, get_current_user per dependency_overrides,
  DB-Pool als In-Memory-Fake (kein Live-Postgres nötig).
"""

import os
import re
import sys
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import notification_routes
from dependencies import get_current_user

_ROUTES_FILE = os.path.join(os.path.dirname(__file__), "..", "notification_routes.py")


# ===========================================================================
# 1. Statischer Wächter: keine Route ohne Auth
# ===========================================================================

_ROUTE_PATTERN = re.compile(
    r'@router\.(get|post|patch|delete|put)\("([^"]*)"\)\s*\nasync def (\w+)\((.*?)\n\):',
    re.S,
)


def _routen():
    with open(_ROUTES_FILE, encoding="utf-8") as fh:
        src = fh.read()
    for m in _ROUTE_PATTERN.finditer(src):
        yield m.group(1).upper(), m.group(2), m.group(3), m.group(4)


class TestRoutenGeschuetzt:
    def test_routen_werden_erkannt(self):
        """Wenn der Regex nichts findet, sind die folgenden Aussagen wertlos."""
        assert len(list(_routen())) >= 2

    def test_keine_route_ohne_auth(self):
        offen = [
            f"{methode} {pfad} ({fn})"
            for methode, pfad, fn, signatur in _routen()
            if "current_user" not in signatur
        ]
        assert not offen, (
            "Route(n) ohne Auth-Prüfung in notification_routes.py: "
            + ", ".join(offen)
            + ". Benachrichtigungen sind personenbezogen — jede Route braucht "
            "current_user = Depends(get_current_user)."
        )

    def test_user_id_kommt_nur_aus_dem_jwt(self):
        """Kein Query-/Body-Parameter darf die user_id von außen setzen."""
        with open(_ROUTES_FILE, encoding="utf-8") as fh:
            src = fh.read()
        for _, pfad, fn, signatur in _routen():
            assert "user_id" not in signatur, (
                f"{fn} ({pfad}) nimmt user_id als Parameter entgegen — "
                "IDOR-Weg; die user_id gehört ausschließlich aus current_user gelesen."
            )
        assert 'current_user["id"]' in src


# ===========================================================================
# 2. Verhalten gegen eine In-Memory-DB
# ===========================================================================

_NOW = datetime(2026, 8, 11, 12, 0, 0)


def _daten():
    """Zwei User: 1 besitzt 11 (ungelesen) + 12 (gelesen), 2 besitzt 21 (ungelesen)."""
    def zeile(nid, gelesen, minuten_alt, titel):
        return {
            "id": nid,
            "legal_update_id": 5,
            "website_id": uuid.UUID("00000000-0000-0000-0000-000000000042"),
            "notification_type": "rescan_required",
            "is_read": gelesen,
            "action_taken": False,
            "created_at": _NOW - timedelta(minutes=minuten_alt),
            "read_at": _NOW if gelesen else None,
            "title": titel,
            "severity": "warning",
            "update_type": "law_change",
            "url": None,
        }

    return {
        1: [zeile(11, False, 10, "TTDSG-Änderung"), zeile(12, True, 5, "DSGVO-Update")],
        2: [zeile(21, False, 1, "BFSG-Frist")],
    }


class FakeConn:
    """Minimaler asyncpg-Ersatz; filtert strikt nach dem user_id-Argument."""

    def __init__(self, rows_by_user):
        self.rows_by_user = rows_by_user
        self.calls = []

    async def fetch(self, query, *args):
        self.calls.append(("fetch", query, args))
        user_id, limit, offset = args[0], args[1], args[2]
        rows = list(self.rows_by_user.get(user_id, []))
        if "is_read = FALSE" in query:
            rows = [r for r in rows if not r["is_read"]]
        # ORDER BY is_read ASC, created_at DESC nachbilden
        rows.sort(key=lambda r: (r["is_read"], -r["created_at"].timestamp()))
        return rows[offset : offset + limit]

    async def fetchval(self, query, *args):
        self.calls.append(("fetchval", query, args))
        user_id = args[0]
        return sum(1 for r in self.rows_by_user.get(user_id, []) if not r["is_read"])

    async def fetchrow(self, query, *args):
        self.calls.append(("fetchrow", query, args))
        nid, user_id = args[0], args[1]
        for r in self.rows_by_user.get(user_id, []):
            if r["id"] == nid:
                return {"id": nid, "read_at": _NOW}
        return None


class _Ctx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _Ctx(self._conn)


def make_app(user=None):
    """Ohne `user` bleibt die echte Auth-Dependency aktiv (für die 401-Tests)."""
    app = FastAPI()
    app.include_router(notification_routes.router)
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _mit_pool(monkeypatch):
    conn = FakeConn(_daten())
    monkeypatch.setattr(notification_routes.db_service, "pool", FakePool(conn))
    return conn


def _user(uid):
    return {"id": uid, "user_id": uid, "email": f"user{uid}@example.com", "is_active": True}


class TestOhneToken:
    def test_get_ohne_token_401(self):
        client = make_app()
        assert client.get("/api/notifications").status_code == 401

    def test_read_ohne_token_401(self):
        client = make_app()
        assert client.post("/api/notifications/11/read").status_code == 401


class TestNurEigene:
    def test_get_liefert_nur_eigene(self, monkeypatch):
        _mit_pool(monkeypatch)
        client = make_app(user=_user(1))
        r = client.get("/api/notifications")
        assert r.status_code == 200
        ids = [n["id"] for n in r.json()["notifications"]]
        assert sorted(ids) == [11, 12]
        assert 21 not in ids

    def test_fremde_user_id_im_query_wird_ignoriert(self, monkeypatch):
        """IDOR-Versuch: User 2 fragt mit ?user_id=1 — sieht trotzdem nur Eigenes."""
        conn = _mit_pool(monkeypatch)
        client = make_app(user=_user(2))
        r = client.get("/api/notifications", params={"user_id": 1})
        assert r.status_code == 200
        assert [n["id"] for n in r.json()["notifications"]] == [21]
        # und die Query wurde tatsächlich mit user_id=2 gebunden
        fetch_args = [a for art, _, a in conn.calls if art == "fetch"][-1]
        assert fetch_args[0] == 2

    def test_ungelesene_zuerst(self, monkeypatch):
        _mit_pool(monkeypatch)
        client = make_app(user=_user(1))
        ids = [n["id"] for n in client.get("/api/notifications").json()["notifications"]]
        assert ids[0] == 11  # ungelesen vor gelesen

    def test_unread_count_zaehlt_nur_eigene(self, monkeypatch):
        _mit_pool(monkeypatch)
        client = make_app(user=_user(1))
        assert client.get("/api/notifications").json()["unread_count"] == 1

    def test_pagination_wird_durchgereicht(self, monkeypatch):
        """LIMIT/OFFSET statt Vollscan — der Leseweg bleibt datenmengen-unabhängig."""
        conn = _mit_pool(monkeypatch)
        client = make_app(user=_user(1))
        r = client.get("/api/notifications", params={"limit": 1, "offset": 0})
        assert len(r.json()["notifications"]) == 1
        fetch_args = [a for art, _, a in conn.calls if art == "fetch"][-1]
        assert fetch_args[1] == 1 and fetch_args[2] == 0

    def test_limit_wird_gedeckelt(self, monkeypatch):
        _mit_pool(monkeypatch)
        client = make_app(user=_user(1))
        assert client.get("/api/notifications", params={"limit": 5000}).status_code == 422


class TestGelesenMarkierung:
    def test_eigene_markieren_ok(self, monkeypatch):
        _mit_pool(monkeypatch)
        client = make_app(user=_user(1))
        r = client.post("/api/notifications/11/read")
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_fremde_id_gibt_404(self, monkeypatch):
        """User 2 versucht, die Benachrichtigung von User 1 zu markieren."""
        conn = _mit_pool(monkeypatch)
        client = make_app(user=_user(2))
        r = client.post("/api/notifications/11/read")
        assert r.status_code == 404
        # Das UPDATE war an user_id=2 gebunden — nicht an den Besitzer
        row_args = [a for art, _, a in conn.calls if art == "fetchrow"][-1]
        assert row_args == (11, 2)

    def test_unbekannte_id_gibt_404(self, monkeypatch):
        _mit_pool(monkeypatch)
        client = make_app(user=_user(1))
        assert client.post("/api/notifications/99999/read").status_code == 404
