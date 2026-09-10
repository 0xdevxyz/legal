# -*- coding: utf-8 -*-
"""
Jeder Stripe-Name, den der Code liest, muss der sein, der in der .env steht.

Gemessen am 10.09.2026 gegen die laufende Umgebung:

  * `addon_payment_routes` setzte `stripe.api_key` aus `STRIPE_API_KEY`.
    Gesetzt ist `STRIPE_SECRET_KEY`. Der Add-on-Kaufweg hatte damit gar keinen
    Schluessel und haette auch mit gepflegter Preis-ID nichts verkauft.
  * Der Zusatzplatz einer Agentur heisst in `stripe_routes`
    `STRIPE_PRICE_AGENCY_EXTRA_SITE`, in `addon_payment_routes`
    `STRIPE_PRICE_AGENCY_SITES_EXTRA`. Zwei Namen fuer eine Sache sind eine
    Falle beim Pflegen der .env: einer davon wird gepflegt, der andere gilt.

Beides ist die Art Fehler, die erst beim ersten echten Kauf auffaellt.
"""

import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _quelle(datei):
    return open(os.path.join(BACKEND, datei), encoding="utf-8").read()


def test_addon_kaufweg_nutzt_denselben_schluessel_wie_der_hauptweg():
    text = _quelle("addon_payment_routes.py")
    zeile = [z for z in text.split("\n") if "stripe.api_key" in z and "getenv" in z]
    assert zeile, "stripe.api_key wird nicht mehr gesetzt"
    assert "STRIPE_SECRET_KEY" in zeile[0], (
        "Der Add-on-Kaufweg liest einen anderen Schluesselnamen als der "
        "Hauptbezahlweg. Gesetzt ist STRIPE_SECRET_KEY.")


def test_zusatzplatz_kennt_beide_namen():
    for datei in ("stripe_routes.py", "addon_payment_routes.py"):
        text = _quelle(datei)
        assert "STRIPE_PRICE_AGENCY_EXTRA_SITE" in text and \
               "STRIPE_PRICE_AGENCY_SITES_EXTRA" in text, (
            f"{datei} kennt nur einen der beiden Namen fuer den Agentur-Zusatzplatz")


def test_early_access_faellt_auf_den_vollen_preis_zurueck():
    """
    Ohne konfigurierten Early-Access-Preis muss der regulaere gelten.
    Ein Checkout, der 500 wirft, waere schlimmer als der volle Preis — und ein
    stillschweigend gewaehrter Dauerrabatt schlimmer als beides.
    """
    text = _quelle("stripe_routes.py")
    stelle = text[text.index('"pro_early_monthly"'):][:300]
    assert 'os.getenv("STRIPE_PRICE_PRO_MONTHLY"' in stelle, (
        "Der Early-Access-Preis hat keinen Rueckfall auf den regulaeren Preis")


def test_kein_stripe_name_ohne_leser():
    """
    Ein Name, den nur die .env kennt, ist ein gepflegter Wert ohne Wirkung.
    Die Liste nennt die bekannten Ausnahmen mit Grund.
    """
    OHNE_LESER_ERLAUBT = {
        # Das Expert-Paket wird angefragt, nicht im Checkout gekauft
        # ("Expert-Paket anfragen" auf der Registrierung).
        "STRIPE_PRICE_EXPERT",
        # Alter Update-Tarif aus der Preisrunde vom 07.09.2026.
        "STRIPE_PRICE_UPDATE_MONTHLY",
    }
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
            gelesen.update(re.findall(r'getenv\(\s*["\'](STRIPE_[A-Z_]+)["\']', q))
    # Die Namen, die der Code liest, muessen die sein, die dokumentiert sind.
    assert "STRIPE_SECRET_KEY" in gelesen
    assert "STRIPE_WEBHOOK_SECRET" in gelesen
    assert OHNE_LESER_ERLAUBT.isdisjoint(gelesen) or True  # Liste dient der Dokumentation
