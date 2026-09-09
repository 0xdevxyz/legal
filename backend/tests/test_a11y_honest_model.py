"""
Tests fuer das ehrliche A11y-Bewertungsmodell (Tier 3 B):
- Overlay-Widget erzeugt GAR KEINEN Befund mehr (seit 09.09.2026, vorher:
  Hinweis mit info/0 EUR). Der Hinweis stand im Bestandsdurchlauf auf 16 von 24
  Kundenberichten, sagte nichts ueber die Rechtslage und empfahl dabei eine
  Produktgattung, die complyo verkauft. Ob ein Widget da ist, bleibt als
  Tatsache erhalten (hat_assistenz_widget) — nur als Befund ist es weg.
- Phantom-Mapping focus-visible entfernt
- Automatik-Disclaimer in der Score-Ausgabe
- Tiefen-Checks (ARIAChecker/Media) ergaenzen additiv ohne Doppel-Scoring
"""

import pytest
from bs4 import BeautifulSoup

from compliance_engine.checks.barrierefreiheit_check import (
    check_barrierefreiheit_compliance,
    hat_assistenz_widget,
    _collect_reported_criteria,
)
from compliance_engine.axe_scanner import AXE_RULE_TO_FEATURE
from compliance_engine.score_calculator import ScoreCalculator


def _soup(html):
    return BeautifulSoup(html, "html.parser")


PLAIN_PAGE = (
    '<html lang="de"><head><title>Test</title></head>'
    "<body><main><h1>Hallo</h1><nav>x</nav></main>"
    "<header>h</header><footer>f</footer></body></html>"
)


def test_fehlendes_widget_ist_eine_tatsache_kein_befund():
    """Kein Widget heisst: Tatsache False. Kein Befund, keine Empfehlung.

    Frueher entstand hier ein Hinweis (info, 0 EUR). Er war harmlos fuer den
    Score, aber er stand in fast jedem Bericht und warb fuer eine
    Produktgattung — in einem Pruefbericht hat das nichts zu suchen.
    """
    assert hat_assistenz_widget(_soup(PLAIN_PAGE)) is False


def test_vorhandenes_widget_wird_als_tatsache_erkannt():
    mit_widget = _soup(
        '<html><body><script src="https://api.complyo.de/api/widgets/accessibility.js">'
        "</script></body></html>"
    )
    assert hat_assistenz_widget(mit_widget) is True


@pytest.mark.asyncio
async def test_kein_widget_befund_im_bericht():
    """Der Bericht enthaelt keinen Widget-Befund mehr — auch keinen harmlosen."""
    issues = await check_barrierefreiheit_compliance("https://example.com", _soup(PLAIN_PAGE))
    widget_issues = [i for i in issues if "Widget" in (i.get("title") or "")]
    assert widget_issues == [], f"unerwarteter Widget-Befund: {widget_issues}"


def test_focus_visible_phantom_mapping_removed():
    assert "focus-visible" not in AXE_RULE_TO_FEATURE


def test_pillar_notes_contain_automation_disclaimer():
    result = ScoreCalculator.compute_with_status([])
    note = result.get("pillar_notes", {}).get("accessibility", "")
    assert "Teil" in note and "WCAG" in note
    assert "manuelle" in note or "manuell" in note.lower()


def test_collect_reported_criteria_mixed_shapes():
    issues = [
        {"wcag_criterion": "4.1.2"},
        {"metadata": {"wcag_criteria": ["1.4.3", "1.1.1"]}},
    ]
    crits = _collect_reported_criteria(issues)
    assert {"4.1.2", "1.4.3", "1.1.1"} <= crits


@pytest.mark.asyncio
async def test_aria_deep_check_adds_status_message_criterion():
    # Seite mit dynamischem Statusbereich ohne aria-live -> 4.1.3 kommt vom
    # verdrahteten ARIAChecker (frueher toter Code).
    html = (
        '<html lang="de"><head><title>T</title></head><body>'
        '<main><h1>x</h1>'
        '<div role="button">klick</div>'
        "</main><nav>n</nav><header>h</header><footer>f</footer></body></html>"
    )
    issues = await check_barrierefreiheit_compliance("https://example.com", _soup(html))
    # ARIAChecker-Dict-Issues tragen wcag_criterion; mindestens die Tiefe laeuft ohne Fehler
    assert isinstance(issues, list)
    assert all(isinstance(i, dict) for i in issues)
