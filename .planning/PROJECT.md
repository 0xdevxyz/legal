# Complyo — Technical Debt & Feature Completeness

## What This Is

Complyo ist eine SaaS-Plattform die Websites automatisch auf DSGVO/TTDSG-Verstöße scannt, KI-generierte Fixes vorschlägt und rechtlich konforme Texte verwaltet. Das Backend ist ein FastAPI-Monolith mit 30+ Routen, zwei Next.js-Frontends (Landing + Dashboard) und Integrationen zu Stripe, eRecht24, Firebase Auth und OpenRouter AI.

Dieser Milestone schließt alle offenen Critical/High-Debt-Items und zwei mittlere Features, die nach dem Security-Hardening-Milestone (v1, abgeschlossen 2026-03-29) noch offen sind.

## Core Value

Das System ist live. Ziel ist es, die letzten ungesicherten Endpoints abzusichern, Analytics-Daten persistent zu speichern und zwei konkrete Features (Email-Notification + Cookie-Settings-Modal) funktionsfähig zu machen.

## Previous Milestone

v1 "Security Hardening & Critical Fixes" — abgeschlossen 2026-03-29. Alle 10 Plans erledigt.
Archiviert unter: `.planning/archive/`

## Requirements

### Validated (aus v1 übernommen, weiterhin gültig)

- ✓ Multi-Site-Support und Agency-Plan — existing
- ✓ Cookie Compliance mit Banner-Generator — existing
- ✓ Accessibility Widget + Patch-Downloads — existing
- ✓ Legal Change Monitoring — existing
- ✓ AI Compliance Scanner und Fix-Generator — existing
- ✓ Stripe Subscriptions (Plans + Add-ons) — existing
- ✓ Google/Apple OAuth via Firebase — existing
- ✓ JWT-Authentifizierung mit Refresh Tokens — existing

### Active (dieser Milestone)

- [ ] AUTH-10: `cookie_compliance_routes.py` ungesicherte Endpoints mit `get_current_user` absichern
- [ ] AUTH-11: `widget_routes.py` generate-patches Endpoint mit `get_current_user` absichern
- [ ] DB-01: Widget-Tracking-Events (`/api/widgets/track`) in DB persistieren
- [ ] DB-02: Upsell-Check (`_check_upsell_opportunity`) mit echter DB-Abfrage implementieren
- [ ] DB-03: Widget-Config (`/api/widgets/config/{site_id}`) aus DB laden
- [ ] DB-04: ML-Feedback (`ai_legal_routes.py:173`) in DB speichern
- [ ] DB-05: Widget-Feedback (`public_routes.py:1388`) in DB persistieren
- [ ] FEAT-01: Email-Service in `expert_service_routes.py` integrieren (2 Emails: Kunde + Team)
- [ ] FEAT-02: Cookie-Settings-Modal in `widgets/cookie_consent.js` implementieren

### Out of Scope

- Neue Features jenseits der definierten Items
- UI-Redesign oder neue Integrationen
- Mobile App, Browser-Extension, VS-Code-Plugin
