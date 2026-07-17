# KI-Fix-Engine

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Zu jedem im Scan ([[scan-analyze-kern]]) gefundenen Problem eine individuelle Lösung per KI
erzeugen (Code-Snippet, Rechtstext, Widget-Config, Anleitung), automatisch auf Syntax/Wirkung/
Regression prüfen und im Dashboard ausliefern. Auslieferung = **Nutzer baut selbst ein**
(Anzeige/Copy-Paste/Export). Auto-Deployment existiert im Code, ist aber nicht angebunden.

## Architektur (end-to-end)
- **UI-Einstieg:** `dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx`
  (Button `.../UnifiedFixButton.tsx` = reine Präsentation; Anzeige `components/ai/AIFixDisplay.tsx`,
  `AIFixPreview.tsx`, `dashboard/FixModal.tsx`) → `dashboard-react/src/hooks/useCompliance.ts`.
- **Queue:** `POST /api/fix-jobs` (`backend/main_production.py:1523`) legt Zeile in `fix_jobs`
  (`status='pending'`) an; Polling `GET /api/fix-jobs/{job_id}/status` (`:1599`) + `/active` (`:1647`).
  Job überlebt Page-Refresh.
- **Worker:** `backend/background_worker.py` — asyncio-Polling-Loop (5 s, `LIMIT 5`), gestartet
  in `main_production.py:484`. **In-Process im API-Container, kein Redis/Celery.** Schreibt
  Progress (10/30/55/85/100 %) + `result` (JSONB) nach `fix_jobs`; Kontext aus `scan_history`.
- **Engine:** `backend/ai_fix_engine/unified_fix_engine.py::UnifiedFixEngine.generate_fix()`
  - Typ-Routing `_determine_fix_type()` → `code|text|widget|guide` (`FixType`, `prompts_v2.py:15`).
  - Prompt via `PromptBuilder`/`ContextBuilder` (`prompts_v2.py`) + JSON-Schema-Vorgabe
    (`CODE_/TEXT_/WIDGET_/GUIDE_FIX_SCHEMA`); Parsing `ResponseParser.extract_json()`.
  - **Provider OpenRouter** (`unified_fix_engine.py:72-73`, `OPENROUTER_API_KEY`), `temperature=0.3`,
    `max_tokens=2000`, 3 Retries. **Modell `moonshotai/kimi-k2.5`** (`prompts_v2.py:25-27`;
    auch `intelligent_analyzer.py:20`). Totalausfall → `_generate_template_based_fix()`.
  - Validierung `ai_fix_engine/validators.py::FixValidator.validate_and_sanitize()`: Schema +
    `HTMLValidator`/`CSSValidator`/`JavaScriptValidator` + `LegalTextValidator` (Pflichtangaben
    Impressum/Datenschutz). Invalid → `status='partial'`, wird trotzdem geliefert.
- **Quality-Gate:** `ai_fix_engine/fix_quality_gate.py` (Aufruf `unified_fix_engine.py:403`)
  - Stufe 1 Syntax (<200 ms): gefährliche Konstrukte (`<script>`, `on*=`, `javascript:`,
    `<iframe|object|embed>`, `eval(`, `innerHTML=`, `document.write`), ARIA-Rollen-Whitelist.
  - Stufe 2 Re-Scan (<5 s): Score vorher/nachher, Issue behoben? · Stufe 3 Regression (<10 s).
  - → `fix.data["quality_gate_status"]` = `validated` | `pending_review` + `quality_gate_log`.
- **Weitere Endpunkte:** `POST /api/v2/ai-fix` (`main_production.py:1281`, Batch über alle
  Issues eines Scans, synchron, ohne Persistenz) · `POST /api/v2/fixes/generate`
  (`backend/fix_routes.py:51`, Limit-/Paywall-Logik, 10/h) · `/fixes/execute` (`:931`, 10/min →
  `smart_fix_generator.py`, template-basiert, **kein** AI-Call) · `/fixes/validate` (`:959`,
  20/min, grober Re-Scan) · `/fixes/export|history|limits|{id}/download|health|{id}/outcome`.
