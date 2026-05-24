# Baseline – 2026-05-24

Erstellt vor Phase A. Alle Zahlen sind der Ist-Zustand am Cleanup-Startdatum.

## LOC & Datei-Zählung
| Kategorie | Anzahl |
|-----------|--------|
| Gesamt Code-Dateien (`.py`, `.js`, `.ts`, `.tsx`) | 2197 |
| Backend `.py` Dateien (root) | 85 |
| Backend gesamt LOC | 42310 |

## Git-Stand
- HEAD: `79a1c2b feat(p10-03): wire ClientGroup + AgencyLogoUpload into agency dashboard page`
- Branch: main (pre-cleanup, kein eigener Branch angelegt)

## requirements.txt Snapshot (backend)
```
aiofiles==23.2.1
aiohttp==3.9.5
asyncpg==0.29.0
beautifulsoup4==4.12.2
lxml>=5.1.0
feedparser==6.0.10
fastapi==0.115.6
httpx==0.27.2
Jinja2==3.1.2
numpy==1.26.2
pandas==2.1.4
passlib[bcrypt]==1.7.4
prometheus-client>=0.20.0
sentry-sdk[fastapi]>=2.0.0
psutil==5.9.6
pydantic>=2.5.0
pydantic-settings>=2.5.2
PyJWT==2.9.0
python-dotenv==1.0.0
python-multipart>=0.0.9
redis==5.0.1
reportlab==4.0.7
requests==2.32.3
scikit-learn==1.3.2
sqlalchemy==2.0.23
alembic==1.13.1
stripe==7.8.0
uvicorn[standard]==0.24.0
fastapi-mcp==0.3.4
email-validator==2.1.0
firebase-admin==6.3.0
slowapi==0.1.9
jsonschema==4.20.0
playwright==1.40.0
certifi>=2024.2.2
paramiko>=3.4.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

## Registrierte Router (main_production.py)
| # | Router-Variable | Kommentar |
|---|----------------|-----------|
| 1 | `public_router` | |
| 2 | `lead_router` | |
| 3 | `admin_router` | |
| 4 | `gdpr_router` | |
| 5 | `i18n_router` | |
| 6 | `legal_news_router` | |
| 7 | `fix_router` | |
| 8 | `website_router` | Website management router |
| 9 | `dashboard_router` | Dashboard metrics router |
| 10 | `auth_routes.router` | Auth router enabled |
| 11 | `payment_routes.router` | Payment router enabled |
| 12 | `stripe_routes.router` | NEW: Freemium Stripe routes |
| 13 | `user_routes.router` | User profile & domain locks |
| 14 | `legal_text_router` | Interner Rechtstexte-Generator (ersetzt eRecht24) |
| 15 | `risk_radar_router` | Risiko-Radar + Frühwarner |
| 16 | `ai_compliance_router` | AI Compliance (ComploAI Guard) |
| 17 | `addon_payment_router` | Add-on Payments (ComploAI Guard & Priority Support) |
| 18 | `widget_router` | Complyo Widgets (Cookie Consent & Accessibility) |
| 19 | `expert_service_router` | Expert Service Booking |
| 20 | `cookie_compliance_router` | Cookie Compliance Management |
| 21 | `ab_test_router` | A/B Testing for Cookie Banner |
| 22 | `tcf_router` | TCF 2.2 Transparency & Consent Framework |
| 23 | `legal_change_router` | Legal Change Monitoring (auto-detect law changes) |
| 24 | `ai_legal_router` | AI Legal System - NEW |
| 25 | `legal_notification_router` | Legal News Notifications - NEW |
| 26 | `accessibility_fix_router` | BFSG Accessibility Fix Pipeline - NEW |
| 27 | `git_router` | Git Integration - Automatic PRs - NEW |
| 28 | `alt_text_router` | Alt-Text AI Generation - NEW |
| 29 | `deep_cookie_scanner_router` | Deep Cookie Scanner - Premium Feature |
| 30 | `legal_document_router` | AUDIT-19: DPA Generator |

## Route-Dateien (backend/*.py)
```
backend/ab_test_routes.py
backend/accessibility_fix_routes.py
backend/addon_payment_routes.py
backend/admin_routes.py
backend/ai_compliance_routes.py
backend/ai_legal_routes.py
backend/alt_text_routes.py
backend/auth_routes.py
backend/cookie_compliance_routes.py
backend/dashboard_routes.py
backend/deep_cookie_scanner_routes.py
backend/enhanced_fix_routes.py        ← NICHT in main_production.py registriert!
backend/expert_service_routes.py
backend/fix_apply_routes.py
backend/fix_routes.py
backend/git_routes.py
backend/knowledge_routes.py           ← NICHT in main_production.py registriert!
backend/lead_routes.py
backend/legal_change_routes.py
backend/legal_document_routes.py
backend/legal_news_routes.py
backend/legal_notification_routes.py
backend/legal_text_routes.py
backend/payment_routes.py
backend/public_routes.py
backend/risk_radar_routes.py
backend/stripe_routes.py
backend/tcf_routes.py
backend/user_routes.py
backend/website_routes.py
backend/widget_routes.py
```
**Nicht-registrierte Routes**: `enhanced_fix_routes.py`, `knowledge_routes.py` – Phase D prüfen.

## Legacy / Backup / Dead Files (Ist-Zustand)
### Widgets (zu löschen in Phase A)
```
backend/widgets/accessibility.js
backend/widgets/accessibility_smart.js
backend/widgets/accessibility-v5.js
backend/widgets/cookie_consent.legacy.js
backend/widgets/cookie_consent.legacy.js.bak
```
**Behalten**: `accessibility-v6.js`, `content_blocker.js`, `cookie_banner_v2.js`, `locales/translations.js`, `optout_center.js`

### eRecht24-Reste (zu löschen in Phase A)
```
backend/init_erecht24_projects.sql
backend/migration_erecht24_fixed.sql
backend/migration_erecht24_full.sql
backend/migrations/migration_deprecate_erecht24.sql
backend/migrations/migration_deprecate_erecht24_rollback.sql
backend/scripts/export_erecht24_data.py
```

### .disabled (zu löschen in Phase A)
```
backend/sql/init_alt_text_fixes.sql.disabled
```

### Fix-Engine-Duplikate (zu konsolidieren in Phase C)
```
backend/compliance_engine/fixer.py          → löschen
backend/compliance_engine/enhanced_fixer.py → löschen
backend/fix_generator.py                    → löschen
backend/ai_fix_engine/unified_fix_engine.py → BEHALTEN (Single-Source)
```

## In-Memory-Probleme (zu migrieren in Phase E)
| Datei | Zeile | Problem | Ziel |
|-------|-------|---------|------|
| `database_service.py` | `use_fallback` | Stiller In-Memory-Fallback bei DB-Down | Fail fast + 503 |
| `git_routes.py` | 34 | OAuth-State In-Memory | Redis TTL 10min |
| `cookie_compliance_routes.py` | 2499 | Rate-Limit Sliding Window In-Memory | Redis ZADD |
| `widget_routes.py` | 621-624 | ZIP in Memory | Streaming / file_storage_service.py |
| `admin_routes.py` | 387 | `"type": "in-memory" if db_service.use_fallback` | entfernen |
