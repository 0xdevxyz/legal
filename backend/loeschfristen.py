"""
Löschfristen — was wie lange bleibt.

Anlass (Prüfung 10.09.2026): automatisch gelöscht wurden ausschliesslich Leads
nach 730 Tagen. Für Scan-Verläufe, Einwilligungsprotokolle,
Wirksamkeitsmeldungen, Auslieferungsprotokolle und Konten nach dem Ende des
Vertrages gab es keine Frist — obwohl die eigene Datenschutzerklärung und
§ 7 des AVV Löschung zusagen. Eine zugesagte Frist ohne Mechanismus ist eine
Falschangabe, keine Lücke.

Die Fristen stehen hier als Daten, nicht als Code über die Tabellen verstreut.
Wer wissen will, wie lange complyo etwas aufhebt, liest diese eine Liste —
und die Datenschutzerklärung kann daraus erzeugt statt danebengeschrieben
werden.

Zwei Klassen von Regeln
-----------------------
`SOFORT` läuft ohne Zutun: Zwischenspeicher, Einmal-Nonces, Betriebstelemetrie.
Da ist Löschen der Normalfall und Aufheben die Ausnahme.

`GESCHUETZT` fasst an, was als Nachweis dient — Einwilligungen, Scan-Verläufe,
Auslieferungsprotokolle — und läuft nur, wenn `LOESCHFRISTEN_SCHARF=ja`
gesetzt ist. Grund: diese Zeilen sind der Beleg, mit dem sich complyo und seine
Kunden im Streitfall verteidigen. Eine Frist, die man aus Versehen zu kurz
gesetzt hat, vernichtet genau den Nachweis, den man aufheben wollte. Der
Schalter zwingt dazu, den Trockenlauf einmal gelesen zu haben.

Kontolöschung
-------------
Ein Konto ohne Anmeldung und ohne Scan seit 36 Monaten hat keinen Zweck mehr,
der die Speicherung trägt (Art. 5 Abs. 1 lit. e). Gelöscht wird nicht sofort:
erst eine Ankündigung per Mail, dann 30 Tage Frist. Konten mit laufendem
Abonnement sind ausgenommen — dort besteht ein Vertrag, unabhängig davon, wann
sich jemand zuletzt angemeldet hat.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SCHARF = (os.getenv("LOESCHFRISTEN_SCHARF", "nein").strip().lower()
          in ("ja", "yes", "true", "1"))

# Konten ohne Anmeldung und ohne Scan werden nach dieser Zeit angekündigt …
KONTO_RUHEND_TAGE = int(os.getenv("LOESCHFRISTEN_KONTO_RUHEND_TAGE", "1095"))  # 36 Monate
# … und diese Frist nach der Ankündigung gelöscht.
KONTO_ANKUENDIGUNG_TAGE = int(os.getenv("LOESCHFRISTEN_KONTO_FRIST_TAGE", "30"))


@dataclass(frozen=True)
class Frist:
    """Eine Löschregel. `bedingung` ist zusätzliches SQL ohne führendes AND."""

    tabelle: str
    spalte: str
    tage: int
    zweck: str
    grundlage: str
    geschuetzt: bool = False
    bedingung: Optional[str] = None

    @property
    def monate(self) -> int:
        return round(self.tage / 30.44)

    def sql(self) -> str:
        wo = f"{self.spalte} < NOW() - INTERVAL '{self.tage} days'"
        if self.bedingung:
            wo += f" AND ({self.bedingung})"
        return f"DELETE FROM {self.tabelle} WHERE {wo}"

    def zaehl_sql(self) -> str:
        wo = f"{self.spalte} < NOW() - INTERVAL '{self.tage} days'"
        if self.bedingung:
            wo += f" AND ({self.bedingung})"
        return f"SELECT COUNT(*) FROM {self.tabelle} WHERE {wo}"


FRISTEN: List[Frist] = [
    # -----------------------------------------------------------------------
    # Ohne Schalter: Zwischenspeicher, Nonces, Telemetrie
    # -----------------------------------------------------------------------
    Frist(
        "geo_ip_cache", "cached_at", 30,
        zweck="Zwischenspeicher der Länderzuordnung zu IP-Hashes",
        grundlage="Art. 6 Abs. 1 lit. f — reiner Cache, jederzeit neu bildbar",
    ),
    Frist(
        "oauth_states", "created_at", 1,
        zweck="Einmal-Nonce des OAuth-Rückwegs",
        grundlage="nach Sekunden verbraucht; alles darüber ist Restmüll",
    ),
    Frist(
        "widget_events", "created_at", 90,
        zweck="Betriebstelemetrie des Widgets (Seitenaufruf, Fehlerbild)",
        grundlage="Art. 6 Abs. 1 lit. f — Fehlersuche, kein Personenbezug",
    ),
    Frist(
        "accessibility_wirkung", "zuletzt", 180,
        zweck="Wirksamkeitsmeldung je Pfad — angewendet, verfehlt, Aufrufe",
        grundlage="Art. 6 Abs. 1 lit. b — Regressionswarnung; ältere Zeilen "
                  "beschreiben eine Seite, die es so nicht mehr gibt",
    ),
    Frist(
        "deep_scan_history", "created_at", 365,
        zweck="Ereignisprotokoll des Tiefenscans",
        grundlage="Art. 6 Abs. 1 lit. b — Ablaufkontrolle des Auftrags",
    ),
    Frist(
        "cookie_ab_assignments", "assigned_at", 365,
        zweck="Zuordnung Besucher-Hash zu Banner-Variante",
        grundlage="Art. 6 Abs. 1 lit. f — Auswertung endet mit dem Test",
    ),
    Frist(
        # Ohne Bestätigung fehlt die Einwilligung. Ohne Einwilligung gibt es
        # keine Rechtsgrundlage, die Adresse überhaupt zu behalten — der
        # unbestätigte Eintrag ist der Fall, in dem Löschen die Pflicht ist.
        "waitlist_leads", "created_at", 30,
        zweck="Warteliste ohne abgeschlossenes Double-Opt-In",
        grundlage="Art. 6 Abs. 1 lit. a — Einwilligung nie erteilt",
        bedingung="confirmed_at IS NULL",
    ),

    # -----------------------------------------------------------------------
    # Nur mit LOESCHFRISTEN_SCHARF=ja: Nachweise und Vertragsdaten
    # -----------------------------------------------------------------------
    Frist(
        # Nur abgelaufene Einwilligungen. Eine noch gültige zu löschen hiesse,
        # den Nachweis für eine Verarbeitung wegzuwerfen, die gerade läuft.
        "cookie_consent_logs", "timestamp", 1095,
        zweck="Nachweis der Einwilligung des Websitebesuchers",
        grundlage="Art. 7 Abs. 1 — Nachweispflicht, dazu die regelmässige "
                  "Verjährung von drei Jahren (§ 195 BGB)",
        geschuetzt=True,
        bedingung="expires_at IS NULL OR expires_at < NOW()",
    ),
    Frist(
        "scan_history", "created_at", 730,
        zweck="Prüfergebnisse der Kundenwebsite",
        grundlage="Art. 6 Abs. 1 lit. b — Vertragsleistung und Verlaufskurve",
        geschuetzt=True,
    ),
    Frist(
        "score_history", "created_at", 730,
        zweck="Punktestand je Website über die Zeit",
        grundlage="Art. 6 Abs. 1 lit. b",
        geschuetzt=True,
    ),
    Frist(
        "accessibility_wirkungsscan", "gemessen_am", 730,
        zweck="Vorher/Nachher-Messung für den Prüfnachweis",
        grundlage="Art. 6 Abs. 1 lit. b — Beleg gegenüber Prüfstellen",
        geschuetzt=True,
    ),
    Frist(
        "fix_application_audit", "applied_at", 1095,
        zweck="Wer hat wann welche Reparatur auf welcher Website ausgeliefert",
        grundlage="Haftungsnachweis; Verjährung drei Jahre (§ 195 BGB)",
        geschuetzt=True,
    ),
    Frist(
        "communication_log", "created_at", 1095,
        zweck="Versandte Nachrichten an Interessenten",
        grundlage="§ 195 BGB",
        geschuetzt=True,
    ),
    Frist(
        "user_journeys", "updated_at", 730,
        zweck="Fortschritt im Einrichtungsweg",
        grundlage="Art. 6 Abs. 1 lit. b",
        geschuetzt=True,
    ),
]


async def _protokolliere(conn, lauf: str, regel: str, tabelle: str,
                         anzahl: int, ausgefuehrt: bool, grundlage: str) -> None:
    """
    Jede Entscheidung wird festgehalten — auch die, nichts zu tun.

    Art. 5 Abs. 2 verlangt, die Einhaltung nachweisen zu können. Ein
    Löschlauf, von dem nur die Wirkung übrig ist, weist nichts nach: die
    gelöschten Zeilen sind ja gerade weg.
    """
    await conn.execute(
        """
        INSERT INTO loeschprotokoll
            (lauf, regel, tabelle, anzahl, ausgefuehrt, grundlage, zeitpunkt)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """,
        lauf, regel, tabelle, anzahl, ausgefuehrt, grundlage,
    )


async def _tabelle_vorhanden(conn, tabelle: str) -> bool:
    return bool(await conn.fetchval(
        "SELECT to_regclass($1) IS NOT NULL", f"public.{tabelle}"
    ))


async def wende_fristen_an(pool, trocken: bool = False) -> Dict[str, Any]:
    """
    Führt alle Fristen aus. `trocken=True` zählt nur und löscht nichts.

    Rückgabe ist der Bericht, den der Cron ins Log schreibt und den der
    Betriebswächter lesen kann.
    """
    lauf = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bericht: Dict[str, Any] = {
        "lauf": lauf,
        "trocken": trocken,
        "scharf": SCHARF,
        "regeln": [],
        "geloescht_gesamt": 0,
        "uebersprungen": 0,
        "fehler": [],
    }

    async with pool.acquire() as conn:
        for frist in FRISTEN:
            if not await _tabelle_vorhanden(conn, frist.tabelle):
                # Kein Fehler: das Schema wächst, und eine Regel für eine
                # Tabelle, die es noch nicht gibt, ist ein Vorgriff, kein Bruch.
                logger.info("Löschfrist übersprungen, Tabelle fehlt: %s", frist.tabelle)
                continue

            darf = (not frist.geschuetzt) or SCHARF
            try:
                betroffen = int(await conn.fetchval(frist.zaehl_sql()) or 0)
            except Exception as e:
                logger.error("Löschfrist %s nicht zählbar: %s", frist.tabelle, e)
                bericht["fehler"].append(f"{frist.tabelle}: {e}")
                continue

            ausgefuehrt = False
            if betroffen and darf and not trocken:
                try:
                    await conn.execute(frist.sql())
                    ausgefuehrt = True
                    bericht["geloescht_gesamt"] += betroffen
                except Exception as e:
                    logger.error("Löschfrist %s fehlgeschlagen: %s", frist.tabelle, e)
                    bericht["fehler"].append(f"{frist.tabelle}: {e}")
                    continue
            elif betroffen and not darf:
                bericht["uebersprungen"] += betroffen

            bericht["regeln"].append({
                "tabelle": frist.tabelle,
                "tage": frist.tage,
                "betroffen": betroffen,
                "ausgefuehrt": ausgefuehrt,
                "geschuetzt": frist.geschuetzt,
                "gesperrt": bool(betroffen and not darf),
            })

            if betroffen:
                await _protokolliere(
                    conn, lauf, f"{frist.tabelle}/{frist.tage}d", frist.tabelle,
                    betroffen, ausgefuehrt, frist.grundlage,
                )

    return bericht


# ---------------------------------------------------------------------------
# Ruhende Konten
# ---------------------------------------------------------------------------

_RUHEND_SQL = f"""
SELECT u.id, u.email, u.full_name, u.created_at, u.loeschung_angekuendigt_am
FROM users u
WHERE u.is_active = TRUE
  AND u.role <> 'admin'
  AND u.created_at < NOW() - INTERVAL '{KONTO_RUHEND_TAGE} days'
  AND NOT EXISTS (
        SELECT 1 FROM subscriptions s
        WHERE s.user_id = u.id AND s.status IN ('active', 'trialing', 'past_due')
      )
  AND NOT EXISTS (
        SELECT 1 FROM user_sessions ses
        WHERE ses.user_id = u.id
          AND ses.created_at > NOW() - INTERVAL '{KONTO_RUHEND_TAGE} days'
      )
  AND NOT EXISTS (
        SELECT 1 FROM scan_history sh
        WHERE sh.user_id = u.id
          AND sh.created_at > NOW() - INTERVAL '{KONTO_RUHEND_TAGE} days'
      )
