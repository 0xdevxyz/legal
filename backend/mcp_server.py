"""
Complyo MCP Server Configuration
Exposiert die Complyo FastAPI-API als MCP-Server fuer KI-Agenten.

Ausgeschlossene Tags (nicht als MCP-Tools verfuegbar):
- admin:   Admin-only Routen (User-Verwaltung, System-Konfiguration)
- stripe:  Stripe-Webhooks & interne Zahlungs-Callbacks
- leads:   Interne Lead-Verwaltung
"""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

EXCLUDED_TAGS = [
    "admin",
    "stripe",
    "leads",
]

MCP_SERVER_DESCRIPTION = """
Complyo Compliance Platform MCP-Server.

Verfuegbare Faehigkeiten:
- Website-Scans starten und Ergebnisse abrufen (DSGVO, WCAG, BFSG, Cookie)
- AI-Fixes generieren und anwenden
- Cookie-Banner konfigurieren und Consent verwalten
- Legal-Dokumente (Datenschutzerklaerung, Impressum, DPA) generieren
- Compliance-Scores und Dashboard-Reports abrufen
- TCF 2.2 Vendor-Listen verwalten
- Accessibility-Fixes (Alt-Text, WCAG) generieren
- Legal-News und Gesetzesaenderungen abrufen
- AI Legal Classifier und Feedback-Learning

Authentifizierung: Bearer-Token (JWT) erforderlich.
Alle Requests muessen den Header 'Authorization: Bearer <token>' enthalten.
"""


def setup_mcp(app: FastAPI) -> FastApiMCP:
    """Initialisiert und mounted den MCP-Server auf die FastAPI-App."""
    mcp = FastApiMCP(
        app,
        name="Complyo MCP",
        description=MCP_SERVER_DESCRIPTION,
        describe_all_responses=True,
        describe_full_response_schema=True,
        exclude_tags=EXCLUDED_TAGS,
    )
    mcp.mount()
    return mcp
