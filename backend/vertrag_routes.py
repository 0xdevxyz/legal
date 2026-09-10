"""
Vertragsstand und Nachholen der Zustimmung fuer Bestandskonten (Prefix /api/auth).

Seit dem 10.09.2026 nimmt die Registrierung AGB und Auftragsverarbeitungs-
vertrag (Art. 28 DSGVO) an und protokolliert das in `vertragsannahmen`. Die
Konten von davor haben nie zugestimmt: am 11.09.2026 stand fuer 16 Konten
keine Zeile mit avv_version. Ohne AVV darf complyo fuer sie keine Daten der
Besucher ihrer Websites verarbeiten. Das Dashboard fragt deshalb den Stand ab
und sperrt den Inhalt, bis die Zustimmung nachgeholt ist (VertragsGate.tsx).

Zwei Routen, beide angemeldet:
  GET  /api/auth/vertragsstand     was gilt, was wurde angenommen, was fehlt
  POST /api/auth/vertrag-annehmen  holt die Zustimmung nach

Die Annahme wird ueber `auth_routes.protokolliere_vertragsannahme` geschrieben,
also mit denselben Feldern (IP, User-Agent, Fassungen) wie bei der
Registrierung. Ein Nachweis, der anders aussieht als der andere, ist zwei
Nachweise.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

import auth_routes
from accessibility_fix_saver import _als_user_id
from dependencies import get_current_user, get_db, rate_limit
from vertragsstand import AGB_VERSION, AVV_VERSION

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class VertragAnnahme(BaseModel):
    unternehmer_bestaetigt: bool = False
    agb_version: Optional[str] = None
    avv_version: Optional[str] = None


async def _juengste_annahme(db, user_id: int) -> Optional[Dict[str, Any]]:
    async with db.acquire() as conn:
        zeile = await conn.fetchrow(
            """SELECT agb_version, avv_version, unternehmer_bestaetigt, angenommen_am
               FROM vertragsannahmen
               WHERE user_id = $1
               ORDER BY angenommen_am DESC, id DESC
               LIMIT 1""",
            user_id,
        )
    return dict(zeile) if zeile else None


def _stand(zeile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    agb = zeile.get("agb_version") if zeile else None
    avv = zeile.get("avv_version") if zeile else None
    angenommen_am = zeile.get("angenommen_am") if zeile else None
    return {
        "agb_version_aktuell": AGB_VERSION,
        "avv_version_aktuell": AVV_VERSION,
        "agb_angenommen": agb,
        "avv_angenommen": avv,
        "agb_fehlt": agb != AGB_VERSION,
        "avv_fehlt": avv != AVV_VERSION,
        "angenommen_am": angenommen_am.isoformat() if angenommen_am else None,
    }


@router.get("/vertragsstand")
async def vertragsstand(user: dict = Depends(get_current_user),
                        db=Depends(get_db)) -> Dict[str, Any]:
    """
    Welche Fassungen gelten und welche der Nutzer angenommen hat.

    Aus der juengsten Zeile je Nutzer. Fehlt sie (Konto von vor dem
    01.09.2026), fehlt beides. Ein Datenbankfehler ist 503, nicht "fehlt":
    das Gate sperrt nur bei einer klaren Antwort, sonst wuerde ein
    Tabellenproblem jeden Kunden aussperren.
    """
    uid = _als_user_id(user.get("user_id") or user.get("id"))
    if uid is None:
        raise HTTPException(status_code=401, detail="Kein Nutzerbezug")
    try:
        zeile = await _juengste_annahme(db, uid)
    except Exception as exc:
        logger.error("Vertragsstand fuer Nutzer %s nicht lesbar: %s", uid, exc)
        raise HTTPException(
            status_code=503,
            detail="Der Vertragsstand kann gerade nicht gelesen werden.",
        )
    return _stand(zeile)


@router.post("/vertrag-annehmen",
             dependencies=[Depends(rate_limit("vertrag_annehmen", 10, 60))])
async def vertrag_annehmen(request: Request, body: VertragAnnahme,
                           user: dict = Depends(get_current_user),
                           db=Depends(get_db)) -> Dict[str, Any]:
    """
    Zustimmung nachholen. Nur die aktuellen Fassungen, nur als Unternehmer.

    Die Fassungen kommen vom Aufrufer mit und werden gegen die aktuellen
    geprueft, statt sie stillschweigend einzusetzen: protokolliert wird, was
    dem Nutzer angezeigt wurde. Zeigt das Dashboard eine veraltete Fassung,
    ist die Antwort 400 und kein falscher Nachweis.
    """
    if not body.unternehmer_bestaetigt:
        raise HTTPException(
            status_code=400,
            detail="Bitte bestätigen Sie, dass Sie als Unternehmer handeln.",
        )
    if body.agb_version != AGB_VERSION or body.avv_version != AVV_VERSION:
        raise HTTPException(
            status_code=400,
            detail=(f"Die angezeigte Fassung ist nicht mehr aktuell "
                    f"(gültig: AGB {AGB_VERSION}, AVV {AVV_VERSION}). "
                    f"Bitte laden Sie die Seite neu."),
        )

    uid = _als_user_id(user.get("user_id") or user.get("id"))
    if uid is None:
        raise HTTPException(status_code=401, detail="Kein Nutzerbezug")

    await auth_routes.protokolliere_vertragsannahme(
        uid, user.get("email") or "", request,
        True, AGB_VERSION, AVV_VERSION,
    )

    # protokolliere_vertragsannahme ist mit Absicht best effort (bei der
    # Registrierung darf ein fehlender Nachweis den Kaufweg nicht abbrechen).
    # Hier ist der Nachweis der ganze Zweck: also nachlesen, ob er steht.
    try:
        zeile = await _juengste_annahme(db, uid)
    except Exception as exc:
        logger.error("Vertragsannahme fuer Nutzer %s nicht nachlesbar: %s", uid, exc)
        zeile = None
    stand = _stand(zeile)
    if stand["agb_fehlt"] or stand["avv_fehlt"]:
        raise HTTPException(
            status_code=503,
            detail="Die Zustimmung konnte nicht gespeichert werden. Bitte versuchen Sie es später noch einmal.",
        )
    return stand
