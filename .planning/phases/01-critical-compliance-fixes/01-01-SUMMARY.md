---
phase: 01-critical-compliance-fixes
plan: 01
subsystem: ui
tags: [react, tailwind, lucide-react, compliance, bfsg, tcf, cookie-banner]

# Dependency graph
requires: []
provides:
  - BfsgDisclaimer.tsx shared component with BFSG deadline text ("28. Juni 2025") and Forward-Looking Compliance messaging
  - All 3 active AB-test landing variants (67% + 17% + 16% traffic) render the BFSG disclaimer unconditionally
  - TCF 2.2 feature in dashboard marked "Coming Soon" with gray styling (no longer "Beta")
  - cookie_banner_v2.js __tcfapi stub documented as opt-in only with AUDIT-02 traceability
affects: [future-landing-variants, cookie-compliance-dashboard, 01-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared landing page component pattern: create BfsgDisclaimer.tsx in /components, import in each variant — DRY across AB variants"
    - "TCF badge lifecycle: Beta -> Coming Soon -> (future) Active, using badge/badgeColor feature-flag fields in AdvancedSettings features array"

key-files:
  created:
    - landing-react/src/components/BfsgDisclaimer.tsx
  modified:
    - landing-react/src/components/ProfessionalLanding.tsx
    - landing-react/src/components/ComplyoOriginalLanding.tsx
    - landing-react/src/components/ComplyoHighConversionLanding.tsx
    - dashboard-react/src/components/cookie-compliance/AdvancedSettings.tsx
    - dashboard-react/src/components/cookie-compliance/TCFManager.tsx
    - backend/widgets/cookie_banner_v2.js

key-decisions:
  - "BfsgDisclaimer placed as first visible element in each variant's return JSX (before HeroSection / first content block) — not in footer, not conditional"
  - "In ComplyoHighConversionLanding (dark bg-gray-900), BfsgDisclaimer renders before <header> to ensure top-of-page visibility"
  - "TCF stub in cookie_banner_v2.js retained as-is (no functional change) — only documentation comments added per CONTEXT.md locked decision"
  - "STATUS: Coming Soon comment added at both the data-tcf gate (line ~193) and above initTCF() definition — satisfies grep check for 2 occurrences"

patterns-established:
  - "Pattern: Shared compliance component in /components root, imported by all active AB variants"
  - "Pattern: Feature badge field in AdvancedSettings features array controls both tab badge and downstream manager header badge"

requirements-completed: [AUDIT-01, AUDIT-02]

# Metrics
duration: 3min
completed: 2026-05-01
---

# Phase 01 Plan 01: Critical Compliance Fixes (BFSG + TCF) Summary

**Shared BfsgDisclaimer component wired into all 3 active landing variants (100% of traffic), and TCF 2.2 rebranded from "Beta" to "Coming Soon" in dashboard + widget documentation comments**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-01T00:04:27Z
- **Completed:** 2026-05-01T00:07:00Z
- **Tasks:** 3
- **Files modified:** 6 (+ 1 created)

## Accomplishments
- Created `BfsgDisclaimer.tsx`: amber alert box with `role="alert"`, `data-testid="bfsg-disclaimer"`, BFSG deadline text ("BFSG-Deadline war der 28. Juni 2025"), Forward-Looking Compliance note, Retroaktiv-Zertifizierung disclaimer
- Wired `<BfsgDisclaimer />` unconditionally into ProfessionalLanding (67%), ComplyoOriginalLanding (17%), ComplyoHighConversionLanding (16%) — all active AB-test variants covered
- AdvancedSettings.tsx TCF entry: `badge: 'Coming Soon'`, `badgeColor: 'bg-gray-500'` (was "Beta" yellow)
- TCFManager.tsx header badge: gray-500/20 styling + "Coming Soon" text
- cookie_banner_v2.js: 6-line STATUS comment above data-tcf gate + 1-line comment above initTCF() — 2 occurrences of "STATUS: Coming Soon", 2 occurrences of "AUDIT-02" for traceability

## Task Commits

Each task was committed atomically:

1. **Task 1: Create shared BfsgDisclaimer component** - `218eb61` (feat)
2. **Task 2: Wire BfsgDisclaimer into all 3 active landing variants** - `40f07ed` (feat)
3. **Task 3: TCF 2.2 "Coming Soon" + widget comments** - `9b5aa30` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `landing-react/src/components/BfsgDisclaimer.tsx` - New shared component: amber alert box with BFSG deadline and Forward-Looking messaging
- `landing-react/src/components/ProfessionalLanding.tsx` - Added import + `<BfsgDisclaimer />` before `<HeroSection />`
- `landing-react/src/components/ComplyoOriginalLanding.tsx` - Added import + `<BfsgDisclaimer />` before inline `<HeroSection />`
- `landing-react/src/components/ComplyoHighConversionLanding.tsx` - Added import + `<BfsgDisclaimer />` as first child before `<header>`
- `dashboard-react/src/components/cookie-compliance/AdvancedSettings.tsx` - TCF entry badge: 'Beta' -> 'Coming Soon', badgeColor: 'bg-yellow-500' -> 'bg-gray-500'
- `dashboard-react/src/components/cookie-compliance/TCFManager.tsx` - Header Badge: yellow -> gray styling, text "Beta" -> "Coming Soon"
- `backend/widgets/cookie_banner_v2.js` - STATUS comments above data-tcf gate (6 lines) and above initTCF() (1 line)

## Decisions Made
- Used `./BfsgDisclaimer` relative import path (all 3 variant files reside in `landing-react/src/components/`) — no path alias needed
- In ComplyoOriginalLanding, inserted `<BfsgDisclaimer />` between `<Navigation />` and `<HeroSection />` (the outer return block, line ~1810) — `HeroSection` is a locally-defined functional component but rendered from the same return block
- TCF stub function body preserved unchanged — only comments added (locked decision: mark as no-op, do not remove)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. TypeScript compiled without errors on both landing-react and dashboard-react after changes.

## Traceability

Exact strings inserted (for downstream grep/verifier use):

| File | String | Purpose |
|------|--------|---------|
| BfsgDisclaimer.tsx | `BFSG-Deadline war der 28. Juni 2025` | AUDIT-01 truth: deadline visible |
| BfsgDisclaimer.tsx | `Forward-Looking Compliance` | AUDIT-01 truth: forward-looking value prop |
| BfsgDisclaimer.tsx | `Retroaktiv-Zertifizierung` | AUDIT-01 truth: no retroactive certification |
| AdvancedSettings.tsx | `badge: 'Coming Soon'` | AUDIT-02 truth: TCF tab badge |
| AdvancedSettings.tsx | `badgeColor: 'bg-gray-500'` | AUDIT-02 truth: gray styling |
| TCFManager.tsx | `Coming Soon` | AUDIT-02 truth: manager header badge |
| TCFManager.tsx | `bg-gray-500/20` | AUDIT-02 truth: gray styling |
| cookie_banner_v2.js | `STATUS: Coming Soon` (x2) | AUDIT-02 truth: stub documented |
| cookie_banner_v2.js | `AUDIT-02` (x2) | Traceability to audit finding |

## User Setup Required

None - no external service configuration required. Browser smoke check recommended:
- Visit `/?variant=professional`, `/?variant=original`, `/?variant=high-conversion` on landing page — BFSG disclaimer visible at top of each variant
- Open Dashboard -> Cookie Compliance -> Advanced Settings -> TCF 2.2 tab — grey "Coming Soon" badge visible

## Next Phase Readiness
- AUDIT-01 and AUDIT-02 truths are now achievable
- Plan 01-02 (AUDIT-03 UA truncation + AUDIT-04 nginx STS header) can proceed independently — no dependencies on this plan

---
*Phase: 01-critical-compliance-fixes*
*Completed: 2026-05-01*
