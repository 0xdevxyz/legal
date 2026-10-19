"""
Waechter: Plattform-Standardpaletten sind keine Markenfarben.

Befund 19.10.2026: „Farben von der Website uebernehmen" lieferte fuer
spedition-mahn.de #abb8c3/#f78da7 (WordPress-Presets cyan-bluish-gray und
pale-pink), fuer zua-zwickau.de dasselbe. WordPress schreibt seine zwoelf
Preset-Farben als --wp--preset--color--* in jede Seite, der Extraktor wertete
CSS-Variablen mit Gewicht 5 und uebernahm sie als Marke. Die echte Farbe
(spedition-mahn.de: Gelb #f2d500 aus dem Theme-Customizer-Block) verlor.

Gefiltert wird nach Wert, damit eigene Paletten eines Themes unter demselben
Variablennamen weiter zaehlen.
"""
import os
import sys

import pytest

_BACKEND = os.path.abspath(
    os.getenv("COMPLYO_BACKEND_SRC")
    or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _BACKEND)

from bs4 import BeautifulSoup  # noqa: E402

from website_crawler import WebsiteCrawler  # noqa: E402

WP_PRESETS = """
<style id="global-styles-inline-css">
:root{--wp--preset--color--black: #000000;--wp--preset--color--cyan-bluish-gray: #abb8c3;
--wp--preset--color--white: #ffffff;--wp--preset--color--pale-pink: #f78da7;
--wp--preset--color--vivid-red: #cf2e2e;--wp--preset--color--luminous-vivid-orange: #ff6900;
--wp--preset--color--luminous-vivid-amber: #fcb900;--wp--preset--color--light-green-cyan: #7bdcb5;
--wp--preset--color--vivid-green-cyan: #00d084;--wp--preset--color--pale-cyan-blue: #8ed1fc;
--wp--preset--color--vivid-cyan-blue: #0693e3;--wp--preset--color--vivid-purple: #9b51e0;}
:root :where(.wp-element-button){background-color: #32373c;color: #fff;}
</style>
"""


def _farben(html: str):
    return WebsiteCrawler().extract_brand_colors(BeautifulSoup(html, "html.parser"), html)


class TestPlattformpalette:
    def test_wordpress_seite_liefert_die_theme_farbe_nicht_die_presets(self):
        html = f"""<html><head>{WP_PRESETS}
        <style id="logistica-style-inline-css">
        .site-header a:hover{{color:#f2d500}} .button{{background:#f2d500}} .accent{{border-color:#f2d500}}
        .button:hover{{background:#eded00}} body{{color:#222222;background:#ffffff}}
        </style></head><body><a href="/">Spedition</a></body></html>"""
        r = _farben(html)
        assert r["primary_color"] == "#f2d500", r
        assert r["accent_color"] == "#eded00", r
        assert not set(r["raw_candidates"]) & {"#abb8c3", "#f78da7", "#cf2e2e", "#32373c"}, r
        # Schwarz aus der WP-Palette bleibt erlaubt (neutral), Text und Hintergrund wie bisher.
        assert r["text_color"] in {"#000000", "#222222"} and r["bg_color"] == "#ffffff", r

    def test_wordpress_seite_ohne_eigene_farben_meldet_nicht_gescrapt(self):
        """Nur Presets, keine Kundenfarbe: lieber Standardvorschlag als Rosa."""
        html = f"<html><head>{WP_PRESETS}</head><body><p>Hallo</p></body></html>"
        r = _farben(html)
        assert r["scraped"] is False, r
        assert r["primary_color"] == "#7c3aed", r

    def test_eigene_variablen_zaehlen_weiter(self):
        """Nicht-WordPress-Seite mit eigener Variable: Verhalten unveraendert."""
        html = """<html><head><style>:root{--primary-color:#1d4ed8;--accent-color:#1e40af}</style>
        </head><body><header style="background:#1d4ed8">x</header></body></html>"""
        r = _farben(html)
        assert r["primary_color"] == "#1d4ed8" and r["accent_color"] == "#1e40af", r

    def test_eigene_theme_palette_unter_wp_variablennamen_bleibt_erlaubt(self):
        """Block-Themes tragen ihre Marke als --wp--preset--color--primary mit eigenem Wert."""
        html = """<html><head><style id="global-styles-inline-css">
        :root{--wp--preset--color--primary: #0a5c36;--wp--preset--color--contrast: #111111;}
        </style></head><body></body></html>"""
        r = _farben(html)
        assert r["primary_color"] == "#0a5c36", r

    def test_elementor_kit_standard_zaehlt_nicht(self):
        html = """<html><head><style>:root{--e-global-color-primary:#6EC1E4;--e-global-color-accent:#61CE70;
        --e-global-color-secondary:#54595F;--e-global-color-text:#7A7A7A}</style>
        <style>.btn{background:#c8102e}</style></head><body></body></html>"""
        r = _farben(html)
        assert r["primary_color"] == "#c8102e", r
        assert "#6ec1e4" not in r["raw_candidates"], r
