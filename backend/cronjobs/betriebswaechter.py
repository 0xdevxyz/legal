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
  6. Datensicherung: gibt es einen frischen Abzug, und war er
     wiederherstellbar? Ergänzt am 07.09.2026 — bis dahin gab es weder
     Zeitplan noch Prüfung, und eine stillschweigend gescheiterte Sicherung
     wäre genauso unsichtbar gewesen wie gar keine.
  7. Rechtsquellen: liefern die RSS-Quellen der Rechtsaenderungs-
     Ueberwachung noch? Ergaenzt am 14.09.2026. Bis dahin waren drei der
     13 aktiven Quellen seit ihrer Anlage stumm (EU Parlament: HTTP 202
     als Fehler gebucht; EDPB News und Datenschutz.org: Feed-Adresse
     leitet auf eine HTML-Seite um, HTTP 200 ohne lesbaren Inhalt) —
     und der Lauf meldete jeden Morgen "Feed fetch completed". Die
     Ueberwachung ist ein verkauftes Merkmal: eine stumme Quelle heisst,
     eine Rechtsaenderung wird nicht bemerkt.
  8. Kernrouten: antworten die Endpunkte, die jeder Kunde anfasst?
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

import feedparser
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
SICHERUNG_MAX_ALTER_STUNDEN = 30  # Tageslauf 02:30 + Puffer
SICHERUNG_MARKE = Path(os.getenv("WAECHTER_SICHERUNG_MARKE",
                                 "/data/waechter/datensicherung.json"))

# Rechtsquellen. Eine Quelle gilt erst nach 30 Tagen ohne Eintrag als
# verdaechtig — Behoerdenfeeds veroeffentlichen wirklich selten. Erst dann
# wird sie live nachgemessen, damit der Waechter nicht stuendlich 13 fremde
# Server abklappert.
QUELLEN_LEER_TAGE = int(os.getenv("WAECHTER_QUELLEN_LEER_TAGE", "30"))
# Wenn ueberhaupt keine Quelle mehr etwas liefert, ist die ganze Saeule tot.
QUELLEN_STILLE_TAGE = int(os.getenv("WAECHTER_QUELLEN_STILLE_TAGE", "7"))

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


def bewerte_quelle(name: str, eintraege_gesamt: int, status: int,
                   eintraege_im_feed: int, fehler: str) -> tuple:
    """Eine Quelle einordnen, die seit QUELLEN_LEER_TAGE nichts geliefert hat.

    Reine Entscheidung, damit sie ohne Netz und ohne DB pruefbar ist.
    Rueckgabe: (schluessel, text) oder None (= kein Befund).

    Die Unterscheidung, auf die es ankommt: eine Quelle, die einen lesbaren
    Feed liefert und nur selten veroeffentlicht (BayLDA: 20 Eintraege, der
    neueste von Maerz), ist gesund. Eine Quelle, die HTTP 200 und nichts
    Lesbares liefert, ist kaputt — sieht aber im Log genauso aus. Wer beide
    gleich behandelt, baut entweder eine Fehlalarm-Maschine oder einen
    Waechter, der den echten Ausfall verschweigt.
    """
    stelle = f"rss_feed_sources: {name}"
    fehler = fehler.rstrip().rstrip(".")
    if fehler:
        return (f"quelle-abruf:{name}",
                f"Rechtsquelle „{name}“ nicht abrufbar: {fehler}. "
                f"Seit {QUELLEN_LEER_TAGE} Tagen kein Eintrag. {stelle}")
    if status in (204, 304):
        # Gueltige Antwort ohne Inhalt. Kein Ausfall.
        return None
    if status >= 400:
        return (f"quelle-abruf:{name}",
                f"Rechtsquelle „{name}“ antwortet mit HTTP {status}. "
                f"Seit {QUELLEN_LEER_TAGE} Tagen kein Eintrag. {stelle}")
    if eintraege_im_feed == 0:
        return (f"quelle-leer:{name}",
                f"Rechtsquelle „{name}“ antwortet mit HTTP {status}, liefert "
                f"aber keinen lesbaren Feed (0 Eintraege). Typisch fuer eine "
                f"Feed-Adresse, die inzwischen auf eine HTML-Seite umleitet. "
                f"{stelle}")
    if eintraege_gesamt == 0:
        return (f"quelle-ohne-treffer:{name}",
                f"Rechtsquelle „{name}“ liefert {eintraege_im_feed} Eintraege, "
                f"aber seit ihrer Anlage wurde kein einziger gespeichert. "
                f"Stichwortfilter (keywords) oder Speicherung pruefen. {stelle}")
    # Feed lebt und hat schon geliefert — veroeffentlicht nur gerade nichts.
    return None


