"""
Einmal-Token für Passwort-Zurücksetzen und E-Mail-Bestätigung.

Beide Vorgänge hatten bis zum 10.09.2026 keinen Weg im Code. Wer sein Passwort
vergaß, hatte kein Konto mehr; `users.is_verified` stand in der Tabelle und
wurde von keiner Route je gesetzt. Es gab nur ein Admin-Kommando, das die
Bestätigungsmail eines *Leads* erneut verschickt — ein anderer Vorgang.

Drei Regeln, an denen solche Token üblicherweise scheitern:

1. **Gespeichert wird nur der Hash.** Wer die Datenbank liest, bekommt sonst
   eine Liste gültiger Passwort-Zurücksetzungen für alle Konten. Der Token
   selbst existiert nur in der Mail. SHA-256 genügt hier, anders als beim
   Passwort: der Token hat 256 Bit Zufall, es gibt nichts zu raten, also
   braucht es auch keine langsame Ableitung.
2. **Eine einzige Verwendung, mit Ablauf.** Eingelöst wird in einer
   Transaktion, die das Einlösen selbst als Bedingung prüft — zwei
   gleichzeitige Aufrufe können nicht beide gewinnen.
3. **Kein Rückschluss auf die Existenz eines Kontos.** Wer "Passwort
   vergessen" für eine fremde Adresse auslöst, bekommt dieselbe Antwort wie
   für die eigene. Das ist eine Anforderung an die *Route*, nicht an dieses
   Modul, steht hier aber, weil es zusammengehört.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Der Zurücksetz-Token liegt in einem Postfach. Je länger er gilt, desto länger
# ist ein einmal mitgelesenes Postfach ein offenes Konto. Eine Stunde reicht,
# um eine Mail zu lesen.
RESET_GUELTIG_MINUTEN = 60

# Die Bestätigung darf länger gelten: sie schaltet nichts frei, sie belegt nur,
# dass die Adresse erreichbar ist. Wer sie erst am nächsten Tag anklickt, soll
# nicht neu anfangen müssen.
BESTAETIGUNG_GUELTIG_STUNDEN = 72

TABELLE_RESET = "passwort_reset"
TABELLE_BESTAETIGUNG = "email_bestaetigung"


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def erzeuge_token() -> str:
    """256 Bit. Nicht ratbar, nicht ableitbar, url-tauglich."""
    return secrets.token_urlsafe(32)


async def lege_an(pool, tabelle: str, user_id: int, gueltig_bis: datetime,
                  ip: Optional[str] = None) -> str:
    """
    Legt einen neuen Token an und gibt ihn im Klartext zurück — das einzige Mal,
    dass er existiert.

    Ältere, noch offene Token desselben Nutzers werden dabei entwertet. Sonst
    bliebe eine versehentlich ausgelöste Zurücksetzung neben der gewollten
    gültig, und die Mail von vorhin wäre weiter ein Schlüssel.
    """
    token = erzeuge_token()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                f"UPDATE {tabelle} SET eingeloest_am = NOW() "
                "WHERE user_id = $1 AND eingeloest_am IS NULL",
                user_id,
            )
            await conn.execute(
                f"INSERT INTO {tabelle} (user_id, token_hash, gueltig_bis, ip_adresse) "
                "VALUES ($1, $2, $3, $4)",
                user_id, _hash(token), gueltig_bis, ip,
            )
    return token


async def lege_reset_an(pool, user_id: int, ip: Optional[str] = None) -> str:
    gueltig_bis = datetime.now(timezone.utc) + timedelta(minutes=RESET_GUELTIG_MINUTEN)
    return await lege_an(pool, TABELLE_RESET, user_id, gueltig_bis, ip)


async def lege_bestaetigung_an(pool, user_id: int, ip: Optional[str] = None) -> str:
    gueltig_bis = datetime.now(timezone.utc) + timedelta(hours=BESTAETIGUNG_GUELTIG_STUNDEN)
    return await lege_an(pool, TABELLE_BESTAETIGUNG, user_id, gueltig_bis, ip)


async def loese_ein(pool, tabelle: str, token: str) -> Optional[int]:
    """
    Löst einen Token ein und gibt die user_id zurück, oder None.

    Das `UPDATE ... WHERE eingeloest_am IS NULL ... RETURNING` ist der Kern:
    Prüfen und Verbrauchen sind ein einziger Schritt. Ein zweiter Aufruf mit
    demselben Token findet die Zeile nicht mehr und bekommt None — auch dann,
    wenn beide Aufrufe gleichzeitig ankommen.
    """
    if not token:
        return None
    async with pool.acquire() as conn:
        zeile = await conn.fetchrow(
            f"UPDATE {tabelle} SET eingeloest_am = NOW() "
            "WHERE token_hash = $1 AND eingeloest_am IS NULL AND gueltig_bis > NOW() "
            "RETURNING user_id",
            _hash(token),
        )
    return int(zeile["user_id"]) if zeile else None


async def loese_reset_ein(pool, token: str) -> Optional[int]:
    return await loese_ein(pool, TABELLE_RESET, token)


async def loese_bestaetigung_ein(pool, token: str) -> Optional[int]:
    return await loese_ein(pool, TABELLE_BESTAETIGUNG, token)


async def raeume_ab(pool) -> int:
    """
    Entfernt abgelaufene und eingelöste Token. Ein verbrauchter Token ist kein
    Nachweis, den jemand aufheben müsste — er ist nur noch ein Hash neben einer
    Konto-Kennung.
    """
    entfernt = 0
    async with pool.acquire() as conn:
        for tabelle in (TABELLE_RESET, TABELLE_BESTAETIGUNG):
            ergebnis = await conn.execute(
                f"DELETE FROM {tabelle} "
                "WHERE gueltig_bis < NOW() - INTERVAL '7 days' OR eingeloest_am < NOW() - INTERVAL '7 days'"
            )
            try:
                entfernt += int(ergebnis.split()[-1])
            except (ValueError, IndexError):
                pass
    return entfernt
