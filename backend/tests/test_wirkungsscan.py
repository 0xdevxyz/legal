"""
Der Wirkungsscan — misst, was der Besucher wirklich vorfindet.

Der normale Scan blockiert complyos eigenes Widget, sonst misst er die von
complyo bereits reparierte Seite und ueberschreibt den Messwert mit einer
Null. Der Preis: niemand hat je den AUSGELIEFERTEN Zustand gemessen. Der
Wirkungsscan misst dieselbe Seite zweimal — ohne und mit Widget — und die
Differenz ist gemessen statt behauptet.

Beim ersten Lauf an echten Kundenseiten hat er sofort geliefert:
complyos EIGENER Cookie-Banner-Knopf trug weisse Schrift auf der
Markenfarbe #1597a3 — 3,5:1 statt 4,5:1. Auf zua-zwickau.de war MIT complyo
ein Kontrastbefund MEHR da als ohne. Genau das, was complyo den
Overlay-Anbietern vorwirft.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.wirkungsscan import _urteil, vergleiche  # noqa: E402


class TestVergleich:
    def test_zaehlt_behobene_regeln(self):
        v = vergleiche({"color-contrast": 19, "link-name": 3},
                       {"color-contrast": 19})
        assert v["summe"] == {"ohne_widget": 22, "mit_widget": 19,
                              "behoben": 3, "quote": 14}
        assert [z["regel"] for z in v["behoben"]] == ["link-name"]

    def test_erkennt_neue_befunde(self):
        v = vergleiche({"color-contrast": 19}, {"color-contrast": 20})
        assert [z["regel"] for z in v["neu"]] == ["color-contrast"]

    def test_leere_messung_teilt_nicht_durch_null(self):
        assert vergleiche({}, {})["summe"]["quote"] == 0


class TestZuschreibung:
    """
    Die wichtigste Regel des Modus: eine Verschlechterung darf nur behauptet
    werden, wenn das Widget nachweislich lief.

    Der erste Anlauf drehte "kein Widget" in "Widget lief" um, sobald sich die
    beiden Messungen unterschieden — und meldete prompt panoart360.de als
    "Verschlechterung durch complyo". Dort ist complyo gar nicht eingebaut;
    der Unterschied war Messrauschen (Lazy Loading, Schieberegler).
    """

    def test_ohne_widget_keine_verschlechterung(self):
        v = vergleiche({"region": 50}, {"region": 49, "landmark-one-main": 1})
        u = _urteil(v, widget_lief=False)
        assert u["lage"] == "kein_widget"
        assert "nicht complyo zuzuschreiben" in u["satz"]

    def test_mit_widget_wird_die_verschlechterung_benannt(self):
        v = vergleiche({"color-contrast": 19}, {"color-contrast": 20})
        u = _urteil(v, widget_lief=True)
        assert u["lage"] == "verschlechterung"
        assert "color-contrast" in u["satz"]

    def test_widget_ohne_wirkung_ist_ein_eigener_zustand(self):
        u = _urteil(vergleiche({"region": 5}, {"region": 5}), widget_lief=True)
        assert u["lage"] == "wirkungslos"

    def test_wirksam_nennt_beide_zahlen(self):
        u = _urteil(vergleiche({"a": 10}, {"a": 4}), widget_lief=True)
        assert u["lage"] == "wirksam"
        assert "10" in u["satz"] and "6" in u["satz"]

    def test_vollstaendig_nur_wenn_nichts_bleibt(self):
        assert _urteil(vergleiche({"a": 7}, {}), widget_lief=True)["lage"] == "vollstaendig"


class TestUrteilIstLesbar:
    def test_jeder_zustand_hat_einen_ganzen_satz(self):
        faelle = [
            (vergleiche({"a": 5}, {"a": 5}), False),
            (vergleiche({"a": 5}, {"a": 6}), True),
            (vergleiche({"a": 5}, {"a": 5}), True),
            (vergleiche({"a": 5}, {"a": 1}), True),
            (vergleiche({"a": 5}, {}), True),
        ]
        for v, lief in faelle:
            u = _urteil(v, lief)
            assert u["satz"].endswith((".", "!")) and len(u["satz"]) > 40
            assert "score" not in u["satz"].lower(), \
                "Eine nackte Zahl ist der Grund, warum niemand Scannern glaubt"


class TestWidgetBeobachtungIstVerdrahtet:
    def test_scanner_kennt_den_schalter(self):
        from compliance_engine.axe_scanner import AxeScanner
        import inspect
        assert "widget_blockieren" in inspect.signature(AxeScanner.scan_page).parameters

    def test_ergebnis_traegt_die_beobachtung(self):
        from compliance_engine.axe_scanner import AxeScanResult
        assert "widget_geladen" in AxeScanResult.__dataclass_fields__


class TestBannerSchriftfarbe:
    """
    complyos eigener Cookie-Banner waehlt die Schriftfarbe jetzt nach Kontrast
    statt immer weiss. Die Markenfarbe des Kunden bleibt unangetastet.
    """

    def test_der_helfer_steht_im_widget(self):
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "widgets", "cookie_banner_v2.js")
        with open(pfad, encoding="utf-8") as fh:
            quelle = fh.read()
        assert "lesbareSchrift" in quelle
        assert "color: ${primaryTextColor}" in quelle
        assert "color: white;\n                    box-shadow" not in quelle, \
            "Der Knopf traegt wieder fest weisse Schrift"
