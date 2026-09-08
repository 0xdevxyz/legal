"""KI-Kosten-Budget: harte Obergrenze pro User/Monat, dazu ein globaler
Notausschalter fuer den ganzen (geteilten) OpenRouter-Account.

Ausgeloest durch den Vorfall vom 04.09.2026: der Umbau auf die entkoppelte
Scan-Pipeline hat an einem Tag den gesamten Account leergefahren, weil jede
einzelne Feld-Pruefung (hybrid_validator) und jedes Bild
(ai_alt_text_generator) einen eigenen, ungebremsten KI-Call ausgeloest hat —
ohne jede Obergrenze. Diese Bremse ist die Voraussetzung dafuer, dass echte
User auf das System koennen, ohne dass ein einzelner Scan oder ein Bug das
Guthaben sprengt.

Zwei Ebenen, weil User-Zuordnung nicht ueberall im Aufrufpfad vorliegt
(z.B. der oeffentliche Vorschau-Scan hat keinen User):
- GLOBAL_TAGES_LIMIT_EUR: haerter Deckel fuer den ganzen Account, gilt immer.
- Budget pro User/Monat: die eigentlichen Zielwerte (2 EUR Einzelplan,
  20 EUR Agentur), gilt ueberall dort, wo eine user_id bekannt ist.

Fail-closed bei Budget, fail-open bei Redis-Ausfall waere falsch herum: wenn
Redis weg ist, kann kein Verbrauch gezaehlt werden - dann lieber KEINE KI
zulassen (Pattern-/Heuristik-Fallback existiert an jeder Aufrufstelle) als
blind weiterzuzahlen. Redis-Ausfall blockiert also KI, nicht den Scan selbst.
"""

import contextvars
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Zielwerte aus der Tarif-Kalkulation: max 2 EUR/Monat fuer Einzelplaene,
# max 20 EUR/Monat fuer Agenturen. plan_type-Werte wie in der users-Tabelle.
BUDGET_EUR_JE_PLAN = {
    "free": 2.0,
    "single": 2.0,
    "pro": 2.0,
    "monitor": 2.0,
    "agency": 20.0,
    "expert": 20.0,
}
STANDARD_BUDGET_EUR = 2.0

# Oeffentliche Vorschau-Scans haben keinen User (scan_auftraege: user_id ist
# dort None). Eigener, kleiner Tagestopf, damit anonyme Besucher nicht das
# Gesamtbudget auffressen koennen.
VORSCHAU_BUDGET_EUR_TAG = float(os.getenv("COMPLYO_AI_VORSCHAU_BUDGET_TAG", "1.0"))

# Systemarbeit ohne Kunden — Rechtsnews einordnen, Hintergrundpflege. Eigener
# Topf, damit sie nicht den Vorschau-Topf leert, der oeffentlichen Scans
# gehoert, und damit ein Amoklauf im Hintergrund nicht als Kundenverbrauch
# durchgeht. Als Konto-Kennung wird die Konstante SYSTEM uebergeben.
SYSTEM = "__system__"
SYSTEM_BUDGET_EUR_TAG = float(os.getenv("COMPLYO_AI_SYSTEM_BUDGET_TAG", "2.0"))

# Account-weiter Notausschalter, unabhaengig von einzelner User-Zuordnung.
# Startwert bewusst knapp gewaehlt (aktueller echter Verbrauch lag bei ca.
# 0,15 EUR/Tag) - lieber zu oft auf Heuristik zurueckfallen als das Konto
# nochmal leerfahren. Hochsetzen, sobald echte Nutzerzahlen das tragen.
GLOBAL_TAGES_LIMIT_EUR = float(os.getenv("COMPLYO_AI_GLOBAL_TAGES_LIMIT_EUR", "5.0"))

USD_EUR_KURS = float(os.getenv("COMPLYO_USD_EUR_KURS", "0.92"))

