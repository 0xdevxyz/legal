#!/usr/bin/env python3
"""
Betriebswächter — meldet stille Ausfälle per Mail, ohne externen Dienst.

Entstanden aus dem Funktions-Audit vom 11.08.2026: Der Banner-Totalausfall
war 10 Stunden unsichtbar (Client-JS, keine Backend-Exception), der
Mail-Demo-Modus wochenlang, die KI-Klassifizierung monatelang. Ein Backend-
Sentry hätte davon wenig gesehen — die Geschäftssignale schon. Genau die
prüft dieser Wächter:

  1. Einwilligungs-Herzschlag: kamen zuletzt Consents rein, wo vorher
     täglich welche kamen? (Der Banner-Crash-Detektor.)
  2. Wirkungs-Herzschlag: melden die Kunden-Widgets noch an /api/wirkung?
  3. Monitor-Puls: hat der Legal-Change-Monitor seinen Tageslauf
     protokolliert? (legal_monitoring_logs, seit 11.08. je Lauf eine Zeile.)
  4. Fehlerdruck & Container-Zustand: liefert der Host-Wrapper mit
     (scripts/betriebswaechter.sh) — docker logs/docker ps sind im
     Container nicht erreichbar.
  5. DSGVO-Hygiene: Löschanträge, die > 7 Tage unbestätigt liegen.

Alarm nur bei Befund; jeder Befund höchstens einmal je 24 h (State-Datei),
damit ein Dauerzustand nicht stündlich mailt. Läuft als Host-Cron über
`docker run` im Backend-Image (DB + SMTP aus der .env). Logging nur nach
stdout — die Crontab-Zeile leitet host-seitig um (Lehre aus dem
knowledge_updater-Crash).
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("betriebswaechter")

DATABASE_URL = os.getenv("DATABASE_URL", "")
EMPFAENGER = os.getenv("COMPLYO_WAECHTER_MAIL", "mail@panoart360.de")
# Telegram ist der Wunsch-Kanal des Betreibers (12.08.); Mail bleibt als
# zweiter Kanal bestehen. Beide fail-open: ein Kanal genügt.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
STATE_PFAD = Path(os.getenv("WAECHTER_STATE_PFAD", "/data/waechter/state.json"))
ERNEUT_NACH_STUNDEN = 24

# Schwellen — bewusst konservativ, damit der Wächter nicht zum Rauschen wird.
CONSENT_MIN_TAGESSCHNITT = 3.0   # erst ab ~3 Consents/Tag ist Stille ein Signal
WIRKUNG_MIN_AKTIVE_SITES = 2     # erst ab 2 meldenden Sites ist Stille ein Signal
FEHLERDRUCK_JE_STUNDE = 20       # ERROR-Zeilen/h im Backend-Log
MONITOR_MAX_ALTER_STUNDEN = 26   # Tageslauf 05:00 + Puffer


def bewerte_herzschlag(vergleich_pro_tag: float, aktuell_24h: int,
                       mindest_schnitt: float) -> bool:
    """True = Alarm: vorher regelmäßig Signale, jetzt komplette Stille."""
    return vergleich_pro_tag >= mindest_schnitt and aktuell_24h == 0


def lade_state() -> dict:
    try:
        return json.loads(STATE_PFAD.read_text())
    except Exception:
        return {}


def speichere_state(state: dict) -> None:
    try:
        STATE_PFAD.parent.mkdir(parents=True, exist_ok=True)
        STATE_PFAD.write_text(json.dumps(state, indent=1))
    except OSError as e:
        # Ohne State mailt der Wächter schlimmstenfalls stündlich — das ist
        # besser als gar nicht, deshalb kein Abbruch.
        logger.warning(f"State nicht schreibbar ({STATE_PFAD}): {e}")


def dedupliziere(befunde: list, state: dict, jetzt: datetime) -> list:
    """Nur Befunde durchlassen, die nicht binnen 24 h schon gemeldet wurden."""
    frisch = []
    for schluessel, text in befunde:
        letzter = state.get(schluessel)
        if letzter:
            try:
                if jetzt - datetime.fromisoformat(letzter) < timedelta(hours=ERNEUT_NACH_STUNDEN):
                    logger.info(f"unterdrückt (schon gemeldet): {schluessel}")
                    continue
            except ValueError:
                pass
        frisch.append((schluessel, text))
        state[schluessel] = jetzt.isoformat()
    return frisch


async def pruefe_datenbank() -> list:
    """Alle DB-gestützten Checks. Liefert [(schluessel, text), ...]."""
    import asyncpg

    befunde = []
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # 1) Einwilligungs-Herzschlag
        vergleich = await conn.fetchval(
            "SELECT count(*)/7.0 FROM cookie_consent_logs "
            "WHERE timestamp >= NOW() - INTERVAL '8 days' "
            "AND timestamp < NOW() - INTERVAL '1 day'"
        ) or 0
        aktuell = await conn.fetchval(
            "SELECT count(*) FROM cookie_consent_logs "
            "WHERE timestamp >= NOW() - INTERVAL '1 day'"
        ) or 0
        if bewerte_herzschlag(float(vergleich), int(aktuell), CONSENT_MIN_TAGESSCHNITT):
            befunde.append((
                "consent-stille",
                f"Keine einzige Cookie-Einwilligung in 24 h (Vorwoche: "
                f"{float(vergleich):.1f}/Tag). So sah der Banner-Totalausfall "
                f"vom 10.08. aus — Banner auf einer Kundenseite prüfen.",
            ))

        # 2) Wirkungs-Herzschlag der Accessibility-Widgets
        aktive = await conn.fetchval(
            "SELECT count(DISTINCT site_id) FROM accessibility_wirkung "
            "WHERE zuletzt >= NOW() - INTERVAL '7 days'"
        ) or 0
        frische = await conn.fetchval(
            "SELECT count(DISTINCT site_id) FROM accessibility_wirkung "
            "WHERE zuletzt >= NOW() - INTERVAL '1 day'"
        ) or 0
        if aktive >= WIRKUNG_MIN_AKTIVE_SITES and frische == 0:
            befunde.append((
                "wirkung-stille",
                f"Kein Widget meldet mehr Wirkung (/api/wirkung): 0 von "
                f"{aktive} zuletzt aktiven Sites in 24 h. Auslieferung von "
                f"accessibility.js prüfen.",
            ))

        # 3) Monitor-Puls (Tabelle wird seit 11.08. je Lauf beschrieben;
        #    solange sie leer ist, greift der Check bewusst noch nicht)
        letzter_lauf = await conn.fetchval(
            "SELECT MAX(scan_date) FROM legal_monitoring_logs WHERE status = 'completed'"
        )
        hat_laeufe = await conn.fetchval("SELECT count(*) FROM legal_monitoring_logs") or 0
        if hat_laeufe and letzter_lauf:
            alter = datetime.now(letzter_lauf.tzinfo) - letzter_lauf
            if alter > timedelta(hours=MONITOR_MAX_ALTER_STUNDEN):
                befunde.append((
                    "monitor-puls",
                    f"Legal-Change-Monitor: letzter erfolgreicher Lauf vor "
                    f"{alter.total_seconds() / 3600:.0f} h (Soll: täglich 05:00). "
                    f"Cron-Log /var/log/complyo-legal-monitor.log prüfen.",
                ))

        # 4) DSGVO-Hygiene: liegengebliebene Löschanträge
        liegend = await conn.fetchval(
            "SELECT count(*) FROM gdpr_deletion_requests "
            "WHERE status = 'pending' AND requested_at < NOW() - INTERVAL '7 days'"
        ) or 0
        if liegend:
            befunde.append((
                "gdpr-antraege",
                f"{liegend} DSGVO-Löschantrag/-anträge seit > 7 Tagen unbestätigt "
                f"(Art. 12: unverzüglich, spätestens ein Monat). "
                f"POST /api/gdpr/admin/confirm-deletion.",
            ))
    finally:
        await conn.close()
    return befunde


def pruefe_host_signale() -> list:
    """Vom Host-Wrapper mitgegebene Signale (docker ps / docker logs)."""
    befunde = []

    status = os.getenv("WAECHTER_CONTAINER_STATUS", "")
    kranke = [z for z in status.splitlines()
              if z.strip() and "(healthy)" not in z]
    if status and kranke:
        befunde.append((
            "container-" + ";".join(sorted(k.split(":")[0] for k in kranke)),
            "Container nicht healthy: " + "; ".join(kranke),
        ))

    try:
        fehler = int(os.getenv("WAECHTER_FEHLER_1H", "0"))
    except ValueError:
        fehler = 0
    if fehler > FEHLERDRUCK_JE_STUNDE:
        beispiele = os.getenv("WAECHTER_FEHLER_BEISPIELE", "").strip()
        befunde.append((
            "fehlerdruck",
            f"{fehler} ERROR-Zeilen im Backend-Log der letzten Stunde "
            f"(Schwelle {FEHLERDRUCK_JE_STUNDE})."
            + (f" Beispiele:\n{beispiele}" if beispiele else ""),
        ))
    return befunde


def baue_telegram_text(befunde: list) -> str:
    zeilen = [f"• {text}" for _, text in befunde]
    return (f"⚠️ complyo-Wächter: {len(befunde)} Befund(e)\n\n"
            + "\n\n".join(zeilen)
            + "\n\nJeder Befund wird höchstens einmal je 24 h gemeldet.")


def sende_telegram(befunde: list) -> bool:
    """Bot-API direkt über stdlib — keine neue Abhängigkeit, 10s-Timeout."""
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT):
        return False
    import urllib.request

    daten = json.dumps({
        "chat_id": TELEGRAM_CHAT,
        "text": baue_telegram_text(befunde)[:4000],  # Telegram-Limit 4096
        "disable_web_page_preview": True,
    }).encode()
    anfrage = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data=daten, headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=10) as antwort:
            ok = json.loads(antwort.read()).get("ok", False)
        if not ok:
            logger.error("Telegram-API antwortete mit ok=false")
        return bool(ok)
    except Exception as e:
        logger.error(f"Telegram-Versand fehlgeschlagen: {e}")
        return False


def sende_mail(befunde: list) -> bool:
    from email_service import email_service

    zeilen = [f"• {text}" for _, text in befunde]
    text = ("Der complyo-Betriebswächter hat Auffälligkeiten gefunden:\n\n"
            + "\n\n".join(zeilen)
            + "\n\nJeder Befund wird höchstens einmal je 24 h gemeldet.")
    html = ("<h2>complyo-Betriebswächter</h2><ul>"
            + "".join(f"<li>{text}</li>" for _, text in befunde)
            + "</ul><p>Jeder Befund wird höchstens einmal je 24&nbsp;h gemeldet.</p>")
    return email_service._send_email(
        to_email=EMPFAENGER,
        subject=f"⚠️ complyo-Wächter: {len(befunde)} Befund(e)",
        html_body=html,
        text_body=text,
    )


def sende_alarm(befunde: list) -> list:
    """Telegram zuerst (Wunsch-Kanal), Mail zusätzlich; ein Kanal genügt.

    Liefert die Kanäle, die WIRKLICH zugestellt haben — nicht die, die es
    versucht haben. Ein „verschickt" über einem gescheiterten Versand ist
    dieselbe Lüge, die den Mail-Demo-Modus wochenlang unsichtbar hielt.
    """
    getragen = []
    if sende_telegram(befunde):
        getragen.append("Telegram")
    if sende_mail(befunde):
        getragen.append("Mail")
    return getragen


async def main() -> int:
    befunde = []
    try:
        befunde.extend(await pruefe_datenbank())
    except Exception as e:
        befunde.append(("datenbank-unerreichbar",
                        f"Datenbank-Checks fehlgeschlagen: {e}"))
    befunde.extend(pruefe_host_signale())

    if not befunde:
        logger.info("Alles ruhig — kein Befund.")
        return 0

    state = lade_state()
    frisch = dedupliziere(befunde, state, datetime.now())
    speichere_state(state)

    if not frisch:
        logger.info(f"{len(befunde)} Befund(e), alle bereits gemeldet.")
        return 0

    for schluessel, text in frisch:
        logger.warning(f"BEFUND {schluessel}: {text}")

    getragen = sende_alarm(frisch)
    if getragen:
        logger.info(f"Alarm mit {len(frisch)} Befund(en) zugestellt über: "
                    + ", ".join(getragen))
        return 0
    logger.error("KEIN Kanal hat zugestellt (Telegram und Mail gescheitert) — "
                 "Befunde stehen oben im Log.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
