# DB-Schema Baseline — 2026-05-15

## scan_history
| Spalte | Typ | Default |
|--------|-----|---------|
| id | uuid | gen_random_uuid() |
| scan_id | varchar(255) | |
| url | varchar(500) | |
| user_id | **INTEGER** | |
| compliance_score | double precision | |
| total_risk_euro | numeric(10,2) | 0 |
| critical_issues | integer | 0 |
| warning_issues | integer | 0 |
| total_issues | integer | 0 |
| scan_data | jsonb | |
| scan_duration_ms | integer | 0 |
| scan_timestamp | timestamp | now() |

**Problem:** `user_id` ist INTEGER. JWT-Claim `id` ist String. `int(current_user["id"])` wirft ValueError wenn String leer oder non-numeric.

## cookie_banner_configs
Alle Spalten vorhanden inkl. `scan_completed_at`, `last_scan_url`, `custom_logo_url`.
**Kein Schema-Drift** — das 500 kommt von der `require_module`-Prüfung oder `get_user_id_from_token`.

## users
| Spalte | Typ |
|--------|-----|
| id | **INTEGER** (nextval) |
| email | varchar(255) UNIQUE |

JWT erzeugt `id = str(user_id)` → `"123"` → DB-Query `WHERE id::text = '123'` ✅ OK.
**Echte Ursache des 500**: `get_current_user_required` → `db_service` nicht gesetzt wenn Endpoint frisch aufgerufen wird.
