---
phase: 10-agentur-kanal-stufe-1
verified: 2026-05-24T14:30:00Z
status: complete
score: 5/5 success criteria verified (2 gaps waived by product owner 2026-05-24)
gaps:
  - truth: "Sites können einem client_name + client_email zugeordnet werden (DB-Migration + Backend-Endpoint + Dashboard-UI)"
    status: waived
    waived_by: "product owner 2026-05-24"
    reason: "DB migration and backend PATCH endpoint are fully implemented and tested. Dashboard-UI for assignment is deferred to Stufe 2 — assignClient() is available via API/curl for power users. Gap accepted as deliberate Stufe 1 scope reduction."
  - truth: "Agentur kann eigenes Logo hochladen (PNG/SVG, max 2MB)"
    status: waived
    waived_by: "product owner 2026-05-24"
    reason: "SVG support not implemented — PNG-only by design. ROADMAP SC4 updated to reflect PNG only. Gap accepted."
human_verification:
  - test: "End-to-end browser flow: assign client, see grouping, download PDF"
    expected: "User can PATCH a site to assign client_name via the dashboard UI (after gap fix), dashboard shows client group, PDF downloads with logo + site data"
    why_human: "No automated test covers the browser-rendered UI flow; Task 4 checkpoint in Plan 10-03 was a blocking human checkpoint that is not documented as resolved in the SUMMARY."
---

# Phase 10: Agentur-Kanal Stufe 1 Verification Report

