"""
Laufzeit-Lizenzprüfung für eingebettete Widgets (Cookie-Banner & Barrierefreiheit).

Zwei Missbrauchswege werden abgedeckt:

1. **Lizenz entzogen** (`revoked`) — die Website wurde im Dashboard entfernt.
   Agenturen könnten sonst eine Seite anlegen, optimieren lassen und danach
   löschen, um das 25-Projekte-Limit zu umgehen und Banner/Widget kostenlos
   weiterzunutzen.

2. **Nicht lizenzierte Domain** (`unlicensed_domain`) — das Snippet läuft auf
   einer Domain, die dem Konto nicht zugeordnet ist. Der Pro-Tarif gilt für
   genau eine Domain; ein Wechsel läuft über den Support. Wer den Code
   stattdessen auf eine weitere Seite kopiert, nutzt ihn unlizenziert.

Erkannt wird die aufrufende Domain am `Origin`- bzw. `Referer`-Header. Beide
setzt der Browser selbst — Seiten-JavaScript kann sie nicht fälschen. Das ist
Vertragsdurchsetzung, keine Sicherheitsmaßnahme: Wer die Anfrage serverseitig
nachbaut, kommt daran vorbei. Für den Zweck genügt es.

Fail-open als Grundregel: Bei unbekannter/Legacy-Konfiguration, fehlenden
Headern oder DB-Fehlern gilt die Lizenz als aktiv. Eine falsch ausgelöste
Sperre auf einer zahlenden Kundenseite wäre teurer als ein übersehener
Verstoß.

Durchsetzungsgrad über `COMPLYO_LICENSE_ENFORCEMENT`:
  off   — keine Domainprüfung
  warn  — Verstoß wird protokolliert und ans Widget gemeldet, das Widget
          arbeitet aber normal weiter (Voreinstellung, gefahrloser Rollout)
  block — Widget stellt die Arbeit ein und zeigt den Verstoßhinweis

Wichtig: Der Fall `revoked` blockt unabhängig davon immer — das war schon
vorher so und soll nicht durch den neuen Schalter aufgeweicht werden.
"""
import logging
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_VALID_MODES = ("off", "warn", "block")


def _enforcement_mode() -> str:
    mode = (os.getenv("COMPLYO_LICENSE_ENFORCEMENT") or "warn").strip().lower()
    return mode if mode in _VALID_MODES else "warn"


# Wird dem Seitenbetreiber angezeigt. Bewusst konfigurierbar — der Text ist
# eine Vertragsaussage und gehoert dem Betreiber, nicht dem Code.
VIOLATION_MESSAGE = os.getenv(
    "COMPLYO_LICENSE_VIOLATION_TEXT",
    "Sie verwenden einen nicht lizenzierten Cookie-Banner und ein nicht "
    "lizenziertes Widget. Dies ist ein Verstoß gegen die Allgemeinen "
    "Geschäftsbedingungen.",
)

REVOKED_MESSAGE = (
    "Für dieses Cookie-Banner besteht keine aktive Lizenz. "
    "Bitte wenden Sie sich an Ihren Administrator."
)


def url_to_site_id(url: str) -> str:
    """
    Leitet die site_id aus einer URL ab — identisch zur Logik beim Anlegen einer
    Website (website_routes.py), damit gespeicherte und berechnete IDs matchen.
    """
    if not url:
        return ""
    raw = str(url).strip()
    parsed = urlparse(raw if raw.startswith("http") else f"https://{raw}")
    hostname = parsed.netloc or parsed.path
    hostname = hostname.split("/")[0].split(":")[0]  # Port und Pfad abschneiden
    hostname = hostname.replace("www.", "")
    return hostname.replace(".", "-").lower()


