# Complyo – Feature-Liste

Stand: 2026-05-24  
Basis: Codebase-Analyse + Docs (md/, data/, backend/, dashboard-react/)

---

# Website Scanner

## Zweck
Analysiert eine Website auf Compliance-Verstöße in den vier Säulen (Barrierefreiheit, Cookies, Rechtstexte, DSGVO). Kern-Feature der gesamten Plattform.

## Nutzer
Alle zahlenden Nutzer und Landing-Demo-Besucher.

## Status
Aktiv

## Abhängigkeiten
`scanner.py`, `quick_scanner.py`, `deep_scanner.py`, `browser_renderer.py`, alle `checks/`-Module, `score_calculator.py`, `public_routes.py`, `main_production.py`

## Probleme
- `scan_duration_ms` wird als Float zurückgegeben, DB-Spalte erwartet Integer → 500-Fehler bei `/api/v2/analyze`
- Response-Shape ist `{ success, data }`, Frontend erwartet teilweise direkte Felder → `issue_groups` fehlt im State
- `int(current_user["id"])` schlägt fehl wenn JWT eine UUID/String-ID enthält → 500

## Verbesserungsideen
- `scan_duration_ms` immer als `int(...)` casten vor DB-Insert
- Response-Shape vereinheitlichen oder Frontend-Store anpassen
- User-ID-Typing durchgängig klären (UUID vs. Integer)

---

# Compliance Score & Risk Calculation

## Zweck
Berechnet einen 0–100 Score aus allen gefundenen Issues. Weist jedem Issue einen Euro-Risikowert zu, damit Nutzer Priorisierung nachvollziehen können.

## Nutzer
Alle Nutzer; sichtbar auf dem Dashboard als Gauge + MetricsCards.

## Status
Aktiv

## Abhängigkeiten
`score_calculator.py`, `risk_calculator.py`, `priority_engine.py`, `ComplianceGauge.tsx`, `MetricsCards.tsx`, `dashboard_routes.py`

## Probleme
- Score-Volatility-Bug wurde laut Docs behoben und deployed
- Score zeigt `0/100` für neu angelegte Sites (expected state, kein Render-Fehler)

## Verbesserungsideen
- Score-Verlauf (Score History) prominenter im Dashboard platzieren
- Branchen-Benchmark-Vergleich vollständig implementieren (aktuell nur in Docs erwähnt)

---

# Barrierefreiheits-Check (WCAG / BFSG)

## Zweck
Prüft Alt-Texte, Kontraste, Keyboard-Navigation, ARIA-Labels, Semantic HTML, Screenreader-Kompatibilität, Focus-Indikatoren. Pflicht ab BFSG 2025.

## Nutzer
Alle Nutzer.

## Status
Aktiv

## Abhängigkeiten
`barrierefreiheit_check.py`, `contrast_analyzer.py`, `aria_checker.py`, `media_accessibility_check.py`, `accessibility_fix_routes.py`, `alt_text_routes.py`

## Probleme
- Touch-Target-Checker, WCAG-AAA-Checks, Table/SVG/Canvas-A11y noch nicht implementiert (in Docs als offen markiert)
- ARIA-Label-Fixes können generische Labels erzeugen, die manuellen Review erfordern

## Verbesserungsideen
- Fehlende WCAG-Checks als eigene Check-Module nachziehen
- ARIA-Label-Qualität durch bessere Kontextextraktion verbessern

---

# KI-generierte Alt-Texte

## Zweck
Erzeugt automatisch beschreibende Alt-Texte für Bilder ohne oder mit generischem Alt-Attribut, via GPT-4 Vision / OpenRouter.

## Nutzer
Alle Nutzer mit Barrierefreiheits-Modul.

## Status
Aktiv

## Abhängigkeiten
`alt_text_routes.py`, `ai_fix_engine/handlers/accessibility_handler.py`, `AltTextReviewQueue.tsx`, OpenRouter-API-Key

