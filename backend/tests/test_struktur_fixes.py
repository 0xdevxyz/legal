"""
Tests für die Struktur-Reparatur.

Der heikelste Fix im ganzen Modul ist `role="main"`. Er ist unsichtbar: sitzt
er falsch, sieht die Seite genauso aus wie vorher und behauptet trotzdem eine
Struktur, die nicht stimmt — ein Screenreader-Nutzer springt dann in die
Kopfzeile statt in den Inhalt. Deshalb stehen hier die Ablehnungsgründe unter
Test, nicht nur die Erfolgsfälle.

Der erste Messlauf über die 24 echten Seiten hat genau die Fehler produziert,
gegen die diese Tests jetzt sichern: `elementor-location-header` als
Hauptinhalt, und `#reviews` / `#kontakt` / `#behandlung` — je ein Abschnitt
unter vielen.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.struktur_fixes import (  # noqa: E402
    HAUPTINHALT_JS, baue_struktur_css, baue_struktur_fixes, iframe_titel,
    viewport_reparieren,
)


class TestViewport:
    def test_zoomsperre_wird_entfernt(self):
        """Echter Wert von einer der gemessenen Seiten."""
        neu = viewport_reparieren("width=device-width,initial-scale=1,maximum-scale=1")
        assert neu == "width=device-width, initial-scale=1"

    def test_user_scalable_no_wird_entfernt(self):
        neu = viewport_reparieren("width=device-width, initial-scale=1, user-scalable=no")
        assert "user-scalable" not in neu
        assert "width=device-width" in neu

    def test_erlaubter_zoom_bleibt_unangetastet(self):
        """Nichts anfassen, wo nichts kaputt ist."""
        assert viewport_reparieren("width=device-width, initial-scale=1") is None
        assert viewport_reparieren("width=device-width, maximum-scale=5") is None

    def test_maximum_scale_ab_zwei_ist_in_ordnung(self):
        """WCAG 1.4.4 verlangt 200 % — genau 2 reicht."""
        assert viewport_reparieren("width=device-width, maximum-scale=2") is None
        assert viewport_reparieren("width=device-width, maximum-scale=1.5") is not None

    def test_kaputter_wert_gilt_als_sperre(self):
        assert viewport_reparieren("maximum-scale=abc, width=device-width") is not None

    def test_leerer_wert(self):
        assert viewport_reparieren("") is None


class TestIframeTitel:
    def test_bekannte_quellen_werden_benannt(self):
        """Echte Fundstelle: die Karte auf doener-bistro-baku.de."""
        assert iframe_titel("https://www.google.com/maps?q=Döner+Bistro") == "Karte von Google Maps"
        assert iframe_titel("https://www.youtube.com/embed/xyz") == "Video von YouTube"
        assert iframe_titel("https://player.vimeo.com/video/1") == "Video von Vimeo"

    def test_unbekannte_quelle_nennt_wenigstens_den_host(self):
        assert iframe_titel("https://buchung.example.de/x") == "Eingebetteter Inhalt von buchung.example.de"

    def test_ohne_quelle_kein_titel(self):
        """"Eingebetteter Inhalt" allein waere formal ein Titel und wertlos."""
        assert iframe_titel("") is None
        assert iframe_titel("about:blank") is None


class TestFixeBauen:
    def _node(self, html="", target=".x"):
        return {"html": html, "target": [target]}

    def test_haupt_selektor_wird_zu_role_main(self):
        fixes = baue_struktur_fixes({"region": [self._node()]}, "#page")
        assert fixes[0] == {
            "selector": "#page", "attribut": "role", "wert": "main",
            "regel": "region", "begruendung": fixes[0]["begruendung"],
        }

    def test_ohne_haupt_selektor_kein_role_main(self):
        """Kein Ziel heisst kein Fix — nicht irgendein Ziel."""
        fixes = baue_struktur_fixes({"region": [self._node()]}, None)
        assert not [f for f in fixes if f["attribut"] == "role"]

    def test_viewport_fix_aus_echtem_markup(self):
        node = self._node(
            '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">'
        )
        fixes = baue_struktur_fixes({"meta-viewport": [node]}, None)
        assert fixes[0]["selector"] == "meta[name=viewport]"
        assert "maximum-scale" not in fixes[0]["wert"]

    def test_frame_ohne_erkennbare_quelle_bekommt_keinen_titel(self):
        node = self._node('<iframe src=""></iframe>', "iframe")
        assert baue_struktur_fixes({"frame-title": [node]}, None) == []

    def test_scrollbereich_wird_tastaturerreichbar(self):
        node = self._node('<div class="reviews-scroll">', ".reviews-scroll")
        fixes = baue_struktur_fixes({"scrollable-region-focusable": [node]}, None)
        assert fixes[0]["attribut"] == "tabindex" and fixes[0]["wert"] == "0"

    def test_jeder_fix_traegt_eine_begruendung(self):
        """Was am Kunden-Markup gedreht wird, muss sich erklaeren lassen."""
        fixes = baue_struktur_fixes({
            "region": [self._node()],
            "scrollable-region-focusable": [self._node(target=".s")],
        }, "#page")
        assert all(f.get("begruendung") for f in fixes)


class TestCss:
    def test_link_im_fliesstext_wird_unterstrichen(self):
        """WCAG 1.4.1: Farbe allein darf einen Link nicht kenntlich machen."""
        regeln = baue_struktur_css({
            "link-in-text-block": [{"target": ["a.mehr"], "html": "<a>Mehr Infos</a>"}]
        })
        assert regeln == [{"selector": "a.mehr",
                           "declarations": "text-decoration: underline !important;"}]

    def test_ohne_befund_kein_css(self):
        assert baue_struktur_css({}) == []


class TestSchutzregelnImBrowsercode:
    """
    Die Ablehnungsgründe stehen im JavaScript, weil sie den gerenderten Baum
    brauchen. Hier wird geprüft, dass sie noch drinstehen — sie sind der
    Unterschied zwischen einem richtigen und einem falschen `main`.
    """

    def test_randbereiche_sind_ausgeschlossen(self):
        for wort in ("header", "footer", "nav", "sidebar", "banner"):
            assert wort in HAUPTINHALT_JS

    def test_mehrheitsregel_ist_vorhanden(self):
        """Ein Abschnitt unter vielen ist nicht der Hauptinhalt."""
        assert "drin * 2 < elemente.length" in HAUPTINHALT_JS

    def test_body_taugt_nicht_als_main(self):
        assert "ziel === document.body" in HAUPTINHALT_JS

    def test_vorhandene_rollen_werden_nicht_ueberschrieben(self):
        assert "getAttribute('role')" in HAUPTINHALT_JS
