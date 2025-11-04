"""
Authentication routes - simplified for development.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/token", response_model=TokenResponse)
async def login():
    """Simplified login for development."""
    return {
        "access_token": "dev_token_12345",
        "token_type": "bearer"
    }


@router.get("/me")
async def get_current_user_info():
    """Get current user information."""
    return {
        "user_id": "default_user",
        "username": "developer",
        "permissions": ["chat", "upload", "metrics"]
    }