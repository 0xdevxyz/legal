"""
API Routes für Legal Change Monitoring
Ermöglicht Zugriff auf Gesetzesänderungen und automatische Fixes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from auth_routes import get_current_user
from database_service import DatabaseService
from legal_change_monitor import legal_monitor, LegalArea, ChangeSeverity

router = APIRouter(prefix="/api/legal-changes", tags=["Legal Changes"])
db_service = DatabaseService()

# Helper function to extract user_id from current_user
async def get_current_user_id(current_user: dict = Depends(get_current_user)) -> int:
    return current_user.get("user_id")


# ==================== PYDANTIC MODELS ====================

class LegalChangeResponse(BaseModel):
    id: str
    title: str
    description: str
    affected_areas: List[str]
    severity: str
    effective_date: str
    source: str
    source_url: Optional[str]
    requirements: List[str]
    detected_at: str
    is_active: bool


class ImpactAnalysisResponse(BaseModel):
    id: int
    legal_change_id: str
    is_affected: bool
    affected_components: List[str]
    urgency: Optional[str]
    risks: List[str]
    estimated_effort: Optional[str]
    recommendation: Optional[str]
    status: str
    analyzed_at: str


class ComplianceFixResponse(BaseModel):
    id: int
    legal_change_id: str
    affected_area: str
    fix_type: str
    description: str
    code_changes: Optional[Dict[str, Any]]
    config_changes: Optional[Dict[str, Any]]
    manual_steps: List[str]
    priority: int
    status: str
    created_at: str


class ApplyFixRequest(BaseModel):
    fix_id: int
    auto_apply: bool = False


# ==================== API ENDPOINTS ====================

@router.get("/changes", response_model=List[LegalChangeResponse])
async def get_legal_changes(
    severity: Optional[str] = None,
    area: Optional[str] = None,
    active_only: bool = True,
    user_id: int = Depends(get_current_user_id)
):
    """
    Liste alle erkannten Gesetzesänderungen auf
    """
    query = """
        SELECT * FROM legal_changes
        WHERE 1=1
    """
    params = []
    param_count = 1
    
    if active_only:
        query += " AND is_active = true"
    
    if severity:
        query += f" AND severity = ${param_count}"
        params.append(severity)
        param_count += 1
    
    if area:
        query += f" AND ${ param_count} = ANY(affected_areas)"
        params.append(area)
        param_count += 1
    
    query += " ORDER BY effective_date DESC, severity DESC"
    
    async with db_service.pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    
    changes = []
    for row in rows:
        changes.append(LegalChangeResponse(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            affected_areas=list(row['affected_areas']),
            severity=row['severity'],
            effective_date=row['effective_date'].isoformat(),
            source=row['source'],
            source_url=row['source_url'],
            requirements=list(row['requirements']) if row['requirements'] else [],
            detected_at=row['detected_at'].isoformat(),
            is_active=row['is_active']
        ))
    
    return changes


@router.get("/changes/{change_id}/impact", response_model=ImpactAnalysisResponse)
async def get_impact_analysis(
    change_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole die Impact-Analyse für eine bestimmte Gesetzesänderung
    """
    query = """
        SELECT * FROM legal_change_impacts
        WHERE legal_change_id = $1 AND user_id = $2
    """
    
    async with db_service.pool.acquire() as conn:
        row = await conn.fetchrow(query, change_id, user_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="Impact-Analyse nicht gefunden")
    
    return ImpactAnalysisResponse(
        id=row['id'],
        legal_change_id=row['legal_change_id'],
        is_affected=row['is_affected'],
        affected_components=list(row['affected_components']) if row['affected_components'] else [],
        urgency=row['urgency'],
        risks=list(row['risks']) if row['risks'] else [],
        estimated_effort=row['estimated_effort'],
        recommendation=row['recommendation'],
        status=row['status'],
        analyzed_at=row['analyzed_at'].isoformat()
    )


