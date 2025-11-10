from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
import secrets
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

# Global reference to services (will be set in main_production.py)
auth_service = None
db_pool = None
oauth_service = None  # OAuth Service for Google & Apple
firebase_verify_token = None  # Firebase token verification function

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: Optional[str] = None
    plan: str = "ki"  # 'ki' oder 'expert'

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RefreshRequest(BaseModel):
    refresh_token: str

async def init_user_limits(user_id: int, plan_type: str):
    """Initialize user_limits for new user"""
    async with db_pool.acquire() as conn:
        # Check if already exists
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM user_limits WHERE user_id = $1)",
            user_id
        )
        
        if not exists:
            websites_max = 1
            exports_max = -1 if plan_type == 'expert' else 10
            
            await conn.execute(
                """
                INSERT INTO user_limits (user_id, plan_type, websites_max, exports_max, exports_reset_date)
                VALUES ($1, $2, $3, $4, CURRENT_DATE + INTERVAL '1 month')
                """,
                user_id, plan_type, websites_max, exports_max
            )
            logger.info(f"User limits initialized for user {user_id} with plan {plan_type}")

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if email exists
        existing = await auth_service.get_user_by_email(request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email bereits registriert"
            )
        
        # Create user
        user = await auth_service.register_user(
            request.email,
            request.password,
            request.full_name,
            request.company
        )
        
        # Initialize user_limits
        await init_user_limits(user['id'], request.plan)
        
        # Create tokens
        access_token = auth_service.create_access_token(user['id'])
        refresh_token = await auth_service.create_refresh_token(user['id'])
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "full_name": user['full_name'],
                "company": user.get('company')
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registrierung fehlgeschlagen"
        )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user"""
    user = await auth_service.authenticate(request.email, request.password)
    if not user:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige Zugangsdaten"
        )
    
    # Create tokens
    access_token = auth_service.create_access_token(user['id'])
    refresh_token = await auth_service.create_refresh_token(user['id'])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "company": user.get('company')
        }
    }

@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Refresh access token"""
    new_access_token = await auth_service.refresh_access_token(request.refresh_token)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(request: RefreshRequest):
    """Logout user (revoke refresh token)"""
    await auth_service.revoke_refresh_token(request.refresh_token)
    return {"message": "Logged out successfully"}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT token"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger Token"
        )
    
    # Get user from database
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User nicht gefunden"
        )
    
    return user

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# ============= OAuth2 Routes (Google & Apple) =============

@router.get("/google")
async def google_oauth_start():
    """Start Google OAuth flow"""
    if not oauth_service:
        raise HTTPException(500, "OAuth service not initialized")
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in database
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO oauth_states (state_token, provider, expires_at)
            VALUES ($1, 'google', $2)
            """,
            state, datetime.utcnow() + timedelta(minutes=10)
        )
    
    # Redirect to Google OAuth
    auth_url = oauth_service.get_google_auth_url(state)
    return {"auth_url": auth_url}

@router.get("/google/callback")
async def google_oauth_callback(code: str, state: str):
    """Handle Google OAuth callback"""
    if not oauth_service:
        raise HTTPException(500, "OAuth service not initialized")
    
    # Verify state token (CSRF protection)
    async with db_pool.acquire() as conn:
        state_record = await conn.fetchrow(
            "SELECT * FROM oauth_states WHERE state_token = $1 AND provider = 'google'",
            state
        )
        
        if not state_record or state_record['expires_at'] < datetime.utcnow():
            raise HTTPException(400, "Invalid or expired state token")
        
        # Delete used state token
        await conn.execute("DELETE FROM oauth_states WHERE state_token = $1", state)
    
    # Exchange code for user info
    try:
        google_user = await oauth_service.exchange_google_code(code)
        
        # Get or create user
        user = await oauth_service.get_or_create_oauth_user(
            provider='google',
            provider_user_id=google_user['id'],
            email=google_user['email'],
            full_name=google_user.get('name', google_user['email'].split('@')[0])
        )
        
        # Create tokens
        access_token = auth_service.create_access_token(user['id'])
        refresh_token = await auth_service.create_refresh_token(user['id'])
        
        # Redirect to frontend with tokens (via URL hash for security)
        frontend_url = "https://app.complyo.tech"
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        )
    
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(500, f"Google OAuth failed: {str(e)}")

@router.get("/apple")
async def apple_oauth_start():
    """Start Apple OAuth flow"""
    if not oauth_service:
        raise HTTPException(500, "OAuth service not initialized")
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in database
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO oauth_states (state_token, provider, expires_at)
            VALUES ($1, 'apple', $2)
            """,
            state, datetime.utcnow() + timedelta(minutes=10)
        )
    
    # Redirect to Apple OAuth
    auth_url = oauth_service.get_apple_auth_url(state)
    return {"auth_url": auth_url}

