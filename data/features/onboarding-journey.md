# Onboarding & Journey

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit — zwei entkoppelte Systeme

## Ziel
Geführte Journey vom ersten Login bis zur verifizierten Compliance: Stages, Schritt-Tracking,
Fortschritt und Anpassung an das Skill-Level des Nutzers. Ist-Zustand: die Workflow-Engine
existiert vollständig, wird aber vom tatsächlichen Onboarding nie aufgerufen.

## Architektur (end-to-end)
- **Engine:** `backend/compliance_engine/workflow_engine.py` (597 Zeilen), Modul-Singleton
  `workflow_engine` (`:597`).
  - Enums: `WorkflowStage` (`:14-19`: `onboarding`, `website_analysis`, `guided_optimization`,
    `compliance_verification`, `maintenance`), `UserSkillLevel` (`:21-25`).
  - Dataclasses: `WorkflowStep` (`:27-41`), `UserJourney` (`:43-57`).
  - **13 Schritte**, hartcodiert in `_initialize_workflow_templates()` (`:71-323`), von
    `welcome_tour` / `skill_assessment` / `website_connection` über `ai_website_scan` bis
    `certificate_generation`, `monitoring_setup`. `_get_total_steps_count()` (`:562`) zählt dynamisch.
  - **State ist persistent**, kein In-Memory-Dict: jeder Zugriff geht über
    `workflow_integration.load_user_journey(user_id)` (`:358-359`, `:378-379`, `:523-524`).
    Nur `self.workflow_templates` (`:69`) ist In-Memory → **Container-Restart unkritisch.**
- **Persistenz:** `backend/compliance_engine/workflow_integration.py` — enthält **keine Routes**,
  nur die Klasse `WorkflowIntegration` (`:17`), das Singleton (`:160`) und
  `init_workflow_integration(db_pool)` (`:163-166`, verdrahtet `main_production.py:452-454`).
  `save_user_journey` (`:26`) serialisiert die Journey und schreibt sie per
  `INSERT ... ON CONFLICT (user_id) DO UPDATE` (`:48-57`); `load_user_journey` (`:66`) liest zurück.
- **Routes:** direkt am `app` in `backend/main_production.py:1352-1396`, alle mit
  `Depends(get_current_user)` (`:1353`, `:1368`, `:1377`, `:1390`):
  `POST /api/v2/workflow/start-journey`, `POST /complete-step`, `GET /current-step`, `GET /progress`.
  - **Ownership sicher:** die `user_id` ist nirgends aus dem Request übernehmbar, sondern immer
    `str(current_user["id"])` aus dem Token (`:1358`). `StartJourneyRequest` (`:167-169`) kennt
    nur `website_url`/`skill_level`, `CompleteStepRequest` (`:171-173`) nur `step_id`/
    `validation_data` — keine `user_id` im Schema. Da `user_journeys.user_id` PK ist, ist jede
    Journey strikt auf den Token-User gescoped. Kein IDOR.
- **Skill-Level:** `UserSkillLevel` (`workflow_engine.py:21-25`) —
  `absolute_beginner` | `beginner` | `intermediate` | `advanced`. Gesetzt aus dem
  Client-Request (`main_production.py:1355`, Default `"beginner"`).
  **Wirkung nur zweifach:** `estimated_completion` (14 / 7 / 3 Tage,
  `workflow_engine.py:344-348`) und `_personalize_step` (`:450-487`) — dort **rein kosmetisch**:
  Emoji-Präfix je Instruction (`:473`, `:482`), Zeit × 1.5 bzw. × 0.7, Visual-Aid-Strings.
  `beginner`/`intermediate` bekommen gar keine Behandlung; die Schrittmenge ist für alle
  Levels identisch.
- **Wizards — 5 aktive, 1 toter, plus die Journey-Seite:**
  - `components/onboarding/OnboardingWizard.tsx` (795 Z.) — `app/page.tsx:11`, gerendert `:54` → **aktiver Einstieg**
  - `components/dashboard/ComplianceWizard.tsx` (380 Z.) — `components/dashboard/WebsiteAnalysis.tsx:25`, gerendert `:860`
  - `components/cookie-compliance/CookieSetupWizard.tsx` — `app/cookie-compliance/page.tsx:24`, gerendert `:330`
  - `components/dashboard/LegalTextWizard.tsx` — `components/dashboard/FixResultModal.tsx:7`, gerendert `:113`
  - `components/accessibility/FixWizard.tsx` (765 Z.) — **toter Code**: nur re-exportiert in
    `components/accessibility/index.ts:5,15`; der einzige Consumer des Barrels
    (`WebsiteAnalysis.tsx:20`) importiert ausschließlich `WidgetIntegrationCard`.
  - `app/journey/page.tsx` (522 Z.) — eigenständiger Flow, react-query, spiegelt `STAGES`
    (`:61-67`) und `SKILL_LEVELS` (`:69-74`) zum Backend-Enum; ruft alle vier
    `/api/v2/workflow/*`-Endpunkte (`:77-95`). Erreichbar **nur** über den Sidebar-Link
    (`components/dashboard/Sidebar.tsx:47`).
