from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import asdict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import hashlib
import jwt
import datetime
import os
import asyncpg
import json
import logging
from compliance_engine.scanner import ComplianceScanner
from compliance_engine.fixer import AIComplianceFixer
from compliance_engine.workflow_engine import workflow_engine, UserSkillLevel
from compliance_engine.workflow_integration import WorkflowIntegration
from compliance_engine.pdf_generator import pdf_generator
# NEU: Enhanced Scanner & AI Fix Engine
from compliance_engine.deep_scanner import DeepScanner
from compliance_engine.data_validator import DataValidator
from ai_fix_engine.intelligent_analyzer import IntelligentAnalyzer
from ai_fix_engine.smart_fix_generator import SmartFixGenerator
from background_worker import start_background_worker, stop_background_worker
from fastapi.responses import StreamingResponse
import io
from payment.stripe_service import StripeService
import stripe

# Import API Routers
from lead_routes import lead_router
from public_routes import public_router
from admin_routes import admin_router
from gdpr_api import gdpr_router
from i18n_api import i18n_router
from legal_news_routes import router as legal_news_router
from fix_routes import fix_router
from website_routes import router as website_router
from dashboard_routes import dashboard_router
import auth_routes  # Auth routes with AuthService
from auth_service import AuthService
import payment_routes  # Payment routes with Stripe
import website_routes  # Website management routes
import stripe_routes  # NEW: Freemium Stripe integration
import user_routes  # User profile & domain locks
from database_service import db_service
from email_service import email_service
from erecht24_rechtstexte_service import erecht24_rechtstexte_service, LegalTextType
from news_service import NewsService
from risk_calculator import RiskCalculator
from fix_generator import FixGenerator
from export_service import ExportService
from firebase_auth import init_firebase_admin, verify_firebase_token

# New Services
from erecht24_service import erecht24_service
from erecht24_webhook_routes import router as erecht24_webhook_router
from compliance_engine.solution_generator import solution_generator
from compliance_engine.cookie_analyzer import cookie_analyzer
from compliance_engine.priority_engine import priority_engine

# AI Compliance Module (ComploAI Guard)
from ai_compliance_routes import router as ai_compliance_router
from addon_payment_routes import router as addon_payment_router
from widget_routes import router as widget_router
from expert_service_routes import router as expert_service_router

# Cookie Compliance Module
from cookie_compliance_routes import router as cookie_compliance_router

# A/B Testing Module for Cookie Banner
from ab_test_routes import router as ab_test_router

# TCF 2.2 Module
try:
    from tcf_routes import router as tcf_router
    TCF_ROUTES_AVAILABLE = True
except ImportError:
    TCF_ROUTES_AVAILABLE = False
    print("⚠️ TCF routes not available")

# Legal Change Monitoring System
from legal_change_routes import router as legal_change_router
from legal_change_monitor import init_legal_monitor

# AI Legal System - NEW
from ai_legal_classifier import init_ai_classifier
from ai_feedback_learning import init_feedback_learning
from ai_legal_routes import router as ai_legal_router

# Legal News Notification System - NEW
from legal_notification_service import init_legal_notification_service
from legal_notification_routes import router as legal_notification_router
from eulex_service import init_eulex_service

# NEW V2 API Routes - Enhanced AI Fix Engine & eRecht24 Integration (Full Version)
from erecht24_routes_v2 import router as erecht24_v2_router

# BFSG Accessibility Fix Pipeline - Anfängerfreundliche Fix-Generierung
from accessibility_fix_routes import accessibility_fix_router, init_routes as init_accessibility_routes

# Git Integration - Automatische PRs für Accessibility-Fixes
from git_routes import git_router, init_git_routes

# Alt-Text AI Generation - KI-generierte Alt-Texte für Bilder
from alt_text_routes import router as alt_text_router

# Models for new endpoints
class AnalyzeRequest(BaseModel):
    url: str

class ExecuteFixRequest(BaseModel):
    fix_id: str
    fix_data: Dict[str, Any]
    context: Dict[str, Any]

class ValidateFixRequest(BaseModel):
    fix_id: str
    website_url: str
    issue_category: str

class AIFixRequest(BaseModel):
    scan_id: str
    company_info: Optional[Dict[str, str]] = None
    fix_categories: Optional[List[str]] = None

class StartJourneyRequest(BaseModel):
    website_url: str
    skill_level: str = "beginner"

class CompleteStepRequest(BaseModel):
    step_id: str
    validation_data: Optional[Dict[str, Any]] = None

class CreateCheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str

# Initialize FastAPI app
app = FastAPI(
    title="Complyo API",
    description="KI-gestützte Website-Compliance-Plattform",
    version="2.2.0"
)

# Static files für CMP-Adapter
from fastapi.staticfiles import StaticFiles
import os
public_dir = os.path.join(os.path.dirname(__file__), "public")
if os.path.exists(public_dir):
    app.mount("/public", StaticFiles(directory=public_dir), name="public")
    print(f"✅ Static files mounted at /public (directory: {public_dir})")

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
_cors_origins = [
    "https://complyo.tech",
    "https://www.complyo.tech",
    "https://app.complyo.tech",
]
if ENVIRONMENT != "production":
    _cors_origins += [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Request-ID"]
)

