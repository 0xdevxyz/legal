# Complyo — Plan: Weitere Schritte (Phasen 4–9)
_Stand: 2026-05-01 | Basis: AUDIT_STATUS.md + Live-DB-Inspektion_

---

## Aktueller Stand

| Phase | Status | Tests |
|-------|--------|-------|
| Phase 1: Critical Compliance Fixes (AUDIT-01–04) | COMPLETE | 11 Unit-Tests grün |
| Phase 2: Accessibility Statement Generator (AUDIT-05) | COMPLETE | 8 Unit-Tests grün |
| Phase 3: E2E Compliance Test Suite (AUDIT-06–08) | COMPLETE | 32 Tests grün |
| Phase 4–9 | AUSSTEHEND | — |

---

## Bekannter Bug: Muss zuerst behoben werden

### BUG-01 — `cookie_compliance_stats` Schema-Mismatch (BLOCKER für Phase 6)
**Problem:** Die Live-DB hat `site_identifier` (varchar) statt `site_id`, und es fehlen die Spalten
`accepted_analytics`, `accepted_marketing`, `accepted_functional`. Der `log_consent`-Endpoint wirft
eine 500 wenn die DB verbunden ist (mocked in Tests).
**Fix:** SQL-Migration + Query in `cookie_compliance_routes.py` anpassen.
**Priorität:** VOR Phase 6 (Revocation Analytics) — sonst keine echten Stats möglich.

---

## Phase 4: Mobile & Extended WCAG Checks
**Ziel:** Scanner erkennt Mobile-Accessibility-Issues und deckt WCAG AAA + Tabellen/SVG/Video/PDF ab
**Abhängigkeit:** Phase 3 abgeschlossen ✓
**Audit-IDs:** AUDIT-09, AUDIT-10, AUDIT-11, AUDIT-12, AUDIT-13
**Aufwand:** ~3 Stunden

### Geplante Änderungen

#### AUDIT-09 — Touch-Target-Checker (44×44px, WCAG 2.5.5)
- **Was:** Scanner-Regel die interaktive Elemente (`<button>`, `<a>`, `<input>`) auf min. 44×44px prüft
- **Wo:** `backend/accessibility_scanner.py` oder äquivalente Scanner-Datei — neue Regel hinzufügen
- **Test:** Neuer pytest-Test: Element mit 30×30px → Verstoß gemeldet; 44×44px → kein Verstoß

#### AUDIT-10 — WCAG AAA Checks
- **Was:** 3 neue Scanner-Regeln: Kontrast 7:1 (1.4.6), Link-Purpose (2.4.9), Visual Presentation (1.4.8)
- **Wo:** Scanner-Modul, neue Regel-Kategorie `wcag_aaa`
- **Test:** Low-Contrast-Element → Verstoß; descriptive link text → kein Verstoß

#### AUDIT-11 — Tabellen / SVG / Canvas Accessibility
- **Was:** `<th>` ohne `scope`, `<table>` ohne `<caption>` → Verstoß; `<svg>` ohne `<title>` + `role="img"` → Verstoß; `<canvas>` ohne `aria-label` → Verstoß
- **Wo:** Scanner-Modul, bestehende Regel-Liste erweitern
- **Test:** HTML-Fixtures mit und ohne Attribute

#### AUDIT-12 — Video Caption Checker
- **Was:** `<video>` ohne `<track kind="captions">` + `srclang` → Verstoß
- **Wo:** Scanner-Modul
- **Test:** Video-Element ohne Track → Warnung

#### AUDIT-13 — PDF-Link Hinweis
- **Was:** `<a href="*.pdf">` oder `<a>` mit "PDF" im Text → Hinweis "PDF-Accessibility manuell prüfen"
- **Wo:** Scanner-Modul, neue Regel vom Typ `info` (nicht `error`)
- **Test:** Link mit `.pdf`-Endung → Info-Meldung

