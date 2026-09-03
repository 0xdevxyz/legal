"""
Tests fuer die Link-Beschriftungen.

Alle Beispiele sind echte Fundstellen aus der Messung vom 06.08.2026 ueber 24
deutsche KMU-Websites — kein einziger konstruierter Fall. Was hier gruen ist,
ist an echtem Markup gruen.

Die wichtigste Zusage steht in TestNichtsErfinden: wo sich nichts ableiten
laesst, kommt kein Vorschlag. Ein falscher Linkname ist schlimmer als ein
fehlender, weil der Nutzer ihm folgt.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.linkname_fixes import (  # noqa: E402
    baue_linkname_vorschlaege, beschriftung_fuer, slug_zu_text,
)


def _n(html, selektor=".x"):
    return {"html": html, "target": [selektor]}


class TestEchteFundstellen:
    def test_social_icon_ohne_text(self):
        """boehme.it: Facebook-Link, komplett leer."""
        r = beschriftung_fuer(
            '<a href="https://www.facebook.com/Boehme.It" '
            'class="social color-light facebook" target="_blank"></a>'
        )
        assert r["label"].startswith("Facebook")
        assert "neuem Fenster" in r["label"]

    def test_twitter_und_instagram(self):
        """fv-wolkenburg.de: drei Icon-Links im Footer."""
        for url, name in (("https://twitter.com/fvwolkenburg", "Twitter"),
                          ("https://instagram.com/fvwolkenburg", "Instagram")):
            r = beschriftung_fuer(f'<a href="{url}" class="btIconWidget"><div></div></a>')
            assert r["label"] == name

    def test_zurueck_nach_oben(self):
        """Genau dieses Markup steht auf bauschlosserei-claus.de."""
        r = beschriftung_fuer('<a id="back_to_top" href="#" class="off"><span></span></a>')
        assert r["label"] == "Nach oben"

    def test_suche_als_icon(self):
        r = beschriftung_fuer(
            '<a href="javascript:void(0)" class="dt-search-icon">'
            '<span class="fa fa-search"></span></a>'
        )
        assert r["label"] == "Suchen"

    def test_schliessen_kreuz(self):
        assert beschriftung_fuer('<a href="#"><i class="fa fa-times"></i></a>')["label"] == "Schließen"

    def test_mobiles_menue_schliessen_ist_spezifischer(self):
        """Muster-Reihenfolge: das spezifischere gewinnt."""
        r = beschriftung_fuer('<a id="btn-close-mobile-menu" href="javascript:;"></a>')
        assert r["label"] == "Menü schließen"

    def test_elementor_popup(self):
        r = beschriftung_fuer(
            '<a class="elementor-icon" href="#elementor-action%3Aaction%3Dpopup%3Aopen"></a>'
        )
        assert r["label"] == "Dialog öffnen"

    def test_pdf_wird_als_dokument_angesagt(self):
        """Ein Nutzer sollte wissen, dass ein PDF aufgeht."""
        r = beschriftung_fuer(
            '<a href="https://www.selectline.de/data/uploads/2015/11/'
            'Leistungsbeschreibung.pdf" target="_blank"><img src="x.png"></a>'
        )
        assert "PDF" in r["label"]
        assert "Leistungsbeschreibung" in r["label"]

    def test_lightbox_bild_nutzt_alt_text(self):
        """spedition-mahn.de: 12 Lightbox-Links auf vier Bilder."""
        r = beschriftung_fuer(
            '<a class="qodef-popup-item" itemprop="image" '
            'href="https://spedition-mahn.de/wp-content/uploads/2026/03/'
            'Z-LO-80-bus-scaled-1.jpg" data-type="image"></a>',
            alt_texte={"z-lo-80-bus-scaled-1.jpg": "Gelber Volvo-Sattelzug der Spedition"},
        )
        assert r["label"] == "Bild vergrößern: Gelber Volvo-Sattelzug der Spedition"

    def test_artikel_link_aus_dem_slug(self):
        """fv-wolkenburg.de: neun Vorschaubild-Links, Titel steckt in der URL."""
        r = beschriftung_fuer(
            '<a href="https://fv-wolkenburg.de/'
            'starke-aufholjagd-des-fv-wolkenburg-rettet-punkteteilung/" '
            'style="display:block"></a>'
        )
        # Grossschreibung ist eine Naeherung: ohne Wortarten laesst sich
        # deutsche Rechtschreibung nicht ableiten. Deshalb Konfidenz 0.5 und
        # menschliche Freigabe — der Titel muss lesbar sein, nicht perfekt.
        assert r["label"] == "Starke Aufholjagd des FV Wolkenburg Rettet Punkteteilung"
        assert r["konfidenz"] <= 0.5

    def test_interner_bereich_aus_dem_slug(self):
        """container-spindler.de: sechsmal derselbe Icon-Link."""
        r = beschriftung_fuer(
            '<a href="/container-uebersicht/" class="kl-iconbox__link">'
            '<span class="mouse-anim-icon"></span></a>'
        )
        assert r["label"] == "Container Uebersicht"

    def test_logo_link_auf_startseite(self):
        r = beschriftung_fuer('<a href="https://naturheilpraxis-decker.de"></a>')
        assert r["label"] == "Startseite"

    def test_nbsp_link_aus_dem_slug(self):
        r = beschriftung_fuer('<a href="/ich-mochte-ein-angebot-anfordern">&nbsp;</a>')
        assert "Angebot" in r["label"]


class TestQuellenrangfolge:
    def test_title_schlaegt_alles(self):
        r = beschriftung_fuer(
            '<a title="Zu unseren Öffnungszeiten" href="https://facebook.com/x"></a>'
        )
        assert r["label"] == "Zu unseren Öffnungszeiten"
        assert r["quelle"] == "title-Attribut"

    def test_alt_text_schlaegt_muster(self):
        r = beschriftung_fuer(
            '<a href="/suche/" class="search"><img src="lupe.png" alt="Suche starten"></a>'
        )
        assert r["label"] == "Suche starten"

    def test_seitentitel_schlaegt_slug(self):
        r = beschriftung_fuer(
            '<a href="/leistungen/"></a>',
            seiten_titel={"/leistungen/": "Unsere Leistungen im Überblick"},
        )
        assert r["label"] == "Unsere Leistungen im Überblick"
        assert r["quelle"] == "Seitentitel"

    def test_slug_bekommt_niedrige_konfidenz(self):
        """Der Notnagel muss als solcher erkennbar sein."""
        r = beschriftung_fuer('<a href="/irgendein-bereich/"></a>')
        assert r["konfidenz"] <= 0.5

    def test_tel_und_mailto(self):
        assert "0371" in beschriftung_fuer('<a href="tel:0371123456"></a>')["label"]
        r = beschriftung_fuer('<a href="mailto:info@beispiel.de?subject=Hallo"></a>')
        assert r["label"] == "E-Mail schreiben an info@beispiel.de"


class TestNichtsErfinden:
    def test_leerer_anker_bekommt_keinen_vorschlag(self):
        """`href="#"` ohne jeden Hinweis: liegenlassen, nicht raten."""
        assert beschriftung_fuer('<a href="#" target="_blank" '
                                 'class="bt_bb_icon_holder"></a>') is None

    def test_ohne_href_kein_vorschlag(self):
        assert beschriftung_fuer("<a></a>") is None

    def test_leeres_html_kein_vorschlag(self):
        assert beschriftung_fuer("") is None

    def test_zu_kurzer_slug_zaehlt_nicht(self):
        assert beschriftung_fuer('<a href="/ab"></a>') is None


class TestSlugZuText:
    def test_bindestriche_werden_woerter(self):
        assert slug_zu_text("container-uebersicht") == "Container Uebersicht"

    def test_fuellwoerter_bleiben_klein(self):
        assert slug_zu_text("das-team-und-die-praxis") == "Das Team und die Praxis"

    def test_kurze_konsonantenfolgen_gelten_als_abkuerzung(self):
        assert "FV" in slug_zu_text("sieg-des-fv-wolkenburg")

    def test_dateiendung_faellt_weg(self):
        assert slug_zu_text("leistungsbeschreibung.pdf") == "Leistungsbeschreibung"

    def test_prozentkodierung_wird_aufgeloest(self):
        assert slug_zu_text("gr%C3%BCne-energie") == "Grüne Energie"

    def test_leerer_slug(self):
        assert slug_zu_text("") == ""


class TestGruppierung:
    def test_gleiches_ziel_wird_zusammengefasst(self):
        """Sechs Icon-Links auf /container-uebersicht/ sind eine Entscheidung."""
        nodes = [_n('<a href="/container-uebersicht/" class="kl-iconbox__link">'
                    '<span class="mouse-anim-icon"></span></a>', f".s{i}")
                 for i in range(6)]
        v = baue_linkname_vorschlaege(nodes)
        assert len(v) == 1
        assert v[0]["stellen"] == 6
        assert len(v[0]["selektoren"]) == 6

    def test_sichere_vorschlaege_stehen_oben(self):
        v = baue_linkname_vorschlaege([
            _n('<a href="/irgendein-bereich/"></a>', ".a"),
            _n('<a href="https://facebook.com/x"></a>', ".b"),
        ])
        assert v[0]["quelle"] == "Plattform"

    def test_unableitbares_taucht_nicht_auf(self):
        v = baue_linkname_vorschlaege([
            _n('<a href="#" class="bt_bb_icon_holder"></a>', ".a"),
            _n('<a href="https://facebook.com/x"></a>', ".b"),
        ])
        assert len(v) == 1


class TestSchaltflaechen:
    def test_such_button_ohne_href(self):
        """
        physiomueller.de: `<button class="gensearch__submit glyphicon-search">`.
        Schaltflaechen haben kein href — die Musterpruefung lief frueher erst
        danach und liess genau diesen Fall fallen.
        """
        r = beschriftung_fuer(
            '<button type="submit" id="searchsubmit" value="go" '
            'class="gensearch__submit glyphicon glyphicon-search"></button>'
        )
        assert r["label"] == "Suchen"

    def test_value_als_letzte_quelle(self):
        r = beschriftung_fuer('<button type="submit" value="Anfrage senden"></button>')
        assert r["label"] == "Anfrage senden"

    def test_nichtssagendes_value_zaehlt_nicht(self):
        assert beschriftung_fuer('<button type="submit" value="go"></button>') is None
