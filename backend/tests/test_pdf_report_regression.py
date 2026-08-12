"""Regression: PDF-Download darf an echten Scan-Daten nicht mehr scheitern.

Zwei Fehler haben live jeden Download in einen 500 laufen lassen:
1. `pillar_scores` kommt aus dem Scanner als LISTE, der Report rief `.items()`
   darauf auf -> AttributeError.
2. Empfehlungstexte enthalten HTML-Beispiele (`<a href="#main" class="...">`),
   die ReportLabs Mini-HTML-Parser mit ValueError ablehnt.
"""
import pytest

from compliance_engine.pdf_generator import ComplianceReportGenerator


@pytest.fixture
def generator():
    return ComplianceReportGenerator()


def _ist_pdf(bytes_) -> bool:
    return bytes_[:4] == b"%PDF" and len(bytes_) > 2000


def test_saeulen_als_liste_erzeugen_ein_pdf(generator):
    """Die Form, in der der Scanner die Saeulen wirklich ablegt."""
    daten = {
        "url": "https://example.org",
        "compliance_score": 42,
        "pillar_scores": [
            {"pillar": "datenschutz", "score": 100},
            {"pillar": "cookies", "score": 10},
            {"pillar": "impressum", "score": 100},
            {"pillar": "barrierefreiheit", "score": 55},
        ],
        "issues": [
            {"title": "Cookie ohne Einwilligung", "description": "x",
             "severity": "critical", "category": "cookies"},
        ],
    }
    assert _ist_pdf(generator.generate_compliance_report(daten))


def test_saeulen_als_dict_funktionieren_weiter(generator):
    """Die alte Dict-Form darf nicht kaputtgehen."""
    daten = {
        "url": "https://example.org",
        "compliance_score": 80,
        "pillar_scores": {"cookies": {"score": 80, "issues": 2}},
        "issues": [],
    }
    assert _ist_pdf(generator.generate_compliance_report(daten))


def test_html_in_empfehlung_bricht_den_report_nicht(generator):
    """Genau der Text, an dem live jeder Download starb."""
    daten = {
        "url": "https://example.org",
        "compliance_score": 30,
        "pillar_scores": [{"pillar": "barrierefreiheit", "score": 30}],
        "issues": [
            {
                "title": "Skip-Link fehlt",
                "description": "Kein Sprunglink vorhanden",
                "severity": "warning",
                "category": "barrierefreiheit",
                "recommendation": (
                    'Fügen Sie am Seitenanfang einen versteckten Skip-Link ein: '
                    '<a href="#main" class="skip-link">Zum Inhalt springen</a>.'
                ),
            }
        ],
    }
    assert _ist_pdf(generator.generate_compliance_report(daten))


def test_unbalanciertes_markup_bricht_den_report_nicht(generator):
    """Abgeschnittene Empfehlungen hinterlassen offene Tags."""
    daten = {
        "url": "https://example.org",
        "compliance_score": 10,
        "pillar_scores": [{"pillar": "cookies", "score": 10}],
        "issues": [
            {
                "title": "Beispiel <div ohne Ende",
                "description": "Text mit <span und & kaufmaennischem Und",
                "severity": "critical",
                "category": "cookies",
                "recommendation": "Setzen Sie <script src=\"...\" >  ohne Abschluss",
            }
        ],
    }
    assert _ist_pdf(generator.generate_compliance_report(daten))


def test_kaputte_saeulen_werden_ignoriert_statt_zu_crashen(generator):
    """Fremdformate duerfen den Report nicht mitreissen."""
    for saeulen in (None, "unsinn", [1, 2, 3], [{"kein_pillar": True}]):
        daten = {
            "url": "https://example.org",
            "compliance_score": 50,
            "pillar_scores": saeulen,
            "issues": [],
        }
        assert _ist_pdf(generator.generate_compliance_report(daten)), saeulen
