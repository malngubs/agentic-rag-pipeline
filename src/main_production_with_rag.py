#!/usr/bin/env python3
"""
Production FastAPI server with Real RAG capabilities
Integrates document processing, vector search, and LLM generation
Version 2.1 - With Document Management Endpoints
"""

import asyncio
import logging
import os
import time
import uuid
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from rag_components import RAGConfig 

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict

# Additional imports for enhanced functionality
import httpx

# Import our RAG system
from rag_components import RAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# 📋 PYDANTIC MODELS
# =============================================================================

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

class DocumentResponse(BaseModel):
    """Document metadata response"""
    doc_id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: str
    chunk_count: int
    status: str
    error_message: Optional[str] = None

class DocumentListResponse(BaseModel):
    """List of documents response"""
    documents: List[DocumentResponse]
    total: int

class DeleteResponse(BaseModel):
    """Document deletion response"""
    success: bool
    doc_id: Optional[str] = None
    filename: Optional[str] = None
    chunks_deleted: Optional[int] = None
    error: Optional[str] = None

# =============================================================================
# 🔌 WEBSOCKET CONNECTION MANAGER
# =============================================================================

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

# =============================================================================
# 🏗️ APPLICATION STATE
# =============================================================================

class ApplicationState:
    """Centralized application state with RAG capabilities"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.conversations: Dict[str, List[Dict]] = {}
        config = RAGConfig()
        self.rag_system = RAGSystem(config)
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
            rag_init_result = await self.rag_system.initialize()
            logger.info(f"RAG system initialization result: {rag_init_result}")
            
            # Update status based on initialization result
            if rag_init_result.get('initialized', False):
                self.rag_status = {
                    'vector_store': True,
                    'llm_manager': True,
                    'initialized': True
                }
                logger.info("✅ RAG system fully initialized!")
            else:
                logger.warning("⚠️ RAG system initialization incomplete")
                self.rag_status = {
                    'vector_store': False,
                    'llm_manager': False,
                    'initialized': False
                }
                
        except Exception as e:
            logger.error(f"❌ RAG initialization error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.rag_status = {
                'vector_store': False,
                'llm_manager': False,
                'initialized': False
            }
        
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

# =============================================================================
# 🚀 FASTAPI APPLICATION
# =============================================================================

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
    version="2.1.0",
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

# =============================================================================
# 📍 API ROUTES
# =============================================================================

@app.get("/", response_class=JSONResponse)
async def root():
    """API root endpoint"""
    return {
        "service": "Macrocomm AI Assistant with RAG",
        "version": "2.1.0",
        "status": "online",
        "llm_provider": "OpenAI",
        "capabilities": ["real_time_chat", "document_processing", "vector_search", "llm_generation", "document_management"],
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "upload": "/api/upload",
            "documents_list": "/api/documents/list",
            "document_details": "/api/documents/{doc_id}",
            "document_delete": "/api/documents/{doc_id}",
            "rag_status": "/api/rag/status",
            "rag_debug": "/api/rag/debug",
            "test_processing": "/api/test-processing",
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
        version="2.1.0",
        components={
            "rag_system": {
                "status": "healthy" if status["rag_initialized"] else "degraded",
                "initialized": str(status["rag_initialized"])
            },
            "vector_store": {
                "status": "healthy" if status["vector_store_available"] else "degraded"
            },
            "llm_service": {
                "status": "healthy" if status["llm_available"] else "degraded",
                "provider": "OpenAI"
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
            "app_state_status": app_state.rag_status,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"RAG status check failed: {e}")
        return {
            "error": "RAG status check failed",
            "details": str(e),
            "app_state_status": app_state.rag_status,
            "timestamp": time.time()
        }

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Enhanced document upload with comprehensive processing and debugging
    This function implements the complete document upload, processing, and indexing pipeline
    """
    start_time = time.time()
    logger.info(f"📤 Upload request received: {file.filename}")
    
    try:
        # Step 1: Validate input and file
        logger.info("🔍 Step 1: Validating upload request...")
        
        if not file.filename:
            logger.error("❌ No filename provided in upload")
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_path = Path(file.filename)
        supported_types = {'.pdf', '.docx', '.txt', '.xlsx', '.xls'}
        file_extension = file_path.suffix.lower()
        
        logger.info(f"📄 File details: {file.filename} (type: {file_extension})")
        
        if file_extension not in supported_types:
            logger.error(f"❌ Unsupported file type: {file_extension}")
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type '{file_extension}'. Supported: {supported_types}"
            )
        
        # Step 2: Read file content with size validation
        logger.info("📖 Step 2: Reading file content...")
        
        try:
            content = await file.read()
            file_size = len(content)
            
            logger.info(f"📊 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            
            # Validate file size (100MB limit)
            if file_size > 100 * 1024 * 1024:
                logger.error(f"❌ File too large: {file_size:,} bytes")
                raise HTTPException(status_code=413, detail="File size exceeds 100MB limit")
            
            if file_size == 0:
                logger.error("❌ Empty file uploaded")
                raise HTTPException(status_code=400, detail="Empty file uploaded")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to read file content: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
        
        # Step 3: Check RAG system status with detailed logging
        logger.info("🔧 Step 3: Checking RAG system availability...")
        
        rag_initialized = app_state.rag_status.get('initialized', False)
        vector_store_available = app_state.rag_status.get('vector_store', False)
        llm_available = app_state.rag_status.get('llm_manager', False)
        
        logger.info(f"🏥 RAG System Status:")
        logger.info(f"   • Initialized: {rag_initialized}")
        logger.info(f"   • Vector Store: {vector_store_available}")
        logger.info(f"   • LLM Available: {llm_available}")
        
        if not rag_initialized:
            logger.warning("⚠️ RAG system not initialized - checking detailed status...")
            
            # Get detailed RAG status for debugging
            try:
                detailed_status = await app_state.rag_system.get_system_status()
                logger.info(f"📋 Detailed RAG Status: {detailed_status}")
                
                # Try to determine why it's not initialized
                if not detailed_status.get('vector_store_connected', False):
                    logger.error("❌ Vector store (Qdrant) not connected - is Qdrant running on localhost:6333?")
                if not detailed_status.get('llm_available', False):
                    logger.error("❌ LLM (OpenAI) not available - check OPENAI_API_KEY environment variable")
                if not detailed_status.get('embedding_model_loaded', False):
                    logger.error("❌ Embedding model not loaded - check model installation")
                    
            except Exception as e:
                logger.error(f"❌ Failed to get detailed RAG status: {str(e)}")
            
            # Return response indicating RAG unavailable but file stored
            return UploadResponse(
                message=f"Document '{file.filename}' uploaded but NOT processed for RAG. "
                       f"RAG system unavailable - check Qdrant (localhost:6333) and OpenAI API key.",
                filename=file.filename,
                size=file_size,
                processed=False,
                chunks_created=None
            )
        
        # Step 4: Process document with comprehensive error handling
        logger.info("⚙️ Step 4: Processing document with RAG system...")
        
        processing_start = time.time()
        processed = False
        chunks_created = 0
        processing_error = None
        
        try:
            logger.info(f"🔄 Calling rag_system.process_document({file_path}, content[{len(content)} bytes])")
            
            # Call the RAG system's process_document method
            processed = await app_state.rag_system.process_document(file_path, content)
            
            processing_time = time.time() - processing_start
            logger.info(f"⏱️ Processing completed in {processing_time:.2f} seconds")
            
            if processed:
                logger.info("✅ Document processed successfully!")
                
                # Get updated system status to find chunk count
                try:
                    status = await app_state.rag_system.get_system_status()
                    chunks_created = status.get('total_chunks', 0)
                    logger.info(f"📊 Total chunks in system: {chunks_created}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not get updated chunk count: {str(e)}")
                    chunks_created = None
                
            else:
                logger.error("❌ Document processing returned False - check server logs for details")
                processing_error = "Document processing pipeline returned False"
                
        except Exception as e:
            processing_error = str(e)
            logger.error(f"❌ Document processing failed with exception: {processing_error}")
            logger.error(f"Exception details: {traceback.format_exc()}")
            processed = False
        
        # Step 5: Build comprehensive response
        total_time = time.time() - start_time
        
        if processed:
            message = f"Document '{file.filename}' uploaded and successfully processed for RAG search!"
            logger.info(f"🎉 Upload completed successfully in {total_time:.2f} seconds")
        else:
            error_detail = f" Error: {processing_error}" if processing_error else ""
            message = f"Document '{file.filename}' uploaded but processing failed.{error_detail} Check server logs for details."
            logger.error(f"💔 Upload completed with processing failure in {total_time:.2f} seconds")
        
        response = UploadResponse(
            message=message,
            filename=file.filename,
            size=file_size,
            processed=processed,
            chunks_created=chunks_created if processed else None
        )
        
        # Log final response for debugging
        logger.info(f"📋 Final response: {response.dict()}")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper error codes)
        raise
        
    except Exception as e:
        # Handle unexpected errors
        total_time = time.time() - start_time
        error_msg = str(e)
        logger.error(f"💥 Unexpected upload error after {total_time:.2f}s: {error_msg}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Document upload failed: {error_msg}"
        )

