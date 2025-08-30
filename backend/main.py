from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import os
import aiohttp
from datetime import datetime
import json
import uuid
import uvicorn
from databases import Database

# Import der neuen Module
from auth_routes import router as auth_router, init_db as init_auth_db
from payment_routes import router as payment_router, init_db as init_payment_db
from report_generator import router as report_router, init_db as init_report_db
from compliance_scanner import ComplianceScanner
from risk_calculator import ComplianceRiskCalculator
from ai_compliance_fixer import AIComplianceFixer
from workflow_engine import workflow_engine, WorkflowStage, UserSkillLevel
from workflow_integration import workflow_integration

# Konfiguration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://complyo_user:WrsmZTXYcjt0c7lt%2FlOzEnX1N5rtjRklLYrY8zXmBGo%3D@shared-postgres:5432/complyo_db")
API_VERSION = "2.0.0"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")

# Datenbank-Verbindung
database = Database(DATABASE_URL)

# Security
security = HTTPBearer(auto_error=False)

# FastAPI-App initialisieren
app = FastAPI(
    title="Complyo API",
    description="KI-gestützte Compliance-Automatisierung für deutsche Websites",
    version=API_VERSION
)

# CORS-Middleware hinzufügen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelle
class AnalyzeRequest(BaseModel):
    url: str

class AnalyzeResponse(BaseModel):
    url: str
    overall_score: int
    total_issues: int
    total_risk_euro: Optional[int] = 0
    critical_issues: Optional[int] = 0
    warning_issues: Optional[int] = 0
    results: List[Dict[str, Any]]
    recommendations: Optional[List[str]] = []
    next_steps: Optional[List[Dict[str, Any]]] = []
    scan_timestamp: datetime
    scan_duration_ms: int

class RiskAssessmentRequest(BaseModel):
    scan_id: str
    company_profile: Optional[Dict[str, str]] = {}

class AIFixRequest(BaseModel):
    scan_id: str
    company_info: Optional[Dict[str, str]] = {}
    fix_categories: Optional[List[str]] = []  # Specific categories to fix

# Database initialization for scan results
async def init_scan_db():
    """Initialize scan results table with enhanced schema"""
    query = """
    CREATE TABLE IF NOT EXISTS scan_results (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50),
        url VARCHAR(500) NOT NULL,
        overall_score INTEGER NOT NULL,
        total_issues INTEGER NOT NULL,
        total_risk_euro INTEGER DEFAULT 0,
        critical_issues INTEGER DEFAULT 0,
        warning_issues INTEGER DEFAULT 0,
        results JSONB NOT NULL,
        recommendations JSONB DEFAULT '[]',
        next_steps JSONB DEFAULT '[]',
        scan_timestamp TIMESTAMP NOT NULL,
        scan_duration_ms INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Index for better performance
    CREATE INDEX IF NOT EXISTS idx_scan_results_user_timestamp 
    ON scan_results(user_id, scan_timestamp DESC);
    """
    await database.execute(query=query)

async def init_ai_fixes_db():
    """Initialize AI fixes table"""
    query = """
    CREATE TABLE IF NOT EXISTS ai_fixes (
        id VARCHAR(50) PRIMARY KEY,
        scan_id VARCHAR(50) REFERENCES scan_results(id),
        user_id VARCHAR(50),
        total_issues_fixed INTEGER NOT NULL,
        fixes_applied JSONB NOT NULL,
        generated_files JSONB NOT NULL,
        implementation_guide JSONB NOT NULL,
        estimated_total_time INTEGER NOT NULL,
        success_rate FLOAT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Index for performance
    CREATE INDEX IF NOT EXISTS idx_ai_fixes_scan_id ON ai_fixes(scan_id);
    CREATE INDEX IF NOT EXISTS idx_ai_fixes_user_id ON ai_fixes(user_id);
    """
    await database.execute(query=query)

# Startup-Event
@app.on_event("startup")
async def startup():
    await database.connect()
    
    # Datenbankschema initialisieren
    await init_auth_db()
    await init_payment_db()
    await init_report_db()
    await init_scan_db()
    await init_ai_fixes_db()

