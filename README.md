# Complyo – DSGVO & BFSG Compliance Plattform

KI-gestützte Compliance-Plattform für DSGVO, TTDSG und BFSG.

## Stack

| Komponente | Technologie | Port |
|------------|------------|------|
| Backend API | FastAPI (Python 3.11) | 8002 |
| Dashboard | Next.js 14 | 3001 |
| Landing Page | Next.js 14 | 3003 |
| Datenbank | PostgreSQL 15 | 5433 |
| Cache | Redis | 6379 |

## Quickstart

```bash
cp .env.example .env
# .env befüllen
docker-compose up -d
```

## Entwicklung

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main_production:app --reload --port 8002

# Dashboard
cd dashboard-react && npm install && npm run dev

# Landing
cd landing-react && npm install && npm run dev
```

## Tests

```bash
# Backend Unit-Tests
cd backend && python3 -m pytest tests/ -v

# E2E-Tests (laufende Container erforderlich)
cd dashboard-react && npx playwright test
```

## Monitoring

- Health: `GET /health`
- Metriken: `GET /metrics` (Bearer `METRICS_TOKEN`)
- API-Docs: `GET /docs` (nur wenn `ENVIRONMENT != production`)

## Migrations

Alle SQL-Migrations werden beim Start automatisch ausgeführt. Übersicht: [`backend/MIGRATIONS.md`](backend/MIGRATIONS.md)

## Wichtige Umgebungsvariablen

Siehe [`.env.example`](.env.example) für alle erforderlichen Variablen.
