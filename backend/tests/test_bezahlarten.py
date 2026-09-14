# -*- coding: utf-8 -*-
"""Keine fest verdrahtete Liste von Bezahlarten im Checkout.

Am 14.09.2026, unmittelbar nach dem Umschalten auf den Live-Schluessel,
antwortete JEDER Checkout mit 400: `['card', 'sepa_debit']` stand fest im
Code, SEPA-Lastschrift war im Live-Konto aber nicht freigeschaltet. Im
Testmodus ist sie automatisch aktiv, deshalb war der Fehler bis zum ersten
echten Aufruf unsichtbar. Der Kunde haette gelesen: "Der Zahlungsanbieter ist
gerade nicht erreichbar."

Welche Bezahlarten moeglich sind, gehoert ins Stripe-Dashboard, nicht in den
Quelltext: dort ist es eine Einstellung, hier waere es bei jeder Aenderung ein
Deploy, und jede nicht freigeschaltete Art bricht den ganzen Kaufweg.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAUFWEGE = ("stripe_routes.py", "addon_payment_routes.py", "payment_routes.py")


def _quelle(datei):
    pfad = os.path.join(BACKEND, datei)
    if not os.path.exists(pfad):
        return ""
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


def test_keine_feste_liste_von_bezahlarten():
    for datei in KAUFWEGE:
        text = _quelle(datei)
        treffer = [z.strip() for z in text.split("\n")
                   if "payment_method_types" in z and not z.lstrip().startswith("#")]
        assert not treffer, (
            f"{datei} schreibt die Bezahlarten fest: {treffer}. Eine Art, die im "
            f"Stripe-Konto nicht freigeschaltet ist, laesst jeden Checkout mit "
            f"400 scheitern.")


def test_checkout_meldet_den_grund_ins_log():
    """Der Kunde bekommt eine ruhige Meldung, das Log den echten Grund.

    Ohne die Logzeile war am 14.09. nur "Der Zahlungsanbieter ist gerade nicht
    erreichbar" zu sehen, und das sah nach einem Netzproblem bei Stripe aus.
    """
    text = _quelle("stripe_routes.py")
    assert re.search(r"logger\.error\(f?\"Stripe error creating checkout", text), (
        "Der Stripe-Fehler wird nicht mehr geloggt")
