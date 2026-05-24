# Phase 10: Agentur-Kanal Stufe 1 — Research

**Researched:** 2026-05-24
**Domain:** Agency multi-client management, branded PDF generation, file upload (logo), FastAPI + ReportLab + asyncpg
**Confidence:** HIGH

---

## Summary

Phase 10 adds a three-feature agency layer on top of the existing cookie-compliance and scan system: (1) per-site client attribution (`client_name`, `client_email` columns on `cookie_banner_configs`), (2) a per-client grouped dashboard view, and (3) branded PDF report download with agency logo. All three features build on infrastructure that already exists and is production-ready — no new library is required.

The PDF stack is **ReportLab 4.0.7** (`reportlab==4.0.7` in `backend/requirements.txt`). Two PDF generators already exist: `backend/pdf_report_generator.py` (compliance reports for leads) and `backend/compliance_engine/pdf_generator.py`. A new `AgencyReportGenerator` class modeled on `ComplianceReportGenerator` is the correct pattern. Logo embedding is handled through `RLImage` (already imported in `pdf_report_generator.py`) from a bytes buffer — PNG works natively; SVG requires conversion to PNG with `cairosvg` or `svglib`, neither of which is installed yet (see Pitfalls).

File upload infrastructure already exists: `FileStorageService` in `backend/file_storage_service.py` (async, aiofiles-based, local-disk storage at `/app/uploads`) and the UploadFile/File multipart pattern is established in `ai_compliance_routes.py` line 882. The service needs a new `logos/` subdirectory and MIME whitelist additions for `image/png` and `image/svg+xml` (currently only document types are allowed).

The existing agency stats endpoint (`GET /api/cookie-compliance/agency/stats`) queries `cookie_compliance_stats` joined to `cookie_banner_configs` by `user_id`. It currently returns per-site aggregates. Extending it to group by `client_name` requires (a) the DB migration, (b) a join change in the SQL, and (c) a frontend restructure in `dashboard-react/src/app/agency/page.tsx`.

**Primary recommendation:** Add `client_name VARCHAR(255)` and `client_email VARCHAR(255)` to `cookie_banner_configs` via a new migration file following the pattern in `backend/migrations/`. Build a new `GET /api/cookie-compliance/agency/clients` endpoint returning client-grouped data. Build `GET /api/cookie-compliance/agency/client-report/{client_name}` that generates PDF bytes inline via ReportLab and streams them with `StreamingResponse`. Add `POST /api/cookie-compliance/agency/logo` for PNG logo upload using the existing `FileStorageService` + `UploadFile` pattern. Store logo path in a new `agency_logo_path` column on the `users` table (single column, no separate table needed for Stufe 1).

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGENCY-01 | Sites können einem `client_name` + `client_email` zugeordnet werden (DB-Migration + Backend-Endpoint + Dashboard-UI) | DB migration adds 2 nullable columns to `cookie_banner_configs`; PUT endpoint updates them; dashboard site-settings form adds 2 fields |
| AGENCY-02 | Agentur-Dashboard zeigt pro-Kunde-Gruppierung: Kunde A — N Sites — Compliance-Score — Acceptance Rate | Extend agency stats endpoint to GROUP BY client_name; frontend re-render with per-client accordions |
| AGENCY-03 | PDF-Report download per Kunde + Agentur-Logo in PDF | New AgencyReportGenerator class (ReportLab); logo stored via FileStorageService; endpoint streams PDF bytes |

</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| reportlab | 4.0.7 | PDF generation | Already installed, used in `pdf_report_generator.py` and `export_service.py` |
| aiofiles | 23.2.1 | Async file I/O for logo storage | Already installed, used by `FileStorageService` |
| python-multipart | >=0.0.9 | Parse multipart/form-data for UploadFile | Already installed, established in ai_compliance_routes |
| asyncpg (via db_pool) | existing | DB queries for client grouping | Project-wide pattern, `db_pool.fetch/fetchrow/execute` |
| fastapi | 0.115.6 | Route definitions | Project-wide |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cairosvg | ~2.7 | SVG→PNG conversion for logo embedding | Only if agency uploads SVG logo; NOT yet installed |
| Pillow | latest | Image resizing/validation for PNG logos | Only if image manipulation needed; NOT yet installed |
| io.BytesIO | stdlib | In-memory PDF generation (no temp files) | For streaming PDF response |
| StreamingResponse | fastapi stdlib | Stream PDF bytes to client | All PDF download endpoints |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ReportLab (existing) | WeasyPrint, pdfkit | ReportLab already installed and working; WeasyPrint requires Pango/Cairo system libs not present |
| Local FileStorageService | S3/MinIO | S3 not configured; local storage is established pattern; easy to migrate later |
| New `agency_logo_path` column on `users` | Separate `agency_profiles` table | Simpler for Stufe 1; Stufe 2 can extract to full profile table |

