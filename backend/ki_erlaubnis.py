"""Darf fuer dieses Konto ein Sprachmodell aufgerufen werden?

Anlass (25.09.2026): Die veroeffentlichte Datenschutzerklaerung sagt zu, die
KI-gestuetzten Funktionen liessen sich ungenutzt lassen. Gemessen war das
nicht so: die Alternativtexte gehen nach jedem Scan an Claude Vision, und
gefragt wurde vorher nur das Tagesbudget.

Diese Stelle beantwortet die Frage, und sie ist absichtlich klein: eine
Abfrage, ein Zwischenspeicher, zwei Fehlerfaelle. Die Regel, welche Aufrufe
sie passieren muessen, steht nicht hier, sondern im Waechtertest
tests/test_ki_erlaubnis.py. So kann sie nicht dadurch verschwinden, dass
jemand eine neue KI-Funktion daneben baut.

Fehlt die Erlaubnis oder ist sie nicht lesbar, gilt: NICHT erlaubt.

Das ist die andere Richtung als beim Tagesbudget, wo ein Ausfall die Pruefung
nicht anhalten soll, und sie ist hier richtig: ein Budgetfehler kostet Geld,
ein Erlaubnisfehler uebermittelt Kundendaten in ein Drittland. Die
Vorbelegung in der Datenbank steht auf 'true', ein Konto ohne Widerspruch
wird also nicht ausgebremst. Nur wenn ueberhaupt keine Antwort zu bekommen
ist, ueberwiegt das Nichtsenden.
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Kurzer Zwischenspeicher. Ein Scan ueber viele Unterseiten fragt sonst
# dieselbe Zeile dutzendfach ab; 60 Sekunden sind kurz genug, dass ein
# Widerspruch beim naechsten Scan wirkt, und lang genug, dass ein Scan nicht
# an der Datenbank haengt.
_ZWISCHENSPEICHER: "dict[str, tuple[float, bool]]" = {}
HALTBARKEIT_SEKUNDEN = 60


def vergessen(user_id=None) -> None:
    """Zwischenspeicher leeren, nachdem die Erlaubnis geaendert wurde.

    Ohne das wuerde ein Widerspruch bis zu einer Minute lang nicht wirken, und
    genau in dieser Minute wuerde der Kunde die Wirkung pruefen wollen.
    """
    if user_id is None:
        _ZWISCHENSPEICHER.clear()
    else:
        _ZWISCHENSPEICHER.pop(str(user_id), None)


async def darf_ki(db, user_id) -> bool:
    """True, wenn dieses Konto KI-Aufrufe erlaubt.

    `db` ist ein asyncpg-Pool oder eine Verbindung, `user_id` die Kontonummer
    (int oder als Zeichenkette).
    """
    if user_id is None or db is None:
        # Kein Konto, kein Kunde: das ist der oeffentliche Weg. Ueber ihn
        # entscheidet der Aufrufer, nicht diese Stelle.
        return False

    schluessel = str(user_id)
    eintrag = _ZWISCHENSPEICHER.get(schluessel)
    jetzt = time.monotonic()
    if eintrag and jetzt - eintrag[0] < HALTBARKEIT_SEKUNDEN:
        return eintrag[1]

    try:
        nummer = int(user_id)
    except (TypeError, ValueError):
        logger.warning(
            "[KI-Erlaubnis] user_id %r ist keine Kontonummer, KI wird nicht "
            "aufgerufen", user_id,
        )
        return False

    try:
        wert = await _lese(db, nummer)
    except Exception as e:
        # Bewusst kein Rueckfall auf 'erlaubt'. Siehe Modulkopf.
        logger.error(
            "[KI-Erlaubnis] nicht lesbar fuer Konto %s (%s) — KI-Aufruf "
            "unterbleibt", nummer, e,
        )
        return False

    if wert is None:
        logger.warning(
            "[KI-Erlaubnis] Konto %s nicht gefunden — KI-Aufruf unterbleibt",
            nummer,
        )
        return False

    _ZWISCHENSPEICHER[schluessel] = (jetzt, bool(wert))
    return bool(wert)


async def _lese(db, nummer: int) -> Optional[bool]:
    frage = "SELECT ki_erlaubt FROM users WHERE id = $1"
    if hasattr(db, "acquire"):
        async with db.acquire() as conn:
            return await conn.fetchval(frage, nummer)
    return await db.fetchval(frage, nummer)


async def setze(db, user_id, erlaubt: bool) -> bool:
    """Erlaubnis setzen und den Zeitpunkt mitschreiben. Gibt den neuen Wert."""
    nummer = int(user_id)
    frage = """
        UPDATE users
        SET ki_erlaubt = $2, ki_erlaubnis_geaendert_am = NOW()
        WHERE id = $1
        RETURNING ki_erlaubt
    """
    if hasattr(db, "acquire"):
        async with db.acquire() as conn:
            neu = await conn.fetchval(frage, nummer, bool(erlaubt))
    else:
        neu = await db.fetchval(frage, nummer, bool(erlaubt))
    vergessen(nummer)
    return bool(neu)
