"""Eine Empfehlung ist ein Hinweis, kein Mangel.

Vier Stellen im Scanner werteten Empfehlungen wie Rechtspflichten, jede auf
ihre Art, und dieselbe Seite bekam je nach Messweg zwei verschiedene Scores:

* axe_scanner: `ist_rechtspflicht` trennte Empfehlung von Pflicht, die
  Herabstufung griff aber nur fuer 'critical'/'high', Werte, die
  `_impact_to_severity` fuer 'moderate' nie liefert. `region`, `heading-order`,
  `landmark-one-main`, `page-has-heading-one` liefen als Warnung durch.
* Skip-Link-Heuristik: 'info' mit 200 EUR, ob die Seite nun <main> hatte oder
  gar keinen Umgehungsweg. WCAG 2.4.1 verlangt einen Weg, keinen Link.
* Heuristische Zwillinge der axe-Empfehlungen (semantische Elemente, H1,
  Landmark-Regions): 'warning' mit 300 bis 800 EUR, sobald axe nicht lief.
* aria-live-Hinweis aus Klassennamen: 500 EUR fuer etwas, das statisch nicht
  messbar ist.

Gemessen am 16.09.2026 nach der Abschaffung der Update-Hochstufung.
"""

import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.axe_scanner import AxeScanner, AxeScanResult, AxeViolation
from compliance_engine.checks.aria_checker import ARIAChecker
from compliance_engine.checks.barrierefreiheit_check import (
    _check_semantic_html, check_barrierefreiheit_compliance,
)
from compliance_engine.scanner import normalize_severities
from compliance_engine.score_calculator import ScoreCalculator


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _axe(rule, impact, tags):
    return AxeScanResult(
        url="https://example.com", timestamp="t", passes=0, incomplete=0,
        inapplicable=0,
        violations=[AxeViolation(
            id=rule, impact=impact, description="d", help="h", help_url="u",
            tags=tags, nodes=[{"target": [".x"], "html": "<div>"}],
        )],
    )


class _I:
    def __init__(self, d):
        self.category = d["category"]
        self.severity = d["severity"]
        self.title = d["title"]
        self.id = d.get("id", "")
        self.is_missing = d.get("is_missing", False)
        self.risk_euro_min = d.get("risk_euro", 0)


class TestAxeEmpfehlungIstHinweis:
    @pytest.mark.parametrize("rule", ["region", "heading-order",
                                      "landmark-one-main", "page-has-heading-one"])
    def test_moderate_best_practice_ist_info(self, rule):
        """Genau die vier, die als Warnung durchliefen."""
        [issue] = AxeScanner().convert_to_structured_issues(
            _axe(rule, "moderate", ["cat.semantics", "best-practice"]))
        assert issue["severity"] == "info"
        assert issue["risk_euro"] == 0
        assert issue["rechtspflicht"] is False

    def test_serious_best_practice_ist_ebenfalls_info(self):
        [issue] = AxeScanner().convert_to_structured_issues(
            _axe("landmark-unique", "serious", ["cat.semantics", "best-practice"]))
        assert issue["severity"] == "info"

    def test_pflicht_behaelt_ihre_stufe(self):
        """Die Gegenprobe: ein echter WCAG-2.1-AA-Verstoss bleibt, was axe sagt."""
        [issue] = AxeScanner().convert_to_structured_issues(
            _axe("image-alt", "critical", ["cat.text-alternatives", "wcag2a", "wcag111"]))
        assert issue["severity"] == "critical"
        assert issue["risk_euro"] > 0
        [issue] = AxeScanner().convert_to_structured_issues(
            _axe("list", "moderate", ["cat.structure", "wcag2a", "wcag131"]))
        assert issue["severity"] == "warning"

    def test_eine_seite_mit_nur_empfehlungen_hat_volle_punktzahl(self):
        """Ende zu Ende: axe-Befund, Normalisierung, Saeulen-Score."""
        rohe = AxeScanner().convert_to_structured_issues(
            _axe("region", "moderate", ["cat.keyboard", "best-practice"]))
        issues = normalize_severities([_I(d) for d in rohe])
        res = ScoreCalculator.compute_with_status(issues)
        assert res["pillar_scores"]["accessibility"] == 100


