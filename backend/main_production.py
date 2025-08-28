from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
import hashlib
import jwt
import datetime
import os
import asyncpg
import json

# Initialize FastAPI app
app = FastAPI(
    title="Complyo API",
    description="KI-gestützte Website-Compliance-Plattform",
    version="2.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
db_pool = None

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Pydantic Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: str
    name: str
    plan: str

# Database functions
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)

async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("✅ Database connected")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

# Utility Functions
def create_jwt_token(user_data: dict) -> str:
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload

# API Routes
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "complyo-backend",
        "version": "2.1.0",
        "ai_enabled": bool(OPENROUTER_API_KEY),
        "environment": ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    db_status = "connected" if db_pool else "disconnected"
    return {
        "status": "healthy",
        "service": "complyo-backend",
        "database": db_status,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    try:
        async with db_pool.acquire() as connection:
            # Get user from database
            user = await connection.fetchrow(
                "SELECT id, email, password_hash, name, plan FROM users WHERE email = $1 AND is_active = true",
                login_data.email
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify password
            if user['password_hash'] != hash_password(login_data.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Create JWT token
            token = create_jwt_token(dict(user))
            
            user_response = {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "plan": user["plan"]
            }
            
            return {
                "success": True,
                "token": token,
                "user": user_response,
                "message": "Login successful"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.get("/api/dashboard/overview")
async def dashboard_overview(current_user: dict = Depends(get_current_user)):
    try:
        async with db_pool.acquire() as connection:
            # Get user projects
            projects = await connection.fetch(
                "SELECT * FROM projects WHERE user_id = $1 ORDER BY created_at DESC",
                current_user["user_id"]
            )
            
            # Calculate stats
            total_projects = len(projects)
            avg_score = sum(p["compliance_score"] for p in projects) // total_projects if total_projects > 0 else 0
            completed_projects = len([p for p in projects if p["status"] == "completed"])
            in_progress_projects = len([p for p in projects if p["status"] == "in_progress"])
            
            return {
                "success": True,
                "data": {
                    "stats": {
                        "total_projects": total_projects,
                        "average_compliance_score": avg_score,
                        "completed_projects": completed_projects,
                        "in_progress_projects": in_progress_projects,
                        "estimated_risk_saved": "€12.500"
                    },
                    "recent_projects": [dict(p) for p in projects[:3]],
                    "recent_activities": [
                        {
                            "type": "success",
                            "message": "Cookie-Banner erfolgreich implementiert",
                            "project": "example.com",
                            "timestamp": "2025-08-08T18:00:00Z"
                        }
                    ]
                }
            }
            
    except Exception as e:
        print(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard data could not be loaded"
        )

@app.get("/api/projects")
async def get_projects(current_user: dict = Depends(get_current_user)):
    try:
        async with db_pool.acquire() as connection:
            projects = await connection.fetch(
                "SELECT * FROM projects WHERE user_id = $1 ORDER BY created_at DESC",
                current_user["user_id"]
            )
            
            return {
                "success": True,
                "data": [dict(p) for p in projects],
                "total": len(projects)
            }
            
    except Exception as e:
        print(f"Projects error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Projects could not be loaded"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
