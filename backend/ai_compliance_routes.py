"""
AI Compliance Routes - EU AI Act API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import io

from auth_service import AuthService
from ai_act_analyzer import ai_act_analyzer, AISystem, RiskClassification, ComplianceResult
from ai_compliance_notification_service import ai_compliance_notification_service
from file_storage_service import file_storage
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

# ==================== DOCUMENTATION GENERATION ====================

class GenerateDocRequest(BaseModel):
    document_type: str = Field(..., description="Type: risk_assessment, technical_documentation, conformity_declaration")

@router.post("/systems/{system_id}/documentation/generate")
async def generate_documentation(
    system_id: str,
    request: GenerateDocRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Generiere AI Act Dokumentation für ein KI-System
    """
    
    check_query = """
        SELECT id, name, description, vendor, purpose, domain, risk_category, 
               risk_reasoning, confidence_score, compliance_score
        FROM ai_systems 
        WHERE id = $1 AND user_id = $2
    """
    system = await db_service.pool.fetchrow(check_query, uuid.UUID(system_id), user_id)
    
    if not system:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    ai_system_data = {
        "id": str(system['id']),
        "name": system['name'],
        "description": system['description'],
        "vendor": system['vendor'],
        "purpose": system['purpose'],
        "domain": system['domain']
    }
    
    classification_data = {
        "risk_category": system['risk_category'] or 'minimal',
        "reasoning": system['risk_reasoning'] or '',
        "confidence": system['confidence_score'] or 0.5,
        "relevant_articles": [],
        "key_concerns": []
    }
    
    if system['risk_category'] == 'high':
        classification_data['relevant_articles'] = [
            "Art. 6 - Klassifizierungsregeln für Hochrisiko-Systeme",
            "Art. 9 - Risikomanagementsystem", 
            "Art. 10 - Daten und Daten-Governance",
            "Art. 11 - Technische Dokumentation",
            "Art. 12 - Aufzeichnungspflichten",
            "Art. 13 - Transparenz und Informationspflichten",
            "Art. 14 - Menschliche Aufsicht",
            "Art. 15 - Genauigkeit, Robustheit und Cybersicherheit"
        ]
    elif system['risk_category'] == 'limited':
        classification_data['relevant_articles'] = [
            "Art. 52 - Transparenzpflichten für bestimmte KI-Systeme"
        ]
    elif system['risk_category'] == 'prohibited':
        classification_data['relevant_articles'] = [
            "Art. 5 - Verbotene Praktiken im Bereich der künstlichen Intelligenz"
        ]
    
    valid_types = ['risk_assessment', 'technical_documentation', 'conformity_declaration']
    if request.document_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Ungültiger Dokumenttyp. Erlaubt: {', '.join(valid_types)}"
        )
    
    try:
        from ai_act_doc_generator import ai_act_doc_generator
        if request.document_type == 'risk_assessment':
            html_content = ai_act_doc_generator.generate_risk_assessment_report(
                ai_system_data, 
                classification_data
            )
            title = f"Risk Assessment Report - {system['name']}"
        elif request.document_type == 'technical_documentation':
            html_content = ai_act_doc_generator.generate_technical_documentation_template(ai_system_data)
            title = f"Technische Dokumentation - {system['name']}"
        else:
            html_content = ai_act_doc_generator.generate_conformity_declaration(ai_system_data)
            title = f"EU-Konformitätserklärung - {system['name']}"
        
        doc_id = uuid.uuid4()
        import json
        content_json = json.dumps({"html": html_content})
        insert_query = """
            INSERT INTO ai_documentation (id, ai_system_id, document_type, title, content, status, version, created_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, 'generated', '1.0', NOW())
            RETURNING id, created_at
        """
        result = await db_service.pool.fetchrow(
            insert_query,
            doc_id,
            uuid.UUID(system_id),
            request.document_type,
            title,
            content_json
        )
        
        return {
            "success": True,
            "document": {
                "id": str(result['id']),
                "document_type": request.document_type,
                "title": title,
                "status": "generated",
                "version": "1.0",
                "created_at": result['created_at'].isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dokumentgenerierung fehlgeschlagen: {str(e)}"
        )

@router.get("/documentation/{doc_id}/download")
async def download_documentation(
    doc_id: str,
    format: str = "html",
    user_id: int = Depends(get_current_user_id)
):
    """
    Download generierte Dokumentation als HTML oder PDF
    """
    
    doc_query = """
        SELECT d.*, s.user_id 
        FROM ai_documentation d
        JOIN ai_systems s ON d.ai_system_id = s.id
        WHERE d.id = $1 AND s.user_id = $2
    """
    doc = await db_service.pool.fetchrow(doc_query, uuid.UUID(doc_id), user_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    content_data = doc['content']
    if isinstance(content_data, dict):
        html_content = content_data.get('html', '')
    elif isinstance(content_data, str):
        import json
        try:
            parsed = json.loads(content_data)
            html_content = parsed.get('html', content_data)
        except:
            html_content = content_data
    else:
        html_content = str(content_data)
    
    filename_base = doc['title'].replace(' ', '_').replace('/', '-')
    
    if format == "pdf":
        try:
            import pdfkit
            pdf_bytes = pdfkit.from_string(html_content, False, options={
                'encoding': 'UTF-8',
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm'
            })
            
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.pdf"
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF-Generierung fehlgeschlagen: {str(e)}. Versuchen Sie HTML-Export."
            )
    else:
        return StreamingResponse(
            io.BytesIO(html_content.encode('utf-8')),
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={filename_base}.html"
            }
        )