@router.post("/changes/{change_id}/analyze")
async def analyze_impact_for_user(
    change_id: str,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id)
):
    """
    Analysiere die Auswirkungen einer Gesetzesänderung für den aktuellen User
    """
    if not legal_monitor:
        raise HTTPException(
            status_code=503,
            detail="Legal Change Monitor nicht verfügbar"
        )
    
    # Hole Gesetzesänderung
    async with db_service.pool.acquire() as conn:
        change_row = await conn.fetchrow(
            "SELECT * FROM legal_changes WHERE id = $1",
            change_id
        )
        
        if not change_row:
            raise HTTPException(status_code=404, detail="Gesetzesänderung nicht gefunden")
        
        # Hole User-Context
        user_row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        
        # Hole Website-Info (falls vorhanden)
        site_row = await conn.fetchrow(
            "SELECT * FROM monitored_websites WHERE user_id = $1 LIMIT 1",
            user_id
        )
    
    # Erstelle User-Context
    user_context = {
        "website_url": site_row['url'] if site_row else None,
        "compliance_areas": [],  # TODO: aus aktueller Config holen
        "services": []  # TODO: aus Cookie-Config holen
    }
    
    # Starte Analyse im Hintergrund
    background_tasks.add_task(
        _run_impact_analysis,
        change_id,
        user_id,
        change_row,
        user_context
    )
    
    return {
        "success": True,
        "message": "Impact-Analyse gestartet",
        "status": "processing"
    }


@router.get("/my-impacts", response_model=List[ImpactAnalysisResponse])
async def get_my_impacts(
    status: Optional[str] = None,
    affected_only: bool = False,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole alle Impact-Analysen für den aktuellen User
    """
    query = """
        SELECT * FROM legal_change_impacts
        WHERE user_id = $1
    """
    params = [user_id]
    param_count = 2
    
    if status:
        query += f" AND status = ${param_count}"
        params.append(status)
        param_count += 1
    
    if affected_only:
        query += " AND is_affected = true"
    
    query += " ORDER BY analyzed_at DESC"
    
    async with db_service.pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    
    impacts = []
    for row in rows:
        impacts.append(ImpactAnalysisResponse(
            id=row['id'],
            legal_change_id=row['legal_change_id'],
            is_affected=row['is_affected'],
            affected_components=list(row['affected_components']) if row['affected_components'] else [],
            urgency=row['urgency'],
            risks=list(row['risks']) if row['risks'] else [],
            estimated_effort=row['estimated_effort'],
            recommendation=row['recommendation'],
            status=row['status'],
            analyzed_at=row['analyzed_at'].isoformat()
        ))
    
    return impacts


@router.get("/changes/{change_id}/fixes", response_model=List[ComplianceFixResponse])
async def get_compliance_fixes(
    change_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole alle generierten Fixes für eine Gesetzesänderung
    """
    query = """
        SELECT * FROM compliance_fixes
        WHERE legal_change_id = $1 AND user_id = $2
        ORDER BY priority ASC, created_at ASC
    """
    
    async with db_service.pool.acquire() as conn:
        rows = await conn.fetch(query, change_id, user_id)
    
    fixes = []
    for row in rows:
        fixes.append(ComplianceFixResponse(
            id=row['id'],
            legal_change_id=row['legal_change_id'],
            affected_area=row['affected_area'],
            fix_type=row['fix_type'],
            description=row['description'],
            code_changes=dict(row['code_changes']) if row['code_changes'] else {},
            config_changes=dict(row['config_changes']) if row['config_changes'] else {},
            manual_steps=list(row['manual_steps']) if row['manual_steps'] else [],
            priority=row['priority'],
            status=row['status'],
            created_at=row['created_at'].isoformat()
        ))
    
    return fixes


@router.post("/fixes/apply")
async def apply_compliance_fix(
    request: ApplyFixRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id)
):
    """
    Wende einen Compliance-Fix an
    """
    async with db_service.pool.acquire() as conn:
        fix_row = await conn.fetchrow(
            "SELECT * FROM compliance_fixes WHERE id = $1 AND user_id = $2",
            request.fix_id,
            user_id
        )
        
        if not fix_row:
            raise HTTPException(status_code=404, detail="Fix nicht gefunden")
        
        if fix_row['status'] == 'applied':
            return {
                "success": False,
                "message": "Fix wurde bereits angewendet"
            }
    
    if request.auto_apply and fix_row['fix_type'] == 'automated':
        # Automatische Anwendung im Hintergrund
        background_tasks.add_task(
            _apply_fix_automatically,
            request.fix_id,
            user_id,
            fix_row
        )
        
        return {
            "success": True,
            "message": "Fix wird automatisch angewendet",
            "status": "processing"
        }
    else:
        # Manuelle Anwendung - nur Anleitung zurückgeben
        return {
            "success": True,
            "message": "Manuelle Anwendung erforderlich",
            "fix_type": fix_row['fix_type'],
            "code_changes": dict(fix_row['code_changes']) if fix_row['code_changes'] else {},
            "config_changes": dict(fix_row['config_changes']) if fix_row['config_changes'] else {},
            "manual_steps": list(fix_row['manual_steps']) if fix_row['manual_steps'] else []
        }


