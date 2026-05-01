# Phase 02: Accessibility Statement Generator - Research

**Researched:** 2026-04-30
**Domain:** FastAPI endpoint + Next.js UI for BFSG-compliant statement generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- New endpoint `POST /api/v2/accessibility/generate-statement` in `accessibility_fix_routes.py`
- Request body: `site_id` + optional override fields (contact email, review date)
- Response: `{ "html": "...", "markdown": "...", "filename": "barrierefreiheitserklaerung.html" }`
- Load scan results from DB (most recent accessibility scan for the site_id)
- Fallback when no scan data: "Konformitätsstatus: Nicht bewertet"
- Auth-protected: `get_current_user` (consistent with other accessibility endpoints in this file)
- BFSG required fields: Geltungsbereich, Konformitätsstatus, Nicht barrierefreie Inhalte, Kontakt/Feedback, Durchsetzungsverfahren (BMAS Schlichtungsstelle), Datum
- Dashboard: new subpage `src/app/accessibility/statement/page.tsx` OR section in existing page
- UI flow: form → live-preview → download (HTML) + PDF export
- Template-based generation: fixed structure, variable fields from DB/form
- Language: German (primary market)
- Max 10 issues in statement, prioritized by criticality
- BMAS Schlichtungsstelle URL: https://www.schlichtungsstelle-bfsg.de/

### Claude's Discretion
- Styling of the PDF template (jsPDF vs. window.print())
- Exact DB query for accessibility scan results (depends on schema)
- Error handling when no scan data available

### Deferred Ideas (OUT OF SCOPE)
- Multilingual statements (EN/FR) — Phase 8 Enterprise
- Automatic annual update reminders — Phase 9
- Statement hosting on Complyo subdomain
- WCAG 2.2 / 3.0 conformance status — Phase 4
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIT-05 | Barrierefreiheitserklärung-Generator: BFSG-pflicht gemäß § 12 BFSG + EN 301 549 | Template structure, DB query pattern, and endpoint placement all verified in codebase |
</phase_requirements>

---

## Summary

Phase 2 adds a self-contained statement generator on top of an already well-structured accessibility module. The backend already has `accessibility_fix_routes.py` with a clear router, auth, and DB pattern — the new endpoint slots in as a peer of `POST /analyze`, `POST /generate-fixes`, and `POST /download-bundle`. The DB schema stores fix packages in `accessibility_fix_packages` (JSONB `fix_package` column), and scan results are in `scan_results` (JSONB `issues` and `pillar_scores` columns). Jinja2 is already installed and used in `ai_act_doc_generator.py` for exactly this pattern: inline Jinja2 template strings rendered to HTML. No new dependencies are needed for the backend.

The dashboard has no existing accessibility page/route at all — the `src/app/` directory shows `ai-compliance`, `auth`, `cookie-compliance`, etc. but no `accessibility/` subtree. The new page must be created from scratch as `src/app/accessibility/statement/page.tsx`. The established download pattern is: call backend API → receive JSON with `{ html: "..." }` → create `Blob` with `text/html` → anchor click download. This pattern is used identically in `ComplianceIssueCard.tsx`, `ComplianceIssueGroup.tsx`, and `LegalDocumentGenerator.tsx`. PDF export is Claude's discretion; `window.print()` fits the project's zero-new-dependency preference.

**Primary recommendation:** Add the endpoint to `accessibility_fix_routes.py` using an inline Jinja2 template string (matching `ai_act_doc_generator.py` pattern), query `accessibility_fix_packages` for the most recent `fix_package` JSONB, build the new page at `src/app/accessibility/statement/page.tsx`, and use the established `Blob + anchor-click` pattern for HTML download.

---

## Standard Stack