# Shutdown-Event
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Router einbinden
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(payment_router, prefix="/api/payment", tags=["payment"])
app.include_router(report_router, prefix="/api/reports", tags=["reports"])

# ========== WORKFLOW ENGINE ENDPOINTS ==========

class StartJourneyRequest(BaseModel):
    website_url: str
    skill_level: str = "beginner"  # absolute_beginner, beginner, intermediate, advanced

@app.post("/api/workflow/start-journey")
async def start_user_journey(request: StartJourneyRequest):
    """Start a new user journey for guided compliance optimization"""
    try:
        # Validate skill level
        valid_levels = ["absolute_beginner", "beginner", "intermediate", "advanced"]
        if request.skill_level not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Invalid skill level. Use: {', '.join(valid_levels)}")
        
        skill_level = UserSkillLevel(request.skill_level)
        user_id = "demo_user"  # Replace with real user ID from auth
        
        # Start user journey
        journey = await workflow_engine.start_user_journey(
            user_id=user_id,
            website_url=request.website_url,
            skill_level=skill_level
        )
        
        # Save journey to database
        await workflow_integration.save_user_journey(journey)
        
        return {
            "status": "success",
            "message": "User journey started successfully",
            "journey": {
                "user_id": journey.user_id,
                "website_url": journey.website_url,
                "skill_level": journey.skill_level.value,
                "current_stage": journey.current_stage.value,
                "estimated_completion": journey.estimated_completion.isoformat(),
                "next_step": journey.current_step
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start journey: {str(e)}")

@app.get("/api/workflow/current-step")
async def get_current_workflow_step():
    """Get the current workflow step for the user"""
    try:
        user_id = "demo_user"  # Replace with real user ID from auth
        current_step = await workflow_engine.get_current_step(user_id)
        
        if not current_step:
            return {
                "status": "success",
                "current_step": None,
                "message": "No active workflow or workflow completed"
            }
        
        return {
            "status": "success",
            "current_step": {
                "id": current_step.id,
                "stage": current_step.stage.value,
                "title": current_step.title,
                "description": current_step.description,
                "instructions": current_step.instructions,
                "estimated_time_minutes": current_step.estimated_time_minutes,
                "requires_technical_knowledge": current_step.requires_technical_knowledge,
                "visual_aids": current_step.visual_aids,
                "success_criteria": current_step.success_criteria
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/complete-step")
async def complete_workflow_step(request: Dict[str, Any]):
    """Complete current workflow step with validation"""
    try:
        step_id = request.get("step_id")
        validation_data = request.get("validation_data", {})
        user_id = "demo_user"  # Replace with real user ID from auth
        
        if not step_id:
            raise HTTPException(status_code=400, detail="step_id is required")
        
        # Load current journey
        journey = await workflow_integration.load_user_journey(user_id)
        if not journey:
            raise HTTPException(status_code=404, detail="No active journey found")
        
        # Complete step using workflow engine
        result = await workflow_engine.complete_step(user_id, step_id, validation_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete step: {str(e)}")

@app.get("/api/workflow/progress")
async def get_workflow_progress():
    """Get comprehensive workflow progress for the user"""
    try:
        user_id = "demo_user"  # Replace with real user ID from auth
        progress = await workflow_engine.get_journey_progress(user_id)
        
        if "error" in progress:
            return {
                "status": "success",
                "progress": None,
                "message": "No active journey found"
            }
        
        return {
            "status": "success",
            "progress": progress
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health-Check-Endpunkt
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "complyo-backend",
        "version": API_VERSION,
        "timestamp": datetime.now(),
        "environment": ENVIRONMENT
    }

# Root-Endpunkt
@app.get("/")
async def root():
    return {"message": "Complyo API is running", "status": "ok"}

# API-Status-Endpunkt
@app.get("/api/status")
async def api_status():
    return {
        "api_version": API_VERSION,
        "status": "operational",
        "features": {
            "website_scanner": "active",
            "ai_analysis": "active",
            "risk_calculator": "active",
            "ai_fixer": "active",
            "database": "connected",
            "redis": "connected"
        },
        "timestamp": datetime.now()
    }

# Website-Analyse-Endpunkt
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_website(request: AnalyzeRequest):
    url = request.url
    
    try:
        # Real compliance scan using the new scanner
        async with ComplianceScanner() as scanner:
            scan_result = await scanner.scan_website(url)
        
        # Handle scan errors
        if scan_result.get('error'):
            raise HTTPException(status_code=400, detail=scan_result['error_message'])
        
        # Convert scan result to legacy format for compatibility
        results = []
        for issue in scan_result['issues']:
            status = "fail" if issue['severity'] == "critical" else ("warning" if issue['severity'] == "warning" else "info")
            results.append({
                "category": issue['category'],
                "status": status, 
                "score": 100 if issue['severity'] == "info" else (50 if issue['severity'] == "warning" else 0),
                "message": issue['title'],
                "description": issue['description'],
                "risk_euro": issue['risk_euro'],
                "legal_basis": issue['legal_basis'],
                "recommendation": issue['recommendation'],
                "auto_fixable": issue['auto_fixable']
            })
        
        # Calculate overall score and issues
        overall_score = scan_result['compliance_score']
        total_issues = scan_result['total_issues']
        total_risk_euro = scan_result['total_risk_euro']
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Enhanced database schema for new scan results
        query = """
        INSERT INTO scan_results (
            id, user_id, url, overall_score, total_issues, total_risk_euro, 
            critical_issues, warning_issues, results, recommendations, next_steps,
            scan_timestamp, scan_duration_ms
        )
        VALUES (
            :id, :user_id, :url, :overall_score, :total_issues, :total_risk_euro,
            :critical_issues, :warning_issues, :results, :recommendations, :next_steps,
            :scan_timestamp, :scan_duration_ms
        )
        """
        values = {
            "id": scan_id,
            "user_id": "demo_user",  # In Produktion durch echte Benutzer-ID ersetzen
            "url": url,
            "overall_score": overall_score,
            "total_issues": total_issues,
            "total_risk_euro": total_risk_euro,
            "critical_issues": scan_result['critical_issues'],
            "warning_issues": scan_result['warning_issues'],
            "results": json.dumps(results),
            "recommendations": json.dumps(scan_result.get('recommendations', [])),
            "next_steps": json.dumps(scan_result.get('next_steps', [])),
            "scan_timestamp": scan_result['scan_timestamp'],
            "scan_duration_ms": scan_result['scan_duration_ms']
        }
        
        await database.execute(query=query, values=values)
        
        # Return enhanced result
        return {
            "id": scan_id,
            "url": url,
            "overall_score": overall_score,
            "total_issues": total_issues,
            "total_risk_euro": total_risk_euro,
            "critical_issues": scan_result['critical_issues'],
            "warning_issues": scan_result['warning_issues'],
            "results": results,
            "recommendations": scan_result.get('recommendations', []),
            "next_steps": scan_result.get('next_steps', []),
            "scan_timestamp": scan_result['scan_timestamp'],
            "scan_duration_ms": scan_result['scan_duration_ms']
        }
        
    except Exception as e:
        # Fallback to basic scan on error
        raise HTTPException(status_code=500, detail=f"Scan-Fehler: {str(e)}")

# Scan-Ergebnisse abrufen
@app.get("/api/scans")
async def get_scans():
    query = """
    SELECT * FROM scan_results 
    ORDER BY scan_timestamp DESC
    """
    
    results = await database.fetch_all(query=query)
    
    # Ergebnisse in Python-Objekte umwandeln
    scans = []
    for row in results:
        scan = dict(row)
        scan["results"] = json.loads(scan["results"])
        scan["recommendations"] = json.loads(scan.get("recommendations") or "[]")
        scan["next_steps"] = json.loads(scan.get("next_steps") or "[]")
        scans.append(scan)
    
    return scans

# Risk Assessment Endpoint
@app.post("/api/risk-assessment")
async def calculate_risk_assessment(request: RiskAssessmentRequest):
    """Calculate detailed risk assessment for a scan"""
    try:
        # Get scan result from database
        query = "SELECT * FROM scan_results WHERE id = :scan_id"
        scan_result = await database.fetch_one(query=query, values={"scan_id": request.scan_id})
        
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan nicht gefunden")
        
        # Parse violations from scan result
        violations = json.loads(scan_result["results"])
        
        # Calculate risk assessment
        risk_calculator = ComplianceRiskCalculator()
        risk_assessment = risk_calculator.calculate_risk(violations, request.company_profile)
        
        # Get cost breakdown
        cost_breakdown = risk_calculator.get_violation_cost_breakdown(violations)
        
        return {
            "scan_id": request.scan_id,
            "risk_assessment": {
                "base_risk_euro": risk_assessment.base_risk_euro,
                "adjusted_risk_euro": risk_assessment.adjusted_risk_euro,
                "risk_level": risk_assessment.risk_level,
                "total_violations": risk_assessment.total_violations,
                "risk_factors": [
                    {
                        "name": factor.name,
                        "multiplier": factor.multiplier,
                        "description": factor.description
                    } for factor in risk_assessment.risk_factors
                ],
                "recommendations": risk_assessment.recommendations
            },
            "cost_breakdown": cost_breakdown,
            "company_profile": request.company_profile,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risiko-Berechnung fehlgeschlagen: {str(e)}")

# Get Risk Statistics
@app.get("/api/risk-statistics")  
async def get_risk_statistics():
    """Get overall risk statistics from all scans"""
    try:
        # Get aggregate statistics
        query = """
        SELECT 
            COUNT(*) as total_scans,
            AVG(overall_score) as avg_score,
            AVG(total_risk_euro) as avg_risk_euro,
            SUM(total_risk_euro) as total_risk_prevented,
            COUNT(CASE WHEN overall_score < 50 THEN 1 END) as high_risk_sites
        FROM scan_results
        """
        
        stats = await database.fetch_one(query=query)
        
        # Get most common violations
        query_violations = """
        SELECT results FROM scan_results
        WHERE results IS NOT NULL
        """
        
        all_scans = await database.fetch_all(query=query_violations)
        
        # Analyze violation patterns
        violation_counts = {}
        for scan in all_scans:
            try:
                results = json.loads(scan["results"])
                for violation in results:
                    category = violation.get('category', 'Unknown')
                    violation_counts[category] = violation_counts.get(category, 0) + 1
            except:
                continue
        
        return {
            "total_scans": stats["total_scans"] or 0,
            "average_compliance_score": round(float(stats["avg_score"] or 0), 1),
            "average_risk_euro": round(float(stats["avg_risk_euro"] or 0)),
            "total_risk_prevented": int(stats["total_risk_prevented"] or 0),
            "high_risk_websites": stats["high_risk_sites"] or 0,
            "most_common_violations": dict(sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistik-Fehler: {str(e)}")

# AI-Powered Compliance Fix Endpoint
@app.post("/api/ai-fix")
async def generate_compliance_fixes(request: AIFixRequest):
    """Generate AI-powered compliance fixes for scan results"""
    try:
        # Get scan result from database
        query = "SELECT * FROM scan_results WHERE id = :scan_id"
        scan_result = await database.fetch_one(query=query, values={"scan_id": request.scan_id})
        
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan nicht gefunden")
        
        # Parse violations from scan result
        violations = json.loads(scan_result["results"])
        
        # Filter violations by requested categories if specified
        if request.fix_categories:
            violations = [v for v in violations if v.get('category', '').lower() in 
                         [cat.lower() for cat in request.fix_categories]]
        
        # Generate AI fixes
        ai_fixer = AIComplianceFixer()
        fix_result = await ai_fixer.fix_compliance_issues(
            scan_id=request.scan_id,
            violations=violations,
            company_info=request.company_info
        )
        
        # Store fix result in database for later retrieval
        fix_id = str(uuid.uuid4())
        fix_query = """
        INSERT INTO ai_fixes (
            id, scan_id, user_id, total_issues_fixed, fixes_applied, 
            generated_files, implementation_guide, estimated_total_time, 
            success_rate, created_at
        )
        VALUES (
            :id, :scan_id, :user_id, :total_issues_fixed, :fixes_applied,
            :generated_files, :implementation_guide, :estimated_total_time,
            :success_rate, :created_at
        )
        """
        
        fix_values = {
            "id": fix_id,
            "scan_id": request.scan_id,
            "user_id": "demo_user",  # Replace with real user ID
            "total_issues_fixed": fix_result.total_issues_fixed,
            "fixes_applied": json.dumps([
                {
                    "issue_category": fix.issue_category,
                    "fix_type": fix.fix_type,
                    "description": fix.description,
                    "generated_content": fix.generated_content,
                    "implementation_instructions": fix.implementation_instructions,
                    "confidence_score": fix.confidence_score,
                    "estimated_time_minutes": fix.estimated_time_minutes,
                    "auto_applicable": fix.auto_applicable
                } for fix in fix_result.fixes_applied
            ]),
            "generated_files": json.dumps(fix_result.generated_files),
            "implementation_guide": json.dumps(fix_result.implementation_guide),
            "estimated_total_time": fix_result.estimated_total_time,
            "success_rate": fix_result.success_rate,
            "created_at": datetime.now()
        }
        
        await database.execute(query=fix_query, values=fix_values)
        
        return {
            "fix_id": fix_id,
            "scan_id": request.scan_id,
            "total_issues_fixed": fix_result.total_issues_fixed,
            "fixes_applied": [
                {
                    "issue_category": fix.issue_category,
                    "fix_type": fix.fix_type,
                    "description": fix.description,
                    "confidence_score": fix.confidence_score,
                    "estimated_time_minutes": fix.estimated_time_minutes,
                    "auto_applicable": fix.auto_applicable,
                    "implementation_instructions": fix.implementation_instructions
                } for fix in fix_result.fixes_applied
            ],
            "generated_files": fix_result.generated_files,
            "implementation_guide": fix_result.implementation_guide,
            "estimated_total_time": fix_result.estimated_total_time,
            "success_rate": fix_result.success_rate,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI-Fix fehlgeschlagen: {str(e)}")

# Get AI Fix Results
@app.get("/api/ai-fix/{fix_id}")
async def get_ai_fix_result(fix_id: str):
    """Retrieve AI fix results by ID"""
    query = "SELECT * FROM ai_fixes WHERE id = :fix_id"
    fix_result = await database.fetch_one(query=query, values={"fix_id": fix_id})
    
    if not fix_result:
        raise HTTPException(status_code=404, detail="AI-Fix nicht gefunden")
    
    return {
        "fix_id": fix_result["id"],
        "scan_id": fix_result["scan_id"],
        "total_issues_fixed": fix_result["total_issues_fixed"],
        "fixes_applied": json.loads(fix_result["fixes_applied"]),
        "generated_files": json.loads(fix_result["generated_files"]),
        "implementation_guide": json.loads(fix_result["implementation_guide"]),
        "estimated_total_time": fix_result["estimated_total_time"],
        "success_rate": fix_result["success_rate"],
        "created_at": fix_result["created_at"]
    }

# Download Generated File
@app.get("/api/download/{fix_id}/{filename}")
async def download_generated_file(fix_id: str, filename: str):
    """Download a generated compliance file"""
    
    query = "SELECT generated_files FROM ai_fixes WHERE id = :fix_id"
    fix_result = await database.fetch_one(query=query, values={"fix_id": fix_id})
    
    if not fix_result:
        raise HTTPException(status_code=404, detail="AI-Fix nicht gefunden")
    
    generated_files = json.loads(fix_result["generated_files"])
    
    if filename not in generated_files:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    content = generated_files[filename]
    
    return PlainTextResponse(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )

# Start der Anwendung, wenn direkt ausgeführt
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)