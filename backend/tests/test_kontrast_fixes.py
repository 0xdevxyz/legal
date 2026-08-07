"""
Tests fuer die Kontrast-Reparatur.

Kontrast ist der haeufigste Pflicht-Verstoss im echten Bestand (192 von 289
Fundstellen auf 24 KMU-Seiten) und zugleich der heikelste Fix: er aendert das
Aussehen der Kundenseite. Jede Regel hier ist deshalb eine Zusage — die
Vorgabe wird wirklich erreicht, der Farbton bleibt, und wo es nicht geht, wird
das gesagt statt geraten.

Die Zahlenbeispiele stammen aus echten Messungen (konditorei-limbach.de,
06.08.2026), nicht aus konstruierten Faellen.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.kontrast_fixes import (  # noqa: E402
    als_css, baue_kontrast_entscheidungen, finde_ersatzfarbe, geforderte_ratio,
    kontrast, verschaerfe, _hex_zu_rgb, _rgb_zu_hex,
)


def _knoten(fg, bg, ratio, selektor, groesse="7.8pt (10.4px)",
            gewicht="normal", erwartet="4.5:1", html="<span>x</span>"):
    return {
        "target": [selektor],
        "html": html,
        "any": [{"data": {
            "fgColor": fg, "bgColor": bg, "contrastRatio": ratio,
            "fontSize": groesse, "fontWeight": gewicht,
            "expectedContrastRatio": erwartet,
        }}],
    }


class TestMathematik:
    def test_kontrast_schwarz_auf_weiss_ist_21(self):
        assert round(kontrast((0, 0, 0), (255, 255, 255)), 1) == 21.0

    def test_gleiche_farbe_hat_ratio_1(self):
        assert round(kontrast((120, 30, 200), (120, 30, 200)), 2) == 1.0

    def test_echter_messwert_wird_reproduziert(self):
        """konditorei-limbach.de: #a86100 auf #edebe5, axe misst 4.02:1."""
        gemessen = kontrast(_hex_zu_rgb("#a86100"), _hex_zu_rgb("#edebe5"))
        assert abs(gemessen - 4.02) < 0.05, gemessen

    def test_farbformate(self):
        assert _hex_zu_rgb("#a86100") == (168, 97, 0)
        assert _hex_zu_rgb("a86100") == (168, 97, 0)
        assert _hex_zu_rgb("#abc") == (170, 187, 204)
        assert _hex_zu_rgb("rgb(168, 97, 0)") == (168, 97, 0)
        assert _hex_zu_rgb("bloedsinn") is None


class TestGeforderteRatio:
    def test_axe_wert_hat_vorrang(self):
        assert geforderte_ratio("40pt", "bold", "3:1") == 3.0

    def test_grosser_text_braucht_nur_drei(self):
        assert geforderte_ratio("20pt", "normal") == 3.0

    def test_fetter_text_ab_14pt_gilt_als_gross(self):
        assert geforderte_ratio("14pt", "bold") == 3.0
        assert geforderte_ratio("14pt", "normal") == 4.5

    def test_normaler_text_braucht_viereinhalb(self):
        assert geforderte_ratio("10pt", "normal") == 4.5


