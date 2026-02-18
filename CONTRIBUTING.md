# Contributing to Complyo

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
- [ ] CHANGELOG.md aktualisiert

## Sicherheitsrelevante Änderungen

Sicherheitslücken bitte **nicht** als öffentliches Issue melden, sondern direkt per E-Mail an das Team.
