# TASK-2: Baseline

**Aufnahme:** 2026-05-24

## DB-Status

| Tabelle | Existiert | Zeilen |
|---------|-----------|--------|
| `tcf_vendors` | ❌ FEHLT | 0 |
| `cookie_compliance_stats` | ✅ | 1 |
| `cookie_banner_configs` | ✅ | – |
| `cookie_services` | ✅ | – |

## Root-Cause-Bestätigung

### Bug 1: `/tcf/vendors` → 500
Tabelle `tcf_vendors` existiert nicht. Der Endpoint führt einen `SELECT FROM tcf_vendors` aus und wirft sofort `UndefinedTable`.  
**Fix:** Migration + GVL-Seed + Cron.

### Bug 2: `/policy/{site}?lang=de` → 500
`cookie_banner_configs.services` ist **JSONB** (`'[]'::jsonb`), der Query versucht aber `ANY(c.services)` – ein Typ-Mismatch für den JOIN mit `cookie_services.service_key`.  
**Fix:** Query auf `jsonb_array_elements_text(c.services)` umstellen.

### Bug 3: `/stats/{site}?days=30` → 404
Aus Docker-Logs: `GET /cookie-compliance/stats/complyo-de?days=30 HTTP/1.0" 404`  
→ Das Frontend-URL-Präfix fehlt `/api/`. Der `ConsentStatistics.tsx` ruft korrekt `/api/cookie-compliance/stats/${siteId}` auf. 
→ Die 404 kommt vom **nginx-Gateway**, das `/api/cookie-compliance/stats/*` nicht korrekt routet – oder die URL die im Browser zu sehen ist kommt aus einer anderen Komponente.  
→ Zusätzlich: SQL-Injection in `days`-Parameter (String-Interpolation).  
**Fix:** Gateway-Routing prüfen + SQL-Injection schließen.

## `cookie_banner_configs.services` Typ
```
services | jsonb | not null | '[]'::jsonb
```
**Gespeichert als JSONB-Array von Strings** (service_keys). JOIN braucht `jsonb_array_elements_text(c.services)`.

## `cookie_compliance_stats` Schema
Tabelle existiert mit allen erforderlichen Spalten (nach Migration `fix_cookie_compliance_stats.sql`). 1 Zeile Testdaten vorhanden.

## Docker-Logs (relevante Zeilen)
```
GET /api/cookie-compliance/tcf/vendors HTTP/1.0" 500
GET /api/cookie-compliance/policy/complyo-de?lang=de HTTP/1.0" 500
GET /cookie-compliance/stats/complyo-de?days=30 HTTP/1.0" 404   ← fehlendes /api/ Präfix
Error getting variant assignment: relation "cookie_ab_tests" does not exist
ERROR:dashboard_routes: column "ai_fixes_count" does not exist
```

## Gateway-Routing
Konfiguration unter `gateway/nginx-production.conf` – wird in TASK-5 geprüft.
