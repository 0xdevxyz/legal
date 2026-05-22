# Phase 2: NextAuth.js v5 Komplett-Migration
Datum: 2026-05-22
Status: completed

## Implementierte Dateien

### Neue Dateien
- `dashboard-react/src/auth.config.ts` — Credentials Provider, JWT/Session Callbacks
- `dashboard-react/src/auth.ts` — NextAuth Handler Export
- `dashboard-react/src/app/api/auth/[...nextauth]/route.ts` — Route Handler
- `dashboard-react/src/types/next-auth.d.ts` — Type Augmentation (User, Session, JWT)
- `dashboard-react/src/lib/api-client.ts` — TanStack Query API Client mit NextAuth Session

### Geänderte Dateien
- `dashboard-react/src/middleware.ts` — auf NextAuth `auth()` Middleware umgestellt
- `dashboard-react/src/contexts/AuthContext.tsx` — NextAuth-Wrapper (backwards compat)
- `dashboard-react/src/hooks/useAuth.ts` — nutzt `useSession`, `signIn`, `signOut`
- `dashboard-react/src/app/providers.tsx` — `SessionProvider` als Root hinzugefügt
- `dashboard-react/.env.local` — NEXTAUTH_URL, NEXTAUTH_SECRET, NEXTAUTH_BACKEND_URL
- `docker-compose.yml` — Dashboard Env-Vars um NextAuth-Vars erweitert

## Dependencies
- `next-auth@5.0.0-beta.28` installiert
- `zod` installiert (für Credentials Validation)

## Fixes via NextAuth
- RC-2 (Endlos-Refresh-Loop): kein manuelles Cookie-Management mehr
- RC-3 (Onboarding-Loop): Session via `update()` persistiert
- RC-5 (401 bei /api/legal-ai/updates): Token aus NextAuth Session

## Auth Flow (Neu)
1. User gibt Email/Password ein → `signIn('credentials', ...)`
2. NextAuth ruft `POST /api/auth/verify-credentials` auf
3. Backend gibt user-Objekt zurück
4. NextAuth erstellt JWT-Session (HttpOnly Cookie via NextAuth)
5. Token via Session-Callback in Session gespeichert
6. API-Requests via `api-client.ts` mit `session.accessToken`

## Tests
- TypeScript: 0 Fehler ✓
- Docker Build: 24/24 static pages ✓
- HTTP 302 Redirect bei unauthentifiziertem Access ✓
