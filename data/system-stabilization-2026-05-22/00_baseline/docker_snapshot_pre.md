# Docker Container Snapshot - Pre-Rebuild
Datum: 2026-05-22

## Complyo Container

| Container | Status | Port | Mem |
|-----------|--------|------|-----|
| complyo-backend | Up 5 days (healthy) | 127.0.0.1:8002->8002 | 193.5MiB / 1GiB |
| complyo-dashboard | Up 6 days (unhealthy) | 127.0.0.1:3001->3000 | 43.6MiB / 512MiB |
| complyo-landing | Up 6 days (unhealthy) | 127.0.0.1:3003->3000 | 43.98MiB / 512MiB |
| complyo-admin | Up 13 days | 127.0.0.1:3004->80 | 1.266MiB / 7.688GiB |
| complyo-postgres | Up 2 weeks (healthy) | 127.0.0.1:5433->5432 | 13.73MiB / 512MiB |
| complyo-redis | Up 2 weeks (healthy) | 127.0.0.1:6380->6379 | 1.777MiB / 256MiB |

## DB: complyo_db - Tabellen (41 total)
ai_classification_feedback, ai_classifications, ai_learning_cycles, ai_solution_cache,
alt_text_review_queue, compliance_fixes, compliance_risk_matrix, cookie_banner_configs,
cookie_banner_revisions, cookie_compliance_stats, cookie_consent_logs, cookie_services,
deep_cookie_scans, deep_scan_history, deep_scan_usage, export_history, fix_jobs,
generated_documents, generated_fixes, legal_change_impacts, legal_change_notifications,
legal_changes, legal_monitoring_logs, legal_news, legal_updates, legal_updates_archive,
modules, oauth_providers, oauth_states, rss_feed_sources, scan_history, score_history,
stripe_customers, subscription_plans, subscriptions, tracked_websites, user_limits,
user_modules, user_sessions, users, waitlist_leads

## users-Tabelle Schema
Spalten: id, email, password_hash, full_name, company, is_active, is_verified,
         created_at, updated_at, onboarding_completed, plan_type
Kein role-Feld → P1-Migration erforderlich: add_user_roles.sql

## Code Inventory
- Backend Python-Dateien: 192
- Frontend TS/TSX-Dateien: 172
- Gesamt relevante Dateien: 385

## Key Backend Dependencies (Container)
- fastapi: 0.115.6
- asyncpg: 0.29.0
- pydantic: 2.13.4
- sentry-sdk: 2.59.0
- stripe: 7.8.0
- uvicorn: 0.24.0

## Key Frontend Dependencies
- next: 14.2.32 (→ target: 15.x)
- react: 18.3.1 (→ target: 19.x)
- tailwindcss: 3.4.17 (→ target: 4.x)
- @tanstack/react-query: 5.84.2
- zustand: 4.5.7
- @chakra-ui/react: 2.10.9 (→ ersetzen durch shadcn/ui v2)
- next-auth: NOT INSTALLED (→ P2 installieren)

## Git Branch
- Rebuilt auf: rebuild-2026-05-22
- Basis-Commit: e833210
