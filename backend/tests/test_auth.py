import pytest
import os
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

from unittest.mock import AsyncMock, MagicMock, patch

class TestAuthService:
    def test_create_access_token(self):
        from auth_service import AuthService
        mock_pool = MagicMock()
        with patch.object(AuthService, '__init__', lambda self, pool: None):
            service = AuthService.__new__(AuthService)
            service.jwt_secret = "test-secret"
            service.jwt_issuer = "https://complyo.tech"
            service.jwt_audience = "complyo-api"
            service.access_token_expire = 60
            token = service.create_access_token("user-123")
            assert token is not None
            assert isinstance(token, str)
    
    def test_verify_token_valid(self):
        from auth_service import AuthService
        import jwt
        service = AuthService.__new__(AuthService)
        service.jwt_secret = "test-secret"
        service.jwt_issuer = "https://complyo.tech"
        service.jwt_audience = "complyo-api"
        service.access_token_expire = 60
        token = service.create_access_token("user-123")
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "user-123"
    
    def test_verify_token_invalid(self):
        from auth_service import AuthService
        service = AuthService.__new__(AuthService)
        service.jwt_secret = "test-secret"
        service.jwt_issuer = "https://complyo.tech"
        service.jwt_audience = "complyo-api"
        service.access_token_expire = 60
        result = service.verify_token("invalid.token.here")
        assert result is None
