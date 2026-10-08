# -*- coding: utf-8 -*-
"""
complyo nennt keine Bussgeldbetraege je Befund mehr.

"Anschrift fehlt im Impressum: 2.000 EUR" war eine erfundene Zahl. Es gibt
keine Bussgeldpraxis je Pflichtangabe, und was eine Abmahnung kostet, haengt
am Streitwert, nicht am Befund. Fuer einen Anbieter, der Rechtssicherheit
verkauft, ist eine erfundene Rechtsfolge in der Kundenansicht selbst eine
irrefuehrende Angabe (Paragraph 5 UWG). Entschieden am 07.10.2026.

An die Stelle des Betrags tritt eine Rangstufe aus Wichtigkeit (Rechtsfolge)
und Dringlichkeit (bekannte Abmahnwelle). Dieser Waechter haelt drei Dinge
fest:

1. Die Rangstufe folgt der Matrix und nennt ihre Begruendung.
2. Kein Antwortobjekt traegt mehr einen Euro-Schluessel.
3. Kein Kundentext in Backend, Dashboard oder Landing beziffert ein Bussgeld.

Was im Abmahn-Radar an Euro steht (typische Forderung mit Quelle), bleibt
dort und ist hier ausdruecklich erlaubt: belegte Praxis einer konkreten Welle.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine import rangstufe as rs

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)


# ---------------------------------------------------------------------------
# 1. Rangstufe
# ---------------------------------------------------------------------------

def _befund(**kw):
    basis = {"category": "impressum", "severity": "critical",
             "title": "Anschrift fehlt im Impressum", "description": "", "is_missing": False}
    basis.update(kw)
    return basis


class TestRangMatrix:
    def test_kritisch_mit_welle_ist_sofort(self):
        r = rs.rang_bestimmen(_befund(category="datenschutz", severity="critical",
                                      title="Google Fonts werden von Google-Servern geladen"))
        assert r["rang"] == rs.SOFORT
        assert "Google Fonts" in r["rang_begruendung"]

    def test_kritisch_mit_impressum_welle_ist_sofort(self):
        r = rs.rang_bestimmen(_befund())
        assert r["rang"] == rs.SOFORT
        assert "Impressum" in r["rang_begruendung"]

    def test_kategorie_allein_ist_kein_stichwort(self):
        """Die Kategorie impressum macht einen Befund nicht zum Wellen-Treffer."""
        r = rs.rang_bestimmen(_befund(title="Vorstand nicht angegeben", category="impressum"))
        assert r["rang"] == rs.ALS_NAECHSTES

    def test_kritisch_ohne_welle_ist_als_naechstes(self):
        r = rs.rang_bestimmen(_befund(title="Vorstand nicht angegeben", category="impressum"))
        assert r["rang"] == rs.ALS_NAECHSTES
        assert r["rang_label"] == "Als Nächstes"

    def test_warnung_mit_fehlendem_element_ist_wichtig(self):
        r = rs.rang_bestimmen(_befund(severity="warning", is_missing=True, title="Keine AGB gefunden"))
        assert r["rang"] == rs.ALS_NAECHSTES

    def test_warnung_ist_einplanen(self):
        r = rs.rang_bestimmen(_befund(severity="warning", title="Telefonnummer fehlt"))
        assert r["rang"] == rs.EINPLANEN

    def test_info_ist_hinweis(self):
        r = rs.rang_bestimmen(_befund(severity="info", title="Impressum: 2 Angaben nicht abschliessend geprueft"))
        assert r["rang"] == rs.HINWEIS

    def test_welle_braucht_dieselbe_saeule(self):
        """'consent' in einem Barrierefreiheits-Befund ist keine Cookie-Welle."""
        r = rs.rang_bestimmen(_befund(category="barrierefreiheit", severity="critical",
                                      title="Consent-Dialog ohne sichtbaren Fokusrahmen"))
        assert r["rang"] == rs.ALS_NAECHSTES

    def test_welle_derselben_saeule_trifft(self):
        """'tastatur' ist ein Stichwort der BFSG-Welle, Saeule accessibility."""
        r = rs.rang_bestimmen(_befund(category="barrierefreiheit", severity="critical",
                                      title="Dialog ohne Tastaturfokus"))
        assert r["rang"] == rs.SOFORT

    def test_jede_stufe_hat_label_und_begruendung(self):
        for schwere, missing in (("critical", False), ("warning", True), ("warning", False), ("info", False)):
            r = rs.rang_bestimmen(_befund(severity=schwere, is_missing=missing))
            assert r["rang"] in rs.STUFEN
            assert r["rang_label"] == rs.LABEL[r["rang"]]
            assert r["rang_begruendung"].endswith(".")
            assert "€" not in r["rang_begruendung"]

    def test_anreichern_und_sortieren(self):
        befunde = [_befund(severity="info"), _befund(severity="critical",
                   category="datenschutz", title="Google Fonts extern"), _befund(severity="warning")]
        angereichert = rs.rang_anreichern(befunde + ["Altformat: reiner Text"])
        assert angereichert[-1] == "Altformat: reiner Text"
        sortiert = rs.nach_rang_sortiert(angereichert[:3])
        assert [b["rang"] for b in sortiert] == [rs.SOFORT, rs.EINPLANEN, rs.HINWEIS]


# ---------------------------------------------------------------------------
# 2. Kein Euro-Schluessel in Antworten
# ---------------------------------------------------------------------------

class TestOhneEurobetraege:
    def test_entfernt_rekursiv(self):
        antwort = {
            "total_risk_euro": 5000,
            "issues": [{"title": "x", "risk_euro": 2000, "risk_range": "1-2"}],
            "issue_groups": [{"total_risk_euro": 3, "sub_issues": [{"risk_euro_max": 1}]}],
            "behalten": {"privacy_risk_euro": 1, "name": "ok"},
        }
        sauber = rs.ohne_eurobetraege(antwort)
        assert sauber == {
            "issues": [{"title": "x"}],
            "issue_groups": [{"sub_issues": [{}]}],
            "behalten": {"name": "ok"},
        }
        assert antwort["total_risk_euro"] == 5000, "das Original bleibt unangetastet"

    def test_compliance_issue_modell_ohne_betrag(self):
        from public_routes import ComplianceIssue, IssueLocation, IssueSolution
        i = ComplianceIssue(
            id="a", category="impressum", severity="critical", title="t", description="d",
            legal_basis="DDG", location=IssueLocation(area="x", hint="y"),
            solution=IssueSolution(code_snippet="", steps=[]), auto_fixable=False,
            **rs.rang_bestimmen(_befund()),
        )
        assert i.risk_euro_min is None and i.risk_euro_max is None and i.risk_range is None
        # "Anschrift fehlt im Impressum" trifft die Impressum-Welle des Radars.
        assert i.rang == rs.SOFORT

    def test_vorschau_bereiche_ohne_betrag(self):
        import asyncio
        from public_routes import _aggregate_risk_categories

        class KeinRechner:
            async def calculate_issue_risk(self, *a, **kw):
                raise AssertionError("die Vorschau darf keinen Betrag mehr berechnen")

        bereiche = asyncio.run(_aggregate_risk_categories(
            [{"category": "cookies", "severity": "critical", "title": "Tracking vor Einwilligung"},
             {"category": "impressum", "severity": "info", "title": "Hinweis"}],
            KeinRechner(),
        ))
        for b in bereiche:
            assert not (set(b) & rs.EURO_SCHLUESSEL), b
        cookies = next(b for b in bereiche if b["id"] == "cookies")
        assert cookies["detected"] and cookies["severity"] == "critical"


# ---------------------------------------------------------------------------
# 3. Kein Kundentext beziffert ein Bussgeld
# ---------------------------------------------------------------------------

# Formulierungen, die einen Betrag als Rechtsfolge behaupten. Jede davon
# stand am 07.10.2026 in einer Kundenansicht.
VERBOTEN = (
    "€ Bußgeld", "€ Bussgeld", "Bußgeld-Risiko", "Bussgeld-Risiko",
    "Geschätztes Risiko", "Geschaetztes Risiko", "Bußgeld vermieden",
    "Potentielles Bußgeld", "Typische Abmahnkosten", "Risiko-Reduktion:</strong> €",
    "Bußgeldrahmen bis ${", "risk_euro_max}€",
)

# Ausgenommen: belegte Praxis (Abmahn-Radar), Ratgeberartikel mit Quellen,
# Vertragstexte, Adminansichten, Tests und Archive.
AUSGENOMMEN = (
    "AbmahnRadar", "/ratgeber/", "/agb/", "/admin/", "/tests/", "/_archive",
    "node_modules", "/.next/", "/md/", "abmahnwellen.py", "CHANGELOG",
    # internes Rechenmodell ohne Ausgabe, nur noch von test_gesamtrisiko benutzt
    "backend/risk_calculator.py",
)

WURZELN = (
    os.path.join(BACKEND),
    os.path.join(REPO, "dashboard-react", "src"),
    os.path.join(REPO, "landing-react", "src"),
)
ENDUNGEN = (".py", ".ts", ".tsx")


def _dateien():
    for wurzel in WURZELN:
        for ordner, unter, namen in os.walk(wurzel):
            unter[:] = [u for u in unter if u not in ("node_modules", ".next", "__pycache__", "_archive_pre_baseline", "tests")]
            for n in namen:
                pfad = os.path.join(ordner, n)
                if n.endswith(ENDUNGEN) and not any(a in pfad for a in AUSGENOMMEN):
                    yield pfad


def test_kein_kundentext_beziffert_ein_bussgeld():
    treffer = []
    for pfad in _dateien():
        try:
            quelle = open(pfad, encoding="utf-8").read()
        except Exception:
            continue
        for zeile_nr, zeile in enumerate(quelle.splitlines(), 1):
            if any(v in zeile for v in VERBOTEN):
                treffer.append(f"{os.path.relpath(pfad, REPO)}:{zeile_nr}: {zeile.strip()[:100]}")
    assert not treffer, "Bussgeld beziffert in:\n" + "\n".join(treffer)


def test_vorschau_antwort_ohne_gesamtrisiko():
    """Die Landing-Vorschau bekommt keine Spanne mehr, nur Zaehlungen."""
    quelle = open(os.path.join(BACKEND, "public_routes.py"), encoding="utf-8").read()
    for schluessel in ("total_risk_range", "total_risk_min", "total_risk_max", "rahmen_max"):
        assert f'"{schluessel}":' not in quelle, schluessel


def test_landing_liest_keine_risikospanne_mehr():
    pfad = os.path.join(REPO, "landing-react", "src", "components", "landing", "WebsiteScanner.tsx")
    quelle = open(pfad, encoding="utf-8").read()
    assert "total_risk_min" not in quelle and "rahmen_max" not in quelle
