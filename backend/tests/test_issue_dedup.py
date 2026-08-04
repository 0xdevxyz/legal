"""
Regressionstests fuer die Zusammenfassung von Doppelmeldungen.

Anlass (Live-Scan complyo.de, 2026-08-04): Heuristik-Check und ARIA-Checker
meldeten dieselben unbeschrifteten Formularfelder unter minimal abweichendem
Titel — einmal als warning, einmal als critical.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.scanner import ComplianceIssue, dedupe_issues


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


class TestDoppelmeldungen:
    def test_schreibvariante_wird_zusammengefasst(self):
        issues = [
            _issue("4 Formular-Felder ohne Label", "warning"),
            _issue("4 Formularfelder ohne Label", "critical"),
        ]
        ergebnis = dedupe_issues(issues)
        assert len(ergebnis) == 1

    def test_schwerste_variante_gewinnt(self):
        """Ein Mangel, den ein Checker als critical sieht, bleibt critical."""
        issues = [
            _issue("4 Formular-Felder ohne Label", "warning"),
            _issue("4 Formularfelder ohne Label", "critical"),
        ]
        assert dedupe_issues(issues)[0].severity == "critical"

        # auch in umgekehrter Reihenfolge
        assert dedupe_issues(list(reversed(issues)))[0].severity == "critical"

    def test_anzahl_im_titel_egal(self):
        issues = [
            _issue("3 Formularfelder ohne Label"),
            _issue("7 Formular-Felder ohne Label"),
        ]
        assert len(dedupe_issues(issues)) == 1

    def test_umlaute_normalisiert(self):
        issues = [
            _issue("Kündigungsbutton fehlt"),
            _issue("Kuendigungsbutton fehlt"),
        ]
        assert len(dedupe_issues(issues)) == 1

    def test_verschiedene_maengel_bleiben_getrennt(self):
        issues = [
            _issue("Formularfelder ohne Label"),
            _issue("Kein Skip-Navigation-Link gefunden"),
            _issue("Landmark-Regions fehlen"),
        ]
        assert len(dedupe_issues(issues)) == 3

    def test_gleicher_titel_andere_saeule_bleibt(self):
        """Dieselbe Formulierung in zwei Säulen ist nicht derselbe Mangel."""
        issues = [
            _issue("Drittlandtransfer nicht dokumentiert", category="datenschutz"),
            _issue("Drittlandtransfer nicht dokumentiert", category="cookie"),
        ]
        assert len(dedupe_issues(issues)) == 2

    def test_reihenfolge_bleibt_erhalten(self):
        issues = [
            _issue("Erster Mangel"),
            _issue("Zweiter Mangel"),
            _issue("Erster Mangel", "critical"),
            _issue("Dritter Mangel"),
        ]
        titel = [i.title for i in dedupe_issues(issues)]
        assert titel == ["Erster Mangel", "Zweiter Mangel", "Dritter Mangel"]

    def test_leere_titel_werden_nicht_verschmolzen(self):
        issues = [_issue(""), _issue("")]
        assert len(dedupe_issues(issues)) == 2
