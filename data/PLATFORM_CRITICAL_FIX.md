# Kritische Plattform-Reparatur — 2026-05-15

## Geänderte Dateien

### Backend

**`backend/auth_service.py`** (Z.44)
- SELECT in `get_user_by_id` um `onboarding_completed` erweitert
- Effekt: `/api/auth/me` liefert jetzt den Onboarding-Status

**`backend/stripe_routes.py`** (Z.99, Z.227)
- `create-checkout`: `current_user.get('uid')` → `current_user.get('user_id') or current_user.get('id')` + E-Mail aus DB holen
- `create-portal-session`: gleicher uid-Fix
- Effekt: Checkout-Flow funktioniert wieder (vorher immer 401)

**`backend/main_production.py`** (Z.1606)
- `SELECT email, name FROM users` → `SELECT email, full_name FROM users`
- Effekt: `/api/v2/payments/create-checkout-session` crasht nicht mehr wegen fehlendem SQL-Feld

### Frontend

**`dashboard-react/src/lib/api.ts`**
- Single-Flight `refreshAccessToken()` eingeführt (Modul-Var `_inflightTokenRefresh`)
- 401-Interceptor nutzt jetzt Single-Flight statt direktem `apiClient.post()`
- Effekt: Parallele 401-Requests stoßen nur einen Refresh an, nicht N

**`dashboard-react/src/contexts/AuthContext.tsx`**
- `markOnboardingCompleted()` Funktion hinzugefügt → `setUser({...prev, onboarding_completed: true})`
- `inflightRefresh` useRef eingeführt, `restoreSession` prüft ob bereits ein Refresh läuft
- `refreshTokenWithRetry`: bei HTTP 429 sofort abbrechen (kein Retry)
- Effekt: Onboarding-Loop bei Reload behoben; kein 429-Retry-Spirale mehr

**`dashboard-react/src/components/onboarding/OnboardingWizard.tsx`**
- `markOnboardingCompleted()` aus AuthContext importiert und nach erfolgreichem API-Call aufgerufen
- Effekt: `user.onboarding_completed` wird sofort im Context auf `true` gesetzt

**`dashboard-react/src/hooks/useMetrics.ts`**
- `useAuth()` importiert, `enabled: !!user && !!accessToken` in `useQuery` ergänzt
- Effekt: `/api/v2/dashboard/metrics` wird nicht mehr vor Auth-Restoration aufgerufen → kein 403

## Deploy-Schritte

```bash
# Backend (auth_service, stripe_routes, main_production)
docker compose restart complyo-backend

# Frontend (AuthContext, api.ts, useMetrics, OnboardingWizard, next.config.js CSP-Fix)
docker compose build complyo-dashboard
docker compose up -d complyo-dashboard
```
