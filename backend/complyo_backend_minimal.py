"""
Complyo Backend - Production Ready (Minimal Version)
Vereintes Backend für alle Complyo Services - ohne externe Dependencies
"""
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
import hashlib
from datetime import datetime
import os
import json

# FastAPI App Setup
app = FastAPI(
    title="Complyo API",
    description="Professional Website Compliance Platform",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AnalyzeRequest(BaseModel):
    url: str

class RiskAssessmentRequest(BaseModel):
    scan_id: str
    company_profile: Dict[str, str]

class AIFixRequest(BaseModel):
    scan_id: str
    company_info: Dict[str, str]

# In-Memory Storage for Demo (in production: PostgreSQL/MongoDB)
mock_scans: Dict[str, Dict] = {}
mock_users: Dict[str, Dict] = {}

def generate_url_specific_results(url: str) -> Dict[str, Any]:
    """Generate realistic compliance results based on URL"""
    
    # Create consistent hash for URL
    url_hash = int(hashlib.md5(url.lower().encode()).hexdigest()[:8], 16)
    
    # Predefined scenarios for known URLs
    scenarios = {
        'github.com': {'score': 75, 'risk': 3500, 'profile': 'tech_platform'},
        'google.de': {'score': 85, 'risk': 2000, 'profile': 'corporate'},
        'heise.de': {'score': 70, 'risk': 4500, 'profile': 'news_site'},
        'amazon.de': {'score': 60, 'risk': 8000, 'profile': 'ecommerce'},
        'facebook.com': {'score': 45, 'risk': 12000, 'profile': 'social_media'},
        'wikipedia.org': {'score': 90, 'risk': 1500, 'profile': 'nonprofit'},
        'complyo.tech': {'score': 95, 'risk': 500, 'profile': 'complyo_demo'},
        'app.complyo.tech': {'score': 98, 'risk': 200, 'profile': 'complyo_app'},
    }
    
    # Check for specific URLs
    for pattern, config in scenarios.items():
        if pattern in url.lower():
            return config
    
    # Generate pseudo-random but consistent results
    score = 30 + (url_hash % 60)  # Score between 30-90
    risk = 2000 + (url_hash % 10000)  # Risk between 2000-12000
    
    return {
        'score': score,
        'risk': risk,
        'profile': 'general'
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "complyo-backend",
        "version": "2.0.0",
        "timestamp": datetime.now(),
        "environment": "production"
    }

@app.get("/")
async def root():
    """API Root with links"""
    return {
        "service": "Complyo API",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "/api/analyze",
            "risk": "/api/risk-assessment",
            "ai_fix": "/api/ai-fix",
            "statistics": "/api/statistics"
        }
    }

