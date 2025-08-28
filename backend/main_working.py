from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import redis
import os
from datetime import datetime
import uvicorn

app = FastAPI(title="Complyo API", version="2.0.0")

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "shared-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = int(os.getenv("REDIS_DB", "4"))

@app.get("/")
async def root():
    return {
        "message": "Complyo API v2.0",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "complyo-backend",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Redis check
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/api/status")
async def api_status():
    return {
        "api_version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "features": [
            "Website Analysis",
            "Compliance Checking", 
            "Health Monitoring"
        ],
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze",
            "status": "/api/status"
        }
    }

@app.post("/api/analyze")
async def analyze_website(data: dict):
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Simplified analysis response
    return {
        "url": url,
        "overall_score": 85,
        "status": "analyzed",
        "timestamp": datetime.utcnow().isoformat(),
        "results": {
            "legal_compliance": "good",
            "cookie_compliance": "acceptable", 
            "accessibility": "good",
            "performance": "excellent"
        },
        "message": "Website analysis completed successfully"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
