# External Integrations

**Analysis Date:** 2026-03-29

## APIs & External Services

**AI / LLM:**
- OpenRouter API - AI legal classification, compliance fix generation, alt-text generation
  - SDK/Client: `httpx` (custom HTTP calls in `backend/ai_legal_classifier.py`, `backend/fix_generator.py`)
  - Models used: `anthropic/claude-3.7-sonnet:beta`, `anthropic/claude-3.5-sonnet`
  - Base URL: `https://openrouter.ai/api/v1/chat/completions`
  - Auth: `OPENROUTER_API_KEY` env var
  - Optional: AI features gracefully degrade if key missing

**Legal Texts Service:**
- eRecht24 API - Generates and manages legally-compliant texts (Datenschutz, Impressum) for customer websites
  - SDK/Client: `httpx` in `backend/erecht24_service.py`
  - API Base: `https://api.e-recht24.de` (env: `ERECHT24_API_URL`)
  - Auth: `ERECHT24_API_KEY` env var; falls back to demo/mock mode if missing
  - Incoming webhooks: `POST /webhooks/erecht24/law-update` in `backend/erecht24_webhook_routes.py`
  - Webhook secret: `ERECHT24_WEBHOOK_SECRET`

**EU Legal Data:**
- EUR-Lex SPARQL API - Fetches EU regulation changes (GDPR, ePrivacy, AI Act, DSA)
  - SDK/Client: `aiohttp` in `backend/eulex_service.py`
  - SPARQL endpoint: `https://publications.europa.eu/webapi/rdf/sparql`
  - Cellar base: `https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:`
  - Auth: None required (public API)
  - Triggered by background worker and scheduled jobs

**Version Control / CI:**
- GitHub API - Creates branches, commits, and pull requests for auto-generated compliance fixes
  - SDK/Client: `httpx` in `backend/compliance_engine/github_integration.py`
  - Base URL: `https://api.github.com`
  - Auth: Per-user `github_token` passed at request time (not a global key)

## Data Storage

**Databases:**
- PostgreSQL 15
  - Connection: `DATABASE_URL` env var (format: `postgresql://user:pass@host:5432/db`)
  - Client: `asyncpg 0.29.0` for raw async queries; `SQLAlchemy 2.0.23` for ORM schema definitions
  - Migrations: Alembic (`backend/alembic/`) plus raw SQL migration files (`backend/migration_*.sql`, `backend/init_*.sql`)
  - Pool: min=2, max=10 connections configured in `backend/database_service.py`
  - Fallback: In-memory dict storage if DB unreachable (only for lead data)

**Caching / Session:**
- Redis 7
  - Connection: `REDIS_URL` (`redis://:password@host:6379`) and `REDIS_HOST` / `REDIS_PASSWORD` env vars
  - Client: `redis 5.0.1` Python library
  - Used in: `backend/fix_generator.py`, `backend/widget_routes.py`, `backend/dependencies.py`
  - Purpose: Rate limiting cache, fix result caching, widget session data

**File Storage:**
- Local filesystem only (no cloud storage detected)
  - Static assets served via FastAPI `StaticFiles` at `/public` from `backend/public/`
  - PDF reports generated in-memory via `reportlab` and streamed as `StreamingResponse`
  - Widget JS/CSS files in `backend/widgets/`

## Authentication & Identity

**Primary Auth (Email/Password):**
- Custom JWT implementation in `backend/auth_service.py`
  - Algorithm: HS256
  - Secret: `JWT_SECRET` env var (mandatory, fails hard on startup)
  - Audience: `"complyo-api"`
  - Issuer: `FRONTEND_URL` env var (default `"https://complyo.tech"`)
  - Access token TTL: 7 days; Refresh token TTL: 30 days
  - Passwords: bcrypt via `passlib[bcrypt]`

**Social Auth — Firebase:**
- Firebase Authentication (Google Sign-In + Email/Password via Firebase)
  - Frontend client: `firebase 12.4.0` SDK in `dashboard-react/src/lib/firebase.ts`
  - Backend verification: `firebase-admin 6.3.0` in `backend/firebase_auth.py`
  - Backend init: service account credentials from `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`, `FIREBASE_CLIENT_EMAIL` env vars
  - Frontend config: 7 `NEXT_PUBLIC_FIREBASE_*` env vars
  - Providers: Google (`GoogleAuthProvider`), Email/Password

