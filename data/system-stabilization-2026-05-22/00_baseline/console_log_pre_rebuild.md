# Browser-Konsolen-Log Pre-Rebuild
Datum: 2026-05-22
Quelle: app.complyo.de (user-reported screenshots)

## Kritische Fehler

### Auth-Endlosschleife
```
POST /api/auth/refresh-cookie 401 (Unauthorized)
```
- Tritt sofort bei Page-Load auf
- Keine Abbruchbedingung → Endlosschleife
- Root Cause: AuthContext.tsx ruft refresh auch ohne Cookie auf (RC-2)

### API-Authentifizierungsfehler
```
GET /api/v2/websites 401 (Unauthorized)
GET /api/legal-ai/updates 401 (Unauthorized)
```
- Folgefehler aus Auth-Schleife
- Session-State verloren nach Page-Reload

### Widget-Verbindungsfehler
```
GET https://api.complyo.tech/api/accessibility/alt-text-fixes ERR_CONNECTION_TIMED_OUT
```
- Root Cause: Widgets hardcoded auf api.complyo.tech statt api.complyo.de (RC-6)
- Betrifft: accessibility.js, accessibility-v5.js, accessibility-v6.js, accessibility_smart.js, optout_center.js, cookie_consent.legacy.js

### Re-Scan 500
```
POST /api/v2/analyze 500 (Internal Server Error)
```
- Root Cause: Unbekannt, Diagnose steht aus (RC-4)

### Stripe-Checkout
- Alle Checkout-Links kaputt
- Root Cause: Frontend ruft /api/v2/payments/create-checkout-session, existiert nicht
- Korrekt: /api/stripe/create-checkout (RC-7)

## Onboarding-Loop
- Onboarding erscheint nach Browser-Neustart, obwohl abgeschlossen
- Root Cause: Cookie-Path-Mismatch → set_cookie(path="/") vs delete_cookie(path="/api/auth") (RC-1)
- Cookie wird nie gelöscht → Session-State geht verloren

## Container-Status zum Zeitpunkt der Analyse
```
complyo-dashboard    Up 6 days (unhealthy)
complyo-landing      Up 6 days (unhealthy)
complyo-backend      Up 5 days (healthy)
```
- Dashboard und Landing markiert als unhealthy
