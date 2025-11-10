"""
Dashboard API Routes
Provides aggregated metrics and statistics for authenticated users
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

dashboard_router = APIRouter(prefix="/api/v2/dashboard", tags=["dashboard"])
security = HTTPBearer()

# Global references (set in main_production.py)
db_pool = None
auth_service = None

class DashboardMetrics(BaseModel):
    totalScore: int
    websites: int
    criticalIssues: int
    scansAvailable: int
    scansUsed: int
    avgScore: int
    totalRiskEuro: int
    # Neue Felder für AI-Fix-Limits
    aiFixesUsed: Optional[int] = 0
    aiFixesMax: Optional[int] = 1
    websitesMax: Optional[int] = 3
    # Trend-Daten
    scoreTrend: Optional[float] = None  # Prozentuale Änderung zum Vormonat
    criticalTrend: Optional[int] = None  # Absolute Änderung kritischer Issues

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        logger.info(f"User authenticated: {user_data.get('user_id')}")
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")

@dashboard_router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get aggregated dashboard metrics for the authenticated user
    
    Returns:
    - totalScore: Average compliance score across all tracked websites
    - websites: Number of tracked websites
    - criticalIssues: Sum of critical issues from latest scans
    - scansAvailable: Based on user plan (100 for AI, unlimited for Expert)
    - scansUsed: Number of scans performed this month
    - avgScore: Same as totalScore
    - totalRiskEuro: Sum of total risk from latest scans
    """
    try:
        # Get user_id from authenticated user
        user_id = user.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Check if database is available
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # For authenticated user, get real metrics
        async with db_pool.acquire() as conn:
            logger.info(f"Fetching dashboard metrics for user_id: {user_id}")
            
            # Get tracked websites count
            websites_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tracked_websites WHERE user_id = $1",
                user_id
            )
            
            # Get latest scans per website
            latest_scans = await conn.fetch("""
                SELECT DISTINCT ON (website_id)
                    website_id,
                    compliance_score,
                    critical_issues,
                    total_risk_euro
                FROM scan_history
                WHERE user_id = $1
                ORDER BY website_id, scan_timestamp DESC
            """, user_id)
            
            # Calculate aggregated metrics
            if latest_scans:
                avg_score = int(sum(scan['compliance_score'] for scan in latest_scans) / len(latest_scans))
                total_critical = sum(scan['critical_issues'] for scan in latest_scans)
                total_risk = sum(scan['total_risk_euro'] or 0 for scan in latest_scans)
            else:
                avg_score = 0
                total_critical = 0
                total_risk = 0
            
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
            old_scans = await conn.fetch("""
                SELECT DISTINCT ON (website_id)
                    website_id,
                    compliance_score,
                    critical_issues
                FROM scan_history
                WHERE user_id = $1 AND scan_timestamp < $2
                ORDER BY website_id, scan_timestamp DESC
            """, user_id, week_ago)
            
            if old_scans and latest_scans:
                old_avg_score = int(sum(scan['compliance_score'] for scan in old_scans) / len(old_scans))
                old_critical = sum(scan['critical_issues'] for scan in old_scans)
                
                # Berechne prozentuale Änderung des Scores
                if old_avg_score > 0:
                    score_trend = round(((avg_score - old_avg_score) / old_avg_score) * 100, 1)
                
                # Absolute Änderung kritischer Issues
                critical_trend = total_critical - old_critical
            
            # Get user plan and limits
            user_limits = await conn.fetchrow(
                "SELECT plan_type, websites_max, ai_fixes_count, ai_fixes_max FROM user_limits WHERE user_id = $1",
                user_id
            )
            
            scans_available = 100 if (user_limits and user_limits['plan_type'] == 'ai') else 999
            websites_max = user_limits['websites_max'] if user_limits else 3
            ai_fixes_used = user_limits['ai_fixes_count'] if user_limits else 0
            ai_fixes_max = user_limits['ai_fixes_max'] if user_limits else 1
            
            return DashboardMetrics(
                totalScore=avg_score,
                websites=websites_count or 0,
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
            websitesMax=3,
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

