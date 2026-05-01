# Roadmap: Complyo Feature Completeness — Cookie, BFSG & Rechtstexte

## Overview

Dieser Milestone bringt Complyo zur Produktionsreife in den drei Kernbereichen Cookie-Banner, Barrierefreiheitsgesetz (BFSG/WCAG) und Rechtstexte/DSGVO. Basis ist der vollständige Audit-Bericht vom 2026-04-30. Alle 24 Audit-Items werden systematisch abgearbeitet, gefolgt von einer Analyse und Implementierung der Rechtstexte- und DSGVO-Features.

## Previous Milestone

- [x] **v1.0: Technical Debt & Feature Completeness** — Auth, DB-Persistenz, Email, Cookie-Modal (2026-04-21)

## Phases

- [x] **Phase 1: Critical Compliance Fixes** — BFSG-Disclaimer, TCF 2.2 deaktivieren, PII-Logging, STS-Header (completed 2026-05-01)
- [ ] **Phase 2: Accessibility Statement Generator** — BFSG-Pflicht: Barrierefreiheitserklärung-Generator
- [ ] **Phase 3: E2E Compliance Test Suite** — Cookie-Flow E2E, Accessibility-Regression, DSGVO §25 Tests
- [ ] **Phase 4: Mobile & Extended WCAG Checks** — Touch-Targets, WCAG AAA, Tabellen/SVG/Canvas, PDF, Video
- [ ] **Phase 5: Dashboard ATAG Compliance** — Dashboard selbst WCAG-konform, ARIA, Alt-Text Review-Workflow
- [ ] **Phase 6: Advanced Cookie Features** — Revocation-Analytics, Per-Service Tracking, DPA-Generator, Rate-Limiting
- [ ] **Phase 7: CMS Docs & Widget Performance** — CMS-Guides, Troubleshooting, Widget <35KB, Axe/Pa11y
- [ ] **Phase 8: Enterprise & International** — Multi-Site Aggregation, EU-Ländervergleich, WCAG 3.0, VPAT
- [ ] **Phase 9: Rechtstexte & DSGVO Audit** — Analyse und Implementierung Rechtstexte + DSGVO-Features

## Phase Details

### Phase 1: Critical Compliance Fixes
**Goal**: Alle kritischen Compliance-Risiken eliminiert: BFSG-Deadline klar kommuniziert, TCF 2.2 Stub aus Produktion entfernt, PII aus Logs bereinigt, HTTPS-Security-Header gesetzt
**Depends on**: Nothing (first phase)
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04
**Success Criteria** (what must be TRUE):
  1. Landing Page zeigt klaren Disclaimer: "BFSG-Deadline war 28.06.2025 — Complyo bietet Forward-Looking-Compliance"
  2. TCF 2.2 in Cookie-Banner-Dashboard als "Coming Soon" markiert, __tcfapi Stub wirft keine false-positive Signale
  3. User-Agent in Consent-Logs wird auf Browser-Familie + Version gekürzt (kein full UA-String)
  4. `Strict-Transport-Security` Header in nginx-Config für api.complyo.de dokumentiert und aktiv

### Phase 2: Accessibility Statement Generator
**Goal**: Barrierefreiheitserklärung-Generator vollständig implementiert — Kunden können BFSG-konforme Erklärung in 2 Minuten generieren und herunterladen
**Depends on**: Phase 1
**Requirements**: AUDIT-05
**Success Criteria** (what must be TRUE):
  1. Backend-Endpoint `POST /api/v2/accessibility/generate-statement` generiert HTML + Markdown Barrierefreiheitserklärung
  2. Generator nutzt Scan-Ergebnisse des jeweiligen Sites um WCAG-Level und bekannte Issues zu befüllen
  3. Dashboard zeigt Generator-UI: Formular → Preview → Download (HTML + PDF-Export)
  4. Generierte Erklärung enthält alle BFSG-Pflichtfelder: Geltungsbereich, Konformitätsstatus, Kontakt, Feedback-Mechanismus, Durchsetzungsverfahren

