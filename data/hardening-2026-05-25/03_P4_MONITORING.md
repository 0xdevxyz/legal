# P4 – Monitoring Dashboard

**Branch**: hardening/p4-monitoring
**Tag end**: hardening-p4-done

## Änderungen

### backend/main_production.py
- Import `Gauge as _PGauge` aus `prometheus_client`
- 6 neue Metriken:
  - `complyo_scans_total` (Counter, label: status)
  - `complyo_fixes_total` (Counter, label: status)
  - `complyo_openrouter_total` (Counter, label: status)
  - `complyo_redis_health` (Gauge)
  - `complyo_postgres_health` (Gauge)
  - `complyo_5xx_total` (Counter, label: endpoint)
- `prometheus_middleware`: 5xx → `_5xx_errors_total.inc()`
- `/health` Endpoint: setzt Redis/Postgres Gauge bei jedem Aufruf

### backend/metrics.py (neu)
- Shared-Module für importierbare Metriken aus Routen (v2-Suffix um Collision mit main_production zu vermeiden)

### backend/ai_fix_engine/unified_fix_engine.py
- OpenRouter-Call success/error → `openrouter_requests_total` Counter

### docker-compose.yml
- Service `prometheus` (127.0.0.1:9090, prom/prometheus:latest)
- Service `grafana` (127.0.0.1:3005, grafana/grafana:latest)
- Volume `grafana_data`

### monitoring/prometheus/prometheus.yml
- scrape_config: `backend:8002/metrics` mit Bearer-Token

### monitoring/prometheus/alerts.yml
- Alert `ScanSuccessRateBelow90` (5min, severity: warning)
- Alert `OpenRouterErrorsHigh` (>10%, severity: critical)
- Alert `DatabaseDown` (severity: critical)
- Alert `RedisDown` (severity: critical)

### monitoring/grafana/provisioning/
- `datasources/prometheus.yml`: Prometheus als Default-Datasource
- `dashboards/dashboards.yml`: Dashboard-Provider

### monitoring/grafana/dashboards/
- `01_overview.json`: Total Requests, 5xx Error Rate, P95 Latency, Load
- `02_compliance_engine.json`: Scan Success Rate, Fix Rate, OpenRouter Failure Rate
- `03_infrastructure.json`: Redis/Postgres Health, 5xx Heatmap

### .env.example
- `GF_SECURITY_ADMIN_USER`
- `GF_SECURITY_ADMIN_PASSWORD`

## Akzeptanzkriterien
- `docker compose up prometheus grafana` → Grafana unter http://127.0.0.1:3005
- Alle 6 KPIs nach `docker compose build backend` + 1 Minute sichtbar
- `prometheus.yml` + `alerts.yml` committed
