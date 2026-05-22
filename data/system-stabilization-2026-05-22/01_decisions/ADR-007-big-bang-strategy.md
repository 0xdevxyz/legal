# ADR-007: Big-Bang-Strategie (kein Staging)

Datum: 2026-05-22
Status: Accepted

## Context
App ist noch in Entwicklung, kein produktiver Einsatz. Kein Staging-Environment geplant.
Scope: 12 Phasen gleichzeitig als sequentieller Sprint.

## Decision
Big-Bang: alle 12 Phasen sequenziell auf Branch rebuild-2026-05-22, dann merge auf main.
Kein Feature-Flagging, kein Rollback-by-Feature.

## Rollback-Strategie
- Docker Image Tag: pre-rebuild-2026-05-22
- Git: Branch main bleibt unberührt bis merge
- DB: db_schema_pre.sql als Restore-Basis
- Runbook: /04_runbooks/rollback.sh

## Consequences
- Alle Änderungen auf rebuild-2026-05-22
- Merge auf main nach P12 (E2E-Tests grün)
- Docker rebuild nach P1, P2, P6 (Breaking Changes)
