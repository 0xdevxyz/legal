import os
import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncpg
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.jwt_secret = os.getenv("JWT_SECRET", "default-secret-change-in-production")
        self.access_token_expire = 7 * 24 * 60  # 7 Tage = 10080 Minuten
        self.refresh_token_expire = 30 * 24 * 60  # 30 days
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )
            return dict(user) if user else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, is_active, is_verified, created_at FROM users WHERE id = $1",
                user_id
            )
            return dict(user) if user else None
    
    async def register_user(self, email: str, password: str, full_name: str, company: str = None) -> Dict:
        """Register a new user"""
        try:
            # Hash password with bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert user
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    INSERT INTO users (email, hashed_password, full_name, company_name)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, email, full_name, company_name, created_at
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
        """Authenticate user with email and password"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1 AND is_active = TRUE",
                email
            )
        
        if not user:
            logger.warning(f"Authentication failed: User not found {email}")
            return None
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['hashed_password'].encode('utf-8')):
            logger.warning(f"Authentication failed: Invalid password for {email}")
            return None
        
        logger.info(f"User authenticated: {email}")
        # Return user without hashed_password
        user_dict = dict(user)
        del user_dict['hashed_password']
        return user_dict
    
    def create_access_token(self, user_id) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": str(user_id),  # Convert UUID to string
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    async def create_refresh_token(self, user_id) -> str:
        """Create and store refresh token"""
        token = secrets.token_urlsafe(64)
        user_id = str(user_id)  # Convert UUID to string
        expires_at = datetime.utcnow() + timedelta(minutes=self.refresh_token_expire)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_sessions (user_id, refresh_token, expires_at)
                VALUES ($1, $2, $3)
                """,
                user_id, token, expires_at
            )
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        async with self.db_pool.acquire() as conn:
            session = await conn.fetchrow(
                """
                SELECT user_id, expires_at FROM user_sessions
                WHERE refresh_token = $1
                """,
                refresh_token
            )
        
        if not session:
            return None
        
        # Check if token is expired
        if session['expires_at'] < datetime.utcnow():
            # Delete expired token
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM user_sessions WHERE refresh_token = $1",
                    refresh_token
                )
            return None
        
        # Create new access token
        return self.create_access_token(session['user_id'])
    
    async def revoke_refresh_token(self, refresh_token: str):
        """Revoke a refresh token (logout)"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_sessions WHERE refresh_token = $1",
                refresh_token
            )
    
    async def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP"
            )
        logger.info(f"Cleaned up expired sessions: {result}")