# USD je Token, aus der OpenRouter-Preisliste (Stand 06.09.2026 abgefragt).
# Bei neuem Modell hier ergaenzen - unbekannte Modelle werden mit dem
# teuersten bekannten Satz gerechnet, lieber Budget zu frueh dicht als eine
# Rechnung ohne Deckel.
PREISE_USD_JE_TOKEN = {
    "anthropic/claude-haiku-4.5": {"prompt": 0.000001, "completion": 0.000005},
    "anthropic/claude-3.7-sonnet:beta": {"prompt": 0.000003, "completion": 0.000015},
    "anthropic/claude-3.5-sonnet": {"prompt": 0.000003, "completion": 0.000015},
    "anthropic/claude-sonnet-4.5": {"prompt": 0.000003, "completion": 0.000015},
    "anthropic/claude-sonnet-4-20250514": {"prompt": 0.000003, "completion": 0.000015},
    # aus ai_fix_engine/unified_fix_engine.py uebernommen (dort eigene Buchhaltung,
    # hier nur fuer den Fall, dass unified_fix_engine spaeter auch ueber dieses
    # Budget laufen soll).
    "moonshotai/kimi-k2.5": {"prompt": 0.0000006, "completion": 0.0000025},
}
_TEUERSTER_BEKANNTER_SATZ = {"prompt": 0.000003, "completion": 0.000015}

# Wer den laufenden Scan bezahlt. Wird einmal am Anfang eines Scans gesetzt,
# damit die Kosten beim richtigen Konto landen, ohne dass user_id durch
# scanner -> checks -> hybrid_validator durchgereicht werden muss. Ein Scan
# ohne gesetztes Konto (oeffentliche Vorschau) faellt auf den Anonym-Topf
# zurueck — das ist gewollt, nicht der Fehlerfall.
_konto: contextvars.ContextVar[Tuple[Optional[str], str]] = contextvars.ContextVar(
    "ki_budget_konto", default=(None, "free")
)


class konto_setzen:
    """Kontext, in dem KI-Kosten einem Konto zugerechnet werden.

    Als Kontextmanager und nicht als schlichtes set(), weil die Scan-Arbeiter
    langlebige Tasks sind, die einen Auftrag nach dem anderen abarbeiten: ohne
    reset() wuerde das Konto des vorigen Auftrags am naechsten kleben.
    """

    def __init__(self, user_id, plan_type: str = "free"):
        self._wert = (
            str(user_id) if user_id is not None else None,
            (plan_type or "free"),
        )
        self._token = None

    def __enter__(self):
        self._token = _konto.set(self._wert)
        return self

    def __exit__(self, *_):
        if self._token is not None:
            _konto.reset(self._token)
        return False


def _konto_aufloesen(user_id, plan_type: str) -> Tuple[Optional[str], str]:
    """Ausdruecklich uebergebenes Konto schlaegt den Kontext, Kontext schlaegt nichts."""
    if user_id is not None:
        return str(user_id), (plan_type or "free")
    kontext_user, kontext_plan = _konto.get()
    if kontext_user is not None:
        return kontext_user, kontext_plan
    return None, (plan_type or "free")


PRAEFIX = "ki:kosten:"
_TTL_TAGE_SEKUNDEN = 3 * 86400
_TTL_MONAT_SEKUNDEN = 35 * 86400

# Schaetzwert fuer die Vor-Pruefung, bevor die echten Token bekannt sind
# (ein Haiku-Call liegt real bei ~0,0015 EUR; grosszuegig aufgerundet, damit
# die Vorabpruefung nie knapper ist als die spaetere echte Buchung).
GESCHAETZTE_KOSTEN_EINZELCALL_EUR = 0.01


async def _redis():
    try:
        from dependencies import get_redis
        return await get_redis()
    except Exception as e:
        logger.warning(f"KI-Budget: Redis nicht erreichbar ({e})")
        return None