## Probleme
- Ohne `OPENROUTER_API_KEY` werden Platzhalter-Texte generiert statt echter Beschreibungen
- Review-Queue-Komponente vorhanden, aber Qualität der KI-Ausgaben variiert

## Verbesserungsideen
- Confidence-Score je Alt-Text anzeigen
- Batch-Processing für große Bildmengen

---

# Cookie Compliance Modul

## Zweck
Cookie-Banner-Verwaltung, Consent-Logging, Google Consent Mode v2, TCF 2.2, A/B-Testing, Consent-Statistiken.

## Nutzer
Alle Nutzer.

## Status
Aktiv (nach Phase-1-Fixes)

## Abhängigkeiten
`cookie_compliance_routes.py`, `cookie_scanner_service.py`, `cookie_analyzer.py`, `checks/cookie_check.py`, `cookie_banner_v2.js`, `ConsentStatistics.tsx`, `CookieBannerDesigner.tsx`, `ServiceManager.tsx`, DB-Tabellen `cookie_configs`, `consent_logs`, `cookie_compliance_stats`

## Probleme
- `cookie_check.py` erkennt nur Banner-Vorhandensein, nicht Tracking-Code (Google Analytics, Facebook Pixel, Matomo) ohne Banner
- `cookie_compliance_routes.py` Zeile 351: `TODO: Get user_id from session/auth` → unvollständige Authentifizierung
- Frühere 500-Fehler auf `/tcf/vendors`, `/policy/{site}`, `/stats/{site}` wurden behoben
- TCF 2.2: keine offizielle CMP-ID, kein vollständiger TC-String-Generator

## Verbesserungsideen
- Tracking-Code-Erkennung in `cookie_check.py` erweitern (Script-URL-Pattern-Matching)
- Auth-TODO in Route beheben
- TCF-Registrierung bei IAB anstoßen (siehe `TODO_TCF_REGISTRIERUNG.md`)

---

# Deep Cookie Scanner

## Zweck
Premium-Feature für tiefergehende Erkennung von Cookies, Tracking-Scripts und Third-Party-Diensten mit Playwright-Rendering.

## Nutzer
Premium-Nutzer.

## Status
Aktiv

## Abhängigkeiten
`deep_cookie_scanner_routes.py`, `compliance_engine/deep_cookie_scanner.py`, Plan-Check via `subscriptions`-Tabelle

## Probleme
- Plan-Check erwartet `user_id: int`, möglicherweise inkompatibel mit UUID-basierten User-IDs

## Verbesserungsideen
- Ergebnis-Export als CSV/JSON
- Scheduling für regelmäßige Deep-Scans

---

# Cookie Banner Widget (v2)

## Zweck
DSGVO/TTDSG-konformes Cookie Banner mit 3 Layouts, 17 Sprachen, TCF-Support, Google Consent Mode. Wird per Script-Tag eingebunden.

## Nutzer
Endnutzer der Kunden-Websites.

## Status
Aktiv

## Abhängigkeiten
`widgets/cookie_banner_v2.js`, `widget_routes.py`, Cookie-Config aus DB, Consent-Endpoint

## Probleme
- Legacy-Widget `cookie_consent.legacy.js` noch im Codebase, aber deprecated

## Verbesserungsideen
- Cookie-Banner-Designer um mehr Layout-Vorlagen erweitern
- Accessibility-Widget und Cookie-Banner kombiniert als Single-Script anbieten

---

# Accessibility Widget (v6)

## Zweck
JS-Widget mit 30+ Accessibility-Features (Schriftgröße, Kontrast, Lesemodus, Keyboard-Navigation, etc.). Einbindung per Script-Tag auf Kunden-Seiten.

## Nutzer
Endnutzer der Kunden-Websites.

## Status
Aktiv

## Abhängigkeiten
`widgets/accessibility-v6.js`, `widget_routes.py`, `widget_manager.py`

