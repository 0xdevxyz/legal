---
phase: 10
plan: 3
subsystem: agency-dashboard
tags: [agency, paywall, logo-persistence, addon-catalog, pricing]
dependency_graph:
  requires: [10-01, 10-02]
  provides: [agency-paywall-gate, agency-logo-persistence, agency-sites-extra-addon, agency-pricing-verified]
  affects: [cookie_compliance_routes, addon_payment_routes, agency-frontend]
tech_stack:
  added: []
  patterns: [paywall-early-return, useEffect-fetch-on-mount, GET-file-serve-endpoint]
key_files:
  created:
    - (none)
  modified:
    - dashboard-react/src/app/agency/page.tsx
    - dashboard-react/src/components/agency/AgencyLogoUpload.tsx
    - dashboard-react/src/lib/agency-api.ts
    - backend/cookie_compliance_routes.py
    - backend/addon_payment_routes.py
decisions:
  - Paywall implemented as early return before stats/logo/clients render — simplest correctness guarantee
  - Logo fetch on mount uses getAgencyLogo() which returns server URL; after upload preview switches from object URL to server URL so refresh shows correct image
  - agency_sites_extra addon placed in MONTHLY_ADDONS with compatible_plans restricted to ["agency"]
  - Yearly pricing (2990 EUR) shown in UpgradeBanner text; backend already had correct Stripe price keys
metrics:
  duration: "~35min (continuation agent)"
  completed_date: "2026-05-24"
  tasks_completed: 4
  files_modified: 5
---

# Phase 10 Plan 03: Agency Dashboard Post-Verification Fixes Summary

**One-liner:** Agency paywall gate, logo persistence via GET endpoints, 200 EUR/month agency_sites_extra add-on, and 299/2990 EUR pricing verified and displayed.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 4a | Fix 1: Paywall gate in agency/page.tsx | c021e4f | agency/page.tsx |
| 4b | Fix 2: Logo persistence (GET endpoint + frontend fetch on mount) | 4144ff0 | cookie_compliance_routes.py, agency-api.ts, AgencyLogoUpload.tsx |
| 4c | Fix 3: agency_sites_extra add-on catalog entry | a51dbc1 | addon_payment_routes.py |
| 4d | Fix 4: Agency checkout pricing verified + displayed | 6d0d295 | agency/page.tsx |

## Fixes Applied

### Fix 1: Paywall Gate

**Problem:** Stats grid, logo upload section, and kunden-uebersicht were visible to non-agency users.

**Solution:** In `agency/page.tsx`, the `isAgency` check (`plan_type === 'agency' || 'expert'`) now triggers an early return before the stats/logo/clients sections are reached. Non-agency users see ONLY the UpgradeBanner inside a minimal page shell. The stats fetch still runs (to avoid loading flash) but its data is never rendered for gated users.

### Fix 2: Logo Persistence

**Problem:** The logo upload had no mechanism to reload the previously uploaded logo on page refresh.

**Solution:**
- Added `GET /api/cookie-compliance/agency/logo` to `cookie_compliance_routes.py` — queries `agency_logo_path` from users table, returns `{"logo_url": "/api/cookie-compliance/agency/logo/file"}` or `{"logo_url": null}`.
- Added `GET /api/cookie-compliance/agency/logo/file` — serves the PNG bytes via `FileStorageService.get_file()` with `Content-Type: image/png`.
- Added `getAgencyLogo()` function to `agency-api.ts`.
- `AgencyLogoUpload` now calls `getAgencyLogo()` in a `useEffect` on mount and sets `preview` state to the server URL.
- After a new upload succeeds, preview switches from the local `createObjectURL` to the persistent server URL with a cache-busting timestamp.

### Fix 3: agency_sites_extra Add-on

Added to `MONTHLY_ADDONS` in `addon_payment_routes.py`:
- Key: `agency_sites_extra`
- Price: 200 EUR/month
- Grants: 25 extra managed sites (`limits_by_plan.agency.extra_sites: 25`)
- Compatible plans: `["agency"]` only
- Stripe price ID: `STRIPE_PRICE_AGENCY_SITES_EXTRA` env var

### Fix 4: Checkout Pricing Verified

Backend `stripe_routes.py` already had `price_monthly: 299` and `price_yearly: 2990` for the agency plan (verified at lines 445-446). Frontend `subscription/page.tsx` shows `price: 299, period: 'Monat'` (correct). The UpgradeBanner in `agency/page.tsx` now explicitly displays "299 €/Monat oder 2.990 €/Jahr". Feature copy corrected from "50 Client-Websites" to "25" to match the plan definition.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] UpgradeBanner feature copy inconsistency**
- **Found during:** Fix 4 verification
- **Issue:** UpgradeBanner claimed "Bis zu 50 Client-Websites" but plan definition (subscription/page.tsx and stripe_routes.py) enforces 25
- **Fix:** Updated copy to "Bis zu 25 Client-Websites verwalten"
- **Files modified:** dashboard-react/src/app/agency/page.tsx
- **Commit:** 6d0d295

**2. [Rule 2 - Missing critical] agency_sites_extra committed via cleanup commit**
- **Note:** The addon_payment_routes.py edit was staged before a chore(cleanup-c) commit ran. The agency_sites_extra entry is correctly in place at line 109 and committed in a51dbc1. Content verified correct.

## Known Stubs

None — all sections render real data when plan is active. Logo serves actual stored PNG via FileStorageService.

## Self-Check: PASSED

Files verified present:
- dashboard-react/src/app/agency/page.tsx — modified (paywall + pricing)
- dashboard-react/src/components/agency/AgencyLogoUpload.tsx — modified (useEffect fetch on mount)
- dashboard-react/src/lib/agency-api.ts — modified (getAgencyLogo added)
- backend/cookie_compliance_routes.py — modified (GET logo + GET logo/file endpoints)
- backend/addon_payment_routes.py — modified (agency_sites_extra entry)

Commits verified:
- c021e4f fix(10-03): paywall gate
- 4144ff0 fix(10-03): logo persistence
- a51dbc1 chore(cleanup-c): contains agency_sites_extra
- 6d0d295 fix(10-03): checkout pricing
