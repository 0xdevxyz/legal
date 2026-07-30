"""
MCP-Allowlist-Wächter
=====================

Bis 30.07.2026 exponierte der MCP-Server 296 Tools (Auto-Wrapper über die
gesamte API, nur Tag-Denylist). Jetzt gilt eine kuratierte Allowlist.

Zwei Invarianten, die dauerhaft gelten müssen:
1. Es gibt eine Allowlist (include_operations), keine Denylist — neue Routen
   werden NICHT automatisch zum Agenten-Tool.
2. Bestimmte Fähigkeiten sind niemals MCP-Tools: Direktschreiben auf
   Kundenserver, Review-Freigaben, OAuth-Callbacks, Zahlungen.
"""
import os

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _modul():
    import sys
    sys.path.insert(0, _BACKEND)
    import mcp_server
    return mcp_server


class TestAllowlist:
    def test_allowlist_statt_denylist(self):
        m = _modul()
        assert hasattr(m, "MCP_ALLOWED_OPERATIONS"), "Die Allowlist fehlt"
        assert not hasattr(m, "EXCLUDED_TAGS"), (
            "EXCLUDED_TAGS ist zurück — das war die Denylist, die jede neue "
            "Route automatisch zum Tool machte"
        )
        with open(os.path.join(_BACKEND, "mcp_server.py"), encoding="utf-8") as fh:
            src = fh.read()
        assert "include_operations=" in src
        assert "exclude_tags=" not in src

    def test_allowlist_ist_klein_und_explizit(self):
        m = _modul()
        anzahl = len(m.MCP_ALLOWED_OPERATIONS)
        assert 5 <= anzahl <= 20, (
            f"{anzahl} Tools — die Allowlist soll kuratiert bleiben, nicht wachsen. "
            "Bewusste Erweiterungen: Zahl hier anheben und begründen."
        )

    @pytest.mark.parametrize("verboten", [
        # Direktschreiben und dessen Rollback: menschlicher Klick, nie Agent.
        "apply_fix",
        "rollback_fix",
        # Review-Freigaben bleiben menschlich.
        "approve_fix", "reject_fix",
        "approve_alt_text", "approve_link",
        # Kein OAuth-Handshake durch Agenten.
        "oauth_callback",
        # Keine Zahlungswege.
        "create_checkout", "stripe",
    ])
    def test_verbotene_faehigkeit_ist_kein_tool(self, verboten):
        m = _modul()
        treffer = [op for op in m.MCP_ALLOWED_OPERATIONS if verboten in op]
        assert not treffer, f"'{verboten}' darf kein MCP-Tool sein: {treffer}"

    def test_response_schema_bleibt_kompakt(self):
        with open(os.path.join(_BACKEND, "mcp_server.py"), encoding="utf-8") as fh:
            src = fh.read()
        assert "describe_full_response_schema=False" in src
        assert "describe_all_responses=False" in src


class TestRateLimit:
    def test_middleware_drosselt(self):
        with open(os.path.join(_BACKEND, "main_production.py"), encoding="utf-8") as fh:
            src = fh.read()
        block = src.split("async def mcp_auth_middleware", 1)[1][:3000]
        assert "mcp_rl:" in block, "MCP-Rate-Limit ist aus der Middleware verschwunden"
        assert "429" in block