## Probleme
- `widget_routes.py` Zeile 462: `TODO: Add auth` für Widget-Management-Endpoint
- Widget-Analytics werden nicht in DB gespeichert (Zeile 178)
- Usage-Count wird nicht aus DB geladen (Zeile 261)
- Fixes werden nicht aus DB geladen (Zeile 479)
- v5 noch aktiv als Legacy-Fallback

## Verbesserungsideen
- Auth für Widget-Management-Endpoints implementieren
- Analytics-Persistierung nachholen
- v4/v5-Widgets formal deprecaten und aus Serving entfernen

---

# KI Fix Engine

## Zweck
Generiert automatisch Code-Fixes (HTML/CSS/JS/PHP), Guides und Rechtstexte für erkannte Compliance-Issues. Orchestriert via Unified Fix Engine mit Handler-System.

## Nutzer
Alle Nutzer ab AI-Plan.

## Status
Aktiv

## Abhängigkeiten
`ai_fix_engine/unified_fix_engine.py`, `smart_fix_generator.py`, alle `handlers/`, `fix_quality_gate.py`, `validators.py`, `prompts_v2.py`, `fix_routes.py`, OpenRouter-API-Key, `ai_solution_cache_service.py`

## Probleme
- Ohne `OPENROUTER_API_KEY` werden Platzhalter-Fixes generiert (`[PLATZHALTER_ERSETZEN]`)
- LiveValidator TODO in `main_production.py` noch nicht implementiert
- `fix_generator.py` (Legacy) noch aktiv neben neuem Unified Engine
- `enhanced_fix_routes.py` existiert, ist aber nicht in `main_production.py` eingebunden

## Verbesserungsideen
- LiveValidator fertigstellen
- Legacy `fix_generator.py` entfernen sobald Unified Engine vollständig stabil
- `enhanced_fix_routes.py` entweder einbinden oder löschen

---

# Fix Anwenden / Deployment Engine

## Zweck
Deployed generierte Fixes direkt via FTP, SFTP, GitHub PR, Netlify, Vercel, WordPress REST oder als ZIP-Download. Mit Backup vor Deployment und Rollback-Möglichkeit.

## Nutzer
Alle Nutzer; Premium für SFTP/GitHub/Netlify/Vercel/WordPress.

## Status
Aktiv (Basis); In Entwicklung (Staging Preview, Screenshot Diff)

## Abhängigkeiten
`fix_apply_routes.py`, `compliance_engine/deployment_engine.py`, `compliance_engine/github_integration.py`, `git_routes.py`, `audit_service.py`, `ApplyFixModal.tsx`

## Probleme
- Staging-Preview-Feature: TODO in `fix_apply_routes.py` Zeile 348
- Background-Task-Tracking: TODO in `fix_apply_routes.py` Zeile 381
- Screenshot-Diff: in Entwicklung, Playwright + pixelmatch benötigt
- Git OAuth-State wird In-Memory gespeichert (bricht bei mehreren Workern / Restart)

## Verbesserungsideen
- OAuth-State in Redis persistieren
- Staging-Preview und Screenshot-Diff fertigstellen
- Background-Task-Status im Dashboard anzeigen

---

# Rechtstext Generator

## Zweck
Generiert Impressum, Datenschutzerklärung, AGB, Widerrufsbelehrung, Cookie-Richtlinie, DPA/AVV. Ersetzt die entfernte eRecht24-Integration.

## Nutzer
Alle Nutzer.

## Status
Aktiv

## Abhängigkeiten
`legal_text_generator.py`, `legal_text_routes.py`, `legal_document_routes.py`, `ai_fix_engine/handlers/legal_text_handler.py`, `LegalDocumentGenerator.tsx`, `LegalTextWizard.tsx`, OpenRouter-API-Key

## Probleme
- Interne KI-Texte sind nicht anwaltlich geprüft (eRecht24 wurde entfernt) → rechtliche Qualität unklar
- eRecht24-Migration läuft noch aus alten DB-Einträgen; einige Docs verweisen noch auf alte Endpunkte
- `LegalDocumentGenerator.tsx` Status unklar (neue Komponente, wenig Docs)

