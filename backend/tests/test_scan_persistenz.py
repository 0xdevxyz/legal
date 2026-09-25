"""Ein gespeicherter Scan traegt seine Saeulenwerte und seinen Rechtsraum.

Anlass (25.09.2026), gemessen auf der Produktionsdatenbank:

    zeilen | mit_overall | mit_compliance | mit_a11y | mit_legal | mit_cookie
    -------+-------------+----------------+----------+-----------+-----------
        51 |           0 |             51 |        0 |         0 |          0

Fuenf Spalten, seit dem Anfang vorhanden, in jeder Zeile leer. Gelesen wurden
sie die ganze Zeit von `_latest_scan_pillars` im Pflichten-Report, der daraus
den Ist-Zustand der Website an die passenden Pflichten haengen soll. Der Leser
prueft auf None und laesst die Angabe dann sauber weg. Deshalb hat nie etwas
gebrannt: die Funktion ist nicht gescheitert, sie hat nur nie etwas geliefert.

Das ist die Fehlerart, gegen die eine Rueckgabe nichts beweist. Nur das
Nachzaehlen in der Zieltabelle zeigt sie.

Drei INSERTs schreiben in scan_history, jeder mit eigener Spaltenliste. Der
Waechter unten liest sie alle und zwingt jede neue dazu, die Werte
mitzunehmen. Er zaehlt zuerst, was er ueberhaupt gefunden hat: ein gruener
Test, der keine Datei liest, prueft nichts.
"""
import os
import re

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from scan_persistenz import (  # noqa: E402
    SAEULE_ZU_SPALTE,
    SPALTEN_REIHENFOLGE,
    werte_fuer_insert,
)

# Dateien, die in scan_history schreiben. Der Waechter faellt, wenn eine von
# ihnen verschwindet: dann hat sich der Schreibweg geaendert und die Liste
# gehoert nachgezogen.
SCHREIBER = ["public_routes.py", "main_production.py"]


def _quelle(name):
    pfad = os.path.join(_BACKEND, name)
    if not os.path.exists(pfad):
        pytest.skip(f"{name} nicht eingehaengt")
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


def test_jedes_insert_in_scan_history_nennt_saeulen_und_rechtsraum():
    gefunden = 0
    luecken = []
    for name in SCHREIBER:
        quelle = _quelle(name)
        for treffer in re.finditer(
            r"INSERT INTO scan_history\s*\((.*?)\)\s*VALUES", quelle, re.S
        ):
            gefunden += 1
            spalten = {s.strip() for s in treffer.group(1).split(",")}
            fehlt = [s for s in SPALTEN_REIHENFOLGE if s not in spalten]
            if fehlt:
                zeile = quelle[: treffer.start()].count("\n") + 1
                luecken.append(f"{name}:{zeile} ohne {fehlt}")

    assert gefunden >= 3, (
        f"Nur {gefunden} INSERT(s) in scan_history gefunden, erwartet mindestens "
        "3. Entweder hat sich der Schreibweg geaendert, oder dieser Waechter "
        "liest die falschen Dateien und prueft damit nichts."
    )
    assert not luecken, (
        "Diese INSERTs speichern einen Punktestand ohne seine Saeulenwerte oder "
        "ohne seinen Rechtsraum: " + "; ".join(luecken)
    )


def test_saeulennamen_decken_sich_mit_dem_bewertungsmodell():
    """Die Zuordnung darf keine Saeule uebersehen.

    Kommt eine fuenfte Saeule hinzu, faellt dieser Test, und nicht erst ein
    Kunde, dem sie im Report fehlt.
    """
    from compliance_engine.score_calculator import ScoreCalculator

    saeulen = set(ScoreCalculator.PILLAR_IDS)
    assert set(SAEULE_ZU_SPALTE) == saeulen, (
        "SAEULE_ZU_SPALTE und ScoreCalculator.PILLAR_IDS gehen auseinander: "
        f"nur im Modell {sorted(saeulen - set(SAEULE_ZU_SPALTE))}, "
        f"nur in der Zuordnung {sorted(set(SAEULE_ZU_SPALTE) - saeulen)}"
    )


