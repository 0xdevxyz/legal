"""
Dashboard API Routes
Provides aggregated metrics and statistics for authenticated users
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from dependencies import get_current_user
from schemas.dashboard import DashboardMetrics as _DashboardMetricsSchema

logger = logging.getLogger(__name__)

dashboard_router = APIRouter(prefix="/api/v2/dashboard", tags=["dashboard"])

# Global references (set in main_production.py)
db_pool = None
auth_service = None

# Kanonisches Website-Limit pro Plan: 1 Seite überall, 25 nur im Agentur-Modus.
# (Es gibt KEINE 3-Seiten-Option.) SSOT — deckt sich mit stripe_routes.PLAN_WEBSITES_MAX.
PLAN_WEBSITES_MAX = {
    "free": 1, "single": 1, "pro": 1, "agency": 25, "expert": 1, "update": 1,
}

class DashboardMetrics(BaseModel):
    totalScore: int
    websites: int
    # Auf wie vielen Websites der Schnitt beruht. Kann kleiner als `websites`
    # sein: nie gepruefte Seiten gehen nicht als 0 in den Schnitt ein.
    scoredWebsites: int = 0
    criticalIssues: int
    scansAvailable: int
    scansUsed: int
    avgScore: int
    totalRiskEuro: int
    # Neue Felder für AI-Fix-Limits
    aiFixesUsed: Optional[int] = 0
    aiFixesMax: Optional[int] = 1
    websitesMax: Optional[int] = 1
    # Trend-Daten
    scoreTrend: Optional[float] = None  # Prozentuale Änderung zum Vormonat
    criticalTrend: Optional[int] = None  # Absolute Änderung kritischer Issues

@dashboard_router.get("/metrics", response_model=_DashboardMetricsSchema)
async def get_dashboard_metrics(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get aggregated dashboard metrics for the authenticated user
    """
    try:
        user_id = user["id"]

        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")

        async with db_pool.acquire() as conn:
            logger.info(f"Fetching dashboard metrics for user_id: {user_id}")
            
            # Get tracked websites count
            websites_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tracked_websites WHERE user_id = $1",
                user_id
            )
            
            # Der Stand je verfolgter Website kommt aus score_history.
            #
            # Bis zum 09.09.2026 wurde hier scan_history gemittelt. Das ist der
            # Mitschnitt der MANUELLEN Dashboard-Scans; der Monitor schreibt
            # ausschliesslich nach score_history und tracked_websites. Seit er
            # laeuft, driftete die Kopfzeile weg: an dem Tag gemessen zeigte sie
            # den Schnitt 32 aus Werten von Juni bis August, waehrend die sechs
            # Seiten tatsaechlich bei 58 standen und am Vortag geprueft worden
            # waren. Daneben stand "letzte Pruefung heute".
            #
            # score_history traegt BEIDE Wege (main_production schreibt sie beim
            # manuellen Scan, cronjobs/website_monitor beim Monitorlauf) und ist
            # damit die einzige vollstaendige und aktuelle Quelle.
            #
            # Der JOIN auf tracked_websites ist kein Beiwerk: vorher lief die
            # Mittelung ueber COALESCE(website_id, url) aus scan_history und zog
            # damit auch Seiten ein, die der Kunde laengst entfernt hat — im
            # gemessenen Fall eine siebte Seite unter der Ueberschrift
            # "6 Websites". Anzahl und Schnitt meinen jetzt dieselbe Menge.
            latest_scans = await conn.fetch("""
                SELECT DISTINCT ON (t.id)
                    t.id AS website_id,
                    s.overall_score AS score,
                    COALESCE((s.pillar_scores->>'critical_issues')::int, 0) AS critical_issues
                FROM tracked_websites t
                JOIN score_history s ON s.website_id = t.id
                WHERE t.user_id = $1 AND s.overall_score IS NOT NULL
                ORDER BY t.id, s.scan_date DESC
            """, user_id)

            # Ungeprueft ist nicht null: eine nie gemessene Seite geht NICHT als
            # 0 in den Schnitt, sie bleibt draussen. `scoredWebsites` sagt, auf
            # wie vielen der Schnitt beruht — sonst stuenden Anzahl und Mittel
            # nebeneinander, ohne dass jemand die Luecke sehen koennte.
            scored_websites = len(latest_scans)

            if latest_scans:
                avg_score = int(sum(scan['score'] for scan in latest_scans) / scored_websites)
                total_critical = sum(scan['critical_issues'] for scan in latest_scans)
            else:
                avg_score = 0
                total_critical = 0

            # Risikosumme gibt es nur in scan_history — score_history fuehrt sie
            # nicht. Auf die verfolgten URLs eingegrenzt, damit wenigstens keine
            # entfernte Seite mehr mitzaehlt.
            total_risk = await conn.fetchval("""
                SELECT COALESCE(SUM(letzte.total_risk_euro), 0) FROM (
                    SELECT DISTINCT ON (h.url) h.total_risk_euro
                    FROM scan_history h
                    JOIN tracked_websites t ON t.url = h.url AND t.user_id = h.user_id
                    WHERE h.user_id = $1
                    ORDER BY h.url, h.scan_timestamp DESC
                ) AS letzte
            """, user_id) or 0
            
            # Get scans this month
            from datetime import datetime, timedelta
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            scans_this_month = await conn.fetchval(
                "SELECT COUNT(*) FROM scan_history WHERE user_id = $1 AND scan_timestamp >= $2",
                user_id, month_start
            )
            
            # Calculate trends (compare with last week)
            score_trend = None
            critical_trend = None
            
            week_ago = datetime.now() - timedelta(days=7)
            # Derselbe Weg fuer den Vergleichsstand — ein Trend zwischen zwei
            # verschiedenen Quellen waere eine Zahl ohne Bedeutung.
            old_scans = await conn.fetch("""
                SELECT DISTINCT ON (t.id)
                    t.id AS website_id,
                    s.overall_score AS score,
                    COALESCE((s.pillar_scores->>'critical_issues')::int, 0) AS critical_issues
                FROM tracked_websites t
                JOIN score_history s ON s.website_id = t.id
                WHERE t.user_id = $1 AND s.scan_date < $2 AND s.overall_score IS NOT NULL
                ORDER BY t.id, s.scan_date DESC
            """, user_id, week_ago)

            if old_scans and latest_scans:
                old_avg_score = int(sum(scan['score'] for scan in old_scans) / len(old_scans))
                old_critical = sum(scan['critical_issues'] for scan in old_scans)
                
                # Berechne prozentuale Änderung des Scores
                if old_avg_score > 0:
                    score_trend = round(((avg_score - old_avg_score) / old_avg_score) * 100, 1)
                
                # Absolute Änderung kritischer Issues
                critical_trend = total_critical - old_critical
            
            # Get user plan and limits
            # ⚠️ Spalten heißen fixes_used/fixes_limit (NICHT ai_fixes_count/-max).
            # Falsche Spaltennamen führten zu einer SQL-Exception → der Endpoint
            # fiel in den Fallback (websitesMax=1, aiFixesMax=1) und zeigte für
            # ALLE Pläne fälschlich „1/1" bzw. „0/1".
            user_limits = await conn.fetchrow(
                "SELECT plan_type, websites_max, fixes_used, fixes_limit FROM user_limits WHERE user_id = $1",
                user_id
            )

            plan_type = user_limits['plan_type'] if user_limits else 'free'
            scans_available = 999
            # Website-Limit kanonisch aus dem Plan ableiten (DB-Spalte kann veraltet/-1/3 sein).
            websites_max = PLAN_WEBSITES_MAX.get(plan_type, 1)
            ai_fixes_used = user_limits['fixes_used'] if user_limits else 0
            # Bezahlte Pläne: unbegrenzte KI-Optimierungen (-1 = unbegrenzt). Nur Free hat das 1-Fix-Freemium-Limit.
            is_paid_plan = plan_type not in (None, '', 'free')
            ai_fixes_max = -1 if is_paid_plan else (user_limits['fixes_limit'] if user_limits else 1)
            
            return DashboardMetrics(
                totalScore=avg_score,
                websites=websites_count or 0,
                scoredWebsites=scored_websites,
                criticalIssues=total_critical,
                scansAvailable=scans_available,
                scansUsed=scans_this_month or 0,
                avgScore=avg_score,
                totalRiskEuro=total_risk,
                aiFixesUsed=ai_fixes_used,
                aiFixesMax=ai_fixes_max,
                websitesMax=websites_max,
                scoreTrend=score_trend,
                criticalTrend=critical_trend
            )
            
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {e}", exc_info=True)
        # Return safe defaults on error
        return DashboardMetrics(
            totalScore=0,
            websites=0,
            criticalIssues=0,
            scansAvailable=100,
            scansUsed=0,
            avgScore=0,
            totalRiskEuro=0,
            aiFixesUsed=0,
            aiFixesMax=1,
            websitesMax=1,
            scoreTrend=None,
            criticalTrend=None
        )

