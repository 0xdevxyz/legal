"""
API-Routen für Nutzer-Benachrichtigungen (user_legal_notifications)
===================================================================

Erster Leseweg für die vom Legal-Change-Monitor erzeugten Benachrichtigungen.
Die Tabelle wurde bislang nur beschrieben, nie gelesen — hier kommen:

- GET  /api/notifications            paginierte Liste, Ungelesene zuerst
- POST /api/notifications/{id}/read  Gelesen-Markierung (nur eigene, idempotent)

Sicherheitsmodell: Jede Route hängt an der kanonischen Auth-Dependency
`get_current_user`; gefiltert wird ausschließlich über die user_id aus dem
JWT — nie über Client-Eingaben (kein IDOR-Weg).

Die Abfragen sind bewusst datenmengen-unabhängig (LIMIT/OFFSET, indizierte
Spalten user_id/is_read) — eine parallel laufende Duplikat-Bereinigung darf
den Leseweg nicht beeinflussen.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies import get_current_user
from database_service import db_service

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def _row_to_dict(row) -> Dict[str, Any]:
    d = dict(row)
    for k in ("created_at", "read_at"):
        if d.get(k) is not None:
            d[k] = d[k].isoformat()
    if d.get("website_id") is not None:
        d["website_id"] = str(d["website_id"])
    if d.get("websites") is not None:
        d["websites"] = [str(u) for u in d["websites"]]
    if d.get("ids") is not None:
        d["ids"] = [int(i) for i in d["ids"]]
    if d.get("website_count") is not None:
        d["website_count"] = int(d["website_count"])
    return d


def _require_pool():
    """DB-Pool holen oder sauber mit 503 antworten (statt AttributeError-500)."""
    if not db_service.pool:
        raise HTTPException(status_code=503, detail="Datenbank nicht verfügbar")
    return db_service.pool


@router.get("")
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    """Benachrichtigungen des angemeldeten Users — Ungelesene zuerst, dann neueste."""
    pool = _require_pool()
    user_id = int(current_user["id"])

    # Der Monitor legt eine Zeile je (Rechts-Update x Website) an. Flach
    # ausgeliefert stand derselbe Titel bei sechs getrackten Seiten sechsmal
    # untereinander — bei 925 Zeilen eine unlesbare Liste. Gruppiert wird
    # deshalb je Rechts-Update; die betroffenen Websites haengen als Liste dran.
    query = """
        SELECT
            MAX(n.id)                              AS id,
            n.legal_update_id,
            ARRAY_AGG(n.id ORDER BY n.id)          AS ids,
            MIN(n.notification_type)               AS notification_type,
            BOOL_AND(n.is_read)                    AS is_read,
            BOOL_OR(n.action_taken)                AS action_taken,
            MAX(n.created_at)                      AS created_at,
            MAX(n.read_at)                         AS read_at,
            COUNT(*)                               AS website_count,
            ARRAY_REMOVE(ARRAY_AGG(tw.url ORDER BY tw.url), NULL) AS websites,
            MIN(lu.title)       AS title,
            MIN(lu.severity)    AS severity,
            MIN(lu.update_type) AS update_type,
            MIN(lu.url)         AS url
        FROM user_legal_notifications n
        LEFT JOIN legal_updates lu ON lu.id = n.legal_update_id
        LEFT JOIN tracked_websites tw ON tw.id = n.website_id
        WHERE n.user_id = $1
    """
    if unread_only:
        query += " AND n.is_read = FALSE"
    query += """
        GROUP BY n.legal_update_id
        ORDER BY BOOL_AND(n.is_read) ASC, MAX(n.created_at) DESC, n.legal_update_id DESC
        LIMIT $2 OFFSET $3
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, user_id, limit, offset)
        # Ungelesen zaehlt Vorgaenge, nicht Zeilen: "6 offene Updates" ist die
        # Zahl, die der Nutzer abarbeiten kann — 925 war nur Tabellenrauschen.
        unread_count = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT legal_update_id)
            FROM user_legal_notifications
            WHERE user_id = $1 AND is_read = FALSE
            """,
            user_id,
        )

    return {
        "notifications": [_row_to_dict(r) for r in rows],
        "unread_count": int(unread_count or 0),
        "limit": limit,
        "offset": offset,
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Markiert eine EIGENE Benachrichtigung als gelesen (idempotent)."""
    pool = _require_pool()
    user_id = int(current_user["id"])

    async with pool.acquire() as conn:
        # Mitmarkieren, was zum selben Rechts-Update gehoert: die Liste zeigt
        # einen Eintrag je Update, also muessen auch alle Zeilen dieses Updates
        # quittiert werden — sonst kaeme der Eintrag als "ungelesen" zurueck.
        row = await conn.fetchrow(
            """
            UPDATE user_legal_notifications
            SET is_read = TRUE,
                read_at = COALESCE(read_at, NOW())
            WHERE user_id = $2
              AND (
                    id = $1
                    OR legal_update_id = (
                        SELECT legal_update_id FROM user_legal_notifications
                        WHERE id = $1 AND user_id = $2 AND legal_update_id IS NOT NULL
                    )
                  )
            RETURNING id, read_at
            """,
            notification_id,
            user_id,
        )

    if not row:
        # Bewusst 404 statt 403: verrät nicht, ob die fremde ID existiert
        raise HTTPException(status_code=404, detail="Benachrichtigung nicht gefunden")

    read_at = row["read_at"]
    return {
        "success": True,
        "id": row["id"],
        "read_at": read_at.isoformat() if read_at else None,
    }
