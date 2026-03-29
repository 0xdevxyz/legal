# Codebase Concerns

**Analysis Date:** 2026-03-29

---

## Security Considerations

**OAuth tokens exposed in URL query parameters:**
- Risk: Access and refresh tokens are transmitted via URL query string (`?access_token=...&refresh_token=...`) in the OAuth callback, not via URL fragment as originally intended. This makes tokens visible in server logs, browser history, and `Referer` headers.
- Files: `backend/auth_routes.py:324`, `dashboard-react/src/app/auth/callback/page.tsx:18-19`
- Current mitigation: Code comment in `auth_routes.py` says "via URL fragment" but the frontend reads them from `searchParams` (query string), not `window.location.hash`.
- Recommendation: Backend must redirect to `#access_token=...` fragment; frontend must read from `window.location.hash`, not `useSearchParams`.

**Admin endpoints lack access control:**
- Risk: Several "admin-only" endpoints enforce no privilege check. Any authenticated user can call them.
- Files: `backend/ai_legal_routes.py:762`, `backend/ai_legal_routes.py:803`, `backend/legal_change_routes.py:363`
- Current mitigation: `# TODO: Admin-Check einbauen` comments only. The `require_admin` dependency exists in `backend/dependencies.py:215` but is not applied to these routes.
- Recommendation: Apply `Depends(require_admin)` from `backend/dependencies.py` to all admin routes immediately.

**`legal_ai_routes.py` authentication is a stub returning a fake user:**
- Risk: `/api/legal-ai/*` endpoints return `{"user_id": "test-user"}` for all requests regardless of token validity.
- Files: `backend/legal_ai_routes.py:19-22`
- Current mitigation: None — the route module is actively included in production.
- Recommendation: Replace stub `get_current_user` with the real dependency from `backend/dependencies.py` or `backend/auth_routes.py`.

**Dynamic SQL query construction via f-string concatenation:**
- Risk: Two endpoints build `UPDATE` queries dynamically by concatenating field names from user-controlled input patterns. If field allowlist validation fails, column injection is possible.
- Files: `backend/ab_test_routes.py:413-419`, `backend/cookie_compliance_routes.py:805-813`
- Current mitigation: Values are parameterized (`$1`, `$2`), but column names come from Pydantic model field names. Risk is low but non-zero if model field names are ever derived from external input.
- Recommendation: Explicitly allowlist permitted column names before constructing the f-string query.

**Add-on Stripe webhook secret defaults to empty string:**
- Risk: `STRIPE_WEBHOOK_SECRET_ADDONS` defaults to `""` (empty string), meaning webhook signature verification silently passes if the env var is not set.
- Files: `backend/addon_payment_routes.py:29`
- Current mitigation: Unlike `stripe_routes.py`, this module does not fail-fast when the secret is missing.
- Recommendation: Add the same `RuntimeError` guard present in `backend/stripe_routes.py:38-40`.

**Refresh token expiry comparison uses naive `datetime.utcnow()`:**
- Risk: `auth_service.py` stores `expires_at` using `datetime.utcnow()` (naive UTC) but the database may return timezone-aware datetimes, causing comparison failures that silently bypass expiry checks.
- Files: `backend/auth_service.py:141`, `backend/auth_service.py:181`
- Current mitigation: None; the `_utcnow()` helper using `timezone.utc` exists but is only used in JWT creation, not in refresh token storage/comparison.
- Recommendation: Use `datetime.now(timezone.utc)` consistently throughout `auth_service.py`.

---

## Tech Debt

**Duplicate JWT implementation (main_production.py vs AuthService):**
- Issue: `backend/main_production.py` contains a standalone `create_jwt_token()` / `verify_jwt_token()` / `get_current_user()` that duplicates logic already centralized in `backend/auth_service.py` and `backend/dependencies.py`. The standalone version creates tokens without `aud`/`iss` claims, making it incompatible with the service-based version.
- Files: `backend/main_production.py:628-667`
- Impact: Tokens created by the old function are rejected by `AuthService.verify_token()`; risk of incorrect auth path being exercised.
- Fix approach: Remove the standalone helpers; route all auth through `AuthService` / `backend/dependencies.py:get_current_user`.

