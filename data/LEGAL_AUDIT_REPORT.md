# Legal Text & DSGVO Compliance Module — Audit Report
Generated: 2026-05-01
Scope: /home/clawd/saas/legal/backend/

---

## 1. ai_legal_routes.py — Endpoint Inventory

**File:** `/home/clawd/saas/legal/backend/ai_legal_routes.py`
**Router prefix:** `/api/legal-ai`

| # | Decorator | Path | Auth | Description |
|---|-----------|------|------|-------------|
| 1 | `@router.GET` | `/api/legal-ai/updates` | Optional (user_id via JWT) | Returns latest AI-classified legal law-change updates (max 6, with auto-archiving and background AI classification trigger) |
| 2 | `@router.GET` | `/api/legal-ai/updates/{update_id}/details` | Required | Returns full detail + AI classification for one update, including whether the current user has already given feedback |
| 3 | `@router.POST` | `/api/legal-ai/updates/{update_id}/classify` | Required | Triggers (or forces re-) AI classification of a specific update in the background |
| 4 | `@router.POST` | `/api/legal-ai/feedback` | PUBLIC (no auth) | Receives user feedback on a classification (implicit/explicit types); saves to DB table `ai_classification_feedback` |
| 5 | `@router.GET` | `/api/legal-ai/archive` | Required | Paginated list of archived updates (older than the newest 6), filterable by severity |
| 6 | `@router.GET` | `/api/legal-ai/stats` | Required | Dashboard statistics via DB stored function `get_legal_updates_stats($user_id)` |
| 7 | `@router.GET` | `/api/legal-ai/learning/insights` | Admin only | Returns AI learning insights (pattern analysis) from `ai_classification_feedback` over N days |
| 8 | `@router.GET` | `/api/legal-ai/learning/suggestions` | Admin only | Returns optimization suggestions from the self-learning feedback system |

---

## 2. compliance_engine/checks/ — Summary

### 2a. datenschutz_check.py
**File:** `/home/clawd/saas/legal/backend/compliance_engine/checks/datenschutz_check.py`

**What it checks:**
- Whether a Datenschutzerklärung link exists on the page (using href/text/aria-label/title heuristics, plus a direct HTTP probe of known paths as fallback)
- If the link is missing: generates a full set of `is_missing=True` issues covering all Art. 13–14 DSGVO mandatory fields
- If the link exists: fetches and deep-analyses the privacy page via `HybridValidator`, checking for presence of: `verantwortlicher`, `zwecke`, `rechtsgrundlage`, `speicherdauer`, `betroffenenrechte`, `beschwerderecht`
- Additionally detects: externally-loaded Google Fonts (DSGVO violation per LG München I Az. 3 O 17493/20), US third-party services (GA/GTM, Meta Pixel, HubSpot, Hotjar, Intercom, Salesforce, Stripe) without a recognizable Drittland transfer basis (SCCs / DPF), and specifically flags outdated Privacy Shield references (Schrems II)

**Art. 13/14 fields mapped:** Verantwortlicher (Art. 13 I a), Zwecke (Art. 13 I c), Rechtsgrundlage (Art. 13 I c), Speicherdauer (Art. 13 II a), Betroffenenrechte (Art. 13 II b), Beschwerderecht (Art. 13 II d), Datenschutzbeauftragter (Art. 13 I b), Drittlandtransfer (Art. 13 I f)

**Supports:** Browser rendering (Playwright/headless) for React/Vue/Next.js SPAs via `smart_fetch_html`.

---

### 2b. impressum_check.py
**File:** `/home/clawd/saas/legal/backend/compliance_engine/checks/impressum_check.py`

**What it checks:**
- Whether an Impressum link exists (href/text/aria-label/title heuristics covering: impressum, imprint, legal-notice, site-notice, anbieterkennzeichnung, /legal, /about/legal)
- Also supports browser rendering for JS-heavy sites
- Delegates deep content analysis (TMG §5 required fields) to downstream logic (function body continues beyond line 80; structure mirrors datenschutz_check)
- Issue dataclass `ImpressumIssue` includes: `is_missing` flag to distinguish "page absent" from "field absent within existing page"

---

