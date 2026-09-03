"""Gesetzlicher Rahmen und realistisches Kostenrisiko sind zwei Zahlen.

Bis zum 03.09.2026 addierte `/api/analyze/preview` die Hoechstwerte aller acht
Kategorien zu EINER Zahl. Die leere Platzhalterseite example.com kam so auf
91.800 EUR. Das entspricht keiner Bussgeldpraxis und macht ausgerechnet einen
Compliance-Anbieter nach Paragraph 5 UWG selbst angreifbar.

Blosses Deckeln haette es nicht geheilt: dann steht auf fast jeder Seite
derselbe Deckelwert. Deshalb werden die beiden Groessen getrennt gefuehrt -
der gesetzliche Rahmen als Tatsache, das Kostenrisiko als Schaetzung.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from risk_calculator import (
    KMU_RISIKO_MAX_EUR,
    TYPISCHE_ABMAHNUNG_MAX_EUR,
    TYPISCHE_ABMAHNUNG_MIN_EUR,
    gesamtrisiko_aus_kategorien,
)


def kategorie(name, min_eur, max_eur, severity='warning', erkannt=True):
    return {
        'id': name,
        'label': name,
        'detected': erkannt,
        'severity': severity,
        'risk_min': min_eur,
        'risk_max': max_eur,
        'issues_count': 1 if erkannt else 0,
    }


# Die echten Werte aus compliance_risk_matrix (market DE, is_active),
# Stand 03.09.2026 - damit der Test den tatsaechlichen Fall abbildet.
MATRIX_DE = [
    kategorie('dsgvo', 2_000, 50_000, 'critical'),
    kategorie('cookies', 1_000, 20_000, 'critical'),
    kategorie('barrierefreiheit', 500, 10_000, 'warning'),
    kategorie('rechtstexte', 500, 5_000, 'critical'),
    kategorie('shop', 500, 3_500, 'warning'),
    kategorie('sicherheit', 500, 2_000, 'warning'),
    kategorie('wettbewerb', 500, 2_000, 'warning'),
    kategorie('preise', 300, 2_000, 'warning'),
]


class TestKeineSummenbildung:
    def test_der_konkrete_fall_example_com(self):
        """Alle acht Bereiche betroffen - vorher 91.800 EUR."""
        ergebnis = gesamtrisiko_aus_kategorien(MATRIX_DE)

        summe_alt = sum(k['risk_max'] for k in MATRIX_DE)
        assert summe_alt > 90_000  # so entstand die alte Zahl
        assert ergebnis['risk_max'] < 15_000
        assert ergebnis['risk_max'] <= KMU_RISIKO_MAX_EUR

    def test_kostenrisiko_bleibt_im_abmahnrahmen(self):
        ergebnis = gesamtrisiko_aus_kategorien(MATRIX_DE)
        assert ergebnis['risk_min'] >= TYPISCHE_ABMAHNUNG_MIN_EUR
        assert ergebnis['risk_max'] <= int(TYPISCHE_ABMAHNUNG_MAX_EUR * 1.6)

    def test_der_deckel_ist_sicherheitsnetz_nicht_die_antwort(self):
        """Im Normalfall darf der Deckel nie greifen - sonst sagt die Zahl nichts."""
        ergebnis = gesamtrisiko_aus_kategorien(MATRIX_DE)
        assert ergebnis['gedeckelt'] is False


class TestRahmenGetrennt:
    def test_gesetzlicher_rahmen_wird_ausgewiesen_und_nicht_gedeckelt(self):
        ergebnis = gesamtrisiko_aus_kategorien(MATRIX_DE)
        assert ergebnis['rahmen_max'] == 50_000  # Art. 83 DSGVO, hoechster Bereich
        assert ergebnis['rahmen_range'] == 'bis 50.000€'

    def test_rahmen_wird_nicht_addiert(self):
        ergebnis = gesamtrisiko_aus_kategorien(MATRIX_DE)
        assert ergebnis['rahmen_max'] < sum(k['risk_max'] for k in MATRIX_DE)

    def test_rahmen_und_kostenrisiko_sind_verschiedene_zahlen(self):
        ergebnis = gesamtrisiko_aus_kategorien(MATRIX_DE)
        assert ergebnis['rahmen_max'] != ergebnis['risk_max']


class TestBreitenzuschlag:
    def test_mehr_kritische_bereiche_erhoehen_das_kostenrisiko(self):
        eins = gesamtrisiko_aus_kategorien([kategorie('a', 1_000, 4_000, 'critical')])
        drei = gesamtrisiko_aus_kategorien([
            kategorie('a', 1_000, 4_000, 'critical'),
            kategorie('b', 1_000, 4_000, 'critical'),
            kategorie('c', 1_000, 4_000, 'critical'),
        ])
        assert drei['risk_max'] > eins['risk_max']

    def test_kritisch_wiegt_schwerer_als_warnung(self):
        krit = gesamtrisiko_aus_kategorien([
            kategorie('a', 1_000, 4_000, 'critical'),
            kategorie('b', 1_000, 4_000, 'critical'),
        ])
        warn = gesamtrisiko_aus_kategorien([
            kategorie('a', 1_000, 4_000, 'warning'),
            kategorie('b', 1_000, 4_000, 'warning'),
        ])
        assert krit['risk_max'] > warn['risk_max']

    def test_zuschlag_ist_unterlinear_und_gedeckelt(self):
        viele = gesamtrisiko_aus_kategorien(
            [kategorie(f'b{i}', 1_000, 4_000, 'critical') for i in range(20)]
        )
        assert viele['risk_max'] <= int(TYPISCHE_ABMAHNUNG_MAX_EUR * 1.6)


class TestGegenprobe:
    """Ein Fix, der den Mangel versteckt, ist kein Fix."""

    def test_keine_befunde_kein_risiko(self):
        ergebnis = gesamtrisiko_aus_kategorien([
            kategorie('dsgvo', 5_000, 20_000, 'critical', erkannt=False),
            kategorie('cookies', 2_000, 8_000, 'critical', erkannt=False),
        ])
        assert ergebnis['risk_max'] == 0
        assert ergebnis['risk_min'] == 0
        assert ergebnis['risk_range'] is None
        assert ergebnis['rahmen_max'] == 0
        assert ergebnis['bereiche_betroffen'] == 0

    def test_leere_liste_faellt_nicht_um(self):
        assert gesamtrisiko_aus_kategorien([])['risk_max'] == 0

    def test_ein_echter_befund_verschwindet_nicht(self):
        ergebnis = gesamtrisiko_aus_kategorien([kategorie('rechtstexte', 800, 2_500)])
        assert ergebnis['risk_max'] >= TYPISCHE_ABMAHNUNG_MIN_EUR
        assert ergebnis['risk_range'] is not None
        assert ergebnis['bereiche_betroffen'] == 1

    def test_nicht_erkannte_kategorien_zaehlen_nicht_zur_breite(self):
        gemischt = gesamtrisiko_aus_kategorien([
            kategorie('a', 1_000, 4_000, 'critical'),
            kategorie('b', 1_000, 9_000, 'critical', erkannt=False),
            kategorie('c', 1_000, 9_000, 'critical', erkannt=False),
        ])
        allein = gesamtrisiko_aus_kategorien([kategorie('a', 1_000, 4_000, 'critical')])
        assert gemischt['risk_max'] == allein['risk_max']
        assert gemischt['rahmen_max'] == 4_000  # nicht 9.000 aus den unerkannten
        assert gemischt['bereiche_betroffen'] == 1


class TestDarstellung:
    def test_spanne_wird_deutsch_formatiert(self):
        ergebnis = gesamtrisiko_aus_kategorien(MATRIX_DE)
        assert '€' in ergebnis['risk_range']
        assert '.' in ergebnis['risk_range']

    def test_min_nie_groesser_als_max(self):
        for faelle in ([kategorie('a', 9_000, 9_000, 'critical')], MATRIX_DE, []):
            ergebnis = gesamtrisiko_aus_kategorien(faelle)
            assert ergebnis['risk_min'] <= ergebnis['risk_max']
