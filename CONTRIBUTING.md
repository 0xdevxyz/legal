# Contributing to Complyo

## Dokumentationsprotokoll (Pflicht)

Jede Code-Änderung erfordert eine Dokumentations-Aktualisierung. Keine Ausnahmen.

### Was muss immer aktualisiert werden?

| Änderung | CHANGELOG.md | Weitere Datei |
|----------|-------------|--------------|
| Bugfix | Eintrag unter aktuellem Datum | — |
| Neues Feature | Eintrag unter aktuellem Datum | `docs/SYSTEM_OVERVIEW.md` wenn neue Route, Service oder DB-Tabelle |
| Neue API-Route | Eintrag + Route-Tabelle in `docs/SYSTEM_OVERVIEW.md` aktualisieren | — |
| Neuer DB-Table | Eintrag + Tabellen-Liste in `docs/SYSTEM_OVERVIEW.md` aktualisieren | — |
| Neuer Service/Handler | Eintrag + Service-Tabelle in `docs/SYSTEM_OVERVIEW.md` aktualisieren | — |
| Security-Fix | Eintrag mit Kategorie `### Security` | `docs/TECHNICAL_DEBT.md` Eintrag schließen |
| Tech-Debt behoben | Eintrag mit Kategorie `### Tech Debt` | `docs/TECHNICAL_DEBT.md` Eintrag als erledigt markieren |
| Neues offenes Problem entdeckt | — | `docs/TECHNICAL_DEBT.md` Eintrag hinzufügen |
| Deployment-Änderung | Eintrag mit Kategorie `### Infrastruktur` | `docs/ENTWICKLUNGSSTAND.md` Status-Tabelle prüfen |
| Widget-Update | Eintrag mit Kategorie `### Widgets` | Widget-Tabelle in `docs/SYSTEM_OVERVIEW.md` prüfen |

### CHANGELOG-Format

```markdown
## [YYYY-MM-DD]

### Kategorie (Backend | Frontend | Security | Tech Debt | Infrastruktur | Widgets | Dokumentation)
- Konkrete Beschreibung was geändert wurde
- Betroffene Datei(en) wenn nicht offensichtlich: `backend/datei.py:Zeile`
```

### Wo stehen welche Informationen?

| Frage | Datei |
|-------|-------|
| Was ist das System? Wie ist es aufgebaut? | `docs/SYSTEM_OVERVIEW.md` |
| Was ist aktuell offen, was ist fertig? | `docs/ENTWICKLUNGSSTAND.md` |
| Was wurde wann geändert? | `CHANGELOG.md` |
| Welche Schulden / Bugs existieren? | `docs/TECHNICAL_DEBT.md` |
| Wie ist die DB-Migrationshistorie? | `backend/MIGRATIONS.md` |
| Was sind die Architektur-Entscheidungen? | `.planning/PROJECT.md` + `.planning/ROADMAP.md` |
| Welche Env-Variablen gibt es? | `docs/ENV_CONFIGURATION.md` |

### Historische Dokumente (nur lesen, nicht mehr bearbeiten)

Die Dateien in `md/` (z.B. `COOKIE_BANNER_DEBUG.md`, `WIDGET-V5-BUGFIXES.md`) sind historische Aufzeichnungen aus der Entwicklungsphase. Sie werden nicht mehr aktualisiert – neue Informationen kommen in `CHANGELOG.md` und `docs/`.

---

## Entwicklungsumgebung einrichten

```bash
cp .env.example .env
# .env befüllen
docker-compose up -d postgres redis
cd backend && pip install -r requirements.txt
uvicorn main_production:app --reload --port 8002
```

## Branch-Strategie

- `main` – Production-ready
- `feature/xxx` – Neue Features
- `fix/xxx` – Bugfixes
- `chore/xxx` – Refactoring, Deps, Doku

## Commit-Konventionen

```
feat: neue Funktion
fix: Bugfix
chore: Wartung, Dependencies
security: Sicherheitsfix
docs: Dokumentation
test: Tests
```

## Code-Standards

- **Python**: PEP 8, Type Hints, keine hardcodierten Credentials
- **TypeScript**: Strict Mode aktiv, kein `any` ohne Kommentar, `sanitizeHtml()` bei `dangerouslySetInnerHTML`
- **Tests**: Neue Backend-Features brauchen Unit-Tests in `backend/tests/`
- **Secrets**: Niemals Secrets committen – alle Werte via Env-Variablen

## Pull Request Checkliste

- [ ] `python3 -m pytest backend/tests/ -v` grün
- [ ] `cd dashboard-react && npm run lint` ohne Fehler
- [ ] `cd dashboard-react && npm run type-check` ohne Fehler
- [ ] Keine neuen Secrets oder hardcodierten Credentials
- [ ] `CHANGELOG.md` aktualisiert (Pflicht, siehe Dokumentationsprotokoll oben)
- [ ] `docs/SYSTEM_OVERVIEW.md` aktualisiert falls neue Route / Service / DB-Tabelle
- [ ] `docs/TECHNICAL_DEBT.md` aktualisiert falls Tech-Debt behoben oder neu entdeckt

## Sicherheitsrelevante Änderungen

Sicherheitslücken bitte **nicht** als öffentliches Issue melden, sondern direkt per E-Mail an das Team.
