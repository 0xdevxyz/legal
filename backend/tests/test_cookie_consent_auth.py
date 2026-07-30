"""
Auth-/Ownership-Tests für cookie_compliance_routes
==================================================

Hintergrund (2026-07-17): 28 von 46 Routen des Cookie-Compliance-Routers hatten
keinerlei Auth-Prüfung. Unter anderem liess sich `GET /consents/{site_id}`
(personenbezogene Consent-Protokolle, Art. 7 DSGVO) ohne Token abrufen und
`POST /import` überschrieb die Banner-Config einer fremden Site.

Zwei Ebenen:
1. `TestOeffentlicheRouten` — statischer Wächter über den Quelltext. Er braucht
   weder fastapi noch DB und schlägt an, sobald eine NEUE Route ohne Auth
   hinzukommt, die nicht ausdrücklich öffentlich sein soll. Das ist der
   eigentliche Regressionsschutz.
2. `TestRequireSiteAccess` — Verhalten des Helfers (fremde site_id -> 403).
"""
import os
import re

import pytest

_ROUTES_FILE = os.path.join(os.path.dirname(__file__), "..", "cookie_compliance_routes.py")

# Routen, die das ausgelieferte Widget bzw. der Website-BESUCHER ohne Complyo-Login
# erreichen muss. Belegt durch die Aufrufe in backend/widgets/*.js.
# NICHTS hier eintragen, das Kundendaten liest oder eine Config schreibt.
OEFFENTLICH_GEWOLLT = {
    "/api/cookie-compliance/config/{site_id}",          # Widget lädt Banner-Config
    "/api/cookie-compliance/consent",                   # Besucher erteilt Consent
    "/api/cookie-compliance/revoke",                    # Besucher widerruft (DSGVO-Recht)
    "/api/cookie-compliance/reconsent-check/{site_id}",  # Widget prüft Re-Consent
    "/api/cookie-compliance/geo-check",                 # Widget: EU/Nicht-EU
    "/api/cookie-compliance/services",                  # öffentlicher Dienst-Katalog
    "/api/cookie-compliance/services/{service_key}",
    "/api/cookie-compliance/tcf/vendors",               # öffentliche IAB-Vendorliste
    "/api/cookie-compliance/policy/{site_id}",          # öffentliche Cookie-Richtlinie
    "/api/cookie-compliance/health",
    "/api/cookie-compliance/scan/capabilities",
}

_ROUTE_PATTERN = re.compile(
    r'@router\.(get|post|patch|delete|put)\("([^"]+)"\)\s*\nasync def (\w+)\((.*?)\n\):',
    re.S,
)


def _routen():
    with open(_ROUTES_FILE, encoding="utf-8") as fh:
        src = fh.read()
    for m in _ROUTE_PATTERN.finditer(src):
        methode, pfad, fn, signatur = m.group(1), m.group(2), m.group(3), m.group(4)
        geschuetzt = any(
            marker in signatur
            for marker in ("credentials", "current_user", "require_admin")
        )
        yield methode.upper(), pfad, fn, geschuetzt


class TestOeffentlicheRouten:
    def test_keine_unerwartet_offene_route(self):
        offen = {pfad for _, pfad, _, geschuetzt in _routen() if not geschuetzt}
        unerwartet = offen - OEFFENTLICH_GEWOLLT
        assert not unerwartet, (
            "Route(n) ohne Auth-Prüfung: "
            + ", ".join(sorted(unerwartet))
            + ". Entweder require_site_access ergänzen oder — falls das Widget die "
            "Route wirklich ohne Login braucht — bewusst in OEFFENTLICH_GEWOLLT aufnehmen."
        )

    def test_allowlist_ist_nicht_verwaist(self):
        """Schützt die Allowlist davor, zur Legende zu werden."""
        vorhandene_pfade = {pfad for _, pfad, _, _ in _routen()}
        verwaist = OEFFENTLICH_GEWOLLT - vorhandene_pfade
        assert not verwaist, f"Allowlist nennt nicht (mehr) existierende Routen: {sorted(verwaist)}"

    @pytest.mark.parametrize(
        "pfad",
        [
            "/api/cookie-compliance/consents/{site_id}",
            "/api/cookie-compliance/consents/{site_id}/export",
            "/api/cookie-compliance/consents/expired",
            "/api/cookie-compliance/import",
            "/api/cookie-compliance/export/{site_id}",
            "/api/cookie-compliance/revisions/{site_id}",
            "/api/cookie-compliance/consent-mode-config",
            "/api/cookie-compliance/age-verification",
            "/api/cookie-compliance/geo-restriction",
            "/api/cookie-compliance/forwarding",
            "/api/cookie-compliance/tcf/config",
            "/api/cookie-compliance/stats/{site_id}",
        ],
    )
    def test_sensible_route_ist_geschuetzt(self, pfad):
        """Namentlich die Routen, die 2026-07-17 offen standen."""
        treffer = [g for _, p, _, g in _routen() if p == pfad]
        assert treffer, f"Route {pfad} nicht gefunden — Test anpassen oder Route wiederherstellen"
        assert all(treffer), f"Route {pfad} ist wieder ohne Auth-Prüfung"

    def test_consent_logs_verlangen_credentials(self):
        """Der Kernbefund: Consent-Protokolle sind personenbezogen."""
        for _, pfad, fn, geschuetzt in _routen():
            if fn == "get_consent_logs":
                assert geschuetzt, "get_consent_logs gibt Consent-Protokolle ohne Auth aus"
                return
        pytest.fail("get_consent_logs nicht gefunden")


class TestRequireSiteAccess:
    """Verhalten des Helfers. Braucht das echte Modul -> läuft im Backend-Container."""

    @pytest.mark.asyncio
    async def test_fremde_site_id_wird_abgelehnt(self, monkeypatch):
        ccr = pytest.importorskip("cookie_compliance_routes")
        from fastapi import HTTPException

        async def _user(_credentials):
            return {"id": 1, "email": "a@b.de"}

        async def _uid(_user):
            return 1

        async def _module(_user, _mod):
            return True

        async def _sites(_uid_):
            return {"eigene-de"}

        monkeypatch.setattr(ccr, "get_current_user_required", _user)
        monkeypatch.setattr(ccr, "get_user_id_from_token", _uid)
        monkeypatch.setattr(ccr, "require_module", _module)
        monkeypatch.setattr(ccr, "get_user_site_ids", _sites)

        with pytest.raises(HTTPException) as exc:
            await ccr.require_site_access("fremde-de", credentials=None)
        assert exc.value.status_code == 403

        user, user_id = await ccr.require_site_access("eigene-de", credentials=None)
        assert user_id == 1

    @pytest.mark.asyncio
    async def test_user_ohne_sites_bekommt_403(self, monkeypatch):
        """Leere Site-Menge darf NICHT als 'darf alles' durchgehen."""
        ccr = pytest.importorskip("cookie_compliance_routes")
        from fastapi import HTTPException

        async def _user(_credentials):
            return {"id": 2}

        async def _uid(_user):
            return 2

        async def _module(_user, _mod):
            return True

        async def _sites(_uid_):
            return set()

        monkeypatch.setattr(ccr, "get_current_user_required", _user)
        monkeypatch.setattr(ccr, "get_user_id_from_token", _uid)
        monkeypatch.setattr(ccr, "require_module", _module)
        monkeypatch.setattr(ccr, "get_user_site_ids", _sites)

        with pytest.raises(HTTPException) as exc:
            await ccr.require_site_access("irgendeine-de", credentials=None)
        assert exc.value.status_code == 403