- **Validatoren (Abgrenzung):** `compliance_engine/live_validator.py` 🟢 genutzt, aber **nur von
  [[accessibility-remediation]]** (`alt_text_routes.py`, Playwright/axe, WCAG-kriteriengenau) ·
  `hybrid_validator.py` (Pattern→KI) genutzt, aber im **Scan** (`checks/impressum_check.py`,
  `datenschutz_check.py`) · `fix_validator.py` (Multi-Stage, Anthropic-SDK) **nirgends importiert**.
- **Deployment/Rollback:** `backend/fix_apply_routes.py` (`/api/v2/fixes/apply`, `/rollback`,
  `/apply/preview`, `/apply/status/{id}`) → `compliance_engine/deployment_engine.py`
  (FTP/SFTP/WordPress-REST/Netlify/Vercel; Backup vor Deploy → `fix_backups`; `rollback()`).
  **Kein UI-Aufruf** (`grep "fixes/apply"` im Dashboard = 0); `preview_engine.py` unimportiert.
  Der real ausgelieferte Fix-Pfad läuft über Fix-Manifest + Channels ([[wordpress-plugin]]).
- **Admin-Review:** `dashboard-react/src/app/admin/fix-review/page.tsx` →
  `/api/admin/fix-review-queue[/{fix_id}/(approve|reject)]` (`backend/admin_routes.py:312+`) auf
  `fix_application_audit.quality_gate_status`. **`backend/ai_review_engine.py` gehört NICHT dazu**
  — das ist die Scan-seitige Issue-/Lösungs-Veredelung (`public_routes.py:20`, Modell
  `anthropic/claude-haiku-4.5`).
- **White-Label:** `ai_fix_engine/white_label.py::WhiteLabelProcessor` entfernt Fremd-Branding
  (eRecht24) aus importierten Rechtstexten. **Nirgends importiert.** Nicht = Agentur-Branding
  ([[billing-plans-addons]]).
- **Plan-Gating:** `fix_routes.py:151` — jeder bezahlte Plan (`plan_type` ≠ leer/`free`) hat
  unbegrenzte KI-Fixes; `free` = 1 Fix, danach HTTP 402. SFTP/SSH nur `managed`/`premium`
  (`fix_apply_routes.py:135,320`).

