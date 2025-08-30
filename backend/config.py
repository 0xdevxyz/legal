"""
Complyo Secure Configuration Management
Environment-based configuration with validation and security
"""

import os
import secrets
from typing import Optional, List
from pydantic import BaseSettings, validator
from functools import lru_cache

class Settings(BaseSettings):
    """
    Secure application settings with validation
    """
    
    # Database Configuration
    database_url: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "complyo_db"
    db_user: str = "complyo_user"
    db_password: str
    db_min_connections: int = 5
    db_max_connections: int = 20
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # JWT & Authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 24
    jwt_refresh_token_expire_days: int = 30
    session_secret: str
    
    # API Keys & External Services
    openrouter_api_key: Optional[str] = None
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    
    # Security Configuration
    allowed_origins: List[str] = ["https://localhost:3000"]
    cors_allow_credentials: bool = True
    security_password_salt: str
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    
    # Environment & Deployment
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_version: str = "2.0.0"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    # Frontend Configuration
    next_public_api_url: str = "http://localhost:8000"
    next_public_app_url: str = "http://localhost:3000"
    next_public_stripe_publishable_key: Optional[str] = None
    
    # Monitoring & Logging
    sentry_dsn: Optional[str] = None
    log_file_path: str = "/var/log/complyo/app.log"
    monitoring_enabled: bool = True
    
    # SSL & Security Headers
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    force_https: bool = False
    secure_cookies: bool = False
    
    # File Upload & Storage
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "/tmp/complyo/uploads"
    allowed_file_types: List[str] = ["pdf", "doc", "docx", "txt"]
    
    # Email Configuration
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@complyo.tech"
    from_name: str = "Complyo Platform"
    
    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret must be at least 32 characters long')
        return v
    
    @validator('security_password_salt')
    def validate_password_salt(cls, v):
        if len(v) < 16:
            raise ValueError('Password salt must be at least 16 characters long')
        return v
    
    @validator('allowed_origins')
    def validate_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allowed_file_types')
    def validate_file_types(cls, v):
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(',')]
        return [ext.lower() for ext in v]
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ['development', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v
    
    def is_production(self) -> bool:
        return self.environment == "production"
    
    def is_development(self) -> bool:
        return self.environment == "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        # Map environment variable names
        fields = {
            'database_url': 'DATABASE_URL',
            'db_host': 'DB_HOST',
            'db_port': 'DB_PORT',
            'db_name': 'DB_NAME',
            'db_user': 'DB_USER',
            'db_password': 'DB_PASSWORD',
            'db_min_connections': 'DB_MIN_CONNECTIONS',
            'db_max_connections': 'DB_MAX_CONNECTIONS',
            'redis_url': 'REDIS_URL',
            'redis_host': 'REDIS_HOST',
            'redis_port': 'REDIS_PORT',
            'redis_password': 'REDIS_PASSWORD',
            'redis_db': 'REDIS_DB',
            'jwt_secret': 'JWT_SECRET',
            'jwt_algorithm': 'JWT_ALGORITHM',
            'jwt_access_token_expire_hours': 'JWT_ACCESS_TOKEN_EXPIRE_HOURS',
            'jwt_refresh_token_expire_days': 'JWT_REFRESH_TOKEN_EXPIRE_DAYS',
            'session_secret': 'SESSION_SECRET',
            'openrouter_api_key': 'OPENROUTER_API_KEY',
            'stripe_api_key': 'STRIPE_API_KEY',
            'stripe_webhook_secret': 'STRIPE_WEBHOOK_SECRET',
            'sendgrid_api_key': 'SENDGRID_API_KEY',
            'allowed_origins': 'ALLOWED_ORIGINS',
            'cors_allow_credentials': 'CORS_ALLOW_CREDENTIALS',
            'security_password_salt': 'SECURITY_PASSWORD_SALT',
            'rate_limit_requests': 'RATE_LIMIT_REQUESTS',
            'rate_limit_window': 'RATE_LIMIT_WINDOW',
            'environment': 'ENVIRONMENT',
            'debug': 'DEBUG',
            'log_level': 'LOG_LEVEL',
            'api_version': 'API_VERSION',
            'server_host': 'SERVER_HOST',
            'server_port': 'SERVER_PORT',
            'next_public_api_url': 'NEXT_PUBLIC_API_URL',
            'next_public_app_url': 'NEXT_PUBLIC_APP_URL',
            'next_public_stripe_publishable_key': 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY',
            'sentry_dsn': 'SENTRY_DSN',
            'log_file_path': 'LOG_FILE_PATH',
            'monitoring_enabled': 'MONITORING_ENABLED',
            'ssl_cert_path': 'SSL_CERT_PATH',
            'ssl_key_path': 'SSL_KEY_PATH',
            'force_https': 'FORCE_HTTPS',
            'secure_cookies': 'SECURE_COOKIES',
            'max_file_size': 'MAX_FILE_SIZE',
            'upload_dir': 'UPLOAD_DIR',
            'allowed_file_types': 'ALLOWED_FILE_TYPES',
            'smtp_host': 'SMTP_HOST',
            'smtp_port': 'SMTP_PORT',
            'smtp_user': 'SMTP_USER',
            'smtp_password': 'SMTP_PASSWORD',
            'from_email': 'FROM_EMAIL',
            'from_name': 'FROM_NAME'
        }

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings
    """
    return Settings()

def generate_secure_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random key
    """
    return secrets.token_urlsafe(length)

def validate_required_env_vars():
    """
    Validate that all required environment variables are set
    """
    required_vars = [
        'DATABASE_URL',
        'JWT_SECRET', 
        'SESSION_SECRET',
        'SECURITY_PASSWORD_SALT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please copy .env.example to .env and set all required values."
        )

# Validate environment on import in production
if os.getenv('ENVIRONMENT') == 'production':
    validate_required_env_vars()

# Export settings instance
settings = get_settings()