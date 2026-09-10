#!/usr/bin/env python3
"""
Täglicher Löschlauf.

Setzt die Fristen aus `loeschfristen.py` durch, kündigt ruhenden Konten die
Löschung an und löscht die, deren Frist abgelaufen ist.

Aufruf:
    python -m cronjobs.loeschfristen_cron            # scharf, nach Konfiguration
    python -m cronjobs.loeschfristen_cron --trocken  # zählt nur, löscht nichts

Crontab (root), eine Stunde nach der Datensicherung, damit ein gelöschter
Datensatz noch im Abzug von heute Nacht steht:
    30 3 * * * docker exec complyo-backend python -m cronjobs.loeschfristen_cron
               >> /var/log/complyo-loeschfristen.log 2>&1

**Der erste Lauf gehört als Trockenlauf gelesen.** Was hier gelöscht wird, ist
weg; die Sicherung hält es 14 Tage, danach nicht mehr. Deshalb steht der Teil,
der Nachweise anfasst, hinter `LOESCHFRISTEN_SCHARF=ja` — siehe
loeschfristen.py.
"""

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg  # noqa: E402

import konto_token  # noqa: E402
import loeschfristen  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("loeschfristen")


async def _ruhende_konten(pool, trocken: bool) -> dict:
    """
    Zwei Stufen: ankündigen, dann löschen.

    Getrennt, weil ein Konto ohne Vorwarnung zu löschen zwar zulässig, aber
    gegenüber einem Kunden, der nur ein Jahr lang nichts zu tun hatte, keine
    Art ist. Die Ankündigung wird beim nächsten Anmelden zurückgenommen.
    """
    from email_service import email_service
    from gdpr_retention_service import gdpr_service

    frontend = os.getenv("FRONTEND_URL", "https://complyo.de").rstrip("/")
    bericht = {"angekuendigt": 0, "geloescht": 0, "fehler": []}

    for konto in await loeschfristen.finde_ruhende_konten(pool):
        if konto.get("loeschung_angekuendigt_am"):
            continue  # laeuft schon
        bericht["angekuendigt"] += 1
        if trocken:
            continue
        try:
            email_service.sende_loeschankuendigung(
                konto["email"],
                konto.get("full_name") or konto["email"],
                loeschfristen.KONTO_ANKUENDIGUNG_TAGE,
                f"{frontend}/login",
            )
            await loeschfristen.kuendige_loeschung_an(pool, konto["id"])
            logger.info("Loeschung angekuendigt: user_id=%s", konto["id"])
        except Exception as e:
            # Ohne zugestellte Ankuendigung wird nicht geloescht: die Marke
            # bleibt ungesetzt, das Konto kommt morgen wieder dran.
            logger.error("Ankuendigung fehlgeschlagen fuer user_id=%s: %s", konto["id"], e)
            bericht["fehler"].append(f"Ankuendigung {konto['id']}: {e}")

    for konto in await loeschfristen.faellige_konten(pool):
        bericht["geloescht"] += 1
        if trocken or not loeschfristen.SCHARF:
            continue
        try:
            # Ein echter Vorgang in gdpr_deletion_requests, kein Sonderweg.
            # Damit hat auch die automatische Loeschung eine Referenznummer,
            # die in der Loeschbestaetigung steht und im Nachhinein belegt,
            # warum das Konto weg ist.
            async with pool.acquire() as conn:
                antrag_id = await conn.fetchval(
                    """
                    INSERT INTO gdpr_deletion_requests
                        (user_id, email, reason, status, requested_at, confirmed_at)
                    VALUES ($1, $2, $3, 'confirmed', NOW(), NOW())
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    konto["id"], konto["email"],
                    f"Automatische Loeschfrist: kein Zugriff seit "
                    f"{loeschfristen.KONTO_RUHEND_TAGE} Tagen, Ankuendigung "
                    f"vor {loeschfristen.KONTO_ANKUENDIGUNG_TAGE} Tagen zugestellt",
                )
            if antrag_id is None:
                # Es laeuft bereits ein offener Antrag des Nutzers selbst.
                # Der hat Vorrang; hier ist nichts zu tun.
                logger.info("Konto %s hat bereits einen offenen Loeschantrag", konto["id"])
                continue

            # Derselbe Weg wie beim Loeschantrag des Nutzers (Art. 17) — eine
            # zweite Loeschroutine waere eine zweite Gelegenheit, eine Tabelle
            # zu vergessen.
            await gdpr_service._execute_user_deletion(
                konto["id"], konto["email"], antrag_id
            )
            logger.warning("Ruhendes Konto geloescht: user_id=%s, Antrag %s",
                           konto["id"], antrag_id)
        except Exception as e:
            logger.error("Loeschung fehlgeschlagen fuer user_id=%s: %s", konto["id"], e)
            bericht["fehler"].append(f"Loeschung {konto['id']}: {e}")

    return bericht


async def main() -> int:
    trocken = "--trocken" in sys.argv

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        logger.error("DATABASE_URL fehlt")
        return 1

    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=3)
    try:
        bericht = await loeschfristen.wende_fristen_an(pool, trocken=trocken)
        print(loeschfristen.als_text(bericht))

        verbrauchte = await konto_token.raeume_ab(pool)
        if verbrauchte:
            print(f"  Einmal-Token abgeraeumt: {verbrauchte}")

        konten = await _ruhende_konten(pool, trocken)
        if konten["angekuendigt"] or konten["geloescht"]:
            print(
                f"  Ruhende Konten: {konten['angekuendigt']} angekuendigt, "
                f"{konten['geloescht']} faellig"
                f"{' (Trockenlauf)' if trocken else ''}"
            )
        if konten["fehler"]:
            print("  Fehler: " + "; ".join(konten["fehler"]))

        if bericht["uebersprungen"]:
            print(
                f"\n  HINWEIS: {bericht['uebersprungen']} Zeilen stehen ueber ihrer "
                "Frist, wurden aber nicht geloescht — LOESCHFRISTEN_SCHARF ist nicht "
                "gesetzt. Die eigene Datenschutzerklaerung sagt diese Loeschung zu."
            )

        return 1 if bericht["fehler"] or konten["fehler"] else 0
    finally:
        await pool.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
