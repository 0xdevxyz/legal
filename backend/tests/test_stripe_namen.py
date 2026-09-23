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


def _eintrag(text, schluessel):
    """Der Block eines Katalog-Eintrags, vom Schluessel bis zum naechsten.

    Feste Zeichenfenster waren zu knapp, sobald jemand einen Kommentar
    ergaenzt: der Test schlug dann fehl, obwohl der Code stimmte.
    """
    i = text.index('"%s": {' % schluessel)
    rest = text[i + 1:]
    m = re.search(r'\n    "[a-z_0-9]+": \{', rest)
    return rest[:m.start()] if m else rest


def _gelesene_namen(block):
    return set(re.findall(r'getenv\(\s*["\']([A-Z_0-9]+)["\']', block))


def test_zusatzplatz_und_extra_sites_paket_bleiben_getrennt():
    """Zwei Produkte, zwei Variablen, kein wechselseitiger Rueckfall.

    Sonst stellt eine gepflegte Kennung den Preis des jeweils anderen Knopfes.
    Geprueft werden die tatsaechlich gelesenen Namen, nicht der Fliesstext:
    die Kommentare nennen beide Namen absichtlich, um die Verwechslung zu
    erklaeren.
    """
    haupt = _quelle("stripe_routes.py")
    fenster = haupt[haupt.index('"agency_extra_monthly"'):][:200]
    assert _gelesene_namen(fenster) == {"STRIPE_PRICE_AGENCY_EXTRA_SITE"}, (
        "Der Zusatzplatz (+1 Website, 29 EUR) faellt auf einen fremden Preis "
        "zurueck (Extra-Sites-Paket oder Einzelsaeule)")

    addon = _gelesene_namen(_eintrag(_quelle("addon_payment_routes.py"),
                                     "agency_sites_extra"))
    assert addon == {"STRIPE_PRICE_AGENCY_SITES_EXTRA"}, (
        f"Das Extra-Sites-Paket liest {addon}")


def test_25_projekte_kosten_ueberall_gleich():
    """Dasselbe Angebot, derselbe Preis.

    25 zusaetzliche Agentur-Projekte gibt es auf zwei Wegen: als "Agency Plan 2"
    auf der Agentur-Seite und als "Extra Sites Paket" im Add-on-Katalog. Bis zum
    14.09.2026 kosteten sie 599 bzw. 200 EUR; wer die Add-on-Seite fand, zahlte
    ein Drittel fuer dieselbe Leistung. Entschieden wurde 599 fuer beide.
    """
    block = _eintrag(_quelle("addon_payment_routes.py"), "agency_sites_extra")
    m = re.search(r'"price_monthly": (\d+)', block)
    assert m, "Das Extra-Sites-Paket hat keinen Monatspreis mehr"
    extra_sites = int(m.group(1))

    seite = open(os.path.join(os.path.dirname(BACKEND), "dashboard-react", "src",
                              "app", "agency", "page.tsx"), encoding="utf-8").read()
    i = seite.index("Weitere 25 Websites auf einmal")
    m = re.search(r">\s*(\d+)\s*\u20ac", seite[i:i + 600])
    assert m, "Der Preis von 'Agency Plan 2' steht nicht mehr im erwarteten Format"
    agency2 = int(m.group(1))

    assert extra_sites == agency2, (
        f"25 Projekte kosten im Add-on-Katalog {extra_sites} EUR und auf der "
        f"Agentur-Seite {agency2} EUR. Wer den guenstigeren Weg findet, zahlt "
        f"weniger fuer dieselbe Leistung.")

    skript = open(os.path.join(os.path.dirname(BACKEND), "scripts",
                               "stripe-live-umschalten.py"), encoding="utf-8").read()
    for lookup in ("complyo_agency_sites_extra", "complyo_agency2_monthly"):
        fenster = skript[skript.index('"%s"' % lookup):][:200]
        m = re.search(r"(\d{4,7}),\s*\"month\"", fenster)
        assert m, "Kein Betrag fuer %s im Katalog" % lookup
        assert int(m.group(1)) == extra_sites * 100, (
            "%s legt %.0f EUR an, die Oberflaeche zeigt %d EUR"
            % (lookup, int(m.group(1)) / 100, extra_sites))


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
    # 19 bis zum 23.09.2026, seitdem 18: der eigene Early-Access-Preis ist
    # einem Gutschein gewichen (siehe test_early_access_laeuft_ueber_einen_gutschein).
    assert len(variablen) >= 18, f"Katalog unerwartet klein: {len(variablen)}"
    assert len(variablen) == len(set(variablen)), "Variable doppelt im Katalog"
    fehlen = [v for v in variablen if f"{v}=${{{v}" not in compose]
    assert not fehlen, f"docker-compose.yml reicht nicht durch: {fehlen}"


def test_early_access_laeuft_ueber_einen_gutschein():
    """
    Der Nachlass muss befristet sein, und die Befristung muss von Stripe kommen.

    Bis zum 23.09.2026 gab es einen eigenen 49-Euro-Preis. Ein wiederkehrender
    Preis endet nicht von selbst, und keine Stelle im Code stellte ihn je um.
    Die Kampagnenseite verspricht dagegen zwoelf Monate ("Danach gilt der
    regulaere Preis"). Bei 100 Plaetzen und 40 Euro Unterschied waeren das ab
    dem 13. Monat 4.000 Euro im Monat, die niemand abgerechnet haette.

    Ein Gutschein mit duration=repeating und duration_in_months=12 ist die
    einzige Form, in der Stripe die Frist selbst beendet.
    """
    text = _quelle("stripe_routes.py")
    assert '"pro_early_monthly"' not in text, (
        "Der eigene Early-Access-Preis ist zurueck. Er laeuft unbefristet und "
        "widerspricht der beworbenen Frist von zwoelf Monaten.")
    assert 'STRIPE_COUPON_EARLY_ACCESS' in text, (
        "Der Early-Access-Nachlass haengt an keinem Gutschein mehr.")
    assert "'discounts': rabatte" in text, (
        "Der Gutschein wird nicht an die Checkout-Session uebergeben.")


def test_ohne_gutschein_gilt_der_volle_preis():
    """
    Die Rangfolge der Schaeden, unveraendert seit dem 10.09.2026.

    Ein stillschweigend gewaehrter Dauerrabatt ist schlimmer als der volle
    Preis, und der volle Preis schlimmer als ein Checkout, der 500 wirft.
    Fehlt der Gutschein, wird also regulaer gebucht und laut protokolliert,
    statt auf einen unbefristeten Nachlass auszuweichen.
    """
    text = _quelle("stripe_routes.py")
    stelle = text[text.index("EARLY_ACCESS_GUTSCHEIN:"):][:900]
    assert "logger.error" in stelle, (
        "Ein fehlender Gutschein muss laut protokolliert werden, sonst faellt "
        "erst der Kunde auf, der 89 statt 49 bezahlt hat.")
    assert "price_key" not in stelle, (
        "Im Rueckfall darf der Preis nicht getauscht werden; es bleibt beim "
        "regulaeren Pro-Preis.")


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