# Request-ID Middleware (MON-003)
import uuid as _uuid
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(_uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("❌ CRITICAL: JWT_SECRET environment variable is required! Set it in your .env file.")
JWT_ALGORITHM = "HS256"

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
db_pool = None
news_service = None
risk_calculator = None
export_service = None
fix_generator = None
auth_service = None

# Logger
logger = logging.getLogger(__name__)

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Stripe
stripe_service = None

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
async def execute_sql_from_file(connection, filepath):
    """Reads and executes a SQL file."""
    with open(filepath, 'r') as f:
        await connection.execute(f.read())

async def init_db():
    """Initializes the database connection and schema."""
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    
    # Automatically apply SQL migration files from sql/ directory
    async with db_pool.acquire() as connection:
        sql_dir = os.path.join(os.path.dirname(__file__), 'sql')
        if os.path.isdir(sql_dir):
            for filename in sorted(os.listdir(sql_dir)):
                if filename.endswith('.sql'):
                    print(f"Applying migration: {filename}")
                    await execute_sql_from_file(connection, os.path.join(sql_dir, filename))
        
        # Apply new schema files (erecht24, score_history, legal_updates)
        backend_dir = os.path.dirname(__file__)
        new_schema_files = [
            'init_erecht24_projects.sql',
            'init_legal_updates.sql',
            'init_score_history.sql'
        ]
        
        for filename in new_schema_files:
            filepath = os.path.join(backend_dir, filename)
            if os.path.exists(filepath):
                try:
                    print(f"⚙️ Initializing schema: {filename}")
                    await execute_sql_from_file(connection, filepath)
                    print(f"✅ {filename} applied")
                except Exception as e:
                    print(f"⚠️ Warning applying {filename}: {e}")

async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()

@app.on_event("startup")
async def startup_event():
    await init_db()

    # Initialize database service for lead management
    await db_service.initialize()

    # Initialize email service
    print(f"✅ Email service initialized ({'DEMO MODE' if email_service.demo_mode else 'SMTP MODE'})")
    
    # Initialize workflow integration with the db_pool
    global workflow_integration_instance
    workflow_integration_instance = WorkflowIntegration(db_pool)
    
    # Initialize Stripe service
    global stripe_service
    stripe_service = StripeService(db_pool)
    
    # Initialize News service
    global news_service
    news_service = NewsService(db_pool)
    
    # Initialize Widget routes with db_pool
    import widget_routes
    widget_routes.db_pool = db_pool
    print("✅ Widget routes initialized with database pool")
    
    # Initialize Public routes with db_pool
    import public_routes
    public_routes.db_pool = db_pool
    print("✅ Public routes initialized with database pool")
    
    # ✅ Initialize AI Solution Cache (Intelligent Caching System)
    from ai_solution_cache_service import AISolutionCache
    public_routes.solution_cache = AISolutionCache(db_pool)
    print("✅ AI Solution Cache initialized (70-85% API call reduction)")
    
    # Initialize Expert Service routes with db_pool
    import expert_service_routes
    expert_service_routes.db_pool = db_pool
    print("✅ Expert service routes initialized with database pool")
    
    # Start Background Worker for fix-jobs
    try:
        await start_background_worker(db_pool)
        print("✅ Background worker for fix-jobs started")
    except Exception as e:
        print(f"⚠️ Background worker start failed: {e}")

    # Auto-fetch news on startup if older than 6 hours
    try:
        async with db_pool.acquire() as conn:
            latest_news = await conn.fetchval(
                "SELECT MAX(fetched_date) FROM legal_news WHERE is_active = TRUE"
            )
            
            should_fetch = False
            if latest_news is None:

                should_fetch = True
            else:
                import datetime
                age_hours = (datetime.datetime.now() - latest_news).total_seconds() / 3600
                if age_hours >= 6:
                    print(f"ℹ️ News are {age_hours:.1f}h old, fetching updates...")
                    should_fetch = True
                else:
                    print(f"✅ News are fresh ({age_hours:.1f}h old)")
            
            if should_fetch:
                result = await news_service.fetch_all_feeds()
                if result['success'] and result['new_articles_count'] > 0:
                    print(f"✅ Fetched {result['new_articles_count']} new articles")
                else:
                    print(f"⚠️ News fetch failed (keeping old news): {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"⚠️ News fetch failed (keeping old news): {e}")
    
    # Initialize Risk Calculator
    global risk_calculator
    risk_calculator = RiskCalculator(db_pool)

    # Initialize Fix Generator
    global fix_generator
    fix_generator = FixGenerator(db_pool)

    # Initialize Export Service
    global export_service
    export_service = ExportService(db_pool)

    # Initialize Auth Service
    global auth_service
    auth_service = AuthService(db_pool)
    # Set global references in auth_routes
    auth_routes.auth_service = auth_service
    auth_routes.db_pool = db_pool
    
    # Initialize BFSG Accessibility Fix routes (after auth_service is ready)
    init_accessibility_routes(db_pool, auth_service, db_service)
    print("✅ BFSG Accessibility Fix routes initialized")
    
    # Initialize Git Integration routes
    init_git_routes(db_pool, auth_service)
    print("✅ Git Integration routes initialized")

    # Initialize Firebase Admin SDK
    firebase_app = init_firebase_admin()
    if firebase_app:
        auth_routes.firebase_verify_token = verify_firebase_token
    else:
        print("⚠️ Firebase Admin SDK not initialized")
    
    # Set global references in payment_routes
    payment_routes.stripe_service = stripe_service
    payment_routes.db_pool = db_pool
    payment_routes.auth_service = auth_service

    # Set global references in website_routes
    website_routes.db_pool = db_pool
    website_routes.auth_service = auth_service

    # Set global references for dashboard routes
    import dashboard_routes
    dashboard_routes.db_pool = db_pool
    dashboard_routes.auth_service = auth_service

    # Set global references for fix routes
    import fix_routes
    fix_routes.db_pool = db_pool
    fix_routes.auth_service = auth_service
    fix_routes.fix_generator = fix_generator
    fix_routes.export_service = export_service

    # Set global references for erecht24_webhook_routes
    import erecht24_webhook_routes
    erecht24_webhook_routes.db_pool = db_pool

    # Set global references for legal_news_routes
    import legal_news_routes
    legal_news_routes.db_pool = db_pool
    legal_news_routes.news_service = news_service
    legal_news_routes.db_pool = db_pool
    
    # Initialize legal_ai_routes with db_pool
    import legal_ai_routes
    legal_ai_routes.db_pool = db_pool
    print("✅ Legal AI routes initialized with database pool")

    # Include API routers
    app.include_router(public_router)
    app.include_router(lead_router)
    app.include_router(admin_router)
    app.include_router(gdpr_router)
    app.include_router(i18n_router)
    app.include_router(legal_news_router)
    app.include_router(fix_router)
    app.include_router(website_router)  # Website management router
    app.include_router(dashboard_router)  # Dashboard metrics router
    app.include_router(auth_routes.router)  # Auth router enabled
    app.include_router(payment_routes.router)  # Payment router enabled
    app.include_router(stripe_routes.router)  # NEW: Freemium Stripe routes
    app.include_router(user_routes.router)  # User profile & domain locks
    app.include_router(erecht24_webhook_router)  # eRecht24 webhooks for legal updates
    app.include_router(erecht24_v2_router)  # NEW V2: Enhanced AI Fix Engine & eRecht24 Integration
    app.include_router(ai_compliance_router)  # AI Compliance (ComploAI Guard)
    app.include_router(addon_payment_router)  # Add-on Payments (ComploAI Guard & Priority Support)
    app.include_router(widget_router)  # Complyo Widgets (Cookie Consent & Accessibility)
    app.include_router(expert_service_router)  # Expert Service Booking
    app.include_router(cookie_compliance_router)  # Cookie Compliance Management
    app.include_router(ab_test_router)  # A/B Testing for Cookie Banner
    
    # TCF 2.2 Routes
    if TCF_ROUTES_AVAILABLE:
        app.include_router(tcf_router)  # TCF 2.2 Transparency & Consent Framework
    
    app.include_router(legal_change_router)  # Legal Change Monitoring (auto-detect law changes)
    app.include_router(ai_legal_router)  # AI Legal System - NEW
    app.include_router(legal_notification_router)  # Legal News Notifications - NEW
    app.include_router(accessibility_fix_router)  # BFSG Accessibility Fix Pipeline - NEW
    app.include_router(git_router)  # Git Integration - Automatic PRs - NEW
    app.include_router(alt_text_router)  # Alt-Text AI Generation - NEW
    
    # Initialize Alt-Text routes
    import alt_text_routes
    alt_text_routes.db_pool = db_pool
    alt_text_routes.auth_service = auth_service
    logger.info("✅ Alt-Text AI routes initialized")
    
    # Initialize Legal Update Integration
    from compliance_engine.legal_update_integration import init_legal_update_integration
    init_legal_update_integration(db_pool)
    logger.info("⚖️ Legal Update Integration initialized")
    
    # Initialize Legal Change Monitor
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        init_legal_monitor(openrouter_key)
        logger.info("🔍 Legal Change Monitor initialized")
    else:
        logger.warning("⚠️ OPENROUTER_API_KEY not found. Legal Change Monitor disabled.")
    
    # Initialize AI Legal Classifier
    if openrouter_key:
        init_ai_classifier(openrouter_key)
        logger.info("🤖 AI Legal Classifier initialized")
    else:
        logger.warning("⚠️ OPENROUTER_API_KEY not found. AI Legal Classifier disabled.")
    
    # Initialize AI Feedback Learning
    init_feedback_learning(db_service)
    logger.info("📚 AI Feedback Learning initialized")
    
    # Initialize Legal Notification Service - NEW
    init_legal_notification_service(db_pool)
    logger.info("📧 Legal Notification Service initialized")
    
    # Initialize EU-Lex Service - NEW
    init_eulex_service(db_pool)
    logger.info("🇪🇺 EU-Lex Service initialized")
    
    # Set global references for user_routes
    user_routes.db_pool = db_pool
    user_routes.auth_service = auth_service
    
    # Set global references for cookie_compliance_routes
    import cookie_compliance_routes
    cookie_compliance_routes.db_pool = db_pool
    cookie_compliance_routes.auth_service = auth_service  # ✅ Auth-Service hinzugefügt
    cookie_compliance_routes.db_service = db_service  # ✅ DB-Service für Modul-Checks
    
    # Set global references for ab_test_routes
    import ab_test_routes
    ab_test_routes.db_pool = db_pool
    
    # Set global references for ai_legal_routes
    import ai_legal_routes
    ai_legal_routes.db_pool = db_pool
    
    # Start daily AI cache cleanup background task
    async def _daily_ai_cache_cleanup():
        while True:
            try:
                await asyncio.sleep(24 * 60 * 60)
                async with db_pool.acquire() as conn:
                    deleted = await conn.fetchval(
                        "DELETE FROM ai_solution_cache WHERE generation_date < NOW() - INTERVAL '30 days' RETURNING COUNT(*)"
                    )
                    logger.info(f"AI cache cleanup: removed {deleted or 0} entries older than 30 days")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"AI cache cleanup error: {e}")

    asyncio.create_task(_daily_ai_cache_cleanup())
    logger.info("✅ Daily AI cache cleanup task scheduled (30-day retention)")

    # GDPR: daily cleanup of expired sessions and inactive accounts
    async def _daily_gdpr_cleanup():
        await asyncio.sleep(60)
        while True:
            try:
                async with db_pool.acquire() as conn:
                    expired_sessions = await conn.fetchval(
                        "DELETE FROM user_sessions WHERE expires_at < NOW() RETURNING COUNT(*)"
                    )
                    old_inactive = await conn.fetchval(
                        "DELETE FROM users WHERE is_active = FALSE AND updated_at < NOW() - INTERVAL '2 years' RETURNING COUNT(*)"
                    )
                    logger.info(f"GDPR cleanup: removed {expired_sessions or 0} expired sessions, {old_inactive or 0} inactive accounts")
                await asyncio.sleep(24 * 60 * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"GDPR cleanup error: {e}")
                await asyncio.sleep(24 * 60 * 60)

    asyncio.create_task(_daily_gdpr_cleanup())
    logger.info("✅ Daily GDPR cleanup task scheduled")

    print("✅ All routers initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    # Stop Background Worker
    try:
        await stop_background_worker()
        print("✅ Background worker stopped")
    except Exception as e:
        print(f"⚠️ Background worker stop failed: {e}")
    
    await close_db()
    await db_service.close()

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
    if "user_id" not in payload and "id" in payload:
        payload["user_id"] = payload["id"]
    return payload

# API Routes
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "complyo-backend",
        "version": "2.2.0",
        "ai_enabled": bool(OPENROUTER_API_KEY),
        "environment": ENVIRONMENT,
        "features": {  # NEU
            "enhanced_scanning": True,
            "smart_fixes": True
        }
    }

@app.get("/health")
async def health_check():
    import time
    checks = {}

    # Database
    db_start = time.monotonic()
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            checks["database"] = {"status": "up", "latency_ms": round((time.monotonic() - db_start) * 1000, 2)}
        else:
            checks["database"] = {"status": "down", "latency_ms": None}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}

    # Redis
    redis_start = time.monotonic()
    try:
        import redis as _redis
        _r = _redis.Redis(
            host=os.getenv("REDIS_HOST", "shared-redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            socket_connect_timeout=1
        )
        _r.ping()
        checks["redis"] = {"status": "up", "latency_ms": round((time.monotonic() - redis_start) * 1000, 2)}
    except Exception:
        checks["redis"] = {"status": "down"}

    # OpenRouter API key present
    checks["openrouter"] = {"status": "configured" if os.getenv("OPENROUTER_API_KEY") else "missing"}

    # Stripe
    checks["stripe"] = {"status": "configured" if os.getenv("STRIPE_SECRET_KEY") else "missing"}

    overall = "healthy" if checks["database"]["status"] == "up" else "degraded"
    return {
        "status": overall,
        "service": "complyo-backend",
        "checks": checks,
        "timestamp": datetime.datetime.now().isoformat()
    }


# ==================== NEU: ENHANCED SCAN API ====================

@app.post("/api/v2/analyze/complete")
@limiter.limit("30/minute")
async def complete_analysis(analyze_request: AnalyzeRequest, request: Request):
    """
    Enhanced comprehensive website analysis with deep scanning and context extraction
    """
    try:
        url = analyze_request.url
        
        # PHASE 1: Deep Scan
        async with DeepScanner() as deep_scanner:
            scan_result = await deep_scanner.comprehensive_scan(url)
        
        # PHASE 2: Validate Completeness
        data_validator = DataValidator()
        validation = data_validator.validate_scan_completeness(scan_result)
        
        # PHASE 3: User Feedback
        feedback_message = data_validator.generate_user_feedback(validation)
        
        # PHASE 4: AI Analysis
        intelligent_analyzer = IntelligentAnalyzer()
        try:
            smart_fixes = await intelligent_analyzer.analyze_and_generate_fixes(scan_result)
        except Exception as e:
            print(f"Warning: AI analysis failed: {e}")
            smart_fixes = []
        
        # PHASE 5: Convert issues to dicts
        issues_list = []
        for issue in scan_result.get("issues", []):
            if hasattr(issue, '__dict__'):
                issues_list.append(asdict(issue))
            elif isinstance(issue, dict):
                issues_list.append(issue)
        
        scan_id = f"scan-{hashlib.md5(f'{url}{datetime.datetime.now()}'.encode()).hexdigest()[:12]}"
        
        return {
            "success": True,
            "scan_id": scan_id,
            "url": url,
            "compliance_score": scan_result.get("compliance_score", 0),
            "website_data": scan_result.get("website_data", {}),
            "seo_data": scan_result.get("seo_data", {}),
            "tech_stack": scan_result.get("tech_stack", {}),
            "structure": scan_result.get("structure", {}),
            "issues": issues_list,
            "smart_fixes": smart_fixes,
            "validation": {
                "complete": validation.get("complete", False),
                "missing_count": validation.get("missing_count", 0),
                "feedback": feedback_message
            },
            "scan_timestamp": datetime.datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error in complete_analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der erweiterten Analyse: {str(e)}"
        )


@app.post("/api/v2/fixes/execute")
@limiter.limit("10/minute")
async def execute_fix(execute_request: ExecuteFixRequest, request: Request):
    """
    Generate complete fix content (code/text/widget/guide)
    """
    try:
        # Initialize Smart Fix Generator
        smart_fix_generator = SmartFixGenerator()
        
        # Inject erecht24 service for legal texts
        smart_fix_generator.set_erecht24_service(erecht24_service)
        
        # Generate fix
        fix_result = await smart_fix_generator.generate(
            execute_request.fix_id, 
            execute_request.fix_data, 
            execute_request.context
        )
        
        return {
            "success": True,
            "fix": fix_result
        }
    
    except Exception as e:
        print(f"Error in execute_fix: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Fix-Generierung: {str(e)}"
        )


@app.post("/api/v2/fixes/validate")
@limiter.limit("20/minute")
async def validate_fix_live(validate_request: ValidateFixRequest, request: Request):
    """
    Validate if a fix has been implemented correctly via targeted re-scan
    """
    try:
        # TODO: Import LiveValidator when created
        # For now, basic validation
        
        # Re-scan website
        async with ComplianceScanner() as scanner:
            scan_result = await scanner.scan_website(validate_request.website_url)
        
        # Check if the specific issue is resolved
        # (simplified - would need more sophisticated matching)
        issues = scan_result.get("issues", [])
        
        resolved = True
        for issue in issues:
            if isinstance(issue, dict):
                if issue.get("category", "").lower() == validate_request.issue_category.lower():
                    resolved = False
                    break
        
        if resolved:
            return {
                "success": True,
                "status": "resolved",
                "message": "Problem behoben! ✅",
                "new_compliance_score": scan_result.get("compliance_score", 0)
            }
        else:
            return {
                "success": True,
                "status": "pending",
                "message": "Bitte überprüfen Sie die Implementierung",
                "suggestions": ["Stellen Sie sicher, dass der Code korrekt eingefügt wurde", "Leeren Sie ggf. den Browser-Cache"]
            }
    
    except Exception as e:
        print(f"Error in validate_fix_live: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Validierung: {str(e)}"
        )


# OLD LOGIN ROUTE - DISABLED (now using auth_routes.py)
# @app.post("/api/auth/login")
# async def login(login_data: LoginRequest):
#     try:
#         async with db_pool.acquire() as connection:
#             # Get user from database
#             user = await connection.fetchrow(
#                 "SELECT id, email, password_hash, name, plan FROM users WHERE email = $1 AND is_active = true",
#                 login_data.email
#             )
#             
#             if not user:
#                 raise HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail="Invalid credentials"
#                 )
#             
#             # Verify password
#             if user['password_hash'] != hash_password(login_data.password):
#                 raise HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail="Invalid credentials"
#                 )
#             
#             # Create JWT token
#             token = create_jwt_token(dict(user))
#             
#             user_response = {
#                 "id": user["id"],
#                 "email": user["email"],
#                 "name": user["name"],
#                 "plan": user["plan"]
#             }
#             
#             return {
#                 "success": True,
#                 "token": token,
#                 "user": user_response,
#                 "message": "Login successful"
#             }
#             
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Login error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Login failed"
#         )

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

@app.post("/api/v2/analyze/quick")
async def quick_analyze_website(request: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    """
    Quick compliance scan (10-20 seconds) for instant feedback
    Returns critical issues only, runs in parallel
    """
    try:
        from compliance_engine.quick_scanner import QuickScanner
        
        async with QuickScanner() as scanner:
            scan_result = await scanner.quick_scan(request.url)
        
        if scan_result.get("error"):
            raise HTTPException(status_code=400, detail=scan_result["error_message"])
        
        # Save quick scan to database
        async with db_pool.acquire() as connection:
            scan_id = f"quick_{current_user['user_id']}_{int(datetime.datetime.now().timestamp())}"
            await connection.execute(
                """
                INSERT INTO scan_history (
                    scan_id, user_id, url, scan_duration_ms, compliance_score, total_risk_euro,
                    critical_issues, warning_issues, total_issues, scan_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                scan_id,
                current_user["user_id"],
                scan_result["url"],
                scan_result["scan_duration_ms"],
                scan_result["compliance_score"],
                scan_result["total_risk_euro"],
                scan_result["critical_issues"],
                scan_result["warning_issues"],
                scan_result["total_issues"],
                json.dumps(scan_result, default=str)  # Store full scan result as JSONB
            )
            new_scan = await connection.fetchrow(
                "SELECT id FROM scan_history WHERE user_id = $1 ORDER BY scan_timestamp DESC LIMIT 1", 
                current_user["user_id"]
            )
        
        return {
            "success": True,
            "scan_type": "quick",
            "data": {**scan_result, "scan_id": str(new_scan['id'])}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick-Scan fehlgeschlagen: {str(e)}"
        )

@app.post("/api/v2/analyze")
async def analyze_website_v2(request: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    """
    Performs a real, in-depth compliance scan of a website.
    """
    try:
        async with ComplianceScanner() as scanner:
            scan_result = await scanner.scan_website(request.url)
        
        if scan_result.get("error"):
            raise HTTPException(status_code=400, detail=scan_result["error_message"])

        async with db_pool.acquire() as connection:
            scan_id = f"scan_{current_user['user_id']}_{int(datetime.datetime.now().timestamp())}"
            await connection.execute(
                """
                INSERT INTO scan_history (
                    scan_id, user_id, url, scan_duration_ms, compliance_score, total_risk_euro,
                    critical_issues, warning_issues, total_issues, scan_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                scan_id,
                current_user["user_id"],
                scan_result["url"],
                scan_result["scan_duration_ms"],
                scan_result["compliance_score"],
                scan_result["total_risk_euro"],
                scan_result["critical_issues"],
                scan_result["warning_issues"],
                scan_result["total_issues"],
                json.dumps(scan_result, default=str)
            )
            new_scan = await connection.fetchrow("SELECT id, scan_id FROM scan_history WHERE user_id = $1 ORDER BY scan_timestamp DESC LIMIT 1", current_user["user_id"])
            
            tracked_site = await connection.fetchrow(
                "SELECT id FROM tracked_websites WHERE user_id = $1 AND url = $2",
                current_user["user_id"], scan_result["url"]
            )
            
            if tracked_site:
                pillar_scores = {
                    "accessibility": scan_result.get("accessibility_score", 0),
                    "gdpr": scan_result.get("gdpr_score", 0),
                    "legal": scan_result.get("legal_score", 0),
                    "cookies": scan_result.get("cookie_score", 0),
                    "critical_issues": scan_result.get("critical_issues", 0)
                }
                await connection.execute(
                    """
                    INSERT INTO score_history (website_id, user_id, overall_score, pillar_scores, scan_date)
                    VALUES ($1, $2, $3, $4, NOW())
                    """,
                    tracked_site["id"],
                    current_user["user_id"],
                    scan_result["compliance_score"],
                    json.dumps(pillar_scores)
                )
                await connection.execute(
                    "UPDATE tracked_websites SET last_score = $1, last_scan_date = NOW(), scan_count = scan_count + 1 WHERE id = $2",
                    scan_result["compliance_score"], tracked_site["id"]
                )

        return {
            "success": True,
            "data": {**scan_result, "scan_id": new_scan['scan_id']}
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis v2 error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analyse fehlgeschlagen: {str(e)}"
        )

@app.post("/api/v2/ai-fix")
async def generate_ai_fixes(request: AIFixRequest, current_user: dict = Depends(get_current_user)):
    """
    Generates AI-powered fixes for a given scan.
    """
    try:
        # 1. Fetch the scan results from the database
        # ✅ FIX: Verwende scan_history statt scan_results
        async with db_pool.acquire() as connection:
            scan_result = await connection.fetchrow(
                "SELECT * FROM scan_history WHERE scan_id = $1 AND user_id = $2",
                request.scan_id, current_user["user_id"]
            )
        
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan not found or access denied.")

        # ✅ FIX: Parse scan_data to get issues
        scan_dict = dict(scan_result)
        if scan_dict.get('scan_data'):
            # scan_data kann String oder Dict sein
            if isinstance(scan_dict['scan_data'], str):
                scan_dict['scan_data'] = json.loads(scan_dict['scan_data'])
            violations = scan_dict['scan_data'].get('issues', [])
        else:
            # Fallback: Versuche issues direkt
            violations = json.loads(scan_result.get("issues", "[]")) if scan_result.get("issues") else []

        # 2. Filter violations if categories are specified
        if request.fix_categories:
            violations = [v for v in violations if v.get('category') in request.fix_categories]

        # 3. Instantiate and run the AI Fixer
        fixer = AIComplianceFixer()
        fix_result = await fixer.fix_compliance_issues(
            scan_id=request.scan_id,
            violations=violations,
            company_info=request.company_info
        )

        # 4. ✅ DB-Speicherung entfernt - fix_jobs Tabelle wird stattdessen verwendet
        # (siehe /api/fix-jobs Endpoint für persistente Speicherung)
        
        return {
            "success": True,
            "data": fix_result
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"AI Fix error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI-Fix-Generierung fehlgeschlagen: {str(e)}"
        )

# ========== WORKFLOW ENDPOINTS ==========

@app.post("/api/v2/workflow/start-journey")
async def start_user_journey(request: StartJourneyRequest, current_user: dict = Depends(get_current_user)):
    try:
        skill_level = UserSkillLevel(request.skill_level)
        journey = await workflow_engine.start_user_journey(
            user_id=str(current_user["user_id"]),
            website_url=request.website_url,
            skill_level=skill_level
        )
        await workflow_integration_instance.save_user_journey(journey)
        return {"success": True, "data": journey}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start journey: {e}")

@app.get("/api/v2/workflow/current-step")
async def get_current_workflow_step(current_user: dict = Depends(get_current_user)):
    try:
        current_step = await workflow_engine.get_current_step(str(current_user["user_id"]))
        return {"success": True, "data": current_step}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current step: {e}")

@app.post("/api/v2/workflow/complete-step")
async def complete_workflow_step(request: CompleteStepRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = await workflow_engine.complete_step(
            user_id=str(current_user["user_id"]),
            step_id=request.step_id,
            validation_data=request.validation_data
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete step: {e}")

@app.get("/api/v2/workflow/progress")
async def get_workflow_progress(current_user: dict = Depends(get_current_user)):
    try:
        progress = await workflow_engine.get_journey_progress(str(current_user["user_id"]))
        return {"success": True, "data": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {e}")

# ========== SCAN PERSISTENCE ENDPOINTS ==========

@app.get("/api/scans/latest")
async def get_latest_scan(current_user: dict = Depends(get_current_user)):
    """
    Holt die letzten Scan-Ergebnisse für den aktuellen User
    Damit Ergebnisse nach Page-Refresh wieder angezeigt werden
    """
    try:
        async with db_pool.acquire() as connection:
            # Hole den letzten Scan
            scan = await connection.fetchrow(
                """
                SELECT 
                    scan_id,
                    url,
                    scan_data,
                    compliance_score,
                    total_risk_euro,
                    critical_issues,
                    warning_issues,
                    total_issues,
                    scan_timestamp,
                    scan_duration_ms
                FROM scan_history
                WHERE user_id = $1
                ORDER BY scan_timestamp DESC
                LIMIT 1
                """,
                current_user["user_id"]
            )
            
            if not scan:
                return {
                    "success": True,
                    "data": None
                }
            
            # Parse scan_data (JSONB)
            scan_dict = dict(scan)
            if scan_dict.get('scan_data'):
                # ✅ FIX: scan_data ist ein String, muss erst geparst werden
                if isinstance(scan_dict['scan_data'], str):
                    scan_dict['scan_data'] = json.loads(scan_dict['scan_data'])
                scan_dict['issues'] = scan_dict['scan_data'].get('issues', [])
                scan_dict['recommendations'] = scan_dict['scan_data'].get('recommendations', [])
                # ✅ NEU: Issue-Gruppen für professionelle UX
                scan_dict['issue_groups'] = scan_dict['scan_data'].get('issue_groups', [])
                scan_dict['grouping_stats'] = scan_dict['scan_data'].get('grouping_stats', {})
            
            return {
                "success": True,
                "data": {
                    "scan_id": scan_dict['scan_id'],
                    "url": scan_dict['url'],
                    "compliance_score": scan_dict['compliance_score'],
                    "total_risk_euro": scan_dict['total_risk_euro'],
                    "critical_issues": scan_dict['critical_issues'],
                    "warning_issues": scan_dict['warning_issues'],
                    "total_issues": scan_dict['total_issues'],
                    "scan_timestamp": scan_dict['scan_timestamp'].isoformat(),
                    "scan_duration_ms": scan_dict['scan_duration_ms'],
                    "issues": scan_dict.get('issues', []),
                    "recommendations": scan_dict.get('recommendations', []),
                    # ✅ NEU: Issue-Gruppen für professionelle UX
                    "issue_groups": scan_dict.get('issue_groups', []),
                    "grouping_stats": scan_dict.get('grouping_stats', {})
                }
            }
    
    except Exception as e:
        print(f"Error loading latest scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Scan-Ergebnisse: {str(e)}"
        )

@app.get("/api/scans/history")
async def get_scan_history(limit: int = 10, current_user: dict = Depends(get_current_user)):
    """
    Holt die Scan-Historie für den aktuellen User
    """
    try:
        async with db_pool.acquire() as connection:
            scans = await connection.fetch(
                """
                SELECT 
                    scan_id,
                    url,
                    compliance_score,
                    total_risk_euro,
                    critical_issues,
                    warning_issues,
                    total_issues,
                    scan_timestamp
                FROM scan_history
                WHERE user_id = $1
                ORDER BY scan_timestamp DESC
                LIMIT $2
                """,
                current_user["user_id"],
                limit
            )
            
            return {
                "success": True,
                "data": [dict(scan) for scan in scans]
            }
    
    except Exception as e:
        print(f"Error loading scan history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Scan-Historie: {str(e)}"
        )

# ========== FIX JOBS ENDPOINTS ==========

class CreateFixJobRequest(BaseModel):
    scan_id: str
    issue_id: str
    issue_data: Dict[str, Any]

@app.post("/api/fix-jobs")
async def create_fix_job(
    request: CreateFixJobRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Erstellt einen neuen Fix-Job für ein Issue
    Der Job läuft im Hintergrund weiter, auch bei Page-Refresh
    """
    try:
        scan_id = request.scan_id
        issue_id = request.issue_id
        issue_data = request.issue_data
        async with db_pool.acquire() as connection:
            # Prüfe ob Scan existiert und dem User gehört
            scan = await connection.fetchrow(
                "SELECT scan_id FROM scan_history WHERE scan_id = $1 AND user_id = $2",
                scan_id, current_user["user_id"]
            )
            
            if not scan:
                raise HTTPException(status_code=404, detail="Scan not found")
            
            # Erstelle Job
            job = await connection.fetchrow(
                """
                INSERT INTO fix_jobs (
                    user_id, scan_id, issue_id, issue_data, 
                    status, progress_percent, current_step
                )
                VALUES ($1, $2, $3, $4, 'pending', 0, 'Initialisierung...')
                RETURNING job_id, created_at
                """,
                current_user["user_id"],
                scan_id,
                issue_id,
                json.dumps(issue_data)
            )
            
            return {
                "success": True,
                "data": {
                    "job_id": job['job_id'],
                    "status": "pending",
                    "created_at": job['created_at'].isoformat()
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating fix job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Fix-Jobs: {str(e)}"
        )

@app.get("/api/fix-jobs/{job_id}/status")
async def get_fix_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """
    Holt den aktuellen Status eines Fix-Jobs
    """
    try:
        async with db_pool.acquire() as connection:
            job = await connection.fetchrow(
                """
                SELECT 
                    job_id, scan_id, issue_id, status, 
                    progress_percent, current_step, result,
                    error_message, created_at, started_at, completed_at
                FROM fix_jobs
                WHERE job_id = $1 AND user_id = $2
                """,
                job_id,
                current_user["user_id"]
            )
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            job_dict = dict(job)
            
            # Parse result wenn vorhanden
            if job_dict.get('result'):
                job_dict['result'] = json.loads(job_dict['result']) if isinstance(job_dict['result'], str) else job_dict['result']
            
            # Konvertiere Timestamps zu ISO-Format
            for key in ['created_at', 'started_at', 'completed_at']:
                if job_dict.get(key):
                    job_dict[key] = job_dict[key].isoformat()
            
            return {
                "success": True,
                "data": job_dict
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Job-Status: {str(e)}"
        )

@app.get("/api/fix-jobs/active")
async def get_active_fix_jobs(current_user: dict = Depends(get_current_user)):
    """
    Holt alle aktiven (pending/processing/completed in letzten 10 Min) Fix-Jobs für den User
    """
    try:
        async with db_pool.acquire() as connection:
            # ✅ FIX: Zeige auch kürzlich abgeschlossene Jobs (10 Minuten)
            jobs = await connection.fetch(
                """
                SELECT job_id, user_id, scan_id, issue_id, issue_data,
                       status, progress_percent, current_step, result,
                       error_message, created_at, started_at, completed_at,
                       estimated_duration_seconds,
                       (created_at + (estimated_duration_seconds || ' seconds')::interval) as estimated_completion
                FROM fix_jobs
                WHERE user_id = $1
                  AND (
                    status IN ('pending', 'processing')
                    OR (status = 'completed' AND completed_at > NOW() - INTERVAL '10 minutes')
                    OR (status = 'failed' AND completed_at > NOW() - INTERVAL '10 minutes')
                  )
                ORDER BY created_at DESC
                """,
                current_user["user_id"]
            )
            
            jobs_list = []
            for job in jobs:
                job_dict = dict(job)
                # Konvertiere Timestamps
                for key in ['created_at', 'estimated_completion']:
                    if job_dict.get(key):
                        job_dict[key] = job_dict[key].isoformat()
                jobs_list.append(job_dict)
            
            return {
                "success": True,
                "data": jobs_list
            }
    
    except Exception as e:
        print(f"Error getting active jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen aktiver Jobs: {str(e)}"
        )

# ========== REPORTING ENDPOINTS ==========

@app.get("/api/v2/reports/{scan_id}/download")
async def download_report(scan_id: str, current_user: dict = Depends(get_current_user)):
    try:
        async with db_pool.acquire() as connection:
            scan_result = await connection.fetchrow(
                "SELECT * FROM scan_history WHERE scan_id = $1 AND user_id = $2",
                scan_id, current_user["user_id"]
            )
        
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan not found or access denied.")

        # 2. Generate the PDF report
        report_bytes = pdf_generator.generate_compliance_report(dict(scan_result))
        
        # 3. Stream the PDF as a response
        return StreamingResponse(io.BytesIO(report_bytes), media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=complyo-report-{scan_id}.pdf"
        })

    except HTTPException:
        raise
    except Exception as e:
        print(f"Report generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF-Generierung fehlgeschlagen: {str(e)}"
        )

# ========== PAYMENT ENDPOINTS ==========

@app.post("/api/v2/payments/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        async with db_pool.acquire() as connection:
            user = await connection.fetchrow(
                "SELECT email, name FROM users WHERE id = $1",
                current_user["user_id"]
            )
        
        result = await stripe_service.create_checkout_session(
            user_id=current_user["user_id"],
            price_id=request.price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            email=user['email'],
            name=user.get('full_name') or user.get('name', 'Unknown')
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

@app.post("/api/v2/payments/create-portal-session")
async def create_portal_session(current_user: dict = Depends(get_current_user)):
    try:
        result = await stripe_service.create_portal_session(
            user_id=current_user["user_id"],
            return_url="https://complyo.ai/dashboard"  # Adjust this URL as needed
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")

@app.get("/api/v2/payments/subscription-status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    try:
        status = await stripe_service.get_subscription_status(current_user["user_id"])
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscription status: {str(e)}")

@app.get("/api/v2/payments/history")
async def get_payment_history(current_user: dict = Depends(get_current_user)):
    try:
        history = await stripe_service.get_payment_history(current_user["user_id"])
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment history: {str(e)}")

@app.get("/api/v2/payments/plans")
async def get_available_plans():
    try:
        plans = await stripe_service.get_available_plans()
        return {"success": True, "data": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available plans: {str(e)}")

@app.post("/api/v2/payments/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_service.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await stripe_service.handle_checkout_completed(session)
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        await stripe_service.handle_subscription_updated(subscription)
    elif event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        await stripe_service.handle_invoice_paid(invoice)

    return {"success": True}


# ===== eRecht24 Rechtstexte API =====
# Automatische Generierung von Impressum, Datenschutzerklärung, etc.

@app.get("/api/erecht24/status")
async def get_erecht24_status():
    """Prüft den Status der eRecht24 Rechtstexte-API"""
    try:
        # Teste API-Verbindung durch Abruf der Client-Liste
        clients = await erecht24_rechtstexte_service.get_client_list()
        
        return {
            "status": "connected" if clients is not None else "disconnected",
            "api_url": erecht24_rechtstexte_service.API_BASE_URL,
            "has_api_key": bool(erecht24_rechtstexte_service.api_key),
            "plugin_key": erecht24_rechtstexte_service.plugin_key,
            "registered_clients": len(clients) if clients else 0
        }
    except Exception as e:
        logger.error(f"❌ eRecht24 Status-Check fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"eRecht24 Status-Check fehlgeschlagen: {str(e)}"
        )


@app.get("/api/erecht24/imprint")
async def get_impressum(
    language: str = "de",
    current_user: dict = Depends(get_current_user)
):
    """
    Generiert ein rechtssicheres Impressum mit eRecht24
    
    Args:
        language: Sprache (de, en, fr)
    """
    try:
        html_text = await erecht24_rechtstexte_service.get_imprint(language)
        
        if not html_text:
            raise HTTPException(
                status_code=404,
                detail="Impressum konnte nicht abgerufen werden. Bitte prüfen Sie Ihren eRecht24 API-Key."
            )
        
        return {
            "success": True,
            "text_type": "imprint",
            "language": language,
            "html": html_text,
            "generated_at": datetime.utcnow().isoformat(),
            "source": "eRecht24"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Impressum-Generierung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Impressum-Generierung fehlgeschlagen: {str(e)}"
        )


@app.get("/api/erecht24/privacy-policy")
async def get_datenschutzerklaerung(
    language: str = "de",
    current_user: dict = Depends(get_current_user)
):
    """
    Generiert eine rechtssichere Datenschutzerklärung mit eRecht24
    
    Args:
        language: Sprache (de, en, fr)
    """
    try:
        html_text = await erecht24_rechtstexte_service.get_privacy_policy(language)
        
        if not html_text:
            raise HTTPException(
                status_code=404,
                detail="Datenschutzerklärung konnte nicht abgerufen werden. Bitte prüfen Sie Ihren eRecht24 API-Key."
            )
        
        return {
            "success": True,
            "text_type": "privacy_policy",
            "language": language,
            "html": html_text,
            "generated_at": datetime.utcnow().isoformat(),
            "source": "eRecht24"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Datenschutzerklärung-Generierung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Datenschutzerklärung-Generierung fehlgeschlagen: {str(e)}"
        )


@app.get("/api/erecht24/privacy-policy-social-media")
async def get_datenschutz_social_media(
    language: str = "de",
    current_user: dict = Depends(get_current_user)
):
    """
    Generiert eine Datenschutzerklärung für Social Media mit eRecht24
    
    Args:
        language: Sprache (de, en, fr)
    """
    try:
        html_text = await erecht24_rechtstexte_service.get_privacy_policy_social_media(language)
        
        if not html_text:
            raise HTTPException(
                status_code=404,
                detail="Social Media Datenschutzerklärung konnte nicht abgerufen werden."
            )
        
        return {
            "success": True,
            "text_type": "privacy_policy_social_media",
            "language": language,
            "html": html_text,
            "generated_at": datetime.utcnow().isoformat(),
            "source": "eRecht24"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Social Media Datenschutz-Generierung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Social Media Datenschutz-Generierung fehlgeschlagen: {str(e)}"
        )


class ERecht24ClientCreate(BaseModel):
    push_uri: str
    cms: str = "Custom"
    cms_version: str = "1.0"
    plugin_name: str = "complyo-ai-compliance"
    author_mail: str = "api@complyo.tech"
    push_method: str = "POST"


@app.post("/api/erecht24/clients")
async def register_erecht24_client(
    client_data: ERecht24ClientCreate,
    current_user: dict = Depends(get_current_user)
):
    """Registriert einen neuen eRecht24 Client für Push-Notifications"""
    try:
        client = await erecht24_rechtstexte_service.create_client(
            push_uri=client_data.push_uri,
            cms=client_data.cms,
            cms_version=client_data.cms_version,
            plugin_name=client_data.plugin_name,
            author_mail=client_data.author_mail,
            push_method=client_data.push_method
        )
        
        if not client:
            raise HTTPException(
                status_code=500,
                detail="Client-Registrierung fehlgeschlagen"
            )
        
        return {
            "success": True,
            "client": client,
            "message": "Client erfolgreich registriert"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Client-Registrierung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Client-Registrierung fehlgeschlagen: {str(e)}"
        )


@app.get("/api/erecht24/clients")
async def list_erecht24_clients(
    current_user: dict = Depends(get_current_user)
):
    """Listet alle registrierten eRecht24 Clients auf"""
    try:
        clients = await erecht24_rechtstexte_service.get_client_list()
        
        if clients is None:
            clients = []
        
        return {
            "success": True,
            "clients": clients,
            "count": len(clients)
        }
    except Exception as e:
        logger.error(f"❌ Client-Listen-Abruf fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Client-Listen-Abruf fehlgeschlagen: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run("main_production:app", host="0.0.0.0", port=port, reload=True)
