"""
Regressionstests für ScoreCalculator – Säulen-Scoring (SSOT v3.0)

Hintergrund (Bug, der hier fixiert wird):
`is_missing` wird von vielen Check-Modulen auch auf einzelne Warning-Sub-Findings
gesetzt ("Widerrufsmöglichkeit fehlt", "Ablehnen-Button fehlt" …). Früher zog
`has_missing_core` eine Säule auf 0, sobald IRGENDEIN Issue darin is_missing=True
hatte → jede Säule mit einer einzelnen "fehlt"-Warnung kollabierte auf 0
(z.B. Rechtstexte 0 trotz nur 1 Shop-Warning).

Vertrag (jetzt erzwungen): Nur ein komplett fehlendes KERN-Element zieht die
Säule auf 0 — und solche Issues sind immer `critical`.
"""

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.score_calculator import ScoreCalculator, PillarStatus


@dataclass
class _Issue:
    """Minimal-Issue mit genau den Feldern, die der ScoreCalculator liest."""
    category: str
    severity: str
    is_missing: bool = False


class TestMissingCoreContract:
    """Kern des Bugs: is_missing darf nur bei critical die Säule nullen."""

    def test_warning_is_missing_does_not_zero_pillar(self):
        # Genau das Szenario "Rechtstexte 0 trotz nur 1 Shop-Warning".
        issues = [_Issue(category="shop", severity="warning", is_missing=True)]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        # 100 - (0*25 + 1*8) = 92  — NICHT 0
        assert scores["legal"] == 92

    def test_critical_is_missing_zeroes_pillar(self):
        # Komplett fehlendes Kern-Element (z.B. A11y-Widget) ist immer critical.
        issues = [_Issue(category="barrierefreiheit", severity="critical", is_missing=True)]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        assert scores["accessibility"] == 0

    def test_multiple_warning_is_missing_only_deducts(self):
        # Drei "fehlt"-Warnings → 100 - 3*8 = 76, nicht 0.
        issues = [
            _Issue(category="cookie", severity="warning", is_missing=True),
            _Issue(category="cookie", severity="warning", is_missing=True),
            _Issue(category="cookie", severity="warning", is_missing=True),
        ]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        assert scores["cookies"] == 76

    def test_is_missing_flag_ignored_for_non_critical_severity(self):
        # Auch info-Level mit is_missing darf nicht nullen.
        issues = [_Issue(category="datenschutz", severity="info", is_missing=True)]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        assert scores["gdpr"] == 100


class TestRealWorldScenario:
    """Nachstellung des panoart360.de-Scans, der den Bug aufgedeckt hat."""

    def test_mixed_pillars_score_correctly(self):
        issues = [
            # accessibility: Widget fehlt (critical core) + 4 Warnings
            _Issue("barrierefreiheit", "critical", is_missing=True),
            _Issue("barrierefreiheit", "warning"),
            _Issue("barrierefreiheit", "warning"),
            _Issue("barrierefreiheit", "warning"),
            _Issue("barrierefreiheit", "warning"),
            # gdpr: 8 Warnings (einige is_missing, aber kein critical)
            *[_Issue("datenschutz", "warning", is_missing=True) for _ in range(3)],
            *[_Issue("security", "warning") for _ in range(4)],
            _Issue("avv", "warning"),
            # legal: 1 Shop-Warning (is_missing)
            _Issue("shop", "warning", is_missing=True),
            # cookies: 4 critical Kern-Element fehlt
            *[_Issue("cookie", "critical", is_missing=True) for _ in range(4)],
        ]
        result = ScoreCalculator.compute(issues)
        pillars = result["pillar_scores"]

        assert pillars["accessibility"] == 0    # Widget fehlt (critical core)
        assert pillars["gdpr"] == 36             # 100 - 8*8
        assert pillars["legal"] == 92            # 100 - 1*8  (vorher fälschlich 0!)
        assert pillars["cookies"] == 0           # 4 critical core fehlt
        # Gesamt = Mittelwert der vier Säulen
        assert result["overall_score"] == round((0 + 36 + 92 + 0) / 4)


class TestBaseline:
    def test_no_issues_is_full_score(self):
        result = ScoreCalculator.compute([])
        assert result["overall_score"] == 100
        assert all(v == 100 for v in result["pillar_scores"].values())


class TestEvidenceBasedV4:
    """
    v4.0 evidenz-basiert: Abwesenheit von Erkennung ist KEIN Nachweis von
    Compliance. Reproduziert u.a. das spedition-mahn.de-Problem (leere Seite
    bekam fälschlich 49 %).
    """

    def test_empty_site_scores_near_zero(self):
        # Seite ohne Impressum/Datenschutz/Cookie-Banner/A11y: jede Säule emittiert
        # ein fehlendes Kern-Element (critical + is_missing).
        issues = [
            _Issue("impressum", "critical", is_missing=True),
            _Issue("datenschutz", "critical", is_missing=True),
            _Issue("cookies", "critical", is_missing=True),
            _Issue("barrierefreiheit", "critical", is_missing=True),
        ]
        result = ScoreCalculator.compute(issues)
        assert result["overall_score"] == 0
        assert all(v == 0 for v in result["pillar_scores"].values())
        assert all(s == PillarStatus.NON_COMPLIANT for s in result["pillar_status"].values())

    def test_unverified_pillar_is_not_counted_as_passed(self):
        # Cookie-Säule konnte nicht geprüft werden (Check abgestürzt) und hat keine
        # Evidenz → 0 Credit + Status unverified, NICHT 100.
        result = ScoreCalculator.compute_with_status([], unverified_pillars={"cookies"})
        assert result["pillar_status"]["cookies"] == PillarStatus.UNVERIFIED
        assert result["pillar_scores"]["cookies"] == 0
        # 3 Säulen bestanden (100), 1 ungeprüft (0) → (100+100+100+0)/4 = 75
        assert result["overall_score"] == 75

    def test_unverified_pillar_with_evidence_uses_issues(self):
        # Liegt trotz "unverified"-Flag echte Evidenz (Issue) vor, gewinnt die Evidenz.
        issues = [_Issue("cookies", "critical", is_missing=True)]
        result = ScoreCalculator.compute_with_status(issues, unverified_pillars={"cookies"})
        assert result["pillar_status"]["cookies"] == PillarStatus.NON_COMPLIANT
        assert result["pillar_scores"]["cookies"] == 0

    def test_effort_classification(self):
        SC = ScoreCalculator
        # auto-fixable → gering, egal welche Severity
        assert SC.classify_effort("critical", auto_fixable=True) == SC.EFFORT_LOW
        # komplett fehlendes Kern-Element (critical+is_missing) → experte
        assert SC.classify_effort("critical", is_missing=True) == SC.EFFORT_EXPERT
        # critical ohne Autofix → experte
        assert SC.classify_effort("critical") == SC.EFFORT_EXPERT
        # warning → mittel
        assert SC.classify_effort("warning") == SC.EFFORT_MEDIUM
        # info → gering
        assert SC.classify_effort("info") == SC.EFFORT_LOW

    def test_status_derivation(self):
        issues = [
            _Issue("datenschutz", "warning"),   # gdpr partial
            _Issue("impressum", "critical", is_missing=True),  # legal non_compliant
        ]
        result = ScoreCalculator.compute(issues)
        status = result["pillar_status"]
        assert status["gdpr"] == PillarStatus.PARTIAL
        assert status["legal"] == PillarStatus.NON_COMPLIANT
        assert status["accessibility"] == PillarStatus.COMPLIANT  # keine Issues, geprüft
        assert status["cookies"] == PillarStatus.COMPLIANT
