# Smoke Test Report — 2026-05-22

## Login

- **URL after login:** `https://app.complyo.de/`
- **Page title:** `Complyo Dashboard - KI-gestützte Website-Compliance`
- **Result:** Login successful. Redirect to `/` after submitting credentials. No error messages visible on the login form.

## Dashboard

- **URL:** `https://app.complyo.de/`
- **Account shown:** `PanoArt360 — Kostenlos`
- **Compliance Score:** 0/100 (website `https://complyo.de` registered, not yet scanned for this account)
- **Visible errors on page:** None in snapshot. 2 console errors + 2 warnings recorded at login time (see console section below).
- **Screenshot:** `/tmp/smoke_dashboard.png` (1.0 MB, full-page)

## Subscription Page

- **URL:** `https://app.complyo.de/subscription`
- **Page title:** `Complyo Dashboard - KI-gestützte Website-Compliance`
- **Page loaded:** Yes — full pricing table rendered (Einzelne Säule 19€, Pro-Paket 49€, Agentur 299€)
- **Current plan shown:** `Unbekannt` (label says "Kostenlos" in badge)
- **Visible errors:** None in snapshot. 1 console error (see below).
- **Screenshot:** `/tmp/smoke_subscription.png` (392 KB, full-page)

## Console Logs (subscription page, final state)

Total: 17 messages — **1 error, 0 warnings**

### Error
```
[ERROR] Failed to load resource: 500 Internal Server Error
  @ https://api.complyo.de/api/legal-notifications/stats
```

### Notable log entries
```
[LOG] [Complyo] ✅ Keine Tracking-Services konfiguriert - kein Banner erforderlich
[LOG] [Complyo] ℹ️ Ihre Website verwendet nur essenzielle Cookies
[LOG] [Complyo] Google Consent Mode v2 initialized (default: denied)
[LOG] [Complyo] Keine gescannten Services für diese Website
```

All other messages are normal widget initialization logs.

## Summary

| Check | Result |
|---|---|
| Login successful | Yes |
| URL after login | `https://app.complyo.de/` |
| Dashboard loads | Yes |
| Dashboard errors (visible) | None |
| Subscription page loads | Yes |
| Subscription page errors (visible) | None |
| Console errors | 1 — `GET /api/legal-notifications/stats` returns 500 |
| Screenshots saved | `/tmp/smoke_dashboard.png`, `/tmp/smoke_subscription.png` |
