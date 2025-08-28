from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
import psycopg2
import os
from datetime import datetime

app = FastAPI(title="Complyo API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

# Database connection
def get_db_connection():
    try:
        DATABASE_URL = "postgresql://complyo_user:WrsmZTXYcjt0c7lt%2FlOzEnX1N5rtjRklLYrY8zXmBGo%3D@shared-postgres:5432/complyo_db"
        import urllib.parse as urlparse
        url = urlparse.urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=urllib.parse.unquote(url.password),
            database=url.path[1:]
        )
        return conn
    except Exception as e:
        print(f"Database error: {e}")
        return None

@app.get("/")
async def root():
    return {"message": "Complyo API v2.0", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "complyo-backend", "version": "2.0.0"}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        print(f"Login attempt: {request.email}")
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Generate password hash
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        print(f"Generated hash: {password_hash}")
        
        # Check database
        cursor.execute("SELECT email, name, plan, password_hash FROM demo_users WHERE email = %s", (request.email,))
        user = cursor.fetchone()
        
        if user:
            print(f"Found user: {user[0]}, stored hash: {user[3]}")
            
            if user[3] == password_hash:
                conn.close()
                return {
                    "access_token": f"demo_token_{user[0]}",
                    "token_type": "bearer",
                    "user": {
                        "email": user[0],
                        "name": user[1],
                        "plan": user[2]
                    }
                }
            else:
                print("Password mismatch")
        else:
            print("User not found")
            
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