**Duplicate Sentry SDK initialization:**
- Issue: `backend/main_production.py` initializes Sentry twice — once at line 23 and once via commented-out duplicate block at lines 50-57, indicating a hasty copy-paste fix.
- Files: `backend/main_production.py:22-57`
- Impact: None currently, but confusing and fragile.
- Fix approach: Remove the commented-out duplicate block entirely.

**Parallel route files for the same feature (v1/v2/simple variants):**
- Issue: Three versions of the legal-update classifier exist as standalone scripts (`backend/classify_new_updates.py`, `backend/classify_new_updates_v2.py`, `backend/classify_new_updates_v3.py`). A `_simple` route variant (`backend/erecht24_routes_v2_simple.py`) also exists alongside the full `backend/erecht24_routes_v2.py` but is not mounted in production.
- Files: `backend/classify_new_updates.py`, `backend/classify_new_updates_v2.py`, `backend/classify_new_updates_v3.py`, `backend/erecht24_routes_v2_simple.py`
- Impact: Unclear which version is canonical; dead code accumulates.
- Fix approach: Delete superseded versions; keep only `classify_new_updates_v3.py` or fold into the proper service.

**Module-level global `db_pool = None` anti-pattern across 15+ route files:**
- Issue: At least 15 route modules declare `db_pool = None` at module scope and expect `main_production.py` to set the attribute at startup. If startup order changes or a module is imported before startup completes, all DB calls fail with `AttributeError` or `NoneType` errors.
- Files: `backend/auth_routes.py:21`, `backend/website_routes.py:18`, `backend/widget_routes.py:25`, `backend/fix_routes.py:27`, `backend/ab_test_routes.py:18`, `backend/cookie_compliance_routes.py:25`, `backend/public_routes.py:36`, `backend/legal_ai_routes.py:28`, and 7 more.
- Impact: Fragile startup; `dependencies.py` solves this correctly but is only partially adopted.
- Fix approach: Migrate all route modules to use `Depends(get_db)` from `backend/dependencies.py` instead of module-level globals.

**Extensive use of bare `print()` instead of structured logging:**
- Issue: 435 occurrences of `print()` across 45 backend files. These bypass the `logging` infrastructure and are invisible to log aggregators (Sentry, Prometheus).
- Files: `backend/main_production.py` (41 occurrences), `backend/cronjobs/legal_news_cronjob.py` (18 occurrences), `backend/setup_erecht24_webhook.py` (50 occurrences), and 42 more files.
- Impact: Production log analysis is incomplete; errors during startup are not captured by Sentry.
- Fix approach: Replace `print()` calls with `logger.info()` / `logger.warning()` / `logger.error()`.

**AI document generator outputs static TODO-placeholder HTML:**
- Issue: `backend/ai_act_doc_generator.py` generates EU AI Act documentation filled with literal `[TODO: ...]` placeholder strings instead of dynamically populated content.
- Files: `backend/ai_act_doc_generator.py:189-399` (25+ TODO placeholders)
- Impact: Feature is effectively non-functional — users receive a template, not real documentation.
- Fix approach: Implement actual AI-driven content generation or clearly mark the feature as "beta/template mode" in the UI.

**Unimplemented Stripe add-on lifecycle callbacks:**
- Issue: `handle_addon_subscription_updated`, `handle_addon_subscription_cancelled`, and `handle_addon_payment_failed` are webhook handlers that contain only `# TODO:` comments and log statements. Subscription cancellations are silently ignored.
- Files: `backend/addon_payment_routes.py:432-449`
- Impact: Cancelled add-on subscriptions are not revoked in the database; users retain access after cancellation.
- Fix approach: Implement database updates in all three handlers using the `stripe_subscription_id`.

**Unimplemented analytics storage:**
- Issue: Widget feedback endpoint explicitly skips storing analytics data with a commented-out `await store_widget_analytics()` call.
- Files: `backend/public_routes.py:1395`
- Impact: No analytics data is ever stored; the widget feedback loop is broken.
- Fix approach: Implement `store_widget_analytics` or remove the endpoint.

---

## Known Bugs

