"""
Was der Besucher als Befund gezaehlt sieht, muss ein Befund sein.

Die Landing zeigt pro Bereich eine Zahl. Diese Zahl entstand bis zum
08.09.2026 nicht aus den Befunden, sondern aus einer zweiten Kategorisierung:
der Beschreibungstext jedes Befundes wurde erneut nach Stichwoertern sortiert.
Im Selbstscan von complyo.de hatte das drei Folgen auf einmal:

  * Der Hinweis "Kein Cookie-Banner erforderlich" — eine Entwarnung mit Risiko
    0 — enthaelt das Wort Cookie und wurde als Cookie-Verstoss gezaehlt.
  * "tracking" stand in zwei Bereichslisten; solche Befunde wurden doppelt
    gezaehlt.
  * Befunde, deren Text in keine Liste passte, verschwanden aus der Anzeige.

13 Befunde ergaben so 12 Zaehlungen, davon zwei doppelt und zwei unsichtbar —
und einen als kritisch markierten DSGVO-Bereich, obwohl kein einziger Befund
kritisch war.
"""

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import public_routes


class RisikoAttrappe:
    """Liefert eine feste Spanne — hier geht es um Zaehlung, nicht um Betraege."""

    def __init__(self):
        self.gefragte_kategorien = []

    async def calculate_issue_risk(self, text, market="DE", category=None):
        self.gefragte_kategorien.append(category)
        return {
            "category": category or "unknown",
            "severity": "warning",
            "risk_min": 1000.0,
            "risk_max": 5000.0,
            "risk_range": "1.000€ - 5.000€",
        }


def befund(kategorie, schwere, titel="Befund", beschreibung="Beschreibung"):
    return {"category": kategorie, "severity": schwere,
            "title": titel, "description": beschreibung}


def aggregiere(issues):
    rechner = RisikoAttrappe()
    bereiche = asyncio.run(
        public_routes._aggregate_risk_categories(issues, rechner)
    )
    return {b["id"]: b for b in bereiche}, rechner


class TestHinweiseSindKeineBefunde:
    def test_entwarnung_zaehlt_nicht_als_verstoss(self):
        # Genau der Satz, den der Cookie-Check ausgibt, wenn alles in Ordnung ist.
        bereiche, _ = aggregiere([befund(
            "cookies", "info",
            "Kein Cookie-Banner erforderlich",
            "Es werden keine einwilligungspflichtigen Cookies gesetzt.",
        )])
        assert bereiche["cookies"]["issues_count"] == 0
        assert bereiche["cookies"]["detected"] is False
        assert bereiche["cookies"]["risk_max"] == 0
        # Verschwinden soll sie trotzdem nicht.
        assert bereiche["cookies"]["hinweise_count"] == 1

    def test_hinweis_treibt_kein_risiko(self):
        bereiche, _ = aggregiere([befund("media_accessibility", "info")])
        assert bereiche["barrierefreiheit"]["risk_max"] == 0


class TestJederBefundGenauEinmal:
    def test_tracking_landet_in_genau_einem_bereich(self):
        bereiche, _ = aggregiere([befund("tracking", "warning")])
        getroffen = [b for b in bereiche.values() if b["issues_count"]]
        assert len(getroffen) == 1
        assert getroffen[0]["id"] == "dsgvo"

    def test_summe_stimmt_mit_der_zahl_der_befunde(self):
        issues = [
            befund("tastaturbedienung", "warning"),
            befund("cookie", "warning"),
            befund("tracking", "warning"),
            befund("datenschutz", "warning"),
            befund("shop", "critical"),
            befund("media_accessibility", "info"),
        ]
        bereiche, _ = aggregiere(issues)
        assert sum(b["issues_count"] for b in bereiche.values()) == 5
        assert sum(b["hinweise_count"] for b in bereiche.values()) == 1

    def test_unbekannte_kategorie_faellt_nicht_heraus(self):
        bereiche, _ = aggregiere([befund("voellig_neue_kategorie", "warning")])
        assert sum(b["issues_count"] for b in bereiche.values()) == 1


class TestSchweregradKommtVomBefund:
    def test_kritisch_bleibt_kritisch(self):
        bereiche, _ = aggregiere([befund("shop", "critical")])
        assert bereiche["shop"]["severity"] == "critical"
        assert bereiche["shop"]["critical_count"] == 1

    def test_warnung_wird_nicht_zu_kritisch(self):
        # Vier Warnungen im Datenschutz ergaben frueher einen kritischen
        # DSGVO-Bereich, weil die Matrixzeile "datenschutz" critical traegt.
        bereiche, _ = aggregiere([befund("datenschutz", "warning") for _ in range(4)])
        assert bereiche["dsgvo"]["severity"] == "warning"
        assert bereiche["dsgvo"]["critical_count"] == 0
        assert bereiche["dsgvo"]["issues_count"] == 4

    def test_kritisch_wird_nicht_zur_warnung(self):
        # Der Widerrufs-Befund ist kritisch; die Textsuche stufte ihn auf
        # "warning" herunter und verharmloste ihn gegenueber dem Besucher.
        bereiche, _ = aggregiere([befund(
            "shop", "critical", "Widerrufsbelehrung fehlt (Online-Shop erkannt)",
            "Online-Shop erkannt, aber keine Widerrufsbelehrung gefunden.",
        )])
        assert bereiche["shop"]["severity"] == "critical"


class TestKategorieWirdNichtGeraten:
    def test_matrix_wird_nach_der_eigenen_kategorie_gefragt(self):
        _, rechner = aggregiere([befund("cookie", "warning", "Irgendein Titel",
                                        "Ein Text ganz ohne einschlaegige Stichwoerter.")])
        assert rechner.gefragte_kategorien == ["cookies"]

    def test_saubere_seite_ergibt_keinen_bereich(self):
        bereiche, _ = aggregiere([])
        assert all(b["detected"] is False for b in bereiche.values())
        assert all(b["risk_max"] == 0 for b in bereiche.values())