- **Einstieg:** Client-Side-Gate in `dashboard-react/src/app/page.tsx:33-55` — kein Redirect
  nach Registrierung, sondern konditionales Rendern: `user?.onboarding_completed` → aus, sonst
  `localStorage['complyo_onboarding_completed']`. Persistiert via
  `POST /api/auth/complete-onboarding` (`OnboardingWizard.tsx:219` → `backend/auth_routes.py:477`).

## DB
Gegen die Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py`, Dump
`backend/alembic/baseline_schema.sql`) verifiziert — genau **eine** Tabelle:
- `user_journeys` (`baseline_schema.sql:2984-2989`): `user_id text NOT NULL`,
  `journey_data text NOT NULL`, `created_at`, `updated_at`. PK auf `user_id` (`:4150-4154`,
  Voraussetzung für das `ON CONFLICT`), Index `idx_user_journeys_updated` (`:5061`).
  Tabellen-/Spalten-Kommentare dokumentieren die Serialisierung (`:2996`, `:3003`).
- `users.onboarding_completed boolean DEFAULT false` (`:1113`).
- **Keine asyncpg-JSONB-Verstöße:** `journey_data` ist `text` (nicht JSONB) und wird korrekt
  mit `json.dumps()` geschrieben (`workflow_integration.py:56`) bzw. `json.loads()` gelesen (`:80`).

## Bekannte Lücken / Offen
- **Onboarding und Journey sind vollständig entkoppelt.** Der `OnboardingWizard` — der reale
  Einstieg — spricht die Workflow-Engine **nie** an; er nutzt `analyzeWebsite`,
  `saveTrackedWebsite` und `/api/auth/complete-onboarding` (`:5`, `:219`). Die einzige Stelle im
  gesamten Frontend, die `/api/v2/workflow/*` aufruft, ist `app/journey/page.tsx`. Damit hängt
  die komplette Engine (13 Schritte, Stages, Skill-Level, Zertifikat) an einer Seite, auf der
  kein neuer Nutzer je landet. `welcome_tour`/`skill_assessment` werden nie ausgelöst.
- **Skill-Assessment ohne Wirkung:** `_determine_skill_level()` (`workflow_integration.py:143-156`)
  berechnet einen Score aus dem Fragebogen, **speichert ihn aber nie** — Zeile `:125` ist
  auskommentiert (`# await self.save_user_assessment(...)`), das Ergebnis geht nur in einen
  Anzeige-String (`:126`). `save_user_assessment` existiert nicht, ebenso wenig eine
  `user_assessments`-Tabelle. Das Level kommt ausschließlich aus dem Client-Request.
- **Skill-Level ist Kosmetik:** außer Emoji-Präfix, Zeitfaktor und `estimated_completion` keine
  Wirkung. Kein Level ändert die Schrittmenge — der Anspruch „Anpassung an das Skill-Level"
  ist derzeit nicht eingelöst.
- **Onboarding-Gate ist per localStorage umgehbar** und fehlerhaft priorisiert: `page.tsx:43-48`
  prüft localStorage, **bevor** Server-State greift → ein User mit `onboarding_completed=false`
  im Backend, aber gesetztem Key sieht das Onboarding nie wieder.
- Kleinere Defekte: `UserSkillLevel(request.skill_level)` (`main_production.py:1355`) wirft bei
  ungültigem String einen `ValueError` → `except Exception` (`:1363`) macht **500** statt 422 ·
  Typ-Mismatches Frontend↔Backend (`estimated_time_remaining?: number`, `journey/page.tsx:57`,
  vs. deutscher String aus `_calculate_remaining_time`, `workflow_engine.py:579-594`;
  `success_criteria?: string[]` `:39` vs. `Dict[str, Any]`) · **`FixWizard.tsx` (765 Z.) toter
  Code** → Löschkandidat · `user_journeys.user_id text` ohne FK auf `users(id)` → verwaiste
  Journeys bei User-Löschung (DSGVO-relevant, `journey_data` enthält die `website_url`).
- **Zu klären:** Soll die Workflow-Engine der Einstieg werden (dann `OnboardingWizard` daran
  anbinden) oder ist sie aufzugeben? Vier aktive Wizards nebeneinander sind ohne diese
  Entscheidung nicht konsolidierbar.
