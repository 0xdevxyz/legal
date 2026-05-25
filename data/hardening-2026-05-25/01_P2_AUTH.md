# P2 – Auth Hardening

**Branch**: hardening/p2-auth
**Tag start**: pre-hardening-p2
**Tag end**: hardening-p2-done
**Tests**: 12/12 grün

## Änderungen

### backend/schemas/auth_internal.py (neu)
- `JWTUserClaim` Pydantic-Model: id (int), user_id (str), jti, iat, nbf, exp

### backend/auth_service.py
- `create_access_token()`: + jti (uuid4), iat, nbf (now-30s clock-skew)
- Default `ACCESS_TOKEN_EXPIRE_MINUTES`: 60 → **15**
- `_blacklist_jti(jti, ttl)` → `redis.setex("jwt:blacklist:{jti}", ttl, "1")`
- `_is_jti_blacklisted(jti)` → `redis.get("jwt:blacklist:{jti}")`
- `_register_jti_in_set(set_key, jti, ttl)` → `SADD jwt:user_jtis:{uid}`
- `create_refresh_token()`: + user_agent, ip_address Parameter
- `refresh_access_token()`: Rotation (DELETE alte Session, INSERT neue)
- `revoke_all_sessions(user_id)`: DELETE alle Sessions
- `blacklist_all_user_jtis(user_id, ttl)`: SMEMBERS + SETEX jede jti

### backend/dependencies.py
- `get_current_user`: nach JWT-Decode → JTI-Blacklist-Check vor DB-Abfrage
- `AuthService` wird mit Redis-Client instanziiert

### backend/auth_routes.py
- `POST /api/auth/logout`: blacklistet JTI aus Access-Token + löscht Refresh-Session + löscht Cookies
- `POST /api/auth/logout-all`: blacklistet alle JTIs via `jwt:user_jtis:{uid}` + löscht alle Sessions

### backend/migrations/add_session_hardening.sql (neu)
- `ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS jti VARCHAR(64)`
- `ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS revoked_at ...`
- `ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS last_used_at ...`
- `ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_agent TEXT`
- `ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)`
- `CREATE INDEX IF NOT EXISTS idx_user_sessions_jti ON user_sessions(jti)`

## Test-Output
```
12 passed in 0.05s
```
