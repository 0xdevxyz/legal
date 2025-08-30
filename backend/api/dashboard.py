"""Dashboard API endpoints"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats():
    return {
        "total_scans": 1247,
        "compliance_score": 94.2,
        "active_projects": 18,
        "vulnerabilities_fixed": 342
    }