### 2c. agb_check.py
**File:** `/home/clawd/saas/legal/backend/compliance_engine/checks/agb_check.py`

**What it checks:**
- Whether AGB (Terms of Service) link exists using broad href/text/aria-label heuristics (agb, allgemeine-geschaeftsbedingungen, terms-of-service, nutzungsbedingungen, gtc, /legal/terms)
- First performs shop-signal detection (`_is_shop()`): counts occurrences of 20+ shop keywords (warenkorb, checkout, kaufen, stripe, paypal, etc.) — AGB are only flagged as required if ≥3 signals found
- For non-shop sites, missing AGB is reported as optional hint only
- Issue dataclass `AGBIssue` has same structure as Datenschutz/Impressum

---

## 3. Legal Text Generator Files

### Found:
| File | Type | Description |
|------|------|-------------|
| `/home/clawd/saas/legal/backend/ai_document_generator.py` | AI generator (Claude/OpenRouter) | Generates Impressum (§5 TMG) and Datenschutzerklärung (DSGVO Art. 13–14) as HTML via Claude 3.5 Sonnet; falls back to static templates; saves to DB table `generated_documents` |
| `/home/clawd/saas/legal/backend/legal_document_routes.py` | Route handler | Exposes `POST /api/v2/legal/generate-dpa` — Generates Auftragsverarbeitungsvertrag (AVV) per Art. 28 DSGVO using Jinja2 template; does NOT use AI |

### Not Found:
- `legal_generator*` — no file
- `privacy_policy*` — no file
- `datenschutz_generator*` — no file
- `impressum_generator*` — no file

The generator logic lives inside `ai_document_generator.py` under method names `generate_impressum_document()` and `generate_datenschutz_document()`.

---

## 4. Database Tables — Legal Texts

### Tables matching legal/datenschutz/impressum/text/document (from `\dt`):

| Table | Notes |
|-------|-------|
| `legal_change_impacts` | Impact assessments for detected legal changes |
| `legal_change_notifications` | Notifications sent to users for legal changes |
| `legal_changes` | Tracked legal changes/updates |
| `legal_monitoring_logs` | Logs of legal monitoring runs |
| `legal_news` | Fetched legal news items |
| `legal_updates` | Core table — law-change updates with AI classification; see schema below |
| `legal_updates_archive` | Archive of older updates |

### `legal_updates` table schema:

| Column | Type | Notes |
|--------|------|-------|
| id | integer | PK |
| update_type | varchar | |
| title | varchar | |
| description | text | |
| severity | varchar | critical / warning / info |
| action_required | boolean | |
| source | varchar | |
| published_at | timestamp | |
| created_at | timestamp | |
| effective_date | date | |
| url | text | |
| classification_id | integer | FK to ai_classifications |
| auto_classified | boolean | |
| classification_override | boolean | |

### CRITICAL GAP — No `generated_documents` table:
`ai_document_generator._save_document()` does `INSERT INTO generated_documents (user_id, doc_type, content, audit_trail, created_at)` but **this table does NOT exist** in the database. The `\dt` output shows no such table. AI-generated Impressum and Datenschutzerklärung cannot be persisted — the method will throw a PostgreSQL error on every save attempt.

---

## 5. Deep Checks on ai_legal_routes.py

### 5a. Endpoint for generating Datenschutzerklärung (privacy policy)?
**NO.** `ai_legal_routes.py` contains zero generation endpoints. It is exclusively a legal-updates/classification/feedback router. The generation capability lives in `ai_document_generator.py` (class `AIDocumentGenerator`), but there is **no route file that exposes it as an HTTP endpoint** (no `@router.POST /generate-datenschutz` or equivalent anywhere in the backend route files audited). `legal_document_routes.py` only exposes the AVV/DPA generator.

### 5b. Endpoint for generating Impressum?
**NO.** Same situation as above — `ai_document_generator.generate_impressum_document()` exists as a Python method but is not wired to any API route.

### 5c. Date/staleness check (last_updated / created_at comparison)?
**NO.** Neither `ai_legal_routes.py` nor the checks contain any logic that:
- Compares a document's `created_at` / `last_updated` against a threshold
- Warns if a Datenschutzerklärung or Impressum is older than N days
- Checks the `effective_date` column of `legal_updates` against today's date for user-document staleness

