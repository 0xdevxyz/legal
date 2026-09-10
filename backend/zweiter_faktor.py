"""
Zweiter Faktor: zeitbasierte Einmalkennwörter (TOTP) und Wiederherstellungscodes.

Warum überhaupt
---------------
Ein complyo-Konto verfügt über die Websites des Kunden: es kann Reparaturen
freigeben, die auf der fremden Seite ausgeliefert werden, und es kann in
verbundene Git-Depots schreiben. Wer das Passwort hat, kann fremden Code auf
Kundenseiten bringen. Für so ein Konto ist ein einziger Faktor zu wenig.

Warum ohne Bibliothek
---------------------
`pyotp` ist im Image nicht vorhanden. TOTP ist RFC 6238 und besteht aus zwölf
Zeilen über `hmac` und `hashlib` aus der Standardbibliothek. Eine neue
Abhängigkeit im Bauplan wäre hier mehr Angriffsfläche als Ersparnis. Die
Umsetzung unten ist gegen die Testvektoren aus Anhang B des RFC geprüft
(siehe tests/test_zweiter_faktor.py).

Das Geheimnis liegt verschlüsselt
---------------------------------
Wer die Datenbank liest, hat sonst alle zweiten Faktoren — der zweite Faktor
wäre dann nur eine zweite Kopie desselben Geheimnisses. Verschlüsselt wird mit
Fernet und einem eigenen Schlüssel (`COMPLYO_2FA_ENC_KEY`), getrennt vom
Git-Token-Schlüssel: ein Schlüssel, ein Zweck. Fehlt er, verweigert die
Einrichtung den Dienst (fail-closed) statt still im Klartext zu speichern —
dieselbe Linie wie in git_token_crypto.py.

Wiederverwendung eines Codes
----------------------------
Ein TOTP-Code gilt 30 Sekunden. Wer ihn in dieser Zeit abfängt, etwa über eine
nachgebaute Anmeldeseite, kann ihn ein zweites Mal einlösen. Deshalb wird jeder
eingelöste Zeitschritt in Redis vermerkt und ein zweites Mal abgewiesen. Ohne
Redis bleibt die Anmeldung möglich, dieser Schutz fällt dann weg — das ist
protokolliert, nicht verschwiegen.
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import struct
import time
from typing import List, Optional, Tuple
from urllib.parse import quote

import bcrypt as _bcrypt
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# RFC 6238 Standardwerte. Google Authenticator, 1Password, Aegis und die
# Passwortmanager der Browser sprechen alle genau das.
ZIFFERN = 6
SCHRITT_SEKUNDEN = 30

# Wie viele Zeitschritte Abweichung geduldet werden. 1 heisst: der Code des
# vorigen und des nächsten Fensters gilt auch — zusammen rund 90 Sekunden.
# Deckt eine fehlgehende Uhr im Telefon und langsames Abtippen ab. Mehr wäre
# eine spürbar längere Gültigkeit für einen abgefangenen Code.
TOLERANZ_SCHRITTE = 1

ANZAHL_WIEDERHERSTELLUNGSCODES = 10


class ZweiterFaktorFehler(Exception):
    """Einrichtung oder Prüfung nicht möglich. Die Meldung ist für das Protokoll."""


# ---------------------------------------------------------------------------
# Verschlüsselung des Geheimnisses
# ---------------------------------------------------------------------------

def _fernet() -> Fernet:
    schluessel = os.getenv("COMPLYO_2FA_ENC_KEY", "").strip()
    if not schluessel:
        raise ZweiterFaktorFehler(
            "COMPLYO_2FA_ENC_KEY fehlt — der zweite Faktor wird weder "
            "gespeichert noch gelesen (fail-closed). Schlüssel erzeugen mit: "
            "python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(schluessel.encode())
    except Exception as e:
        raise ZweiterFaktorFehler(f"COMPLYO_2FA_ENC_KEY ist kein gültiger Fernet-Schlüssel: {e}")


def verschluessele(geheimnis: str) -> str:
    return _fernet().encrypt(geheimnis.encode()).decode()


def entschluessele(chiffre: str) -> str:
    try:
        return _fernet().decrypt(chiffre.encode()).decode()
    except InvalidToken as e:
        # Kein Rückfall auf Klartext: eine nicht entschlüsselbare Chiffre ist
        # ein Fehler, kein Geheimnis.
        raise ZweiterFaktorFehler(f"Zweiter Faktor nicht entschlüsselbar: {e}")


# ---------------------------------------------------------------------------
# TOTP nach RFC 6238
# ---------------------------------------------------------------------------

def erzeuge_geheimnis() -> str:
    """160 Bit Zufall, Base32 ohne Füllzeichen — das Format, das die Apps lesen."""
    roh = secrets.token_bytes(20)
    return base64.b32encode(roh).decode().rstrip("=")


def _geheimnis_bytes(geheimnis: str) -> bytes:
    roh = geheimnis.strip().replace(" ", "").upper()
    fehlend = (-len(roh)) % 8
    try:
        return base64.b32decode(roh + "=" * fehlend)
    except Exception as e:
        raise ZweiterFaktorFehler(f"Geheimnis ist kein gültiges Base32: {e}")


def _hotp(geheimnis: bytes, zaehler: int, ziffern: int = ZIFFERN) -> str:
    """HOTP nach RFC 4226 — der Baustein, auf dem TOTP sitzt."""
    nachricht = struct.pack(">Q", zaehler)
    verdaut = hmac.new(geheimnis, nachricht, hashlib.sha1).digest()
    versatz = verdaut[-1] & 0x0F
    zahl = struct.unpack(">I", verdaut[versatz:versatz + 4])[0] & 0x7FFFFFFF
    return str(zahl % (10 ** ziffern)).zfill(ziffern)


def _zeitschritt(zeitpunkt: Optional[float] = None) -> int:
    return int((zeitpunkt if zeitpunkt is not None else time.time()) // SCHRITT_SEKUNDEN)


def code_fuer(geheimnis: str, zeitpunkt: Optional[float] = None) -> str:
    """Der Code, der gerade gilt. Nur für Tests und die Einrichtungsvorschau."""
    return _hotp(_geheimnis_bytes(geheimnis), _zeitschritt(zeitpunkt))


def pruefe_code(geheimnis: str, eingabe: str,
                zeitpunkt: Optional[float] = None) -> Optional[int]:
    """
    Prüft einen eingetippten Code.

    Rückgabe: der Zeitschritt, zu dem der Code passt — den braucht der Aufrufer,
    um die Wiederverwendung zu sperren. `None`, wenn kein Fenster passt.

    Verglichen wird mit `compare_digest`: ein Vergleich, der bei der ersten
    abweichenden Ziffer abbricht, verrät über die Laufzeit, wie viele Ziffern
    stimmten.
    """
    sauber = "".join(z for z in (eingabe or "") if z.isdigit())
    if len(sauber) != ZIFFERN:
        return None

    roh = _geheimnis_bytes(geheimnis)
    jetzt = _zeitschritt(zeitpunkt)
    for versatz in range(-TOLERANZ_SCHRITTE, TOLERANZ_SCHRITTE + 1):
        schritt = jetzt + versatz
        if hmac.compare_digest(_hotp(roh, schritt), sauber):
            return schritt
    return None


def otpauth_uri(geheimnis: str, email: str, herausgeber: str = "complyo") -> str:
    """
    Die Adresse, die als QR-Code angezeigt wird. Format nach der
    Key-Uri-Spezifikation, die alle gängigen Apps lesen.
    """
    kennung = quote(f"{herausgeber}:{email}", safe="")
    return (
        f"otpauth://totp/{kennung}"
        f"?secret={geheimnis}"
        f"&issuer={quote(herausgeber, safe='')}"
        f"&algorithm=SHA1&digits={ZIFFERN}&period={SCHRITT_SEKUNDEN}"
    )


# ---------------------------------------------------------------------------
# Wiederverwendungssperre
# ---------------------------------------------------------------------------

async def schritt_schon_benutzt(redis, user_id: int, schritt: int) -> bool:
    if not redis:
        return False
    try:
        return bool(await redis.get(f"2fa:benutzt:{user_id}:{schritt}"))
    except Exception as e:
        logger.warning("2FA-Wiederverwendungssperre nicht lesbar: %s", e)
        return False


async def merke_schritt(redis, user_id: int, schritt: int) -> None:
    if not redis:
        logger.warning(
            "2FA ohne Redis: Code von Nutzer %s kann innerhalb seines Fensters "
            "ein zweites Mal eingelöst werden", user_id
        )
        return
    try:
        # Haltbarkeit = Toleranzfenster plus ein Schritt Sicherheitsabstand.
        ttl = SCHRITT_SEKUNDEN * (TOLERANZ_SCHRITTE * 2 + 2)
        await redis.setex(f"2fa:benutzt:{user_id}:{schritt}", ttl, "1")
    except Exception as e:
        logger.warning("2FA-Wiederverwendungssperre nicht schreibbar: %s", e)


# ---------------------------------------------------------------------------
# Wiederherstellungscodes
# ---------------------------------------------------------------------------

def erzeuge_wiederherstellungscodes(anzahl: int = ANZAHL_WIEDERHERSTELLUNGSCODES) -> List[str]:
    """
    Codes für den Fall, dass das Telefon weg ist. Ohne sie ist ein verlorenes
    Telefon ein verlorenes Konto, und der Support-Weg dorthin wäre eine
    Hintertür an der Anmeldung vorbei.

    Format `xxxxx-xxxxx` aus einem Alphabet ohne 0/O und 1/l/I — abgeschrieben
    wird das hier von Papier.
    """
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    codes = []
    for _ in range(anzahl):
        teile = ["".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(2)]
        codes.append("-".join(teile))
    return codes


def normalisiere_code(code: str) -> str:
    return "".join(z for z in (code or "").lower() if z.isalnum())


def hashe_wiederherstellungscode(code: str) -> str:
    """
    bcrypt, wie beim Passwort. Ein Wiederherstellungscode ist ein Passwort mit
    einer einzigen Verwendung; im Klartext gespeichert wäre er eine Liste von
    Generalschlüsseln in derselben Datenbank.
    """
    return _bcrypt.hashpw(normalisiere_code(code).encode(), _bcrypt.gensalt()).decode()


def pruefe_wiederherstellungscode(code: str, hash_wert: str) -> bool:
    try:
        return _bcrypt.checkpw(normalisiere_code(code).encode(), hash_wert.encode())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Datenbankzugriff
# ---------------------------------------------------------------------------

async def ist_aktiv(pool, user_id: int) -> bool:
    """True, wenn der Nutzer den zweiten Faktor eingerichtet UND bestätigt hat."""
    async with pool.acquire() as conn:
        return bool(await conn.fetchval(
            "SELECT bestaetigt_am IS NOT NULL FROM user_totp WHERE user_id = $1",
            user_id,
        ))


async def lade_geheimnis(pool, user_id: int, nur_bestaetigt: bool = True) -> Optional[str]:
    async with pool.acquire() as conn:
        zeile = await conn.fetchrow(
            "SELECT geheimnis_chiffre, bestaetigt_am FROM user_totp WHERE user_id = $1",
            user_id,
        )
    if not zeile:
        return None
    if nur_bestaetigt and zeile["bestaetigt_am"] is None:
        return None
    return entschluessele(zeile["geheimnis_chiffre"])


async def lege_an(pool, user_id: int) -> str:
    """
    Legt ein neues, noch unbestätigtes Geheimnis an und gibt es im Klartext
    zurück — genau einmal, für den QR-Code. Ein erneuter Aufruf ersetzt ein
    unbestätigtes Geheimnis; ein bestätigtes wird nicht angetastet.
    """
    geheimnis = erzeuge_geheimnis()
    chiffre = verschluessele(geheimnis)
    async with pool.acquire() as conn:
        vorhanden = await conn.fetchval(
            "SELECT bestaetigt_am FROM user_totp WHERE user_id = $1", user_id
        )
        if vorhanden is not None:
            raise ZweiterFaktorFehler("Der zweite Faktor ist für dieses Konto bereits aktiv.")
        await conn.execute(
            """
            INSERT INTO user_totp (user_id, geheimnis_chiffre, erstellt_am)
            VALUES ($1, $2, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET geheimnis_chiffre = EXCLUDED.geheimnis_chiffre,
                          erstellt_am = NOW(), bestaetigt_am = NULL
            """,
            user_id, chiffre,
        )
    return geheimnis


async def bestaetige(pool, user_id: int, codes: List[str]) -> None:
    """Schaltet den zweiten Faktor scharf und legt die Wiederherstellungscodes ab."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            betroffen = await conn.execute(
                "UPDATE user_totp SET bestaetigt_am = NOW() "
                "WHERE user_id = $1 AND bestaetigt_am IS NULL",
                user_id,
            )
            if betroffen.endswith(" 0"):
                raise ZweiterFaktorFehler("Kein unbestätigter zweiter Faktor für dieses Konto.")
            await conn.execute("DELETE FROM user_wiederherstellungscodes WHERE user_id = $1", user_id)
            for code in codes:
                await conn.execute(
                    "INSERT INTO user_wiederherstellungscodes (user_id, code_hash) VALUES ($1, $2)",
                    user_id, hashe_wiederherstellungscode(code),
                )


