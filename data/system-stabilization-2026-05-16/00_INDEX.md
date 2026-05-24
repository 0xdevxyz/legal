# System-Stabilisierung – Index

**Datum:** 2026-05-16  
**Session-Ziel:** Auth → Scan → Widget konsolidieren

## Status

| Phase | Beschreibung | Status |
|-------|-------------|--------|
| Phase 0 | Vorbereitung & Baseline-Audit | ✅ Abgeschlossen |
| Phase 1 | Auth-Konsolidierung (8 → 1 get_current_user) | ✅ Deployed |
| Phase 2 | Scan-500 Fix (score_history + Logging) | ✅ Deployed |
| Phase 3 | Widget Null-Guard (closePanel) | ✅ Deployed |
| Phase 4 | End-to-End Final Report | ✅ Bereit für Live-Test |

## Sub-Reports

- [01_AUTH_BASELINE.md](./01_AUTH_BASELINE.md) — Ist-Zustand der 8 Varianten
- [01_AUTH_CONSOLIDATION.md](./01_AUTH_CONSOLIDATION.md) — Phase 1 Diff
- [02_SCAN_500_ROOT_CAUSE.md](./02_SCAN_500_ROOT_CAUSE.md) — Phase 2 Root Cause
- [03_WIDGET_FIX.md](./03_WIDGET_FIX.md) — Phase 3 Null-Guard
- [04_FINAL_REPORT.md](./04_FINAL_REPORT.md) — Abschlussbericht

## Offene Punkte (Folge-Session)

- `scan_history.website_id` UUID-Migration
- `cookie_ab_tests` Tabelle anlegen
- Auth-E2E-Tests
