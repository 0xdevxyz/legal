# -*- coding: utf-8 -*-
"""
Ein Wert in der .env, den docker compose nicht durchreicht, wirkt nicht.

Der Fall, an dem es aufgefallen ist: `STRIPE_PRICE_PRO_EARLY_MONTHLY`. Der
49-Euro-Preis war in Stripe angelegt (geprueft: 49,00 EUR, monatlich, aktiv)
und in der .env eingetragen — stand aber nicht in der `environment`-Liste des
backend-Dienstes. Damit erreichte er den Container nie, und
`pro_early_monthly` fiel auf den regulaeren Pro-Preis zurueck. Die Startseite
versprach den ersten 100 Konten 49 Euro, gebucht worden waeren 89.

Drei Ebenen muessen zusammenpassen, und geprueft wurde bisher keine:
Stripe -> .env -> compose -> Code. Dieser Test prueft die mittlere Fuge.
"""

import os
import re

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(BACKEND)
COMPOSE = os.path.join(WURZEL, "docker-compose.yml")

# Namen, die der Code liest, ohne dass sie durchgereicht werden muessen.
NICHT_NOETIG = {
    # Alter Name, nur noch als Rueckfall im Code (gesetzt ist STRIPE_SECRET_KEY).
    "STRIPE_API_KEY",
    # Zweitname desselben Preises; die andere Schreibweise wird durchgereicht.
    "STRIPE_PRICE_AGENCY_EXTRA_SITE",
    # Optionale Zweitstaffel, in keiner Umgebung gesetzt.
    "STRIPE_PRICE_AGENCY2_MONTHLY",
    "STRIPE_PRICE_AGENCY2_YEARLY",
    "STRIPE_PRICE_AGENCY",
    "STRIPE_PRICE_UPDATE",
    "STRIPE_PRICES",
    "STRIPE_FILE",
}


def _gelesene_namen():
    gelesen = set()
    for wurzel, ordner, dateien in os.walk(BACKEND):
        if any(t in wurzel.split(os.sep) for t in
               ("_archive_pre_baseline", "venv", "__pycache__", "tests")):
            continue
        for name in dateien:
            if not name.endswith(".py") or ".bak" in name:
                continue
            try:
                q = open(os.path.join(wurzel, name), encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            gelesen.update(re.findall(r'getenv\(\s*["\'](STRIPE_[A-Z_0-9]+)["\']', q))
    return gelesen


@pytest.mark.skipif(not os.path.exists(COMPOSE), reason="docker-compose.yml nicht eingehaengt")
def test_jeder_gelesene_stripe_wert_wird_durchgereicht():
    compose = open(COMPOSE, encoding="utf-8").read()
    fehlend = sorted(
        n for n in _gelesene_namen()
        if n not in NICHT_NOETIG and f"- {n}=" not in compose
    )
    assert not fehlend, (
        "Diese Werte liest der Code, docker compose reicht sie aber nicht an den "
        "Container durch — sie stehen dann wirkungslos in der .env:\n  "
        + "\n  ".join(fehlend)
    )


@pytest.mark.skipif(not os.path.exists(COMPOSE), reason="docker-compose.yml nicht eingehaengt")
def test_early_access_preis_wird_durchgereicht():
    """Der Fall, an dem es aufgefallen ist. Namentlich, damit er nicht zurueckkommt."""
    compose = open(COMPOSE, encoding="utf-8").read()
    assert "- STRIPE_PRICE_PRO_EARLY_MONTHLY=" in compose
    assert "- EARLY_ACCESS_PLAETZE=" in compose, (
        "Die Platzgrenze muss aus derselben Quelle kommen wie der Zaehler auf "
        "der Kampagnenseite, sonst laufen Anzeige und Kaufweg auseinander.")
