# Phase 1 – Auth-Konsolidierung

**Datum:** 2026-05-16

## Problem

8 separate `get_current_user`-Implementierungen in verschiedenen Route-Dateien. Jede mit subtil anderen JWT-Decode-Parametern und unterschiedlicher user_id-Behandlung → erklärt 401 vs 403 vs "durch" auf verschiedenen Routen.

## Durchgeführte Änderungen

### `backend/dependencies.py` — Single Source of Truth

`get_current_user` von "JWT-Payload zurückgeben" zu vollständigem Flow:
1. JWT validieren (aud, iss, sig, exp)
2. `user_id` aus Payload extrahieren → `int`
3. DB-Lookup via `AuthService.get_user_by_id(user_id)`
4. `is_active` prüfen → 403 wenn deaktiviert
5. Garantiert `id: int` im Return-Dict

`get_current_user_optional` gleiches Muster ohne Exception.

### Migrierte Dateien (lokale Definition entfernt → Import)

| Datei | Was entfernt | Was hinzugefügt |
|-------|-------------|----------------|
| `website_routes.py` | lokale def + get_user_id_from_token helper | `from dependencies import get_current_user` |
| `dashboard_routes.py` | lokale def + user.get("user_id") | `from dependencies import get_current_user`, `user["id"]` |
| `fix_routes.py` | lokale def | `from dependencies import get_current_user` |
| `fix_apply_routes.py` | lokale def | `from dependencies import get_current_user` |
| `git_routes.py` | lokale def | `from dependencies import get_current_user` |
| `stripe_routes.py` | Wrapper auf auth_routes | `from dependencies import get_current_user` |
| `auth_routes.py` | lokale def mit DB-Lookup | `from dependencies import get_current_user` (re-export) |
| `ai_legal_routes.py` | importiert aus auth_routes | bleibt (auth_routes re-exportiert aus dependencies) |

### Zusätzliche Fixes

- `website_routes.py`: `get_user_id_from_token(user)` überall durch `user["id"]` ersetzt
- `website_routes.py`: `AND tw.user_id = $2::uuid` → `AND tw.user_id = $2` (int, kein UUID-Cast)
- `fix_apply_routes.py`: `current_user.get('user_id')` → `current_user.get('id')`
- `ai_legal_routes.py`: `get_current_user_id` vereinfacht (kein Extra-DB-Lookup mehr)
- `dashboard_routes.py`: `user.get("user_id")` → `user["id"]`

## Erwartetes Ergebnis

| Endpoint | Vorher | Nachher |
|----------|--------|---------|
| `GET /api/v2/websites` | 403 Forbidden (manchmal) | 200 OK |
| `GET /api/legal-ai/updates` | 401 Unauthorized | 200 OK |
| `GET /api/v2/dashboard/metrics` | str-zu-int TypeError | 200 OK |
| `POST /api/v2/analyze` | 500 (auth-indirekt) | 200 (oder 500 aus anderem Grund → Phase 2) |