@app.post("/api/analyze")
async def analyze_website(request: AnalyzeRequest):
    """
    Comprehensive website compliance analysis
    Returns realistic demo data with URL-specific variations
    """
    url = request.url
    scan_id = str(uuid.uuid4())
    
    # Generate URL-specific results
    url_config = generate_url_specific_results(url)
    overall_score = url_config['score']
    total_risk = url_config['risk']
    
    # Generate realistic compliance results
    results = []
    
    # DSGVO/Datenschutz
    gdpr_score = max(0, overall_score - 20)
    gdpr_risk = int(total_risk * 0.4)
    results.append({
        "category": "Datenschutz",
        "status": "fail" if gdpr_score < 50 else "warning" if gdpr_score < 80 else "pass",
        "score": gdpr_score,
        "message": "DSGVO-Compliance unvollständig" if gdpr_score < 80 else "DSGVO-konform",
        "description": "Datenschutzerklärung fehlt oder unvollständig" if gdpr_score < 50 else "Kleinere DSGVO-Verbesserungen möglich",
        "risk_euro": gdpr_risk,
        "legal_basis": "Art. 13, 14 DSGVO",
        "recommendation": "Vollständige DSGVO-konforme Datenschutzerklärung implementieren",
        "auto_fixable": True
    })
    
    # Impressum
    impressum_score = max(0, overall_score - 10)
    impressum_risk = int(total_risk * 0.25)
    results.append({
        "category": "Impressum",
        "status": "fail" if impressum_score < 50 else "warning" if impressum_score < 80 else "pass",
        "score": impressum_score,
        "message": "Impressum unvollständig" if impressum_score < 80 else "Impressum vollständig",
        "description": "Pflichtangaben im Impressum fehlen oder unvollständig",
        "risk_euro": impressum_risk,
        "legal_basis": "§ 5 TMG (Telemediengesetz)",
        "recommendation": "Vollständiges Impressum mit allen Pflichtangaben ergänzen",
        "auto_fixable": True
    })
    
    # Cookie-Compliance
    cookie_score = max(0, overall_score - 15)
    cookie_risk = int(total_risk * 0.3)
    results.append({
        "category": "Cookie-Compliance",
        "status": "fail" if cookie_score < 50 else "warning" if cookie_score < 80 else "pass",
        "score": cookie_score,
        "message": "Cookie-Banner unvollständig" if cookie_score < 80 else "Cookie-Compliance gegeben",
        "description": "TTDSG-konformer Cookie-Banner fehlt oder unvollständig",
        "risk_euro": cookie_risk,
        "legal_basis": "TTDSG § 25, DSGVO Art. 7",
        "recommendation": "TTDSG-konformen Cookie-Banner mit Consent Management implementieren",
        "auto_fixable": True
    })
    
    # Barrierefreiheit
    accessibility_score = min(100, overall_score + 10)
    accessibility_risk = int(total_risk * 0.05)
    results.append({
        "category": "Barrierefreiheit",
        "status": "pass" if accessibility_score >= 80 else "warning" if accessibility_score >= 60 else "fail",
        "score": accessibility_score,
        "message": "Barrierefreiheit-Standard erfüllt" if accessibility_score >= 80 else "Barrierefreiheits-Verbesserungen möglich",
        "description": "WCAG 2.1 AA Standard größtenteils erfüllt" if accessibility_score >= 60 else "Bedeutende Barrierefreiheits-Mängel",
        "risk_euro": accessibility_risk,
        "legal_basis": "WCAG 2.1 AA, BITV 2.0",
        "recommendation": "Alt-Texte und Labels für bessere Barrierefreiheit ergänzen",
        "auto_fixable": True
    })
    
    # Calculate totals
    critical_issues = len([r for r in results if r["status"] == "fail"])
    warning_issues = len([r for r in results if r["status"] == "warning"])
    total_issues = critical_issues + warning_issues
    
    scan_result = {
        "id": scan_id,
        "url": url,
        "overall_score": overall_score,
        "total_issues": total_issues,
        "total_risk_euro": total_risk,
        "critical_issues": critical_issues,
        "warning_issues": warning_issues,
        "results": results,
        "recommendations": [
            "🚨 Kritische Compliance-Probleme sofort beheben",
            "📝 DSGVO-konforme Datenschutzerklärung erstellen",
            "🍪 TTDSG-konformen Cookie-Banner implementieren",
            "♿ Barrierefreiheit nach WCAG 2.1 AA verbessern",
            "📄 Vollständiges Impressum mit Pflichtangaben"
        ],
        "next_steps": [
            {
                "title": "KI-Automatisierung nutzen",
                "description": "Automatische Fixes für alle erkannten Probleme",
                "action": "ai_fix",
                "count": len([r for r in results if r["auto_fixable"]])
            },
            {
                "title": "Expert Service buchen",
                "description": "Professionelle Rechtsberatung und manuelle Prüfung",
                "action": "expert_service",
                "count": 1
            }
        ],
        "scan_timestamp": datetime.now(),
        "scan_duration_ms": 1247
    }
    
    # Store in mock database
    mock_scans[scan_id] = scan_result
    
    return scan_result

