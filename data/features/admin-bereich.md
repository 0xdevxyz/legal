# Admin-Bereich (intern)

**Stand:** 2026-07-29 · **Status:** 🟡 nur Backend-API + Fix-Review-Seite im Dashboard.
Das statische Admin-Panel (`simple-admin/`) ist am 29.07.2026 ersatzlos entfernt worden.

## Ziel
Interner Adminbereich für Lead-Verwaltung, Analytics-Trends, System-Health und eine
Fix-Review-Queue zur menschlichen Freigabe von KI-Fixes ([[ai-fix-engine]]).
Ist-Zustand: der Bereich ist verdrahtet, aber in Produktion nicht konfiguriert und in
weiten Teilen Stub.

## Architektur (end-to-end)
- **Routes:** `backend/admin_routes.py`, Prefix `/api/admin` (`:15`), registriert
  `backend/main_production.py:66` (Import) / `:602` (`include_router`). 11 Routen:
  - `GET /dashboard/overview` (`:27`), `GET /leads` (`:67`), `GET /leads/{lead_id}` (`:119`),
    `POST /leads/{lead_id}/resend-verification` (`:161`), `DELETE /leads/{lead_id}` (`:208`),
    `GET /analytics/trends` (`:238`), `GET /system/health` (`:264`).
  - Fix-Review: `GET /fix-review-queue` (`:312`), `GET /fix-review-queue/{fix_id}` (`:362`),
    `POST /fix-review-queue/{fix_id}/approve` (`:397`), `.../reject` (`:437`).
- **Auth:** `verify_admin_access` (`admin_routes.py:17-25`) — `ADMIN_API_KEY` als
  **Query-Parameter** (`api_key: str = Query(..., alias="api_key")`). Auf allen 11 Routen
  angewendet, keine ungeschützte Route. Kein Default-Key; fehlt die Env → 503 (fail-closed).
- **Zweites, konkurrierendes Modell:** `require_admin` (`backend/dependencies.py:292-311`),
  rollenbasiert über `users.role != "admin"` → 403, JWT-/Session-basiert. Genutzt in
  `cookie_compliance_routes.py:1717`, `legal_change_routes.py:358,652,674,694,724`,
  `ai_legal_routes.py:754,794`. **`admin_routes.py` nutzt es nicht.**
- **Fix-Review-Queue (Backend):** Query `admin_routes.py:323-345` —
  `SELECT ... FROM fix_application_audit faa LEFT JOIN tracked_websites tw ... LEFT JOIN users u
  WHERE faa.quality_gate_status = 'pending_review' ORDER BY faa.applied_at DESC LIMIT $1 OFFSET $2`.
  Approve/Reject setzen `quality_gate_status` per UPDATE (`:411`, `:455`).
- **UI:** `dashboard-react/src/app/admin/fix-review/page.tsx` — einzige Datei unter
  `app/admin/` (kein Layout, keine Middleware, kein Route-Guard). Key aus
  `process.env.NEXT_PUBLIC_ADMIN_API_KEY ?? ""` (`:34`), als Query-Param an
  `/api/admin/fix-review-queue` (`:48`) und `.../{id}/{approve|reject}` (`:73`).
  `GET /fix-review-queue/{fix_id}` wird **nie** aufgerufen — das Detail-Panel rendert aus dem
  Listen-Objekt (`:198-242`); der im Docstring versprochene HTML-Diff (`admin_routes.py:369`)
  existiert weder in Query noch UI.
- **Abgrenzung:** `backend/ai_review_engine.py` gehört **nicht** zum Adminbereich — es ist die
  scan-seitige Issue-/Lösungs-Veredelung (`public_routes.py:20`, `compliance_engine/scanner.py:865`,
  Modell `anthropic/claude-haiku-4.5`). Siehe [[ai-fix-engine]].
- **Funktionierender HITL-Pfad:** `backend/accessibility_fix_saver.py` (Default-Status
  `'pending'`, `:28`; eigene `get_review_queue()`, `:222`) auf den intakten
  `accessibility_*_fixes`-Tabellen — genutzt von `accessibility_post_scan_processor.py:12,26`,
  `widget_routes.py:20,518,601`, `alt_text_routes.py:21`. Details: [[accessibility-remediation]].

## DB
Gegen die Baseline (`backend/alembic/baseline_schema.sql`, 57 Tabellen) verifiziert:
- Vorhanden: `users`, `tracked_websites`, `fix_jobs`, `waitlist_leads`,
  `accessibility_alt_text_fixes` / `_document_fixes` / `_link_fixes`.
- **[BEHOBEN 2026-07-17]** `fix_application_audit`, `fix_backups` und `leads` fehlten in der
  Baseline — via Alembic-Revision `0003_missing_lead_and_audit_tables` nachgezogen (gegen die
  Live-DB angewendet). Weiterhin nicht angelegt: `staging_deployments` (Produktentscheidung offen).
- Der Lead-Bereich adressiert eine `leads`-Tabelle; diese existiert seit Alembic 0003 wieder
  (neben `waitlist_leads`), s. [[lead-free-scan-funnel]].