## Verbesserungsideen
- KI-generierte Rechtstexte mit Haftungshinweis und Empfehlung zum Anwalt versehen
- Versionierung/Archiv aller generierten Dokumente ausbauen
- Textvorlagen regelmäßig gegen aktuelle Rechtslage prüfen

---

# Legal Change Monitoring

## Zweck
Überwacht Gesetzesänderungen (DSGVO, BFSG, NIS2 etc.), klassifiziert Relevanz/Dringlichkeit per KI, benachrichtigt Nutzer und empfiehlt Handlungen.

## Nutzer
Alle Nutzer.

## Status
Aktiv; teilweise buggy

## Abhängigkeiten
`legal_change_monitor.py`, `legal_change_routes.py`, `ai_legal_classifier.py`, `ai_legal_routes.py`, `legal_notification_service.py`, `legal_notification_routes.py`, `LegalNews.tsx`, `LegalActionWidget.tsx`, `EarlyWarningFeed.tsx`, `RiskRadarStatus.tsx`, `eulex_service.py`, Cronjobs

## Probleme
- `ai_legal_routes.py` Zeile 632/673: `TODO: Admin-Check einbauen` → fehlende Autorisierung
- `ai_legal_routes.py` Zeile 728–731: Industry, compliance_areas, services werden nicht geladen
- `legal_change_routes.py` Zeile 364: `TODO: Admin-Check`
- `legal_change_routes.py` Zeile 549: Automatische Fix-Anwendung nicht implementiert
- `legal_change_routes.py` Zeile 201–202: Compliance-Areas nicht aus Config
- `legal_change_routes.py` nutzt `current_user.get("user_id")` statt `"id"` → möglicherweise immer None

## Verbesserungsideen
- Admin-Checks implementieren
- User-ID-Feld in `legal_change_routes.py` korrigieren
- Automatische Fix-Auslösung bei kritischen Gesetzesänderungen einbauen

---

# Risk Radar

## Zweck
Frühwarn-System für rechtliche Risiken. Aggregiert Scan-Findings, Gesetzesänderungen und Branchen-Risiken zu einem Radar-Score mit Handlungsempfehlungen.

## Nutzer
Alle Nutzer.

## Status
Aktiv

## Abhängigkeiten
`risk_radar_routes.py`, `RiskRadarStatus.tsx`, Legal Change Monitoring, Scanner-Findings

## Probleme
- `GET /api/risk-radar/score` akzeptiert `user_id` als Query-Parameter – unklar ob Endpoint öffentlich oder auth-geschützt

## Verbesserungsideen
- Auth-Schutz explizit dokumentieren / erzwingen
- Risk Radar mit konkreten Gesetzes-Deadlines verbinden (z.B. BFSG-Frist)

---

# AI Compliance Guard (EU AI Act)

## Zweck
Modul zur Compliance-Prüfung von KI-Systemen nach EU AI Act. Nutzer können eigene KI-Systeme registrieren, Risikoeinstufung durchführen und Dokumentation generieren.

## Nutzer
Unternehmen die KI-Systeme betreiben (Add-on, Extra-Buchung).

## Status
Aktiv

## Abhängigkeiten
`ai_compliance_routes.py`, `ai_compliance_worker.py`, `ai_act_analyzer.py`, `ai_act_doc_generator.py`, `addon_payment_routes.py`, `/ai-compliance/*`-Seiten, Stripe Add-on

## Probleme
- Keine spezifischen Bugs dokumentiert
- Template-TODOs in generierten Dokumenten sind laut Docs absichtlich

## Verbesserungsideen
- Automatische Updates wenn sich EU AI Act Leitlinien ändern
- Dokumenten-Export in verschiedenen Formaten (PDF, Word)

---

# XAI Erklärbarkeits-System