OHNE_ALLES = (
    '<html lang="de"><head><title>T</title></head>'
    '<body><div><a href="/leistungen">Leistungen</a></div><p>Text</p></body></html>'
)
MIT_MAIN = (
    '<html lang="de"><head><title>T</title></head>'
    '<body><div><a href="/leistungen">Leistungen</a></div><main><p>Text</p></main></body></html>'
)
MIT_UEBERSCHRIFT = (
    '<html lang="de"><head><title>T</title></head>'
    '<body><div><a href="/leistungen">Leistungen</a></div><h2>Text</h2></body></html>'
)
MIT_SKIP = (
    '<html lang="de"><head><title>T</title></head>'
    '<body><a href="#main">Zum Inhalt springen</a><div><a href="/x">Nav</a></div>'
    '<div id="main"><p>Text</p></div></body></html>'
)


async def _skip_befunde(html):
    issues = await check_barrierefreiheit_compliance("https://example.com", _soup(html))
    return [i for i in issues if "Skip-Navigation-Link" in (i.get("title") or "")]


class TestSkipLinkHeuristik:
    @pytest.mark.asyncio
    async def test_kein_umgehungsweg_ist_ein_verstoss(self):
        [b] = await _skip_befunde(OHNE_ALLES)
        assert b["severity"] == "warning"
        assert b["title"].startswith("WCAG 2.4.1")
        assert b["risk_euro"] == 200

    @pytest.mark.asyncio
    async def test_main_landmark_erfuellt_241(self):
        """ARIA11: ein Landmark ist ein Umgehungsweg. Der Link bleibt Empfehlung."""
        [b] = await _skip_befunde(MIT_MAIN)
        assert b["severity"] == "info"
        assert b["risk_euro"] == 0
        assert "empfohlen" in b["title"]

    @pytest.mark.asyncio
    async def test_ueberschriften_erfuellen_241(self):
        """H69: eine Ueberschriftenstruktur ebenso."""
        [b] = await _skip_befunde(MIT_UEBERSCHRIFT)
        assert b["severity"] == "info"

    @pytest.mark.asyncio
    async def test_vorhandener_skip_link_erzeugt_nichts(self):
        assert await _skip_befunde(MIT_SKIP) == []

    @pytest.mark.asyncio
    async def test_die_reparatur_findet_beide_fassungen(self):
        """Der Post-Scan-Prozessor sucht 'skip' und 'zum inhalt springen' im
        Text; beide Fassungen muessen ihn weiter erreichen."""
        for html in (OHNE_ALLES, MIT_MAIN):
            [b] = await _skip_befunde(html)
            blob = (b["title"] + " " + b["description"] + " " + b["recommendation"]).lower()
            assert "skip" in blob and "zum inhalt springen" in blob


class TestHeuristischeZwillinge:
    @pytest.mark.asyncio
    async def test_fehlende_h1_ist_hinweis(self):
        issues = await _check_semantic_html(_soup(
            "<html><body><main><h2>x</h2></main><nav></nav><header></header><footer></footer></body></html>"))
        [b] = [i for i in issues if i.title == "Keine H1-Überschrift gefunden"]
        assert b.severity == "info"
        assert b.risk_euro == 0

    @pytest.mark.asyncio
    async def test_fehlende_landmarks_sind_hinweis(self):
        issues = await _check_semantic_html(_soup("<html><body><h1>x</h1></body></html>"))
        [b] = [i for i in issues if i.title == "Fehlende semantische HTML-Elemente"]
        assert b.severity == "info"
        assert b.risk_euro == 0

    def test_aria_landmarks_sind_hinweis(self):
        [b] = ARIAChecker()._check_landmarks(_soup("<html><body><p>x</p></body></html>"), "https://x")
        assert b["severity"] == "info"
        assert b["risk_euro"] == 0

    def test_aria_live_hinweis_traegt_kein_risiko(self):
        [b] = ARIAChecker()._check_live_regions(
            _soup('<html><body><div class="message">x</div></body></html>'), "https://x")
        assert b["severity"] == "info"
        assert b["risk_euro"] == 0

    @pytest.mark.asyncio
    async def test_gleicher_score_mit_und_ohne_axe(self):
        """Der eigentliche Zweck: eine Seite ohne Landmarks und H1 bekommt ueber
        die Heuristik dieselbe Bewertung wie ueber axe, naemlich keine Abzuege."""
        heur = await _check_semantic_html(_soup("<html><body><p>x</p></body></html>"))
        axe = AxeScanner().convert_to_structured_issues(
            _axe("landmark-one-main", "moderate", ["cat.semantics", "best-practice"]))
        for liste in (
            [_I({"category": "barrierefreiheit", "severity": i.severity,
                 "title": i.title, "risk_euro": i.risk_euro}) for i in heur],
            [_I(d) for d in axe],
        ):
            res = ScoreCalculator.compute_with_status(normalize_severities(liste))
            assert res["pillar_scores"]["accessibility"] == 100
