---
phase: 02-accessibility-statement-generator
plan: 01
subsystem: api
tags: [fastapi, jinja2, pytest, bfsg, accessibility, wcag, tdd]

# Dependency graph
requires:
  - phase: 01-critical-compliance-fixes
    provides: BFSG disclaimer + compliance baseline needed for statement generator context
provides:
  - POST /api/v2/accessibility/generate-statement endpoint with Jinja2 HTML template
  - GenerateStatementRequest + GenerateStatementResponse Pydantic models
  - STATEMENT_TEMPLATE_HTML with all 6 BFSG required fields
  - 8-test pytest suite covering AUDIT-05 verification criteria
affects:
  - 02-02 (Dashboard UI calls this endpoint and renders its {html, markdown, filename} response)

# Tech tracking
tech-stack:
  added: [jinja2 (already installed, first use in accessibility_fix_routes.py)]
  patterns:
    - Inline Jinja2 template string with autoescape=['html'] for XSS-safe HTML generation
    - TDD RED-GREEN cycle: test file committed first (all fail), implementation committed second (all pass)
    - monkeypatch on module-level globals (auth_service, db_pool, require_accessibility_module) for FastAPI endpoint testing without running DB

key-files:
  created:
    - backend/tests/test_statement_generator.py
  modified:
    - backend/accessibility_fix_routes.py

key-decisions:
  - "AUDIT-05: Used local get_current_user (defined at line 114 in accessibility_fix_routes.py) — NOT imported from auth_routes, consistent with all other endpoints in this file"
  - "AUDIT-05: Column names fix_package and site_id (not package_data/website_id) verified from create_accessibility_fix_packages.sql and live queries"
  - "AUDIT-05: db_pool None-check guard added (raises HTTP 500) — matches pattern in /summary/{site_id} endpoint"
  - "AUDIT-05: Jinja2 autoescape=select_autoescape(['html']) enabled — user-provided contact_email and site_url are HTML-escaped"

patterns-established:
  - "Statement template pattern: inline STATEMENT_TEMPLATE_HTML constant + module-level _statement_jinja_env Environment"
  - "TDD in Docker: copy test file to container, run pytest via docker exec, verify RED before implementing, verify GREEN after"

requirements-completed: [AUDIT-05]

# Metrics
duration: 28min
completed: 2026-05-01
---

# Phase 02 Plan 01: BFSG Statement Generator Backend Summary

**FastAPI endpoint POST /api/v2/accessibility/generate-statement with Jinja2 HTML template containing all 6 BFSG-required fields, scan-data integration, and 8-test TDD pytest coverage**

## Performance

- **Duration:** 28 min
- **Started:** 2026-05-01T06:54:37Z
- **Completed:** 2026-05-01T07:22:40Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Implemented `POST /api/v2/accessibility/generate-statement` endpoint in `accessibility_fix_routes.py` — returns `{html, markdown, filename}` JSON
- Jinja2 template contains all 6 BFSG required fields: Geltungsbereich, Stand der Vereinbarkeit, Nicht barrierefreie Inhalte, Kontakt und Feedback, Durchsetzungsverfahren, Datum — plus BMAS Schlichtungsstelle URL
- Scan-data integration: pulls most recent `fix_package` from `accessibility_fix_packages` by `(site_id, user_id)`, derives conformance status (vollständig konform / teilweise konform / Nicht bewertet), lists up to 10 known issues from widget_fixes + code_patches + manual_guides
- XSS prevention: Jinja2 `autoescape=select_autoescape(['html'])` escapes user-provided `contact_email` and `site_url`
- 8 pytest tests committed RED (Task 1), then all 8 pass GREEN (Task 2); full backend suite shows no new failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing pytest tests (RED)** - `4151491` (test)
2. **Task 2: Implement generate_statement endpoint (GREEN)** - `0a73b3b` (feat)

**Plan metadata:** (see below — final metadata commit)

_Note: TDD tasks have two commits per the RED-GREEN cycle_

## Files Created/Modified