## Abgrenzung zu [[accessibility-remediation]]
Zwei getrennte Systeme: fachlich überlappend („Fix"), aber **kein gemeinsamer Code-Pfad, kein
gemeinsames Modell, kein gemeinsamer Fix-Speicher**.

| | KI-Fix-Engine | [[accessibility-remediation]] |
|---|---|---|
| Auslöser | Nutzer klickt „Problem beheben" je Issue | Post-Scan-Processor automatisch |
| Generator | `unified_fix_engine.py` (OpenRouter/kimi-k2.5) | `accessibility_post_scan_processor.py` (heuristisch) |
| Speicher | `fix_jobs.result` (JSONB), `generated_fixes` | `accessibility_*_fixes` (stabile `site_id`) |
| Freigabe | Quality-Gate automatisch | HITL-Worklist (`pending`→`approved`) |
| Auslieferung | Anzeige/Copy-Paste/Export im Dashboard | `GET /api/accessibility/fix-manifest/{site_id}` → 3 Channels |
| Scope | alle Kategorien (DSGVO, Impressum, Cookies, A11y) | nur WCAG/BFSG |

Konkret: Die KI-Fix-Engine schreibt **nicht** ins Fix-Manifest — ein von ihr erzeugter
A11y-Fix landet nie auf der Kundenseite. `ai_fix_engine/handlers/accessibility_handler.py`
suggeriert Überlappung, ist aber ungenutzt (s. u.).

## DB
- `fix_jobs` — Queue + Ergebnis (`issue_data`, `status`, `progress_percent`, `current_step`,
  `result` JSONB). DDL: `backend/migration_fix_jobs.sql`, `backend/database_setup.sql:148`.
  **Nicht** in `ensure_migrations` (`main_production.py:396`).
- `user_limits` — `fixes_used`/`fixes_limit`/`fix_started`/`money_back_eligible` (Freemium).
- `generated_fixes` — Tracking je Fix (`migrations/complete_migration.sql:179`).
- `fix_application_audit` — Audit (`backend/audit_service.py`); Spalte `quality_gate_status` per
  `migrations/add_rule_versioning.sql:43`; Basis der Admin-Review-Queue.
- `fix_backups`, `staging_deployments` (`migrations/create_fix_audit_trail.sql`) — mangels UI ungenutzt.
- Metrik-Tabellen: `fix_outcomes`, `fix_acceptance_metrics`, `fix_generation_stats`,
  `fix_user_feedback`, `ai_fix_monitoring`.

## Bekannte Lücken / Offen
- **Rate-Limiting fehlt am teuersten Pfad** (vgl. `planning/STRUKTUR_FIXES_LAUNCH_PLAN.md`):
  `POST /api/v2/ai-fix` (Batch über *alle* Issues) und `POST /api/fix-jobs` haben **kein**
  `@limiter.limit`. Gedrosselt nur `/fixes/generate` (10/h), `/execute` (10/min), `/validate`
  (20/min). Soll: 5/min auf KI-Generierung.
- **Admin-Review hängt in der Luft:** `audit_service.log_fix_application()` schreibt
  `quality_gate_status` **nie** in `fix_application_audit`; die Engine legt ihn nur in
  `fix_jobs.result` ab → Review-Queue dürfte dauerhaft leer sein, **de facto keine menschliche
  Freigabe für KI-Fixes**. Gegen Live-DB zu verifizieren.
- **Fallback-Kette wirkungslos:** `AIModel.CLAUDE_SONNET/GPT4/GPT4_TURBO` sind alle auf
  `moonshotai/kimi-k2.5` gesetzt → `fallback_chain` ruft zweimal dasselbe Modell; bei
  OpenRouter-Ausfall greift direkt der Template-Fallback.
- **`ai_fix_engine/handlers/` ist toter Code:** `LegalTextHandler`, `CookieBannerHandler`,
  `AccessibilityHandler`, `CodeFixHandler`, `GuideHandler` nur in `handlers/__init__.py`
  exportiert, von keinem Modul importiert — die Engine routet über `prompts_v2.PromptBuilder`.
  Die realen Fix-Typen sind `FixType` (code/text/widget/guide).
- **Verdacht toter Code (GitHub-PR-Deployment):** `backend/git_routes.py` ist zwar registriert
  (`main_production.py:135,557`), aber `grep "v2/git"` im Dashboard = 0 Treffer;
  `compliance_engine/github_integration.py` von keinem Modul importiert; `POST
  /api/v2/fixes/propose-pr` (`fix_routes.py:542`) ohne UI-Einstieg. → Kein produktives Feature;
  Entscheidung nötig (entfernen oder anbinden).
- **Plan-Gate-Bug (zu prüfen):** `fix_apply_routes.py:135,320` liest `current_user.get('plan')`,
  der Auth-Layer liefert aber `plan_type` (derselbe Bug war in `fix_routes.py` behoben) →
  Default `'ai'` → SFTP-Gate greift vermutlich nie.
- Weiterer unbenutzter Code: `compliance_engine/fix_validator.py`, `preview_engine.py`,
  `ai_fix_engine/white_label.py`, `ai_fix_engine/monitoring.py`.
- `fix_jobs` fehlt im self-healing Migrations-Runner → auf frischer DB nur via
  `database_setup.sql`/`init_all_tables.sh`.
