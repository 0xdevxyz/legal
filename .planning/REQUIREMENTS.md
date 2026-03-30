# Requirements: Complyo Security Hardening & Critical Fixes

**Defined:** 2026-03-29
**Core Value:** Kunden müssen darauf vertrauen können, dass ihre Daten sicher sind und Subscriptions korrekt verwaltet werden.

## v1 Requirements

### Authentication & Security

- [ ] **AUTH-01**: OAuth-Tokens werden via URL-Fragment übertragen (`#access_token=...`), nicht via Query-String
- [ ] **AUTH-02**: `/api/legal-ai/*` Endpoints nutzen echte JWT-Authentifizierung (kein Fake-User-Stub)
- [ ] **AUTH-03**: Alle Admin-Endpoints sind mit `Depends(require_admin)` aus `backend/dependencies.py` geschützt
- [ ] **AUTH-04**: Refresh-Token-Expiry-Vergleich nutzt `datetime.now(timezone.utc)` konsistent (kein Timezone-Mismatch)
- [ ] **AUTH-05**: Stripe Add-on Webhook Secret schlägt bei fehlendem Env-Var mit RuntimeError fehl (kein silent pass)

### Stripe & Payments

- [ ] **STRIPE-01**: Add-on Subscription Cancellation entzieht Datenbankzugang sofort nach Stripe-Event
- [ ] **STRIPE-02**: Add-on Subscription Update und Payment-Failed Handler sind implementiert
- [ ] **STRIPE-03**: Stripe Webhook Secret Guard in `addon_payment_routes.py` entspricht dem in `stripe_routes.py`

### Tech Debt (Blocking)

- [ ] **DEBT-01**: Duplicate JWT-Funktionen in `main_production.py` (Zeilen 628-667) entfernt — nur noch `AuthService`
- [ ] **DEBT-02**: `legal_ai_routes.py` entfernt und aus `main_production.py` ausgehängt
- [ ] **DEBT-03**: API Base URL auf eine einzige Quelle konsolidiert (aktuell 6 Duplikate im Dashboard)

## v2 Requirements

### Testing

- **TEST-01**: Backend-Route-Tests für Auth-Flows
- **TEST-02**: Stripe Webhook Integration Tests
- **TEST-03**: Frontend Unit Tests für Auth-Context

### Performance

- **PERF-01**: `db_pool = None` Global-Pattern durch `Depends(get_db)` ersetzen (15+ Dateien)
- **PERF-02**: Background Worker auf `FOR UPDATE SKIP LOCKED` umstellen
- **PERF-03**: `SELECT *` durch explizite Spalten ersetzen (40+ Stellen)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Neue Features | Erst nach Security-Milestone |
| WordPress Plugin Änderungen | Eigener Scope, nicht kritisch |
| Landing Page Änderungen | Nicht sicherheitsrelevant |
| AI Document Generator TODO-Fixes | Feature-Work, nicht Security |
| Logging (print → logger) | Tech Debt, niedrige Priorität |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 2 | Pending |
| STRIPE-01 | Phase 2 | Pending |
| STRIPE-02 | Phase 2 | Pending |
| STRIPE-03 | Phase 2 | Pending |
| DEBT-01 | Phase 3 | Pending |
| DEBT-02 | Phase 3 | Pending |
| DEBT-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 after initialization*
