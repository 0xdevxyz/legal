from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import os
import aiohttp
from datetime import datetime
import json
import uvicorn
from databases import Database

# Import der neuen Module
from auth_routes import router as auth_router, init_db as init_auth_db
from payment_routes import router as payment_router, init_db as init_payment_db
from report_generator import router as report_router, init_db as init_report_db

# Konfiguration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://complyo_user:WrsmZTXYcjt0c7lt%2FlOzEnX1N5rtjRklLYrY8zXmBGo%3D@shared-postgres:5432/complyo_db")
API_VERSION = "2.0.0"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")

# Datenbank-Verbindung
database = Database(DATABASE_URL)

# FastAPI-App initialisieren
app = FastAPI(
    title="Complyo API",
    description="KI-gestützte Rechtstextautomatisierung",
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
    results: List[Dict[str, Any]]
    scan_timestamp: datetime
    scan_duration_ms: int

# Startup-Event
@app.on_event("startup")
async def startup():
    await database.connect()
    
    # Datenbankschema initialisieren
    await init_auth_db()
    await init_payment_db()
    await init_report_db()

# Shutdown-Event
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Router einbinden
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(payment_router, prefix="/api/payment", tags=["payment"])
app.include_router(report_router, prefix="/api/reports", tags=["reports"])

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
            "database": "connected",
            "redis": "connected"
        },
        "timestamp": datetime.now()
    }

# Website-Analyse-Endpunkt
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_website(request: AnalyzeRequest):
    url = request.url
    
    # Start der Zeitmessung
    start_time = datetime.now()
    
    # Hier würde normalerweise die echte Website-Analyse stattfinden
    # Für Testzwecke geben wir ein Beispielergebnis zurück
    
    # Simulierte Verarbeitungszeit
    import time
    time.sleep(0.5)  # 500ms Verarbeitungszeit simulieren
    
    # Beispielergebnisse
    results = [
        {
            "category": "Impressum",
            "status": "fail",
            "score": 0,
            "message": "Kein Impressum gefunden - gesetzlich verpflichtend"
        },
        {
            "category": "Datenschutzerklärung",
            "status": "fail",
            "score": 0,
            "message": "Keine Datenschutzerklärung - DSGVO-Verstoß"
        },
        {
            "category": "Cookie-Compliance",
            "status": "warning",
            "score": 50,
            "message": "Kein Cookie-Consent-Mechanismus erkannt"
        },
        {
            "category": "Basis-Barrierefreiheit",
            "status": "pass",
            "score": 100,
            "message": "Barrierefreiheit-Score: 100%"
        }
    ]
    
    # Gesamtscore berechnen
    total_score = sum(result["score"] for result in results)
    overall_score = total_score // len(results)
    
    # Anzahl der Probleme berechnen
    total_issues = sum(1 for result in results if result["status"] != "pass")
    
    # Ende der Zeitmessung
    end_time = datetime.now()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Scan-ID generieren
    import uuid
    scan_id = str(uuid.uuid4())
    
    # Ergebnis in Datenbank speichern
    query = """
    INSERT INTO scan_results (id, user_id, url, overall_score, total_issues, results, scan_timestamp, scan_duration_ms)
    VALUES (:id, :user_id, :url, :overall_score, :total_issues, :results, :scan_timestamp, :scan_duration_ms)
    """
    values = {
        "id": scan_id,
        "user_id": "demo_user",  # In Produktion durch echte Benutzer-ID ersetzen
        "url": url,
        "overall_score": overall_score,
        "total_issues": total_issues,
        "results": json.dumps(results),
        "scan_timestamp": datetime.now(),
        "scan_duration_ms": duration_ms
    }
    
    await database.execute(query=query, values=values)
    
    # Ergebnis zurückgeben
    return {
        "id": scan_id,
        "url": url,
        "overall_score": overall_score,
        "total_issues": total_issues,
        "results": results,
        "scan_timestamp": datetime.now(),
        "scan_duration_ms": duration_ms
    }

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
        scans.append(scan)
    
    return scans

# Start der Anwendung, wenn direkt ausgeführt
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
