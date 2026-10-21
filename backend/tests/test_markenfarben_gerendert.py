"""
Markenfarben aus der gerenderten Seite.

Befund 21.10.2026: "Farben von Website auslesen" lag meist daneben. Der
Quelltext-Extraktor zaehlt, wie oft eine Farbe im CSS steht; Themes fuehren
ganze Paletten, die Marke steht in einer Regel. Jetzt zaehlt, was der Browser
rendert: Knoepfe, Kopfbereich, grosse Flaechen, Links, Ueberschriften.

Die Bewertung ist ohne Browser testbar (bewerte_farbproben). Der Browserlauf
ist ein eigener Test, der ohne Chromium uebersprungen wird; lokal ohne
"playwright install" hilft COMPLYO_CHROMIUM=/pfad/zu/chromium.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.markenfarben_gerendert import (  # noqa: E402
    PLAYWRIGHT_VERFUEGBAR, bewerte_farbproben, markenfarben_aus_seite,
)


def _probe(rolle, farbe, flaeche=0):
    return {'rolle': rolle, 'farbe': farbe, 'flaeche': flaeche, 'tag': 'div'}


class TestBewertung:
    def test_knopffarbe_schlaegt_haeufige_linkfarbe(self):
        proben = (
            [_probe('knopf', 'rgb(242, 213, 0)')] * 3            # gelbe Knoepfe
            + [_probe('link', 'rgb(29, 78, 216)')] * 8           # viele blaue Links
            + [_probe('seite', 'rgb(255, 255, 255)', 1_000_000)]
            + [_probe('text', 'rgb(34, 34, 34)')]
        )
        r = bewerte_farbproben(proben)
        assert r['primary_color'] == '#f2d500'
        assert r['accent_color'] == '#1d4ed8'
        assert r['bg_color'] == '#ffffff' and r['text_color'] == '#222222'
        assert r['scraped'] is True and r['quelle'] == 'gerendert'

    def test_grau_und_durchsichtig_zaehlen_nicht(self):
        proben = [
            _probe('knopf', 'rgb(68, 68, 68)'),           # grauer Knopf
            _probe('knopf', 'rgba(0, 0, 0, 0)'),           # durchsichtig
            _probe('knopf', 'rgba(220, 38, 38, 0.2)'),     # fast durchsichtig
            _probe('kopf', 'transparent'),
        ]
        assert bewerte_farbproben(proben) is None

    def test_plattform_standardknopf_ist_keine_marke(self):
        proben = [_probe('knopf', 'rgb(50, 55, 60)')] * 4 + [_probe('kopf', 'rgb(10, 92, 54)')]
        r = bewerte_farbproben(proben, ausgeschlossen=frozenset({'#32373c'}))
        assert r['primary_color'] == '#0a5c36'

    def test_ohne_zweite_farbe_wird_der_akzent_abgedunkelt(self):
        r = bewerte_farbproben([_probe('knopf', 'rgb(29, 78, 216)')])
        assert r['primary_color'] == '#1d4ed8'
        assert r['accent_color'] != '#1d4ed8'
        assert r['accent_color'].startswith('#')

    def test_aehnliche_zweite_farbe_ist_kein_akzent(self):
        # Zwei Blautoene, kaum unterscheidbar: der Akzent wird abgeleitet,
        # nicht der fast gleiche Nachbar genommen.
        r = bewerte_farbproben([_probe('knopf', 'rgb(29, 78, 216)')] * 2 + [_probe('link', 'rgb(30, 80, 220)')])
        assert r['accent_color'] not in ('#1d4ed8', '#1e50dc')

    def test_leere_proben(self):
        assert bewerte_farbproben([]) is None


SEITE = """
<html><head><style>
:root { --wp--preset--color--vivid-red: #cf2e2e; --wp--preset--color--pale-pink: #f78da7; }
body { margin: 0; background: #fff; color: #222; font-family: sans-serif; }
header { background: #0a5c36; height: 80px; }
.wp-block-button__link { background: #f2d500; color: #111; padding: 12px 24px; display: inline-block; }
a { color: #0a5c36; }
.alert { background: #cf2e2e; color: #fff; width: 10px; height: 10px; }
#cookie-banner { position: fixed; bottom: 0; left: 0; right: 0; background: #1d4ed8; padding: 20px; }
#cookie-banner button { background: #2563eb; color: #fff; }
</style></head><body>
<header><a href="/">Logo</a></header>
<main>
  <h1>Willkommen</h1>
  <p><a href="/leistungen">Leistungen</a> und <a href="/kontakt">Kontakt</a></p>
  <a class="wp-block-button__link" href="/anfrage">Anfrage senden</a>
  <a class="wp-block-button__link" href="/termin">Termin</a>
  <span class="alert"></span>
</main>
<div id="cookie-banner"><button>Alle akzeptieren</button><button>Ablehnen</button></div>
</body></html>
"""


@pytest.mark.skipif(not PLAYWRIGHT_VERFUEGBAR, reason="Playwright fehlt")
def test_browserlauf_nimmt_knopf_und_kopf_und_ignoriert_den_fremden_banner():
    from playwright.async_api import async_playwright

    async def lauf():
        async with async_playwright() as pw:
            start = {}
            if os.getenv('COMPLYO_CHROMIUM'):
                start['executable_path'] = os.getenv('COMPLYO_CHROMIUM')
            try:
                browser = await pw.chromium.launch(headless=True, args=['--no-sandbox'], **start)
            except Exception as e:  # kein Browser installiert
                pytest.skip(f"Chromium nicht startbar: {e}")
            try:
                page = await browser.new_page(viewport={'width': 1280, 'height': 900})
                await page.set_content(SEITE)
                return await markenfarben_aus_seite(page, frozenset({'#32373c'}))
            finally:
                await browser.close()

    r = asyncio.run(lauf())
    assert r is not None
    assert r['primary_color'] == '#f2d500', r      # die beiden Knoepfe
    assert r['accent_color'] == '#0a5c36', r       # Kopfbereich und Links
    assert '#1d4ed8' not in r['raw_candidates'], r  # fremder Cookie-Banner
    assert '#2563eb' not in r['raw_candidates'], r  # dessen Knoepfe
    assert r['bg_color'] == '#ffffff' and r['text_color'] == '#222222'