def kosten_eur(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Rechnet echten Token-Verbrauch einer Antwort in EUR um."""
    satz = PREISE_USD_JE_TOKEN.get(model, _TEUERSTER_BEKANNTER_SATZ)
    usd = prompt_tokens * satz["prompt"] + completion_tokens * satz["completion"]
    return usd * USD_EUR_KURS


def _monat_schluessel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _tag_schluessel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def budget_frei(
    user_id: Optional[str],
    plan_type: str = "free",
    voraussichtliche_kosten_eur: float = GESCHAETZTE_KOSTEN_EINZELCALL_EUR,
) -> bool:
    """Darf JETZT noch ein KI-Call gemacht werden?

    Prueft immer zuerst den globalen Tages-Deckel (Notausschalter fuer den
    ganzen Account), danach das Budget des einzelnen Users fuer den Monat
    (oder den Vorschau-Tagestopf bei anonymem Scan). Kein Redis erreichbar
    -> kein KI-Call, siehe Modul-Docstring.
    """
    user_id, plan_type = _konto_aufloesen(user_id, plan_type)

    r = await _redis()
    if r is None:
        return False

    try:
        global_key = f"{PRAEFIX}global:{_tag_schluessel()}"
        global_verbraucht = float(await r.get(global_key) or 0.0)
        if global_verbraucht + voraussichtliche_kosten_eur > GLOBAL_TAGES_LIMIT_EUR:
            logger.warning(
                "KI-Budget: globaler Tages-Deckel erreicht "
                f"({global_verbraucht:.2f}/{GLOBAL_TAGES_LIMIT_EUR:.2f} EUR) - KI blockiert"
            )
            return False

        if user_id == SYSTEM:
            system_key = f"{PRAEFIX}system:{_tag_schluessel()}"
            verbraucht = float(await r.get(system_key) or 0.0)
            if verbraucht + voraussichtliche_kosten_eur > SYSTEM_BUDGET_EUR_TAG:
                logger.warning(
                    "KI-Budget: Systemtopf erschoepft "
                    f"({verbraucht:.2f}/{SYSTEM_BUDGET_EUR_TAG:.2f} EUR) - KI blockiert"
                )
                return False
            return True

        if user_id is None:
            vorschau_key = f"{PRAEFIX}vorschau:{_tag_schluessel()}"
            verbraucht = float(await r.get(vorschau_key) or 0.0)
            return verbraucht + voraussichtliche_kosten_eur <= VORSCHAU_BUDGET_EUR_TAG

        budget = BUDGET_EUR_JE_PLAN.get((plan_type or "free").lower(), STANDARD_BUDGET_EUR)
        user_key = f"{PRAEFIX}user:{user_id}:{_monat_schluessel()}"
        verbraucht = float(await r.get(user_key) or 0.0)
        return verbraucht + voraussichtliche_kosten_eur <= budget
    except Exception as e:
        logger.warning(f"KI-Budget: Pruefung fehlgeschlagen, KI wird sicherheitshalber blockiert ({e})")
        return False


async def kosten_buchen(user_id: Optional[str], kosten_eur_wert: float) -> None:
    """Bucht tatsaechliche Kosten nach einem erfolgreichen KI-Call. Wirft nie."""
    if kosten_eur_wert <= 0:
        return
    user_id, _ = _konto_aufloesen(user_id, "free")
    r = await _redis()
    if r is None:
        return
    try:
        pipe = r.pipeline()
        global_key = f"{PRAEFIX}global:{_tag_schluessel()}"
        pipe.incrbyfloat(global_key, kosten_eur_wert)
        pipe.expire(global_key, _TTL_TAGE_SEKUNDEN)
        if user_id == SYSTEM:
            system_key = f"{PRAEFIX}system:{_tag_schluessel()}"
            pipe.incrbyfloat(system_key, kosten_eur_wert)
            pipe.expire(system_key, _TTL_TAGE_SEKUNDEN)
        elif user_id is None:
            vorschau_key = f"{PRAEFIX}vorschau:{_tag_schluessel()}"
            pipe.incrbyfloat(vorschau_key, kosten_eur_wert)
            pipe.expire(vorschau_key, _TTL_TAGE_SEKUNDEN)
        else:
            user_key = f"{PRAEFIX}user:{user_id}:{_monat_schluessel()}"
            pipe.incrbyfloat(user_key, kosten_eur_wert)
            pipe.expire(user_key, _TTL_MONAT_SEKUNDEN)
        await pipe.execute()
    except Exception as e:
        logger.warning(f"KI-Budget: Buchung fehlgeschlagen ({e})")


async def verbrauch_user_monat(user_id: str) -> float:
    """Fuer Anzeige/Audit: bisheriger KI-Verbrauch des Users diesen Monat in EUR."""
    r = await _redis()
    if r is None:
        return 0.0
    try:
        user_key = f"{PRAEFIX}user:{user_id}:{_monat_schluessel()}"
        return float(await r.get(user_key) or 0.0)
    except Exception:
        return 0.0


async def verbrauch_global_heute() -> float:
    """Fuer Anzeige/Audit: bisheriger Gesamt-Verbrauch des Accounts heute in EUR."""
    r = await _redis()
    if r is None:
        return 0.0
    try:
        global_key = f"{PRAEFIX}global:{_tag_schluessel()}"
        return float(await r.get(global_key) or 0.0)
    except Exception:
        return 0.0
