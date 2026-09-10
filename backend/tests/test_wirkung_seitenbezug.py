# -*- coding: utf-8 -*-
"""
"Ziel nicht gefunden" muss heissen: nicht gefunden, wo es sein sollte.

Eine Kontrastregel wird auf einer bestimmten Seite gemessen. Auf allen anderen
Seiten der Website findet ihr Selektor nichts — voellig richtig, dort gibt es
das Element ja nicht. Das Widget zaehlte das trotzdem als `verfehlt`.

Gemessen am 10.09.2026 in `accessibility_wirkung`:
    complyo.de   24 angewendet, 118 verfehlt
    loqal.io     33 angewendet, 797 verfehlt
    spedition-mahn.de  37 angewendet, 181 verfehlt

Und der Pruefnachweis — das Dokument, das ein Kunde einer Pruefstelle vorlegt —
schrieb dazu: "Bei einigen Reparaturen wurde das Ziel nicht mehr gefunden. Das
deutet auf eine Aenderung an der Website hin." Ein Fehlalarm in genau dem
Papier, das Vertrauen herstellen soll.

Seit dem Manifest die Herkunftsseite je Regel mitliefert, lassen sich die
Faelle trennen: kein Ziel auf DER gemessenen Seite ist ein Fehlschlag, kein
Ziel auf einer anderen ist schlicht nichts zu tun.
"""

import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDGET = os.path.join(BACKEND, "widgets", "a11y_remediation.js")


def _js():
    return open(WIDGET, encoding="utf-8").read()


def test_manifest_liefert_die_herkunftsseite_je_regel():
    quelle = open(os.path.join(BACKEND, "widget_routes.py"), encoding="utf-8").read()
    assert "_mit_seite" in quelle, "Die Regeln tragen ihre Herkunftsseite nicht"
    assert 'setdefault("seite"' in quelle


def test_widget_kennt_die_dritte_kategorie_fuer_css_regeln():
    js = _js()
    treffer = re.search(r"css_regeln:\s*\{([^}]*)\}", js)
    assert treffer, "Bilanz fuer css_regeln nicht gefunden"
    assert "unnoetig" in treffer.group(1), (
        "css_regeln kennt nur angewendet/verfehlt — dann landet jede Regel "
        "einer anderen Seite wieder im Fehlalarm")


def test_regel_einer_anderen_seite_zaehlt_nicht_als_fehlschlag():
    js = _js()
    stelle = js[js.index("var trifft = 0;"):][:1500]
    assert "vonDieserSeite" in stelle, (
        "Die Zaehlung unterscheidet nicht, auf welcher Seite die Regel gemessen wurde")
    assert "zaehltUnnoetig('css_regeln'" in stelle, (
        "Regeln fremder Seiten werden nicht als 'nichts zu tun' gezaehlt")


def test_ohne_angabe_bleibt_es_bei_der_vorsichtigen_zaehlung():
    """Aeltere Manifeste tragen keine Seite — dann lieber Fehlschlag als Schoenrechnen."""
    js = _js()
    stelle = js[js.index("function vonDieserSeite"):][:400]
    assert "return true" in stelle, (
        "Ohne Herkunftsangabe muss die Regel als zur Seite gehoerig gelten")


def test_empfangsseite_nimmt_unnoetig_entgegen():
    quelle = open(os.path.join(BACKEND, "wirkung_routes.py"), encoding="utf-8").read()
    assert "unnoetig: int" in quelle
    # `unnoetig` darf in keine der beiden Summen einfliessen.
    assert "verfehlt = sum(z.verfehlt for z in arten.values())" in quelle
