# -*- coding: utf-8 -*-
"""Eine Kuendigung muss alles zurueckgeben, was der Kauf gegeben hat.

Am 15.09.2026 mit signierten Ereignissen gegen den laufenden Dienst gemessen,
einen Tag nach dem Live-Schalten. Zwei Haelften desselben Fehlers:

  * Hauptkaufweg: die Kuendigung setzte `user_limits.plan_type` auf free,
    liess die vier Saeulen in `user_modules` aber auf 'active'. Der Zugang
    wird aus beiden abgeleitet (`_module_zugang`), also behielt ein
    gekuendigtes Konto den vollen Funktionsumfang.
  * Add-ons: der Kauf erhoeht `websites_max` additiv, die Kuendigung nahm die
    Plaetze nicht zurueck. Ein Monat Extra-Sites-Paket, 25 Plaetze fuer immer.

Beide Male faellt nichts auf: kein Fehler, kein Log, nur ein Kunde, der
weiterbenutzt, wofuer er nicht mehr zahlt.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _block(datei, funktion):
    with open(os.path.join(BACKEND, datei), encoding="utf-8") as fh:
        text = fh.read()
    i = text.index(f"async def {funktion}")
    m = re.search(r"\nasync def ", text[i + 10:])
    return text[i:i + 10 + m.start()] if m else text[i:]


def test_kuendigung_schaltet_die_saeulen_ab():
    block = _block("stripe_routes.py", "handle_subscription_deleted")
    assert "user_modules" in block, (
        "Die Kuendigung fasst user_modules nicht an: das Konto behaelt alle "
        "Saeulen, obwohl der Tarif auf free steht.")
    assert "'cancelled'" in block or '"cancelled"' in block
    assert "stripe_subscription_id = $2" in block, (
        "Die Kuendigung muss auf DIESE Subscription eingegrenzt sein, sonst "
        "verliert ein Konto auch daneben gebuchte Einzelsaeulen.")


def test_kuendigung_gibt_das_website_kontingent_zurueck():
    block = _block("addon_payment_routes.py", "handle_addon_subscription_cancelled")
    assert "websites_max" in block, (
        "Die Add-on-Kuendigung nimmt die zusaetzlichen Plaetze nicht zurueck.")
    assert "extra_sites" in block
    assert "GREATEST" in block, "Ohne Untergrenze kann das Kontingent negativ werden"


def test_kuendigung_wirkt_nur_einmal():
    """Stripe stellt Ereignisse mehrfach zu. Zweimal abziehen waere schlimmer
    als gar nicht: der Kunde verlaere Plaetze, fuer die er zahlt."""
    block = _block("addon_payment_routes.py", "handle_addon_subscription_cancelled")
    assert "status = 'active'" in block, (
        "Die Kuendigung grenzt nicht auf die aktive Zeile ein; eine zweite "
        "Zustellung zieht das Kontingent noch einmal ab.")
