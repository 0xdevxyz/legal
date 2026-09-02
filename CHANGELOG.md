# Changelog

> Jede Code-Änderung wird hier eingetragen. Format: `## [YYYY-MM-DD]` mit Kategorien.  
> Detaillierte Analyse offener Punkte: `data/technisch/TECHNICAL_DEBT.md`  
> Systemübersicht: `data/architektur/SYSTEM_OVERVIEW.md`  
> Offene Tasks & Entwicklungsstand: `data/anleitungen/ENTWICKLUNGSSTAND.md`

---

## [2026-09-02]

### Frontend
- Kampagnen-Landingpage `/early-access` (`landing-react/src/app/early-access/`, `src/components/kampagne/`): Early-Access-Warteliste mit Anlass BFSG, Angebot 35 € statt 49 € für die ersten 100 bestätigten Anmeldungen. Bewusst auf `noindex` — ein befristetes Sonderangebot soll nicht dauerhaft in der Suche stehen und den regulären Preis untergraben
- `WartelistenFormular` wertet eine `204`-Antwort nicht länger als Erfolg: bei ausgelöster Bot-Abwehr antwortet der Endpunkt still mit leerem Rumpf, das alte `JoinEarlySection` zeigte darauf eine Bestätigung an und der Besucher wartete auf eine Mail, die nie kam
- Formular wartet vor dem Absenden bis zur 4-Sekunden-Marke der serverseitigen Zeitfalle, statt den Eintrag zu verlieren — Browser-Autofill unterschreitet sie mühelos
- `PlatzZaehler` liest den Stand über `/api/leads/waitlist/plaetze` aus der Datenbank; fällt der Zähler aus, wird keine Zahl gezeigt statt einer geratenen

### Backend
- **Waitlist-Strecke war vollständig tot**: `lead_routes.py` rief durchgehend `db_service.execute_query(...)` auf, eine Methode, die `DatabaseService` nicht hat. Jede Anmeldung wäre in einen `AttributeError` und damit in einen 500er gelaufen. Auf das echte Muster `async with db_service.get_connection()` mit asyncpg umgestellt
- **Rate-Limit galt global statt pro Besucher**: `join_waitlist` las `request.client.host`, hinter nginx immer die Gateway-IP — nach drei Anmeldungen in zehn Minuten hätte das Formular jedem weiteren Besucher `429` geantwortet. Jetzt über `get_client_ip` (respektiert `TRUSTED_PROXIES`), derselbe Fehler wie beim Landing-Scanner am 12.08.2026
- `source` wird gesäubert statt gegen eine Allowlist aus drei Werten verworfen; alles andere fiel vorher still auf `early-access` zurück und machte bezahlten Traffic nicht auswertbar
- Herkunft je Anmeldung: `campaign`, `utm_*` und `landing_path` werden aufgenommen; `landing_path` gegen offene Weiterleitung geprüft (auch das protokollrelative `//fremde.domain`), weil er das Redirect nach dem Opt-In-Klick steuert
- Double-Opt-In leitet auf die Ursprungsseite zurück statt immer auf `/` — wer über eine Anzeige kam, landete nach dem Klick auf etwas Fremdem
- Neuer offener Endpunkt `GET /api/leads/waitlist/plaetze` (Kontingent, vergeben, frei); bewusst in `LEADS_OEFFENTLICH_GEWOLLT`, gibt nur die Zahl vergebener Plätze heraus, nicht die Lead-Gesamtzahl
- Platznummern aus `waitlist_platz_seq`, vergeben erst bei der Bestätigung: ein unbestätigter Eintrag darf keinen der 100 Plätze blockieren. `angebot` ist eine Servereigenschaft und wird nicht aus dem Request übernommen
- `send_waitlist_admin_notification` trägt Herkunft und zugesagtes Angebot und meldet eine fehlende `ADMIN_NOTIFY_EMAIL` im Log, statt still mit `return False` auszusteigen
- Migration `0018_waitlist_kampagne`: Herkunfts- und Angebotsspalten auf `waitlist_leads`, Sequence `waitlist_platz_seq`
- **Einwilligungsnachweis belegte nichts**: `collect_lead` (`POST /api/leads/collect`) und die Verify-Route (`GET /api/leads/verify/{token}`) schrieben `request.client.host` in den DSGVO-Audit-Trail (`consent_ip_address` bzw. `db_service.verify_email`). Hinter nginx ist das immer die Gateway-IP `172.22.0.x`, bei jedem einzelnen Lead stand also dieselbe interne Adresse. Ein Nachweis, der für alle Einwilligungen denselben Wert trägt, zeigt gegenüber der Aufsicht nur, dass die Anfrage durch den eigenen Proxy lief. Beide Stellen jetzt über `get_client_ip` wie `join_waitlist` (respektiert `TRUSTED_PROXIES`)
- `cookie_compliance_routes.py` hatte eine eigene, ungeprüfte `get_client_ip`, die `X-Forwarded-For` blind übernahm und damit die richtige Fassung aus `dependencies` verdeckte. Diesen Header setzt der Client selbst: das Einwilligungsprotokoll des Cookie-Banners war so fälschbar, und ein fälschbarer Nachweis ist keiner. Die lokale Funktion greift jetzt auf `dependencies.get_client_ip` durch; der Rückgabetyp bleibt `Optional[str]`, damit `log_consent` bei fehlender IP wie bisher auf den Device-Fingerprint ausweicht statt den Wortlaut `unknown` zu hashen
- `GET /api/cookie-compliance/geo-check` las `request.headers.get('X-Forwarded-For', request.client.host)`: derselbe fälschbare Header, dazu ein `AttributeError`, sobald `request.client` fehlt. Ohne ermittelbare IP wird jetzt nur der Geo-Cache übersprungen, die Länderkennung läuft weiter

