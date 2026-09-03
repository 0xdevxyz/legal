# PDF-Report & Export

**Stand:** 2026-07-17 · **Status:** 🟢 live (PDF-Download live, Audit-Log/-Export seit
2026-07-17 funktionsfähig)

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
- **[BEHOBEN 2026-07-17] Fehlten in der Baseline:** `fix_application_audit`, `fix_backups` —
  jetzt via Alembic-Revision `0003_missing_lead_and_audit_tables` (additiv, gegen die Live-DB
  angewendet) nachgezogen. Die Archiv-Skripte bleiben tabu.
- **[BEHOBEN 2026-07-17] `fix_audit_trail` war nirgends definiert** — eine Geistertabelle, aus
  der aber beide Audit-Endpunkte lasen. Fix: beide Reader lesen jetzt `fix_application_audit`
  (die Writer-Tabelle, `main_production.py:1820/1854`).
- asyncpg-JSONB-Regel in `audit_service.py` **eingehalten**: jede JSONB-Bindung ist
  `json.dumps()`-gewrappt (`:87,133,200,202,258,312,314,499`).

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] Audit-Log und Audit-Export waren tot** (lasen `fix_audit_trail` →
  `UndefinedTableError`/500) und **Write/Read nutzten verschiedene Tabellen** (`audit_service`
  schrieb `fix_application_audit`, die Endpunkte lasen `fix_audit_trail`). Fix: Reader auf
  `fix_application_audit` umgestellt + Tabelle via Alembic 0003 angelegt → Audit-Log/-Export
  funktionsfähig. (Die Routen selektieren weiterhin `backup_id`/`rollback_available` — ob jeder
  Writer diese füllt, bleibt zu prüfen.)
- **[BEHOBEN 2026-07-17] Kein Rate-Limit auf PDF-Export** (Plan 1.4). Fix:
  `/api/v2/reports/{scan_id}/download` hat jetzt `Depends(rate_limit("report_download", 10, 60))`
  (`main_production.py:1770`). (`/audit/export` und die Agentur-Route noch prüfen.)
- `limit`/`offset` in `/api/v2/audit/log` sind **ungebounded** (`limit: int = 50` ohne `le=`)
  → `?limit=10000000` möglich.
- **[BEHOBEN 2026-07-17] `detail=str(e)`-Leaks in den Audit-Handlern:** beide gaben DB-Fehlertexte
  an den Client. Fix: beide liefern jetzt generisch `detail="Interner Fehler"`
  (`main_production.py:1842/1883`).
- Zwei `ComplianceReportGenerator`-Forks mit divergierenden Signaturen (s. o.) — zusammenführen.
