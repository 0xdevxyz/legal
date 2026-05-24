# Phase C – Fix-Engine-Konsolidierung

**Branch**: `cleanup/phase-c-fix-engines`
**Datum**: 2026-05-24
**Status**: completed (AIComplianceFixer migration deferred – see below)

## Audit-Ergebnis

### Fix-Engine-Inventar (vorher)
| Datei | LOC | Status | Aktion |
|-------|-----|--------|--------|
| `backend/ai_fix_engine/unified_fix_engine.py` | 648 | Aktiv, Single-Source | BEHALTEN |
| `backend/fix_generator.py` | 1045 | Legacy, wurde von `fix_routes.py` genutzt | GELÖSCHT |
| `backend/compliance_engine/enhanced_fixer.py` | 359 | Nie genutzt (enhanced_fixer_routes.py orphaned) | GELÖSCHT |
| `backend/enhanced_fix_routes.py` | ~350 | Orphaned (kein `include_router`) | GELÖSCHT |
| `backend/compliance_engine/fixer.py` | 781 | Noch aktiv in `main_production.py:1212` | MIGRATION DEFERRED |

### Durchgeführte Migrationen

#### fix_generator.py → UnifiedFixEngine
- `main_production.py:82`: `from fix_generator import FixGenerator` → `from ai_fix_engine.unified_fix_engine import UnifiedFixEngine as FixGenerator`
- `main_production.py:460`: `FixGenerator(db_pool)` → `FixGenerator()` (UnifiedFixEngine benötigt keinen db_pool)
- `fix_routes.py:164,596`: `generate_fix(issue_id, issue_category, user_id, plan_type)` → `generate_fix(issue={...}, context={...})`

#### enhanced_fixer.py + enhanced_fix_routes.py
- Beide orphaned: `enhanced_fix_routes.py` hatte keinen `include_router`-Eintrag in `main_production.py`
- Einfach gelöscht ohne Migration notwendig

### Deferred: AIComplianceFixer (compliance_engine/fixer.py)
`main_production.py:1212` instantiiert noch `AIComplianceFixer()` für `/api/v2/ai-fix` Endpoint.
- Migration zu `UnifiedFixEngine` erfordert Interface-Mapping für `fix_compliance_issues(scan_id, violations, company_info)`
- `UnifiedFixEngine.generate_fix(issue, context)` verarbeitet ein Issue pro Call; Batch-Wrapper nötig
- **Empfehlung**: In Phase C+1 (nächste Iteration) umstellen, mit Integration-Test

## Gelöschte Dateien
```
backend/fix_generator.py              (1045 LOC)
backend/compliance_engine/enhanced_fixer.py  (359 LOC)
backend/enhanced_fix_routes.py        (~350 LOC)
```
Gesamt entfernt: ~1754 LOC

## Beibehaltene Dateien
```
backend/ai_fix_engine/unified_fix_engine.py    ← Single-Source Fix Engine
backend/compliance_engine/fixer.py             ← Noch aktiv, Migration deferred
```

## Commit + Tag
- Commit: `chore(cleanup-c): consolidate fix engines - remove legacy generators`
- Tag: `cleanup-phase-c-done`
