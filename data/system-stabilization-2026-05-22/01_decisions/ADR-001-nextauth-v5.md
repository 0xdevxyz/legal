# ADR-001: NextAuth.js v5 als Auth-Layer

Datum: 2026-05-22
Status: Accepted

## Context
Das bestehende Auth-System basiert auf manuellem Cookie-Management in FastAPI (auth_routes.py) mit einem React-Context (AuthContext.tsx). Es hat mehrere kritische Bugs:
- Cookie-Path-Mismatch (RC-1): set_cookie(path="/") vs delete_cookie(path="/api/auth") → Cookie nie gelöscht
- Refresh-Loop (RC-2): Kein Cookie-Check vor Refresh-Call → Endlos-401

## Decision
Vollständige Migration auf NextAuth.js v5 (Auth.js).

## Consequences
- Backend wird zu reinem Credentials-Provider: POST /api/auth/verify-credentials
- AuthContext.tsx, auth-api.ts, hooks/useAuth.ts werden gelöscht
- Dashboard middleware.ts wird NextAuth-basiert
- Session via JWT (NextAuth-Secret), HttpOnly-Cookie via NextAuth
- Backend-Endpoints: /api/auth/verify-credentials, /api/auth/session-info, /api/auth/csrf-token