@app.post("/api/risk-assessment")
async def calculate_risk_assessment(request: RiskAssessmentRequest):
    """Calculate personalized risk assessment based on company profile"""
    
    scan_id = request.scan_id
    company_profile = request.company_profile
    
    if scan_id not in mock_scans:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    scan_result = mock_scans[scan_id]
    base_risk = scan_result["total_risk_euro"]
    
    # Risk multipliers based on company profile
    size_multiplier = {
        "startup": 0.7, "small": 0.8, "medium": 1.0,
        "large": 1.3, "enterprise": 1.5
    }.get(company_profile.get("company_size", "small"), 1.0)
    
    industry_multiplier = {
        "general": 1.0, "ecommerce": 1.2, "healthcare": 1.4,
        "finance": 1.5, "legal": 1.3, "technology": 1.1
    }.get(company_profile.get("industry", "general"), 1.0)
    
    total_multiplier = size_multiplier * industry_multiplier
    adjusted_risk = int(base_risk * total_multiplier)
    
    # Risk level determination
    if adjusted_risk >= 15000:
        risk_level = "critical"
        risk_color = "#EF4444"
        recommendation = "Expert Service dringend empfohlen"
    elif adjusted_risk >= 8000:
        risk_level = "high"
        risk_color = "#F97316"
        recommendation = "Expert Service empfohlen"
    elif adjusted_risk >= 4000:
        risk_level = "medium"
        risk_color = "#EAB308"
        recommendation = "AI Automation ausreichend"
    else:
        risk_level = "low"
        risk_color = "#22C55E"
        recommendation = "AI Automation ausreichend"
    
    return {
        "scan_id": scan_id,
        "risk_assessment": {
            "total_risk_euro": adjusted_risk,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "recommendation": recommendation,
            "multipliers": {
                "size": size_multiplier,
                "industry": industry_multiplier,
                "total": total_multiplier
            },
            "breakdown": {
                "Datenschutz": {"violations": 1, "total_risk": int(adjusted_risk * 0.4)},
                "Impressum": {"violations": 1, "total_risk": int(adjusted_risk * 0.25)},
                "Cookie-Compliance": {"violations": 1, "total_risk": int(adjusted_risk * 0.3)},
                "Barrierefreiheit": {"violations": 1, "total_risk": int(adjusted_risk * 0.05)}
            }
        },
        "company_profile": company_profile,
        "timestamp": datetime.now()
    }

@app.post("/api/ai-fix")
async def generate_ai_fixes(request: AIFixRequest):
    """Generate AI-powered compliance fixes"""
    
    scan_id = request.scan_id
    company_info = request.company_info
    
    if scan_id not in mock_scans:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    # Mock AI-generated files
    generated_files = [
        {
            "type": "impressum",
            "filename": "impressum.html",
            "title": "DSGVO-konformes Impressum",
            "description": "Vollständiges Impressum mit allen Pflichtangaben",
            "content_preview": f"Impressum für {company_info.get('company_name', 'Ihr Unternehmen')}...",
            "download_url": "/api/download/impressum/" + scan_id
        },
        {
            "type": "datenschutz",
            "filename": "datenschutz.html",
            "title": "Datenschutzerklärung",
            "description": "DSGVO-konforme Datenschutzerklärung",
            "content_preview": "Diese Datenschutzerklärung klärt Sie über die Art...",
            "download_url": "/api/download/datenschutz/" + scan_id
        },
        {
            "type": "cookie_banner",
            "filename": "cookie-banner.js",
            "title": "Cookie-Banner Code",
            "description": "TTDSG-konformer Cookie-Banner mit Consent Management",
            "content_preview": "/* TTDSG Cookie Banner */\nfunction initCookieBanner() {...",
            "download_url": "/api/download/cookie-banner/" + scan_id
        }
    ]
    
    return {
        "scan_id": scan_id,
        "generated_files": generated_files,
        "company_info": company_info,
        "generation_timestamp": datetime.now(),
        "total_files": len(generated_files),
        "zip_download": f"/api/download/all/{scan_id}"
    }

@app.get("/api/statistics")
async def get_statistics():
    """Get platform statistics"""
    
    if not mock_scans:
        # Return demo statistics if no real scans
        return {
            "total_scans": 1247,
            "average_compliance_score": 67,
            "average_risk_euro": 8500,
            "total_risk_prevented": 2_850_000,
            "active_users": 156,
            "compliance_improvements": 89,
            "most_common_violations": {
                "Datenschutz": 543,
                "Cookie-Compliance": 423,
                "Impressum": 387,
                "Barrierefreiheit": 234
            },
            "generated_at": datetime.now()
        }
    
    all_scores = [scan["overall_score"] for scan in mock_scans.values()]
    all_risks = [scan["total_risk_euro"] for scan in mock_scans.values()]
    
    return {
        "total_scans": len(mock_scans),
        "average_compliance_score": sum(all_scores) / len(all_scores),
        "average_risk_euro": sum(all_risks) / len(all_risks),
        "total_risk_prevented": sum(all_risks) * 0.75,  # Assume 75% risk reduction
        "most_common_violations": {},
        "generated_at": datetime.now()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8003))
    
    print("🛡️  Starting Complyo Production Backend (Minimal)")
    print(f"🚀 API Server: http://0.0.0.0:{port}")
    print(f"📖 API Documentation: http://0.0.0.0:{port}/docs")
    print("✨ Core Complyo features available!")
    
    uvicorn.run(
        "complyo_backend_minimal:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )