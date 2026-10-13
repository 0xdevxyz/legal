"""
BFSG-Einordnung nach Unternehmensprofil und Messprotokoll (13.10.2026).

Drei Profile, drei Stufen. Die Messung bleibt (Schweregrad, Punktestand),
Betrag und Rechtsgrundlage folgen der Einordnung. Kein Text darf ein
Rechtsurteil behaupten ("nicht betroffen"). Bestandenes entsteht aus dem
axe-Messprotokoll, nie aus der Abwesenheit von Befunden.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import bfsg_einordnung as be
from compliance_engine import messprotokoll as mp
from compliance_engine.scanner import ComplianceIssue

PROFIL_GREIFT = {"employees": "10-49", "revenue": "2-10m", "b2c": True, "online_shop": True}
PROFIL_KLEINST = {"employees": "1-9", "revenue": "<=2m", "b2c": True, "digital_service": True}
PROFIL_B2B = {"employees": "10-49", "revenue": "2-10m", "b2c": False, "online_shop": False}


def _issue(title, severity="warning", risk=500, category="barrierefreiheit",
           legal_basis="WCAG 2.1 Level A (1.1.1), BFSG §12"):
    return ComplianceIssue(category=category, severity=severity, title=title,
                           description="", risk_euro=risk, recommendation="r",
                           legal_basis=legal_basis)


# --------------------------------------------------------------------------
# einordnen
# --------------------------------------------------------------------------

def test_drei_profile_drei_stufen():
    assert be.einordnen(PROFIL_GREIFT, seitenmerkmale=True)["status"] == be.GREIFT
    assert be.einordnen(PROFIL_KLEINST, seitenmerkmale=True)["status"] == be.OFFEN
    assert be.einordnen(PROFIL_B2B, seitenmerkmale=False)["status"] == be.NICHT_ANGEZEIGT


def test_ohne_profil_bleibt_offen():
    e = be.einordnen(None, seitenmerkmale=False)
    assert e["status"] == be.OFFEN
    assert e["profil_vorhanden"] is False
    assert e["profil_pfad"] == "/pflichten-report"
    assert "profil" in e["text"].lower()


def test_profil_ohne_pflichtfelder_zaehlt_als_fehlend():
    e = be.einordnen({"b2c": True, "online_shop": True}, seitenmerkmale=True)
    assert e["status"] == be.OFFEN and e["profil_vorhanden"] is False


def test_widerspruch_profil_gegen_seite_wird_offen():
    """Profil sagt kein Online-Vertrag, die Seite zeigt eine Kasse: nachfragen."""
    e = be.einordnen(PROFIL_B2B, seitenmerkmale=True)
    assert e["status"] == be.OFFEN
    assert any("Profil" in g for g in e["gruende"])


def test_beschriftung_der_saeule():
    assert be.einordnen(PROFIL_GREIFT, seitenmerkmale=True)["saeulen_beschriftung"] == "Barrierefreiheit (BFSG)"
    assert be.einordnen(PROFIL_B2B, seitenmerkmale=False)["saeulen_beschriftung"] == "Barrierefreiheit (WCAG 2.1 AA)"
    assert "offen" in be.einordnen(None, seitenmerkmale=False)["saeulen_beschriftung"]


def test_kriterien_zeigen_profilwerte():
    e = be.einordnen(PROFIL_KLEINST, seitenmerkmale=False)
    werte = {k["schluessel"]: k["wert"] for k in e["kriterien"]}
    assert werte["beschaeftigte"] == "1 bis 9"
    assert werte["umsatz"] == "bis 2 Mio. €"
    assert werte["verbraucher"] == "ja"
    assert werte["online_vertrag"] == "ja"
    assert werte["kleinstunternehmen"] == "ja"
    assert werte["seitenmerkmale"] == "nein"


@pytest.mark.parametrize("profil,merkmale", [
    (PROFIL_GREIFT, True), (PROFIL_KLEINST, True), (PROFIL_B2B, False),
    (PROFIL_B2B, True), (None, False), (None, True),
])
def test_kein_rechtsurteil_im_text(profil, merkmale):
    """RDG: 'nach Ihren Angaben', 'pruefen', nie 'Sie sind nicht betroffen'."""
    e = be.einordnen(profil, seitenmerkmale=merkmale)
    gesamt = " ".join([e["text"], e["label"], e["hinweis"], e["saeulen_beschreibung"]] + e["gruende"]).lower()
    assert not re.search(r"nicht betroffen|sind sie (nicht )?verpflichtet|gilt nicht f", gesamt), gesamt
    assert "angaben" in gesamt or "prüfen" in gesamt or "pruefen" in gesamt


def test_einordnung_stimmt_mit_pflichtenradar_ueberein():
    from pflichten_katalog import evaluate_pflichten
    for profil in (PROFIL_GREIFT, PROFIL_KLEINST, PROFIL_B2B):
        radar = next(i for i in evaluate_pflichten(profil)["items"] if i["id"] == "bfsg")
        assert be.einordnen(profil, seitenmerkmale=False)["status"] == radar["status"]


# --------------------------------------------------------------------------
# anwenden
# --------------------------------------------------------------------------

def test_nicht_angezeigt_nimmt_betrag_und_anker_heraus():
    e = be.einordnen(PROFIL_B2B, seitenmerkmale=False)
    issues = [
        _issue("Bild ohne Alt-Text", "critical", 500),
        _issue("Barrierefreiheitserklärung fehlt (BFSG §14)", "warning", 2000,
               legal_basis="EU-Richtlinie 2019/882 (European Accessibility Act), BFSG §14"),
        _issue("Impressum fehlt", "critical", 3000, category="impressum", legal_basis="DDG §5"),
    ]
    out = be.anwenden(issues, e)
    alt, erkl, impressum = out
    assert alt.severity == "critical", "Schweregrad ist Messung und bleibt"
    assert alt.risk_euro == 0
    assert "BFSG §12" not in alt.legal_basis
    assert alt.legal_basis.startswith("WCAG 2.1 Level A (1.1.1)")
    assert "nach Ihren Angaben" in alt.legal_basis
    assert alt.metadata["bfsg_einordnung"] == be.NICHT_ANGEZEIGT
    assert erkl.severity == "info" and erkl.risk_euro == 0
    assert "keine BFSG-Pflicht" in erkl.title
    assert impressum.risk_euro == 3000 and impressum.legal_basis == "DDG §5"


def test_greift_laesst_messung_und_betrag():
    e = be.einordnen(PROFIL_GREIFT, seitenmerkmale=True)
    issues = [_issue("Bild ohne Alt-Text", "critical", 500),
              _issue("Barrierefreiheitserklärung fehlt, nur Pflicht für B2C-Dienste", "info", 0)]
    alt, erkl = be.anwenden(issues, e)
    assert alt.risk_euro == 500 and alt.legal_basis.endswith("BFSG §12")
    assert erkl.severity == "warning" and erkl.risk_euro == 2000 and "§14" in erkl.title


def test_offen_betrag_null_grundlage_bleibt():
    e = be.einordnen(None, seitenmerkmale=False)
    (alt,) = be.anwenden([_issue("Bild ohne Alt-Text", "warning", 500)], e)
    assert alt.risk_euro == 0
    assert "BFSG §12" in alt.legal_basis and "offen" in alt.legal_basis


def test_anwenden_ist_idempotent():
    e = be.einordnen(PROFIL_B2B, seitenmerkmale=False)
    (alt,) = be.anwenden([_issue("Bild ohne Alt-Text")], e)
    einmal = alt.legal_basis
    be.anwenden([alt], e)
    assert alt.legal_basis == einmal


def test_anwenden_mit_dicts_und_ohne_einordnung():
    d = {"category": "barrierefreiheit", "severity": "warning", "title": "x",
         "risk_euro": 300, "legal_basis": "BFSG §12, WCAG 2.1 (1.3.1)"}
    assert be.anwenden([d], None)[0]["risk_euro"] == 300
    be.anwenden([d], be.einordnen(PROFIL_B2B, seitenmerkmale=False))
    assert d["risk_euro"] == 0 and d["legal_basis"].startswith("WCAG 2.1 (1.3.1)")


def test_ohne_bfsg_anker():
    assert be.ohne_bfsg_anker("WCAG 2.1 Level A (1.1.1), BFSG §12") == "WCAG 2.1 Level A (1.1.1)"
    assert be.ohne_bfsg_anker("BFSG §12, WCAG 2.1 (1.3.1, Info and Relationships)") == "WCAG 2.1 (1.3.1, Info and Relationships)"
    assert be.ohne_bfsg_anker("BFSG §14") == "WCAG 2.1"


# --------------------------------------------------------------------------
# Messprotokoll
# --------------------------------------------------------------------------

REGELN_A = [
    {"id": "image-alt", "help": "Images must have alternate text", "description": "d",
     "helpUrl": "https://dequeuniversity.com/rules/axe/4.8/image-alt", "tags": ["wcag2a", "wcag111"], "nodes": [1, 2, 3]},
    {"id": "region", "help": "All page content should be contained by landmarks", "description": "d",
     "tags": ["best-practice"], "nodes": [1]},
]
REGELN_B = [
    {"id": "image-alt", "help": "Images must have alternate text", "description": "d",
     "tags": ["wcag2a", "wcag111"], "nodes": [1]},
    {"id": "label", "help": "Form elements must have labels", "description": "d",
     "tags": ["wcag2a", "wcag412"], "nodes": [2, 2]},
]


def _normiert(regeln):
    return [{**r, "nodes": len(r["nodes"])} for r in regeln]


def test_marker_wird_herausgezogen_und_zaehlt_nicht():
    issues = [_issue("Bild ohne Alt-Text"), mp.marker("https://a.de/", _normiert(REGELN_A))]
    rest, saetze = mp.ziehe(issues)
    assert len(rest) == 1 and rest[0].title == "Bild ohne Alt-Text"
    assert len(saetze) == 1 and saetze[0]["page_url"] == "https://a.de/"
    assert [r["id"] for r in saetze[0]["regeln"]] == ["image-alt", "region"]


def test_positive_checks_fassen_seiten_zusammen():
    saetze = [
        {"page_url": "https://a.de/", "regeln": _normiert(REGELN_A)},
        {"page_url": "https://a.de/kontakt", "regeln": _normiert(REGELN_B)},
    ]
    pc = mp.positive_checks(saetze, seiten_gesamt=3)
    nach_id = {p["id"]: p for p in pc}
    assert set(nach_id) == {"image-alt", "region", "label"}
    assert nach_id["image-alt"]["seiten"] == 2 and nach_id["image-alt"]["elemente"] == 4
    assert nach_id["image-alt"]["wcag"] == ["1.1.1"]
    assert nach_id["image-alt"]["rechtspflicht"] is True
    assert nach_id["region"]["rechtspflicht"] is False
    assert pc[0]["rechtspflicht"] is True and pc[-1]["id"] == "region", "Rechtspflichten zuerst"
    assert "keine Abweichung" in nach_id["label"]["wortlaut"]
    assert "2 von 3 Seiten" in nach_id["image-alt"]["wortlaut"]
    assert nach_id["image-alt"]["status"] == mp.STATUS


def test_wortwahl_keine_zustandsbehauptung():
    pc = mp.positive_checks([{"page_url": "u", "regeln": _normiert(REGELN_A)}], seiten_gesamt=1)
    for p in pc:
        text = (p["wortlaut"] + " " + p["title"]).lower()
        for verboten in ("erfüllt", "konform", "bestanden"):
            assert verboten not in text, (verboten, text)


def test_axe_result_traegt_bestandene_regeln():
    from compliance_engine.axe_scanner import AxeScanner
    roh = {"violations": [], "passes": REGELN_A, "incomplete": [], "inapplicable": []}
    erg = AxeScanner()._parse_results("https://a.de/", roh)
    assert erg.passes == 2
    assert [b["id"] for b in erg.bestanden] == ["image-alt", "region"]
    assert erg.bestanden[0]["nodes"] == 3 and erg.bestanden[0]["help_url"].endswith("image-alt")
    assert "bestanden" in erg.to_dict()


def test_bestandenes_nicht_mehr_aus_abwesenheit():
    """Der alte Weg (sechs Kategorien gelten als bestanden, wenn kein Befund
    darin liegt, plus 'Grundlegende Anforderungen erfüllt' ab 50 Punkten)
    darf nicht zurueckkommen."""
    pfad = os.path.join(os.path.dirname(__file__), "..", "public_routes.py")
    with open(pfad, encoding="utf-8") as f:
        quelle = f.read()
    assert "_generate_positive_checks" not in quelle
    assert "Grundlegende Compliance-Anforderungen erfüllt" not in quelle
    assert 'scan_result.get("positive_checks")' in quelle
