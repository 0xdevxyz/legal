# Architecture Truth

> Letzte Aktualisierung: 2026-05-24 (nach Cleanup-Phase A–E)

---

## VISION (Nordstern – NICHT jetzt)

> "KI-gestützte Infrastrukturtechnologie zur kontinuierlichen regulatorischen Website-Compliance für KMU"

**AKTUELLE PHASE: STABILITÄT. KEINE neue Feature-Entwicklung bis Smoke-Test grün.**

---

## SEKTION 1 – REALITÄT HEUTE

### Stack
| Schicht | Technologie | Version |
|---------|------------|---------|
| Backend | FastAPI | 0.115.6 |
| DB | PostgreSQL (asyncpg) | asyncpg 0.29.0 |
| Cache/State | Redis | redis 5.0.1 |
| Auth | PyJWT + passlib[bcrypt] | JWT 2.9.0 / passlib 1.7.4 |
| AI | OpenRouter (Claude 3.5 Sonnet) | via aiohttp |
| Frontend Dashboard | Next.js + React + TypeScript | – |
| Frontend Landing | Next.js + React | – |
| Widgets | Vanilla JS | v6 (accessibility), v2 (cookie) |
| Payments | Stripe | stripe 7.8.0 |

### Aktive Services (backend/)
| Service | Datei | Verantwortung |
|---------|-------|---------------|
| AuthService | `auth_service.py` | JWT Issue/Verify, bcrypt |
| DatabaseService | `database_service.py` | Lead/Addon/Module CRUD (asyncpg) |
| EmailService | `email_service.py` | SMTP (Double-Opt-In, Notifications) |
| CookieScanner | `cookie_scanner_service.py` | Playwright-based Cookie-Detection |
| FileStorageService | `file_storage_service.py` | S3/Lokal File Storage |
| NewsService | `news_service.py` | RSS/Legal News Feed |
| RiskCalculator | `risk_calculator.py` | Compliance Score |

### Fix-Engine
**Single-Source**: `backend/ai_fix_engine/unified_fix_engine.py`
- `UnifiedFixEngine.generate_fix(issue, context)` → `FixResult`
- Wird genutzt von: `fix_routes.py` (via global injection), `background_worker.py`, `ai_fix_engine/handlers/accessibility_handler.py`
- `AIComplianceFixer` (`compliance_engine/fixer.py`) – noch aktiv für `/api/v2/ai-fix` Endpoint (Migration ausstehend Phase C+1)

### Registrierte Router (main_production.py) – 30 aktiv
public, lead, admin, gdpr, i18n, legal_news, fix, website, dashboard, auth, payment, stripe, user, legal_text, risk_radar, ai_compliance, addon_payment, widget, expert_service, cookie_compliance, ab_test, tcf, legal_change, ai_legal, legal_notification, accessibility_fix, git, alt_text, deep_cookie_scanner, legal_document

### In-Memory-Status (nach Phase E)
| Bereich | Status |
|---------|--------|
| DB-Fallback (`use_fallback`) | ENTFERNT |
| Admin-Leads Fallback | ENTFERNT |
| OAuth-State | Redis (TTL 600s) |
| Rate-Limit Consent-Logs | Redis (ZADD Sliding Window) |
| ZIP-Download | Filesystem (tempfile) |

### Auth-Flow
1. `POST /auth/login` → `auth_service.verify_credentials()` → JWT (Access 15min, Refresh 7d)
2. Alle geschützten Endpoints: `Depends(get_current_user)` → `dependencies.py` → JWT decode
3. Admin: `verify_admin_access()` in `admin_routes.py`
4. OAuth (GitHub/GitLab): State in Redis TTL 600s, Code-Exchange via `oauth_service.py`

### Datenpfade
```
User → FastAPI → asyncpg Pool → PostgreSQL
User → FastAPI → Redis (OAuth State, Rate-Limit, Auth Cache)
CookieScanner → Playwright → Website → Response
Fix-Engine → OpenRouter API → Claude 3.5 Sonnet → FixResult
Widgets → Static JS served via FastAPI (/api/widgets/*.js)
```

---

## SEKTION 2 – WAS WURDE ENTFERNT

Siehe `/data/_truth/KILL_LIST.md`

---

## SEKTION 3 – NORDSTERN (SPÄTER)

Diese Sektion beschreibt die Zukunft. Sie ist **kein Arbeitsauftrag**.

Die Vision: Ein Compliance-Infrastruktur-Dienst, der:
- Kontinuierlich regulatorische Änderungen überwacht (EU-Recht, DSGVO, BFSG, NIS2)
- Automatisch Fixes für KMU-Websites generiert und deployed
- Über Git-Integration (PR-basiert) oder direkte Deployment-Pipelines
- Mit messbarer Compliance-Score-Entwicklung über Zeit
- Multilinguale Unterstützung (DE, EN, FR, PL, IT)
- EFRE-förderfähige KI-Forschungskomponente (Explainability, Adaptive Remediation)

**Wann**: Erst wenn Smoke-Test grün, DB-Migration stabil, Auth-Flow zuverlässig.

---

## SEKTION 4 – UPDATE-REGEL

Dieses Dokument wird aktualisiert:
1. Nach jeder Cleanup-Phase (A, B, C…)
2. Nach jedem neuen Router-Eintrag in `main_production.py`
3. Nach jeder Änderung am Auth-Flow
4. Nach jeder neuen Service-Datei in `backend/`

**Nicht** nach Features, die noch nicht produktiv sind.