### Phase 3: E2E Compliance Test Suite
**Goal**: Automatisierte Tests verifizieren dass Cookie-Banner und Accessibility-Widget korrekt funktionieren und DSGVO §25 TTDSG erfüllen
**Depends on**: Phase 1
**Requirements**: AUDIT-06, AUDIT-07, AUDIT-08
**Success Criteria** (what must be TRUE):
  1. E2E-Test: Banner erscheint → User klickt "Nur Notwendige" → Consent in DB gespeichert → Analytics-Scripts geblockt
  2. E2E-Test: User klickt "Alle akzeptieren" → alle 4 Kategorien in Consent-Log → GTM dataLayer.push korrekt
  3. E2E-Test: Accessibility-Widget lädt → Toggle aktiviert → CSS-Klasse auf body → localStorage persistiert
  4. Compliance-Validation-Test: verifiziert DSGVO §25 TTDSG — kein Tracking vor Einwilligung

### Phase 4: Mobile & Extended WCAG Checks
**Goal**: Scanner erkennt Mobile-Accessibility-Issues und deckt WCAG AAA sowie Tabellen-, SVG-, Canvas-, Video- und PDF-Accessibility ab
**Depends on**: Phase 3
**Requirements**: AUDIT-09, AUDIT-10, AUDIT-11, AUDIT-12, AUDIT-13
**Success Criteria** (what must be TRUE):
  1. Scanner prüft Touch-Target-Größen (min 44x44px nach WCAG 2.5.5) und meldet Verstöße
  2. WCAG AAA Checks implementiert: 1.4.6 Contrast Enhanced (7:1), 2.4.9 Link Purpose, 1.4.8 Visual Presentation
  3. Tabellen: `<th scope>` und `<caption>` Validierung; SVG: `<title>` + `role="img"` Check; Canvas: aria-label Check
  4. Video-Checker prüft `<track kind="captions">` auf Vorhandensein UND `srclang` Attribut
  5. PDF-Scan: erkennt PDF-Links auf Seite und gibt Hinweis dass PDF-Accessibility manuell geprüft werden muss

### Phase 5: Dashboard ATAG Compliance
**Goal**: Das Complyo-Dashboard selbst ist WCAG 2.1 AA konform — alle interaktiven Elemente sind per Tastatur erreichbar und Screen-Reader-kompatibel; Alt-Text-Review-Workflow verhindert ungeprüfte AI-Texte in Produktion
**Depends on**: Phase 4
**Requirements**: AUDIT-14, AUDIT-15
**Success Criteria** (what must be TRUE):
  1. Alle Buttons, Links, Inputs im Dashboard haben sichtbare Focus-Indikatoren (outline ≥ 2px, contrast ≥ 3:1)
  2. Navigation per Tab/Shift+Tab durch gesamtes Dashboard möglich ohne Maus
  3. Alle Bilder und Icons im Dashboard haben aria-label oder alt-Text
  4. Alt-Text-Review-Queue im Dashboard: KI-generierte Alt-Texte landen in "Pending Review" — erst nach manueller Freigabe deployed

### Phase 6: Advanced Cookie Features
**Goal**: Consent-Revocation wird getrackt und ausgewertet; Per-Service Consent-Tracking aktiv; DPA-Generator für Kunden verfügbar; API-Rate-Limiting schützt vor Abuse
**Depends on**: Phase 5
**Requirements**: AUDIT-16, AUDIT-17, AUDIT-18, AUDIT-19
**Success Criteria** (what must be TRUE):
  1. Wenn User Einwilligung widerruft: Revocation-Event in `cookie_consent_logs` mit `action="revoke"` gespeichert
  2. Dashboard zeigt Revocation-Rate über Zeit (Chart: Acceptance vs. Revocation)
  3. Consent-Log speichert per-Service-Einwilligung (z.B. `{"ga4": true, "fbpixel": false}`) statt nur Kategorien
  4. `POST /api/v2/legal/generate-dpa` generiert DPA-Vorlage (Auftragsverarbeitungsvertrag) als DOCX/PDF
  5. Rate-Limiting: max 100 Consent-Logs/Minute pro Site-ID (Sliding Window)

