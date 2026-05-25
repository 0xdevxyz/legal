"""
Complyo Dependency Injection Module
====================================

This module provides FastAPI dependencies for:
- Database connections
- Authentication
- Services
- Rate limiting

Usage:
    from dependencies import get_db, get_current_user, get_auth_service

    @router.get("/api/data")
    async def get_data(
        db: asyncpg.Pool = Depends(get_db),
        current_user: dict = Depends(get_current_user)
    ):
        ...
"""

import os
from typing import Optional, AsyncGenerator, List
from functools import lru_cache

import asyncpg
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging

logger = logging.getLogger(__name__)

# ==========================================
# Configuration
# ==========================================

class Settings:
    """Application settings loaded from environment."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.jwt_secret = os.getenv("JWT_SECRET")
        self.jwt_algorithm = "HS256"
        self.jwt_audience = "complyo-api"
        self.jwt_issuer = os.getenv("FRONTEND_URL", "https://complyo.tech")
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Validate required settings
        if not self.jwt_secret:
            raise RuntimeError("JWT_SECRET environment variable is required!")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL environment variable is required!")

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# ==========================================
# Database Dependencies
# ==========================================

# Global connection pool (initialized at startup)
_db_pool: Optional[asyncpg.Pool] = None
_redis_client: Optional[aioredis.Redis] = None

async def init_db_pool() -> asyncpg.Pool:
    """Initialize database connection pool."""
    global _db_pool
    if _db_pool is None:
        settings = get_settings()
        _db_pool = await asyncpg.create_pool(settings.database_url)
    return _db_pool

async def close_db_pool():
    """Close database connection pool."""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None

async def init_redis() -> Optional[aioredis.Redis]:
    """Initialize Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            settings = get_settings()
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await _redis_client.ping()
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            _redis_client = None
    return _redis_client

async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

async def get_db() -> asyncpg.Pool:
    """
    Dependency: Get database connection pool.
    
    Usage:
        @router.get("/users")
        async def get_users(db: asyncpg.Pool = Depends(get_db)):
            async with db.acquire() as conn:
                return await conn.fetch("SELECT * FROM users")
    """
    if _db_pool is None:
        await init_db_pool()
    return _db_pool

async def get_redis() -> Optional[aioredis.Redis]:
    """
    Dependency: Get Redis client (optional).
    
    Returns None if Redis is not available.
    
    Usage:
        @router.get("/cached")
        async def get_cached(redis: Optional[aioredis.Redis] = Depends(get_redis)):
            if redis:
                cached = await redis.get("key")
    """
    return _redis_client

# ==========================================
# Authentication Dependencies
# ==========================================

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Kanonische Auth-Dependency — Single Source of Truth.

    - Validiert JWT aus Bearer-Header ODER HttpOnly-Cookie 'access_token'
    - Lädt User aus DB via AuthService.get_user_by_id
    - Garantiert: id ist int, is_active ist True
    - Wirft 401 bei Token-Problem oder User-nicht-gefunden
    - Wirft 403 bei deaktiviertem User
    """
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

    raw_id = payload.get("user_id") or payload.get("id") or payload.get("sub")
    try:
        user_id = int(raw_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user_id in token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    jti = payload.get("jti")
    if jti:
        redis = await get_redis()
        if redis:
            try:
                blacklisted = await redis.get(f"jwt:blacklist:{jti}")
                if blacklisted:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has been revoked",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"JTI blacklist check failed: {e}")

    db = await get_db()
    from auth_service import AuthService
    auth = AuthService(db, await get_redis())
    user = await auth.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    user["id"] = int(user["id"])
    return user

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings)
) -> Optional[dict]:
    """
    Dependency: Get current user if authenticated, None otherwise.
    Does NOT raise exception if not authenticated.
    Reads token from Bearer header OR HttpOnly 'access_token' cookie.
    """
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

    raw_id = payload.get("user_id") or payload.get("id") or payload.get("sub")
    try:
        user_id = int(raw_id)
    except (TypeError, ValueError):
        return None

    db = await get_db()
    from auth_service import AuthService
    auth = AuthService(db)
    user = await auth.get_user_by_id(user_id)
    if not user or not user.get("is_active", True):
        return None

    user["id"] = int(user["id"])
    return user

async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Dependency: Require admin role access.
    
    Raises HTTPException 403 if not admin.
    
    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
            ...
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

# ==========================================
# Service Dependencies
# ==========================================

# Import services lazily to avoid circular imports
_auth_service = None
_stripe_service = None
_news_service = None

async def get_auth_service():
    """
    Dependency: Get AuthService instance.
    
    Usage:
        @router.post("/login")
        async def login(auth: AuthService = Depends(get_auth_service)):
            return await auth.authenticate(email, password)
    """
    global _auth_service
    if _auth_service is None:
        from auth_service import AuthService
        db = await get_db()
        _auth_service = AuthService(db)
    return _auth_service

async def get_stripe_service():
    """Dependency: Get StripeService instance."""
    global _stripe_service
    if _stripe_service is None:
        from payment.stripe_service import StripeService
        db = await get_db()
        _stripe_service = StripeService(db)
    return _stripe_service

async def get_news_service():
    """Dependency: Get NewsService instance."""
    global _news_service
    if _news_service is None:
        from news_service import NewsService
        db = await get_db()
        _news_service = NewsService(db)
    return _news_service

# ==========================================
# Utility Dependencies
# ==========================================

def get_client_ip(request: Request) -> str:
    """
    Dependency: Get client IP address.
    
    Only trusts X-Forwarded-For from known trusted proxies (TRUSTED_PROXIES env var,
    comma-separated). Falls back to direct client IP if the source is not trusted.
    """
    _trusted_raw = os.getenv("TRUSTED_PROXIES", "")
    trusted_proxies: List[str] = [p.strip() for p in _trusted_raw.split(",") if p.strip()]
    
    direct_ip = request.client.host if request.client else None
    
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded and direct_ip and direct_ip in trusted_proxies:
        return forwarded.split(",")[0].strip()
    
    return direct_ip or "unknown"

# ==========================================
# Lifecycle Management
# ==========================================

async def startup():
    """Initialize all dependencies on application startup."""
    print("🔄 Initializing dependencies...")
    await init_db_pool()
    await init_redis()
    print("✅ Dependencies initialized")

async def shutdown():
    """Cleanup all dependencies on application shutdown."""
    print("🔄 Shutting down dependencies...")
    await close_redis()
    await close_db_pool()
    print("✅ Dependencies cleaned up")


