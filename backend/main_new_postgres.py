from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
import psycopg2
from datetime import datetime

app = FastAPI(title="Complyo API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginRequest(BaseModel):
    email: str
    password: str

def get_db_connection():
    return psycopg2.connect(host="shared-postgres", port=5432, user="complyo_user", password="complyo123", database="complyo_db")

@app.get("/")
async def root():
    return {"message": "Complyo API v2.0", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "complyo-backend", "version": "2.0.0"}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        cursor.execute("SELECT email, name, plan FROM demo_users WHERE email = %s AND password_hash = %s", (request.email, password_hash))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {"access_token": f"demo_token_{user[0]}", "token_type": "bearer", "user": {"email": user[0], "name": user[1], "plan": user[2]}}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
