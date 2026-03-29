# Codebase Structure

**Analysis Date:** 2026-03-29

## Directory Layout

```
legal/                              # Repository root
├── backend/                        # FastAPI Python backend
│   ├── main_production.py          # App entry point — registers all routers
│   ├── dependencies.py             # FastAPI DI: db pool, auth, redis
│   ├── auth_service.py             # JWT auth + user management
│   ├── auth_routes.py              # /api/auth/* endpoints
│   ├── database_service.py         # Lead management DB wrapper (with fallback)
│   ├── email_service.py            # SMTP email sender
│   ├── payment/                    # Stripe integration
│   │   └── stripe_service.py
│   ├── compliance_engine/          # Core scanning & fix logic
│   │   ├── scanner.py              # Main ComplianceScanner
│   │   ├── deep_scanner.py         # DeepScanner (enhanced)
│   │   ├── fixer.py                # AIComplianceFixer
│   │   ├── workflow_engine.py      # Step-by-step fix workflow
│   │   ├── checks/                 # Modular compliance check functions
│   │   └── prompts/                # AI prompt templates
│   ├── ai_fix_engine/              # AI-powered fix generation
│   │   ├── intelligent_analyzer.py # OpenRouter/Claude API client
│   │   ├── smart_fix_generator.py  # Fix orchestrator
│   │   ├── unified_fix_engine.py   # Unified entry point
│   │   └── handlers/               # Per-category fix handlers
│   ├── background_worker.py        # Async job queue (polls fix_jobs table)
│   ├── cronjobs/                   # Scheduled tasks (crontab)
│   │   ├── legal_news_cronjob.py
│   │   └── fetch_news.py
│   ├── scanner/                    # Headless browser scanner
│   │   └── headless_scanner.py
│   ├── git_service/                # GitHub PR automation
│   │   └── git_service.py
│   ├── widgets/                    # Embeddable JS widgets served as static
│   │   └── locales/
│   ├── public/                     # Static files (CMP adapter JS)
│   ├── alembic/                    # DB migration framework config
│   │   └── versions/
│   ├── migrations/                 # Raw SQL migration scripts
│   ├── sql/                        # SQL files auto-applied at startup
│   ├── tests/                      # Backend tests
│   ├── *_routes.py                 # ~25 feature route modules
│   ├── *_service.py                # Service layer modules
│   ├── init_*.sql                  # Table initialization scripts
│   ├── migration_*.sql             # Schema migration scripts
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard-react/                # Authenticated SaaS dashboard (Next.js 14)
│   ├── src/
│   │   ├── app/                    # Next.js App Router pages
│   │   │   ├── layout.tsx          # Root layout (Providers, cookie banner)
│   │   │   ├── page.tsx            # Dashboard home
│   │   │   ├── auth/callback/      # OAuth token receipt handler
│   │   │   ├── ai-compliance/      # AI compliance module pages
│   │   │   ├── cookie-compliance/  # Cookie compliance page
│   │   │   ├── profile/            # User profile settings
│   │   │   ├── subscription/       # Plan management
│   │   │   ├── login/              # Login page
│   │   │   ├── register/           # Registration page
│   │   │   └── journey/            # Onboarding journey
│   │   ├── components/             # React components (feature-organized)
│   │   │   ├── accessibility/      # BFSG accessibility components
│   │   │   ├── ai/                 # AI assistant widget
│   │   │   ├── ai-compliance/      # AI compliance module components
│   │   │   ├── charts/             # Data visualization
│   │   │   ├── cookie-compliance/  # Cookie banner designer components
│   │   │   ├── dashboard/          # Main dashboard widgets
│   │   │   ├── fix-guide/          # Fix tutorial components
│   │   │   ├── fixes/              # Fix application components
│   │   │   ├── guards/             # Plan/auth route guards (PlanGuard.tsx)
│   │   │   ├── layout/             # Footer, shell components
│   │   │   ├── legal/              # Legal document components
│   │   │   ├── legal-changes/      # Legal news/change widgets
│   │   │   ├── onboarding/         # Onboarding flow components
│   │   │   ├── setup/              # Site setup components
│   │   │   ├── ui/                 # Shared design-system primitives (shadcn/ui)
│   │   │   └── workflow/           # Step-by-step workflow components
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx     # Auth state + login/logout/refresh
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useCompliance.ts
│   │   │   ├── useDashboardInitialization.ts
│   │   │   └── useMetrics.ts
│   │   ├── lib/                    # API clients + utilities
│   │   │   ├── api.ts              # Main axios client (auth interceptors)
│   │   │   ├── api-utils.ts        # Shared fetch helpers
│   │   │   ├── ai-compliance-api.ts
│   │   │   ├── auth-api.ts
│   │   │   ├── constants.ts        # APP_CONFIG, thresholds
│   │   │   ├── firebase.ts         # Firebase SDK init
│   │   │   └── utils.ts
│   │   ├── stores/
│   │   │   └── dashboard.ts        # Zustand global store
│   │   └── types/                  # TypeScript interfaces
│   │       ├── api.ts
│   │       ├── dashboard.ts
│   │       ├── website.ts
│   │       └── ai-compliance.ts
│   ├── tests/
│   │   └── e2e/                    # Playwright E2E tests
│   ├── scripts/                    # Build scripts
│   ├── Dockerfile.prod
│   └── package.json
├── landing-react/                  # Public marketing site (Next.js 14)
│   ├── src/
│   │   ├── app/                    # App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── ABTestRouter.tsx    # A/B test variant switcher
│   │   │   ├── admin/              # Admin panel pages
│   │   │   ├── agb/                # Terms of service
│   │   │   ├── datenschutz/        # Privacy policy
│   │   │   ├── impressum/          # Legal notice
│   │   │   └── verify-email/       # Email verification page
│   │   ├── components/             # Landing-specific components
│   │   │   ├── ComplyoHighConversionLanding.tsx
│   │   │   ├── ComplyoOriginalLanding.tsx
│   │   │   ├── CookieBannerLoader.tsx
│   │   │   └── modern-landing/
│   │   ├── hooks/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── constants.ts
│   │   ├── stores/
│   │   └── types/
│   ├── Dockerfile.prod
│   └── package.json
├── gateway/                        # Nginx gateway (dev/fallback)
│   ├── nginx.conf
│   └── Dockerfile
├── nginx/                          # Production Nginx config
│   └── production.conf             # SSL termination, upstreams, rate limits
├── simple-admin/                   # Static HTML admin panel (served via nginx)
├── wordpress-plugin/               # WordPress plugin for widget embedding
├── backup-scripts/                 # Database backup utilities
├── scripts/                        # Deployment helper scripts
├── docs/                           # Additional documentation
├── ssl/                            # SSL certificate files
├── docker-compose.yml              # Full-stack container orchestration
└── .env                            # Environment variables (DO NOT COMMIT)
```

