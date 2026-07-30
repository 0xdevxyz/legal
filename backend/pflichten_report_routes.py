"""
Pflichten-Report-API (Phase 7.2 „Pflichtenradar").

- PUT  /api/pflichten-report/profile  — Firmenprofil speichern (JSONB answers)
- GET  /api/pflichten-report/profile  — Profil laden
- GET  /api/pflichten-report          — Report: Katalog × Profil (+ Scan-Kontext)

Plan-Gating: Free-Plan sieht Zähler + die Top-3-Pflichten (Teaser), zahlende
Pläne den vollen Report. RDG-Haftungs-Design liegt im Katalog selbst
(Selbst-Check-Wording, confidence, evidence) — siehe pflichten_katalog.py.
"""
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dependencies import get_current_user, get_db
from pflichten_katalog import evaluate_pflichten, APPLIES, CHECK
from pflichten_events import sync_pflichten_events, get_events_for_rules

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pflichten-report", tags=["Pflichten-Report"])

TEASER_LIMIT = 3

ALLOWED_KEYS = {
    "employees", "revenue", "b2c", "online_shop", "digital_service",
    "uses_ai_chat", "uses_ai_decisions", "ai_generated_content",
    "sends_b2b_invoices", "sells_connected_products", "critical_sector",
    "newsletter", "employees_data", "branche",
}


class ProfileRequest(BaseModel):
    answers: Dict[str, Any] = Field(..., description="Profil-Antworten (siehe pflichten_katalog.py)")


async def _get_plan_type(db, user_id: int) -> str:
    row = await db.fetchrow(
        "SELECT plan_type FROM user_limits WHERE user_id = $1", user_id
    )
    return (row["plan_type"] if row and row["plan_type"] else "free").lower()


