# Gesetzesänderungs-Überwachung (Legal Change Monitoring)

**Stand:** 2026-09-28 · **Status:** 🟢 live (Kette läuft täglich; offen: Mail-Benachrichtigung ohne Cron, Auto-Rechtstexte unvollständig)

## Ziel
Gesetzesänderungen (DSGVO, TTDSG/TDDDG, BFSG, AI Act, UWG, Widerrufsrecht, PPWR) automatisch
erfassen, Dringlichkeit und Rechtsbereich per KI bestimmen, betroffene Nutzer benachrichtigen
und daraus Folgeaktionen auslösen: Rescan der überwachten Websites, neue deklarative
Website-Prüfungen ([[scan-analyze-kern]]) und Neuerzeugung betroffener Rechtstexte
([[legal-text-generator]]).

## Architektur (end-to-end)

### 1. Erfassung
- **RSS-News (Quelle der Erkennung):** `backend/news_service.py`, `NewsService.fetch_all_feeds()`
  über `rss_feed_sources` (13 aktive Feeds, live gezählt), schreibt in `legal_news`.
  Cron täglich 06:00 (`backend/cronjobs/fetch_news.py`, nur noch RSS, seit `cd044a9` keine
  zweite Monitor-Ausführung mehr). HTTP 202 gilt seit `a1ba3d8` nicht mehr als Fehler.
  Zwei Feeds fallen dauerhaft aus (Log 2026-09-27): „EU Parlament Digitales“ (Bot-Schutz,
  HTTP 202 challenge) und „Datenschutz.org“ (kein gültiger Feed).
- **Erkennung per LLM, gegroundet:** `backend/legal_change_monitor.py`
  - `monitor_legal_changes()` (Z. 152) liest über `_fetch_news_since_last_run()` (Z. 182) die
    neuen `legal_news`-Zeilen seit dem letzten erfolgreichen Lauf (`legal_monitoring_logs.scan_date`,
    max. 50). Ohne neue News kein LLM-Aufruf. Keine freie LLM-Recherche mehr; die Quellen-Map
    in `__init__` (Z. 143) ist ungenutzter Rest.
  - `_build_monitoring_prompt()` (Z. 606), `_call_ai_api()` (Z. 574) läuft über `ki_zugang.chat`
    (Budgetdeckel), Modell `OPENROUTER_LEGAL_MODEL`, in Prod nicht gesetzt, also Standard
    `anthropic/claude-sonnet-4.5` (Z. 585).
  - `_parse_legal_changes()` (Z. 734) mit Pro-Objekt-Salvage bei kaputtem JSON (Log 2026-09-27:
    „Salvage: 1 Änderungen aus invalidem JSON geborgen“).
  - Datenmodell: `LegalArea` (8 Werte: `cookie_compliance`, `datenschutz`, `impressum`,
    `barrierefreiheit`, `wettbewerbsrecht`, `verbraucherschutz`, `ai_act`, `verpackung`),
    `ChangeSeverity` (`critical|high|medium|low|info`).
- **EUR-Lex:** trägt zur Erkennung nichts bei.
  - `backend/cronjobs/eurlex_crawler.py` läuft montags 04:00 (`docker run ... legal-backend`) und
    pflegt nur den Gesetzeskorpus unter `knowledge/laws/<sprache>/<AKT>/` für die
    Wissensbasis ([[knowledge-base-gesetzes-vault]]). Neuabruf erst nach 30 Tagen
    (`EURLEX_MAX_AGE_DAYS`), deshalb meldeten die Läufe vom 07., 14. und 21.09. je
    „0 Rechtsakte, 0 verworfen, 0 Fehler“; Stand der Akte 2026-08-28.
  - `backend/eulex_service.py` wird nur aus `knowledge/knowledge_ingestion_service.py`
    (`fetch_from_eulex`) und `main_production.py` (Init, Z. 821) angesprochen. In `legal_news`
    steht keine Zeile mit EUR-Lex-Quelle (live, SELECT). Der Feed „EUR-Lex Neuigkeiten“ im
    Wissens-Updater (07:00) antwortete vom 22. bis 26.09. mit HTTP 202, am 27.09. mit 0 Treffern.