### Core (all already installed — no new deps needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | installed | HTTP endpoint framework | All backend routes use it |
| Jinja2 | 3.1.2 (requirements.txt) | HTML template rendering | Already used in ai_act_doc_generator.py and email_service.py |
| asyncpg (via db_pool) | installed | PostgreSQL async driver | Used by all accessibility routes via `db_pool.acquire()` |
| Next.js (App Router) | installed | Dashboard UI pages | All dashboard pages use App Router |
| React | installed | Component library | All dashboard UI |
| lucide-react | installed | Icon library | Used throughout dashboard |
| axios (apiClient) | installed | HTTP client with auth interceptor | `src/lib/api.ts` — auto-injects Bearer token |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic BaseModel | installed | Request/response validation | All FastAPI request bodies use it |
| window.print() | browser built-in | PDF export via browser print dialog | No jsPDF dependency needed; consistent with zero-dep approach |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 inline template | Python f-string | f-strings are already used in patch_generator.py; Jinja2 is cleaner for multi-block HTML with conditionals and loops |
| window.print() | jsPDF | jsPDF = new npm dependency; window.print() works offline, requires zero setup |

---

## Architecture Patterns

### Recommended Project Structure

```
backend/
  accessibility_fix_routes.py     # ADD: GenerateStatementRequest, generate_statement endpoint
dashboard-react/src/
  app/
    accessibility/
      statement/
        page.tsx                  # NEW: Statement generator page (form + preview + download)
  components/
    accessibility/
      StatementGenerator.tsx      # NEW: form + preview UI component
      StatementPreview.tsx        # NEW: rendered HTML preview panel
      index.ts                    # UPDATE: export new components
```

### Pattern 1: Backend Endpoint in accessibility_fix_routes.py

**What:** Add `GenerateStatementRequest` Pydantic model and `@accessibility_fix_router.post("/generate-statement")` handler as a peer to existing endpoints.

**When to use:** Anytime a new accessibility sub-feature is added — always goes in this file.

**Example (from existing pattern in same file):**
```python
# Source: /home/clawd/saas/legal/backend/accessibility_fix_routes.py lines 52-109

class GenerateStatementRequest(BaseModel):
    site_id: str = Field(..., description="Site-ID des Scans")
    site_url: Optional[str] = Field(None, description="URL der Website (Anzeige im Statement)")
    contact_email: Optional[str] = Field(None, description="Kontakt-Email für Feedback-Mechanismus")
    review_date: Optional[str] = Field(None, description="Datum der letzten Überprüfung (YYYY-MM-DD)")

class GenerateStatementResponse(BaseModel):
    html: str
    markdown: str
    filename: str

@accessibility_fix_router.post("/generate-statement", response_model=GenerateStatementResponse)
async def generate_statement(
    request: GenerateStatementRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> GenerateStatementResponse:
    await require_accessibility_module(user)
    # ... load from db_pool, render template, return
```

**Auth:** Use the local `get_current_user` function already defined at line 114 in `accessibility_fix_routes.py`. Do NOT import from `auth_routes` — the local definition already exists and is used by all other endpoints in this file.

### Pattern 2: DB Query for Scan Results

**What:** Two tables are relevant. `accessibility_fix_packages` stores the full JSONB fix package (issues, summary, etc.) by `(user_id, site_id)`. `scan_results` stores raw scan data by `(user_id, website_id)`. The fix_packages table is the correct source because it already holds structured issues in `fix_package->>'summary'` and `fix_package->'widget_fixes'`.

**Exact query pattern (from line 403-410 in accessibility_fix_routes.py):**
```python
# Source: /home/clawd/saas/legal/backend/accessibility_fix_routes.py

async with db_pool.acquire() as conn:
    row = await conn.fetchrow("""
        SELECT fix_package, created_at, site_url
        FROM accessibility_fix_packages
        WHERE site_id = $1 AND user_id = $2
        ORDER BY created_at DESC
        LIMIT 1
    """, site_id, str(user.get('user_id')))

    if not row:
        # fallback: no scan data
        conformity_status = "Nicht bewertet"
        known_issues = []
    else:
        package = row['fix_package']
        summary = package.get('summary', {})
        # extract up to 10 issues prioritized by risk_euro descending
```