@router.post("/apple/callback")
async def apple_oauth_callback(code: str, state: str):
    """Handle Apple OAuth callback (POST)"""
    if not oauth_service:
        raise HTTPException(500, "OAuth service not initialized")
    
    # Verify state token (CSRF protection)
    async with db_pool.acquire() as conn:
        state_record = await conn.fetchrow(
            "SELECT * FROM oauth_states WHERE state_token = $1 AND provider = 'apple'",
            state
        )
        
        if not state_record or state_record['expires_at'] < datetime.utcnow():
            raise HTTPException(400, "Invalid or expired state token")
        
        # Delete used state token
        await conn.execute("DELETE FROM oauth_states WHERE state_token = $1", state)
    
    # Exchange code for user info
    try:
        apple_user = await oauth_service.exchange_apple_code(code)
        
        # Get or create user
        user = await oauth_service.get_or_create_oauth_user(
            provider='apple',
            provider_user_id=apple_user['sub'],
            email=apple_user['email'],
            full_name=apple_user.get('name', {}).get('firstName', apple_user['email'].split('@')[0])
        )
        
        # Create tokens
        access_token = auth_service.create_access_token(user['id'])
        refresh_token = await auth_service.create_refresh_token(user['id'])
        
        # Redirect to frontend with tokens
        frontend_url = "https://app.complyo.tech"
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        )
    
    except Exception as e:
        logger.error(f"Apple OAuth error: {e}")
        raise HTTPException(500, f"Apple OAuth failed: {str(e)}")

# ============= Firebase Auth Route =============

class FirebaseTokenRequest(BaseModel):
    id_token: str
    plan: str = "ki"  # Default plan for Firebase users

@router.post("/firebase-verify", response_model=TokenResponse)
async def firebase_verify(request: FirebaseTokenRequest):
    """
    Verify Firebase ID token and create/login user
    
    This endpoint:
    1. Verifies Firebase ID token with Admin SDK
    2. Creates user if doesn't exist (or gets existing user)
    3. Returns Complyo JWT tokens for API access
    """
    if not firebase_verify_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Auth ist nicht konfiguriert. Bitte Standardanmeldung verwenden."
        )
    
    try:
        # Verify Firebase token
        firebase_user = await firebase_verify_token(request.id_token)
        
        # Get or create user in Complyo database
        user = await auth_service.get_user_by_email(firebase_user['email'])
        
        if not user:
            # Create new user from Firebase data
            logger.info(f"Creating new user from Firebase: {firebase_user['email']}")
            user = await auth_service.register_user(
                email=firebase_user['email'],
                password=None,  # No password for Firebase users
                full_name=firebase_user.get('name', firebase_user['email'].split('@')[0]),
                company=None,
                firebase_uid=firebase_user['firebase_uid']
            )
            
            # Initialize user limits
            await init_user_limits(user['id'], request.plan)
        
        # Create Complyo JWT tokens
        access_token = auth_service.create_access_token(user['id'])
        refresh_token = await auth_service.create_refresh_token(user['id'])
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "full_name": user['full_name'],
                "company": user.get('company')
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Firebase verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase Authentifizierung fehlgeschlagen: {str(e)}"
        )

# ============= Health Check =============

@router.get("/health")
async def auth_health():
    """Health check for auth service"""
    return {
        "status": "healthy",
        "service": "authentication",
        "auth_service_initialized": auth_service is not None,
        "db_pool_initialized": db_pool is not None,
        "oauth_service_initialized": oauth_service is not None,
        "firebase_auth_initialized": firebase_verify_token is not None
    }
