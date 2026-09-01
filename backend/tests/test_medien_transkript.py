"""
Transkript-Erkennung beim Medien-Check.

Ein Transkript galt nur dann als vorhanden, wenn es als Link auf eine andere
Seite lag. Steht der Volltext direkt unter dem Video — die bessere Loesung,
weil niemand die Seite verlassen muss — sah der Check ihn nicht und meldete
"Video ohne Transkript-Link". Wer es richtig machte, bekam den Befund trotzdem.

Die Erkennung darf aber nicht auf eine blosse Ueberschrift hereinfallen: "Hier
kommt bald das Transkript" ist keines.
"""

import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.media_accessibility_check import MediaAccessibilityChecker


VOLLTEXT = (
    'Datenschutz, Cookie-Banner, Barrierefreiheit – wer blickt da noch durch? '
    'Jede Woche neue Pflichten, und auf der eigenen Website sammeln sich still '
    'die Warnzeichen, während der Laden laufen soll. Hinter dem Chaos stecken '
    'genau vier Säulen: Barrierefreiheit für alle Besucher, Datenschutz, saubere '
    'Cookie-Einwilligung und rechtssichere Texte vom Impressum bis zum Widerruf.'
)


def seite(inneres: str) -> BeautifulSoup:
    return BeautifulSoup(
        f'<html><body><div class="karte">'
        f'<video src="/film.mp4"></video>{inneres}'
        f'</div></body></html>',
        'html.parser',
    )


@pytest.fixture(scope="module")
def pruefer():
    return MediaAccessibilityChecker()


class TestTranskriptWirdErkannt:
    def test_volltext_in_details(self, pruefer):
        suppe = seite(f'<details><summary>Transkript anzeigen</summary><p>{VOLLTEXT}</p></details>')
        video = suppe.find('video')
        assert pruefer._has_nearby_transcript(video, suppe)

    def test_volltext_in_abschnitt_mit_ueberschrift(self, pruefer):
        suppe = seite(f'<section><h3>Transkript</h3><p>{VOLLTEXT}</p></section>')
        video = suppe.find('video')
        assert pruefer._has_nearby_transcript(video, suppe)

    def test_link_zaehlt_weiterhin(self, pruefer):
        suppe = seite('<a href="/transkript/">Zum Transkript</a>')
        video = suppe.find('video')
        assert pruefer._has_nearby_transcript(video, suppe)

    def test_aria_describedby_zaehlt_weiterhin(self, pruefer):
        suppe = BeautifulSoup(
            f'<html><body><video src="/film.mp4" aria-describedby="tx"></video>'
            f'<div id="tx">{VOLLTEXT}</div></body></html>',
            'html.parser',
        )
        assert pruefer._has_nearby_transcript(suppe.find('video'), suppe)


class TestKeinFalschesTranskript:
    def test_ueberschrift_ohne_text_zaehlt_nicht(self, pruefer):
        suppe = seite('<details><summary>Transkript folgt in Kürze</summary></details>')
        video = suppe.find('video')
        assert not pruefer._has_nearby_transcript(video, suppe), (
            'eine Ankuendigung ist kein Transkript'
        )

    def test_langer_text_ohne_kennzeichnung_zaehlt_nicht(self, pruefer):
        suppe = seite(f'<section><h3>Über uns</h3><p>{VOLLTEXT}</p></section>')
        video = suppe.find('video')
        assert not pruefer._has_nearby_transcript(video, suppe), (
            'irgendein langer Text neben dem Video ist kein Transkript'
        )

    def test_leere_seite(self, pruefer):
        suppe = seite('')
        assert not pruefer._has_nearby_transcript(suppe.find('video'), suppe)


class TestAudiodeskription:
    """Liegt eine Textalternative vor, ist WCAG 1.2.3 (Level A) erfuellt.
    Offen bleibt 1.2.5 (Level AA) — der Befund muss das unterscheiden, statt
    beides als denselben Mangel zu melden."""

    def _befunde(self, pruefer, suppe):
        return pruefer._check_video_elements('https://example.test', suppe)

    def test_mit_transkript_wird_der_befund_zum_hinweis(self, pruefer):
        suppe = seite(f'<details><summary>Transkript</summary><p>{VOLLTEXT}</p></details>')
        befunde = self._befunde(pruefer, suppe)
        audio = [b for b in befunde if 'Audiodeskription' in b.title]
        assert audio, 'der Punkt darf nicht verschwinden, nur weil ein Transkript da ist'
        assert audio[0].severity == 'info', f'erwartet info, ist {audio[0].severity}'
        assert audio[0].wcag_criteria == ['1.2.5'], (
            f'1.2.3 ist mit der Textalternative erfuellt: {audio[0].wcag_criteria}'
        )

    def test_ohne_transkript_bleibt_es_eine_warnung(self, pruefer):
        suppe = seite('')
        befunde = self._befunde(pruefer, suppe)
        audio = [b for b in befunde if 'Audiodeskription' in b.title]
        assert audio and audio[0].severity == 'warning'
        assert '1.2.3' in audio[0].wcag_criteria
