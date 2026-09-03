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
  6. Kernrouten: antworten die Endpunkte, die jeder Kunde anfasst?
     Ergänzt am 01.09.2026, weil /api/user/profile und
     /api/legal-ai/archive tagelang 500 warfen und der Wächter
     trotzdem stündlich "alles ruhig" meldete: die Seiten werden zu
     selten aufgerufen, um den Fehlerdruck-Schwellwert zu reißen.

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
import time
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

# Kernrouten, stellvertretend für die vier Säulen plus Konto und Bezahlung.
# Bewusst kurz: der Wächter soll Ausfälle melden, nicht die API testen.
ROUTEN_BASIS = os.getenv("WAECHTER_API_BASIS", "http://complyo-backend:8002")
ROUTEN_OEFFENTLICH = [
    "/api/health",
    "/api/stripe/plans",
    "/api/knowledge/search?q=impressum",
    "/api/widgets/accessibility.js",
    "/api/widgets/cookie-compliance.js",
]
ROUTEN_ANGEMELDET = [
    "/api/user/profile",
    "/api/v2/dashboard/metrics",
    "/api/legal-ai/archive",
    "/api/cookie-compliance/my-config",
    "/api/accessibility/agency/worklist",
]
# Konto, in dessen Namen die angemeldeten Routen geprüft werden.
WAECHTER_KONTO_ID = int(os.getenv("WAECHTER_KONTO_ID", "5"))
ROUTEN_ZEITLIMIT = 25


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


async def pruefe_kernrouten() -> list:
    """
    Ruft die Kernrouten auf und meldet alles, was nicht 2xx antwortet.

    Ein 500 auf einer selten benutzten Seite erzeugt keinen Fehlerdruck und
    blieb deshalb unsichtbar. Diese Prüfung findet ihn beim ersten Lauf.
    Sie ist fail-open: ist der Aufruf selbst nicht möglich (kein aiohttp,
    Netz weg), gibt es genau einen Befund statt einer Fehlerflut.
    """
    befunde = []
    try:
        import aiohttp
    except Exception as e:
        return [("routen-pruefung-unmoeglich",
                 f"Kernrouten nicht prüfbar: {e}")]

    kopf = {}
    try:
        from auth_service import AuthService
        kopf = {"Authorization": "Bearer "
                + AuthService(None).create_access_token(WAECHTER_KONTO_ID)}
    except Exception as e:
        befunde.append(("routen-token",
                        f"Kein Prüf-Token für Konto {WAECHTER_KONTO_ID}: {e} — "
                        "die angemeldeten Routen bleiben ungeprüft."))

    zeitlimit = aiohttp.ClientTimeout(total=ROUTEN_ZEITLIMIT)
    kaputt = []
    async with aiohttp.ClientSession(timeout=zeitlimit) as sitzung:
        aufgaben = [(pfad, {}) for pfad in ROUTEN_OEFFENTLICH]
        if kopf:
            aufgaben += [(pfad, kopf) for pfad in ROUTEN_ANGEMELDET]
        for pfad, kopfzeilen in aufgaben:
            try:
                async with sitzung.get(ROUTEN_BASIS + pfad,
                                       headers=kopfzeilen) as antwort:
                    if antwort.status >= 300:
                        kaputt.append(f"{pfad} → {antwort.status}")
            except Exception as e:
                kaputt.append(f"{pfad} → nicht erreichbar ({type(e).__name__})")

    if kaputt:
        befunde.append((
            "kernrouten-" + ";".join(sorted(k.split(" ")[0] for k in kaputt)),
            "Kernrouten antworten nicht: " + "; ".join(kaputt),
        ))
    return befunde


# Probescan: die Kernfunktion selbst pruefen, nicht nur ihre Umgebung.
#
# Der Lasttest vom 03.09.2026 hat die Luecke gezeigt: nach acht gleichzeitigen
# Scans lieferte /api/analyze-preview nichts mehr, waehrend /api/health und
# /api/stripe/plans 60 von 60 Mal mit 200 antworteten. Der Waechter meldete
# "alles ruhig", das Produkt war tot.
#
# Ein Statuscheck allein reicht dafuer NICHT: _preview_scan_fehler() gibt bei
# jedem Scannerfehler ein gewoehnliches dict zurueck, FastAPI macht daraus
# HTTP 200 mit success:false. Wer nur den Code prueft, sieht gruen, waehrend
# jeder Kundenscan scheitert. Deshalb wird der Inhalt bewertet.
PROBESCAN_ZIEL = os.getenv("WAECHTER_PROBESCAN_ZIEL", "https://complyo.de")
PROBESCAN_ZEITLIMIT = int(os.getenv("WAECHTER_PROBESCAN_ZEITLIMIT", "120"))
# Gemessen am 03.09.2026: ein Scan von complyo.de dauert 16-18 s, unter Last
# von sechs gleichzeitigen Scans 33 s. Oberhalb davon ist etwas im Argen,
# auch wenn am Ende noch ein Ergebnis kommt.
PROBESCAN_WARNAB_S = 45


