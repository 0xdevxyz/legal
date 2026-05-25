---
phase: 10-agentur-kanal-stufe-1
plan: "01"
subsystem: backend
tags: [agency, cookie-compliance, fastapi, postgresql, tdd, file-upload]
dependency_graph:
  requires: []
  provides: [AGENCY-01-endpoint, AGENCY-02-endpoint, AGENCY-03-endpoint, agency-client-migration]
  affects: [backend/cookie_compliance_routes.py, backend/migrations/, backend/tests/]
tech_stack:
  added: []
  patterns: [TDD red-green, asyncpg UPDATE 0 ownership check, FastAPI UploadFile PNG-only]
key_files:
  created:
    - backend/migrations/add_agency_client_fields.sql (21 lines)
    - backend/tests/conftest.py (14 lines)
    - backend/tests/test_agency.py (264 lines)
  modified:
    - backend/cookie_compliance_routes.py (+156 lines, 2669 total)
decisions:
  - "No require_module gating on agency endpoints — matches existing /agency/stats pattern; module gating deferred to follow-up phase"
  - "s.site_id column reference (not s.site_identifier) — matches working /agency/stats query to avoid live-DB schema bug"
  - "PNG validation by content_type only (not magic bytes) — pragmatic for Phase 10 Stufe 1 scope"
metrics:
  duration: "~20min"
  completed_date: "2026-05-24"
  tasks_completed: 3
  files_changed: 4
---

# Phase 10 Plan 01: Agency Channel Stufe 1 — Backend Foundation Summary

One-liner: FastAPI agency endpoints for per-site client attribution (PATCH), grouped client list (GET), and PNG logo upload (POST) backed by idempotent asyncpg migration adding 3 columns and 1 partial index.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | TDD RED — failing pytest tests + conftest | 1e33bd2 | backend/tests/test_agency.py, backend/tests/conftest.py |
| 2 | DB migration for client fields + logo path | 23a0940 | backend/migrations/add_agency_client_fields.sql |
| 3 | TDD GREEN — three endpoints implemented | 3f0877f | backend/cookie_compliance_routes.py |

## Files Created / Modified

| File | Action | Lines |
|------|--------|-------|
| backend/migrations/add_agency_client_fields.sql | Created | 21 |
| backend/tests/conftest.py | Created | 14 |
| backend/tests/test_agency.py | Created | 264 |
| backend/cookie_compliance_routes.py | Modified | +156 (2669 total) |

## SQL Columns Added

| Table | Column | Type | Notes |
|-------|--------|------|-------|
| cookie_banner_configs | client_name | VARCHAR(255) | Agency client display name |
| cookie_banner_configs | client_email | VARCHAR(255) | Agency client contact email |
| users | agency_logo_path | TEXT | Relative path to PNG logo file |
| (index) | idx_banner_config_user_client | PARTIAL | ON (user_id, client_name) WHERE client_name IS NOT NULL |

## Endpoints Registered

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| PATCH | /api/cookie-compliance/agency/sites/{site_id}/client | assign_client_to_site | Assign client_name + client_email; returns 404 on unowned site |
| GET | /api/cookie-compliance/agency/clients | get_agency_clients | Grouped client list with site_count + acceptance_rate |
| POST | /api/cookie-compliance/agency/logo | upload_agency_logo | PNG-only, 2MB limit, stores path in users.agency_logo_path |

## Test Results

All 8 tests in `backend/tests/test_agency.py` pass GREEN:

- test_assign_client (PATCH 200 + db_pool.execute called with UPDATE)
- test_assign_client_not_found (PATCH 404 on UPDATE 0)
- test_get_agency_clients (GET grouped response with acceptance_rate)
- test_clients_excludes_null (SQL contains `c.client_name IS NOT NULL`)
- test_logo_upload_png_ok (PNG accepted, agency_logo_path updated)
- test_logo_upload_svg_rejected (SVG returns 400 with PNG mention)
- test_logo_upload_jpeg_rejected (JPEG returns 400)
- test_logo_upload_too_large (>2MB returns 400 with size mention)

No regressions in other test files caused by these changes.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All endpoints are fully wired. Migration is idempotent SQL ready for manual `psql` execution.

## Self-Check: PASSED
