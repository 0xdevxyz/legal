# Complyo Audit Status — Cookie, BFSG & Rechtstexte
_Stand: 2026-05-01 — ALLE PHASEN ABGESCHLOSSEN_

## Gesamtübersicht

| Phase | Audit-IDs | Status | Tests |
|-------|-----------|--------|-------|
| Phase 1: Critical Compliance Fixes | AUDIT-01–04 | **COMPLETE** | 11 Unit-Tests grün |
| Phase 2: Accessibility Statement Generator | AUDIT-05 | **COMPLETE** | 8 Tests grün |
| Phase 3: E2E Compliance Test Suite | AUDIT-06–08 | **COMPLETE** | 32 Tests grün |
| Phase 4: Mobile & Extended WCAG | AUDIT-09–13 | **COMPLETE** | 13 Tests grün |
| Phase 5: Dashboard ATAG Compliance | AUDIT-14–15 | **COMPLETE** | DB-Tabelle + Endpoints verifiziert |
| Phase 6: Advanced Cookie Features | AUDIT-16–19 | **COMPLETE** | Endpoints + DB-Migrations |
| Phase 7: CMS Docs & Widget Performance | AUDIT-20–23 | **COMPLETE** | Axe-Core npm script + Seiten |
| Phase 8: Enterprise & International | AUDIT-24–27 | **COMPLETE** | 4 Endpoints + Dashboard-Seiten |
| Phase 9: Rechtstexte & DSGVO Audit | AUDIT-28 | **COMPLETE** | 10 Tests grün |
| BUG-01: Schema-Fix | — | **FIXED** | INSERT-Test grün |

---

## Phase 1: Critical Compliance Fixes — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-01 | BFSG-Disclaimer auf Landing Page | `BfsgDisclaimer.tsx` in alle 3 A/B-Varianten | `landing-react/src/components/BfsgDisclaimer.tsx` |
| AUDIT-02 | TCF 2.2 "Coming Soon" (war "Beta") | Badge + Widget-Kommentar | `AdvancedSettings.tsx`, `TCFManager.tsx`, `cookie_banner_v2.js` |
| AUDIT-03 | User-Agent PII-Minimierung | `truncate_user_agent()` mit findall+min | `backend/cookie_compliance_routes.py:233` |
| AUDIT-04 | HSTS + Security-Header nginx | 5 Header in alle 4 HTTPS-Blöcke | `/etc/nginx/sites-available/complyo.de` |

---

## Phase 2: Accessibility Statement Generator — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-05 | BFSG-Barrierefreiheitserklärung | Backend Jinja2-Endpoint + Dashboard-UI | `accessibility_fix_routes.py:495`, `StatementGenerator.tsx`, `accessibility/statement/page.tsx` |

---

## Phase 3: E2E Compliance Test Suite — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-06 | Cookie Consent Flow E2E | Python TestClient Tests | `backend/tests/test_consent_flow.py` |
| AUDIT-07 | Accessibility Widget E2E | Playwright Tests | `tests/e2e/accessibility-widget.spec.ts` |
| AUDIT-08 | DSGVO §25 TTDSG Tests | Pytest + Playwright | `test_dsgvo_compliance.py`, `test_tcf_compliance.py`, `cookie-compliance.spec.ts` |

---

## Phase 4: Mobile & Extended WCAG — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-09 | Touch-Targets 44×44px (WCAG 2.5.5) | `_check_touch_targets()` Scanner-Regel | `compliance_engine/checks/barrierefreiheit_check.py` |
| AUDIT-10 | WCAG AAA: Vague Links, Line-Height | `_check_wcag_aaa()` | `barrierefreiheit_check.py` |
| AUDIT-11 | Tabellen/SVG/Canvas-Accessibility | `_check_tables_svg_canvas()` | `barrierefreiheit_check.py` |
| AUDIT-12 | Video Caption Check (WCAG 1.2.2) | `_check_video_captions()` | `barrierefreiheit_check.py` |
| AUDIT-13 | PDF-Links Info-Hinweis | `_check_pdf_links()` | `barrierefreiheit_check.py` |

**Tests:** `backend/tests/test_wcag_extended.py` — 13 Tests, alle grün

---

## Phase 5: Dashboard ATAG Compliance — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-14 | Focus-Indikatoren (WCAG 2.4.7, ATAG) | `:focus-visible` in globals.css | `dashboard-react/src/app/globals.css` |
| AUDIT-15 | Alt-Text Review Queue | 4 Endpoints + Komponente + Seite | `accessibility_fix_routes.py`, `AltTextReviewQueue.tsx`, `accessibility/review/page.tsx` |

**DB-Migration:** `backend/migrations/create_alt_text_review_queue.sql`

---

## Phase 6: Advanced Cookie Features — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-16 | Consent Revocation (DSGVO Art. 7 Abs. 3) | `POST /api/cookie-compliance/revoke` | `cookie_compliance_routes.py` |
| AUDIT-17 | Revocation Analytics Chart | `GET /api/cookie-compliance/revocation-stats/{site_id}` | `cookie_compliance_routes.py` |
| AUDIT-18 | Per-Service Consent Stats | `GET /api/cookie-compliance/service-stats/{site_id}` | `cookie_compliance_routes.py` |
| AUDIT-19 | DPA-Generator (AV-Vertrag DSGVO Art. 28) | `POST /api/v2/legal/generate-dpa` | `backend/legal_document_routes.py` |

**DB-Migrations:** `add_action_to_consent_logs.sql`

---

