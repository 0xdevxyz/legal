import os
import bcrypt as _bcrypt
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import uuid4
import asyncpg
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min

def _utcnow():
    return datetime.now(timezone.utc)

class AuthService:
    def __init__(self, db_pool: asyncpg.Pool, redis_client=None):
        self.db_pool = db_pool
        self.redis = redis_client

        self.jwt_secret = os.getenv("JWT_SECRET")
        if not self.jwt_secret:
            raise RuntimeError("❌ CRITICAL: JWT_SECRET environment variable is required!")
        self.jwt_issuer = os.getenv("FRONTEND_URL", "https://complyo.tech")
        self.jwt_audience = "complyo-api"
        self.access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.refresh_token_expire = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")) * 24 * 60
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, company, password_hash, is_active, is_verified, created_at FROM users WHERE email = $1",
                email
            )
            return dict(user) if user else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID including plan_type and active_modules"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, company, is_active, is_verified, created_at, onboarding_completed, role FROM users WHERE id = $1",
                user_id
            )
            if not user:
                return None

            result = dict(user)

            # plan_type + plan_limits aus user_limits
            limits = await conn.fetchrow(
                "SELECT plan_type, websites_max, exports_max FROM user_limits WHERE user_id = $1",
                user_id
            )
            if limits:
                result['plan_type'] = limits['plan_type']
                result['plan_limits'] = {
                    'websites_max': limits['websites_max'],
                    'exports_max':  limits['exports_max'],
                }
            else:
                result['plan_type'] = 'free'
                result['plan_limits'] = {'websites_max': 1, 'exports_max': 10}

            # aktive Module
            modules = await conn.fetch(
                """
                SELECT module_id FROM user_modules
                WHERE user_id = $1 AND status = 'active'
                  AND (expires_at IS NULL OR expires_at > NOW())
                """,
                user_id
            )
            result['active_modules'] = [r['module_id'] for r in modules]

            return result
    
    async def register_user(self, email: str, password: str, full_name: str, company: str = None) -> Dict:
        """Register a new user"""
        try:
            # Hash password with bcrypt
            password_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
            
            # Insert user
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    INSERT INTO users (email, password_hash, full_name, company)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, email, full_name, company, created_at
                    """,
                    email, password_hash, full_name, company
                )

            logger.info(f"User registered: {email}")
            return dict(user)
        except asyncpg.UniqueViolationError:
            logger.warning(f"Registration failed: Email already exists {email}")
            raise ValueError("Email already registered")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise
    
    async def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password, enforcing brute-force lockout."""
        lockout_key = f"login_fail:{email.lower()}"

        if self.redis:
            try:
                attempts = await self.redis.get(lockout_key)
                if attempts and int(attempts) >= _MAX_ATTEMPTS:
                    ttl = await self.redis.ttl(lockout_key)
                    logger.warning(f"Account locked: {email} ({attempts} attempts, {ttl}s remaining)")
                    raise HTTPException(
                        status_code=429,
                        detail=f"Account temporarily locked due to too many failed attempts. Try again in {ttl} seconds."
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Redis lockout check failed: {e}")

        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, company, password_hash, is_active, is_verified, created_at FROM users WHERE email = $1 AND is_active = TRUE",
                email
            )

        if not user:
            if self.redis:
                try:
                    await self.redis.incr(lockout_key)
                    await self.redis.expire(lockout_key, _LOCKOUT_SECONDS)
                except Exception:
                    pass
            logger.warning(f"Authentication failed: User not found {email}")
            return None

        if not _bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            if self.redis:
                try:
                    await self.redis.incr(lockout_key)
                    await self.redis.expire(lockout_key, _LOCKOUT_SECONDS)
                except Exception:
                    pass
            logger.warning(f"Authentication failed: Invalid password for {email}")
            return None

        if self.redis:
            try:
                await self.redis.delete(lockout_key)
            except Exception:
                pass

        logger.info(f"User authenticated: {email}")
        user_dict = dict(user)
        del user_dict['password_hash']
        return user_dict
    
    def create_access_token(self, user_id) -> str:
        """Create JWT access token with jti, iat, nbf claims"""
        now = _utcnow()
        now_ts = int(now.timestamp())
        expire_seconds = self.access_token_expire * 60
        jti = str(uuid4())
        payload = {
            "id": str(user_id),
            "user_id": str(user_id),
            "jti": jti,
            "iat": now_ts,
            "nbf": now_ts - 30,
            "exp": now + timedelta(minutes=self.access_token_expire),
            "iss": self.jwt_issuer,
            "aud": self.jwt_audience,
            "type": "access"
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        if self.redis:
            import asyncio
            uid = int(user_id)
            set_key = f"jwt:user_jtis:{uid}"
            max_ttl = expire_seconds + 60
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._register_jti_in_set(set_key, jti, max_ttl))
            except Exception:
                pass

        return token

    async def _register_jti_in_set(self, set_key: str, jti: str, ttl: int):
        """Add jti to user's active-JTI set in Redis (best-effort)."""
        if not self.redis:
            return
        try:
            await self.redis.sadd(set_key, jti)
            await self.redis.expire(set_key, ttl)
        except Exception as e:
            logger.warning(f"Redis SADD jti failed: {e}")

    async def _blacklist_jti(self, jti: str, ttl_seconds: int):
        """Put jti on the Redis blacklist with TTL = remaining token lifetime."""
        if not self.redis:
            return
        try:
            await self.redis.setex(f"jwt:blacklist:{jti}", ttl_seconds, "1")
        except Exception as e:
            logger.warning(f"Redis blacklist jti failed: {e}")

    async def _is_jti_blacklisted(self, jti: str) -> bool:
        """Return True if jti is on the Redis blacklist."""
        if not self.redis:
            return False
        try:
            result = await self.redis.get(f"jwt:blacklist:{jti}")
            return result is not None
        except Exception as e:
            logger.warning(f"Redis blacklist check failed: {e}")
            return False
    
    async def create_refresh_token(self, user_id, user_agent: str = None, ip_address: str = None) -> str:
        """Create and store refresh token with session metadata"""
        token = secrets.token_urlsafe(64)
        user_id = int(user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.refresh_token_expire)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_sessions (user_id, refresh_token, expires_at, user_agent, ip_address)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, token, expires_at, user_agent, ip_address
            )
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"], audience=self.jwt_audience, issuer=self.jwt_issuer)
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str, user_agent: str = None, ip_address: str = None) -> Optional[tuple]:
        """Refresh access token using refresh token (with rotation + reuse-detection)"""
        async with self.db_pool.acquire() as conn:
            session = await conn.fetchrow(
                """
                SELECT user_id, expires_at FROM user_sessions
                WHERE refresh_token = $1
                """,
                refresh_token
            )
        
        if not session:
            logger.warning("Refresh token not found in DB — possible reuse attack, checking token format")
            return None
        
        if session['expires_at'] < datetime.now(timezone.utc):
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM user_sessions WHERE refresh_token = $1",
                    refresh_token
                )
            return None
        
        user_id = session['user_id']
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_sessions WHERE refresh_token = $1",
                refresh_token
            )
        
        new_access_token = self.create_access_token(user_id)
        new_refresh_token = await self.create_refresh_token(user_id, user_agent=user_agent, ip_address=ip_address)
        
        return new_access_token, new_refresh_token
    
    async def revoke_refresh_token(self, refresh_token: str):
        """Revoke a refresh token (logout)"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_sessions WHERE refresh_token = $1",
                refresh_token
            )

    async def revoke_all_sessions(self, user_id: int):
        """Delete all sessions for a user (logout-all or reuse-attack response)."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_sessions WHERE user_id = $1",
                user_id
            )
        logger.info(f"All sessions revoked for user_id={user_id}")

    async def blacklist_all_user_jtis(self, user_id: int, ttl_seconds: int):
        """Blacklist every jti stored in jwt:user_jtis:{user_id} Redis set."""
        if not self.redis:
            return
        set_key = f"jwt:user_jtis:{user_id}"
        try:
            members = await self.redis.smembers(set_key)
            for jti in members:
                await self._blacklist_jti(jti, ttl_seconds)
            await self.redis.delete(set_key)
        except Exception as e:
            logger.warning(f"Redis blacklist-all failed for user_id={user_id}: {e}")

    async def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP"
            )
        logger.info(f"Cleaned up expired sessions: {result}")