async def pruefe_rechtsquellen() -> list:
    """Liefern die RSS-Quellen der Rechtsaenderungs-Ueberwachung noch?

    Gemessen wird die Zieltabelle `legal_news`, nicht der Rueckgabewert des
    Abrufs. Der sagte am 14.09.2026 elf Morgen in Folge "11 Feeds
    verarbeitet", waehrend drei Quellen nie einen Eintrag erzeugt hatten.

    Nur Quellen, die in der Tabelle auffaellig sind, werden live nachgemessen
    — und zwar mit demselben Abruf, den der Dienst benutzt (NewsService.
    _abrufen). Ein Waechter, der anders abruft als das Produkt, bewacht
    seinen eigenen Code.
    """
    import asyncpg
    from news_service import NewsService

    befunde = []
    abruf = NewsService(None)  # _abrufen braucht den Pool nicht
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        aktive = await conn.fetch(
            f"""
            SELECT s.name, s.url,
                   (SELECT count(*) FROM legal_news n WHERE n.source = s.name)
                       AS gesamt,
                   (SELECT count(*) FROM legal_news n WHERE n.source = s.name
                        AND n.fetched_date >= NOW() - INTERVAL '{QUELLEN_LEER_TAGE} days')
                       AS frisch
            FROM rss_feed_sources s
            WHERE s.is_active = TRUE
            ORDER BY s.id
            """
        )
        if not aktive:
            return [("quellen-keine-aktive",
                     "Keine einzige aktive Rechtsquelle konfiguriert. Die "
                     "Rechtsaenderungs-Ueberwachung laeuft ins Leere.")]

        # 1) Saeulen-Puls: kommt ueberhaupt noch etwas herein?
        juengster = await conn.fetchval("SELECT MAX(fetched_date) FROM legal_news")
        if juengster:
            alter = datetime.now() - juengster
            if alter > timedelta(days=QUELLEN_STILLE_TAGE):
                befunde.append((
                    "quellen-stille",
                    f"Seit {alter.days} Tagen kein einziger neuer Rechts-Eintrag "
                    f"aus {len(aktive)} aktiven Quellen (Soll: taeglich 06:00, "
                    f"cronjobs/fetch_news.py). /var/log/complyo-news-fetch.log.",
                ))

        # 2) Die still gebliebenen Quellen einzeln nachmessen.
        stumm = [q for q in aktive if q["frisch"] == 0]
        for q in stumm:
            status, eintraege, fehler = 0, 0, ""
            try:
                response, fehler = await abruf._abrufen(q["url"], q["name"])
                if response is not None:
                    status = response.status_code
                    if status < 400 and status not in (204, 304):
                        gelesen = feedparser.parse(response.text)
                        eintraege = len(gelesen.entries)
            except Exception as e:
                fehler = f"{type(e).__name__}: {e}"
            befund = bewerte_quelle(q["name"], int(q["gesamt"]), status,
                                    eintraege, fehler)
            if befund:
                befunde.append(befund)

        liefernd = len(aktive) - len(stumm)
        logger.info(f"Rechtsquellen: {liefernd} von {len(aktive)} aktiven Quellen "
                    f"haben in {QUELLEN_LEER_TAGE} Tagen geliefert, "
                    f"{len(stumm)} stumm, {len(befunde)} Befund(e).")
    finally:
        await conn.close()
    return befunde


