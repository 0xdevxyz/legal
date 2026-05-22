# Phase 3: Re-Scan 500 Fix
Datum: 2026-05-22
Status: completed

## Root Cause

**Primär:** `CSRFMiddleware.dispatch()` → `response.set_cookie()` auf GET-Responses
→ `response.headers.pop("content-length")` — `MutableHeaders` hat kein `pop()`
→ führte zu `RuntimeError: Response content longer than Content-Length`
→ alle folgenden Requests in der gleichen Verbindung scheiterten mit 500

## Fixes

### csrf_middleware.py
1. `response.headers.pop("content-length", None)` → `del response.headers["content-length"]`
   - Korrekte API für `MutableHeaders`
2. EXEMPT_PATHS erweitert um `/api/v2/analyze`, `/api/v2/analyze/quick`, `/api/v2/analyze/complete`

### main_production.py  
1. `scanner.scan_website()` mit `asyncio.wait_for(timeout=120.0)` gewrappt
2. `asyncio.TimeoutError` separat gefangen → HTTP 504 statt 500
3. `logger.exception()` robuster (kein `dir()` Check mehr)

## Verifizierung
- `GET /api/auth/health` → 200 + CSRF-Cookie korrekt gesetzt ✓
- Backend `healthy` ✓
- Kein `RuntimeError: Response content longer than Content-Length` in Logs ✓
