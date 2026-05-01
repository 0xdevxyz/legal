---
phase: 02-accessibility-statement-generator
plan: 02
subsystem: ui
tags: [react, nextjs, tailwind, lucide-react, blob-download, window-print, bfsg, accessibility]

# Dependency graph
requires:
  - phase: 02-accessibility-statement-generator
    plan: 01
    provides: POST /api/v2/accessibility/generate-statement returning {html, markdown, filename}
provides:
  - Next.js App Router page /accessibility/statement
  - StatementGenerator React component (form + API call + live iframe preview + HTML download + PDF export)
  - Barrel export in dashboard-react/src/components/accessibility/index.ts
affects:
  - Future navigation plans (nav link to /accessibility/statement not yet added — see Known Stubs)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Blob+anchor download pattern (consistent with ComplianceIssueCard.tsx — createObjectURL + revokeObjectURL)
    - PDF export via window.open + document.write + window.print() — zero new npm dependencies
    - Sandboxed iframe preview (sandbox="" attribute on srcDoc iframe for defense in depth)
    - Client-side URL-to-siteId validation via generateSiteId + isValidSiteId before API call

key-files:
  created:
    - dashboard-react/src/components/accessibility/StatementGenerator.tsx
    - dashboard-react/src/app/accessibility/statement/page.tsx
  modified:
    - dashboard-react/src/components/accessibility/index.ts

key-decisions:
  - "AUDIT-05 SC3: Used window.print() for PDF export (not jsPDF/html2pdf) — consistent with RESEARCH.md recommendation, zero new dependencies"
  - "AUDIT-05 SC3: Preview iframe uses sandbox='' attribute — backend uses Jinja2 autoescape but defense in depth is cheap"
  - "AUDIT-05 SC3: Nav link to /accessibility/statement deferred — not in plan scope, documented in Known Stubs for follow-up"

patterns-established:
  - "New dashboard page pattern: thin 'use client' page component wrapping a self-contained feature component"
  - "Blob download: always use createObjectURL + revokeObjectURL pattern from ComplianceIssueCard.tsx"

requirements-completed: [AUDIT-05]

# Metrics
duration: 12min
completed: 2026-05-01
---

# Phase 02 Plan 02: BFSG Statement Generator Dashboard UI Summary

**Next.js page at /accessibility/statement with StatementGenerator component: form (siteUrl, contactEmail, reviewDate) → POST /api/v2/accessibility/generate-statement → sandboxed iframe preview → Blob HTML download + window.print() PDF export**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-01T09:20:18Z
- **Completed:** 2026-05-01T09:32:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Built `StatementGenerator.tsx` — self-contained React component with form, apiClient POST call, live preview iframe, HTML download (Blob+anchor), and PDF export (window.print)
- Created `/accessibility/statement` Next.js App Router page at `src/app/accessibility/statement/page.tsx`
- Appended `StatementGenerator` default export to accessibility barrel `index.ts`
- TypeScript compiles cleanly (exit 0, zero errors on new files and full project)
- Zero new npm dependencies introduced
- AUDIT-05 SC3 satisfied: Dashboard now shows Generator-UI with Formular → Preview → Download flow

## Task Commits

Each task was committed atomically:

1. **Task 1: Build StatementGenerator React component** - `48a7086` (feat)
2. **Task 2: Create Next.js App Router page** - `bef3a44` (feat)

**Plan metadata:** (see below — final metadata commit)

## Files Created/Modified

- `dashboard-react/src/components/accessibility/StatementGenerator.tsx` — 'use client' React component with form (siteUrl required, contactEmail optional, reviewDate), calls POST /api/v2/accessibility/generate-statement via apiClient, renders response in sandboxed iframe, HTML download via Blob+anchor, PDF via window.print()
- `dashboard-react/src/app/accessibility/statement/page.tsx` — Thin wrapper page, 'use client', default export AccessibilityStatementPage, `<main>` landmark with bg-gray-50, imports StatementGenerator
- `dashboard-react/src/components/accessibility/index.ts` — Added `export { default as StatementGenerator } from './StatementGenerator'`

## Page Route

**URL:** `/accessibility/statement`

**Component public surface:** `StatementGenerator` takes no props — fully self-contained.

**How users reach the page:** Currently no nav link in the dashboard sidebar. Users must navigate directly to the URL. A nav link addition is deferred (not in plan scope — see Known Stubs).

## AUDIT-05 Completion Status

| Criterion | Plan | Status |
|-----------|------|--------|
| SC1: Returns {html, markdown, filename} | 02-01 | Done (backend) |
| SC2: Scan data integration + fallback | 02-01 | Done (backend) |
| SC3: Dashboard UI: Formular → Preview → Download | 02-02 | Done (this plan) |
| SC4: All 6 BFSG required fields in template | 02-01 | Done (backend) |

AUDIT-05 is fully satisfied: all 4 success criteria covered across Plans 02-01 and 02-02.

## Decisions Made

- Used `window.print()` for PDF export (not jsPDF/html2pdf) — RESEARCH.md confirms this is the project standard; keeps zero new dependencies
- Preview iframe uses `sandbox=""` attribute — Jinja2 autoescape on the backend already prevents XSS, but a sandboxed iframe is cheap defense in depth
- Navigation link to `/accessibility/statement` was NOT added — out of scope for this plan; documented in Known Stubs below

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- `npx tsc --noEmit` resolves to a stub/wrapper on this system (returns "This is not the tsc command you are looking for"). TypeScript check was performed via `./dashboard-react/node_modules/.bin/tsc --noEmit -p dashboard-react/tsconfig.json` from the repo root — exit code 0.

## Known Stubs

**Navigation link to /accessibility/statement not added**
- **Files:** No dashboard nav/sidebar file modified
- **Reason:** RESEARCH.md Pitfall 4 identified this as a deferred item; adding a nav link was explicitly out of scope for Plan 02-02 per the plan output section
- **Resolution:** A future plan (or quick fix) should add a link in the dashboard navigation to surface this page to users. Without a nav link, users must know to navigate directly to `/accessibility/statement`.

## User Setup Required

None — the page and component are immediately available when the Next.js dev server or production build runs.

## Next Phase Readiness

- Phase 02 complete: backend (Plan 02-01) + Dashboard UI (Plan 02-02) deliver end-to-end Barrierefreiheitserklärung-Generator
- AUDIT-05 fully satisfied across both plans
- No blockers for Phase 03+

---
*Phase: 02-accessibility-statement-generator*
*Completed: 2026-05-01*