**Installation (only if SVG upload needed):**
```bash
pip install cairosvg Pillow
```
Add to `backend/requirements.txt`.

**Version verification:** ReportLab 4.0.7 confirmed in `/home/clawd/saas/legal/backend/requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure

New files to create:
```
backend/
├── migrations/
│   └── add_agency_client_fields.sql          # client_name, client_email on cookie_banner_configs
│                                             # agency_logo_path on users
├── agency_report_generator.py               # New class: AgencyReportGenerator
└── (cookie_compliance_routes.py extended)   # New endpoints added here

dashboard-react/src/app/agency/
├── page.tsx                                  # Extended: per-client grouping view
└── components/
    └── ClientGroup.tsx                       # New component: accordion per client
```

### Pattern 1: DB Migration — Add nullable columns

**What:** Add `client_name VARCHAR(255)` and `client_email VARCHAR(255)` to `cookie_banner_configs`. Add `agency_logo_path TEXT` to `users`.
**When to use:** Extending existing tables with optional agency metadata.
**Example:**
```sql
-- Source: pattern from backend/migrations/add_agency_plan.sql
ALTER TABLE cookie_banner_configs
  ADD COLUMN IF NOT EXISTS client_name  VARCHAR(255),
  ADD COLUMN IF NOT EXISTS client_email VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_banner_config_client_name
  ON cookie_banner_configs(user_id, client_name)
  WHERE client_name IS NOT NULL;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS agency_logo_path TEXT;
