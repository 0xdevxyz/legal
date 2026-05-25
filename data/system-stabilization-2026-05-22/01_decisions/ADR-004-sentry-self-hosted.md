# ADR-004: Self-Hosted Sentry (sentry.complyo.de)

Datum: 2026-05-22
Status: Accepted

## Context
Kein Error-Monitoring vorhanden. Das sentry-sdk[fastapi] ist zwar in requirements.txt, aber SENTRY_DSN ist nicht konfiguriert. Keine Frontend-Error-Boundaries.

## Decision
Self-Hosted Sentry auf sentry.complyo.de via docker-compose.sentry.yml.

## Consequences
- docker-compose.sentry.yml mit onpremise-setup
- Backend: SENTRY_DSN_BACKEND ENV → sentry_sdk.init() in main_production.py
- Frontend: @sentry/nextjs, instrumentation.ts + instrumentation-client.ts
- Error-Boundaries: global in layout.tsx + pro kritische Page
- Releases: git commit hash als release tag