**Social Auth — Direct OAuth2:**
- Google OAuth2 (direct, parallel to Firebase path) in `backend/oauth_service.py`
  - Config: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` env vars
  - Callback: `{FRONTEND_URL}/auth/google/callback`
- Apple Sign-In in `backend/oauth_service.py`
  - Config: `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` env vars
  - Callback: `{FRONTEND_URL}/auth/apple/callback`

## Payments

**Stripe:**
- Subscription management (Pro, Agency plans) and one-time addon purchases
  - SDK: `stripe 7.8.0` Python library
  - Backend services: `backend/stripe_routes.py`, `backend/payment/stripe_service.py`
  - Auth: `STRIPE_SECRET_KEY` env var (mandatory, hard fail on startup)
  - Webhook endpoint: receives Stripe events; validated via `STRIPE_WEBHOOK_SECRET`
  - Price IDs: `STRIPE_PRICE_PRO_MONTHLY`, `STRIPE_PRICE_PRO_YEARLY`, `STRIPE_PRICE_AGENCY_MONTHLY`, `STRIPE_PRICE_AGENCY_YEARLY`, `STRIPE_PRICE_SINGLE_MODULE`, `STRIPE_PRICE_COMPLETE`, `STRIPE_PRICE_EXPERT_MONTHLY`
  - Plans stored in DB: `user_limits` table tracks `plan_type` and per-user quotas
  - Safety guard: `DEV_MODE=true` or `BYPASS_PAYMENT=true` with `ENVIRONMENT=production` raises `RuntimeError` at import time

## Email

**SMTP (transactional email):**
- Provider: Configurable SMTP; defaults to `smtp.gmail.com:587`
  - Implementation: stdlib `smtplib` + `Jinja2` templates in `backend/email_service.py`
  - Config: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SENDER_EMAIL`, `SENDER_NAME` env vars
  - Demo mode: If no SMTP credentials set, emails are logged to console
  - Usage: Verification emails (double opt-in), compliance report delivery, lead management

## Monitoring & Observability

**Error Tracking:**
- Sentry via `sentry-sdk[fastapi] >=2.0.0`
  - Initialized in `backend/main_production.py` at startup
  - Config: `SENTRY_DSN` env var (optional — skipped if not set)
  - `traces_sample_rate: 0.1` (10% of transactions)

**Metrics:**
- Prometheus via `prometheus-client >=0.20.0`
  - Counters and histograms for HTTP requests/duration exposed in `backend/main_production.py`
  - Metrics endpoint protected by `METRICS_TOKEN` env var
  - Request-ID middleware adds `X-Request-ID` header to all responses

**Logging:**
- Python stdlib `logging` throughout all backend modules
- Log level configurable via environment

## CI/CD & Deployment

**Hosting:**
- Self-hosted Docker Compose on Linux VPS
  - Reverse proxy: nginx-proxy (external `proxy-network` in `docker-compose.yml`)
  - SSL: Let's Encrypt via nginx-proxy companion (LETSENCRYPT_HOST env vars)

**CI Pipeline:**
- None detected (no GitHub Actions, GitLab CI, or similar config files found)

## Webhooks & Callbacks

**Incoming:**
- `POST /webhooks/erecht24/law-update` — eRecht24 legal text change notifications (`backend/erecht24_webhook_routes.py`)
  - Verified via HMAC-SHA256 signature header `X-Erecht24-Signature` against `ERECHT24_WEBHOOK_SECRET`
- Stripe webhook endpoint in `backend/stripe_routes.py` and `backend/payment_routes.py`
  - Verified via Stripe's `construct_event` with `STRIPE_WEBHOOK_SECRET`

**Outgoing:**
- OpenRouter AI API — AI fix and classification requests
- EUR-Lex SPARQL — Legal regulation change polling
- eRecht24 REST API — Legal text project management
- GitHub REST API — Automated PR creation for compliance fixes
- Google OAuth2 token endpoint (`https://oauth2.googleapis.com/token`) — User login flow
- Apple OAuth token endpoint — User login flow
- SMTP server — Transactional emails

## Browser Automation

**Playwright + Chromium:**
- Used for website compliance scanning (not just testing)
  - Chromium installed in backend Docker image at `/app/.cache/ms-playwright`
  - `PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright` env var set in Dockerfile
  - Used in `backend/compliance_engine/browser_renderer.py`, `backend/compliance_engine/screenshot_service.py`, `backend/website_crawler.py`

## Environment Configuration Summary

**Critical (must be set, hard fail otherwise):**
- `DATABASE_URL`
- `JWT_SECRET`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `REDIS_PASSWORD`
- `POSTGRES_PASSWORD`

**Optional (features degrade gracefully):**
- `OPENROUTER_API_KEY` — AI features disabled if missing
- `FIREBASE_*` — Social login disabled if missing
- `ERECHT24_API_KEY` — Demo mode if missing
- `SENTRY_DSN` — Error tracking skipped if missing
- `SMTP_USERNAME` / `SMTP_PASSWORD` — Email logged to console if missing
- `GOOGLE_CLIENT_ID/SECRET`, `APPLE_*` — Direct OAuth disabled if missing

---

*Integration audit: 2026-03-29*
