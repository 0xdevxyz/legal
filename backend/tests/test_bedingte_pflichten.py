"""
Eine Pflicht wird geprueft, wo sie besteht — nicht auf jeder Seite.

Am 08.09.2026 bewertete complyo.de sich im eigenen Scanner mit 55/100. Neun der
dreizehn Befunde kamen aus deklarativen Pruefungen und betrafen Pflichten, die
fuer die Seite gar nicht gelten: ein Ablehnen-Knopf in einem Cookie-Banner, den
es nicht gibt, ein USA-Hinweis fuer Transfers, die nicht stattfinden, ein
DSA-Transparenzbericht fuer eine Plattform, die es nicht ist.

Zwei Gate-Formen waren die Ursache, und beide sind hier festgenagelt:

  {"always": true}                  laeuft auf jeder Website
  {"keywords_any": ["cookie", ...]} trifft jede Seite, die ueber Cookies
                                    SCHREIBT (ein Footer-Link genuegt)

Die Bedingung gehoert stattdessen in `applies_when.requires` und wird gegen
belegte Tatsachen geprueft. Fehlt der Beleg, laeuft die Pruefung nicht.
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import declarative_check_runner as runner
from compliance_engine import scan_kontext
from compliance_engine.check_spec_rules import gate_entscheidet_nichts


def check(slug: str, applies_when: dict) -> dict:
    """Eine Pruefung, die ein Element verlangt, das auf der Testseite fehlt."""
    return {
        "id": 1,
        "slug": slug,
        "category": "cookie",
        "title": "Ablehnen-Knopf fehlt",
        "description": "Kein Ablehnen-Knopf gefunden.",
        "recommendation": "Ablehnen-Knopf ergaenzen.",
        "legal_basis": "TDDDG § 25",
        "severity": "warning",
        "risk_euro": 5000,
        "applies_when": applies_when,
        "detection": {
            "type": "required_element",
            "html_patterns": [r"<button[^>]*>alle ablehnen"],
            "link_text_keywords": ["alle ablehnen"],
        },
    }


class Registry:
    def __init__(self, checks):
        self._checks = checks

    async def get_active_checks(self, force_refresh=False):
        return self._checks


@pytest.fixture
def seite():
    # Eine gewoehnliche Seite: erwaehnt Cookies im Footer, hat aber weder
    # Banner noch Tracking — der Normalfall bei Kundenseiten.
    return BeautifulSoup(
        "<html><body><p>Willkommen.</p>"
        "<footer><a href='/cookie-richtlinie'>Cookie-Richtlinie</a></footer>"
        "</body></html>",
        "html.parser",
    )


def lauf(checks, seite, kontext):
    runner.declarative_check_registry = Registry(checks)
    try:
        return asyncio.run(
            runner.run_declarative_checks("https://beispiel.de", seite, None, kontext=kontext)
        )
    finally:
        runner.declarative_check_registry = None


class TestGateStaerke:
    def test_bedingungslos_ohne_voraussetzung_ist_kein_gate(self):
        assert gate_entscheidet_nichts({"always": True})
        assert gate_entscheidet_nichts({})

    def test_nur_allerweltswoerter_sind_kein_gate(self):
        grund = gate_entscheidet_nichts(
            {"keywords_any": ["cookie", "einwilligung", "tracking", "analytics"]}
        )
        assert grund and "generisch" in grund

    def test_belegte_tatsache_ist_ein_gate(self):
        assert gate_entscheidet_nichts({"requires": ["consent_banner"]}) is None

    def test_seitentyp_ist_ein_gate(self):
        assert gate_entscheidet_nichts({"site_type": "shop"}) is None

    def test_ein_spezifisches_stichwort_genuegt(self):
        assert gate_entscheidet_nichts({"keywords_any": ["e-zigarette", "verdampfer"]}) is None


class TestRunnerLaesstBedingungsloseChecksAus:
    def test_always_ohne_requires_laeuft_nicht(self, seite):
        befunde = lauf([check("banner-ablehnen", {"always": True})], seite, {})
        assert befunde == [], "eine bedingungslose Pruefung darf keinen Befund erzeugen"

    def test_generisches_stichwortgate_laeuft_nicht(self, seite):
        befunde = lauf(
            [check("banner-usa", {"keywords_any": ["cookie", "einwilligung"]})], seite, {}
        )
        assert befunde == []


class TestVoraussetzungEntscheidet:
    def test_ohne_banner_kein_befund(self, seite):
        befunde = lauf(
            [check("banner-ablehnen", {"requires": ["consent_banner"]})],
            seite,
            {"consent_banner": False},
        )
        assert befunde == []

    def test_mit_banner_wird_geprueft(self, seite):
        befunde = lauf(
            [check("banner-ablehnen", {"requires": ["consent_banner"]})],
            seite,
            {"consent_banner": True},
        )
        assert len(befunde) == 1
        assert befunde[0]["metadata"]["declarative_check_slug"] == "banner-ablehnen"

    def test_alle_voraussetzungen_muessen_zutreffen(self, seite):
        gate = {"requires": ["consent_banner", "drittland_usa"]}
        assert lauf([check("usa", gate)], seite,
                    {"consent_banner": True, "drittland_usa": False}) == []
        assert len(lauf([check("usa", gate)], seite,
                        {"consent_banner": True, "drittland_usa": True})) == 1

    def test_unbekannte_tatsache_erzeugt_keinen_befund(self, seite):
        # Tippfehler oder eine Tatsache, die noch niemand erhebt: nicht pruefen
        # ist die sichere Richtung — ein verpasster Fund ist billiger als ein
        # erfundener.
        befunde = lauf([check("dsa", {"requires": ["plattform_ugc"]})], seite,
                       {"plattform_ugc": False})
        assert befunde == []
        befunde = lauf([check("dsa", {"requires": ["gibt_es_nicht"]})], seite, {})
        assert befunde == []

    def test_ohne_kontext_wird_nichts_behauptet(self, seite):
        # Altpfad ohne Kontext: bedingte Pflichten sind nicht entscheidbar.
        befunde = lauf([check("banner", {"requires": ["consent_banner"]})], seite, None)
        assert befunde == []


class TestKontextErhebung:
    def test_seite_ohne_banner_und_tracker(self, seite):
        fakten = scan_kontext.ermittle(seite, html=str(seite))
        assert fakten["consent_banner"] is False
        assert fakten["consent_tracking"] is False
        assert fakten["drittland_usa"] is False

    def test_tracker_wird_erkannt(self):
        html = ("<html><body><script src='https://www.googletagmanager.com/gtm.js?id=x'>"
                "</script></body></html>")
        fakten = scan_kontext.ermittle(BeautifulSoup(html, "html.parser"), html=html)
        assert fakten["consent_tracking"] is True

    def test_alle_bekannten_fakten_werden_geliefert(self, seite):
        fakten = scan_kontext.ermittle(seite, html=str(seite))
        assert set(fakten) == set(scan_kontext.BEKANNTE_FAKTEN)

    def test_newsletter_formular(self):
        html = ("<html><body><form><label>Newsletter abonnieren</label>"
                "<input type='email' name='mail'></form></body></html>")
        fakten = scan_kontext.ermittle(BeautifulSoup(html, "html.parser"), html=html)
        assert fakten["newsletter_formular"] is True
