# report_generator.py - Add to your FastAPI backend

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import uuid
import jinja2
import pdfkit
import json
from auth_routes import get_current_active_user
from databases import Database

# Database setup - this will be imported from main.py context
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://complyo_user:WrsmZTXYcjt0c7lt%2FlOzEnX1N5rtjRklLYrY8zXmBGo%3D@shared-postgres:5432/complyo_db")
database = Database(DATABASE_URL)

# Configure router
router = APIRouter()

# Configure Jinja2 templates
template_loader = jinja2.FileSystemLoader(searchpath="./templates")
template_env = jinja2.Environment(loader=template_loader)

# Models
class ComplianceResult(BaseModel):
    url: str
    overall_score: int
    total_issues: int
    results: List[Dict[str, Any]]
    scan_timestamp: datetime
    scan_duration_ms: int

class ReportRequest(BaseModel):
    scan_id: str
    include_details: bool = True
    language: str = "de"  # de or en

class Report(BaseModel):
    id: str
    user_id: str
    scan_id: str
    created_at: datetime
    file_path: str
    url: Optional[str] = None

# Helper functions
def create_report_filename(user_id, url):
    """Create a unique filename for the report"""
    sanitized_url = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"report_{user_id[:8]}_{sanitized_url[:30]}_{timestamp}.pdf"
    return filename

async def get_scan_result(scan_id: str, user_id: str):
    """Retrieve scan result from database"""
    query = """
    SELECT * FROM scan_results 
    WHERE id = :scan_id AND user_id = :user_id
    """
    values = {"scan_id": scan_id, "user_id": user_id}
    result = await database.fetch_one(query=query, values=values)
    
    if not result:
        return None
    
    # Parse the JSON results field
    scan_data = dict(result)
    scan_data["results"] = json.loads(scan_data["results"])
    
    return scan_data

def risk_calculator(results):
    """Calculate financial risk from compliance issues"""
    risk_amounts = {
        "Impressum": {
            "fail": {"min": 500, "max": 3000},
            "warning": {"min": 100, "max": 500},
            "pass": {"min": 0, "max": 0}
        },
        "Datenschutzerklärung": {
            "fail": {"min": 1000, "max": 5000},
            "warning": {"min": 500, "max": 1000},
            "pass": {"min": 0, "max": 0}
        },
        "Cookie-Compliance": {
            "fail": {"min": 1000, "max": 5000},
            "warning": {"min": 500, "max": 2000},
            "pass": {"min": 0, "max": 0}
        },
        "Basis-Barrierefreiheit": {
            "fail": {"min": 500, "max": 2000},
            "warning": {"min": 100, "max": 500},
            "pass": {"min": 0, "max": 0}
        }
    }
    
    total_min = 0
    total_max = 0
    
    for result in results:
        category = result.get("category")
        status = result.get("status")
        
        if category in risk_amounts and status in risk_amounts[category]:
            total_min += risk_amounts[category][status]["min"]
            total_max += risk_amounts[category][status]["max"]
    
    return {"min": total_min, "max": total_max}

def generate_recommendations(results):
    """Generate specific recommendations based on issues"""
    recommendations = []
    
    for result in results:
        category = result.get("category")
        status = result.get("status")
        
        if status == "fail":
            if category == "Impressum":
                recommendations.append({
                    "priority": "Hoch",
                    "title": "Impressum erstellen",
                    "description": "Ein rechtsgültiges Impressum nach §5 TMG ist verpflichtend. "
                                  "Fügen Sie alle erforderlichen Angaben hinzu: Name, Anschrift, Kontaktdaten, "
                                  "Vertretungsberechtigte, Registernummer und -gericht, Umsatzsteuer-ID.",
                    "action": "Compliance-Fix aktivieren oder Experten-Service nutzen"
                })
            elif category == "Datenschutzerklärung":
                recommendations.append({
                    "priority": "Hoch",
                    "title": "Datenschutzerklärung erstellen",
                    "description": "Eine DSGVO-konforme Datenschutzerklärung ist gesetzlich verpflichtend. "
                                  "Informieren Sie über Datenverarbeitung, Rechtsgrundlagen und Betroffenenrechte.",
                    "action": "Compliance-Fix aktivieren oder Experten-Service nutzen"
                })
            elif category == "Cookie-Compliance":
                recommendations.append({
                    "priority": "Hoch", 
                    "title": "Cookie-Banner implementieren",
                    "description": "Cookies erfordern explizite Nutzereinwilligung nach TTDSG §25. "
                                  "Implementieren Sie einen rechtskonformen Cookie-Consent-Banner.",
                    "action": "Compliance-Fix aktivieren"
                })
            elif category == "Barrierefreiheit":
                recommendations.append({
                    "priority": "Mittel",
                    "title": "Barrierefreiheit verbessern", 
                    "description": "Verbessern Sie die Zugänglichkeit nach WCAG 2.1 AA Standards. "
                                  "Fügen Sie Alt-Texte hinzu und optimieren Sie die Keyboard-Navigation.",
                    "action": "Compliance-Fix aktivieren"
                })

        return recommendations

    def _generate_next_steps(self, scan_results: List[Dict], recommendations: List[Dict]) -> List[str]:
        """Generate actionable next steps"""
        next_steps = [
            "1. Kritische Compliance-Verstöße sofort beheben",
            "2. Rechtliche Texte (Impressum, Datenschutzerklärung) aktualisieren",
            "3. Cookie-Consent-Banner implementieren",
            "4. Barrierefreiheit schrittweise verbessern",
            "5. Regelmäßige Compliance-Checks durchführen"
        ]
        
        critical_issues = len([r for r in scan_results if r.get('status') == 'fail'])
        if critical_issues > 3:
            next_steps.insert(0, f"🚨 DRINGEND: {critical_issues} kritische Probleme sofort angehen!")
            
        return next_steps

# Database initialization
async def init_db():
    """Initialize reports table"""
    query = """
    CREATE TABLE IF NOT EXISTS reports (
        id VARCHAR(50) PRIMARY KEY,
        scan_id VARCHAR(50),
        user_id VARCHAR(50),
        title VARCHAR(200) NOT NULL,
        content TEXT NOT NULL,
        report_type VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        file_path VARCHAR(500)
    );
    
    CREATE INDEX IF NOT EXISTS idx_reports_scan_id ON reports(scan_id);
    CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
    """
    
    await database.execute(query=query)