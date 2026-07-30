"""
Complyo MCP Server — kuratierte Tool-Allowlist.

Bis 30.07.2026 war der MCP-Server ein Auto-Wrapper über die gesamte API:
296 Tools aus 302 OpenAPI-Pfaden, gefiltert nur über eine Tag-Denylist
(admin/stripe/leads). Jede neue Route wurde automatisch zum Agenten-Tool —
inklusive kostenverursachender und seiteneffektbehafteter Endpunkte.

Jetzt gilt eine **Allowlist** (include_operations). Ein Agent kann:
- Scans starten und Ergebnisse lesen
- KI-Fixes anstoßen und deren Status/Ergebnis lesen (das Auslieferungs-
  Gating der Review-Kette greift dort serverseitig)
- die A11y-Worklist und das Fix-Manifest lesen
- den GitHub-Kanal bedienen: Status, Repos, **PR erstellen** (der Kunde
  merged), PR-Liste, **PR-Revert** — das ist der strategische Weg
  "GitHub + Rollback" (Betreiber-Vorgabe 29.07.2026)

Bewusst NICHT als Tool verfügbar:
- Direct-Deploy (/api/v2/fixes/apply) und dessen Rollback — Serverschreiben
  bleibt ein menschlicher Klick im Dashboard, die KI löst es nie aus
- Admin-Freigaben (approve/reject) — Review bleibt menschlich
- OAuth-Verbindung, Billing, Konto- und Lead-Verwaltung

Zusätzlich: MCP-eigenes Rate-Limit (Redis, pro Nutzer) in der Auth-Middleware
(main_production.mcp_auth_middleware) — ein legitim authentifizierter Agent
soll die kostenverursachenden Routen nicht ungebremst treiben können.
"""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

# Kuratierte Tools: FastAPI-operationIds (Methode + Pfad im Namen kodiert).
# Der Wächter-Test tests/test_mcp_allowlist.py hält diese Liste ehrlich.
MCP_ALLOWED_OPERATIONS = [
    # Scan
    "analyze_website_v2_api_v2_analyze_post",
    "quick_analyze_website_api_v2_analyze_quick_post",
    # KI-Fixes (Job-Pipeline; Gating der Review-Kette greift im Endpunkt)
    "create_fix_job_api_fix_jobs_post",
    "get_fix_job_status_api_fix_jobs__job_id__status_get",
    "get_active_fix_jobs_api_fix_jobs_active_get",
    # Barrierefreiheit: lesen
    "accessibility_worklist_api_accessibility_worklist_get",
    "get_fix_manifest_api_accessibility_fix_manifest__site_id__get",
    # GitHub-Kanal: der strategische Weg (PR statt Direktschreiben, Revert als Rollback)
    "git_connection_status_api_v2_git_status_get",
    "list_connected_repos_api_v2_git_repos_get",
    "apply_patches_api_v2_git_apply_patches_post",
    "list_pull_requests_api_v2_git_prs_get",
    "revert_pull_request_api_v2_git_prs__pr_id__revert_post",
]

MCP_SERVER_DESCRIPTION = """
Complyo Compliance Platform MCP-Server (kuratiert).

Verfügbare Fähigkeiten:
- Website-Scans starten und Ergebnisse abrufen (DSGVO, WCAG, BFSG, Cookie)
- KI-Fixes generieren und deren Status abrufen (freigegebene Inhalte)
- Barrierefreiheits-Worklist und Fix-Manifest lesen
- GitHub-Integration: Fixes als Pull Request vorschlagen, PR-Status,
  PR-Revert als Rollback — gemerged wird immer vom Kunden

Nicht über MCP möglich (bewusst): Direktschreiben auf Kundenserver,
Review-Freigaben, Kontoverwaltung, Zahlungen.

Authentifizierung: Bearer-Token (JWT) erforderlich.
Alle Requests müssen den Header 'Authorization: Bearer <token>' enthalten.
"""


def setup_mcp(app: FastAPI) -> FastApiMCP:
    """Initialisiert und mounted den MCP-Server auf die FastAPI-App."""
    mcp = FastApiMCP(
        app,
        name="Complyo MCP",
        description=MCP_SERVER_DESCRIPTION,
        # Kompakte Tool-Beschreibungen: das volle Response-Schema blähte
        # tools/list massiv auf, ohne den Agenten zu helfen.
        describe_all_responses=False,
        describe_full_response_schema=False,
        include_operations=MCP_ALLOWED_OPERATIONS,
    )
    mcp.mount()
    return mcp