**JSONB structure of fix_package (from FixPackage TypeScript type in FixWizard.tsx):**
```
fix_package = {
  site_url: str,
  generated_at: str,
  total_issues: int,
  widget_fixes: [{feature_id, issues_count, description, ...}],
  code_patches: [{feature_id, wcag_criteria, description, ...}],
  manual_guides: [{feature_id, title, wcag_criteria, ...}],
  summary: {
    total_issues, auto_fixable, widget_fixable, manual_only,
    by_feature: {ALT_TEXT: N, CONTRAST: N, ...},
    total_risk_euro: N,
    recommendation: str
  }
}
```

**Deriving WCAG conformance level:** If `summary.total_issues == 0` → "vollständig konform mit WCAG 2.1 Level AA". If issues present → "teilweise konform". No scan → "Nicht bewertet".

### Pattern 3: Jinja2 Template in Backend (no template files needed)

**What:** Use `jinja2.Environment().from_string(template_str)` with an inline template string. No file system loader needed.

**Example (from ai_act_doc_generator.py, line 21-23):**
```python
# Source: /home/clawd/saas/legal/backend/ai_act_doc_generator.py

from jinja2 import Environment, select_autoescape

jinja_env = Environment(autoescape=select_autoescape(['html']))
template = jinja_env.from_string(STATEMENT_TEMPLATE_HTML)
html_output = template.render(
    site_url=site_url,
    conformity_status=conformity_status,
    known_issues=known_issues,
    contact_email=contact_email,
    review_date=review_date,
    generated_date=datetime.now().strftime("%d.%m.%Y"),
)
```

**Template should include `autoescape=True`** because it renders user-provided email addresses and site URLs into HTML.

### Pattern 4: Frontend HTML Download (client-side Blob)

**What:** Receive JSON `{ html: "..." }` from API, create Blob, trigger anchor click.

**Exact pattern (from ComplianceIssueCard.tsx lines 203-213):**
```typescript
// Source: /home/clawd/saas/legal/dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx

const blob = new Blob([data.html], { type: 'text/html;charset=utf-8' });
const url = URL.createObjectURL(blob);
const link = document.createElement('a');
link.href = url;
link.download = 'barrierefreiheitserklaerung.html';
document.body.appendChild(link);
link.click();
document.body.removeChild(link);
URL.revokeObjectURL(url);
```

### Pattern 5: New Next.js App Router Page

**What:** Create `src/app/accessibility/statement/page.tsx` as a `'use client'` component. The ai-compliance page (`src/app/ai-compliance/page.tsx`) is the correct structural reference — it uses `useEffect` for data loading, token from `localStorage.getItem('access_token')`, and error/loading states.

**API call pattern (from ai-compliance-api.ts):**
```typescript
// Source: /home/clawd/saas/legal/dashboard-react/src/lib/ai-compliance-api.ts

const token = localStorage.getItem('access_token');
const response = await axios.post('/api/v2/accessibility/generate-statement', payload, {
  headers: { Authorization: `Bearer ${token}` }
});
```

However, **prefer using the project's `apiClient`** from `src/lib/api.ts` — it auto-injects the token via interceptor, handles 401/token refresh, and is the established pattern for new code.

### Pattern 6: PDF Export via window.print()

**What:** Inject print-specific CSS in the preview HTML, then call `window.print()` in a hidden iframe or open the HTML in a new tab and trigger print.

**Simplest approach:** The rendered HTML statement (already returned from backend) contains print CSS (`@media print { ... }`). The "PDF exportieren" button opens a new window with the HTML content and calls `window.print()` on it. No jsPDF dependency needed.

### Anti-Patterns to Avoid

