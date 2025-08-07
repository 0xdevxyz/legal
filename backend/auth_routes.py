# auth_routes.py - Add to your FastAPI backend

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from passlib.context import CryptContext
import uuid
from databases import Database
import os

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET", "9ECBjaQa7KwoyciJtLTQjc/fWRClrsMUXl5LSpIwi+I9y3wPnD1ZAZ6On+WGukAZ2bmkgInnjJjBEeU2xkluEQ==")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30*24*60  # 30 days
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://complyo_user:WrsmZTXYcjt0c7lt%2FlOzEnX1N5rtjRklLYrY8zXmBGo%3D@shared-postgres:5432/complyo_db")

# Database setup
database = Database(DATABASE_URL)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    company: Optional[str] = None

class UserCreate(UserBase):
    password: str
    subscription_tier: str = "free"  # free, basic, expert

class User(UserBase):
    id: str
    created_at: datetime
    subscription_tier: str
    is_active: bool
    api_key: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class SubscriptionTier(BaseModel):
    tier_id: str
    name: str
    price_monthly: float
    features: List[str]

# Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(user_id: str):
    query = "SELECT * FROM users WHERE id = :user_id"
    return await database.fetch_one(query=query, values={"user_id": user_id})

async def get_user_by_email(email: str):
    query = "SELECT * FROM users WHERE email = :email"
    return await database.fetch_one(query=query, values={"email": email})

async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception
    user = await get_user(user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Router
router = APIRouter()

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    # Check if user already exists
    db_user = await get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    query = """
    INSERT INTO users(id, email, password, full_name, company, subscription_tier, is_active, api_key, created_at)
    VALUES (:id, :email, :password, :full_name, :company, :subscription_tier, :is_active, :api_key, :created_at)
    RETURNING id, email, full_name, company, subscription_tier, is_active, api_key, created_at
    """
    values = {
        "id": user_id,
        "email": user.email,
        "password": hashed_password,
        "full_name": user.full_name,
        "company": user.company,
        "subscription_tier": user.subscription_tier,
        "is_active": True,
        "api_key": api_key,
        "created_at": datetime.utcnow()
    }
    
    result = await database.fetch_one(query=query, values=values)
    return result

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user = Depends(get_current_active_user)):
    return current_user

@router.get("/subscription/tiers")
async def get_subscription_tiers():
    """Return available subscription tiers"""
    return [
        {
            "tier_id": "free",
            "name": "Free Scan",
            "price_monthly": 0,
            "features": ["Single compliance scan", "Basic report", "Risk assessment"]
        },
        {
            "tier_id": "basic",
            "name": "KI-Automatisierung",
            "price_monthly": 39,
            "features": [
                "Unlimited compliance scans",
                "AI-powered fixes",
                "Cookie banner implementation",
                "Monthly re-scans",
                "Compliance dashboard"
            ]
        },
        {
            "tier_id": "expert",
            "name": "Experten-Service",
            "price_monthly": 39,
            "setup_fee": 2000,
            "features": [
                "All Basic features",
                "Personal expert support",
                "Deep-dive audit",
                "Industry-specific compliance",
                "Custom integration",
                "Expert hotline"
            ]
        }
    ]

@router.post("/subscription/upgrade")
async def upgrade_subscription(
    tier_id: str,
    current_user = Depends(get_current_active_user)
):
    """Upgrade user subscription tier - placeholder for Stripe integration"""
    # In real implementation, this would integrate with Stripe
    # and only update after successful payment
    
    query = """
    UPDATE users SET subscription_tier = :tier_id
    WHERE id = :user_id
    RETURNING id, email, full_name, company, subscription_tier, is_active, api_key, created_at
    """
    values = {"tier_id": tier_id, "user_id": current_user["id"]}
    
    result = await database.fetch_one(query=query, values=values)
    return result

# DB Init function - call this when your app starts
async def init_db():
    # Create users table if it doesn't exist
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(50) PRIMARY KEY,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        full_name VARCHAR(100),
        company VARCHAR(100),
        subscription_tier VARCHAR(20) NOT NULL,
        is_active BOOLEAN NOT NULL,
        api_key VARCHAR(50) UNIQUE NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    """
    await database.execute(query=query)