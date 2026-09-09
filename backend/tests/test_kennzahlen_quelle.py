# -*- coding: utf-8 -*-
"""Anzahl und Schnitt meinen dieselben Websites, und beide sind aktuell.

Am 09.09.2026 zeigte die Kopfzeile "6 Websites · Ø 33 von 100". Nachgemessen
stimmte keine der drei Zahlen:

* Der Schnitt kam aus `scan_history`, dem Mitschnitt der MANUELLEN Scans. Der
  Monitor schreibt nur nach `score_history` und `tracked_websites`. Fuenf der
  sechs Werte stammten aus Juni bis August, waehrend daneben "letzte Pruefung
  heute" stand. Echt: 58, angezeigt: 32.
* Gemittelt wurde ueber SIEBEN Eintraege, darunter eine Seite, die der Kunde
  entfernt hatte — unter der Ueberschrift "6 Websites".
* Die 33 selbst passte zu gar nichts: die Abfrage war mit 401 gescheitert, und
  die Anzeige fiel stillschweigend auf alte Werte aus dem Browser-Speicher
  zurueck.

Alle drei sind unsichtbar, solange niemand gegen die Datenbank nachrechnet. Es
gibt keine Fehlermeldung, die Zahl steht einfach da. Fuer ein Produkt, dessen
Verkaufsargument "im Browser nachgemessen" ist, ist das der teuerste Fehler.
"""

import os
import re

import pytest

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def quelle(*teile):
    return open(os.path.join(BACKEND, *teile), encoding="utf-8").read()


def metrics_block() -> str:
    s = quelle("dashboard_routes.py")
    start = s.index("async def get_dashboard_metrics")
    return s[start:s.index("@dashboard_router", start + 10)] if "@dashboard_router" in s[start + 10:] else s[start:]


class TestQuelleDerKennzahlen:
    def test_schnitt_kommt_aus_score_history(self):
        """score_history traegt beide Scan-Wege, scan_history nur den manuellen."""
        b = metrics_block()
        assert "JOIN score_history s ON s.website_id = t.id" in b

    def test_nur_verfolgte_websites_zaehlen(self):
        """Ohne den JOIN zog eine entfernte Seite den Schnitt mit herunter."""
        b = metrics_block()
        assert b.count("FROM tracked_websites t") >= 2

    def test_kein_mittel_mehr_ueber_scan_history(self):
        b = metrics_block()
        assert "COALESCE(website_id::text, url)" not in b

    def test_trend_nutzt_dieselbe_quelle(self):
        """Ein Trend zwischen zwei Quellen waere eine Zahl ohne Bedeutung."""
        b = metrics_block()
        alt = b[b.index("old_scans = await conn.fetch"):]
        alt = alt[:alt.index('""", user_id, week_ago)')]
        assert "score_history" in alt

    def test_ungeprueft_geht_nicht_als_null_ein(self):
        b = metrics_block()
        assert "s.overall_score IS NOT NULL" in b

    def test_grundlage_des_schnitts_wird_gemeldet(self):
        b = metrics_block()
        assert "scoredWebsites=scored_websites" in b
        assert "scored_websites = len(latest_scans)" in b


class TestSchema:
    def test_antwort_traegt_die_grundlage(self):
        assert "scoredWebsites" in quelle("schemas", "dashboard.py")


_FRONTEND = os.path.join(BACKEND, "..", "dashboard-react")
ohne_frontend = pytest.mark.skipif(
    not os.path.isdir(_FRONTEND),
    reason="Frontend-Quelltext liegt nicht neben backend/ (z. B. im Container) — laeuft in CI",
)


def fquelle(*teile):
    return open(os.path.join(_FRONTEND, "src", *teile), encoding="utf-8").read()


@ohne_frontend
class TestAnzeige:
    def test_kein_rueckfall_auf_alte_werte(self):
        """`?? metrics.totalScore` machte aus einer gescheiterten Abfrage eine
        Aussage."""
        s = fquelle("components", "dashboard", "Orientierungsband.tsx")
        assert "metrics.totalScore" not in s
        assert "metrics.criticalIssues" not in s
        assert "metrics.websites" not in s

    def test_gescheiterte_abfrage_wird_benannt(self):
        s = fquelle("components", "dashboard", "Orientierungsband.tsx")
        assert "Kennzahlen gerade nicht abrufbar" in s

    def test_luecke_zwischen_anzahl_und_schnitt_wird_sichtbar(self):
        s = fquelle("components", "dashboard", "Orientierungsband.tsx")
        assert "aus ${gemessen} geprüften" in s

    def test_typ_kennt_die_grundlage(self):
        assert "scoredWebsites" in fquelle("hooks", "useMetrics.ts")
