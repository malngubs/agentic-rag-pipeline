"""
FastAPI dependencies for authentication, rate limiting, and other shared functionality.
"""

import time
import logging
from typing import Dict, Optional
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
    """
    Get current user from request.
    For now, returns a default user for development.
    """
    # Development mode - return default user
    user = {
        "user_id": "default_user",
        "session_id": f"session_{int(time.time())}",
        "permissions": ["chat", "upload", "metrics"],
        "rate_limit": 60  # requests per minute
    }
    
    # In production, implement proper JWT token validation here
    if credentials:
        # Validate JWT token and extract user info
        pass
    
    return user


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = {}  # {user_id: [(timestamp, count), ...]}
        self.window_size = 60  # 1 minute window
        self.max_requests = 60  # max requests per window
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits."""
        now = time.time()
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                (timestamp, count) for timestamp, count in self.requests[user_id]
                if now - timestamp < self.window_size
            ]
        else:
            self.requests[user_id] = []
        
        # Count current requests
        current_requests = sum(count for _, count in self.requests[user_id])
        
        if current_requests >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current request
        self.requests[user_id].append((now, 1))
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def get_rate_limiter() -> RateLimiter:
    """Get rate limiter dependency."""
    return rate_limiter


async def get_settings():
    """Get application settings."""
    from config.settings import get_settings
    return get_settings()