"""
Rechteausweitung beim Add-on-Kauf + MCP-Auth
============================================

Befund (2026-07-17): `POST /api/addons/subscribe/{addon_key}` nahm den Plan aus
dem Request-Body (`AddAddonRequest.user_plan`). Ein Professional-Kunde konnte
`user_plan: "enterprise"` senden und bekam `{"ai_systems": -1}` (unbegrenzt)
statt 10 — zum Professional-Preis. Der Wert wanderte über die Stripe-Metadaten
in `create_user_addon` und war damit dauerhaft wirksam.

Zwei Ebenen (analog test_cookie_consent_auth.py):
1. Unit-Tests gegen `resolve_addon_plan` / den Endpunkt mit gemockter DB.
2. Statische Wächter über den Quelltext (brauchen weder fastapi noch DB).
"""
import os
import re

import pytest

_ADDON_FILE = os.path.join(os.path.dirname(__file__), "..", "addon_payment_routes.py")
_MAIN_FILE = os.path.join(os.path.dirname(__file__), "..", "main_production.py")


def _quelltext(pfad):
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


class _FakeConn:
    """Minimaler asyncpg-Connection-Ersatz — liefert einen festen plan_type."""

    def __init__(self, plan_type):
        self._plan_type = plan_type
        self.queries = []

    async def fetchval(self, query, *args):
        self.queries.append(query)
        return self._plan_type

    async def fetchrow(self, query, *args):
        return {"email": "kunde@example.com"}

    async def execute(self, query, *args):
        return "UPDATE 1"


class _FakeConnCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


def _patch_db(monkeypatch, apr, plan_type):
    conn = _FakeConn(plan_type)
    monkeypatch.setattr(apr.db_service, "get_connection", lambda: _FakeConnCtx(conn))
    return conn


