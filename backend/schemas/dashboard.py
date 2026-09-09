from pydantic import BaseModel, ConfigDict
from typing import Optional


class DashboardMetrics(BaseModel):
    totalScore: int
    websites: int
    # Grundlage des Schnitts; kleiner als `websites`, wenn Seiten nie geprueft
    # wurden. Ohne dieses Feld stuenden Anzahl und Mittel unverbunden nebeneinander.
    scoredWebsites: int = 0
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
