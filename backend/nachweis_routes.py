"""
Der öffentliche Prüfnachweis.

Warum öffentlich
----------------
Ein Nachweis, den nur der Betreiber sieht, ist kein Nachweis, sondern ein
Bericht. Der Wert entsteht erst, wenn ein Dritter ihn aufrufen kann: die
Prüfstelle, der Anwalt der Gegenseite, ein Besucher, der eine Barriere gemeldet
hat. Deshalb hängt der Link in der Barrierefreiheitserklärung, und deshalb
braucht er keine Anmeldung.

Was das nicht ist
-----------------
Kein Siegel. Ein Siegel behauptet ein Ergebnis; dieses Protokoll zeigt eine
Methode und **benennt seine eigenen Lücken**. Hugo vergibt ab Score 60 ein
Verifikations-Siegel — das ist eine Note, keine Nachprüfbarkeit.

Datensparsam
------------
Ausgeliefert werden Messwerte, Regelnamen und Begründungen. Keine
Kundendaten, keine E-Mail-Adressen, keine Nutzer-IDs. Der Zugriffsschlüssel ist
aus site_id und einem Server-Geheimnis abgeleitet: stabil (der Link in der
Erklärung darf nicht verfallen), aber nicht aus der Domain errechenbar.

Ohne konfiguriertes Geheimnis (`COMPLYO_NACHWEIS_SECRET`) liefert der Endpunkt
nichts aus. Lieber kein öffentlicher Nachweis als einer mit ratbarem Schlüssel.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from compliance_engine.nachweis_generator import (
    baue_nachweis, erklaerung_aus_nachweis, nachweis_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nachweis", tags=["nachweis"])

db_pool = None


def _geheimnis() -> str:
    return os.getenv("COMPLYO_NACHWEIS_SECRET", "")


async def _daten_fuer(site_id: str) -> Optional[Dict[str, Any]]:
    """Sammelt die gespeicherten Messungen und Reparaturen einer Site."""
    if not db_pool:
        return None

    async with db_pool.acquire() as conn:
        zeilen = await conn.fetch(
            """SELECT fix_type, payload, status, updated_at
               FROM accessibility_document_fixes
               WHERE site_id = $1 AND fix_type IN ('kontrast-css', 'struktur')""",
            site_id,
        )
        alt_live = await conn.fetchval(
            """SELECT COUNT(*) FROM accessibility_alt_text_fixes
               WHERE site_id = $1 AND status = 'approved'""",
            site_id,
        )
        url = await conn.fetchval(
            """SELECT url FROM tracked_websites
               WHERE regexp_replace(lower(url), '^https?://(www\\.)?', '') LIKE $1
               LIMIT 1""",
            site_id.replace("-de", ".de").replace("-", "%") + "%",
        )

    if not zeilen:
        return None

    vorher: Dict[str, int] = {}
    nachher: Dict[str, int] = {}
    fixes: List[Dict[str, Any]] = []
    gemessen_am = None

    for z in zeilen:
        payload = z["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (ValueError, TypeError):
                continue
        if not isinstance(payload, dict):
            continue

        # Nur freigegebene Reparaturen erscheinen im Nachweis. Ein Protokoll
        # ueber Fixes, die nie live gingen, waere eine Faelschung.
        if z["status"] != "approved":
            continue

        if z["fix_type"] == "struktur":
            for regel, werte in (payload.get("je_regel") or {}).items():
                if isinstance(werte, (list, tuple)) and len(werte) == 2:
                    vorher[regel] = vorher.get(regel, 0) + int(werte[0])
                    nachher[regel] = nachher.get(regel, 0) + int(werte[1])
            fixes.extend(payload.get("fixes") or [])
        elif z["fix_type"] == "kontrast-css":
            vorher["color-contrast"] = int(payload.get("vorher") or 0)
            nachher["color-contrast"] = int(payload.get("nachher") or 0)
            for e in payload.get("entscheidungen") or []:
                if e.get("freigabe") != "approved":
                    continue
                fixes.append({
                    "regel": "color-contrast",
                    "attribut": "color",
                    "selector": (e.get("selektoren") or [""])[0],
                    "begruendung": (
                        f"{e.get('vordergrund')} auf {e.get('hintergrund')}: "
                        f"{e.get('ist_ratio')}:1 → {e.get('neue_ratio')}:1 "
                        f"({e.get('stellen')} Stellen)"
                    ),
                })
        if z["updated_at"] and (not gemessen_am or z["updated_at"] > gemessen_am):
            gemessen_am = z["updated_at"]

    if not vorher:
        return None

    return {
        "site_url": url or f"https://{site_id.replace('-de', '.de')}",
        "vorher": vorher,
        "nachher": nachher,
        "fixes": fixes,
        "alt_live": int(alt_live or 0),
        "gemessen_am": gemessen_am.strftime("%Y-%m-%d %H:%M") if gemessen_am else None,
    }


@router.get("/{site_id}/{token}")
async def oeffentlicher_nachweis(site_id: str, token: str) -> JSONResponse:
    """
    Das Prüfprotokoll einer Website — ohne Anmeldung abrufbar.

    Der Token muss zur site_id passen; ein falscher gibt 404, nicht 403. Ob es
    zu einer Domain überhaupt einen Nachweis gibt, ist selbst eine Auskunft.
    """
    geheim = _geheimnis()
    if not geheim:
        logger.warning("COMPLYO_NACHWEIS_SECRET nicht gesetzt — Nachweis deaktiviert")
        raise HTTPException(status_code=404, detail="Nicht gefunden")

    import hmac
    if not hmac.compare_digest(token, nachweis_token(site_id, geheim)):
        raise HTTPException(status_code=404, detail="Nicht gefunden")

    daten = await _daten_fuer(site_id)
    if not daten:
        raise HTTPException(status_code=404, detail="Nicht gefunden")

    nachweis = baue_nachweis(
        site_id=site_id,
        site_url=daten["site_url"],
        messung_vorher=daten["vorher"],
        messung_nachher=daten["nachher"],
        fixes=daten["fixes"],
        alt_texte_live=daten["alt_live"],
        gemessen_am=daten["gemessen_am"],
    )
    return JSONResponse(
        content=nachweis,
        headers={
            "Access-Control-Allow-Origin": "*",
            # Kurz cachen: der Nachweis aendert sich nur mit einem neuen Scan,
            # muss aber nach einer Reparatur zeitnah stimmen.
            "Cache-Control": "public, max-age=900",
        },
    )


@router.get("/{site_id}/{token}/erklaerung")
async def oeffentliche_erklaerung(
    site_id: str, token: str, anbieter: str = "", kontakt: str = ""
) -> JSONResponse:
    """Die Barrierefreiheitserklärung als Markdown — aus derselben Messung."""
    antwort = await oeffentlicher_nachweis(site_id, token)
    nachweis = json.loads(antwort.body)

    basis = os.getenv("COMPLYO_PUBLIC_URL", "https://complyo.de").rstrip("/")
    text = erklaerung_aus_nachweis(
        nachweis,
        anbieter=anbieter or nachweis["site_url"],
        kontakt=kontakt or "über das Kontaktformular dieser Website",
        nachweis_url=f"{basis}/nachweis/{site_id}/{token}",
    )
    return JSONResponse(
        content={"markdown": text, "gemessen_am": nachweis["gemessen_am"]},
        headers={"Access-Control-Allow-Origin": "*",
                 "Cache-Control": "public, max-age=900"},
    )


def init_nachweis_routes(pool) -> None:
    global db_pool
    db_pool = pool
    if not _geheimnis():
        logger.warning(
            "COMPLYO_NACHWEIS_SECRET fehlt — der oeffentliche Pruefnachweis "
            "bleibt aus. Ohne Geheimnis waere der Zugriffsschluessel ratbar."
        )
    else:
        logger.info("✅ Oeffentlicher Pruefnachweis bereit")
