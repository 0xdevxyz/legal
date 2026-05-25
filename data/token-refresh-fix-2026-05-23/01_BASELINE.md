# Baseline — Token-Refresh-Fix
**Datum:** 2026-05-23

## Backend-Konfiguration (unveränderter Stand)

| Parameter | Wert | Quelle |
|---|---|---|
| Access-Token-Lebensdauer | 60 Minuten | `AUTH_SERVICE_EXPIRE_MINUTES` env / `auth_service.py:29` |
| Refresh-Token-Lebensdauer | 30 Tage | `REFRESH_TOKEN_EXPIRE_DAYS` env / `auth_service.py:30` |
| Token-Rotation | Ja | `auth_service.py:refresh_access_token()` |
| Refresh-Cookie-Endpoint | `POST /api/auth/refresh-cookie` | `auth_routes.py:247` |
| Refresh-Body-Endpoint | `POST /api/auth/refresh` | `auth_routes.py:217` |
| Cookie-Name | `refresh_token` | `auth_routes.py:126` |
| Cookie-Flags | `httponly=True, secure=True, samesite="lax"` | `auth_routes.py:127` |

## Aktueller Frontend-Flow (defekt)

```
1. Login → access_token in localStorage + window.__complyo_access_token + NextAuth-JWT
2. Request → Axios Request-Interceptor → resolveAccessToken() → localStorage.getItem('access_token')
3. Nach 60 Min: Token abgelaufen
4. Backend antwortet 401
5. Response-Interceptor: original._retry = true → resolveAccessToken() erneut
   → gibt denselben abgelaufenen Token zurück (kein Refresh!)
6. Zweiter Request: erneut 401
7. delete window.__complyo_access_token → window.location.href = '/login'
8. User wird ausgeloggt ❌
```

## Direkt-Zugriffe auf localStorage (38 Stellen)

| Datei | Zeile | Code |
|---|---|---|
| `lib/api-client.ts` | 11 | `localStorage.getItem("access_token")` |
| `lib/api.ts` | 20 | `localStorage.getItem('access_token')` |
| `lib/auth-helper.ts` | 5 | `localStorage.getItem('access_token')` |
| `lib/ai-compliance-api.ts` | 35 | `localStorage.getItem('access_token')` |
| `contexts/AuthContext.tsx` | 80 | `localStorage.setItem('access_token', ...)` |
| `contexts/AuthContext.tsx` | 91 | `localStorage.removeItem('access_token')` |
| `contexts/AuthContext.tsx` | 128 | `localStorage.removeItem('access_token')` |
| `components/setup/ERecht24Setup.tsx` | 85 | `localStorage.getItem('access_token')` |
| `components/cookie-compliance/RevocationChart.tsx` | 51 | `localStorage.getItem('access_token')` |
| `components/cookie-compliance/ConsentModeSettings.tsx` | 32 | `localStorage.getItem('token') \|\| localStorage.getItem('access_token')` |
| `components/cookie-compliance/ServiceManager.tsx` | 61 | `localStorage.getItem('token') \|\| localStorage.getItem('access_token')` |
| `components/cookie-compliance/TCFManager.tsx` | 45 | `localStorage.getItem('token') \|\| localStorage.getItem('access_token')` |
| `components/fixes/ApplyFixModal.tsx` | 114 | `localStorage.getItem('access_token')` |
| `components/dashboard/ExpertServiceModal.tsx` | 34 | `localStorage.getItem('access_token')` |
| `components/dashboard/LegalTextWizard.tsx` | 75 | `localStorage.getItem('access_token')` |
| `components/dashboard/ComplianceIssueGroup.tsx` | 128 | `localStorage.getItem('access_token')` |
| `components/dashboard/ComplianceIssueGroup.tsx` | 160 | `localStorage.getItem('access_token')` |
| `components/dashboard/ComplianceIssueCard.tsx` | 193 | `localStorage.getItem('access_token')` |
| `components/dashboard/ComplianceIssueCard.tsx` | 456 | `localStorage.getItem('access_token')` |
| `components/dashboard/DomainLockStatus.tsx` | 34 | `localStorage.getItem('access_token')` |
| `components/dashboard/CookieComplianceWidget.tsx` | 40 | `localStorage.getItem('token') \|\| localStorage.getItem('access_token')` |
| `components/dashboard/TCFComplianceWidget.tsx` | 58 | `localStorage.getItem('access_token')` |
| `components/dashboard/LegalArchiveModal.tsx` | 56 | `localStorage.getItem('access_token')` |
| `components/dashboard/LegalNews.tsx` | 186 | `localStorage.getItem('access_token')` |
| `components/legal/LegalDocumentGenerator.tsx` | 184 | `localStorage.getItem('access_token')` |
| `components/legal-changes/LegalActionWidget.tsx` | 69 | `localStorage.getItem('access_token')` |
| `components/legal-changes/LegalActionWidget.tsx` | 113 | `localStorage.getItem('access_token')` |
| `components/legal-changes/LegalActionWidget.tsx` | 140 | `localStorage.getItem('access_token')` |
| `app/cookie-compliance/page.tsx` | 66 | `localStorage.getItem('token') \|\| localStorage.getItem('access_token')` |
| `app/profile/page.tsx` | 40 | `localStorage.getItem('access_token')` |
| `app/register/page.tsx` | 84 | `localStorage.getItem('access_token')` |

## Bekannte Probleme (vor Fix)

1. **Kein Refresh beim 401**: Interceptor ruft nie `POST /api/auth/refresh-cookie` auf.
2. **Veralteter Token im Retry**: Bei 401 wird derselbe abgelaufene Token nochmal versucht.
3. **Hard-Redirect**: Kein sauberer `signOut()`, nur `window.location.href = '/login'`.
4. **NextAuth-Session entkoppelt**: `jwt`-Callback aktualisiert `accessToken` nie nach Login.
5. **Kein Single-Flight-Schutz**: Parallele 401-Antworten würden N Refresh-Calls auslösen.
6. **28+ Komponenten** umgehen den Interceptor via direktem `fetch + localStorage`.
