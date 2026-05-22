# Phase 1: Backend Auth-Hardening
Datum: 2026-05-22
Status: completed

## Implementierte Fixes

### RC-1: Cookie-Path-Fix
- `logout` Endpoint: `delete_cookie(path="/api/auth")` → `path="/"`
- Domain-Argument ergänzt: `domain=COOKIE_DOMAIN`
- Verifiziert: `Set-Cookie: refresh_token=""; Path=/` ✓

### RC-2: Refresh-Cookie 204 statt 401
- `refresh-cookie` Endpoint: bei fehlendem Cookie → `JSONResponse(status_code=204, content=None)`
- Verhindert Endlos-401-Schleife im Frontend
- Verifiziert: `HTTP 204` ohne Cookie ✓

### Neue Endpoints für NextAuth.js v5
- `POST /api/auth/verify-credentials` — Credentials-Provider-Endpoint
  - Gibt user-Objekt mit id, email, full_name, plan_type, role, onboarding_completed zurück
- `GET /api/auth/session-info` — Session-Callback-Endpoint (JWT-geschützt)
  - Gibt enriched session data zurück inkl. active_modules

### DB-Migration: users.role
- Neues Feld: `role VARCHAR(20) DEFAULT 'customer' CHECK (role IN ('admin', 'agency', 'customer'))`
- Index: `idx_users_role`
- Migration-Datei: `backend/migrations/add_user_roles.sql`
- Angewendet auf complyo_db ✓

### auth_service.py
- `get_user_by_id` lädt jetzt `role` Feld mit

### dependencies.py
- `require_admin` auf role-basiertes RBAC umgestellt (kein `is_superuser` mehr)

## Tests
- `GET /health` → 200 healthy ✓
- `GET /api/auth/health` → auth_service_initialized: true ✓
- `POST /api/auth/refresh-cookie` (kein Cookie) → 204 ✓
- `POST /api/auth/logout` → Set-Cookie Path=/ ✓
