# Roadmap: Technical Debt & Feature Completeness

## Overview

Dieser Milestone schließt die letzten offenen Auth-Lücken, persistiert Analytics-Daten in der Datenbank und vervollständigt zwei konkrete Features (Email-Benachrichtigung + Cookie-Settings-Modal). Alle Items stammen aus `docs/TECHNICAL_DEBT.md` (Critical/High/Medium).

## Phases

- [x] **Phase 1: Auth-Debt** — Letzte ungesicherte Endpoints in widget_routes.py absichern
- [x] **Phase 2: DB-Integration** — 5 Stellen die Daten nur loggen auf echte DB-Persistenz umstellen
- [x] **Phase 3: Feature-Vervollständigung** — Email-Service + Cookie-Settings-Modal implementiert

## Phase Details

### Phase 1: Auth-Debt
**Goal**: Alle noch ungesicherten Endpoints geben 401 ohne gültigen JWT zurück; kein Hardcode user_id mehr
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-10, AUTH-11
**Success Criteria** (what must be TRUE):
  1. `POST /api/accessibility/patches/generate` gibt 401 ohne Bearer Token zurück
  2. `user_id=1` Hardcode in `generate_accessibility_patches` entfernt — user_id kommt aus JWT
  3. Alle bestehenden geschützten Endpoints in `cookie_compliance_routes.py` geben weiterhin korrekt 401 zurück
**Plans**: 2 plans

Plans:
- [x] 01-01: `widget_routes.py` — `get_current_user` aus `dependencies.py` einbinden, `user_id=1` Hardcode entfernen, `db_pool: asyncpg.Pool = Depends(lambda: None)` auf echten Pool umstellen
- [x] 01-02: `cookie_compliance_routes.py` — Auth-Flow verifiziert: alle Endpoints die `get_current_user_required` verwenden geben korrekt 401 zurück

### Phase 2: DB-Integration
**Goal**: Widget-Events, Feedback und Config werden in der Datenbank persistiert statt nur geloggt
**Depends on**: Phase 1
**Requirements**: DB-01, DB-02, DB-03, DB-04, DB-05
**Success Criteria** (what must be TRUE):
  1. `/api/widgets/track` INSERT landet in `widget_events` Tabelle (Migration falls nötig)
  2. `_check_upsell_opportunity` führt echte COUNT-Abfrage auf `widget_usage_stats` durch
  3. `/api/widgets/config/{site_id}` lädt Config aus DB mit Default-Fallback
  4. Feedback in `ai_legal_routes.py` wird in DB gespeichert
  5. `/sites/{site_id}/widget-feedback` in `public_routes.py` persistiert in DB
  6. Kein Endpoint bricht bei DB-Fehler — alle Analytics-Pfade haben silent-fail
**Plans**: 5 plans

Plans:
- [x] 02-01: `widget_routes.py:215` — `track_widget_event` DB-INSERT aktivieren + Migration `create_widget_events.sql`
- [x] 02-02: `widget_routes.py:306` — `_check_upsell_opportunity` echte DB-Abfrage auf `widget_usage_stats`
- [x] 02-03: `widget_routes.py:326` — `get_widget_config` aus `cookie_banner_configs` DB laden mit Default-Fallback
- [x] 02-04: `ai_legal_routes.py:173` — Feedback INSERT in `legal_update_feedback` Tabelle (bereits via `ai_feedback_learning` implementiert, verifiziert)
- [x] 02-05: `public_routes.py:1388` — `widget_feedback` INSERT in `widget_events` analog zu 02-01

### Phase 3: Feature-Vervollständigung
**Goal**: Email-Notifications für Expert-Anfragen funktionieren; Cookie-Settings-Modal ist bedienbar
**Depends on**: Phase 2
**Requirements**: FEAT-01, FEAT-02
**Success Criteria** (what must be TRUE):
  1. Expert-Anfrage löst 2 Emails aus: Kunden-Bestätigung + Team-Notification (via `email_service._send_email`)
  2. Email-Versand-Fehler bricht die Expert-Anfrage nicht ab (bestehender try/except bleibt)
  3. Cookie-Settings-Modal öffnet sich wenn User auf Settings-Button klickt
  4. Modal zeigt Kategorien mit Toggles; Speichern-Button ruft Consent-Update auf
  5. Modal-Stil konsistent mit bestehendem Banner
**Plans**: 2 plans

Plans:
- [x] 03-01: `expert_service_routes.py:271` — `EmailService` importieren, `_send_email` für Kunde + Team aufrufen
- [x] 03-02: `widgets/cookie_consent.js:214` — Settings-Modal implementieren mit Kategorien-Toggles und Consent-Persistierung

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auth-Debt | 2/2 | Complete | 2026-04-21 |
| 2. DB-Integration | 5/5 | Complete | 2026-04-21 |
| 3. Feature-Vervollständigung | 2/2 | Complete | 2026-04-21 |
