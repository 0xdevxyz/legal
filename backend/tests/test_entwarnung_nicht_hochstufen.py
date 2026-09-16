"""Ein Gesetzes-Update bewertet nicht. Es steht daneben.

`apply_updates_to_scan_results` hob bis zum 15.09.2026 JEDEN Befund einer
Kategorie eine Stufe an, sobald dazu ein kritisches Update vorlag, und erhoehte
sein Risiko um die Haelfte. Getroffen hat das zuerst die Befunde, die gerade
KEINEN Mangel melden ("Kein Cookie-Banner erforderlich", "Struktur-Reparatur
vorbereitet"): Gesamtscore complyo.de 92 -> 90 ab dem 11.09.2026.

Am 16.09.2026 fiel auch die zweite Haelfte der Regel. Gemessen an den 339
aktiven Updates hatten cookies (141 relevante), datenschutz (139) und
barrierefreiheit (35) DAUERHAFT ein kritisches Update: jeder Mangel dieser drei
Saeulen zaehlte permanent 25 statt 8 Punkte, waehrend shop und
ai_act_transparency unberuehrt blieben, weil sie im Kategorien-Woerterbuch
fehlten. Verschaerft wurde nach Wortliste, nicht nach Schwere.

Was ein Befund wiegt, entscheidet der Check, der ihn gemessen hat.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.legal_update_integration import LegalUpdateIntegration


KRITISCHES_UPDATE = {
    "id": 675,
    "title": "Aktualisierte Guidance zu Cookie-Consent-Gültigkeitsdauer",
    "url": "https://www.datenschutzkonferenz-online.de/",
    "severity": "critical",
    "category": "cookies",
    "update_type": "court_ruling",
    "description": "Cookie-Einwilligung, Gueltigkeitsdauer",
}


def _anwenden(issues, updates=None):
    scan = {"issues": issues, "total_risk_euro": 1000}
    return LegalUpdateIntegration(db_pool=None).apply_updates_to_scan_results(
        scan, updates or [KRITISCHES_UPDATE])


def _befund(severity, risiko, titel):
    return {"category": "cookies", "severity": severity, "risk_euro": risiko,
            "title": titel}


class TestDieStufeBleibtWieGemessen:
    def test_entwarnung_bleibt_info(self):
        """Der gemessene Fall von complyo.de."""
        b = _anwenden([_befund("info", 0, "Kein Cookie-Banner erforderlich")])["issues"][0]
        assert b["severity"] == "info"

    def test_vorbereitete_reparatur_bleibt_info(self):
        """complyo darf den Kunden nicht dafuer bestrafen, dass es repariert."""
        b = _anwenden([_befund("info", 0, "Struktur-Reparatur vorbereitet")])["issues"][0]
        assert b["severity"] == "info"

    def test_warnung_bleibt_warnung(self):
        """Die zweite Haelfte der alten Regel: kein 'critical' per Wortliste."""
        b = _anwenden([_befund("warning", 2000, "Banner ohne gleichwertigen Ablehnen-Knopf")])["issues"][0]
        assert b["severity"] == "warning"

    def test_kritisch_bleibt_kritisch(self):
        b = _anwenden([_befund("critical", 5000, "Tracking vor Einwilligung")])["issues"][0]
        assert b["severity"] == "critical"


class TestDasRisikoBleibtWieGemessen:
    def test_kein_aufschlag_am_befund(self):
        b = _anwenden([_befund("warning", 2000, "Banner ohne Ablehnen-Knopf")])["issues"][0]
        assert b["risk_euro"] == 2000
        assert "risk_increase_reason" not in b

    def test_kein_aufschlag_auf_die_summe(self):
        """Vorher +30 % auf das Gesamtrisiko, sobald irgendein Befund stieg."""
        assert _anwenden([_befund("warning", 2000, "x")])["total_risk_euro"] == 1000


class TestDasUpdateStehtDaneben:
    def test_nachweis_haengt_am_befund(self):
        """Die Information geht nicht verloren, sie bewertet nur nicht mehr."""
        b = _anwenden([_befund("warning", 2000, "x")])["issues"][0]
        assert b["relevant_updates"][0]["id"] == 675

    def test_auch_an_einer_entwarnung(self):
        """Dort ist es eine Beobachtungsempfehlung."""
        b = _anwenden([_befund("info", 0, "Kein Cookie-Banner erforderlich")])["issues"][0]
        assert b["relevant_updates"][0]["id"] == 675

    def test_hoechstens_drei_updates_je_befund(self):
        updates = [dict(KRITISCHES_UPDATE, id=i) for i in range(1, 6)]
        b = _anwenden([_befund("warning", 2000, "x")], updates)["issues"][0]
        assert len(b["relevant_updates"]) == 3

    def test_fremde_kategorie_bekommt_nichts(self):
        b = _anwenden([{"category": "shop", "severity": "warning",
                        "risk_euro": 500, "title": "x"}])["issues"][0]
        assert "relevant_updates" not in b

    def test_zaehler_meint_angehaengte_befunde(self):
        """`affected_issues_count` zaehlte vorher Hochstufungen; heute zaehlt es,
        woran ein Update haengt."""
        ergebnis = _anwenden([_befund("info", 0, "a"), _befund("warning", 1, "b")])
        assert ergebnis["affected_issues_count"] == 2
        assert ergebnis["legal_updates_applied"] is True


class TestKeineBewertungMehrImModul:
    def test_die_methode_schreibt_keine_stufe(self):
        """Regressionsschutz gegen die Rueckkehr der Hochstufung."""
        import inspect
        src = inspect.getsource(LegalUpdateIntegration.apply_updates_to_scan_results)
        assert "issue['severity'] =" not in src
        assert "issue['risk_euro'] =" not in src
        assert "* 1.3" not in src and "* 1.5" not in src

    def test_der_tote_severity_helfer_ist_weg(self):
        """`_get_max_severity` diente ausschliesslich der abgeschafften
        Hochstufung; kein Aufrufer bleibt uebrig (16.09.2026)."""
        assert not hasattr(LegalUpdateIntegration, "_get_max_severity")