def host_from_request(request) -> str:
    """
    Domain der einbettenden Seite aus den Browser-Headern.

    `Origin` ist die verlässlichere Quelle; `Referer` springt ein, wenn der
    Browser kein Origin sendet (z. B. bei einfachen GET-Anfragen ohne CORS).
    Beide werden vom Browser gesetzt und sind aus der Seite heraus nicht
    manipulierbar.
    """
    if request is None:
        return ""
    try:
        headers = request.headers
    except AttributeError:
        return ""
    for key in ("origin", "referer"):
        value = headers.get(key)
        if value and value.lower() not in ("null", "undefined"):
            return value
    return ""


async def _licensed_site_ids(pool, site_id: str):
    """
    Alle site_ids, die zum Konto hinter dieser site_id gehören.

    Rückgabe `None` bedeutet: nicht ermittelbar (Legacy-Konfiguration, kein
    Owner, DB-Fehler) — der Aufrufer behandelt das als lizenziert.
    """
    try:
        cfg = await pool.fetchrow(
            "SELECT user_id FROM cookie_banner_configs WHERE site_id = $1 LIMIT 1",
            site_id,
        )
        if not cfg:
            # Bislang stiller Fail-open. Der WARN-Log schafft die
            # Entscheidungsgrundlage fuer enforcement=block: Erst wenn hier
            # ueber laengere Zeit keine legitimen Kunden mehr auftauchen,
            # darf der Schalter guten Gewissens umgelegt werden.
            logger.warning(
                "[Lizenz] unbekannte site_id %s: in keiner Config-Tabelle "
                "gefunden — fail-open, Widget bleibt aktiv",
                site_id,
            )
            return None
        if cfg["user_id"] is None:
            return None
        rows = await pool.fetch(
            "SELECT url FROM tracked_websites WHERE user_id = $1",
            cfg["user_id"],
        )
        return {url_to_site_id(r["url"]) for r in rows if r["url"]}
    except Exception as exc:
        logger.warning("[Lizenz] Konnte Lizenzumfang für %s nicht laden: %s", site_id, exc)
        return None


async def evaluate_license(pool, site_id: str, request=None) -> dict:
    """
    Bewertet die Lizenzlage für ein ausgeliefertes Widget.

    Rückgabe:
        status    — 'active' | 'revoked' | 'unlicensed_domain'
        enforced  — True, wenn das Widget die Arbeit einstellen soll
        active    — rückwärtskompatibles Gegenstück zu `enforced`
        message   — Text für den Seitenbetreiber (None bei 'active')
    """
    ok = {"status": "active", "enforced": False, "active": True, "message": None}

    if pool is None or not site_id:
        return ok

    licensed = await _licensed_site_ids(pool, site_id)
    if licensed is None:
        return ok

    # Fall 1: Website wurde im Dashboard entfernt → blockt immer.
    if site_id not in licensed:
        logger.warning("[Lizenz] Entzogen: site_id=%s ist keinem Konto mehr zugeordnet", site_id)
        return {
            "status": "revoked",
            "enforced": True,
            "active": False,
            "message": REVOKED_MESSAGE,
        }

    # Fall 2: Snippet läuft auf einer fremden Domain.
    mode = _enforcement_mode()
    if mode == "off":
        return ok

    host = host_from_request(request)
    if not host:
        return ok  # ohne Header keine Aussage möglich → fail-open

    host_id = url_to_site_id(host)
    if not host_id or host_id in licensed:
        return ok

    logger.warning(
        "[Lizenz] Nicht lizenzierte Domain: snippet von site_id=%s laeuft auf %s "
        "(lizenziert: %s) — Modus %s",
        site_id, host_id, sorted(licensed), mode,
    )
    return {
        "status": "unlicensed_domain",
        "enforced": mode == "block",
        "active": mode != "block",
        "message": VIOLATION_MESSAGE,
    }


async def site_has_active_license(pool, site_id: str) -> bool:
    """Rückwärtskompatible Kurzform ohne Domainprüfung."""
    result = await evaluate_license(pool, site_id, request=None)
    return result["active"]