**Deliverables:**
- `backend/accessibility_scanner.py` (oder äquivalent) — 5 neue Regeln
- `backend/tests/test_wcag_extended.py` — ~15 Tests

---

## Phase 5: Dashboard ATAG Compliance
**Ziel:** Dashboard selbst WCAG 2.1 AA konform + Alt-Text-Review-Workflow
**Abhängigkeit:** Phase 4
**Audit-IDs:** AUDIT-14, AUDIT-15
**Aufwand:** ~4 Stunden

### Geplante Änderungen

#### AUDIT-14 — Focus-Indikatoren
- **Was:** Alle Buttons, Links, Inputs im Dashboard mit sichtbaren Focus-Indikatoren (CSS: `outline ≥ 2px, Kontrast ≥ 3:1`)
- **Wo:** `dashboard-react/src/styles/globals.css` oder Tailwind-Config — globale Focus-Styles
- **Methode:** `focus-visible:ring-2 focus-visible:ring-blue-500` Tailwind-Klasse auf alle interaktiven Elemente, oder globales CSS `:focus-visible { outline: 2px solid #3b82f6; outline-offset: 2px; }`
- **Test:** Playwright `page.keyboard.press('Tab')` durch alle Hauptseiten → `focusedElement` hat sichtbaren Outline

#### AUDIT-15 — Alt-Text Review Queue
- **Was:** KI-generierte Alt-Texte landen in "Pending Review" Queue statt direkt in Produktion
- **Wo:**
  - `backend/accessibility_fix_routes.py` — neues Feld `alt_text_status` (pending/approved) im Response
  - `dashboard-react/src/components/accessibility/` — neue `AltTextReviewQueue.tsx` Komponente
  - `dashboard-react/src/app/accessibility/review/page.tsx` — neue Review-Seite
- **Test:** Mock-AI generiert Alt-Text → landet in `pending` Queue; nach Approve → `approved` Status

**Deliverables:**
- `dashboard-react/src/styles/` — globale Focus-Styles
- `backend/accessibility_fix_routes.py` — alt_text_status Feld
- `dashboard-react/src/components/accessibility/AltTextReviewQueue.tsx` — neu
- `dashboard-react/src/app/accessibility/review/page.tsx` — neu
- `backend/tests/test_alt_text_review.py` — ~6 Tests

---

## Phase 6: Advanced Cookie Features
**Ziel:** Revocation-Tracking, Per-Service Consent, DPA-Generator, Rate-Limiting
**Abhängigkeit:** Phase 5 + BUG-01 Schema-Fix
**Audit-IDs:** AUDIT-16, AUDIT-17, AUDIT-18, AUDIT-19
**Aufwand:** ~5 Stunden

### Voraussetzung: BUG-01 Schema-Fix
Vor Phase 6 muss `cookie_compliance_stats` migriert werden:
```sql
-- Migration: fix_cookie_compliance_stats.sql
ALTER TABLE cookie_compliance_stats RENAME COLUMN site_identifier TO site_id;
ALTER TABLE cookie_compliance_stats ADD COLUMN IF NOT EXISTS accepted_analytics INTEGER DEFAULT 0;
ALTER TABLE cookie_compliance_stats ADD COLUMN IF NOT EXISTS accepted_marketing INTEGER DEFAULT 0;
ALTER TABLE cookie_compliance_stats ADD COLUMN IF NOT EXISTS accepted_functional INTEGER DEFAULT 0;
```
Und in `cookie_compliance_routes.py` den Stats-Upsert entsprechend anpassen.

### Geplante Änderungen

#### AUDIT-16 — Consent Revocation Event
- **Was:** Neuer Endpoint `POST /api/cookie-compliance/revoke` oder `action="revoke"` im bestehenden Endpoint
- **Wo:** `backend/cookie_compliance_routes.py` — neuer Endpoint oder erweitertes `ConsentLog` Modell mit `action` Feld
- **DB:** `cookie_consent_logs` Tabelle — neues Feld `action` (accept/revoke/update)
- **Test:** Revoke-Request → `action="revoke"` in DB gespeichert