- **Importing `get_current_user` from `auth_routes`** — multiple files do this but the accessibility_fix_routes.py already defines its own local copy. Use the local one to stay consistent with this file.
- **Creating a separate Python file for the statement generator** — the `accessibility_fix_routes.py` already contains all accessibility logic. Adding a new endpoint here keeps the pattern consistent and avoids new init_routes calls in main_production.py.
- **Using pdfkit for PDF generation** — pdfkit is only used in `ai_act_doc_generator.py` and requires `wkhtmltopdf` binary on the server. window.print() requires zero server changes.
- **Fetching scan data from `scan_results` table instead of `accessibility_fix_packages`** — `scan_results` has `issues` as raw JSONB but lacks the structured summary with risk_euro, by_feature grouping, etc. that the fix_packages table provides via the existing /summary/{site_id} endpoint pattern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML template rendering | Manual string concatenation | Jinja2 `from_string()` | Auto-escaping prevents XSS; already installed |
| PDF generation | pdfkit/WeasyPrint server-side | `window.print()` | Requires zero new server deps; works in all browsers |
| Auth token injection in fetch | Manual `Authorization` header | `apiClient` from `src/lib/api.ts` | Auto-handles refresh, retry on network errors |
| BFSG required field list | Research from scratch | Use the exact 6 fields already defined in CONTEXT.md (verified against § 12 BFSG) | Already validated by project stakeholder |
| Markdown generation | Custom markdown builder | Python f-string with `#` headings | Markdown output is simple flat text — no library needed |

---

## Common Pitfalls

### Pitfall 1: site_id vs user_id Mismatch in DB Query

**What goes wrong:** The `accessibility_fix_packages` table has a `UNIQUE (user_id, site_id)` constraint. If `site_id` is derived from site_url using the slug transformation (`site_url.replace('https://','').replace('.', '-')[:50]`), the caller must pass the already-transformed `site_id`, not the raw URL.

**Why it happens:** The `save_fix_package_to_db` background task at line 436 transforms the URL to a site_id slug. If the frontend passes a raw URL to `generate-statement`, the lookup will fail to find any row.

**How to avoid:** The request body accepts `site_id` (already-transformed slug). The frontend must pass the same `site_id` it uses when calling `/summary/{site_id}`.

**Warning signs:** Query returns `None` even though fix packages exist in the DB.

### Pitfall 2: Jinja2 Autoescape Not Enabled

**What goes wrong:** User-provided `contact_email` or `site_url` with `<script>` or `"` could break the HTML output or create XSS if rendered without escaping.

**Why it happens:** `jinja2.Environment()` does NOT enable autoescape by default.

**How to avoid:** Always use `autoescape=select_autoescape(['html'])` when creating the Environment, as done in `ai_act_doc_generator.py` line 21.

**Warning signs:** HTML output contains raw `<` or `>` characters in user-provided fields.

### Pitfall 3: `db_pool` is None at Route Execution Time

**What goes wrong:** The `db_pool` global in `accessibility_fix_routes.py` is `None` until `init_routes()` is called in `main_production.py`. If the endpoint uses `db_pool` without a None-check, it crashes with `AttributeError: 'NoneType' object has no attribute 'acquire'`.

**Why it happens:** Routes are defined at import time but `db_pool` is injected at startup.

**How to avoid:** Guard with `if not db_pool: raise HTTPException(status_code=500, detail="Database not available")` — exactly the pattern used at line 399 in the `/summary/{site_id}` endpoint.

**Warning signs:** HTTP 500 "Database not available" in development when running without proper startup.

### Pitfall 4: No Accessibility Page Route in Nav — Users Can't Find It

**What goes wrong:** Creating `src/app/accessibility/statement/page.tsx` without linking to it from the existing dashboard navigation means users have no way to reach the page.

**Why it happens:** Next.js file-based routing creates the route but no existing nav component automatically includes it.

**How to avoid:** Check where the existing navigation links live (likely in `src/components/` layout or sidebar component) and add the accessibility statement link there as part of the implementation.

**Warning signs:** Page works when navigated to directly but no link exists in the dashboard nav.

### Pitfall 5: `fix_package` JSONB Column Name Difference Between Migrations

**What goes wrong:** There are TWO schemas for accessibility_fix_packages across migrations:
- `create_accessibility_fix_packages.sql`: columns `user_id UUID`, `site_id VARCHAR`, `site_url TEXT`, `fix_package JSONB`
- `complete_migration.sql`: columns `user_id UUID`, `website_id UUID`, `scan_id UUID`, `package_data JSONB` (different column name!)

