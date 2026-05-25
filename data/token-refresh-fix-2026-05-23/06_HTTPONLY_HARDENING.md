# Phase 5 — HttpOnly-Härtung: Access-Token aus localStorage entfernt
**Datum:** 2026-05-23

## Ziel

Access-Token verlässt `localStorage` vollständig. XSS-Angriffe können den Token nicht mehr über `document.cookie` oder `localStorage` stehlen.

## Vorher / Nachher

| | Vorher | Nachher |
|---|---|---|
| `localStorage['access_token']` | Token gespeichert (XSS-angreifbar) | Nicht vorhanden (`null`) |
| Memory-Cache `window.__complyo_access_token` | Vorhanden | Weiterhin vorhanden (verschwindet bei Reload) |
| HttpOnly-Cookie `access_token` | Nicht vorhanden | Gesetzt vom Backend (nicht via JS lesbar) |
| HttpOnly-Cookie `refresh_token` | Vorhanden | Unverändert |

## Backend-Änderungen (`auth_routes.py`)

Alle drei Token-ausliefernden Endpoints setzen jetzt zusätzlich ein `access_token` HttpOnly-Cookie:

- `POST /api/auth/register` — `access_token`-Cookie + `refresh_token`-Cookie
- `POST /api/auth/login` — `access_token`-Cookie + `refresh_token`-Cookie
- `POST /api/auth/refresh-cookie` — `access_token`-Cookie + `refresh_token`-Cookie

Cookie-Konfiguration:
```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,        # Nur über HTTPS
    samesite="lax",
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    path="/",
    domain=COOKIE_DOMAIN
)
```

## Backend-Änderungen (`dependencies.py`)

`get_current_user` und `get_current_user_optional` lesen Token jetzt aus:
1. `Authorization: Bearer <token>` Header (weiterhin unterstützt)
2. `access_token` HttpOnly-Cookie (neu, Fallback)

Priorität: Header > Cookie.

## Frontend-Änderungen

### `lib/auth-refresh.ts`
- `getAccessToken()`: Liest **nur** aus Memory-Cache (`window.__complyo_access_token`), kein `localStorage` mehr
- `setAccessToken()`: Schreibt **nur** in Memory-Cache
- `clearAccessToken()`: Löscht **nur** Memory-Cache

### `app/auth/callback/page.tsx`
- Kein `localStorage.setItem('access_token')` mehr
- Nutzt `setAccessToken()` (Memory) + `apiClient` mit `withCredentials` (Cookie)

### `components/SocialLoginButtons.tsx`
- Kein `localStorage.setItem('access_token')` mehr
- Nutzt `setAccessToken()` + `apiClient.post` für Checkout

## XSS-Verifikation

Nach Deployment in DevTools-Konsole prüfen:
```js
localStorage.getItem('access_token')  // → null ✅
document.cookie  // → refresh_token und access_token nicht sichtbar (httponly) ✅
window.__complyo_access_token  // → vorhanden (Memory, verschwindet bei Reload)
```

## Auth-Flow nach Reload

1. Browser sendet `access_token`-Cookie automatisch mit jedem Request (`withCredentials: true`)
2. Backend validiert Token aus Cookie → 200
3. Wenn Cookie abgelaufen: Backend antwortet 401
4. Axios-Interceptor: `refreshAccessToken()` → `POST /api/auth/refresh-cookie`
5. Neuer `access_token`-Cookie wird gesetzt, Memory-Cache befüllt
6. Original-Request wird wiederholt