- Keine asyncpg-JSONB-Verstöße: `admin_routes.py` baut JSONB serverseitig über
  `jsonb_build_array`/`jsonb_build_object` (`:459-466`), `$3` ist reiner Text (`:473`).
  `ai_review_engine.py` greift gar nicht auf die DB zu.

## Bekannte Lücken / Offen
- **Der gesamte Adminbereich ist in Produktion tot.** `ADMIN_API_KEY` ist weder in
  `docker-compose.yml` noch in `.env` gesetzt → `_ADMIN_API_KEY is None` → alle 11 Routen
  antworten 503. Live verifiziert: `GET /api/admin/system/health?api_key=x` → 503
  `{"detail":"Admin access not configured"}`, während `/health` 200 liefert.
- **Fix-Review-Queue ist eine Fassade — es gibt de facto keine menschliche Freigabe.** Von den
  vier unabhängigen Bruchstellen ist eine behoben, drei bleiben (jede allein ausreichend):
  1. **[BEHOBEN 2026-07-17]** `fix_application_audit` fehlte in der Baseline (→
     `UndefinedTableError`/500) — jetzt via Alembic 0003 angelegt. Die Queue bleibt aber
     **praktisch leer**, solange kein Writer `quality_gate_status='pending_review'` setzt (Punkt 2).
  2. `audit_service.log_fix_application()` (`audit_service.py:186-203`) listet 18 Spalten
     explizit auf — `quality_gate_status`/`quality_gate_log` sind **nicht** darunter. Kein Code
     im Repo schreibt den Status je in die Tabelle; die einzigen Writes sind die Admin-UPDATEs,
     die `pending_review` bereits voraussetzen (zirkulär).
  3. Der Wert landet stattdessen in `fix_jobs.result` (`unified_fix_engine.py:404-405` →
     `background_worker.py:105`), in der Baseline als **`text`** deklariert, nicht `jsonb`.
  4. Typkonflikt: `fix_application_audit.id` ist UUID (Archiv-DDL), Route (`:364 fix_id: int`)
     und UI (`page.tsx:15 id: number`) erwarten `int` → 422 auf jede Detail-/Approve-URL.
  → Fixes mit `pending_review` gehen unbemerkt durch. Bei einem Compliance-Produkt mit
  Haftungsanspruch der gewichtigste Befund. Bestätigt die Annahme aus [[ai-fix-engine]].
- **API-Key als Query-Parameter** (`admin_routes.py:17-23`): landet in Nginx-Access-Logs,
  Browser-History und Referer-Headern. Sollte ein Header (oder `require_admin`) sein.
  Zusätzlich: `!=` statt `secrets.compare_digest` (Timing-Seitenkanal, kaum ausnutzbar); Key
  wird bei Import gelesen → Rotation erfordert Neustart; der **Key selbst wird als
  `reviewed_by` in die DB geschrieben** (`:407`, `:451`) — ein Secret als Audit-Identität,
  ohne echte Reviewer-Zuordnung.
- **Zwei konkurrierende Admin-Modelle** (`verify_admin_access` vs. `require_admin`) im selben
  Backend. Auf eines konsolidieren — `require_admin` ist das tragfähigere.
- **Latentes Leck:** `NEXT_PUBLIC_ADMIN_API_KEY` würde von Next.js zur Buildzeit ins
  Client-Bundle inlined → der Admin-Key wäre für jeden Dashboard-Besucher lesbar (Vollzugriff
  inkl. `DELETE /leads/{id}`). Aktuell **nicht** ausnutzbar, weil die Variable nirgends gesetzt
  ist (`grep` = nur die Lesestelle). Wird sie gesetzt, ist das Leck sofort real — die Seite darf
  so nicht scharf geschaltet werden.
- **Stubs statt Implementierung:** `/leads` gibt hart `leads = []`/`total_count = 0` zurück
  (`:80-81`), `/analytics/trends` liefert `trends = []` (`:248`), `/system/health` hartcodierte
  Strings ohne echte Checks (`:270-297`, z. B. `"uptime": "99.9%"`). Der fehlende
  `leads`-Tabellenzugriff fällt dadurch nicht auf — der Fehler ist wegcodiert, nicht behoben.
- **`simple-admin/` ist am 29.07.2026 entfernt** (erledigt). Das Verzeichnis war leer —
  die einzige Datei `simple-admin/index.html` wurde am 2025-11-10 gelöscht (Commit `a3cd3a1`).
  Der Compose-Dienst `admin` (`nginx:alpine`, `127.0.0.1:3004:80`) lieferte seither HTTP 403
  auf ein leeres Verzeichnis, ohne dass ein Reverse-Proxy-Eintrag darauf zeigte.
  Ältere Statusberichte führten ihn als „laufendes Admin-Panel" — sie haben Container-Liveness
  mit Funktion verwechselt. Dienst, Container und Verzeichnis sind jetzt weg;
  `backend/admin_routes.py` und `dashboard-react/src/app/admin/fix-review/` bleiben unberührt.
