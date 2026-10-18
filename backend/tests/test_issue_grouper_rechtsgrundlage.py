"""Keine Gruppenkarte ohne Rechtsgrundlage.

Gemessen am 16.10.2026 in scan_history.scan_data der letzten 40 Scans: alle
1.185 Einzelbefunde trugen eine legal_basis, alle 41 Gruppenkarten aus
issue_grouper.py keine ("Datenschutzerklaerung fehlt komplett" 20, "Cookie
Issues" 15, "Shop Issues" 5, "Cookies Issues" 1). Startseite und Erklaervideo
versprechen "jeder Befund mit Rechtsgrundlage", und die Gruppenkarte ist der
Befund, den der Kunde zuerst sieht.

Regel: die Gruppe uebernimmt die Rechtsgrundlage ihres Hauptbefunds, sonst die
des ersten Mitglieds mit Angabe, und faellt erst dann auf eine feste Angabe je
Kategorie zurueck. Die festen Angaben kommen fuer nationale Anker aus
rechtsgrundlagen.py, damit der Rechtsraum mitwandert.
"""
import pytest

from compliance_engine.issue_grouper import IssueGrouper
from compliance_engine.rechtsgrundlagen import (
    AGB_KONTROLLE,
    ANBIETERKENNZEICHNUNG,
    COOKIE_EINWILLIGUNG,
    PREISANGABE,
    WIDERRUF,
    grundlage,
)


def _befund(category, title, legal_basis=None, is_missing=True, severity="critical"):
    issue = {
        "id": f"{category}_{title}",
        "category": category,
        "title": title,
        "severity": severity,
        "is_missing": is_missing,
        "risk_euro": 100,
    }
    if legal_basis is not None:
        issue["legal_basis"] = legal_basis
    return issue


def _gruppe(issues, jurisdiction="de"):
    """Mehr als drei fehlende Befunde einer Kategorie ergeben eine Gruppe."""
    ergebnis = IssueGrouper().group_issues(issues, jurisdiction)
    assert ergebnis["issue_groups"], "Erwartet wurde eine Gruppenkarte"
    return ergebnis["issue_groups"]


# ---------------------------------------------------------------------------
# 1. Hauptbefund zuerst
# ---------------------------------------------------------------------------
def test_gruppe_uebernimmt_rechtsgrundlage_des_hauptbefunds():
    issues = [
        _befund("datenschutz", "Datenschutzerklärung fehlt", "DSGVO Art. 13-14"),
        _befund("datenschutz", "Verantwortlicher fehlt", "DSGVO Art. 13 Abs. 1 lit. a"),
        _befund("datenschutz", "Zweck fehlt", "DSGVO Art. 13 Abs. 1 lit. c"),
        _befund("datenschutz", "Speicherdauer fehlt", "DSGVO Art. 13 Abs. 2 lit. a"),
    ]
    (gruppe,) = _gruppe(issues)
    assert gruppe["title"] == "Datenschutzerklärung fehlt komplett"
    assert gruppe["parent_issue"]["title"] == "Datenschutzerklärung fehlt"
    assert gruppe["legal_basis"] == "DSGVO Art. 13-14"


def test_ohne_hauptbefund_zaehlt_das_erste_mitglied_mit_angabe():
    issues = [
        _befund("shop", "AGB unvollständig", ""),
        _befund("shop", "Widerrufsbelehrung unvollständig",
                "BGB §355 Abs. 2, EGBGB Art. 246a §1"),
        _befund("shop", "Gesamtpreis unklar", "PAngV §3 Abs. 1, UWG §3a"),
        _befund("shop", "Versandkosten unklar", "PAngV §3 Abs. 2"),
    ]
    (gruppe,) = _gruppe(issues)
    assert gruppe["legal_basis"] in {
        "BGB §355 Abs. 2, EGBGB Art. 246a §1",
        "PAngV §3 Abs. 1, UWG §3a",
        "PAngV §3 Abs. 2",
    }
    assert gruppe["legal_basis"]


