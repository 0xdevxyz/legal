"""Die Musterliste misst Verbreitung, nicht Seitengroesse.

Der Musterextraktor schreibt die Liste, aus der der Wissensspeicher lernt,
welche Befunde bei complyos Kunden wirklich vorkommen. Bis zum 03.09.2026
ordnete er nach der reinen Zahl der Fundstellen. Gemessen an den echten
Scandaten stand damit ganz oben:

    98 Fundstellen | WCAG 1.1.1: SVG ohne <title> oder role="img"

Nachgezaehlt kamen diese 98 aus 4 Scans auf 2 Websites - zwei icon-lastige
Seiten. Die fehlende Werbekennzeichnung traf dagegen 5 verschiedene Websites
und rangierte tiefer. Der Lernkreislauf lernte also, welche einzelne Seite die
meisten Symbole hat, nicht, welches Problem die meisten Kunden haben.

Dazu kam: der Spitzenreiter war zu dem Zeitpunkt 30 Tage nicht mehr
aufgetreten. Nicht, weil Kundenseiten repariert wurden, sondern weil die
erzeugende Pruefung entfernt worden war. Ein Phantom fuehrte die Rangliste an.
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def _extractor(tmp_path, monkeypatch):
    import knowledge.pattern_extractor as pe

    monkeypatch.setattr(pe, "PATTERNS_DIR", tmp_path)
    return pe


def _zeile(titel, websites, fundstellen, scans, tage_her=0, kategorie="barrierefreiheit"):
    return {
        "titel": titel,
        "kategorie": kategorie,
        "websites": websites,
        "haeufigkeit": fundstellen,
        "scans": scans,
        "zuletzt": datetime.now() - timedelta(days=tage_her),
    }


class TestRangfolge:
    def test_abfrage_ordnet_nach_websites(self):
        """Die Reihenfolge entsteht in SQL - hier festgenagelt."""
        import knowledge.pattern_extractor as pe

        quelle = open(pe.__file__, encoding="utf-8").read()
        assert "ORDER BY websites DESC, haeufigkeit DESC" in quelle, (
            "Die Musterliste ordnet wieder nach Fundstellen - eine einzelne "
            "icon-lastige Seite uebernimmt damit den Spitzenplatz"
        )
        assert "COUNT(DISTINCT sh.url)" in quelle

    def test_tabelle_weist_websites_und_fundstellen_getrennt_aus(self, tmp_path, monkeypatch):
        pe = _extractor(tmp_path, monkeypatch)
        ex = pe.PatternExtractor()
        ex._schreibe_haeufigkeitsmuster([
            _zeile("Viele Symbole auf einer Seite", websites=2, fundstellen=98, scans=4),
        ])
        text = (tmp_path / "haeufigste-befunde-patterns.md").read_text(encoding="utf-8")

        assert "| Websites | Fundstellen | Scans |" in text
        assert "| 2 | 98 | 4 |" in text, (
            "Websites und Fundstellen muessen als getrennte Zahlen lesbar sein - "
            "sonst liest man 98 als 98 betroffene Kunden"
        )


class TestVeralteteBefunde:
    def test_alter_befund_wird_als_veraltet_markiert(self, tmp_path, monkeypatch):
        pe = _extractor(tmp_path, monkeypatch)
        ex = pe.PatternExtractor()
        ex._schreibe_haeufigkeitsmuster([
            _zeile("Aus einer entfernten Pruefung", 2, 98, 4, tage_her=30),
        ])
        text = (tmp_path / "haeufigste-befunde-patterns.md").read_text(encoding="utf-8")
        assert "veraltet" in text
        assert "30 Tage" in text

    def test_frischer_befund_wird_nicht_markiert(self, tmp_path, monkeypatch):
        """Gegenprobe: die Markierung darf nicht ueberall stehen."""
        pe = _extractor(tmp_path, monkeypatch)
        ex = pe.PatternExtractor()
        ex._schreibe_haeufigkeitsmuster([
            _zeile("Taeglich gesehen", 5, 22, 22, tage_her=1),
        ])
        text = (tmp_path / "haeufigste-befunde-patterns.md").read_text(encoding="utf-8")
        zeilen = [z for z in text.splitlines() if "Taeglich gesehen" in z]
        assert len(zeilen) == 1
        assert "veraltet" not in zeilen[0]

    def test_grenze_liegt_bei_dreissig_tagen(self, tmp_path, monkeypatch):
        pe = _extractor(tmp_path, monkeypatch)
        assert pe.VERALTET_AB_TAGEN == 30
        ex = pe.PatternExtractor()
        ex._schreibe_haeufigkeitsmuster([
            _zeile("Knapp darunter", 3, 10, 10, tage_her=29),
            _zeile("Knapp darueber", 3, 10, 10, tage_her=31),
        ])
        text = (tmp_path / "haeufigste-befunde-patterns.md").read_text(encoding="utf-8")
        darunter = next(z for z in text.splitlines() if "Knapp darunter" in z)
        darueber = next(z for z in text.splitlines() if "Knapp darueber" in z)
        assert "veraltet" not in darunter
        assert "veraltet" in darueber


class TestGegenprobe:
    def test_ohne_zeitstempel_keine_falsche_markierung(self, tmp_path, monkeypatch):
        pe = _extractor(tmp_path, monkeypatch)
        ex = pe.PatternExtractor()
        zeile = _zeile("Ohne Datum", 3, 10, 10)
        zeile["zuletzt"] = None
        ex._schreibe_haeufigkeitsmuster([zeile])
        text = (tmp_path / "haeufigste-befunde-patterns.md").read_text(encoding="utf-8")
        assert "veraltet" not in next(z for z in text.splitlines() if "Ohne Datum" in z)

    def test_leere_liste_erzeugt_keine_datei_mit_falschem_inhalt(self, tmp_path, monkeypatch):
        pe = _extractor(tmp_path, monkeypatch)
        ex = pe.PatternExtractor()
        ex._schreibe_haeufigkeitsmuster([])
        text = (tmp_path / "haeufigste-befunde-patterns.md").read_text(encoding="utf-8")
        # Kopf und Tabellenkopf ja, aber keine erfundenen Zeilen
        assert "| Websites | Fundstellen | Scans |" in text
        datenzeilen = [
            z for z in text.splitlines()
            if z.startswith("| ") and not z.startswith("| ---") and "Websites" not in z
        ]
        assert datenzeilen == []
