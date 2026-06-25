"""
Risk Radar Routes — /api/risk-radar/*
Ersetzt den bisherigen "Abmahnschutz" durch ein mehrstufiges Risiko-Radar.

Routen:
  GET  /api/risk-radar/score              — Aggregierter Risiko-Score mit Kategorien
  GET  /api/risk-radar/early-warnings     — Abmahnfallen-Frühwarnungen aus Update-Pipeline
  GET  /api/risk-radar/summary            — Kompakte Zusammenfassung (für Dashboard-Karte)

Kein "Abmahnschutz"-Versprechen. Klarer Disclaimer auf allen Responses.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Query

from legal_disclaimer import DISCLAIMER_SHORT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk-radar", tags=["risk-radar"])

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

LAW_CATEGORY_MAP = {
    "dsgvo": ["datenschutz", "dsgvo", "gdpr", "privacy", "data protection"],
    "ttdsg": ["ttdsg", "cookie", "tracking", "einwilligung", "consent"],
    "uwg": ["uwg", "wettbewerb", "competition", "werbung", "marketing", "agb"],
    "bfsg": ["bfsg", "barrierefreiheit", "accessibility", "wcag", "barriere"],
    "agb": ["agb", "allgemeine geschäftsbedingungen", "terms", "tos", "verträge"],
}


def _classify_law_category(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in LAW_CATEGORY_MAP.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "other"


@router.get("/score")
async def get_risk_radar_score(
    domain: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
):
    """
    Aggregierter Risiko-Score mit Kategorien.
    Nutzt risk_calculator + scan_history für domainspezifische Scores.
    """
    from dependencies import get_db_pool
    db_pool = await get_db_pool()

    categories = {
        "dsgvo": {"score": 0, "label": "DSGVO", "issues": []},
        "ttdsg": {"score": 0, "label": "TTDSG / Cookies", "issues": []},
        "uwg": {"score": 0, "label": "UWG / Wettbewerb", "issues": []},
        "bfsg": {"score": 0, "label": "BFSG / Barrierefreiheit", "issues": []},
        "agb": {"score": 0, "label": "AGB / Vertragsrecht", "issues": []},
    }
    top_risks = []
    overall_score = 0
    last_updated = None

    try:
        async with db_pool.acquire() as conn:
            if domain:
                scan_row = await conn.fetchrow(
                    """
                    SELECT id, compliance_score, issues, created_at
                    FROM scan_history
                    WHERE url ILIKE $1 OR url ILIKE $2
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    f"%{domain}%",
                    f"{domain}%",
                )
                if scan_row:
                    overall_score = max(0, 100 - int(scan_row["compliance_score"] or 0))
                    last_updated = scan_row["created_at"]

                    import json as _json
                    raw_issues = scan_row.get("issues") or "[]"
                    if isinstance(raw_issues, str):
                        issues_list = _json.loads(raw_issues)
                    else:
                        issues_list = raw_issues or []

                    for issue in issues_list[:20]:
                        issue_text = (
                            issue.get("description") or issue.get("message") or str(issue)
                        )
                        cat = _classify_law_category(issue_text)
                        if cat in categories:
                            categories[cat]["score"] = min(100, categories[cat]["score"] + 15)
                            categories[cat]["issues"].append(issue_text[:120])

                    top_risks = [
                        {
                            "category": cat,
                            "label": categories[cat]["label"],
                            "score": categories[cat]["score"],
                            "top_issue": categories[cat]["issues"][0] if categories[cat]["issues"] else None,
                            "recommendation": _get_recommendation(cat),
                        }
                        for cat in categories
                        if categories[cat]["score"] > 0
                    ]
                    top_risks.sort(key=lambda x: x["score"], reverse=True)
                    top_risks = top_risks[:3]

    except Exception as e:
        logger.error(f"Risk Radar Score Fehler: {e}", exc_info=True)

    return {
        "overall_risk_score": overall_score,
        "risk_level": _risk_level_label(overall_score),
        "categories": categories,
        "top_risks": top_risks,
        "last_updated": last_updated.isoformat() if last_updated else None,
        "domain": domain,
        "disclaimer": DISCLAIMER_SHORT,
        "source": "complyo-risk-radar",
        "note": "Risiko-Score basiert auf letztem Scan. Kein Abmahnschutz-Versprechen.",
    }


