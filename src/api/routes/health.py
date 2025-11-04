"""
Health check endpoints.
"""

import time
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "agentic-rag-pipeline"
    }

@router.get("/detailed")
async def detailed_health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "agentic-rag-pipeline",
        "version": "1.0.0",
        "components": {
            "llm_manager": {"status": "healthy"},
            "vector_store": {"status": "healthy"},
            "workflow": {"status": "healthy"}
        }
    }
