"""
Laufzeit-Lizenzprüfung für eingebettete Widgets (Cookie-Banner & Barrierefreiheit).

Hintergrund: Agenturen könnten eine Website anlegen, optimieren lassen und dann
wieder aus dem Dashboard entfernen, um das 25-Projekte-Limit zu umgehen und den
funktionierenden Banner/Widget kostenlos weiterzunutzen. Statt das Löschen zu
sperren, erzwingen wir die Lizenz am ausgelieferten Artefakt: Sobald die
zugehörige `tracked_websites`-Zeile fehlt, gilt die Lizenz als entzogen — der
Banner zeigt einen Hinweis, das Barrierefreiheits-Widget funktioniert nicht mehr.

Fail-open: Bei unbekannter/Legacy-Konfiguration oder DB-Fehlern wird die Lizenz
als aktiv behandelt, damit echte Kundenseiten niemals fälschlich gebrochen werden.
"""
from urllib.parse import urlparse


def url_to_site_id(url: str) -> str:
    """
    Leitet die site_id aus einer URL ab — identisch zur Logik beim Anlegen einer
    Website (website_routes.py), damit gespeicherte und berechnete IDs matchen.
    """
    if not url:
        return ""
    raw = str(url)
    parsed = urlparse(raw if raw.startswith("http") else f"https://{raw}")
    hostname = parsed.netloc or parsed.path
    hostname = hostname.replace("www.", "")
    return hostname.replace(".", "-").lower()


async def site_has_active_license(pool, site_id: str) -> bool:
    """
    True, solange Banner/Widget für diese site_id lizenziert sind.

    Lizenz gilt als entzogen, sobald der Betreiber die zugehörige Website im
    Dashboard entfernt hat (keine passende tracked_websites-Zeile mehr).
    `pool` ist ein asyncpg.Pool (fetchrow/fetch akquirieren intern).
    """
    if pool is None or not site_id:
        return True
    try:
        cfg = await pool.fetchrow(
            "SELECT user_id FROM cookie_banner_configs WHERE site_id = $1 LIMIT 1",
            site_id,
        )
        # Keine/legacy Konfiguration ohne Owner → nicht brechen
        if not cfg or cfg["user_id"] is None:
            return True
        rows = await pool.fetch(
            "SELECT url FROM tracked_websites WHERE user_id = $1",
            cfg["user_id"],
        )
        return any(url_to_site_id(r["url"]) == site_id for r in rows)
    except Exception:
        # Bei DB-Problemen fail-open
        return True
