# Phase 2: Accessibility Statement Generator - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Barrierefreiheitserklärung-Generator vollständig implementiert. Kunden können über das Dashboard eine BFSG-konforme Barrierefreiheitserklärung in 2 Minuten generieren, vorschauen und herunterladen.

Nach BFSG (Barrierefreiheitsstärkungsgesetz) und EU Web Accessibility Directive ist eine Barrierefreiheitserklärung auf der Webseite **gesetzliche Pflicht**. Complyo muss diesen Generator anbieten um als vollständiges Compliance-Tool zu gelten.

Scope:
1. Backend-API: `POST /api/v2/accessibility/generate-statement` — generiert HTML + Markdown-Statement
2. Generator befüllt Statement automatisch aus Scan-Ergebnissen des jeweiligen Sites (WCAG-Level, bekannte Issues)
3. Dashboard UI: Formular → Preview → Download (HTML-Datei + PDF-Export)
4. Statement enthält alle BFSG-Pflichtfelder gemäß § 12 BFSG und EN 301 549

</domain>

<decisions>
## Implementation Decisions

### Backend API (AUDIT-05)
- Neuer Endpoint `POST /api/v2/accessibility/generate-statement` in `accessibility_fix_routes.py`
- Request body: `site_id` + optionale Override-Felder (Kontakt-Email, Datum der Überprüfung)
- Response: `{ "html": "...", "markdown": "...", "filename": "barrierefreiheitserklaerung.html" }`
- Scan-Ergebnisse aus DB laden (letzte Accessibility-Scan-Ergebnisse für die site_id)
- Falls kein Scan vorhanden: "Konformitätsstatus: Nicht bewertet" als Fallback
- Auth-geschützt: `get_current_user_required` (konsistent mit anderen accessibility-Endpoints)

### BFSG-Pflichtfelder
Die generierte Erklärung muss enthalten (§ 12 BFSG + EU-Mustervorlage):
1. **Geltungsbereich** — welche Website / welcher Service
2. **Stand der Vereinbarkeit** — vollständig / teilweise / nicht konform mit EN 301 549 / WCAG 2.1
3. **Nicht barrierefreie Inhalte** — aus Scan-Ergebnissen befüllt (oder "keine bekannt")
4. **Kontakt / Feedback-Mechanismus** — Email-Adresse für Anfragen
5. **Durchsetzungsverfahren** — Verweis auf zuständige Stelle (BFSG § 16: Schlichtungsstelle beim BMAS)
6. **Datum** — der letzten Überprüfung

### Dashboard UI
- Neue Seite/Unterseite in Accessibility-Bereich des Dashboards
- Formular: Kontakt-Email, Datum der Überprüfung, optionale Freitextfelder
- Live-Preview: Statement-Text gerendert in der Seite
- Download-Button: HTML-Datei direkt
- "PDF exportieren": Browser-Print-to-PDF oder jsPDF
- Konsistentes Design mit bestehendem Accessibility-Dashboard

### Statement-Inhalt-Generierung
- Template-basiert: feste Struktur, variable Felder aus DB/Formular
- Sprache: Deutsch (Primärmarkt)
- Format-Variante für EN/HTML: sauber semantisch markiert
- WCAG-Level aus letztem Scan: AA (Zielwert) oder tatsächlicher Wert
- Bekannte Issues: max. 10 aus letztem Scan, priorisiert nach Kritikalität

### Claude's Discretion
- Styling der PDF-Vorlage (ob jsPDF oder window.print())
- Exact DB query für Accessibility-Scan-Ergebnisse (je nach Schema)
- Fehlerhandling wenn keine Scan-Daten vorhanden

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/accessibility_fix_routes.py` — bestehende Accessibility-API, hier neuer Endpoint rein
- `dashboard-react/src/components/accessibility/` — 5 bestehende Accessibility-UI-Komponenten
- `backend/accessibility_patch_generator.py` — Code-Generierungs-Pattern zum Referenzieren
- `dashboard-react/src/app/accessibility/` — bestehende Accessibility-Dashboard-Seite

### Established Patterns
- FastAPI Endpoints: Auth via `get_current_user_required`, DB via `db_pool`
- Dashboard: React-Komponenten in `src/components/`, Pages in `src/app/`
- Download-Pattern: ähnlich wie bestehende `download-bundle` Endpoint

### Integration Points
- Endpoint in `backend/accessibility_fix_routes.py` (neue Route hinzufügen)
- Dashboard: neue Unterseite `src/app/accessibility/statement/page.tsx` oder Abschnitt in bestehender Seite
- DB: `accessibility_fix_packages` oder direkte Scan-Ergebnis-Tabelle abfragen

</code_context>

<specifics>
## Specific Ideas

- Statement-Template als Python f-string oder Jinja2-Template (je was im Projekt schon da ist)
- Download als Response mit `Content-Disposition: attachment` Header
- BMAS Schlichtungsstelle URL: https://www.schlichtungsstelle-bfsg.de/
- EU-Mustervorlage als Referenz: https://ec.europa.eu/info/accessibility-statement-guidelines

</specifics>

<deferred>
## Deferred Ideas

- Mehrsprachige Statements (EN/FR) — Phase 8 Enterprise
- Automatisches jährliches Update-Reminder (Phase 9 / Rechtstexte)
- Statement-Hosting auf Complyo-Subdomain — nice-to-have
- WCAG 2.2 / 3.0 Konformitätsstatus — Phase 4 extended WCAG

</deferred>
