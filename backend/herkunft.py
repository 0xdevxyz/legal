# -*- coding: utf-8 -*-
"""Herkunft (utm) von Registrierung und Kauf in die Datenbank schreiben.

Anlass (07.10.2026): Die Entscheidungsregel nach Woche 45 zaehlt Kaeufe je
Kanal. Die utm-Werte reisten bis in die Stripe-Metadaten (PR #10), blieben
dort aber liegen: der Webhook schrieb sie nicht in die Datenbank, und die
Registrierung schrieb sie nirgends hin. Eine Auswertung ohne Stripe-Zugriff
war damit unmoeglich, und ein kostenloses Konto liess sich keinem Kanal
zuordnen.

Zwei Schreibstellen, beide best effort:

* `registrierung_festhalten`: nach dem Anlegen eines Kontos, nur wenn eine
  Herkunft mitkam.
* `kauf_festhalten`: nach der Freischaltung eines Abos (Webhook und
  verify-checkout), idempotent ueber die Abo-Kennung.

Best effort mit Absicht, wie `protokolliere_vertragsannahme`: schlaegt der
Schreibvorgang fehl, etwa weil Migration 0037 noch nicht gelaufen ist, darf
das weder die Registrierung noch die Freischaltung eines bezahlten Plans
abbrechen. Eine fehlende Zuordnung ist ein Mangel in der Statistik, eine
nicht freigeschaltete Zahlung ein Ausfall.

Die Werte stammen aus der Adresszeile eines Fremden. Deshalb Positivliste der
Schluessel und ein enges Zeichenmuster (dasselbe wie im Dashboard und beim
Checkout), alles andere faellt still weg.
"""
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SCHLUESSEL = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")

# fullmatch statt match mit $: in Python laesst `$` ein Zeilenende am Ende
# durch ("linkedin\n"), das Gegenstueck in TypeScript nicht.
_MUSTER = re.compile(r"[A-Za-z0-9_.:-]{1,120}")
_PLAN_MUSTER = re.compile(r"[a-z0-9_]{1,20}")


def bereinige(roh: Any) -> Dict[str, str]:
    """Nur die fuenf utm-Schluessel, nur harmlose Zeichen, sonst nichts.

    Gibt immer ein Dict zurueck. Aus `roh` wird nie etwas anderes gelesen als
    die Positivliste, insbesondere nie `user_id` oder `plan`, auf denen die
    Freischaltung haengt.
    """
    # Stripe-Objekte sind dict-Unterklassen, in Tests reicht ein dict; alles
    # ohne .get (None, Text, Liste) ergibt nichts.
    if isinstance(roh, (str, bytes, list, tuple)) or not hasattr(roh, "get"):
        return {}
    ergebnis: Dict[str, str] = {}
    for schluessel in SCHLUESSEL:
        wert = roh.get(schluessel)
        if isinstance(wert, str) and _MUSTER.fullmatch(wert):
            ergebnis[schluessel] = wert
    return ergebnis


async def registrierung_festhalten(pool, user_id: Any, herkunft: Any) -> bool:
    """Haelt die Herkunft eines neuen Kontos fest. True, wenn geschrieben.

    Ohne (gueltige) Herkunft passiert nichts: ein Konto ohne Eintrag zaehlt
    in der Auswertung als "ohne Herkunft", eine Zeile mit lauter NULL waere
    dasselbe in mehr Speicher.
    """
    h = bereinige(herkunft)
    if not h:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO registrierung_herkunft
                    (user_id, utm_source, utm_medium, utm_campaign, utm_content, utm_term)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) DO NOTHING
                """,
                int(user_id),
                h.get("utm_source"), h.get("utm_medium"), h.get("utm_campaign"),
                h.get("utm_content"), h.get("utm_term"),
            )
        return True
    except Exception as exc:
        logger.warning("Herkunft der Registrierung von Konto %s nicht festgehalten: %s",
                       user_id, exc)
        return False


async def kauf_festhalten(conn, user_id: Any, subscription_id: Optional[str],
                          plan: Optional[str], metadata: Any) -> bool:
    """Haelt Tarif und Herkunft eines Kaufs fest. True, wenn die Zeile geschrieben wurde.

    Wird nach JEDER Freischaltung aufgerufen, auch wenn `_apply_plan_activation`
    False meldet: `customer.subscription.created` legt die Zeile in
    `subscriptions` unter Umstaenden schon vor `checkout.session.completed` an,
    und der Kauf waere sonst nie eingetragen worden. Idempotent: die Abo-Kennung
    ist der Primaerschluessel, eine Wiederholung aendert nichts.

    Auch ohne utm-Werte wird eine Zeile geschrieben, damit der Tarif aus den
    Checkout-Metadaten erhalten bleibt (`subscriptions.plan_type` steht nach
    `customer.subscription.created` fest auf 'pro').
    """
    if not subscription_id:
        return False
    h = bereinige(metadata)
    plan_text = plan if isinstance(plan, str) and _PLAN_MUSTER.fullmatch(plan) else None
    try:
        await conn.execute(
            """
            INSERT INTO kauf_herkunft
                (stripe_subscription_id, user_id, plan,
                 utm_source, utm_medium, utm_campaign, utm_content, utm_term)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (stripe_subscription_id) DO NOTHING
            """,
            str(subscription_id), int(user_id), plan_text,
            h.get("utm_source"), h.get("utm_medium"), h.get("utm_campaign"),
            h.get("utm_content"), h.get("utm_term"),
        )
        return True
    except Exception as exc:
        logger.warning("Herkunft des Kaufs %s (Konto %s) nicht festgehalten: %s",
                       subscription_id, user_id, exc)
        return False