```

### Pattern 2: Logo Upload Endpoint

**What:** `POST /api/cookie-compliance/agency/logo` — accepts PNG/SVG multipart upload, stores via FileStorageService.
**When to use:** All file uploads in this project.
**Example:**
```python
# Source: pattern from backend/ai_compliance_routes.py lines 879-915
@router.post("/api/cookie-compliance/agency/logo")
async def upload_agency_logo(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    content = await file.read()
    # validate MIME: image/png, image/svg+xml, max 2MB
    # save via file_storage.save_file(user_id, content, file.filename, system_id="logos")
    # UPDATE users SET agency_logo_path = $1 WHERE id = $2
    return {"logo_url": relative_path}
```

### Pattern 3: Per-Client Grouping SQL

**What:** Aggregate cookie_compliance_stats grouped by client_name.
**When to use:** Building the agency per-client dashboard view.
**Example:**
```sql
-- Source: derived from existing agency stats query at cookie_compliance_routes.py lines 2522-2545
SELECT
  c.client_name,
  c.client_email,
  COUNT(DISTINCT c.site_id)            AS site_count,
  SUM(s.total_impressions)             AS total_impressions,
  SUM(s.accepted_all + s.accepted_partial) AS total_accepted,
  ROUND(
    SUM(s.accepted_all + s.accepted_partial)::numeric /
    NULLIF(SUM(s.total_impressions), 0), 4
  ) AS acceptance_rate
FROM cookie_banner_configs c
LEFT JOIN cookie_compliance_stats s
       ON s.site_id = c.site_id
      AND s.date >= CURRENT_DATE - INTERVAL '30 days'
WHERE c.user_id = $1
GROUP BY c.client_name, c.client_email
ORDER BY c.client_name NULLS LAST;
```

### Pattern 4: PDF Generation with Logo (ReportLab)

**What:** Generate PDF bytes in-memory, embed logo PNG via `RLImage`.
**When to use:** Any PDF generation in this project.
**Example:**
```python
# Source: pattern from backend/pdf_report_generator.py
import io
from reportlab.platypus import Image as RLImage, SimpleDocTemplate
from fastapi.responses import StreamingResponse

async def generate_client_report(client_name, sites_data, logo_bytes=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, ...)
    story = []
    if logo_bytes:
        img_buf = io.BytesIO(logo_bytes)
        logo_img = RLImage(img_buf, width=4*cm, height=2*cm, kind='proportional')
        story.append(logo_img)
    # ... build story ...
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Endpoint streams it:
# return StreamingResponse(io.BytesIO(pdf_bytes),
#     media_type="application/pdf",
#     headers={"Content-Disposition": f"attachment; filename=report_{client_name}.pdf"})
```

### Pattern 5: Compliance Score for Per-Site PDF Data

**What:** For each site in a client's PDF, pull the latest `compliance_score` and top 3 issues from `scan_history`.
**When to use:** PDF report generation per client.
**Example:**
```sql
SELECT DISTINCT ON (sh.website_id)
  tw.url,
  sh.compliance_score,
  sh.critical_issues,
  sh.scan_data
FROM scan_history sh
JOIN tracked_websites tw ON tw.id = sh.website_id
WHERE tw.user_id = $1
  AND tw.url ILIKE '%' || $2 || '%'   -- match by site_id from cookie_banner_configs
ORDER BY sh.website_id, sh.scan_timestamp DESC;
```

Note: `scan_history.scan_data` is a JSONB column holding `{"detected_issues": [...], "overall_score": N, ...}`. Top 3 issues are extracted via `scan_data->'detected_issues'` in Python, sorted by severity.

### Anti-Patterns to Avoid

- **Using WeasyPrint or pdfkit:** Not installed, would require system-level Pango/Cairo. ReportLab is the existing stack.
- **Streaming SVG directly to RLImage:** ReportLab's `RLImage` does not accept SVG. Must convert to PNG bytes first via cairosvg (or reject SVG and serve PNG-only for Stufe 1).
- **Hardcoding logo as a URL:** Logo must be loaded as bytes from disk (FileStorageService.get_file), not fetched via HTTP during PDF generation.
- **New separate `agency_clients` table:** Over-engineered for Stufe 1. The two nullable columns on `cookie_banner_configs` and `agency_logo_path` on `users` are sufficient. A proper agency profile table is a Stufe 2 concern.
- **Modifying the existing `get_agency_stats` endpoint:** That endpoint is used by the existing dashboard. Add a new `GET /api/cookie-compliance/agency/clients` endpoint instead to avoid breaking the current stats card.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF byte generation | Custom HTML→PDF pipeline | ReportLab SimpleDocTemplate + BytesIO | Already in production; RLImage handles logo embedding |
| File validation + async save | Custom multipart handler | `FileStorageService.validate_file` + `save_file` | Already handles size limits, path traversal protection, sha256 hash |
| Auth check in new endpoints | Re-implement JWT decode | `get_current_user_required(credentials)` from cookie_compliance_routes.py line 56 | Module-check + user_id extraction in one call |
| Per-site URL lookup | Hardcoding or re-parsing | `cookie_banner_configs.site_id` → `tracked_websites.url` JOIN | URL is in `tracked_websites`; `cookie_banner_configs` has `site_id` for the join key |

**Key insight:** This phase adds ~3-4 new DB columns, 3-4 new endpoints, 1 new Python class, and modifies 1 existing frontend page. No new infrastructure. Resist scope creep toward full agency profile management.

---

## Common Pitfalls

### Pitfall 1: SVG logos not supported by RLImage
**What goes wrong:** Agency uploads `.svg` file → `RLImage(bytes_io)` raises TypeError or produces blank image.
**Why it happens:** ReportLab's `RLImage` wraps PIL/Pillow and reads raster formats. SVG is a vector XML format.
**How to avoid:** Two options: (a) restrict logo upload to PNG/JPEG only for Stufe 1 — simpler, no new deps; (b) install `cairosvg` and convert SVG→PNG bytes before passing to RLImage. Recommended: **PNG only** for Stufe 1 — add explicit MIME check `image/png` only and return 400 for SVG.
**Warning signs:** Silent blank image in PDF or `Exception during PDF build`.

### Pitfall 2: client_name NULL grouping
**What goes wrong:** Sites without `client_name` set appear in a NULL group, confusing the dashboard.
**Why it happens:** `GROUP BY client_name` collapses all unassigned sites into `client_name = NULL`.
**How to avoid:** In the SQL query use `COALESCE(c.client_name, '(Nicht zugeordnet)')` for display, but exclude from grouped view unless `client_name IS NOT NULL`. Backend should filter `WHERE c.client_name IS NOT NULL` for the grouped endpoint; keep the existing stats endpoint unchanged for total aggregation.
**Warning signs:** Dashboard shows a client row with empty/null name and unexpectedly large numbers.

### Pitfall 3: scan_history not linked to cookie_banner_configs
**What goes wrong:** Can't get `compliance_score` per site for the PDF because `scan_history` references `tracked_websites.id` (integer FK), not `cookie_banner_configs.site_id` (varchar).
**Why it happens:** The two tables use different site identification schemes. `tracked_websites.url` vs `cookie_banner_configs.site_id` (which is a slug, e.g., `example-com`).
**How to avoid:** In the PDF generation query, join: `tracked_websites` → `scan_history` using `tw.user_id = $1`. If the site is registered in both systems, match by URL substring or by `site_id` slug convention. If no scan history exists for a site, show "Kein Scan verfügbar" in the PDF row rather than failing.
**Warning signs:** Empty PDF table rows or 500 during report generation.

### Pitfall 4: Logo path traversal via user-supplied filename
**What goes wrong:** Malicious filename like `../../../etc/passwd` used in `save_file`.
**Why it happens:** FileStorageService uses `_generate_filename()` which strips dangerous chars — but only if you call it. If you bypass it, you expose path traversal.
**How to avoid:** Always use `FileStorageService.save_file()` — it internally calls `_generate_filename()` which sanitizes the filename. Never use `file.filename` directly as a disk path.
**Warning signs:** FileStorageService has a path-traversal check in `get_file` (line 112-114) but not a check that the caller used a safe name.

### Pitfall 5: cookie_banner_configs has no URL column — need JOIN to get display URL
**What goes wrong:** When building the per-client PDF report, you need the human-readable URL for each site but `cookie_banner_configs` only stores `site_id` (a slug).
**Why it happens:** Schema design: `cookie_banner_configs.site_id` is a slug like `example-com`, not a URL. The actual URL is in `tracked_websites.url`.
**How to avoid:** Join via: `tracked_websites tw ON tw.user_id = c.user_id AND tw.url ILIKE '%' || replace(c.site_id, '-', '.') || '%'` — or use `last_scan_url` which IS present on `cookie_banner_configs` (confirmed at line 431 of cookie_compliance_routes.py). Use `last_scan_url` as the display URL in the PDF.

---

## Code Examples

### agency/clients endpoint (new, companion to existing agency/stats)
```python
# Source: pattern from cookie_compliance_routes.py lines 2512-2560
@router.get("/api/cookie-compliance/agency/clients")
async def get_agency_clients(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    if not db_pool:
        return {"clients": []}
    rows = await db_pool.fetch(
        """SELECT
             c.client_name,
             c.client_email,
             COUNT(DISTINCT c.site_id)                                   AS site_count,
             SUM(COALESCE(s.total_impressions, 0))                       AS total_impressions,
             SUM(COALESCE(s.accepted_all, 0) + COALESCE(s.accepted_partial, 0)) AS total_accepted
           FROM cookie_banner_configs c
           LEFT JOIN cookie_compliance_stats s
                  ON s.site_id = c.site_id
                 AND s.date >= CURRENT_DATE - INTERVAL '30 days'
           WHERE c.user_id = $1 AND c.client_name IS NOT NULL
           GROUP BY c.client_name, c.client_email
           ORDER BY c.client_name""",
        user_id
    )
    clients = [dict(r) for r in rows]
    for cl in clients:
        total = cl["total_impressions"] or 0
        cl["acceptance_rate"] = round(cl["total_accepted"] / total, 4) if total else 0.0
    return {"clients": clients}
```

### Assign client to site (PATCH endpoint)
```python
@router.patch("/api/cookie-compliance/agency/sites/{site_id}/client")
async def assign_client_to_site(
    site_id: str,
    body: ClientAssignRequest,  # {client_name: str, client_email: str}
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    await db_pool.execute(
        """UPDATE cookie_banner_configs
           SET client_name = $1, client_email = $2, updated_at = NOW()
           WHERE site_id = $3 AND user_id = $4""",
        body.client_name, body.client_email, site_id, user_id
    )
    return {"ok": True}
```

### Logo upload (new endpoint, same file as above)
```python
@router.post("/api/cookie-compliance/agency/logo")
async def upload_agency_logo(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = await get_current_user_required(credentials)
    user_id = int(user.get("id") or user.get("user_id"))
    content = await file.read()
    # PNG only for Stufe 1
    if file.content_type not in ("image/png",):
        raise HTTPException(status_code=400, detail="Nur PNG-Logos werden unterstützt.")
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Logo zu groß (max 2MB).")
    info = await file_storage.save_file(user_id, content, file.filename, system_id="logos")
    await db_pool.execute(
        "UPDATE users SET agency_logo_path = $1 WHERE id = $2",
        info["relative_path"], user_id
    )
    return {"relative_path": info["relative_path"]}
```

### AgencyReportGenerator skeleton (new file: backend/agency_report_generator.py)
```python
# Source: modeled on backend/pdf_report_generator.py
import io
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet

class AgencyReportGenerator:
    def generate(
        self,
        client_name: str,
        sites: List[Dict[str, Any]],  # [{url, compliance_score, critical_issues, top_issues[3]}]
        agency_logo_bytes: Optional[bytes] = None,
        generated_at: str = "",
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, ...)
        story = []
        if agency_logo_bytes:
            logo = RLImage(io.BytesIO(agency_logo_bytes), width=4*cm, height=2*cm, kind='proportional')
            story.append(logo)
        # header: client_name, date
        # table: site URL | compliance_score | top 3 issues
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WeasyPrint for HTML→PDF | ReportLab programmatic PDF | Existing codebase | No system libs needed; all layout is code-defined |
| Separate agency profile table | Nullable columns on existing tables | Stufe 1 design decision | Simpler migration, sufficient for Phase 10 scope |

**Deprecated/outdated:**
- erecht24 integration modules: deleted (migration `migration_deprecate_erecht24.sql` confirms). Do not reference.
- `cookie_compliance_stats` schema uses `site_identifier` NOT `site_id` in some queries — confirmed bug (STATE.md blockers). When joining `cookie_compliance_stats`, use `site_identifier = c.site_id` OR rely on the existing agency stats query pattern which already works correctly. Verify in production schema before writing migration.

---

## Open Questions

1. **`cookie_compliance_stats.site_identifier` vs `site_id`**
   - What we know: STATE.md Blockers says "cookie_compliance_stats DB schema bug: uses `site_identifier` not `site_id` — causes 500 errors on live DB; mocked in all tests"
   - What's unclear: The existing agency stats query at line 2530 uses `s.site_id`. Either the schema was fixed, or the column name varies. The `init_cookie_compliance.sql` schema shows `site_id VARCHAR(255)` — but that's the schema definition file, not necessarily what's live.
   - Recommendation: In the new clients endpoint SQL, use the same column reference as the existing working agency stats query (`s.site_id`). In Wave 0, add a migration guard that confirms the column exists.

2. **`tracked_websites` → `cookie_banner_configs` join for per-site compliance score**
   - What we know: `scan_history` links to `tracked_websites.id` (integer UUID FK). `cookie_banner_configs` has `site_id` varchar slug and `last_scan_url` TEXT.
   - What's unclear: Is `last_scan_url` reliably populated for all sites?
   - Recommendation: Use `last_scan_url` as display URL in PDF. For the compliance score lookup, join `scan_history` via `tracked_websites` using `user_id` and match `tw.url` contains the site slug, or accept that some sites may have no scan history and show "Kein Score verfügbar".

3. **`users` table schema — is `agency_logo_path` addable?**
   - What we know: `users` table is referenced throughout the codebase. The column does not exist yet.
   - What's unclear: Are there any ORM layers or fixed column selections that would break on adding a column?
   - Recommendation: The project uses raw asyncpg queries (no ORM), so `ALTER TABLE users ADD COLUMN IF NOT EXISTS agency_logo_path TEXT` is safe. All existing queries use explicit column lists.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Backend | Yes | 3.12.3 | — |
| reportlab | PDF generation | Yes | 4.0.7 | — |
| aiofiles | Logo storage | Yes | 23.2.1 | — |
| python-multipart | UploadFile parsing | Yes | >=0.0.9 | — |
| asyncpg | DB queries | Yes | existing | — |
| Pillow / PIL | PNG validation (optional) | No | — | Skip image validation; accept all bytes |
| cairosvg | SVG→PNG for logos | No | — | Restrict logo to PNG only (recommended) |
| FastAPI StreamingResponse | PDF download | Yes (stdlib) | — | — |

**Missing dependencies with no fallback:**
- None (all required features achievable with installed packages if SVG is restricted to PNG)

**Missing dependencies with fallback:**
- `cairosvg`: required only for SVG logo support — fallback is PNG-only restriction (recommended for Stufe 1)
- `Pillow`: required only for image dimension validation — fallback is size-in-bytes check only (2MB limit enforced in code)

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ (tests/requirements.txt) |
| Config file | none — see Wave 0 |
| Quick run command | `cd /home/clawd/saas/legal/backend && python -m pytest tests/test_agency.py -x` |
| Full suite command | `cd /home/clawd/saas/legal/backend && python -m pytest tests/ -x --ignore=tests/__pycache__` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGENCY-01 | PATCH assigns client_name/client_email to site; GET returns updated fields | unit (monkeypatch db_pool) | `pytest tests/test_agency.py::test_assign_client -x` | No — Wave 0 |
| AGENCY-01 | Invalid site_id returns 404 | unit | `pytest tests/test_agency.py::test_assign_client_not_found -x` | No — Wave 0 |
| AGENCY-02 | GET /agency/clients returns grouped result with site_count + acceptance_rate | unit (monkeypatch db_pool) | `pytest tests/test_agency.py::test_get_agency_clients -x` | No — Wave 0 |
| AGENCY-02 | Sites with no client_name excluded from grouped endpoint | unit | `pytest tests/test_agency.py::test_clients_excludes_null -x` | No — Wave 0 |
| AGENCY-03 | Logo upload accepts PNG, rejects SVG/JPEG, rejects >2MB | unit | `pytest tests/test_agency.py::test_logo_upload -x` | No — Wave 0 |
| AGENCY-03 | PDF generation returns bytes with non-zero length | unit | `pytest tests/test_agency.py::test_pdf_generation -x` | No — Wave 0 |
| AGENCY-03 | PDF generation with logo embeds without error | unit | `pytest tests/test_agency.py::test_pdf_with_logo -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_agency.py -x`
- **Per wave merge:** `pytest tests/ -x --ignore=tests/__pycache__`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_agency.py` — all AGENCY-01/02/03 test cases
- [ ] No pytest.ini found — add `[pytest]` to `backend/tests/requirements.txt` or create minimal `pytest.ini` in `backend/`
- [ ] Confirm `cd backend && python -m pytest` resolves imports (existing tests use `os.environ.setdefault` pattern — same approach needed)

*(No existing test infrastructure covers agency features — all must be created in Wave 0)*

---

## Sources

### Primary (HIGH confidence)
- `backend/init_cookie_compliance.sql` — definitive `cookie_banner_configs` schema (all columns confirmed, no `client_name`/`client_email`)
- `backend/cookie_compliance_routes.py` lines 2512–2560 — existing agency stats endpoint pattern
- `backend/pdf_report_generator.py` — ReportLab 4.0.7 patterns, `RLImage` import confirmed
- `backend/file_storage_service.py` — FileStorageService full API (validate_file, save_file, get_file)
- `backend/ai_compliance_routes.py` lines 879–930 — UploadFile/File multipart upload pattern
- `backend/requirements.txt` — confirmed packages: reportlab 4.0.7, aiofiles 23.2.1, python-multipart, fastapi 0.115.6
- `backend/init_scan_history.sql` — scan_history schema: compliance_score (INTEGER), scan_data (JSONB), critical_issues
- `dashboard-react/src/app/agency/page.tsx` — current agency page: no per-client grouping, flat site list

### Secondary (MEDIUM confidence)
- `backend/migrations/add_agency_plan.sql` — agency plan feature flags include `agency_reports: true`
- `.planning/STATE.md` Blockers — `cookie_compliance_stats` site_identifier bug (not yet fixed as of 2026-05-01)
- `backend/init_user_limits.sql` lines 58–70 — `tracked_websites` schema (no URL column on `cookie_banner_configs`)
- ReportLab 4.0 docs (knowledge): `RLImage(BytesIO, width=N, height=N, kind='proportional')` for logo embedding

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages confirmed from requirements.txt + source files
- Architecture: HIGH — all patterns derived from existing production code in same codebase
- Pitfalls: HIGH (DB schema bugs) / MEDIUM (SVG limitation — known ReportLab behavior, not verified against v4.0.7 changelog)

**Research date:** 2026-05-24
**Valid until:** 2026-06-24 (stable stack, 30-day window)
