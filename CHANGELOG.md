# Changelog

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