def pruefe_datensicherung() -> list:
    """Liegt ein frischer, geprüfter Abzug vor?

    Die Sicherung schreibt bei JEDEM Ausstieg eine Marke, auch beim
    Fehlschlag. Damit lassen sich drei Zustände unterscheiden, die von aussen
    sonst gleich aussehen: sie lief und war gut, sie lief und scheiterte, sie
    lief gar nicht. Der dritte ist der gefährlichste — genau so verhielten
    sich der Banner-Ausfall, die Alt-Text-Speicherung und die Vault-Crons.

    `wiederherstellung_geprueft` ist die Angabe, auf die es ankommt. Ein Abzug,
    der nie zurückgespielt wurde, ist eine Vermutung; die Sicherung spielt ihn
    deshalb bei jedem Lauf in eine Wegwerf-Datenbank ein und vergleicht die
    Zeilen. Steht hier "nein", gibt es zwar eine Datei, aber keine Zusage.
    """
    if not SICHERUNG_MARKE.exists():
        return [("sicherung-nie-gelaufen",
                 f"Keine Marke der Datensicherung unter {SICHERUNG_MARKE}. "
                 "Entweder läuft der Cron nicht, oder er kam nie bis zum Ende.")]

    try:
        marke = json.loads(SICHERUNG_MARKE.read_text())
    except Exception as e:
        return [("sicherung-marke-unlesbar",
                 f"Marke der Datensicherung ist nicht lesbar: {e}")]

    befunde = []
    ergebnis = marke.get("ergebnis")
    if ergebnis not in ("erfolgreich", "uebersprungen"):
        befunde.append(("sicherung-fehlgeschlagen",
                        f"Letzte Datensicherung meldet '{ergebnis}': "
                        f"{marke.get('meldung', 'ohne Angabe')}"))

    if ergebnis == "erfolgreich" and marke.get("wiederherstellung_geprueft") != "ja":
        befunde.append(("sicherung-ungeprueft",
                        "Es gibt einen Abzug, aber die Wiederherstellungsprobe "
                        "ist nicht durchgelaufen. Eine Sicherung ohne Probe ist "
                        "eine Vermutung."))

    try:
        zeitpunkt = datetime.fromisoformat(
            marke.get("zeitpunkt", "").replace("Z", "+00:00"))
        alter = (datetime.now(zeitpunkt.tzinfo) - zeitpunkt).total_seconds() / 3600
        if alter > SICHERUNG_MAX_ALTER_STUNDEN:
            befunde.append(("sicherung-veraltet",
                            f"Letzte Datensicherung ist {alter:.0f} h alt "
                            f"(Grenze {SICHERUNG_MAX_ALTER_STUNDEN} h). "
                            "Der Cron läuft offenbar nicht mehr."))
    except (ValueError, TypeError):
        befunde.append(("sicherung-ohne-zeitpunkt",
                        "Marke der Datensicherung trägt keinen lesbaren Zeitpunkt."))

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

# Der Probescan ist Systemarbeit und soll nicht aus dem Vorschau-Topf bezahlt
# werden, der Interessenten gehoert (15.09.2026: 100 % des Vorschau-Verbrauchs
# kam aus diesem einen Selbstscan). Das Backend erkennt ihn an diesem Kopf.
# Fehlt das Geheimnis, bucht der Scan wie bisher auf den Vorschau-Topf — das ist
# der alte Zustand, kein Ausfall: der Waechter prueft weiter, nur die
# Kostenstelle stimmt dann nicht.
PROBESCAN_KOPF = "X-Complyo-Probescan"
PROBESCAN_TOKEN = (os.getenv("COMPLYO_PROBESCAN_TOKEN") or "").strip()


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
            kopfzeilen = (
                {PROBESCAN_KOPF: PROBESCAN_TOKEN} if PROBESCAN_TOKEN else {}
            )
            async with sitzung.post(
                ROUTEN_BASIS + "/api/analyze-preview",
                json={"url": PROBESCAN_ZIEL},
                headers=kopfzeilen,
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


def pruefe_bezahlweg() -> list:
    """Kann überhaupt jemand bezahlen?

    Seit dem Launch-Audit vom 31.08.2026 steht Stripe auf einem Testschlüssel.
    Das ist kein technischer Ausfall, deshalb fiel es keinem Wächter auf: alle
    Routen antworten, der Checkout öffnet sich, nur echte Karten werden
    abgelehnt. Elf Tage lang stand der Punkt auf einer Entscheidungsliste,
    die niemand täglich liest. Ein Geschäftssignal, das den Umsatz auf null
    hält, gehört in denselben Kanal wie ein kranker Container. Gemeldet wird
    einmal am Tag (ERNEUT_NACH_STUNDEN), nicht stündlich.
    """
    if os.getenv("ENVIRONMENT", "production") != "production":
        return []
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        return [("stripe-schluessel-fehlt",
                 "STRIPE_SECRET_KEY ist nicht gesetzt: kein Bezahlweg.")]
    if key.startswith("sk_test_"):
        return [("stripe-testmodus",
                 "Stripe läuft mit Testschlüssel (sk_test_): kein Kunde kann bezahlen. "
                 "Umschalten mit scripts/stripe-live-umschalten.py, Ablauf in "
                 "planning/STRIPE_LIVE_CHECKLISTE.md.")]
    return []


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
    try:
        befunde.extend(await pruefe_rechtsquellen())
    except Exception as e:
        befunde.append(("quellen-pruefung-abgestuerzt",
                        f"Pruefung der Rechtsquellen fehlgeschlagen: {e}"))
    try:
        befunde.extend(pruefe_datensicherung())
    except Exception as e:
        befunde.append(("sicherung-pruefung-abgestuerzt",
                        f"Prüfung der Datensicherung fehlgeschlagen: {e}"))
    befunde.extend(pruefe_host_signale())
    befunde.extend(pruefe_bezahlweg())

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
