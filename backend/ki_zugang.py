"""Die eine Stelle, an der complyo ein Sprachmodell ruft.

Vorher gab es vierzehn. Acht davon hingen an keinem Budget: der
Tagesdeckel aus `compliance_engine.ai_budget` konnte gar nicht greifen, weil
diese Aufrufe ihn nie fragten. Gemessen am 15.09.2026 liefen so rund 30 % des
Tagesverbrauchs an jeder Kontrolle vorbei (Redis buchte 0,130 EUR, OpenRouter
berechnete 0,180 EUR). Das ist dieselbe Form wie der Vorfall vom 04.09.2026,
bei dem das Guthaben des geteilten Kontos an einem Tag aufgebraucht war.

Ein Deckel, den eine Aufrufstelle umgehen kann, ist kein Deckel. Deshalb nicht
"an jeder Stelle daran denken", sondern eine Engstelle, an der das Denken
einmal passiert:

  * vor dem Aufruf `ai_budget.budget_frei`, sonst `BudgetErschoepft`,
  * nach dem Aufruf `ai_budget.kosten_buchen` aus der echten `usage`-Antwort
    des Anbieters, nicht aus einer Schaetzung,
  * `X-Title` immer gesetzt, damit in der Abrechnung des Anbieters kein
    Aufruf mehr als "Unknown" steht und sich jeder Posten einem Zweck
    zuordnen laesst.

Wer das Konto setzt, entscheidet `ai_budget.konto_setzen` weiter ueber einen
ContextVar. Diese Datei reicht `user_id` nur durch, wenn eine Aufrufstelle es
ausdruecklich besser weiss.

Neue Aufrufstellen: hierdurch. `backend/tests/test_ki_engstelle.py` laesst
keine zweite Stelle zu, die sich ihren eigenen Zugang zum Anbieter baut.
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp

from compliance_engine import ai_budget

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"

# Prometheus-Zaehler, fail-open ohne metrics-Modul (wie an den bisherigen
# Aufrufstellen, damit die vorhandenen Dashboards weiterzaehlen).
try:
    from metrics import openrouter_requests_total as _openrouter_counter
except Exception:  # pragma: no cover - metrics ist optional
    _openrouter_counter = None


class BudgetErschoepft(RuntimeError):
    """Das Budget laesst diesen Aufruf nicht zu.

    Eigene Klasse und nicht einfach `None`: an fast jeder Aufrufstelle gibt es
    einen Heuristik-Rueckfall, der greifen soll. Der Unterschied zwischen "die
    KI hat nichts geliefert" und "wir haben bewusst nicht gefragt" gehoert aber
    ins Log, sonst sieht ein erschoepftes Budget aus wie ein Anbieterausfall.
    """


@dataclass
class KIAntwort:
    erfolg: bool
    inhalt: Optional[str] = None
    modell: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    kosten_eur: float = 0.0
    fehler: Optional[str] = None
    dauer_ms: int = 0
    rohdaten: Dict[str, Any] = field(default_factory=dict)

    @property
    def tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def _schluessel() -> Optional[str]:
    return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")


def _kopfzeilen(zweck: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_schluessel()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://complyo.de",
        # Steht in der Abrechnung des Anbieters als "App". Ohne ihn heisst der
        # Posten dort "Unknown" und laesst sich keinem Zweck zuordnen.
        "X-Title": f"Complyo {zweck}",
    }


async def chat(
    *,
    model: str,
    messages: List[Dict[str, str]],
    zweck: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    timeout: int = 30,
    versuche: int = 1,
    zusatz: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    plan_type: str = "free",
    geschaetzte_kosten_eur: Optional[float] = None,
) -> KIAntwort:
    """Ein Modellaufruf, gedeckelt und gebucht.

    Wirft `BudgetErschoepft`, wenn das Budget den Aufruf nicht zulaesst. Alle
    anderen Fehler kommen als `KIAntwort(erfolg=False, fehler=...)` zurueck,
    damit die Rueckfaelle der Aufrufstellen wie bisher greifen.
    """
    if not _schluessel():
        return KIAntwort(erfolg=False, modell=model,
                         fehler="OPENROUTER_API_KEY nicht konfiguriert")

    geschaetzt = (
        geschaetzte_kosten_eur
        if geschaetzte_kosten_eur is not None
        else ai_budget.GESCHAETZTE_KOSTEN_EINZELCALL_EUR
    )
    if not await ai_budget.budget_frei(user_id, plan_type, geschaetzt):
        raise BudgetErschoepft(
            f"KI-Budget laesst '{zweck}' nicht zu (Modell {model})"
        )

    rumpf: Dict[str, Any] = {"model": model, "messages": messages}
    if max_tokens is not None:
        rumpf["max_tokens"] = max_tokens
    if temperature is not None:
        rumpf["temperature"] = temperature
    if zusatz:
        rumpf.update(zusatz)

    begonnen = time.time()
    letzter_fehler = "unbekannt"

    for versuch in range(max(1, versuche)):
        try:
            async with aiohttp.ClientSession() as sitzung:
                async with sitzung.post(
                    OPENROUTER_URL,
                    headers=_kopfzeilen(zweck),
                    json=rumpf,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as antwort:
                    dauer = int((time.time() - begonnen) * 1000)

                    if antwort.status == 200:
                        daten = await antwort.json()
                        usage = daten.get("usage") or {}
                        pt = int(usage.get("prompt_tokens", 0) or 0)
                        ct = int(usage.get("completion_tokens", 0) or 0)
                        kosten = ai_budget.kosten_eur(model, pt, ct)
                        await ai_budget.kosten_buchen(user_id, kosten)
                        if _openrouter_counter:
                            _openrouter_counter.labels(status="success").inc()
                        try:
                            inhalt = daten["choices"][0]["message"]["content"]
                        except (KeyError, IndexError, TypeError):
                            inhalt = None
                        return KIAntwort(
                            erfolg=inhalt is not None,
                            inhalt=inhalt,
                            modell=model,
                            prompt_tokens=pt,
                            completion_tokens=ct,
                            kosten_eur=kosten,
                            fehler=None if inhalt is not None else "Antwort ohne Inhalt",
                            dauer_ms=dauer,
                            rohdaten=daten,
                        )

                    if antwort.status == 429 and versuch + 1 < versuche:
                        # Kein Budgetverbrauch, nichts gebucht. Warten und noch
                        # einmal, wie die Fix-Engine es vorher selbst tat.
                        letzter_fehler = "Rate limit erreicht"
                        await asyncio.sleep(2 ** versuch)
                        continue

                    letzter_fehler = f"HTTP {antwort.status}"
                    try:
                        letzter_fehler += f": {(await antwort.text())[:200]}"
                    except Exception:
                        pass
                    break

        except Exception as e:
            letzter_fehler = f"{type(e).__name__}: {e}"
            if versuch + 1 < versuche:
                await asyncio.sleep(2 ** versuch)
                continue
            break

    if _openrouter_counter:
        _openrouter_counter.labels(status="error").inc()
    logger.warning(f"KI-Aufruf '{zweck}' ({model}) fehlgeschlagen: {letzter_fehler}")
    return KIAntwort(
        erfolg=False,
        modell=model,
        fehler=letzter_fehler,
        dauer_ms=int((time.time() - begonnen) * 1000),
    )


async def einbettung(
    *,
    model: str,
    eingabe: str,
    zweck: str,
    timeout: int = 20,
    user_id: Optional[str] = None,
    plan_type: str = "free",
) -> Optional[List[float]]:
    """Einbettungsvektor, ebenfalls gedeckelt und gebucht.

    Kostet je Aufruf fast nichts (drei Token), haengt aber aus demselben Grund
    am Budget wie alles andere: eine Aufrufstelle, die den Deckel nicht fragt,
    ist eine Aufrufstelle, die ihn spaeter sprengen kann. Gibt `None` zurueck,
    wenn nichts zu holen war - der Aufrufer faellt dann auf Stichwortsuche
    zurueck.
    """
    if not _schluessel():
        return None

    if not await ai_budget.budget_frei(user_id, plan_type, 0.0001):
        raise BudgetErschoepft(f"KI-Budget laesst '{zweck}' nicht zu")

    try:
        async with aiohttp.ClientSession() as sitzung:
            async with sitzung.post(
                EMBEDDING_URL,
                headers=_kopfzeilen(zweck),
                json={"model": model, "input": eingabe},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as antwort:
                if antwort.status != 200:
                    logger.warning(
                        f"Einbettung '{zweck}' ({model}): HTTP {antwort.status}"
                    )
                    return None
                daten = await antwort.json()
                usage = daten.get("usage") or {}
                kosten = ai_budget.kosten_eur(
                    model,
                    int(usage.get("prompt_tokens", 0) or 0),
                    int(usage.get("completion_tokens", 0) or 0),
                )
                await ai_budget.kosten_buchen(user_id, kosten)
                return daten["data"][0]["embedding"]
    except BudgetErschoepft:
        raise
    except Exception as e:
        logger.warning(f"Einbettung '{zweck}' ({model}) fehlgeschlagen: {e}")
        return None