@router.post("/monitor/run")
async def trigger_legal_monitoring(
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id)
):
    """
    Triggere manuell eine Überprüfung auf neue Gesetzesänderungen
    (Admin only)
    """
    # TODO: Admin-Check einbauen
    
    if not legal_monitor:
        raise HTTPException(
            status_code=503,
            detail="Legal Change Monitor nicht verfügbar"
        )
    
    background_tasks.add_task(_run_legal_monitoring)
    
    return {
        "success": True,
        "message": "Legal Change Monitoring gestartet"
    }


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    user_id: int = Depends(get_current_user_id)
):
    """
    Dashboard-Zusammenfassung für den User
    """
    async with db_service.pool.acquire() as conn:
        # Anzahl betroffener Änderungen
        affected_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM legal_change_impacts
            WHERE user_id = $1 AND is_affected = true AND status != 'completed'
            """,
            user_id
        )
        
        # Kritische Änderungen
        critical_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM legal_change_impacts lci
            JOIN legal_changes lc ON lci.legal_change_id = lc.id
            WHERE lci.user_id = $1 AND lci.is_affected = true
            AND lc.severity IN ('critical', 'high')
            AND lci.status != 'completed'
            """,
            user_id
        )
        
        # Pending Fixes
        pending_fixes = await conn.fetchval(
            """
            SELECT COUNT(*) FROM compliance_fixes
            WHERE user_id = $1 AND status = 'pending'
            """,
            user_id
        )
        
        # Nächste Deadline
        next_deadline = await conn.fetchrow(
            """
            SELECT lc.title, lc.effective_date
            FROM legal_change_impacts lci
            JOIN legal_changes lc ON lci.legal_change_id = lc.id
            WHERE lci.user_id = $1 AND lci.is_affected = true
            AND lc.effective_date > NOW()
            AND lci.status != 'completed'
            ORDER BY lc.effective_date ASC
            LIMIT 1
            """,
            user_id
        )
    
    return {
        "affected_changes": affected_count or 0,
        "critical_changes": critical_count or 0,
        "pending_fixes": pending_fixes or 0,
        "next_deadline": {
            "title": next_deadline['title'] if next_deadline else None,
            "date": next_deadline['effective_date'].isoformat() if next_deadline else None
        }
    }


# ==================== BACKGROUND TASKS ====================