The `legal_updates.effective_date` column exists in the DB schema but is never used for staleness detection in the routes — it is only passed through as a display field.

### 5d. Art. 13/14 DSGVO validation?
**PARTIAL — only in the check layer, not in the generator.**
- `datenschutz_check.py` validates an *existing* remote URL for Art. 13/14 fields (see section 2a above).
- `ai_document_generator._build_datenschutz_prompt()` instructs Claude to include Art. 13/14 sections, but there is **no post-generation validation** that verifies the AI output actually contains all mandatory fields before saving/returning.
- `ai_legal_routes.py` itself has no Art. 13/14 validation at all.

### 5e. Feedback endpoint — does it save to DB?
**YES — with caveats.**

- **Endpoint:** `POST /api/legal-ai/feedback` (public, no authentication)
- **What it does:** Accepts `FeedbackRequest` (update_id, classification_id, feedback_type, user_action, time_to_action, context_data); delegates to `ai_feedback_learning.AIFeedbackLearning.record_feedback()`
- **DB save:** Inserts into `ai_classification_feedback` table: `(user_id, update_id, classification_id, feedback_type, user_action, time_to_action, context_data, created_at)` — **YES, saves to DB**
- **After save:** Calls `_trigger_learning_if_needed()` asynchronously to potentially update AI prompts
- **Caveat 1:** `user_id` is not extracted from the JWT in this endpoint — the function signature is `async def submit_feedback(feedback: FeedbackRequest, user_id: Optional[int] = None)` — `user_id` is never injected because `Depends(get_current_user_id)` is absent. Every feedback record is saved with `user_id=None`.
- **Caveat 2:** The endpoint is fully public (no auth). Any unauthenticated caller can flood the feedback table.

---

## 6. Existing Features Summary

| Feature | Status | File(s) |
|---------|--------|---------|
| Compliance check — Datenschutzerklärung (link + content) | PRESENT | `compliance_engine/checks/datenschutz_check.py` |
| Compliance check — Impressum (link detection) | PRESENT | `compliance_engine/checks/impressum_check.py` |
| Compliance check — AGB (shop-conditional) | PRESENT | `compliance_engine/checks/agb_check.py` |
| AI classification of legal law-changes | PRESENT | `ai_legal_routes.py`, `ai_legal_classifier.py` |
| Legal updates feed (classified, paginated) | PRESENT | `GET /api/legal-ai/updates` |
| Archive of old updates | PRESENT | `GET /api/legal-ai/archive` |
| Stats dashboard | PRESENT | `GET /api/legal-ai/stats` |
| Feedback collection (saves to DB) | PRESENT (broken user_id) | `POST /api/legal-ai/feedback`, `ai_feedback_learning.py` |
| Self-learning insights (admin) | PRESENT | `GET /api/legal-ai/learning/insights` |
| AI-based Impressum generator (method) | PRESENT, NOT EXPOSED | `ai_document_generator.py` |
| AI-based Datenschutzerklärung generator (method) | PRESENT, NOT EXPOSED | `ai_document_generator.py` |
| AVV/DPA generator (Art. 28 DSGVO) | PRESENT, EXPOSED | `POST /api/v2/legal/generate-dpa`, `legal_document_routes.py` |
| Browser rendering for JS sites | PRESENT | `compliance_engine/browser_renderer.py` |
| Google Fonts DSGVO violation detection | PRESENT | `datenschutz_check.py` |
| US Drittlandtransfer / Schrems II detection | PRESENT | `datenschutz_check.py` |

---

