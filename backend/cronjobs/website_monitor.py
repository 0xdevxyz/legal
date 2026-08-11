#!/usr/bin/env python3
"""
Website-Monitoring
==================
Laeuft taeglich und beantwortet fuer jede beobachtete Website eine Frage:
**hat sich etwas geaendert, das die Rechtslage beruehrt?**

Warum nicht einfach jede Nacht alles neu scannen: Ein Vollscan kostet
Browser-Rendering, axe-core und KI-Aufrufe. Bei 1.000 beobachteten Domains
waeren das 30.000 Vollscans im Monat — bei einem Monatspreis im niedrigen
zweistelligen Bereich rechnet sich das nicht, und die allermeisten Scans
faenden exakt dasselbe wie am Vortag.

Deshalb zwei Stufen:

  1. LEICHTER CHECK (taeglich, Kosten nahe null)
     Startseite und Pflichtseiten abrufen, Fingerabdruck der rechtlich
     relevanten Teile bilden. Aendert sich nichts, ist nichts zu tun.

  2. VOLLSCAN (nur wenn noetig)
     - der Fingerabdruck hat sich geaendert (Seite wurde angefasst)
     - die eingestellte Frequenz ist faellig (weekly/monthly)
     - `rescan_required` ist gesetzt (neue Rechtslage; setzt der
       Legal-Change-Monitor)

Verschlechtert sich der Score oder kommt ein kritischer Befund dazu, wird eine
Benachrichtigung geschrieben. Genau das ist der Wert fuer den Kunden: nicht
"wir scannen taeglich", sondern "wir melden uns, wenn etwas kaputtgeht".
"""

import asyncio
import hashlib
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from bs4 import BeautifulSoup

_log_handlers = [logging.StreamHandler()]
try:
    _log_handlers.append(logging.FileHandler("/var/log/complyo-website-monitor.log", mode="a"))
except OSError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_log_handlers,
)
logger = logging.getLogger("website_monitor")

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Wie oft ein Vollscan spaetestens faellig wird, auch ohne erkannte Aenderung.
FREQUENZ_TAGE = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
}
FREQUENZ_STANDARD = 7

# Gleichzeitige Vollscans. Bewusst niedrig: die Scans laufen gegen fremde
# Server und teilen sich einen Browser.
PARALLELE_SCANS = 3

# Ab wieviel Punkten Verschlechterung benachrichtigt wird. Kleine Schwankungen
# (z.B. ein zusaetzliches Deko-Bild ohne Alt-Text) sollen niemanden wecken.
SCHWELLE_VERSCHLECHTERUNG = 5