async def schalte_ab(pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM user_totp WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM user_wiederherstellungscodes WHERE user_id = $1", user_id)


async def loese_wiederherstellungscode_ein(pool, user_id: int, eingabe: str) -> bool:
    """
    Prüft einen Wiederherstellungscode und verbraucht ihn.

    Durchlaufen werden alle noch offenen Codes; bcrypt lässt keine Suche über
    den Hash zu. Bei zehn Codes ist das ein knapper Wimpernschlag und
    gleichzeitig der Grund, warum der Versuch ratenbegrenzt sein muss.
    """
    async with pool.acquire() as conn:
        offene = await conn.fetch(
            "SELECT id, code_hash FROM user_wiederherstellungscodes "
            "WHERE user_id = $1 AND benutzt_am IS NULL",
            user_id,
        )
        for zeile in offene:
            if pruefe_wiederherstellungscode(eingabe, zeile["code_hash"]):
                await conn.execute(
                    "UPDATE user_wiederherstellungscodes SET benutzt_am = NOW() WHERE id = $1",
                    zeile["id"],
                )
                return True
    return False


async def offene_wiederherstellungscodes(pool, user_id: int) -> int:
    async with pool.acquire() as conn:
        return int(await conn.fetchval(
            "SELECT COUNT(*) FROM user_wiederherstellungscodes "
            "WHERE user_id = $1 AND benutzt_am IS NULL",
            user_id,
        ) or 0)
