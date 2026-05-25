# 2026-05-24_fix-generate-website-structures-schema

**Datum**: 2026-05-24
**Severity**: P2
**Status**: open
**Trigger**: Smoke-Test Schritt 5 – `POST /api/v2/fixes/generate` schlägt fehl
**Betroffene Komponenten**: `fix_routes.py`, `fix_generator.py` (alt, im Container), `website_structures` Tabelle
**Root Cause**: Die Tabelle `website_structures` existiert nicht (oder fehlt Spalte `is_active`) in der produktiven Datenbank. Das `fix_generator.py`-Query referenziert `website_structures.is_active`, die Tabelle wurde aber nie migriert oder der Fix-Endpoint wurde auf einem DB-Stand deployed, bei dem die Migration noch fehlt.
**Fix-Commit**: pending – nach Container-Rebuild und DB-Migration-Prüfung
**Lessons Learned**: Jeder neue Endpoint muss vor Deployment gegen die Produktions-DB-Schema verifiziert werden. Migration-Script muss vor `docker compose up` laufen.
**Pattern-Tag**: `regression`, `db-schema`

## Reproduktion
```bash
TOKEN=<valid-jwt>
curl -X POST http://localhost:8002/api/v2/fixes/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"issue_id":"test-1","issue_category":"impressum"}'
# → 500 Internal Server Error
# Backend-Log: column "is_active" of relation "website_structures" does not exist
```

## Nächste Schritte
1. Prüfen: `SELECT * FROM information_schema.tables WHERE table_name = 'website_structures';`
2. Falls nicht vorhanden: Migration `init_website_structures.sql` identifizieren und einspielen
3. Container mit neuem Image rebuilden (cleanup-Branches gemergt)
4. Smoke-Test Schritt 5 wiederholen
