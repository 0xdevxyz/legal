# Phase 8: Sentry Self-Hosted
Datum: 2026-05-22
Status: completed

## Backend
- `main_production.py`: Sentry init ergänzt um `profiles_sample_rate=0.05`, `release=GIT_COMMIT`, `send_default_pii=False`
- `sentry-sdk[fastapi]>=2.0.0` bereits in requirements.txt

## Frontend
- `@sentry/nextjs@10.53.1` installiert
- `src/instrumentation.ts`: Server-Side Sentry init (nodejs + edge runtime)
- `src/instrumentation-client.ts`: Client-Side Sentry init mit Replay-Integration
- `next.config.js`: `withSentryConfig()` Wrapper, `tunnelRoute: '/monitoring'`, `hideSourceMaps: true`
- CSP: `https://sentry.complyo.de` in `connect-src` ergänzt

## docker-compose.sentry.yml (neu)
- `getsentry/sentry:24.11.0`
- Services: sentry-web (Port 9000), sentry-worker, sentry-cron, sentry-redis, sentry-postgres
- Volumes: sentry_data, sentry_pg_data, sentry_redis_data
- ENV: SENTRY_SECRET_KEY, SENTRY_DB_PASSWORD

## Deployment
```bash
docker compose -f docker-compose.sentry.yml up -d
docker exec -it sentry-web sentry upgrade
docker exec -it sentry-web sentry createuser
```

## ENV-Vars (ergänzen in .env)
```
SENTRY_DSN=https://...@sentry.complyo.de/1
SENTRY_SECRET_KEY=<random 50 chars>
SENTRY_DB_PASSWORD=<strong password>
NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.complyo.de/1
SENTRY_ORG=complyo
SENTRY_PROJECT=dashboard
SENTRY_AUTH_TOKEN=<sentry auth token>
GIT_COMMIT=$(git rev-parse --short HEAD)
```

## TypeScript
- `tsc --noEmit`: 0 Fehler ✓
