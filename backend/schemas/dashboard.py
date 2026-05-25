from pydantic import BaseModel, ConfigDict
from typing import Optional


class DashboardMetrics(BaseModel):
    totalScore: int
    websites: int
    criticalIssues: int
    scansAvailable: int
    scansUsed: int
    avgScore: int
    totalRiskEuro: int
    aiFixesUsed: Optional[int] = 0
    aiFixesMax: Optional[int] = 1
    websitesMax: Optional[int] = 3
    scoreTrend: Optional[float] = None
    criticalTrend: Optional[int] = None

    model_config = ConfigDict(frozen=True, extra="allow")


class DashboardOverview(BaseModel):
    user_id: int
    plan_type: Optional[str] = None
    websites_count: int
    last_scan_at: Optional[str] = None
    compliance_score: Optional[float] = None

    model_config = ConfigDict(frozen=True, extra="allow")
