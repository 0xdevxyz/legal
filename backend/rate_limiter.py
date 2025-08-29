"""
Complyo Rate Limiting & API Protection System
Advanced rate limiting with Redis backend and security features
"""

import time
import redis
import hashlib
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Request, Depends
from functools import wraps
import logging
from datetime import datetime, timedelta
import json

from config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Advanced rate limiting with multiple algorithms and Redis backend
    """
    
    def __init__(self):
        self.redis_client = self._setup_redis()
        self.fallback_storage: Dict[str, Dict] = {}  # In-memory fallback
        
    def _setup_redis(self):
        """Setup Redis connection for rate limiting"""
        try:
            client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True
            )
            # Test connection
            client.ping()
            logger.info("✅ Redis connected for rate limiting")
            return client
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed, using in-memory fallback: {e}")
            return None
    
    def get_client_identifier(self, request: Request) -> str:
        """
        Generate unique client identifier from request
        """
        # Try to get user ID from auth token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Extract user ID from token (simplified)
                token = auth_header.split(" ")[1]
                # Use token hash as identifier (more secure than decoding)
                return f"user:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
            except:
                pass
        
        # Fallback to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    async def is_rate_limited(
        self, 
        request: Request, 
        limit: int = None, 
        window: int = None,
        per_user: bool = True
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request should be rate limited
        Returns: (is_limited, rate_info)
        """
        limit = limit or settings.rate_limit_requests
        window = window or settings.rate_limit_window
        
        # Generate rate limit key
        client_id = self.get_client_identifier(request) if per_user else "global"
        endpoint = request.url.path
        rate_key = f"rate_limit:{client_id}:{endpoint}"
        
        current_time = int(time.time())
        window_start = current_time - (current_time % window)
        
        if self.redis_client:
            return await self._redis_rate_limit_check(rate_key, limit, window, window_start)
        else:
            return self._memory_rate_limit_check(rate_key, limit, window, window_start)
    
    async def _redis_rate_limit_check(
        self, 
        rate_key: str, 
        limit: int, 
        window: int, 
        window_start: int
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Redis-based sliding window rate limiting
        """
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(rate_key, 0, time.time() - window)
            
            # Count current requests in window
            pipe.zcard(rate_key)
            
            # Add current request
            current_time = time.time()
            pipe.zadd(rate_key, {str(current_time): current_time})
            
            # Set expiry for cleanup
            pipe.expire(rate_key, window + 60)
            
            # Execute pipeline
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for the request we just added
            
            # Check if limit exceeded
            is_limited = current_count > limit
            
            if is_limited:
                # Remove the request we just added since it's rejected
                self.redis_client.zrem(rate_key, str(current_time))
            
            # Calculate reset time
            reset_time = window_start + window
            remaining = max(0, limit - current_count + (1 if is_limited else 0))
            
            rate_info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "retry_after": reset_time - int(time.time()) if is_limited else 0
            }
            
            return is_limited, rate_info
            
        except Exception as e:
            logger.error(f"Redis rate limiting failed: {e}")
            # Fallback to memory-based limiting
            return self._memory_rate_limit_check(rate_key, limit, window, window_start)
    
    def _memory_rate_limit_check(
        self, 
        rate_key: str, 
        limit: int, 
        window: int, 
        window_start: int
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Memory-based rate limiting fallback
        """
        current_time = time.time()
        
        # Initialize or get existing data
        if rate_key not in self.fallback_storage:
            self.fallback_storage[rate_key] = {"requests": [], "window_start": window_start}
        
        rate_data = self.fallback_storage[rate_key]
        
        # Clean expired requests
        rate_data["requests"] = [
            req_time for req_time in rate_data["requests"] 
            if req_time > current_time - window
        ]
        
        # Check limit
        current_count = len(rate_data["requests"])
        is_limited = current_count >= limit
        
        if not is_limited:
            rate_data["requests"].append(current_time)
            current_count += 1
        
        # Calculate rate info
        reset_time = window_start + window
        remaining = max(0, limit - current_count)
        
        rate_info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": reset_time - int(current_time) if is_limited else 0
        }
        
        return is_limited, rate_info
    
    async def record_request(self, request: Request, response_status: int):
        """
        Record request for analytics and monitoring
        """
        if not self.redis_client:
            return
        
        try:
            client_id = self.get_client_identifier(request)
            endpoint = request.url.path
            timestamp = int(time.time())
            
            # Record request analytics
            analytics_key = f"analytics:requests:{datetime.now().strftime('%Y%m%d')}"
            analytics_data = {
                "timestamp": timestamp,
                "client_id": client_id,
                "endpoint": endpoint,
                "status": response_status,
                "user_agent": request.headers.get("User-Agent", "")[:100]
            }
            
            # Store in Redis list with expiry
            self.redis_client.lpush(analytics_key, json.dumps(analytics_data))
            self.redis_client.expire(analytics_key, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Failed to record request analytics: {e}")

class SecurityHeaders:
    """
    Security headers middleware for enhanced protection
    """
    
    @staticmethod
    def add_security_headers(response):
        """
        Add comprehensive security headers
        """
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        if settings.is_production():
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com; "
                "frame-src https://js.stripe.com;"
            )
        
        # HTTPS enforcement in production
        if settings.force_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=('self'), usb=()"
        )
        
        return response

# Rate limiting decorators
def rate_limit(limit: int = None, window: int = None, per_user: bool = True):
    """
    Rate limiting decorator for FastAPI endpoints
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Try to get from kwargs
                request = kwargs.get('request')
            
            if not request:
                logger.warning("Rate limiter: Could not find Request object")
                return await func(*args, **kwargs)
            
            # Check rate limit
            limiter = RateLimiter()
            is_limited, rate_info = await limiter.is_rate_limited(
                request, limit, window, per_user
            )
            
            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset"]),
                        "Retry-After": str(rate_info["retry_after"])
                    }
                )
            
            # Execute original function
            response = await func(*args, **kwargs)
            
            # Record successful request
            await limiter.record_request(request, 200)
            
            return response
        
        return wrapper
    return decorator

def strict_rate_limit(limit: int = 10, window: int = 60):
    """
    Strict rate limiting for sensitive endpoints (login, register, etc.)
    """
    return rate_limit(limit=limit, window=window, per_user=False)

# Global instances
rate_limiter = RateLimiter()
security_headers = SecurityHeaders()