#### AUDIT-17 — Revocation-Rate Dashboard Chart
- **Was:** Dashboard-Chart: Acceptance vs. Revocation Rate über Zeit
- **Wo:**
  - `backend/cookie_compliance_routes.py` — erweiterter Stats-Endpoint liefert revocation_rate
  - `dashboard-react/src/components/cookie-compliance/` — neues Chart-Widget (Recharts oder bestehende Chart-Lib)
- **Test:** Stats-Endpoint liefert `revocation_rate: 0.0` wenn keine Revocations

#### AUDIT-18 — Per-Service Consent Tracking
- **Was:** Consent-Log speichert per-Service statt nur Kategorien: `{"ga4": true, "fbpixel": false}`
- **Wo:** `ConsentLog` Modell hat bereits `services_accepted` Feld — in DB-Insert aktivieren
- **DB:** `cookie_consent_logs.services_accepted` Feld nutzen (falls vorhanden, sonst anlegen)
- **Test:** Request mit `services_accepted: ["ga4"]` → in DB gespeichert

#### AUDIT-19 — DPA-Generator (Auftragsverarbeitungsvertrag)
- **Was:** `POST /api/v2/legal/generate-dpa` → DOCX/PDF Vorlage
- **Wo:** Neuer Route-File `backend/legal_document_routes.py` oder Erweiterung von `ai_legal_routes.py`
- **Lib:** `python-docx` (bereits in requirements? prüfen) oder Jinja2 → HTML → weasyprint
- **Test:** Request mit Pflichtfeldern → Response enthält Download-URL oder Base64-Dokument

**Deliverables:**
- `backend/db/fix_cookie_compliance_stats.sql` — Migration
- `backend/cookie_compliance_routes.py` — Revoke-Endpoint + Stats-Erweiterung
- `backend/legal_document_routes.py` — DPA-Generator (neu oder erweitert)
- `dashboard-react/src/components/cookie-compliance/RevocationChart.tsx` — neu
- `backend/tests/test_revocation.py` — ~8 Tests
- `backend/tests/test_dpa_generator.py` — ~5 Tests

---

## Phase 7: CMS Docs & Widget Performance
**Ziel:** CMS-Guides, Troubleshooting-FAQ, Widget <35KB, Axe-Core Tests
**Abhängigkeit:** Phase 6
**Audit-IDs:** AUDIT-20, AUDIT-21, AUDIT-22, AUDIT-23
**Aufwand:** ~3 Stunden

### Geplante Änderungen

#### AUDIT-20 — CMS-Guides
- **Was:** Dashboard-Seite mit Copy-Paste Snippets für WordPress, Shopify, Wix, Squarespace
- **Wo:** `dashboard-react/src/app/docs/cms/page.tsx` + Komponenten

#### AUDIT-21 — Troubleshooting-FAQ
- **Was:** "Banner nicht sichtbar?" Checklist mit 8 häufigen Ursachen
- **Wo:** `dashboard-react/src/app/docs/troubleshooting/page.tsx`

#### AUDIT-22 — Widget Performance (<35KB gzip)
- **Was:** `cookie_banner_v2.js` und `accessibility-v6.js` auf unter 35KB gzip komprimieren
- **Aktuell:** ~40–50KB
- **Methode:** Dead code elimination (TCF-Stub entfernen, ungenutzte Features), dann `gzip` messen
- **Tool:** `gzip -c cookie_banner_v2.js | wc -c`

#### AUDIT-23 — Axe-Core Tests (`npm run test:a11y`)
- **Was:** Axe-Core-Tests gegen Dashboard-Hauptseiten
- **Wo:** `dashboard-react/tests/e2e/axe-accessibility.spec.ts` + npm script in `package.json`
- **Lib:** `@axe-core/playwright` (bereits recherchiert, Version 4.11.3)

