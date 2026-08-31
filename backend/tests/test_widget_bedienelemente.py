"""
Beschriftung der Bedienelemente in den eigenen Widgets.

Das Barrierefreiheits-Widget erzeugte vier WCAG-Verstoesse gegen genau das,
wofuer es da ist: die vier Schieberegler (Schriftgroesse, Zeilenhoehe,
Buchstaben-, Wortabstand) hatten ein <label> ohne for-Attribut, das den Regler
auch nicht umschloss — fuer Screenreader also gar keine Beschriftung. Weil das
Widget auf jeder Kundenseite laeuft, stand der Verstoss ueberall, und auf
complyo.de nullte er die Saeule Barrierefreiheit.

Ein placeholder zaehlt nicht als Beschriftung (WCAG 3.3.2).
"""

import os
import re

import pytest

WIDGETS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'widgets')
)


def _lies(name: str) -> str:
    with open(os.path.join(WIDGETS, name), encoding='utf-8') as f:
        return f.read()


def _bedienelemente(quelltext: str):
    """Alle <input>-Tags als Rohtext."""
    return re.findall(r'<input\b[^>]*>', quelltext, re.IGNORECASE | re.DOTALL)


def _ist_beschriftet(tag: str, quelltext: str) -> bool:
    """aria-label, aria-labelledby oder ein <label for="..."> mit passender id."""
    if re.search(r'aria-label(?:ledby)?\s*=\s*["\'][^"\']+["\']', tag):
        return True
    treffer = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', tag)
    if not treffer:
        return False
    kennung = treffer.group(1)
    # Template-Platzhalter lassen sich statisch nicht aufloesen
    if '${' in kennung:
        return True
    return bool(re.search(
        r'<label[^>]*\bfor\s*=\s*["\']' + re.escape(kennung) + r'["\']', quelltext
    ))


class TestBarrierefreiheitsWidget:
    QUELLE = 'accessibility-v6.js'

    @pytest.mark.parametrize("regler", [
        "fontSize", "lineHeight", "letterSpacing", "wordSpacing",
    ])
    def test_regler_ist_beschriftet(self, regler):
        quelltext = _lies(self.QUELLE)
        tags = [t for t in _bedienelemente(quelltext) if f'{regler}-slider' in t]
        assert tags, f"Regler {regler}-slider nicht gefunden"
        assert _ist_beschriftet(tags[0], quelltext), (
            f"{regler}-slider hat keine Beschriftung, die ein Screenreader vorliest"
        )

    def test_kein_bedienelement_ohne_beschriftung(self):
        quelltext = _lies(self.QUELLE)
        ohne = [t for t in _bedienelemente(quelltext)
                if not _ist_beschriftet(t, quelltext)]
        assert not ohne, f"unbeschriftete Bedienelemente: {ohne}"


class TestCookieBanner:
    QUELLE = 'cookie_banner_v2.js'

    def test_kein_bedienelement_ohne_beschriftung(self):
        quelltext = _lies(self.QUELLE)
        ohne = [t for t in _bedienelemente(quelltext)
                if not _ist_beschriftet(t, quelltext)]
        assert not ohne, f"unbeschriftete Bedienelemente: {ohne}"

    def test_platzhalter_gilt_nicht_als_beschriftung(self):
        """Sicherung der Pruefregel selbst."""
        tag = '<input type="text" id="such" placeholder="Suchen...">'
        assert not _ist_beschriftet(tag, tag)
