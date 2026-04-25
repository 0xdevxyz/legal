# Complyo — Security Hardening & Critical Fixes

## What This Is

Complyo ist eine SaaS-Plattform die Websites automatisch auf DSGVO/TTDSG-Verstöße scannt, KI-generierte Fixes vorschlägt und rechtlich konforme Texte verwaltet. Das Backend ist ein FastAPI-Monolith mit 30+ Routen, zwei Next.js-Frontends (Landing + Dashboard) und Integrationen zu Stripe, eRecht24, Firebase Auth und OpenRouter AI.

Dieser Milestone fokussiert auf **kritische Sicherheitslücken und Revenue-Bugs** die vor weiterem Featurebau behoben werden müssen.

## Core Value

Kunden müssen darauf vertrauen können, dass ihre Compliance-Daten sicher sind und ihre Subscriptions korrekt verwaltet werden.

## Requirements

### Validated

- ✓ Multi-Site-Support und Agency-Plan — existing
- ✓ Cookie Compliance mit Banner-Generator — existing
- ✓ Accessibility Widget + Patch-Downloads — existing
- ✓ Legal Change Monitoring (EUR-Lex, eRecht24) — existing
- ✓ AI Compliance Scanner und Fix-Generator — existing
- ✓ Stripe Subscriptions (Plans + Add-ons) — existing
- ✓ Google/Apple OAuth via Firebase — existing
- ✓ JWT-Authentifizierung mit Refresh Tokens — existing

### Active

- [ ] AUTH-01: OAuth-Tokens werden via URL-Fragment übertragen, nicht Query-String
- [ ] AUTH-02: `legal_ai_routes.py` Auth-Stub durch echte Authentifizierung ersetzen
- [ ] AUTH-03: Admin-Endpoints mit `require_admin` absichern
- [ ] AUTH-04: `datetime.utcnow()` durch `datetime.now(timezone.utc)` ersetzen (Session-Expiry-Bug)
- [ ] STRIPE-01: Add-on Subscription Cancellation implementieren (Zugang wird nach Kündigung entzogen)
- [ ] STRIPE-02: Stripe Webhook Secret Guard für Add-on-Handler
- [ ] DEBT-01: Doppelte JWT-Implementierung in `main_production.py` entfernen
- [ ] DEBT-02: `legal_ai_routes.py` und `ai_legal_routes.py` konsolidieren
- [ ] DEBT-03: API Base URL auf single source of truth reduzieren (6 Duplikate)

### Out of Scope

- Neue Features — erst nach diesem Security-Milestone
- Frontend-Tests — separater Milestone
- `db_pool = None` Migrations zu `Depends(get_db)` — zu groß für diesen Milestone, separat
- Performance-Optimierungen (SELECT *, Background Worker) — separater Milestone

## Context

- Backend: `backend/` — FastAPI, Python 3.11, asyncpg, 30+ Routen
- Dashboard: `dashboard-react/` — Next.js 14, TypeScript
- Auth: Firebase (OAuth) + eigenes JWT-System in `backend/auth_service.py`
- Payments: Stripe — drei separate Webhook-Handler in `payment_routes.py`, `stripe_routes.py`, `main_production.py`
- Kritischste Datei: `backend/main_production.py` (1847 Zeilen) — Startup, Routing, JWT-Duplikat
- Codebase-Map: `.planning/codebase/` (erstellt 2026-03-29)

## Constraints

- **Kompatibilität**: Keine Breaking Changes an der Auth-API — Mobile/WordPress-Clients müssen weiter funktionieren
- **Deployment**: Docker Compose auf eigenem Server, kein CI/CD — manuelle Deployments
- **Testing**: Kein Test-Framework für Backend-Routes vorhanden — Fixes müssen manuell verifizierbar sein
- **Stripe**: Webhook-Änderungen müssen im Stripe-Dashboard synchron aktualisiert werden

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Security-Milestone vor Feature-Arbeit | Auth-Stub in Produktion ist kritisches Risiko | — Pending |
| `legal_ai_routes.py` komplett entfernen statt fixen | Redundant zu `ai_legal_routes.py`, kein Value | — Pending |
| URL-Fragment statt Query-String für OAuth | Tokens dürfen nicht in Server-Logs erscheinen | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-29 after initialization*
