# Dashboard-Fix Session — 2026-05-15

**Repo:** `/home/clawd/saas/legal`
**Ziel:** Alle kritischen Dashboard-Fehler (403/500/Redirects/PDF/Widget) beheben.

## Issue-Status

| # | Issue | Datei | Status |
|---|-------|-------|--------|
| 1 | POST /api/v2/analyze → 500 | backend/main_production.py | ✅ Behoben |
| 2 | GET /api/cookie-compliance/my-config → 500 | backend/cookie_compliance_routes.py | ✅ Behoben |
| 3 | GET /api/v2/websites → 403 | backend/website_routes.py | ✅ Behoben |
| 4 | GET /api/ai/systems → 403 | dashboard-react ai-compliance/page.tsx | ✅ Bereits handled (→ /upgrade) |
| 5 | GET /api/ai/stats → 403 | lib/ai-compliance-api.ts | ✅ Logging entfernt |
| 6 | GET /api/addons/my-addons → 403 | lib/ai-compliance-api.ts | ✅ Graceful 403 |
| 7 | Widget TypeError: null.hidden | backend/widgets/accessibility-v6.js | ✅ Behoben |
| 8 | Cookie Compliance Freischalten → Redirect | dashboard-react/cookie-compliance/page.tsx | ✅ Direkter Checkout |
| 9 | Agency Plan aktivieren → Redirect | dashboard-react/agency/page.tsx | ✅ Direkter Checkout |
| 10 | Abo & Rechnungen nicht aufrufbar | dashboard-react/subscription/page.tsx | ✅ Auth-Fix |
| 11 | Legal Updates nicht geladen | components/dashboard/LegalNews.tsx | ✅ apiClient + Auth |
| 12 | PDF-Export schlägt fehl | components/dashboard/WebsiteAnalysis.tsx | ✅ localhost→API_URL |

## DB-Schema Baseline (2026-05-15)

- `users.id` = **INTEGER** (nextval sequence)
- `scan_history.user_id` = **INTEGER**
- `cookie_banner_configs.user_id` = **INTEGER**
- `cookie_banner_configs` hat `scan_completed_at`, `last_scan_url`, `custom_logo_url` ✅ (bereits vorhanden)
- JWT-Claims enthalten `id` als **String** → INT-Cast nötig

## Root Causes (Zusammenfassung)

1. **Auth-Token-Inkonsistenz**: Frontend nutzt `window.__complyo_access_token`, `localStorage`, `safeStorage` parallel
2. **Hardcoded localhost:8002** in PDF-Export (nur für `complyo.tech`, nicht `complyo.de`)
3. **`int(current_user["id"])` schlägt fehl** wenn JWT `id`-Claim leer oder kein Integer
4. **UX**: Plan-Aktivierungs-Buttons navigieren nur zu `/subscription` statt direktem Checkout
5. **Widget**: `check.hidden` ohne Null-Guard
