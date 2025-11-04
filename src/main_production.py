#!/usr/bin/env python3
"""
Production FastAPI server with Real RAG capabilities
Integrates document processing, vector search, and LLM generation
"""

import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict

# Import our RAG system
from rag_components import RAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models
class ChatMessage(BaseModel):
    """Chat message model with fixed field naming"""
    model_config = ConfigDict(protected_namespaces=())
    
    message: str
    conversation_id: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    timeout_seconds: int = Field(default=30, ge=1, le=300)

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    conversation_id: str
    response_time: float
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sources: List[str] = []
    using_rag: Optional[bool] = False
    context_found: Optional[int] = 0

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    service: str
    version: str
    components: Dict[str, Dict[str, str]]

class UploadResponse(BaseModel):
    """Document upload response"""
    message: str
    filename: str
    size: int
    processed: bool
    chunks_created: Optional[int] = None

# WebSocket Connection Manager (same as before)
class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict = None):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = client_info or {}
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_info.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

# Application state with RAG system
class ApplicationState:
    """Centralized application state with RAG capabilities"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.conversations: Dict[str, List[Dict]] = {}
        self.rag_system = RAGSystem()
        self.rag_status = {
            'vector_store': False,
            'llm_manager': False,
            'initialized': False
        }
        self.startup_complete = False
    
    async def initialize_components(self):
        """Initialize all system components including RAG"""
        logger.info("🚀 Initializing system components...")
        
        # Initialize RAG system
        try:
            self.rag_status = await self.rag_system.initialize()
            logger.info(f"RAG system status: {self.rag_status}")
        except Exception as e:
            logger.error(f"RAG initialization error: {e}")
            self.rag_status = {'vector_store': False, 'llm_manager': False, 'initialized': False}
        
        self.startup_complete = True
        logger.info("🎯 System initialization complete!")
    
    def get_system_status(self) -> Dict:
        """Get current system status including RAG"""
        return {
            "startup_complete": self.startup_complete,
            "rag_initialized": self.rag_status.get('initialized', False),
            "vector_store_available": self.rag_status.get('vector_store', False),
            "llm_available": self.rag_status.get('llm_manager', False),
            "active_connections": len(self.connection_manager.active_connections),
            "total_conversations": len(self.conversations)
        }

# Global application state
app_state = ApplicationState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("🚀 Starting Agentic RAG Pipeline with Real RAG...")
    await app_state.initialize_components()
    
    # Store state in app for access
    app.state.app_state = app_state
    app.state.connection_manager = app_state.connection_manager
    
    logger.info("✅ Application startup complete!")
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down...")
    await app_state.rag_system.close()
    logger.info("✅ Shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="Macrocomm AI Assistant with RAG",
    description="Advanced Agentic RAG Pipeline with Real Document Processing",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/", response_class=JSONResponse)
async def root():
    """API root endpoint"""
    return {
        "service": "Macrocomm AI Assistant with RAG",
        "version": "2.0.0",
        "status": "online",
        "capabilities": ["real_time_chat", "document_processing", "vector_search", "llm_generation"],
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "upload": "/api/upload",
            "rag_status": "/api/rag/status",
            "docs": "/docs",
            "widget_demo": "/frontend/widget/demo.html",
            "admin": "/frontend/widget/admin.html"
        },
        "websocket": "/ws/chat"
    }

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors"""
    return Response(status_code=204)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check including RAG components"""
    status = app_state.get_system_status()
    
    return HealthResponse(
        status="healthy" if status["startup_complete"] else "starting",
        timestamp=time.time(),
        service="agentic-rag-pipeline-with-rag",
        version="2.0.0",
        components={
            "rag_system": {
                "status": "healthy" if status["rag_initialized"] else "degraded",
                "initialized": str(status["rag_initialized"])
            },
            "vector_store": {
                "status": "healthy" if status["vector_store_available"] else "degraded"
            },
            "llm_service": {
                "status": "healthy" if status["llm_available"] else "degraded"
            },
            "websocket": {
                "status": "healthy",
                "connections": str(status["active_connections"])
            },
            "conversations": {
                "status": "healthy",
                "total": str(status["total_conversations"])
            }
        }
    )

@app.get("/api/rag/status")
async def rag_status():
    """Get detailed RAG system status"""
    try:
        status = await app_state.rag_system.get_system_status()
        return {
            "rag_system": status,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"RAG status check failed: {e}")
        return {
            "error": "RAG status check failed",
            "timestamp": time.time()
        }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Enhanced chat endpoint with RAG capabilities"""
    start_time = time.time()
    
    try:
        # Generate conversation ID if not provided
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        # Check if RAG system is available
        if app_state.rag_status.get('initialized', False):
            # Use RAG system for response
            rag_result = await app_state.rag_system.query(message.message)
            
            response_text = rag_result['response']
            sources = rag_result['sources']
            using_rag = rag_result['using_rag']
            context_found = rag_result.get('context_found', 0)
            
        else:
            # Fallback to demo responses
            response_text = await generate_demo_response(message.message)
            sources = ["demo_responses"]
            using_rag = False
            context_found = 0
        
        # Store conversation
        if conversation_id not in app_state.conversations:
            app_state.conversations[conversation_id] = []
        
        app_state.conversations[conversation_id].append({
            "user": message.message,
            "assistant": response_text,
            "timestamp": time.time(),
            "using_rag": using_rag,
            "sources": sources,
            "context_found": context_found
        })
        
        response_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            response_time=response_time,
            intent="informational",
            confidence=0.95 if using_rag else 0.8,
            sources=sources,
            using_rag=using_rag,
            context_found=context_found
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed")

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Enhanced document upload with real processing"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_path = Path(file.filename)
        supported_types = {'.pdf', '.docx', '.txt', '.xlsx'}
        
        if file_path.suffix.lower() not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {supported_types}"
            )
        
        # Read file content
        content = await file.read()
        
        # Process document if RAG system is available
        processed = False
        chunks_created = None
        
        if app_state.rag_status.get('initialized', False):
            try:
                processed = await app_state.rag_system.process_document(file_path, content)
                if processed:
                    # Get document info (simplified - you could enhance this)
                    chunks_created = len(content) // 1000  # Rough estimate
                    logger.info(f"Document processed: {file.filename}")
                else:
                    logger.error(f"Document processing failed: {file.filename}")
            except Exception as e:
                logger.error(f"Document processing error: {e}")
                processed = False
        
        return UploadResponse(
            message=f"Document '{file.filename}' uploaded successfully" + 
                   (" and processed for RAG" if processed else " (processing unavailable)"),
            filename=file.filename,
            size=len(content),
            processed=processed,
            chunks_created=chunks_created
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Document upload failed")

async def generate_demo_response(user_message: str) -> str:
    """Fallback demo responses when RAG is not available"""
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "hey"]):
        return "👋 Hello! I'm the Macrocomm AI Assistant with RAG capabilities. Upload documents to enable intelligent document-based responses."
    
    elif any(word in message_lower for word in ["document", "upload", "file"]):
        return "📄 You can upload PDF, DOCX, TXT, or Excel files. Once uploaded, I'll be able to answer questions based on your documents. The RAG system needs Ollama and Qdrant to be running."
    
    elif any(word in message_lower for word in ["rag", "system", "status"]):
        return "🔧 RAG system status: Check /api/rag/status for detailed information. Make sure Ollama (http://localhost:11434) and Qdrant (localhost:6333) are running."
    
    else:
        return f"🤖 I received your message: '{user_message}'. For document-based responses, please upload documents and ensure the RAG system is running (Ollama + Qdrant)."

