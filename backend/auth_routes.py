from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
import secrets
import os
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from schemas.auth import LoginResponse, RegisterResponse, RefreshResponse, MeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

# Global reference to services (will be set in main_production.py)
auth_service = None
db_pool = None
oauth_service = None  # OAuth Service for Google & Apple
firebase_verify_token = None  # Firebase token verification function

# Cookie domain for cross-subdomain sharing (app.complyo.de <-> api.complyo.de)
COOKIE_DOMAIN = ".complyo.de" if os.getenv("ENVIRONMENT", "production") == "production" else None

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

@router.post("/register", response_model=RegisterResponse)
@limiter.limit("3/hour")
async def register(request: Request, body: RegisterRequest):
    """Register a new user"""
    if auth_service is None:
        logger.error("Auth service not initialized")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    if db_pool is None:
        logger.error("Database pool not initialized")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available"
        )
    
    try:
        # Check if email exists
        existing = await auth_service.get_user_by_email(body.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email bereits registriert"
            )
        
        # Create user
        user = await auth_service.register_user(
            body.email,
            body.password,
            body.full_name,
            body.company
        )
        
        # Initialize user_limits
        await init_user_limits(user['id'], body.plan)
        
        # Create tokens
        access_token = auth_service.create_access_token(user['id'])
        refresh_token = await auth_service.create_refresh_token(user['id'])
        
        is_secure = os.getenv("ENVIRONMENT", "production") == "production"
        access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        response = JSONResponse({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user['id']),
                "email": user['email'],
                "full_name": user['full_name'],
                "company": user.get('company'),
                "onboarding_completed": False
            }
        })
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=access_token_expire * 60,
            path="/",
            domain=COOKIE_DOMAIN
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
            domain=COOKIE_DOMAIN
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registrierung fehlgeschlagen"
        )
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

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    """Login user"""
    if auth_service is None:
        logger.error("Auth service not initialized")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    try:
        user = await auth_service.authenticate(body.email, body.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Zugangsdaten"
            )
        
        # Create tokens
        access_token = auth_service.create_access_token(user['id'])
        refresh_token = await auth_service.create_refresh_token(user['id'])

        async with auth_service.db_pool.acquire() as conn:
            onboarding_completed = await conn.fetchval(
                "SELECT onboarding_completed FROM users WHERE id = $1", user['id']
            ) or False

        is_secure = os.getenv("ENVIRONMENT", "production") == "production"
        access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        response = JSONResponse({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user['id']),
                "email": user['email'],
                "full_name": user['full_name'],
                "company": user.get('company'),
                "onboarding_completed": onboarding_completed
            }
        })
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=access_token_expire * 60,
            path="/",
            domain=COOKIE_DOMAIN
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
            domain=COOKIE_DOMAIN
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login fehlgeschlagen"
        )

@router.post("/refresh", response_model=RefreshResponse)
@limiter.limit("10/minute")
async def refresh_token(request: Request, body: RefreshRequest):
    """Refresh access token with token rotation"""
    result = await auth_service.refresh_access_token(body.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    new_access_token, new_refresh_token = result
    is_secure = os.getenv("ENVIRONMENT", "production") == "production"
    response = JSONResponse({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    })
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
        domain=COOKIE_DOMAIN
    )
    return response

@router.post("/refresh-cookie")
@limiter.limit("10/minute")
async def refresh_token_from_cookie(request: Request):
    """Refresh access token using HttpOnly cookie (with token rotation)"""
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        return JSONResponse(status_code=204, content=None)
    result = await auth_service.refresh_access_token(refresh_token_value)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    new_access_token, new_refresh_token = result
    payload = auth_service.verify_token(new_access_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token verification failed")
    raw_id = payload.get("user_id") or payload.get("id") or payload.get("sub")
    if not raw_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID not found in token")
    try:
        user_id = int(raw_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid user ID in token")
    async with auth_service.db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, full_name, company, plan_type, onboarding_completed FROM users WHERE id = $1",
            user_id
        )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    is_secure = os.getenv("ENVIRONMENT", "production") == "production"
    access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    response = JSONResponse({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "company": user.get("company"),
            "plan_type": user.get("plan_type", "free"),
            "onboarding_completed": user.get("onboarding_completed") or False
        }
    })
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=access_token_expire * 60,
        path="/",
        domain=COOKIE_DOMAIN
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
        domain=COOKIE_DOMAIN
    )
    return response

