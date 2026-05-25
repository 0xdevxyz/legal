# API Contract – Breaking Change Policy

## Scope
Auth (`/api/auth/*`), Dashboard (`/api/v2/dashboard/*`), Fix (`/api/v2/fixes/*`)

## Rules

### Major (Breaking) – Snapshot-Update required
- Entfernte Felder aus Response-Schema
- Geänderte Feld-Typen (z.B. `int` → `str`)
- Entfernte Endpoints
- Geänderte HTTP-Methode

**Prozess**: PR mit neuem Snapshot + `BREAKING CHANGE` in Commit-Message + Migration-Doku in `data/hardening-*/contracts/`

### Minor (Additive) – No Snapshot-Update
- Neue optionale Felder in Response (alle Schemas haben `extra="allow"`)
- Neue Endpoints
- Neue Query-Parameter (optional)

## Current Version
`X-API-Version: 1.0`

## Snapshot Location
`data/hardening-2026-05-25/contracts/openapi.snapshot.json`

## CI Gate
`pytest backend/tests/test_contracts.py -v` – muss grün sein vor Deploy