**Deliverables:**
- `dashboard-react/src/app/docs/cms/page.tsx` — neu
- `dashboard-react/src/app/docs/troubleshooting/page.tsx` — neu
- `dashboard-react/tests/e2e/axe-accessibility.spec.ts` — neu
- `dashboard-react/package.json` — `test:a11y` npm script

---

## Phase 8: Enterprise & International
**Ziel:** Multi-Site Aggregation, EU-Ländervergleich, WCAG 3.0 Readiness, VPAT
**Abhängigkeit:** Phase 7
**Audit-IDs:** AUDIT-24, AUDIT-25, AUDIT-26, AUDIT-27
**Aufwand:** ~5 Stunden

### Geplante Änderungen

#### AUDIT-24 — Agency-Dashboard Multi-Site Aggregation
- **Was:** Aggregierte Consent-Statistiken über alle verwalteten Sites
- **Wo:** `backend/cookie_compliance_routes.py` — neuer Endpoint `GET /api/cookie-compliance/agency/stats`
- **Dashboard:** `dashboard-react/src/app/agency/page.tsx`

#### AUDIT-25 — EU-Compliance Ländervergleich
- **Was:** Tab mit DE/AT/CH (DSGVO+TTDSG), FR (CNIL), IT (Garante), NL (AP)
- **Wo:** `dashboard-react/src/app/compliance/countries/page.tsx`
- **Inhalt:** Statische, redaktionell gepflegte Daten (kein API-Call nötig)

#### AUDIT-26 — WCAG 3.0 Readiness Report
- **Was:** Scanner-Report: WCAG 3.0 APCA Contrast-Änderungen und neue Kriterien
- **Wo:** `backend/accessibility_fix_routes.py` — neuer Endpoint `GET /api/v2/accessibility/wcag3-readiness/{site_id}`

#### AUDIT-27 — VPAT 2.4 Conformance Report
- **Was:** `GET /api/v2/accessibility/vpat-report/{site_id}` → Markdown-Dokument
- **Wo:** `backend/accessibility_fix_routes.py` — neuer Endpoint, Jinja2-Template

**Deliverables:**
- `backend/accessibility_fix_routes.py` — 2 neue Endpoints (WCAG 3.0, VPAT)
- `backend/cookie_compliance_routes.py` — Agency-Stats-Endpoint
- `dashboard-react/src/app/agency/page.tsx` — neu
- `dashboard-react/src/app/compliance/countries/page.tsx` — neu
- `backend/tests/test_enterprise.py` — ~8 Tests

---

## Phase 9: Rechtstexte & DSGVO Audit
**Ziel:** Vollständiger Audit + Implementierung Rechtstexte-Modul + DSGVO Art. 13/14 Compliance
**Abhängigkeit:** Phase 8
**Audit-IDs:** AUDIT-28
**Aufwand:** ~6 Stunden (größte Phase — vollständiger Audit + Implementierung)

### Geplante Analyse

#### Schritt 1: Audit des bestehenden Rechtstexte-Moduls
Zu prüfende Dateien:
- `backend/ai_legal_routes.py` — Datenschutzerklärung, Impressum, AGB, Cookie-Richtlinie Generator
- `backend/legal_document_routes.py` — falls vorhanden
- `dashboard-react/src/app/legal/` — Dashboard-Seiten
- Bestehende Jinja2-/AI-Templates

Prüfpunkte:
- Art. 13 DSGVO: Alle Pflichtangaben in generierter Datenschutzerklärung?
- Art. 14 DSGVO: Informationen bei indirekter Erhebung?
- § 5 TMG Impressum: Alle Pflichtfelder (Name, Anschrift, Kontakt, USt-ID)?
- Stale-Detection: Datum der letzten Aktualisierung gespeichert?
- AGB: Widerrufsrecht, Haftungsausschluss vorhanden?

