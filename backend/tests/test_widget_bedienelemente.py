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


class TestKachelnSindSchalter:
    """Die neunzehn Kacheln des Bedienfelds muessen Schalter sein, keine Kisten.

    Bis zum 18.09.2026 waren sie <div data-feature="..."> mit einer
    Klickbehandlung: kein role, kein tabindex, keine Taste. Mit der Tastatur
    allein war das Barrierefreiheits-Widget nicht bedienbar, ein Screenreader
    las Text statt Schaltern. Es lief so auf sechs Kundenseiten.

    Warum das so lange unbemerkt blieb: axe kann ein <div> mit Klickbehandlung
    nicht als Bedienelement erkennen, es gibt nichts zu pruefen. Gemeldet wurde
    nur die Folge - ein scrollbarer Bereich ohne irgendetwas Fokussierbares.
    Ein Waechter auf der Quelle ist deshalb hier nicht die zweitbeste Loesung,
    sondern die einzige, die den Fall direkt benennt.
    """

    QUELLE = 'accessibility-v6.js'

    def test_kacheln_bekommen_rolle_und_fokus(self):
        q = _lies(self.QUELLE)
        assert "tile.setAttribute('role', 'button')" in q, (
            "Die Kacheln tragen keine Rolle mehr - ein Screenreader liest "
            "wieder Text statt Schalter."
        )
        assert "tile.setAttribute('tabindex', '0')" in q, (
            "Die Kacheln sind nicht mehr fokussierbar - mit der Tastatur "
            "allein ist das Widget dann unbedienbar."
        )

    def test_kacheln_hoeren_auf_die_tastatur(self):
        q = _lies(self.QUELLE)
        assert "tile.addEventListener('keydown'" in q, (
            "Kein keydown auf den Kacheln: fokussierbar, aber nicht "
            "ausloesbar ist keine Bedienbarkeit."
        )
        stelle = q[q.index("tile.addEventListener('keydown'"):][:400]
        for taste in ("'Enter'", "' '"):
            assert taste in stelle, f"Taste {taste} loest die Kachel nicht aus"
        assert "preventDefault" in stelle, (
            "Ohne preventDefault scrollt die Leertaste die Seite, statt die "
            "Kachel zu schalten."
        )

    def test_zustand_steht_im_markup(self):
        q = _lies(self.QUELLE)
        assert "aria-pressed" in q, "Der Schaltzustand wird nicht angesagt"
        assert "aria-haspopup" in q, (
            "Die vier Kacheln mit Schiebereglern oeffnen einen Dialog, sie "
            "sind keine Schalter - das muss im Markup stehen."
        )