**`auth/callback` page reads tokens from query string, not URL fragment:**
- Symptoms: On OAuth login, tokens may be silently unavailable if the URL routing strips query parameters; also tokens are exposed in browser history.
- Files: `dashboard-react/src/app/auth/callback/page.tsx:18-19`
- Trigger: Any Google/Apple OAuth sign-in.
- Workaround: Users can manually append `?access_token=...` to the URL; not viable in production.

**`datetime.utcnow()` timezone mismatch can bypass session expiry:**
- Symptoms: Expired refresh tokens may not be invalidated if asyncpg returns timezone-aware timestamps.
- Files: `backend/auth_service.py:181`
- Trigger: Depends on PostgreSQL timezone configuration; affects `refresh_access_token()`.
- Workaround: None.

**Debug `console.log` statements shipped to production in `WebsiteAnalysis.tsx`:**
- Symptoms: Browser console is polluted with `📊 Final analysisData:`, `🔍 PERSISTENCE DEBUG:` output on every render cycle.
- Files: `dashboard-react/src/components/dashboard/WebsiteAnalysis.tsx:51-91`
- Trigger: Every page load when a scan result is displayed.
- Workaround: Suppress in browser DevTools; no code fix applied.

---

## Performance Bottlenecks

**Repeated `SELECT *` queries throughout backend:**
- Problem: Over 40 instances of `SELECT *` queries retrieve entire row sets when only specific columns are needed.
- Files: `backend/main_production.py:946,990,1149,1523`, `backend/auth_service.py:31,106`, `backend/legal_change_routes.py:84,136,178,187,193`, `backend/ai_legal_routes.py:419,430,502,852`, and 30+ more.
- Cause: Convenience during development; never optimized.
- Improvement path: Replace with explicit column lists to reduce data transfer and improve query plan coverage.

**Background worker polls database every 5 seconds on a tight loop:**
- Problem: `BackgroundWorker` runs an infinite `while` loop with `asyncio.sleep(5)` querying the `fix_jobs` table constantly.
- Files: `backend/background_worker.py:31-37`
- Cause: No event-based trigger or message queue.
- Improvement path: Add `LISTEN/NOTIFY` PostgreSQL triggers on the `fix_jobs` table, or migrate to a proper queue (Redis, Celery).

**API URL detection runs at every request via function call:**
- Problem: `getApiBaseURL()` is defined as an inline function and invoked once at module init in `api.ts`, but the same hostname-detection logic is duplicated across at least 6 separate files (`lib/api.ts`, `lib/api-utils.ts`, `lib/constants.ts`, `lib/ai-compliance-api.ts`, `components/SocialLoginButtons.tsx`, `app/register/page.tsx`).
- Files: `dashboard-react/src/lib/api.ts:5-28`, `dashboard-react/src/lib/api-utils.ts:21-32`, `dashboard-react/src/lib/constants.ts:12-20`, `dashboard-react/src/lib/ai-compliance-api.ts:28-37`, `dashboard-react/src/components/SocialLoginButtons.tsx:14-21`, `dashboard-react/src/app/register/page.tsx:16-23`
- Cause: No single source of truth for the API base URL.
- Improvement path: Export one `getApiBaseURL()` from `lib/api-utils.ts` and import it everywhere; controlled by a single `NEXT_PUBLIC_API_URL` env var.

---

## Fragile Areas

**`main_production.py` startup sequence (1847 lines):**
- Files: `backend/main_production.py`
- Why fragile: The entire application startup, service initialization, dependency wiring, and some inline route definitions are packed into a single file. Global state is mutated sequentially; any import failure or unhandled exception in `startup()` leaves the application partially initialized.
- Safe modification: Only add new startup steps at the bottom of the `@app.on_event("startup")` handler; never reorder existing steps without testing the full startup.
- Test coverage: No automated startup integration test.

**`cookie_compliance_routes.py` (2311 lines, largest file):**
- Files: `backend/cookie_compliance_routes.py`
- Why fragile: Monolithic route file with 32 endpoints, no rate limiting, and complex JSONB config mutation logic. The `update_query` is constructed with f-string column concatenation (see Security section).
- Safe modification: Any schema change to `cookie_banner_configs` requires manual audit of all 32 endpoints.
- Test coverage: No unit tests; only indirect coverage through E2E smoke test.

