"""
Ein Abrufweg fuer alles, was der Scanner auf fremden Servern anfasst.

Hintergrund (Sicherheitsreview 2026-08-31): `ssrf_protection.validate_url` stand
an der Haustuer, also an den Routen, aber an keinem Schritt danach. Vier Stellen
holten mit eigener aiohttp-Logik und `allow_redirects=True` Daten, deren Adresse
aus der GEPRUEFTEN Seite stammt und die damit jemand frei setzt:

- page_discovery liest die robots.txt und folgt jeder `Sitemap:`-Zeile
- scanner._fetch_page folgt Umleitungen der Startseite
- declarative_check_runner prueft Kandidatenpfade
- der KI-Bildnachweis laedt die Bilder der Seite

Damit liess sich complyo dazu bringen, aus dem internen Docker-Netz heraus
beliebige Adressen abzurufen (`Sitemap: http://169.254.169.254/...`).

Dieses Modul buendelt den Abruf an EINER Stelle und prueft JEDE Station der
Umleitungskette einzeln. Umleitungen werden bewusst selbst verfolgt: mit
`allow_redirects=True` fuehrt aiohttp sie aus, bevor irgendjemand sie sehen
kann, und eine Pruefung der Ausgangsadresse laeuft ins Leere.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp

from ssrf_protection import validate_url, SSRFError, pruefe_adresse

logger = logging.getLogger(__name__)

# Mehr Stationen braucht kein legitimer Server; jede weitere ist ein Umweg,
# der nur Prueflast erzeugt.
MAX_UMLEITUNGEN = 3
UMLEITUNGS_CODES = (301, 302, 303, 307, 308)


@dataclass
class Abruf:
    """Ergebnis eines Abrufs. Nur Daten, keine offene Verbindung."""

    status: int
    url: str                      # endgueltige Adresse nach allen Umleitungen
    headers: Dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    @property
    def content_type(self) -> str:
        return (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()

    def text(self) -> str:
        """Koerper als Text. Kaputte Kodierung darf keinen Scan abbrechen."""
        return self.body.decode("utf-8", errors="replace")


async def hole(
    session: Optional[aiohttp.ClientSession],
    url: str,
    *,
    timeout: Optional[int] = None,
    max_bytes: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
    max_umleitungen: int = MAX_UMLEITUNGEN,
) -> Optional[Abruf]:
    """
    Holt eine fremde Adresse, jede Station einzeln geprueft.

    Gibt None zurueck, wenn die Adresse gesperrt ist, die Verbindung scheitert
    oder die Umleitungskette zu lang wird. Ein Fehlerstatus (4xx/5xx) ist KEIN
    None: der Scanner unterscheidet "nicht erreichbar" von "antwortet mit 404",
    und diese Unterscheidung geht sonst verloren.

    max_bytes begrenzt den gelesenen Koerper. None liest ihn vollstaendig.
    """
    eigene = session is None
    if eigene:
        session = aiohttp.ClientSession()
    try:
        for _ in range(max_umleitungen + 1):
            try:
                validate_url(url)
            except SSRFError as e:
                logger.info(f"Abruf gesperrt ({e}): {url}")
                return None

            anfrage: Dict[str, Any] = {"allow_redirects": False}
            if headers:
                anfrage["headers"] = headers
            if timeout is not None:
                anfrage["timeout"] = aiohttp.ClientTimeout(total=timeout)

            async with session.get(url, **anfrage) as antwort:
                ziel = antwort.headers.get("Location")
                if antwort.status in UMLEITUNGS_CODES and ziel:
                    url = urljoin(url, ziel)
                    continue
                koerper = (
                    await antwort.content.read(max_bytes) if max_bytes
                    else await antwort.read()
                )
                return Abruf(
                    status=antwort.status,
                    url=str(antwort.url),
                    headers=dict(antwort.headers),
                    body=koerper,
                )

        logger.info(f"Abruf abgebrochen, mehr als {max_umleitungen} Umleitungen: {url}")
        return None
    except Exception as e:
        logger.debug(f"Abruf fehlgeschlagen {url}: {e}")
        return None
    finally:
        if eigene:
            await session.close()


# ---------------------------------------------------------------------------
# Die Schranke am Verbindungsaufbau
# ---------------------------------------------------------------------------
#
# `hole` prueft jede Adresse, bevor sie geholt wird. Das genuegt fuer den
# Abrufweg dieses Moduls, aber der Scanner hat rund zwanzig Stellen, die sich
# selbst eine Sitzung bauen und `session.get(..., allow_redirects=True)`
# rufen - Impressum, Datenschutz, AGB, Shop, der Bilddownload des
# Alt-Text-Generators. Deren Adressen stammen aus der geprueften Seite.
#
# Zwei Loecher bleiben selbst bei sauberer Adresspruefung:
#   1. aiohttp folgt Umleitungen selbst; das Ziel sieht niemand vorher.
#   2. Zwischen Pruefung und Verbindung darf derselbe Name auf eine andere
#      Adresse zeigen (DNS-Rebinding).
#
# Beides schliesst nur eine Pruefung im Augenblick des Verbindungsaufbaus.
# Genau das tut dieser Connector: er prueft JEDE aufgeloeste Adresse, egal ob
# sie aus der ersten Anfrage, aus einer Umleitung oder aus einer zweiten
# Namensaufloesung stammt.


class GepruefterConnector(aiohttp.TCPConnector):
    """TCPConnector, der keine Verbindung zu einer internen Adresse aufbaut."""

    async def _resolve_host(self, host, port, traces=None):
        hosts = await super()._resolve_host(host, port, traces)
        for eintrag in hosts:
            adresse = eintrag.get("host")
            if not adresse:
                continue
            try:
                pruefe_adresse(adresse)
            except SSRFError as e:
                logger.info(f"Verbindung gesperrt ({e}): {host} -> {adresse}")
                raise SSRFError(f"{host} zeigt auf eine interne Adresse") from None
        return hosts


def sichere_session(**kwargs) -> aiohttp.ClientSession:
    """
    Eine aiohttp-Sitzung, die keine internen Adressen erreicht.

    Ersetzt `aiohttp.ClientSession(...)` ueberall dort, wo die Adresse aus
    einer fremden Seite stammen kann. Ein uebergebener `connector` wird
    bewusst NICHT uebernommen: er waere genau die Luecke, die dieser Weg
    schliesst. Ein `ssl=`-Argument wird an den geprueften Connector
    weitergereicht, weil mehrere Aufrufer eigene SSL-Zusammenhaenge setzen.
    """
    ssl_wert = kwargs.pop("ssl", None)
    alter = kwargs.pop("connector", None)
    if alter is not None and ssl_wert is None:
        # Die Aufrufer bauten sich bisher einen TCPConnector nur, um ihren
        # SSL-Zusammenhang zu setzen. Den uebernehmen wir; der Connector selbst
        # wird verworfen (ungenutzt, also ohne Verbindungen - aiohttp raeumt
        # ihn still ab), denn er waere die Luecke, die dieser Weg schliesst.
        ssl_wert = getattr(alter, "_ssl", None)
    connector_args = {}
    if ssl_wert is not None:
        connector_args["ssl"] = ssl_wert
    for name in ("limit", "limit_per_host", "ttl_dns_cache", "force_close"):
        if name in kwargs:
            connector_args[name] = kwargs.pop(name)
    # Ohne DNS-Zwischenspeicher: ein zwischengespeicherter Eintrag umginge die
    # Pruefung nicht (sie sitzt hinter dem Cache), aber kurze Lebensdauer haelt
    # den Scanner naeher an der Wirklichkeit der geprueften Seite.
    connector_args.setdefault("ttl_dns_cache", 30)
    kwargs["connector"] = GepruefterConnector(**connector_args)
    return aiohttp.ClientSession(**kwargs)
