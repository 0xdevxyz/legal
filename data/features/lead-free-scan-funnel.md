# Lead- / Free-Scan-Funnel

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Akquisekanal: kostenloser Compliance-Scan ohne Login, danach Lead-Erfassung mit
Double-Opt-in (§ 7 UWG / Art. 6 Abs. 1 lit. a DSGVO) und Report-Zustellung per E-Mail.
Zweiter Pfad: Early-Access-**Warteliste** mit eigenem Double-Opt-in.

## Architektur (end-to-end)
- **Scan-Einstieg:** `backend/public_routes.py`
  - `POST /api/analyze` (Zeile 106) — `current_user: dict = Depends(get_current_user)`,
    also der eingeloggte Pfad.
  - `POST /api/analyze-preview` (Zeile 1883) — **ohne Auth, ohne Rate-Limit-Dependency**,
    voller Scan. Details in [[scan-analyze-kern]].
- **Lead-Routen:** `backend/lead_routes.py` (Router-Prefix `/api/leads`, in
  `main_production.py:601` eingebunden). Kein Auth-Gate auf irgendeiner Route.
  - `POST /collect` — dedupliziert über `db_service.get_lead_by_email`; bereits
    verifiziert → Report sofort, sonst Verifikationsmail erneut. Neu → `create_lead`
    (liefert `lead_id` + `verification_token`) + `send_verification_email` als
    `BackgroundTask`. IP/User-Agent als DSGVO-Audit-Trail.
  - `GET /verify/{token}` — `db_service.verify_email(token, ip, ua)`, danach
    `send_compliance_report` (PDF via `pdf_report_generator`).
  - `POST /unsubscribe` — `update_lead_status_by_email(email, 'unsubscribed')`.
  - `GET /stats` — `db_service.get_lead_statistics()`.
  - `POST /waitlist` — Honeypot-Feld `website` → 204; IP-Hash (`SECRET_SALT`, SHA-256);
    **In-Memory-Rate-Limit** `_check_rate_limit` (3 / 10 min, `defaultdict`) ;
    `secrets.token_urlsafe(32)`, 7 Tage gültig; INSERT in `waitlist_leads`;
    Bestätigungs- + Admin-Mail als BackgroundTasks.
  - `GET /waitlist/confirm?token=` — prüft Ablauf, setzt `confirmed_at`, **löscht den
    Token** (`confirm_token = NULL`), Redirect `?confirmed=1|0`.
- **E-Mail:** `backend/email_service.py` — `EmailService._send_email` ist der einzige
  Versandpfad; `send_verification_email`, `send_compliance_report`,
  `send_waitlist_confirmation`, `send_waitlist_admin_notification` laufen alle darüber.

## DB
Gegen die Alembic-Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py`,
Dump `backend/alembic/baseline_schema.sql`) und die Live-DB verifiziert:
- `waitlist_leads` — vorhanden (Baseline `baseline_schema.sql:3283`, live bestätigt).
- **`leads` — [BEHOBEN 2026-07-17]**: fehlte weder in Baseline noch in der laufenden DB;
  `database_service.py` las/schrieb sie trotzdem (`INSERT INTO leads`, `SELECT * FROM leads`,
  `COUNT(*) FROM leads`). Jetzt via Alembic-Revision `0003_missing_lead_and_audit_tables`
  angelegt (zusammen mit `lead_consents`, `communication_log`, `email_verifications`) und gegen
  die Live-DB angewendet. Archiv-SQL (`_archive_pre_baseline/`) bleibt tabu.
- `analysis_data` wird korrekt mit `json.dumps(...)` geschrieben
  (`database_service.py:87`) → asyncpg-JSONB-Regel eingehalten.
- `backend/init_lead_tables.py` **existiert nicht (mehr)** — der Tote-Code-Verdacht ist
  gegenstandslos.

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] Der klassische Lead-Pfad war funktionsunfähig (höchste Priorität).**
  Ohne Tabelle `leads` lief `POST /collect` in `UndefinedTableError` → 500; `GET /stats` fing
  die Exception ab und lieferte still `total_leads: 0, … "success": true`. Fix: `leads` (plus
  `lead_consents`, `communication_log`, `email_verifications`) via Alembic-Revision
  `0003_missing_lead_and_audit_tables` (additiv, gegen die Live-DB angewendet) nachgezogen →
  `POST /collect` durchläuft jetzt die normale Validierung (live verifiziert). Wächter
  `tests/test_schema_completeness.py` leitet fehlende Tabellen künftig aus INSERT/FROM ab.
- **Double-Opt-in ist faktisch tot.** `email_service.py:35` setzt
  `demo_mode = not all([self.smtp_username, self.smtp_password])`; im Container sind
  `SMTP_USERNAME` und `SMTP_PASSWORD` **leer** (nur `SMTP_HOST` gesetzt) → `_send_email`
  (:127) printet die Mail auf die Konsole und **gibt `True` zurück** (:142). Betrifft
  Verifikations-, Report-, Waitlist-Bestätigungs- und Admin-Mail gleichermaßen. Der
  Aufrufer bekommt Erfolg gemeldet, der Nutzer nie eine Mail — Waitlist-Einträge bleiben
  dauerhaft `confirmed_at IS NULL`. Gleiches Muster wie der SMTP-`demo_mode` in
  `legal_notification_service.py`. Fix: SMTP-Credentials setzen **und** `demo_mode` in
  Produktion hart abschalten statt still `True` zu liefern.
- **[BEHOBEN 2026-07-17] `GET /api/leads/stats` war ohne Auth abrufbar** (Geschäftskennzahlen:
  Lead-Gesamtzahl, verifizierte/konvertierte Leads). Fix: `Depends(require_admin)`
  (`lead_routes.py:501`).
- **[BEHOBEN 2026-07-17] `POST /api/leads/unsubscribe` nahm eine beliebige E-Mail ohne
  Token/Auth** → jeder konnte jeden fremden Lead abmelden. Fix: signierter Unsubscribe-Token
  (`unsubscribe_token_for`, HMAC aus E-Mail + JWT_SECRET; `hmac.compare_digest`, fail-closed).
- **[BEHOBEN 2026-07-17] `POST /api/analyze-preview`: voller Scan ohne Rate-Limit** → DoS-/
  Kostenfläche (Playwright/LLM je Request). Fix: `dependencies=[Depends(rate_limit("analyze_preview", 3, 60))]`
  (`public_routes.py:1884`, 3/60s). Weiterhin bewusst ohne Auth (Funnel-Einstieg),
  s. [[scan-analyze-kern]].
- Das Waitlist-Rate-Limit ist **prozesslokal** (`defaultdict` im RAM), nicht Redis-basiert
  wie `dependencies.rate_limit` → überlebt keinen Neustart und greift nicht über mehrere
  Worker. Umstellung auf `rate_limit(...)` naheliegend.
- `GET /api/leads/waitlist` (Admin-CSV-Export) ist als TODO markiert (`lead_routes.py:241`).
- **[BEHOBEN 2026-07-17] `WaitlistJoinRequest.validate_source`:** die `allowed`-Menge listete
  `"complyo.de"` doppelt (Rest einer `.tech`→`.de`-Umstellung, vgl. [[live-domains]]) →
  Duplikat entfernt, Menge jetzt `{"early-access", "complyo.de", "landing"}`.