# ---------------------------------------------------------------------------
# 2. Fester Rueckfall je Kategorie, Anker aus rechtsgrundlagen.py
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("category,erwartet", [
    ("datenschutz", "DSGVO Art. 13"),
    ("impressum", grundlage(ANBIETERKENNZEICHNUNG, "de")),
    ("cookies", grundlage(COOKIE_EINWILLIGUNG, "de") + ", DSGVO Art. 6 Abs. 1 lit. a"),
    ("cookie", grundlage(COOKIE_EINWILLIGUNG, "de") + ", DSGVO Art. 6 Abs. 1 lit. a"),
    ("shop", ", ".join(grundlage(t, "de") for t in (WIDERRUF, PREISANGABE, AGB_KONTROLLE))),
])
def test_rueckfall_je_kategorie_deutsch(category, erwartet):
    issues = [_befund(category, f"Angabe {n} fehlt") for n in range(4)]
    (gruppe,) = _gruppe(issues, "de")
    assert gruppe["legal_basis"] == erwartet
    assert erwartet  # der Rueckfall selbst darf nie leer sein


def test_rueckfall_deutsche_schreibweise_wie_im_pruefkern():
    """Die Anker stehen so, wie sie die Einzelbefunde heute ausgeben."""
    issues = [_befund("impressum", f"Angabe {n} fehlt") for n in range(4)]
    (gruppe,) = _gruppe(issues, "de")
    assert gruppe["legal_basis"] == "DDG §5"

    issues = [_befund("cookies", f"Angabe {n} fehlt") for n in range(4)]
    (gruppe,) = _gruppe(issues, "de")
    assert gruppe["legal_basis"] == "TDDDG §25, DSGVO Art. 6 Abs. 1 lit. a"


def test_rueckfall_folgt_dem_rechtsraum():
    """Ausserhalb Deutschlands kein deutsches Gesetz, sondern die Richtlinie."""
    issues = [_befund("cookies", f"Angabe {n} fehlt") for n in range(4)]
    (gruppe,) = _gruppe(issues, "eu")
    assert gruppe["legal_basis"] == (
        "Richtlinie 2002/58/EG Art. 5 Abs. 3, DSGVO Art. 6 Abs. 1 lit. a")
    assert "TDDDG" not in gruppe["legal_basis"]


def test_enrich_scan_results_reicht_den_rechtsraum_durch():
    scan = {
        "jurisdiction": "eu",
        "issues": [_befund("cookies", f"Angabe {n} fehlt") for n in range(4)],
    }
    ergebnis = IssueGrouper().enrich_scan_results(scan)
    (gruppe,) = ergebnis["issue_groups"]
    assert gruppe["legal_basis"].startswith("Richtlinie 2002/58/EG")


# ---------------------------------------------------------------------------
# 3. Alt-Text-Gruppe (Strategie 2)
# ---------------------------------------------------------------------------
def test_alt_text_gruppe_uebernimmt_wcag_angabe():
    issues = [
        _befund("accessibility", f"Bild {n} ohne Alt-Text",
                "WCAG 2.1 Level A (1.1.1), BFSG §12", is_missing=False)
        for n in range(3)
    ]
    (gruppe,) = _gruppe(issues)
    assert gruppe["group_id"] == "accessibility_images"
    assert gruppe["legal_basis"] == "WCAG 2.1 Level A (1.1.1), BFSG §12"


# ---------------------------------------------------------------------------
# 4. Die Messung vom 16.10.: ein gemischter Scan ergibt keine leere Karte
# ---------------------------------------------------------------------------
def test_keine_gruppenkarte_ohne_rechtsgrundlage():
    issues = []
    for category in ("datenschutz", "impressum", "cookies", "cookie", "shop"):
        issues += [_befund(category, f"{category} Angabe {n} fehlt") for n in range(5)]
    issues += [
        _befund("accessibility", f"Bild {n} ohne Alt-Text", "WCAG 2.1 Level A (1.1.1), BFSG §12",
                is_missing=False)
        for n in range(3)
    ]
    ergebnis = IssueGrouper().enrich_scan_results({"issues": issues, "jurisdiction": "de"})
    gruppen = ergebnis["issue_groups"]
    assert len(gruppen) == 6
    leer = [g["title"] for g in gruppen if not (g.get("legal_basis") or "").strip()]
    assert leer == [], f"Gruppenkarten ohne Rechtsgrundlage: {leer}"
