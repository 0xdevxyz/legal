# Phase A – Dead Code Purge

**Branch**: `cleanup/phase-a-dead-code`
**Datum**: 2026-05-24
**Status**: completed

## Was wurde gelöscht

### 1. Legacy Widget-Dateien
| Datei | Grund |
|-------|-------|
| `backend/widgets/accessibility.js` | Veraltet, v6 ist aktiv |
| `backend/widgets/accessibility_smart.js` | Experimentell, nie produktiv |
| `backend/widgets/accessibility-v5.js` | Durch v6 ersetzt |
| `backend/widgets/cookie_consent.legacy.js` | Legacy-Version, ersetzt durch `cookie_banner_v2.js` |
| `backend/widgets/cookie_consent.legacy.js.bak` | Backup-Kopie, kein Wert |

**Code-Anpassung**: `widget_routes.py:166-180` – Version-Parameter entfernt, Route liefert immer `accessibility-v6.js`.

### 2. eRecht24-Reste
| Datei | Grund |
|-------|-------|
| `backend/init_erecht24_projects.sql` | eRecht24 komplett migriert (Removal 2026-05-23) |
| `backend/migration_erecht24_fixed.sql` | eRecht24-Migration abgeschlossen |
| `backend/migration_erecht24_full.sql` | eRecht24-Migration abgeschlossen |
| `backend/migrations/migration_deprecate_erecht24.sql` | Bereits eingespielt |
| `backend/migrations/migration_deprecate_erecht24_rollback.sql` | Rollback irrelevant, DB migriert |
| `backend/scripts/export_erecht24_data.py` | Export-Script für beendete Migration |

**Code-Anpassung**: `backend/init_all_tables.sh:17` – `init_erecht24_projects.sql` aus SQL-Liste entfernt.

### 3. Disabled-Files
| Datei | Grund |
|-------|-------|
| `backend/sql/init_alt_text_fixes.sql.disabled` | Disabled = nie ausgeführt, Inhalt ist in aktiver Migration |

## Beibehaltene Widget-Dateien (aktiv)
```
backend/widgets/accessibility-v6.js   ← Einzige aktive Version
backend/widgets/content_blocker.js
backend/widgets/cookie_banner_v2.js
backend/widgets/locales/translations.js
backend/widgets/optout_center.js
```

## Verifikation
- `grep -r "accessibility-v5\|accessibility_smart\|cookie_consent.legacy" backend/` → 0 Treffer
- `grep -r "init_erecht24\|migration_erecht24\|export_erecht24" backend/*.py` → 0 Treffer (nur init_all_tables.sh bereinigt)
- Keine `.bak`, `.disabled` Dateien mehr im `backend/` Verzeichnis (außer .next/cache)

## Commit + Tag
- Commit: `chore(cleanup-a): remove legacy widgets, erecht24 remnants, disabled files`
- Tag: `cleanup-phase-a-done`
