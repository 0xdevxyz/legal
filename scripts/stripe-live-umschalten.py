#!/usr/bin/env python3
"""
Stripe von Test auf Live umschalten, ohne im Dashboard zu klicken.

Warum es dieses Skript gibt
---------------------------
Seit dem Launch-Audit vom 31.08.2026 steht auf der Entscheidungsliste:
"Stripe läuft auf sk_test_, niemand kann zahlen." Der Grund, warum das liegen
blieb, war nie die Entscheidung, sondern die Arbeit dahinter: 19 Preise in
13 Produkten von Hand anlegen, zwei Webhook-Endpunkte registrieren, die
Secrets abschreiben, zwanzig Zeilen in der .env tauschen, und bei einem
Tippfehler bucht der erste Kunde einen Preis, den es nicht gibt (das war am
10.09. bereits einmal so: der 49-Euro-Preis erreichte den Container nie).

Dieses Skript macht aus der Stunde Klickarbeit einen Aufruf und aus dem
Tippfehler-Risiko eine Prüfung. Es braucht nur den Live-Geheimschlüssel, den
ausschliesslich der Kontoinhaber aus dem Stripe-Dashboard holen kann.

Aufruf
------
    # 1. Im Live-Modus Produkte, Preise und Webhooks anlegen (idempotent:
    #    vorhandene Preise werden über lookup_key wiedergefunden, nicht doppelt
    #    angelegt) und alles gleich in die .env eintragen (Kopie vorher):
    python3 scripts/stripe-live-umschalten.py anlegen --schreiben

    #    Der Schlüssel wird unsichtbar abgefragt; er steht damit weder in der
    #    Shell-Historie noch in der Prozessliste. Ohne --schreiben gibt das
    #    Skript den .env-Block nur aus.

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
    # Early Access hat seit dem 23.09.2026 keinen eigenen Preis mehr. Der
    # Nachlass laeuft ueber den Gutschein `early-access-12m` auf den regulaeren
    # Pro-Preis: 40 Euro Abzug, duration=repeating, duration_in_months=12.
    #
    # Der Kommentar, der hier stand, sagte "Die Zwoelf-Monats-Grenze setzt der
    # Code beim Verlaengern durch, nicht Stripe". Das war nie so: es gab keine
    # Stelle, die verlaengert oder umstellt. Ein wiederkehrender Preis laeuft
    # unbefristet, und der Nachlass waere dauerhaft geblieben.
    ("complyo_agency_monthly",    "complyo Agentur",      59900,  "month", "STRIPE_PRICE_AGENCY_MONTHLY"),
    ("complyo_agency_yearly",     "complyo Agentur",      599000, "year",  "STRIPE_PRICE_AGENCY_YEARLY"),
    ("complyo_single_monthly",    "complyo Einzelsäule",  2900,   "month", "STRIPE_PRICE_SINGLE_MODULE"),
    ("complyo_monitor_monthly",   "complyo Monitoring",   3900,   "month", "STRIPE_PRICE_MONITOR_MONTHLY"),
    ("complyo_monitor_yearly",    "complyo Monitoring",   39000,  "year",  "STRIPE_PRICE_MONITOR_YEARLY"),
    ("complyo_expert_einmalig",   "complyo Expert",       399000, None,    "STRIPE_PRICE_EXPERT"),
    ("complyo_update_monthly",    "complyo Expert",       2900,   "month", "STRIPE_PRICE_UPDATE_MONTHLY"),

    # ── Agentur-Erweiterungen, buchbar wenn die 25 Projekte voll sind ────────
    # Beide Knoepfe stehen auf /agency, sobald das Limit erreicht ist.
    ("complyo_agency_extra_site", "complyo Agentur Zusatzplatz",
     2900,   "month", "STRIPE_PRICE_AGENCY_EXTRA_SITE"),
    ("complyo_agency2_monthly",   "complyo Agentur Folgepaket",
     59900,  "month", "STRIPE_PRICE_AGENCY2_MONTHLY"),
    ("complyo_agency2_yearly",    "complyo Agentur Folgepaket",
     599000, "year",  "STRIPE_PRICE_AGENCY2_YEARLY"),

    # ── Add-ons aus dem Add-on-Katalog (backend/addon_payment_routes.py) ─────
    # Die Betraege sind die, die der Katalog dem Kunden anzeigt. Weichen sie
    # ab, zeigt die Oberflaeche einen Preis und Stripe bucht einen anderen;
    # `pruefen` vergleicht deshalb beide Seiten.
    ("complyo_comploai_guard",    "complyo ComploAI Guard",
     9900,   "month", "STRIPE_PRICE_COMPLOAI_GUARD"),
    ("complyo_priority_support",  "complyo Priority Support",
     8900,   "month", "STRIPE_PRICE_PRIORITY_SUPPORT"),
    # Gleiches Angebot wie das Folgepaket (25 Projekte), deshalb derselbe
    # Betrag. Bis zum 14.09.2026 standen hier 200 EUR.
    ("complyo_agency_sites_extra", "complyo Extra Sites Paket",
     59900,  "month", "STRIPE_PRICE_AGENCY_SITES_EXTRA"),
    ("complyo_expert_ai_audit",   "complyo Expert AI Act Audit",
     299900, None,    "STRIPE_PRICE_EXPERT_AUDIT"),
    ("complyo_implementation",    "complyo AI Act Implementation Support",
     199900, None,    "STRIPE_PRICE_IMPLEMENTATION"),
    ("complyo_custom_integration", "complyo Custom Integration",
     399900, None,    "STRIPE_PRICE_CUSTOM_INTEGRATION"),
]

# Kein Preis darf an zwei Stellen haengen. Bis zum 14.09.2026 lasen der
# Zusatzplatz (+1 Website, 29 EUR) und das Extra-Sites-Paket (+25 Sites,
# 200 EUR) dieselben zwei Variablennamen wechselseitig; eine gepflegte Kennung
# haette den einen Knopf auf den Preis des anderen gestellt.
_variablen = [k[4] for k in KATALOG]
assert len(_variablen) == len(set(_variablen)), "Variable doppelt im Katalog"
_lookups = [k[0] for k in KATALOG]
assert len(_lookups) == len(set(_lookups)), "lookup_key doppelt im Katalog"

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

def anlegen(key: str, schreiben: bool = False) -> int:
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

    werte = {"STRIPE_SECRET_KEY": key}
    werte.update(dict(z.split("=", 1) for z in env_zeilen if not z.startswith("#")))

    # Ein Webhook-Geheimnis zeigt Stripe NUR bei der Anlage. Existierte der
    # Endpunkt schon, steht in der .env weiter das Geheimnis aus dem Testmodus,
    # und jede Signaturpruefung scheitert: Kuendigungen und fehlgeschlagene
    # Zahlungen kaemen nie an, ohne dass irgendwo ein Fehler auftaucht.
    ohne_geheimnis = [v for _, v, _ in WEBHOOKS if v not in werte]
    if ohne_geheimnis:
        print()
        print("ACHTUNG: fuer diese Endpunkte gibt es kein frisches Geheimnis,")
        print("weil sie in Stripe schon bestanden:")
        for v in ohne_geheimnis:
            print(f"  {v}")
        print("Im Dashboard unter Developers > Webhooks > Endpunkt > 'Reveal'")
        print("nachlesen und von Hand eintragen. Bleibt der Testwert stehen,")
        print("scheitert jede Signaturpruefung stillschweigend.")

    if schreiben:
        return env_schreiben(werte)

    print()
    print("=== In /home/clawd/saas/legal/.env eintragen (vorher Kopie: cp .env .env.bak-$(date +%F)-vor-live) ===")
    print(f"STRIPE_SECRET_KEY={key}")
    print("STRIPE_PUBLISHABLE_KEY=pk_live_...   # aus dem Dashboard, wird vom Backend nicht benutzt, nur der Vollständigkeit halber")
    for z in env_zeilen:
        print(z)
    print("=== danach: cd /home/clawd/saas/legal && docker compose up -d backend  (Umgebungsvariablen greifen erst beim Neuanlegen des Containers) ===")
    print("=== dann: python3 scripts/stripe-live-umschalten.py pruefen ===")
    return 0


ENV_PFAD = "/home/clawd/saas/legal/.env"


def env_schreiben(werte: dict) -> int:
    """Traegt die Werte in die .env ein, mit Kopie vorher.

    Warum das Skript das selbst macht und nicht der Mensch per Copy-Paste:
    der Block enthaelt zwei Webhook-Geheimnisse und zwanzig Kennungen. Jede
    davon von Hand zu uebertragen ist genau die Gelegenheit, bei der eine
    Zeile verrutscht, und eine verrutschte Preis-Kennung bucht beim ersten
    Kunden den falschen Betrag. Ausserdem bleibt der Schluessel damit auf
    dem Server: er geht nicht durch eine Zwischenablage und nicht durch ein
    Chatfenster.

    Bestehende Zeilen werden ersetzt, unbekannte angehaengt, alles andere
    bleibt Zeichen fuer Zeichen stehen. Die alte Fassung liegt daneben.
    """
    from datetime import datetime
    if not os.path.exists(ENV_PFAD):
        print(f"{ENV_PFAD} gibt es nicht.")
        return 2

    with open(ENV_PFAD, encoding="utf-8") as fh:
        zeilen = fh.readlines()

    kopie = f"{ENV_PFAD}.bak-{datetime.now().strftime('%Y%m%d-%H%M')}-vor-live"
    with open(kopie, "w", encoding="utf-8") as fh:
        fh.writelines(zeilen)
    os.chmod(kopie, 0o600)

    offen = dict(werte)
    neu_zeilen = []
    ersetzt = []
    for zeile in zeilen:
        name = zeile.split("=", 1)[0].strip()
        if name in offen and not zeile.lstrip().startswith("#"):
            # Den alten Wert als Kommentar stehen lassen: der Rueckweg soll
            # in der Datei selbst ablesbar sein, nicht nur in der Kopie.
            neu_zeilen.append(f"# bis {datetime.now().strftime('%d.%m.%Y')} (Testmodus): {zeile.rstrip()}\n")
            neu_zeilen.append(f"{name}={offen.pop(name)}\n")
            ersetzt.append(name)
        else:
            neu_zeilen.append(zeile)

    if offen:
        neu_zeilen.append(f"\n# Ergaenzt am {datetime.now().strftime('%d.%m.%Y')} beim Umschalten auf Live-Preise.\n")
        for name, wert in offen.items():
            neu_zeilen.append(f"{name}={wert}\n")

    with open(ENV_PFAD, "w", encoding="utf-8") as fh:
        fh.writelines(neu_zeilen)
    os.chmod(ENV_PFAD, 0o600)

    print()
    print(f"In die .env geschrieben. Kopie der alten Fassung: {kopie}")
    print(f"  ersetzt ({len(ersetzt)}): " + ", ".join(sorted(ersetzt)))
    if offen:
        print(f"  ergaenzt ({len(offen)}): " + ", ".join(sorted(offen)))
    print()
    print("Naechster Schritt (baut das Image mit, der Code ist hineingebacken):")
    print("    cd /home/clawd/saas/legal && docker compose build backend && docker compose up -d backend")
    print("Danach:")
    print("    python3 scripts/stripe-live-umschalten.py pruefen")
    return 0


# ---------------------------------------------------------------------------
# pruefen
# ---------------------------------------------------------------------------

# Was die Oberflaeche dem Kunden als Preis anzeigt, je lookup_key. Quelle sind
# die beiden Kataloge im Backend, nicht eine zweite Liste von Hand: eine Liste,
# die man pflegen muss, laeuft irgendwann auseinander, und dann zeigt die
# Oberflaeche einen Preis und Stripe bucht einen anderen. Genau das war am
# 10.09.2026 der Fall (49 EUR gezeigt, 89 EUR gebucht).
BEWORBEN = {
    # lookup_key: (Datei, Schluessel im Katalog, Feldname)
    "complyo_comploai_guard":     ("backend/addon_payment_routes.py", "comploai_guard", "price_monthly"),
    "complyo_priority_support":   ("backend/addon_payment_routes.py", "priority_support", "price_monthly"),
    "complyo_agency_sites_extra": ("backend/addon_payment_routes.py", "agency_sites_extra", "price_monthly"),
    "complyo_expert_ai_audit":    ("backend/addon_payment_routes.py", "expert_ai_audit", "price"),
    "complyo_implementation":     ("backend/addon_payment_routes.py", "implementation_support", "price"),
    "complyo_custom_integration": ("backend/addon_payment_routes.py", "custom_integration", "price"),
    "complyo_pro_monthly":        ("backend/stripe_routes.py", '"id": "pro"', "price_monthly"),
    "complyo_pro_yearly":         ("backend/stripe_routes.py", '"id": "pro"', "price_yearly"),
    "complyo_agency_monthly":     ("backend/stripe_routes.py", '"id": "agency"', "price_monthly"),
    "complyo_agency_yearly":      ("backend/stripe_routes.py", '"id": "agency"', "price_yearly"),
    "complyo_monitor_monthly":    ("backend/stripe_routes.py", '"id": "monitor"', "price_monthly"),
    "complyo_monitor_yearly":     ("backend/stripe_routes.py", '"id": "monitor"', "price_yearly"),
}


def beworbene_betraege(wurzel: str) -> dict:
    """Liest die angezeigten Preise aus den Backend-Katalogen, in Cent."""
    import re as _re
    quellen = {}
    ergebnis = {}
    for lookup, (datei, schluessel, feld) in BEWORBEN.items():
        pfad = os.path.join(wurzel, datei)
        if pfad not in quellen:
            try:
                with open(pfad, encoding="utf-8") as fh:
                    quellen[pfad] = fh.read()
            except OSError:
                quellen[pfad] = ""
        text = quellen[pfad]
        if schluessel.startswith('"id"'):
            i = text.find(schluessel)
        else:
            i = text.find('"%s": {' % schluessel)
        if i < 0:
            continue
        m = _re.search(r'"%s": (\d+)' % feld, text[i:i + 1200])
        if m:
            ergebnis[lookup] = int(m.group(1)) * 100
    return ergebnis


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

    # Zeigt die Oberflaeche denselben Betrag, den Stripe bucht?
    wurzel = os.path.dirname(os.path.abspath(env_pfad))
    beworben = beworbene_betraege(wurzel)
    for lookup, produktname, betrag, intervall, variable in KATALOG:
        erwartet = beworben.get(lookup)
        if erwartet is not None and erwartet != betrag:
            befunde.append(
                f"{produktname} ({lookup}): die Oberflaeche zeigt "
                f"{erwartet / 100:.2f} EUR, angelegt sind {betrag / 100:.2f} EUR."
            )

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
        schreiben = "--schreiben" in argv
        key = os.getenv("STRIPE_LIVE_SECRET_KEY", "")
        if not key:
            # Abfrage ohne Anzeige, statt den Schluessel in die Befehlszeile zu
            # schreiben: dort landet er in der Shell-Historie und in der
            # Prozessliste, wo ihn jeder auf der Maschine lesen kann.
            import getpass
            try:
                key = getpass.getpass("Stripe Live-Geheimschluessel (sk_live_..., Eingabe bleibt unsichtbar): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAbgebrochen.")
                return 2
        if not key:
            print("Kein Schluessel eingegeben. Der Kontoinhaber findet ihn im"
                  " Stripe-Dashboard unter Developers > API keys (Live mode).")
            return 2
        try:
            return anlegen(key, schreiben=schreiben)
        except StripeFehler as e:
            print(f"Stripe-Fehler: {e}")
            return 1
    env_pfad = argv[2] if len(argv) > 2 else "/home/clawd/saas/legal/.env"
    return pruefen(env_pfad)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