## Directory Purposes

**`backend/`:**
- Purpose: All server-side logic; single FastAPI process serving the entire REST API
- Contains: 25+ route modules, service classes, compliance engine, AI fix engine, DB migration files, cron jobs
- Key files: `backend/main_production.py` (entry point), `backend/dependencies.py` (DI), `backend/requirements.txt`

**`backend/compliance_engine/`:**
- Purpose: Website compliance scanning and fix generation engine
- Contains: Scanner, fixer, deep scanner, workflow engine, modular checks per compliance area (DSGVO, cookie, accessibility), AI prompt templates
- Key files: `backend/compliance_engine/scanner.py`, `backend/compliance_engine/fixer.py`, `backend/compliance_engine/checks/`

**`backend/ai_fix_engine/`:**
- Purpose: AI-powered generation of compliance code fixes via OpenRouter/Claude
- Contains: Intelligent analyzer (LLM client), smart fix generator, unified engine, per-category handlers
- Key files: `backend/ai_fix_engine/intelligent_analyzer.py`, `backend/ai_fix_engine/smart_fix_generator.py`

**`backend/payment/`:**
- Purpose: Stripe payment integration
- Key files: `backend/payment/stripe_service.py`

**`backend/migrations/` and `backend/sql/`:**
- Purpose: SQL schema migrations; files in `backend/sql/` are auto-applied on startup (sorted alphabetically)
- Contains: Raw `.sql` files; also `backend/alembic/` for Alembic-tracked migrations
- Generated: No — manually authored. Committed: Yes.