**Dual Stripe webhook handlers (three separate files):**
- Files: `backend/payment_routes.py`, `backend/stripe_routes.py`, `backend/main_production.py:1614`
- Why fragile: Three separate endpoint handlers consume Stripe webhooks, each with partial event coverage. It is unclear which one handles which event type in production, and the same event may be processed by multiple handlers.
- Safe modification: Before adding any Stripe webhook logic, map all three files to determine which events are handled where.
- Test coverage: None.

**Migration system split between Alembic (1 migration) and raw SQL (19 files):**
- Files: `backend/alembic/versions/20251125_0001_initial_schema.py`, `backend/migrations/*.sql`
- Why fragile: Alembic is configured but only has one version. All subsequent schema changes are raw SQL files applied manually. There is no migration order record, making it impossible to reproduce a fresh database reliably.
- Safe modification: Apply new schema changes only after determining current DB state manually.
- Test coverage: None.

---

## Test Coverage Gaps

**Frontend (dashboard-react) has no unit or integration tests:**
- What's not tested: All React components, API client code, auth context, compliance data transformations, store logic.
- Files: `dashboard-react/src/` (entire directory)
- Risk: UI regressions ship silently; the `WebsiteAnalysis.tsx` persistence logic (89 lines of useEffect chains) has no coverage.
- Priority: High

**Backend route handlers for AI compliance, cookie compliance, and widget are untested:**
- What's not tested: `backend/ai_compliance_routes.py` (27 endpoints), `backend/cookie_compliance_routes.py` (32 endpoints), `backend/widget_routes.py`.
- Files: `backend/tests/` — no corresponding test files for these modules.
- Risk: Payment, cookie consent, and AI compliance features can regress undetected.
- Priority: High

**No integration tests for the Stripe payment flows:**
- What's not tested: Checkout session creation, webhook event processing, subscription lifecycle, add-on cancellation (which is also unimplemented — see Tech Debt section).
- Files: `backend/stripe_routes.py`, `backend/payment_routes.py`, `backend/addon_payment_routes.py`
- Risk: Revenue-critical paths are untested.
- Priority: High

**E2E tests only cover 3 trivial smoke checks:**
- What's not tested: Login flow, scan flow, fix application, cookie compliance UI, Stripe checkout.
- Files: `dashboard-react/tests/e2e/smoke.spec.ts`
- Risk: Core user journeys break without any test signal.
- Priority: Medium

---

## Scaling Limits

**`fix_jobs` polling worker (no queue):**
- Current capacity: Processes 5 jobs per poll cycle (every 5 seconds), single asyncio task per process.
- Limit: Does not scale horizontally; multiple worker processes would double-process jobs without a locking mechanism.
- Scaling path: Add `FOR UPDATE SKIP LOCKED` to the job query in `backend/background_worker.py:48`, or migrate to a Redis-backed queue.

**In-memory news fetch on startup:**
- Current capacity: Fetches all RSS feeds on every server start if cache is >6 hours old.
- Limit: With many feeds and slow upstreams, cold starts take 30+ seconds; crashes during fetch block startup.
- Scaling path: Move news fetching entirely to `backend/cronjobs/legal_news_cronjob.py`; remove from startup hook in `backend/main_production.py:370-399`.

---

## Dependencies at Risk

**Firebase Admin SDK used but optional:**
- Risk: `backend/firebase_auth.py` initializes Firebase at import time; if env vars are missing the module silently returns `None`. Routes that call `verify_firebase_token` will return HTTP 503 without error logging.
- Impact: Social login (Google/Apple) silently unavailable if Firebase env vars are not set.
- Migration plan: Add a startup health check that warns explicitly if Firebase is unconfigured.

**`legal_ai_routes` and `ai_legal_routes` both mounted simultaneously:**
- Risk: `backend/legal_ai_routes.py` (unauthenticated stub) and `backend/ai_legal_routes.py` (real authenticated routes) are both imported and initialized in `backend/main_production.py:118,467`. They operate on the same database tables but have different auth guards.
- Impact: The stub routes at `/api/legal-ai/*` bypass authentication entirely, potentially exposing data at overlapping endpoints.
- Migration plan: Remove `legal_ai_routes.py` entirely; consolidate all legal-AI endpoints into `ai_legal_routes.py`.

---

*Concerns audit: 2026-03-29*
