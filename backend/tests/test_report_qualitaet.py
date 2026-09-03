"""
Regressionstests fuer die Report-Qualitaet.

Alle drei Faelle stammen aus echten Scans vom 2026-08-04 (loqal.io,
spedition-mahn.de) und haben dort den Score verfaelscht oder den Report
unlesbar gemacht.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.scanner import (
    ComplianceIssue,
    dedupe_issues,
    normalize_severities,
)
from compliance_engine.axe_translations import AXE_DE, uebersetze


def _issue(title, severity="warning", category="barrierefreiheit"):
    return ComplianceIssue(
        category=category,
        severity=severity,
        title=title,
        description="",
        risk_euro=100,
        recommendation="",
        legal_basis="",
    )


class TestSeverityVereinheitlichung:
    """
    'WCAG 1.2.2: Video ohne Untertitel-Track' trug severity='error'. Der
    ScoreCalculator kennt nur critical/warning/info — der Befund kostete
    keinen Punkt und faerbte keinen Saeulen-Status.
    """

    def test_error_wird_critical(self):
        issues = normalize_severities([_issue("Video ohne Untertitel", "error")])
        assert issues[0].severity == "critical"

    def test_bekannte_stufen_bleiben(self):
        issues = normalize_severities([
            _issue("a", "critical"), _issue("b", "warning"), _issue("c", "info"),
        ])
        assert [i.severity for i in issues] == ["critical", "warning", "info"]

    def test_grossschreibung_egal(self):
        assert normalize_severities([_issue("a", "ERROR")])[0].severity == "critical"

    def test_unbekannte_stufe_wird_warning_nicht_verschluckt(self):
        """Im Zweifel zählt ein Mangel, statt lautlos aus der Wertung zu fallen."""
        assert normalize_severities([_issue("a", "bananenfoermig")])[0].severity == "warning"

    def test_leere_stufe_wird_warning(self):
        assert normalize_severities([_issue("a", "")])[0].severity == "warning"


class TestSaeulenweiteZusammenfassung:
    def test_gleicher_mangel_aus_zwei_kategorien(self):
        """
        "Video ohne Untertitel" kam aus 'barrierefreiheit' UND
        'media_accessibility' — zwei Kategorien, eine Säule, ein Mangel.
        """
        issues = [
            _issue("Video ohne Untertitel", "critical", "barrierefreiheit"),
            _issue("Video ohne Untertitel", "critical", "media_accessibility"),
        ]
        assert len(dedupe_issues(issues)) == 1

    def test_wcag_praefix_oeffnet_keinen_neuen_mangel(self):
        issues = [
            _issue("WCAG 1.2.2: Video ohne Untertitel", "warning"),
            _issue("Video ohne Untertitel", "critical"),
        ]
        ergebnis = dedupe_issues(issues)
        assert len(ergebnis) == 1
        assert ergebnis[0].severity == "critical"

    def test_verschiedene_saeulen_bleiben_getrennt(self):
        issues = [
            _issue("Angabe fehlt", "warning", "barrierefreiheit"),
            _issue("Angabe fehlt", "warning", "datenschutz"),
        ]
        assert len(dedupe_issues(issues)) == 2


class TestAxeUebersetzung:
    def test_bekannte_regel_wird_deutsch(self):
        titel, beschreibung = uebersetze(
            "region", "All page content should be contained by landmarks", "…"
        )
        assert titel == "Inhalte außerhalb von Landmark-Bereichen"
        assert "Screenreader" in beschreibung

    def test_heading_order_wird_deutsch(self):
        titel, _ = uebersetze("heading-order", "Heading levels should only increase by one", "")
        assert titel == "Überschriftenebenen springen"

    def test_unbekannte_regel_behaelt_original(self):
        """Lieber sichtbar unübersetzt als frei erfunden."""
        titel, beschreibung = uebersetze("gibt-es-nicht", "Some english help", "Some english desc")
        assert titel == "Some english help"
        assert beschreibung == "Some english desc"

    def test_regel_id_als_letzter_rueckfall(self):
        titel, _ = uebersetze("gibt-es-nicht", "", "")
        assert titel == "gibt-es-nicht"

    def test_keine_englischen_resttexte_in_der_tabelle(self):
        """Wächter: jeder Eintrag muss wirklich übersetzt sein."""
        verdaechtig = ("should", "must", "elements", " the ", "missing")
        for rule_id, (titel, beschreibung) in AXE_DE.items():
            text = f"{titel} {beschreibung}".lower()
            treffer = [w for w in verdaechtig if w in text]
            assert not treffer, f"{rule_id}: englischer Rest {treffer} in '{titel}'"

    def test_tabelle_ist_vollstaendig_befuellt(self):
        for rule_id, eintrag in AXE_DE.items():
            assert len(eintrag) == 2, rule_id
            assert eintrag[0].strip(), f"{rule_id}: leerer Titel"
            assert eintrag[1].strip(), f"{rule_id}: leere Beschreibung"