@router.put("/profile")
async def save_profile(
    body: ProfileRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    answers = {k: v for k, v in body.answers.items() if k in ALLOWED_KEYS}
    if not answers:
        raise HTTPException(status_code=422, detail="Keine gültigen Profil-Felder übergeben")
    # JSONB immer über json.dumps schreiben (asyncpg-Pool hat keinen json-Codec)
    await db.execute(
        """
        INSERT INTO company_profiles (user_id, answers, updated_at)
        VALUES ($1, $2::jsonb, NOW())
        ON CONFLICT (user_id)
        DO UPDATE SET answers = $2::jsonb, updated_at = NOW()
        """,
        current_user["id"], json.dumps(answers),
    )
    return {"success": True, "saved_keys": sorted(answers.keys())}


@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    row = await db.fetchrow(
        "SELECT answers, updated_at FROM company_profiles WHERE user_id = $1",
        current_user["id"],
    )
    if not row:
        return {"exists": False, "answers": {}}
    answers = row["answers"]
    if isinstance(answers, str):
        answers = json.loads(answers)
    return {"exists": True, "answers": answers, "updated_at": row["updated_at"]}


async def _latest_scan_pillars(db, user_id: int) -> Optional[Dict[str, Any]]:
    """Jüngster Scan des Users → Säulen-Scores als Ist-Zustand-Kontext."""
    row = await db.fetchrow(
        """
        SELECT url, overall_score, accessibility_score, cookie_score,
               legal_score, privacy_score, scan_date
        FROM scan_history
        WHERE user_id = $1
        ORDER BY scan_date DESC NULLS LAST
        LIMIT 1
        """,
        user_id,
    )
    if not row:
        return None
    return {
        "url": row["url"],
        "scan_date": row["scan_date"].isoformat() if row["scan_date"] else None,
        "pillars": {
            "accessibility": row["accessibility_score"],
            "cookies": row["cookie_score"],
            "legal": row["legal_score"],
            "gdpr": row["privacy_score"],
        },
        "overall": row["overall_score"],
    }


@router.get("/updates")
async def get_updates_feed(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Phase 7.3 „lebender Pflichten-Graph": Änderungs-Feed zu den Pflichten,
    die laut Profil relevant sind (applies/check). Lazy-Sync aus dem
    Legal-Change-Monitoring — kein eigener Cron nötig.
    """
    user_id = current_user["id"]
    prow = await db.fetchrow(
        "SELECT answers FROM company_profiles WHERE user_id = $1", user_id
    )
    if not prow:
        raise HTTPException(
            status_code=404,
            detail="Kein Firmenprofil vorhanden — bitte zuerst den Fragebogen ausfüllen.",
        )
    answers = prow["answers"]
    if isinstance(answers, str):
        answers = json.loads(answers)

    try:
        await sync_pflichten_events(db)
    except Exception as e:
        logger.warning(f"Pflichten-Events-Sync fehlgeschlagen (Feed liefert Bestand): {e}")

    report = evaluate_pflichten(answers)
    relevant_rules = [i["id"] for i in report["items"] if i["status"] in (APPLIES, CHECK)]
    titles = {i["id"]: i["title"] for i in report["items"]}
    events = await get_events_for_rules(db, relevant_rules)
    for ev in events:
        ev["rule_title"] = titles.get(ev["rule_id"], ev["rule_id"])
        if ev.get("published_at"):
            ev["published_at"] = ev["published_at"].isoformat()
        if ev.get("effective_date"):
            ev["effective_date"] = ev["effective_date"].isoformat()

    plan_type = await _get_plan_type(db, user_id)
    is_paid = plan_type not in ("free", "freemium")
    total = len(events)
    if not is_paid:
        events = events[:2]
    return {
        "relevant_rules": relevant_rules,
        "total_events": total,
        "events": events,
        "locked": not is_paid,
        "teaser": (
            {"hidden_count": total - len(events),
             "upgrade_hint": f"{total - len(events)} weitere Entwicklungen zu Ihren Pflichten im Pro-Plan."}
            if not is_paid and total > len(events) else None
        ),
        "disclaimer": (
            "Automatisch zugeordnete Meldungen aus dem Rechts-Monitoring — "
            "Information, keine Rechtsberatung. Quelle jeweils verlinkt."
        ),
    }


@router.get("")
async def get_report(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = current_user["id"]
    prow = await db.fetchrow(
        "SELECT answers FROM company_profiles WHERE user_id = $1", user_id
    )
    if not prow:
        raise HTTPException(
            status_code=404,
            detail="Kein Firmenprofil vorhanden — bitte zuerst den Fragebogen ausfüllen.",
        )
    answers = prow["answers"]
    if isinstance(answers, str):
        answers = json.loads(answers)

    report = evaluate_pflichten(answers)

    # Ist-Zustand aus dem letzten Website-Scan an passende Pflichten hängen
    scan = await _latest_scan_pillars(db, user_id)
    if scan:
        for item in report["items"]:
            pillar = item.get("scan_pillar")
            if pillar and scan["pillars"].get(pillar) is not None:
                item["scan_status"] = {
                    "pillar": pillar,
                    "score": scan["pillars"][pillar],
                    "scanned_url": scan["url"],
                    "scan_date": scan["scan_date"],
                }
    report["scan_context"] = scan

    plan_type = await _get_plan_type(db, user_id)
    is_paid = plan_type not in ("free", "freemium")
    report["plan_type"] = plan_type
    report["locked"] = not is_paid
    if not is_paid:
        # Teaser: volle Zähler, aber nur die Top-3-Einträge im Detail
        visible = report["items"][:TEASER_LIMIT]
        hidden_count = max(0, len(report["items"]) - len(visible))
        applies_hidden = sum(
            1 for r in report["items"][TEASER_LIMIT:] if r["status"] == APPLIES
        )
        report["items"] = visible
        report["teaser"] = {
            "hidden_count": hidden_count,
            "hidden_applies": applies_hidden,
            "upgrade_hint": (
                f"{hidden_count} weitere Einordnungen (davon {applies_hidden} "
                f"wahrscheinlich zutreffend) im Pro-Plan."
            ),
        }
    return report
