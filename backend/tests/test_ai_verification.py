"""
Tests für die KI-Verifikations-Verdrahtung im Scanner (v4.0).
Der eigentliche KI-Aufruf wird gemockt — getestet wird die Logik:
UNVERIFIED → (compliant | non_compliant | bleibt unverified).
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bs4 import BeautifulSoup

import ai_review_engine
from compliance_engine.scanner import ComplianceScanner, ComplianceIssue


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _patch_verdict(monkeyverdict):
    async def fake(pillar, page_text, evidence=None):
        return monkeyverdict
    ai_review_engine.ai_verify_pillar = fake


class TestAiVerificationWiring:
    def setup_method(self):
        self._orig = ai_review_engine.ai_verify_pillar

    def teardown_method(self):
        ai_review_engine.ai_verify_pillar = self._orig

    def test_ai_confirms_compliant_removes_unverified(self):
        _patch_verdict({"compliant": True, "missing": [], "reason": "ok", "confidence": 0.9})
        scanner = ComplianceScanner()
        soup = BeautifulSoup("<html><body>Datenschutz ...</body></html>", "html.parser")
        issues, unverified = _run(
            scanner._ai_verify_unverified_pillars(soup, [], {"gdpr"})
        )
        assert "gdpr" not in unverified
        assert issues == []  # konform → kein Issue

    def test_ai_confirms_non_compliant_adds_critical_issue(self):
        _patch_verdict({"compliant": False, "missing": ["Verantwortlicher"], "reason": "fehlt", "confidence": 0.8})
        scanner = ComplianceScanner()
        soup = BeautifulSoup("<html><body>nichts</body></html>", "html.parser")
        issues, unverified = _run(
            scanner._ai_verify_unverified_pillars(soup, [], {"gdpr"})
        )
        assert "gdpr" not in unverified
        assert len(issues) == 1
        assert issues[0].category == "datenschutz"
        assert issues[0].severity == "critical"
        assert issues[0].is_missing is True

    def test_ai_unavailable_keeps_unverified(self):
        _patch_verdict(None)
        scanner = ComplianceScanner()
        soup = BeautifulSoup("<html><body>x</body></html>", "html.parser")
        issues, unverified = _run(
            scanner._ai_verify_unverified_pillars(soup, [], {"cookies"})
        )
        assert "cookies" in unverified  # bleibt ungeprüft
        assert issues == []
