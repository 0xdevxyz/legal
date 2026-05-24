# Complyo Big Bang Rebuild - Index
Datum: 2026-05-22
Branch: rebuild-2026-05-22
Strategie: Big-Bang (sequenziell, 12 Phasen)

## Verzeichnisstruktur

```
system-stabilization-2026-05-22/
├── 00_baseline/
│   ├── console_log_pre_rebuild.md   - Browser-Konsolen-Fehler (8 Root Causes)
│   ├── db_schema_pre.sql            - PostgreSQL Schema-Dump (4322 lines)
│   ├── backend_logs_pre.txt         - Backend Logs vor Rebuild
│   └── docker_snapshot_pre.md      - Container-Status + Inventory
├── 01_decisions/
│   ├── ADR-001-nextauth-v5.md       - NextAuth.js v5 Migration
│   ├── ADR-002-shadcn-tailwind-v4.md - UI-Stack Entscheidung
│   ├── ADR-003-rbac-roles.md        - Rollen-Modell admin/agency/customer
│   ├── ADR-004-sentry-self-hosted.md - Sentry auf sentry.complyo.de
│   ├── ADR-005-widget-proxy.md      - Widget Domain-Fix + First-Party-Proxy
│   ├── ADR-006-stripe-consolidation.md - Stripe-Path-Konsolidierung
│   └── ADR-007-big-bang-strategy.md - Rollout-Strategie
├── 02_phases/                       - Phase-Logs P1-P12
├── 03_diagrams/                     - Architektur-Diagramme
├── 04_runbooks/
│   └── rollback.sh                  - Rollback-Skript
└── 99_final/                        - Final Report nach P12

## Root Causes

| ID | Datei | Problem | Phase |
|----|-------|---------|-------|
| RC-1 | auth_routes.py | set_cookie(path="/") vs delete_cookie(path="/api/auth") | P1 |
| RC-2 | AuthContext.tsx | Refresh-Call ohne Cookie-Check → 401-Loop | P2 |
| RC-3 | - | Folgefehler RC-1/RC-2: Onboarding-Loop | P2 |
| RC-4 | main_production.py:~1090 | /api/v2/analyze 500 | P3 |
| RC-5 | - | /api/legal-ai/updates 401 (Folgefehler Auth) | P2 |
| RC-6 | widgets/*.js | hardcoded api.complyo.tech | P4 |
| RC-7 | api.ts | createCheckoutSession falscher Pfad | P5 |
| RC-8 | auth_routes.py | CSRF nicht initialisiert | P1 |

## Tech Stack (Neu)
- Auth: NextAuth.js v5 (Auth.js)
- UI: shadcn/ui v2 + Tailwind v4 (OKLCH)
- State: TanStack Query v5 + Zustand
- Sentry: Self-Hosted (sentry.complyo.de)
- Rollen: admin / agency / customer
- Widgets: api.complyo.de + static.complyo.de First-Party-Proxy

## Phase-Status

| Phase | Beschreibung | Status |
|-------|-------------|--------|
| P0 | Vorbereitung & Baseline | completed |
| P1 | Backend Auth-Hardening | completed |
| P2 | NextAuth.js v5 Migration | completed |
| P3 | Re-Scan 500 Fix | completed |
| P4 | Widgets + First-Party-Proxy | completed |
| P5 | Stripe-Path-Konsolidierung | completed |
| P6 | Redesign Foundation | completed |
| P7 | Redesign Pages | completed |
| P8 | Sentry Self-Hosted | completed |
| P9 | Notifications-System | completed |
| P10 | Dashboard-Widgets + Multi-Domain | completed |
| P11 | Audit-Log + Export/Backup + Admin-Panel | completed |
| P12 | E2E-Tests + Cutover + Final-Report | completed |
```
