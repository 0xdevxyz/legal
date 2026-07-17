# DSGVO-Betroffenenrechte & Retention

**Stand:** 2026-07-17 · **Status:** 🔵 geplant (Code vorhanden, produktiv wirkungslos)

## Ziel
Compliance am eigenen Produkt: Auskunft (Art. 15/20), Löschung (Art. 17) und automatisierte
Aufbewahrungsbegrenzung (Art. 5 Abs. 1 lit. e) für die von Complyo selbst verarbeiteten Daten.

## Architektur (end-to-end)
- **Routes:** `backend/gdpr_api.py` — `gdpr_router` (Prefix `/api/gdpr`), Include
  `main_production.py:603`. **7 Endpunkte, alle live in `openapi.json`:**
  - `POST /request-deletion` — Body `{email, reason, confirmation}`; 400 ohne `confirmation`.
  - `POST /export-data` — Body `{email}`; Versand des Exports per
    `email_service.send_data_export_email` als `BackgroundTask`.
  - `GET /retention-info?email=` — Aufbewahrungsdaten zu einer E-Mail.
  - `POST /admin/update-retention`, `GET /admin/cleanup-status`, `POST /admin/run-cleanup` —
    geschützt durch `_verify_admin(admin_api_key)`: Query-Parameter gegen `ADMIN_API_KEY`;
    503 wenn die Env-Var fehlt, 401 bei Mismatch.
  - `GET /privacy-policy` — statische Metadaten (Kontakt `datenschutz@complyo.de`).
- **Service:** `backend/gdpr_retention_service.py` — Singleton `gdpr_service`,
  `GDPR_RETENTION_DAYS` (Default 730).
  - `perform_retention_cleanup()` — holt `get_leads_for_retention_cleanup()`, benachrichtigt,
    löscht via `delete_lead_permanently()`, arbeitet danach offene Löschanträge ab.
  - `request_data_deletion()` / `get_data_for_export()` — beide über
    `db_service.get_lead_by_email(email)`.
  - `start_automated_cleanup()` / `stop_automated_cleanup()` existieren, werden aber
    **nirgends aufgerufen** (verifiziert) → `is_running` in `/admin/cleanup-status` ist
    dauerhaft `False`. Der Löschlog (`self.deletion_log`) ist reiner Prozess-Speicher.
- **Background-Task:** `_daily_gdpr_cleanup()` in `backend/main_production.py:720-750`,
  gestartet mit `asyncio.create_task()` (Zeile 750). 60 s Delay, danach 24-h-Schleife über
  `db_pool`: expired `user_sessions`, inaktive `users` (>2 Jahre), `cookie_consent_logs`
  (>1 Jahr), `ai_call_logs` (>90 Tage), `email_verifications` (abgelaufen).
  Ruft `perform_retention_cleanup()` **nicht** auf — zwei getrennte Mechanismen.
- **`backend/backup_retention.py`** — 37-Zeilen-Standalone-Skript (`__main__`), das die drei
  Retention-DELETEs aus `_daily_gdpr_cleanup()` **wortgleich dupliziert**. Von keinem Modul,
  Dockerfile, Compose-Service oder systemd-Unit referenziert (verifiziert) → **toter Code**.

## DB
- Kein eigenes Schema; das Feature löscht ausschließlich in fremden Tabellen.
- `backend/alembic/baseline_schema.sql` / Revision `20260717_baseline_2026_07.py` sind die
  einzige Quelle der Wahrheit; `backend/migrations/_archive_pre_baseline/` (46 Dateien) ist gesperrt.
- **Vorhanden** in der Live-DB: `users`, `user_sessions`, `cookie_consent_logs`.
- **Nicht vorhanden** (verifiziert): `leads`, `ai_call_logs`, `email_verifications`,
  und damit auch `communication_log`/`lead_consents` (aus `delete_lead_permanently()`).

## Bekannte Lücken / Offen
- **`_daily_gdpr_cleanup()` läuft, löscht aber nichts (verifiziert).** Alle fünf Statements
  nutzen `DELETE ... RETURNING COUNT(*)` — in PostgreSQL unzulässig. Live-Log:
  `✅ Daily GDPR cleanup task scheduled`, danach exakt
  `WARNING: GDPR cleanup error: aggregate functions are not allowed in RETURNING`;
  0 Vorkommen von `GDPR cleanup: removed`. Die erste Anweisung wirft, der `except` fängt,
  schläft 24 h und scheitert erneut — **dauerhaft**. Fix: `RETURNING COUNT(*)` entfernen und
  die Trefferzahl aus dem `DELETE …`-Status-Tag lesen (`conn.execute`).
  Der identische Defekt steckt in `backend/backup_retention.py`.
- Selbst nach dem Fix bräche der Lauf an `ai_call_logs` / `email_verifications` — beide
  Tabellen existieren nicht.
- **Keine Auth, keine Ownership auf den Betroffenen-Endpunkten (verifiziert).**
  `POST /request-deletion` und `POST /export-data` identifizieren allein über eine
  E-Mail-Adresse im Body — keine Dependency, kein Token, kein Verifikations-Link.
  `GET /retention-info?email=` ebenso (live 422 = Validierung, kein 401). Faktischer Schutz
  ist nur die globale `CSRFMiddleware` (`main_production.py:238`), die alle POSTs ohne Token
  mit 403 abweist — **kein** Ownership-Nachweis. Der Export mildert sich dadurch, dass er an
  die angefragte Adresse geht; die **Löschung** hat keine solche Bremse. Selbe Klasse Lücke wie
  die am 2026-07-17 in `cookie_compliance_routes.py` geschlossenen 28 offenen Routen →
  Double-Opt-In-Token oder Auth-Dependency erforderlich.
- Praktisch entschärft ist beides derzeit nur dadurch, dass `leads` gar nicht existiert:
  `get_lead_by_email` läuft ins Leere, `/request-deletion` liefert „No data found",
  `/export-data` 404. Der gesamte `gdpr_retention_service` adressiert ein Datenmodell, das
  in der Baseline nicht mehr vorkommt — **zu klären**, ob es ersatzlos entfällt (dann Modul
  + Routen entfernen) oder auf `users`/[[lead-free-scan-funnel]] umgeschrieben wird.
- **Konkurrierende Retention-Mechanismen (3 Stück):** `_daily_gdpr_cleanup()` (läuft, wirkungslos),
  `gdpr_service.perform_retention_cleanup()` (nur manuell über `/admin/run-cleanup`) und
  `backup_retention.py` (tot). Zusätzlich existiert in
  `backend/cookie_compliance_routes.py:1716` `delete_expired_consents()` (SQL-Funktion
  `SELECT delete_expired_consents()`), die laut [[cookie-consent-management]] **nicht**
  automatisch läuft. `_daily_gdpr_cleanup()` würde `cookie_consent_logs` pauschal nach 1 Jahr
  löschen und damit die konfigurierbare Consent-Retention überstimmen — die Frist ist an zwei
  Stellen unterschiedlich definiert. Auf **einen** Mechanismus konsolidieren.
- `/admin/cleanup-status` meldet `is_running: false` und Statistiken aus dem
  Prozess-Speicher — nach jedem Neustart leer; kein revisionssicherer Löschnachweis.
- `ADMIN_API_KEY` wird als **Query-Parameter** übergeben → landet in Access-Logs. Auf Header
  umstellen.
