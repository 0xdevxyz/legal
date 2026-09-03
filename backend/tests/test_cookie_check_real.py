"""
Echte Import-Tests fuer die Cookie-Kernheuristiken (Produktionscode):
- _assess_dark_pattern (Groessen-/Farb-/Schrift-Vergleich Accept vs Reject)
- consent_render_needed (Muss die Seite fuer echte Banner-Pruefung gerendert werden?)

Frueher wurde die Cookie-Erkennung nur ueber im-Test-nachgebaute Logik geprueft.
"""

from bs4 import BeautifulSoup

from compliance_engine.checks.cookie_check import (
    _assess_dark_pattern,
    consent_render_needed,
)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


# ---------------- Dark-Pattern ----------------

def test_dark_pattern_flagged_when_reject_tiny_and_unstyled():
    buttons = [
        {"text": "Alle akzeptieren", "w": 200, "h": 50, "bg": "rgb(0,120,0)", "fontSize": "16px"},
        {"text": "Ablehnen", "w": 80, "h": 20, "bg": "transparent", "fontSize": "12px"},
    ]
    findings = _assess_dark_pattern(buttons)
    assert findings, "kleiner, unauffaelliger Ablehnen-Button muss als Dark Pattern erkannt werden"


def test_no_dark_pattern_when_buttons_equal():
    buttons = [
        {"text": "Akzeptieren", "w": 120, "h": 40, "bg": "rgb(0,0,0)", "fontSize": "14px"},
        {"text": "Ablehnen", "w": 120, "h": 40, "bg": "rgb(0,0,0)", "fontSize": "14px"},
    ]
    assert _assess_dark_pattern(buttons) == []


def test_no_dark_pattern_without_reject_button():
    # Kein Reject vorhanden -> _assess meldet nichts (wird an anderer Stelle behandelt)
    buttons = [{"text": "Alle akzeptieren", "w": 200, "h": 50, "bg": "rgb(0,120,0)", "fontSize": "16px"}]
    assert _assess_dark_pattern(buttons) == []


def test_dark_pattern_empty_input():
    assert _assess_dark_pattern([]) == []


# ---------------- consent_render_needed ----------------

def test_render_needed_for_known_cmp_script():
    soup = _soup('<html><head><script src="https://consent.cookiebot.com/uc.js"></script></head></html>')
    assert consent_render_needed(soup) is True


def test_render_needed_for_custom_banner_loader():
    soup = _soup('<html><head><script src="/assets/cookie-banner.js"></script></head></html>')
    assert consent_render_needed(soup) is True


def test_render_not_needed_for_plain_page():
    soup = _soup('<html><body><h1>Willkommen</h1><p>Kein Banner hier.</p></body></html>')
    assert consent_render_needed(soup) is False
