"""
AI Compliance Routes - EU AI Act API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid

from auth_service import AuthService
from ai_act_analyzer import ai_act_analyzer, AISystem, RiskClassification, ComplianceResult
from database_service import db_service

router = APIRouter(prefix="/api/ai", tags=["AI Compliance"])
security = HTTPBearer()

# Request/Response Models
class AISystemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    vendor: Optional[str] = None
    purpose: str
    domain: Optional[str] = None
    deployment_date: Optional[date] = None
    data_types: Optional[List[str]] = []
    affected_persons: Optional[List[str]] = []
    website_id: Optional[str] = None

class AISystemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    purpose: Optional[str] = None
    domain: Optional[str] = None
    deployment_date: Optional[date] = None
    data_types: Optional[List[str]] = None
    affected_persons: Optional[List[str]] = None
    status: Optional[str] = None

class AISystemResponse(BaseModel):
    id: str
    name: str
    description: str
    vendor: Optional[str]
    purpose: str
    domain: Optional[str]
    risk_category: Optional[str]
    risk_reasoning: Optional[str]
    confidence_score: Optional[float]
    compliance_score: int
    last_assessment_date: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime
    website_id: Optional[str]

class ScanRequest(BaseModel):
    force_rescan: bool = False

class ScanResponse(BaseModel):
    scan_id: str
    ai_system_id: str
    compliance_score: int
    overall_risk_score: float
    risk_category: str
    status: str
    created_at: datetime
    

# ==================== AI SYSTEMS MANAGEMENT ====================

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user ID from JWT token"""
    from auth_routes import get_current_user
    user = await get_current_user(credentials)
    return user["user_id"]

