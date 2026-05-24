# Phase D – Route Audit & TODO-Auth

**Branch**: `cleanup/phase-d-routes`
**Datum**: 2026-05-24
**Status**: completed (audit + documentation; no deletions – see decisions below)

## Route-Inventar

### Registrierte Routes (main_production.py)
| # | Router | Route-Datei | Auth | Status |
|---|--------|------------|------|--------|
| 1 | `public_router` | `public_routes.py` | public (intentional) | ok |
| 2 | `lead_router` | `lead_routes.py` | – | ok |
| 3 | `admin_router` | `admin_routes.py` | admin-only | ok |
| 4 | `gdpr_router` | `gdpr_api.py` | – | ok |
| 5 | `i18n_router` | `i18n_api.py` | – | ok |
| 6 | `legal_news_router` | `legal_news_routes.py` | – | ok |
| 7 | `fix_router` | `fix_routes.py` | get_current_user | ok |
| 8 | `website_router` | `website_routes.py` | – | ok |
| 9 | `dashboard_router` | `dashboard_routes.py` | – | ok |
| 10 | `auth_routes.router` | `auth_routes.py` | auth endpoints | ok |
| 11 | `payment_routes.router` | `payment_routes.py` | – | ok |
| 12 | `stripe_routes.router` | `stripe_routes.py` | – | ok |
| 13 | `user_routes.router` | `user_routes.py` | – | ok |
| 14 | `legal_text_router` | `legal_text_routes.py` | – | ok |
| 15 | `risk_radar_router` | `risk_radar_routes.py` | – | ok |
| 16 | `ai_compliance_router` | `ai_compliance_routes.py` | – | ok |
| 17 | `addon_payment_router` | `addon_payment_routes.py` | – | ok |
| 18 | `widget_router` | `widget_routes.py` | public widget endpoints | ok |
| 19 | `expert_service_router` | `expert_service_routes.py` | – | ok |
| 20 | `cookie_compliance_router` | `cookie_compliance_routes.py` | – | ok |
| 21 | `ab_test_router` | `ab_test_routes.py` | – | ok |
| 22 | `tcf_router` | `tcf_routes.py` | – | ok |
| 23 | `legal_change_router` | `legal_change_routes.py` | – | ok |
| 24 | `ai_legal_router` | `ai_legal_routes.py` | – | ok |
| 25 | `legal_notification_router` | `legal_notification_routes.py` | – | ok |
| 26 | `accessibility_fix_router` | `accessibility_fix_routes.py` | – | ok |
| 27 | `git_router` | `git_routes.py` | – | ok |
| 28 | `alt_text_router` | `alt_text_routes.py` | – | ok |
| 29 | `deep_cookie_scanner_router` | `deep_cookie_scanner_routes.py` | – | ok |
| 30 | `legal_document_router` | `legal_document_routes.py` | – | ok |

### Nicht-registrierte Route-Dateien
| Datei | Router | Grund nicht registriert | Entscheidung |
|-------|--------|------------------------|--------------|
| `fix_apply_routes.py` | `apply_router` | Relative Import-Fehler (`.compliance_engine`) – nie lauffähig | LÖSCHEN in Phase C+1 oder reparieren |
| `knowledge_routes.py` | `router` | Knowledge-Feature neu, noch nicht aktiviert | AKTIVIEREN oder LÖSCHEN nach Entscheidung |

## TODO-Auth-Analyse
Alle gescannten TODOs in Route-Dateien sind **feature-level TODOs** (unfertige Features), keine ungesichwerten Auth-Bypass-TODOs:

| Datei | Zeile | TODO | Typ |
|-------|-------|------|-----|
| `fix_apply_routes.py` | 186 | `# TODO: Aus deployment_result extrahieren` | Feature-TODO |
| `fix_apply_routes.py` | 328 | `# TODO: Implementierung des Staging-Preview-Features` | Feature-TODO |
| `fix_apply_routes.py` | 361 | `# TODO: Implementierung von Background-Task-Tracking` | Feature-TODO |
| `legal_change_routes.py` | 201-202 | `# TODO: aus aktueller Config holen` | Feature-TODO |
| `legal_change_routes.py` | 547 | `# TODO: Implementiere automatische Fix-Anwendung` | Feature-TODO |

**Befund**: Kein aktiver Route-Endpoint ohne Auth der eigentlich auth-geschützt sein sollte.

## Entscheidungen
1. `fix_apply_routes.py` – Enthält relativen Import-Fehler (`.compliance_engine`), war nie funktionsfähig → Phase D+1: reparieren oder löschen
2. `knowledge_routes.py` – Feature in Entwicklung, nicht aktiviert → Phase D+1: entscheiden ob aktivieren
3. Keine kritischen Auth-Lücken gefunden in aktiven Routes

## Commit + Tag
- Commit: `chore(cleanup-d): route audit complete - document orphaned routes`
- Tag: `cleanup-phase-d-done`
