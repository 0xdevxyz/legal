
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# Import our auth system
from auth_system import router as auth_router, Base, engine

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown

app = FastAPI(
    title="Complyo API",
    description="AI-powered Website Compliance Platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://complyo.tech",
        "https://app.complyo.tech",
        "http://localhost:3000",
        "http://localhost:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

# Keep existing routes
@app.get("/")
async def root():
    return {
        "message": "Complyo API v2.0",
        "status": "ok",
        "features": [
            "User Authentication",
            "Website Management",
            "Compliance Scanning",
            "Dashboard Analytics"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "complyo-backend",
        "version": "2.0.0"
    }
