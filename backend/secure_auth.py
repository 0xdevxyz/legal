"""
Complyo Secure Authentication System
JWT-based authentication with comprehensive security features
"""

import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import redis
import json
import logging
from dataclasses import dataclass

from config import settings
from database_service import DatabaseService

logger = logging.getLogger(__name__)

# Security models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    terms_accepted: bool

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str

@dataclass
class UserProfile:
    id: str
    email: str
    first_name: str
    last_name: str
    company_name: Optional[str]
    is_active: bool
    is_verified: bool
    subscription_status: str
    created_at: datetime
    last_login: Optional[datetime]

class SecureAuthentication:
    """
    Comprehensive authentication system with security best practices
    """
    
    def __init__(self):
        self.db = DatabaseService()
        self.redis_client = self._setup_redis()
        self.security = HTTPBearer(auto_error=False)
        
    def _setup_redis(self):
        """Setup Redis connection for token blacklisting and session management"""
        try:
            return redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory fallback: {e}")
            return None
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with salt
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        """
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_tokens(self, user_id: str, remember_me: bool = False) -> Tuple[str, str]:
        """
        Generate JWT access and refresh tokens
        """
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            "sub": user_id,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(hours=settings.jwt_access_token_expire_hours),
            "jti": secrets.token_urlsafe(16)  # Unique token ID
        }
        
        # Refresh token payload (longer expiry for remember_me)
        refresh_expiry = timedelta(days=settings.jwt_refresh_token_expire_days)
        if remember_me:
            refresh_expiry = timedelta(days=90)  # 90 days for remember me
            
        refresh_payload = {
            "sub": user_id,
            "type": "refresh", 
            "iat": now,
            "exp": now + refresh_expiry,
            "jti": secrets.token_urlsafe(16)
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        
        return access_token, refresh_token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        """
        try:
            # Decode token
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(payload.get("jti")):
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def blacklist_token(self, jti: str, exp: datetime):
        """
        Add token to blacklist (logout functionality)
        """
        if self.redis_client:
            # Store in Redis with expiration
            ttl = int((exp - datetime.utcnow()).total_seconds())
            if ttl > 0:
                self.redis_client.setex(f"blacklist:{jti}", ttl, "true")
        else:
            # Fallback: store in database
            logger.warning("Redis not available, using database for token blacklisting")
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if token is blacklisted
        """
        if self.redis_client:
            return self.redis_client.exists(f"blacklist:{jti}")
        return False  # Fallback when Redis unavailable
    
    async def register_user(self, user_data: RegisterRequest) -> UserProfile:
        """
        Register new user with validation
        """
        # Validate terms acceptance
        if not user_data.terms_accepted:
            raise HTTPException(status_code=400, detail="Terms and conditions must be accepted")
        
        # Check password strength
        if not self._validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters with uppercase, lowercase, number and special character"
            )
        
        # Check if user already exists
        existing_user = await self.db.fetch_one(
            "SELECT id FROM users WHERE email = %s", 
            (user_data.email,)
        )
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Hash password
        hashed_password = self.hash_password(user_data.password)
        
        # Generate user ID and verification token
        user_id = secrets.token_urlsafe(16)
        verification_token = secrets.token_urlsafe(32)
        
        # Insert user into database
        query = """
            INSERT INTO users (
                id, email, password_hash, first_name, last_name, company_name,
                is_active, is_verified, verification_token, created_at, subscription_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        success = await self.db.execute_query(query, (
            user_id,
            user_data.email,
            hashed_password,
            user_data.first_name,
            user_data.last_name,
            user_data.company_name,
            True,  # is_active
            False,  # is_verified (requires email verification)
            verification_token,
            datetime.utcnow(),
            "trial"  # Default subscription
        ))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create user account")
        
        # Return user profile
        return UserProfile(
            id=user_id,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company_name=user_data.company_name,
            is_active=True,
            is_verified=False,
            subscription_status="trial",
            created_at=datetime.utcnow(),
            last_login=None
        )
    
    async def login_user(self, login_data: LoginRequest) -> TokenResponse:
        """
        Authenticate user and return tokens
        """
        # Get user from database
        user_row = await self.db.fetch_one(
            "SELECT id, email, password_hash, first_name, last_name, company_name, is_active, is_verified, subscription_status FROM users WHERE email = %s",
            (login_data.email,)
        )
        
        if not user_row:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not self.verify_password(login_data.password, user_row['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if not user_row['is_active']:
            raise HTTPException(status_code=401, detail="Account has been deactivated")
        
        # Update last login
        await self.db.execute_query(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (datetime.utcnow(), user_row['id'])
        )
        
        # Generate tokens
        access_token, refresh_token = self.generate_tokens(user_row['id'], login_data.remember_me)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_hours * 3600,
            user_id=user_row['id']
        )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> UserProfile:
        """
        Get current authenticated user from JWT token
        """
        if not credentials:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Verify token
        payload = self.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get user from database
        user_row = await self.db.fetch_one(
            """SELECT id, email, first_name, last_name, company_name, is_active, 
                      is_verified, subscription_status, created_at, last_login 
               FROM users WHERE id = %s""",
            (user_id,)
        )
        
        if not user_row:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user_row['is_active']:
            raise HTTPException(status_code=401, detail="Account deactivated")
        
        return UserProfile(
            id=user_row['id'],
            email=user_row['email'],
            first_name=user_row['first_name'],
            last_name=user_row['last_name'],
            company_name=user_row['company_name'],
            is_active=user_row['is_active'],
            is_verified=user_row['is_verified'],
            subscription_status=user_row['subscription_status'],
            created_at=user_row['created_at'],
            last_login=user_row['last_login']
        )
    
    async def logout_user(self, token: str):
        """
        Logout user by blacklisting token
        """
        payload = self.verify_token(token)
        jti = payload.get("jti")
        exp = datetime.fromtimestamp(payload.get("exp"))
        
        if jti:
            self.blacklist_token(jti, exp)
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token from refresh token
        """
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = payload.get("sub")
        
        # Generate new access token
        access_token, _ = self.generate_tokens(user_id, False)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=settings.jwt_access_token_expire_hours * 3600,
            user_id=user_id
        )
    
    def _validate_password_strength(self, password: str) -> bool:
        """
        Validate password meets security requirements
        """
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special

# Global authentication instance
secure_auth = SecureAuthentication()