## Zweck
Zeigt Nutzern warum eine Compliance-Entscheidung getroffen wurde: Norm-Zitate, Triggering Factors, Counterfactuals, Confidence Breakdown.

## Nutzer
Alle Nutzer (in Legal Change Dashboard).

## Status
Idee / In Entwicklung (EFRE-Komponente)

## Abhängigkeiten
`ai_legal_classifier.py`, `migrations/add_xai_explanation_fields.sql`, `XAIExplanationCard.tsx`

## Probleme
- Migration `add_xai_explanation_fields.sql` möglicherweise noch nicht in Produktion deployed
- Frontend-Komponente `XAIExplanationCard.tsx` existiert, aber unklar ob aktiv eingebunden

## Verbesserungsideen
- Migration deployen und Status verifizieren
- XAI-Karte in Legal Change Dashboard einbinden

---

# Knowledge Base / Hybrid Retrieval

## Zweck
Rechtsnormen-Wissenskorpus in 5 Sprachen (DE/EN/FR/IT/PL) mit BM25 + Embedding Retrieval (pgvector). Basis für KI-gestützte Compliance-Bewertungen.

## Nutzer
Interne Plattform-Komponente (kein direktes User-Frontend).

## Status
Idee / In Entwicklung (EFRE-Komponente)

## Abhängigkeiten
`backend/knowledge/`, `knowledge_routes.py`, `migrations/add_pgvector_knowledge.sql`, pgvector PostgreSQL Extension

## Probleme
- `knowledge_routes.py` ist nicht in `main_production.py` eingebunden → API nicht erreichbar
- `add_pgvector_knowledge.sql`-Migration möglicherweise noch nicht deployed
- EUR-Lex Crawler (`cronjobs/eurlex_crawler.py`) noch nicht produktiv eingesetzt

## Verbesserungsideen
- `knowledge_routes.py` in Main App einbinden
- Migration deployen und pgvector-Extension aktivieren
- EUR-Lex Crawler in Produktions-Crontab aufnehmen

---

# Authentication & Session Management

## Zweck
Login, Registrierung, JWT-Tokens, Refresh-Token, OAuth (Google/Apple via Firebase), Session-Verwaltung.

## Nutzer
Alle Nutzer.

## Status
Aktiv; technische Schulden vorhanden

## Abhängigkeiten
`auth_routes.py`, `auth_service.py`, `firebase_auth.py`, `oauth_service.py`, `csrf_middleware.py`, `AuthContext.tsx`, `auth-refresh.ts`, `middleware.ts`, DB `users`, `user_sessions`

## Probleme
- Access-Token-Lifetime 7 Tage (zu lang, Security-Risiko)
- Zwei JWT-Libraries im Projekt (PyJWT + python-jose)
- Zwei Passwort-Hashing-Libraries (bcrypt + passlib)
- JWT speichert `id` als String, Backend macht teils `int(user_id)` → `ValueError` bei UUID-artigen IDs
- `SELECT *` in `get_user_by_email`

## Verbesserungsideen
- Token-Lifetime auf 1 Stunde reduzieren, Refresh-Token-Rotation implementieren
- Eine JWT-Library wählen, andere entfernen
- User-ID-Typ in JWT konsistent machen (entweder immer int oder immer UUID)

---

# Zahlung & Abonnements

## Zweck
Stripe-Integration für Checkout, Abonnement-Verwaltung, Add-on-Käufe, Webhook-Handling.

## Nutzer
Alle zahlenden Nutzer.

## Status
Aktiv

## Abhängigkeiten
`payment_routes.py`, `stripe_routes.py`, `payment/stripe_service.py`, `addon_payment_routes.py`, `SubscriptionPlans.tsx`, `StripePaywallModal.tsx`, `/subscription`-Seite

## Probleme
- `BYPASS_PAYMENT` und `DEV_MODE` Umgebungsvariablen existieren (Sicherheitsrisiko in Produktion, aber durch Guard abgesichert)
- Docs erwähnen Stripe Price-ID-Placeholder-Problem; aktueller Stand unklar