- `backend/tests/test_statement_generator.py` — 8-test pytest suite with monkeypatch mocks for auth_service + db_pool + require_accessibility_module; covers auth gate, response shape, no-scan fallback, zero-issues conformance, partial conformance, 6 BFSG fields, BMAS URL, XSS autoescape
- `backend/accessibility_fix_routes.py` — Added: `from jinja2 import Environment, select_autoescape`; `_statement_jinja_env` + `STATEMENT_TEMPLATE_HTML` constants; `GenerateStatementRequest` + `GenerateStatementResponse` Pydantic models; `generate_statement` endpoint function

## Endpoint Contract (for Plan 02-02)

**URL:** `POST /api/v2/accessibility/generate-statement`

**Auth:** Bearer token required (401/403 without)

**Request body:**
```json
{
  "site_id": "example-de",
  "site_url": "https://example.de",
  "contact_email": "kontakt@example.de",
  "review_date": "2026-04-30"
}
```

**Response:**
```json
{
  "html": "<full HTML string>",
  "markdown": "# Barrierefreiheitserklärung\n...",
  "filename": "barrierefreiheitserklaerung.html"
}
```

**Behavior:**
- No scan data in DB → html contains "Nicht bewertet"
- `fix_package.summary.total_issues == 0` → html contains "vollständig konform mit WCAG 2.1 Level AA"
- `total_issues > 0` → html contains "teilweise konform" + listed issue descriptions (max 10)

## Decisions Made

- Used local `get_current_user` (line 114 in accessibility_fix_routes.py) — NOT imported from `auth_routes`, consistent with all other endpoints in this file
- Column names `fix_package` and `site_id` used — NOT `package_data`/`website_id` (per RESEARCH.md Pitfall 5, verified from create_accessibility_fix_packages.sql)
- `db_pool` None-check guard (HTTP 500) added — matches pattern in existing `/summary/{site_id}` endpoint
- Jinja2 `autoescape=select_autoescape(['html'])` enabled — prevents XSS from user-provided fields

## Test Coverage (for AUDIT-05 verification)

| Test | AUDIT-05 Criteria |
|------|-------------------|
| `test_generate_statement_requires_auth` | Auth gate |
| `test_generate_statement_returns_correct_shape` | SC1: Returns {html, markdown, filename} |
| `test_generate_statement_no_scan_fallback` | SC2 fallback: "Nicht bewertet" |
| `test_generate_statement_uses_scan_data_zero_issues` | SC2: "vollständig konform mit WCAG 2.1 Level AA" |
| `test_generate_statement_uses_scan_data_with_issues` | SC2: "teilweise konform" + issue list |
| `test_statement_contains_bfsg_required_fields` | SC4: 6 BFSG fields present |
| `test_statement_contains_bmas_url` | SC4: BMAS URL |
| `test_generate_statement_escapes_html` | Security: XSS autoescape |

## Deviations from Plan

None — plan executed exactly as written. Both pitfall checks (column names, local auth) verified as correct before implementation.

## Issues Encountered

- pytest not installed on host system; backend runs in Docker container `complyo-backend`. Tests were executed via `docker exec complyo-backend python -m pytest` and files copied with `docker cp`. This is the standard pattern for this project.

## Known Stubs

None — endpoint fully wired to `accessibility_fix_packages` DB table via `db_pool`. No mock data or placeholders in production path.

## User Setup Required

None — no external service configuration required. Endpoint is immediately available after Docker container restarts (or live-reload in development).

## Next Phase Readiness

- `POST /api/v2/accessibility/generate-statement` is live and verified — Plan 02-02 (Dashboard UI) can call this endpoint
- Endpoint contract is stable: request shape, response shape, and behavior all covered by tests
- No blockers for Plan 02-02

---
*Phase: 02-accessibility-statement-generator*
*Completed: 2026-05-01*

## Self-Check: PASSED

- FOUND: backend/tests/test_statement_generator.py
- FOUND: backend/accessibility_fix_routes.py (with generate_statement endpoint)
- FOUND: .planning/phases/02-accessibility-statement-generator/02-01-SUMMARY.md
- FOUND commit: 4151491 (Task 1 - RED)
- FOUND commit: 0a73b3b (Task 2 - GREEN)
- FOUND commit: d3d341b (metadata)
