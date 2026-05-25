# Complyo MCP-Server Integration

**Status:** Implementiert  
**Datum:** 2026-05-08  
**Technologie:** `fastapi-mcp==0.3.4`

---

## Was wurde gebaut

Complyo ist jetzt als **MCP-Server (Model Context Protocol)** erreichbar unter:

- **Produktion:** `https://api.complyo.de/mcp`
- **Lokal:** `http://localhost:8002/mcp`
- **Transport:** SSE (Server-Sent Events)
- **Auth:** Bearer JWT (bestehender Complyo-Token)

KI-Agenten (Claude Desktop, eigene Agents, Cursor) koennen damit alle Complyo-Funktionen direkt aufrufen.

---

## Geaenderte Dateien

| Datei | Aenderung |
|---|---|
| `backend/requirements.txt` | `fastapi-mcp==0.3.4` hinzugefuegt |
| `backend/mcp_server.py` | **Neu** – MCP-Konfigurationsmodul |
| `backend/main_production.py` | MCP-Mount nach Router-Init + Auth-Middleware |
| `backend/csrf_middleware.py` | `/mcp` zu `EXEMPT_PREFIXES` hinzugefuegt |
| `nginx/production.conf` | `/mcp` Location-Block mit SSE-Support |
| `data/mcp-agent-config.json` | **Neu** – Agent-Konfiguration |

---

## Verfuegbare MCP-Tools (Tool-Gruppen)

Alle FastAPI-Routen werden automatisch als MCP-Tools exposiert, ausser:

**Ausgeschlossen (EXCLUDED_TAGS):**
- `admin` – interne Verwaltung
- `stripe` – Webhook-Callbacks
- `leads` – Lead-Verwaltung

**Verfuegbar fuer Agents:**
- `websites` – Scans starten, Websites verwalten
- `fixes` – AI-Fixes generieren & anwenden
- `cookie-compliance` – Cookie-Banner & Consent
- `legal-documents` – DSGVO-Dokumente (DSE, Impressum, DPA)
- `dashboard` – Scores & Reports
- `ai-compliance` – ComplyAI Guard
- `accessibility-alt-text` – BFSG/WCAG Fixes
- `TCF 2.2` – Vendor Consent Framework
- `Legal AI` – Gesetzesaenderungs-Analyse
- `Legal Changes` – Live-Monitoring
- `Legal Notifications` – Benachrichtigungen
- `git-integration` – Automatische PRs

---

## Sicherheit

| Massnahme | Detail |
|---|---|
| JWT Bearer Token | Pflicht auf allen `/mcp`-Requests (Middleware in `main_production.py`) |
| CSRF-Exempt | `/mcp` in `EXEMPT_PREFIXES` (kein Cookie-basierter CSRF noetig bei Bearer-Auth) |
| Admin-Routen | Durch `exclude_tags=["admin"]` blockiert |
| Stripe-Webhooks | Durch `exclude_tags=["stripe"]` blockiert |
| Rate-Limiting | NGINX: `api_limit burst=5` auf `/mcp` |
| SSE-Timeout | NGINX: `proxy_read_timeout 3600s` |
| CORS | Bestehende CORS-Middleware greift |

---

## Claude Desktop einrichten

1. `~/.claude/config.json` (oder Claude Desktop Settings) oeffnen
2. Eintragen:

```json
{
  "mcpServers": {
    "complyo": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://api.complyo.de/mcp",
        "--header",
        "Authorization: Bearer <DEIN_COMPLYO_JWT_TOKEN>"
      ]
    }
  }
}
```

3. Claude Desktop neu starten
4. Im Chat: "Scanne die Website https://example.com auf DSGVO-Konformitaet"

---

## Deployment

```bash
# Im Projekt-Root
docker-compose build backend
docker-compose up -d backend nginx

# Smoke-Test
curl -H "Authorization: Bearer <TOKEN>" https://api.complyo.de/mcp
```

---

## Smoke-Test Befehle

```bash
# 1. MCP-Endpunkt erreichbar?
curl -I -H "Authorization: Bearer <TOKEN>" https://api.complyo.de/mcp

# 2. Ohne Token -> sollte 401 zurueckgeben
curl -I https://api.complyo.de/mcp

# 3. Tool-Liste per MCP-Protokoll
curl -X POST https://api.complyo.de/mcp \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

Erwartetes Ergebnis von `tools/list`: ~25-30 Tools aus allen nicht-ausgeschlossenen Routen.