**`backend/widgets/`:**
- Purpose: Embeddable JavaScript widgets (cookie consent, accessibility) bundled and served
- Contains: Widget JS source files, locale JSON files

**`backend/public/`:**
- Purpose: Static files mounted at `/public` on the API; primarily CMP adapter JavaScript
- Generated: No. Committed: Yes.

**`dashboard-react/src/app/`:**
- Purpose: Next.js 14 App Router pages; each subdirectory is a route
- Contains: `page.tsx` files; `layout.tsx` for root layout; route-specific logic

**`dashboard-react/src/components/`:**
- Purpose: Feature-organized React components
- Pattern: Each feature domain has its own subdirectory (e.g., `cookie-compliance/`, `accessibility/`, `dashboard/`)
- Shared primitives: `dashboard-react/src/components/ui/` (shadcn/ui component library)

**`dashboard-react/src/lib/`:**
- Purpose: API clients, constants, utilities; all backend communication goes through here
- Key files: `dashboard-react/src/lib/api.ts` (main axios client with JWT interceptor)

**`dashboard-react/src/stores/`:**
- Purpose: Zustand global client state
- Key files: `dashboard-react/src/stores/dashboard.ts`

**`landing-react/`:**
- Purpose: Public-facing marketing website; completely separate Next.js app from the dashboard
- Contains: Landing page variants (A/B test), legal pages (AGB, Datenschutz, Impressum)

## Key File Locations

**Entry Points:**
- `backend/main_production.py`: FastAPI app creation, startup/shutdown lifecycle, router registration
- `dashboard-react/src/app/layout.tsx`: Dashboard root layout (Providers wrapper)
- `landing-react/src/app/layout.tsx`: Landing root layout
- `docker-compose.yml`: Container orchestration for all services

**Configuration:**
- `backend/dependencies.py`: DI container — db pool, redis, JWT settings, service factories
- `dashboard-react/src/lib/constants.ts`: `APP_CONFIG` with API base URL logic, compliance thresholds
- `nginx/production.conf`: Nginx upstreams, SSL settings, rate-limit zones
- `.env`: All secrets and environment overrides (never read directly — existence noted only)

**Core Business Logic:**
- `backend/compliance_engine/scanner.py`: Website compliance scanner (DSGVO, cookie, accessibility checks)
- `backend/ai_fix_engine/intelligent_analyzer.py`: LLM-based fix generator (OpenRouter/Claude)
- `backend/background_worker.py`: Async fix-job queue processor
- `backend/auth_service.py`: User registration, login, JWT issuance, plan limits
- `backend/legal_change_monitor.py`: Automatic legal change detection and classification

**Authentication:**
- `backend/auth_routes.py`: `/api/auth/*` — login, register, refresh, OAuth callback
- `dashboard-react/src/contexts/AuthContext.tsx`: Frontend auth state with auto-refresh
- `dashboard-react/src/app/auth/callback/page.tsx`: OAuth token receipt and redirect

**Payment:**
- `backend/payment/stripe_service.py`: Stripe customer/subscription management
- `backend/payment_routes.py`: `/api/payment/*` endpoints
- `backend/stripe_routes.py`: Freemium-specific Stripe checkout endpoints

**Testing:**
- `backend/tests/`: Python backend tests
- `dashboard-react/tests/e2e/`: Playwright E2E tests

## Naming Conventions

