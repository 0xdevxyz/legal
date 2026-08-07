"""
Wächter für die portfolioweite Barrierefreiheit (Agentur-Tarif).

Warum diese Datei streng ist
----------------------------
An diesem Weg hängt der Preisunterschied: zwanzig Websites kosten einzeln
20 × 49 € = 980 €, der Agentur-Tarif 299 €. Die Rechnung geht nur auf, wenn die
Arbeit wie EIN Vorgang läuft — und sie kippt sofort ins Gegenteil, wenn eine
Sammelaktion mehr anfasst als angekündigt. Ein Knopf, der über zwanzig
Kundenwebsites geht, muss belegbar genau treffen.

Die vier Zusagen:
  1. Jede Route verlangt Anmeldung.
  2. Fremde Websites sind tabu, auch in der Massenaktion.
  3. Es gibt eine Vorschau — vor dem Klick, nicht danach.
  4. Es gibt KEINE websiteübergreifende Farbfreigabe. Die Messung über 24
     echte Seiten ergab 63 Farbpaare, kein einziges auf mehr als einer
     Website; so ein Knopf wäre geraten, nicht abgeleitet.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import agentur_a11y_routes as agentur  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile: str) -> str:
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


_ROUTE = re.compile(
    r'@router\.(get|post)\("([^"]*)"\)\s*\nasync def (\w+)\(((?:[^()]|\([^()]*\))*)\)',
    re.S,
)


def _routen():
    for m in _ROUTE.finditer(_lese("agentur_a11y_routes.py")):
        yield m.group(1).upper(), m.group(2), m.group(3), m.group(4)


class TestRouten:
    def test_routen_werden_erkannt(self):
        """Findet der Regex nichts, sind alle folgenden Tests wertlos."""
        assert len(list(_routen())) >= 4

    def test_jede_route_verlangt_anmeldung(self):
        offen = {f"{m} {p}" for m, p, _, sig in _routen()
                 if "get_required_user" not in sig}
        assert not offen, "Agentur-Route(n) ohne Anmeldung: " + ", ".join(sorted(offen))

    def test_router_ist_registriert(self):
        """
        Die Routen existieren sonst nur auf der Platte. Genau so bleibt eine
        fertige Funktion unbenutzt — deshalb steht die Registrierung unter Test.
        """
        src = _lese("main_production.py")
        assert "agentur_a11y_router" in src
        assert "app.include_router(agentur_a11y_router)" in src
        assert "init_agentur_a11y_routes(db_pool)" in src


class TestKeineFarbenUeberWebsitesHinweg:
    def test_es_gibt_keine_portfolioweite_farbfreigabe(self):
        """
        Der Verzicht ist eine Entscheidung, keine Lücke: 63 Farbpaare über 24
        Websites, kein einziges doppelt. Wer diesen Knopf nachrüstet, sollte
        vorher neu messen.
        """
        pfade = [p for _, p, _, _ in _routen()]
        assert not any("farben" in p and "alle" in p for p in pfade)
        assert "/farben-freigeben" in pfade

    def test_farbfreigabe_verlangt_genau_eine_website(self):
        assert "site_id" in agentur.FarbenFreigabeRequest.model_fields
        assert set(agentur.FarbenFreigabeRequest.model_fields) == {"site_id"}

    def test_der_grund_steht_im_code(self):
        """Damit die Entscheidung nicht als Versäumnis missverstanden wird."""
        src = _lese("agentur_a11y_routes.py")
        assert "63 Farbpaare" in src


class TestSammelfreigabe:
    def test_schwelle_trennt_vision_von_heuristik(self):
        """
        Im echten Bestand gibt es genau zwei Konfidenzen: 0,900 wenn Claude
        Vision das Bild gesehen hat, 0,700 für die Kontext-Heuristik
        ("Bild: Image 20"). Die Schwelle ist gemessen, nicht gesetzt.
        """
        assert agentur.VISION_SCHWELLE == 0.9

    def test_nichtssagendes_faellt_auch_bei_hoher_konfidenz_durch(self):
        gut = {"confidence": 0.95, "suggested_alt": "Gelber Sattelzug vor der Halle"}
        muell = {"confidence": 0.95, "suggested_alt": "Bild: Image 20"}
        assert agentur._ist_brauchbar(gut, 0.9)
        assert not agentur._ist_brauchbar(muell, 0.9)

    def test_unter_der_schwelle_bleibt_liegen(self):
        heuristik = {"confidence": 0.7, "suggested_alt": "Team vor dem Firmensitz"}
        assert not agentur._ist_brauchbar(heuristik, 0.9)

    def test_kaputte_konfidenz_gilt_als_ungeeignet(self):
        assert not agentur._ist_brauchbar({"confidence": None, "suggested_alt": "x"}, 0.9)
        assert not agentur._ist_brauchbar({"confidence": "abc", "suggested_alt": "x"}, 0.9)

    def test_es_gibt_eine_vorschau(self):
        """Eine Massenaktion ohne vorherige Auskunft ist ein Knopf, den man bereut."""
        assert "/sammelfreigabe/vorschau" in [p for _, p, _, _ in _routen()]


class TestFremdeWebsitesBleibenTabu:
    def test_sammelfreigabe_prueft_die_site_ids(self):
        src = _lese("agentur_a11y_routes.py")
        block = src[src.index("async def sammelfreigabe("):]
        block = block[:block.index("@router.post(\"/farben-freigeben\")")]
        assert "Kein Zugriff auf diese Website" in block
        assert "status_code=403" in block

    def test_farbfreigabe_prueft_die_site_id(self):
        src = _lese("agentur_a11y_routes.py")
        block = src[src.index("async def farben_freigeben("):]
        assert "status_code=403" in block

    def test_die_website_liste_kommt_immer_vom_konto(self):
        """
        `_eigene_sites` ist die einzige Quelle — nirgends darf eine site_id aus
        der Anfrage ungeprüft weiterverwendet werden.
        """
        src = _lese("agentur_a11y_routes.py")
        assert src.count("_eigene_sites(user_id)") >= 4
