# Smoke Test Results — 2026-05-23

## Goal
Verify that after login, the dashboard loads WITHOUT 401 console errors on
`/api/v2/websites`, `/api/v2/dashboard/metrics`, `/api/legal-notifications/stats`.

## Steps Executed
1. PWCLI set to `$HOME/.verdent/skills/playwright/scripts/playwright_cli.sh`
2. Opened `https://app.complyo.de/login`
3. Filled email `mail@panoart360.de` and password `Panoart2026!`, clicked "Anmelden"
4. Waited 4 seconds
5. Took snapshot + screenshot → `/tmp/smoke_auth_fix.png`
6. Retrieved console logs (`"$PWCLI" console`)
7. Navigated to `https://app.complyo.de/subscription`, waited 3 s, snapshot + screenshot → `/tmp/smoke_subscription_fix.png`
8. Closed browser

---

## Results

### Current URL after login
`https://app.complyo.de/` — **Dashboard reached successfully.**
Page title: "Complyo Dashboard - KI-gestützte Website-Compliance"

### Loading spinner / skeleton visible?
No spinner or skeleton visible after 4 seconds. The full dashboard rendered including:
- Sidebar navigation (Dashboard, Cookie-Compliance, Barrierefreiheit, AI-Compliance, Dokumente, Agentur)
- Domain hero section showing `https://complyo.de`
- Optimierungsprozess widget (5 steps, step 1 expanded)
- Compliance Score gauge
- Metrics cards
- Legal News feed (3 articles)
- Cookie-Compliance management block

### 401 / Unauthorized / API errors?
**NONE.**
- Total console messages on dashboard: **42 (Errors: 0, Warnings: 1)**
- Zero errors mentioning 401, Unauthorized, getTrackedWebsites, or "API Response Error"
- The single warning was an autocomplete attribute hint from the login form (not an API error)

### Compliance score visible and non-zero?
Score is visible: **0/100** labelled "Kritisch".
The score is zero because the tracked website (`https://complyo.de`) has not yet been fully scanned/fixed — this is expected data state, not a rendering failure. The gauge, sub-scores (DSGVO 0, Cookie 0, Barriere 0) and all metric cards rendered correctly.

### Subscription page — any error messages?
**No errors.** Page loaded cleanly at `https://app.complyo.de/subscription`.
Console on subscription page: **16 messages (Errors: 0, Warnings: 0)** — all from the Complyo cookie-compliance widget, no API errors.
Page content: Current plan shown as "Unbekannt / Kostenlos" with full pricing table (Einzelne Säule 19€, Pro-Paket 49€, Agentur 299€).

### Full console error list
**Zero console errors across both pages.**

Dashboard page (42 messages, 0 errors, 1 warning):
- [WARNING] autocomplete attribute hint on login form input (from login page, not dashboard)
- All other messages: Complyo widget init logs + app debug logs (📊, 🔍, ✅ prefixes)

Subscription page (16 messages, 0 errors, 0 warnings):
- All messages: Complyo cookie-compliance widget init sequence only

---

## Summary
All three targeted API endpoints (`/api/v2/websites`, `/api/v2/dashboard/metrics`, `/api/legal-notifications/stats`) returned no 401 errors in the browser console. Authentication is working correctly. The dashboard and subscription page both load without any Unauthorized or API Response Error messages.