**Backend Files:**
- Route modules: `<feature>_routes.py` (e.g., `auth_routes.py`, `cookie_compliance_routes.py`)
- Service modules: `<feature>_service.py` (e.g., `auth_service.py`, `email_service.py`)
- SQL init scripts: `init_<table>.sql` (e.g., `init_cookie_compliance.sql`)
- SQL migration scripts: `migration_<feature>.sql` or `<YYYYMMDD>_<seq>_<name>.py` (alembic)

**Frontend Files:**
- Pages: `page.tsx` inside a route directory
- Components: `PascalCase.tsx` (e.g., `CookieBannerDesigner.tsx`)
- Hooks: `camelCase.ts` prefixed with `use` (e.g., `useAuth.ts`)
- API clients: `<feature>-api.ts` or `api.ts`
- Types: `<domain>.ts` inside `src/types/`
- Stores: `<domain>.ts` inside `src/stores/`

**Directories:**
- Backend: snake_case (`compliance_engine/`, `ai_fix_engine/`)
- Frontend: kebab-case for feature dirs (`cookie-compliance/`, `ai-compliance/`, `fix-guide/`)
- Frontend: PascalCase for component files within those dirs

## Where to Add New Code

**New Backend Feature (route + service):**
- Route handler: `backend/<feature>_routes.py` (create new file with `router = APIRouter(prefix="/api/<feature>", tags=["..."])`)
- Service class: `backend/<feature>_service.py`
- Register router in: `backend/main_production.py` startup_event, add `app.include_router(...)`
- Inject db_pool in startup: `<module>.db_pool = db_pool`

**New Compliance Check:**
- Implement check function: `backend/compliance_engine/checks/<area>_check.py`
- Export from: `backend/compliance_engine/checks/__init__.py`
- Import and call in: `backend/compliance_engine/scanner.py`

**New Dashboard Page:**
- Create directory: `dashboard-react/src/app/<route-name>/`
- Add `page.tsx` with `'use client'` directive if using hooks/state
- Wrap restricted content with `<PlanGuard>` from `dashboard-react/src/components/guards/PlanGuard.tsx`

**New Dashboard Component:**
- Place in: `dashboard-react/src/components/<feature-domain>/<ComponentName>.tsx`
- Shared UI primitives: `dashboard-react/src/components/ui/`

**New API Client Function:**
- Add to: `dashboard-react/src/lib/api.ts` (general) or create `dashboard-react/src/lib/<feature>-api.ts`

**New Database Table:**
- Write schema: `backend/init_<table>.sql`
- Add to startup schema list in `backend/main_production.py` `init_db()` function, or add `.sql` to `backend/sql/` for auto-apply

**Utilities:**
- Backend shared helpers: `backend/dependencies.py` (DI) or a new `backend/<name>_service.py`
- Frontend shared utilities: `dashboard-react/src/lib/utils.ts` or `dashboard-react/src/lib/api-utils.ts`

## Special Directories

**`backend/sql/`:**
- Purpose: SQL files auto-executed in alphabetical order during every app startup (`init_db()`)
- Generated: No. Committed: Yes. Use with care — must be idempotent (use `CREATE TABLE IF NOT EXISTS`, `ON CONFLICT DO NOTHING`).

**`backend/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes. Committed: No.

**`backend/alembic/versions/`:**
- Purpose: Alembic-tracked schema migrations with version history
- Generated: Partially (via `alembic revision`). Committed: Yes.

**`dashboard-react/tests/e2e/`:**
- Purpose: Playwright end-to-end tests for the dashboard UI
- Generated: No. Committed: Yes.

**`simple-admin/`:**
- Purpose: Static HTML/CSS/JS admin panel served by Nginx at port 3004 (no framework)
- Generated: No. Committed: Yes.

**`wordpress-plugin/`:**
- Purpose: WordPress plugin for embedding Complyo cookie consent widget
- Generated: No. Committed: Yes.

---

*Structure analysis: 2026-03-29*
