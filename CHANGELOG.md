# Changelog

> Jede Code-Änderung wird hier eingetragen. Format: `## [YYYY-MM-DD]` mit Kategorien.  
> Detaillierte Analyse offener Punkte: `data/technisch/TECHNICAL_DEBT.md`  
> Systemübersicht: `data/architektur/SYSTEM_OVERVIEW.md`  
> Offene Tasks & Entwicklungsstand: `data/anleitungen/ENTWICKLUNGSSTAND.md`

---

## [2026-05-23]

### Security — HttpOnly-Härtung Access-Token (Phase 5)
- `backend/auth_routes.py`: Login/Register/Refresh-Cookie-Endpoints setzen `access_token` jetzt als HttpOnly-Cookie (`httponly=True, secure=True, samesite="lax"`)
- `backend/dependencies.py`: `get_current_user` + `get_current_user_optional` lesen Token aus Bearer-Header **oder** `access_token`-Cookie
- `dashboard-react/src/lib/auth-refresh.ts`: `localStorage` komplett entfernt — Token nur noch in Memory (`window.__complyo_access_token`) + HttpOnly-Cookie
- `dashboard-react/src/app/auth/callback/page.tsx`: kein `localStorage.setItem('access_token')` mehr
- `dashboard-react/src/components/SocialLoginButtons.tsx`: kein `localStorage.setItem('access_token')` mehr

**Auswirkung:** `localStorage.getItem('access_token')` liefert `null`. XSS kann Access-Token nicht mehr exfiltrieren.


- `dashboard-react/src/lib/auth-refresh.ts` (neu): Zentrales Token-Modul mit `getAccessToken`, `setAccessToken`, `clearAccessToken`, `refreshAccessToken` (Single-Flight-Pattern)
- `dashboard-react/src/lib/api-client.ts`: Response-Interceptor erneuert abgelaufene Access-Tokens transparent via `POST /api/auth/refresh-cookie`; Pending-Queue für parallele 401-Requests → exakt 1 Refresh-Call
- `dashboard-react/src/auth.config.ts`: `accessTokenExpiresAt` im NextAuth-JWT; `session.error`-Propagation für erzwungenen Logout
- `dashboard-react/src/contexts/AuthContext.tsx`: Reagiert auf `RefreshAccessTokenError` mit sauberem `signOut`
- `dashboard-react/src/lib/api.ts` + `ai-compliance-api.ts`: Eigene Axios-Clients konsolidiert → nutzen zentralen `getApiClient()` mit Refresh-Logik
- `dashboard-react/src/lib/auth-helper.ts`: Deprecated → Re-Export aus `auth-refresh.ts`
- 21 Komponenten/Seiten: `fetch + localStorage.getItem('access_token')` → `apiClient` (kein Token-Direktzugriff mehr)
- `dashboard-react/.eslintrc.json`: ESLint-Regel blockiert künftige `localStorage.getItem('access_token')` Direkt-Zugriffe

**Auswirkung:** Sessions werden nicht mehr nach 60 Min beendet. Abgelaufene Access-Tokens werden automatisch über den HttpOnly-Cookie-Refresh-Token erneuert.

---

## [2026-04-21]

### Security – Auth-Debt Phase 1 (alle Punkte abgeschlossen)
- `widget_routes.py`: `generate_accessibility_patches` Endpoint mit `get_current_user` aus `dependencies.py` abgesichert — gibt 401 ohne Bearer Token zurück
- `widget_routes.py`: `user_id=1` Hardcode entfernt — user_id kommt jetzt aus `current_user["user_id"]`
- `widget_routes.py`: `Depends(lambda: None)` auf echten `get_db` Pool umgestellt
- `cookie_compliance_routes.py`: Auth-Flow verifiziert — alle Endpoints mit `get_current_user_required` geben korrekt 401 zurück

### Backend – DB-Integration Phase 2 (alle Punkte abgeschlossen)
- `widget_routes.py`: `track_widget_event` schreibt Events in `widget_events` Tabelle (INSERT via db_pool, silent-fail bei DB-Fehler)
- `widget_routes.py`: `_check_upsell_opportunity` führt echte COUNT-Abfrage auf `widget_usage_stats` durch
- `widget_routes.py`: `get_widget_config` lädt Banner-Config aus `cookie_banner_configs` mit Default-Fallback
- `public_routes.py`: `widget_feedback` persistiert Events in `widget_events` Tabelle
- `ai_legal_routes.py`: Feedback-Persistierung via `ai_feedback_learning.record_feedback` verifiziert — kein neuer Tech Debt

