"""Genau ein Bezahlweg, genau ein Webhook-Ziel.

Am 31.08.2026 hatte complyo drei Bezahl-Router nebeneinander:
/api/stripe/* (stripe_routes.py, den das Dashboard benutzt), /api/payment/*
(payment_routes.py) und /api/v2/payments/* (in main_production, auf
payment/stripe_service.py). Alle drei waren eingebunden, alle drei antworteten,
und alle drei boten einen /webhook an.

Vor dem Live-Gang muss in Stripe eine Webhook-Adresse eingetragen werden. Von
drei plausibel aussehenden Adressen war genau eine richtig. Wer eine der beiden
anderen eingetragen haette, dessen erste bezahlte Rechnung waere in einen
Schreibzugriff auf eine nie angelegte Zahlungstabelle gelaufen: der Kunde
zahlt, complyo erfaehrt es nie.

Die beiden abgeloesten Wege sind am 03.09.2026 entfernt worden. Dieser Test
haelt fest, dass sie nicht zurueckkommen.
"""

import os
import re

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _alle_quellen():
    treffer = []
    for wurzel, verzeichnisse, dateien in os.walk(BACKEND):
        verzeichnisse[:] = [
            d for d in verzeichnisse
            if d not in {"tests", "alembic", "_archive_pre_baseline", "__pycache__"}
        ]
        for name in dateien:
            if name.endswith(".py"):
                treffer.append(os.path.join(wurzel, name))
    return treffer


class TestNurEinBezahlweg:
    def test_keine_v2_payments_routen_mehr(self):
        gefunden = []
        muster = re.compile(r"@app\.(?:get|post|put|delete)\(\s*[\"']/api/v2/payments")
        for pfad in _alle_quellen():
            with open(pfad, encoding="utf-8") as fh:
                if muster.search(fh.read()):
                    gefunden.append(os.path.relpath(pfad, BACKEND))
        assert not gefunden, f"/api/v2/payments ist zurueck in: {gefunden}"

    def test_kein_api_payment_router_mehr(self):
        gefunden = []
        muster = re.compile(r"APIRouter\([^)]*prefix\s*=\s*[\"']/api/payment[\"']")
        for pfad in _alle_quellen():
            with open(pfad, encoding="utf-8") as fh:
                if muster.search(fh.read()):
                    gefunden.append(os.path.relpath(pfad, BACKEND))
        assert not gefunden, f"/api/payment-Router ist zurueck in: {gefunden}"

    def test_abgeloeste_stripe_service_klasse_ist_weg(self):
        """payment/stripe_service.py verlangte Tabellen und Spalten, die es nie gab."""
        assert not os.path.exists(os.path.join(BACKEND, "payment", "stripe_service.py"))
        # Auf Import pruefen, nicht auf Erwaehnung: der Grund fuer die Loeschung
        # steht als Kommentar in main_production und soll dort stehen bleiben.
        muster = re.compile(r"(?:from\s+payment[\w.]*\s+import|import\s+payment\b|StripeService\s*\()")
        gefunden = [
            os.path.relpath(p, BACKEND)
            for p in _alle_quellen()
            if muster.search(open(p, encoding="utf-8").read())
        ]
        assert not gefunden, f"StripeService wieder eingebunden in: {gefunden}"

    def test_der_kaufweg_des_dashboards_bleibt_bestehen(self):
        """Gegenprobe: die Aufraeumaktion darf den lebenden Weg nicht mitnehmen."""
        pfad = os.path.join(BACKEND, "stripe_routes.py")
        assert os.path.exists(pfad), "stripe_routes.py fehlt - das ist der echte Kaufweg"
        text = open(pfad, encoding="utf-8").read()
        assert 'prefix="/api/stripe"' in text
        for route in ("/create-checkout", "/webhook", "/subscription-status", "/verify-checkout"):
            assert route in text, f"{route} fehlt in stripe_routes.py"


class TestWebhookZiele:
    def test_hoechstens_die_beiden_erwarteten_webhooks(self):
        """Ein Webhook fuer Abos (/api/stripe), einer fuer Zusatzmodule (/api/addons).

        Mehr duerfen es nicht werden: jede weitere Adresse ist eine weitere
        Gelegenheit, beim Eintrag in Stripe die falsche zu erwischen.
        """
        mit_webhook = []
        for pfad in _alle_quellen():
            text = open(pfad, encoding="utf-8").read()
            if re.search(r"@(?:router|app)\.post\(\s*[\"'][^\"']*webhook", text):
                mit_webhook.append(os.path.basename(pfad))
        assert sorted(mit_webhook) == ["addon_payment_routes.py", "stripe_routes.py"], (
            f"Unerwartete Webhook-Endpunkte: {sorted(mit_webhook)}"
        )
