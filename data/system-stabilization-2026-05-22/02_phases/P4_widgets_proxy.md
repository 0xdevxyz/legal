# Phase 4: Widgets + First-Party-Proxy
Datum: 2026-05-22
Status: completed

## Root Cause
RC-6: 6 Widget-Dateien hardcoded auf https://api.complyo.tech (falsche Domain, nicht erreichbar).
Adblocker blockieren externe Tracker-Skripte.

## Fixes

### Widget API_BASE – konfigurierbar via data-api-base Attribut
Alle Widgets lesen jetzt `data-api-base` vom Script-Tag, Fallback: `https://api.complyo.de`

| Datei | Änderung |
|-------|----------|
| `backend/widgets/accessibility-v6.js` | `currentScript.getAttribute('data-api-base') \|\| 'https://api.complyo.de'` |
| `backend/widgets/optout_center.js` | gleiche Logik, `currentScript` fallback |
| `backend/widgets/accessibility_smart.js` | gleiche Logik + `/v1` Suffix |
| `backend/widgets/cookie_consent.legacy.js` | `.tech` → `.de` (DEPRECATED file) |
| `backend/public/privacy-shield.js` | `apiUrl: 'https://api.complyo.de'` |
| `backend/public/cookie-blocker.js` | `apiUrl: 'https://api.complyo.de'` |

### nginx-production.conf
- CORS map: `.complyo.de` und `.complyo.tech` Domains hinzugefügt
- Neuer `api.complyo.de` Server-Block (primär)
- `api.complyo.tech` → 301 Redirect auf `api.complyo.de` (Backward-Compat)
- HTTP→HTTPS Redirect für beide Domains zusammengefasst

### gateway/nginx-static-proxy.conf (neu)
- `static.complyo.de` First-Party-Proxy
- `/assets/a.js` → accessibility widget
- `/assets/c.js` → cookie banner v2
- `/assets/o.js` → optout center
- Backward-Compat: `/widget/*` → `https://api.complyo.de/widgets/*`