@router.post("/oauth-pickup")
async def oauth_token_pickup(request: Request):
    """
    One-time endpoint for the frontend OAuth callback page to collect the
    access token after a social login redirect.

    The access token is stored in a short-lived (5 min) HttpOnly cookie
    'access_token_once' after the OAuth redirect. This endpoint returns it
    exactly once and immediately clears the cookie.
    """
    token = request.cookies.get("access_token_once")
    if not token:
        raise HTTPException(status_code=400, detail="No pending OAuth token")

    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    user_id = int(payload.get("user_id") or payload.get("id") or payload.get("sub"))
    async with auth_service.db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, full_name, company, plan_type, onboarding_completed FROM users WHERE id = $1",
            user_id
        )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    is_secure = os.getenv("ENVIRONMENT", "production") == "production"
    response = JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "company": user.get("company"),
            "plan_type": user.get("plan_type", "free"),
            "onboarding_completed": user.get("onboarding_completed") or False,
        }
    })
    response.delete_cookie(key="access_token_once", path="/api/auth", httponly=True, secure=is_secure, samesite="lax")
    return response


@router.post("/logout")
async def logout(request: Request):
    """Logout user: blacklist JTI, revoke refresh token, clear cookies"""
    import jwt as _jwt
    from dependencies import get_settings

    token_from_cookie = request.cookies.get("refresh_token")
    token_from_body: Optional[str] = None
    try:
        body = await request.json()
        token_from_body = body.get("refresh_token")
    except Exception:
        pass

    token = token_from_cookie or token_from_body
    if token:
        await auth_service.revoke_refresh_token(token)

    access_token: Optional[str] = None
    cred_header = request.headers.get("Authorization", "")
    if cred_header.startswith("Bearer "):
        access_token = cred_header[7:]
    if not access_token:
        access_token = request.cookies.get("access_token")

    if access_token and auth_service:
        try:
            settings = get_settings()
            payload = _jwt.decode(
                access_token,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                import time
                ttl = max(int(exp - time.time()), 1)
                await auth_service._blacklist_jti(jti, ttl)
        except Exception:
            pass

    is_secure = os.getenv("ENVIRONMENT", "production") == "production"
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie(key="refresh_token", path="/", httponly=True, secure=is_secure, samesite="lax", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="access_token", path="/", httponly=True, secure=is_secure, samesite="lax", domain=COOKIE_DOMAIN)
    return response


@router.post("/logout-all")
async def logout_all(request: Request):
    """Logout all sessions for the current user: blacklist all JTIs, delete all sessions"""
    import jwt as _jwt
    from dependencies import get_settings

    current_user: Optional[dict] = None
    try:
        cred_header = request.headers.get("Authorization", "")
        token: Optional[str] = None
        if cred_header.startswith("Bearer "):
            token = cred_header[7:]
        if not token:
            token = request.cookies.get("access_token")
        if token:
            settings = get_settings()
            payload = _jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
            )
            raw_id = payload.get("user_id") or payload.get("id")
            if raw_id:
                current_user = {"id": int(raw_id)}
    except Exception:
        pass

    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    user_id = current_user["id"]
    expire_seconds = auth_service.access_token_expire * 60
    await auth_service.blacklist_all_user_jtis(user_id, expire_seconds)
    await auth_service.revoke_all_sessions(user_id)

    is_secure = os.getenv("ENVIRONMENT", "production") == "production"
    response = JSONResponse({"message": "All sessions logged out"})
    response.delete_cookie(key="refresh_token", path="/", httponly=True, secure=is_secure, samesite="lax", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="access_token", path="/", httponly=True, secure=is_secure, samesite="lax", domain=COOKIE_DOMAIN)
    return response