class TestErsatzfarbe:
    def test_erreicht_die_vorgabe_wirklich(self):
        """Die Kernzusage: der Vorschlag besteht die Pruefung, die er fixt."""
        vg, hg = _hex_zu_rgb("#a86100"), _hex_zu_rgb("#edebe5")
        neu, ratio = finde_ersatzfarbe(vg, hg, 4.5)
        assert ratio >= 4.5
        assert abs(kontrast(neu, hg) - ratio) < 0.01

    def test_farbton_bleibt_erhalten(self):
        """Ein Kunde soll seine Farbe wiedererkennen, keinen Fremdkoerper sehen."""
        import colorsys
        vg = _hex_zu_rgb("#a86100")
        neu, _ = finde_ersatzfarbe(vg, _hex_zu_rgb("#edebe5"), 4.5)
        h_alt = colorsys.rgb_to_hls(*(c / 255 for c in vg))[0]
        h_neu = colorsys.rgb_to_hls(*(c / 255 for c in neu))[0]
        assert abs(h_alt - h_neu) < 0.02, (h_alt, h_neu)

    def test_naechstliegende_richtung_gewinnt(self):
        """Auf hellem Grund wird abgedunkelt, nicht aufgehellt."""
        neu, _ = finde_ersatzfarbe(_hex_zu_rgb("#a86100"), _hex_zu_rgb("#edebe5"), 4.5)
        assert sum(neu) < sum(_hex_zu_rgb("#a86100"))

    def test_auf_dunklem_grund_wird_aufgehellt(self):
        neu, _ = finde_ersatzfarbe(_hex_zu_rgb("#333355"), _hex_zu_rgb("#111111"), 4.5)
        assert sum(neu) > sum(_hex_zu_rgb("#333355"))

    def test_minimale_aenderung_nicht_gleich_schwarz(self):
        """Kein Zuschlagen mit dem Holzhammer: nur so weit wie noetig."""
        neu, ratio = finde_ersatzfarbe(_hex_zu_rgb("#a86100"), _hex_zu_rgb("#edebe5"), 4.5)
        assert neu != (0, 0, 0)
        assert ratio < 6.0, f"deutlich uebers Ziel hinaus: {ratio}"

    def test_unloesbarer_fall_gibt_none(self):
        """Mittelgrau auf Mittelgrau: kein Ton dieser Farbe schafft 7:1."""
        assert finde_ersatzfarbe((128, 128, 128), (125, 125, 125), 7.0) is None


class TestEntscheidungen:
    def test_gleiche_farbpaare_werden_zu_einer_entscheidung(self):
        """
        Der eigentliche Wert: 11 Fundstellen auf konditorei-limbach.de sind in
        Wahrheit eine Handvoll Farbpaare. Eine Freigabe repariert viele Stellen.
        """
        nodes = [_knoten("#a86100", "#edebe5", 4.02, f".rc:nth-child({i})")
                 for i in range(1, 12)]
        e = baue_kontrast_entscheidungen(nodes)
        assert len(e) == 1
        assert e[0]["stellen"] == 11
        assert len(e[0]["selektoren"]) == 11

    def test_verschiedene_paare_bleiben_getrennt(self):
        e = baue_kontrast_entscheidungen([
            _knoten("#a86100", "#edebe5", 4.02, ".a"),
            _knoten("#999999", "#ffffff", 2.85, ".b"),
        ])
        assert len(e) == 2

    def test_wirkungsvollste_entscheidung_steht_oben(self):
        e = baue_kontrast_entscheidungen(
            [_knoten("#999999", "#ffffff", 2.85, ".selten")] +
            [_knoten("#a86100", "#edebe5", 4.02, f".haeufig{i}") for i in range(5)]
        )
        assert e[0]["stellen"] == 5

    def test_unloesbares_wird_benannt_statt_geraten(self):
        e = baue_kontrast_entscheidungen(
            [_knoten("#808080", "#7d7d7d", 1.03, ".x", erwartet="7:1")]
        )
        assert e[0]["loesbar"] is False
        assert e[0]["vorschlag"] is None
        assert "Hintergrund" in e[0]["hinweis"]

    def test_unloesbares_steht_hinten(self):
        e = baue_kontrast_entscheidungen([
            _knoten("#808080", "#7d7d7d", 1.03, ".x", erwartet="7:1"),
            _knoten("#a86100", "#edebe5", 4.02, ".y"),
        ])
        assert e[0]["loesbar"] is True
        assert e[-1]["loesbar"] is False

    def test_knoten_ohne_farbdaten_werden_uebersprungen(self):
        assert baue_kontrast_entscheidungen([{"target": [".x"], "any": []}]) == []

    def test_deckel_greift(self):
        nodes = [_knoten(_rgb_zu_hex((i, i, i)), "#ffffff", 2.0, f".s{i}")
                 for i in range(60, 100)]
        assert len(baue_kontrast_entscheidungen(nodes, max_gruppen=5)) == 5


class TestCSS:
    def test_css_enthaelt_selektoren_und_neue_farbe(self):
        e = baue_kontrast_entscheidungen([
            _knoten("#a86100", "#edebe5", 4.02, ".rc-source"),
        ])
        css = als_css(e)
        assert ".rc-source" in css
        assert e[0]["vorschlag"] in css
        assert "!important" in css

    def test_unloesbares_erzeugt_keine_regel(self):
        e = baue_kontrast_entscheidungen(
            [_knoten("#808080", "#7d7d7d", 1.03, ".x", erwartet="7:1")]
        )
        assert ".x" not in als_css(e)

    def test_kommentar_nennt_vorher_und_nachher(self):
        e = baue_kontrast_entscheidungen([_knoten("#a86100", "#edebe5", 4.02, ".x")])
        css = als_css(e)
        assert "4.02:1" in css and "#a86100" in css


