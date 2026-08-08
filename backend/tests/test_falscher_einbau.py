"""
Das Widget muss merken, wenn es falsch eingebaut ist.

Gefunden im Browser auf einer echten Seite: loqal.io laedt das Cookie-Widget
mit `data-site-id="loqal-io"` und das Barrierefreiheits-Widget direkt daneben
mit `data-site-id="scan_5_1783852724"` — einer Scan-Kennung. Das Manifest
antwortete darauf mit HTTP 200 und einem leeren Koerper, das Widget wendete
brav nichts an, und niemand konnte es bemerken. Die Seite haette auch nach
jeder Freigabe nie eine Reparatur bekommen.

Die Ursache ist die doppeldeutige Antwort: ein leeres Manifest heisst
entweder "hier gibt es nichts zu tun" oder "du fragst unter der falschen
Kennung". Beides gleich zu beantworten war der Fehler.

Zweiter Fund am selben Ort: Skip-Link und landmark-main liefen ganz ausserhalb
der Wirkungsbilanz. Blieb der Skip-Link mangels aufloesbarem Ziel aus, meldete
das niemand — ausgerechnet der Fall, fuer den die Ueberwachung da ist.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import wirkung_routes  # noqa: E402

WIDGET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "widgets", "a11y_remediation.js")


def _widget() -> str:
    with open(WIDGET, encoding="utf-8") as fh:
        return fh.read()


def _widget_ohne_kommentare() -> str:
    """
    Der Code ohne Kommentare — die Begruendungen nennen die Fundstellen
    woertlich und wuerden jeden Waechter hier gruen faerben.
    """
    q = re.sub(r"/\*.*?\*/", "", _widget(), flags=re.S)
    return re.sub(r"^\s*//.*$", "", q, flags=re.M)


class TestManifestSagtObDieKennungBekanntIst:
    def test_route_liefert_das_feld(self):
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "widget_routes.py")
        with open(pfad, encoding="utf-8") as fh:
            quelle = fh.read()
        assert '"bekannt": bekannt' in quelle
        assert "tracked_websites" in quelle, \
            "Ohne Abgleich mit den gefuehrten Websites ist jede leere Site unbekannt"

    def test_widget_wertet_es_aus(self):
        q = _widget_ohne_kommentare()
        assert "d.bekannt === false" in q
        assert "unbekannteKennung = true" in q

    def test_widget_meldet_es_weiter(self):
        assert "unbekannte_kennung: unbekannteKennung" in _widget_ohne_kommentare()

    def test_endpunkt_nimmt_es_entgegen(self):
        m = wirkung_routes.WirkungsMeldung(pfad="/", unbekannte_kennung=True)
        assert m.unbekannte_kennung is True

    def test_standard_ist_falsch(self):
        assert wirkung_routes.WirkungsMeldung(pfad="/").unbekannte_kennung is False


class TestDokumentFixesStehenInDerBilanz:
    def test_bilanz_kennt_die_art(self):
        assert "dokument_fixes: { angewendet: 0, verfehlt: 0, unnoetig: 0 }" \
            in _widget_ohne_kommentare()

    def test_skiplink_ohne_ziel_gilt_als_verfehlt(self):
        q = _widget_ohne_kommentare()
        # Im Zweig ohne aufloesbares Ziel muss gezaehlt werden.
        block = q.split("function applySkipLink")[1].split("function ")[0]
        assert "bilanz.dokument_fixes.verfehlt++" in block

    def test_vorhandenes_main_ist_unnoetig_und_kein_fehlschlag(self):
        q = _widget_ohne_kommentare()
        block = q.split("function applyLandmarkMain")[1].split("function ")[0]
        assert "bilanz.dokument_fixes.unnoetig++" in block, \
            "Eine Seite mit eigenem <main> darf keinen Regressionsalarm ausloesen"

    def test_meldung_traegt_die_art(self):
        assert "dokument_fixes: bilanz.dokument_fixes" in _widget_ohne_kommentare()


class TestUnnoetigVerfaelschtKeineSumme:
    def test_zaehler_kennt_unnoetig(self):
        z = wirkung_routes.Zaehler(angewendet=1, verfehlt=0, unnoetig=7)
        assert z.unnoetig == 7

    def test_unnoetig_zaehlt_weder_als_arbeit_noch_als_fehlschlag(self):
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "wirkung_routes.py")
        with open(pfad, encoding="utf-8") as fh:
            quelle = fh.read()
        assert "angewendet = sum(z.angewendet for z in arten.values())" in quelle
        assert "verfehlt = sum(z.verfehlt for z in arten.values())" in quelle
        assert "sum(z.unnoetig" not in quelle


class TestBetriebsblick:
    def test_warnliste_existiert(self):
        assert callable(wirkung_routes.falsch_eingebaute_kennungen)
