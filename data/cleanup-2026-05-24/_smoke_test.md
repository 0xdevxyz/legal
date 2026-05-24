# Smoke Test – Reproduzierbarer Ablauf pro Phase

Nach jeder Phase diesen Test durchführen. Alle Schritte müssen grün sein bevor der Phase-Branch gemergt wird.

## Voraussetzungen
- Backend läuft: `uvicorn backend.main_production:app --reload`
- DB erreichbar (Postgres)
- Redis erreichbar
- `.env` konfiguriert

## Test-Ablauf

### 1. Health Check
```bash
curl -s http://localhost:8000/health | jq .
```
Erwartung: `{"status": "healthy", "database": "postgresql", "redis": "connected"}`
FAIL wenn: `"database": "in-memory"` oder `"redis": "unavailable"`

### 2. Login (Auth)
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass"}' | jq .access_token
```
Erwartung: JWT-Token zurück (nicht null, nicht leer)

### 3. Website-Scan
```bash
TOKEN="<aus Schritt 2>"
curl -s -X POST http://localhost:8000/websites/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' | jq .scan_id
```
Erwartung: `scan_id` vorhanden

### 4. Dashboard-Metrics
```bash
curl -s http://localhost:8000/dashboard/metrics \
  -H "Authorization: Bearer $TOKEN" | jq .total_websites
```
Erwartung: Zahl >= 0, kein 500

### 5. Fix-Apply (Compliance Engine)
```bash
curl -s -X POST http://localhost:8000/fix/apply \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"website_id": 1, "fix_type": "cookie_banner"}' | jq .status
```
Erwartung: `"success"` oder `"pending"` (nicht `"error"`)

### 6. Cookie-Banner Widget
```bash
curl -s http://localhost:8000/widgets/cookie-consent.js | head -5
```
Erwartung: JavaScript-Content, kein 404

### 7. Accessibility Widget (v6)
```bash
curl -s http://localhost:8000/widgets/accessibility-v6.js | head -5
```
Erwartung: JavaScript-Content, kein 404

## Fehler-Protokoll
| Datum | Phase | Schritt | Fehler | Fix |
|-------|-------|---------|--------|-----|
| – | – | – | – | – |
