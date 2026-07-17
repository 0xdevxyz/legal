# Gesetzesänderungs-Überwachung (Legal Change Monitoring)

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Gesetzesänderungen (DSGVO, TTDSG/ePrivacy, BFSG, AI Act, UWG, Widerrufsrecht) automatisch
erfassen, den **Handlungsbedarf per KI klassifizieren**, betroffene User benachrichtigen und
daraus Folgeaktionen auslösen: neue deklarative Website-Prüfungen ([[scan-analyze-kern]])
und Re-Generierung betroffener Rechtstexte ([[legal-text-generator]]).
Die Erfassung läuft produktiv; der **Auto-Update-Trigger für Rechtstexte feuert seit
2026-07-17 tatsächlich** (Vokabular-Mismatch behoben, siehe „Bekannte Lücken").

## Architektur (end-to-end)

### 1. Erfassung — zwei parallele Pipelines
- **KI-Recherche (primär):** `backend/legal_change_monitor.py`
  - `LegalChangeMonitor.monitor_legal_changes()` (Z. 142) → `_build_monitoring_prompt()` (Z. 521)
    lässt ein LLM freie Recherche über Quellen wie `eur-lex.europa.eu`, BfDI, Bundesanzeiger
    machen. **Keine echten Crawler** — die Quellen-Map (Z. 134) ist nur Prompt-Kontext.
  - `_call_ai_api()` (Z. 485) → OpenRouter, Modell `os.getenv("OPENROUTER_LEGAL_MODEL",
    "anthropic/claude-sonnet-4.5")` (Z. 495). Antwort → `_extract_json()` /
    `_parse_legal_changes()` (Z. 613) → `LegalChange`-Objekte.
  - Datenmodell: `LegalArea` (7 Werte: `cookie_compliance`, `datenschutz`, `impressum`,
    `barrierefreiheit`, `wettbewerbsrecht`, `verbraucherschutz`, `ai_act`),
    `ChangeSeverity` (`critical|high|medium|low|info`).
- **RSS-News (sekundär):** `backend/news_service.py` — `NewsService.fetch_all_feeds()` über
  `rss_feed_sources` (14 aktive Feeds), schreibt in `legal_news`.
- **EUR-Lex (SPARQL):** `backend/eulex_service.py` — `EULexService.fetch_recent_changes()`
  (Z. 55) → `_query_eurlex_changes()` (CELLAR-SPARQL) → `_save_legal_change()` (Z. 167)
  schreibt in **`legal_news`**, nicht in `legal_updates`. Eingebunden über
  `backend/main_production.py` und `backend/knowledge/knowledge_ingestion_service.py`
  ([[knowledge-base-gesetzes-vault]]). **Läuft in keinem Cron** — nur On-Demand.

### 2. Klassifikation
- `backend/ai_legal_classifier.py` — `self.model = "anthropic/claude-3.7-sonnet:beta"`
  (Z. 148) via OpenRouter. Klassifiziert je Update:
  - `ActionType` (8 Werte: `scan_website`, `update_cookie_banner`, `update_privacy_policy`,
    `update_impressum`, `check_accessibility`, `review_manually`, `consult_legal`,
    `information_only`), `DecisionConfidence` (`high|medium|low`),
    `ActionRecommendation` (Priorität 1–10, Button-Text/Farbe/Icon, `requires_paid_plan`),
    `NormReference`/`Factor` (XAI-Erklärung).
  - Persistenz: `ai_classifications`; `legal_updates.classification_id` referenziert sie.
  - Aufrufer: `backend/ai_legal_routes.py`, `backend/risk_radar_routes.py`,
    `backend/compliance_engine/scanner.py`.
- **Feedback-Learning:** `backend/ai_feedback_learning.py` — `AIFeedbackLearning`
  - `record_feedback()` (Z. 103) → `ai_classification_feedback` (User bestätigt/verwirft eine
    KI-Empfehlung; UI: Feedback-Buttons in `LegalNews.tsx` → `POST /api/legal-ai/feedback`).
  - `analyze_classification_performance()`, `get_learning_insights()`,
    `get_optimization_suggestions()`; `_trigger_learning_if_needed()` (Z. 413) →
    `_adapt_prompts_from_feedback()` → `_run_learning_cycle()` → `ai_learning_cycles`.

### 3. Persistenz + Fan-out
- `LegalChangeMonitor.monitor_and_persist()` (Z. 209) ist die Kette:
  - `_save_change_to_db()` (Z. 286) → `legal_updates`; Dedup über `title` + `published_at::date`.
  - `LegalUpdateIntegration.process_new_legal_update()` — `backend/compliance_engine/legal_update_integration.py` (Z. 306):
    Regel-Zuordnung, `_extract_affected_categories()`, `_flag_websites_for_rescan()` (Z. 389),
    `create_scan_notification_for_users()` (Z. 252) → In-App-Benachrichtigung.
    `get_relevant_updates_for_category()` / `apply_updates_to_scan_results()` /
    `get_fix_priority_adjustments()` hängen Legal-Updates an laufende Scans.
  - `on_legal_change()` (Z. 162) → **Auto-Update-Trigger**, siehe unten.
  - `_generate_declarative_check()` (Z. 185) → `compliance_engine/check_generator.py`
    `generate_check_for_legal_update()` erzeugt per LLM eine **neue deklarative Prüfung**
    in `compliance_checks` (`source_legal_update_id` FK). Status via
    `AUTO_ACTIVATE_GENERATED_CHECKS` (`active` vs. `pending_review`). Funktioniert produktiv.

### 4. Auto-Update-Trigger für Rechtstexte → [[legal-text-generator]]
- `legal_change_monitor.py:162` `on_legal_change(change, saved_id)` →
  `get_legal_text_generator(db_pool).regenerate_affected_users(affected_areas=..., legal_update_id=..., severity=...)`
  (seit 2026-07-17 `affected_areas` statt `affected_laws`).
- **Severity-Gate:** nur `>= medium` (`severity_order`-Index-Vergleich, Z. 373).
- **Area→DocType-Map** (`legal_text_generator.LEGAL_AREA_TO_DOCUMENT_TYPES` +
  `resolve_document_types()`): mappt jetzt direkt die `LegalArea`-Werte
  (`datenschutz`/`cookie_compliance` → PRIVACY + COOKIE_POLICY, `impressum`/`barrierefreiheit`
  → IMPRINT, `verbraucherschutz` → TOS + WITHDRAWAL, `wettbewerbsrecht` → TOS); zusätzlich
  Alias-Map für Gesetzesnamen. Details der Generierung stehen in [[legal-text-generator]].

### 5. Benachrichtigung
- **In-App:** `legal_update_integration.create_scan_notification_for_users()` →
  `user_legal_notifications` / `ai_compliance_notifications`. Läuft (Log: „6 User über
  Legal Update #514 benachrichtigt").
- **E-Mail:** `backend/legal_notification_service.py` — `process_new_legal_changes()` (Z. ~403),
  `_send_email()`, Confirm/Dismiss per Token. **Nur manuell auslösbar** über
  `backend/legal_notification_routes.py:251` (`BackgroundTasks`), in keinem Cron.
- **UI:** `dashboard-react/src/components/dashboard/LegalNews.tsx` → `GET /api/legal/news`,
  `GET /api/legal-ai/updates`, `POST /api/legal-ai/feedback`.
- **Endpunkte:** `/api/legal-changes/*` (12, `legal_change_routes.py`), `/api/legal-ai/*` (12,
  `ai_legal_routes.py`), `/api/legal-notifications/*` (7), `/api/legal/*` (4, `legal_news_routes.py`).

## Läuft das produktiv?
**Ja — Erfassung + Check-Generierung laufen täglich; der Rechtstext-Auto-Update feuert seit
2026-07-17 ebenfalls (Vokabular-Mismatch behoben).**
- Cron liegt **im Host-Crontab** (`crontab -l` als root), nicht im Container — der
  Backend-Container hat gar kein `cron`/`crontab` installiert. Beide Zeilen nutzen `docker exec`:
  - `0 5 * * *` → `cronjobs/legal_change_monitor_cron.py` → `LegalChangeMonitor.monitor_and_persist()`
    → Log `/var/log/complyo-legal-monitor.log`.
  - `0 6 * * *` → `cronjobs/fetch_news.py` → (a) `NewsService.fetch_all_feeds()`,
    (b) `run_legal_intelligence_pipeline()` = **nochmal** `monitor_and_persist()` →
    `/var/log/complyo-news-fetch.log`. Der Monitor läuft dadurch 2×/Tag.
- Letzter Lauf 2026-07-17 05:01: „7 erkannt, 7 neu, 1 neue Prüfungen erzeugt"
  (`newsletter-abmeldung-pflicht`, status=active). Der 06:00-Lauf: 14 Feeds, 5 neue Items.
- `cronjobs/legal_news_cronjob.py`, `cronjobs/eurlex_crawler.py` und
  `legal_notification_service.process_new_legal_changes` stehen in **keinem** Cron.
- Keine systemd-Timer für Legal-Monitoring (`complyo-widerruf-critical.timer` existiert, ist
  aber seit 2026-06-19 nicht mehr gelaufen — separater Zweck, zu prüfen).
- `main_production.py` startet nur `init_legal_monitor(openrouter_key)` (Z. 656) — reine
  Objekt-Initialisierung für die Routes, **kein** Background-Task/Scheduler.

## DB
Alle Tabellen sind Teil der Alembic-Baseline `backend/alembic/versions/20260717_baseline_2026_07.py`
(Wrapper; das Schema selbst liegt als pg_dump in `backend/alembic/baseline_schema.sql`) —
Single Source of Truth. Die alten SQL-Dateien unter `backend/migrations/_archive_pre_baseline/`
(u.a. `migration_legal_changes.sql`, `add_legal_news_sources.sql`) **nicht mehr anwenden**.
- **`legal_updates`** (`baseline_schema.sql:2519`) — zentrale Tabelle:
  `id, update_type, title, description, severity, action_required, source, published_at,
  created_at, effective_date, url, classification_id → ai_classifications(id),
  auto_classified, classification_override`.
  - **Schreiber:** nur `legal_change_monitor._save_change_to_db()`.
  - **Leser:** `legal_update_integration`, `ai_legal_routes`, `legal_change_routes`,
    `legal_notification_service`, `risk_radar_routes`; `compliance_checks.source_legal_update_id`
    und `generated_documents.legal_update_id` referenzieren sie.
- Weitere: `legal_news` (RSS + EUR-Lex), `rss_feed_sources`, `legal_changes`,
  `legal_change_impacts`, `legal_change_notifications`, `legal_monitoring_logs`,
  `legal_updates_archive`, `user_legal_notifications`, `ai_classifications`,
  `ai_classification_feedback`, `ai_learning_cycles`, `ai_compliance_notifications`.

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] Auto-Update-Trigger feuerte nie — Vokabular-Mismatch (kritisch).**
  `on_legal_change()` übergab `LegalArea`-Werte (`datenschutz`, `cookie_compliance`, …), die
  `doc_type_map` erwartete aber Gesetzesnamen (`DSGVO`, `TTDSG`, …) → kein Substring-Match,
  **120 von 120** Regen-Läufen endeten mit `'no affected document types'`, nie wurde ein
  Rechtstext automatisch regeneriert. Fix (Gegenstück im Generator): neue SSOT
  `LEGAL_AREA_TO_DOCUMENT_TYPES` + `resolve_document_types()`; `on_legal_change` übergibt jetzt
  `affected_areas`. Wächter `tests/test_legal_area_mapping.py`. Siehe [[legal-text-generator]].
- **E-Mail-Benachrichtigung im `demo_mode` (verifiziert).**
  `legal_notification_service.py:32`: `self.demo_mode = not all([self.smtp_username, self.smtp_password])`.
  In Produktion sind `SMTP_USERNAME` und `SMTP_PASSWORD` **leer** → `_send_email()` (Z. ~403)
  loggt nur `[DEMO] Would send email to …` und gibt `True` zurück. **Es gehen keine Mails raus**;
  Aufrufer sehen fälschlich Erfolg. In-App-Benachrichtigungen sind nicht betroffen.
- **Live-SQL-Fehler bei jedem Lauf:** `rule_versioning_service.find_rules_affected_by_legal_update`
  bricht mit `UndefinedColumnError: column "issue_category" does not exist` ab
  (`backend/compliance_engine/rule_versioning_service.py:191/201/232` liest `issue_category`
  aus `compliance_risk_matrix`; die Spalte existiert dort in der Baseline nicht — nur auf
  `generated_fixes`). Folge: `0 rules, 0 sites` in jedem `process_new_legal_update`.
  Tabelle `compliance_rules` existiert in der Baseline gar nicht.
- **Zwei Pipelines, ein Tisch — Stolperfalle.** RSS/EUR-Lex schreiben nach `legal_news`,
  nur der `LegalChangeMonitor`-Pfad schreibt nach `legal_updates` und löst Regen +
  Check-Generierung aus. `scripts/setup_legal_news.sh` richtet **keine** Regenerierung ein.
- **`scripts/setup_legal_news.sh` hat hartkodierte Fremdpfade** `/opt/projects/saas-project-2/backend`
  (Z. ~40/51/57) — existiert im echten Repo (`/home/clawd/saas/legal`) nicht. Die vom Skript
  ausgegebenen Crontab-Zeilen (`legal_news_cronjob.py`, 4-stündlich + Digest 09:00) zeigen ins
  Leere und sind **nicht** installiert. Skript ist obsolet → entfernen oder korrigieren.
- **Kein Rate-Limiting auf `/api/legal-ai/*`** (12 LLM-Endpunkte in `backend/ai_legal_routes.py`):
  nur `Depends(get_current_user_id)`, kein `slowapi`/Limiter. Deckt sich mit
  `planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` 1.4. Kostenrisiko pro authentifiziertem User.
- **`eulex_service` und `cronjobs/eurlex_crawler.py` laufen in keinem Cron** — EUR-Lex-Daten
  kommen nur durch Zufall (On-Demand-Aufrufe) rein. Nutzen unklar → zu prüfen.
- **Monitor-Erkennung ist reine LLM-Recherche ohne Verifikation** — keine Quellenprüfung
  gegen echte Feeds, Halluzinationsrisiko bei `_parse_legal_changes()`. Generierte Checks
  sollten über `AUTO_ACTIVATE_GENERATED_CHECKS=false` (`pending_review`) laufen; im letzten
  Lauf wurde der Check mit `status=active` erzeugt → Flag-Zustand in Prod prüfen.
- `backend/classify_new_updates_v3.py` liegt in `backend/_archive_pre_baseline/` — toter Code.
