"""Auftragsablage für entkoppelte Scans.

Bis 03.09.2026 hielt jeder Scan seine HTTP-Verbindung offen, 16 bis 18 Sekunden
lang. Das hatte zwei Folgen, beide gemessen:

1. Der Speicher wuchs nicht nur mit den laufenden Browsern, sondern mit den
   WARTENDEN Anfragen. Bei einem Browser-Semaphor von 6 war das Backend schon
   bei 16 gleichzeitigen Anfragen am 2-GiB-Anschlag, obwohl nie mehr als sechs
   Browser liefen. Bei 22 lieferten vier Scans daraufhin 14 statt 13 Befunde —
   dasselbe Ziel, anderes Ergebnis, je nach Serverlast.
2. `proxy_read_timeout 120s` auf api.complyo.de ist eine harte Wand. Ein Scan,
   der in der Warteschlange steht, läuft irgendwann dagegen, während der Server
   ihn zu Ende rechnet und niemand das Ergebnis abholt.

Die Ablage trennt Annahme und Ausführung: der Auftrag bekommt eine Kennung, die
Verbindung schließt sofort, das Ergebnis wird abgeholt.

**Fail-open ist hier Pflicht, nicht Bequemlichkeit.** Fällt Redis aus, darf der
Scanner nicht stehen. `verfuegbar()` meldet das, und der Aufrufer nimmt den
alten synchronen Weg. Ein Scanner, der ohne Redis gar nicht mehr scannt, wäre
schlechter als der Zustand vorher.
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Ergebnisse müssen den Abholvorgang überleben, aber nicht den Tag. Eine Stunde
# reicht für jeden Ladebalken und hält die Ablage klein.
TTL_SEKUNDEN = 3600

# Auftrag hängt auf "laeuft" fest, wenn der Arbeiter stirbt. Wer länger als
# diese Spanne läuft, gilt als verloren — sonst wartet die Anzeige ewig.
LAUFZEIT_GRENZE_SEKUNDEN = 600

PRAEFIX = "scan:auftrag:"

# Welcher Scan hinter dem Auftrag steckt. Der Arbeiter entscheidet danach,
# welche Funktion er ruft — der oeffentliche Vorschau-Scan und der
# angemeldete Vollscan sind verschiedene Wege mit verschiedenen Budgets.
ART_PREVIEW = "preview"
ART_V2 = "v2"

WARTEND = "wartend"
LAEUFT = "laeuft"
FERTIG = "fertig"
FEHLGESCHLAGEN = "fehlgeschlagen"


def neue_kennung() -> str:
    """Kennung im Format, das scan_progress.token_gueltig() akzeptiert.

    Die Fortschrittsanzeige prüft gegen ^[A-Za-z0-9-]{8,64}$. Eine Kennung, die
    dort durchfällt, hätte zur Folge, dass der Auftrag zwar läuft, der Balken
    aber stumm bleibt.
    """
    return f"scan-{uuid.uuid4().hex}"


async def _redis():
    """Redis-Verbindung oder None. Wirft nie."""
    try:
        from dependencies import get_redis
        return await get_redis()
    except Exception as e:
        logger.warning(f"Auftragsablage: Redis nicht erreichbar ({e})")
        return None


async def verfuegbar() -> bool:
    """Kann entkoppelt gearbeitet werden? Wenn nein: synchroner Weg."""
    return await _redis() is not None


async def anlegen(
    url: str,
    kennung: Optional[str] = None,
    user_id: Optional[str] = None,
    art: str = ART_PREVIEW,
    zusatz: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Legt einen Auftrag im Zustand `wartend` an. None, wenn Redis fehlt.

    `user_id` bindet den Auftrag an ein Konto. Der oeffentliche Vorschau-Scan
    hat keinen Besitzer (None) — sein Ergebnis ist ohnehin oeffentlich. Der
    angemeldete Vollscan hat einen, und der Abholweg prueft ihn: die Kennung
    ist zwar 128 Bit lang und praktisch nicht zu raten, aber "praktisch nicht
    zu raten" ist keine Zugriffskontrolle.

    `zusatz` nimmt auf, was der Arbeiter spaeter braucht und im Auftrag stehen
    muss, weil er den Anfragekontext nicht mehr hat — beim v2-Scan etwa das
    Seitenbudget aus dem Tarif.
    """
    r = await _redis()
    if r is None:
        return None

    kennung = kennung or neue_kennung()
    auftrag = {
        "kennung": kennung,
        "url": url,
        "zustand": WARTEND,
        "art": art,
        "user_id": str(user_id) if user_id is not None else None,
        "erstellt": time.time(),
    }
    if zusatz:
        auftrag.update(zusatz)
    try:
        await r.set(PRAEFIX + kennung, json.dumps(auftrag), ex=TTL_SEKUNDEN)
    except Exception as e:
        logger.warning(f"Auftrag {kennung} nicht ablegbar: {e}")
        return None
    return kennung