### 2. Klassifikation
- Dringlichkeit und Rechtsbereiche bestimmt das Erkennungs-LLM selbst (Felder `severity`,
  `affected_areas` im Prompt, Z. 676 ff.), im 05:00-Lauf.
- `backend/ai_legal_classifier.py` (Modell fest `anthropic/claude-3.7-sonnet:beta`, Z. 149)
  hängt **nicht** in der Cron-Kette. Aufrufer nur `ai_legal_routes.py` (`POST
  /api/legal-ai/updates/{id}/classify`, Z. 475, Rate-Limit 5/60 s), `risk_radar_routes.py`,
  `compliance_engine/scanner.py`. Live: 11 Zeilen in `ai_classifications`, letzte 2026-08-12;
  nur 8 von 413 `legal_updates` tragen eine `classification_id`.
- Feedback-Learning (`backend/ai_feedback_learning.py`, `ai_classification_feedback`,
  `ai_learning_cycles`): im Code vorhanden, Nutzung nicht geprüft.

### 3. Persistenz und Fan-out
`LegalChangeMonitor.monitor_and_persist()` (Z. 282) je erkannter Änderung:
- `_save_change_to_db()` (Z. 372) → `legal_updates`. Dedup über normalisierten Titel ohne
  Datumsfenster (früher `published_at::date`, erzeugte Dauer-Duplikate).
- `LegalUpdateIntegration.process_new_legal_update()`
  (`backend/compliance_engine/legal_update_integration.py`, Z. 317):
  1. `RuleVersioningService.find_rules_affected_by_legal_update()`
     (`compliance_engine/rule_versioning_service.py`, Z. 238) liest `compliance_risk_matrix.category`
     (Alias `issue_category`), Keywords über `keywords_for_rule_category()` samt
     `RULE_CATEGORY_ALIASES`; danach `bump_rule_version()` → `rule_changelog` (live 337 Zeilen).
     Logs 23. bis 25.09.: 0 bis 2 Regeln je Update.
  2. `_flag_websites_for_rescan()` (Z. 429) markiert **alle** aktiven `tracked_websites`
     (bewusst ohne Kategorie-Auswahl), nicht bei Duplikaten (Guard seit 15.09.).
     Abgearbeitet von `cronjobs/website_monitor.py` (04:30, Vollscan bei `rescan_required`)
     und nach jedem Scan in `public_routes.py:522` zurückgesetzt.
  3. `create_scan_notification_for_users()` (Z. 263) → `user_legal_notifications`
     (`rescan_required`), nicht bei Duplikaten. Log 2026-09-27: „6 User über Legal Update #805
     benachrichtigt“.
- Rechtstext-Neuerzeugung `on_legal_change()` (Z. 233), **nur bei `high`/`critical`**
  (Gate in `monitor_and_persist`), siehe Abschnitt 4.
- `_generate_declarative_check()` (Z. 258) → `compliance_engine/check_generator.py`
  `generate_check_for_legal_update()` (Z. 383): neue Prüfung in `compliance_checks`
  (`source_legal_update_id`). Status nach `_auto_activate()` (Z. 237); in Prod
  `AUTO_ACTIVATE_GENERATED_CHECKS=false` → `pending_review`. Safety-Governor: `critical` nie
  automatisch aktiv (`2858edf`). Qualitäts-Gate und Themen-Dedup (`25efcb9`, `823cb66`).
  Live aus Rechtsupdates: 33 `active`, 9 `pending_review`, 127 `disabled`.
- Ausführung der Prüfungen: `compliance_engine/declarative_check_runner.py`
  (`DeclarativeCheckRegistry` lädt `status='active'`, `run_declarative_checks()`), aufgerufen
  aus `compliance_engine/scanner.py`.
- Scan-Anreicherung: `scanner.py:1144` wendet aktive Updates über
  `apply_updates_to_scan_results()` an. Lief bis `5df1aca` (10.09.) nie, weil der Dienst per
  Wert importiert wurde. Seit `f140714`/`47f12e6` (15./16.09.) hängt ein Update nur noch an
  Befunden seiner Kategorie und hebt keine Entwarnungen und keinen Gesamtrisiko-Aufschlag mehr an.