@router.post("/systems", response_model=AISystemResponse)
async def create_ai_system(
    system_data: AISystemCreate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Registriere ein neues KI-System
    """
    
    # Check if user has ComploAI Guard addon
    has_addon = await db_service.check_user_addon(user_id, "comploai_guard")
    if not has_addon:
        raise HTTPException(
            status_code=403,
            detail="ComploAI Guard Add-on erforderlich. Bitte upgraden Sie Ihren Plan."
        )
    
    # Check limits
    limits = await db_service.get_addon_limits(user_id, "comploai_guard")
    current_count = await db_service.count_user_ai_systems(user_id)
    
    max_systems = limits.get("ai_systems", 10)
    if max_systems != -1 and current_count >= max_systems:
        raise HTTPException(
            status_code=403,
            detail=f"Limit von {max_systems} KI-Systemen erreicht. Bitte upgraden Sie Ihren Plan."
        )
    
    # Create AI system
    system_id = str(uuid.uuid4())
    
    query = """
        INSERT INTO ai_systems (
            id, user_id, website_id, name, description, vendor, 
            purpose, domain, deployment_date, data_types, affected_persons,
            status, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'active', NOW(), NOW())
        RETURNING *
    """
    
    import json
    result = await db_service.pool.fetchrow(
        query,
        system_id,
        user_id,
        system_data.website_id,
        system_data.name,
        system_data.description,
        system_data.vendor,
        system_data.purpose,
        system_data.domain,
        system_data.deployment_date,
        json.dumps(system_data.data_types) if system_data.data_types else None,
        json.dumps(system_data.affected_persons) if system_data.affected_persons else None
    )
    
    return AISystemResponse(
        id=str(result['id']),
        name=result['name'],
        description=result['description'],
        vendor=result['vendor'],
        purpose=result['purpose'],
        domain=result['domain'],
        risk_category=result['risk_category'],
        risk_reasoning=result['risk_reasoning'],
        confidence_score=result['confidence_score'],
        compliance_score=result['compliance_score'] or 0,
        last_assessment_date=result['last_assessment_date'],
        status=result['status'],
        created_at=result['created_at'],
        updated_at=result['updated_at'],
        website_id=str(result['website_id']) if result['website_id'] else None
    )

@router.get("/systems", response_model=List[AISystemResponse])
async def get_ai_systems(
    user_id: int = Depends(get_current_user_id),
    status: Optional[str] = None
):
    """
    Hole alle KI-Systeme des Users
    """
    
    # Check if user has ComploAI Guard addon
    has_addon = await db_service.check_user_addon(user_id, "comploai_guard")
    if not has_addon:
        raise HTTPException(
            status_code=403,
            detail="ComploAI Guard Add-on erforderlich"
        )
    
    query = """
        SELECT * FROM ai_systems 
        WHERE user_id = $1
    """
    params = [user_id]
    
    if status:
        query += " AND status = $2"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    
    results = await db_service.pool.fetch(query, *params)
    
    return [
        AISystemResponse(
            id=str(row['id']),
            name=row['name'],
            description=row['description'],
            vendor=row['vendor'],
            purpose=row['purpose'],
            domain=row['domain'],
            risk_category=row['risk_category'],
            risk_reasoning=row['risk_reasoning'],
            confidence_score=row['confidence_score'],
            compliance_score=row['compliance_score'] or 0,
            last_assessment_date=row['last_assessment_date'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            website_id=str(row['website_id']) if row['website_id'] else None
        )
        for row in results
    ]

@router.get("/systems/{system_id}", response_model=AISystemResponse)
async def get_ai_system(
    system_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole Details eines spezifischen KI-Systems
    """
    
    query = """
        SELECT * FROM ai_systems 
        WHERE id = $1 AND user_id = $2
    """
    
    result = await db_service.pool.fetchrow(query, uuid.UUID(system_id), user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    return AISystemResponse(
        id=str(result['id']),
        name=result['name'],
        description=result['description'],
        vendor=result['vendor'],
        purpose=result['purpose'],
        domain=result['domain'],
        risk_category=result['risk_category'],
        risk_reasoning=result['risk_reasoning'],
        confidence_score=result['confidence_score'],
        compliance_score=result['compliance_score'] or 0,
        last_assessment_date=result['last_assessment_date'],
        status=result['status'],
        created_at=result['created_at'],
        updated_at=result['updated_at'],
        website_id=str(result['website_id']) if result['website_id'] else None
    )

@router.put("/systems/{system_id}", response_model=AISystemResponse)
async def update_ai_system(
    system_id: str,
    update_data: AISystemUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Aktualisiere ein KI-System
    """
    
    # Check ownership
    check_query = "SELECT id FROM ai_systems WHERE id = $1 AND user_id = $2"
    exists = await db_service.pool.fetchrow(check_query, uuid.UUID(system_id), user_id)
    
    if not exists:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    # Build update query dynamically
    update_fields = []
    values = []
    param_count = 1
    
    import json
    for field, value in update_data.dict(exclude_unset=True).items():
        if value is not None:
            if field in ['data_types', 'affected_persons']:
                value = json.dumps(value)
            update_fields.append(f"{field} = ${param_count}")
            values.append(value)
            param_count += 1
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="Keine Aktualisierungen angegeben")
    
    values.append(uuid.UUID(system_id))
    values.append(user_id)
    
    query = f"""
        UPDATE ai_systems 
        SET {', '.join(update_fields)}, updated_at = NOW()
        WHERE id = ${param_count} AND user_id = ${param_count + 1}
        RETURNING *
    """
    
    result = await db_service.pool.fetchrow(query, *values)
    
    return AISystemResponse(
        id=str(result['id']),
        name=result['name'],
        description=result['description'],
        vendor=result['vendor'],
        purpose=result['purpose'],
        domain=result['domain'],
        risk_category=result['risk_category'],
        risk_reasoning=result['risk_reasoning'],
        confidence_score=result['confidence_score'],
        compliance_score=result['compliance_score'] or 0,
        last_assessment_date=result['last_assessment_date'],
        status=result['status'],
        created_at=result['created_at'],
        updated_at=result['updated_at'],
        website_id=str(result['website_id']) if result['website_id'] else None
    )

@router.delete("/systems/{system_id}")
async def delete_ai_system(
    system_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Lösche ein KI-System
    """
    
    query = """
        DELETE FROM ai_systems 
        WHERE id = $1 AND user_id = $2
        RETURNING id
    """
    
    result = await db_service.pool.fetchrow(query, uuid.UUID(system_id), user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    return {"message": "KI-System erfolgreich gelöscht", "id": system_id}

# ==================== AI COMPLIANCE SCANNING ====================

@router.post("/systems/{system_id}/scan", response_model=ScanResponse)
async def scan_ai_system(
    system_id: str,
    scan_request: ScanRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Führe einen Compliance-Scan für ein KI-System durch
    """
    
    # Get AI system
    system_query = "SELECT * FROM ai_systems WHERE id = $1 AND user_id = $2"
    system = await db_service.pool.fetchrow(system_query, uuid.UUID(system_id), user_id)
    
    if not system:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    # Create AISystem object for analyzer
    import json
    ai_system = AISystem(
        id=str(system['id']),
        name=system['name'],
        description=system['description'],
        vendor=system['vendor'],
        purpose=system['purpose'],
        domain=system['domain'],
        deployment_date=str(system['deployment_date']) if system['deployment_date'] else None,
        data_types=json.loads(system['data_types']) if system['data_types'] else [],
        affected_persons=json.loads(system['affected_persons']) if system['affected_persons'] else []
    )
    
    # Step 1: Classify risk if not already done or force_rescan
    risk_category = system['risk_category']
    if not risk_category or scan_request.force_rescan:
        print(f"Classifying risk for AI system: {system['name']}")
        risk_classification = await ai_act_analyzer.classify_risk_category(ai_system)
        risk_category = risk_classification.risk_category
        
        # Update AI system with risk classification
        update_query = """
            UPDATE ai_systems 
            SET risk_category = $1, risk_reasoning = $2, confidence_score = $3, updated_at = NOW()
            WHERE id = $4
        """
        await db_service.pool.execute(
            update_query,
            risk_classification.risk_category,
            risk_classification.reasoning,
            risk_classification.confidence,
            uuid.UUID(system_id)
        )
    
    # Step 2: Check compliance
    print(f"Checking compliance for AI system: {system['name']} (Risk: {risk_category})")
    compliance_result = await ai_act_analyzer.check_compliance(ai_system, risk_category)
    
    # Step 3: Save scan results
    scan_id = str(uuid.uuid4())
    
    scan_query = """
        INSERT INTO ai_compliance_scans (
            id, ai_system_id, user_id, compliance_score, overall_risk_score,
            risk_assessment, documentation_status, findings, recommendations,
            requirements_met, requirements_failed, status, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'completed', NOW())
        RETURNING *
    """
    
    scan_result = await db_service.pool.fetchrow(
        scan_query,
        uuid.UUID(scan_id),
        uuid.UUID(system_id),
        user_id,
        compliance_result.compliance_score,
        compliance_result.overall_risk_score,
        json.dumps({"risk_category": risk_category}),
        json.dumps({}),  # documentation_status - to be implemented
        json.dumps(compliance_result.findings),
        compliance_result.recommendations,
        json.dumps(compliance_result.requirements_met),
        json.dumps(compliance_result.requirements_failed)
    )
    
    # Update AI system with latest compliance score
    update_system_query = """
        UPDATE ai_systems 
        SET compliance_score = $1, last_assessment_date = NOW(), updated_at = NOW()
        WHERE id = $2
    """
    await db_service.pool.execute(
        update_system_query,
        compliance_result.compliance_score,
        uuid.UUID(system_id)
    )
    
    return ScanResponse(
        scan_id=str(scan_result['id']),
        ai_system_id=system_id,
        compliance_score=scan_result['compliance_score'],
        overall_risk_score=scan_result['overall_risk_score'],
        risk_category=risk_category,
        status=scan_result['status'],
        created_at=scan_result['created_at']
    )

@router.get("/systems/{system_id}/scans")
async def get_system_scans(
    system_id: str,
    user_id: int = Depends(get_current_user_id),
    limit: int = 10
):
    """
    Hole alle Scans für ein KI-System
    """
    
    # Check ownership
    check_query = "SELECT id FROM ai_systems WHERE id = $1 AND user_id = $2"
    exists = await db_service.pool.fetchrow(check_query, uuid.UUID(system_id), user_id)
    
    if not exists:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    query = """
        SELECT * FROM ai_compliance_scans 
        WHERE ai_system_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """
    
    results = await db_service.pool.fetch(query, uuid.UUID(system_id), limit)
    
    import json
    return [
        {
            "scan_id": str(row['id']),
            "ai_system_id": str(row['ai_system_id']),
            "compliance_score": row['compliance_score'],
            "overall_risk_score": row['overall_risk_score'],
            "risk_assessment": json.loads(row['risk_assessment']) if row['risk_assessment'] else {},
            "findings": json.loads(row['findings']) if row['findings'] else [],
            "recommendations": row['recommendations'],
            "status": row['status'],
            "created_at": row['created_at']
        }
        for row in results
    ]

@router.get("/scans/{scan_id}")
async def get_scan_details(
    scan_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole detaillierte Scan-Ergebnisse
    """
    
    query = """
        SELECT s.*, a.name as system_name, a.risk_category
        FROM ai_compliance_scans s
        JOIN ai_systems a ON s.ai_system_id = a.id
        WHERE s.id = $1 AND s.user_id = $2
    """
    
    result = await db_service.pool.fetchrow(query, uuid.UUID(scan_id), user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    import json
    return {
        "scan_id": str(result['id']),
        "ai_system_id": str(result['ai_system_id']),
        "system_name": result['system_name'],
        "risk_category": result['risk_category'],
        "compliance_score": result['compliance_score'],
        "overall_risk_score": result['overall_risk_score'],
        "risk_assessment": json.loads(result['risk_assessment']) if result['risk_assessment'] else {},
        "findings": json.loads(result['findings']) if result['findings'] else [],
        "requirements_met": json.loads(result['requirements_met']) if result['requirements_met'] else [],
        "requirements_failed": json.loads(result['requirements_failed']) if result['requirements_failed'] else [],
        "recommendations": result['recommendations'],
        "status": result['status'],
        "created_at": result['created_at']
    }

# ==================== AI ACT KNOWLEDGE BASE ====================

@router.get("/act/requirements")
async def get_ai_act_requirements():
    """
    Hole alle AI Act Requirements
    """
    
    return {
        "risk_categories": ai_act_analyzer.risk_categories,
        "high_risk_requirements": ai_act_analyzer.high_risk_requirements
    }

@router.get("/act/requirements/{risk_category}")
async def get_requirements_by_category(risk_category: str):
    """
    Hole Requirements für eine spezifische Risikokategorie
    """
    
    if risk_category not in ai_act_analyzer.risk_categories:
        raise HTTPException(status_code=404, detail="Risikokategorie nicht gefunden")
    
    category_info = ai_act_analyzer.risk_categories[risk_category]
    applicable_requirements = [
        req for req in ai_act_analyzer.high_risk_requirements
        if risk_category in req["mandatory_for"]
    ]
    required_docs = ai_act_analyzer.get_required_documentation(risk_category)
    
    return {
        "category": risk_category,
        "info": category_info,
        "requirements": applicable_requirements,
        "required_documentation": required_docs
    }

# ==================== DOCUMENTATION ====================

@router.get("/systems/{system_id}/documentation")
async def get_system_documentation(
    system_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole alle Dokumentation für ein KI-System
    """
    
    # Check ownership
    check_query = "SELECT id, risk_category FROM ai_systems WHERE id = $1 AND user_id = $2"
    system = await db_service.pool.fetchrow(check_query, uuid.UUID(system_id), user_id)
    
    if not system:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    # Get existing documentation
    docs_query = "SELECT * FROM ai_documentation WHERE ai_system_id = $1 ORDER BY created_at DESC"
    docs = await db_service.pool.fetch(docs_query, uuid.UUID(system_id))
    
    # Get required documentation based on risk category
    required_docs = ai_act_analyzer.get_required_documentation(system['risk_category'] or 'minimal')
    
    import json
    return {
        "required": required_docs,
        "existing": [
            {
                "id": str(doc['id']),
                "document_type": doc['document_type'],
                "title": doc['title'],
                "status": doc['status'],
                "version": doc['version'],
                "created_at": doc['created_at'],
                "file_url": doc['file_url']
            }
            for doc in docs
        ]
    }

@router.get("/stats")
async def get_ai_compliance_stats(
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole AI Compliance Statistiken für Dashboard
    """
    
    # Check if user has addon
    has_addon = await db_service.check_user_addon(user_id, "comploai_guard")
    if not has_addon:
        raise HTTPException(
            status_code=403,
            detail="ComploAI Guard Add-on erforderlich"
        )
    
    # Get total systems
    total_systems_query = "SELECT COUNT(*) as count FROM ai_systems WHERE user_id = $1 AND status = 'active'"
    total_systems = await db_service.pool.fetchval(total_systems_query, user_id) or 0
    
    # Get systems by risk category
    risk_query = """
        SELECT risk_category, COUNT(*) as count 
        FROM ai_systems 
        WHERE user_id = $1 AND status = 'active' AND risk_category IS NOT NULL
        GROUP BY risk_category
    """
    risk_distribution = await db_service.pool.fetch(risk_query, user_id)
    
    # Get average compliance score
    compliance_query = """
        SELECT AVG(compliance_score) as avg_score 
        FROM ai_systems 
        WHERE user_id = $1 AND status = 'active' AND compliance_score IS NOT NULL
    """
    avg_compliance = await db_service.pool.fetchval(compliance_query, user_id) or 0
    
    # Get recent scans
    recent_scans_query = """
        SELECT COUNT(*) as count 
        FROM ai_compliance_scans 
        WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
    """
    recent_scans = await db_service.pool.fetchval(recent_scans_query, user_id) or 0
    
    return {
        "total_systems": total_systems,
        "risk_distribution": {row['risk_category']: row['count'] for row in risk_distribution},
        "average_compliance_score": round(float(avg_compliance), 1) if avg_compliance else 0,
        "scans_last_30_days": recent_scans
    }