## Verbesserungsideen
- `DEV_MODE`/`BYPASS_PAYMENT` vollständig aus Produktions-Codebase entfernen statt nur guarden
- Stripe Webhook-Signatur-Validierung in Tests abdecken

---

# Agency / Multi-Client Management

## Zweck
Agentur-Dashboard für Verwaltung mehrerer Kunden-Websites, Client-Gruppiering, PDF-Report-Download, eigenes Branding/Logo.

## Nutzer
Agenturen (Agentur-Plan).

## Status
Aktiv (neu implementiert)

## Abhängigkeiten
`/agency`-Frontend-Seite, `AgencyLogoUpload.tsx`, `ClientGroup.tsx`, Backend-Agency-Endpoints, `agency_report_generator.py`, `pdf_report_generator.py`

## Probleme
- Sehr neue Implementierung, wenige Docs; Stabilität unklar

## Verbesserungsideen
- White-Label-Export ausbauen (Logo in PDFs, Custom-Domain für Widget-Serving)
- Bulk-Scan für alle Kunden-Websites

---

# Expert Service

## Zweck
Nutzer können eine Buchung für persönliche Implementierung durch das Complyo-Team anfragen. Entspricht dem "Expert Plan" (2.000€ Setup).

## Nutzer
Nutzer die keine eigene Implementierung durchführen wollen.

## Status
Aktiv; teilweise buggy

## Abhängigkeiten
`expert_service_routes.py`, `ExpertServiceModal.tsx`, `email_service.py`, DB `expert_service_requests`

## Probleme
- `expert_service_routes.py`: Auth/User-Ownership fehlt (optionaler `user_id` Query-Param ohne Auth-Dependency)
- Email-Service-Integration war laut Technical Debt Zeile 271 incomplete; neuere Docs sagen "fixed"

## Verbesserungsideen
- Auth-Dependency für `/request` Endpoint erzwingen
- Automatische Bestätigungs-E-Mail an Nutzer verifizieren

---

# Lead Management / Waitlist

## Zweck
Sammelt Interessenten-Leads für die Plattform, mit DSGVO-Consent und Double-Opt-in.

## Nutzer
Landing-Page-Besucher / Interessenten.

## Status
Aktiv

## Abhängigkeiten
`lead_routes.py`, `migrations/create_waitlist_leads.sql`, `database_service.py`, Landing-Page-Formulare

## Probleme
- `database_service.py` hat Silent-Fallback zu In-Memory-Storage bei DB-Ausfall → Lead-Datenverlust möglich

## Verbesserungsideen
- In-Memory-Fallback entfernen oder explizit fehler-eskalieren
- Double-Opt-in E-Mail-Flow testen

---

# Internationalisierung (i18n)

## Zweck
Backend-API und Widget-Übersetzungen in 5 Sprachen (DE/EN/FR/IT/PL). Dashboard selbst aktuell DE/EN.

## Nutzer
Alle Nutzer und Widget-Endnutzer.

## Status
Aktiv

## Abhängigkeiten
`i18n_api.py`, `i18n_service.py`, `widgets/locales/translations.js`, Cookie Banner v2 und Accessibility Widget v6

## Probleme
- Keine bekannten Bugs dokumentiert
- Dashboard-i18n (React-Seiten) noch nicht vollständig auf alle 5 Sprachen erweitert

## Verbesserungsideen
- Dashboard-UI vollständig i18n-fähig machen
- Sprach-Erkennung aus Browser-Header automatisch nutzen

---

# MCP Server

## Zweck
Model Context Protocol Server zur Anbindung der Plattform an KI-Agenten und externe Automatisierungs-Tools.

## Nutzer
Entwickler / interne Automatisierung.

## Status
Idee / In Entwicklung

## Abhängigkeiten
`mcp_server.py`, `data/mcp-agent-config.json`, `data/MCP_INTEGRATION_PLAN.md`

