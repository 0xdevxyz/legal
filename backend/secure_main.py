"""
Complyo Secure Production Backend
Fully secured FastAPI application with comprehensive protection
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional, Any
import asyncio
import uuid
from datetime import datetime
import time

# Import secure components
from config import settings, validate_required_env_vars
from secure_auth import secure_auth, LoginRequest, RegisterRequest, TokenResponse, UserProfile
from secure_database import secure_db
from rate_limiter import rate_limiter, rate_limit, strict_rate_limit, SecurityHeaders
from monitoring import (
    structured_logger, request_monitor, health_monitor,
    log_info, log_warning, log_error, log_security_event,
    SecurityEventType, log_performance
)
from workflow_engine import workflow_engine, WorkflowStage, UserSkillLevel
from workflow_integration import WorkflowIntegration

# Validate environment on startup
if settings.is_production():
    validate_required_env_vars()

# Initialize FastAPI with security configuration
app = FastAPI(
    title="Complyo Secure API",
    description="Production-ready Website Compliance Platform with Enterprise Security",
    version=settings.api_version,
    docs_url="/docs" if not settings.is_production() else None,  # Disable docs in production
    redoc_url="/redoc" if not settings.is_production() else None,
    openapi_url="/openapi.json" if not settings.is_production() else None
)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.is_development() else settings.allowed_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request/Response middleware for monitoring and security
@app.middleware("http")
async def security_monitoring_middleware(request: Request, call_next):
    """
    Comprehensive request monitoring and security middleware
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Extract client information
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"
    
    user_agent = request.headers.get("User-Agent", "")
    endpoint = request.url.path
    method = request.method
    
    # Monitor request
    async with request_monitor.monitor_request(request_id, endpoint, method):
        try:
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = SecurityHeaders.add_security_headers(response)
            
            # Calculate response time
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            
            # Log successful request
            log_info(
                f"{method} {endpoint} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "client_ip": client_ip,
                    "user_agent": user_agent[:100]
                }
            )
            
            # Record request analytics
            await rate_limiter.record_request(request, response.status_code)
            
            return response
            
        except Exception as e:
            # Log error
            log_error(
                f"Request failed: {method} {endpoint}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "client_ip": client_ip,
                    "user_agent": user_agent
                }
            )
            
            # Log security event for 4xx/5xx errors
            if isinstance(e, HTTPException):
                if e.status_code >= 400:
                    log_security_event(
                        SecurityEventType.SUSPICIOUS_ACTIVITY,
                        ip_address=client_ip,
                        endpoint=endpoint,
                        user_agent=user_agent,
                        details={"status_code": e.status_code, "detail": e.detail}
                    )
            
            raise e

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize secure services"""
    
    log_info("🚀 Starting Complyo Secure Backend")
    
    # Initialize database with connection pooling
    db_connected = await secure_db.connect()
    if not db_connected:
        log_error("❌ Failed to connect to database")
        raise RuntimeError("Database connection failed")
    
    log_info("✅ All services initialized successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    
    log_info("🛑 Shutting down Complyo Backend")
    
    # Cleanup database connections
    await secure_db.disconnect()
    
    log_info("✅ Shutdown completed")

# ========== AUTHENTICATION ENDPOINTS ==========

@app.post("/api/auth/register", response_model=Dict[str, Any])
@strict_rate_limit(limit=5, window=300)  # 5 registrations per 5 minutes
async def register_user(
    request: Request,
    user_data: RegisterRequest,
    background_tasks: BackgroundTasks
):
    """
    Secure user registration with comprehensive validation
    """
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Register user
        user_profile = await secure_auth.register_user(user_data)
        
        # Log security event
        log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            ip_address=client_ip,
            endpoint="/api/auth/register",
            user_id=user_profile.id,
            user_agent=request.headers.get("User-Agent", ""),
            details={"action": "registration"}
        )
        
        # TODO: Send welcome email in background
        # background_tasks.add_task(send_welcome_email, user_profile.email)
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "user": {
                "id": user_profile.id,
                "email": user_profile.email,
                "name": f"{user_profile.first_name} {user_profile.last_name}"
            },
            "verification_required": not user_profile.is_verified
        }
        
    except HTTPException as e:
        # Log failed registration attempt
        log_security_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            ip_address=client_ip,
            endpoint="/api/auth/register",
            user_agent=request.headers.get("User-Agent", ""),
            details={"error": e.detail, "email": user_data.email}
        )
        raise e

@app.post("/api/auth/login", response_model=TokenResponse)
@strict_rate_limit(limit=10, window=300)  # 10 login attempts per 5 minutes
async def login_user(
    request: Request,
    login_data: LoginRequest
):
    """
    Secure user authentication with monitoring
    """
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Authenticate user
        token_response = await secure_auth.login_user(login_data)
        
        # Log successful login
        log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            ip_address=client_ip,
            endpoint="/api/auth/login",
            user_id=token_response.user_id,
            user_agent=request.headers.get("User-Agent", ""),
            details={"remember_me": login_data.remember_me}
        )
        
        return token_response
        
    except HTTPException as e:
        # Log failed login attempt
        log_security_event(
            SecurityEventType.LOGIN_FAILURE,
            ip_address=client_ip,
            endpoint="/api/auth/login",
            user_agent=request.headers.get("User-Agent", ""),
            details={"error": e.detail, "email": login_data.email},
            severity="high"
        )
        raise e

@app.post("/api/auth/logout")
@rate_limit(limit=20, window=60)
async def logout_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(secure_auth.security)
):
    """
    Secure user logout with token blacklisting
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Blacklist token
        await secure_auth.logout_user(credentials.credentials)
        
        # Log logout
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            ip_address=client_ip,
            endpoint="/api/auth/logout",
            user_agent=request.headers.get("User-Agent", ""),
            details={"action": "logout"}
        )
        
        return {"status": "success", "message": "Logged out successfully"}
        
    except Exception as e:
        log_error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

