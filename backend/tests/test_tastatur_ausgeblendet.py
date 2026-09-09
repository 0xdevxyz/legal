"""
tabindex="-1" ist nur dort ein Mangel, wo das Element auch angeboten wird.

Der Tastatur-Check meldete jedes <a>, <button>, <input>, <select> und
<textarea> mit tabindex="-1" als "nicht per Tastatur erreichbar". Fuer
ausgeblendete Elemente ist das genau verkehrt: ein Honeypot-Feld — ein
Formularfeld, das nur Bots ausfuellen sollen — wird bewusst mit aria-hidden
versehen und aus dem Sichtfeld geschoben; tabindex="-1" gehoert dann dazu und
ist die konforme Loesung, nicht der Verstoss.

Auf complyo.de selbst waren am 08.09.2026 beide Befunde der Saeule
Barrierefreiheit genau solche Honeypot-Felder (das Wartelisten-Formular steht
zweimal auf der Startseite).
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.barrierefreiheit_check import _check_keyboard_navigation


def pruefe(html: str):
    soup = BeautifulSoup(f"<html><body>{html}</body></html>", "html.parser")
    return asyncio.run(_check_keyboard_navigation(soup))


HONEYPOT = (
    '<div class="absolute left-[-9999px]" aria-hidden="true">'
    '<label for="website">Website</label>'
    '<input id="website" type="text" tabindex="-1" autocomplete="off">'
    "</div>"
)


class TestAusgeblendetesIstKeinMangel:
    def test_honeypot_wird_nicht_gemeldet(self):
        assert pruefe(HONEYPOT) == []

    def test_zwei_honeypots_bleiben_zwei_nicht_befunde(self):
        assert pruefe(HONEYPOT + HONEYPOT) == []

    @pytest.mark.parametrize("html", [
        '<button tabindex="-1" disabled>Senden</button>',
        '<input type="hidden" tabindex="-1" name="token">',
        '<a tabindex="-1">Kein href, also ohnehin nicht fokussierbar</a>',
        '<div aria-hidden="true"><button tabindex="-1">Deko</button></div>',
        '<button tabindex="-1" style="display:none">Versteckt</button>',
        '<div style="position:absolute;left:-9999px"><input tabindex="-1"></div>',
    ])
    def test_der_nutzung_entzogene_elemente(self, html):
        assert pruefe(html) == []


class TestEchteFallenBleibenBefund:
    def test_sichtbarer_button_ohne_tabreihenfolge(self):
        befunde = pruefe('<button tabindex="-1" id="kaufen">Jetzt kaufen</button>')
        assert len(befunde) == 1
        assert befunde[0].severity == "warning"

    def test_die_fundstelle_steht_im_befund(self):
        befunde = pruefe('<button tabindex="-1" id="kaufen">Jetzt kaufen</button>')
        # Ohne Fundstelle ist der Befund nicht nachpruefbar.
        assert 'id="kaufen"' in befunde[0].description

    def test_zaehlung_stimmt_wenn_beides_vorkommt(self):
        befunde = pruefe(HONEYPOT + '<a href="/x" tabindex="-1">Link</a>')
        assert len(befunde) == 1
        assert befunde[0].title.startswith("1 ")
