"""Hintergrundarbeiter für entkoppelte Scans.

Nimmt Aufträge aus einer prozessinternen Warteschlange, führt den Scan aus und
legt das Ergebnis in der Auftragsablage (scan_auftraege) ab.

**Warum die Warteschlange im Prozess liegt und nicht in Redis.** Der Zustand
der Aufträge liegt in Redis, die Reihenfolge nicht. Das ist bewusst der
kleinere erste Schritt: uvicorn läuft heute mit einem Arbeiter, also gibt es
genau einen Verbraucher. Zieht der Scan später in einen eigenen Container um,
wird nur der Transport getauscht — die Zustandsschicht bleibt, wie sie ist.
Eine Redis-Liste jetzt schon einzuziehen hieße, Abfrageschleifen und
Sichtbarkeitsfristen zu bauen, die heute niemand braucht.

**Was das kostet, steht hier ehrlich:** Aufträge in der Warteschlange
überleben keinen Neustart des Containers. Sie stehen dann für immer auf
`wartend`. Deshalb räumt `beende()` beim Herunterfahren auf, und
`scan_auftraege.hole()` erklärt zu lange laufende Aufträge von sich aus für
gescheitert. Ein Auftrag geht also verloren — aber er hängt nicht.
"""

import asyncio
import logging
import os
from typing import Optional, Set

from compliance_engine import scan_auftraege as sa

logger = logging.getLogger(__name__)

# Wie viele Aufträge gleichzeitig abgearbeitet werden.
#
# Der Browser-Semaphor (COMPLYO_BROWSER_PARALLEL, Vorgabe 6) begrenzt die
# Browser; dieser Wert begrenzt, wie viele Scans überhaupt gleichzeitig in
# Arbeit sind. Gemessen am 03.09.: bei sechs gleichzeitigen Scans lag die
# Speicherspitze bei 973 MiB von 2 GiB. Sechs Arbeiter passen also bequem,
# und der Rest wartet in der Schlange statt im Speicher.
ARBEITER_ANZAHL = max(1, int(os.getenv("COMPLYO_ARBEITER_ANZAHL", "6")))

# Obergrenze der Schlange. Ohne Deckel nimmt der Dienst unbegrenzt Aufträge an
# und verspricht Ergebnisse, die erst in einer halben Stunde kommen. Lieber
# früh und ehrlich ablehnen.
WARTESCHLANGE_MAX = max(1, int(os.getenv("COMPLYO_WARTESCHLANGE_MAX", "100")))

_warteschlange: Optional[asyncio.Queue] = None
_arbeiter: list = []
_in_arbeit: Set[str] = set()


def laeuft() -> bool:
    return bool(_arbeiter)


def wartend_anzahl() -> int:
    return _warteschlange.qsize() if _warteschlange else 0


async def einreihen(kennung: str, url: str) -> bool:
    """Auftrag in die Schlange stellen. False, wenn sie voll ist."""
    if _warteschlange is None:
        logger.warning("Arbeiter laeuft nicht — Auftrag nicht einreihbar")
        return False
    try:
        _warteschlange.put_nowait((kennung, url))
        return True
    except asyncio.QueueFull:
        logger.warning(f"Warteschlange voll ({WARTESCHLANGE_MAX}) — {kennung} abgelehnt")
        return False


async def _eine_runde(kennung: str, url: str) -> None:
    """Ein Auftrag von Anfang bis Ende. Wirft nie."""
    _in_arbeit.add(kennung)
    try:
        await sa.markiere_laufend(kennung)
        # Spaet importiert: public_routes zieht beim Import halb main_production
        # mit, ein Import auf Modulebene wuerde einen Ringschluss erzeugen.
        from public_routes import fuehre_preview_scan_aus

        ergebnis = await fuehre_preview_scan_aus(url)

        # fuehre_preview_scan_aus wirft nicht, sondern meldet Fehler im dict.
        # Ein Ergebnis mit success=False ist ein Fehlschlag, auch wenn technisch
        # nichts geworfen wurde — genau die Falle, die den Waechter blind machte.
        if isinstance(ergebnis, dict) and ergebnis.get("success") is True:
            await sa.markiere_fertig(kennung, ergebnis)
        else:
            grund = (ergebnis or {}).get("message") or "Die Prüfung ist fehlgeschlagen."
            await sa.markiere_fehlgeschlagen(kennung, grund)
    except asyncio.CancelledError:
        # Herunterfahren mitten im Scan: als gescheitert ablegen, nicht
        # stillschweigend auf `laeuft` stehen lassen.
        await sa.markiere_fehlgeschlagen(
            kennung, "Der Dienst wurde während der Prüfung neu gestartet."
        )
        raise
    except Exception as e:
        logger.error(f"Auftrag {kennung} gescheitert: {e}", exc_info=True)
        await sa.markiere_fehlgeschlagen(kennung, "Bei der Prüfung ist ein Fehler aufgetreten.")
    finally:
        _in_arbeit.discard(kennung)


async def _schleife(nummer: int) -> None:
    logger.info(f"Scan-Arbeiter {nummer} bereit")
    while True:
        kennung, url = await _warteschlange.get()
        try:
            await _eine_runde(kennung, url)
        finally:
            _warteschlange.task_done()


async def starte() -> None:
    """Warteschlange und Arbeiter hochfahren. Mehrfacher Aufruf ist harmlos."""
    global _warteschlange
    if _arbeiter:
        return
    _warteschlange = asyncio.Queue(maxsize=WARTESCHLANGE_MAX)
    for i in range(ARBEITER_ANZAHL):
        _arbeiter.append(asyncio.create_task(_schleife(i + 1)))
    logger.info(f"{ARBEITER_ANZAHL} Scan-Arbeiter gestartet, Schlange max {WARTESCHLANGE_MAX}")


async def beende() -> None:
    """Arbeiter anhalten und offene Auftraege ehrlich als gescheitert ablegen.

    Ohne das bleiben Auftraege nach einem Neustart fuer immer auf `wartend`
    oder `laeuft` stehen, und die Anzeige beim Kunden dreht sich endlos.
    """
    global _warteschlange
    for t in _arbeiter:
        t.cancel()
    if _arbeiter:
        await asyncio.gather(*_arbeiter, return_exceptions=True)
    _arbeiter.clear()

    # Was noch in der Schlange lag, hat nie begonnen.
    offen = []
    while _warteschlange and not _warteschlange.empty():
        try:
            kennung, _ = _warteschlange.get_nowait()
            offen.append(kennung)
        except asyncio.QueueEmpty:
            break
    for kennung in offen:
        await sa.markiere_fehlgeschlagen(
            kennung, "Der Dienst wurde neu gestartet, bevor die Prüfung begann."
        )
    if offen:
        logger.info(f"{len(offen)} wartende Auftraege als gescheitert abgelegt")

    _warteschlange = None
