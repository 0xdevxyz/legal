"""
Auth-/Ownership-Tests für ab_test_routes
========================================

Befund (2026-07-29): Der A/B-Testing-Router war ohne jede Auth-Prüfung
registriert. `POST /api/ab-tests`, `/start`, `/stop` und `DELETE /{test_id}`
waren öffentlich erreichbar — jeder konnte für eine fremde `site_id` einen Test
anlegen, den laufenden Test einer fremden Seite stoppen oder löschen und damit
die ausgelieferte Banner-Konfiguration fremder Kunden verändern.

Aufbau analog test_cookie_consent_auth.py:
1. `TestOeffentlicheRouten` — statischer Wächter über den Quelltext. Schlägt an,
   sobald eine neue Route ohne Auth hinzukommt. Braucht weder fastapi noch DB.
2. `TestOwnership` — Verhalten der Helfer bei fremder site_id / test_id.
"""
import os
import re

import pytest

_ROUTES_FILE = os.path.join(os.path.dirname(__file__), "..", "ab_test_routes.py")

# Routen, die der Besucher-Browser ohne Complyo-Login erreichen muss.
# Belegt durch die Aufrufe in backend/widgets/cookie_banner_v2.js.
# NICHTS hier eintragen, das Testkonfigurationen liest oder schreibt.
OEFFENTLICH_GEWOLLT = {
    "/assign/{site_id}/{visitor_id}",  # Banner holt die Variante des Besuchers
    "/track",                          # Banner meldet Impression/Entscheidung
}

_ROUTE_PATTERN = re.compile(
    r'@router\.(get|post|patch|delete|put)\("([^"]*)"\)\s*\nasync def (\w+)\((.*?)\n\):',
    re.S,
)


def _routen():
    with open(_ROUTES_FILE, encoding="utf-8") as fh:
        src = fh.read()
    for m in _ROUTE_PATTERN.finditer(src):
        methode, pfad, fn, signatur = m.group(1), m.group(2), m.group(3), m.group(4)
        geschuetzt = "current_user" in signatur
        yield methode.upper(), pfad, fn, geschuetzt


class TestOeffentlicheRouten:
    def test_routen_werden_erkannt(self):
        """Wenn der Regex nichts findet, sind alle folgenden Tests wertlos."""
        assert len(list(_routen())) >= 9

    def test_keine_unerwartet_offene_route(self):
        offen = {pfad for _, pfad, _, geschuetzt in _routen() if not geschuetzt}
        unerwartet = offen - OEFFENTLICH_GEWOLLT
        assert not unerwartet, (
            "Route(n) ohne Auth-Prüfung: "
            + ", ".join(sorted(unerwartet))
            + ". Entweder current_user + assert_site_owner/assert_test_owner ergänzen "
            "oder — falls das Banner die Route ohne Login braucht — bewusst in "
            "OEFFENTLICH_GEWOLLT aufnehmen."
        )

    def test_allowlist_ist_nicht_verwaist(self):
        vorhandene = {pfad for _, pfad, _, _ in _routen()}
        verwaist = OEFFENTLICH_GEWOLLT - vorhandene
        assert not verwaist, f"Allowlist nennt nicht (mehr) existierende Routen: {sorted(verwaist)}"

    @pytest.mark.parametrize(
        "pfad", ["", "/{test_id}", "/site/{site_id}", "/{test_id}/start", "/{test_id}/stop"]
    )
    def test_verwaltungsroute_ist_geschuetzt(self, pfad):
        """Namentlich die Routen, die am 29.07.2026 offen standen."""
        treffer = [g for _, p, _, g in _routen() if p == pfad]
        assert treffer, f"Route {pfad!r} nicht gefunden — Test anpassen oder Route wiederherstellen"
        assert all(treffer), f"Route {pfad!r} ist wieder ohne Auth-Prüfung"

    def test_ownership_wird_auch_wirklich_aufgerufen(self):
        """current_user in der Signatur allein schützt nicht — der Helfer muss laufen."""
        with open(_ROUTES_FILE, encoding="utf-8") as fh:
            src = fh.read()
        for fn in ("create_ab_test", "get_ab_test", "get_site_tests", "update_ab_test",
                   "start_ab_test", "stop_ab_test", "delete_ab_test"):
            koerper = src.split(f"async def {fn}(", 1)[1].split("\n@router.", 1)[0]
            assert "assert_site_owner(" in koerper or "assert_test_owner(" in koerper, (
                f"{fn} hat current_user, prüft aber keine Ownership"
            )

    def test_track_akzeptiert_nur_laufende_tests(self):
        """Der öffentliche Track-Endpunkt darf keine beliebige test_id beschreiben."""
        with open(_ROUTES_FILE, encoding="utf-8") as fh:
            src = fh.read()
        koerper = src.split("async def track_ab_result(", 1)[1]
        assert "status = 'running'" in koerper, (
            "track_ab_result prüft nicht mehr, ob der Test läuft — "
            "fremde Zählwerte könnten beliebige Tests verfälschen"
        )


class TestOwnership:
    """assert_site_owner / assert_test_owner gegen eine gemockte DB."""

    @staticmethod
    def _modul():
        try:
            import ab_test_routes
        except Exception:  # pragma: no cover — läuft nur im Backend-Container
            pytest.skip("ab_test_routes nicht importierbar")
        return ab_test_routes

    class _Pool:
        """Minimaler asyncpg-Pool-Ersatz."""

        def __init__(self, antworten):
            self._antworten = list(antworten)
            self.abfragen = []

        async def fetchrow(self, query, *args):
            self.abfragen.append((query, args))
            return self._antworten.pop(0) if self._antworten else None

    @pytest.mark.asyncio
    async def test_fremde_site_id_wird_abgelehnt(self):
        apr = self._modul()
        from fastapi import HTTPException

        pool = self._Pool([None])  # Kein Treffer in cookie_banner_configs
        with pytest.raises(HTTPException) as exc:
            await apr.assert_site_owner(pool, {"id": 42}, "fremde-site")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_eigene_site_id_wird_durchgelassen(self):
        apr = self._modul()
        pool = self._Pool([{"?column?": 1}])
        await apr.assert_site_owner(pool, {"id": 42}, "eigene-site")
        # Die Abfrage muss die user_id wirklich einsetzen, sonst prüft sie nichts.
        _, args = pool.abfragen[0]
        assert args == ("eigene-site", 42)

    @pytest.mark.asyncio
    async def test_unbekannte_test_id_ergibt_404(self):
        apr = self._modul()
        from fastapi import HTTPException

        pool = self._Pool([None])
        with pytest.raises(HTTPException) as exc:
            await apr.assert_test_owner(pool, {"id": 42}, 999)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_fremder_test_ergibt_404_nicht_403(self):
        """Kein Existenz-Leak: fremde Tests sehen aus wie nicht vorhandene."""
        apr = self._modul()
        from fastapi import HTTPException

        # 1. Abfrage findet den Test, 2. Abfrage (Ownership) findet nichts.
        pool = self._Pool([{"site_id": "fremde-site"}, None])
        with pytest.raises(HTTPException) as exc:
            await apr.assert_test_owner(pool, {"id": 42}, 7)
        assert exc.value.status_code == 404
