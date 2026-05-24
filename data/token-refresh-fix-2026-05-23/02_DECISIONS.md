# Entscheidungs-Log — Token-Refresh-Fix
**Datum:** 2026-05-23

## D-001: Refresh-Strategie — Client-seitig (Variante A)

**Entscheidung:** Token-Refresh läuft ausschließlich client-seitig via `POST /api/auth/refresh-cookie`.

**Begründung:**
- NextAuth-Server-Code hat keinen Zugriff auf den Browser-HttpOnly-Cookie.
- Der `jwt`-Callback in `auth.config.ts` läuft server-seitig und kann das Cookie nicht lesen.
- Variante B (refresh_token im NextAuth-JWT-Body) erzeugt doppeltes Token-Handling und ist schwerer zu warten.
- Variante A: Refresh im Axios-Interceptor → nach Erfolg `useSession().update()` aufrufen → NextAuth-Session synchron.

**Konsequenz:** Server-seitiger `jwt`-Callback nur für Ablauf-Tracking und Error-Propagation (`token.error`).

---

## D-002: Single-Flight-Refresh via Promise-Queue

**Entscheidung:** Bei N parallelen 401-Antworten wird genau ein Refresh-Request gestartet. Alle weiteren 401-Requests werden in eine `_pendingRequests`-Queue eingereiht und nach erfolgreichem Refresh mit dem neuen Token wiederholt.

**Begründung:** Ohne dieses Muster würden N parallele Requests N Refresh-Calls auslösen, was zu Race Conditions und Token-Rotation-Problemen führt (Backend rotiert Refresh-Token bei jedem Call).

---

## D-003: `lib/api.ts` bleibt als Wrapper erhalten

**Entscheidung:** `lib/api.ts` wird **nicht gelöscht**, sondern der interne `apiClient` wird durch Import aus `api-client.ts` ersetzt. Die Business-Funktionen (`analyzeWebsite`, `generateFix` etc.) bleiben unverändert.

**Begründung:**
- Zu viele Importe zeigen auf `lib/api.ts` (domainspezifische Funktionen).
- Ein Hard-Delete würde Build-Fehler erzeugen.
- Der Fix der Token-Logik reicht, wenn der zugrundeliegende Axios-Client der gleiche ist.

---

## D-004: `auth-helper.ts` als Deprecated-Wrapper beibehalten

**Entscheidung:** `auth-helper.ts` wird nicht gelöscht, sondern re-exportiert aus `auth-refresh.ts` mit `@deprecated`-Markierung.

**Begründung:** Bricht keine bestehenden Imports, macht Migration sichtbar ohne sofortigen Handlungsbedarf.

---

## D-005: Cookie-Domain-Setup

**Produktions-Domain:** `api.complyo.tech` (Backend) und `app.complyo.tech` (Frontend).

**Einstellung:** `SameSite=Lax` für `refresh_token`-Cookie, `Secure=true`, `HttpOnly=true`.

**Cross-Origin-Hinweis:** Bei Cross-Origin-Requests (app.complyo.tech → api.complyo.tech) muss `withCredentials: true` im Axios-Client gesetzt sein (bereits der Fall) und CORS muss `allow_credentials=True` mit explizit gesetzter `allow_origins`-Liste (kein `*`) konfiguriert sein.

---

## D-006: `accessTokenExpiresAt` im NextAuth-JWT

**Entscheidung:** `accessTokenExpiresAt` als Unix-Timestamp (ms) im NextAuth-JWT speichern. Berechnet als `Date.now() + 60 * 60 * 1000` beim Login. Proaktiver Refresh 5 Minuten vor Ablauf via `signOut` + `error`-Feld (kein server-seitiger Refresh, wegen D-001).

**Konsequenz:** `AuthContext.tsx` reagiert auf `session.error === 'RefreshAccessTokenError'` mit sauberem Logout.
