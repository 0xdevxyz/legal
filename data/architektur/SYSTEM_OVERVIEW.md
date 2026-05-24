# Complyo – System-Übersicht (Master-Referenz)

> **Zweck:** Kompakter Einstiegspunkt für jede neue Entwicklungssession.  
> **Letzte Aktualisierung:** 2026-04-10  
> **Version:** 2.2.0  
> **Status:** Production (Live auf complyo.de / complyo.tech)

---

## Inhaltsverzeichnis

1. [Was ist Complyo?](#1-was-ist-complyo)
2. [Technologie-Stack](#2-technologie-stack)
3. [Infrastruktur & Domains](#3-infrastruktur--domains)
4. [Verzeichnisstruktur](#4-verzeichnisstruktur)
5. [Backend – FastAPI](#5-backend--fastapi)
6. [Frontend Dashboard – Next.js](#6-frontend-dashboard--nextjs)
7. [Frontend Landing – Next.js](#7-frontend-landing--nextjs)
8. [Datenbank – PostgreSQL](#8-datenbank--postgresql)
9. [Widgets (JS)](#9-widgets-js)
10. [Das 4-Säulen-Compliance-System](#10-das-4-säulen-compliance-system)
11. [KI-Fix-Engine (Unified Fix Engine)](#11-ki-fix-engine-unified-fix-engine)
12. [Kritische Datenpfade](#12-kritische-datenpfade)
13. [Umgebungsvariablen](#13-umgebungsvariablen)
14. [Preismodell & Pläne](#14-preismodell--pläne)
15. [Wichtige Einzeldokumente](#15-wichtige-einzeldokumente)

---

## 1. Was ist Complyo?

KI-gestützte SaaS-Plattform zur automatischen Website-Compliance-Prüfung nach deutschem/europäischem Recht.

**Kernfunktionen:**
- Automatischer Website-Scan (4 Compliance-Säulen)
- KI-generierte Code-Fixes, Rechtstexte und Schritt-für-Schritt-Guides
- Cookie-Banner-Generator (DSGVO/TTDSG-konform)
- Accessibility-Widget (WCAG 2.1 AA / BFSG)
- Legal-News-Feed (KI-klassifiziert)
- eRecht24-Integration (anwaltlich geprüfte Rechtstexte)
- Deployment-Engine (FTP, SFTP, GitHub PR, Netlify, Vercel, WordPress, ZIP)

**Zielgruppe:** KMU, Shops, Agenturen ohne Rechts- oder Techexpertise.

---

## 2. Technologie-Stack

| Layer | Technologie |
|-------|------------|
| Backend | FastAPI (Python 3.11+), asyncpg, asyncio |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Datenbank | PostgreSQL 15, raw asyncpg (kein ORM) |
| Cache / Queue | Redis 7 |
| KI | OpenRouter API → Claude 3.5 Sonnet (primär), GPT-4 (Fallback) |
| Auth | Firebase Auth + JWT (PyJWT) |
| Payment | Stripe (Subscriptions + Webhooks) |
| Rechtstexte | eRecht24 API + Webhook |
| Scanner | Playwright (Headless Chromium) |
| Infrastruktur | Docker Compose, NGINX Gateway, Let's Encrypt |
| Monitoring | Sentry, Prometheus/Grafana (optional) |

---

## 3. Infrastruktur & Domains

| Service | Domain | Interner Port |
|---------|--------|--------------|
| Landing Page | complyo.de / complyo.tech | 3003 |
| Dashboard | app.complyo.de | 3001 |
| Backend API | api.complyo.de | 8002 |
| PostgreSQL | intern | 5433 (host-mapped) |
| Redis | intern | 6380 (host-mapped) |
| Admin Panel | intern | 3004 |

NGINX Gateway (proxy-network) leitet alle Domains auf die jeweiligen Container.  
SSL via Let's Encrypt / Certbot (automatische Erneuerung).

---

## 4. Verzeichnisstruktur

```
saas/legal/
├── backend/                    # FastAPI Backend (api.complyo.de)
│   ├── ai_fix_engine/          # KI-Fix-Engine (Unified Fix Engine)
│   │   ├── handlers/           # Fix-Handler je Typ
│   │   ├── unified_fix_engine.py
│   │   ├── prompts_v2.py       # Prompt-Templates & JSON-Schemas
│   │   └── validators.py       # Fix-Validierung
│   ├── compliance_engine/      # Scanner, Checks, Code-Generierung
│   │   ├── checks/             # 4-Säulen-Checks (je eine Datei)
│   │   ├── scanner.py          # Standard-Scanner (30–60s)
│   │   ├── deep_scanner.py     # Deep-Scanner (60–120s)
│   │   ├── quick_scanner.py    # Quick-Scanner (10–20s)
│   │   └── deployment_engine.py
│   ├── widgets/                # JS-Widgets (direkt ausgeliefert)
│   ├── migrations/             # SQL-Migrationsskripte
│   ├── tests/                  # pytest-Tests
│   ├── main_production.py      # FastAPI Entry-Point (alle Router)
│   ├── database_service.py     # DB-Pool & Queries
│   ├── auth_service.py         # JWT + Session-Management
│   └── requirements.txt
├── dashboard-react/            # Next.js Dashboard (app.complyo.de)
│   └── src/
│       ├── app/                # Next.js App Router Pages
│       ├── components/         # React-Komponenten
│       ├── contexts/           # AuthContext, ThemeContext
│       ├── hooks/              # useAuth, useCompliance, useMetrics
│       ├── lib/                # api.ts, api-utils.ts, firebase.ts
│       ├── stores/             # Zustand-Store (dashboard.ts)
│       └── types/              # TypeScript-Typen
├── landing-react/              # Next.js Landing (complyo.de)
├── gateway/                    # NGINX-Konfiguration
├── docs/                       # Technische Dokumentation (hier)
├── md/                         # Weitere Projektdokumente
├── scripts/                    # Deploy- & Wartungsskripte
└── docker-compose.yml
```

---

## 5. Backend – FastAPI

### Entry-Point

`backend/main_production.py` – registriert alle Router, startet Background-Worker, initialisiert Services.

### Alle registrierten Router (Reihenfolge aus main_production.py)

| Router-Import | Präfix / Notiz |
|---------------|---------------|
| `public_router` | `/api` – Öffentliche Analyse (kein Auth) |
| `lead_router` | `/api/leads` |
| `admin_router` | `/api/admin` |
| `gdpr_router` | `/api/gdpr` – Art. 17 & 20 |
| `i18n_router` | `/api/i18n` |
| `legal_news_router` | `/api/legal` |
| `fix_router` | `/api/v2/fixes` |
| `website_router` | `/api/v2/websites` |
| `dashboard_router` | `/api/v2/dashboard` |
| `auth_routes.router` | `/api/auth` |
| `payment_routes.router` | `/api/payment` |
| `stripe_routes.router` | `/api/stripe` – Freemium |
| `user_routes.router` | `/api/user` |
| `erecht24_webhook_router` | `/webhooks/erecht24` |
| `erecht24_v2_router` | `/api/v2` |
| `ai_compliance_router` | `/api/ai` – EU AI Act |
| `addon_payment_router` | `/api/addons` |
| `widget_router` | `/api/widgets` |
| `expert_service_router` | `/api/expert-service` |
| `cookie_compliance_router` | `/api/cookies` |
| `ab_test_router` | `/api/ab-tests` |
| `tcf_router` | `/api/tcf` – conditional import |
| `legal_change_router` | `/api/legal-changes` |
| `ai_legal_router` | `/api/legal-ai` |
| `legal_notification_router` | `/api/legal-notifications` |
| `accessibility_fix_router` | `/api/v2/accessibility` |
| `git_router` | `/api/v2/git` |
| `alt_text_router` | `/api/accessibility` |

### Kern-Services

| Service | Datei | Beschreibung |
|---------|-------|-------------|
| `db_service` | `database_service.py` | asyncpg-Pool, alle DB-Abfragen |
| `auth_service` | `auth_service.py` | JWT erstellen/prüfen, Sessions |
| `email_service` | `email_service.py` | SMTP-Versand |
| `erecht24_service` | `erecht24_service.py` | eRecht24 REST-API |
| `erecht24_rechtstexte_service` | `erecht24_rechtstexte_service.py` | Rechtstexte-SDK |
| `export_service` | `export_service.py` | PDF/HTML-Export |
| `news_service` | `news_service.py` | RSS-Feed-Parser |
| `cookie_scanner_service` | `cookie_scanner_service.py` | Cookie-Erkennung (40+ Services) |
| `gdpr_retention_service` | `gdpr_retention_service.py` | Automatische Datenlöschung |
| `i18n_service` | `i18n_service.py` | Übersetzungen (DE/EN) |
| `ai_solution_cache_service` | `ai_solution_cache_service.py` | KI-Antworten cachen (70–85% Reduktion) |

### KI-Services

| Service | Datei | Beschreibung |
|---------|-------|-------------|
| `AIActAnalyzer` | `ai_act_analyzer.py` | EU AI Act Risiko-Klassifizierung |
| `AIActDocGenerator` | `ai_act_doc_generator.py` | AI Act Dokumenten-Generator |
| `AIDocumentGenerator` | `ai_document_generator.py` | Impressum/Datenschutz generieren |
| `AIFeedbackLearning` | `ai_feedback_learning.py` | Lern-Loop aus User-Feedback |
| `AILegalClassifier` | `ai_legal_classifier.py` | Gesetzesänderungs-Klassifizierung |

### Compliance Engine – Scanner

| Scanner | Datei | Dauer | Wann |
|---------|-------|-------|------|
| QuickScanner | `quick_scanner.py` | 10–20 s | Schnellcheck |
| BaseScanner | `scanner.py` | 30–60 s | Standard |
| DeepScanner | `deep_scanner.py` | 60–120 s | Vollanalyse |

### Compliance Engine – Checks (`checks/`)

| Datei | Prüft |
|-------|-------|
| `barrierefreiheit_check.py` | WCAG 2.1, BFSG, Widget-Erkennung |
| `impressum_check.py` | TMG §5 Pflichtangaben |
| `datenschutz_check.py` | DSGVO Art. 13/14 |
| `cookie_check.py` | TTDSG §25, Banner-Erkennung |
| `tcf_check.py` | IAB TCF 2.2 |
| `aria_checker.py` | ARIA-Rollen, Properties, States |
| `media_accessibility_check.py` | Video/Audio-Untertitel |
| `deep_content_analyzer.py` | KI-basierter Multi-Layer-Parser |

### `ComplianceIssue` Datenmodell (Python)

```python
@dataclass
class ComplianceIssue:
    category: str        # "barrierefreiheit" | "cookies" | "impressum" | "datenschutz"
    severity: str        # "critical" | "warning" | "info"
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool
    is_missing: bool
    # Optional:
    screenshot_url, element_html, fix_code, suggested_alt, image_src, metadata
```

---

## 6. Frontend Dashboard – Next.js

**URL:** `app.complyo.de` | **Framework:** Next.js 14 App Router | **Pfad:** `dashboard-react/`

### Pages (`src/app/`)

| Route | Funktion |
|-------|---------|
| `/` | Haupt-Dashboard (DomainHeroSection + WebsiteAnalysis + LegalNews + CookieWidget) |
| `/login` | Login |
| `/register` | Registrierung |
| `/profile` | Benutzerprofil |
| `/subscription` | Abo-Verwaltung |
| `/cookie-compliance` | Cookie-Banner-Konfiguration |
| `/journey` | Guided Compliance Journey |
| `/privacy` | Datenschutz-Einstellungen |
| `/ai-compliance` | EU AI Act Modul |
| `/ai-compliance/systems/new` | KI-System registrieren |
| `/ai-compliance/systems/[id]` | KI-System Details |
| `/ai-compliance/upgrade` | AI Guard Add-on |

### Haupt-Komponenten (`src/components/dashboard/`)

| Komponente | Funktion |
|------------|---------|
| `DashboardHeader.tsx` | Navigation, User-Menu, Theme-Toggle |
| `DomainHeroSection.tsx` | URL-Eingabe, Score-Anzeige, KI-CTA |
| `WebsiteAnalysis.tsx` | Compliance-Issues, Fix-Buttons |
| `LegalNews.tsx` | Rechtliche Neuigkeiten |
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
| `OptimizationQuickNav.tsx` | Schnell-Navigation |

### State Management

| Datei | Typ | Zweck |
|-------|-----|-------|
| `contexts/AuthContext.tsx` | React Context | User-Session, JWT-Tokens |
| `contexts/ThemeContext.tsx` | React Context | Dark/Light Mode |
| `stores/dashboard.ts` | Zustand | Scan-Daten, Website-State |

### Hooks

| Hook | Datei | Zweck |
|------|-------|-------|
| `useAuth` | `hooks/useAuth.ts` | Auth-Context-Wrapper |
| `useCompliance` | `hooks/useCompliance.ts` | Scan-Status, Issues |
| `useMetrics` | `hooks/useMetrics.ts` | Dashboard-Metriken |
| `useDashboardInitialization` | `hooks/useDashboardInitialization.ts` | Initial-Daten laden |

### API-Client (`src/lib/api.ts`)

- Axios-Client mit `baseURL = NEXT_PUBLIC_API_URL`
- Request-Interceptor: JWT aus `localStorage.access_token`
- Response-Interceptor: Token-Refresh bei 401, Retry bei Netzwerkfehler, Auto-Logout
- URL-Normalisierung vor jedem Scan-Request

### TypeScript-Typen

`src/types/api.ts`:
- `ComplianceIssue` – einzelnes Issue
- `IssueGroup` – Gruppe verwandter Issues
- `ComplianceAnalysis` – vollständige Scan-Antwort
- `FixResult` – KI-Fix-Ergebnis
- `UserLimits` – Plan-Limits
- `TCFData` – IAB TCF 2.2 Daten

`src/types/dashboard.ts`:
- `DashboardState`, `Website`, `User`, `DashboardMetrics`

---

## 7. Frontend Landing – Next.js

**URL:** `complyo.de` | **Pfad:** `landing-react/`

### Pages

| Route | Funktion |
|-------|---------|
| `/` | Landing (A/B-Test zwischen Varianten) |
| `/agb` | AGB |
| `/datenschutz` | Datenschutzerklärung |
| `/impressum` | Impressum |
| `/gdpr` | GDPR-Info |
| `/admin` | Admin-Panel (geschützt) |

### Landing-Varianten (A/B-Test)

- `ComplyoOriginalLanding.tsx`
- `ComplyoModernLanding.tsx`
- `ComplyoHighConversionLanding.tsx`
- `ComplyoViralLanding.tsx`
- `AlfimaLanding.tsx`
- `ProfessionalLanding.tsx`

---

## 8. Datenbank – PostgreSQL

**System:** PostgreSQL 15 | **Zugriff:** raw asyncpg (kein ORM)  
**Migrations:** SQL-Dateien in `backend/migrations/`

### Kern-Tabellen

| Tabelle | Beschreibung |
|---------|-------------|
| `users` | User-Account, Subscription, Login |
| `user_sessions` | Refresh-Tokens |
| `user_limits` | Plan-Typ, Fix-Kontingent, Website-Limit |
| `websites` | Tracking-Websites |
| `tracked_websites` | Alternative (Kompatibilität) |
| `scans` | Scan-Ergebnisse (JSONB) |
| `scan_history` | Scan-Verlauf |
| `fix_jobs` | Asynchrone Fix-Jobs |
| `generated_fixes` | Generierte Fixes (Audit) |
| `fix_application_audit` | Deployment-Audit-Trail |
| `fix_backups` | Backup vor Deployment |
| `legal_news` | Rechtliche Neuigkeiten |
| `rss_feed_sources` | RSS-Feed-Quellen |
| `cookie_configs` | Cookie-Banner-Konfigurationen |
| `consent_logs` | DSGVO-Consent-Logs (3 Jahre) |
| `ab_tests` | A/B-Test-Definitionen |
| `ai_solution_cache` | Gecachte KI-Antworten |
| `legal_updates` | Gesetzesänderungen (klassifiziert) |
| `staging_deployments` | Preview-Deployments |

---

## 9. Widgets (JS)

**Pfad:** `backend/widgets/`  
Werden direkt über `widget_routes.py` ausgeliefert.

| Widget | Datei | Status |
|--------|-------|--------|
| Accessibility Widget v6 | `accessibility-v6.js` | **AKTIV** |
| Cookie Banner v2 | `cookie_banner_v2.js` | **AKTIV** |
| Content Blocker | `content_blocker.js` | AKTIV |
| Accessibility Widget v5 | `accessibility-v5.js` | Legacy |
| Accessibility Smart | `accessibility_smart.js` | Legacy |

**Accessibility Widget v6:** Grid-Layout, 30+ Features, Multi-Language (17 Sprachen), WCAG 2.1 AA  
**Cookie Banner v2:** DSGVO/TTDSG-konform, 3 Layouts, 17 Sprachen, IAB TCF 2.2, Consent-Logging

---

## 10. Das 4-Säulen-Compliance-System

| Säule | Rechtsgrundlage | Max. Bußgeld | Auto-Fix-Rate |
|-------|----------------|-------------|--------------|
| **Barrierefreiheit** | BFSG / WCAG 2.1 (seit 28.06.2025) | 100.000 € | ~60 % |
| **Cookie-Compliance** | TTDSG §25 / DSGVO | 300.000 € / 20 Mio. € | ~90 % |
| **Rechtstexte** | TMG §5 Impressum / RStV §55 | 50.000 € + Abmahnungen | ~70 % |
| **DSGVO** | DSGVO Art. 13/14 | 20 Mio. € / 4 % Umsatz | ~75 % |

### Säule 1 – Barrierefreiheit (WCAG 2.1 / BFSG)

| ID | Prüfpunkt | Auto-Fix |
|----|-----------|---------|
| 1.1 | Accessibility-Widget | Ja |
| 1.2 | Alt-Texte für Bilder (SC 1.1.1) | KI-gestützt |
| 1.3 | Farbkontraste (SC 1.4.3) min. 4.5:1 | Ja (CSS) |
| 1.4 | Tastaturbedienung (SC 2.1.1) | Eingeschränkt |
| 1.5 | Focus-Sichtbarkeit (SC 2.4.7) | Ja (`:focus-visible`) |
| 1.6 | ARIA-Labels (SC 4.1.2) | Eingeschränkt |
| 1.7 | Semantisches HTML5 (SC 1.3.1) | Nein |
| 1.8 | Screenreader-Kompatibilität | Teilweise |

### Säule 2 – Cookie-Compliance

| ID | Prüfpunkt | Auto-Fix |
|----|-----------|---------|
| 2.1 | Cookie-Consent-Banner vorhanden | Ja |
| 2.2 | Opt-In Mechanismus | Ja |
| 2.3 | Ablehnungsmöglichkeit | Ja |
| 2.4 | Cookie-Informationspflicht | Teilweise |
| 2.5 | Widerrufsmöglichkeit | Ja |
| 2.6 | Consent-Logs (Nachweis) | Ja |
| 2.7 | Kein Tracking ohne Consent | Ja |

### Säule 3 – Rechtstexte (Impressum)

| ID | Prüfpunkt | Auto-Fix |
|----|-----------|---------|
| 3.1 | Impressum-Link vorhanden | Ja |
| 3.2 | Firmenname / Name | Teilweise |
| 3.3 | Postanschrift | Teilweise |
| 3.4 | E-Mail & Telefon | Teilweise |
| 3.5 | Handelsregister | Nein |
| 3.6 | USt-ID | Nein |
| 3.7 | Verantwortlicher (RStV §55) | Teilweise |

### Säule 4 – DSGVO

| ID | Prüfpunkt | Auto-Fix |
|----|-----------|---------|
| 4.1 | Datenschutzerklärung vorhanden & verlinkt | Ja |
| 4.2 | Verantwortlicher mit Kontakt | Teilweise |
| 4.3 | Zwecke der Datenverarbeitung | KI-gestützt |
| 4.4 | Rechtsgrundlagen (Art. 6 DSGVO) | KI-gestützt |
| 4.5 | Speicherdauer | KI-gestützt |
| 4.6 | Betroffenenrechte | KI-gestützt |
| 4.7 | Beschwerderecht Aufsichtsbehörde | KI-gestützt |
| 4.8 | Datenschutzbeauftragter (falls nötig) | Nein |

---

## 11. KI-Fix-Engine (Unified Fix Engine)

**Pfad:** `backend/ai_fix_engine/`  
**Entry-Point:** `unified_fix_engine.py` → `UnifiedFixEngine`

### Flow

```
API-Request (fix_routes.py)
    ↓
UnifiedFixEngine.generate_fix(issue, context)
    ↓
Fix-Typ bestimmen (CODE | TEXT | WIDGET | GUIDE)
    ↓
Handler auswählen
    ↓
PromptBuilder.build_prompt() → AI-Call (OpenRouter)
    ↓ (Retry 3x, Fallback Claude → GPT-4 → Template)
Response parsen & validieren (FixValidator)
    ↓
FixResult zurückgeben
```

### Handler

| Handler | Datei | Zuständigkeit |
|---------|-------|--------------|
| `LegalTextHandler` | `handlers/legal_text_handler.py` | Impressum, Datenschutz, AGB |
| `CookieBannerHandler` | `handlers/cookie_handler.py` | Cookie-Consent, TTDSG §25 |
| `AccessibilityHandler` | `handlers/accessibility_handler.py` | WCAG 2.1, Alt-Texte, ARIA |
| `CodeFixHandler` | `handlers/code_handler.py` | HTML/CSS/JS/PHP Fixes |
| `GuideHandler` | `handlers/guide_handler.py` | Schritt-für-Schritt-Guides |

### Fix-Typen & Ausgabeformate

| Typ | Ausgabe |
|-----|---------|
| `CODE` | HTML/CSS/JS-Snippet, direkt einbaubar |
| `TEXT` | Rechtstext (Impressum, Datenschutz, AGB) als HTML |
| `GUIDE` | Schritt-für-Schritt-Anleitung (mit CMS-Auswahl) |
| `WIDGET` | Widget-Einbindungs-Code + Konfiguration |

### KI-Modelle (via OpenRouter)

| Modell | Rolle |
|--------|-------|
| `anthropic/claude-3.5-sonnet` | Primär |
| `openai/gpt-4` | Fallback |
| `openai/gpt-4-turbo` | Fallback 2 |
| Template | Letzter Fallback (kein AI-Call) |

### `FixResult` Datenmodell

```python
@dataclass
class FixResult:
    fix_id: str
    fix_type: str
    status: str          # "success" | "partial" | "failed"
    data: Dict[str, Any]
    validation_result: Optional[ValidationResult]
    metadata: Dict[str, Any]
    generated_at: str
    ai_model_used: str
    generation_time_ms: int
    fallback_used: bool
```

### Deployment-Methoden

1. FTP Upload (automatisches Backup + Rollback)
2. SFTP/SSH (Premium)
3. GitHub Pull Request (Branch: `complyo-fix-{id}`)
4. Netlify Deployment
5. Vercel Deployment
6. WordPress REST API
7. ZIP-Download (manuell)

---

## 12. Kritische Datenpfade

### Scan-Flow

```
POST /api/analyze (public_routes.py)
  → QuickScanner.scan()
    → checks/* parallel (asyncio.gather)
      → barrierefreiheit_check
      → cookie_check
      → impressum_check
      → datenschutz_check
    → issue_grouper.group_issues()
    → ComplianceAnalysis zurückgeben
```

### Fix-Flow

```
POST /api/v2/fixes/generate (fix_routes.py)
  → Limit-Check (user_limits Tabelle)
  → UnifiedFixEngine.generate_fix(issue, context)
    → Handler auswählen
    → AI-Call (OpenRouter, 3 Retry)
    → FixValidator.validate()
  → Fix in generated_fixes speichern
  → FixResult zurückgeben
```

### Auth-Flow

```
POST /api/auth/login (auth_routes.py)
  → AuthService.authenticate()
    → DB: users Tabelle prüfen (bcrypt)
    → JWT erstellen (15 min)
    → Refresh-Token erstellen (30 Tage)
    → user_sessions speichern
  → access_token + refresh_token zurückgeben

POST /api/auth/refresh
  → Refresh-Token in user_sessions prüfen
  → Neues JWT ausstellen
```

### Cookie-Banner-Flow

```
Widget-Load (cookie_banner_v2.js)
  → Consent-Status prüfen (localStorage)
  → Falls kein Consent: Banner anzeigen
  → User-Auswahl → consent_logs speichern (POST /api/cookies/consent)
  → content_blocker.js blockiert Scripts bis Consent
```

---

## 13. Umgebungsvariablen

```env
# Datenbank
DATABASE_URL=postgresql://complyo_user:PASSWORD@postgres:5432/complyo_db

# KI
OPENROUTER_API_KEY=sk-or-...

# eRecht24
ERECHT24_API_KEY=...
ERECHT24_API_URL=https://api.e-recht24.de

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_SINGLE_MODULE=price_...
STRIPE_PRICE_COMPLETE=price_...
STRIPE_PRICE_EXPERT_MONTHLY=price_...

# Auth
JWT_SECRET=...
FIREBASE_PROJECT_ID=...
FIREBASE_PRIVATE_KEY=...
FIREBASE_CLIENT_EMAIL=...

# Redis
REDIS_PASSWORD=...

# E-Mail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SENDER_EMAIL=noreply@complyo.de

# Feature-Flags
UNLIMITED_FIXES=false
BYPASS_PAYMENT=false
ENVIRONMENT=production

# Monitoring
SENTRY_DSN=...
METRICS_TOKEN=...
```

---

## 14. Preismodell & Pläne

| Plan | Preis | Enthält |
|------|-------|---------|
| **AI Plan** | 39 €/Monat | 1 Website, unbegrenzte Scans, KI-Fixes, Self-Service |
| **Expert Plan** | 39 €/Monat + 2.000 € Setup | AI-Features + direkte Implementierung durch Complyo |
| **Individuell** | auf Anfrage | Agentur, Multi-Site, White-Label |

**Stripe-Pläne (intern):**
- `STRIPE_PRICE_SINGLE_MODULE` – Einzelmodul (19 €)
- `STRIPE_PRICE_COMPLETE` – Komplett (49 €)
- `STRIPE_PRICE_EXPERT_MONTHLY` – Expert (39 €/Monat)

---

## 15. Wichtige Einzeldokumente

| Dokument | Pfad | Inhalt |
|----------|------|--------|
| Codebase-Handbuch | `CODEBASE_HANDBUCH.md` | Detailliertes Handbuch (Stand 2026-02-07) |
| Architektur Fix-Engine | `docs/ARCHITEKTUR-FIX-ENGINE.md` | Scanner + Fixer Architektur |
| 4-Säulen-System | `docs/4-SAEULEN-SYSTEM.md` | Alle Prüfpunkte mit Bußgeldern |
| Plattform-Übersicht | `md/PLATTFORM_UEBERSICHT.md` | Executive Summary |
| Roadmap | `md/ROADMAP.md` | Backlog & geplante Features |
| Features Komplett | `md/COMPLYO_FEATURES_COMPLETE.md` | Alle implementierten Features |
| DB Migrations | `docs/DATABASE_MIGRATIONS.md` | Migrations-Prozess |
| Env Config | `docs/ENV_CONFIGURATION.md` | Alle Env-Variablen |
| Technical Debt | `docs/TECHNICAL_DEBT.md` | Bekannte Schulden |
| Legal-Update-Integration | `docs/LEGAL-UPDATE-INTEGRATION.md` | Legal-Change-Monitoring |
| Deployment Guide | `md/DEPLOYMENT_GUIDE.md` | Produktions-Deployment |
| SSL Fix 2026 | `md/SSL_FIX_2026.md` | SSL-Erneuerungs-Fix |
