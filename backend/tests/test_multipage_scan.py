"""
Tests fuer die Mehrseiten-Pruefung.

Anlass: complyo prueft bis 08/2026 nur die Startseite. Die Widerrufsbelehrung
steht aber auf /agb, das Formular ohne Datenschutzhinweis auf /kontakt.
Wettbewerber scannen 50-100 Unterseiten je Durchlauf.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.page_discovery import (
    KLASSE_ANGEBOT, KLASSE_INHALT, KLASSE_INTERAKTION, KLASSE_PFLICHT,
    klassifiziere, _normalisiere,
)
from compliance_engine.scanner import ComplianceIssue, dedupe_issues


class TestSeitenKlassifikation:
    def test_pflichtseiten(self):
        for pfad in ("/impressum", "/impressum.html", "/datenschutz",
                     "/datenschutzerklaerung", "/agb", "/widerruf",
                     "/cookie-richtlinie", "/barrierefreiheit"):
            assert klassifiziere("https://x.de" + pfad) == KLASSE_PFLICHT, pfad

    def test_interaktionsseiten(self):
        for pfad in ("/kontakt", "/checkout", "/warenkorb", "/anmeldung",
                     "/newsletter", "/terminbuchung"):
            assert klassifiziere("https://x.de" + pfad) == KLASSE_INTERAKTION, pfad

    def test_ratgeberartikel_ist_keine_pflichtseite(self):
        """
        Echter Fehler der ersten Fassung: "/blog-dsgvo-2024" galt als
        Datenschutzerklärung. Auf einem Ratgeberartikel die Vollständigkeit
        von Pflichtangaben zu prüfen, erzeugt garantierte Fehlbefunde.
        """
        assert klassifiziere("https://x.de/blog-dsgvo-2024") == KLASSE_INHALT
        assert klassifiziere("https://x.de/blog/datenschutz-tipps") == KLASSE_INHALT
        assert klassifiziere("https://x.de/ratgeber/cookie-banner-pflicht") == KLASSE_INHALT

    def test_marketing_landingpage_ist_keine_pflichtseite(self):
        """"/dsgvo-website-check" verkauft eine Prüfung, ist aber keine."""
        assert klassifiziere("https://x.de/dsgvo-website-check") == KLASSE_INHALT
        assert klassifiziere("https://x.de/barrierefreiheit-website-testen") == KLASSE_INHALT

    def test_startseite_und_dateien_werden_uebersprungen(self):
        assert klassifiziere("https://x.de/") is None
        assert klassifiziere("https://x.de") is None
        assert klassifiziere("https://x.de/datenschutz.pdf") is None
        assert klassifiziere("https://x.de/logo.png") is None

    def test_unbekannte_seiten_kosten_kein_budget(self):
        assert klassifiziere("https://x.de/irgendwas") is None
        assert klassifiziere("https://x.de/xyz/123") is None


class TestHostVereinheitlichung:
    def test_www_wird_an_startseite_angeglichen(self):
        """
        Sitemaps liefern oft www, die Links im HTML nicht — ohne Abgleich
        würde dieselbe Seite zweimal gescannt.
        """
        assert _normalisiere("https://www.x.de/agb", host_wie="https://x.de") == "https://x.de/agb"
        assert _normalisiere("https://x.de/agb", host_wie="https://www.x.de") == "https://www.x.de/agb"

    def test_fremde_domain_bleibt_unberuehrt(self):
        assert _normalisiere("https://andere.de/agb", host_wie="https://x.de") == "https://andere.de/agb"

    def test_trailing_slash_und_fragment(self):
        assert _normalisiere("https://x.de/agb/") == "https://x.de/agb"
        assert _normalisiere("https://x.de/agb#unten") == "https://x.de/agb"


def _issue(title, seite, severity="warning", category="barrierefreiheit"):
    i = ComplianceIssue(
        category=category, severity=severity, title=title, description="",
        risk_euro=100, recommendation="", legal_basis="",
    )
    i.metadata = {"page_url": seite}
    return i


class TestFundstellen:
    """
    Der eigentliche Gewinn der Mehrseiten-Prüfung ist nicht "mehr Befunde",
    sondern die Antwort auf "wo überall?". In der ersten Fassung gingen alle
    14 Unterseiten-Befunde von panoart360.de verloren, weil sie denselben
    Titel trugen wie ein Startseiten-Befund.
    """

    def test_seiten_werden_gesammelt(self):
        issues = [
            _issue("Fehlende semantische HTML-Elemente", "https://x.de"),
            _issue("Fehlende semantische HTML-Elemente", "https://x.de/agb"),
            _issue("Fehlende semantische HTML-Elemente", "https://x.de/kontakt"),
        ]
        ergebnis = dedupe_issues(issues)
        assert len(ergebnis) == 1
        meta = ergebnis[0].metadata
        assert meta["seiten_betroffen"] == 3
        assert "https://x.de/agb" in meta["fundstellen"]
        assert "https://x.de/kontakt" in meta["fundstellen"]

    def test_einzelner_fund_bekommt_keine_fundstellenliste(self):
        """Kein Rauschen, wenn ein Mangel nur einmal vorkommt."""
        ergebnis = dedupe_issues([_issue("Nur hier", "https://x.de")])
        assert "fundstellen" not in (ergebnis[0].metadata or {})

    def test_schwerste_stufe_gewinnt_auch_ueber_seiten(self):
        issues = [
            _issue("Formularfelder ohne Label", "https://x.de", "warning"),
            _issue("Formularfelder ohne Label", "https://x.de/kontakt", "critical"),
        ]
        ergebnis = dedupe_issues(issues)
        assert len(ergebnis) == 1
        assert ergebnis[0].severity == "critical"
        assert ergebnis[0].metadata["seiten_betroffen"] == 2

    def test_verschiedene_maengel_bleiben_getrennt(self):
        issues = [
            _issue("Kontrast zu gering", "https://x.de"),
            _issue("Skip-Link fehlt", "https://x.de/agb"),
        ]
        assert len(dedupe_issues(issues)) == 2
