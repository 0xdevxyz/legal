# AI-Act-Compliance (ComplyoAI Guard)

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Kostenpflichtiges Add-on (`comploai_guard`, 99 €/Monat): Register aller eingesetzten
KI-Systeme, automatische Risiko-Einstufung nach EU AI Act (verboten / hoch / begrenzt /
minimal), Compliance-Scan gegen die Artikelpflichten, Generierung der AI-Act-Pflichtdoku
(Risk Assessment, Technische Dokumentation, Konformitätserklärung) inkl. Upload/
Versionierung, Zeitplan-Scans und E-Mail-/In-App-Alerts bei Score-Verschlechterung.
Abgrenzung: reguliert **KI-Systeme des Kunden**, nicht Website-Texte ([[legal-text-generator]])
und nicht Rechtsänderungen ([[legal-change-monitoring]]).

## Architektur (end-to-end)
- **Routes:** `backend/ai_compliance_routes.py` (Prefix `/api/ai`, 27 Endpunkte),
  registriert in `backend/main_production.py:616`.
  - Auth über die kanonische Dependency `dependencies.get_current_user`
    (`ai_compliance_routes.py:81` → `get_current_user_id`).
  - **Register:** `POST/GET /systems`, `GET/PUT/DELETE /systems/{id}`.
  - **Scan:** `POST /systems/{id}/scan` (`:337`), `GET /systems/{id}/scans`, `GET /scans/{id}`.
  - **Katalog:** `GET /act/requirements`, `GET /act/requirements/{risk_category}` — liest
    `ai_act_analyzer.risk_categories` / `.high_risk_requirements` (statisch, ohne Auth).
  - **Doku:** `GET /systems/{id}/documentation` (Soll/Ist), `POST /systems/{id}/documentation/
    generate` (`:656`), `.../documentation/list`, `.../documentation/upload` (Multipart →
    `file_storage_service`), `GET /documentation/{id}/download` (HTML/PDF),
    `GET /documentation/file/{path}`, `GET /documentation/{id}/versions`, `DELETE /documentation/{id}`.
  - **Zeitplan:** `POST/GET/DELETE /systems/{id}/schedule` (`:1296`) — `daily|weekly|monthly`
    + `schedule_hour`, `next_run_at` wird beim Anlegen berechnet.
  - **Alerts:** `GET/PUT /notifications`, `/notifications/{id}/read`, `/notifications/read-all`,
    `GET/PUT /settings/alerts`. **Stats:** `GET /stats`.
- **Klassifizierung:** `backend/ai_act_analyzer.py` — **zweistufig**:
  - Stufe 1 regelbasiert: `classify_risk_category` (`:242`) prüft `prohibited_keywords`
    (`:250`, 4 Kategorien: social scoring, Manipulation, Echtzeit-Biometrie, Emotionserkennung)
    gegen `name+description+purpose+domain`; **≥2 Keyword-Treffer** → sofort
    `risk_category="prohibited"`, confidence 0.95, ohne KI-Aufruf.
  - Stufe 2 KI: sonst `_build_classification_prompt` → `_call_ai_api` (`:580`) gegen
    **OpenRouter**, Modell `anthropic/claude-3.5-sonnet`, `temperature=0.3`, JSON-Antwort.
    Bei Fehler konservativer Fallback `risk_category="high"`, confidence 0.3.
  - `check_compliance(ai_system, risk_category)` (`:303`) → Score + `findings` /
    `requirements_met` / `requirements_failed`; `get_required_documentation` (`:339`) liefert
    die je Kategorie nötigen Dokumente.
- **Doku-Generator:** `backend/ai_act_doc_generator.py` — **kein KI-Aufruf**, Jinja2-
  Templates + `pdfkit`: `generate_risk_assessment_report` (`:26`, Art. 9),
  `generate_technical_documentation_template` (`:161`, Art. 11), `generate_conformity_declaration`
  (`:322`). Das sind die drei einzigen erlaubten `document_type`-Werte
  (`ai_compliance_routes.py:713`). Ergebnis-HTML → `ai_documentation.content` als
  `{"html": ...}`.
  - **`backend/ai_document_generator.py` gehört NICHT zu diesem Modul** — er erzeugt
    Impressum/Datenschutz via OpenRouter (`self.model = "anthropic/claude-3.5-sonnet"`,
    `:20`) und wird nur von `ai_legal_routes.py:1160` genutzt → siehe [[legal-text-generator]].
- **Worker:** `backend/ai_compliance_worker.py` — kein Cron, sondern asyncio-Endlosschleife
  (`check_interval = 60` s), gestartet in `main_production.py:493` via
  `asyncio.create_task(start_ai_compliance_worker())` (im Web-Prozess, nicht separat).
  - `process_scheduled_scans` holt fällige `ai_scheduled_scans` (`next_run_at <= now`),
    re-klassifiziert, schreibt `ai_compliance_scans` und setzt `next_run_at` neu.
  - `process_scan_reminders` erinnert an lange nicht gescannte Systeme.
- **Benachrichtigungen:** `backend/ai_compliance_notification_service.py` — SMTP
  (`smtplib`, `SMTP_HOST`/`SMTP_USERNAME`…); ohne Credentials **Demo-Mode**: E-Mails werden
  nur geloggt (`:27`, `:34`). `send_compliance_alert` (Score-Abfall),
  `send_high_risk_alert`, `send_scan_reminder`. Parallel schreibt der Worker
  `ai_compliance_notifications` für die In-App-Liste.
