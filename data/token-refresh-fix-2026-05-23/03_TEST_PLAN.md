# Test-Plan — Token-Refresh-Fix

## Szenarien

### S1: Access-Token läuft ab → transparenter Refresh

**Vorbedingung:** User ist eingeloggt.  
**Setup:** `ACCESS_TOKEN_EXPIRE_MINUTES=1` in `.env` (1 Minute für Tests).  
**Schritte:**
1. Einloggen
2. 61 Sekunden warten
3. Beliebigen API-Call auslösen (z. B. Dashboard laden)

**Erwartet:** API-Call gelingt, kein Logout, Network-Tab zeigt `POST /api/auth/refresh-cookie` gefolgt vom originalen Request.  
**Pass-Kriterium:** Kein Redirect nach `/login`.

---

### S2: 5 parallele Requests bei abgelaufenem Token → Single-Flight

**Setup:** Token abgelaufen (S1-Setup), 5 gleichzeitige API-Calls triggern.  
**Erwartet:** Genau **1** `POST /api/auth/refresh-cookie` im Network-Tab, alle 5 Requests erhalten 2xx.  
**Pass-Kriterium:** Network-Tab zeigt ≤1 Refresh-Call.

---

### S3: Refresh-Token abgelaufen → sauberer Logout

**Setup:** `REFRESH_TOKEN_EXPIRE_DAYS=0` ODER `user_sessions`-Eintrag manuell löschen.  
**Schritte:**
1. Access-Token abgelaufen
2. API-Call auslösen
3. Interceptor ruft `refresh-cookie` auf
4. Backend antwortet 401

**Erwartet:** `signOut({ callbackUrl: '/login' })` → Redirect nach `/login`, kein Endlos-Loop.  
**Pass-Kriterium:** User landet auf Login-Seite, keine Konsolen-Fehler-Schleife.

---

### S4: Refresh-Token revoziert (nach Logout) → Redirect

**Setup:** User loggt sich aus (Refresh-Token in DB gelöscht), Access-Token noch vorhanden.  
**Schritte:** In neuem Tab API-Call auslösen.  
**Erwartet:** `refresh-cookie` schlägt fehl → Redirect nach `/login`.

---

### S5: Migrierte Komponente nutzt neuen Token

**Ziel:** `ComplianceIssueGroup`, `ApplyFixModal` etc. nutzen nach Migration `apiClient`.  
**Prüfung:** Network-Tab zeigt `Authorization: Bearer <token>` ohne `localStorage`-Direktzugriff.  
**Pass-Kriterium:** Requests erfolgreich, Token ist aktuell (Timestamp prüfen via jwt.io).

---

### S6: NextAuth-Session-Update nach Refresh sichtbar

**Schritte:**
1. Token abgelaufen
2. API-Call triggert Refresh
3. `useSession().data.accessToken` in DevTools prüfen (via React DevTools)

**Erwartet:** `accessToken` in Session enthält neuen Token (anderer `exp`-Timestamp).  
**Pass-Kriterium:** Session ist aktuell nach Refresh.

---

## Smoke-Tests (manuell, schnell)

```bash
# Backend: Refresh-Cookie-Endpoint
curl -X POST https://api.complyo.tech/api/auth/refresh-cookie \
  -H "Content-Type: application/json" \
  --cookie "refresh_token=<valid_token>" \
  -v

# Erwartet: 200 + { access_token, refresh_token }

# Mit ungültigem Cookie:
curl -X POST https://api.complyo.tech/api/auth/refresh-cookie \
  -H "Content-Type: application/json" \
  --cookie "refresh_token=invalid" \
  -v

# Erwartet: 401
```

## Akzeptanzkriterien Gesamt

- [ ] S1: Transparent Refresh — Pass
- [ ] S2: Single-Flight — Pass
- [ ] S3: Expired Refresh-Token → Logout — Pass
- [ ] S4: Revoked Refresh-Token → Redirect — Pass
- [ ] S5: Migrierte Komponenten nutzen Token korrekt — Pass
- [ ] S6: NextAuth-Session aktuell nach Refresh — Pass
- [ ] `localStorage.getItem('access_token')` nur noch in `auth-refresh.ts` — Pass
- [ ] ESLint blockiert neue Direkt-Zugriffe — Pass
