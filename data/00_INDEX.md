# Complyo — Projekt-Master-Index

**Letzte Aktualisierung:** 2026-05-15  
**Plattform-Version:** 2.2.0  
**Produktionsstatus:** Live — `https://app.complyo.tech` / `https://api.complyo.tech`

---

## Schnellnavigation

| Ich suche... | Dokument |
|---|---|
| Was ist gerade offen / TODO? | [Offene Punkte](#offene-punkte) |
| Was wurde zuletzt geändert? | [Letzte Änderungen](#letzte-nderungen) |
| EFRE-Förderantrag | [efre/00_INDEX.md](efre/00_INDEX.md) |
| Fehler & Bugs | [Fehler & Audit-Dokumente](#fehler--audit) |
| Security-Status | [Security](#security) |
| Cookie-Banner-Status | [Cookie & Consent](#cookie--consent) |
| Deployment-Anleitung | [Deployment](#deployment) |
| Projektstruktur & Architektur | [Struktur & Architektur](#struktur--architektur) |

---

## Produktionsstatus (Stand 2026-05-15)

| Dienst | URL | Status |
|--------|-----|--------|
| Dashboard | `https://app.complyo.tech` | Live |
| Landing | `https://complyo.tech` | Live |
| API | `https://api.complyo.tech` | Live |
| API Health | `/api/v2/health` | `{"status":"healthy","database":"connected"}` |
| Backend | Python 3.11, Version 2.2.0 | Healthy |
| Postgres | Port 5432 | Connected |
| Redis | Port 6379 | Running |

---

## Offene Punkte

### Blocker

| # | Problem | Datei | Auswirkung |
|---|---------|-------|------------|
| B-01 | `cookie_compliance_stats` Schema-Mismatch: Live-DB hat `site_identifier` statt `site_id`, fehlende Spalten `accepted_analytics`, `accepted_marketing`, `accepted_functional` | `backend/cookie_compliance_routes.py` | `log_consent` wirft HTTP 500 mit echter DB — **blockiert Phase 6 Revocation Analytics** |

### Offen / Pending

| # | Bereich | Beschreibung | Priorität |
|---|---------|-------------|-----------|
| O-01 | Accessibility | Phase 4: Touch-Target-Checker (WCAG 2.5.5), WCAG-AAA-Checks, Table/SVG/Canvas-A11y | Mittel |
| O-02 | Accessibility | Phase 5–9 aus `PLAN_WEITERER_VERLAUF.md` noch nicht begonnen | Mittel |
| O-03 | TCF/IAB | Offizielle IAB-CMP-Registrierung unvollständig — kein CMP-ID, kein TC-String-Generator, kein GVL-UI | Niedrig (bedarfsgesteuert) |
| O-04 | Dashboard | Phase 1.3 KI-Integration (Button-Handler, API-Integration) — evtl. durch neuere Architektur überholt | Klären |
| O-05 | Error Audit | 163 identifizierte Fehler/Logging-Findings aus `01_ERROR_AUDIT_REPORT.md` — Umsetzungsstatus unklar | Mittel |
| O-06 | Null-Safety | `group.sub_issues.slice(...)` kann crashen wenn `sub_issues` null/undefined | Niedrig |
| O-07 | Code-Qualität | Black/flake8/pylint nicht einheitlich durchgesetzt; TypeScript Prettier fehlend | Niedrig |
| O-08 | Observability | APM-Integration fehlt; Uptime-Monitoring fehlt; Health-Checks nur basic | Niedrig |
| O-09 | Token-Migration | P1-Item aus `OPTIMIERUNGS_FORTSCHRITT.md` — größeres Refactoring noch offen | Mittel |
| O-10 | EFRE | Benchmark-Set: 20/100 Fälle annotiert — 80 weitere benötigen Anwalt-Review | Mittel |
| O-11 | EFRE AP4 | Multilinguale Wissensmodelle: Corpus-Aufbau angelegt, EUR-Lex-Crawler noch nicht produktiv gelaufen | Mittel |

---

## Letzte Änderungen

| Datum | Bereich | Was |
|-------|---------|-----|
| 2026-05-15 | EFRE | AP1–AP5 vollständig implementiert + dokumentiert in `data/efre/` |
| 2026-05-15 | Cookie | Cookie-Banner-Rollout Phase 1+2 abgeschlossen (`cookie-banner-rollout-progress.md`) |
| 2026-05-13 | UI | Light-Theme-Fix für Landing-App (`LIGHT_THEME_FIX.md`) |
| 2026-05-09 | Domain | Domain-Lock & Onboarding-Flow-Analyse (`DOMAIN_LOCK_ONBOARDING_ANALYSIS.md`) |
| 2026-05-05 | Security | Security Round 2: Logout-Cookie, CSRF, SSRF, Dependency-Audit (`SECURITY_ROUND2_LOG.md`) |
| 2026-05-05 | Audit | Codebase-Audit + Duplicate-File-Audit (`CODEBASE_AUDIT_SUMMARY.md`, `DUPLICATE_FILE_AUDIT.md`) |
| 2026-05-04 | Audit | Error-Audit-Report: 163 Findings im Dashboard (`01_ERROR_AUDIT_REPORT.md`) |
| 2026-05-02 | Dashboard | Phase 1.1+1.2: KI-Assistant entfernt, OptimizationProcessWidget eingebaut |
| 2026-04-27 | Deployment | Score-Calculator-Deployment erfolgreich (`DEPLOYMENT_SUCCESS.md`) |
| 2026-04-25 | Score | Rating-Volatility-Fix deployed — nicht-deterministisches Score-Problem behoben |
| 2026-04-21 | Auth/Backend | Auth-Debt Phase 1: echte `get_current_user`, DB-Integration, Expert-Service-Email |

---

## Verzeichnisstruktur

```
data/
├── 00_INDEX.md                  ← diese Datei (Projekt-Master)
├── architektur/                 ← Systemarchitektur & Diagramme
│   ├── SYSTEM_OVERVIEW.md
│   ├── 4-SAEULEN-SYSTEM.md
│   ├── ARCHITEKTUR-FIX-ENGINE.md
│   └── scanner_flow.excalidraw
├── technisch/                   ← Technische Referenz-Dokumente
│   ├── ENV_CONFIGURATION.md
│   ├── DATABASE_MIGRATIONS.md
│   ├── CI_CD_SETUP.md
│   ├── DEPENDENCY_INJECTION.md
│   ├── LEGAL-UPDATE-INTEGRATION.md
│   └── TECHNICAL_DEBT.md
├── anleitungen/                 ← Guides & Entwicklungsstand
│   ├── USER-GUIDE-AUTO-FIX.md
│   └── ENTWICKLUNGSSTAND.md
├── efre/                        ← EFRE-Förderantrag-Mappe
│   ├── 00_INDEX.md
│   ├── AP1–AP5 + budget + patent + kooperationen/
│   ├── FORSCHUNG_ENTWICKLUNG_NACHWEIS.md
│   ├── GREEN_COMPLIANCE_MODULE_SPEC.md
│   └── EFRE_PITCH_DECK_OUTLINE.md
└── [weitere *.md]               ← Audit-, Deployment-, Feature-Logs
```

---

## Themencluster & Dokumente

### Architektur & System

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [architektur/SYSTEM_OVERVIEW.md](architektur/SYSTEM_OVERVIEW.md) | Master-Referenz: Tech-Stack, Services, Datenpfade | Referenz |
| [architektur/4-SAEULEN-SYSTEM.md](architektur/4-SAEULEN-SYSTEM.md) | Die 4 Compliance-Säulen: Barrierefreiheit, Cookie, Rechtstexte, DSGVO | Referenz |
| [architektur/ARCHITEKTUR-FIX-ENGINE.md](architektur/ARCHITEKTUR-FIX-ENGINE.md) | Fix-Engine, Scanner, API-Architektur | Referenz |
| [architektur/scanner_flow.excalidraw](architektur/scanner_flow.excalidraw) | Scanner-Flow Diagramm | Referenz |

### Technische Referenz

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [technisch/ENV_CONFIGURATION.md](technisch/ENV_CONFIGURATION.md) | Alle Umgebungsvariablen, Pflicht vs. optional | Aktuell |
| [technisch/DATABASE_MIGRATIONS.md](technisch/DATABASE_MIGRATIONS.md) | Alembic-Befehle, Migration-Workflow | Referenz |
| [technisch/CI_CD_SETUP.md](technisch/CI_CD_SETUP.md) | GitHub Actions, Builds, Tests, Deployment | Referenz |
| [technisch/DEPENDENCY_INJECTION.md](technisch/DEPENDENCY_INJECTION.md) | FastAPI Dependencies: DB, Redis, Auth, Services | Referenz |
| [technisch/LEGAL-UPDATE-INTEGRATION.md](technisch/LEGAL-UPDATE-INTEGRATION.md) | Legal-Update-Pipeline: Webhooks, RSS, AI-Monitoring | Referenz |
| [technisch/TECHNICAL_DEBT.md](technisch/TECHNICAL_DEBT.md) | Technische Schulden & kritische TODOs | Teils veraltet |

### Anleitungen

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [anleitungen/USER-GUIDE-AUTO-FIX.md](anleitungen/USER-GUIDE-AUTO-FIX.md) | Nutzer-Guide: autonome Compliance-Behebung | Aktuell |
| [anleitungen/ENTWICKLUNGSSTAND.md](anleitungen/ENTWICKLUNGSSTAND.md) | Live-Services, implementierte Features, offene Tasks | Teils veraltet |

### EFRE / F&E-Förderantrag

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [efre/00_INDEX.md](efre/00_INDEX.md) | Master-Index EFRE-Mappe | Aktuell |
| [efre/AP1_semantische_klassifikation.md](efre/AP1_semantische_klassifikation.md) | pgvector, Hybrid-Retrieval, Multi-Label, Benchmark | Aktuell |
| [efre/AP2_autonome_empfehlungen.md](efre/AP2_autonome_empfehlungen.md) | Auto-Fix-Engine Whitepaper, Constraint-Taxonomie | Aktuell |
| [efre/AP3_adaptive_remediation.md](efre/AP3_adaptive_remediation.md) | Closed-Loop-Lernsystem, Drift-Detection | Aktuell |
| [efre/AP4_multilinguale_wissensmodelle.md](efre/AP4_multilinguale_wissensmodelle.md) | Multilingualer Korpus, EUR-Lex-Crawler | Aktuell |
| [efre/AP5_explainable_ai.md](efre/AP5_explainable_ai.md) | XAI-Schema, Norm-Citations, Counterfactuals | Aktuell |
| [efre/budget_kalkulation.md](efre/budget_kalkulation.md) | 312.950 € F&E-Budget, 250 PT | Aktuell |
| [efre/patentrecherche_auto_fix.md](efre/patentrecherche_auto_fix.md) | Patentfähigkeits-Analyse Auto-Fix-Engine | Aktuell |
| [efre/kooperationen/brief_TU_berlin.md](efre/kooperationen/brief_TU_berlin.md) | Kooperationsbrief TU Berlin | Vorlage |
| [efre/kooperationen/brief_uni_muenster.md](efre/kooperationen/brief_uni_muenster.md) | Kooperationsbrief Uni Münster (ITM) | Vorlage |
| [efre/benchmarks/legal_classification_v1.jsonl](efre/benchmarks/legal_classification_v1.jsonl) | 20 annotierte Testfälle (Ziel: 100) | In Arbeit |
| [efre/FORSCHUNG_ENTWICKLUNG_NACHWEIS.md](efre/FORSCHUNG_ENTWICKLUNG_NACHWEIS.md) | F&E-Nachweis für Förderantrag (aktualisiert) | Aktuell |
| [efre/GREEN_COMPLIANCE_MODULE_SPEC.md](efre/GREEN_COMPLIANCE_MODULE_SPEC.md) | Green-Compliance-Modul Spezifikation (CO₂-Analyse) | Spezifikation |
| [efre/EFRE_PITCH_DECK_OUTLINE.md](efre/EFRE_PITCH_DECK_OUTLINE.md) | Pitch-Deck-Vorlage für Förderstellen (15 Slides) | Vorlage |

### Security

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [SECURITY_IMPLEMENTATION_LOG.md](SECURITY_IMPLEMENTATION_LOG.md) | Round 1: DB-Passwort, Auth, Cleanup | Umgesetzt |
| [SECURITY_ROUND2_LOG.md](SECURITY_ROUND2_LOG.md) | Round 2: Logout-Cookie, CSRF, SSRF, Deps | Umgesetzt |
| [login_cors_csrf_fix.md](login_cors_csrf_fix.md) | CORS + CSRF Login-Fix | Umgesetzt |
| [CODEBASE_AUDIT_SUMMARY.md](CODEBASE_AUDIT_SUMMARY.md) | Offene Sicherheits-/Qualitätsprobleme | Teils offen |

### Fehler & Audit

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [01_ERROR_AUDIT_REPORT.md](01_ERROR_AUDIT_REPORT.md) | 163 Dashboard-Fehler-Findings | Offen |
| [02_ERROR_AUDIT_QUICK_REFERENCE.md](02_ERROR_AUDIT_QUICK_REFERENCE.md) | Top-Fix-Liste, Implementierungs-Checkliste | Offen |
| [02_STORAGE_AUDIT.md](02_STORAGE_AUDIT.md) | localStorage/sessionStorage Mapping | Referenz |
| [03_NULL_SAFETY_ANALYSIS.md](03_NULL_SAFETY_ANALYSIS.md) | Null-Safety-Probleme im Frontend | Offen |
| [04_UI_FIXES_CHECKLIST.md](04_UI_FIXES_CHECKLIST.md) | UI-Konsistenz-Checkliste | Offen |
| [LEGAL_AUDIT_REPORT.md](LEGAL_AUDIT_REPORT.md) | Rechtstext/DSGVO-Audit | Teils offen |
| [AUDIT_STATUS.md](AUDIT_STATUS.md) | Cookie/BFSG/Rechtstexte Audit-Status | Teils offen |
| [DUPLICATE_FILE_AUDIT.md](DUPLICATE_FILE_AUDIT.md) | Veraltete/doppelte Dateien | Offen |

### Cookie & Consent

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [cookie-banner-rollout-progress.md](cookie-banner-rollout-progress.md) | Rollout Phase 1+2 abgeschlossen | **Aktuellstes** |
| [cookie-banner-color-scraping.md](cookie-banner-color-scraping.md) | Brand-Color-Scraping für Banner | Umgesetzt |
| [cookie-erkennung-plan.md](cookie-erkennung-plan.md) | Plan: verbesserte Tracking-Erkennung | Offen |
| [PLAN_WEITERER_VERLAUF.md](PLAN_WEITERER_VERLAUF.md) | Phase 4–9 Plan, BUG-01 Blocker | Offen |

### Rating & Score

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [rating-volatility-fix-implementation.md](rating-volatility-fix-implementation.md) | Fix-Implementierung Score-Volatilität | Umgesetzt |
| [rating-volatility-fix-quickstart.md](rating-volatility-fix-quickstart.md) | Quickstart für Score-Fix | Referenz |
| [DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md) | Deployment-Bestätigung Score-Fix | Umgesetzt |
| [rating-volatility-root-cause.md](rating-volatility-root-cause.md) | Root-Cause-Analyse | Veraltet (Fix deployed) |

### Deployment

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [DEPLOYMENT_EXECUTE.sh](DEPLOYMENT_EXECUTE.sh) | Deployment-Skript | Aktuell |
| [DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md) | Deployment-Checkliste | Referenz |
| [INTEGRATION_PRODUCTION.md](INTEGRATION_PRODUCTION.md) | Score-Calculator Production-Integration | Umgesetzt |

### Dashboard & UI

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [dashboard-redesign-plan.md](dashboard-redesign-plan.md) | Redesign-Plan Dark-Hybrid-Theme | Offen/Plan |
| [AI_FIX_DEBUG.md](AI_FIX_DEBUG.md) | AI-Fix-Flow Debug-Notes | Offen |
| [DOMAIN_LOCK_ONBOARDING_ANALYSIS.md](DOMAIN_LOCK_ONBOARDING_ANALYSIS.md) | Domain-Lock & Payment-Quota-Analyse | Aktuell |

### Struktur & Architektur

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [PROJECT_STRUCTURE_ANALYSIS.md](PROJECT_STRUCTURE_ANALYSIS.md) | Theme, Layout, Komponenten-Inventar | Aktuell |
| [THEME_FILES_DIRECTORY_MAP.md](THEME_FILES_DIRECTORY_MAP.md) | Vollständige Theme-Datei-Map | Aktuell |
| [THEME_QUICK_REFERENCE.md](THEME_QUICK_REFERENCE.md) | Theme-Switching Quick Reference | Aktuell |
| [QUALITY_PROCESS_DOCUMENTATION.md](QUALITY_PROCESS_DOCUMENTATION.md) | Legal-Update-Pipeline Qualitätsprozess | Aktuell |
| [KNOWLEDGE_VAULT_STRUCTURE.md](KNOWLEDGE_VAULT_STRUCTURE.md) | Obsidian Knowledge Vault Struktur | Aktuell |

### Landing & Marketing

| Dokument | Inhalt | Status |
|----------|--------|--------|
| [saas-landing-done.md](saas-landing-done.md) | Abgeschlossene Landing-Komponenten | Umgesetzt |
| [agency-page-rewrite.md](agency-page-rewrite.md) | Agency-Page Rewrite-Plan | Offen |

### Veraltete / historische Dokumente

Diese Dokumente sind abgelöst oder nur noch historisch relevant:

| Dokument | Warum veraltet |
|----------|----------------|
| [00_INDEX.md](00_INDEX.md) — diese Datei war alt | Ersetzt durch diese Version |
| [ANLEITUNG_WIDGET_SICHTBAR_MACHEN.md](ANLEITUNG_WIDGET_SICHTBAR_MACHEN.md) | Bezieht sich auf lokalen Dev-Stand vom 2026-05-02 |
| [rating-volatility-root-cause.md](rating-volatility-root-cause.md) | Problem behoben und deployed |
| [FINAL_SUMMARY.md](FINAL_SUMMARY.md) | Zusammenfassung Rating-Fix — deployed |

---

## Bekannte technische Schulden (nach Priorität)

| Priorität | Problem | Modul |
|-----------|---------|-------|
| Hoch | `cookie_compliance_stats` Schema-Mismatch (B-01) | `backend/cookie_compliance_routes.py` |
| Mittel | Token-Migration (P1-Item, größeres Refactoring) | `backend/auth_service.py` |
| Mittel | Error-Audit 163 Findings: Umsetzung nicht dokumentiert | `dashboard-react/` |
| Mittel | Redis Scan-Caching: Status unklar | `backend/compliance_engine/` |
| Niedrig | APM/Uptime-Monitoring fehlt | Infra |
| Niedrig | Black/Prettier/flake8 nicht einheitlich | Gesamtprojekt |
| Niedrig | Docstrings und Type Hints unvollständig | `backend/` |
| Niedrig | TCF 2.2 IAB-Registrierung (bedarfsgesteuert) | `backend/widgets/cookie_banner_v2.js` |

---

## Neue Migrationen (noch nicht alle in Produktion)

Folgende Migrations-Dateien wurden im Rahmen der EFRE-Implementierung erstellt und müssen noch ausgerollt werden:

| Datei | Inhalt |
|-------|--------|
| `backend/migrations/add_pgvector_knowledge.sql` | pgvector Extension + knowledge_embeddings + classification_benchmark_runs |
| `backend/migrations/add_fix_acceptance_metrics.sql` | fix_acceptance_metrics Tabelle + View |
| `backend/migrations/add_prompt_versioning.sql` | prompt_versions + fix_outcomes + classification_drift_log |
| `backend/migrations/add_xai_explanation_fields.sql` | cited_norms, triggering_factors, counterfactuals Spalten in ai_compliance_logs |

---

## Neue Produktions-Komponenten (EFRE-Implementierung)

| Komponente | Datei | Beschreibung |
|------------|-------|-------------|
| Hybrid-Retrieval | `backend/knowledge/knowledge_retriever.py` | BM25 + Embedding kombiniert |
| Language-Aware Retrieval | `backend/knowledge/language_aware_retriever.py` | Spracherkennung + cross-linguales Fallback |
| XAI-Schema | `backend/ai_legal_classifier.py` | NormReference, ExplanationDoc, build_explanation() |
| Closed-Loop Learning | `backend/ai_feedback_learning.py` | _trigger_learning_if_needed() + _adapt_prompts_from_feedback() |
| EUR-Lex-Crawler | `backend/cronjobs/eurlex_crawler.py` | Monatlicher Korpus-Update (nicht aktiv geplant) |
| Drift-Detector | `backend/cronjobs/drift_detector.py` | Wöchentliche KL-Divergenz-Prüfung (nicht aktiv geplant) |
| XAI-Frontend | `dashboard-react/src/components/XAIExplanationCard.tsx` | Norm-Zitate + Confidence-Breakdown UI |
| Fix-Outcome-Route | `backend/fix_routes.py` | POST /api/fixes/{fix_id}/outcome |
| i18n 5 Sprachen | `backend/i18n_service.py` | DE/EN/FR/IT/PL |
| Multilinguale Wissensmodelle | `knowledge/laws/de|en|fr|it|pl/` | Rechtsnormen-Korpus strukturiert |
| Norm-Mapping-Ontologie | `knowledge/laws/_mapping.yaml` | DSGVO↔GDPR↔RGPD Cross-Referenzen |
