"""
Complyo User Authentication System
JWT-based authentication with registration, login, and user management
"""
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "complyo_secret_key_change_in_production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = 24
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30

# Security
security = HTTPBearer()

# User Models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    subscription_status: str
    created_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserProfile

class AuthService:
    def __init__(self):
        # Mock user database (in production: PostgreSQL)
        self.users_db: Dict[str, Dict] = {}
        self.sessions_db: Dict[str, Dict] = {}
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def register_user(self, user_data: UserRegistration) -> Token:
        """Register new user"""
        
        # Check if user already exists
        if user_data.email in [u["email"] for u in self.users_db.values()]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(user_data.password)
        
        user_record = {
            "id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "company_name": user_data.company_name,
            "phone": user_data.phone,
            "website": user_data.website,
            "subscription_status": "trial",  # 7-day free trial
            "created_at": datetime.utcnow(),
            "last_login": None,
            "email_verified": False,
            "trial_expires": datetime.utcnow() + timedelta(days=7)\n        }
        
        self.users_db[user_id] = user_record
        
        # Create tokens
        access_token = self.create_access_token(user_id, user_data.email)
        refresh_token = self.create_refresh_token(user_id)
        
        # Create user profile
        user_profile = UserProfile(
            id=user_id,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company_name=user_data.company_name,
            phone=user_data.phone,
            website=user_data.website,
            subscription_status="trial",
            created_at=user_record["created_at"],
            email_verified=False
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user=user_profile
        )
    
    def login_user(self, login_data: UserLogin) -> Token:
        """Login user and return tokens"""
        
        # Find user by email
        user_record = None
        for user in self.users_db.values():
            if user["email"] == login_data.email:
                user_record = user
                break
        
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not self.verify_password(login_data.password, user_record["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        user_record["last_login"] = datetime.utcnow()
        
        # Create tokens
        access_token = self.create_access_token(user_record["id"], user_record["email"])
        refresh_token = self.create_refresh_token(user_record["id"])
        
        # Create user profile
        user_profile = UserProfile(
            id=user_record["id"],
            email=user_record["email"],
            first_name=user_record["first_name"],
            last_name=user_record["last_name"],
            company_name=user_record["company_name"],
            phone=user_record["phone"],
            website=user_record["website"],
            subscription_status=user_record["subscription_status"],
            created_at=user_record["created_at"],
            last_login=user_record["last_login"],
            email_verified=user_record["email_verified"]
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user=user_profile
        )
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
        """Get current user from JWT token"""
        
        token = credentials.credentials
        payload = self.verify_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("user_id")
        if not user_id or user_id not in self.users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user_record = self.users_db[user_id]
        
        return UserProfile(
            id=user_record["id"],
            email=user_record["email"],
            first_name=user_record["first_name"],
            last_name=user_record["last_name"],
            company_name=user_record["company_name"],
            phone=user_record["phone"],
            website=user_record["website"],
            subscription_status=user_record["subscription_status"],
            created_at=user_record["created_at"],
            last_login=user_record["last_login"],
            email_verified=user_record["email_verified"]
        )
    
    def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("user_id")
        if not user_id or user_id not in self.users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user_record = self.users_db[user_id]
        
        # Create new tokens
        new_access_token = self.create_access_token(user_record["id"], user_record["email"])
        new_refresh_token = self.create_refresh_token(user_record["id"])
        
        # Create user profile
        user_profile = UserProfile(
            id=user_record["id"],
            email=user_record["email"],
            first_name=user_record["first_name"],
            last_name=user_record["last_name"],
            company_name=user_record["company_name"],
            phone=user_record["phone"],
            website=user_record["website"],
            subscription_status=user_record["subscription_status"],
            created_at=user_record["created_at"],
            last_login=user_record["last_login"],
            email_verified=user_record["email_verified"]
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user=user_profile
        )
    
    def update_user_profile(self, user_id: str, updates: Dict) -> UserProfile:
        """Update user profile"""
        
        if user_id not in self.users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_record = self.users_db[user_id]
        
        # Update allowed fields
        allowed_fields = ["first_name", "last_name", "company_name", "phone", "website"]
        for field, value in updates.items():
            if field in allowed_fields:
                user_record[field] = value
        
        return UserProfile(
            id=user_record["id"],
            email=user_record["email"],
            first_name=user_record["first_name"],
            last_name=user_record["last_name"],
            company_name=user_record["company_name"],
            phone=user_record["phone"],
            website=user_record["website"],
            subscription_status=user_record["subscription_status"],
            created_at=user_record["created_at"],
            last_login=user_record["last_login"],
            email_verified=user_record["email_verified"]
        )
    
    def get_user_statistics(self) -> Dict:
        """Get user statistics"""
        
        total_users = len(self.users_db)
        trial_users = len([u for u in self.users_db.values() if u["subscription_status"] == "trial"])
        active_users = len([u for u in self.users_db.values() if u["subscription_status"] == "active"])
        verified_users = len([u for u in self.users_db.values() if u["email_verified"]])
        
        return {
            "total_users": total_users,
            "trial_users": trial_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "conversion_rate": (active_users / total_users * 100) if total_users > 0 else 0,
            "verification_rate": (verified_users / total_users * 100) if total_users > 0 else 0
        }

# Global auth service instance
auth_service = AuthService()

# Dependency functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """Dependency to get current authenticated user"""
    return auth_service.get_current_user(credentials)

def get_current_active_user(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Dependency to get current active user with subscription check"""
    # In production: check subscription status and trial expiry
    return current_user