# WebSocket endpoint with RAG integration
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with RAG capabilities"""
    client_info = {
        "client_host": websocket.client.host if websocket.client else "unknown",
        "connected_at": time.time()
    }
    
    try:
        await app_state.connection_manager.connect(websocket, client_info)
        
        # Send welcome message with RAG status
        rag_available = app_state.rag_status.get('initialized', False)
        welcome_msg = "WebSocket connected! Real-time chat is active." + (
            " RAG system ready for document-based queries." if rag_available 
            else " RAG system not available - using demo responses."
        )
        
        await websocket.send_json({
            "type": "system",
            "message": welcome_msg,
            "rag_available": rag_available,
            "timestamp": time.time()
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "chat":
                message = data.get("message", "")
                conversation_id = data.get("conversation_id") or str(uuid.uuid4())
                
                try:
                    start_time = time.time()
                    
                    # Use RAG system if available
                    if app_state.rag_status.get('initialized', False):
                        rag_result = await app_state.rag_system.query(message)
                        response_text = rag_result['response']
                        sources = rag_result['sources']
                        using_rag = rag_result['using_rag']
                        context_found = rag_result.get('context_found', 0)
                    else:
                        response_text = await generate_demo_response(message)
                        sources = ["demo_responses"]
                        using_rag = False
                        context_found = 0
                    
                    response_time = time.time() - start_time
                    
                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "message": response_text,
                        "conversation_id": conversation_id,
                        "response_time": response_time,
                        "timestamp": time.time(),
                        "using_rag": using_rag,
                        "sources": sources,
                        "context_found": context_found,
                        "intent": "conversational",
                        "confidence": 0.95 if using_rag else 0.8
                    })
                    
                except Exception as e:
                    logger.error(f"WebSocket message processing failed: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "I encountered an error processing your request. Please try again.",
                        "timestamp": time.time()
                    })
    
    except WebSocketDisconnect:
        app_state.connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        app_state.connection_manager.disconnect(websocket)

# Static file serving (same as before)
def setup_static_files():
    """Setup static file serving"""
    try:
        possible_paths = [
            Path("../frontend"),
            Path("frontend"), 
            Path("./frontend"),
            Path(__file__).parent.parent / "frontend"
        ]
        
        frontend_path = None
        for path in possible_paths:
            if path.exists():
                frontend_path = path
                break
        
        if frontend_path:
            app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")
            logger.info(f"✅ Frontend static files mounted from: {frontend_path.absolute()}")
            return True
        else:
            logger.warning("⚠️ Frontend directory not found")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Static file mounting failed: {e}")
        return False

# Setup static files
setup_static_files()

# Development server
if __name__ == "__main__":
    logger.info("🚀 Starting RAG-enabled development server...")
    uvicorn.run(
        "main_production_with_rag:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        access_log=True,
        log_level="info",
        reload_dirs=["../"]
    )