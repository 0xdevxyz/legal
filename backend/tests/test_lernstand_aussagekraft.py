"""Eine Quote entsteht je Befundtyp, nicht über alle zusammen.

Beim ersten Lauf gegen echte Daten meldete der Lernstand
`aussagekraeftig: True` bei 42 Entscheidungen — während jede einzelne Zeile
`belege_reichen: False` sagte, weil keine Art für sich auch nur 24 erreichte.
Die Gesamtmarke summierte über sechs verschiedene Verfahren.

Dreißig Entscheidungen aus sechs Verfahren sagen über keines davon etwas.
"""

import datetime as dt
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lernstand as ls
from tests.test_lernstand import FakeConn, FakePool, zeile


@pytest.mark.asyncio
class TestAussagekraft:
    async def test_summe_ueber_viele_typen_ist_nicht_aussagekraeftig(self):
        """Der konkrete Fall vom 04.09.: 42 Entscheidungen, kein Typ ueber 24."""
        conn = FakeConn({
            "accessibility_alt_text_fixes": [zeile(vor=24, an=23, offen=1)],
            "accessibility_document_fixes": [
                zeile(typ="skip-link", vor=6, an=6),
                zeile(typ="landmark-main", vor=6, an=6),
                zeile(typ="struktur", vor=4, an=4),
                zeile(typ="css-rule", vor=2, an=2),
            ],
        })
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["entscheidungen_gesamt"] == 41
        assert d["aussagekraeftig"] is False, "Summe ueber Typen zaehlt nicht"
        assert d["typen_mit_belegen"] == []

    async def test_ein_typ_mit_genug_belegen_reicht(self):
        conn = FakeConn({"accessibility_alt_text_fixes": [zeile(vor=40, an=31, ab=9)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["aussagekraeftig"] is True
        assert d["typen_mit_belegen"] == ["bild-ohne-alt-text"]

    async def test_knapp_darunter_reicht_nicht(self):
        """Gegenprobe an der Schwelle."""
        conn = FakeConn({"accessibility_alt_text_fixes":
                         [zeile(vor=40, an=ls.BELEGE_MINDESTENS - 1, ab=0)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["aussagekraeftig"] is False


@pytest.mark.asyncio
class TestAblehnungen:
    async def test_ohne_ablehnung_wird_das_vermerkt(self):
        """Ohne eine einzige Ablehnung ist jede Quote 100 % — daraus laesst
        sich nichts lernen."""
        conn = FakeConn({"accessibility_alt_text_fixes": [zeile(vor=40, an=40)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["ablehnungen_gesamt"] == 0
        assert d["ablehnungen_vorhanden"] is False
        # ... und zwar auch dann, wenn die Belege sonst reichen wuerden.
        assert d["aussagekraeftig"] is True

    async def test_mit_ablehnungen_umgekehrt(self):
        conn = FakeConn({"accessibility_alt_text_fixes": [zeile(vor=40, an=31, ab=9)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["ablehnungen_gesamt"] == 9
        assert d["ablehnungen_vorhanden"] is True
