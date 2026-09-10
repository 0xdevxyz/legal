# -*- coding: utf-8 -*-
"""
jsonb kommt als Zeichenkette zurück, nicht als Liste.

Der Verbindungspool setzt keinen jsonb-Codec (`set_type_codec`). asyncpg
liefert solche Spalten deshalb als Text. Die meisten Leser wissen das und
parsen; `get_blocking_config` tat es nicht:

    selected_services = config['services'] if config['services'] else []

Bei einer leeren Liste steht in der Spalte der Text "[]". Der ist wahr,
`len("[]")` ist 2, und der Aufruf ging mit einer Zeichenkette in
`ANY($1::text[])`. Ergebnis: der Endpunkt antwortete fuer JEDE Site mit 500 —
gemessen am 10.09.2026 als einziger verbliebener 500er im Durchlauf ueber
105 Endpunkte.

Der Endpunkt liefert die Sperrliste fuer Drittanbieter-Skripte. Das Widget
holt sie derzeit ueber einen anderen Weg, die Sperre wirkte also; ein
Endpunkt, der nie antworten kann, gehoert trotzdem repariert.
"""

import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLE = os.path.join(BACKEND, "cookie_compliance_routes.py")


def _abschnitt(name: str) -> str:
    quelle = open(QUELLE, encoding="utf-8").read()
    start = quelle.index(f"async def {name}(")
    ende = quelle.find("\nasync def ", start + 10)
    return quelle[start:ende if ende > 0 else len(quelle)]


def test_sperrliste_parst_die_jsonb_spalte():
    text = _abschnitt("get_blocking_config")
    assert "isinstance(roh, str)" in text, (
        "Die Spalte `services` wird wieder ungeparst benutzt — sie kommt als "
        "Zeichenkette, und `len('[]')` ist 2.")
    assert "json.loads" in text


def test_sperrliste_uebergibt_eine_liste_von_zeichenketten():
    text = _abschnitt("get_blocking_config")
    assert "[str(x) for x in roh]" in text, (
        "Was in ANY($1::text[]) geht, muss eine Liste von Zeichenketten sein")


def test_kaputte_daten_brechen_den_endpunkt_nicht():
    """Ein unlesbarer Wert darf zu einer leeren Liste fuehren, nicht zu 500."""
    text = _abschnitt("get_blocking_config")
    assert "except (ValueError, TypeError)" in text
