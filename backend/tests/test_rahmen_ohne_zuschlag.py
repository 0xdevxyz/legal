"""Der gesetzliche Rahmen wird zitiert, nicht gerechnet.

Beim ersten Live-Scan nach der Trennung von Rahmen und Kostenrisiko stand
"Gesetzlicher Bussgeldrahmen daneben: bis 75.000 EUR" auf der Landing. In der
Matrix steht 50.000 EUR. Die 75.000 waren 50.000 mal dem Fundstellen-Zuschlag
der Kategorie: gelesen wurde 'risk_max', und das traegt den Zuschlag bereits.

Damit wurde eine geschaetzte Zahl als Gesetzesangabe ausgewiesen - genau der
Fehler, den die Trennung beseitigen sollte, nur eine Zeile tiefer.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from risk_calculator import gesamtrisiko_aus_kategorien


def kategorie(name, risk_min, risk_max, rahmen_max, severity='critical'):
    """Wie _aggregate_risk_categories sie baut: risk_max MIT Zuschlag,
    rahmen_max ohne."""
    return {
        'id': name,
        'label': name,
        'detected': True,
        'severity': severity,
        'risk_min': risk_min,
        'risk_max': risk_max,
        'rahmen_max': rahmen_max,
        'issues_count': 1,
    }


class TestRahmenOhneZuschlag:
    def test_der_konkrete_fall_vom_live_scan(self):
        """Matrix sagt 50.000, Kategorie meldet 75.000 nach Zuschlag."""
        ergebnis = gesamtrisiko_aus_kategorien([
            kategorie('dsgvo', 3_000, 75_000, 50_000),
        ])
        assert ergebnis['rahmen_max'] == 50_000, "Rahmen darf den Zuschlag nicht tragen"
        assert ergebnis['rahmen_range'] == 'bis 50.000€'

    def test_rahmen_ist_nie_der_gerechnete_hoechstwert(self):
        kategorien = [
            kategorie('dsgvo', 3_000, 75_000, 50_000),
            kategorie('cookies', 1_500, 30_000, 20_000),
        ]
        ergebnis = gesamtrisiko_aus_kategorien(kategorien)
        assert ergebnis['rahmen_max'] == 50_000
        assert ergebnis['rahmen_max'] < max(k['risk_max'] for k in kategorien)

    def test_hoechster_rahmen_gewinnt_nicht_hoechstes_risk_max(self):
        """Gegenprobe: die Kategorie mit dem groessten Zuschlag ist nicht
        automatisch die mit dem groessten Gesetzesrahmen."""
        ergebnis = gesamtrisiko_aus_kategorien([
            # viele Fundstellen, kleiner Rahmen -> hoher Zuschlag
            kategorie('barrierefreiheit', 750, 15_000, 10_000),
            # eine Fundstelle, grosser Rahmen -> kein Zuschlag
            kategorie('dsgvo', 2_000, 50_000, 50_000),
        ])
        assert ergebnis['rahmen_max'] == 50_000


class TestRueckfall:
    def test_ohne_rahmen_max_faellt_es_auf_risk_max_zurueck(self):
        """Aeltere Aufrufer, die das Feld nicht setzen, duerfen nicht umfallen."""
        ergebnis = gesamtrisiko_aus_kategorien([
            {
                'id': 'alt',
                'detected': True,
                'severity': 'critical',
                'risk_min': 1_000,
                'risk_max': 9_000,
            },
        ])
        assert ergebnis['rahmen_max'] == 9_000

    def test_rahmen_max_null_wird_nicht_als_fehlend_gelesen(self):
        """0 ist ein gueltiger Wert und darf nicht auf risk_max zurueckfallen -
        sonst zeigt eine Kategorie ohne Gesetzesrahmen den Schaetzwert an."""
        ergebnis = gesamtrisiko_aus_kategorien([
            kategorie('ohne_rahmen', 500, 4_000, 0),
        ])
        assert ergebnis['rahmen_max'] == 0
        assert ergebnis['rahmen_range'] is None
