# Phase 2 – Scan-500 Root Cause

**Datum:** 2026-05-16

## Beobachteter Fehler

```
Analysis v2 error: operator does not exist: uuid = integer
HINT:  No operator matches the given name and argument types.
INFO: POST /api/v2/analyze HTTP/1.0" 500 Internal Server Error
```

## Root Cause

`score_history`-Tabelle existierte nicht in der Datenbank.

`analyze_website_v2` (Z. 1145–1154 `main_production.py`):
```python
await connection.execute(
    "INSERT INTO score_history (website_id, user_id, overall_score, pillar_scores, scan_date)
     VALUES ($1, $2, $3, $4, NOW())",
    tracked_site["id"],   # UUID aus tracked_websites
    ...
)
```

→ `score_history` fehlte → PostgreSQL gab "relation does not exist" → 500

Zusätzlich: `tracked_websites.id` ist UUID, aber `score_history.website_id` war in der alten Migration als INTEGER definiert → zweiter Typ-Mismatch sobald die Tabelle existiert hätte.

## Fix

### 1. Tabelle direkt anlegen mit korrekten Typen

```sql
CREATE TABLE IF NOT EXISTS score_history (
    id SERIAL PRIMARY KEY,
    website_id UUID,
    user_id INTEGER,
    overall_score DOUBLE PRECISION,
    pillar_scores JSONB,
    scan_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Logging-Härtung in `main_production.py:1167`

Vorher:
```python
print(f"Analysis v2 error: {e}")
```

Nachher:
```python
logger.exception(f"Analysis v2 error for url={request.url}, user_id=...")
```

→ Stacktrace erscheint jetzt immer im Log.

## Verifikation

```bash
docker exec complyo-postgres psql -U complyo_user -d complyo_db -c "\d score_history"
# → Tabelle existiert mit website_id UUID, user_id INTEGER
```
