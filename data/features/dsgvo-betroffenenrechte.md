# DSGVO-Betroffenenrechte & Retention

**Stand:** 2026-07-17 · **Status:** 🟡 teilbehoben (Retention-Cleanup löscht jetzt,
Betroffenen-Endpunkte token-gebunden; Datenmodell-Klärung offen)

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
- **Vorhanden** in der Live-DB: `users`, `user_sessions`, `cookie_consent_logs`; seit
  Alembic 0003 (2026-07-17) auch `leads`, `email_verifications`, `communication_log`,
  `lead_consents` ([[lead-free-scan-funnel]]).
- **Nicht vorhanden** (verifiziert): `ai_call_logs` — der Cleanup überspringt die Tabelle jetzt
  aber sauber, statt zu scheitern.

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] `_daily_gdpr_cleanup()` lief, löschte aber nichts.** Alle fünf
  Statements nutzten `DELETE ... RETURNING COUNT(*)` — in PostgreSQL unzulässig; die erste
  Anweisung warf `aggregate functions are not allowed in RETURNING`, der `except` fing,
  schlief 24 h, scheiterte erneut. Fix: `RETURNING COUNT(*)` entfernt, Trefferzahl aus dem
  asyncpg-Command-Tag (`"DELETE 42" → 42`); fehlende Tabellen kippen den Lauf nicht mehr,
  sondern werden übersprungen. Beleg: 123 abgelaufene Sessions lagen zuvor unlöschbar in der DB
  und werden nun gelöscht. (Der identische Defekt in `backend/backup_retention.py` bleibt —
  toter Code.) `email_verifications` existiert seit Alembic 0003; `ai_call_logs` fehlt weiter,
  wird aber jetzt sauber übersprungen.
- **[BEHOBEN 2026-07-17] Keine Auth/Ownership auf den Betroffenen-Endpunkten.**
  `POST /request-deletion` und `POST /export-data` identifizierten den Betroffenen allein über
  eine E-Mail im Body — kein Token. Fix: neue Dependency `get_verified_email` zieht die E-Mail
  aus dem JWT (`gdpr_api.py:29`), das `email`-Body-Feld entfällt → Betroffener = Token-Inhaber
  (IDOR geschlossen). Abgesichert durch `tests/test_gdpr_knowledge_auth.py`.
  (`GET /retention-info?email=` als reiner Lese-Endpunkt zu prüfen.)
- Der `gdpr_retention_service` adressiert das `leads`-Datenmodell; `leads` existiert seit
  Alembic 0003 wieder (2026-07-17), damit greifen `get_lead_by_email` / `/request-deletion` /
  `/export-data` jetzt gegen echte Daten. **Weiter zu klären**, ob das Modul auf
  `users`/[[lead-free-scan-funnel]] konsolidiert wird — die Betroffenen-Endpunkte sind nun aber
  token-gebunden statt E-Mail-adressierbar.
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
