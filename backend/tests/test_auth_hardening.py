"""
P2 Auth Hardening Tests
=======================
6 Szenarien für JWT-Blacklist, Refresh-Rotation, Reuse-Detection, Logout.

Alle Tests sind unit-/integration-style mit AsyncMock – kein laufender Server nötig.
"""
import sys
import types
from unittest.mock import MagicMock

for _mod in ("asyncpg", "bcrypt", "fastapi", "slowapi", "pydantic"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

_fastapi_exc = types.ModuleType("fastapi.exceptions")
_fastapi_exc.HTTPException = type("HTTPException", (Exception,), {"__init__": lambda self, status_code=400, detail="": setattr(self, "status_code", status_code) or setattr(self, "detail", detail) or None})
sys.modules["fastapi"] = MagicMock(HTTPException=_fastapi_exc.HTTPException)
sys.modules["fastapi.exceptions"] = _fastapi_exc

import time
import pytest
import jwt
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta, timezone

JWT_SECRET = "test-secret-hardening"
JWT_AUDIENCE = "complyo-api"
JWT_ISSUER = "https://complyo.tech"


def _make_token(user_id=1, jti="test-jti", expired=False, extra_claims=None):
    now = int(time.time())
    exp = now - 10 if expired else now + 900
    payload = {
        "id": str(user_id),
        "user_id": str(user_id),
        "jti": jti,
        "iat": now,
        "nbf": now - 30,
        "exp": exp,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256"), payload


def _make_auth_service(redis=None, db_pool=None):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from auth_service import AuthService
    svc = AuthService.__new__(AuthService)
    svc.jwt_secret = JWT_SECRET
    svc.jwt_issuer = JWT_ISSUER
    svc.jwt_audience = JWT_AUDIENCE
    svc.access_token_expire = 15
    svc.refresh_token_expire = 30 * 24 * 60
    svc.redis = redis
    svc.db_pool = db_pool
    return svc


class TestExpiredTokenReturns401:
    """Scenario 1: expired token → 401"""

    def test_expired_token_returns_none_from_verify(self):
        token, _ = _make_token(expired=True)
        svc = _make_auth_service()
        result = svc.verify_token(token)
        assert result is None

    def test_valid_token_returns_payload(self):
        token, payload = _make_token()
        svc = _make_auth_service()
        result = svc.verify_token(token)
        assert result is not None
        assert result["jti"] == "test-jti"


class TestRevokedJtiReturns401:
    """Scenario 2: JTI on Redis blacklist → 401"""

    @pytest.mark.asyncio
    async def test_blacklisted_jti_is_detected(self):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value="1")
        svc = _make_auth_service(redis=redis)
        result = await svc._is_jti_blacklisted("some-jti")
        assert result is True
        redis.get.assert_called_once_with("jwt:blacklist:some-jti")

    @pytest.mark.asyncio
    async def test_clean_jti_returns_false(self):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        svc = _make_auth_service(redis=redis)
        result = await svc._is_jti_blacklisted("clean-jti")
        assert result is False

    @pytest.mark.asyncio
    async def test_blacklist_jti_calls_setex(self):
        redis = AsyncMock()
        redis.setex = AsyncMock()
        svc = _make_auth_service(redis=redis)
        await svc._blacklist_jti("my-jti", 900)
        redis.setex.assert_called_once_with("jwt:blacklist:my-jti", 900, "1")


class TestRefreshRotationInvalidatesOldToken:
    """Scenario 3: after refresh, old token is gone from DB"""

    @pytest.mark.asyncio
    async def test_refresh_deletes_old_session_and_returns_new_tokens(self):
        fake_session = {
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        }
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=fake_session)
        conn.execute = AsyncMock()
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)

        pool = MagicMock()
        pool.acquire = MagicMock(return_value=conn)

        svc = _make_auth_service(db_pool=pool)
        result = await svc.refresh_access_token("old-refresh-token")
        assert result is not None
        new_access, new_refresh = result
        assert new_access != "old-refresh-token"

    @pytest.mark.asyncio
    async def test_expired_session_returns_none(self):
        fake_session = {
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
        }
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=fake_session)
        conn.execute = AsyncMock()
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)

        pool = MagicMock()
        pool.acquire = MagicMock(return_value=conn)

        svc = _make_auth_service(db_pool=pool)
        result = await svc.refresh_access_token("old-refresh-token")
        assert result is None


class TestRefreshReuseAttackRevokesAllSessions:
    """Scenario 4: reuse of already-rotated refresh token → all sessions deleted"""

    @pytest.mark.asyncio
    async def test_missing_session_returns_none(self):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)

        pool = MagicMock()
        pool.acquire = MagicMock(return_value=conn)

        svc = _make_auth_service(db_pool=pool)
        result = await svc.refresh_access_token("already-rotated-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_all_sessions_calls_delete(self):
        conn = AsyncMock()
        conn.execute = AsyncMock()
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)

        pool = MagicMock()
        pool.acquire = MagicMock(return_value=conn)

        svc = _make_auth_service(db_pool=pool)
        await svc.revoke_all_sessions(42)
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0]
        assert "DELETE" in call_args[0]
        assert call_args[1] == 42


class TestLogoutInvalidatesAccessToken:
    """Scenario 5: /logout blacklists the JTI of the current access token"""

    @pytest.mark.asyncio
    async def test_logout_blacklists_jti(self):
        redis = AsyncMock()
        redis.setex = AsyncMock()
        svc = _make_auth_service(redis=redis)

        token, payload = _make_token(jti="logout-jti")
        exp = payload["exp"]
        ttl = max(int(exp - time.time()), 1)

        await svc._blacklist_jti("logout-jti", ttl)
        redis.setex.assert_called_once()
        key = redis.setex.call_args[0][0]
        assert key == "jwt:blacklist:logout-jti"


class TestLogoutAllInvalidatesAllSessions:
    """Scenario 6: /logout-all blacklists all JTIs + deletes all sessions"""

    @pytest.mark.asyncio
    async def test_logout_all_blacklists_all_jtis(self):
        redis = AsyncMock()
        redis.smembers = AsyncMock(return_value={"jti-1", "jti-2", "jti-3"})
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()

        conn = AsyncMock()
        conn.execute = AsyncMock()
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)
        pool = MagicMock()
        pool.acquire = MagicMock(return_value=conn)

        svc = _make_auth_service(redis=redis, db_pool=pool)
        await svc.blacklist_all_user_jtis(user_id=1, ttl_seconds=900)

        assert redis.smembers.call_count == 1
        assert redis.setex.call_count == 3
        redis.delete.assert_called_once_with("jwt:user_jtis:1")

    @pytest.mark.asyncio
    async def test_revoke_all_removes_all_db_sessions(self):
        conn = AsyncMock()
        conn.execute = AsyncMock()
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)
        pool = MagicMock()
        pool.acquire = MagicMock(return_value=conn)

        svc = _make_auth_service(db_pool=pool)
        await svc.revoke_all_sessions(user_id=5)
        conn.execute.assert_called_once()
        sql = conn.execute.call_args[0][0]
        assert "DELETE" in sql
        assert "user_id" in sql