### Tests
- `tests/test_waitlist.py`: Mocks bildeten mit `mock_db.execute_query` eine Methode nach, die es nie gab — MagicMock erfindet jedes Attribut, deshalb war die Suite grün, während die Strecke in Produktion tot war. Auf das echte Verbindungsmuster umgestellt
- Neu `TestDbServiceVertrag`: vergleicht die in `lead_routes` aufgerufenen `db_service`-Methoden gegen die echte Klasse — genau dieser Test hätte den Ausfall gefangen
- Neu `TestEchteBesucherIp`, `TestHerkunft` sowie Prüfungen auf offene Weiterleitung im `landing_path`
- `test_source_allowlist_ohne_duplikat` durch `test_herkunft_wird_gesaeubert_statt_verworfen` ersetzt (die Allowlist ist bewusst entfallen)
- Neu `TestEinwilligungsIpImAuditTrail`: prüft an `collect_lead` und der Verify-Route, dass die IP des Besuchers im Nachweis landet, und zwar mit Gegenprobe gegen einen nicht hinterlegten Proxy. Beide Tests fallen gegen den alten Stand (`testclient` statt `203.0.113.7`); die Gegenprobe hält fest, dass ein blindes Übernehmen von `X-Forwarded-For` keine Lösung wäre
- Neu `TestCookieConsentIpNichtFaelschbar`: schlägt an, sobald in `cookie_compliance_routes.py` wieder ein ungeprüftes `X-Forwarded-For` steht

### Infrastruktur
- `docker-compose.yml`: `ADMIN_NOTIFY_EMAIL` wird an das Backend durchgereicht — stand in der `.env`, kam nie im Container an, und die Benachrichtigung stieg deshalb still aus. Dazu `EARLY_ACCESS_PLAETZE` und `EARLY_ACCESS_ANGEBOT`
- backend und landing neu gebaut und deployt; Migration `0018` gegen Produktion gelaufen; Testsuite im Backend-Image: 1579 passed, 66 skipped
- Anmeldung und Double-Opt-In über die öffentliche Domain durchgespielt (Herkunft in der Datenbank, Rückleitung auf `/early-access/`, Platz 1 vergeben), Testdaten anschließend entfernt und Sequence zurückgesetzt
- Testsuite im Backend-Image nach den IP-Korrekturen: 1620 passed, 29 skipped. Die Korrekturen an Lead- und Cookie-Consent-Strecke sind committet, aber noch **nicht deployt** — dafür muss das Backend-Image neu gebaut werden

