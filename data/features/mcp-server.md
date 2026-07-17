# MCP-Server (KI-Agenten-Zugang)

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Die gesamte Complyo-FastAPI-App als MCP-Server für KI-Agenten exponieren, damit Agenten
Scans starten, Fixes generieren, Banner konfigurieren und Legal-Dokumente erzeugen können,
ohne die REST-API einzeln zu integrieren. Technisch ein Auto-Wrapper über das OpenAPI-Schema
(`fastapi-mcp`), keine handgeschriebenen Tools.

## Architektur (end-to-end)
- **Setup:** `backend/mcp_server.py` (49 Z.)
  - `setup_mcp(app)` → `FastApiMCP(app, name="Complyo MCP", describe_all_responses=True,
    describe_full_response_schema=True, exclude_tags=EXCLUDED_TAGS)` + `mcp.mount()`.
  - `EXCLUDED_TAGS = ["admin", "stripe", "leads"]` — der einzige Filter. **Alles andere wird
    zum Tool**, es gibt keine kuratierte Tool-Liste.
- **Mount:** `backend/main_production.py:755-758` → `/mcp` (SSE-Transport), Nachrichten-Endpunkt
  `/mcp/messages/?session_id=…`.
- **Auth-Gate:** `backend/main_production.py:281-292`, Middleware `mcp_auth_middleware`
  - prüft für `request.url.path.startswith("/mcp")` **nur die Existenz** von
    `Authorization: Bearer …` — **kein JWT-Decode, keine Signatur-, Ablauf- oder User-Prüfung**.
  - Die eigentliche Autorisierung passiert erst im gewrappten Endpoint (`Depends`-Kette).
- **Verifiziert live gegen `https://api.complyo.de/mcp`:**
  - ohne Header → `401`; mit `Authorization: Bearer fake` → `200` + offener SSE-Stream.
  - `initialize` + `tools/list` mit `Bearer fake` → **296 Tools** vollständig ausgeliefert
    (inkl. Namen, Beschreibungen, Input-/Output-Schemata der kompletten API).
  - `tools/call get_current_user_info_api_auth_me_get` → `401 Authentication failed`
    (Endpoint-Auth greift, Status wird durchgereicht).
  - `tools/call get_dashboard_stats_api_v2_dashboard_stats_get` → `200` mit Daten,
    weil dieser Endpoint selbst keine Auth hat.

## Bekannte Lücken / Offen
- **Auth-Middleware ist rein syntaktisch (hoch).** Jeder beliebige String nach `Bearer `
  öffnet die Session. Der Schutz der Tools ist damit exakt der Schutz der darunterliegenden
  Endpunkte — die Middleware fügt **null** Sicherheit hinzu, suggeriert sie aber
  (`MCP_SERVER_DESCRIPTION`: „Bearer-Token (JWT) erforderlich"). Fix: JWT im Middleware
  validieren (bestehender `auth_service`), sonst 401.
- **Ungeschützte Endpunkte sind über `/mcp` ohne gültiges Token nutzbar (hoch).**
  Belegt an `/api/v2/dashboard/stats`; ebenso betroffen: `/api/risk-radar/*`
  (siehe [[risiko-radar]], keine Auth, `user_id` als freier Query-Param). Die MCP-Fläche
  macht diese Lücken maschinenlesbar auffindbar.
- **Tool-Fläche unkuratiert (hoch).** 296 Tools aus 302 OpenAPI-Pfaden. Darunter Routen mit
  Nebenwirkungen und Kosten (Scan-Start, AI-Fix-Generierung, LLM-Aufrufe). Diese sind
  zwar auth-pflichtig, aber ein einmal legitim authentifizierter Agent hat damit
  ungebremsten Zugriff auf alle kostenverursachenden Routen. Es gibt **kein
  MCP-spezifisches Rate-Limit und keine Plan-/Kontingent-Prüfung auf MCP-Ebene**.
  Empfehlung: Allowlist statt Tag-Denylist.
- **`describe_full_response_schema=True`** bläht jede Tool-Beschreibung mit dem vollen
  Response-Schema auf → sehr großer `tools/list`-Payload für Clients.
- **Nicht beworben, keine bekannte Nutzung.** Kein Frontend-Bezug, keine Doku für Kunden,
  kein Eintrag in Landing/Dashboard. Faktisch ein unbeaufsichtigt exponierter Endpunkt.
- Ob `fastapi-mcp` das Client-Token korrekt an *alle* Endpoint-Typen weiterreicht, ist nur
  für die zwei getesteten Tools belegt — für die restlichen 294 **unklar / zu prüfen**.
