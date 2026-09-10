# -*- coding: utf-8 -*-
"""
Der letzte Bildschirm vor dem Kauf muss den Preis nennen, der eingezogen wird.

Gemessen am 10.09.2026: die Tarifkarten der Registrierung zeigten die gueltige
Preisliste (Einzelsaeule 29, Pro 89, Agentur 599, Monitoring 39), die
Zusammenfassung darunter aber die alte (19 / 49 / 299 / 19). Stripe buchte die
neue ab. Wer "Weiter zur Zahlung" drueckte, hatte gerade 49 EUR gelesen und
zahlte 89 EUR — beim Agentur-Tarif 599 statt 299.

Das ist derselbe Fehler wie am 01.09.2026, als der Landing-Knopf "Monitoring
buchen, 19 EUR" bei 76 EUR landete: zwei Preislisten im selben Formular, von
denen eine gepflegt wird.

Die Zusammenfassung holt die Betraege jetzt aus derselben Quelle wie der
Checkout (GET /api/stripe/plans). Dieser Test haelt fest, dass keine zweite
Liste zurueckkehrt — und dass die Tarifkarten zum Backend passen.
"""

import os
import re

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(BACKEND)
REGISTRIERUNG = os.path.join(WURZEL, "dashboard-react", "src", "app", "register", "page.tsx")

frontend_da = pytest.mark.skipif(
    not os.path.exists(REGISTRIERUNG), reason="dashboard-react nicht eingehaengt")


def _backend_preise():
    """Die Preisliste, die /api/stripe/plans ausliefert."""
    quelle = open(os.path.join(BACKEND, "stripe_routes.py"), encoding="utf-8").read()
    abschnitt = quelle[quelle.index('@router.get("/plans")'):]
    abschnitt = abschnitt[:abschnitt.index("\n@")] if "\n@" in abschnitt else abschnitt
    preise = {}
    for treffer in re.finditer(
            r'"id":\s*"(\w+)".*?"price_monthly":\s*(\d+),\s*"price_yearly":\s*(\d+)',
            abschnitt, re.S):
        preise[treffer.group(1)] = (int(treffer.group(2)), int(treffer.group(3)))
    return preise


def test_backend_kennt_die_erwarteten_tarife():
    preise = _backend_preise()
    assert preise.get("pro") == (89, 890), f"Pro-Tarif unerwartet: {preise.get('pro')}"
    assert preise.get("agency") == (599, 5990)
    assert preise.get("monitor") == (39, 390)


@frontend_da
def test_zusammenfassung_holt_die_preise_vom_backend():
    text = open(REGISTRIERUNG, encoding="utf-8").read()
    assert "/api/stripe/plans" in text, (
        "Die Registrierung holt die Preise nicht aus derselben Quelle wie der Checkout")


@frontend_da
@pytest.mark.parametrize("verboten", [
    "monthly: 49", "monthly: 299", "monthly: 19",
    "yearly: 490", "yearly: 2990", "yearly: 190",
])
def test_keine_zweite_preisliste_im_formular(verboten):
    text = open(REGISTRIERUNG, encoding="utf-8").read()
    assert verboten not in text, (
        f"'{verboten}' steht wieder fest im Formular. Preise gehoeren an eine Stelle — "
        "die, aus der auch der Checkout liest.")


@frontend_da
def test_tarifkarten_stimmen_mit_dem_backend_ueberein():
    text = open(REGISTRIERUNG, encoding="utf-8").read()
    preise = _backend_preise()
    karten = dict(re.findall(r"id:\s*'(\w+)',\s*name:\s*'[^']*',\s*price:\s*'([^']*)'", text))
    abweichungen = []
    for kennung, (monat, _jahr) in preise.items():
        if kennung == "free" or kennung not in karten:
            continue
        if str(monat) not in karten[kennung]:
            abweichungen.append(f"{kennung}: Karte sagt '{karten[kennung]}', Backend {monat} EUR")
    assert not abweichungen, "Tarifkarten weichen vom Backend ab:\n  " + "\n  ".join(abweichungen)


@frontend_da
def test_ohne_geladene_preise_steht_keine_zahl_da():
    """Lieber kein Preis als ein falscher."""
    text = open(REGISTRIERUNG, encoding="utf-8").read()
    assert "Preis wird geladen" in text