## Phase 7: CMS Docs & Widget Performance — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-20 | CMS Integration Guides | WordPress/Shopify/Wix/Squarespace Snippets | `dashboard-react/src/app/docs/cms/page.tsx` |
| AUDIT-21 | Troubleshooting-FAQ (8 Ursachen) | Checklist-Seite | `dashboard-react/src/app/docs/troubleshooting/page.tsx` |
| AUDIT-22 | Widget < 35KB gzip | Bereits erfüllt: 26KB (cookie_banner) + 15KB (a11y) | Kein Fix nötig — gemessen mit `gzip -c \| wc -c` |
| AUDIT-23 | `npm run test:a11y` Axe-Core | Playwright Spec + npm script | `tests/e2e/axe-accessibility.spec.ts`, `package.json` |

---

## Phase 8: Enterprise & International — COMPLETE

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-24 | Agency Multi-Site Aggregation | `GET /api/cookie-compliance/agency/stats` | `cookie_compliance_routes.py` |
| AUDIT-25 | EU Compliance Ländervergleich | Statische Seite DE/FR/IT/NL/AT | `dashboard-react/src/app/compliance/countries/page.tsx` |
| AUDIT-26 | WCAG 3.0 Readiness Report (APCA) | `GET /api/v2/accessibility/wcag3-readiness/{site_id}` | `accessibility_fix_routes.py` |
| AUDIT-27 | VPAT 2.4 Conformance Report | `GET /api/v2/accessibility/vpat-report/{site_id}` | `accessibility_fix_routes.py` |

---

## Phase 9: Rechtstexte & DSGVO Audit — COMPLETE

### Audit-Ergebnisse

| Problem | Schwere | Status |
|---------|---------|--------|
| `generated_documents` Tabelle fehlte — Dokumente wurden nicht persistiert | CRITICAL | FIXED |
| Kein HTTP-Endpoint für Datenschutzerklärung-Generator (nur Python-Klasse) | HIGH | FIXED |
| Kein HTTP-Endpoint für Impressum-Generator | HIGH | FIXED |
| Kein Stale-Reminder (Dokumente >365 Tage nicht aktualisiert) | HIGH | FIXED |
| Art. 13/14 DSGVO Post-Validation fehlte | HIGH | FIXED |
| Feedback-Endpoint hatte `user_id=None` (nie gesetzt) | MEDIUM | FIXED |

| AUDIT | Beschreibung | Fix | Dateien |
|-------|-------------|-----|---------|
| AUDIT-28a | `generated_documents` Tabelle | CREATE TABLE + Migration | `migrations/create_generated_documents.sql` |
| AUDIT-28b | `POST /api/v1/legal/generate-impressum` | Neuer Endpoint + `_static_impressum()` | `ai_legal_routes.py` |
| AUDIT-28c | `POST /api/v1/legal/generate-datenschutz` | Neuer Endpoint + Art.13-Validator + `_static_datenschutz()` | `ai_legal_routes.py` |
| AUDIT-28d | `GET /api/v1/legal/documents/stale-check` | Stale-Reminder Endpoint | `ai_legal_routes.py` |
| AUDIT-28e | `POST /api/v1/legal/documents/{id}/mark-reviewed` | Manuelles Review-Marking | `ai_legal_routes.py` |
| AUDIT-28f | Art. 13 Validator `_validate_art13_fields()` | 6 Pflichtfelder-Check (Verantwortlicher, Zweck, Rechtsgrundlage, Speicherdauer, Rechte, Beschwerderecht) | `ai_legal_routes.py` |
| AUDIT-28g | Feedback-Endpoint user_id Fix | `Depends(get_current_user_id)` statt `None` | `ai_legal_routes.py` |

---

## BUG-01: Schema-Fix — FIXED

| Problem | Fix |
|---------|-----|
| `cookie_compliance_stats.site_identifier` → `site_id` umbenennen | `ALTER TABLE ... RENAME COLUMN` |
| Fehlende Spalten: `accepted_analytics`, `accepted_marketing`, `accepted_functional`, `updated_at` | `ADD COLUMN IF NOT EXISTS` |
| Falscher CONFLICT-Target `(site_id, date)` | Index neu erstellt |

**Migration:** `backend/migrations/fix_cookie_compliance_stats.sql`

---

## Alle DB-Migrations (2026-05-01)

| Datei | Beschreibung |
|-------|-------------|
| `fix_cookie_compliance_stats.sql` | BUG-01: site_identifier → site_id, neue Spalten |
| `add_action_to_consent_logs.sql` | AUDIT-16: action Spalte (accept/revoke/update) |
| `create_alt_text_review_queue.sql` | AUDIT-15: Alt-Text Review Queue |
| `create_generated_documents.sql` | AUDIT-28: Legal Documents Persistenz |

---

## Bekannte verbleibende Lücken

| # | Problem | Priorität |
|---|---------|-----------|
| 1 | Kein Sidebar-Nav-Link zu `/accessibility/statement`, `/accessibility/review`, `/docs/cms`, `/docs/troubleshooting`, `/agency`, `/compliance/countries` | Niedrig |
| 2 | TCF 2.2 nicht implementiert (€1.575/Jahr IAB-Registrierung) | Business-Entscheidung |
| 3 | APCA Contrast (WCAG 3.0) Automatik-Scanner noch nicht implementiert | Niedrig |
| 4 | `RevocationChart.tsx` im Dashboard noch nicht erstellt | Niedrig |
| 5 | `npm run test:a11y` erfordert laufenden Dashboard-Server (kein Mock) | Niedrig |

---

_Erstellt: 2026-05-01 | Alle 28 Audit-Punkte bearbeitet_
