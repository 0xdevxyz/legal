import os
import httpx
from typing import Optional, Dict
import asyncpg
from auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

class OAuthService:
    """
    OAuth2 Integration für Google und Apple Sign-In
    """
    
    def __init__(self, db_pool: asyncpg.Pool, auth_service: AuthService):
        self.db_pool = db_pool
        self.auth_service = auth_service
        
        # Google OAuth Config
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("FRONTEND_URL", "https://app.complyo.tech") + "/auth/google/callback"
        
        # Apple OAuth Config
        self.apple_client_id = os.getenv("APPLE_CLIENT_ID")  # Service ID
        self.apple_team_id = os.getenv("APPLE_TEAM_ID")
        self.apple_key_id = os.getenv("APPLE_KEY_ID")
        self.apple_private_key = os.getenv("APPLE_PRIVATE_KEY")  # .p8 file content
        self.apple_redirect_uri = os.getenv("FRONTEND_URL", "https://app.complyo.tech") + "/auth/apple/callback"
    
    def get_google_auth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL"""
        scopes = "openid email profile"
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.google_client_id}&"
            f"redirect_uri={self.google_redirect_uri}&"
            f"response_type=code&"
            f"scope={scopes}&"
            f"state={state}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
    
    async def exchange_google_code(self, code: str) -> Dict:
        """Exchange Google authorization code for user info"""
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "redirect_uri": self.google_redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Google token exchange failed: {token_response.text}")
                raise Exception("Failed to exchange Google code")
            
            token_data = token_response.json()
            access_token = token_data["access_token"]
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                logger.error(f"Google userinfo failed: {user_response.text}")
                raise Exception("Failed to get Google user info")
            
            return user_response.json()
    
    def get_apple_auth_url(self, state: str) -> str:
        """Generate Apple OAuth authorization URL"""
        scopes = "name email"
        return (
            f"https://appleid.apple.com/auth/authorize?"
            f"client_id={self.apple_client_id}&"
            f"redirect_uri={self.apple_redirect_uri}&"
            f"response_type=code&"
            f"scope={scopes}&"
            f"response_mode=form_post&"
            f"state={state}"
        )
    
    async def exchange_apple_code(self, code: str) -> Dict:
        """Exchange Apple authorization code for user info"""
        import jwt as pyjwt
        from datetime import datetime, timedelta
        
        # Generate client_secret (JWT signed with Apple private key)
        now = datetime.utcnow()
        client_secret = pyjwt.encode(
            {
                "iss": self.apple_team_id,
                "iat": now,
                "exp": now + timedelta(minutes=5),
                "aud": "https://appleid.apple.com",
                "sub": self.apple_client_id
            },
            self.apple_private_key,
            algorithm="ES256",
            headers={"kid": self.apple_key_id}
        )
        
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.post(
                "https://appleid.apple.com/auth/token",
                data={
                    "code": code,
                    "client_id": self.apple_client_id,
                    "client_secret": client_secret,
                    "redirect_uri": self.apple_redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Apple token exchange failed: {token_response.text}")
                raise Exception("Failed to exchange Apple code")
            
            token_data = token_response.json()
            id_token = token_data["id_token"]
            
            # Decode ID token to get user info
            # Note: In production, verify the token signature with Apple's public key
            user_info = pyjwt.decode(id_token, options={"verify_signature": False})
            
            return user_info
    
    async def get_or_create_oauth_user(self, provider: str, provider_user_id: str, email: str, full_name: str) -> Dict:
        """
        Get or create user from OAuth provider data
        """
        async with self.db_pool.acquire() as conn:
            # Check if OAuth link exists
            oauth_link = await conn.fetchrow(
                """
                SELECT user_id FROM oauth_providers
                WHERE provider = $1 AND provider_user_id = $2
                """,
                provider, provider_user_id
            )
            
            if oauth_link:
                # User exists, return user data
                user = await conn.fetchrow(
                    "SELECT id, email, full_name, company, is_active FROM users WHERE id = $1",
                    oauth_link['user_id']
                )
                return dict(user)
            
            # Check if user with this email already exists
            existing_user = await conn.fetchrow(
                "SELECT id, email, full_name, company, is_active FROM users WHERE email = $1",
                email
            )
            
            if existing_user:
                # Link existing user to OAuth provider
                user_id = existing_user['id']
            else:
                # Create new user (no password for OAuth users)
                user = await conn.fetchrow(
                    """
                    INSERT INTO users (email, password_hash, full_name, is_verified)
                    VALUES ($1, $2, $3, TRUE)
                    RETURNING id, email, full_name, company, is_active
                    """,
                    email,
                    '',  # No password for OAuth users
                    full_name
                )
                user_id = user['id']
                
                # Initialize user_limits for new user
                await conn.execute(
                    """
                    INSERT INTO user_limits (user_id, plan_type, websites_max, exports_max, exports_reset_date)
                    VALUES ($1, 'ki', 1, 10, CURRENT_DATE + INTERVAL '1 month')
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    user_id
                )
            
            # Link OAuth provider
            await conn.execute(
                """
                INSERT INTO oauth_providers (user_id, provider, provider_user_id, provider_email)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (provider, provider_user_id) DO NOTHING
                """,
                user_id, provider, provider_user_id, email
            )
            
            # Get user data
            user = await conn.fetchrow(
                "SELECT id, email, full_name, company, is_active FROM users WHERE id = $1",
                user_id
            )
            
            logger.info(f"OAuth user created/linked: {email} via {provider}")
            return dict(user)

