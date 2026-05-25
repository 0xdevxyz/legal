# Codebase Audit Summary
Date: 2026-05-05

---

## 1. requirements.txt

**Key findings:**
- FastAPI 0.115.6 + Uvicorn (async backend)
- asyncpg 0.29.0 (PostgreSQL, async)
- PyJWT 2.9.0 + python-jose[cryptography] 3.3.0 — two JWT libraries in parallel (redundancy/conflict risk)
- passlib[bcrypt] 1.7.4 + bcrypt 4.1.2 — also duplicated (two password hashing libs)
- Stripe 7.8.0, Firebase-admin 6.3.0, slowapi 0.1.9 (rate limiting)
- Sentry SDK, Prometheus client (observability)
- Playwright 1.40.0 (headless browser — unusually heavy for a backend dep)
- paramiko >= 3.4.0 (SSH — unclear use case in a SaaS backend)
- scikit-learn + numpy + pandas (ML pipeline present)

**Security concerns:**
- certifi 2023.11.17 — outdated, may lack recent CA certs
- lxml 4.9.3 — old; known XXE/parsing CVEs in older versions
- python-multipart 0.0.6 — older version, check for recent CVEs
- paramiko presence is a potential attack surface if misused

**Code quality issues:**
- Dual JWT libs (PyJWT + python-jose) suggests inconsistent auth implementation across the codebase
- Dual bcrypt libs (bcrypt + passlib[bcrypt]) is redundant

---

## 2. main_production.py (lines 1–100)

**Structure:**
- FastAPI app with CORS middleware, slowapi rate limiting, HTTPBearer security
- Sentry DSN initialized early (conditional on env var)
- Prometheus metrics (Counter + Histogram) defined at module level
- Modular router imports: 15+ routers loaded (auth, payments, gdpr, i18n, compliance, AI, etc.)
- Background worker started/stopped on lifespan
- Firebase admin initialized for token verification

**Security measures:**
- slowapi rate limiting on remote address
- HTTPBearer token scheme
- Sentry error tracking (sampling at 10%)
- `JWT_SECRET` enforced via env var (raises RuntimeError if missing — seen in auth_service.py)

**Security concerns:**
- Sentry SDK imported twice (lines 23 and 57); the second init is commented out with `[DUPLICATE-REMOVED]` tags — messy but non-breaking
- No explicit CORS origin whitelist visible in these 100 lines (may be configured further down)

**Code quality issues:**
- Duplicate `import sentry_sdk` / `_sentry_sdk` at lines 23 and 57
- Heavy import surface (~20 top-level service imports) — slow startup, tight coupling
- Emoji comments (`# ✅ FIX:`, `# NEU:`) in production code — informal style

---

## 3. auth_service.py (lines 1–80)

**Auth mechanisms:**
- bcrypt for password hashing (`bcrypt.hashpw` with `gensalt()`)
- PyJWT for token signing
- `JWT_SECRET` from env — hard fails at startup if missing (good)
- Access token expiry: 7 days (10080 min) — long-lived, increases breach window
- Refresh token expiry: 30 days
- `jwt_issuer` set to `FRONTEND_URL` env var, `jwt_audience` hardcoded to `"complyo-api"`
- `_utcnow()` helper uses timezone-aware UTC datetime

**Security concerns:**
- 7-day access token lifetime is unusually long for a production SaaS — should be 15–60 min with refresh token rotation
- `get_user_by_email` uses `SELECT *` — returns all columns including password hash to callers
- No visible token revocation / blacklist mechanism in these lines

**Code quality issues:**
- `SELECT *` in `get_user_by_email` (line 31) — over-fetches, leaks password hash to caller
- Multiple async DB calls within `get_user_by_id` without a transaction — inconsistent read risk

---

## 4. database_service.py (lines 1–80)

**Key findings:**
- asyncpg connection pool (min 2, max 10, 60s timeout)
- Falls back silently to in-memory storage (`fallback_storage` dict) if DB connection fails
- `DATABASE_URL` has a hardcoded default: `postgresql://complyo_user:ComplYo2025SecurePass@localhost:5432/complyo_db`
- GDPR-compliant lead schema: stores consent timestamp, IP, user agent, legal basis, retention date

**Security concerns:**
- CRITICAL: Hardcoded default database credentials in source code (line 19) — `ComplYo2025SecurePass` will be committed to version control
- Silent fallback to in-memory storage means a DB outage produces no visible error and data is silently lost on restart
- `fallback_storage` is not thread/process-safe at scale

**Code quality issues:**
- Hardcoded credentials as default arg — must be removed; no default should exist
- `get_connection()` calls `initialize()` lazily if pool is None — racy in concurrent startup scenarios
- `use_fallback = True` with `return True` masks initialization failure entirely

---

## 5. data/technisch/TECHNICAL_DEBT.md

**Key findings:**
- 80 TODO/FIXME entries across 26 files (as of Nov 2025)
- 4 CRITICAL items, 9 HIGH, 11 MEDIUM, 56 LOW (intentional template placeholders)

**Critical issues documented:**
- `legal_ai_routes.py:20` — uses hardcoded test-user instead of real auth
- `cookie_compliance_routes.py:351` — user_id not read from session/auth
- `widget_routes.py:462` — auth dependency commented out
- `stripe_routes.py:32` — Stripe Price IDs default to placeholder `"price_XXXXX"`

**High issues:**
- Widget analytics, usage counts, and fix data not persisted to DB (5 locations)
- Admin privilege checks missing on 3 admin-only endpoints

**Code quality issues:**
- Multiple production endpoints lack authentication entirely (CRITICAL category)
- Missing admin checks on privileged routes (`ai_legal_routes.py:632,673`)
- No ML feedback loop persisted (`legal_ai_routes.py:173`)

---

## 6. docker-compose.yml

**Key findings:**
- 5 services: postgres:15-alpine, redis:7-alpine, backend, landing (Next.js), dashboard (Next.js), admin (nginx static)
- All ports bound to `127.0.0.1` only — not exposed publicly (correct)
- Uses `proxy-network` (external) — implies nginx-proxy/Traefik reverse proxy in front
- Let's Encrypt auto-cert via `VIRTUAL_HOST` / `LETSENCRYPT_HOST` env vars
- Backend memory limited to 1 GB (1.5 GB swap)
- `POSTGRES_PASSWORD` and `JWT_SECRET` use `:?` syntax — fail-fast if unset (good)
- Redis requires password (`--requirepass`)

**Security concerns:**
- `BYPASS_PAYMENT` and `UNLIMITED_FIXES` env vars exist with `false` defaults — dangerous flags; if accidentally set to `true` in prod, bypasses billing entirely
- Admin panel is plain nginx serving static files — no auth visible at the compose level
- `SMTP_PASSWORD` defaults to empty string (`""`) — no fail-fast enforcement
- Firebase private key passed as plain env var — acceptable but sensitive

**Code quality issues:**
- `STRIPE_WEBHOOK_SECRET_ADDONS` defaults to `STRIPE_WEBHOOK_SECRET` via nested interpolation — may silently reuse wrong secret
- No resource limits on postgres, redis, landing, or dashboard containers
- No explicit `HEALTHCHECK` on backend, landing, or dashboard services