#### Schritt 2: Gap-Implementierung
Basierend auf Audit-Ergebnis — typisch erwartete Gaps:
- **Stale-Reminder:** Automatischer Hinweis wenn Datenschutzerklärung >365 Tage nicht aktualisiert
  - `backend/legal_document_routes.py` — Endpoint prüft `last_updated` Datum
  - Dashboard-Banner: "Ihre Datenschutzerklärung wurde zuletzt am [Datum] aktualisiert — Überprüfung empfohlen"
- **Art. 13 Checkliste:** Validator der generierte Datenschutzerklärungen gegen alle Pflichtfelder prüft
- **Cookie-Richtlinie:** Automatisch aus Consent-Log-Daten befüllen (welche Services tatsächlich genutzt)

**Deliverables (nach Audit bekannt):**
- `data/PHASE9_AUDIT_REPORT.md` — vollständiger Audit-Bericht Rechtstexte
- Implementierungen basierend auf Audit-Findings
- `backend/tests/test_rechtstexte.py` — Tests für alle neuen/geänderten Endpoints

---

## Empfohlene Ausführungsreihenfolge

```
BUG-01 Fix (10 min)
    ↓
Phase 4: Mobile/WCAG Extended (3h)
    ↓
Phase 5: Dashboard ATAG (4h)
    ↓
Phase 6: Advanced Cookie (5h)  ← requires BUG-01 fix
    ↓
Phase 7: CMS Docs + Performance (3h)
    ↓
Phase 8: Enterprise (5h)
    ↓
Phase 9: Rechtstexte + DSGVO (6h)  ← User-Originalauftrag: "gleicher Test für Rechtstexte und DSGVO"
```

**Gesamtaufwand:** ~31 Stunden (ohne Pausen, inkl. TDD und Verifikation je Phase)

---

## Priorisierung nach Business-Impact

| Priorität | Phase / Bug | Grund |
|-----------|-------------|-------|
| **KRITISCH** | BUG-01: Schema-Fix | Verhindert echte Consent-Stats in Produktion |
| **HOCH** | Phase 6: Revocation-Tracking (AUDIT-16/17) | Rechtlich relevant — DSGVO Art. 7 Abs. 3 Widerruf |
| **HOCH** | Phase 9: Rechtstexte + DSGVO | User-Originalauftrag; höchstes rechtliches Risiko |
| **MITTEL** | Phase 4: WCAG Extended | Verbessert Produkt-Tiefe, wenig akutes Risiko |
| **MITTEL** | Phase 5: Dashboard ATAG | BFSG gilt auch für das eigene Dashboard |
| **MITTEL** | Phase 6: DPA-Generator (AUDIT-19) | Kundenwert hoch, aber kein Compliance-Risiko |
| **NIEDRIG** | Phase 7: CMS Guides | Nice-to-have, kein Compliance-Gap |
| **NIEDRIG** | Phase 8: Enterprise | Für Agency-Kunden, kein akutes Problem |

---

## Offene Lücken (nicht in Phasen abgedeckt)

| # | Problem | Wo | Empfehlung |
|---|---------|-----|------------|
| 1 | Kein Sidebar-Nav-Link zu `/accessibility/statement` | Dashboard Navigation | In Phase 5 (Dashboard ATAG) mitbeheben |
| 2 | `widget_routes.py` generate-patches ohne Auth (user_id=1 hardcoded) | REQUIREMENTS.md AUTH-11 | In Phase 5 oder 6 beheben |
| 3 | Cookie-Settings-Modal nicht implementiert (TODO in cookie_consent.js) | REQUIREMENTS.md FEAT-02 | In Phase 6 (Advanced Cookie) |
| 4 | `_check_upsell_opportunity` enthält nur `pass` | REQUIREMENTS.md DB-02 | Nice-to-have, Phase 7 oder 8 |

---

_Erstellt: 2026-05-01 | Basis: AUDIT_STATUS.md, STATE.md, ROADMAP.md, Live-DB-Inspektion_
