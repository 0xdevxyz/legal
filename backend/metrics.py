"""
Shared Prometheus metrics for Complyo backend.
Import from here in routes to avoid circular imports with main_production.
"""
from prometheus_client import Counter as _C, Gauge as _G

scan_requests_total = _C("complyo_scans_total_v2", "Scan requests", ["status"])
fix_requests_total = _C("complyo_fixes_total_v2", "Fix generation requests", ["status"])
openrouter_requests_total = _C("complyo_openrouter_total_v2", "OpenRouter API calls", ["status"])
redis_health_gauge = _G("complyo_redis_health_v2", "Redis health (1=up, 0=down)")
postgres_health_gauge = _G("complyo_postgres_health_v2", "Postgres health (1=up, 0=down)")
errors_5xx_total = _C("complyo_5xx_total_v2", "5xx errors", ["endpoint"])
