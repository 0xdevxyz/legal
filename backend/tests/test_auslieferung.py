"""
Der Auslieferungszustand darf nie eine falsche Entwarnung geben.

Beim Oberflaechen-Durchlauf war das der teuerste Befund: von sechs
Kundenwebsites liefert genau EINE aus. Auf den anderen ist alles freigegeben,
das Dashboard meldete "erledigt", und beim Besucher kam nichts an — weil das
Skript fehlt, unter einer falschen Kennung laeuft oder entfernt wurde.

Die erste Fassung der Anzeige machte aus "hat sich irgendwann mal gemeldet"
ein "laeuft". spedition-mahn.de hatte GENAU EINEN Aufruf mit 1 angewendet und
33 verfehlt, und im HTML steht das Skript inzwischen gar nicht mehr — die
Anzeige haette gruen gezeigt. Eine falsche Entwarnung ist schlimmer als keine
Anzeige, deshalb diese Tests.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import agentur_a11y_routes as agentur  # noqa: E402


def _quelle() -> str:
    pfad = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "agentur_a11y_routes.py")
    with open(pfad, encoding="utf-8") as fh:
        quelle = fh.read()
    # Docstrings und Kommentare raus — sie nennen die Zustaende woertlich.
    quelle = re.sub(r'"""[\s\S]*?"""', "", quelle)
    return "\n".join(re.sub(r"#.*$", "", z) for z in quelle.splitlines())


class TestZustaende:
    def test_alle_fuenf_sind_im_code(self):
        q = _quelle()
        for zustand in ("laeuft", "greift_nicht", "verstummt",
                        "nichts_da", "nichts_zu_tun"):
            assert f'"{zustand}"' in q, zustand

    def test_alt_texte_loesen_keinen_alarm_aus(self):
        """
        Die erste Regel war `verfehlt > angewendet` ueber ALLE Arten und
        schlug damit im GESUNDEN Fall Alarm: zua-zwickau.de meldete
        "0 angewendet, 5 verfehlt", weil die Bilder ihre Alt-Texte laengst
        tragen (nichts anzuwenden) und die freigegebenen Alt-Texte zu Bildern
        gehoeren, die auf dieser Unterseite nicht vorkommen (normal).

        Alt-Text-Fehlschlaege sind Rauschen aus der Seitenstruktur, kein
        Regressionssignal. Der Alarm darf sie nicht mitzaehlen.
        """
        q = _quelle()
        assert "verfehlt > angewendet" not in q, \
            "Alter Alarm zurueck — er feuert auf gesunden Websites"
        assert "selektor_arten" in q
        i = q.index("selektor_arten")
        block = q[i:i + 200]
        assert "alt_texte" not in block, \
            "Alt-Texte gehoeren nicht in den Alarm"
        for art in ("css_regeln", "struktur", "link_labels", "dokument_fixes"):
            assert art in block, art

    def test_alarm_nur_wenn_gar_nichts_greift(self):
        """
        Lieber ein Alarm zu wenig als einer zu viel: erst wenn KEINE einzige
        selektorgebundene Reparatur mehr greift, ist es ein Befund.
        """
        assert "if s_verfehlt and not s_angewendet:" in _quelle()

    def test_alte_meldung_ist_kein_laeuft(self):
        q = _quelle()
        assert "tage_her >= STILL_AB_TAGEN" in q

    def test_schwelle_ist_gesetzt_und_grosszuegig(self):
        assert 1 <= agentur.STILL_AB_TAGEN <= 30


class TestSummeZaehltAlleFehlzustaende:
    def test_nicht_nur_nichts_da(self):
        """
        Die Summe zaehlte anfangs nur 'nichts_da'. Eine Website, deren Widget
        entfernt wurde oder deren Reparaturen ins Leere laufen, fehlte in der
        Zahl — und das ist genau der Fall, den niemand von selbst bemerkt.
        """
        q = _quelle()
        i = q.index("websites_ohne_auslieferung")
        block = q[i:i + 260]
        for zustand in ("nichts_da", "verstummt", "greift_nicht"):
            assert zustand in block, zustand


class TestDieAnzeigeStehtNebenDerArbeit:
    def test_worklist_ruft_die_pruefung_je_website(self):
        q = _quelle()
        assert "await _auslieferung(sid)" in q

    def test_pruefung_ist_vor_dem_dekorator_definiert(self):
        """
        Der Helfer stand einmal ZWISCHEN `@router.get("/worklist")` und der
        Funktion — dadurch hing der Dekorator am Helfer und die echte Route
        verlor ihre Anmeldepflicht. Ein Waechtertest hat das gefangen; hier
        steht es nochmal ausdruecklich.
        """
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "agentur_a11y_routes.py")
        with open(pfad, encoding="utf-8") as fh:
            roh = fh.read()
        assert roh.index("async def _auslieferung") < roh.index('@router.get("/worklist")')