## Probleme
- Kein API-Endpoint in `main_production.py` eingebunden
- Implementierungsstand unklar

## Verbesserungsideen
- MCP Server-Scope definieren und in Main App einbinden
- Auth-Mechanismus für MCP festlegen

---

# Admin Dashboard

## Zweck
Internes Admin-Interface für Lead-Verwaltung, Fix-Review und System-Überwachung. Läuft auf Port 3004 als separates `simple-admin`.

## Nutzer
Internes Team (Complyo).

## Status
Aktiv

## Abhängigkeiten
`admin_routes.py`, `/simple-admin/`, `/admin/fix-review`-Frontend-Seite

## Probleme
- Admin-Auth über Query-Parameter (`?api_key=...`) – schwacher Mechanismus (Keys können in Logs/Proxies erscheinen)
- Missing Admin-Checks in `ai_legal_routes.py` und `legal_change_routes.py`

## Verbesserungsideen
- Admin-Auth auf Bearer-Token oder Session-basiert umstellen
- Admin-Checks in Legal-Routen implementieren

---

# Landing Page / Marketing

## Zweck
Öffentliche Marketing-Site mit Website-Scanner-Demo, Pricing, Features, A/B-Testing verschiedener Landing-Varianten.

## Nutzer
Interessenten / potenzielle Kunden.

## Status
Aktiv

## Abhängigkeiten
`landing-react/`, `ABTestRouter.tsx`, `public_routes.py` (Demo-Scanner), diverse Landing-Varianten-Komponenten

## Probleme
- Keine aktuellen Bugs dokumentiert

## Verbesserungsideen
- A/B-Test-Ergebnisse tracken und auswerten
- Conversion-Optimierung auf Basis von Lead-Daten

---

# Infrastruktur / Deployment

## Zweck
Docker-Compose-basiertes Produktions-Setup mit NGINX Gateway, SSL via Certbot, GitHub Actions CI/CD, Prometheus Metrics, Sentry Error Monitoring.

## Nutzer
DevOps / Betrieb.

## Status
Aktiv

## Abhängigkeiten
`docker-compose.yml`, `gateway/nginx-production.conf`, `scripts/`, `.github/workflows/`, Sentry, Prometheus

## Probleme
- Git OAuth-State In-Memory (bricht bei Restart/Multi-Worker)
- APM/Uptime-Monitoring fehlt laut Docs
- Hardcodede Standard-DB-Credentials in `database_service.py`
- In-Memory-Fallback-Storage in `database_service.py`

## Verbesserungsideen
- OAuth-State nach Redis migrieren
- APM (z.B. Grafana + Prometheus) einrichten
- DB-Credentials ausschließlich aus Umgebungsvariablen lesen, Fallback entfernen

---

# Deprecated / Zu entfernen

## eRecht24 Integration
**Status:** Entfernen  
Backend-Dateien wurden entfernt, aber einige Docs und DB-Daten referenzieren noch alte Endpunkte. Migration-Rollback-Script vorhanden.

## Accessibility Widget v4/v5
**Status:** Entfernen  
`accessibility.js`, `accessibility_smart.js`, `accessibility-v5.js` werden noch serviert aber sind überholt durch v6.

## Legacy Cookie Consent Widget
**Status:** Entfernen  
`cookie_consent.legacy.js` noch im Filesystem.

## Enhanced Fix Routes
**Status:** Idee / Unklar  
`enhanced_fix_routes.py` existiert, ist aber nicht in `main_production.py` eingebunden. Entweder einbinden oder löschen.

## Knowledge Routes
**Status:** Idee  
`knowledge_routes.py` existiert, ist nicht eingebunden. Wenn Knowledge Base aktiviert wird, muss das nachgeholt werden.

## Legacy Fix Generator
**Status:** Entfernen (sobald Unified Engine stabil)  
`fix_generator.py` noch aktiv neben dem neuen `ai_fix_engine/unified_fix_engine.py`.
