"""
Der Wirkungsscan als Endpunkt.

Ein eigener Modus neben dem normalen Scan, bewusst mit eigener Adresse: er
beantwortet eine andere Frage. Der normale Scan fragt "was ist an dieser
Website nicht in Ordnung". Der Wirkungsscan fragt "**kommt an, was wir
versprochen haben**" — und misst es, statt es zu behaupten.

Er ist die Antwort auf den teuersten Befund des Audits: von sechs betreuten
Kundenwebsites lieferte genau eine tatsaechlich aus. Freigegeben war ueberall
alles, das Dashboard meldete "erledigt", und beim Besucher kam nichts an.
Diese Luecke war nur deshalb unsichtbar, weil niemand den ausgelieferten
Zustand gemessen hat.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dependencies import get_current_user, rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wirkungsscan", tags=["wirkungsscan"])

db_pool = None


class WirkungsscanRequest(BaseModel):
    url: str = Field(..., description="Die zu messende Seite")
    wcag_level: str = Field("wcag21aa", description="Regelsatz")


async def _besitzt(user: Dict[str, Any], url: str) -> bool:
    """
    Nur eigene Websites. Der Scan laedt eine fremde Seite zweimal — das ist
    zwar oeffentlich abrufbarer Inhalt, aber kein Grund, complyo zum
    Lastwerkzeug gegen Dritte zu machen.
    """
    if not db_pool:
        return False
    from site_id_utils import derive_site_id
    gesucht = derive_site_id(url)
    uid = user.get("user_id") or user.get("id")
    try:
        uid = int(uid)
    except (TypeError, ValueError):
        return False
    async with db_pool.acquire() as conn:
        zeilen = await conn.fetch(
            "SELECT url FROM tracked_websites WHERE user_id = $1", uid)
    return any(derive_site_id(z["url"]) == gesucht for z in zeilen)


@router.post("", dependencies=[Depends(rate_limit("wirkungsscan", 10, 3600))])
async def starte_wirkungsscan(
    anfrage: WirkungsscanRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Misst dieselbe Seite zweimal — ohne und mit complyo-Widget.

    Dauert etwa doppelt so lange wie ein normaler Scan, weil es zwei echte
    Browserlaeufe sind. Das Rate-Limit ist entsprechend eng.
    """
    if not await _besitzt(user, anfrage.url):
        raise HTTPException(
            status_code=403,
            detail=("Diese Website ist Ihrem Konto nicht zugeordnet. Fügen Sie "
                    "sie unter „Websites“ hinzu, dann können Sie sie messen."))

    from compliance_engine.axe_scanner import AxeScanner
    from compliance_engine.wirkungsscan import wirkungsscan

    try:
        ergebnis = await wirkungsscan(AxeScanner(), anfrage.url,
                                      wcag_level=anfrage.wcag_level)
    except Exception as e:
        logger.error("Wirkungsscan fuer %s fehlgeschlagen: %r",
                     anfrage.url, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=("Die Messung ist auf unserer Seite fehlgeschlagen — nicht "
                    "an Ihrer Website. Der Fehler ist protokolliert."))

    if not ergebnis.get("success"):
        # Eine halbe Messung ist keine Messung. Lieber sagen, dass es nicht
        # geklappt hat, als eine Differenz aus einem Lauf zu erfinden.
        raise HTTPException(status_code=502, detail=ergebnis.get("fehler"))

    # Ergebnis festhalten, damit der Verlauf sichtbar wird: eine einzelne
    # Messung ist ein Foto, erst die Reihe zeigt, ob es haelt.
    if db_pool:
        try:
            import json as _json
            from site_id_utils import derive_site_id
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO accessibility_wirkungsscan
                           (site_id, url, ohne_widget, mit_widget, lage, ergebnis)
                       VALUES ($1, $2, $3, $4, $5, $6::jsonb)""",
                    derive_site_id(anfrage.url), anfrage.url,
                    ergebnis["ohne_widget"]["gesamt"],
                    ergebnis["mit_widget"]["gesamt"],
                    ergebnis["urteil"]["lage"],
                    _json.dumps(ergebnis, ensure_ascii=False))
        except Exception as e:
            logger.warning("Wirkungsscan nicht gespeichert: %s", e)

    return ergebnis


SCHEMA = """
CREATE TABLE IF NOT EXISTS accessibility_wirkungsscan (
    id           BIGSERIAL PRIMARY KEY,
    site_id      VARCHAR(100) NOT NULL,
    url          TEXT         NOT NULL,
    ohne_widget  INTEGER      NOT NULL,
    mit_widget   INTEGER      NOT NULL,
    lage         VARCHAR(32)  NOT NULL,
    ergebnis     JSONB        NOT NULL,
    gemessen_am  TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wirkungsscan_site
    ON accessibility_wirkungsscan (site_id, gemessen_am DESC);
"""


@router.get("/{site_id}/verlauf")
async def verlauf(site_id: str,
                  user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Die letzten Messungen einer Website — der Verlauf, nicht das Foto."""
    if not db_pool:
        return {"success": True, "messungen": []}
    from site_id_utils import derive_site_id
    uid = user.get("user_id") or user.get("id")
    try:
        uid = int(uid)
    except (TypeError, ValueError):
        raise HTTPException(status_code=403, detail="Kein Zugriff")

    async with db_pool.acquire() as conn:
        eigene = await conn.fetch(
            "SELECT url FROM tracked_websites WHERE user_id = $1", uid)
        if site_id not in {derive_site_id(z["url"]) for z in eigene}:
            raise HTTPException(status_code=403, detail="Kein Zugriff auf diese Website")
        zeilen = await conn.fetch(
            """SELECT ohne_widget, mit_widget, lage, gemessen_am
               FROM accessibility_wirkungsscan
               WHERE site_id = $1 ORDER BY gemessen_am DESC LIMIT 30""",
            site_id)

    return {
        "success": True,
        "site_id": site_id,
        "messungen": [
            {"ohne_widget": z["ohne_widget"], "mit_widget": z["mit_widget"],
             "behoben": max(0, z["ohne_widget"] - z["mit_widget"]),
             "lage": z["lage"],
             "gemessen_am": z["gemessen_am"].strftime("%Y-%m-%d %H:%M")}
            for z in zeilen
        ],
    }


async def init_wirkungsscan_routes(pool) -> None:
    global db_pool
    db_pool = pool
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(SCHEMA)
            logger.info("✅ Wirkungsscan bereit")
        except Exception as e:
            logger.error("Wirkungsscan-Tabelle nicht angelegt: %s", e)
