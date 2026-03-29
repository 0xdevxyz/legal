# Architecture

**Analysis Date:** 2026-03-29

## Pattern Overview

**Overall:** Multi-tier SaaS platform with a monolithic FastAPI backend, two separate Next.js 14 frontends (landing + dashboard), and a PostgreSQL + Redis data layer. All components are containerized and connected via a Docker bridge network with Nginx reverse proxy SSL termination.

**Key Characteristics:**
- Backend is a single FastAPI process exposing 30+ router modules, all initialized at startup with injected dependencies (db_pool, auth_service)
- Frontend is split into two independent Next.js apps: `landing-react` (marketing, unauthenticated) and `dashboard-react` (authenticated SaaS app)
- No service mesh or microservices; all business logic lives in the single backend process
- Services communicate exclusively over HTTP REST — the dashboard fetches `https://api.complyo.de` via axios with JWT Bearer token
- Background processing runs in-process via `BackgroundWorker` (asyncio task loop polling every 5 seconds)

## Layers

**API Layer (Route Handlers):**
- Purpose: Accept HTTP requests, validate inputs, delegate to services
- Location: `backend/*_routes.py` (e.g., `backend/auth_routes.py`, `backend/cookie_compliance_routes.py`)
- Contains: FastAPI `APIRouter` instances, Pydantic request/response models, rate-limit decorators
- Depends on: Service layer, dependency injection (`backend/dependencies.py`)
- Used by: Frontend API clients, external webhooks

**Service Layer:**
- Purpose: Business logic, external API orchestration
- Location: `backend/auth_service.py`, `backend/payment/stripe_service.py`, `backend/news_service.py`, `backend/email_service.py`, `backend/erecht24_service.py`, `backend/erecht24_rechtstexte_service.py`
- Contains: Classes initialized with `asyncpg.Pool`, async methods, no HTTP knowledge
- Depends on: Database layer, external SDKs (Stripe, eRecht24, Firebase)
- Used by: Route handlers

**Compliance Engine:**
- Purpose: Scan websites for DSGVO/TTDSG/accessibility violations and generate AI fixes
- Location: `backend/compliance_engine/` (scanner, fixer, deep_scanner, workflow_engine, checks/, prompts/)
- Contains: `ComplianceScanner`, `AIComplianceFixer`, `DeepScanner`, `WorkflowEngine`, modular check functions
- Depends on: OpenRouter AI API (via `OPENROUTER_API_KEY`), aiohttp for crawling, BeautifulSoup for HTML parsing
- Used by: Route handlers in `backend/fix_routes.py`, `backend/dashboard_routes.py`

**AI Fix Engine:**
- Purpose: Context-aware AI generation of personalized compliance code fixes
- Location: `backend/ai_fix_engine/` (intelligent_analyzer, smart_fix_generator, unified_fix_engine, handlers/)
- Contains: `IntelligentAnalyzer` (calls `anthropic/claude-3.5-sonnet` via OpenRouter), `SmartFixGenerator`, `BackgroundWorker`
- Depends on: OpenRouter API, eRecht24 service
- Used by: `backend/background_worker.py`, fix route handlers

**Database Layer:**
- Purpose: Async PostgreSQL access
- Location: `backend/dependencies.py` (pool management), `backend/database_service.py` (lead management wrapper)
- Contains: `asyncpg.Pool` global singleton, `get_db()` FastAPI dependency, `DatabaseService` class with in-memory fallback
- Pattern: Raw asyncpg queries — no ORM. Queries are inline SQL strings in service/route files.
- Used by: All services and route handlers

**Frontend API Client Layer:**
- Purpose: Typed HTTP client for dashboard → backend communication
- Location: `dashboard-react/src/lib/api.ts`, `dashboard-react/src/lib/ai-compliance-api.ts`, `dashboard-react/src/lib/auth-api.ts`, `dashboard-react/src/lib/api-utils.ts`
- Contains: axios instance with request interceptors for Bearer token injection and 401 → refresh-token retry
- Depends on: `localStorage` for `access_token` and `refresh_token`
- Used by: React components, hooks, pages

**State Management Layer (Frontend):**
- Purpose: Client-side state for dashboard data
- Location: `dashboard-react/src/stores/dashboard.ts`, `dashboard-react/src/contexts/AuthContext.tsx`
- Contains: Zustand store (`useDashboardStore`) for website/metrics/compliance state; React Context (`AuthContext`) for auth identity
- Pattern: Zustand with `subscribeWithSelector` middleware; auto token refresh every 50 minutes via `useEffect`

## Data Flow

**Compliance Scan Flow:**

1. User submits URL via dashboard page (e.g., `dashboard-react/src/app/`)
2. Dashboard axios client POSTs to `/api/scan` with Bearer token
3. `backend/fix_routes.py` or `backend/dashboard_routes.py` validates JWT via `get_current_user` dependency
4. Route handler calls `ComplianceScanner.scan()` in `backend/compliance_engine/scanner.py`
5. Scanner crawls the URL with aiohttp/BeautifulSoup and delegates to modular checks in `backend/compliance_engine/checks/`
6. Issues are grouped by `IssueGrouper`, scored by `RiskCalculator`
7. Result written to `scan_history` PostgreSQL table
8. Response returned to frontend; frontend updates Zustand store

**AI Fix Generation Flow:**

1. Route handler creates a `fix_jobs` record in PostgreSQL (status=pending)
2. `BackgroundWorker` (running as asyncio task in the same process) polls `fix_jobs` every 5 seconds
3. Worker calls `SmartFixGenerator` → `IntelligentAnalyzer.analyze_and_generate_fixes()`
4. `IntelligentAnalyzer` sends request to OpenRouter (`anthropic/claude-3.5-sonnet`)
5. Generated fix is written back to the database and job status set to `completed`
6. Frontend polls or receives the fix via subsequent GET request

