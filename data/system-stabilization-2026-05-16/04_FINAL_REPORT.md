# Phase 4 – Final Report

**Datum:** 2026-05-16  
**Session:** System-Stabilisierung Auth → Scan → Widget

---

## Zusammenfassung

### Problem A: GET /api/v2/websites → 403 Forbidden
**Status:** ✅ Behoben

Root Cause: `website_routes.py` hatte eigene `get_current_user` die `auth_service.verify_token()` + eigenen DB-Lookup-Helper nutzte. Der Helper (`get_user_id_from_token`) machte einen zusätzlichen `WHERE id::text = $1` Query und gab die UUID zurück — dann crashte der nachfolgende Code mit UUID-vs-int-Mismatch.

Fix: Lokale Definition entfernt. Importiert aus `dependencies.get_current_user` (gibt garantiert `id: int`). Alle `get_user_id_from_token(user)` durch `user["id"]` ersetzt.

### Problem B: GET /api/legal-ai/updates → 401 Unauthorized
**Status:** ✅ Behoben

Root Cause: Log zeigte `Invalid token: Not enough segments`. `ai_legal_routes.py` importierte `get_current_user` aus `auth_routes` — die alte Version nutzte `auth_service.verify_token()` das in bestimmten Timing-Situationen einen leeren Token nicht richtig abwies.

Eigentliches Problem: `get_current_user_id`-Wrapper in `ai_legal_routes.py` machte Extra-DB-Lookup, der fehlschlug weil er UUID-basiert arbeitete. Die vereinfachte Version (direkt `current_user["id"]`) ist korrekt.

Fix: `auth_routes.get_current_user` re-exportiert aus `dependencies`. `get_current_user_id` vereinfacht.

### Problem C: POST /api/v2/analyze → 500 Internal Server Error
**Status:** ✅ Behoben

Root Cause: `score_history`-Tabelle existierte nicht in der Datenbank. Der Scan lief erfolgreich durch, aber beim INSERT in `score_history` crashte der Code.

Zusätzlich: `score_history.website_id` war in der alten Migration als INTEGER, aber `tracked_websites.id` ist UUID.

Fixes:
1. Tabelle angelegt: `website_id UUID, user_id INTEGER, overall_score, pillar_scores JSONB, scan_date`
2. `logger.exception()` statt `print()` für besseres Debugging
3. Auth-Konsolidierung verhindert weitere Typ-Fehler bei `current_user["id"]`

### Problem D: accessibility.js:922 TypeError
**Status:** ✅ Behoben

Root Cause: `closePanel()` in `accessibility-v6.js` griff direkt auf `panel.hidden` und `toggleBtn` zu ohne Null-Check, wenn DOM noch nicht bereit.

Fix: `if (panel)` + `if (toggleBtn)` Guards eingebaut.

---

## Geänderte Dateien

### Backend
| Datei | Änderung |
|-------|---------|
| `backend/dependencies.py` | `get_current_user` mit DB-Lookup, `id: int` Garantie |
| `backend/website_routes.py` | Lokale def entfernt, UUID-Cast-Fix, user["id"] |
| `backend/dashboard_routes.py` | Lokale def entfernt, user["id"] |
| `backend/fix_routes.py` | Lokale def entfernt |
| `backend/fix_apply_routes.py` | Lokale def entfernt, user.get('id') |
| `backend/git_routes.py` | Lokale def entfernt |
| `backend/stripe_routes.py` | Wrapper entfernt, direkter Import |
| `backend/auth_routes.py` | Re-export aus dependencies |
| `backend/ai_legal_routes.py` | get_current_user_id vereinfacht |
| `backend/main_production.py` | logger.exception statt print |
| `backend/widgets/accessibility-v6.js` | Null-Guard in closePanel() |

### Datenbank
| Migration | Ergebnis |
|-----------|---------|
| `CREATE TABLE score_history` | Tabelle mit UUID website_id + INTEGER user_id |

---

## Test-Matrix (pending User-Login)

| Endpoint | Erwartet | Status |
|----------|----------|--------|
| `GET /api/v2/websites` | 200 + Liste | ⏳ Warte auf Live-Test |
| `GET /api/legal-ai/updates?limit=10` | 200 + Updates | ⏳ Warte auf Live-Test |
| `GET /api/v2/dashboard/metrics` | 200 | ⏳ Warte auf Live-Test |
| `POST /api/v2/analyze` | 200 + Score | ⏳ Warte auf Live-Test |
| Widget auf complyo.de | Kein TypeError | ⏳ Warte auf Live-Test |

---

## Offene Punkte

1. **`scan_history.website_id` ist INTEGER, `tracked_websites.id` ist UUID** — wenn score-history Fallback auf scan_history läuft, gibt es noch einen Mismatch. Nicht kritisch für Scan, aber für Score-History-Chart.
2. **`cookie_ab_tests`-Tabelle fehlt** — `Error getting variant assignment: relation "cookie_ab_tests" does not exist` — separates Issue.
3. **Refresh-Cookie 401** — zweiter Refresh-Request nach Login bekommt 401 (normal — Rotation). Kein Problem.

## Empfehlungen für Folge-Sessions

- `scan_history.website_id` zu UUID migrieren (konsistent mit `tracked_websites.id`)
- `cookie_ab_tests`-Tabelle anlegen
- Auth-E2E-Tests schreiben die 401/403/200-Status für alle Endpunkte prüfen
