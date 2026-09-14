# -*- coding: utf-8 -*-
"""Stripe-Webhooks muessen an der CSRF-Schranke vorbeikommen.

Am 15.09.2026, einen Tag nach dem Live-Schalten, mit einem signierten Ereignis
gemessen: JEDER Webhook wurde mit 403 "CSRF token missing or invalid"
abgewiesen. Stripe schickt seine Ereignisse ohne Sitzung und ohne Cookie, der
Double-Submit-Check kann dort nie aufgehen.

Was das bedeutet hat: eine Zahlung haette den Tarif nicht freigeschaltet, eine
Kuendigung waere nie angekommen, eine fehlgeschlagene Abbuchung nie gemeldet.
Stripe wiederholt drei Tage lang und gibt dann auf.

Das ist der vierte Fall derselben Klasse (siehe die Kommentare in
csrf_middleware.py). Deshalb ein Test, der jede POST-Route mit "webhook" im
Pfad gegen die Ausnahmeliste haelt: die naechste neue Webhook-Route faellt
hier auf, nicht beim Kunden.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _quelle(datei):
    with open(os.path.join(BACKEND, datei), encoding="utf-8") as fh:
        return fh.read()


def _ausgenommen(pfad, text):
    if f'"{pfad}"' in text:
        return True
    for praefix in re.findall(r'"(/[a-z/_-]+/)"', text[text.index("EXEMPT_PREFIXES"):]):
        if pfad.startswith(praefix):
            return True
    return False


def test_stripe_webhooks_sind_ausgenommen():
    text = _quelle("csrf_middleware.py")
    for pfad in ("/api/stripe/webhook", "/api/addons/webhook"):
        assert _ausgenommen(pfad, text), (
            f"{pfad} steht nicht in EXEMPT_PATHS. Stripe hat kein CSRF-Cookie: "
            f"jedes Ereignis wird mit 403 abgewiesen, Zahlungen schalten nichts "
            f"frei und Kuendigungen kommen nie an.")


def test_jede_webhook_route_ist_ausgenommen():
    """Die naechste neue Webhook-Route soll hier auffallen, nicht beim Kunden."""
    csrf = _quelle("csrf_middleware.py")
    gefunden = []
    for name in sorted(os.listdir(BACKEND)):
        if not name.endswith(".py") or ".bak" in name:
            continue
        text = _quelle(name)
        m = re.search(r'router\s*=\s*APIRouter\(\s*prefix\s*=\s*["\']([^"\']+)', text)
        if not m:
            continue
        praefix = m.group(1)
        for route in re.findall(r'@router\.post\(\s*["\']([^"\']*webhook[^"\']*)["\']', text):
            gefunden.append(praefix + route)

    assert gefunden, "Keine Webhook-Route gefunden — sucht der Test noch richtig?"
    fehlend = [p for p in gefunden if not _ausgenommen(p, csrf)]
    assert not fehlend, f"Webhook-Routen ohne CSRF-Ausnahme: {fehlend}"


def test_ausnahme_traegt_ihre_begruendung():
    """Eine Ausnahme ohne Grund wird beim naechsten Aufraeumen entfernt."""
    text = _quelle("csrf_middleware.py")
    stelle = text[text.index("/api/stripe/webhook") - 1200:text.index("/api/stripe/webhook")]
    assert "Signatur" in stelle, (
        "Bei der Webhook-Ausnahme fehlt der Grund: sie ist zulaessig, WEIL die "
        "Routen ihre Berechtigung aus der Stripe-Signatur ziehen.")
