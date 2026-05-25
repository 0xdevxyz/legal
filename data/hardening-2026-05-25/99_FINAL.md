# Hardening 2026-05-25 – Final Report

**Tag**: `hardening-2026-05-25-complete`
**Datum**: 2026-05-25
**Branches**: hardening/p2-auth, hardening/p3-contracts, hardening/p4-monitoring → main

---

## Ergebnisse

### P2 – Auth Hardening ✅

| Kriterium | Status |
|-----------|--------|
| 12/12 Tests grün | ✅ |
| JWT mit jti + iat + nbf | ✅ |
| Redis JTI-Blacklist | ✅ |
| Refresh-Token-Rotation | ✅ |
| Reuse-Detection (alle Sessions gelöscht) | ✅ |
| POST /auth/logout (JTI blacklisten) | ✅ |
| POST /auth/logout-all (alle JTIs + Sessions) | ✅ |
| ACCESS_TOKEN_EXPIRE_MINUTES default 15 | ✅ |
| user_sessions Migration SQL | ✅ |

### P3 – API Contract Freeze ✅

| Kriterium | Status |
|-----------|--------|
| schemas/auth.py (LoginResponse, etc.) frozen | ✅ |
| schemas/dashboard.py frozen | ✅ |
| schemas/fixes.py frozen | ✅ |
| response_model auf auth Endpoints | ✅ |
| response_model auf dashboard Endpoints | ✅ |
| response_model auf fix /generate | ✅ |
| X-API-Version: 1.0 Header | ✅ |
| openapi.snapshot.json committed (stub) | ✅ (Update nach docker compose build) |
| test_contracts.py: 2 pass, 3 skip (backend offline) | ✅ |
| data/_truth/API_CONTRACT.md | ✅ |

### P4 – Monitoring Dashboard ✅

| Kriterium | Status |
|-----------|--------|
| complyo_scans_total Counter | ✅ |
| complyo_fixes_total Counter | ✅ |
| complyo_openrouter_total Counter (in unified_fix_engine) | ✅ |
| complyo_redis_health Gauge (in /health) | ✅ |
| complyo_postgres_health Gauge (in /health) | ✅ |
| complyo_5xx_total Counter (in Middleware) | ✅ |
| Prometheus Service (127.0.0.1:9090) | ✅ |
| Grafana Service (127.0.0.1:3005) | ✅ |
| 01_overview.json | ✅ |
| 02_compliance_engine.json | ✅ |
| 03_infrastructure.json | ✅ |
| prometheus.yml + alerts.yml | ✅ |

---

## Offene Punkte

1. **openapi.snapshot.json** – Stub, muss nach `docker compose build backend` befüllt werden:
   ```bash
   curl http://localhost:8002/openapi.json > data/hardening-2026-05-25/contracts/openapi.snapshot.json
   git add data/hardening-2026-05-25/contracts/openapi.snapshot.json && git commit -m "chore: update openapi snapshot"
   ```

2. **monitoring/prometheus/metrics_token** – Datei muss für Bearer-Auth erstellt werden:
   ```bash
   echo -n "$METRICS_TOKEN" > monitoring/prometheus/metrics_token
   ```

3. **P2-Incident: website_structures.is_active** – Pre-existing, liegt in `data/_incidents/`. Nicht Teil dieses Plans.

4. **user_sessions Migration** – Muss gegen laufende DB ausgeführt werden:
   ```bash
   docker compose exec postgres psql -U postgres -d complyo -f /migrations/add_session_hardening.sql
   ```

5. **test_contracts.py live-Tests** – Werden grün nach `docker compose build backend` + Backend läuft.

---

## Commit-History

```
23a17be merge(p4-monitoring)
9978307 merge(p3-contracts)
f59c66a merge(p2-auth)
649326e feat(p4-monitoring): 6 Prometheus KPIs, Grafana+Prometheus
949d305 feat(p3-contracts): frozen schemas, response_model, X-API-Version
2615535 feat(p2-auth): jti/iat/nbf, Redis blacklist, rotation, logout-all, 12 tests
```
