# Technology Stack

**Analysis Date:** 2026-03-29

## Languages

**Primary:**
- Python 3.11 - Backend API (`backend/`)
- TypeScript 5.5 - Dashboard frontend (`dashboard-react/src/`)
- TypeScript 5.9 - Landing page frontend (`landing-react/src/`)

**Secondary:**
- JavaScript - WordPress plugin (`wordpress-plugin/complyo-compliance/`), static admin panel (`simple-admin/`)
- SQL - Database migrations and schema files (`backend/*.sql`, `backend/alembic/`, `backend/migrations/`)

## Runtime

**Environment:**
- Python 3.11 (containerized via `python:3.11-slim` Docker image)
- Node.js 20.x (inferred from `@types/node: ^20.14.11` in dashboard)
- Docker + Docker Compose for orchestration

**Package Manager:**
- Python: `pip` (no lockfile, direct `requirements.txt`)
- Node (dashboard): `npm` — lockfile: `dashboard-react/package-lock.json` present
- Node (landing): `npm` — lockfile: `landing-react/package-lock.json` present

## Frameworks

**Core (Backend):**
- FastAPI 0.115.6 - REST API server (`backend/main_production.py`)
- Uvicorn 0.24.0 - ASGI server, runs on port 8002
- Pydantic 2.5.0 - Data validation and settings
- SQLAlchemy 2.0.23 - ORM (schema definitions)
- Alembic 1.13.1 - Database migrations (`backend/alembic/`)

**Core (Frontend):**
- Next.js 14.2.x - Both dashboard (`dashboard-react/`) and landing (`landing-react/`), output: `standalone`
- React 18.3.1 - Component framework
- Tailwind CSS 3.4.x - Utility styling

**UI Components (Dashboard):**
- Chakra UI 2.8.2 - Component library
- Radix UI (dialog, label, select, switch) - Headless primitives
- Framer Motion 11.x - Animations
- Recharts 2.x - Data visualization
- Lucide React - Icon set

**State Management:**
- Zustand 4.5.4 (dashboard) / 5.0.8 (landing) - Client state
- TanStack Query 5.x (both frontends) - Server state and caching
- React Context - Auth state (`dashboard-react/src/contexts/AuthContext.tsx`)

**Testing:**
- pytest 8.0+ with pytest-asyncio 0.23+ - Backend (`backend/tests/`)
- Playwright 1.40.0 - Browser automation and end-to-end testing (also used for scanning)

**Build/Dev:**
- ESLint 8.57 + eslint-config-next - Linting (dashboard)
- Husky 9 + lint-staged - Git hooks (dashboard)
- Prettier - Code formatting via lint-staged

## Key Dependencies

**Critical (Backend):**
- `asyncpg 0.29.0` - Async PostgreSQL driver, used throughout all services
- `PyJWT 2.9.0` - JWT creation and verification (`backend/auth_service.py`)
- `stripe 7.8.0` - Payment processing (`backend/stripe_routes.py`, `backend/payment/stripe_service.py`)
- `firebase-admin 6.3.0` - Firebase token verification (`backend/firebase_auth.py`)
- `playwright 1.40.0` - Headless Chromium for website scanning (`backend/Dockerfile` installs Chromium)
- `slowapi 0.1.9` - Rate limiting middleware
- `sentry-sdk[fastapi] >=2.0.0` - Error tracking
- `prometheus-client >=0.20.0` - Metrics exposure

**AI / ML:**
- `scikit-learn 1.3.2` - ML utilities
- `numpy 1.26.2`, `pandas 2.1.4` - Data processing
- OpenRouter API (external, via `httpx`) - AI completions using `anthropic/claude-3.7-sonnet:beta` and `anthropic/claude-3.5-sonnet`

**Infrastructure:**
- `redis 5.0.1` - Caching and session storage
- `aiohttp 3.9.5` - Async HTTP client (EU-Lex integration)
- `httpx 0.27.2` - Async HTTP client (eRecht24, OpenRouter, OAuth)
- `reportlab 4.0.7` - PDF report generation
- `Jinja2 3.1.2` - Email templates

**Critical (Frontend):**
- `axios 1.7.x` - HTTP client with auth interceptors (`dashboard-react/src/lib/api.ts`)
- `firebase 12.4.0` - Client-side auth (Google Sign-In, email/password)
- `dompurify 3.2.3` - XSS sanitization
- `date-fns 3.6.0` - Date formatting

## Configuration

**Environment:**
- Backend: `python-dotenv` loads `.env` at runtime; all secrets via environment variables
- Frontend: Next.js `NEXT_PUBLIC_*` env vars; set at build time or via Docker environment
- All secrets required at startup — missing `JWT_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` cause hard `RuntimeError` on boot

**Required Backend Env Vars:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` / `REDIS_HOST` / `REDIS_PASSWORD` - Redis connection
- `JWT_SECRET` - Token signing (mandatory)
- `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + price IDs - Payments (mandatory)
- `OPENROUTER_API_KEY` - AI features (optional, disables AI if missing)
- `FIREBASE_PROJECT_ID` + `FIREBASE_PRIVATE_KEY` + `FIREBASE_CLIENT_EMAIL` - Social login
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` - Email
- `SENTRY_DSN` - Error tracking (optional)
- `ERECHT24_API_KEY` + `ERECHT24_WEBHOOK_SECRET` - Legal texts service (optional, demo mode if missing)

**Required Frontend Env Vars (Dashboard):**
- `NEXT_PUBLIC_API_URL` - Backend base URL
- `NEXT_PUBLIC_FIREBASE_*` - 7 Firebase config values

**Build:**
- Backend: `docker build ./backend` — installs pip deps then Playwright Chromium
- Frontend: `next build` with `output: 'standalone'` — separate `Dockerfile.prod` per frontend

## Platform Requirements

**Development:**
- Docker + Docker Compose
- Python 3.11
- Node.js 20.x
- Ports: 8002 (backend), 3001 (dashboard), 3003 (landing), 6380 (Redis), 5433 (PostgreSQL)

**Production:**
- Docker Compose with external `proxy-network` (nginx-proxy + Let's Encrypt)
- Domains: `api.complyo.de` (backend), `app.complyo.de` (dashboard), `complyo.de` (landing)
- Backend memory limited to 1GB / 1.5GB swap
- PostgreSQL 15 (alpine), Redis 7 (alpine)
- SSL via Let's Encrypt (LETSENCRYPT_HOST env vars on each service)

---

*Stack analysis: 2026-03-29*