@router.get("/early-warnings")
async def get_early_warnings(
    user_id: Optional[int] = Query(None),
    severity_min: str = Query("low", description="Mindestseverity: info|low|medium|high|critical"),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
):
    """
    Abmahnfallen-Frühwarnungen aus der Update-Pipeline.
    Klassifiziert durch ai_legal_classifier mit Severity-Filter.
    """
    from dependencies import get_db_pool
    db_pool = await get_db_pool()

    try:
        min_idx = SEVERITY_ORDER.index(severity_min.lower())
    except ValueError:
        min_idx = 1

    warnings = []
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, title, summary, severity, source, url,
                       published_at, created_at, category
                FROM legal_updates
                WHERE severity = ANY($1)
                  AND created_at > NOW() - INTERVAL '90 days'
                ORDER BY created_at DESC
                LIMIT $2
                """,
                [s for s in SEVERITY_ORDER if SEVERITY_ORDER.index(s) >= min_idx],
                limit,
            )
            for row in rows:
                law_cat = _classify_law_category(row["title"] or "")
                warnings.append({
                    "id": row["id"],
                    "title": row["title"],
                    "summary": (row.get("summary") or "")[:300],
                    "severity": row["severity"],
                    "law_category": law_cat,
                    "source": row.get("source"),
                    "url": row.get("url"),
                    "published_at": row["published_at"].isoformat() if row.get("published_at") else None,
                    "detected_at": row["created_at"].isoformat() if row.get("created_at") else None,
                    "action_required": row["severity"] in ["high", "critical"],
                    "recommendation": _get_recommendation(law_cat),
                })
    except Exception as e:
        logger.warning(f"legal_updates Tabelle nicht verfügbar oder leer: {e}")
        try:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, title, content, category, source_url, published_at, created_at
                    FROM legal_news
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit,
                )
                for row in rows:
                    law_cat = _classify_law_category(row["title"] or "")
                    warnings.append({
                        "id": row["id"],
                        "title": row["title"],
                        "summary": (row.get("content") or "")[:300],
                        "severity": "info",
                        "law_category": law_cat,
                        "source": row.get("category"),
                        "url": row.get("source_url"),
                        "published_at": row["published_at"].isoformat() if row.get("published_at") else None,
                        "detected_at": row["created_at"].isoformat() if row.get("created_at") else None,
                        "action_required": False,
                        "recommendation": _get_recommendation(law_cat),
                    })
        except Exception as e2:
            logger.error(f"Frühwarnungen konnten nicht geladen werden: {e2}")

    return {
        "warnings": warnings,
        "count": len(warnings),
        "severity_filter": severity_min,
        "disclaimer": DISCLAIMER_SHORT,
        "note": "Frühwarnsystem — keine Rechtsberatung, kein Abmahnschutz-Versprechen.",
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/summary")
async def get_risk_radar_summary(
    domain: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
):
    """Kompakte Zusammenfassung für Dashboard-Karte."""
    score_data = await get_risk_radar_score(domain=domain, user_id=user_id)
    warnings_data = await get_early_warnings(limit=5, severity_min="medium")

    critical_warnings = [w for w in warnings_data["warnings"] if w["severity"] in ["high", "critical"]]

    return {
        "overall_risk_score": score_data["overall_risk_score"],
        "risk_level": score_data["risk_level"],
        "top_risks": score_data["top_risks"][:3],
        "critical_warnings": critical_warnings[:2],
        "has_action_required": len(critical_warnings) > 0,
        "disclaimer": DISCLAIMER_SHORT,
        "domain": domain,
    }


def _risk_level_label(score: int) -> str:
    if score == 0:
        return "minimal"
    if score <= 20:
        return "niedrig"
    if score <= 50:
        return "mittel"
    if score <= 75:
        return "hoch"
    return "kritisch"


def _get_recommendation(category: str) -> str:
    recs = {
        "dsgvo": "Datenschutzerklärung und Einwilligungsprozesse prüfen",
        "ttdsg": "Cookie-Banner-Konfiguration und Consent-Management prüfen",
        "uwg": "AGB, Preisangaben und Werbetexte auf Konformität prüfen",
        "bfsg": "Barrierefreiheits-Erklärung und WCAG-Konformität prüfen",
        "agb": "AGB auf AGB-Recht-Konformität und aktuelle Rechtslage prüfen",
        "other": "Allgemeine Compliance-Prüfung empfohlen",
    }
    return recs.get(category, recs["other"])
