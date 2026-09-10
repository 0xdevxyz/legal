"""
Die Adressen des oeffentlichen Pruefnachweises, fuer den angemeldeten Kunden.

Der Nachweis (nachweis_routes.py) ist seit August oeffentlich abrufbar und
die Erklaerung wird aus der Messung erzeugt. Nur: der Kunde hat davon nichts
gesehen. Im Dashboard gab es bis zum 11.09.2026 keinen Link, keinen
Einbettungscode, keine Adresse, die er in seine Barrierefreiheitserklaerung
haette setzen koennen. Der zentrale Beleg lag da und wurde nicht abgeholt.

Dieser Router liefert je Website des Nutzers die vier Adressen und den
fertigen Einbettungscode. Er ist angemeldet, weil er den Zugriffsschluessel
ausgibt; das Protokoll selbst bleibt oeffentlich und ist datensparsam (siehe
nachweis_routes).

Ohne `COMPLYO_NACHWEIS_SECRET` gibt es keinen Schluessel und deshalb auch
keine Adressen. Das steht dann als Grund in der Antwort, statt dass das
Dashboard Links zeigt, die auf 404 laufen.
"""
import html
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

import nachweis_routes
from accessibility_fix_saver import _als_user_id
from compliance_engine.nachweis_generator import nachweis_token
from dependencies import get_current_user, get_db
from site_id_utils import derive_site_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nachweis-links", tags=["nachweis"])

LINKTEXT = "Prüfnachweis zur Barrierefreiheit"


def _api_basis() -> str:
    """Die Adresse des Backends fuer die Rohfassungen (JSON, Markdown).

    Dieselbe Variable wie die Cookie-Richtlinie (PUBLIC_API_BASE), damit es
    nicht zwei Meinungen darueber gibt, wo die API von aussen erreichbar ist.
    """
    return os.getenv("PUBLIC_API_BASE", "https://api.complyo.de").rstrip("/")


def adressen_fuer(site_id: str, token: str) -> Dict[str, str]:
    """Die vier Adressen einer Website. Reine Funktion, damit sie testbar ist."""
    oeffentlich = nachweis_routes.oeffentliche_basis()
    api = _api_basis()
    return {
        "nachweis_seite": f"{oeffentlich}/nachweis/{site_id}/{token}",
        "erklaerung_seite": f"{oeffentlich}/nachweis/{site_id}/{token}/erklaerung",
        "nachweis_json": f"{api}/api/nachweis/{site_id}/{token}",
        "erklaerung_markdown": f"{api}/api/nachweis/{site_id}/{token}/erklaerung",
    }


def einbettung_fuer(nachweis_seite: str) -> str:
    """Der Link, den der Kunde in seine Seite setzt. Escaped, obwohl site_id
    und Token nur aus [a-z0-9-] bestehen: der Code landet in fremdem HTML."""
    return f'<a href="{html.escape(nachweis_seite, quote=True)}">{LINKTEXT}</a>'


@router.get("")
async def nachweis_links(user: dict = Depends(get_current_user),
                         db=Depends(get_db)) -> Dict[str, Any]:
    """Je Website des Nutzers: gibt es einen Nachweis, und wo ist er."""
    geheim = nachweis_routes._geheimnis()
    if not geheim:
        return {
            "verfuegbar": False,
            "grund": ("Der öffentliche Prüfnachweis ist auf diesem Server nicht "
                      "eingerichtet (COMPLYO_NACHWEIS_SECRET fehlt)."),
            "websites": [],
        }

    uid = _als_user_id(user.get("user_id") or user.get("id"))
    websites: List[Dict[str, Any]] = []
    if uid is not None:
        async with db.acquire() as conn:
            zeilen = await conn.fetch(
                """SELECT id, url FROM tracked_websites
                   WHERE user_id = $1
                   ORDER BY is_primary DESC, created_at ASC""",
                uid,
            )
    else:
        zeilen = []

    for z in zeilen:
        url = z["url"]
        site_id = derive_site_id(url)
        token = nachweis_token(site_id, geheim)
        # Dieselbe Quelle wie der oeffentliche Endpunkt: was hier "vorhanden"
        # heisst, liefert dort auch eine Seite. Ein Link auf 404 waere schlimmer
        # als kein Link.
        daten = await nachweis_routes._daten_fuer(site_id)
        adressen = adressen_fuer(site_id, token)
        websites.append({
            "website_id": z["id"],
            "url": url,
            "site_id": site_id,
            "nachweis_vorhanden": bool(daten),
            "gemessen_am": daten["gemessen_am"] if daten else None,
            "urls": adressen,
            "einbettung": einbettung_fuer(adressen["nachweis_seite"]),
        })

    return {"verfuegbar": True, "websites": websites}
