# Phase E – In-Memory-Eliminierung

**Branch**: `cleanup/phase-e-no-fallback`
**Datum**: 2026-05-24
**Status**: completed

## Durchgeführte Migrationen

### 1. database_service.py – use_fallback entfernt
**Problem**: `use_fallback`-Flag war toter Code (wurde nur auf `False` gesetzt, nie auf `True`). Alle `if self.use_fallback:` Branches gaben statische Dummy-Daten zurück.

**Fix**: 
- `use_fallback` Attribut komplett entfernt
- Alle 6 `if self.use_fallback:` Guard-Blöcke entfernt
- `initialize()` wirft bereits `RuntimeError` bei DB-Down → Fail Fast ist vorhanden

**Dateien**: `backend/database_service.py`

### 2. admin_routes.py – Fallback-Branches entfernt
**Problem**: 5 Endpoints prüften `db_service.use_fallback` und verwendeten `db_service.fallback_storage['leads']` (dict das nie befüllt wurde).

**Fix**: Alle `if db_service.use_fallback:` Branches entfernt. Database-only Pfad ist der einzige Pfad.

**Dateien**: `backend/admin_routes.py`

### 3. git_routes.py – OAuth-State: In-Memory → Redis
**Problem**: `oauth_states: Dict[str, Dict]` – globales Python-Dict, verliert State bei Restart, nicht skalierbar, kein Ablauf.

**Fix**:
- `_set_oauth_state()`, `_get_oauth_state()`, `_del_oauth_state()` als async-Funktionen mit Redis SETEX (TTL 600s)
- `redis_client` global + Injection über `init_git_routes(pool, auth_svc, redis_svc)`
- `main_production.py:482`: `init_git_routes(db_pool, auth_service, _async_redis)`

**Dateien**: `backend/git_routes.py`, `backend/main_production.py`

### 4. cookie_compliance_routes.py – Rate-Limit: In-Memory → Redis
**Problem**: `_rate_limit_windows: Dict[str, deque]` – verliert State bei Restart, kein horizontales Scaling.

**Fix**:
- `check_rate_limit()` als async-Funktion mit Redis ZADD/ZREMRANGEBYSCORE Sliding Window
- Graceful degradation: falls `redis_client is None` → `return True` (kein Hard-Fail)
- `redis_client` global + Injection aus `main_production.py`
- Call site in `log_consent()` auf `await check_rate_limit()` umgestellt

**Dateien**: `backend/cookie_compliance_routes.py`, `backend/main_production.py`

### 5. widget_routes.py – ZIP-Storage: In-Memory → Filesystem (tempfile)
**Problem**: `generate_accessibility_patches._temp_storage` – function-level dict, verliert State bei Restart.

**Fix**:
- ZIP wird in `tempfile.gettempdir()` als `complyo_patches_{download_id}.zip` gespeichert
- Download-Endpoint liest Datei, löscht sie nach Auslieferung (einmalig)

**Dateien**: `backend/widget_routes.py`

## Akzeptanzkriterien (Phase E)
- [x] Kein `use_fallback` in `database_service.py`
- [x] Kein `fallback_storage` in `admin_routes.py`
- [x] OAuth-State in Redis (TTL 10min)
- [x] Rate-Limit in Redis (ZADD Sliding Window)
- [x] ZIP nicht im RAM gespeichert

## Noch offen (Phase E+1)
- `docker-compose`: `depends_on: db: condition: service_healthy` hinzufügen
- `/health` Endpoint: 503 zurückgeben wenn DB oder Redis nicht erreichbar

## Commit + Tag
- Commit: `chore(cleanup-e): eliminate all in-memory fallbacks, migrate to Redis`
- Tag: `cleanup-phase-e-done`