@router.get("/systems/{system_id}/documentation/list")
async def list_system_documentation(
    system_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Liste alle generierten Dokumente für ein KI-System
    """
    
    check_query = "SELECT id FROM ai_systems WHERE id = $1 AND user_id = $2"
    system = await db_service.pool.fetchrow(check_query, uuid.UUID(system_id), user_id)
    
    if not system:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    docs_query = """
        SELECT id, document_type, title, status, version, created_at, updated_at
        FROM ai_documentation 
        WHERE ai_system_id = $1 
        ORDER BY created_at DESC
    """
    docs = await db_service.pool.fetch(docs_query, uuid.UUID(system_id))
    
    return {
        "documents": [
            {
                "id": str(doc['id']),
                "document_type": doc['document_type'],
                "title": doc['title'],
                "status": doc['status'],
                "version": doc['version'],
                "created_at": doc['created_at'].isoformat() if doc['created_at'] else None,
                "updated_at": doc['updated_at'].isoformat() if doc['updated_at'] else None
            }
            for doc in docs
        ]
    }

# ==================== DOCUMENT UPLOAD ====================

@router.post("/systems/{system_id}/documentation/upload")
async def upload_documentation(
    system_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: str = Form(None),
    user_id: int = Depends(get_current_user_id)
):
    """
    Upload eines Dokuments für ein KI-System
    """
    
    check_query = "SELECT id, name FROM ai_systems WHERE id = $1 AND user_id = $2"
    system = await db_service.pool.fetchrow(check_query, uuid.UUID(system_id), user_id)
    
    if not system:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    file_content = await file.read()
    file_size = len(file_content)
    
    is_valid, error_msg = file_storage.validate_file(
        file.filename,
        file.content_type,
        file_size
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        file_info = await file_storage.save_file(
            user_id=user_id,
            file_content=file_content,
            original_filename=file.filename,
            system_id=system_id
        )
        
        existing_query = """
            SELECT id, version FROM ai_documentation 
            WHERE ai_system_id = $1 AND document_type = $2
            ORDER BY version DESC LIMIT 1
        """
        existing_doc = await db_service.pool.fetchrow(
            existing_query, 
            uuid.UUID(system_id), 
            document_type
        )
        
        new_version = 1
        if existing_doc:
            new_version = (existing_doc['version'] or 0) + 1
        
        doc_title = title or f"{document_type.replace('_', ' ').title()} - {system['name']}"
        
        doc_id = uuid.uuid4()
        import json
        content_json = json.dumps({
            "type": "uploaded",
            "file_path": file_info['relative_path'],
            "original_filename": file_info['original_filename'],
            "file_size": file_info['file_size'],
            "content_type": file_info['content_type'],
            "file_hash": file_info['file_hash']
        })
        
        insert_query = """
            INSERT INTO ai_documentation 
            (id, ai_system_id, document_type, title, content, file_url, status, version, created_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, 'uploaded', $7, NOW())
            RETURNING id, created_at
        """
        result = await db_service.pool.fetchrow(
            insert_query,
            doc_id,
            uuid.UUID(system_id),
            document_type,
            doc_title,
            content_json,
            file_info['relative_path'],
            new_version
        )
        
        return {
            "success": True,
            "document": {
                "id": str(result['id']),
                "document_type": document_type,
                "title": doc_title,
                "status": "uploaded",
                "version": str(new_version),
                "filename": file_info['original_filename'],
                "file_size": file_info['file_size'],
                "created_at": result['created_at'].isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload fehlgeschlagen: {str(e)}"
        )

@router.get("/documentation/file/{file_path:path}")
async def download_uploaded_file(
    file_path: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Download einer hochgeladenen Datei
    """
    
    doc_query = """
        SELECT d.*, s.user_id 
        FROM ai_documentation d
        JOIN ai_systems s ON d.ai_system_id = s.id
        WHERE d.file_url = $1 AND s.user_id = $2
    """
    doc = await db_service.pool.fetchrow(doc_query, file_path, user_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden oder kein Zugriff")
    
    file_content = await file_storage.get_file(file_path)
    
    if not file_content:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    content_data = doc['content']
    if isinstance(content_data, dict):
        content_type = content_data.get('content_type', 'application/octet-stream')
        original_filename = content_data.get('original_filename', 'document')
    else:
        import json
        try:
            parsed = json.loads(content_data) if isinstance(content_data, str) else {}
            content_type = parsed.get('content_type', 'application/octet-stream')
            original_filename = parsed.get('original_filename', 'document')
        except:
            content_type = 'application/octet-stream'
            original_filename = 'document'
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={original_filename}"
        }
    )

