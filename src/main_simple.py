"""
Simplified FastAPI Main Application.
This version starts with basic functionality and can be extended.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our routes
from api.routes import chat_router, health_router
from api.websockets import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agentic RAG Pipeline",
    description="Production-ready RAG system with agentic reasoning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
connection_manager = ConnectionManager()

# Include routers
app.include_router(chat_router, prefix="/v1/chat", tags=["chat"])
app.include_router(health_router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Agentic RAG Pipeline",
        "version": "1.0.0",
        "status": "running"
    }

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Echo back for now (later integrate with RAG)
            response = f"Echo: {data}"
            
            # Send response back
            await connection_manager.send_personal_message(response, websocket)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)

if __name__ == "__main__":
    logger.info("🚀 Starting Agentic RAG Pipeline...")
    
    uvicorn.run(
        "main_simple:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        access_log=True,
        log_level="info"
    )