"""
Der Verbraucherausschluss steht in den AGB, nicht auf der Startseite.

Die B2B-Erkennung las bis zum 08.09.2026 nur den Text der geladenen Seite.
Die Klarstellung "Vertragsschluss mit Verbrauchern ist ausgeschlossen" steht
aber praktisch nie auf der Startseite, sondern in Ziffer 1 der AGB — auch bei
complyo.de selbst. Die Erkennung konnte deshalb bei kaum einem echten
B2B-Anbieter greifen, und jedes B2B-SaaS-Angebot mit Preisliste bekam einen
kritischen Befund ueber 3.000 EUR fuer eine Widerrufsbelehrung, die es nicht
schuldet.

Der Beleg dagegen lag jedes Mal auf einer Seite, die der Scanner ohnehin
abruft.
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks import shop_check


STARTSEITE = (
    "<html><body>"
    "<h1>Die Compliance-Plattform</h1>"
    "<p>Alle Preise netto zzgl. USt.</p>"
    "<footer><a href='/agb'>AGB</a></footer>"
    "</body></html>"
)

AGB_B2B = (
    "<html><body><h1>AGB</h1>"
    "<p>(3) Unsere Angebote richten sich ausschließlich an Unternehmer im Sinne "
    "des § 14 BGB. Ein Vertragsschluss mit Verbrauchern im Sinne des § 13 BGB "
    "ist ausgeschlossen.</p></body></html>"
)

AGB_VERBRAUCHER = (
    "<html><body><h1>AGB</h1>"
    "<p>Als Verbraucher haben Sie ein Widerrufsrecht von 14 Tagen.</p>"
    "</body></html>"
)


@pytest.fixture
def seite():
    return BeautifulSoup(STARTSEITE, "html.parser")


def lauf(seite, agb_html, monkeypatch):
    async def _text(url, session=None):
        return agb_html

    monkeypatch.setattr(shop_check, "_fetch_page_text", _text)
    return asyncio.run(
        shop_check.erkenne_reines_b2b_mit_agb("https://beispiel.de", seite, None)
    )


class TestAgbWirdMitgelesen:
    def test_klarstellung_nur_in_den_agb_wird_gefunden(self, seite, monkeypatch):
        assert lauf(seite, AGB_B2B, monkeypatch) is True

    def test_startseite_allein_haette_es_uebersehen(self, seite):
        # Der Beleg fuer den Unterschied: dieselbe Startseite, alter Weg.
        assert shop_check.erkenne_reines_b2b(seite) is False

    def test_agb_ohne_klarstellung_bleibt_verbrauchergeschaeft(self, seite, monkeypatch):
        assert lauf(seite, AGB_VERBRAUCHER, monkeypatch) is False

    def test_unerreichbare_agb_kippen_den_check_nicht(self, seite, monkeypatch):
        async def _kaputt(url, session=None):
            raise RuntimeError("Seite nicht erreichbar")

        monkeypatch.setattr(shop_check, "_fetch_page_text", _kaputt)
        ergebnis = asyncio.run(
            shop_check.erkenne_reines_b2b_mit_agb("https://beispiel.de", seite, None)
        )
        # Im Zweifel Verbrauchergeschaeft — das ist die sichere Richtung.
        assert ergebnis is False

    def test_klarstellung_auf_der_startseite_genuegt_weiterhin(self, monkeypatch):
        soup = BeautifulSoup(
            "<html><body><p>Verkauf nicht an Verbraucher.</p></body></html>",
            "html.parser",
        )
        gerufen = []

        async def _text(url, session=None):
            gerufen.append(url)
            return AGB_VERBRAUCHER

        monkeypatch.setattr(shop_check, "_fetch_page_text", _text)
        ergebnis = asyncio.run(
            shop_check.erkenne_reines_b2b_mit_agb("https://beispiel.de", soup, None)
        )
        assert ergebnis is True
        assert gerufen == [], "die AGB brauchte es hier gar nicht"
