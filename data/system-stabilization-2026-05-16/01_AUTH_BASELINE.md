# Phase 0 – Auth-Varianten-Audit (Baseline)

**Datum:** 2026-05-16

## Identifizierte Root Causes (aus Logs + Code-Analyse)

### Problem 1: Token-Claims sind Strings, DB erwartet Integer

`auth_service.create_access_token()` schreibt:
```python
"id": str(user_id),        # → "5" (String!)
"user_id": str(user_id),   # → "5" (String!)
```

Routes, die `user.get("user_id")` direkt ans DB-Query übergeben, crashen:
```
TypeError: 'str' object cannot be interpreted as an integer
```
→ Betrifft: `dashboard_routes.py` (Z. 82), diverse andere Stellen in `main_production.py`

### Problem 2: 8 separate get_current_user-Implementierungen

| Datei | Methode | Decodet aud/iss? | DB-Lookup? | user_id-Typ in Return |
|-------|---------|------------------|------------|----------------------|
| `dependencies.py` | jwt.decode direkt | ✅ Ja | ❌ Nein (gibt Payload zurück) | str (aus Token) |
| `auth_routes.py` | auth_service.verify_token → get_user_by_id | ✅ Ja | ✅ Ja | int (aus DB) |
| `website_routes.py` | auth_service.verify_token | ✅ Ja | ✅ Ja (eigener Helper) | uuid (aus DB!) |
| `dashboard_routes.py` | auth_service.verify_token | ✅ Ja | ❌ Nein | str (aus Token) |
| `fix_routes.py` | (eigene) | ? | ? | int (forciert) |
| `fix_apply_routes.py` | (eigene) | ? | ? | ? |
| `git_routes.py` | (eigene) | ? | ? | ? |
| `stripe_routes.py` | (eigene) | ? | ? | ? |
| `main_production.py` | from dependencies import get_current_user | ✅ Ja | ❌ Nein | str (Payload) |

**Kern-Inkonsistenz:**
- `auth_routes.get_current_user` → gibt vollständiges User-Dict mit `id: int` zurück
- `dependencies.get_current_user` → gibt rohen JWT-Payload mit `id: str` zurück
- `main_production.py` importiert aus `dependencies` → `current_user["id"]` ist String → INT-Konvertierung nötig

### Problem 3: score_history-Tabelle fehlt in DB

```
Did not find any relation named "score_history"
```
→ Migration `init_score_history.sql` wurde nicht ausgeführt.
→ `analyze_website_v2` crasht mit `operator does not exist: uuid = integer` beim INSERT in `score_history`.

Tatsächliche Fehlerstelle (nach Scan-Erfolg):
```
tracked_site = await connection.fetchrow(
    "SELECT id FROM tracked_websites WHERE user_id = $1 AND url = $2",
    user_id_int, scan_result["url"]
)
if tracked_site:
    await connection.execute(
        "INSERT INTO score_history ..."  # ← Tabelle existiert nicht!
    )
```

### Problem 4: /api/legal-ai/updates → 401

Log-Beweis:
```
WARNING:auth_service:Invalid token: Not enough segments
```
→ Der Frontend-`LegalNews`-Component schickt einen kaputten/leeren Token-String.
→ Betrifft: `dashboard-react/src/components/dashboard/LegalNews.tsx:236`

## Geplante Fixes

1. **`dependencies.py`** → `get_current_user` macht DB-Lookup + gibt `id` als `int` zurück (=single source of truth)
2. **Alle lokalen `get_current_user` ersetzen** durch Import aus `dependencies`
3. **`score_history`-Tabelle anlegen** (Migration ausführen oder inline erstellen)
4. **`LegalNews.tsx`** → Token-Handling prüfen + fixen
