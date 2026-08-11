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

    query = """
        SELECT n.id, n.legal_update_id, n.website_id, n.notification_type,
               n.is_read, n.action_taken, n.created_at, n.read_at,
               lu.title, lu.severity, lu.update_type, lu.url
        FROM user_legal_notifications n
        LEFT JOIN legal_updates lu ON lu.id = n.legal_update_id
        WHERE n.user_id = $1
    """
    if unread_only:
        query += " AND n.is_read = FALSE"
    query += """
        ORDER BY n.is_read ASC, n.created_at DESC, n.id DESC
        LIMIT $2 OFFSET $3
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, user_id, limit, offset)
        unread_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM user_legal_notifications
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
        row = await conn.fetchrow(
            """
            UPDATE user_legal_notifications
            SET is_read = TRUE,
                read_at = COALESCE(read_at, NOW())
            WHERE id = $1 AND user_id = $2
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