### 4. Auto-Update der Rechtstexte → [[legal-text-generator]]
- `on_legal_change()` ruft `get_legal_text_generator(db_pool).regenerate_affected_users(
  affected_areas=..., legal_update_id=..., severity=...)`. Auflösung Bereich → Dokumenttyp
  über `LEGAL_AREA_TO_DOCUMENT_TYPES` (Wächter `tests/test_legal_area_mapping.py`).
- Feuert live: Log 2026-09-25 `{'triggered': 1, 'affected_users': 1, 'affected_doc_types':
  ['cookie-policy', 'privacy'], 'legal_update_id': '804'}`. Die Verknüpfung steht in
  `generated_documents.metadata.legal_update_id` (die Spalte `legal_update_id` bleibt leer).
- Live: 11 automatisch erzeugte Datenschutzerklärungen (`regeneration_trigger='legal_update'`),
  **alle 11** mit fehlenden Pflicht-Markern; siehe Lücken.

### 5. Benachrichtigung
- **In-App:** `user_legal_notifications` über `create_scan_notification_for_users()`; live 1.467
  Zeilen, letzte 2026-09-27 05:00.
- **E-Mail:** `backend/legal_notification_service.py`, `process_new_legal_changes()` (Z. 35)
  liest `legal_news` (severity `critical`/`warning`, 7 Tage) und schreibt
  `legal_change_notifications`; Empfänger über `users.is_verified` (Z. 109, Fix `98d1204`).
  `demo_mode` (Z. 33): SMTP-Zugang ist in Prod gesetzt (`SMTP_USERNAME`, `SMTP_PASSWORD`
  vorhanden, `ENVIRONMENT=production`), also kein Demo-Modus. Fiele er doch an, liefert
  `_send_email()` (Z. 399) in Prod jetzt `False` statt vorgetäuschtem Erfolg.
  **Aufruf aber nur manuell**: `POST /api/legal-notifications/process-new`
  (`legal_notification_routes.py:248`) oder `cronjobs/legal_news_cronjob.py`, der in keinem
  Cron steht. Live: `legal_change_notifications` hat 0 Zeilen.
- **UI:** `dashboard-react/src/components/dashboard/LegalNews.tsx` → `GET /api/legal/news`,
  `GET /api/legal-ai/updates`, `POST /api/legal-ai/feedback` (nicht erneut geprüft).
- **Endpunkte:** `/api/legal-changes/*` (14, `legal_change_routes.py`), `/api/legal-ai/*`
  (12, `ai_legal_routes.py`), `/api/legal-notifications/*` (7), `/api/legal/*` (4,
  `legal_news_routes.py`). Die Benachrichtigungs- und Wirkungsanalyse-Endpunkte antworten erst
  seit `5df1aca` (vorher dauerhaft 503 bzw. leer).

## Läuft das produktiv?
**Ja.** Host-Crontab (root, nur lesend mit `crontab -l` geprüft):
- `0 4 * * 1` EUR-Lex-Korpus (`docker run ... cronjobs/eurlex_crawler.py`) → `/var/log/complyo-eurlex.log`
- `0 5 * * *` `docker exec complyo-backend python3 /app/cronjobs/legal_change_monitor_cron.py`
  → `/var/log/complyo-legal-monitor.log`; schreibt je Lauf eine Zeile `legal_monitoring_logs`
  (live 48 × `completed`, letzte 2026-09-27 05:00).
- `0 6 * * *` `cronjobs/fetch_news.py` (nur RSS) → `/var/log/complyo-news-fetch.log`
- `30 4 * * *` `cronjobs/website_monitor.py` arbeitet `rescan_required` ab.
- Nicht im Cron: `cronjobs/legal_news_cronjob.py` (E-Mail-Benachrichtigung, Digest).
- Letzte Läufe: 2026-09-25 „8 erkannt, 8 neu, 5 neue Prüfungen“; 2026-09-26 „0 erkannt“;
  2026-09-27 „1 erkannt, 1 neu“, Update #805, 6 Sites zum Rescan markiert.
- Fehler seit Juli: 2026-09-05 OpenRouter 402 (Guthaben), 2026-09-03/04
  `template_version does not exist` in der Neuerzeugung, seither nicht mehr im Log.
