# PDF-Report & Export

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit (PDF-Download live, Audit-Export tot)

## Ziel
Scan-Ergebnisse als PDF-Compliance-Report zum Download, KI-Fixes als HTML/PDF-Export und
ein Audit-Log über angewandte Fixes (Anzeige + CSV-Export). Agentur-Kundenreports mit
Agentur-Logo laufen separat → [[agentur-white-label]].

## Architektur (end-to-end)
- **PDF-Bibliothek:** durchgehend **reportlab** (platypus). Kein weasyprint/fpdf.
- **Zwei Generatoren — beide aktiv, keiner tot.** Beide definieren dieselbe Klasse
  `ComplianceReportGenerator` und dasselbe Modul-Singleton `pdf_generator`, haben aber
  **verschiedene Consumer und divergierende Signaturen**:
  - `backend/pdf_report_generator.py:531` → importiert von `backend/email_service.py:17`,
    Aufruf `:87` mit **zwei** Argumenten `generate_compliance_report(analysis_data, lead_data)`
    (Lead-/Mail-Pfad, [[lead-free-scan-funnel]]).
  - `backend/compliance_engine/pdf_generator.py:526` → importiert von
    `backend/main_production.py:52`, Aufruf `:1725` mit **einem** Argument
    `generate_compliance_report(report_data)` (Dashboard-Download).
  - Geforkte Kopien, kein Dead Code — aber gleicher Klassen-/Symbolname bei
    unterschiedlichem Verhalten. Drift-/Konsolidierungskandidat.
- **Report-Download:** `GET /api/v2/reports/{scan_id}/download`
  (`backend/main_production.py:1700`, direkt via `@app.get`, kein Router).
  - Auth `Depends(get_current_user)`. **Ownership korrekt erzwungen** (`:1704-1710`):
    `SELECT * FROM scan_history WHERE scan_id = $1 AND user_id::text = $2` → fremde
    `scan_id` liefert 404 („Scan not found or access denied"), kein Existenz-Leak.
  - `scan_data` wird je nach Typ (`str`/`dict`) geparst, dann synchron gerendert und als
    `StreamingResponse` ausgeliefert. **Kein Caching.**
- **Fix-Export:** `backend/export_service.py` — exportiert **HTML und PDF**, *nicht* CSV/JSON.
  `ExportService.export_fix(fix_id, user_id, export_format='html')` (`:26`), `_export_as_html`
  (`:125`), `_export_as_pdf` (`:329`, eigene reportlab-Styles, kein Generator-Reuse).
  Verdrahtet `main_production.py:539,586` → `backend/fix_routes.py:30`, Aufruf `:308`.
  Ownership per JOIN-Filter `WHERE gf.id = $1 AND gf.user_id = $2` (`:54-55`).
- **Audit-Log:** `GET /api/v2/audit/log` (`main_production.py:1743`) und
  `GET /api/v2/audit/export` (`:1769`, CSV via `csv.DictWriter`). Auth
  `Depends(get_current_user)`, Ownership `WHERE user_id = $1`.
- **Audit-Schreiber:** `backend/audit_service.py` — `log_fix_application()` u. a., einziger
  Aufrufer `backend/fix_apply_routes.py:171`. Schreibt `fix_application_audit` + `fix_backups`.
- **Datei-Ablage:** `backend/file_storage_service.py` — Singleton `file_storage` (`:138`),
  `FILE_STORAGE_PATH` (Default `/app/uploads`, `:31-34`), Layout
  `<storage>/ai_documentation/<user_id>/`. Extension- + MIME-Whitelist, 50 MB Limit (`:16-26`),
  randomisierte/sanitisierte Dateinamen (`:47-52`) → kein Path-Traversal. Genutzt von
  `ai_compliance_routes.py:16` und dem Agentur-Logo ([[agentur-white-label]]).

## DB
Gegen die Alembic-Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py`,
Dump `backend/alembic/baseline_schema.sql`, 57 Tabellen) verifiziert:
- Vorhanden: `scan_history` (Report-Quelle), `generated_fixes` + `user_limits` + `export_history`
  (Fix-Export), `users.agency_logo_path`.
- **Fehlen in der Baseline:** `fix_application_audit`, `fix_backups` — nur noch in
  `backend/migrations/_archive_pre_baseline/` (`create_fix_audit_trail.sql`,
  `complete_migration.sql`, `add_rule_versioning.sql`), die nicht mehr angewendet werden dürfen.
- **`fix_audit_trail` ist nirgends definiert** — weder Baseline noch Archiv (`grep` über alle
  `*.sql` = 0 Treffer). Genau aus dieser Tabelle lesen aber beide Audit-Endpunkte.
- asyncpg-JSONB-Regel in `audit_service.py` **eingehalten**: jede JSONB-Bindung ist
  `json.dumps()`-gewrappt (`:87,133,200,202,258,312,314,499`).

## Bekannte Lücken / Offen
- **Audit-Log und Audit-Export sind tot.** Sie lesen `fix_audit_trail`, eine Tabelle, die im
  Repo nirgends existiert → jeder Aufruf endet in `UndefinedTableError` → HTTP 500. Verifiziert.
- **Write und Read nutzen verschiedene Tabellen:** `audit_service.py` schreibt
  `fix_application_audit`, die Endpunkte lesen `fix_audit_trail`. Selbst mit angelegter Tabelle
  läge dort nichts. Zusätzlich selektieren die Routen Spalten (`backup_id`,
  `rollback_available`), die kein Writer je füllt. Welche Tabelle die intendierte ist:
  **zu klären**.
- **`fix_application_audit`/`fix_backups` fehlen in der Baseline** → auf einer frisch aus der
  Baseline aufgebauten DB läuft auch `audit_service` in `UndefinedTableError`. Das Feature
  funktioniert allenfalls auf gewachsenen DBs mit Pre-Baseline-Migrationen. Nachzuziehen als
  Alembic-Revision.
- **Kein Rate-Limit auf PDF-Export** (Plan 1.4 fordert Drosselung). slowapi ist vorhanden
  (`main_production.py:9-11,209-211`), aber nur auf `/api/v2/analyze/complete` (30/min, `:867`),
  `/api/v2/fixes/execute` (10/min, `:932`), `/api/v2/fixes/validate` (20/min, `:960`).
  `/api/v2/reports/{scan_id}/download` rendert synchron und ohne Cache → unlimitierter
  CPU-Amplifier für jeden eingeloggten User. Auch `/audit/export` und die Agentur-Route sind offen.
- `limit`/`offset` in `/api/v2/audit/log` sind **ungebounded** (`limit: int = 50` ohne `le=`)
  → `?limit=10000000` möglich.
- Beide Audit-Handler geben `detail=str(e)` an den Client (`:1766`, `:1804`) → DB-Fehlertexte leaken.
- Zwei `ComplianceReportGenerator`-Forks mit divergierenden Signaturen (s. o.) — zusammenführen.