- **Frontend:** `dashboard-react/src/app/ai-compliance/` — `page.tsx` (Übersicht/Stats),
  `systems/new/page.tsx`, `systems/[id]/page.tsx` (Detail, Scan, Doku, Zeitplan),
  `upgrade/page.tsx` (Add-on-Kauf), `layout.tsx`.

## DB
Alle Tabellen sind in der Alembic-Baseline `backend/alembic/baseline_schema.sql` (angewendet
über `backend/alembic/versions/20260717_baseline_2026_07.py`) enthalten — keine Lücke:
- `ai_systems` (`:1506`) — Register; `data_types`/`affected_persons` als JSONB.
- `ai_compliance_scans` (`:1404`) — Scan-Ergebnisse (`findings`, `requirements_met/failed` JSONB).
- `ai_documentation` (`:1428`) — generierte + hochgeladene Dokumente, `content` JSONB,
  `version` (Versionierung über `ai_system_id` + `document_type`).
- `ai_scheduled_scans` (`:1487`), `ai_compliance_notifications` (`:1383`),
  `ai_compliance_alert_settings` (`:1364`).
- `user_addons` (`:2962`) — Add-on-Besitz + `limits` (JSONB).
- JSONB-Regel eingehalten: alle Writes gehen über `json.dumps()` (Routes `:137`, `:411-416`,
  `:737`, `:938`; Worker `:230-234`) — siehe Merkregel asyncpg-JSONB-Codec.

## Voraussetzungen
- **Add-on `comploai_guard`** — Definition in `backend/addon_payment_routes.py:64`
  (`MONTHLY_ADDONS`, `price_monthly: 99`, Stripe-Preis via `STRIPE_PRICE_COMPLOAI_GUARD`);
  Kauf über `POST /subscribe/{addon_key}`, Stripe-Webhook schreibt `user_addons`.
- Gate im Modul: `db_service.check_user_addon(user_id, "comploai_guard")`
  (`database_service.py:367`, prüft `status='active'` + `expires_at`) plus
  `get_addon_limits` (`:386`) → `limits["ai_systems"]` (Default 10, `-1` = unbegrenzt).
  Geprüft in `POST /systems` (`:95`), `GET /systems` (`:169`), `GET /stats` (`:607`).
- `backend/license_check.py` ist **nicht** beteiligt (Site-Lizenzen für Widget/Banner).
- Details zu Plänen/Add-ons: [[billing-plans-addons]].
- `OPENROUTER_API_KEY` für die Klassifizierung; SMTP-Vars für echte Alerts.

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] Worker rief nicht existierende Methode**: `ai_compliance_worker.py`
  rief `ai_act_analyzer.classify_system(...)` — existiert nicht (heißt `classify_risk_category`)
  — und `check_compliance(system_data, classification)` gegen die Signatur
  `check_compliance(ai_system: AISystem, risk_category: str)`. Geplante Scans liefen in einen
  `AttributeError`, den `logger.error` verschluckte → Zeitplan-Feature war faktisch tot. Fix:
  Worker baut jetzt ein `AISystem`-Modell, ruft `classify_risk_category` und übergibt
  `classification_model.risk_category` (str) an `check_compliance`; `logger.error` → `logger.exception`
  (Stacktrace sichtbar). Abgesichert durch `tests/test_ai_compliance_worker_contract.py`.
- **Add-on-Gate lückenhaft**: `POST /systems/{id}/scan`, `.../documentation/generate`,
  `.../schedule` und alle Doku-/Notification-Routen prüfen `check_user_addon` **nicht** —
  nur Ownership. Wer das Add-on kündigt, kann Bestandssysteme weiter scannen und Doku
  generieren.
- **Rate-Limiting teilbehoben (2026-07-17):** `POST /systems/{id}/documentation/generate` trägt
  jetzt `Depends(rate_limit("ai_doc_generate", 5, 60))` (`ai_compliance_routes.py:656`).
  `POST /systems/{id}/scan` (`:337`) ist **weiterhin ungedrosselt** — offener OpenRouter-Kostenpfad
  (vgl. `planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` 1.4).
- **Ownership: keine Lücke** — alle systemspezifischen Queries filtern `user_id = $2` bzw.
  joinen `ai_systems s ON ... AND s.user_id = $2` (`:222`, `:348`, `:569`, `:669`, `:783`,
  `:850`, `:893`, `:996`, `:1043`, `:1071`, `:1306`).
- Prohibited-Heuristik ist grob: 2 lose Keyword-Treffer (z. B. „Emotion" + „Schule")
  genügen für die härteste Einstufung → False-Positive-Risiko, keine Kontextprüfung.
- `documentation_status` wird beim Scan als leeres `{}` geschrieben
  (`ai_compliance_routes.py:412`, Kommentar „to be implemented").
- Notification-Versand läuft ohne SMTP-Credentials still im Demo-Mode (nur Log) — ob in
  Prod gesetzt: zu prüfen.
- Worker läuft im Web-Prozess: bei mehreren Backend-Replicas würden geplante Scans
  mehrfach ausgeführt (kein Locking auf `ai_scheduled_scans`).
