# File Audit Summary
Date: 2026-05-05

---

## 1. dashboard-react/src/lib/api.ts (lines 1–80)

**Key Findings:**
- Axios instance (`apiClient`) created with `withCredentials: true` and 60s timeout.
- Base URL resolved via `getApiBaseUrl()` utility.
- Request interceptor reads `access_token` from `localStorage` and attaches as `Authorization: Bearer <token>`.
- Response interceptor handles:
  - Network errors (ERR_NETWORK): retries once after 1s.
  - 401 Unauthorized: attempts token refresh via `POST /api/auth/refresh` using `refresh_token` from localStorage; on success stores new token; on failure clears all auth keys and redirects to `/login`.

**Security Concerns:**
- Tokens stored in `localStorage` — vulnerable to XSS (not HttpOnly cookies).
- Both `access_token` and `refresh_token` cleared from localStorage on logout, but the original storage in localStorage is the root concern.
- `_retry` flag on the original request prevents infinite retry loops — correct pattern.

**Notable Patterns:**
- Dual retry strategy: network-level retry + auth-level refresh.
- Clean separation of request/response interceptors.

---

## 2. dashboard-react/src/contexts/AuthContext.tsx (lines 1–100)

**Key Findings:**
- `getApiBase()` resolves API URL: env var > hostname check > fallback to `localhost:8002`.
- Hardcoded hostnames: `complyo.tech`, `complyo.de`, `localhost`.
- `User` interface includes `plan_type` enum, `active_modules`, and `plan_limits` (fixes_used, fixes_limit).
- `AuthContextType` exposes: `user`, `accessToken`, `login`, `register`, `logout`, `isAuthenticated`, `isLoading`.
- Auto-refresh token every 50 minutes (token TTL = 60 min) with `retries=3`.
- Refresh uses native `fetch` with `AbortController` (10s timeout).
- On successful refresh: updates React state, `localStorage`, and sets a **cookie**: `access_token=...; max-age=30 days; SameSite=Lax; Secure`.

**Security Concerns:**
- `access_token` stored in both `localStorage` AND a cookie — inconsistent token storage strategy.
- Cookie is set client-side with `Secure` and `SameSite=Lax` (good), but NOT `HttpOnly` (bad — still JS-accessible).
- Cookie `max-age` is 30 days regardless of token TTL (60 min) — stale cookie after expiry.
- `refresh_token` only in `localStorage`, not in cookie.

**Notable Patterns:**
- `AuthContext` with `createContext` / `useContext` pattern.
- SSR guard: `typeof document !== 'undefined'` before cookie write.
- Token auto-refresh interval set up in `useEffect`.

---

## 3. dashboard-react/next.config.js (full)

**Key Findings:**
- `output: 'standalone'` — Docker-friendly standalone build.
- TypeScript and ESLint errors are NOT ignored during builds (`ignoreBuildErrors: false`).
- `NEXT_PUBLIC_API_URL` env var exposed to browser; defaults to `http://localhost:8002`.
- Rewrites: `/api/:path*` proxies to `NEXT_PUBLIC_API_URL/:path*`.
- Security headers applied globally (`/(.*)`): `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: origin-when-cross-origin`.
- Image domains whitelisted: `complyo.tech`, `app.complyo.tech`, `api.complyo.tech`.
- `optimizePackageImports` for `lucide-react` and `recharts`.

**Security Concerns:**
- Missing `Content-Security-Policy` header.
- Missing `Strict-Transport-Security` (HSTS) header.
- Missing `Permissions-Policy` header.
- Rewrite destination uses `NEXT_PUBLIC_API_URL` — if env var is unset, defaults to `http://` (plaintext) in development.

**Notable Patterns:**
- Minimal but correct security header setup.
- Proxy rewrite avoids CORS in production by routing through Next.js.

---

## 4. backend/auth_routes.py (lines 1–100)

**Key Findings:**
- FastAPI router at `/api/auth`.
- Rate limiting via `slowapi`: register endpoint limited to `3/hour` per IP.
- Pydantic models: `RegisterRequest` (email, password, full_name, company, plan), `LoginRequest`, `TokenResponse` (access + refresh tokens), `RefreshRequest`.
- Global module-level vars for `auth_service`, `db_pool`, `oauth_service`, `firebase_verify_token` — injected from `main_production.py` (not dependency injection).
- `init_user_limits()`: inserts into `user_limits` table on first registration; `exports_max=-1` for expert plan (unlimited); defaults to 10 exports.
- Register endpoint checks for existing email before creating user.

**Security Concerns:**
- Global mutable service references (`auth_service = None`) are set externally — not using FastAPI's `Depends()` pattern, which is less testable and potentially unsafe.
- No explicit password strength validation visible in these 100 lines.
- Plan type `"ki"` as default — non-standard naming.

**Notable Patterns:**
- `slowapi` rate limiter on registration (3/hour) — good DDoS protection.
- `EmailStr` used for email validation.
- `HTTPBearer` security scheme declared but not used in these first 100 lines.

---

## 5. backend/dependencies.py (full)

**Key Findings:**
- `Settings` class loads from env: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `OPENROUTER_API_KEY`, `FRONTEND_URL`, `ENVIRONMENT`.
- Raises `RuntimeError` at startup if `JWT_SECRET` or `DATABASE_URL` are missing.
- JWT: algorithm `HS256`, audience `complyo-api`, issuer from `FRONTEND_URL`.
- `get_current_user`: decodes JWT, validates audience + issuer, raises 401 on expiry or invalid token.
- `get_current_user_optional`: same but returns `None` instead of raising — for public endpoints.
- `require_admin`: queries `users.is_superuser` DB field for admin check.
- `get_client_ip`: reads `X-Forwarded-For` header (first IP only).
- Redis is optional — silently returns `None` if unavailable.
- Lazy singleton pattern for services (`_auth_service`, `_stripe_service`, `_news_service`).

**Security Concerns:**
- `HS256` is symmetric — shared secret must be kept secure; `RS256` (asymmetric) would be stronger for distributed services.
- `X-Forwarded-For` is read without any IP whitelist for trusted proxies — could be spoofed.
- `lru_cache` on `get_settings()` means settings are loaded once; env var changes at runtime won't be picked up.
- JWT detail error leaks: `detail=f"Invalid token: {str(e)}"` exposes internal error messages.

**Notable Patterns:**
- Clean DI module with lifecycle `startup()` / `shutdown()` hooks.
- `asyncpg` connection pool with `aioredis` for async DB and cache.
- `auto_error=False` on `HTTPBearer` allows optional auth dependency pattern.

---

## 6. .gitignore (full)

**Key Findings:**
- Covers: `node_modules/`, `.next/`, `build/`, `dist/`, coverage, logs, `.db`/`.sqlite` files, `__pycache__`, `venv/`, IDEs, OS files.
- `.env` and `.env.*` patterns appear **6 times** (duplicated entries).
- `docker-compose*.yml` appears twice.
- `ssl/`, `ssl-certs/`, `*.key`, `*.pem` — SSL certificates excluded.
- `docker-compose.production.yml` excluded 3 times.
- Trailing indented block near bottom (`   node_modules/` etc.) — malformed with leading spaces.

**Security Concerns:**
- Despite many `.env` entries, the repetition suggests the file was appended to multiple times without deduplication — low risk but messy.
- `*.key` and `*.pem` are excluded — good.
- No explicit exclusion of `*.secret`, `*.credentials`, or `secrets/` directories.

**Notable Patterns:**
- `.gitignore` is JS-project-first (npm artifacts at top), Python added later.
- Duplicate entries throughout — should be cleaned up.
