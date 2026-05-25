# Security & Cleanup Implementation Log
Datum: 2026-05-05

## Phase 1 – Kritische Sicherheitslücken

### 1.1 Hardcodiertes DB-Passwort entfernt
- `backend/database_service.py`: Default-Wert `ComplYo2025SecurePass` entfernt
- Startup-Check: `RuntimeError` wenn `DATABASE_URL` nicht gesetzt
- Alle Fallback-Methoden (`_create_lead_fallback`, `_get_lead_by_email_fallback`, etc.) entfernt
- Stille `use_fallback=True`-Logik durch explizite Fehler ersetzt
- `.env.example` mit Platzhaltern angelegt

### 1.2 Unauthentifizierte Endpoints
- Überprüft: `ai_legal_routes.py` Endpoints bereits mit `Depends(get_current_user)` gesichert
- `widget_routes.py` Alt-Text-Endpoint: bewusst public (Widget-Daten für Besucher)
- `cookie_compliance_routes.py` Consent-Log: bewusst public (DSGVO-Einwilligung von Besuchern)

### 1.3 Access Token Lifetime & Refresh-Rotation
- `backend/auth_service.py`: TTL von 7 Tagen → **60 Minuten** (per ENV `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh-Token-TTL über ENV `REFRESH_TOKEN_EXPIRE_DAYS` (Default: 30 Tage)
- `refresh_access_token()`: gibt jetzt Tuple `(access_token, refresh_token)` zurück
- Bei jedem Refresh: altes Token wird **sofort gelöscht** (Rotation)
- `auth_routes.py` `/refresh` und `/refresh-cookie` aktualisiert

### 1.4 Token-Speicherung: localStorage → HttpOnly Cookies
- `dashboard-react/src/contexts/AuthContext.tsx`:
  - `localStorage.setItem('access_token', ...)` komplett entfernt
  - `localStorage.setItem('refresh_token', ...)` komplett entfernt
  - Manuelles `document.cookie`-Setzen via JS entfernt
  - Session-Restore nutzt jetzt `/api/auth/refresh-cookie` (HttpOnly Cookie)
  - Auto-Refresh nutzt jetzt `/api/auth/refresh-cookie`
  - `setAccessTokenWithSync()`: synct Token in `window.__complyo_access_token`
- `dashboard-react/src/lib/api.ts`:
  - Token-Injektion nutzt `window.__complyo_access_token` statt localStorage
  - 401-Handling nutzt `/api/auth/refresh-cookie` statt `localStorage.getItem('refresh_token')`

## Phase 2 – Sicherheitsverbesserungen

### 2.1 HTTP-Sicherheitsheader
- `dashboard-react/next.config.js` ergänzt:
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(self), usb=()`
  - `Content-Security-Policy`: vollständige CSP mit allen nötigen Quellen
  - `Referrer-Policy` auf `strict-origin-when-cross-origin` verschärft

### 2.2 JWT-Fehlermeldungen neutralisiert
- `backend/dependencies.py`: `detail=f"Invalid token: {str(e)}"` → `"Authentication failed"`
- Interne Fehler über `logger.warning()` geloggt

### 2.3 X-Forwarded-For Proxy-Whitelist
- `backend/dependencies.py`: `get_client_ip()` liest `TRUSTED_PROXIES` aus ENV
- `X-Forwarded-For` wird nur akzeptiert wenn direkter Client-IP in der Whitelist ist

### 2.4 Doppelte Auth-Bibliotheken konsolidiert
- `requirements.txt`: `bcrypt==4.1.2` und `python-jose[cryptography]` entfernt
- `auth_service.py`, `main_production.py`, `user_routes.py`: direkte `bcrypt`-Aufrufe → `passlib.CryptContext`
- `lxml==4.9.3` → `lxml>=5.1.0` (CVE-Fixes)
- `certifi==2023.11.17` → `certifi>=2024.2.2`

### 2.6 Doppelte Sentry-Initialisierung bereinigt
- `backend/main_production.py`: zweite `import sentry_sdk` + auskommentierte Duplikat-Blöcke entfernt
- Saubere Einzel-Initialisierung mit `sentry_sdk as _sentry_sdk`

### 2.7 BYPASS_PAYMENT Guard
- `backend/main_production.py`: Startup-Check — `BYPASS_PAYMENT=true` in production → `RuntimeError`
- `UNLIMITED_FIXES=true` in production → `logger.warning`
- Flags aus `docker-compose.yml` entfernt (nur noch über `.env` steuerbar)

### 2.8 Docker HEALTHCHECK & Ressourcen-Limits
- `docker-compose.yml`:
  - Backend: HEALTHCHECK auf `/health`, `start_period: 40s`
  - Landing + Dashboard: HEALTHCHECK auf Port 3000
  - postgres: `mem_limit: 512m`
  - redis: `mem_limit: 256m`
  - landing + dashboard: je `mem_limit: 512m`

## Phase 3 – Code-Qualität

### 3.1 SELECT * ersetzt
- `backend/auth_service.py`: Explizite Spalten in `get_user_by_email()` und `authenticate()`
- Passwort-Hash wird nur noch intern für Verifikation genutzt, nicht an Aufrufer weitergegeben

### 3.2 Stille DB-Fallback-Logik entfernt
- Bereits in Task 1.1 erledigt: alle Fallback-Methoden in `database_service.py` entfernt

### 3.3 Doppelte Komponente konsolidiert
- `dashboard-react/src/components/dashboard/ERecht24CookieManager.tsx` gelöscht (identisch mit ComplyoCookieManager)
- `ComplyoCookieManager.tsx` bleibt als einzige Komponente

### 3.4 Ressourcen-Limits
- Bereits in Task 2.8 erledigt

## Phase 4 – Dateilöschungen

### 4.1 Obsolete Backend-Skripte (6 Dateien)
- `backend/classify_new_updates.py` — durch v3 ersetzt
- `backend/classify_new_updates_v2.py` — durch v3 ersetzt
- `backend/classify_legal_updates.py` — durch `ai_legal_classifier.py` ersetzt
- `backend/classify_legal_updates_simple.py` — nicht importiert
- `backend/erecht24_routes_v2_simple.py` — Diagnose-Stub
- `backend/update_main.py` — Migrations-Artefakt mit falschem Pfad

### 4.3 Root-Level Temporärdateien
- Gelöscht: `COOKIE_BANNER_DEBUG_SCRIPT.js`, `COOKIE_BANNER_MANUAL_TEST.html`
- Gelöscht: `compressed_image.jpg`, `compressed_under_4mb.jpg`
- Verschoben: `scanner_flow.excalidraw` → `docs/`
- Verschoben: `deploy_ai_legal_production.sh` → `scripts/`
- Gelöscht aus `backend/public/`: 7 HTML-Testdateien (banner-demo, test-banner, etc.)

## Gesamtübersicht geänderter Dateien

```
backend/
  database_service.py      — Passwort, Fallback-Logik
  auth_service.py          — Token-TTL, Refresh-Rotation, SELECT*, passlib
  auth_routes.py           — Token-Rotation, Cookie-Rotation
  dependencies.py          — JWT-Error, Proxy-Whitelist, Logger
  main_production.py       — Sentry-Duplikat, BYPASS_PAYMENT-Guard, passlib
  user_routes.py           — passlib Migration
  requirements.txt         — bcrypt, python-jose entfernt; lxml, certifi aktualisiert
  [6 Dateien gelöscht]
  public/[7 HTML-Testdateien gelöscht]

dashboard-react/
  src/contexts/AuthContext.tsx  — localStorage entfernt, HttpOnly Cookie-Flow
  src/lib/api.ts               — localStorage entfernt, window.__complyo_access_token
  next.config.js               — Security Headers (HSTS, CSP, Permissions)
  src/components/dashboard/
    ERecht24CookieManager.tsx  — gelöscht (Duplikat)

docker-compose.yml             — HEALTHCHECK, Ressourcen-Limits, Flags entfernt
.env.example                   — neu angelegt
docs/scanner_flow.excalidraw   — verschoben von Root
scripts/deploy_ai_legal_production.sh  — verschoben von Root
```
