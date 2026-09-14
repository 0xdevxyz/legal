# -*- coding: utf-8 -*-
"""Eine gescheiterte Freischaltung darf nicht als erledigt gelten.

Stripe wiederholt ein Ereignis nur, wenn der Endpunkt einen Fehler meldet.
`handle_checkout_completed` fing jede Ausnahme ab und lief still weiter; der
Webhook antwortete mit 200, Stripe hakte das Ereignis ab. Ein Kunde haette
bezahlt und nichts bekommen, und der einzige Hinweis waere eine Logzeile
gewesen.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _block(funktion):
    with open(os.path.join(BACKEND, "stripe_routes.py"), encoding="utf-8") as fh:
        text = fh.read()
    i = text.index(f"async def {funktion}")
    m = re.search(r"\nasync def ", text[i + 10:])
    return text[i:i + 10 + m.start()] if m else text[i:]


def test_gescheiterte_freischaltung_wird_gemeldet():
    block = _block("handle_checkout_completed")
    fehlerzweig = block[block.index("except Exception"):]
    assert re.search(r"\n\s+raise\b", fehlerzweig), (
        "Die Ausnahme wird geschluckt: der Webhook meldet 200, Stripe "
        "wiederholt nie, und die Zahlung schaltet nichts frei.")


def test_webhook_gibt_fehler_nach_aussen_weiter():
    block = _block("stripe_webhook")
    assert "status_code=500" in block, (
        "Der Webhook meldet Stripe keinen Fehler; ohne 500 gibt es keine "
        "Wiederholung.")