async def hole(kennung: str) -> Optional[Dict[str, Any]]:
    """Auftrag lesen. None, wenn unbekannt, abgelaufen oder Redis weg.

    Ein Auftrag, der zu lange auf `laeuft` steht, wird beim Lesen als
    fehlgeschlagen gemeldet. Sonst wartet die Anzeige auf einen Arbeiter, den
    es nicht mehr gibt — etwa nach einem Neustart des Containers mitten im Scan.
    """
    r = await _redis()
    if r is None:
        return None
    try:
        roh = await r.get(PRAEFIX + kennung)
    except Exception as e:
        logger.warning(f"Auftrag {kennung} nicht lesbar: {e}")
        return None
    if not roh:
        return None

    try:
        auftrag = json.loads(roh)
    except Exception:
        logger.warning(f"Auftrag {kennung} unlesbar abgelegt")
        return None

    if auftrag.get("zustand") == LAEUFT:
        begonnen = auftrag.get("begonnen") or auftrag.get("erstellt") or 0
        if time.time() - begonnen > LAUFZEIT_GRENZE_SEKUNDEN:
            auftrag["zustand"] = FEHLGESCHLAGEN
            auftrag["fehler"] = (
                "Die Prüfung wurde abgebrochen — vermutlich wurde der Dienst "
                "während des Laufs neu gestartet."
            )
    return auftrag


async def _schreibe(kennung: str, aenderung: Dict[str, Any]) -> bool:
    """Bestehenden Auftrag ergänzen. Legt nichts an, was es nicht gibt."""
    r = await _redis()
    if r is None:
        return False
    try:
        roh = await r.get(PRAEFIX + kennung)
        if not roh:
            return False
        auftrag = json.loads(roh)
        auftrag.update(aenderung)
        await r.set(PRAEFIX + kennung, json.dumps(auftrag), ex=TTL_SEKUNDEN)
        return True
    except Exception as e:
        logger.warning(f"Auftrag {kennung} nicht schreibbar: {e}")
        return False


async def markiere_laufend(kennung: str) -> bool:
    return await _schreibe(kennung, {"zustand": LAEUFT, "begonnen": time.time()})


async def markiere_fertig(kennung: str, ergebnis: Dict[str, Any]) -> bool:
    return await _schreibe(kennung, {
        "zustand": FERTIG,
        "ergebnis": ergebnis,
        "beendet": time.time(),
    })


async def markiere_fehlgeschlagen(kennung: str, fehler: str) -> bool:
    return await _schreibe(kennung, {
        "zustand": FEHLGESCHLAGEN,
        "fehler": fehler,
        "beendet": time.time(),
    })


def gehoert_zu(auftrag: Dict[str, Any], user_id: Optional[str]) -> bool:
    """Darf dieses Konto den Auftrag sehen?

    Auftraege ohne Besitzer (der oeffentliche Vorschau-Scan) sind fuer jeden
    abholbar, der die Kennung hat — ihr Ergebnis ist eine oeffentliche
    Website-Bewertung. Auftraege MIT Besitzer gehoeren genau diesem Konto.
    """
    besitzer = auftrag.get("user_id")
    if besitzer is None:
        return True
    return besitzer == str(user_id) if user_id is not None else False


def ist_endzustand(zustand: Optional[str]) -> bool:
    """Muss der Abholer weiter fragen, oder ist er fertig?"""
    return zustand in (FERTIG, FEHLGESCHLAGEN)
