"""
Tests fuer die Fortschritts-Registry.

Anlass: Die erste Live-Anzeige taktete sich an einer ERWARTETEN Laufzeit
entlang und sprang beim ersten echten Scan um. Jetzt melden die Checks selbst —
diese Tests sichern den Vertrag zwischen Scanner und Anzeige.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine import scan_progress as sp


def _frisch(token="test-token-1234"):
    sp.starte(token)
    return token


class TestRegistry:
    def test_start_registriert_statische_gruppen(self):
        t = _frisch()
        stand = sp.hole(t)
        titel = [g["titel"] for g in stand["gruppen"]]
        assert "Rechtstexte & Pflichtangaben" in titel
        assert "Barrierefreiheit (BFSG)" in titel
        assert all(not c["fertig"] for g in stand["gruppen"] for c in g["checks"])

    def test_melde_markiert_genau_einen_check(self):
        t = _frisch()
        sp.melde(t, "Rechtstexte & Pflichtangaben", "Impressum")
        stand = sp.hole(t)
        fertig = [c["name"] for g in stand["gruppen"] for c in g["checks"] if c["fertig"]]
        assert fertig == ["Impressum"]

    def test_unbekannter_check_wird_nachgetragen_statt_verloren(self):
        """Die Anzeige darf nie weniger wissen als das Backend."""
        t = _frisch()
        sp.melde(t, "Mehrseiten-Prüfung", "/agb")
        stand = sp.hole(t)
        mp = next(g for g in stand["gruppen"] if g["titel"] == "Mehrseiten-Prüfung")
        assert mp["checks"] == [{"name": "/agb", "fertig": True}]

    def test_registriere_checks_dupliziert_nicht(self):
        t = _frisch()
        sp.registriere_checks(t, "Mehrseiten-Prüfung", ["/agb", "/kontakt"])
        sp.registriere_checks(t, "Mehrseiten-Prüfung", ["/agb", "/impressum"])
        stand = sp.hole(t)
        mp = next(g for g in stand["gruppen"] if g["titel"] == "Mehrseiten-Prüfung")
        assert [c["name"] for c in mp["checks"]] == ["/agb", "/kontakt", "/impressum"]

    def test_abschliessen_setzt_alles_fertig(self):
        """Die Anzeige darf nie unfertig stehenbleiben, wenn die Antwort da ist."""
        t = _frisch()
        sp.abschliessen(t)
        stand = sp.hole(t)
        assert stand["fertig"] is True
        assert all(c["fertig"] for g in stand["gruppen"] for c in g["checks"])

    def test_nach_meldet_auch_bei_fehler(self):
        """Ein abgestuerzter Check ist ABGEARBEITET — sonst haengt die Anzeige."""
        t = _frisch()

        async def kaputt():
            raise RuntimeError("check kaputt")

        async def lauf():
            try:
                await sp.nach(kaputt(), t, "Technik & Sicherheit", "SSL & Security-Header")
            except RuntimeError:
                pass

        asyncio.run(lauf())
        stand = sp.hole(t)
        tech = next(g for g in stand["gruppen"] if g["titel"] == "Technik & Sicherheit")
        assert any(c["name"] == "SSL & Security-Header" and c["fertig"] for c in tech["checks"])

    def test_nach_ohne_token_wickelt_nicht(self):
        async def echt():
            return 42

        async def lauf():
            return await sp.nach(echt(), None, "x", "y")

        assert asyncio.run(lauf()) == 42

    def test_token_validierung(self):
        assert sp.token_gueltig("abc12345-def0-1234-5678-90abcdef1234")
        assert sp.token_gueltig("scan-1699999999-123456")
        assert not sp.token_gueltig("")
        assert not sp.token_gueltig("kurz")
        assert not sp.token_gueltig("böse/../pfad")
        assert not sp.token_gueltig("x" * 100)

    def test_unbekanntes_token_liefert_none(self):
        assert sp.hole("gibt-es-nicht-123") is None