## 7. Critical Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| `generated_documents` table missing in DB | CRITICAL | `ai_document_generator._save_document()` will crash — table does not exist |
| No HTTP endpoint for Impressum generation | HIGH | `AIDocumentGenerator.generate_impressum_document()` is never called from any route |
| No HTTP endpoint for Datenschutzerklärung generation | HIGH | `AIDocumentGenerator.generate_datenschutz_document()` is never called from any route |
| Feedback endpoint has no user_id injection | HIGH | Every feedback record saved with `user_id=None`; Depends(get_current_user_id) missing from submit_feedback signature |
| No date/staleness check on user's legal texts | HIGH | No logic anywhere checks if a user's Datenschutzerklärung or Impressum is outdated |
| Art. 13/14 post-generation validation absent | MEDIUM | AI-generated Datenschutzerklärung is not validated for mandatory fields before delivery |
| Feedback endpoint is fully public (no rate-limit) | MEDIUM | Unauthenticated flood possible on `POST /api/legal-ai/feedback` |
| `effective_date` never used for user alerts | MEDIUM | Column exists in `legal_updates` but is never compared to trigger staleness warnings |
| Impressum deep content check (TMG §5 fields) | MEDIUM | `impressum_check.py` detects the link but deeper TMG §5 field validation (beyond line 80) needs verification |
| `recommended_actions` field always `None` | LOW | `ClassifiedUpdateResponse.recommended_actions` is hardcoded to `None` in both list and archive endpoints (TODO comment in code) |
| Archive query has a bug (`count_query` undefined) | MEDIUM | `get_archive()` references `count_query` variable that is never initialized — endpoint will throw NameError at runtime |

---

## 8. Missing DSGVO Art. 13/14 Fields

The check layer (`datenschutz_check.py`) covers these Art. 13/14 fields:

| DSGVO Field | Art. Reference | Checked | Generated (Prompt) | Post-Gen Validated |
|-------------|---------------|---------|-------------------|--------------------|
| Verantwortlicher (Name + Kontakt) | Art. 13 I a | YES | YES | NO |
| Datenschutzbeauftragter | Art. 13 I b | YES (warning) | YES | NO |
| Zwecke der Verarbeitung | Art. 13 I c | YES | YES | NO |
| Rechtsgrundlage (Art. 6 DSGVO) | Art. 13 I c | YES | YES | NO |
| Berechtigte Interessen | Art. 13 I d | NO | PARTIAL | NO |
| Empfänger / Kategorien von Empfängern | Art. 13 I e | NO | PARTIAL | NO |
| Drittlandtransfer + Garantien | Art. 13 I f | YES (heuristic) | YES | NO |
| Speicherdauer / Kriterien | Art. 13 II a | YES | YES | NO |
| Betroffenenrechte (Auskunft, Berichtigung, Löschung, Einschränkung, Portabilität, Widerspruch) | Art. 13 II b | YES (grouped) | YES | NO |
| Widerrufsrecht (Einwilligung) | Art. 13 II c | NO | YES | NO |
| Beschwerderecht (Aufsichtsbehörde) | Art. 13 II d | YES | YES | NO |
| Automatisierte Entscheidungsfindung / Profiling | Art. 13 II f | NO | NO | NO |
| Daten nicht direkt erhoben (Art. 14 specific) | Art. 14 II f | NO | NO | NO |

**Not covered at all anywhere:** Art. 13 I d (berechtigte Interessen detail), Art. 13 I e (Empfänger granularity), Art. 13 II c (Widerrufsrecht in check layer), Art. 13 II f (Profiling), Art. 14 II f (indirect data collection source)

---

## 9. File Path Reference

| What | Path |
|------|------|
| AI Legal Updates routes | `/home/clawd/saas/legal/backend/ai_legal_routes.py` |
| AI Document Generator (Impressum + DS) | `/home/clawd/saas/legal/backend/ai_document_generator.py` |
| AVV/DPA route | `/home/clawd/saas/legal/backend/legal_document_routes.py` |
| Feedback learning system | `/home/clawd/saas/legal/backend/ai_feedback_learning.py` |
| Datenschutz compliance check | `/home/clawd/saas/legal/backend/compliance_engine/checks/datenschutz_check.py` |
| Impressum compliance check | `/home/clawd/saas/legal/backend/compliance_engine/checks/impressum_check.py` |
| AGB compliance check | `/home/clawd/saas/legal/backend/compliance_engine/checks/agb_check.py` |
| Datenschutz AI prompt | `/home/clawd/saas/legal/backend/compliance_engine/prompts/datenschutz_prompt.txt` |
| Impressum AI prompt | `/home/clawd/saas/legal/backend/compliance_engine/prompts/impressum_prompt.txt` |
| DB migration — legal updates | `/home/clawd/saas/legal/backend/migrations/migration_legal_changes.sql` |
