"""
Tests für die deterministischen Erkennungs-Heuristiken (v4.0):
- Soft-404-Guard: HTTP 200 ohne valide Pflichttext-Inhalte zählt NICHT als gefunden.
- Tracking-Erkennung: GTM/inline/Third-Party werden als Tracking erkannt.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bs4 import BeautifulSoup

from compliance_engine.checks.impressum_check import _looks_like_impressum
from compliance_engine.checks.datenschutz_check import _looks_like_datenschutz
from compliance_engine.checks.cookie_check import check_cookie_compliance


class TestSoft404Impressum:
    def test_real_impressum_passes(self):
        text = """Impressum. Angaben gemäß § 5 DDG. Mustermann GmbH,
                  Musterstraße 1, 12345 Berlin. E-Mail: info@example.de"""
        assert _looks_like_impressum(text) is True

    def test_catch_all_marketing_page_rejected(self):
        # Soft-404: Seite liefert 200, ist aber inhaltlich kein Impressum.
        text = "Willkommen auf unserer Startseite! Jetzt günstig Pakete versenden."
        assert _looks_like_impressum(text) is False

    def test_keyword_without_mandatory_field_rejected(self):
        text = "Impressum"  # nur Überschrift, keine Adresse/E-Mail
        assert _looks_like_impressum(text) is False


class TestSoft404Datenschutz:
    def test_real_privacy_policy_passes(self):
        text = """Datenschutzerklärung. Verantwortlicher im Sinne der DSGVO.
                  Rechtsgrundlage Art. 6. Ihre Betroffenenrechte und die Speicherdauer."""
        assert _looks_like_datenschutz(text) is True

    def test_catch_all_rejected(self):
        text = "Unsere Spedition bringt Ihre Ware sicher ans Ziel."
        assert _looks_like_datenschutz(text) is False


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestTrackingDetection:
    def test_gtm_inline_triggers_cookie_critical(self):
        # GTM ohne Banner → Cookie-Säule muss kritisch werden (kein Freifahrtschein).
        html = """<html><head>
            <script>(function(w,d){w.dataLayer=w.dataLayer||[];})(window,document);</script>
            <script src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXX"></script>
            </head><body>Inhalt</body></html>"""
        soup = BeautifulSoup(html, 'html.parser')
        issues = _run(check_cookie_compliance("https://example.de", soup, None))
        severities = {i['severity'] for i in issues}
        assert 'critical' in severities

    def test_no_scripts_no_critical(self):
        # Wirklich statische Seite ohne Scripts/Embeds → kein kritisches Cookie-Issue.
        html = "<html><head></head><body><h1>Hallo</h1></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        issues = _run(check_cookie_compliance("https://example.de", soup, None))
        severities = {i['severity'] for i in issues}
        assert 'critical' not in severities