### Tech Debt
- `log_consent` (`POST /api/cookie-compliance/consent`) zieht weiterhin ein vom Client mitgeschicktes `ip_address` der selbst ermittelten IP vor. Damit bleibt der Nachweis von außen beeinflussbar, auch wenn der Rückfall jetzt geprüft ist. Bewusst nicht mit umgestellt, weil das den Vertrag des ausgelieferten Banner-Skripts ändert; gehört vor dem nächsten Widget-Release entschieden
- `landing-react/src/components/saas-landing/JoinEarlySection.tsx` und die Sicherungskopie `JoinEarlySection.tsx.bak.20260729` gelöscht. Die Sektion war seit `e630896` ("Preise, Navigation und Kaufweg statt Warteliste") aus `EarlyAccessLanding` genommen und danach nirgends mehr eingebunden: kein Import, kein `#waitlist`-Anker, keine Route. Sie trug beide Fehler, die heute in `WartelistenFormular` behoben wurden (`204` als Erfolg gewertet, keine Wartezeit bis zur Zeitfalle), und hätte sie beim nächsten Wiedereinbau zurück in die Seite gebracht. Zwei Formulare gegen denselben Endpunkt zu pflegen war die Ursache der Abweichung, deshalb löschen statt nachziehen: `WartelistenFormular` ist der eine verbleibende Weg auf die Warteliste

---

## [2026-08-11]

### Backend
- Dashboard-Scanpfad `POST /api/v2/analyze` vollwertig: Multipage-Scan mit Seitenbudget, KI-Review (fail-open) und Accessibility-Post-Prozessor (Alt-Texte/Fix-Manifest) — vorher Single-Page ohne Fix-Erzeugung; `scan_token` (Live-Fortschritt) und `legal_update_id` werden jetzt angenommen und persistiert (`backend/main_production.py`)
- Landing-Preview: Mock-Antwort bei Scannerfehlern entfernt — statt aus dem URL-Hash gewürfelter Befunde mit `success:true` kommt ein ehrlicher Fehlerzustand (`backend/public_routes.py:_preview_scan_fehler`)
- `scan_history`-Persistenz im Analyze-Pfad in eigenen try-Block: Schema-Drift übersprang vorher still die komplette Fix-Erzeugung (`backend/public_routes.py`)
- Toter Endpunkt `POST /sites/{site_id}/widget-feedback` entfernt (wurde von keinem Widget aufgerufen; Selbstüberwachung läuft über `POST /api/wirkung`)
- Website-Monitor: Alarm-Vergleichsquery repariert (`scan_timestamp` statt `scan_date`, Join über `user_id`+`url` wegen NULL-`website_id`) — der „kritische Befunde gestiegen"-Alarm war seit je stumm; `score_history.pillar_scores` auf einheitliches Dict-Format inkl. `critical_issues` normalisiert (`backend/cronjobs/website_monitor.py`)
- DSGVO-Cleanup erweitert: `leads`-Retention (Ablauf + Löschantrag > 30 Tage) im Daily-Cleanup, `cookie_consent_logs` einheitlich 24 Monate (vorher 1 Jahr hier, 24 Monate in der Policy, 3 Jahre DB-Default); GDPR-Retention-Service-Loop (Löschankündigungen/-bestätigungen, Kontolöschungen) wird jetzt beim Start tatsächlich gestartet (`backend/main_production.py`)
- `tests/test_schema_completeness.py`: Schema-Parser erkennt `op.create_table`-Revisionen (z. B. 0014 `gdpr_deletion_requests`) — der Test meldete die Tabelle fälschlich als fehlend

### Infrastruktur
- `scripts/legal_updates_dedup.sql` gegen Produktion ausgeführt: 719 → 330 `legal_updates` (Titel-Duplikate entfernt, Referenzen in `notifications`/`pflichten_events` umgehängt, Backup-Tabelle angelegt); Reihenfolge beachtet — erst Monitor-Deploy, dann Dedup, damit der alte Cron keine neuen Duplikate erzeugt
- backend/dashboard/landing neu gebaut und deployt (inkl. Audit-Stand c5876a4); Testsuite im Backend-Image: 1348 passed, 86 skipped
- E-Mail-Versand live: SMTP auf eigenen Mailserver umgestellt (mail.complyo.de:587/STARTTLS, Absender noreply@complyo.de) — Demo-Modus in Produktion beendet, Zustellung mit Testmail verifiziert; Zugangsdaten nur in der Server-.env

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
