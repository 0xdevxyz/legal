# Login/Onboarding CORS + CSRF Fix

## Problem
- `app.complyo.de` → `api.complyo.de`: CORS blockiert (kein `Access-Control-Allow-Origin` Header)
- `/api/analyze` und `/api/v2/dashboard/metrics`: HTTP 403 durch CSRF-Middleware (fehlender X-CSRF-Token)

## Root Causes
1. `nginx/complyo.de`: `api.complyo.de`-Block hatte keine CORS-Header → Browser blockiert Cross-Origin-Requests
2. `backend/csrf_middleware.py`: `/api/analyze` fehlte in `EXEMPT_PATHS` → 403 Forbidden beim POST

## Changes
- `backend/csrf_middleware.py`: `/api/analyze` zu EXEMPT_PATHS hinzugefügt
- `nginx/complyo.de`: CORS map + preflight (OPTIONS) + CORS-Header für `api.complyo.de`-Block

## Deploy
1. nginx neu laden: `sudo nginx -t && sudo systemctl reload nginx`
2. Backend neu starten: `docker compose restart backend` oder `systemctl restart complyo-backend`
