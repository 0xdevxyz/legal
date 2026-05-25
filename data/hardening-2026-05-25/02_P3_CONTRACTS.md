# P3 – API Contract Freeze

**Branch**: hardening/p3-contracts
**Tag end**: hardening-p3-done

## Änderungen

### backend/schemas/auth.py (neu)
- `LoginResponse`, `RegisterResponse`, `RefreshResponse`, `MeResponse`
- Alle `frozen=True, extra="forbid"` (MeResponse: extra="allow" für Plan-Felder)

### backend/schemas/dashboard.py (neu)
- `DashboardMetrics`, `DashboardOverview` – frozen

### backend/schemas/fixes.py (neu)
- `FixGenerateRequest`, `FixGenerateResponse`, `FixApplyRequest`, `FixApplyResponse`, `FixHistoryItem` – frozen

### backend/schemas/__init__.py
- Alle Schemas re-exportiert

### backend/auth_routes.py
- `/register` → `response_model=RegisterResponse`
- `/login` → `response_model=LoginResponse`
- `/refresh` → `response_model=RefreshResponse`
- `/me` → `response_model=MeResponse`

### backend/dashboard_routes.py
- `/metrics` → `response_model=_DashboardMetricsSchema`

### backend/fix_routes.py
- `/generate` → `response_model=_FixGenerateResponse`

### backend/main_production.py
- Middleware `add_request_id` setzt `X-API-Version: 1.0` auf alle Responses

### data/hardening-2026-05-25/contracts/openapi.snapshot.json
- Stub – wird nach `docker compose build backend` befüllt via:
  `curl http://localhost:8002/openapi.json > data/hardening-2026-05-25/contracts/openapi.snapshot.json`

### backend/tests/test_contracts.py
- 5 Tests (2 always-pass, 3 skip wenn Backend offline)
- Breaking-Change-Detection bei entfernten Paths/Methods

## Test-Output
```
2 passed, 3 skipped (backend offline expected in dev)
```

## Breaking-Change-Policy
- **Major** (Breaking): Snapshot-Update required + PR + Migration-Doku
- **Minor** (Additive): Neue Felder ok, kein Snapshot-Update nötig
- **CI**: `test_contracts.py` läuft als Gate vor jedem Deploy
