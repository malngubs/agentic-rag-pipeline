"""
============================================================================
🛡️ RATE LIMITER MIDDLEWARE - MACROCOMM BI PLATFORM
============================================================================

Rate limiting middleware to protect API endpoints from abuse.

Features:
- Per-IP rate limiting
- Per-endpoint rate limiting
- Sliding window algorithm
- Redis-based storage (with fallback to in-memory)
- Customizable limits per endpoint
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple
import redis
from loguru import logger

# Rate limit configuration (requests per minute)
RATE_LIMITS = {
    "/api/chat": 20,              # 20 requests per minute
    "/ws/chat/stream": 20,
    "/api/documents/upload": 10,   # 10 uploads per minute
    "/api/documents/list": 60,
    "/api/analytics/query": 30,
    "default": 60,                 # Default limit for other endpoints
}

class RateLimiter:
    def __init__(self, redis_url: str = None):
        """
        Initialize rate limiter with optional Redis backend.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
        """
        self.redis_client = None
        self.in_memory_store: Dict[str, list] = defaultdict(list)

        # Try to connect to Redis
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Rate limiter using Redis backend")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed, using in-memory fallback: {e}")
                self.redis_client = None
        else:
            logger.info("📝 Rate limiter using in-memory storage")

    def _get_rate_limit(self, path: str) -> int:
        """Get rate limit for a specific path."""
        # Match exact path
        if path in RATE_LIMITS:
            return RATE_LIMITS[path]

        # Match path prefix
        for pattern, limit in RATE_LIMITS.items():
            if path.startswith(pattern):
                return limit

        return RATE_LIMITS["default"]

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Uses IP address, but can be extended to use API keys, user IDs, etc.
        """
        # Get real IP from X-Forwarded-For header (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _check_rate_limit_redis(self, key: str, limit: int, window: int = 60) -> Tuple[bool, int]:
        """
        Check rate limit using Redis backend.

        Returns: (is_allowed, remaining_requests)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window

            # Remove old requests outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            request_count = self.redis_client.zcard(key)

            if request_count < limit:
                # Add current request
                self.redis_client.zadd(key, {str(current_time): current_time})
                self.redis_client.expire(key, window)  # Auto-expire after window
                return True, limit - request_count - 1
            else:
                return False, 0

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True, limit

    def _check_rate_limit_memory(self, key: str, limit: int, window: int = 60) -> Tuple[bool, int]:
        """
        Check rate limit using in-memory storage.

        Returns: (is_allowed, remaining_requests)
        """
        current_time = time.time()
        window_start = current_time - window

        # Remove old requests
        self.in_memory_store[key] = [
            req_time for req_time in self.in_memory_store[key]
            if req_time > window_start
        ]

        request_count = len(self.in_memory_store[key])

        if request_count < limit:
            self.in_memory_store[key].append(current_time)
            return True, limit - request_count - 1
        else:
            return False, 0

    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if request should be rate limited.

        Raises HTTPException if rate limit exceeded.
        """
        # Skip rate limiting for health check endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return

        # Get client identifier and rate limit
        client_id = self._get_client_identifier(request)
        path = request.url.path
        limit = self._get_rate_limit(path)

        # Create unique key for this client+endpoint
        key = f"rate_limit:{client_id}:{path}"

        # Check rate limit
        if self.redis_client:
            is_allowed, remaining = self._check_rate_limit_redis(key, limit)
        else:
            is_allowed, remaining = self._check_rate_limit_memory(key, limit)

        # Set rate limit headers
        request.state.rate_limit_limit = limit
        request.state.rate_limit_remaining = remaining

        # Raise exception if limit exceeded
        if not is_allowed:
            logger.warning(f"🚫 Rate limit exceeded for {client_id} on {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} requests per minute",
                    "retry_after": 60,  # seconds
                    "limit": limit,
                    "remaining": 0,
                },
            )

    def get_stats(self, client_id: str = None) -> Dict:
        """Get rate limiting statistics."""
        if self.redis_client:
            # Get all keys for this client
            pattern = f"rate_limit:{client_id}:*" if client_id else "rate_limit:*"
            keys = self.redis_client.keys(pattern)
            return {
                "backend": "redis",
                "total_keys": len(keys),
                "client_id": client_id,
            }
        else:
            return {
                "backend": "in-memory",
                "total_keys": len(self.in_memory_store),
                "client_id": client_id,
            }


# Global rate limiter instance
rate_limiter = None


def get_rate_limiter(redis_url: str = None) -> RateLimiter:
    """Get or create global rate limiter instance."""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RateLimiter(redis_url)
    return rate_limiter


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting.

    Usage in main.py:
        from middleware.rate_limiter import rate_limit_middleware
        app.middleware("http")(rate_limit_middleware)
    """
    limiter = get_rate_limiter()

    try:
        # Check rate limit
        await limiter.check_rate_limit(request)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if hasattr(request.state, "rate_limit_limit"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response

    except HTTPException as exc:
        # Return rate limit error as JSON
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers={
                "X-RateLimit-Limit": str(RATE_LIMITS.get(request.url.path, RATE_LIMITS["default"])),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 60),
                "Retry-After": "60",
            },
        )