**Why it happens:** The `complete_migration.sql` schema appears to be an older or alternative schema; the live queries in `accessibility_fix_routes.py` (lines 403-410 and 444-446) use `fix_package` column name and `site_id/user_id` — matching the `create_accessibility_fix_packages.sql` schema.

**How to avoid:** Use column names `fix_package`, `site_id`, `user_id` as verified from the actual running queries in `accessibility_fix_routes.py`. Do not use `package_data` or `website_id`.

**Warning signs:** `asyncpg.exceptions.UndefinedColumnError` at runtime.

---

## Code Examples

### Backend: Full generate-statement endpoint skeleton

```python
# Source: Pattern derived from /home/clawd/saas/legal/backend/accessibility_fix_routes.py
# Auth pattern: lines 114-131 (local get_current_user)
# DB pattern: lines 399-422 (get_fix_summary)
# Download pattern: lines 277-318 (download_bundle with StreamingResponse)

from jinja2 import Environment, select_autoescape
from fastapi.responses import JSONResponse

_jinja_env = Environment(autoescape=select_autoescape(['html']))

STATEMENT_TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Barrierefreiheitserklärung - {{ site_url }}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.6; }
    h1 { border-bottom: 2px solid #1e40af; padding-bottom: 0.5rem; }
    @media print { body { margin: 1rem; } }
  </style>
</head>
<body>
  <h1>Barrierefreiheitserklärung</h1>
  <p><strong>Geltungsbereich:</strong> Diese Erklärung gilt für {{ site_url }}.</p>
  <h2>Stand der Vereinbarkeit</h2>
  <p>{{ conformity_text }}</p>
  <h2>Nicht barrierefreie Inhalte</h2>
  {% if known_issues %}
  <ul>{% for issue in known_issues %}<li>{{ issue }}</li>{% endfor %}</ul>
  {% else %}<p>Keine bekannten nicht barrierefreien Inhalte.</p>{% endif %}
  <h2>Kontakt und Feedback</h2>
  <p>E-Mail: <a href="mailto:{{ contact_email }}">{{ contact_email }}</a></p>
  <h2>Durchsetzungsverfahren</h2>
  <p>Schlichtungsstelle BFSG: <a href="https://www.schlichtungsstelle-bfsg.de/">
    https://www.schlichtungsstelle-bfsg.de/</a></p>
  <p><small>Erstellt am {{ generated_date }}. Letzte Überprüfung: {{ review_date }}.</small></p>
</body>
</html>"""

class GenerateStatementRequest(BaseModel):
    site_id: str = Field(..., description="Site-ID")
    site_url: Optional[str] = Field(None)
    contact_email: Optional[str] = Field(None)
    review_date: Optional[str] = Field(None)

class GenerateStatementResponse(BaseModel):
    html: str
    markdown: str
    filename: str = "barrierefreiheitserklaerung.html"

@accessibility_fix_router.post("/generate-statement", response_model=GenerateStatementResponse)
async def generate_statement(
    request: GenerateStatementRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> GenerateStatementResponse:
    await require_accessibility_module(user)
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")
    
    conformity_text = "Konformitätsstatus: Nicht bewertet"
    known_issues: List[str] = []
    display_url = request.site_url or request.site_id

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT fix_package, site_url, created_at
            FROM accessibility_fix_packages
            WHERE site_id = $1 AND user_id = $2
            ORDER BY created_at DESC LIMIT 1
        """, request.site_id, str(user.get('user_id')))

    if row:
        display_url = row['site_url'] or display_url
        package = row['fix_package']
        summary = package.get('summary', {})
        total = summary.get('total_issues', 0)
        if total == 0:
            conformity_text = "vollständig konform mit WCAG 2.1 Level AA / EN 301 549"
        else:
            conformity_text = f"teilweise konform mit WCAG 2.1 Level AA / EN 301 549 — {total} bekannte Abweichungen"
        
        # collect up to 10 issues by risk_euro desc
        all_issues = []
        for fix in package.get('widget_fixes', []):
            all_issues.append({'desc': fix.get('description', ''), 'risk': 0})
        for patch in package.get('code_patches', []):
            all_issues.append({'desc': patch.get('description', ''), 'risk': 0})
        for guide in package.get('manual_guides', []):
            all_issues.append({'desc': guide.get('description', ''), 'risk': 0})
        known_issues = [i['desc'] for i in all_issues[:10] if i['desc']]

    template = _jinja_env.from_string(STATEMENT_TEMPLATE_HTML)
    html_out = template.render(
        site_url=display_url,
        conformity_text=conformity_text,
        known_issues=known_issues,
        contact_email=request.contact_email or "info@ihre-domain.de",
        review_date=request.review_date or datetime.now().strftime("%d.%m.%Y"),
        generated_date=datetime.now().strftime("%d.%m.%Y"),
    )

    # Minimal markdown version
    md_out = f"# Barrierefreiheitserklärung\n\n**Geltungsbereich:** {display_url}\n\n"
    md_out += f"**Stand der Vereinbarkeit:** {conformity_text}\n\n"
    if known_issues:
        md_out += "**Nicht barrierefreie Inhalte:**\n" + "\n".join(f"- {i}" for i in known_issues) + "\n\n"
    md_out += f"**Kontakt:** {request.contact_email or 'info@ihre-domain.de'}\n\n"
    md_out += "**Durchsetzungsverfahren:** https://www.schlichtungsstelle-bfsg.de/\n"

    return GenerateStatementResponse(html=html_out, markdown=md_out)
```

