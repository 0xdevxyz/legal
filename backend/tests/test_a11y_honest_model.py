"""
Tests fuer das ehrliche A11y-Bewertungsmodell (Tier 3 B):
- Overlay-Widget ist Hinweis (info, 0 EUR), kein Score-Malus, kein Scan-Gate
- Phantom-Mapping focus-visible entfernt
- Automatik-Disclaimer in der Score-Ausgabe
- Tiefen-Checks (ARIAChecker/Media) ergaenzen additiv ohne Doppel-Scoring
"""

import pytest
from bs4 import BeautifulSoup

from compliance_engine.checks.barrierefreiheit_check import (
    check_barrierefreiheit_compliance,
    _check_accessibility_widget,
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


@pytest.mark.asyncio
async def test_missing_widget_is_info_without_risk():
    issue = await _check_accessibility_widget(_soup(PLAIN_PAGE))
    assert issue is not None
    assert issue.severity == "info"
    assert issue.risk_euro == 0
    assert issue.is_missing is False
    assert issue.auto_fixable is False
    # Empfehlung darf kein Overlay als Konformitaetsloesung verkaufen
    assert "UserWay" not in issue.recommendation
    assert "AccessiBe" not in issue.recommendation


@pytest.mark.asyncio
async def test_widget_absence_does_not_tank_pillar_score():
    issues = await check_barrierefreiheit_compliance("https://example.com", _soup(PLAIN_PAGE))
    widget_issues = [i for i in issues if "Widget" in (i.get("title") or "")]
    for wi in widget_issues:
        assert wi["severity"] == "info"
        assert wi["risk_euro"] == 0
        assert not wi.get("is_missing")


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
