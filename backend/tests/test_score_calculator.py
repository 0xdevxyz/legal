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
    title: str = ""


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


class TestTypSaettigung:
    """
    Ein einzelner Befund-Typ darf eine Säule nicht im Alleingang auf 0 ziehen.

    Anlass (echter Schaden, 2026-08-04): ein zu grober WCAG-1.1.1-SVG-Check
    meldete jedes dekorative Lucide-Icon einzeln — 59 Warnungen à 8 Punkte
    drückten complyo.de von 100 % auf 28 %.
    """

    def test_massenbefund_kippt_saeule_nicht(self):
        issues = [
            _Issue("barrierefreiheit", "warning", title="SVG ohne Textalternative")
            for _ in range(59)
        ]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        # gedeckelt auf 3 × 8 = 24 Abzug statt 59 × 8 = 472
        assert scores["accessibility"] == 76

    def test_erste_funde_kosten_voll(self):
        issues = [
            _Issue("barrierefreiheit", "warning", title="SVG ohne Textalternative")
            for _ in range(2)
        ]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        assert scores["accessibility"] == 84  # 100 - 2*8

    def test_verschiedene_typen_zaehlen_einzeln(self):
        """Sättigung greift pro Typ, nicht pro Säule — echte Vielfalt kostet."""
        issues = [
            _Issue("barrierefreiheit", "warning", title="Kontrast zu gering"),
            _Issue("barrierefreiheit", "warning", title="Skip-Link fehlt"),
            _Issue("barrierefreiheit", "warning", title="Landmark-Regions fehlen"),
            _Issue("barrierefreiheit", "warning", title="Formularfelder ohne Label"),
            _Issue("barrierefreiheit", "warning", title="Semantische Elemente fehlen"),
        ]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        assert scores["accessibility"] == 60  # 100 - 5*8, nichts gedeckelt

    def test_zahlen_im_titel_bilden_denselben_typ(self):
        """
        "3 Formularfelder ohne Label" und "7 Formularfelder ohne Label" sind
        derselbe Befund-Typ — die Anzahl im Titel darf keinen neuen Typ öffnen,
        sonst umgeht ein Check die Sättigung durch wechselnde Zahlen.
        """
        issues = [
            _Issue("barrierefreiheit", "warning", title="3 Formularfelder ohne Label"),
            _Issue("barrierefreiheit", "warning", title="7 Formularfelder ohne Label"),
            _Issue("barrierefreiheit", "warning", title="9 Formularfelder ohne Label"),
            _Issue("barrierefreiheit", "warning", title="12 Formularfelder ohne Label"),
        ]
        crit, warn = ScoreCalculator.count_effective_severities(issues)
        assert (crit, warn) == (0, 3)

    def test_critical_und_warning_saettigen_getrennt(self):
        issues = [_Issue("shop", "critical", title="Widerrufsbelehrung fehlt")] * 10
        crit, warn = ScoreCalculator.count_effective_severities(issues)
        assert (crit, warn) == (3, 0)

    def test_ohne_titel_keine_saettigung(self):
        """Kein Titel → kein bestimmbarer Typ → lieber voll zählen."""
        issues = [_Issue("datenschutz", "warning") for _ in range(6)]
        crit, warn = ScoreCalculator.count_effective_severities(issues)
        assert (crit, warn) == (0, 6)

    def test_issue_liste_bleibt_vollstaendig(self):
        """
        Gedeckelt wird nur der SCORE. Der Nutzer muss weiterhin jeden
        einzelnen Fund sehen — sonst verschwindet Arbeit aus der Liste.
        """
        issues = [
            _Issue("barrierefreiheit", "warning", title="SVG ohne Textalternative")
            for _ in range(20)
        ]
        result = ScoreCalculator.compute_with_status(issues)
        assert result["pillar_scores"]["accessibility"] == 76
        assert len(issues) == 20  # Eingabeliste unangetastet


class TestWarnungsBoden:
    """
    0 muss Totalausfall bedeuten, nicht "viele Kleinigkeiten".

    panoart360.de stand auf DSGVO 0/100 bei 14 Warnungen und keinem einzigen
    kritischen Verstoß — Impressum da, Datenschutzerklärung da. Dieselbe Null
    wie eine Seite ganz ohne Datenschutzerklärung.
    """

    def test_viele_warnungen_fallen_nicht_auf_null(self):
        issues = [
            _Issue("datenschutz", "warning", title=f"Lücke {w}")
            for w in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N")
        ]
        scores = ScoreCalculator.calculate_pillar_scores(issues)
        assert scores["gdpr"] == ScoreCalculator.WARNING_ONLY_FLOOR

    def test_wenige_warnungen_rechnen_normal(self):
        issues = [_Issue("datenschutz", "warning", title="Eine Lücke")]
        assert ScoreCalculator.calculate_pillar_scores(issues)["gdpr"] == 92

    def test_critical_faellt_weiterhin_bis_null(self):
        """Der Boden gilt nur ohne kritischen Befund."""
        issues = [_Issue("datenschutz", "critical", title=f"Verstoß {n}") for n in "ABCD"]
        assert ScoreCalculator.calculate_pillar_scores(issues)["gdpr"] == 0

    def test_fehlendes_kernelement_bleibt_null(self):
        issues = [_Issue("datenschutz", "critical", is_missing=True, title="Datenschutzerklärung fehlt")]
        assert ScoreCalculator.calculate_pillar_scores(issues)["gdpr"] == 0

    def test_boden_gilt_auch_gemischt_ohne_critical(self):
        """
        Titel ohne durchlaufende Nummern — sonst greift die Typ-Sättigung und
        der Boden wird gar nicht erst erreicht.
        """
        themen = [
            "Widerrufsbelehrung unvollständig", "AGB ohne Gerichtsstand",
            "Preisangabe ohne Versandkosten", "Lieferzeit fehlt",
            "Zahlungsarten unklar", "Garantiebedingungen fehlen",
            "Streitschlichtung nicht genannt", "Kündigungsfrist unklar",
            "Vertragstext nicht abrufbar", "Bestellbestätigung fehlt",
            "Rücksendekosten ungeklärt", "Mängelhaftung unvollständig",
            "Verfügbarkeit nicht angegeben", "Mindestlaufzeit unklar",
        ]
        issues = [_Issue("shop", "warning", title=t) for t in themen]
        issues += [_Issue("shop", "info", title="Hinweis")]
        assert ScoreCalculator.calculate_pillar_scores(issues)["legal"] == ScoreCalculator.WARNING_ONLY_FLOOR
