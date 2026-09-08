"""
Ein Anmeldeformular ist kein Cookie-Banner.

Zwei Fehler wirkten hier zusammen und trafen jede Tailwind-Seite:

1. Der Attribut-Blob eines Knopfes enthaelt seine CSS-Klassen. Tailwind
   schreibt den deaktivierten Zustand als `disabled:cursor-not-allowed` — darin
   steckt "allowed", und das Muster fuer Zustimmungs-Knoepfe suchte nach
   "allow". Jeder Knopf mit dieser Standardklasse galt damit als
   "Alle akzeptieren".
2. Der Banner-Kontext liess das blosse Wort "datenschutz" genuegen. Jedes
   Anmelde- und Kontaktformular verlinkt die Datenschutzerklaerung.

Zusammen machten sie aus dem Wartelisten-Formular auf complyo.de einen
Consent-Banner. Die Dark-Pattern-Pruefung lief anschliessend auf einem
Anmeldeformular — und meldete dort einen fehlenden Ablehnen-Knopf.
"""

import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.cookie_check import (
    _classify_consent_buttons,
    _find_consent_container,
)


def suppe(html: str) -> BeautifulSoup:
    return BeautifulSoup(f"<html><body>{html}</body></html>", "html.parser")


# Das Formular von complyo.de, verkuerzt auf die tragenden Teile.
WARTELISTE = """
<div class="bg-white rounded-2xl border p-6">
  <form>
    <label for="mail">E-Mail-Adresse</label>
    <input id="mail" type="email" name="email">
    <button class="inline-flex bg-akzent-400 disabled:cursor-not-allowed">Platz sichern</button>
    <p>Ich bin einverstanden, dass complyo meine E-Mail-Adresse speichert.
       Widerruf jederzeit. Näheres in der
       <a class="underline" href="/datenschutz">Datenschutzerklärung</a>.</p>
  </form>
</div>
"""

ECHTER_BANNER = """
<div class="complyo-cookie-banner">
  <p>Wir verwenden Cookies, um unsere Website zu verbessern.</p>
  <div class="complyo-actions">
    <button class="disabled:cursor-not-allowed">Alle akzeptieren</button>
    <button>Nur essenzielle Cookies akzeptieren</button>
    <button>Individuelle Datenschutzeinstellungen</button>
  </div>
</div>
"""

NUR_AKZEPTIEREN = """
<div class="cookie-hinweis">
  <p>Diese Seite verwendet Cookies.</p>
  <button>Alle akzeptieren</button>
</div>
"""


class TestTailwindKlasseIstKeineZustimmung:
    def test_cursor_not_allowed_macht_keinen_akzeptieren_knopf(self):
        el = suppe('<div class="cookie">'
                   '<button class="disabled:cursor-not-allowed">Absenden</button></div>')
        assert _classify_consent_buttons(el.find("div"))["accept"] is False

    def test_echter_akzeptieren_knopf_wird_weiter_erkannt(self):
        el = suppe('<div class="cookie"><button class="btn-allow-all">OK</button></div>')
        assert _classify_consent_buttons(el.find("div"))["accept"] is True

    def test_akzeptieren_ueber_den_text_bleibt_erkannt(self):
        el = suppe('<div class="cookie">'
                   '<button class="disabled:cursor-not-allowed">Alle akzeptieren</button></div>')
        assert _classify_consent_buttons(el.find("div"))["accept"] is True


class TestFormulareSindKeineBanner:
    def test_warteliste_wird_nicht_als_banner_gelesen(self):
        assert _find_consent_container(suppe(WARTELISTE)) is None

    def test_kontaktformular_wird_nicht_als_banner_gelesen(self):
        html = """
        <div class="kontakt">
          <p>Ihre Daten verarbeiten wir nach unserer Datenschutzerklärung.</p>
          <textarea name="nachricht"></textarea>
          <button class="disabled:cursor-not-allowed">Nachricht senden</button>
        </div>
        """
        assert _find_consent_container(suppe(html)) is None

    def test_blosser_footer_link_ist_kein_banner(self):
        html = '<div class="footer"><a href="/cookie-richtlinie">Cookie-Richtlinie</a></div>'
        assert _find_consent_container(suppe(html)) is None


class TestEchteBannerWerdenWeiterGefunden:
    def test_banner_mit_ablehnen_knopf(self):
        el = _find_consent_container(suppe(ECHTER_BANNER))
        assert el is not None
        klassen = _classify_consent_buttons(el)
        assert klassen["accept"] is True
        # "Nur essenzielle Cookies akzeptieren" IST der Ablehnen-Knopf.
        assert klassen["reject"] is True

    def test_banner_ohne_ablehnen_knopf_bleibt_auffindbar(self):
        el = _find_consent_container(suppe(NUR_AKZEPTIEREN))
        assert el is not None
        assert _classify_consent_buttons(el)["reject"] is False

    def test_kategorie_schalter_stoeren_nicht(self):
        html = """
        <div class="cookie-consent">
          <p>Einwilligung in Cookies</p>
          <input type="checkbox" name="analytics">
          <button>Alle akzeptieren</button>
          <button>Ablehnen</button>
        </div>
        """
        assert _find_consent_container(suppe(html)) is not None
