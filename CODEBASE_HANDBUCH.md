# Complyo Codebase Handbuch

> **Letzte Aktualisierung:** 2026-02-07  
> **Version:** 2.2.0  
> **Zweck:** Zentrale Dokumentation als Leitfaden für Entwicklung und Wartung

---

## Inhaltsverzeichnis

1. [Projekt-Übersicht](#1-projekt-übersicht)
2. [Architektur](#2-architektur)
3. [Backend](#3-backend)
4. [Frontend Dashboard](#4-frontend-dashboard)
5. [Frontend Landing](#5-frontend-landing)
6. [Widgets](#6-widgets)
7. [Datenbank](#7-datenbank)
8. [Deployment & Infrastruktur](#8-deployment--infrastruktur)
9. [Dateien zur Löschung vorgeschlagen](#9-dateien-zur-löschung-vorgeschlagen)

---

## 1. Projekt-Übersicht

**Complyo** ist eine KI-gestützte SaaS-Plattform für Website-Compliance mit Fokus auf:
- **DSGVO** (Datenschutz-Grundverordnung)
- **TTDSG** (Telekommunikation-Telemedien-Datenschutz-Gesetz)
- **TMG** (Telemediengesetz)
- **BFSG** (Barrierefreiheitsstärkungsgesetz)
- **EU AI Act** (KI-Verordnung)

### Kernfunktionen

| Feature | Beschreibung |
|---------|-------------|
| **Compliance-Scanner** | Automatische Prüfung von Websites auf rechtliche Konformität |
| **AI Fix-Engine** | KI-generierte Lösungsvorschläge für Compliance-Probleme |
| **Cookie-Banner** | DSGVO-konformes Cookie-Consent-Management |
| **Accessibility-Widget** | WCAG 2.1 AA Barrierefreiheit |
| **Legal News** | RSS-Feed-basierte Rechtsänderungs-Überwachung |
| **eRecht24 Integration** | Anwaltlich geprüfte Rechtstexte |

---

## 2. Architektur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            NGINX Gateway                                │
│                         (SSL, Routing, CORS)                            │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Landing     │       │    Dashboard    │       │     Backend     │
│   (Next.js)   │       │    (Next.js)    │       │    (FastAPI)    │
│ complyo.tech  │       │ app.complyo.tech│       │ api.complyo.tech│
└───────────────┘       └─────────────────┘       └────────┬────────┘
                                                           │
                        ┌──────────────────────────────────┼──────────────────────────────────┐
                        │                                  │                                  │
                        ▼                                  ▼                                  ▼
               ┌────────────────┐               ┌─────────────────┐               ┌─────────────────┐
               │   PostgreSQL   │               │    OpenRouter   │               │    eRecht24     │
               │   (Datenbank)  │               │   (AI Models)   │               │     (API)       │
               └────────────────┘               └─────────────────┘               └─────────────────┘
```

### Verzeichnisstruktur

```
saas-project-2/
├── backend/               # FastAPI Backend
│   ├── ai_fix_engine/    # KI-basierte Fix-Generierung
│   ├── compliance_engine/ # Scanner und Checks
│   ├── widgets/          # JavaScript Widgets
│   ├── migrations/       # SQL Migrationen
│   └── tests/            # Unit Tests
├── dashboard-react/       # Next.js Dashboard App
│   └── src/
│       ├── app/          # Pages (App Router)
│       ├── components/   # React Komponenten
│       └── lib/          # API, Utilities
├── landing-react/         # Next.js Landing Page
│   └── src/
│       ├── app/          # Pages
│       └── components/   # Landing Komponenten
├── gateway/               # NGINX Konfiguration
├── docs/                  # Technische Dokumentation
├── md/                    # Projekt-Dokumentation
└── scripts/               # Deployment & Maintenance
```

---

## 3. Backend

### 3.1 Haupt-Entry-Point

**`main_production.py`** - FastAPI Anwendung

- **Version:** 2.2.0
- **Basis-URL:** `https://api.complyo.tech`
- **Port:** 8000

### 3.2 API Routes Übersicht

| Route-Datei | Präfix | Funktion |
|-------------|--------|----------|
| `auth_routes.py` | `/api/auth` | Authentifizierung (JWT + Firebase) |
| `user_routes.py` | `/api/user` | Benutzerprofil, Domain-Locks |
| `public_routes.py` | `/api` | Öffentliche API (Widget-Analysen) |
| `website_routes.py` | `/api/v2/websites` | Website-Tracking |
| `dashboard_routes.py` | `/api/v2/dashboard` | Dashboard-Metriken |
| `fix_routes.py` | `/api/v2/fixes` | KI-Fix-Generierung |
| `fix_apply_routes.py` | `/api/v2/fixes` | Fix-Deployment (FTP/SFTP/GitHub) |
| `accessibility_fix_routes.py` | `/api/v2/accessibility` | BFSG-Fixes |
| `alt_text_routes.py` | `/api/accessibility` | KI-generierte Alt-Texte |
| `cookie_compliance_routes.py` | `/api/cookies` | Cookie-Consent-Management |
| `ab_test_routes.py` | `/api/ab-tests` | A/B-Testing |
| `tcf_routes.py` | `/api/tcf` | IAB TCF 2.2 Compliance |
| `erecht24_routes_v2.py` | `/api/v2` | eRecht24 Integration |
| `erecht24_webhook_routes.py` | `/webhooks/erecht24` | Gesetzesänderungs-Webhooks |
| `legal_news_routes.py` | `/api/legal` | Rechtliche Neuigkeiten |
| `legal_change_routes.py` | `/api/legal-changes` | Legal Change Monitoring |
| `ai_legal_routes.py` | `/api/legal-ai` | KI-klassifizierte Gesetzesänderungen |
| `ai_compliance_routes.py` | `/api/ai` | EU AI Act Compliance |
| `payment_routes.py` | `/api/payment` | Stripe-Integration |
| `stripe_routes.py` | `/api/stripe` | Freemium-Modell |
| `addon_payment_routes.py` | `/api/addons` | Add-on-Zahlungen |
| `git_routes.py` | `/api/v2/git` | GitHub/GitLab PR-Automation |
| `widget_routes.py` | `/api/widgets` | Widget-Serving |
| `admin_routes.py` | `/api/admin` | Admin-Dashboard |
| `lead_routes.py` | `/api/leads` | Lead-Management |
| `expert_service_routes.py` | `/api/expert-service` | Expertservice-Buchung |
| `gdpr_api.py` | `/api/gdpr` | DSGVO-Datenrechte (Art. 17 & 20) |
| `i18n_api.py` | `/api/i18n` | Internationalisierung |

### 3.3 Services

| Service | Datei | Funktion |
|---------|-------|----------|
| **AuthService** | `auth_service.py` | JWT-Token, Session-Management |
| **DatabaseService** | `database_service.py` | PostgreSQL mit Fallback |
| **EmailService** | `email_service.py` | SMTP Email-Versand |
| **AuditService** | `audit_service.py` | Fix-Audit-Trail |
| **CookieScannerService** | `cookie_scanner_service.py` | Cookie-Erkennung (40+ Services) |
| **ERecht24Service** | `erecht24_service.py` | eRecht24 API + White-Label |
| **ERecht24RechtstexteService** | `erecht24_rechtstexte_service.py` | Rechtstexte-SDK |
| **ExportService** | `export_service.py` | PDF/HTML-Export |
| **GDPRRetentionService** | `gdpr_retention_service.py` | Automatische Datenlöschung |
| **I18nService** | `i18n_service.py` | Übersetzungen (DE/EN) |
| **NewsService** | `news_service.py` | RSS-Feed-Parser |
| **OAuthService** | `oauth_service.py` | Google & Apple Sign-In |

### 3.4 AI Services

| Service | Datei | Funktion |
|---------|-------|----------|
| **AISolutionCacheService** | `ai_solution_cache_service.py` | Intelligentes AI-Caching (70-85% Reduktion) |
| **AIActAnalyzer** | `ai_act_analyzer.py` | EU AI Act Risiko-Klassifizierung |
| **AIActDocGenerator** | `ai_act_doc_generator.py` | AI Act Dokumentations-Generator |
| **AIDocumentGenerator** | `ai_document_generator.py` | Impressum/Datenschutz-Generierung |
| **AIFeedbackLearning** | `ai_feedback_learning.py` | Selbstlernendes Feedback-System |
| **AILegalClassifier** | `ai_legal_classifier.py` | Gesetzesänderungs-Klassifizierung |

### 3.5 AI Fix Engine (`ai_fix_engine/`)

Zentrale KI-Engine für automatische Compliance-Fixes.

#### Architektur-Flow

```
API Request → UnifiedFixEngine → Fix-Typ-Bestimmung
                    ↓
             AI-Call (Claude 3.5 → GPT-4 Fallback → Template)
                    ↓
             Response-Parsing & Validation
                    ↓
        ┌──────────┴──────────┐
        │                     │
   ┌────┴────┐          ┌────┴────┐
   │ Handler │          │ Handler │
   └─────────┘          └─────────┘
        │                     │
        └──────────┬──────────┘
                   ↓
              FixResult
```

#### Handler

| Handler | Datei | Zuständigkeit |
|---------|-------|---------------|
| **LegalTextHandler** | `handlers/legal_text_handler.py` | Impressum, Datenschutz, AGB |
| **CookieBannerHandler** | `handlers/cookie_handler.py` | Cookie-Consent, TTDSG §25 |
| **AccessibilityHandler** | `handlers/accessibility_handler.py` | WCAG 2.1, Alt-Texte, ARIA |
| **CodeFixHandler** | `handlers/code_handler.py` | HTML/CSS/JS/PHP Fixes |
| **GuideHandler** | `handlers/guide_handler.py` | Schritt-für-Schritt-Anleitungen |

#### Kern-Komponenten

| Komponente | Datei | Funktion |
|------------|-------|----------|
| **UnifiedFixEngine** | `unified_fix_engine.py` | Zentrale Orchestrierung |
| **PromptBuilder** | `prompts_v2.py` | Prompt-Templates & JSON-Schemas |
| **FixValidator** | `validators.py` | Schema-, Syntax-, Legal-Validation |
| **IntelligentAnalyzer** | `intelligent_analyzer.py` | Issue-Kategorisierung (Legacy) |

### 3.6 Compliance Engine (`compliance_engine/`)

Scanner und Checker für Website-Compliance.

#### Scanner-Hierarchie

| Scanner | Datei | Dauer | Einsatz |
|---------|-------|-------|---------|
| **QuickScanner** | `quick_scanner.py` | 10-20s | Schnellcheck, kritische Issues |
| **BaseScanner** | `scanner.py` | 30-60s | Standard-Analyse |
| **DeepScanner** | `deep_scanner.py` | 60-120s | Vollständige Analyse mit Context |

#### Checks (`checks/`)

| Check | Datei | Prüft |
|-------|-------|-------|
| **BarrierefreiheitCheck** | `barrierefreiheit_check.py` | WCAG 2.1, BFSG, Widget-Erkennung |
| **ImpressumCheck** | `impressum_check.py` | TMG §5 Pflichtangaben |
| **DatenschutzCheck** | `datenschutz_check.py` | DSGVO Art. 13/14 |
| **CookieCheck** | `cookie_check.py` | TTDSG §25, Banner-Erkennung |
| **TCFCheck** | `tcf_check.py` | IAB TCF 2.2 Compliance |
| **ARIAChecker** | `aria_checker.py` | ARIA-Labels, Landmarks |
| **MediaAccessibilityCheck** | `media_accessibility_check.py` | Video/Audio-Untertitel |
| **DeepContentAnalyzer** | `deep_content_analyzer.py` | KI-basierte Content-Analyse |

#### Weitere Komponenten

| Komponente | Datei | Funktion |
|------------|-------|----------|
| **BrowserRenderer** | `browser_renderer.py` | Headless Chromium für JS-Seiten |
| **ContrastAnalyzer** | `contrast_analyzer.py` | WCAG Kontrast-Prüfung |
| **PDFGenerator** | `pdf_generator.py` | Compliance-Reports als PDF |
| **CodeGenerator** | `code_generator.py` | Framework-spezifische Fixes |
| **WorkflowEngine** | `workflow_engine.py` | Guided User Journey |
| **GitHubIntegration** | `github_integration.py` | Automatische PRs |

### 3.7 Tests (`tests/`)

| Test | Datei | Prüft |
|------|-------|-------|
| **TestBarrierefreiheit** | `test_barrierefreiheit.py` | ARIA, Kontrast |
| **TestBFSGFeatures** | `test_bfsg_features.py` | BFSG-Compliance |
| **TestCookies** | `test_cookies.py` | Cookie-Scanning |
| **TestDatenschutz** | `test_datenschutz.py` | Datenschutz-Checks |
| **TestImpressum** | `test_impressum.py` | Impressum-Checks |
| **TestTCFCompliance** | `test_tcf_compliance.py` | TCF 2.2 |

### 3.8 Cronjobs (`cronjobs/`)

| Cronjob | Datei | Intervall | Funktion |
|---------|-------|-----------|----------|
| **FetchNews** | `fetch_news.py` | Täglich 06:00 | RSS-Feed-Abruf |

---

## 4. Frontend Dashboard

**Pfad:** `dashboard-react/`  
**Framework:** Next.js 14 (App Router)  
**URL:** `https://app.complyo.tech`

### 4.1 Seiten (`src/app/`)

| Route | Datei | Funktion |
|-------|-------|----------|
| `/` | `page.tsx` | Haupt-Dashboard mit WebsiteAnalysis, LegalNews, CookieWidget |
| `/login` | `login/page.tsx` | Login (Email/Passwort + OAuth) |
| `/register` | `register/page.tsx` | Registrierung |
| `/profile` | `profile/page.tsx` | Benutzerprofil |
| `/subscription` | `subscription/page.tsx` | Abo-Verwaltung |
| `/cookie-compliance` | `cookie-compliance/page.tsx` | Cookie-Banner-Konfiguration |
| `/journey` | `journey/page.tsx` | Guided Compliance Journey |
| `/privacy` | `privacy/page.tsx` | Datenschutz-Einstellungen |
| `/ai-compliance` | `ai-compliance/page.tsx` | EU AI Act Modul |
| `/ai-compliance/systems/new` | `ai-compliance/systems/new/page.tsx` | KI-System registrieren |
| `/ai-compliance/systems/[id]` | `ai-compliance/systems/[id]/page.tsx` | KI-System Details |
| `/ai-compliance/upgrade` | `ai-compliance/upgrade/page.tsx` | AI Guard Add-on kaufen |

### 4.2 Komponenten (`src/components/`)

#### Dashboard-Komponenten (`dashboard/`)

| Komponente | Funktion |
|------------|----------|
| `DashboardHeader.tsx` | Navigation, User-Menu, Theme-Toggle |
| `DomainHeroSection.tsx` | URL-Eingabe, Score-Anzeige, KI-CTA |
| `WebsiteAnalysis.tsx` | Compliance-Issues mit Fix-Buttons |
| `LegalNews.tsx` | Rechtliche Neuigkeiten Widget |
| `CookieComplianceWidget.tsx` | Cookie-Status & Banner-Link |
| `AIComplianceCard.tsx` | EU AI Act Sidebar |
| `UnifiedFixButton.tsx` | KI-Fix-Generierung auslösen |
| `FixModal.tsx` | Fix-Anzeige & Download |
| `FixResultModal.tsx` | Fix-Ergebnis mit Code-Preview |
| `ExpertServiceModal.tsx` | Expertservice-Buchung |
| `StripePaywallModal.tsx` | Upgrade-Aufforderung |
| `ScanHistoryPanel.tsx` | Frühere Scans |
| `ActiveJobsPanel.tsx` | Laufende Fix-Jobs |
| `ComplianceIssueGroup.tsx` | Gruppierte Issues |
| `ComplianceIssueCard.tsx` | Einzelnes Issue |

#### Cookie-Compliance (`cookie-compliance/`)

| Komponente | Funktion |
|------------|----------|
| `cookie-compliance.tsx` | Haupt-Konfigurationsseite |
| `CookieBannerDesigner.tsx` | Visueller Banner-Editor |
| `ServiceManager.tsx` | Cookie-Service-Verwaltung |
| `ConsentStatistics.tsx` | Consent-Statistiken |
| `ABTestManager.tsx` | Banner A/B-Tests |
| `TCFManager.tsx` | TCF 2.2 Konfiguration |
| `ConsentModeSettings.tsx` | Google Consent Mode v2 |
| `IntegrationGuide.tsx` | Code-Snippets |

#### Accessibility (`accessibility/`)

| Komponente | Funktion |
|------------|----------|
| `AccessibilityWidget.tsx` | Widget-Integration |
| `FixWizard.tsx` | Schritt-für-Schritt-Fix |
| `ImageIssuesList.tsx` | Bilder ohne Alt-Text |
| `PatchDownloadCard.tsx` | Fix-Download |

#### AI (`ai/`)

| Komponente | Funktion |
|------------|----------|
| `AIAssistant.tsx` | Floating AI-Chat-Bot |
| `AIFixDisplay.tsx` | Fix-Anzeige |
| `AIFixPreview.tsx` | Code-Preview |

#### UI (`ui/`)

Standard shadcn/ui Komponenten: `button`, `card`, `dialog`, `input`, `select`, `tabs`, `checkbox`, `switch`, `slider`, `progress`, `badge`, `alert`, `textarea`, `label`, `Toast`, `Skeleton`

### 4.3 State Management

| Store/Context | Datei | Funktion |
|---------------|-------|----------|
| **AuthContext** | `contexts/AuthContext.tsx` | User-Session, JWT-Tokens |
| **ThemeContext** | `contexts/ThemeContext.tsx` | Dark/Light Mode |
| **DashboardStore** | `stores/dashboard.ts` | Zustand für Scan-Daten (Zustand) |

### 4.4 Hooks

| Hook | Datei | Funktion |
|------|-------|----------|
| `useAuth` | `hooks/useAuth.ts` | Auth-Context-Wrapper |
| `useCompliance` | `hooks/useCompliance.ts` | Scan-Status, Issues |
| `useMetrics` | `hooks/useMetrics.ts` | Dashboard-Metriken |
| `useDashboardInitialization` | `hooks/useDashboardInitialization.ts` | Initial-Daten laden |

### 4.5 API-Utilities (`lib/`)

| Datei | Funktion |
|-------|----------|
| `api.ts` | Backend-API-Aufrufe |
| `api-utils.ts` | Fetch-Wrapper, Error-Handling |
| `auth-api.ts` | Auth-spezifische Calls |
| `ai-compliance-api.ts` | AI Act Modul API |
| `firebase.ts` | Firebase Auth Config |
| `constants.ts` | API-URLs, Konfiguration |
| `utils.ts` | Hilfsfunktionen |

---

## 5. Frontend Landing

**Pfad:** `landing-react/`  
**Framework:** Next.js 14  
**URL:** `https://complyo.tech`

### 5.1 Seiten

| Route | Datei | Funktion |
|-------|-------|----------|
| `/` | `page.tsx` | Haupt-Landing-Page (mit A/B-Test-Router) |
| `/impressum` | `impressum/page.tsx` | Impressum |
| `/datenschutz` | `datenschutz/page.tsx` | Datenschutzerklärung |
| `/agb` | `agb/page.tsx` | AGB |
| `/gdpr` | `gdpr/page.tsx` | GDPR-Anfragen |
| `/verify-email` | `verify-email/page.tsx` | Email-Verifizierung |
| `/admin` | `admin/page.tsx` | Admin-Login |
| `/admin/dashboard` | `admin/dashboard/page.tsx` | Admin-Dashboard |

### 5.2 Landing-Page-Varianten

| Variante | Komponente | Stil |
|----------|------------|------|
| **Original** | `ComplyoOriginalLanding.tsx` | Klassisch, informativ |
| **Modern** | `ComplyoModernLanding.tsx` | Minimalistisch, modern |
| **HighConversion** | `ComplyoHighConversionLanding.tsx` | Conversion-optimiert |
| **Viral** | `ComplyoViralLanding.tsx` | Social-Media-optimiert |
| **Alfima** | `AlfimaLanding.tsx` | White-Label für Alfima |
| **Professional** | `ProfessionalLanding.tsx` | B2B-fokussiert |

### 5.3 Landing-Komponenten (`components/landing/`)

| Komponente | Funktion |
|------------|----------|
| `HeroSection.tsx` | Hero mit Scanner-Demo |
| `ProductFeatures.tsx` | Feature-Übersicht |
| `PricingTable.tsx` | Preismodelle |
| `BenefitsGrid.tsx` | Vorteile-Grid |
| `Testimonials.tsx` | Kundenstimmen |
| `FAQAccordion.tsx` | Häufige Fragen |
| `CTASection.tsx` | Call-to-Action |
| `TrustMetrics.tsx` | Vertrauens-Metriken |
| `WebsiteScanner.tsx` | Live-Scanner-Demo |
| `InteractiveDemo.tsx` | Interaktive Demo |
| `VideoDemo.tsx` | Video-Einbindung |
| `ComplianceBadges.tsx` | Compliance-Badges |

### 5.4 A/B-Testing

**`ABTestRouter.tsx`** - Automatische Verteilung auf Landing-Varianten basierend auf:
- Cookie-basierter Zuweisung
- Admin-Override per Query-Parameter

---

## 6. Widgets

**Pfad:** `backend/widgets/`

### 6.1 Accessibility Widgets

| Widget | Datei | Version | Status |
|--------|-------|---------|--------|
| **Accessibility v6** | `accessibility-v6.js` | 6.0.0 | **AKTIV** (aktuell) |
| **Accessibility v5** | `accessibility-v5.js` | 5.0.0 | Legacy (noch in Verwendung) |
| **Accessibility** | `accessibility.js` | 1.0.0 | **VERALTET** |
| **Accessibility Smart** | `accessibility_smart.js` | - | **VERALTET** |

#### Features (v6)

- Grid-Layout (3 Spalten, UserWay-Style)
- 30+ Accessibility-Features
- Multi-Language (DE/EN)
- Keyboard-Shortcuts (CTRL+U)
- LocalStorage-Persistenz
- WCAG 2.1 AA konform

### 6.2 Cookie Widgets

| Widget | Datei | Version | Status |
|--------|-------|---------|--------|
| **Cookie Banner v2** | `cookie_banner_v2.js` | 2.0.0 | **AKTIV** |
| **Cookie Consent** | `cookie_consent.js` | 1.0.0 | **VERALTET** |
| **Content Blocker** | `content_blocker.js` | - | **AKTIV** (Addon) |
| **Optout Center** | `optout_center.js` | - | **AKTIV** (Addon) |

#### Features (Cookie Banner v2)

- DSGVO/TTDSG-konform
- 3 Layouts: Banner, Modal, Floating
- Google Consent Mode v2
- Granulares Consent-Management
- 17 Sprachen
- Content-Blocker-Integration
- TCF 2.2 Support

### 6.3 Public Scripts (`backend/public/`)

| Script | Funktion | Status |
|--------|----------|--------|
| `cookie-blocker.js` | Script-Blocking vor Consent | **AKTIV** |
| `privacy-shield.js` | Social-Media-Privacy | **AKTIV** |
| `complyo-cmp-adapter.js` | CMP-Adapter | **AKTIV** |

### 6.4 Übersetzungen

**`locales/translations.js`** - Multi-Language Support für Widgets (17 Sprachen)

---

## 7. Datenbank

**System:** PostgreSQL  
**ORM:** Keine (Raw asyncpg)  
**Migrationen:** SQL-Dateien

### 7.1 Haupt-Tabellen

| Tabelle | Funktion |
|---------|----------|
| `users` | Benutzerkonten, Subscription-Status |
| `user_sessions` | JWT Refresh-Tokens |
| `websites` | Registrierte Websites |
| `tracked_websites` | Website-Tracking (Legacy-Compat) |
| `scans` | Scan-Ergebnisse |
| `scan_history` | Scan-Historie |
| `fix_jobs` | Background Fix-Jobs |
| `legal_news` | Rechtliche Neuigkeiten |
| `rss_feed_sources` | RSS-Feed-Quellen |

### 7.2 Cookie/Consent-Tabellen

| Tabelle | Funktion |
|---------|----------|
| `cookie_configs` | Banner-Konfigurationen |
| `consent_logs` | Consent-Events |
| `cookie_services` | Erkannte Cookie-Services |
| `ab_tests` | A/B-Test-Definitionen |
| `ab_test_results` | A/B-Test-Ergebnisse |

### 7.3 Feature-Tabellen

| Tabelle | Funktion |
|---------|----------|
| `user_modules` | Freigeschaltete Module pro User |
| `user_addons` | Gekaufte Add-ons |
| `domain_locks` | Domain-Binding für Fixes |
| `fix_audit_trail` | Audit-Log für Fixes |
| `ai_solution_cache` | KI-Lösungs-Cache |
| `legal_updates` | Gesetzesänderungen |

### 7.4 Wichtige SQL-Dateien

| Datei | Funktion |
|-------|----------|
| `database_setup.sql` | Haupt-Schema (alle Core-Tabellen) |
| `init_auth_tables.sql` | Auth-Tabellen |
| `init_cookie_compliance.sql` | Cookie-Tabellen |
| `migration_freemium_model.sql` | Freemium-Pläne |
| `migrations/complete_migration.sql` | Vollständige Migration |

---

## 8. Deployment & Infrastruktur

### 8.1 Docker-Konfiguration

| Datei | Funktion |
|-------|----------|
| `docker-compose.yml` | Development-Setup |
| `docker-compose.production.yml` | Production-Setup |
| `backend/Dockerfile` | Backend-Image |
| `dashboard-react/Dockerfile.prod` | Dashboard-Image |
| `landing-react/Dockerfile.prod` | Landing-Image |
| `gateway/Dockerfile` | NGINX-Image |

### 8.2 NGINX (`gateway/`)

| Datei | Funktion |
|-------|----------|
| `nginx.conf` | Development-Konfig |
| `nginx-production.conf` | Production-Konfig |
| `cors_config` | CORS-Regeln |
| `proxy_config` | Proxy-Settings |

### 8.3 SSL (`ssl/`)

- Certbot-basierte Let's Encrypt Zertifikate
- Automatische Erneuerung via Cronjob

### 8.4 Scripts (`scripts/`)

| Script | Funktion |
|--------|----------|
| `deploy-production.sh` | Production-Deployment |
| `ssl-setup.sh` | SSL-Zertifikat-Setup |
| `renew-ssl.sh` | SSL-Erneuerung |
| `backup-system.sh` | System-Backup |
| `security-audit.sh` | Security-Audit |

### 8.5 Backup (`backup-scripts/`)

| Script | Funktion |
|--------|----------|
| `backup-postgres.sh` | PostgreSQL-Backup |
| `restore-postgres.sh` | PostgreSQL-Restore |
| `setup-cron.sh` | Cron-Setup |

---

## 9. Dateien zur Löschung vorgeschlagen

### 9.1 Backend - Veraltete/Ungenutzte Dateien

#### Definitiv löschen (nicht referenziert)

| Datei | Grund |
|-------|-------|
| `classify_legal_updates.py` | Nicht importiert, durch `ai_legal_classifier.py` ersetzt |
| `classify_legal_updates_simple.py` | Nicht importiert, Legacy |
| `classify_new_updates.py` | Nicht importiert, Legacy |
| `classify_new_updates_v2.py` | Nicht importiert, Legacy |
| `classify_new_updates_v3.py` | Nicht importiert, Legacy |
| `cleanup_old_functions.py` | Einmaliges Cleanup-Script |
| `create_master_user.py` | Einmaliges Setup-Script |
| `create_master_user_direct.py` | Einmaliges Setup-Script |
| `reset_master_password.py` | Einmaliges Script |
| `test_freemium_flow.py` | Test-Script |
| `setup_ai_legal_system.py` | Einmaliges Setup |
| `setup_erecht24_webhook.py` | Einmaliges Setup |
| `run_migration.py` | Einmaliges Script |
| `migrate.py` | Einmaliges Script |
| `init_lead_tables.py` | Einmaliges Script |
| `update_main.py` | Veraltetes Update-Script |
| `erecht24_routes_v2_simple.py` | Nicht referenziert, Legacy |

#### Widgets - Veraltete Versionen

| Datei | Grund |
|-------|-------|
| `widgets/accessibility.js` | v1, ersetzt durch v6 |
| `widgets/accessibility_smart.js` | Nicht referenziert |
| `widgets/cookie_consent.js` | v1, ersetzt durch v2 |

#### Public - Test-Dateien

| Datei | Grund |
|-------|-------|
| `public/banner-demo-final.html` | Test-Datei |
| `public/banner-test-clean.html` | Test-Datei |
| `public/cookie-test.html` | Test-Datei |
| `public/integration-fixed.html` | Test-Datei |
| `public/test-banner-production.html` | Test-Datei |
| `public/test-banner.html` | Test-Datei |

#### SQL - Redundante/Einmalige Migrationen

| Datei | Grund |
|-------|-------|
| `create_master_user.sql` | Einmalig ausgeführt |
| `add_lead_management.sql` | In `database_setup.sql` integriert |

### 9.2 Root-Verzeichnis

| Datei | Grund |
|-------|-------|
| `COOKIE_BANNER_DEBUG_SCRIPT.js` | Debug-Script |
| `COOKIE_BANNER_MANUAL_TEST.html` | Test-Datei |
| `deploy_ai_legal_production.sh` | Einmaliges Deployment |

### 9.3 Markdown-Dateien (md/)

**Behalten:**
- `README.md`
- `API_DOCUMENTATION.md`
- `PLATTFORM_UEBERSICHT.md`
- `ROADMAP.md`

**Löschen (veraltet/Debug):**

| Datei | Grund |
|-------|-------|
| Alle `COOKIE_BANNER_*.md` Dateien (15+) | Debug-Dokumentation |
| `SSL_FIX_*.md` Dateien | Einmalige Fixes |
| `WIDGET-V5-*.md` Dateien | Veraltet (v6 aktuell) |
| `TASK_ISSUE_GROUPS_DEBUG.md` | Debug |
| `BUGFIX_WIDGET_ERKENNUNG.md` | Einmaliger Fix |

### 9.4 Landing - Backup-Dateien

| Datei | Grund |
|-------|-------|
| `page.tsx.backup` | Backup |
| `ComplyoOriginalLanding.tsx.backup` | Backup |
| `ComplyoHighConversionLanding.tsx.backup` | Backup |

### 9.5 Dashboard - Veraltete Dateien

| Datei | Grund |
|-------|-------|
| `Dockerfile.debug` | Debug-Dockerfile |
| `next.config.debug.js` | Debug-Konfig |

---

## Zusammenfassung

### Statistiken

| Bereich | Anzahl |
|---------|--------|
| **Backend Routes** | 28 |
| **Backend Services** | 18 |
| **Dashboard Pages** | 12 |
| **Dashboard Komponenten** | ~100 |
| **Landing Varianten** | 6 |
| **Aktive Widgets** | 4 |
| **Datenbank-Tabellen** | ~30 |
| **Zur Löschung vorgeschlagen** | ~50 Dateien |

### Kritische Pfade

1. **Scan-Flow:** `public_routes.py` → `scanner.py` → `checks/*` → `issue_grouper.py`
2. **Fix-Flow:** `fix_routes.py` → `unified_fix_engine.py` → `handlers/*` → `validators.py`
3. **Auth-Flow:** `auth_routes.py` → `auth_service.py` → `database_service.py`
4. **Cookie-Banner:** `widget_routes.py` → `cookie_banner_v2.js` → `content_blocker.js`

### Wichtige Umgebungsvariablen

```env
DATABASE_URL=postgresql://...
OPENROUTER_API_KEY=sk-...
ERECHT24_API_KEY=...
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET_KEY=...
SMTP_HOST=...
SMTP_USER=...
SMTP_PASSWORD=...
```

---

**Ende des Handbuchs**
