"""
Chat API routes for the RAG system.
"""

import asyncio
import logging
import time
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    conversation_id: str
    response_time: float

# Simple in-memory storage
conversations = {}

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint."""
    start_time = time.time()
    
    try:
        # Generate conversation ID if not provided
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        # Simple response for now
        response_text = f"I received your message: {message.message}"
        
        # Store conversation
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        conversations[conversation_id].append({
            "user": message.message,
            "assistant": response_text,
            "timestamp": time.time()
        })
        
        response_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            response_time=response_time
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed")

@router.get("/health")
async def chat_health():
    """Chat system health check."""
    return {
        "status": "healthy",
        "total_conversations": len(conversations)
    }
