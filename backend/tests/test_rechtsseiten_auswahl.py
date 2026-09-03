"""
Auswahl der zu pruefenden Rechtsseite.

Die Checks nahmen den ERSTEN Link, dessen Adresse ein Stichwort enthielt. Auf
complyo.de ist das die Produktseite /dsgvo-website-check/ — die eigentliche
Erklaerung unter /datenschutz/ wurde nie geoeffnet, und der Check meldete alle
sechs DSGVO-Pflichtangaben als fehlend. Kandidaten werden jetzt bewertet.
"""

import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.datenschutz_check import _find_datenschutz_links
from compliance_engine.checks.impressum_check import _find_impressum_links


SEITE_MIT_WERBELINKS = """
<html><body>
  <nav>
    <a href="/dsgvo-website-check/">DSGVO Website Check jetzt kostenlos starten</a>
    <a href="/leistungen/datenschutz-beratung/">Datenschutz-Beratung</a>
    <a href="/blog/dsgvo-bussgelder/">DSGVO-Bussgelder im Ueberblick</a>
    <a href="/impressum-generator/">Impressum-Generator testen</a>
  </nav>
  <main><p>Inhalt</p></main>
  <footer>
    <a href="/impressum/">Impressum</a>
    <a href="/datenschutz/">Datenschutz</a>
    <a href="/agb/">AGB</a>
  </footer>
</body></html>
"""


@pytest.fixture(scope="module")
def suppe():
    return BeautifulSoup(SEITE_MIT_WERBELINKS, 'html.parser')


class TestDatenschutzseite:
    def test_erklaerung_schlaegt_produktseite(self, suppe):
        bester = _find_datenschutz_links(suppe)[0]
        assert bester.get('href') == '/datenschutz/', (
            f"geprueft wuerde {bester.get('href')} statt der Datenschutzerklaerung"
        )

    def test_produktseiten_bleiben_hinten(self, suppe):
        adressen = [a.get('href') for a in _find_datenschutz_links(suppe)]
        assert adressen.index('/datenschutz/') < adressen.index('/dsgvo-website-check/')
        assert adressen.index('/datenschutz/') < adressen.index('/blog/dsgvo-bussgelder/')


class TestImpressumsseite:
    def test_impressum_schlaegt_generator(self, suppe):
        bester = _find_impressum_links(suppe)[0]
        assert bester.get('href') == '/impressum/', (
            f"geprueft wuerde {bester.get('href')} statt des Impressums"
        )


class TestOhneFooter:
    """Ohne Footer darf die Bewertung trotzdem die richtige Seite waehlen."""

    NUR_NAVIGATION = """
    <html><body><nav>
      <a href="/service/datenschutz-check/">Datenschutz-Check</a>
      <a href="/datenschutzerklaerung">Datenschutzerklaerung</a>
    </nav></body></html>
    """

    def test_genauer_pfad_gewinnt(self):
        suppe = BeautifulSoup(self.NUR_NAVIGATION, 'html.parser')
        assert _find_datenschutz_links(suppe)[0].get('href') == '/datenschutzerklaerung'


class TestKeineKandidaten:
    def test_leere_liste_bleibt_leer(self):
        suppe = BeautifulSoup("<html><body><a href='/kontakt'>Kontakt</a></body></html>",
                              'html.parser')
        assert _find_datenschutz_links(suppe) == []
        assert _find_impressum_links(suppe) == []