**Authentication Flow:**

1. User POSTs credentials to `/api/auth/login`
2. `AuthService.authenticate()` verifies bcrypt hash against `users` table
3. JWT access token (7-day) and refresh token (30-day) are returned
4. Frontend stores both in `localStorage`; axios interceptor attaches Bearer token to every request
5. On 401, interceptor auto-calls `/api/auth/refresh` with refresh token
6. OAuth (Google/Apple) redirects to `/api/auth/oauth/callback`, backend redirects to `/auth/callback` page with tokens in query string; `dashboard-react/src/app/auth/callback/page.tsx` stores them in localStorage

**State Management:**
- Server state: PostgreSQL (users, websites, scans, fixes, limits, subscriptions)
- Cache: Redis (optional; graceful degradation if unavailable)
- Client state: Zustand store in `dashboard-react/src/stores/dashboard.ts`
- Auth tokens: `localStorage` (access_token, refresh_token, user JSON)

## Key Abstractions

**FastAPI Dependency Injection:**
- Purpose: Provides db_pool, redis, auth_service, current_user to route handlers
- Location: `backend/dependencies.py`
- Pattern: `Depends(get_db)`, `Depends(get_current_user)`, `Depends(require_admin)` — async functions returning singletons or validated JWT payloads

**Route Module Pattern:**
- Purpose: Each feature domain has its own `*_routes.py` file registered on startup
- Examples: `backend/auth_routes.py`, `backend/cookie_compliance_routes.py`, `backend/ai_compliance_routes.py`, `backend/legal_change_routes.py`
- Pattern: Module exposes a `router = APIRouter(prefix="/api/...", tags=[...])` and has module-level globals (`db_pool`, `auth_service`) injected by `main_production.py` startup event

**Service Singleton Pattern:**
- Purpose: Services hold db_pool and are instantiated once at startup
- Examples: `AuthService(db_pool)`, `StripeService(db_pool)`, `NewsService(db_pool)`
- Pattern: Global variable in `main_production.py`; injected into route modules as `module.service = instance`

**Compliance Check Modules:**
- Purpose: Pluggable rule-based and AI-enhanced compliance checks
- Location: `backend/compliance_engine/checks/`
- Pattern: Functions `check_<area>_compliance(soup, url, ...) -> List[ComplianceIssue]` imported by `scanner.py`

**Plan Guard (Frontend):**
- Purpose: Restricts UI routes based on user subscription plan
- Location: `dashboard-react/src/components/guards/PlanGuard.tsx`
- Pattern: Wraps page content; reads `user.plan_type` from `AuthContext`

## Entry Points

**Backend API Server:**
- Location: `backend/main_production.py`
- Triggers: `uvicorn backend.main_production:app` (via `backend/Dockerfile`)
- Responsibilities: Creates FastAPI app, configures CORS/rate-limiting/middleware, runs `startup_event()` which initializes db_pool, services, and registers all routers

**Dashboard Frontend:**
- Location: `dashboard-react/src/app/layout.tsx`
- Triggers: Next.js 14 App Router; root layout wraps all pages in `<Providers>` (AuthContext + Zustand)
- Responsibilities: Theme initialization, cookie banner script injection, global layout

**Landing Frontend:**
- Location: `landing-react/src/app/layout.tsx`, `landing-react/src/app/page.tsx`
- Triggers: Next.js 14 App Router
- Responsibilities: Marketing pages, A/B test routing via `landing-react/src/app/ABTestRouter.tsx`

**Background Worker:**
- Location: `backend/background_worker.py`
- Triggers: `start_background_worker()` called in `startup_event()`; runs as asyncio task inside the FastAPI process
- Responsibilities: Polls `fix_jobs` table every 5 seconds; processes pending AI fix generation jobs

**Cronjobs:**
- Location: `backend/cronjobs/legal_news_cronjob.py`, `backend/cronjobs/fetch_news.py`
- Triggers: System crontab (installed via `backend/cronjobs/install_crontab.sh`)
- Responsibilities: Fetching external legal news RSS feeds into the database

## Error Handling

**Strategy:** Raise `HTTPException` with appropriate status codes in route handlers; services raise raw exceptions that routes catch and re-raise as `HTTPException`. Sentry SDK captures unhandled exceptions if `SENTRY_DSN` is set.

**Patterns:**
- Route handlers use `try/except Exception as e` blocks returning `{"error": str(e)}` with `500` status
- Services use `raise HTTPException(...)` directly for business-rule violations
- Frontend axios interceptor catches 401 and retries once with refresh token; network errors retry once after 1s delay
- `DatabaseService` has in-memory fallback if PostgreSQL is unreachable (lead management only)

## Cross-Cutting Concerns

**Logging:** Python `logging` module throughout backend; `logger = logging.getLogger(__name__)` per module. Frontend uses `console.error` / `console.log`.

**Validation:** Pydantic `BaseModel` on all request bodies. Raw SQL with parameterized `$1`, `$2` placeholders (asyncpg).

**Authentication:** JWT HS256 with audience `complyo-api` and issuer set to `FRONTEND_URL`. All protected endpoints use `Depends(get_current_user)`. Optional auth via `Depends(get_current_user_optional)`. Admin routes use `Depends(require_admin)`.

**Observability:** Prometheus metrics counter/histogram via middleware at `backend/main_production.py` lines 231–239; Sentry error tracking initialized at startup; `X-Request-ID` header added to every response.

**Rate Limiting:** `slowapi` limiter at `10r/s` general, `5r/s` for auth endpoints. Configured in `backend/main_production.py` and `nginx/production.conf`.

---

*Architecture analysis: 2026-03-29*
