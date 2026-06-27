import hmac
import os
import secrets
import logging
from typing import Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

EXEMPT_PATHS: Set[str] = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/api/auth/refresh-cookie",
    "/api/auth/logout",
    "/api/auth/firebase-verify",
    "/api/auth/google",
    "/api/auth/google/callback",
    "/api/auth/apple",
    "/api/auth/apple/callback",
    "/api/auth/complete-onboarding",
    "/api/auth/verify-credentials",
    "/api/analyze",
    "/api/analyze-preview",
    "/api/v2/analyze",
    "/api/v2/analyze/quick",
    "/api/v2/analyze/complete",
    # Public widget telemetry endpoints — called cross-origin from customer
    # websites by the embedded banner/widget. They carry no session cookie and
    # no Bearer token, so the double-submit CSRF check can never succeed and
    # would silently drop every consent log (DSGVO Art. 7 proof of consent).
    "/api/cookie-compliance/consent",
    "/api/ab-tests/track",
    "/api/widgets/analytics",
    "/health",
    "/metrics",
}

EXEMPT_PREFIXES = (
    "/api/webhooks/",
    "/widget/",
    "/api/widget/",
    "/api/leads/",
    "/mcp",
)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
COOKIE_MAX_AGE = 60 * 60 * 8  # 8 hours

_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
_COOKIE_DOMAIN = ".complyo.de" if _ENVIRONMENT == "production" else None


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)
            if not request.cookies.get(CSRF_COOKIE_NAME):
                token = secrets.token_hex(32)
                cookie_kwargs = dict(
                    key=CSRF_COOKIE_NAME,
                    value=token,
                    max_age=COOKIE_MAX_AGE,
                    httponly=False,
                    secure=_ENVIRONMENT == "production",
                    samesite="lax",
                    path="/",
                )
                if _COOKIE_DOMAIN:
                    cookie_kwargs["domain"] = _COOKIE_DOMAIN
                response.set_cookie(**cookie_kwargs)
                if "content-length" in response.headers:
                    del response.headers["content-length"]
            return response

        path = request.url.path

        if path in EXEMPT_PATHS or path.startswith(EXEMPT_PREFIXES):
            return await call_next(request)

        # Requests with a Bearer JWT are already CSRF-safe: the token cannot be
        # stolen cross-origin, so the double-submit cookie check is not needed.
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            logger.warning(
                f"CSRF token missing for {request.method} {path} "
                f"(cookie={'present' if cookie_token else 'missing'}, "
                f"header={'present' if header_token else 'missing'})"
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid"},
            )

        if not hmac.compare_digest(cookie_token, header_token):
            logger.warning(f"CSRF token mismatch for {request.method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid"},
            )

        return await call_next(request)