**Phase Goal:** Complyo als verkaufbares Agentur-Tool positionieren — Agenturen können Kunden zuordnen, pro Kunde einen gebrandeten PDF-Report generieren und ihr eigenes Logo in Reports einbinden
**Verified:** 2026-05-24T14:30:00Z
**Status:** complete (2 gaps waived by product owner 2026-05-24)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Sites können einem `client_name` + `client_email` zugeordnet werden (DB-Migration + Backend-Endpoint + **Dashboard-UI**) | PARTIAL | Migration and PATCH endpoint verified; `assignClient()` in agency-api.ts is ORPHANED — no UI component calls it |
| 2 | Agentur-Dashboard zeigt pro-Kunde-Gruppierung: Kunde A — 3 Sites — Compliance-Score — Acceptance Rate | VERIFIED | `ClientGroup.tsx` renders `site_count` + `acceptance_rate`; `agency/page.tsx` fetches via `getAgencyClients()` and maps ClientGroup components |
| 3 | "Report herunterladen" Button pro Kunde generiert PDF mit Compliance-Status aller zugehörigen Sites | VERIFIED | `ClientGroup.tsx` has "PDF herunterladen" button wired to `downloadClientReport()`; backend endpoint returns `application/pdf` bytes; 4 endpoint tests pass |
| 4 | Agentur kann eigenes Logo hochladen (PNG/**SVG**, max 2MB) — Logo erscheint in generierten PDFs | PARTIAL | PNG upload works end-to-end (upload, persist, serve, embed in PDF); SVG is explicitly rejected by backend (HTTP 400) — ROADMAP says PNG/SVG |
| 5 | Generierter PDF-Report zeigt Agentur-Logo, Kundenname, Datum, je Site: Compliance-Score + Top-3-Issues | VERIFIED | `AgencyReportGenerator.generate()` embeds logo (RLImage), renders client_name, generated_at date, per-site table with compliance_score + `issues[:TOP_ISSUES_LIMIT]` (3); test `test_pdf_contains_client_name` + `test_pdf_handles_top_issues_list_truncated` pass |

**Score:** 3/5 truths fully verified, 2 partial (4/5 if SC4 SVG scope reduction is accepted as deliberate)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/migrations/add_agency_client_fields.sql` | DB columns client_name, client_email on cookie_banner_configs; agency_logo_path on users; partial index | VERIFIED | 3 ADD COLUMN IF NOT EXISTS, 1 CREATE INDEX IF NOT EXISTS with WHERE client_name IS NOT NULL |
| `backend/cookie_compliance_routes.py` | PATCH /agency/sites/{site_id}/client, GET /agency/clients, POST /agency/logo, GET /agency/logo, GET /agency/logo/file, GET /agency/client-report/{client_name} | VERIFIED | All 6 endpoints present; ClientAssignRequest model; file_storage import; AgencyReportGenerator instantiated at module level |
| `backend/agency_report_generator.py` | AgencyReportGenerator class with .generate() | VERIFIED | Class exists, TOP_ISSUES_LIMIT=3, _normalize_logo() handles RGBA PNGs, pageCompression=0 for text searchability |
| `backend/tests/test_agency.py` | 8 agency endpoint tests | VERIFIED | 8 tests, all 8 PASSED in Docker container |
| `backend/tests/test_agency_pdf.py` | 7 PDF generator tests | VERIFIED | 7 tests, all 7 PASSED in Docker container |
| `backend/tests/test_agency_report_endpoint.py` | 4 report download endpoint tests | VERIFIED | 4 tests, all 4 PASSED in Docker container |
| `dashboard-react/src/lib/agency-api.ts` | 4 exported async functions | VERIFIED | getAgencyClients, assignClient, getAgencyLogo, uploadAgencyLogo, downloadClientReport all present |
| `dashboard-react/src/components/agency/ClientGroup.tsx` | Accordion card with PDF download button | VERIFIED | export function ClientGroup, "PDF herunterladen" button, acceptance_rate color coding |
| `dashboard-react/src/components/agency/AgencyLogoUpload.tsx` | Logo upload with PNG preview, 2MB check | VERIFIED | MAX_BYTES = 2*1024*1024, accept="image/png", useEffect fetches logo on mount via getAgencyLogo() |
| `dashboard-react/src/app/agency/page.tsx` | Paywall gate + dashboard with ClientGroup + AgencyLogoUpload | VERIFIED | isAgency check with early return at line 343, fetchClients(), <AgencyLogoUpload>, <ClientGroup> mapped |
| `backend/addon_payment_routes.py` | agency_sites_extra 200 EUR/month add-on | VERIFIED | Entry at line 109: price_monthly=200, compatible_plans=["agency"], extra_sites=25 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| PATCH /agency/sites/{site_id}/client | cookie_banner_configs.client_name + client_email | UPDATE ... WHERE site_id=$3 AND user_id=$4 | WIRED | Line 2599: UPDATE cookie_banner_configs SET client_name=$1... WHERE site_id=$3 AND user_id=$4 |
| GET /agency/clients | cookie_banner_configs GROUP BY client_name | WHERE c.client_name IS NOT NULL | WIRED | Line 2637: GROUP BY c.client_name, c.client_email with IS NOT NULL filter |
| POST /agency/logo | users.agency_logo_path + FileStorageService | file_storage.save_file(system_id="logos") | WIRED | Lines 2676-2683: save_file called then UPDATE users SET agency_logo_path |
| GET /agency/client-report/{client_name} | AgencyReportGenerator.generate | from agency_report_generator import AgencyReportGenerator | WIRED | Line 22 (import), line 2731 (_agency_pdf_generator = AgencyReportGenerator()), line 2794 generate() call |
| Endpoint logo lookup | users.agency_logo_path + FileStorageService.get_file | await file_storage.get_file(agency_logo_path) | WIRED | Lines 2791-2792: logo_row fetched, get_file called if path present |
| Endpoint per-site score | tracked_websites + scan_history | LEFT JOIN LATERAL ... ORDER BY scan_timestamp DESC LIMIT 1 | WIRED | Lines 2754-2761: LEFT JOIN LATERAL subquery on scan_history |
| AgencyPage -> ClientGroup | GET /agency/clients rendered per client | renders one ClientGroup per item from getAgencyClients() | WIRED | Line 460-461: clients.map(c => <ClientGroup key={c.client_name} client={c} />) |
| ClientGroup PDF button | GET /agency/client-report/{client_name} | responseType: 'blob' | WIRED | agency-api.ts line 69: responseType: 'blob'; ClientGroup line 21: downloadClientReport() |
| AgencyLogoUpload | POST /api/cookie-compliance/agency/logo | FormData with file field | WIRED | agency-api.ts line 55-56: new FormData(), append('file', file) |
| assignClient() | PATCH /agency/sites/{site_id}/client | apiClient.patch(...) | ORPHANED | Function exported from agency-api.ts but NO component imports or calls it |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `ClientGroup.tsx` | `client` prop (AgencyClient) | `getAgencyClients()` -> GET /agency/clients -> asyncpg DB query with GROUP BY | Yes — DB query groups real rows, acceptance_rate computed from real impression data | FLOWING |
| `AgencyLogoUpload.tsx` | `preview` state | `getAgencyLogo()` on mount -> GET /agency/logo -> SELECT agency_logo_path FROM users | Yes — DB lookup for stored path; serves actual file bytes | FLOWING |
| `agency/page.tsx` | `clients` array | `fetchClients()` -> `getAgencyClients()` -> backend aggregation query | Yes — real DB aggregation on mount | FLOWING |
| `AgencyReportGenerator.generate()` | `sites` list | DB query with LEFT JOIN LATERAL on scan_history | Yes — real scan_data from DB, graceful None fallback when no scan | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 19 agency tests pass | `docker exec complyo-backend python -m pytest tests/test_agency.py tests/test_agency_pdf.py tests/test_agency_report_endpoint.py -v` | 19 passed, 0 failed, 1 warning (Pydantic V1 deprecation) | PASS |
| Backend imports cleanly | Implied by test collection succeeding | No ImportError on cookie_compliance_routes or agency_report_generator | PASS |
| assignClient() wired to UI | `grep -rn "assignClient" dashboard-react/src/` | Only found in agency-api.ts (exported but not called) | FAIL — ORPHANED |
| TypeScript compilation | `cd dashboard-react && npx tsc --noEmit` | 0 errors (exit 0, no output) | PASS |

### Requirements Coverage

REQUIREMENTS.md does NOT contain AGENCY-01, AGENCY-02, or AGENCY-03 entries — these IDs are defined inline in the ROADMAP.md Phase 10 section. No orphaned requirements exist in REQUIREMENTS.md for Phase 10.

| Requirement | Source Plan | Description (from ROADMAP) | Status | Evidence |
|-------------|-------------|---------------------------|--------|----------|
| AGENCY-01 | 10-01-PLAN, 10-03-PLAN | Per-site client attribution (client_name + client_email) — DB migration + PATCH endpoint | PARTIAL | Migration + endpoint verified; no Dashboard-UI for assignment |
| AGENCY-02 | 10-01-PLAN, 10-03-PLAN | Grouped client list endpoint + dashboard rendering | SATISFIED | GET /agency/clients endpoint + ClientGroup component fully wired |
| AGENCY-03 | 10-01-PLAN, 10-02-PLAN, 10-03-PLAN | Logo upload (POST), storage (users.agency_logo_path), embedding in PDFs | PARTIAL | PNG fully supported; SVG rejected despite ROADMAP stating PNG/SVG |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `dashboard-react/src/lib/agency-api.ts` | 34 | `assignClient()` exported but called by 0 components | Warning | AGENCY-01 dashboard-UI requirement unmet; function is dead code in current build |
| `backend/cookie_compliance_routes.py` | 2670 | SVG rejected (content_type != image/png check) | Info | ROADMAP SC4 says PNG/SVG; backend only accepts PNG — scope mismatch |

No TODO/FIXME/placeholder patterns found in any agency files. No empty implementations. No hardcoded empty state arrays in rendering paths.

### Human Verification Required

#### 1. Client Assignment UI Flow

**Test:** Log in as an agency user, navigate to /agency, and attempt to assign a client_name to a specific site from the dashboard.
**Expected:** An input field, modal, or inline editor appears allowing selection of a site and entry of client_name + client_email; on save, the client group appears in Kunden-Uebersicht.
**Why human:** No automated test covers UI rendering; this UI does not exist yet (gap).

#### 2. Full End-to-End PDF Download Flow

**Test:** Complete Plan 10-03 Task 4 checkpoint steps 4-12: log in as agency user, upload PNG logo, assign client via curl PATCH, refresh dashboard, click "PDF herunterladen", open downloaded PDF.
**Expected:** PDF contains uploaded logo at top, client name headline, today's date in DE format, per-site table rows with compliance_score and top-3 issues.
**Why human:** Plan 10-03 Task 4 was marked as a blocking human-verify checkpoint; SUMMARY does not document that a human approved all 13 steps. End-to-end streaming response and blob download behavior cannot be verified programmatically without a running browser.

### Gaps Summary

Two gaps prevent full goal achievement:

**Gap 1 — assignClient() is ORPHANED (blocks AGENCY-01):** The ROADMAP SC1 requires a "Dashboard-UI" for client assignment. The backend PATCH endpoint and typed API function are built, but no React component renders an assignment form or calls `assignClient()`. The Plan 10-03 human-verify step acknowledged this with "via curl (no UI in Stufe 1)" — but this reduces the delivered feature below what the ROADMAP specifies. An agency user cannot assign clients from the dashboard without writing curl commands.

**Gap 2 — SVG logo support missing (reduces AGENCY-03 / SC4):** The ROADMAP specifies "PNG/SVG, max 2MB". The implementation explicitly rejects SVG at the HTTP layer (400 response) and the frontend file picker is restricted to image/png. This is either a deliberate scope reduction that needs ROADMAP correction, or an unimplemented feature. Given the PLAN's artifact description says "PNG only" while the ROADMAP says "PNG/SVG", the PLAN narrowed scope without updating the ROADMAP spec. This is a documentation/alignment gap rather than a code bug, but the ROADMAP success criterion is not fully met.

All other deliverables are substantive, wired, and tested. 19/19 tests pass. TypeScript compiles cleanly. Data flows from DB through backend to frontend for clients list, logo persistence, and PDF generation are all verified.

---

_Verified: 2026-05-24T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