class TestVerschaerfen:
    """
    Zweiter Anlauf, wenn die Messung hinter der Rechnung zurueckbleibt.

    Realer Anlass: Deckkraft ueber dem Element. axe meldet die effektive Farbe
    nach Mischung, eine gesetzte Farbe wird ebenso gemischt — der Vorschlag
    kommt gedaempft an. Aus der Ferne nicht berechenbar, also nachlegen.
    """

    def _entscheidung(self):
        return baue_kontrast_entscheidungen(
            [_knoten("#a86100", "#edebe5", 4.02, ".x")]
        )[0]

    def test_gemessener_fehlbetrag_erzeugt_dunkleren_vorschlag(self):
        e = self._entscheidung()
        erster = e["vorschlag"]
        assert verschaerfe(e, gemessene_ratio=2.1) is True
        assert sum(_hex_zu_rgb(e["vorschlag"])) < sum(_hex_zu_rgb(erster))

    def test_rundenzaehler_waechst(self):
        e = self._entscheidung()
        verschaerfe(e, 2.1)
        assert e["runden"] == 2

    def test_ausgereizte_farbe_meldet_ehrlich_fehlschlag(self):
        """Ist Schwarz erreicht, hilft kein weiteres Nachlegen."""
        e = self._entscheidung()
        for _ in range(12):
            if not verschaerfe(e, 1.05):
                break
        assert verschaerfe(e, 1.05) is False

    def test_unsinnige_messung_aendert_nichts(self):
        e = self._entscheidung()
        vorher = e["vorschlag"]
        assert verschaerfe(e, 0.0) is False
        assert e["vorschlag"] == vorher

    def test_schon_gute_messung_verschaerft_nicht_ins_bodenlose(self):
        """Knapp verfehlt heisst kleiner Nachschlag, nicht Schwarz."""
        e = self._entscheidung()
        verschaerfe(e, 4.4)
        assert e["vorschlag"] != "#000000"


class TestCssRobustheit:
    def test_je_selektor_eine_regel(self):
        """
        Kommagetrennte Selektoren sind ein Risiko: ist einer ungueltig,
        verwirft der Browser die ganze Regel. axe-Selektoren stammen aus
        fremden Seiten — ein Ausreisser darf nicht alles mitreissen.
        """
        e = baue_kontrast_entscheidungen([
            _knoten("#a86100", "#edebe5", 4.02, ".a"),
            _knoten("#a86100", "#edebe5", 4.02, ".b"),
        ])
        css = als_css(e)
        assert css.count("color:") == 2
        assert ",\n" not in css


class TestManifestFormat:
    def test_regeln_haben_das_format_des_manifests(self):
        """`a11y_remediation.js` erwartet {selector, declarations} — sonst nichts."""
        from compliance_engine.kontrast_fixes import als_css_regeln
        e = baue_kontrast_entscheidungen([
            _knoten("#a86100", "#edebe5", 4.02, ".a"),
            _knoten("#a86100", "#edebe5", 4.02, ".b"),
        ])
        regeln = als_css_regeln(e)
        assert len(regeln) == 2
        assert set(regeln[0]) == {"selector", "declarations"}
        assert regeln[0]["declarations"].startswith("color: #")
        assert "!important" in regeln[0]["declarations"]

    def test_unbestaetigtes_wird_nicht_ausgeliefert(self):
        """
        Was die Nachmessung im Browser nicht bestanden hat, geht nicht raus —
        sonst waere die Zusage "verifiziert" nur ein Wort.
        """
        from compliance_engine.kontrast_fixes import als_css_regeln
        e = baue_kontrast_entscheidungen([_knoten("#a86100", "#edebe5", 4.02, ".a")])
        e[0]["bestaetigt"] = False
        assert als_css_regeln(e) == []

    def test_bestaetigtes_wird_ausgeliefert(self):
        from compliance_engine.kontrast_fixes import als_css_regeln
        e = baue_kontrast_entscheidungen([_knoten("#a86100", "#edebe5", 4.02, ".a")])
        e[0]["bestaetigt"] = True
        assert len(als_css_regeln(e)) == 1