"""


async def finde_ruhende_konten(pool) -> List[Dict[str, Any]]:
    async with pool.acquire() as conn:
        zeilen = await conn.fetch(_RUHEND_SQL)
    return [dict(z) for z in zeilen]


async def kuendige_loeschung_an(pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET loeschung_angekuendigt_am = NOW() WHERE id = $1",
            user_id,
        )


async def faellige_konten(pool) -> List[Dict[str, Any]]:
    """
    Konten, deren angekündigte Frist abgelaufen ist.

    Die Ankündigung wird beim nächsten Anmelden zurückgesetzt (siehe
    auth_routes.login) — wer sich meldet, ist nicht ruhend.
    """
    async with pool.acquire() as conn:
        zeilen = await conn.fetch(
            f"""
            SELECT id, email, full_name FROM users
            WHERE is_active = TRUE
              AND role <> 'admin'
              AND loeschung_angekuendigt_am IS NOT NULL
              AND loeschung_angekuendigt_am < NOW() - INTERVAL '{KONTO_ANKUENDIGUNG_TAGE} days'
            """
        )
    return [dict(z) for z in zeilen]


def als_text(bericht: Dict[str, Any]) -> str:
    """Der Bericht als Klartext fürs Log und für die Mail."""
    zeilen = [
        f"Löschlauf {bericht['lauf']}"
        f"{' (Trockenlauf)' if bericht['trocken'] else ''}"
        f" — scharf: {'ja' if bericht['scharf'] else 'nein'}",
    ]
    for regel in bericht["regeln"]:
        if not regel["betroffen"]:
            continue
        stand = "gelöscht" if regel["ausgefuehrt"] else (
            "GESPERRT (LOESCHFRISTEN_SCHARF fehlt)" if regel["gesperrt"] else "nur gezählt"
        )
        zeilen.append(
            f"  {regel['tabelle']}: {regel['betroffen']} Zeilen älter als "
            f"{regel['tage']} Tage — {stand}"
        )
    if not any(r["betroffen"] for r in bericht["regeln"]):
        zeilen.append("  keine Zeile über der Frist")
    if bericht["fehler"]:
        zeilen.append("  Fehler: " + "; ".join(bericht["fehler"]))
    return "\n".join(zeilen)