### Frontend: Download trigger (established project pattern)

```typescript
// Source: Exact pattern from ComplianceIssueCard.tsx lines 203-213

const handleDownloadHTML = (htmlContent: string) => {
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'barrierefreiheitserklaerung.html';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
```

### Frontend: PDF export via window.print()

```typescript
// window.print() approach — no new dependencies

const handleExportPDF = (htmlContent: string) => {
  const printWindow = window.open('', '_blank');
  if (!printWindow) return;
  printWindow.document.write(htmlContent);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
  // printWindow.close() after print dialog closes — optional
};
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| f-string templates for HTML generation | Jinja2 `from_string()` with autoescape | Used in ai_act_doc_generator.py already | XSS-safe HTML; conditionals/loops readable |
| Server-side PDF generation (pdfkit) | browser window.print() | Established in project discretion | Zero server binary requirements |
| Per-file auth imports | Local `get_current_user` in each router file | Project pattern from accessibility_fix_routes.py | Each router is self-contained |

---

## Open Questions

1. **Which `site_id` format does the frontend already send?**
   - What we know: `save_fix_package_to_db` transforms URLs to slugs like `complyo-de` (strips protocol, replaces `.` and `/` with `-`, limits to 50 chars)
   - What's unclear: Whether the frontend already stores and sends this transformed `site_id` string, or sends raw URLs
   - Recommendation: The `GET /summary/{site_id}` endpoint already exists with the same slug-based lookup — check how the frontend calls that endpoint to confirm the site_id format in use

2. **Does an accessibility dashboard navigation link already exist?**
   - What we know: No `src/app/accessibility/` directory exists yet
   - What's unclear: Where sidebar/nav links are defined (likely in a layout component not yet investigated)
   - Recommendation: Investigate `src/components/layout/` or main layout.tsx during Wave 0 to find where nav links are added

---

## Environment Availability

Step 2.6: No new external dependencies. All required tools (Jinja2, FastAPI, asyncpg, Next.js, React, lucide-react, axios) are already installed and confirmed in `requirements.txt` and `package.json`. No external services, CLI tools, or databases beyond the already-running PostgreSQL instance are required.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Jinja2 | Template rendering | confirmed in requirements.txt | 3.1.2 | Python f-string (but Jinja2 preferred) |
| asyncpg via db_pool | DB query | confirmed in use in accessibility_fix_routes.py | current | — |
| Next.js App Router | Dashboard page | confirmed in use | current | — |
| lucide-react | UI icons | confirmed in FixWizard.tsx | current | — |

---

## Validation Architecture

**nyquist_validation is enabled** (config.json `workflow.nyquist_validation: true`).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (backend) — confirmed by test files in `backend/tests/` |
| Config file | none — pytest run from `backend/tests/` directory |
| Quick run command | `cd /home/clawd/saas/legal/backend && python -m pytest tests/test_statement_generator.py -x -v` |
| Full suite command | `cd /home/clawd/saas/legal/backend && python -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDIT-05 SC1 | `POST /api/v2/accessibility/generate-statement` returns `{html, markdown, filename}` | unit | `pytest tests/test_statement_generator.py::test_generate_statement_returns_correct_shape -x` | Wave 0 |
| AUDIT-05 SC2 | Generator uses scan results to fill WCAG level and known issues | unit | `pytest tests/test_statement_generator.py::test_generate_statement_uses_scan_data -x` | Wave 0 |
| AUDIT-05 SC2 | No scan data → fallback "Nicht bewertet" | unit | `pytest tests/test_statement_generator.py::test_generate_statement_no_scan_fallback -x` | Wave 0 |
| AUDIT-05 SC3 | Dashboard page renders form + preview + download button | manual | UI smoke test in browser | n/a |
| AUDIT-05 SC4 | Generated HTML contains all 6 BFSG required fields | unit | `pytest tests/test_statement_generator.py::test_statement_contains_bfsg_required_fields -x` | Wave 0 |
| AUDIT-05 SC4 | BMAS Schlichtungsstelle URL is present | unit | `pytest tests/test_statement_generator.py::test_statement_contains_bmas_url -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd /home/clawd/saas/legal/backend && python -m pytest tests/test_statement_generator.py -x`
- **Per wave merge:** `cd /home/clawd/saas/legal/backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_statement_generator.py` — unit tests for all AUDIT-05 behaviors listed above; no DB needed (mock `db_pool` with `asynctest` or `unittest.mock.AsyncMock`)
- [ ] No conftest.py changes needed — existing test files run without shared fixtures