- Systemd: nur `complyo-widerruf-critical.timer`, zuletzt 2026-06-19, anderer Zweck.

## DB
Schema: Alembic-Baseline `backend/alembic/versions/20260717_baseline_2026_07.py` (Dump
`backend/alembic/baseline_schema.sql`) plus Folgerevisionen, u.a. 0006 (Regel-Versionierung:
`rule_version`, `valid_from`, `is_active` an `compliance_risk_matrix`, Tabelle `rule_changelog`).
Archiv-SQL unter `backend/migrations/_archive_pre_baseline/` nicht anwenden.
- `legal_updates` (`baseline_schema.sql:2519`), live 413 Zeilen, letzte 2026-09-27.
  Schreiber nur `_save_change_to_db()`.
- `legal_news` 565 Zeilen, `rss_feed_sources` 13 aktiv, `user_legal_notifications` 1.467,
  `legal_change_notifications` 0, `ai_classifications` 11, `rule_changelog` 337,
  `legal_monitoring_logs` 48.
- `legal_changes`: 0 Zeilen. Der einzige Beispieldatensatz (erfundene „Cookie-Banner-Pflicht“)
  wurde mit `5df1aca` entfernt; nichts im Code schreibt dorthin.

## Bekannte Lücken / Offen
- **Auto-Rechtstexte ersetzen den aktiven Text durch unvollständige Fassungen.** Alle 11
  automatisch erzeugten Datenschutzerklärungen fehlen Pflicht-Marker (Log 2026-09-25: „fehlende
  Pflicht-Marker: Betroffenenrechte, Zwecke der Verarbeitung, Beschwerderecht bei der
  Aufsichtsbehoerde“). `legal_text_generator` speichert trotzdem mit `is_active=true` und
  deaktiviert die Vorgängerfassung; aktive Fassung live mit 3 fehlenden Markern. Gehört zur
  Gegenseite [[legal-text-generator]].
- **E-Mail-Benachrichtigung läuft nie automatisch.** SMTP ist gesetzt, aber
  `process_new_legal_changes` steht in keinem Cron; `legal_change_notifications` ist leer.
- **`POST /api/legal-notifications/process-new` ist nicht auf Admins beschränkt**: Docstring
  sagt „Admin only“, Dependency ist nur `get_current_user` (Z. 251). Jedes Konto kann die
  Mailwelle an alle verifizierten Nutzer anstoßen.
- **Zwei RSS-Quellen tot** (EU Parlament Digitales, Datenschutz.org): ersetzen oder abschalten.
- **EUR-Lex liefert keine Änderungsmeldungen**, nur Korpus. Wer „EUR-Lex-Überwachung“ erwartet,
  bekommt sie nicht.
- **KI-Klassifikator hängt nicht in der Kette** und nutzt ein festes Altmodell
  (`claude-3.7-sonnet:beta`); `classification_id` bleibt für neue Updates leer.
- **Erkennung bleibt LLM-Auslegung** von RSS-Texten; Prüfungen landen deshalb als
  `pending_review` und brauchen Admin-Freigabe (9 offen).
- **Rescan-Markierung trifft bei jedem neuen Update alle aktiven Sites** (bewusst, Begründung
  im Code), damit bei täglichen Updates praktisch täglich Vollscans.
- **Rate-Limit** nur auf den drei teuren `/api/legal-ai/*`-Routen (Z. 475/1023/1057).
- `scripts/setup_legal_news.sh` zeigt weiter auf `/opt/projects/saas-project-2/backend`
  (Z. 53/58/92): obsolet.
- **Behoben:** `issue_category`-Abbruch in der Regel-Versionierung (letzter Fehler 2026-07-29,
  Fix `f95bfe7` mit Revision 0006); tote Dienstbindung in Scanner und Routen (`5df1aca`);
  Legal-Mail-Empfänger über `email_verified` (`98d1204`); doppelter Monitor-Lauf (`cd044a9`);
  Update-Aufschlag auf alle Befunde (`f140714`, `47f12e6`).
- `backend/_archive_pre_baseline/classify_new_updates_v3.py`: toter Code, liegt weiter im Archiv.