async def pruefe_scanpfad() -> list:
    """Fuehrt einen echten Scan aus und bewertet das Ergebnis inhaltlich."""
    try:
        import aiohttp
    except Exception as e:
        return [("probescan-unmoeglich", f"Probescan nicht ausführbar: {e}")]

    zeitlimit = aiohttp.ClientTimeout(total=PROBESCAN_ZEITLIMIT)
    begonnen = time.monotonic()
    try:
        async with aiohttp.ClientSession(timeout=zeitlimit) as sitzung:
            async with sitzung.post(
                ROUTEN_BASIS + "/api/analyze-preview",
                json={"url": PROBESCAN_ZIEL},
            ) as antwort:
                status = antwort.status
                try:
                    daten = await antwort.json()
                except Exception:
                    daten = None
    except asyncio.TimeoutError:
        return [("probescan-zeitlimit",
                 f"Probescan von {PROBESCAN_ZIEL} kam in "
                 f"{PROBESCAN_ZEITLIMIT}s zu keinem Ergebnis. Der Scanpfad "
                 "steht — Kernrouten können trotzdem grün sein.")]
    except Exception as e:
        return [("probescan-fehler",
                 f"Probescan von {PROBESCAN_ZIEL} nicht möglich: "
                 f"{type(e).__name__}: {e}")]

    dauer = time.monotonic() - begonnen
    befunde = []

    if status >= 300:
        return [("probescan-status",
                 f"Probescan antwortete mit HTTP {status} "
                 f"(nach {dauer:.0f}s).")]

    if not isinstance(daten, dict):
        return [("probescan-antwortform",
                 f"Probescan lieferte kein auswertbares JSON (HTTP {status}).")]

    # Der eigentliche Punkt: HTTP 200 heisst hier nichts.
    if daten.get("success") is not True:
        return [("probescan-erfolglos",
                 f"Probescan meldet success={daten.get('success')!r} bei "
                 f"HTTP {status}: {daten.get('message') or daten.get('error')}. "
                 "Genau dieser Fall bleibt bei einer reinen Statusprüfung "
                 "unsichtbar.")]

    kategorien = daten.get("risk_categories")
    if not isinstance(kategorien, list) or not kategorien:
        befunde.append(("probescan-leer",
                        "Probescan war erfolgreich, liefert aber keine "
                        "Risikokategorien — der Scan lief, hat aber nichts "
                        "gemessen."))

    if daten.get("score") is None:
        befunde.append(("probescan-ohne-score",
                        "Probescan liefert keinen Score."))

    if dauer > PROBESCAN_WARNAB_S:
        befunde.append((
            "probescan-langsam",
            f"Probescan brauchte {dauer:.0f}s (üblich 16-18s, unter Last 33s). "
            "Der Scanpfad ist überlastet, bevor er ausfällt.",
        ))

    return befunde


def pruefe_neustarts() -> list:
    """Meldet, was der Gesundheitswächter in den letzten 24 h neu gestartet hat.

    Ein automatischer Neustart repariert das Symptom. Bleibt er unerwähnt,
    verschwindet die Ursache aus dem Blick — dann läuft der Dienst scheinbar
    störungsfrei, während er stündlich neu gestartet wird.
    """
    pfad = "/data/waechter/neustarts.log"
    if not os.path.exists(pfad):
        return []

    grenze = int(time.time()) - 86400
    neustarts, aufgegeben = {}, {}
    try:
        with open(pfad, encoding="utf-8", errors="replace") as f:
            for zeile in f:
                teile = zeile.split()
                if len(teile) < 3:
                    continue
                try:
                    wann = int(teile[0])
                except ValueError:
                    continue
                if wann < grenze:
                    continue
                ziel = neustarts if teile[2] == "neugestartet" else aufgegeben
                ziel[teile[1]] = ziel.get(teile[1], 0) + 1
    except Exception as e:
        return [("neustart-journal", f"Neustart-Journal nicht lesbar: {e}")]

    befunde = []
    if aufgegeben:
        befunde.append((
            "neustart-aufgegeben-" + ";".join(sorted(aufgegeben)),
            "Wiederholte Neustarts halfen nicht, der Wächter hat aufgegeben: "
            + ", ".join(f"{k} ({v}x)" for k, v in sorted(aufgegeben.items()))
            + ". Das braucht einen Menschen.",
        ))
    if neustarts:
        befunde.append((
            "neustart-" + ";".join(sorted(neustarts)),
            "In den letzten 24 h automatisch neu gestartet: "
            + ", ".join(f"{k} ({v}x)" for k, v in sorted(neustarts.items()))
            + ". Der Dienst läuft wieder, die Ursache ist damit nicht behoben.",
        ))
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
    try:
        befunde.extend(await pruefe_kernrouten())
        befunde.extend(await pruefe_scanpfad())
        befunde.extend(pruefe_neustarts())
    except Exception as e:
        befunde.append(("routen-pruefung-abgestuerzt",
                        f"Kernrouten-Prüfung fehlgeschlagen: {e}"))
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