# =============================================================================
# 📄 DOCUMENT MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/api/documents/list", response_model=DocumentListResponse)
async def list_documents():
    """
    Get list of all indexed documents with metadata
    """
    try:
        logger.info("📋 Fetching document list...")
        
        documents = await app_state.rag_system.get_all_documents()
        
        document_responses = [
            DocumentResponse(**doc) for doc in documents
        ]
        
        logger.info(f"✅ Retrieved {len(document_responses)} documents")
        
        return DocumentListResponse(
            documents=document_responses,
            total=len(document_responses)
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@app.get("/api/documents/{doc_id}", response_model=DocumentResponse)
async def get_document_details(doc_id: str):
    """
    Get detailed information about a specific document
    """
    try:
        logger.info(f"📄 Fetching details for document: {doc_id}")
        
        doc_details = await app_state.rag_system.get_document_details(doc_id)
        
        if not doc_details:
            logger.warning(f"Document not found: {doc_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"✅ Retrieved details for: {doc_details['filename']}")
        
        return DocumentResponse(**doc_details)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@app.delete("/api/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str):
    """
    Delete a document and all its associated chunks from the vector store
    """
    try:
        logger.info(f"🗑️ Deleting document: {doc_id}")
        
        result = await app_state.rag_system.delete_document(doc_id)
        
        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Failed to delete document: {error_msg}")
            raise HTTPException(status_code=404 if "not found" in error_msg.lower() else 500, detail=error_msg)
        
        logger.info(f"✅ Successfully deleted document: {result.get('filename')}")
        
        return DeleteResponse(
            success=True,
            doc_id=result.get("doc_id"),
            filename=result.get("filename"),
            chunks_deleted=result.get("chunks_deleted")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# =============================================================================
# 💬 CHAT ENDPOINTS
# =============================================================================

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

async def generate_demo_response(user_message: str) -> str:
    """Fallback demo responses when RAG is not available"""
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "hey"]):
        return "👋 Hello! I'm the Macrocomm AI Assistant powered by OpenAI. Upload documents to enable intelligent document-based responses."
    
    elif any(word in message_lower for word in ["document", "upload", "file"]):
        return "📄 You can upload PDF, DOCX, TXT, or Excel files. Once uploaded, I'll be able to answer questions based on your documents using OpenAI's GPT-4o-mini."
    
    elif any(word in message_lower for word in ["rag", "system", "status"]):
        return "🔧 RAG system status: Check /api/rag/status for detailed information. Make sure Qdrant (http://localhost:6333) is running and OpenAI API key is configured."
    
    else:
        return f"🤖 I received your message: '{user_message}'. For document-based responses, please upload documents and ensure the RAG system is running (Qdrant + OpenAI)."

# =============================================================================
# 🔌 WEBSOCKET ENDPOINT
# =============================================================================

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
            " RAG system ready for document-based queries (powered by OpenAI)." if rag_available 
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
                    
                    # Send response - FIXED: Using consistent field name 'message'
                    await websocket.send_json({
                        "type": "response",
                        "message": response_text,  # ← KEY FIX: Using 'message' field
                        "response": response_text,  # ← Also include 'response' for backwards compatibility
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

# =============================================================================
# 🧪 DEBUG AND TESTING ENDPOINTS
# =============================================================================

@app.get("/api/rag/debug")
async def rag_debug():
    """
    Comprehensive debugging endpoint to diagnose RAG system issues
    """
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "server_status": "running",
        "rag_system_checks": {}
    }
    
    try:
        logger.info("🔍 Running comprehensive RAG system diagnostics...")
        
        # Check 1: Basic RAG system existence
        debug_info["rag_system_checks"]["system_exists"] = hasattr(app_state, 'rag_system')
        
        if hasattr(app_state, 'rag_system'):
            # Check 2: RAG system status
            try:
                status = await app_state.rag_system.get_system_status()
                debug_info["rag_system_checks"]["detailed_status"] = status
            except Exception as e:
                debug_info["rag_system_checks"]["status_error"] = str(e)
            
            # Check 3: Individual components
            debug_info["rag_system_checks"]["components"] = {}
            
            # Vector Store
            try:
                if hasattr(app_state.rag_system, 'vector_store') and app_state.rag_system.vector_store:
                    debug_info["rag_system_checks"]["components"]["vector_store"] = {
                        "exists": True,
                        "client_exists": hasattr(app_state.rag_system.vector_store, 'client'),
                        "host": getattr(app_state.rag_system.vector_store, 'host', 'unknown'),
                        "port": getattr(app_state.rag_system.vector_store, 'port', 'unknown')
                    }
                else:
                    debug_info["rag_system_checks"]["components"]["vector_store"] = {"exists": False}
            except Exception as e:
                debug_info["rag_system_checks"]["components"]["vector_store"] = {"error": str(e)}
            
            # LLM Manager
            try:
                if hasattr(app_state.rag_system, 'llm_manager') and app_state.rag_system.llm_manager:
                    debug_info["rag_system_checks"]["components"]["llm_manager"] = {
                        "exists": True,
                        "provider": "OpenAI",
                        "model": app_state.rag_system.llm_manager.current_model,
                        "client_exists": app_state.rag_system.llm_manager.client is not None
                    }
                else:
                    debug_info["rag_system_checks"]["components"]["llm_manager"] = {"exists": False}
            except Exception as e:
                debug_info["rag_system_checks"]["components"]["llm_manager"] = {"error": str(e)}
            
            # Embedding Model
            try:
                debug_info["rag_system_checks"]["components"]["embedding_model"] = {
                    "loaded": hasattr(app_state.rag_system, 'embedding_model') and 
                             app_state.rag_system.embedding_model is not None
                }
            except Exception as e:
                debug_info["rag_system_checks"]["components"]["embedding_model"] = {"error": str(e)}
        
        # Check 4: External services connectivity
        debug_info["external_services"] = {}
        
        # Test Qdrant connection
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:6333/collections")
                debug_info["external_services"]["qdrant"] = {
                    "accessible": response.status_code == 200,
                    "status_code": response.status_code,
                    "url": "http://localhost:6333"
                }
        except Exception as e:
            debug_info["external_services"]["qdrant"] = {
                "accessible": False,
                "error": str(e),
                "url": "http://localhost:6333"
            }
        
        # Check OpenAI API key presence
        debug_info["external_services"]["openai"] = {
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "provider": "OpenAI GPT-4o-mini"
        }
        
        # Check 5: App state
        debug_info["app_state"] = {
            "startup_complete": getattr(app_state, 'startup_complete', False),
            "rag_status": getattr(app_state, 'rag_status', {}),
            "conversations_count": len(getattr(app_state, 'conversations', {}))
        }
        
        logger.info("✅ RAG system diagnostics completed")
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ Debug endpoint failed: {str(e)}")
        debug_info["debug_error"] = str(e)
        return debug_info

@app.post("/api/test-processing")
async def test_document_processing():
    """
    Test document processing with a simple text sample
    """
    logger.info("🧪 Testing document processing pipeline...")
    
    try:
        # Create test content
        test_content = """
        This is a test document for the RAG system.
        
        The Advanced Agentic RAG Pipeline implements human-like thought processes
        for intelligent document processing and retrieval.
        
        Key features include:
        - Comprehensive document processing (PDF, DOCX, TXT, Excel)
        - Intelligent chunking strategies
        - Vector-based similarity search
        - OpenAI GPT-4o-mini powered response generation
        - Enhanced error handling and debugging
        - Document metadata management
        
        This system demonstrates how AI can process documents,
        understand context, and provide relevant responses to user queries.
        """
        
        test_filename = "test_document.txt"
        test_file_path = Path(test_filename)
        test_content_bytes = test_content.encode('utf-8')
        
        logger.info(f"📝 Created test document: {len(test_content_bytes)} bytes")
        
        # Test the processing pipeline
        if app_state.rag_status.get('initialized', False):
            logger.info("🔄 Testing RAG processing pipeline...")
            
            result = await app_state.rag_system.process_document(test_file_path, test_content_bytes)
            
            if result:
                logger.info("✅ Test processing successful!")
                
                # Test query
                logger.info("🔍 Testing query processing...")
                query_result = await app_state.rag_system.query("What are the key features?")
                
                return {
                    "test_status": "success",
                    "processing_result": result,
                    "query_test": {
                        "query": "What are the key features?",
                        "response": query_result.get("response", "No response"),
                        "using_rag": query_result.get("using_rag", False),
                        "context_found": query_result.get("context_found", 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error("❌ Test processing failed")
                return {
                    "test_status": "failed",
                    "error": "Processing returned False",
                    "timestamp": datetime.now().isoformat()
                }
        else:
            logger.warning("⚠️ RAG system not initialized for testing")
            return {
                "test_status": "skipped",
                "reason": "RAG system not initialized",
                "rag_status": app_state.rag_status,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Test processing failed: {str(e)}")
        return {
            "test_status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }

# =============================================================================
# 📁 STATIC FILE SERVING
# =============================================================================

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

# =============================================================================
# 🚀 DEVELOPMENT SERVER
# =============================================================================

if __name__ == "__main__":
    logger.info("🚀 Starting RAG-enabled development server with OpenAI...")
    uvicorn.run(
        "main_production_with_rag:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        access_log=True,
        log_level="info",
        reload_dirs=["../"]
    )