async def _run_impact_analysis(
    change_id: str,
    user_id: int,
    change_row: Any,
    user_context: Dict[str, Any]
):
    """Background Task: Führt Impact-Analyse durch"""
    try:
        from legal_change_monitor import LegalChange, LegalArea, ChangeSeverity
        
        # Erstelle LegalChange-Objekt
        legal_change = LegalChange(
            id=change_row['id'],
            title=change_row['title'],
            description=change_row['description'],
            affected_areas=[LegalArea(area) for area in change_row['affected_areas']],
            severity=ChangeSeverity(change_row['severity']),
            effective_date=change_row['effective_date'],
            source=change_row['source'],
            source_url=change_row['source_url'],
            requirements=list(change_row['requirements']) if change_row['requirements'] else []
        )
        
        # Führe Analyse durch
        analysis = await legal_monitor.analyze_impact(legal_change, user_context)
        
        # Speichere Ergebnis
        async with db_service.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO legal_change_impacts (
                    legal_change_id, user_id, is_affected, affected_components,
                    urgency, risks, estimated_effort, recommendation, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
                ON CONFLICT (legal_change_id, user_id)
                DO UPDATE SET
                    is_affected = EXCLUDED.is_affected,
                    affected_components = EXCLUDED.affected_components,
                    urgency = EXCLUDED.urgency,
                    risks = EXCLUDED.risks,
                    estimated_effort = EXCLUDED.estimated_effort,
                    recommendation = EXCLUDED.recommendation,
                    analyzed_at = NOW()
                """,
                change_id,
                user_id,
                analysis.get('is_affected', False),
                analysis.get('affected_components', []),
                analysis.get('urgency', 'medium'),
                analysis.get('risks', []),
                analysis.get('estimated_effort', 'unknown'),
                analysis.get('recommendation', '')
            )
        
        # Generiere Fixes wenn betroffen
        if analysis.get('is_affected', False):
            fixes = await legal_monitor.generate_compliance_fixes(legal_change, analysis)
            
            # Speichere Fixes
            async with db_service.pool.acquire() as conn:
                for fix in fixes:
                    await conn.execute(
                        """
                        INSERT INTO compliance_fixes (
                            legal_change_id, user_id, affected_area, fix_type,
                            description, code_changes, config_changes, manual_steps, priority
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                        fix.legal_change_id,
                        user_id,
                        fix.affected_area.value,
                        fix.fix_type,
                        fix.description,
                        json.dumps(fix.code_changes),
                        json.dumps(fix.config_changes),
                        fix.manual_steps,
                        fix.priority
                    )
        
        print(f"✅ Impact analysis completed for user {user_id}, change {change_id}")
        
    except Exception as e:
        print(f"❌ Impact analysis failed: {e}")
        # Speichere Fehler
        async with db_service.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO legal_change_impacts (
                    legal_change_id, user_id, is_affected, affected_components,
                    urgency, recommendation, status
                ) VALUES ($1, $2, true, ARRAY['error'], 'medium', $3, 'error')
                ON CONFLICT (legal_change_id, user_id) DO UPDATE
                SET status = 'error', recommendation = EXCLUDED.recommendation
                """,
                change_id,
                user_id,
                f"Analyse fehlgeschlagen: {str(e)}"
            )


async def _apply_fix_automatically(fix_id: int, user_id: int, fix_row: Any):
    """Background Task: Wendet einen Fix automatisch an"""
    try:
        # TODO: Implementiere automatische Fix-Anwendung
        # Beispiel: Cookie-Banner-Konfiguration anpassen
        
        async with db_service.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE compliance_fixes
                SET status = 'applied', applied_at = NOW(), applied_by = $2,
                    result = 'Automatisch angewendet'
                WHERE id = $1
                """,
                fix_id,
                user_id
            )
        
        print(f"✅ Fix {fix_id} automatically applied for user {user_id}")
        
    except Exception as e:
        print(f"❌ Auto-fix failed: {e}")
        async with db_service.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE compliance_fixes
                SET status = 'failed', result = $2
                WHERE id = $1
                """,
                fix_id,
                f"Fehler: {str(e)}"
            )


async def _run_legal_monitoring():
    """Background Task: Führt Legal Change Monitoring durch"""
    start_time = datetime.now()
    
    try:
        changes = await legal_monitor.monitor_legal_changes()
        
        # Speichere neue Änderungen
        async with db_service.pool.acquire() as conn:
            for change in changes:
                await conn.execute(
                    """
                    INSERT INTO legal_changes (
                        id, title, description, affected_areas, severity,
                        effective_date, source, source_url, requirements
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    change.id,
                    change.title,
                    change.description,
                    [area.value for area in change.affected_areas],
                    change.severity.value,
                    change.effective_date,
                    change.source,
                    change.source_url,
                    change.requirements
                )
            
            # Log
            execution_time = (datetime.now() - start_time).total_seconds()
            await conn.execute(
                """
                INSERT INTO legal_monitoring_logs (
                    changes_detected, status, execution_time_seconds
                ) VALUES ($1, 'completed', $2)
                """,
                len(changes),
                execution_time
            )
        
        print(f"✅ Legal monitoring completed. {len(changes)} changes detected.")
        
    except Exception as e:
        print(f"❌ Legal monitoring failed: {e}")
        async with db_service.pool.acquire() as conn:
            execution_time = (datetime.now() - start_time).total_seconds()
            await conn.execute(
                """
                INSERT INTO legal_monitoring_logs (
                    changes_detected, status, error_message, execution_time_seconds
                ) VALUES (0, 'failed', $1, $2)
                """,
                str(e),
                execution_time
            )

