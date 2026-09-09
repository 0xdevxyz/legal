"""
Vier Befundarten aus dem Bestandsdurchlauf vom 09.09.2026.

Gemessen wurde über 24 echte deutsche KMU-Websites, ausgewertet nach Häufigkeit
je Befundart. Wo eine Pflicht auf fast allen Seiten gleichzeitig gerissen wird,
liegt der Fehler in der Prüfung, nicht im Bestand.

    Fehlende semantische HTML-Elemente        20/24  ─┐ ein Mangel,
    N Landmark-Regions fehlen                 19/24   ├ vier Befunde,
    Inhalte außerhalb von Landmark-Bereichen  18/24   │ vier Risikobeiträge
    Kein <main>-Bereich vorhanden             11/24  ─┘
    Barrierefreiheitserklärung fehlt (BFSG)   19/24    Anwendungsbereich ungeprüft
    Kundenbewertungen ohne Disclosure (UWG)   15/24    CSS-Klassen als Bewertung
    Hinweis: Kein Assistenz-Widget gefunden   16/24    Eigenwerbung im Bericht
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.barrierefreiheit_check import (
    _bfsg_anwendungsbereich,
    _ist_heuristischer_strukturhinweis,
    _merge_axe_into_heuristic,
    hat_assistenz_widget,
)
from compliance_engine.checks.uwg_check import check_uwg_compliance


def suppe(html: str) -> BeautifulSoup:
    return BeautifulSoup(f"<html><body>{html}</body></html>", "html.parser")


# ---------------------------------------------------------------------------
# 1. Ein Mangel, ein Befund
# ---------------------------------------------------------------------------

class TestLandmarkBlaehung:
    def test_strukturhinweise_werden_erkannt(self):
        for titel in ("Fehlende semantische HTML-Elemente",
                      "3 Landmark-Regions fehlen",
                      "1 Landmark-Regions fehlen",
                      "Keine H1-Überschrift gefunden"):
            assert _ist_heuristischer_strukturhinweis({"title": titel}), titel

    def test_echte_befunde_bleiben(self):
        for titel in ("WCAG 1.1.1: Bild ohne Alt-Text",
                      "Zu geringer Farbkontrast",
                      "Formularfeld ohne Label",
                      "Überschriftenebenen springen"):
            assert not _ist_heuristischer_strukturhinweis({"title": titel}), titel

    def test_axe_verdraengt_den_heuristischen_hinweis(self):
        heuristik = [
            {"title": "Fehlende semantische HTML-Elemente", "category": "barrierefreiheit",
             "legal_basis": "BFSG §12, WCAG 2.1 (1.3.1, Info and Relationships)"},
            {"title": "3 Landmark-Regions fehlen", "category": "barrierefreiheit",
             "legal_basis": "WCAG 2.1 (1.3.1), BFSG §12"},
            {"title": "WCAG 1.1.1: Bild ohne Alt-Text", "category": "barrierefreiheit",
             "legal_basis": "WCAG 2.1 (1.1.1)"},
        ]
        axe = [{"title": "Kein <main>-Bereich vorhanden", "category": "barrierefreiheit",
                "metadata": {"wcag_criteria": ["1.3.1"], "axe_rule_id": "landmark-one-main"}}]

        zusammen = _merge_axe_into_heuristic(heuristik, axe)
        titel = [i["title"] for i in zusammen]

        assert "Fehlende semantische HTML-Elemente" not in titel
        assert "3 Landmark-Regions fehlen" not in titel
        assert "Kein <main>-Bereich vorhanden" in titel, "axe muss den Mangel melden"
        assert "WCAG 1.1.1: Bild ohne Alt-Text" in titel, "fremde Befunde bleiben"

    def test_axe_landmark_verdraengt_den_aria_befund(self):
        from compliance_engine.checks.barrierefreiheit_check import _axe_merkmale
        # Die axe-Regel `region` traegt keine wcag-Tags — die Entdopplung muss
        # deshalb ueber die Merkmalskennung laufen, nicht ueber das Kriterium.
        axe_region = {"title": "Inhalte außerhalb von Landmark-Bereichen",
                      "metadata": {"feature_id": "LANDMARKS", "axe_rule_id": "region",
                                   "wcag_criteria": []}}
        assert "LANDMARKS" in _axe_merkmale([axe_region])
        assert _axe_merkmale([{"title": "x", "metadata": {}}]) == set()

    def test_ohne_axe_bleibt_der_hinweis(self):
        # _merge_axe_into_heuristic wird nur aufgerufen, wenn axe lief. Ohne axe
        # ist der heuristische Hinweis die einzige Quelle und muss bleiben.
        heuristik = [{"title": "Fehlende semantische HTML-Elemente",
                      "category": "barrierefreiheit",
                      "legal_basis": "BFSG §12, WCAG 2.1 (1.3.1, Info and Relationships)"}]
        assert _ist_heuristischer_strukturhinweis(heuristik[0]) is True
        # kein Merge-Aufruf => Befund bleibt in der Liste
        assert len(heuristik) == 1


# ---------------------------------------------------------------------------
# 2. BFSG nur, wo es gilt
# ---------------------------------------------------------------------------

class TestBfsgAnwendungsbereich:
    @pytest.mark.parametrize("html", [
        '<button>In den Warenkorb</button>',
        '<a href="/checkout">Zur Kasse</a>',
        '<button>Jetzt kostenpflichtig bestellen</button>',
        '<a href="/termin">Termin buchen</a>',
        '<a href="/konto">Mein Konto</a>',
    ])
    def test_b2c_dienst_wird_erkannt(self, html):
        assert _bfsg_anwendungsbereich(suppe(html)) is True

    @pytest.mark.parametrize("html", [
        '<h1>Bauschlosserei Claus</h1><p>Tore, Geländer, Reparaturen.</p>',
        '<h1>Zahnarztpraxis Mittweida</h1><p>Sprechzeiten: Mo-Fr 8-18 Uhr.</p>',
        '<h1>Physiotherapie Müller</h1><p>Rufen Sie uns an: 03727 12345</p>',
        '<h1>Tennisclub Limbach</h1><p>Unsere Plätze und Trainingszeiten.</p>',
    ])
    def test_darstellungsseite_ist_nicht_im_anwendungsbereich(self, html):
        assert _bfsg_anwendungsbereich(suppe(html)) is False


# ---------------------------------------------------------------------------
# 3. Bewertungen, nicht Klassennamen
# ---------------------------------------------------------------------------

def uwg(html: str):
    return asyncio.run(check_uwg_compliance("https://beispiel.de", suppe(html)))


def hat_bewertungsbefund(befunde) -> bool:
    return any("Verifikations-Disclosure" in b["title"] for b in befunde)


class TestBewertungserkennung:
    @pytest.mark.parametrize("html", [
        # Das, was die alte Erkennung auf 15 von 24 Seiten ausgeloest hat.
        '<div class="star-rating"></div><p>Willkommen bei der Bauschlosserei.</p>',
        '<div class="wp-block-rating"><span class="stars"></span></div>',
        '<footer><a href="/bewertungen">Bewertungen</a></footer>',
        '<span class="icon">★</span><p>Unsere Leistungen im Überblick.</p>',
        '<script>var reviewSlider = {stars: 5};</script><p>Herzlich willkommen.</p>',
    ])
    def test_markup_allein_ist_keine_bewertung(self, html):
        assert not hat_bewertungsbefund(uwg(html)), html[:50]

    def test_strukturierte_daten_gelten_als_beleg(self):
        html = ('<script type="application/ld+json">'
                '{"@type":"AggregateRating","ratingValue":"4.8"}</script>'
                '<p>Unsere Leistungen.</p>')
        assert hat_bewertungsbefund(uwg(html))

    def test_sichtbare_bewertung_mit_zahl_gilt(self):
        html = ('<section><h2>Kundenbewertungen</h2>'
                '<p>4,8 von 5 Sternen aus 120 Bewertungen</p></section>')
        assert hat_bewertungsbefund(uwg(html))

    def test_bewertung_mit_offenlegung_erzeugt_keinen_befund(self):
        html = ('<section><h2>Kundenbewertungen</h2>'
                '<p>4,8 von 5 Sternen</p>'
                '<p>Alle Bewertungen stammen von verifizierten Käufern.</p></section>')
        assert not hat_bewertungsbefund(uwg(html))


# ---------------------------------------------------------------------------
# 4. Kein Werbeplatz im Prüfbericht
# ---------------------------------------------------------------------------

class TestWidgetIstTatsacheKeinBefund:
    def test_kein_widget_ergibt_False_statt_befund(self):
        assert hat_assistenz_widget(suppe("<p>Eine ganz normale Seite.</p>")) is False

    def test_widget_wird_erkannt(self):
        html = '<script src="https://api.complyo.de/api/widgets/accessibility.js"></script>'
        assert hat_assistenz_widget(suppe(html)) is True

    def test_fremdes_widget_wird_erkannt(self):
        assert hat_assistenz_widget(
            suppe('<script src="https://cdn.userway.org/widget.js"></script>')) is True

    def test_kein_befund_mehr_im_quelltext(self):
        import inspect
        from compliance_engine.checks import barrierefreiheit_check
        quelle = inspect.getsource(barrierefreiheit_check)
        # Auf die Konstruktion pruefen, nicht auf das Wort: die Begruendung,
        # warum der Befund weg ist, steht als Kommentar weiterhin im Quelltext.
        assert "title=Hinweis: Kein Assistenz-Widget gefunden" not in quelle, \
            "Der Hinweis darf nicht mehr als Befund entstehen"
