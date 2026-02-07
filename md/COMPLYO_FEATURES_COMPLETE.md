# 🚀 Complyo – Vollständige Feature-Übersicht
## Alle implementierten Features auf einen Blick

**Stand:** 23. November 2025  
**Version:** 2.0  
**Status:** Production-Ready ✅

---

## 📋 Inhaltsverzeichnis

1. [Kern-Features](#1-kern-features)
2. [Website Scanner & Analyse](#2-website-scanner--analyse)
3. [KI-Fix Generator & Code-Ausgabe](#3-ki-fix-generator--code-ausgabe)
4. [Fix-Anwendung & Deployment](#4-fix-anwendung--deployment)
5. [Rechtssicherheit & Haftung](#5-rechtssicherheit--haftung)
6. [Integrationen](#6-integrationen)
7. [Dashboard & UX](#7-dashboard--ux)
8. [Backend-Architektur](#8-backend-architektur)
9. [Barrierefreiheit (WCAG 2.1)](#9-barrierefreiheit-wcag-21)
10. [DSGVO & Datenschutz](#10-dsgvo--datenschutz)
11. [Cookie-Compliance (TTDSG)](#11-cookie-compliance-ttdsg)
12. [Premium-Features](#12-premium-features)
13. [Monitoring & Analytics](#13-monitoring--analytics)
14. [API & Webhooks](#14-api--webhooks)

---

## 1. Kern-Features

### 1.1 Website-Scanner
- **HTML-Extraktion:** Vollständiger DOM-Tree-Parser
- **CSS-Analyse:** Inline, External & Embedded Styles
- **JavaScript-Erkennung:** Tracking-Skripte & Third-Party-Libraries
- **Screenshot-Capture:** Playwright-basiert für visuelle Analyse
- **Performance-Scan:** Lighthouse-ähnliche Metriken

### 1.2 Compliance-Analyse (4 Säulen)
1. **Barrierefreiheit (WCAG 2.1 Level AA)**
   - Alt-Text-Prüfung
   - Kontrast-Analyse
   - ARIA-Validierung
   - Keyboard-Navigation
   - Focus-Indikatoren
   
2. **Datenschutz (DSGVO)**
   - Impressum-Check
   - Datenschutzerklärung-Validierung
   - Cookie-Banner-Prüfung
   - SSL/TLS-Verschlüsselung
   
3. **Cookie-Compliance (TTDSG §25)**
   - Cookie-Scanner
   - Consent-Management-Prüfung
   - Third-Party-Tracking-Erkennung
   
4. **Rechtstexte (TMG)**
   - Impressum §5 TMG
   - Widerrufsbelehrung
   - AGB-Struktur

### 1.3 Compliance-Score
- **0-100 Punkte-System**
- **Gewichtung nach Kritikalität:**
  - Barrierefreiheit: 30%
  - Datenschutz: 30%
  - Cookies: 25%
  - Rechtstexte: 15%
- **Score-History:** Tracking über Zeit
- **Branchen-Benchmark:** Vergleich mit ähnlichen Websites

---

## 2. Website Scanner & Analyse

### 2.1 Deep Content Analyzer
**Datei:** `backend/compliance_engine/checks/deep_content_analyzer.py`

- **Multi-Layer-Parsing:**
  - HTML-Semantik
  - JSON-LD Structured Data
  - OpenGraph Meta-Tags
  - Schema.org Markup
  
- **Content-Extraction:**
  - Headings (H1-H6)
  - Links & Navigation
  - Forms & Input-Fields
  - Images & Media
  - Scripts & Iframes

### 2.2 ARIA Checker
**Datei:** `backend/compliance_engine/checks/aria_checker.py`

- **ARIA-Rollen-Validierung**
- **ARIA-Properties-Check** (aria-label, aria-describedby, etc.)
- **ARIA-States-Monitoring** (aria-expanded, aria-hidden, etc.)
- **Accessibility-Tree-Generierung**

### 2.3 Cookie Analyzer
**Datei:** `backend/compliance_engine/cookie_analyzer.py`

- **Cookie-Typen-Klassifizierung:**
  - Notwendig
  - Funktional
  - Analytisch
  - Marketing
  
- **Third-Party-Cookie-Erkennung**
- **Cookie-Lifetime-Analyse**
- **TTDSG-Compliance-Check**

### 2.4 Barrierefreiheit-Check
**Datei:** `backend/compliance_engine/checks/barrierefreiheit_check.py`

- **Alt-Text-Analyse:**
  - Fehlende Alt-Texte erkennen
  - Generische Alt-Texte ("image", "photo") flaggen
  - AI-Vorschläge für Alt-Texte
  
- **Kontrast-Ratio-Prüfung:**
  - Text/Background-Kontraste
  - WCAG AA: 4.5:1 für Normal-Text
  - WCAG AA: 3:1 für Large-Text
  
- **Focus-Indicator-Check:**
  - Sichtbare Focus-Styles
  - Keyboard-Navigation-Pfad

### 2.5 Impressum & Datenschutz-Check
**Dateien:**
- `backend/compliance_engine/checks/impressum_check.py`
- `backend/compliance_engine/checks/datenschutz_check.py`

- **Impressum §5 TMG:**
  - Name/Firma
  - Anschrift
  - Kontaktdaten
  - Vertretungsberechtigte
  - Register-Nummer
  
- **Datenschutzerklärung DSGVO:**
  - Verantwortlicher
  - Zwecke der Verarbeitung
  - Rechtsgrundlagen
  - Betroffenenrechte
  - Speicherdauer

---

## 3. KI-Fix Generator & Code-Ausgabe

### 3.1 Unified Fix Engine
**Datei:** `backend/ai_fix_engine/unified_fix_engine.py`

- **Multi-Format-Output:**
  - Code-Snippets (HTML/CSS/JS)
  - Text-Vorlagen
  - Step-by-Step-Guides
  - Widget-Einbindungen

### 3.2 Fix-Typen

#### 3.2.1 Code-Fixes
**Handler:** `backend/ai_fix_engine/handlers/accessibility_handler.py`

- **HTML-Fixes:**
  - Alt-Text-Injection
  - ARIA-Label-Ergänzung
  - Semantic HTML-Verbesserungen
  - Skip-Links
  
- **CSS-Fixes:**
  - Kontrast-Verbesserungen
  - Focus-Indikatoren
  - Reduced-Motion-Support
  - Print-Styles
  
- **JavaScript-Fixes:**
  - Keyboard-Event-Handler
  - Screen-Reader-Announcements
  - Dynamic Content-Updates

#### 3.2.2 Text-Fixes
**Handler:** `backend/ai_fix_engine/handlers/legal_text_handler.py`

- **Rechtstexte:**
  - Impressum (TMG §5)
  - Datenschutzerklärung (DSGVO)
  - AGB
  - Widerrufsbelehrung
  - Cookie-Richtlinie
  
- **eRecht24-Integration:**
  - Abmahnsichere Texte
  - Automatische Updates
  - API-Synchronisation

#### 3.2.3 Guide-Fixes
**Handler:** `backend/ai_fix_engine/handlers/guide_handler.py`

- **Schritt-für-Schritt-Anleitungen:**
  - WordPress-Guides
  - Shopify-Guides
  - Custom-CMS-Guides
  - HTML/CSS-Tutorials
  
- **Schwierigkeitsgrade:**
  - Anfänger
  - Fortgeschritten
  - Experte

#### 3.2.4 Widget-Fixes
**Handler:** `backend/ai_fix_engine/handlers/cookie_handler.py`

- **Complyo Accessibility Widget:**
  - Runtime-Fixes für Alt-Texte
  - Kontrast-Anpassungen (User-gesteuert)
  - Font-Size-Control
  - Screen-Reader-Optimierungen

### 3.3 Code-Package-Generator
**Datei:** `backend/compliance_engine/code_package_generator.py`

- **Framework-Support:**
  - Pure HTML/CSS/JS
  - React/Next.js
  - Vue.js/Nuxt
  - Angular
  - WordPress
  - Shopify
  
- **Export-Formate:**
  - ZIP-Archiv
  - GitHub Gist
  - CodeSandbox-Link
  - NPM Package (für Frameworks)

### 3.4 Accessibility Patch Generator
**Datei:** `backend/accessibility_patch_generator.py`

- **Hybrid-Modell:** Widget + Permanente Patches
- **ZIP-Bundle enthält:**
  - HTML-Patches (Beispiele)
  - CSS-Fixes (produktionsbereit)
  - WordPress XML-Import
  - FTP-Anleitung
  - README mit Haftungsausschluss

---

## 4. Fix-Anwendung & Deployment

### 4.1 Deployment-Engine
**Datei:** `backend/compliance_engine/deployment_engine.py`

#### Deployment-Methoden:

**1. FTP Upload**
- Automatischer Upload
- Verzeichnis-Struktur-Erhalt
- Recursive Directory Creation
- Error-Handling & Retry-Logic

**2. SFTP/SSH Upload (Premium)**
- Verschlüsselte Übertragung
- SSH-Key-Support
- Sudo-Permissions
- Port-Konfiguration

**3. GitHub Pull Request**
- Automatische PR-Erstellung
- Branch: `complyo-fix-{id}`
- Commit-Message mit Fix-Details
- CI/CD-Integration

**4. Netlify Deployment**
- Build-Trigger via API
- Environment-Variables
- Deploy-Preview-URL
- Production-Deploy

**5. Vercel Deployment**
- API-basiertes Deployment
- Automatic HTTPS
- Global CDN
- Serverless Functions

**6. WordPress API**
- WP REST API Integration
- Media-Upload
- Post/Page-Updates
- Theme-File-Injection

### 4.2 Backup & Rollback
**Datei:** `backend/compliance_engine/deployment_engine.py` (rollback-Methode)

- **Automatisches Backup:**
  - Vor jedem Deployment
  - 30-Tage-Aufbewahrung
  - Komprimierte Speicherung
  
- **Rollback-Funktion:**
  - One-Click-Restore
  - Versionierung
  - Diff-Preview vor Rollback

### 4.3 Apply-Routes (API)
**Datei:** `backend/fix_apply_routes.py`

**Endpoints:**
- `POST /api/v2/fixes/apply` – Fix anwenden
- `POST /api/v2/fixes/rollback` – Rollback durchführen
- `POST /api/v2/fixes/apply/preview` – Staging-Preview (Premium)
- `GET /api/v2/fixes/apply/status/{id}` – Deployment-Status

### 4.4 Frontend: Apply-Modal
**Datei:** `dashboard-react/src/components/fixes/ApplyFixModal.tsx`

**Workflow:**
1. **Methode wählen** (FTP, SFTP, GitHub, ZIP)
2. **Credentials eingeben** (verschlüsselt übertragen)
3. **Backup-Option** (empfohlen)
4. **Bestätigung** (mit Haftungsausschluss)
5. **Deployment** (mit Progress-Indicator)
6. **Erfolg/Fehler** (mit Details)

---

## 5. Rechtssicherheit & Haftung

### 5.1 Haftungsklauseln
**Datei:** `COMPLYO_TERMS_LIABILITY.md`

**Kernpunkte:**
- ✅ Code-Änderungen nur nach Nutzer-Bestätigung
- ✅ Keine automatischen Schreibzugriffe
- ✅ Nutzer übernimmt Verantwortung
- ✅ KI-Fixes können Fehler enthalten
- ✅ Backup-Empfehlung
- ✅ Haftung begrenzt auf Abo-Gebühr (max. 5.000€)
- ✅ Widerrufsrecht erlischt mit erstem Fix

### 5.2 UI-Disclaimer
**Dateien:**
- `dashboard-react/src/components/dashboard/ConfirmFixModal.tsx`
- `dashboard-react/src/components/fixes/ApplyFixModal.tsx`

**Anzeige:**
- Vor jeder Fix-Generierung
- Vor jedem Deployment
- In ZIP-Exports (README)
- Verlinkung zu vollständigen AGB

### 5.3 Audit Trail
**Dateien:**
- `backend/migrations/create_fix_audit_trail.sql` (DB-Schema)
- `backend/audit_service.py` (Logging-Service)

**Logging:**
- ✅ Jede Fix-Generierung
- ✅ Jeden Download
- ✅ Jede Anwendung
- ✅ Jeden Rollback
- ✅ IP-Adresse & User-Agent
- ✅ Zeitstempel
- ✅ User-Bestätigung (Checkbox-Status)

**Datenbank-Tabellen:**
- `fix_application_audit` – Haupttabelle
- `fix_backups` – Backup-Verwaltung
- `staging_deployments` – Premium-Staging

**Views:**
- `user_audit_summary` – Statistiken pro User
- `recent_audit_log` – Letzte 1000 Einträge

### 5.4 Frontend: Audit-Log-Dashboard
**Datei:** `dashboard-react/src/components/dashboard/FixAuditLog.tsx`

**Features:**
- Tabelle mit allen Aktionen
- Filter nach Action-Type
- Rollback-Button (falls Backup vorhanden)
- Error-Details-Modal
- Export als CSV (geplant)

---

## 6. Integrationen

### 6.1 eRecht24 API
**Dateien:**
- `backend/erecht24_manager.py`
- `backend/erecht24_routes_v2.py`
- `backend/erecht24_service.py`

**Features:**
- Abmahnsichere Rechtstexte
- Automatische Updates via Webhook
- Impressum-Generator
- Datenschutzerklärung-Generator
- Project-API-Key-Management

**Text-Typen:**
- Impressum
- Datenschutzerklärung (Standard)
- Datenschutzerklärung (Social Media)
- Datenschutzerklärung (Google Fonts)

### 6.2 GitHub Actions Integration
**Datei:** `.github/workflows/ai-fix-pr.yml`

**Workflow:**
1. Repository Dispatch Event
2. Complyo sendet PR-Payload
3. GitHub Actions erstellt Branch
4. Commit mit Fix-Code
5. Pull Request öffnen
6. CI/CD-Tests laufen
7. Review & Merge

### 6.3 WordPress Integration
**Bereiche:**
- **Plugin (separates Projekt):** Spamify
- **XML-Import:** Mediathek (Alt-Texte)
- **REST API:** Theme-File-Updates
- **Gutenberg-Blocks:** Custom Accessibility-Blocks

### 6.4 Widget-System
**Dateien:**
- `backend/widgets/accessibility-v5.js`
- `backend/widget_routes.py`
- `backend/widget_manager.py`

**Features:**
- **Runtime-Fixes:**
  - Alt-Text-Injection
  - Kontrast-Toggle
  - Font-Size-Control
  - Screen-Reader-Modus
  
- **Analytics:**
  - Widget-Usage-Tracking
  - User-Interactions
  - A/B-Testing
  - Upsell-Opportunities

---

## 7. Dashboard & UX

### 7.1 Compliance-Dashboard
**Datei:** `dashboard-react/src/components/dashboard/WebsiteAnalysis.tsx`

**Widgets:**
1. **Compliance-Score** (Hero-Section)
2. **Issue-Kategorien** (4 Säulen)
3. **Quick Wins** (Einfache Fixes)
4. **Widget-Status-Badge** (Neu!)
5. **Legal News** (Gesetzesänderungen)
6. **Fix-History** (Letzte Aktionen)

### 7.2 Widget-Status-Badge
**Komponenten:**
- `dashboard-react/src/components/dashboard/AbmahnschutzStatus.tsx`
- Fix: `has_accessibility_widget` aus Backend übertragen

**Anzeige:**
- ✅ "Aktiv" (grün) – Widget läuft
- ⚠️ "Nicht eingebunden" (gelb) – Widget fehlt
- Dynamisch basierend auf Scanner-Ergebnis

### 7.3 Fix-Modal
**Datei:** `dashboard-react/src/components/dashboard/FixModal.tsx`

**Features:**
- KI-Fix-Anzeige
- Syntax-Highlighting (Prism.js)
- Diff-Viewer (Vorher/Nachher)
- Copy-to-Clipboard
- Download-Button
- Apply-Button (öffnet ApplyFixModal)

### 7.4 Diff-Viewer
**Datei:** `dashboard-react/src/components/fixes/FixPreview.tsx`

**Modi:**
- **Side-by-Side:** Vorher/Nachher nebeneinander
- **Unified:** Git-ähnliche Diff-Ansicht
- Syntax-Highlighting
- Zeilennummern
- Farbcodierung (Rot=Entfernt, Grün=Hinzugefügt)

### 7.5 Legal-News-Widget
**Datei:** `dashboard-react/src/components/dashboard/LegalNews.tsx`

**Features:**
- Automatische Updates
- AI-Klassifizierung (relevance, urgency)
- Filter nach Kategorie
- Archiv-Modal
- Feedback-System (helpful/not helpful)

---

## 8. Backend-Architektur

### 8.1 Scanner Engine
**Datei:** `backend/compliance_engine/scanner.py`

**Ablauf:**
1. URL-Validierung
2. HTML-Download (requests/httpx)
3. DOM-Parsing (BeautifulSoup)
4. CSS-Extraktion (cssutils)
5. JS-Analyse (regex-based)
6. Screenshot (Playwright)
7. Issue-Detection (alle Checker)
8. Score-Berechnung
9. Ergebnis-Speicherung

### 8.2 Fix-Generator
**Datei:** `backend/fix_generator.py`

**KI-Modelle:**
- OpenAI GPT-4 (Standard)
- Anthropic Claude (Fallback)
- Local LLMs (geplant für Premium)

**Prompts:**
- `backend/compliance_engine/prompts/impressum_prompt.txt`
- `backend/compliance_engine/prompts/datenschutz_prompt.txt`
- `backend/compliance_engine/prompts/accessibility_prompt.txt`
- `backend/compliance_engine/prompts/cookie_consent_prompt.txt`

### 8.3 Datenbank-Schema
**Haupttabellen:**
- `users` – Benutzer
- `websites` – Domains
- `analysis_results` – Scan-Ergebnisse
- `generated_fixes` – Fix-Daten
- `fix_application_audit` – Audit-Log (NEU!)
- `fix_backups` – Backups (NEU!)
- `staging_deployments` – Staging (Premium, NEU!)

**Indizes & Optimierungen:**
- `backend/database_optimization.sql`
- Connection-Pooling (asyncpg)
- Prepared Statements
- EXPLAIN ANALYZE für Queries

### 8.4 API-Routes
**Übersicht:**
- `backend/main_production.py` – Haupt-App
- `backend/fix_routes.py` – Fix-Generierung
- `backend/fix_apply_routes.py` – Fix-Anwendung (NEU!)
- `backend/widget_routes.py` – Widget-Analytics
- `backend/erecht24_routes_v2.py` – eRecht24-Integration
- `backend/legal_change_routes.py` – Legal-News

### 8.5 Monitoring & Logging
**Datei:** `backend/ai_fix_engine/monitoring.py`

**Metriken:**
- API-Response-Times
- AI-Model-Latency
- Error-Rates
- User-Feedback-Scores
- Token-Usage (OpenAI)

**Logs:**
- Structured Logging (JSON)
- Log-Levels (DEBUG, INFO, WARN, ERROR)
- Sentry-Integration (Production)

---

## 9. Barrierefreiheit (WCAG 2.1)

### 9.1 Checker-Suite
**Dateien:**
- `backend/compliance_engine/checks/barrierefreiheit_check.py`
- `backend/compliance_engine/checks/aria_checker.py`

**Prüfungen:**

#### Level A (Critical):
- ✅ Alt-Texte für Bilder
- ✅ Formularbeschriftungen
- ✅ Keyboard-Zugänglichkeit
- ✅ Sprachattribut (`<html lang="de">`)
- ✅ Page Title

#### Level AA (Standard):
- ✅ Kontrast-Ratio (4.5:1 / 3:1)
- ✅ Focus-Indikatoren
- ✅ Link-Texte (nicht "hier klicken")
- ✅ Heading-Hierarchie
- ✅ Skip-Links

#### Level AAA (Enhanced):
- Link-Kontrast 7:1
- Erweiterte Text-Spacing
- Reflow (kein horizontales Scrollen bei 320px)

### 9.2 Fix-Typen (Barrierefreiheit)

**Alt-Texte:**
- AI-generiert (GPT-4 Vision)
- Kontext-basiert
- SEO-optimiert
- Sprach-spezifisch

**Kontraste:**
- Automatische Color-Anpassung
- WCAG-konforme Paletten
- CSS-Variable-Injection

**ARIA-Labels:**
- Semantic HTML First
- ARIA als Fallback
- Screen-Reader-Testing

**Focus-Styles:**
- `:focus-visible` Support
- Sichtbare Outlines
- Custom Focus-Rings

### 9.3 Widget-Features
**Datei:** `backend/widgets/accessibility-v5.js`

**User-Controls:**
- Kontrast erhöhen
- Font-Size +/- 
- Highlight Links
- Screen-Reader-Modus
- Reduce Motion

---

## 10. DSGVO & Datenschutz

### 10.1 Datenschutz-Checker
**Datei:** `backend/compliance_engine/checks/datenschutz_check.py`

**Prüfungen:**
- Impressum vorhanden?
- Datenschutzerklärung vorhanden?
- SSL-Verschlüsselung?
- Cookie-Banner vorhanden?
- Verarbeitungsverzeichnis?
- Betroffenenrechte erwähnt?
- Speicherfristen definiert?

### 10.2 DSGVO-Konformität (Complyo selbst)
- Alle Daten in EU (Hetzner, Deutschland)
- Verschlüsselte DB-Verbindungen
- Verschlüsselte Passwörter (bcrypt)
- Session-Management mit Expiry
- GDPR-Retention-Service
- Daten-Löschung auf Anfrage (30 Tage)
- AVV auf Anfrage

**Datei:** `backend/gdpr_retention_service.py`

### 10.3 Rechtstexte-Generator
**Datei:** `backend/ai_fix_engine/handlers/legal_text_handler.py`

**Templates:**
- Impressum (TMG §5)
- Datenschutzerklärung (DSGVO Art. 13)
- AGB
- Widerrufsbelehrung

**Platzhalter:**
- [FIRMENNAME]
- [ANSCHRIFT]
- [EMAIL]
- [TELEFON]
- etc.

**⚠️ Disclaimer:** KI-generierte Texte sind NICHT abmahnsicher!  
**Empfehlung:** eRecht24-Integration nutzen.

---

## 11. Cookie-Compliance (TTDSG)

### 11.1 Cookie-Scanner
**Datei:** `backend/compliance_engine/cookie_analyzer.py`

**Erkennung:**
- First-Party-Cookies
- Third-Party-Cookies
- LocalStorage
- SessionStorage
- IndexedDB

**Klassifizierung:**
- Notwendig (Technisch erforderlich)
- Funktional (Benutzerkomfort)
- Analytisch (Google Analytics, etc.)
- Marketing (Facebook Pixel, etc.)

### 11.2 Cookie-Banner-Check
**Prüfungen:**
- Banner vorhanden?
- Opt-In vor Cookie-Setzung?
- Granulare Einwilligung?
- Widerrufsmöglichkeit?
- Privacy-Policy-Link?

### 11.3 Cookie-Consent-Generator
**Datei:** `backend/ai_fix_engine/handlers/cookie_handler.py`

**Output:**
- HTML für Cookie-Banner
- JavaScript für Consent-Management
- CSS für Styling
- Cookie-Richtlinien-Text

### 11.4 Consent-Logging
**Datei:** `backend/cookie_compliance_routes.py`

**Tabelle:** `consent_logs`
- User-Consent speichern
- Zeitstempel
- IP-Adresse
- Consent-Choices (JSON)
- Nachweis für 3 Jahre

---

## 12. Premium-Features

### 12.1 Staging-Preview (Managed-Plan)
**Datei:** `backend/fix_apply_routes.py` (Preview-Endpoint)

**Workflow:**
1. Temporäre Subdomain erstellen (`preview-{id}.complyo.tech`)
2. Fix auf Staging deployen
3. Screenshots erstellen (Before/After)
4. Diff-Image generieren (Pixelmatch)
5. User-Approval abwarten
6. Live-Deploy oder Verwerfen

**Technologie:**
- Playwright für Screenshots
- Pixelmatch für Diff
- Docker-Container für Isolation

### 12.2 SFTP/SSH-Deployment
**Datei:** `backend/compliance_engine/deployment_engine.py`

**Features:**
- Paramiko-basiert
- SSH-Key-Authentication
- Sudo-Permissions
- Port-Konfiguration
- Automatisches Backup

### 12.3 Priority-Support
- Dedicated Account Manager
- 24/7 Support-Hotline
- Video-Calls
- Custom-Integrationen

### 12.4 White-Label (Enterprise)
- Custom Branding
- Eigene Domain
- Logo & Farben
- Kein "Powered by Complyo"

---

## 13. Monitoring & Analytics

### 13.1 Fix-Monitoring
**Datei:** `backend/ai_fix_engine/monitoring.py`

**Metriken:**
- Fix-Generation-Time
- AI-Model-Usage
- Token-Consumption
- User-Feedback-Ratings
- Fix-Application-Rate

**Datenbank-Tabellen:**
- `ai_fix_monitoring` – Events
- `ai_model_usage` – AI-Calls
- `fix_user_feedback` – Ratings

### 13.2 Widget-Analytics
**Datei:** `backend/widget_routes.py`

**Tracking:**
- Widget-Loads
- Feature-Usage (Kontrast, Font-Size, etc.)
- User-Sessions
- Accessibility-Tool-Interactions

**Privacy:**
- Anonymisierte Daten
- Keine PII
- DSGVO-konform

### 13.3 Legal-Change-Monitoring
**Datei:** `backend/legal_change_monitor.py`

**Quellen:**
- Bundesgesetzblatt
- EU-Amtsblatt
- IT-Recht-Kanzlei
- RSS-Feeds

**AI-Klassifizierung:**
- Relevanz (0-10)
- Dringlichkeit (low/medium/high)
- Betroffene Branchen
- Handlungsbedarf

**Datei:** `backend/ai_legal_classifier.py`

### 13.4 Feedback-Learning
**Datei:** `backend/ai_feedback_learning.py`

**Lern-Loop:**
1. User gibt Feedback (helpful/not helpful)
2. Feedback wird gespeichert
3. AI-Prompts werden angepasst
4. Fix-Qualität verbessert sich
5. Kontinuierliche Optimierung

---

## 14. API & Webhooks

### 14.1 Public API Endpoints

**Scan API:**
```
POST /api/v2/scan
Body: { "url": "https://example.com" }
Response: { "scan_id": "...", "status": "scanning" }
```

**Fix-Generator API:**
```
POST /api/v2/fixes/generate
Body: { "issue_id": "...", "issue_category": "..." }
Response: { "fix_id": "...", "fix_data": {...} }
```

**Apply API:**
```
POST /api/v2/fixes/apply
Body: { "fix_id": "...", "deployment_method": "ftp", "credentials": {...} }
Response: { "success": true, "deployment_id": "...", "backup_id": "..." }
```

**Rollback API:**
```
POST /api/v2/fixes/rollback
Body: { "backup_id": "...", "credentials": {...} }
Response: { "success": true, "audit_id": "..." }
```

**Audit-Log API:**
```
GET /api/v2/audit/log?limit=50
Response: { "audit_log": [...], "statistics": {...} }
```

### 14.2 Webhooks

**eRecht24 Webhook:**
```
POST /api/webhook/erecht24
Body: { "project_key": "...", "text_type": "...", "updated_at": "..." }
Action: Update Rechtstexte in DB
```

**GitHub Webhook:**
```
POST /api/webhook/github
Body: { "pr_merged": true, "fix_id": "...", "deployment_id": "..." }
Action: Mark Fix as Deployed
```

### 14.3 Rate Limiting
**Datei:** `backend/fix_routes.py`

**Limits:**
- AI Plan: 10 Fix-Generierungen/Stunde
- Expert Plan: Unbegrenzt
- Public API: 100 Requests/Tag
- Webhook: 1000 Requests/Tag

### 14.4 Authentication
- JWT-Token-basiert
- Bearer-Token im Header
- Refresh-Token-Mechanismus
- Session-Management

**Datei:** `backend/auth_service.py`

---

## 🎯 Zusammenfassung

### Implementiert ✅
- ✅ Website-Scanner (4 Säulen)
- ✅ KI-Fix-Generator (Code, Text, Guide, Widget)
- ✅ Deployment-Engine (FTP, SFTP, GitHub, etc.)
- ✅ Backup & Rollback
- ✅ Audit Trail (rechtssicher)
- ✅ Haftungsklauseln (AGB + UI)
- ✅ eRecht24-Integration
- ✅ Widget-System
- ✅ Diff-Viewer
- ✅ Dashboard mit allen Komponenten
- ✅ Legal-News mit AI-Klassifizierung
- ✅ API mit allen Endpoints
- ✅ Monitoring & Analytics

### In Entwicklung 🚧
- Staging-Preview (Backend fertig, Frontend TODO)
- Screenshot-Diff (Playwright-Integration)
- Advanced AI-Learning
- White-Label-Solution

### Geplant 📅
- Mobile App
- Browser-Extension
- VS-Code-Plugin
- Figma-Plugin

---

## 📊 Statistiken

- **Backend-Dateien:** ~150
- **Frontend-Komponenten:** ~80
- **API-Endpoints:** ~50
- **Datenbank-Tabellen:** ~30
- **Unterstützte Frameworks:** 6+
- **Deployment-Methoden:** 6
- **WCAG-Kriterien geprüft:** 50+
- **DSGVO-Checks:** 20+

---

## 🚀 Deployment-Ready

Alle Features sind production-ready und können sofort genutzt werden!

**Vollständige Dokumentation:**
- `COMPLYO_TERMS_LIABILITY.md` – Haftungsklauseln
- `API_DOCUMENTATION.md` – API-Referenz
- `docs/USER-GUIDE-AUTO-FIX.md` – User-Guides
- `docs/ARCHITEKTUR-FIX-ENGINE.md` – Technische Architektur

---

**© 2025 Complyo.tech** – Made with ❤️ for compliance and accessibility