class TestResolveAddonPlan:
    """Der Plan kommt aus der DB, nicht vom Client."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "plan_type,erwartet",
        [
            ("pro", "professional"),
            ("professional", "professional"),
            ("free", "starter"),
            ("single", "starter"),
            ("premium", "business"),
            ("complete", "business"),
            ("expert", "business"),
            ("agency", "agency"),
            ("enterprise", "enterprise"),
            ("PRO", "professional"),  # Gross-/Kleinschreibung egal
        ],
    )
    async def test_mapping(self, monkeypatch, plan_type, erwartet):
        apr = pytest.importorskip("addon_payment_routes")
        _patch_db(monkeypatch, apr, plan_type)
        assert await apr.resolve_addon_plan(42) == erwartet

    @pytest.mark.asyncio
    @pytest.mark.parametrize("plan_type", ["quantum_deluxe", "", None])
    async def test_unbekannter_plan_faellt_auf_kleinsten_satz(self, monkeypatch, plan_type):
        """Unbekannt/keine Subscription → starter, NIEMALS enterprise."""
        apr = pytest.importorskip("addon_payment_routes")
        _patch_db(monkeypatch, apr, plan_type)

        plan = await apr.resolve_addon_plan(42)
        assert plan == "starter"

        limits = apr.MONTHLY_ADDONS["comploai_guard"]["limits_by_plan"][plan]
        assert limits == {"ai_systems": 10}
        # Kleinster Satz: keiner der anderen Pläne ist restriktiver.
        assert limits["ai_systems"] != -1

    @pytest.mark.asyncio
    async def test_db_fehler_faellt_auf_kleinsten_satz(self, monkeypatch):
        apr = pytest.importorskip("addon_payment_routes")

        def _boom():
            raise RuntimeError("DB weg")

        monkeypatch.setattr(apr.db_service, "get_connection", _boom)
        assert await apr.resolve_addon_plan(42) == apr.FALLBACK_ADDON_PLAN == "starter"


class TestKeineRechteausweitung:
    """Der Kernbefund: Client-gesendetes user_plan darf nichts bewirken."""

    @pytest.mark.asyncio
    async def test_body_user_plan_enterprise_wird_ignoriert(self, monkeypatch):
        apr = pytest.importorskip("addon_payment_routes")

        # DB sagt: dieser Account ist 'pro' (= Katalog-Plan 'professional').
        _patch_db(monkeypatch, apr, "pro")

        async def _check_user_addon(_uid, _key):
            return False

        monkeypatch.setattr(apr.db_service, "check_user_addon", _check_user_addon)

        erfasst = {}

        class _FakeSession:
            url = "https://checkout.stripe.test/s/1"
            id = "cs_test_1"

        def _create(**kwargs):
            erfasst.update(kwargs)
            return _FakeSession()

        monkeypatch.setattr(apr.stripe.checkout.Session, "create", staticmethod(_create))

        # Angriff: Professional-Account behauptet 'enterprise'.
        request = apr.AddAddonRequest(addon_key="comploai_guard", user_plan="enterprise")
        await apr.subscribe_to_addon("comploai_guard", request, user_id=42)

        import json

        limits = json.loads(erfasst["metadata"]["limits"])
        assert limits == {"ai_systems": 10}, (
            "Client-gesendetes user_plan='enterprise' hat die Limits verändert — "
            "Rechteausweitung wieder offen"
        )
        assert limits.get("ai_systems") != -1

    def test_endpunkt_bleibt_kompatibel_zum_frontend(self):
        """
        Das Frontend (dashboard-react/src/lib/ai-compliance-api.ts) sendet user_plan
        weiterhin mit. Das darf keinen Validierungsfehler auslösen — nur wirkungslos sein.
        """
        apr = pytest.importorskip("addon_payment_routes")
        req = apr.AddAddonRequest(addon_key="comploai_guard", user_plan="enterprise")
        assert req.addon_key == "comploai_guard"


class TestStatischeWaechter:
    """Brauchen weder fastapi noch DB."""

    def test_limits_werden_nicht_aus_dem_body_gezogen(self):
        src = _quelltext(_ADDON_FILE)
        assert "data.user_plan" not in src, (
            "addon_payment_routes liest wieder data.user_plan — der Plan muss "
            "serverseitig via resolve_addon_plan aus der DB kommen"
        )
        assert "resolve_addon_plan(user_id)" in src

    def test_kein_plan_ist_grosszuegiger_als_der_fallback(self):
        """Der Fallback muss der kleinste Limit-Satz sein."""
        apr = pytest.importorskip("addon_payment_routes")
        limits_by_plan = apr.MONTHLY_ADDONS["comploai_guard"]["limits_by_plan"]
        fallback = limits_by_plan[apr.FALLBACK_ADDON_PLAN]["ai_systems"]

        def _gewicht(n):
            return float("inf") if n == -1 else n  # -1 = unbegrenzt

        assert _gewicht(fallback) == min(
            _gewicht(v["ai_systems"]) for v in limits_by_plan.values()
        )

    def test_mapping_deckt_alle_bekannten_plan_types_ab(self):
        apr = pytest.importorskip("addon_payment_routes")
        # Werte aus stripe_routes.PLAN_WEBSITES_MAX + deep_cookie_scanner_routes.check_premium_plan
        bekannt = {
            "free", "single", "pro", "agency", "expert", "update",
            "premium", "enterprise", "complete",
        }
        fehlend = bekannt - set(apr.PLAN_TYPE_TO_ADDON_PLAN)
        assert not fehlend, f"plan_type ohne explizites Mapping: {sorted(fehlend)}"

    def test_mapping_zeigt_nur_auf_existierende_katalog_plaene(self):
        apr = pytest.importorskip("addon_payment_routes")
        katalog = set()
        for addon in apr.MONTHLY_ADDONS.values():
            katalog |= set(addon.get("limits_by_plan", {}))
            katalog |= set(addon.get("compatible_plans", []))
        unbekannt = set(apr.PLAN_TYPE_TO_ADDON_PLAN.values()) - katalog
        assert not unbekannt, f"Mapping zeigt auf Nicht-Katalog-Pläne: {sorted(unbekannt)}"

    def test_site_kontingent_addon_erhoeht_websites_max(self):
        """agency_sites_extra muss das Limit additiv erhöhen (wie stripe_routes)."""
        src = _quelltext(_ADDON_FILE)
        assert "websites_max = COALESCE(websites_max, 0) + $2" in src, (
            "Site-Kontingent-Add-on legt wieder nur eine user_addons-Zeile an, "
            "ohne websites_max zu erhöhen"
        )


class TestMcpAuthMiddleware:
    """Die MCP-Middleware darf kein blosser Präfix-Vergleich mehr sein."""

    def _middleware_quelltext(self):
        src = _quelltext(_MAIN_FILE)
        m = re.search(
            r"async def mcp_auth_middleware\(request: Request, call_next\):(.*?)\n@app\.middleware",
            src,
            re.S,
        )
        assert m, "mcp_auth_middleware nicht gefunden"
        return m.group(1)

    def test_kein_reiner_praefix_vergleich(self):
        body = self._middleware_quelltext()
        # startswith("Bearer ") darf höchstens zum Zerlegen des Headers dienen,
        # niemals als alleinige Entscheidung über 401 vs. Durchlass.
        assert "get_current_user" in body, (
            "MCP-Middleware validiert das Token nicht über den kanonischen "
            "Verifikationspfad (dependencies.get_current_user)"
        )

    def test_nutzt_kanonischen_pfad_statt_eigenem_jwt_decode(self):
        body = self._middleware_quelltext()
        assert "jwt.decode" not in body, (
            "MCP-Middleware implementiert die JWT-Prüfung selbst neu — "
            "dependencies.get_current_user wiederverwenden"
        )

    def test_lehnt_ungueltiges_token_mit_401_ab(self):
        body = self._middleware_quelltext()
        assert "HTTPException" in body and "401" in body