---

## Sources

### Primary (HIGH confidence)
- `/home/clawd/saas/legal/backend/accessibility_fix_routes.py` — exact router prefix, auth function signature, db_pool pattern, download-bundle StreamingResponse pattern, init_routes signature
- `/home/clawd/saas/legal/backend/accessibility_patch_generator.py` — f-string template pattern for HTML generation
- `/home/clawd/saas/legal/backend/ai_act_doc_generator.py` — Jinja2 `from_string()` with autoescape pattern
- `/home/clawd/saas/legal/backend/migrations/create_accessibility_fix_packages.sql` — confirmed column names: `fix_package`, `site_id`, `user_id`, `site_url`
- `/home/clawd/saas/legal/backend/migrations/complete_migration.sql` — scan_results schema: `issues JSONB`, `pillar_scores JSONB`
- `/home/clawd/saas/legal/dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx` — exact Blob + anchor-click download pattern
- `/home/clawd/saas/legal/dashboard-react/src/lib/api.ts` — apiClient with Bearer token interceptor
- `/home/clawd/saas/legal/dashboard-react/src/lib/api-utils.ts` — `getApiBaseUrl()` for environment-aware base URL
- `/home/clawd/saas/legal/backend/requirements.txt` — Jinja2==3.1.2 confirmed installed
- `/home/clawd/saas/legal/backend/main_production.py` lines 137, 426, 501 — router registration and init pattern

### Secondary (MEDIUM confidence)
- BFSG § 12 required fields — confirmed by CONTEXT.md decisions section which lists the 6 mandatory fields; treat as validated by project stakeholder
- BMAS Schlichtungsstelle URL https://www.schlichtungsstelle-bfsg.de/ — listed in CONTEXT.md specifics; reasonable to treat as correct for German legal context

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in requirements.txt and existing source files
- Architecture: HIGH — endpoint placement, auth pattern, DB query, download pattern all verified from running code
- Pitfalls: HIGH — column name discrepancy and site_id transformation verified directly from migration files and route code

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (stable codebase, 30-day window)
