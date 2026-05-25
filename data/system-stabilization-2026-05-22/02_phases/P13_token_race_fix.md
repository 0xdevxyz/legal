# P13 — Token-Race-Condition Fix (2026-05-23)

## Problem
Nach Login und bei jedem Reload erschien eine Welle von 401-Fehlern in der Browser-Konsole:
- `GET /api/v2/websites 401 Unauthorized`
- `GET /api/v2/dashboard/metrics 401 Unauthorized`
- `GET /api/legal-notifications/stats 401 Unauthorized`

## Root Cause
`useSession()` (NextAuth v5) ist async. Dashboard-Komponenten renderten sofort nach Mount und feuerten API-Calls, bevor `window.__complyo_access_token` durch den AuthContext gesetzt war. Außerdem wurde der Token-Sync im Render-Body (nicht in `useEffect`) ausgeführt — nicht deterministisch zeitlich vor den `useEffect`s der Kinder.

## Lösung — Drei-Schichten-Verteidigung

### Schicht 1: AuthContext (`src/contexts/AuthContext.tsx`)
- Token-Sync aus Render-Body entfernt → in `useEffect([status, session?.accessToken])` verschoben.
- Neues `isAuthReady`-Flag: `true` sobald `status !== 'loading'` und Token (falls authenticated) gesetzt ist.
- Self-Heal: Wenn `status=authenticated` aber Token fehlt → einmalig `update()` aufrufen.

### Schicht 2: AuthGuard (`src/components/auth/AuthGuard.tsx`)
- Neue Client-Component, liest `isAuthReady` aus `useAuth()`.
- Solange `!isAuthReady`: Zeigt Loading-Skeleton (Spinner + "Wird geladen…").
- Bei `!isAuthenticated` nach Ready: `router.replace('/login')`.
- Eingebunden in `SidebarLayout.tsx` — wraps alle nicht-public Pages.

### Schicht 3: api.ts Interceptor (`src/lib/api.ts`)
- `resolveAccessToken(): Promise<string | null>`:
  1. Sync-Lookup aus `window.__complyo_access_token` / `localStorage`.
  2. Falls leer: `getSession()` aufrufen mit Inflight-Promise-Cache (verhindert N parallele Calls).
  3. Timeout nach 3s.
- Request-Interceptor auf `async` umgestellt, nutzt `await resolveAccessToken()`.
- Response-Interceptor bei 401: ruft `resolveAccessToken()` nochmals (damit der frische Token genutzt wird), dann Retry.
- Logging: Nur echte Fehler (status ≥ 500 oder persistente 401 nach Retry) → `console.warn`. Kein Spam mehr.

## Ergebnis (Smoke-Test 2026-05-23)
- Login → Dashboard: **0 Konsolen-Errors** (vorher: 8–15 rote 401-Errors)
- Subscription-Seite: **0 Konsolen-Errors**
- Dashboard rendert vollständig, Sidebar + Score + Widgets korrekt

## Migrationshinweis
Neue geschützte Pages müssen **innerhalb** von `SidebarLayout` liegen (alle Routes außer `/login`, `/register`, `/auth/callback`, `/privacy`). Falls eine neue Route zur `AUTH_ROUTES`-Liste in `SidebarLayout.tsx` hinzukommt, wird sie automatisch vom AuthGuard ausgenommen.