@app.get("/api/auth/me", response_model=Dict[str, Any])
@rate_limit(limit=60, window=60)  # 60 requests per minute
async def get_current_user_info(
    current_user: UserProfile = Depends(secure_auth.get_current_user)
):
    """
    Get current authenticated user information
    """
    return {
        "status": "success",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "company_name": current_user.company_name,
            "is_verified": current_user.is_verified,
            "subscription_status": current_user.subscription_status,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
    }

# ========== SECURE WORKFLOW ENDPOINTS ==========

class StartJourneyRequest(BaseModel):
    website_url: str
    skill_level: str = "beginner"

@app.post("/api/workflow/start-journey")
@rate_limit(limit=10, window=300)  # 10 journey starts per 5 minutes
async def start_user_journey(
    request: StartJourneyRequest,
    current_user: UserProfile = Depends(secure_auth.get_current_user)
):
    """Start a new user journey for guided compliance optimization"""
    try:
        # Validate skill level
        valid_levels = ["absolute_beginner", "beginner", "intermediate", "advanced"]
        if request.skill_level not in valid_levels:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid skill level. Use: {', '.join(valid_levels)}"
            )
        
        skill_level = UserSkillLevel(request.skill_level)
        
        # Start user journey
        journey = await workflow_engine.start_user_journey(
            user_id=current_user.id,
            website_url=request.website_url,
            skill_level=skill_level
        )
        
        # Save journey to database using secure integration
        workflow_integration = WorkflowIntegration()
        await workflow_integration.save_user_journey(journey)
        
        log_info(
            f"Journey started for user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "website_url": request.website_url,
                "skill_level": skill_level.value
            }
        )
        
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
        log_error(f"Failed to start journey: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start journey: {str(e)}")

@app.get("/api/workflow/current-step")
@rate_limit(limit=30, window=60)
async def get_current_workflow_step(
    current_user: UserProfile = Depends(secure_auth.get_current_user)
):
    """Get the current workflow step for the authenticated user"""
    try:
        current_step = await workflow_engine.get_current_step(current_user.id)
        
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
        log_error(f"Failed to get current step: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/complete-step")
@rate_limit(limit=20, window=300)
async def complete_workflow_step(
    request: Dict[str, Any],
    current_user: UserProfile = Depends(secure_auth.get_current_user)
):
    """Complete current workflow step with validation"""
    try:
        step_id = request.get("step_id")
        validation_data = request.get("validation_data", {})
        
        if not step_id:
            raise HTTPException(status_code=400, detail="step_id is required")
        
        # Load current journey
        workflow_integration = WorkflowIntegration()
        journey = await workflow_integration.load_user_journey(current_user.id)
        if not journey:
            raise HTTPException(status_code=404, detail="No active journey found")
        
        # Complete step using workflow engine
        result = await workflow_engine.complete_step(current_user.id, step_id, validation_data)
        
        log_info(
            f"Workflow step completed: {step_id}",
            extra={
                "user_id": current_user.id,
                "step_id": step_id,
                "status": result.get("status")
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to complete step: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete step: {str(e)}")

@app.get("/api/workflow/progress")
@rate_limit(limit=30, window=60)
async def get_workflow_progress(
    current_user: UserProfile = Depends(secure_auth.get_current_user)
):
    """Get comprehensive workflow progress for the authenticated user"""
    try:
        progress = await workflow_engine.get_journey_progress(current_user.id)
        
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
        log_error(f"Failed to get progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== MONITORING & HEALTH ENDPOINTS ==========

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    """
    try:
        # Check database health
        db_health = await health_monitor.check_database_health(secure_db)
        
        # Get system health
        system_health = health_monitor.get_system_health()
        
        # Check if all critical components are healthy
        all_healthy = (
            db_health.get("status") == "healthy" and
            system_health.get("status") == "healthy"
        )
        
        status_code = 200 if all_healthy else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if all_healthy else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.api_version,
                "environment": settings.environment,
                "system": system_health,
                "database": db_health
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/api/monitoring/security-summary")
@rate_limit(limit=10, window=60)
async def get_security_summary(
    current_user: UserProfile = Depends(secure_auth.get_current_user)
):
    """
    Get security events summary (admin only)
    """
    # TODO: Add admin role check
    return structured_logger.get_security_summary()

@app.get("/api/monitoring/performance")
@rate_limit(limit=10, window=60)
async def get_performance_metrics(
    current_user: UserProfile = Depends(secure_auth.get_current_user)
):
    """
    Get performance metrics summary (admin only)
    """
    # TODO: Add admin role check
    db_performance = await secure_db.get_performance_stats()
    system_performance = structured_logger.get_performance_summary()
    
    return {
        "database": db_performance,
        "application": system_performance,
        "active_requests": request_monitor.get_active_requests_count()
    }

# ========== ERROR HANDLERS ==========

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler with logging
    """
    log_warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "endpoint": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler for unhandled errors
    """
    log_error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "endpoint": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ========== MAIN APPLICATION ==========

if __name__ == "__main__":
    log_info("🚀 Starting Complyo Secure Backend Server")
    
    # Configure SSL for production
    ssl_config = {}
    if settings.is_production() and settings.ssl_cert_path and settings.ssl_key_path:
        ssl_config = {
            "ssl_keyfile": settings.ssl_key_path,
            "ssl_certfile": settings.ssl_cert_path
        }
    
    uvicorn.run(
        "secure_main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.is_development(),
        log_config=None,  # Use our custom logging
        **ssl_config
    )