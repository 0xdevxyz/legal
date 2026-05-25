# Cleanup 2026-05-24 – Index

> **Vision-Anker (Nordstern, SPÄTER)**: "KI-gestützte Infrastrukturtechnologie zur kontinuierlichen regulatorischen Website-Compliance für KMU"
> **AKTUELLE PHASE: STABILITÄT. KEINE Innovation.**

## Ziel
Mentale Entlastung + technische Schuldenreduktion + Wahrheits-Anker. Kein neues Feature. Fokus: PRODUKTVERTRAUEN.

## Strategie
Hybrid – offensichtlich totes hart löschen, sensibles sicher migrieren, Wahrheit am Ende dokumentieren.

## Branch-Schema
| Phase | Branch | Tag |
|-------|--------|-----|
| 0 – Pre-Flight | `cleanup/phase-0-preflight` | `pre-cleanup-baseline` |
| A – Dead Code | `cleanup/phase-a-dead-code` | `cleanup-phase-a-done` |
| B – Libraries | `cleanup/phase-b-libraries` | `cleanup-phase-b-done` |
| C – Fix Engines | `cleanup/phase-c-fix-engines` | `cleanup-phase-c-done` |
| D – Route Audit | `cleanup/phase-d-routes` | `cleanup-phase-d-done` |
| E – No In-Memory | `cleanup/phase-e-no-fallback` | `cleanup-phase-e-done` |
| F – Truth Docs | `cleanup/phase-f-truth-docs` | `cleanup-complete` |

## Phasen-Status
| Phase | Status | Datei |
|-------|--------|-------|
| 0 – Pre-Flight | in_progress | 01_BASELINE.md, _smoke_test.md |
| A – Dead Code | pending | 02_PHASE_A_DEAD_CODE.md |
| B – Libraries | pending | 03_PHASE_B_LIBRARIES.md |
| C – Fix Engines | pending | 04_PHASE_C_FIX_ENGINES.md |
| D – Route Audit | pending | 05_PHASE_D_ROUTE_AUDIT.md |
| E – No In-Memory | pending | 06_PHASE_E_NO_INMEMORY.md |
| F – Truth Docs | pending | 07_PHASE_F_TRUTH_DOCS.md |
| Final Report | pending | 99_FINAL_REPORT.md |

## Akzeptanzkriterien
### Code
- Keine `*.bak`, `*.disabled`, `*.legacy.*` Dateien
- Keine eRecht24-Referenz im aktiven Code
- Genau eine JWT-Lib, eine Pwd-Lib, eine Fix-Engine
- Kein `use_fallback`-Branch in `database_service.py`
- Kein In-Memory für State / Rate-Limit / Sessions
- Jede Route auth-gesichert oder explizit public
- Smoke-Test (Login → Scan → Dashboard → Fix-Apply → Cookie-Banner) grün

### Dokumentation
- `/data/cleanup-2026-05-24/` komplett (00–07 + 99)
- `/data/_truth/ARCHITECTURE_TRUTH.md` + `KILL_LIST.md` vorhanden
- `/data/_incidents/` mit Schema und Index