@router.delete("/documentation/{doc_id}")
async def delete_documentation(
    doc_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Lösche ein Dokument
    """
    
    doc_query = """
        SELECT d.*, s.user_id 
        FROM ai_documentation d
        JOIN ai_systems s ON d.ai_system_id = s.id
        WHERE d.id = $1 AND s.user_id = $2
    """
    doc = await db_service.pool.fetchrow(doc_query, uuid.UUID(doc_id), user_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    if doc['file_url']:
        await file_storage.delete_file(doc['file_url'])
    
    delete_query = "DELETE FROM ai_documentation WHERE id = $1"
    await db_service.pool.execute(delete_query, uuid.UUID(doc_id))
    
    return {"success": True, "message": "Dokument gelöscht"}

@router.get("/documentation/{doc_id}/versions")
async def get_document_versions(
    doc_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole alle Versionen eines Dokuments
    """
    
    doc_query = """
        SELECT d.document_type, d.ai_system_id, s.user_id 
        FROM ai_documentation d
        JOIN ai_systems s ON d.ai_system_id = s.id
        WHERE d.id = $1 AND s.user_id = $2
    """
    doc = await db_service.pool.fetchrow(doc_query, uuid.UUID(doc_id), user_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    versions_query = """
        SELECT id, title, status, version, created_at, updated_at
        FROM ai_documentation
        WHERE ai_system_id = $1 AND document_type = $2
        ORDER BY version DESC
    """
    versions = await db_service.pool.fetch(
        versions_query, 
        doc['ai_system_id'], 
        doc['document_type']
    )
    
    return {
        "versions": [
            {
                "id": str(v['id']),
                "title": v['title'],
                "status": v['status'],
                "version": v['version'],
                "created_at": v['created_at'].isoformat() if v['created_at'] else None,
                "updated_at": v['updated_at'].isoformat() if v['updated_at'] else None
            }
            for v in versions
        ]
    }

# ==================== NOTIFICATIONS ====================

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole alle Benachrichtigungen für den User
    """
    
    query = """
        SELECT id, ai_system_id, notification_type, severity, title, message, 
               metadata, is_read, created_at
        FROM ai_compliance_notifications
        WHERE user_id = $1
    """
    
    if unread_only:
        query += " AND is_read = FALSE"
    
    query += " ORDER BY created_at DESC LIMIT $2"
    
    notifications = await db_service.pool.fetch(query, user_id, limit)
    
    return {
        "notifications": [
            {
                "id": str(n['id']),
                "ai_system_id": str(n['ai_system_id']) if n['ai_system_id'] else None,
                "type": n['notification_type'],
                "severity": n['severity'],
                "title": n['title'],
                "message": n['message'],
                "metadata": n['metadata'] if isinstance(n['metadata'], dict) else {},
                "is_read": n['is_read'],
                "created_at": n['created_at'].isoformat() if n['created_at'] else None
            }
            for n in notifications
        ],
        "unread_count": sum(1 for n in notifications if not n['is_read'])
    }

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Markiere Benachrichtigung als gelesen
    """
    
    query = """
        UPDATE ai_compliance_notifications 
        SET is_read = TRUE, read_at = NOW()
        WHERE id = $1 AND user_id = $2
        RETURNING id
    """
    result = await db_service.pool.fetchrow(query, uuid.UUID(notification_id), user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Benachrichtigung nicht gefunden")
    
    return {"success": True}

@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    user_id: int = Depends(get_current_user_id)
):
    """
    Markiere alle Benachrichtigungen als gelesen
    """
    
    query = """
        UPDATE ai_compliance_notifications 
        SET is_read = TRUE, read_at = NOW()
        WHERE user_id = $1 AND is_read = FALSE
    """
    await db_service.pool.execute(query, user_id)
    
    return {"success": True}

# ==================== ALERT SETTINGS ====================

class AlertSettingsUpdate(BaseModel):
    email_on_compliance_drop: Optional[bool] = None
    email_on_high_risk: Optional[bool] = None
    email_on_scan_reminder: Optional[bool] = None
    email_on_scan_completed: Optional[bool] = None
    compliance_drop_threshold: Optional[int] = None
    scan_reminder_days: Optional[int] = None
    inapp_notifications: Optional[bool] = None

@router.get("/settings/alerts")
async def get_alert_settings(
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole Alert-Einstellungen des Users
    """
    
    query = """
        SELECT * FROM ai_compliance_alert_settings WHERE user_id = $1
    """
    settings = await db_service.pool.fetchrow(query, user_id)
    
    if not settings:
        return {
            "email_on_compliance_drop": True,
            "email_on_high_risk": True,
            "email_on_scan_reminder": True,
            "email_on_scan_completed": False,
            "compliance_drop_threshold": 10,
            "scan_reminder_days": 30,
            "inapp_notifications": True
        }
    
    return {
        "email_on_compliance_drop": settings['email_on_compliance_drop'],
        "email_on_high_risk": settings['email_on_high_risk'],
        "email_on_scan_reminder": settings['email_on_scan_reminder'],
        "email_on_scan_completed": settings['email_on_scan_completed'],
        "compliance_drop_threshold": settings['compliance_drop_threshold'],
        "scan_reminder_days": settings['scan_reminder_days'],
        "inapp_notifications": settings['inapp_notifications']
    }

@router.put("/settings/alerts")
async def update_alert_settings(
    settings: AlertSettingsUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Aktualisiere Alert-Einstellungen
    """
    
    existing = await db_service.pool.fetchrow(
        "SELECT id FROM ai_compliance_alert_settings WHERE user_id = $1",
        user_id
    )
    
    if existing:
        updates = []
        values = [user_id]
        idx = 2
        
        for field, value in settings.dict(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ${idx}")
                values.append(value)
                idx += 1
        
        if updates:
            query = f"""
                UPDATE ai_compliance_alert_settings 
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE user_id = $1
            """
            await db_service.pool.execute(query, *values)
    else:
        data = settings.dict(exclude_unset=True)
        query = """
            INSERT INTO ai_compliance_alert_settings (id, user_id, email_on_compliance_drop, 
                email_on_high_risk, email_on_scan_reminder, email_on_scan_completed,
                compliance_drop_threshold, scan_reminder_days, inapp_notifications)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        await db_service.pool.execute(
            query,
            uuid.uuid4(),
            user_id,
            data.get('email_on_compliance_drop', True),
            data.get('email_on_high_risk', True),
            data.get('email_on_scan_reminder', True),
            data.get('email_on_scan_completed', False),
            data.get('compliance_drop_threshold', 10),
            data.get('scan_reminder_days', 30),
            data.get('inapp_notifications', True)
        )
    
    return {"success": True}

# ==================== SCHEDULED SCANS ====================

class ScheduledScanCreate(BaseModel):
    schedule_type: str = Field(..., description="daily, weekly, monthly")
    schedule_day: Optional[int] = None
    schedule_hour: int = 9

@router.post("/systems/{system_id}/schedule")
async def create_scheduled_scan(
    system_id: str,
    schedule: ScheduledScanCreate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Erstelle einen geplanten Scan für ein KI-System
    """
    
    check_query = "SELECT id FROM ai_systems WHERE id = $1 AND user_id = $2"
    system = await db_service.pool.fetchrow(check_query, uuid.UUID(system_id), user_id)
    
    if not system:
        raise HTTPException(status_code=404, detail="KI-System nicht gefunden")
    
    if schedule.schedule_type not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(status_code=400, detail="Ungültiger schedule_type")
    
    now = datetime.utcnow()
    next_run = now.replace(hour=schedule.schedule_hour, minute=0, second=0, microsecond=0)
    
    if next_run <= now:
        next_run += timedelta(days=1)
    
    if schedule.schedule_type == 'weekly' and schedule.schedule_day is not None:
        days_until = (schedule.schedule_day - next_run.weekday()) % 7
        if days_until == 0 and next_run <= now:
            days_until = 7
        next_run += timedelta(days=days_until)
    elif schedule.schedule_type == 'monthly' and schedule.schedule_day is not None:
        next_run = next_run.replace(day=min(schedule.schedule_day, 28))
        if next_run <= now:
            if next_run.month == 12:
                next_run = next_run.replace(year=next_run.year + 1, month=1)
            else:
                next_run = next_run.replace(month=next_run.month + 1)
    
    existing = await db_service.pool.fetchrow(
        "SELECT id FROM ai_scheduled_scans WHERE ai_system_id = $1",
        uuid.UUID(system_id)
    )
    
    if existing:
        query = """
            UPDATE ai_scheduled_scans 
            SET schedule_type = $1, schedule_day = $2, schedule_hour = $3, 
                next_run_at = $4, is_active = TRUE, updated_at = NOW()
            WHERE ai_system_id = $5
            RETURNING id
        """
        result = await db_service.pool.fetchrow(
            query,
            schedule.schedule_type,
            schedule.schedule_day,
            schedule.schedule_hour,
            next_run,
            uuid.UUID(system_id)
        )
    else:
        query = """
            INSERT INTO ai_scheduled_scans (id, user_id, ai_system_id, schedule_type, 
                schedule_day, schedule_hour, next_run_at, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
            RETURNING id
        """
        result = await db_service.pool.fetchrow(
            query,
            uuid.uuid4(),
            user_id,
            uuid.UUID(system_id),
            schedule.schedule_type,
            schedule.schedule_day,
            schedule.schedule_hour,
            next_run
        )
    
    return {
        "success": True,
        "schedule": {
            "id": str(result['id']),
            "schedule_type": schedule.schedule_type,
            "schedule_day": schedule.schedule_day,
            "schedule_hour": schedule.schedule_hour,
            "next_run_at": next_run.isoformat()
        }
    }

@router.get("/systems/{system_id}/schedule")
async def get_scheduled_scan(
    system_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole geplanten Scan für ein KI-System
    """
    
    query = """
        SELECT s.* FROM ai_scheduled_scans s
        JOIN ai_systems sys ON s.ai_system_id = sys.id
        WHERE s.ai_system_id = $1 AND sys.user_id = $2
    """
    schedule = await db_service.pool.fetchrow(query, uuid.UUID(system_id), user_id)
    
    if not schedule:
        return {"schedule": None}
    
    return {
        "schedule": {
            "id": str(schedule['id']),
            "schedule_type": schedule['schedule_type'],
            "schedule_day": schedule['schedule_day'],
            "schedule_hour": schedule['schedule_hour'],
            "is_active": schedule['is_active'],
            "last_run_at": schedule['last_run_at'].isoformat() if schedule['last_run_at'] else None,
            "next_run_at": schedule['next_run_at'].isoformat() if schedule['next_run_at'] else None
        }
    }

@router.delete("/systems/{system_id}/schedule")
async def delete_scheduled_scan(
    system_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Lösche geplanten Scan
    """
    
    query = """
        UPDATE ai_scheduled_scans s
        SET is_active = FALSE, updated_at = NOW()
        FROM ai_systems sys
        WHERE s.ai_system_id = sys.id 
        AND s.ai_system_id = $1 
        AND sys.user_id = $2
        RETURNING s.id
    """
    result = await db_service.pool.fetchrow(query, uuid.UUID(system_id), user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Geplanter Scan nicht gefunden")
    
    return {"success": True}

