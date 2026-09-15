"""Ein Gesetzes-Update darf keinen Mangel erfinden.

`apply_updates_to_scan_results` hob bis zum 15.09.2026 JEDEN Befund einer
Kategorie eine Stufe an, sobald dazu ein kritisches Update vorlag. Getroffen hat
das vor allem die Befunde, die gerade KEINEN Mangel melden:

* "Kein Cookie-Banner erforderlich" (Risiko 0, TDDDG §25 Abs. 2) wurde zur
  Warnung und kostete 8 Punkte in der Cookie-Saeule.
* "Struktur-Reparatur vorbereitet" und "Kontrast-Reparatur vorbereitet" ebenso —
  complyo bestrafte den Kunden also dafuer, dass complyo selbst repariert hatte.

Live gemessen auf complyo.de: Gesamtscore 92 -> 90, Cookie-Saeule 100 -> 92,
genau ab dem Scan vom 11.09.2026, in dem die Entwarnung als 'warning' ankam.
Gegenprobe mit 'info': Saeule wieder 100.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.legal_update_integration import (
    LegalUpdateIntegration, _ist_mangel,
)


KRITISCHES_UPDATE = {
    "id": 675,
    "title": "Aktualisierte Guidance zu Cookie-Consent-Gültigkeitsdauer",
    "url": "https://www.datenschutzkonferenz-online.de/",
    "severity": "critical",
    "category": "cookies",
    "update_type": "court_ruling",
    "description": "Cookie-Einwilligung, Gueltigkeitsdauer",
}


def _integration():
    return LegalUpdateIntegration(db_pool=None)


def _anwenden(issues, updates=None):
    scan = {"issues": issues, "total_risk_euro": 1000}
    return _integration().apply_updates_to_scan_results(
        scan, updates or [KRITISCHES_UPDATE])


class TestEntwarnungBleibtEntwarnung:
    def test_kein_banner_erforderlich_wird_keine_warnung(self):
        """Der gemessene Fall von complyo.de."""
        issues = [{"category": "cookies", "severity": "info", "risk_euro": 0,
                   "title": "Kein Cookie-Banner erforderlich"}]
        ergebnis = _anwenden(issues)
        assert ergebnis["issues"][0]["severity"] == "info"

    def test_vorbereitete_reparatur_wird_keine_warnung(self):
        """complyo darf den Kunden nicht dafuer bestrafen, dass es repariert."""
        issues = [{"category": "cookies", "severity": "info", "risk_euro": 0,
                   "title": "Struktur-Reparatur vorbereitet"}]
        assert _anwenden(issues)["issues"][0]["severity"] == "info"

    def test_das_urteil_steht_trotzdem_am_befund(self):
        """Die Information geht nicht verloren, sie bewertet nur nicht mehr.
        Bei einer Entwarnung ist sie eine Beobachtungsempfehlung."""
        issues = [{"category": "cookies", "severity": "info", "risk_euro": 0,
                   "title": "Kein Cookie-Banner erforderlich"}]
        befund = _anwenden(issues)["issues"][0]
        assert befund["relevant_updates"][0]["id"] == 675

    def test_eine_entwarnung_zaehlt_nicht_als_betroffen(self):
        """`affected_issues_count` traegt sonst eine Zahl, hinter der kein
        einziger Mangel steht — und das Gesamtrisiko stiege um 30 %."""
        issues = [{"category": "cookies", "severity": "info", "risk_euro": 0,
                   "title": "Kein Cookie-Banner erforderlich"}]
        ergebnis = _anwenden(issues)
        assert ergebnis["affected_issues_count"] == 0
        assert ergebnis["total_risk_euro"] == 1000

    def test_entwarnung_bekommt_kein_erhoehtes_risiko(self):
        issues = [{"category": "cookies", "severity": "info", "risk_euro": 0,
                   "title": "Kein Cookie-Banner erforderlich"}]
        befund = _anwenden(issues)["issues"][0]
        assert befund["risk_euro"] == 0
        assert "risk_increase_reason" not in befund


class TestEchterMangelSteigtWeiter:
    """Was die Regel leisten soll, leistet sie unveraendert: ein neues Urteil
    macht einen BESTEHENDEN Mangel dringlicher."""

    def test_warnung_wird_kritisch(self):
        issues = [{"category": "cookies", "severity": "warning",
                   "risk_euro": 2000,
                   "title": "Banner ohne gleichwertigen Ablehnen-Knopf"}]
        ergebnis = _anwenden(issues)
        assert ergebnis["issues"][0]["severity"] == "critical"
        assert ergebnis["affected_issues_count"] == 1

    def test_risiko_steigt_um_die_haelfte(self):
        issues = [{"category": "cookies", "severity": "warning",
                   "risk_euro": 2000, "title": "Banner ohne Ablehnen-Knopf"}]
        befund = _anwenden(issues)["issues"][0]
        assert befund["risk_euro"] == 3000
        assert befund["risk_increase_reason"]

    def test_bereits_kritisch_bleibt_kritisch_und_zaehlt_nicht_doppelt(self):
        issues = [{"category": "cookies", "severity": "critical",
                   "risk_euro": 2000, "title": "Tracking vor Einwilligung"}]
        ergebnis = _anwenden(issues)
        assert ergebnis["issues"][0]["severity"] == "critical"
        assert ergebnis["affected_issues_count"] == 0

    def test_ohne_kritisches_update_bleibt_alles_wie_gemessen(self):
        leichtes = dict(KRITISCHES_UPDATE, severity="medium")
        issues = [{"category": "cookies", "severity": "warning",
                   "risk_euro": 2000, "title": "Banner ohne Ablehnen-Knopf"}]
        befund = _anwenden(issues, [leichtes])["issues"][0]
        assert befund["severity"] == "warning"
        assert befund["risk_euro"] == 2000


class TestTrennlinie:
    """`_ist_mangel` zieht dieselbe Linie wie der ScoreCalculator: was Punkte
    kostet, ist ein Mangel."""

    def test_info_ist_kein_mangel(self):
        assert _ist_mangel({"severity": "info"}) is False

    def test_warning_und_critical_sind_mangel(self):
        assert _ist_mangel({"severity": "warning"}) is True
        assert _ist_mangel({"severity": "critical"}) is True

    def test_fehlende_angabe_gilt_als_hinweis(self):
        """Ohne Stufe ist nichts gemessen — dann wird auch nichts angehoben."""
        assert _ist_mangel({}) is False

    def test_schreibweise_entscheidet_nicht(self):
        assert _ist_mangel({"severity": " Warning "}) is True