def _fingerabdruck(html: str) -> str:
    """
    Fingerabdruck der rechtlich relevanten Seitenteile.

    Bewusst NICHT der ganze HTML-Hash: der aendert sich bei jedem Cache-Buster,
    jedem Zufalls-Token und jedem rotierenden Werbebanner — dann waere jeder
    Tag ein Vollscan und die Ersparnis dahin. Betrachtet werden die Teile, an
    denen sich Compliance ueberhaupt aendern kann.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return hashlib.sha256(html.encode("utf-8", "replace")).hexdigest()

    teile: List[str] = []

    # eingebundene Skripte (Tracker!) — nur Host+Pfad, ohne Query
    for tag in soup.find_all("script", src=True):
        src = tag["src"].split("?")[0]
        teile.append(f"script:{src}")

    # Formulare: Anzahl Felder und Ziel
    for form in soup.find_all("form"):
        felder = len(form.find_all(["input", "select", "textarea"]))
        teile.append(f"form:{form.get('action', '')}:{felder}")

    # Links auf Pflichtseiten
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        for wort in ("impressum", "datenschutz", "agb", "widerruf", "cookie", "barrierefrei"):
            if wort in href:
                teile.append(f"link:{wort}")
                break

    # Bilder ohne Alt-Text (Anzahl) und iframes (Einbettungen)
    ohne_alt = sum(1 for img in soup.find_all("img") if not (img.get("alt") or "").strip())
    teile.append(f"img_ohne_alt:{ohne_alt}")
    teile.append(f"iframes:{len(soup.find_all('iframe'))}")

    # sichtbarer Text, grob — faengt geaenderte Rechtstexte
    text = " ".join((soup.get_text(separator=" ") or "").split())
    teile.append(f"textlen:{len(text) // 100}")

    roh = "|".join(sorted(teile))
    return hashlib.sha256(roh.encode("utf-8", "replace")).hexdigest()


async def _hole(url: str, timeout: int = 15) -> Optional[str]:
    import aiohttp
    import ssl as _ssl
    import certifi

    ctx = _ssl.create_default_context(cafile=certifi.where())
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ctx)) as s:
            async with s.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={"User-Agent": "Mozilla/5.0 (compatible; ComplyoMonitor/1.0)"},
                allow_redirects=True,
            ) as r:
                if r.status >= 400:
                    return None
                return await r.text()
    except Exception as e:
        logger.info(f"   nicht abrufbar: {url} ({type(e).__name__})")
        return None


def _vollscan_noetig(site: dict, neuer_abdruck: Optional[str]) -> "tuple[bool, str]":
    """Entscheidet, ob ein Vollscan laufen muss — und nennt den Grund."""
    if site.get("rescan_required"):
        return True, f"neue Rechtslage ({site.get('rescan_reason') or 'Rescan angefordert'})"

    letzter = site.get("last_scan_date")
    if not letzter:
        return True, "noch nie geprüft"

    tage = FREQUENZ_TAGE.get((site.get("scan_frequency") or "").lower(), FREQUENZ_STANDARD)
    if datetime.utcnow() - letzter >= timedelta(days=tage):
        return True, f"turnusmäßig fällig ({site.get('scan_frequency') or 'weekly'})"

    alter_abdruck = (site.get("content_fingerprint") or "")
    if neuer_abdruck and alter_abdruck and neuer_abdruck != alter_abdruck:
        return True, "Seiteninhalt hat sich geändert"

    if neuer_abdruck and not alter_abdruck:
        return True, "erster Fingerabdruck"

    return False, "unverändert"


async def _scanne(url: str, budget: int) -> Optional[dict]:
    from compliance_engine.scanner import ComplianceScanner

    try:
        async with ComplianceScanner() as scanner:
            return await scanner.scan_website_multipage(url, max_seiten=budget)
    except Exception as e:
        logger.warning(f"   Scan fehlgeschlagen für {url}: {type(e).__name__}: {e}")
        return None


async def _benachrichtige(conn, site: dict, alt: Optional[float], neu: float, kritisch: int):
    """
    Schreibt eine Benachrichtigung — aber nur, wenn es etwas zu sagen gibt.

    Erster Testlauf als Warnung: zua-zwickau.de bekam eine Meldung bei
    28 -> 68 — einer VERBESSERUNG — weil "kritische Befunde vorhanden" als
    Ausloeser galt. Gemeldet wird jetzt nur, was schlechter wurde: Score-Sturz
    oder MEHR kritische Befunde als beim letzten Scan. Eine Meldung "alles wie
    gestern" ist keine Information, sondern Rauschen, das Nutzer abschalten
    laesst.
    """
    if not site.get("notification_enabled", True):
        return
    if alt is None:
        return

    verschlechtert = (alt - neu) >= SCHWELLE_VERSCHLECHTERUNG

    kritisch_gestiegen = False
    if kritisch > 0:
        try:
            # Audit 11.08.: vorher `WHERE website_id = $1 ORDER BY scan_date`
            # — scan_history.website_id war in allen Zeilen NULL (uuid-vs-int-
            # Drift) und die Spalte heißt scan_timestamp; die Query warf immer
            # und der Alarm blieb still. Jetzt zusätzlich über user_id+url
            # joinen. Kein OFFSET: dieser Cron schreibt selbst kein
            # scan_history, die neueste Zeile IST der letzte erfasste Scan.
            vorher = await conn.fetchval(
                """
                SELECT critical_issues FROM scan_history
                WHERE website_id = $1 OR (user_id = $2 AND url = $3)
                ORDER BY scan_timestamp DESC LIMIT 1
                """,
                site["id"], site["user_id"], site["url"],
            )
            kritisch_gestiegen = vorher is not None and kritisch > vorher
        except Exception:
            # Kein Verlauf auffindbar -> lieber still bleiben als falsch alarmieren
            kritisch_gestiegen = False

    if not verschlechtert and not kritisch_gestiegen:
        return

    try:
        await conn.execute(
            """
            INSERT INTO user_legal_notifications
                (user_id, website_id, notification_type, created_at)
            VALUES ($1, $2, $3, now())
            """,
            site["user_id"],
            site["id"],
            "score_drop" if verschlechtert else "critical_increase",
        )
        logger.info(
            f"   Benachrichtigung: {site['url']} {alt:.0f} → {neu:.0f} "
            f"({kritisch} kritisch)"
        )
    except Exception as e:
        # Nie den ganzen Lauf an einer Benachrichtigung scheitern lassen.
        logger.warning(f"   Benachrichtigung fehlgeschlagen: {e}")


async def main():
    if not DATABASE_URL:
        logger.error("DATABASE_URL fehlt — Abbruch")
        return 1

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    gescannt = geprueft = uebersprungen = 0

    try:
        async with pool.acquire() as conn:
            # Spalte fuer den Fingerabdruck bei Bedarf anlegen — der Job soll
            # ohne separaten Migrationsschritt lauffaehig sein.
            await conn.execute(
                "ALTER TABLE tracked_websites "
                "ADD COLUMN IF NOT EXISTS content_fingerprint TEXT"
            )
            await conn.execute(
                "ALTER TABLE tracked_websites "
                "ADD COLUMN IF NOT EXISTS last_check_date TIMESTAMP"
            )
            sites = await conn.fetch(
                """
                SELECT id, url, user_id, scan_frequency, notification_enabled,
                       last_scan_date, last_score, rescan_required, rescan_reason,
                       content_fingerprint
                FROM tracked_websites
                WHERE status = 'active'
                ORDER BY COALESCE(last_scan_date, '1970-01-01'::timestamp) ASC
                """
            )

        logger.info(f"Website-Monitoring: {len(sites)} beobachtete Website(s)")
        semaphor = asyncio.Semaphore(PARALLELE_SCANS)

        async def eine(row):
            nonlocal gescannt, geprueft, uebersprungen
            site = dict(row)
            url = site["url"]
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            geprueft += 1
            html = await _hole(url)
            abdruck = _fingerabdruck(html) if html else None

            noetig, grund = _vollscan_noetig(site, abdruck)
            if not noetig:
                uebersprungen += 1
                logger.info(f"   {url}: {grund} — kein Vollscan")
                async with pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE tracked_websites SET last_check_date = now() WHERE id = $1",
                        site["id"],
                    )
                return

            logger.info(f"   {url}: {grund} → Vollscan")
            async with semaphor:
                ergebnis = await _scanne(url, budget=10)
            if not ergebnis:
                return

            gescannt += 1
            score = ergebnis.get("overall_score") or ergebnis.get("compliance_score") or 0
            kritisch = ergebnis.get("critical_issues", 0)
            alt = site.get("last_score")

            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE tracked_websites
                    SET last_score = $2, last_scan_date = now(), last_check_date = now(),
                        content_fingerprint = COALESCE($3, content_fingerprint),
                        scan_count = COALESCE(scan_count, 0) + 1,
                        rescan_required = FALSE, updated_at = now()
                    WHERE id = $1
                    """,
                    site["id"], float(score), abdruck,
                )
                try:
                    # Auf das Ziel-Dict-Format normalisieren (Spiegel von
                    # main_production): der Scanner liefert die Listenform
                    # [{pillar, score, status}], score_history soll aber
                    # einheitlich das Dict inkl. critical_issues tragen.
                    _liste = ergebnis.get("pillar_scores") or []
                    _by = {p.get("pillar"): p.get("score", 0)
                           for p in _liste if isinstance(p, dict)}
                    _pillar_dict = {
                        "accessibility": _by.get("accessibility", 0),
                        "gdpr": _by.get("gdpr", 0),
                        "legal": _by.get("legal", 0),
                        "cookies": _by.get("cookies", 0),
                        "critical_issues": int(kritisch or 0),
                    }
                    await conn.execute(
                        """
                        INSERT INTO score_history (website_id, user_id, overall_score, pillar_scores)
                        VALUES ($1, $2, $3, $4)
                        """,
                        site["id"], site["user_id"], float(score),
                        __import__("json").dumps(_pillar_dict),
                    )
                except Exception as e:
                    logger.warning(f"   Score-Verlauf nicht geschrieben: {e}")

                await _benachrichtige(conn, site, alt, float(score), kritisch)

        await asyncio.gather(*[eine(r) for r in sites], return_exceptions=True)

        logger.info(
            f"Fertig: {geprueft} geprüft, {gescannt} vollgescannt, "
            f"{uebersprungen} unverändert übersprungen"
        )
        return 0
    finally:
        await pool.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
