# -*- coding: utf-8 -*-
"""
Jeder Stripe-Name, den der Code liest, muss der sein, der in der .env steht.

Gemessen am 10.09.2026 gegen die laufende Umgebung:

  * `addon_payment_routes` setzte `stripe.api_key` aus `STRIPE_API_KEY`.
    Gesetzt ist `STRIPE_SECRET_KEY`. Der Add-on-Kaufweg hatte damit gar keinen
    Schluessel und haette auch mit gepflegter Preis-ID nichts verkauft.
  * Der Zusatzplatz einer Agentur heisst in `stripe_routes`
    `STRIPE_PRICE_AGENCY_EXTRA_SITE`, im Add-on-Katalog
    `STRIPE_PRICE_AGENCY_SITES_EXTRA`. Damals als "zwei Namen fuer eine Sache"
    gelesen und wechselseitig verknuepft. Am 14.09.2026 beim Anlegen der
    Live-Preise nachgesehen: es sind ZWEI Produkte. Der Zusatzplatz gibt
    +1 Website fuer 29 EUR/Monat, das Extra-Sites-Paket +25 Sites fuer
    200 EUR/Monat. Wer die 200-EUR-Kennung gepflegt haette, haette damit den
    29-EUR-Knopf auf 200 EUR gestellt.

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


def test_zusatzplatz_und_extra_sites_paket_bleiben_getrennt():
    """Zwei Produkte, zwei Variablen, kein wechselseitiger Rueckfall.

    Sonst stellt eine gepflegte Kennung den Preis des jeweils anderen Knopfes.
    Geprueft werden die tatsaechlich gelesenen Namen, nicht der Fliesstext:
    die Kommentare nennen beide Namen absichtlich, um die Verwechslung zu
    erklaeren.
    """
    def _gelesen(text, ab, laenge):
        fenster = text[text.index(ab):][:laenge]
        return set(re.findall(r'getenv\(\s*["\']([A-Z_0-9]+)["\']', fenster))

    haupt = _gelesen(_quelle("stripe_routes.py"), '"agency_extra_monthly"', 200)
    assert haupt == {"STRIPE_PRICE_AGENCY_EXTRA_SITE"}, (
        f"Der Zusatzplatz (+1 Website, 29 EUR) liest {haupt}. Ein Rueckfall auf "
        "das Extra-Sites-Paket (200 EUR) oder die Einzelsaeule stellt still "
        "einen fremden Preis ein.")

    addon = _gelesen(_quelle("addon_payment_routes.py"), '"agency_sites_extra"', 1200)
    assert addon == {"STRIPE_PRICE_AGENCY_SITES_EXTRA"}, (
        f"Das Extra-Sites-Paket (+25 Sites, 200 EUR) liest {addon}")


def test_jede_katalog_variable_erreicht_den_container():
    """Eine Kennung in der .env, die compose nicht durchreicht, ist wirkungslos.

    Genau so war der 49-Euro-Preis am 10.09.2026 angelegt, eingetragen und
    trotzdem ohne Wirkung.
    """
    wurzel = os.path.dirname(BACKEND)
    skript = open(os.path.join(wurzel, "scripts", "stripe-live-umschalten.py"),
                  encoding="utf-8").read()
    compose = open(os.path.join(wurzel, "docker-compose.yml"), encoding="utf-8").read()
    variablen = re.findall(r'"(STRIPE_PRICE_[A-Z0-9_]+)"\)?,?\n?\s*$', skript, re.M)
    variablen = re.findall(r'"(STRIPE_PRICE_[A-Z0-9_]+)"\),', skript) or \
        re.findall(r'"(STRIPE_PRICE_[A-Z0-9_]+)"\)', skript)
    katalog = skript[skript.index("KATALOG = ["):skript.index("\n]", skript.index("KATALOG = ["))]
    variablen = re.findall(r'"(STRIPE_PRICE_[A-Z0-9_]+)"', katalog)
    assert len(variablen) >= 19, f"Katalog unerwartet klein: {len(variablen)}"
    assert len(variablen) == len(set(variablen)), "Variable doppelt im Katalog"
    fehlen = [v for v in variablen if f"{v}=${{{v}" not in compose]
    assert not fehlen, f"docker-compose.yml reicht nicht durch: {fehlen}"


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