### Features – Phase 3 (alle Punkte abgeschlossen)
- `expert_service_routes.py`: `EmailService` importiert, `_send_expert_request_email` versendet 2 echte Emails (Kunden-Bestätigung + Team-Notification) via `email_service._send_email`; Email-Fehler brechen Anfrage nicht ab
- `widgets/cookie_consent.js`: Cookie-Settings-Modal vollständig implementiert — 4 Kategorien (Notwendig, Funktional, Analytik, Marketing) mit Toggle-Switches, Auswahl-Speichern und Alle-akzeptieren-Button; Consent wird in localStorage persistiert und via `complyoConsent` Event dispatched

### Tech Debt
- `widget_routes.py`: `import json` und `import logging` hinzugefügt
- `widget_routes.py`: `from dependencies import get_current_user, get_db` hinzugefügt
- `expert_service_routes.py`: `from email_service import email_service` hinzugefügt

---

## [2026-04-10]

### Dokumentation
- `data/architektur/SYSTEM_OVERVIEW.md` erstellt – Master-Referenz für alle Entwicklungssessions (Tech-Stack, Router, Services, Datenpfade, Env-Variablen)
- `data/anleitungen/ENTWICKLUNGSSTAND.md` erstellt – Offene Tasks, Technical Debt nach Priorität, Coding-Konventionen, Session-Checkliste
- `CONTRIBUTING.md` erweitert – verbindliches Dokumentationsprotokoll für alle Code-Änderungen

---

## [2026-03-29]

### Security – Auth Hardening (Phase 1, alle Punkte abgeschlossen)
- OAuth-Callback: Token-Übergabe von Query-String auf URL-Fragment umgestellt (`#access_token=...`)
- `legal_ai_routes.py`: Auth-Stub (`{"user_id": "test-user"}`) durch echte `Depends(get_current_user)` ersetzt
- Admin-Endpoints abgesichert: `require_admin` Dependency auf `ai_legal_routes.py:762`, `ai_legal_routes.py:803`, `legal_change_routes.py:363` angewendet
- `auth_service.py:141,181`: `datetime.utcnow()` durch `datetime.now(timezone.utc)` ersetzt (Session-Expiry-Bug)

### Security – Stripe Hardening (Phase 2, alle Punkte abgeschlossen)
- `addon_payment_routes.py`: `RuntimeError`-Guard bei leerem `STRIPE_WEBHOOK_SECRET_ADDONS` (analog zu `stripe_routes.py:38-40`)
- `handle_addon_subscription_cancelled`: DB-Zugang wird bei Abo-Kündigung sofort entzogen
- `handle_addon_subscription_updated` + `handle_addon_payment_failed`: Handler implementiert mit DB-Updates via `stripe_subscription_id`

### Tech Debt (Phase 3, alle Punkte abgeschlossen)
- `main_production.py:628-667`: Doppelte JWT-Helpers (`create_jwt_token`, `verify_jwt_token`, `get_current_user`) entfernt – alle Auth-Pfade laufen durch `AuthService` / `dependencies.py`
- `legal_ai_routes.py` gelöscht und aus `main_production.py` ausgehängt (Import + `include_router` entfernt)
- API Base URL konsolidiert: `getApiBaseUrl()` nur noch in `dashboard-react/src/lib/api-utils.ts`, alle 5 Duplikat-Dateien importieren daraus

