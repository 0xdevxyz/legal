# Security Round 2 — Implementation Log
Datum: 2026-05-05

## S1 — Logout Cookie clearen
- `auth_routes.py` /logout: liest refresh_token aus Cookie UND Body
- Ruft `revoke_refresh_token()` auf
- Löscht HttpOnly-Cookie explizit via `response.delete_cookie()`
- War vorher: Cookie blieb bis natürlichem Ablauf im Browser

## S2 — CSRF-Schutz (Double-Submit Cookie Pattern)
- Neue Datei: `backend/csrf_middleware.py`
- GET/HEAD/OPTIONS: setzt `csrf_token` Cookie (plain, JS-lesbar)
- POST/PUT/PATCH/DELETE: vergleicht Cookie mit `X-CSRF-Token` Header via `hmac.compare_digest`
- Exempt: /api/auth/*, /api/webhooks/*, /widget/*, /health, /metrics, /api/leads/*
- Aktivierung via `CSRF_PROTECTION=false` ENV deaktivierbar (für Tests)
- `main_production.py`: Middleware registriert, `X-CSRF-Token` zu CORS allow_headers ergänzt
- `dashboard-react/src/lib/api.ts`: Request-Interceptor liest `csrf_token` Cookie und setzt Header

## S3 — Account-Lockout (Redis-basiert)
- `auth_service.py`:
  - `AuthService.__init__()` nimmt optionalen `redis_client` Parameter
  - `authenticate()`: prüft `login_fail:{email}` Key in Redis vor Passwort-Check
  - Nach `_MAX_ATTEMPTS` (5, ENV `LOGIN_MAX_ATTEMPTS`) → HTTP 429 mit TTL
  - Fehlgeschlagener Versuch: inkrementiert Counter, setzt TTL auf `_LOCKOUT_SECONDS` (900s = 15min, ENV konfigurierbar)
  - Erfolgreicher Login: löscht Counter
  - Wenn Redis nicht verfügbar: Lockout wird übersprungen, kein Fehler
- `main_production.py`:
  - `_async_redis` global (redis.asyncio) im startup_event initialisiert
  - `AuthService(db_pool, redis_client=_async_redis)` aufgerufen

## S4 — SSRF-Schutz
- Neue Datei: `backend/ssrf_protection.py`
  - `validate_url()`: blockiert private IPv4/IPv6, Loopback, Link-Local, Cloud-Metadata-Endpoints
  - DNS-Auflösung: resolved IP wird ebenfalls gegen Private-Network-Liste geprüft
  - `SSRFError` Exception für ungültige URLs
  - `safe_url_or_none()` für non-critical Pfade
- `website_crawler.py`: `validate_url()` vor erstem Netzwerk-Request aufgerufen
- `cookie_scanner_service.py`: `validate_url()` vor `_fetch_html()` aufgerufen

## S5 — SQL-Injection Audit
- `database_service.py update_lead_status()`: Spalten-Namen kommen aus expliziter Whitelist
  `['last_contacted', 'report_sent_at']` — kein User-Input erreicht Query-String
- Alle Werte als `$n`-Parameter (asyncpg parameterized) — SICHER, keine Änderungen nötig

## S6 — Nginx Härtung
- `nginx/production.conf`:
  - `server_tokens off` im http-Block ergänzt
  - `X-XSS-Protection: 1; mode=block` entfernt (veraltet, kann XSS ermöglichen)
  - `X-Frame-Options` von SAMEORIGIN → DENY verschärft
  - `Strict-Transport-Security` von 31536000 → 63072000 (2 Jahre) erhöht
  - `Permissions-Policy` für alle Server-Blöcke ergänzt

## S7 — Dependency Audit als CI-Schritt
- `.github/workflows/ci.yml`: neuer Job `dependency-audit`
  - `pip-audit --requirement requirements.txt` → Markdown-Report als Artifact
  - `npm audit --audit-level=high` für dashboard + landing → JSON-Report als Artifacts
  - Retention: 30 Tage
  - Läuft bei jedem Push/PR

## S8 — OAuth Token nicht in URL-Fragment
- Kritisches Fix: Tokens wurden als `#access_token=...` in URL übergeben
  (sichtbar in Browser-Verlauf, Nginx-Logs, Referer-Headers)
- `auth_routes.py` Google + Apple Callback:
  - `access_token` → kurzlebiges HttpOnly Cookie `access_token_once` (5 min TTL)
  - `refresh_token` → reguläres HttpOnly Cookie
  - Redirect zu `/auth/callback?provider=google&status=ok` (keine Token in URL)
- Neuer Endpoint `POST /api/auth/oauth-pickup`:
  - Liest `access_token_once` Cookie genau einmal aus
  - Gibt Token + User-Daten zurück
  - Löscht Cookie sofort nach Auslieferung
  - Fehler: interner Server-Fehlertext entfernt

## S9 — Auth 500-Fehlerdetails entfernen
- `auth_routes.py` register + login:
  - `detail=f"Registration failed: {str(e)}"` → `"Registrierung fehlgeschlagen"`
  - `detail=f"Login failed: {str(e)}"` → `"Login fehlgeschlagen"`
  - Vollständige Fehlerdetails nur noch im `logger.error()` (intern)

## Neue Dateien
- `backend/csrf_middleware.py`
- `backend/ssrf_protection.py`

## Geänderte Dateien
- `backend/auth_service.py`
- `backend/auth_routes.py`
- `backend/main_production.py`
- `backend/website_crawler.py`
- `backend/cookie_scanner_service.py`
- `dashboard-react/src/lib/api.ts`
- `nginx/production.conf`
- `.github/workflows/ci.yml`