### Phase 7: CMS Docs & Widget Performance
**Goal**: CMS-spezifische Deploymentguides, Troubleshooting-FAQ und Performance-optimiertes Widget (<35KB gzip) sowie Axe/Pa11y Integration als Regressions-Suite
**Depends on**: Phase 6
**Requirements**: AUDIT-20, AUDIT-21, AUDIT-22, AUDIT-23
**Success Criteria** (what must be TRUE):
  1. Docs-Seite im Dashboard enthält Guides für: WordPress (Plugin + manuell), Shopify, Wix, Squarespace mit Copy-Paste-Snippets
  2. Troubleshooting-Seite: "Banner nicht sichtbar?" Checklist mit 8 häufigen Ursachen
  3. `cookie_banner_v2.js` + `accessibility-v6.js` gzip-komprimiert jeweils <35KB (aktuell 40-50KB)
  4. `npm run test:a11y` führt Axe-Core-Tests gegen Dashboard-Hauptseiten aus und schlägt fehl bei WCAG-Violations

### Phase 8: Enterprise & International
**Goal**: Multi-Site Consent-Aggregation, EU-Ländervergleich-Tool, WCAG 3.0 Readiness Assessment und VPAT/ACR Generator für Enterprise-Kunden
**Depends on**: Phase 7
**Requirements**: AUDIT-24, AUDIT-25, AUDIT-26, AUDIT-27
**Success Criteria** (what must be TRUE):
  1. Agency-Dashboard zeigt aggregierte Consent-Statistiken über alle verwalteten Sites (Gesamt-Acceptance-Rate)
  2. Neuer Tab "EU-Compliance" zeigt Ländervergleich: DE/AT/CH (DSGVO+TTDSG), FR (CNIL), IT (Garante), NL (AP) — mit je 3-5 Besonderheiten
  3. Scanner generiert WCAG 3.0 Readiness Report: listet WCAG 3.0 APCA Contrast-Änderungen und neue Kriterien
  4. `GET /api/v2/accessibility/vpat-report/{site_id}` generiert VPAT 2.4 Rev 508/WCAG Conformance Report als Markdown

### Phase 9: Rechtstexte & DSGVO Audit
**Goal**: Vollständige Analyse des Rechtstexte- und DSGVO-Compliance-Moduls; alle gefundenen Gaps implementiert; Datenschutzerklärung-Generator, Cookie-Richtlinie und Impressum vollständig und rechtssicher
**Depends on**: Phase 8
**Requirements**: AUDIT-28
**Success Criteria** (what must be TRUE):
  1. Audit-Bericht erstellt: Vollständige Feature-Matrix für Rechtstexte (Datenschutzerklärung, Impressum, AGB, Cookie-Richtlinie)
  2. Alle kritischen und hohen Gaps aus dem Audit implementiert
  3. DSGVO-Compliance-Checkliste (Art. 13/14 Informationspflichten) verifiziert gegen generierte Datenschutzerklärungen
  4. Automatischer Hinweis wenn Datenschutzerklärung >365 Tage nicht aktualisiert wurde

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Critical Compliance Fixes | 2/2 | Complete    | 2026-05-01 |
| 2. Accessibility Statement Generator | 0/0 | Not Started | - |
| 3. E2E Compliance Test Suite | 0/0 | Not Started | - |
| 4. Mobile & Extended WCAG Checks | 0/0 | Not Started | - |
| 5. Dashboard ATAG Compliance | 0/0 | Not Started | - |
| 6. Advanced Cookie Features | 0/0 | Not Started | - |
| 7. CMS Docs & Widget Performance | 0/0 | Not Started | - |
| 8. Enterprise & International | 0/0 | Not Started | - |
| 9. Rechtstexte & DSGVO Audit | 0/0 | Not Started | - |
