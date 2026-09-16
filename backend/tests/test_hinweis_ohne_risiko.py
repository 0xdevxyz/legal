"""Nachlese der Live-Scans vom 16.09.2026 (panoart360, osteopathie-limbach, zua-zwickau).

Vier Unsauberkeiten, die erst im echten Bericht sichtbar wurden:

* Ein Hinweis mit Abmahnrisiko: "Guetezeichen ohne verlinkten Nachweis
  erkannt" stand auf info und trug 1.000 EUR in der Risikosumme des Kunden.
* Dieselbe fehlende Barrierefreiheitserklaerung zweimal im Bericht, einmal
  als Warnung (Buchungsseite), einmal als Hinweis (Startseite).
* "A ohne zugaengliches Label" aus dem Quelltext, obwohl axe den Link auf dem
  gerenderten DOM als benannt erkannte.
* Ein axe-Titel auf Englisch: "ARIA role should be appropriate for the element".
"""

import os
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.axe_translations import uebersetze as uebersetze_axe
from compliance_engine.checks.aria_checker import ARIAChecker
from compliance_engine.scanner import ComplianceIssue, dedupe_issues, normalize_severities


def _issue(title, severity, risk=0, category="barrierefreiheit"):
    return ComplianceIssue(category=category, severity=severity, title=title,
                           description="", risk_euro=risk, recommendation="r",
                           legal_basis="l")


class TestHinweisTraegtKeinRisiko:
    def test_info_wird_auf_null_gesetzt(self):
        [i] = normalize_severities([_issue("Gütezeichen/Siegel ohne verlinkten Nachweis erkannt", "info", 1000)])
        assert i.risk_euro == 0

    def test_mangel_behaelt_sein_risiko(self):
        [i] = normalize_severities([_issue("Bild ohne Alt-Text", "warning", 500)])
        assert i.risk_euro == 500

    def test_auch_nach_normalisierung_einer_fremden_stufe(self):
        """'minor' wird 'warning', nicht 'info'; das Risiko bleibt dann."""
        [i] = normalize_severities([_issue("x", "minor", 300)])
        assert i.severity == "warning" and i.risk_euro == 300


class TestEineErklaerungEinBefund:
    def test_die_strengere_fassung_gewinnt(self):
        hinweis = _issue("Barrierefreiheitserklärung fehlt — nur Pflicht für B2C-Dienste", "info")
        warnung = _issue("Barrierefreiheitserklärung fehlt (BFSG §14)", "warning", 2000)
        ergebnis = dedupe_issues([hinweis, warnung])
        assert len(ergebnis) == 1
        assert ergebnis[0].severity == "warning"

    def test_reihenfolge_spielt_keine_rolle(self):
        hinweis = _issue("Barrierefreiheitserklärung fehlt — nur Pflicht für B2C-Dienste", "info")
        warnung = _issue("Barrierefreiheitserklärung fehlt (BFSG §14)", "warning", 2000)
        [e] = dedupe_issues([warnung, hinweis])
        assert e.severity == "warning"

    def test_andere_befunde_bleiben_getrennt(self):
        a = _issue("Kein Cookie-Banner erkannt (kein Tracking gefunden)", "info", category="cookies")
        b = _issue("Kein Cookie-Banner erforderlich", "info", category="cookies")
        assert len(dedupe_issues([a, b])) == 2


def _a(html):
    return BeautifulSoup(html, "html.parser").find("a")


class TestZugaenglicherNameAusDemInhalt:
    def test_bild_mit_alt_benennt_den_link(self):
        assert ARIAChecker()._has_accessible_name(_a('<a href="/"><img src="l.png" alt="Startseite"></a>'))

    def test_bild_ohne_alt_benennt_nicht(self):
        assert not ARIAChecker()._has_accessible_name(_a('<a href="#"><img src="l.png" alt=""></a>'))

    def test_svg_mit_title_benennt(self):
        assert ARIAChecker()._has_accessible_name(_a('<a href="#"><svg><title>Nach oben</title></svg></a>'))

    def test_icon_mit_aria_label_benennt(self):
        assert ARIAChecker()._has_accessible_name(_a('<a href="#"><i class="fa" aria-label="Menü"></i></a>'))

    def test_anker_ohne_href_ist_kein_link(self):
        assert ARIAChecker()._has_accessible_name(_a('<a id="top"></a>'))

    def test_leerer_link_auf_raute_bleibt_ein_mangel(self):
        assert not ARIAChecker()._has_accessible_name(_a('<a href="#"><i class="fa fa-up"></i></a>'))


class TestDeutscherTitel:
    def test_aria_allowed_role_ist_uebersetzt(self):
        titel, _ = uebersetze_axe("aria-allowed-role", "ARIA role should be appropriate for the element", "")
        assert "ARIA-Rolle" in titel

    def test_landmark_regeln_sind_uebersetzt(self):
        for regel in ("landmark-no-duplicate-main", "landmark-main-is-top-level",
                      "focusable-no-name", "label-title-only"):
            titel, _ = uebersetze_axe(regel, "english", "")
            assert titel and "english" not in titel.lower(), regel


class TestHeuristikTrittZurueckWennAxeLief:
    def test_der_merge_block_kennt_die_regel(self):
        pfad = os.path.join(os.path.dirname(__file__), "..", "compliance_engine",
                            "checks", "barrierefreiheit_check.py")
        src = open(pfad, encoding="utf-8").read()
        assert "endswith(\'ohne zugängliches Label\')" in src
        assert "axe_issues is not None" in src.split("ARIAChecker().check_aria_compliance")[1][:900]