def test_report_liest_den_rechtsraum_mit():
    quelle = _quelle("pflichten_report_routes.py")
    i = quelle.index("FROM scan_history")
    select = quelle[max(0, i - 400):i]
    assert "jurisdiction" in select, (
        "Der Pflichten-Report holt den Punktestand ohne seinen Rechtsraum. "
        "Dann steht im Report eine Zahl, deren Bezugsrahmen niemand mehr kennt."
    )


class TestWerteFuerInsert:
    def _ergebnis(self, **zusatz):
        basis = {
            "compliance_score": 62,
            "jurisdiction": "de",
            "pillar_scores": [
                {"pillar": "accessibility", "score": 50, "status": "partial"},
                {"pillar": "gdpr", "score": 100, "status": "compliant"},
                {"pillar": "legal", "score": 100, "status": "compliant"},
                {"pillar": "cookies", "score": 100, "status": "compliant"},
            ],
        }
        basis.update(zusatz)
        return basis

    def test_reihenfolge_entspricht_der_spaltenliste(self):
        werte = werte_fuer_insert(self._ergebnis())
        assert len(werte) == len(SPALTEN_REIHENFOLGE)
        benannt = dict(zip(SPALTEN_REIHENFOLGE, werte))
        assert benannt == {
            "overall_score": 62.0,
            "accessibility_score": 50.0,
            "privacy_score": 100.0,
            "legal_score": 100.0,
            "cookie_score": 100.0,
            "jurisdiction": "de",
        }

    def test_ungemessene_saeule_bleibt_leer_und_wird_nicht_null(self):
        """"Nicht gemessen" und "null Punkte" sind zwei Aussagen.

        Die zweite waere eine Behauptung ueber die Website des Kunden, und der
        Report wuerde sie anzeigen.
        """
        ergebnis = self._ergebnis(pillar_scores=[
            {"pillar": "accessibility", "score": 50},
            {"pillar": "gdpr", "score": None, "status": "unverified"},
        ])
        benannt = dict(zip(SPALTEN_REIHENFOLGE, werte_fuer_insert(ergebnis)))
        assert benannt["accessibility_score"] == 50.0
        assert benannt["privacy_score"] is None

    def test_selbst_gerechneter_gesamtwert_schlaegt_den_des_scanners(self):
        """public_routes zeigt dem Kunden seinen eigenen Mittelwert.

        Wenn die beiden auseinandergehen, muss das Gespeicherte das sein, was
        der Kunde gesehen hat. Sonst widerspricht der Verlauf der Anzeige.
        """
        benannt = dict(zip(
            SPALTEN_REIHENFOLGE,
            werte_fuer_insert(self._ergebnis(), overall=87),
        ))
        assert benannt["overall_score"] == 87.0

    def test_fehlender_rechtsraum_wird_nicht_zu_de_erfunden(self):
        ergebnis = self._ergebnis()
        del ergebnis["jurisdiction"]
        benannt = dict(zip(SPALTEN_REIHENFOLGE, werte_fuer_insert(ergebnis)))
        assert benannt["jurisdiction"] is None, (
            "Ein fehlender Rechtsraum muss NULL bleiben. Eine Vorbelegung auf "
            "'de' wuerde eine Herkunft behaupten, die niemand gemessen hat."
        )

    def test_unbrauchbare_werte_werfen_nicht(self):
        """Die Persistenz darf am Ergebnis nicht scheitern.

        Ein Scan, der fertig gerechnet ist, soll nicht daran verloren gehen,
        dass eine Saeule Unsinn enthaelt.
        """
        ergebnis = self._ergebnis(
            compliance_score="viel",
            pillar_scores=[
                {"pillar": "accessibility", "score": "gut"},
                "kein Dict",
                {"pillar": "unbekannt", "score": 10},
            ],
        )
        benannt = dict(zip(SPALTEN_REIHENFOLGE, werte_fuer_insert(ergebnis)))
        assert benannt["overall_score"] is None
        assert benannt["accessibility_score"] is None

    def test_leeres_ergebnis_liefert_lauter_none(self):
        werte = werte_fuer_insert({})
        assert set(werte) == {None}
