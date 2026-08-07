"""
Waechter fuer die Freigabe der Farbentscheidungen.

Die Kontrast-Reparatur war einmal vollstaendig gebaut, verifiziert und
verdrahtet — und trotzdem wertlos, weil niemand sie freigeben konnte. Der Fix
lag korrekt auf 'pending', und 'pending' liefert das Manifest nicht aus. Eine
Funktion ohne Knopf ist keine Funktion.

Diese Datei haelt die drei Zusagen fest, an denen das haengt:
  1. Es gibt einen Endpunkt, und er prueft Anmeldung und Eigentum.
  2. Ausgeliefert wird nur, was jemand freigegeben hat — nie mehr.
  3. Eine eigene Farbe wird geprueft, nicht geglaubt.

Dazu die Verdrahtung ins Frontend: Endpunkt, Karte und Einbindung muessen
zusammenpassen, sonst klickt der Kunde ins Leere.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DASHBOARD = os.path.join(
    os.path.dirname(_BACKEND), "dashboard-react", "src", "components", "accessibility"
)

# Der Standard-Testlauf haengt nur backend/ in den Container. Dann kann diese
# Datei die Oberflaeche nicht sehen — sie wird uebersprungen statt rot zu
# werden. Wer die Frontend-Waechter braucht (CI, lokal, mit vollem Repo),
# bekommt sie automatisch; die Zusagen ans Backend gelten immer.
_OHNE_FRONTEND = pytest.mark.skipif(
    not os.path.isdir(_DASHBOARD),
    reason="dashboard-react nicht eingehaengt — Frontend-Waechter uebersprungen",
)


def _lese(pfad: str) -> str:
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


def _backend(*teile: str) -> str:
    return _lese(os.path.join(_BACKEND, *teile))


def _frontend(datei: str) -> str:
    return _lese(os.path.join(_DASHBOARD, datei))


class TestEndpunkt:
    def test_es_gibt_ihn(self):
        assert '@router.post("/approve-kontrast")' in _backend("alt_text_routes.py")

    def test_er_verlangt_anmeldung_und_eigentum(self):
        """
        Ohne Ownership koennte ein angemeldeter Nutzer die Farben einer FREMDEN
        Website aendern — sichtbar, sofort, auf einer Seite, die ihm nicht
        gehoert.
        """
        src = _backend("alt_text_routes.py")
        block = src[src.index('@router.post("/approve-kontrast")'):]
        block = block[:block.index('@router.get("/worklist")')]
        assert "get_required_user" in block
        assert "require_site_ownership" in block

    def test_worklist_liefert_die_entscheidungen(self):
        src = _backend("alt_text_routes.py")
        assert "get_kontrast_entscheidungen" in src
        assert '"kontrast": {' in src

    def test_offene_entscheidungen_zaehlen_als_zu_pruefen(self):
        """Sonst steht oben '0 zu prüfen', obwohl Arbeit liegt."""
        src = _backend("alt_text_routes.py")
        block = src[src.index('"totals": {'):]
        assert 'freigabe") == "pending"' in block[:400]


class TestNurFreigegebenesGehtRaus:
    def test_regeln_werden_aus_zugestimmten_neu_gebaut(self):
        src = _backend("accessibility_fix_saver.py")
        block = src[src.index("async def set_kontrast_freigabe"):]
        block = block[:block.index("async def get_kontrast_entscheidungen")]
        assert 'e.get("freigabe") == "approved"' in block
        assert 'payload["rules"] = als_css_regeln' in block

    def test_ohne_zustimmung_bleibt_die_zeile_pending(self):
        src = _backend("accessibility_fix_saver.py")
        block = src[src.index("async def set_kontrast_freigabe"):]
        assert 'zeilen_status = "approved" if freigegeben else "pending"' in block

    def test_status_typ_ist_eindeutig(self):
        """
        `$2` steht einmal als Spaltenwert und einmal im Vergleich. Ohne
        ausdruecklichen Typ lehnt Postgres die Anweisung ab — im Durchstich
        genau so passiert.
        """
        src = _backend("accessibility_fix_saver.py")
        assert "status = $2::varchar" in src
        assert "CASE WHEN $2::varchar = 'approved'" in src


class TestEigeneFarbeWirdGeprueft:
    def test_zu_schwache_farbe_wird_abgelehnt(self):
        src = _backend("accessibility_fix_saver.py")
        block = src[src.index("async def set_kontrast_freigabe"):]
        assert "erreicht < ziel" in block
        assert '"ok": False' in block

    def test_die_erreichte_ratio_wird_neu_berechnet(self):
        """Der gespeicherte Wert muss zur Farbe passen, nicht zum Vorschlag."""
        src = _backend("accessibility_fix_saver.py")
        block = src[src.index("async def set_kontrast_freigabe"):]
        assert 'eintrag["neue_ratio"] = erreicht' in block


@_OHNE_FRONTEND
class TestOberflaeche:
    def test_karte_existiert(self):
        assert os.path.exists(os.path.join(_DASHBOARD, "KontrastFreigabe.tsx"))

    def test_karte_ruft_den_richtigen_endpunkt(self):
        assert "/api/accessibility/approve-kontrast" in _frontend("KontrastFreigabe.tsx")

    def test_karte_haengt_in_der_worklist(self):
        src = _frontend("AccessibilityWorklist.tsx")
        assert "KontrastFreigabe" in src
        assert "data.kontrast" in src

    def test_freigabe_laesst_sich_zuruecknehmen(self):
        """Ein Fehlklick darf nicht endgueltig sein."""
        assert "Zurückziehen" in _frontend("KontrastFreigabe.tsx")

    def test_vorschau_rechnet_die_eigene_farbe_nach(self):
        """
        Sonst zeigt das Muster die neue Farbe und die Kennzahl daneben die des
        alten Vorschlags — eine Zahl, die nicht zum Bild passt.
        """
        src = _frontend("KontrastFreigabe.tsx")
        assert "function ratio(" in src
        assert "zu wenig" in src

    def test_nach_der_freigabe_wird_neu_geladen(self):
        """Ohne das zeigt die Karte einen Stand, den es nicht mehr gibt."""
        assert "onGeaendert()" in _frontend("KontrastFreigabe.tsx")
