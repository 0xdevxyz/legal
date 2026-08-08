"""
Zwei Fehler an derselben Zeile der Kontrast-Gruppierung.

Beide sind an gebauten Pruefstuecken aufgefallen, nicht an Kundenseiten — die
24 vermessenen Seiten sind sich zu aehnlich (alle WordPress, alle Elementor),
um so etwas zu zeigen.

1. Shadow DOM brachte die GANZE Kontrastreparatur zum Absturz.
   axe liefert `target` fuer ein Element im Shadow DOM als verschachtelte
   Liste: `[["mein-element", "p"]]`. Der alte Code nahm `target[0]` und legte
   damit eine Liste ab; `sorted(set(...))` warf spaeter
   `TypeError: unhashable type: 'list'`. Weil der Aufrufer fail-open ist, verlor
   die Seite daraufhin JEDE Farbreparatur — nicht nur die eine Fundstelle, und
   ohne dass es jemandem auffiel. Ein einziges Web Component genuegte, und
   Cookie-Banner wie Usercentrics oder Cookiebot benutzen genau das.

2. Der Selektor-Deckel log den Kunden an.
   Bei 50 Selektoren war Schluss, `stellen` zaehlte aber weiter. Eine
   Entscheidung meldete "1500 Stellen"; das erzeugte CSS erreichte 50. Der
   Kunde gab die grosse Zahl frei und bekam die kleine. Gemessen an einem
   Pruefstueck mit 1500 gleichen Absaetzen: 1500 -> 1450.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.kontrast_fixes import (  # noqa: E402
    SELEKTOR_DECKEL, _selektor_aus_ziel, als_css, als_css_regeln,
    baue_kontrast_entscheidungen,
)


def _knoten(target, fg="#aaaaaa", bg="#ffffff"):
    return {
        "target": target,
        "html": "<p>x</p>",
        "any": [{"id": "color-contrast", "data": {
            "fgColor": fg, "bgColor": bg, "contrastRatio": 2.3,
            "fontSize": "16px", "fontWeight": "normal",
            "expectedContrastRatio": "4.5:1",
        }}],
    }


class TestSelektorAusZiel:
    def test_normalfall(self):
        assert _selektor_aus_ziel(["p.text"]) == "p.text"

    def test_shadow_dom_gibt_none(self):
        assert _selektor_aus_ziel([["mein-element", "p.text"]]) is None

    def test_leeres_ziel(self):
        assert _selektor_aus_ziel([]) is None
        assert _selektor_aus_ziel(None) is None

    def test_leere_zeichenkette(self):
        assert _selektor_aus_ziel(["  "]) is None


class TestShadowDomStuerztNichtMehr:
    def test_gemischte_seite_liefert_weiter_css(self):
        """
        Der eigentliche Schaden: eine erreichbare Fundstelle NEBEN einer im
        Shadow DOM. Frueher verlor die Seite dadurch beide.
        """
        e = baue_kontrast_entscheidungen([
            _knoten(["p.normal"]),
            _knoten([["mein-element", "p.innen"]]),
        ])
        css = als_css(e)          # warf frueher TypeError
        regeln = als_css_regeln(e)
        assert "p.normal" in css
        assert len(regeln) == 1

    def test_shadow_stellen_werden_ausgewiesen(self):
        e = baue_kontrast_entscheidungen([
            _knoten(["p.normal"]),
            _knoten([["x-el", "p.a"]]),
            _knoten([["x-el", "p.b"]]),
        ])[0]
        assert e["stellen"] == 3
        assert e["abgedeckt"] == 1
        assert e["im_shadow_dom"] == 2
        assert "Shadow DOM" in e["deckung_hinweis"]

    def test_altbestand_mit_listen_bricht_nicht(self):
        """Entscheidungen aus der Datenbank, vor der Reparatur entstanden."""
        alt = [{"loesbar": True, "vorschlag": "#595959",
                "vordergrund": "#aaaaaa", "hintergrund": "#ffffff",
                "ist_ratio": 2.3, "neue_ratio": 4.5, "stellen": 2,
                "selektoren": ["p.gut", ["x-el", "p.schlecht"]]}]
        assert "p.gut" in als_css(alt)
        assert len(als_css_regeln(alt)) == 1


class TestDeckelIstEhrlich:
    def test_abgedeckt_entspricht_den_selektoren(self):
        e = baue_kontrast_entscheidungen(
            [_knoten([f"p:nth-child({i})"]) for i in range(10)])[0]
        assert e["stellen"] == 10 and e["abgedeckt"] == 10
        assert "deckung_hinweis" not in e

    def test_ueber_dem_deckel_wird_die_luecke_benannt(self):
        n = SELEKTOR_DECKEL + 25
        e = baue_kontrast_entscheidungen(
            [_knoten([f"p:nth-child({i})"]) for i in range(n)])[0]
        assert e["stellen"] == n
        assert e["abgedeckt"] == SELEKTOR_DECKEL
        assert "25" in e["deckung_hinweis"]

    def test_deckel_ist_nicht_wieder_auf_50(self):
        assert SELEKTOR_DECKEL >= 200, \
            "50 war zu niedrig — eine Entscheidung versprach 1500 und lieferte 50"
