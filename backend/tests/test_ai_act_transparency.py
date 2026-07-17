"""Tests für den AI-Act-Transparenz-Check (Art. 50 KI-VO) und den BFSG-Report."""
import pytest
from bs4 import BeautifulSoup

from compliance_engine.checks.ai_act_transparency_check import check_ai_act_transparency
from compliance_engine.scanner import ComplianceScanner, ComplianceIssue


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


@pytest.mark.asyncio
async def test_ki_nativer_bot_ohne_hinweis_ergibt_warning():
    html = '<html><body><script src="https://embed.chatbase.co/widget.js"></script></body></html>'
    issues = await check_ai_act_transparency("https://example.de", _soup(html))
    assert len(issues) == 1
    issue = issues[0]
    assert issue["severity"] == "warning"
    assert issue["category"] == "ai_act_transparency"
    assert "Chatbase" in issue["title"]
    # Haftungs-Design: Confidence + Fundstelle sind Pflicht
    assert issue["metadata"]["confidence"] > 0
    assert "chatbase" in issue["metadata"]["evidence"]
    assert "Art. 50" in issue["legal_basis"]


@pytest.mark.asyncio
async def test_ki_nativer_bot_mit_hinweis_ergibt_info():
    html = (
        '<html><body><p>Unser KI-Assistent beantwortet Ihre Fragen.</p>'
        '<script src="https://embed.chatbase.co/widget.js"></script></body></html>'
    )
    issues = await check_ai_act_transparency("https://example.de", _soup(html))
    assert len(issues) == 1
    assert issues[0]["severity"] == "info"
    assert issues[0]["risk_euro"] == 0
    assert issues[0]["metadata"]["disclosure_found"] is True


@pytest.mark.asyncio
async def test_chat_plattform_ergibt_pruefhinweis_info():
    html = '<html><body><script src="https://widget.intercom.io/widget/abc"></script></body></html>'
    issues = await check_ai_act_transparency("https://example.de", _soup(html))
    assert len(issues) == 1
    assert issues[0]["severity"] == "info"
    assert "prüfen" in issues[0]["title"].lower()


@pytest.mark.asyncio
async def test_erkennung_auch_ueber_netzwerk_requests():
    html = "<html><body></body></html>"
    issues = await check_ai_act_transparency(
        "https://example.de", _soup(html),
        request_urls=["https://cdn.botpress.cloud/webchat/v1/inject.js"],
    )
    assert len(issues) == 1
    assert "Botpress" in issues[0]["title"]


@pytest.mark.asyncio
async def test_keine_chat_systeme_keine_issues():
    html = '<html><body><script src="https://cdn.example.com/app.js"></script></body></html>'
    issues = await check_ai_act_transparency("https://example.de", _soup(html))
    assert issues == []


def _issue(category="barrierefreiheit", severity="critical", risk=1000,
           title="x", is_missing=False):
    return ComplianceIssue(
        category=category, severity=severity, title=title, description="d",
        risk_euro=risk, recommendation="r", legal_basis="l", is_missing=is_missing,
    )


def test_bfsg_report_shop_in_scope_mit_zahlen():
    issues = [
        _issue(severity="critical", risk=2000),
        _issue(severity="warning", risk=500),
        _issue(category="impressum", severity="critical", risk=3000),
    ]
    report = ComplianceScanner._build_bfsg_report(
        issues, {"accessibility": 42.0}, {"accessibility": "partial"},
        is_shop=True, has_widget=False,
    )
    assert report["likely_in_scope"] is True
    assert report["critical_issues"] == 1
    assert report["warning_issues"] == 1
    assert report["risk_euro"] == 2500  # nur Accessibility-Issues
    assert report["deadline_passed"] is True
    assert "100.000" in report["enforcement_note"]
    assert "Rechtsberatung" in report["disclaimer"]


def test_bfsg_report_erkennt_fehlende_erklaerung():
    issues = [_issue(title="BFSG-Barrierefreiheitserklärung fehlt", is_missing=True)]
    report = ComplianceScanner._build_bfsg_report(
        issues, {"accessibility": 0}, {"accessibility": "non_compliant"},
        is_shop=False, has_widget=True,
    )
    assert report["statement_found"] is False
    assert report["likely_in_scope"] is False
    assert "selbst prüfen" in report["scope_note"]


def test_ai_act_report_aggregiert_provider():
    issues = [
        {"severity": "warning", "metadata": {"provider": "Chatbase", "confidence": 0.95, "evidence": "e"}},
        {"severity": "info", "metadata": {"provider": "Intercom (Fin AI möglich)", "confidence": 0.85, "evidence": "e"}},
    ]
    report = ComplianceScanner._build_ai_act_report(issues)
    assert report["ai_systems_detected"] == 2
    assert report["action_needed"] is True
    assert report["providers"][0]["provider"] == "Chatbase"
