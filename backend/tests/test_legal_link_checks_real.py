"""
Echte Import-Tests gegen die PRODUKTIONS-Erkennung fuer Impressum/Datenschutz.

Ersetzt die Aussagekraft der frueheren Schein-Tests (test_impressum.py /
test_datenschutz.py), die BeautifulSoup-Logik im Test nachbauten statt die echten
Check-Funktionen zu importieren. Hier werden die realen Funktionen aus
compliance_engine/checks/*_check.py geprueft.
"""

from bs4 import BeautifulSoup

from compliance_engine.checks.impressum_check import (
    _find_impressum_links,
    _looks_like_impressum,
)
from compliance_engine.checks.datenschutz_check import (
    _find_datenschutz_links,
    _looks_like_datenschutz,
)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


# ---------------- Impressum: Link-Erkennung ----------------

def test_impressum_link_by_href():
    links = _find_impressum_links(_soup('<a href="/impressum">Impressum</a>'))
    assert len(links) == 1


def test_impressum_link_by_text_keyword():
    links = _find_impressum_links(_soup('<a href="/x">Rechtliche Hinweise</a>'))
    assert len(links) == 1


def test_impressum_link_by_aria_label():
    links = _find_impressum_links(_soup('<a href="/x" aria-label="Impressum"></a>'))
    assert len(links) == 1


def test_no_impressum_link_on_unrelated_nav():
    links = _find_impressum_links(
        _soup('<a href="/">Start</a><a href="/blog">Blog</a>')
    )
    assert links == []


# ---------------- Impressum: Soft-404-Inhalts-Heuristik ----------------

def test_looks_like_impressum_keyword_plus_email():
    assert _looks_like_impressum("Impressum — Kontakt: info@firma.de") is True


def test_looks_like_impressum_keyword_plus_plz_address():
    assert _looks_like_impressum("Impressum\nMusterweg 1\n04109 Leipzig") is True


def test_not_impressum_keyword_without_pflichtmerkmal():
    # Keyword vorhanden, aber weder E-Mail noch PLZ-Adresse -> Soft-404-Schutz
    assert _looks_like_impressum("Impressum kommt bald.") is False


def test_not_impressum_empty():
    assert _looks_like_impressum("") is False


# ---------------- Datenschutz: Link-Erkennung ----------------

def test_datenschutz_link_by_href():
    links = _find_datenschutz_links(_soup('<a href="/datenschutz">Datenschutz</a>'))
    assert len(links) == 1


def test_datenschutz_link_by_text_privacy_policy():
    links = _find_datenschutz_links(_soup('<a href="/p">Privacy Policy</a>'))
    assert len(links) == 1


def test_no_datenschutz_link_on_unrelated_nav():
    assert _find_datenschutz_links(_soup('<a href="/kontakt">Kontakt</a>')) == []


# ---------------- Datenschutz: Soft-404-Inhalts-Heuristik ----------------

def test_looks_like_datenschutz_keyword_plus_two_markers():
    text = (
        "Datenschutzerklärung. Verantwortlich im Sinne der DSGVO. "
        "Wir verarbeiten personenbezogene Daten auf Rechtsgrundlage Art. 6."
    )
    assert _looks_like_datenschutz(text) is True


def test_not_datenschutz_keyword_only():
    assert _looks_like_datenschutz("Datenschutz ist uns wichtig.") is False


def test_not_datenschutz_empty():
    assert _looks_like_datenschutz("") is False
