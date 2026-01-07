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
from typing import Optional, AsyncGenerator
from functools import lru_cache

import asyncpg
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Dependency: Get current authenticated user.
    
    Raises HTTPException 401 if not authenticated.
    
    Usage:
        @router.get("/profile")
        async def get_profile(current_user: dict = Depends(get_current_user)):
            return {"user_id": current_user["user_id"]}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings)
) -> Optional[dict]:
    """
    Dependency: Get current user if authenticated, None otherwise.
    
    Does NOT raise exception if not authenticated.
    
    Usage:
        @router.get("/public")
        async def public_endpoint(user: Optional[dict] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user['email']}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

async def require_admin(
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Pool = Depends(get_db)
) -> dict:
    """
    Dependency: Require admin/superuser access.
    
    Raises HTTPException 403 if not admin.
    
    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
            ...
    """
    async with db.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT is_superuser FROM users WHERE id = $1",
            current_user.get("user_id")
        )
    
    if not user or not user["is_superuser"]:
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
    
    Handles X-Forwarded-For header for proxied requests.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

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


