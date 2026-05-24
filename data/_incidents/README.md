# Incident Log – Schema & Workflow

## Zweck
Jeder produktionsrelevante Fehler, Datenverlust-Risiko oder Sicherheitsvorfall wird hier strukturiert dokumentiert.
Ziel: Schnelle Orientierung, keine Wiederholung, Pattern-Erkennung.

## Severity-Level
| Level | Definition | Reaktionszeit |
|-------|-----------|---------------|
| P0 | Produktionsausfall / Datenverlust-Risiko | Sofort |
| P1 | Kritische Funktion beeinträchtigt (Login, Payment, Scan) | < 1h |
| P2 | Feature degradiert, Workaround existiert | < 24h |
| P3 | Minor Bug / Performance / Kosmetik | Nächster Sprint |

## Dateistruktur
```
/data/_incidents/
├── README.md          ← dieses Dokument
├── INDEX.md           ← Tabellen-Index aller Incidents
└── YYYY-MM-DD_<slug>/
    └── YYYY-MM-DD_<slug>.md
```

## Slug-Konvention
`YYYY-MM-DD_<kurze-beschreibung-mit-bindestrichen>`

Beispiel: `2026-05-24_in-memory-oauth-state-loss`

## Pflichtfelder pro Incident
```markdown
# <SLUG>

**Datum**: YYYY-MM-DD
**Severity**: P0 / P1 / P2 / P3
**Status**: open / resolved / won't-fix
**Trigger**: Was hat den Incident ausgelöst?
**Betroffene Komponenten**: z.B. git_routes.py, Redis, Auth
**Root Cause**: Technische Ursache (nicht Symptom)
**Fix-Commit**: <git-hash> oder "pending"
**Lessons Learned**: Was ändert sich am Prozess?
**Pattern-Tag**: `in-memory` / `auth` / `data-loss` / `regression` / `config` / `dependency`
```

## Workflow
1. Incident entsteht → Ordner + Datei anlegen (sofort, auch unvollständig)
2. Root Cause gefunden → ausfüllen
3. Fix committed → Fix-Commit eintragen
4. `INDEX.md` aktualisieren
5. Status auf `resolved` setzen

## Verbotenes
- Incidents NICHT rückwirkend schönreden
- Lessons Learned NICHT leer lassen
- Keine Incidents löschen (höchstens `won't-fix`)