@dashboard_router.get("/stats")
async def get_dashboard_stats(user_id: int = 1):
    """
    Get detailed statistics for the user
    
    Returns comprehensive stats including:
    - Recent scans
    - Trending issues
    - Risk distribution
    """
    try:
        if not db_pool:
            return {"error": "Database not available"}
        
        async with db_pool.acquire() as conn:
            # Recent scans
            recent_scans = await conn.fetch("""
                SELECT 
                    scan_id,
                    url,
                    compliance_score,
                    total_risk_euro,
                    critical_issues,
                    warning_issues,
                    scan_timestamp
                FROM scan_history
                WHERE user_id = $1
                ORDER BY scan_timestamp DESC
                LIMIT 10
            """, user_id)
            
            # Issue category distribution
            issue_categories = await conn.fetch("""
                SELECT 
                    (issue->>'category')::text as category,
                    COUNT(*) as count
                FROM scan_history sh,
                     jsonb_array_elements(scan_data->'issues') as issue
                WHERE sh.user_id = $1
                GROUP BY category
                ORDER BY count DESC
                LIMIT 10
            """, user_id)
            
            return {
                "recent_scans": [dict(row) for row in recent_scans],
                "issue_categories": [dict(row) for row in issue_categories]
            }
            
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}", exc_info=True)
        return {"error": str(e)}

