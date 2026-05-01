---
phase: 01-critical-compliance-fixes
plan: "02"
subsystem: backend-cookie-compliance, nginx-infrastructure
tags: [AUDIT-03, AUDIT-04, DSGVO, HSTS, security-headers, UA-truncation]
dependency_graph:
  requires: ["01-01"]
  provides: ["DSGVO-compliant consent logs", "HSTS on all 4 HTTPS server blocks"]
  affects: ["backend/cookie_compliance_routes.py", "/etc/nginx/sites-available/complyo.de"]
tech_stack:
  added: ["pytest unit tests for truncate_user_agent"]
  patterns: ["priority-based regex match for UA detection", "server-block-level nginx security headers"]
key_files:
  created:
    - backend/tests/test_ua_truncation.py
    - nginx/complyo.de
  modified:
    - backend/cookie_compliance_routes.py
    - /etc/nginx/sites-available/complyo.de
decisions:
  - "Used findall+priority-index instead of re.search because Edge/OPR/CriOS tokens appear AFTER Chrome in the UA string — re.search finds leftmost match regardless of alternation order"
  - "Placed security headers at server-block level (not inside location blocks) to avoid inheritance shadowing per nginx pitfall"
  - "Kept HTTP redirect blocks (port 80) header-free — HSTS over HTTP is ignored by spec"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-01T00:14:43Z"
  tasks_completed: 2
  files_changed: 4
---

# Phase 01 Plan 02: UA Truncation + HSTS Security Headers Summary

DSGVO-compliant user-agent truncation added to consent logs and HSTS preload-ready security headers deployed to all 4 live nginx HTTPS server blocks.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | AUDIT-03: truncate_user_agent helper + 11 unit tests | ddc11f5 | backend/cookie_compliance_routes.py, backend/tests/test_ua_truncation.py |
| 2 | AUDIT-04: HSTS + security headers in nginx live config | 28d6a60 | /etc/nginx/sites-available/complyo.de, nginx/complyo.de |

## New Helper: truncate_user_agent

**Import path:** `from cookie_compliance_routes import truncate_user_agent`

**Signature:**
```python
def truncate_user_agent(ua_string) -> str:
    """Returns 'Browser/MajorVersion' (e.g. 'Chrome/120') or 'unknown'."""
```

**Location in file:** `backend/cookie_compliance_routes.py`, immediately after `hash_ip_address()` in the Helper Functions section (~line 233).

**Call site:** `log_consent()` endpoint — replaces the old `[:500]` raw UA slice with `truncate_user_agent(raw_ua)` before DB insert.

## Test File

**Path:** `backend/tests/test_ua_truncation.py`

**Tests passing:** 11 / 11

```
tests/test_ua_truncation.py::test_empty_returns_unknown PASSED
tests/test_ua_truncation.py::test_none_returns_unknown PASSED
tests/test_ua_truncation.py::test_chrome_ua PASSED
tests/test_ua_truncation.py::test_firefox_ua PASSED
tests/test_ua_truncation.py::test_edge_ua_matches_edge_not_chrome PASSED
tests/test_ua_truncation.py::test_opera_ua PASSED
tests/test_ua_truncation.py::test_mobile_chrome_ios PASSED
tests/test_ua_truncation.py::test_safari_macos PASSED
tests/test_ua_truncation.py::test_curl_unknown PASSED
tests/test_ua_truncation.py::test_custom_bot_unknown PASSED
tests/test_ua_truncation.py::test_result_is_short PASSED
======================== 11 passed, 1 warning in 0.62s =========================
```

## Live Security Headers (api.complyo.de)

```
curl -s -I https://api.complyo.de/health
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

All 5 security headers confirmed live on `api.complyo.de`. Same headers present in all 4 HTTPS server blocks (`complyo.de`, `app.complyo.de`, `api.complyo.de`, `dashboard.complyo.de`).

## Backup Location

Pre-change nginx config backed up to: `/etc/nginx/sites-available/complyo.de.bak.20260430`

## AUDIT-03 + AUDIT-04 Truths Now Achievable

- **AUDIT-03 T1:** New consent logs store only `'Browser/Version'` (e.g. `'Chrome/120'`) — old `[:500]` raw UA slice is removed.
- **AUDIT-03 T2:** `truncate_user_agent()` returns correct format for Chrome, Firefox, Safari, Edge, Opera, CriOS — and `'unknown'` for curl/bots — confirmed by 11 passing unit tests.
- **AUDIT-04 T1:** `curl -s -I https://api.complyo.de` returns `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`.
- **AUDIT-04 T2:** `nginx -t` confirms config syntactically correct and `systemctl reload nginx` completes without error.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Priority-based regex match to fix Edge/OPR ordering**
- **Found during:** Task 1, GREEN phase (2 failing tests: test_edge_ua_matches_edge_not_chrome, test_opera_ua)
- **Issue:** The plan's `re.search()` approach finds the leftmost token in the string. Edge UAs place `Chrome/120` before `Edg/120` in the string — `re.search()` would return Chrome even though the regex alternation lists Edg first. Same issue for OPR.
- **Fix:** Replaced `re.search()` with `re.findall()` + priority-index selection. All tokens are found and the one with the highest priority rank (lowest index in the priority list) is selected. This correctly returns `Edge/120` for Edge UAs and `OPR/106` for Opera UAs.
- **Files modified:** `backend/cookie_compliance_routes.py` (truncate_user_agent function body)
- **Commit:** ddc11f5 (included in same task commit)

## Known Stubs

None — all plan goals are fully implemented and verified live.

## Self-Check: PASSED

- test_ua_truncation.py: FOUND
- cookie_compliance_routes.py: FOUND (truncate_user_agent defined + wired)
- nginx/complyo.de: FOUND (live + in repo)
- nginx backup: FOUND (/etc/nginx/sites-available/complyo.de.bak.20260430)
- Commit ddc11f5 (Task 1): FOUND
- Commit 28d6a60 (Task 2): FOUND
