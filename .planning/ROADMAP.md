# Roadmap: Complyo Security Hardening & Critical Fixes

## Overview

Dieser Milestone behebt kritische Sicherheitslücken und Revenue-Bugs die vor weiterem Featurebau geschlossen werden müssen. Phase 1 beseitigt die gravierendsten Auth-Lücken (Token-Exposure im Browser-Log, unauthentifizierte Produktions-Endpoints, Timezone-Bug). Phase 2 härtet die Stripe-Integration und schließt die Lücke bei Abo-Kündigungen. Phase 3 räumt den Tech-Debt auf der diese Bugs erst ermöglicht hat.

## Phases

- [ ] **Phase 1: Auth Security** — OAuth-Token-Exposure schließen, Auth-Stub entfernen, Admin-Endpoints sichern, Timezone-Bug fixen
- [ ] **Phase 2: Stripe Hardening** — Webhook-Secret guard, Add-on Cancellation/Updated/PaymentFailed implementieren
- [ ] **Phase 3: Tech Debt Consolidation** — Doppeltes JWT entfernen, legal_ai_routes.py löschen, API-URL-Duplikate konsolidieren

## Phase Details

### Phase 1: Auth Security
**Goal**: Alle aktiven Auth-Sicherheitslücken schließen — kein unauthentifizierter Produktions-Endpoint, keine Token in Server-Logs, kein Timezone-Mismatch bei Session-Expiry
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):
  1. OAuth-Callback-URL enthält keine Token in der Query-String — `?access_token=` erscheint nicht in Server-Logs oder Browser-History
  2. Alle `/api/legal-ai/*` Endpoints geben 401 zurück wenn kein gültiger JWT-Token mitgeschickt wird
  3. Admin-only Endpoints geben 403 zurück für normale authentifizierte User
  4. Expired Refresh-Tokens werden konsistent abgelehnt unabhängig von PostgreSQL-Timezone-Konfiguration
**Plans**: 4 plans

Plans:
- [x] 01-01: OAuth URL-Fragment fix — Backend redirect auf `#access_token=...`, Frontend liest aus `window.location.hash`
- [x] 01-02: legal_ai_routes.py Auth-Stub ersetzen — `get_current_user` Stub durch echten Depends aus `dependencies.py`
- [x] 01-03: `require_admin` auf alle Admin-Endpoints anwenden — `ai_legal_routes.py:762`, `ai_legal_routes.py:803`, `legal_change_routes.py:363`
- [x] 01-04: datetime.utcnow() Bug fixen — `auth_service.py:141` und `auth_service.py:181` auf `datetime.now(timezone.utc)` umstellen

### Phase 2: Stripe Hardening
**Goal**: Stripe Webhook-Integration ist sicher und vollständig — kein silent pass bei fehlendem Secret, keine unbezahlten Subscriptions die aktiv bleiben
**Depends on**: Phase 1
**Requirements**: AUTH-05, STRIPE-01, STRIPE-02, STRIPE-03
**Success Criteria** (what must be TRUE):
  1. Backend-Start schlägt mit `RuntimeError` fehl wenn `STRIPE_WEBHOOK_SECRET_ADDONS` nicht gesetzt ist
  2. Nach `customer.subscription.deleted` Event wird der Add-on-Zugang in der Datenbank sofort entzogen
  3. `customer.subscription.updated` und `invoice.payment_failed` Events werden verarbeitet und der Subscription-Status in der DB aktualisiert
**Plans**: 3 plans

Plans:
- [x] 02-01: Webhook Secret Guard in `addon_payment_routes.py` — `RuntimeError` bei leerem `STRIPE_WEBHOOK_SECRET_ADDONS` wie in `stripe_routes.py:38-40`
- [x] 02-02: Add-on Subscription Cancellation implementieren — `handle_addon_subscription_cancelled` entzieht DB-Zugang per `stripe_subscription_id`
- [x] 02-03: Add-on Subscription Updated + Payment Failed implementieren — `handle_addon_subscription_updated` und `handle_addon_payment_failed` Handler mit DB-Updates

### Phase 3: Tech Debt Consolidation
**Goal**: Dead Code und Duplikate entfernt — eine einzige JWT-Implementierung, kein unmountetes Auth-Stub-Modul, eine API-Base-URL-Quelle
**Depends on**: Phase 2
**Requirements**: DEBT-01, DEBT-02, DEBT-03
**Success Criteria** (what must be TRUE):
  1. `main_production.py` enthält keine standalone `create_jwt_token` / `verify_jwt_token` / `get_current_user` Funktionen mehr
  2. `legal_ai_routes.py` existiert nicht mehr und ist aus `main_production.py` ausgehängt
  3. API Base URL wird in `dashboard-react` aus einer einzigen Quelle (`lib/api-utils.ts`) importiert — kein `getApiBaseURL()` Duplikat in den anderen 5 Dateien
**Plans**: 3 plans

Plans:
- [x] 03-01: Duplikate JWT-Helpers aus `main_production.py:628-667` entfernen — alle Auth-Pfade routen durch `AuthService` / `dependencies.py`
- [x] 03-02: `legal_ai_routes.py` löschen und aus `main_production.py` aushängen (Import + Router-Include entfernen)
- [x] 03-03: API Base URL konsolidieren — `getApiBaseUrl()` nur in `lib/api-utils.ts`, alle 5 Duplikat-Dateien importieren daraus

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auth Security | 4/4 | Complete | 2026-03-29 |
| 2. Stripe Hardening | 3/3 | Complete | 2026-03-29 |
| 3. Tech Debt Consolidation | 3/3 | Complete | 2026-03-29 |