### Codebase-Analyse
- `.planning/codebase/` erstellt: `ARCHITECTURE.md`, `CONCERNS.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `STACK.md`, `STRUCTURE.md`, `TESTING.md`
- `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` erstellt

---

## [2026-02-18]

### Sicherheit & Stabilität
- aiohttp CVE-2024-23334 behoben: 3.9.1 → 3.9.5
- Rate Limiting auf Auth-Endpoints (3/h Register, 5/min Login, 10/min Refresh)
- HttpOnly Cookie für Refresh-Token (XSS-Schutz)
- JWT Issuer/Audience Claims Validierung
- CORS Environment-Split (HTTP-Origins nur in Nicht-Production)
- DOMPurify XSS-Sanitierung in 6 Dashboard-Komponenten
- Hardcodierte DB-Credentials aus 5 Utility-Skripten entfernt
- ERECHT24_API_KEY korrekt in Docker-Container übergeben

### Backend
- FastAPI 0.115.6, httpx 0.27.2, PyJWT 2.9.0, requests 2.32.3
- Erweiterter `/health`-Endpoint mit DB/Redis/API-Latenz
- Request-ID-Middleware für Tracing
- Täglicher AI-Cache-Cleanup-Job (30-Tage-Retention)
- Täglicher GDPR-Cleanup: abgelaufene Sessions + inaktive Accounts
- Tägliche Backup-Retention: Consent-Logs (1J), AI-Logs (90T), E-Mail-Verif.
- Sentry SDK Integration (opt-in via `SENTRY_DSN`)
- Prometheus `/metrics` Endpoint (token-geschützt via `METRICS_TOKEN`)
- Playwright Browser-Pool mit `asyncio.Semaphore(3)`
- `datetime.utcnow()` durch timezone-aware `datetime.now(UTC)` ersetzt
- 6 neue DB-Indizes: scan_results, compliance_fixes, legal_news

### Widgets
- Gzip-Komprimierung aktiv auf allen Widget-Endpoints
- Content-basierte ETags für Browser-Caching
- Cache-Control: 24h + `stale-while-revalidate=3600`

### Frontend
- DOMPurify `sanitizeHtml()` Utility in `src/lib/sanitize.ts`
- package-lock.json für dompurify aktualisiert

### Infrastruktur
- `docker-compose.yml`: ERECHT24_API_KEY, SENTRY_DSN, METRICS_TOKEN
- `.env.example` aktualisiert
- ESLint-Konfiguration in dashboard + landing verschärft
- Husky Pre-Commit-Hooks konfiguriert
- Swagger/Redoc nur im Nicht-Production-Modus aktiv

### Tests & Dokumentation
- Unit-Tests: `tests/test_auth.py`, `tests/test_i18n.py` (6 Tests, alle grün)
- E2E-Tests: `smoke.spec.ts`, `accessibility.spec.ts` (Playwright)
- `MIGRATIONS.md`: Alle 30 SQL-Dateien dokumentiert
- `README.md` erstellt

---

## [2026-02-07]

### Features
- Legal News Scraping: BfDI, BMAS, IT-Recht Kanzlei, Dr. Datenschutz, Haufe, Heise
- EU-Lex API Integration (SPARQL) für EU-Recht (DSGVO, AI Act, DSA)
- E-Mail-Benachrichtigungen bei kritischen Gesetzesänderungen
- Nutzer-Bestätigungsflow für Legal Updates
- Dashboard-Widget LegalActionWidget
- Optimierter Cronjob mit variablen Fetch-Intervallen (4–12h)

---

## [2026-02-06]

### Fixes & Launch-Readiness
- 56 fehlende DB-Tabellen erstellt
- Registrierung vollständig funktionsfähig
- Mobile Hamburger-Navigation auf Landing Page
- Legal-Footer (Impressum/Datenschutz/AGB) auf allen Landing-Varianten
- NEXT_PUBLIC_DASHBOARD_URL als Env-Variable
- SEO: Open Graph, Twitter Cards, robots.txt, sitemap.ts
- "Passwort vergessen"-Link repariert
- Profil-Seite an echte API-Endpoints angebunden
- TypeScript + ESLint Checks aktiviert
- PUT /api/user/profile, /api/user/billing, /api/user/password
- Non-root User im Backend-Dockerfile

---

## [2026-01-23]

### Features
- Cookie Scanner Service & Compliance-Checks erweitert
- Cookie-Banner-Widgets mit Lokalisierung
- Neue UI-Komponenten: Skeleton, SuccessAnimation
- Legal Pages: AGB, Datenschutz, Impressum

---

## [2026-01-07]

### Features
- TCF 2.2 Compliance System
- Accessibility Fix Pipeline (BFSG)
- AI Act Dokumentations-Generator
- Fix Audit Trail System
- Alembic Migration Setup
- Accessibility Widget & Fix Wizard
- Cookie Consent Modal
- TCF Compliance Widget

---

## [2025-12-xx] – Initial Release

- KI-gestützte Website-Compliance-Analyse (DSGVO, TTDSG, BFSG)
- Cookie-Consent-Widget (v1, v2)
- Accessibility-Widget (v1–v6)
- eRecht24 Integration
- Stripe Freemium-Modell
- Firebase Auth
- PDF-Report-Generator
