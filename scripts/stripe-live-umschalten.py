#!/usr/bin/env python3
"""
Stripe von Test auf Live umschalten, ohne im Dashboard zu klicken.

Warum es dieses Skript gibt
---------------------------
Seit dem Launch-Audit vom 31.08.2026 steht auf der Entscheidungsliste:
"Stripe läuft auf sk_test_, niemand kann zahlen." Der Grund, warum das liegen
blieb, war nie die Entscheidung, sondern die Arbeit dahinter: zehn Preise in
vier Produkten von Hand anlegen, zwei Webhook-Endpunkte registrieren, die
Secrets abschreiben, zwölf Zeilen in der .env tauschen, und bei einem Tippfehler
bucht der erste Kunde einen Preis, den es nicht gibt (das war am 10.09. bereits
einmal so: der 49-Euro-Preis erreichte den Container nie).

Dieses Skript macht aus der Stunde Klickarbeit einen Aufruf und aus dem
Tippfehler-Risiko eine Prüfung. Es braucht nur den Live-Geheimschlüssel, den
ausschliesslich der Kontoinhaber aus dem Stripe-Dashboard holen kann.

Aufruf
------
    # 1. Im Live-Modus Produkte, Preise und Webhooks anlegen (idempotent:
    #    vorhandene Preise werden über lookup_key wiedergefunden, nicht doppelt
    #    angelegt) und den fertigen .env-Block ausgeben:
    STRIPE_LIVE_SECRET_KEY=sk_live_... python3 scripts/stripe-live-umschalten.py anlegen

    # 2. Nach dem Eintragen in die .env und `docker compose up -d backend`:
    #    prüft die .env gegen Stripe (Modus, jede Preis-ID vorhanden, aktiv,
    #    richtiger Betrag, Webhooks registriert):
    python3 scripts/stripe-live-umschalten.py pruefen [/pfad/zur/.env]

Keine Abhängigkeiten ausser der Standardbibliothek: das Skript läuft auf dem
Host, nicht im Container, weil die .env dort liegt.

Die Beträge sind die der Preisrunde "Weg B" vom 07.09.2026 (siehe Memory
"complyo Tarifmodell"), netto, weil complyo nur an Unternehmer verkauft
(AGB Ziffer 1); Stripe rechnet die Umsatzsteuer über tax_behavior=exclusive
dazu, sobald Stripe Tax aktiv ist.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

STRIPE_API = "https://api.stripe.com/v1"

# lookup_key -> (Produktname, Betrag in Cent, Intervall oder None, .env-Variable)
KATALOG = [
    ("complyo_pro_monthly",       "complyo Pro",          8900,   "month", "STRIPE_PRICE_PRO_MONTHLY"),
    ("complyo_pro_yearly",        "complyo Pro",          89000,  "year",  "STRIPE_PRICE_PRO_YEARLY"),
    # Early Access: die ersten 100 bestätigten Wartelistenplätze, 49 statt 89.
    # Die Zwölf-Monats-Grenze setzt der Code beim Verlängern durch, nicht Stripe.
    ("complyo_pro_early_monthly", "complyo Pro",          4900,   "month", "STRIPE_PRICE_PRO_EARLY_MONTHLY"),
    ("complyo_agency_monthly",    "complyo Agentur",      59900,  "month", "STRIPE_PRICE_AGENCY_MONTHLY"),
    ("complyo_agency_yearly",     "complyo Agentur",      599000, "year",  "STRIPE_PRICE_AGENCY_YEARLY"),
    ("complyo_single_monthly",    "complyo Einzelsäule",  2900,   "month", "STRIPE_PRICE_SINGLE_MODULE"),
    ("complyo_monitor_monthly",   "complyo Monitoring",   3900,   "month", "STRIPE_PRICE_MONITOR_MONTHLY"),
    ("complyo_monitor_yearly",    "complyo Monitoring",   39000,  "year",  "STRIPE_PRICE_MONITOR_YEARLY"),
    ("complyo_expert_einmalig",   "complyo Expert",       399000, None,    "STRIPE_PRICE_EXPERT"),
    ("complyo_update_monthly",    "complyo Expert",       2900,   "month", "STRIPE_PRICE_UPDATE_MONTHLY"),
]

# Welche Ereignisse die beiden Webhook-Handler tatsächlich auswerten
# (stripe_routes.py Zeile ~654 ff., addon_payment_routes.py Zeile ~534 ff.).
# Mehr abonnieren hiesse mehr Rauschen im Log, weniger hiesse stille Ausfälle.
WEBHOOKS = [
    ("https://api.complyo.de/api/stripe/webhook", "STRIPE_WEBHOOK_SECRET", [
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_succeeded",
        "invoice.payment_failed",
    ]),
    ("https://api.complyo.de/api/addons/webhook", "STRIPE_WEBHOOK_SECRET_ADDONS", [
        "checkout.session.completed",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_succeeded",
        "invoice.payment_failed",
    ]),
]


class StripeFehler(Exception):
    pass


def _anfrage(key: str, methode: str, pfad: str, daten=None):
    url = STRIPE_API + pfad
    body = None
    if daten is not None:
        body = urllib.parse.urlencode(_flach(daten), doseq=True).encode()
    req = urllib.request.Request(url, data=body, method=methode)
    req.add_header("Authorization", "Basic " + base64.b64encode((key + ":").encode()).decode())
    if body is not None:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=40) as antwort:
            return json.load(antwort)
    except urllib.error.HTTPError as e:
        try:
            fehler = json.load(e)["error"]
            raise StripeFehler(f"{e.code} {fehler.get('type')}: {fehler.get('message')}") from None
        except (ValueError, KeyError):
            raise StripeFehler(f"HTTP {e.code} bei {methode} {pfad}") from None


def _flach(daten, praefix=""):
    """Stripe erwartet Formularkodierung: {'a': {'b': 1}} -> a[b]=1, Listen -> a[0]=x."""
    flach = []
    for k, v in daten.items():
        name = f"{praefix}[{k}]" if praefix else k
        if isinstance(v, dict):
            flach.extend(_flach(v, name))
        elif isinstance(v, (list, tuple)):
            for i, e in enumerate(v):
                flach.append((f"{name}[{i}]", e))
        elif isinstance(v, bool):
            flach.append((name, "true" if v else "false"))
        else:
            flach.append((name, v))
    return flach


def _alle(key: str, pfad: str, **params):
    """Alle Seiten einer Liste."""
    params = dict(params, limit=100)
    ergebnis = []
    while True:
        seite = _anfrage(key, "GET", pfad + "?" + urllib.parse.urlencode(params, doseq=True))
        ergebnis.extend(seite["data"])
        if not seite.get("has_more"):
            return ergebnis
        params["starting_after"] = seite["data"][-1]["id"]


def modus(key: str) -> str:
    if key.startswith("sk_live_"):
        return "live"
    if key.startswith("sk_test_"):
        return "test"
    return "unbekannt"


# ---------------------------------------------------------------------------
# anlegen
# ---------------------------------------------------------------------------

def anlegen(key: str) -> int:
    if modus(key) != "live":
        print("Der Schlüssel in STRIPE_LIVE_SECRET_KEY ist kein Live-Schlüssel (sk_live_...).")
        return 2

    konto = _anfrage(key, "GET", "/account")
    print(f"Stripe-Konto: {konto.get('business_profile', {}).get('name') or konto['id']} "
          f"(charges_enabled={konto.get('charges_enabled')}, "
          f"payouts_enabled={konto.get('payouts_enabled')})")
    if not konto.get("charges_enabled"):
        print("WARNUNG: charges_enabled ist false. Stripe nimmt in diesem Zustand kein Geld an;"
              " erst die Kontoaktivierung im Dashboard abschliessen (Unternehmensdaten, Bankkonto).")

    produkte = {p["name"]: p for p in _alle(key, "/products", active=True)}
    preise = {p.get("lookup_key"): p for p in _alle(key, "/prices", active=True) if p.get("lookup_key")}

    env_zeilen = []
    for lookup, produktname, betrag, intervall, variable in KATALOG:
        produkt = produkte.get(produktname)
        if not produkt:
            produkt = _anfrage(key, "POST", "/products", {"name": produktname})
            produkte[produktname] = produkt
            print(f"Produkt angelegt: {produktname} ({produkt['id']})")

        preis = preise.get(lookup)
        if preis:
            passt = (preis["unit_amount"] == betrag
                     and (preis.get("recurring") or {}).get("interval") == intervall
                     and preis["product"] == produkt["id"])
            if not passt:
                print(f"WARNUNG: Preis {lookup} existiert ({preis['id']}), aber mit anderem Betrag/"
                      f"Intervall/Produkt. Nicht angefasst, bitte im Dashboard klären.")
        else:
            daten = {
                "product": produkt["id"],
                "currency": "eur",
                "unit_amount": betrag,
                "lookup_key": lookup,
                "tax_behavior": "exclusive",
                "nickname": lookup,
            }
            if intervall:
                daten["recurring"] = {"interval": intervall}
            preis = _anfrage(key, "POST", "/prices", daten)
            preise[lookup] = preis
            print(f"Preis angelegt: {lookup} = {betrag / 100:.2f} EUR "
                  f"{'/' + intervall if intervall else 'einmalig'} ({preis['id']})")
        env_zeilen.append(f"{variable}={preis['id']}")

    vorhandene = {w["url"]: w for w in _alle(key, "/webhook_endpoints")}
    for url, variable, ereignisse in WEBHOOKS:
        w = vorhandene.get(url)
        if w:
            fehlend = sorted(set(ereignisse) - set(w.get("enabled_events") or []))
            if fehlend and "*" not in (w.get("enabled_events") or []):
                _anfrage(key, "POST", f"/webhook_endpoints/{w['id']}",
                         {"enabled_events": sorted(set(ereignisse) | set(w["enabled_events"]))})
                print(f"Webhook {url}: Ereignisse ergänzt: {', '.join(fehlend)}")
            else:
                print(f"Webhook {url}: vorhanden ({w['status']})")
            env_zeilen.append(f"# {variable}: Secret nur bei der Anlage sichtbar; im Dashboard unter"
                              f" Developers > Webhooks > {url} > 'Reveal' nachlesen")
        else:
            w = _anfrage(key, "POST", "/webhook_endpoints", {
                "url": url, "enabled_events": ereignisse,
                "description": "complyo Backend (angelegt von scripts/stripe-live-umschalten.py)",
            })
            print(f"Webhook angelegt: {url} ({w['id']})")
            env_zeilen.append(f"{variable}={w['secret']}")

    print()
    print("=== In /home/clawd/saas/legal/.env eintragen (vorher Kopie: cp .env .env.bak-$(date +%F)-vor-live) ===")
    print(f"STRIPE_SECRET_KEY={key}")
    print("STRIPE_PUBLISHABLE_KEY=pk_live_...   # aus dem Dashboard, wird vom Backend nicht benutzt, nur der Vollständigkeit halber")
    for z in env_zeilen:
        print(z)
    print("=== danach: cd /home/clawd/saas/legal && docker compose up -d backend  (Umgebungsvariablen greifen erst beim Neuanlegen des Containers) ===")
    print("=== dann: python3 scripts/stripe-live-umschalten.py pruefen ===")
    return 0


# ---------------------------------------------------------------------------
# pruefen
# ---------------------------------------------------------------------------

def lies_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            zeile = zeile.strip()
            if not zeile or zeile.startswith("#") or "=" not in zeile:
                continue
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip().strip('"').strip("'")
    return werte


def pruefen(env_pfad: str) -> int:
    env = lies_env(env_pfad)
    key = env.get("STRIPE_SECRET_KEY", "")
    if not key:
        print(f"STRIPE_SECRET_KEY fehlt in {env_pfad}")
        return 2
    m = modus(key)
    print(f"Modus laut .env: {m}")
    befunde = []
    if m != "live":
        befunde.append("Stripe läuft NICHT im Live-Modus: kein Kunde kann bezahlen.")

    try:
        preise = {p["id"]: p for p in _alle(key, "/prices")}
    except StripeFehler as e:
        print(f"Stripe antwortet nicht: {e}")
        return 2

    for lookup, produktname, betrag, intervall, variable in KATALOG:
        pid = env.get(variable)
        if not pid:
            befunde.append(f"{variable} fehlt in der .env ({lookup}).")
            continue
        p = preise.get(pid)
        if not p:
            befunde.append(f"{variable}={pid}: Preis existiert in diesem Stripe-Modus nicht.")
            continue
        if not p["active"]:
            befunde.append(f"{variable}={pid}: Preis ist inaktiv.")
        if p["unit_amount"] != betrag:
            befunde.append(f"{variable}={pid}: {p['unit_amount'] / 100:.2f} EUR statt {betrag / 100:.2f} EUR.")
        ist_intervall = (p.get("recurring") or {}).get("interval")
        if ist_intervall != intervall:
            befunde.append(f"{variable}={pid}: Intervall {ist_intervall} statt {intervall}.")

    webhooks = {w["url"]: w for w in _alle(key, "/webhook_endpoints")}
    for url, variable, ereignisse in WEBHOOKS:
        w = webhooks.get(url)
        if not w:
            befunde.append(f"Webhook-Endpunkt {url} ist in Stripe nicht registriert: "
                           f"Abos würden nach Zahlung nie freigeschaltet, ausser über verify-checkout.")
            continue
        if w["status"] != "enabled":
            befunde.append(f"Webhook {url}: Status {w['status']}.")
        fehlend = sorted(set(ereignisse) - set(w.get("enabled_events") or []))
        if fehlend and "*" not in (w.get("enabled_events") or []):
            befunde.append(f"Webhook {url}: Ereignisse fehlen: {', '.join(fehlend)}.")
        if not env.get(variable, "").startswith("whsec_"):
            befunde.append(f"{variable} fehlt in der .env oder ist kein whsec_-Secret.")

    # Der Container muss dieselben Werte sehen wie die .env. Am 10.09.2026 stand
    # STRIPE_PRICE_PRO_EARLY_MONTHLY in der .env, aber nicht in der
    # environment-Liste der compose-Datei, und erreichte den Container nie.
    compose = os.path.join(os.path.dirname(os.path.abspath(env_pfad)), "docker-compose.yml")
    if os.path.exists(compose):
        with open(compose, encoding="utf-8") as fh:
            compose_text = fh.read()
        for _, _, _, _, variable in KATALOG:
            if f"{variable}=" not in compose_text and f"${{{variable}" not in compose_text:
                befunde.append(f"{variable} wird in docker-compose.yml nicht an den Container durchgereicht.")

    if befunde:
        print(f"{len(befunde)} Befund(e):")
        for b in befunde:
            print(f"  - {b}")
        return 1
    print("Alles stimmig: Live-Modus, alle Preise vorhanden und korrekt, Webhooks registriert, compose reicht alles durch.")
    return 0


def main(argv) -> int:
    if len(argv) < 2 or argv[1] not in ("anlegen", "pruefen"):
        print(__doc__)
        return 2
    if argv[1] == "anlegen":
        key = os.getenv("STRIPE_LIVE_SECRET_KEY", "")
        if not key:
            print("STRIPE_LIVE_SECRET_KEY nicht gesetzt. Den Live-Geheimschlüssel holt der Kontoinhaber"
                  " im Stripe-Dashboard unter Developers > API keys (Live mode).")
            return 2
        try:
            return anlegen(key)
        except StripeFehler as e:
            print(f"Stripe-Fehler: {e}")
            return 1
    env_pfad = argv[2] if len(argv) > 2 else "/home/clawd/saas/legal/.env"
    return pruefen(env_pfad)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