@router.post("/complete-onboarding")
async def complete_onboarding(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Mark onboarding as completed for the current user"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    raw_id = payload.get("user_id") or payload.get("id") or payload.get("sub")
    if not raw_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
    try:
        user_id = int(raw_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token")
    async with auth_service.db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET onboarding_completed = TRUE WHERE id = $1", user_id
        )
    return {"onboarding_completed": True}

from dependencies import get_current_user

@router.get("/me", response_model=MeResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# ============= NextAuth.js v5 Credential Endpoints =============

class VerifyCredentialsRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/verify-credentials")
@limiter.limit("5/minute")
async def verify_credentials(request: Request, body: VerifyCredentialsRequest):
    """NextAuth.js v5 credentials provider endpoint — verify email/password and return user data"""
    if auth_service is None:
        raise HTTPException(status_code=503, detail="Auth service not available")
    user = await auth_service.authenticate(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    async with auth_service.db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT onboarding_completed, role FROM users WHERE id = $1",
            user['id']
        )
        limits_row = await conn.fetchrow(
            "SELECT plan_type FROM user_limits WHERE user_id = $1",
            user['id']
        )
    plan_type = limits_row['plan_type'] if limits_row else (row['plan_type'] if row and 'plan_type' in row.keys() else 'free')
    return {
        "id": str(user['id']),
        "email": user['email'],
        "full_name": user.get('full_name'),
        "company": user.get('company'),
        "plan_type": plan_type,
        "role": row['role'] if row else 'customer',
        "onboarding_completed": row['onboarding_completed'] if row else False,
    }

@router.get("/session-info")
async def session_info(current_user: dict = Depends(get_current_user)):
    """Return enriched session data for NextAuth.js v5 session callback"""
    return {
        "id": str(current_user['id']),
        "email": current_user.get('email'),
        "full_name": current_user.get('full_name'),
        "company": current_user.get('company'),
        "plan_type": current_user.get('plan_type', 'free'),
        "role": current_user.get('role', 'customer'),
        "onboarding_completed": current_user.get('onboarding_completed', False),
        "active_modules": current_user.get('active_modules', []),
    }

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
        
        # Set HttpOnly cookie and redirect cleanly — never put tokens in URL fragments
        is_secure = os.getenv("ENVIRONMENT", "production") == "production"
        frontend_url = os.getenv("FRONTEND_URL", "https://app.complyo.tech")
        response = RedirectResponse(url=f"{frontend_url}/auth/callback?provider=google&status=ok")
        response.set_cookie(
            key="access_token_once",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=300,  # 5 min one-time pickup window
            path="/api/auth",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
            domain=COOKIE_DOMAIN,
        )
        return response

    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(500, "OAuth authentication failed")

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
        
        is_secure = os.getenv("ENVIRONMENT", "production") == "production"
        frontend_url = os.getenv("FRONTEND_URL", "https://app.complyo.tech")
        response = RedirectResponse(url=f"{frontend_url}/auth/callback?provider=apple&status=ok")
        response.set_cookie(
            key="access_token_once",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=300,
            path="/api/auth",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
            domain=COOKIE_DOMAIN,
        )
        return response

    except Exception as e:
        logger.error(f"Apple OAuth error: {e}")
        raise HTTPException(500, "OAuth authentication failed")

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
                "id": str(user['id']),
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

@router.post("/admin/reset-master-password")
@limiter.limit("3/hour")
async def reset_master_password(request: Request, admin_key: str = Query(..., alias="admin_key")):
    """
    Admin Endpoint: Setzt das Passwort für master@complyo.tech zurück

    Query Parameter:
    - admin_key: Admin-Schlüssel (muss als ADMIN_KEY env var gesetzt sein)
    """
    import bcrypt
    
    # Admin-Authentifizierung via Env-Var (kein Default-Wert!)
    expected_key = os.getenv("ADMIN_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin key not configured"
        )
    if admin_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    if auth_service is None or db_pool is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Services not initialized"
        )

    email = "master@complyo.tech"
    # Password must be provided via query param — never hardcoded
    new_password = os.getenv("MASTER_RESET_PASSWORD")
    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MASTER_RESET_PASSWORD env var not set"
        )
    
    try:
        # Prüfe ob User existiert
        user = await auth_service.get_user_by_email(email)
        
        if not user:
            # User erstellen
            user = await auth_service.register_user(
                email,
                new_password,
                "Master User",
                "Complyo"
            )
            
            # User Limits initialisieren
            await init_user_limits(user['id'], 'expert')
            
            logger.info(f"Master user created: {email}")
            return {
                "success": True,
                "message": "Master user created — password set from MASTER_RESET_PASSWORD env var",
                "email": email,
            }
        else:
            # Passwort zurücksetzen
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE users
                    SET hashed_password = $1,
                        is_active = TRUE,
                        is_verified = TRUE
                    WHERE email = $2
                    """,
                    password_hash, email
                )

            logger.info(f"Master user password reset: {email}")
            return {
                "success": True,
                "message": "Password reset successfully — new password is in MASTER_RESET_PASSWORD env var",
                "email": email,
            }
            
    except Exception as e:
        logger.error(f"Error resetting master password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )
