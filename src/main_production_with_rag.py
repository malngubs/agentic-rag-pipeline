#!/usr/bin/env python3
"""
Production FastAPI server with Real RAG capabilities + Phase 1 Analytics
Integrates document processing, vector search, LLM generation, conversation history, and analytics
Version 2.2 - Phase 1 Complete: Analytics, Citations, Conversation History
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
import json

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict

# Import our RAG system
from rag_components import RAGSystem, RAGConfig

# ✨ PHASE 1 IMPORTS - New functionality
try:
    from analytics_database import AnalyticsDatabase
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    logging.warning("⚠️ analytics_database.py not found - analytics disabled")

try:
    from source_citations import CitationBuilder
    CITATIONS_AVAILABLE = True
except ImportError:
    CITATIONS_AVAILABLE = False
    logging.warning("⚠️ source_citations.py not found - enhanced citations disabled")

try:
    from auth import (
        AuthManager, UserCreate, UserLogin, TokenResponse, UserResponse,
        get_current_user, get_current_user_optional, set_auth_manager,
        require_viewer, require_editor, require_admin, RoleChecker
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logging.warning("⚠️ auth.py not found - authentication disabled")

try:
    from audit_log import AuditLogger, set_audit_logger, get_audit_logger
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    logging.warning("⚠️ audit_log.py not found - audit logging disabled")

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
    """Chat message model"""
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
    # Phase 1: Enhanced citations
    citations: Optional[List[Dict]] = []

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

# ✨ PHASE 1: New Models
class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    conversations: List[Dict]
    total: int

class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response"""
    total_queries: int
    total_conversations: int
    avg_response_time: float
    total_cost: float
    total_documents: int
    total_chunks: int
    success_rate: float

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
    """Centralized application state with RAG capabilities and Phase 1 analytics"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Core RAG system
        config = RAGConfig()
        self.rag_system = RAGSystem(config)
        self.rag_status = {
            'vector_store': False,
            'llm_manager': False,
            'initialized': False
        }
        
        # ✨ PHASE 1: Analytics database
        self.analytics_db = None
        if ANALYTICS_AVAILABLE:
            try:
                self.analytics_db = AnalyticsDatabase(db_path="data/analytics.db")
                logger.info("✅ Analytics database initialized: data/analytics.db")
            except Exception as e:
                logger.error(f"❌ Analytics database initialization failed: {e}")
                self.analytics_db = None
        
        # ✨ PHASE 1: Citation builder
        self.citation_builder = None
        if CITATIONS_AVAILABLE:
            try:
                self.citation_builder = CitationBuilder()
                logger.info("✅ Citation builder initialized")
            except Exception as e:
                logger.error(f"❌ Citation builder initialization failed: {e}")
                self.citation_builder = None

        # ✨ PHASE 2: Authentication system
        self.auth_manager = None
        if AUTH_AVAILABLE:
            try:
                self.auth_manager = AuthManager(db_path="data/auth.db")
                set_auth_manager(self.auth_manager)  # Set global instance
                logger.info("✅ Authentication system initialized: data/auth.db")
            except Exception as e:
                logger.error(f"❌ Authentication system initialization failed: {e}")
                self.auth_manager = None

        # ✨ PHASE 2: Audit logging system
        self.audit_logger = None
        if AUDIT_AVAILABLE:
            try:
                self.audit_logger = AuditLogger(db_path="data/audit_log.db")
                set_audit_logger(self.audit_logger)
                logger.info("✅ Audit logging system initialized: data/audit_log.db")
            except Exception as e:
                logger.error(f"❌ Audit logging system initialization failed: {e}")
                self.audit_logger = None

        self.startup_complete = False
    
    async def initialize_components(self):
        """Initialize all system components including RAG"""
        logger.info("🚀 Starting Agentic RAG Pipeline with Phase 1 Features...")
        
        # Ensure data directory exists for analytics
        os.makedirs("data", exist_ok=True)
        
        # Initialize RAG system
        try:
            rag_init_result = await self.rag_system.initialize()
            logger.info(f"RAG system initialization result: {rag_init_result}")
            
            if rag_init_result.get('initialized', False):
                self.rag_status = {
                    'vector_store': True,
                    'llm_manager': True,
                    'initialized': True
                }
                logger.info("✅ RAG System (OpenAI GPT-4o-mini)")
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
        logger.info("📊 Phase 1 Features: Analytics ✅, Citations ✅, Conversation History ✅")
    
    def get_system_status(self) -> Dict:
        """Get current system status including RAG and Phase 1 features"""
        return {
            "startup_complete": self.startup_complete,
            "rag_initialized": self.rag_status.get('initialized', False),
            "vector_store_available": self.rag_status.get('vector_store', False),
            "llm_available": self.rag_status.get('llm_manager', False),
            "active_connections": len(self.connection_manager.active_connections),
            "total_conversations": len(self.conversations),
            # Phase 1 status
            "analytics_enabled": self.analytics_db is not None,
            "citations_enabled": self.citation_builder is not None
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
    logger.info("🚀 Starting Agentic RAG Pipeline with Phase 1 Features...")
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
    title="Macrocomm AI Assistant with RAG + Analytics",
    description="Advanced Agentic RAG Pipeline with Conversation History and Analytics",
    version="2.2.0",
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
# 📁 STATIC FILE SERVING
# =============================================================================

def setup_static_files():
    """Setup static file serving for frontend assets"""
    try:
        # Mount frontend directory for HTML files
        possible_frontend_paths = [
            Path("../frontend"),
            Path("frontend"), 
            Path("./frontend"),
            Path(__file__).parent.parent / "frontend"
        ]
        
        frontend_path = None
        for path in possible_frontend_paths:
            if path.exists():
                frontend_path = path
                break
        
        if frontend_path:
            app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")
            logger.info(f"✅ Frontend files mounted from: {frontend_path.absolute()}")
        
        # Mount static directory for JavaScript files
        possible_static_paths = [
            Path("../static"),
            Path("static"),
            Path("./static"),
            Path(__file__).parent.parent / "static",
        ]
        
        static_path = None
        for path in possible_static_paths:
            if path.exists():
                static_path = path
                break
        
        if static_path:
            app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
            logger.info(f"✅ Static files mounted from: {static_path.absolute()}")
            return True
        else:
            logger.warning("⚠️ Static directory not found - creating it now")
            static_dir = Path("./static")
            static_dir.mkdir(exist_ok=True)
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            logger.info(f"📁 Created and mounted static directory: {static_dir.absolute()}")
            logger.info("⚠️ Please place macrocomm-bubble.js in the static/ directory")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Static file mounting failed: {e}")
        return False

# Setup static files
setup_static_files()

# =============================================================================
# 📍 CORE API ROUTES
# =============================================================================

@app.get("/api/info", response_class=JSONResponse)
async def root():
    """API root endpoint"""
    return {
        "service": "Macrocomm AI Assistant with RAG + Phase 1 Analytics",
        "version": "2.2.0",
        "status": "online",
        "llm_provider": "OpenAI GPT-4o-mini",
        "phase_1_features": ["conversation_history", "analytics", "cost_tracking", "enhanced_citations"],
        "capabilities": [
            "real_time_chat", 
            "document_processing", 
            "vector_search", 
            "llm_generation", 
            "document_management",
            "conversation_history",  # ✨ Phase 1
            "usage_analytics",        # ✨ Phase 1
            "cost_tracking"           # ✨ Phase 1
        ],
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "upload": "/api/upload",
            "documents_list": "/api/documents/list",
            "document_details": "/api/documents/{doc_id}",
            "document_delete": "/api/documents/{doc_id}",
            "rag_status": "/api/rag/status",
            # ✨ Phase 1 endpoints
            "conversations": "/api/conversations",
            "analytics_summary": "/api/analytics/summary",
            "analytics_export": "/api/analytics/export",
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

# =============================================================================
# 🌐 HTML SERVING ROUTES - Production Frontend
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main index.html page"""
    try:
        possible_paths = [
            Path("../index.html"),
            Path("index.html"),
            Path("./index.html"),
            Path(__file__).parent / "index.html",
            Path(__file__).parent.parent / "index.html"
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return HTMLResponse(content=f.read())
        
        raise HTTPException(status_code=404, detail="Index page not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin.html", response_class=HTMLResponse)
async def serve_admin():
    """Serve the admin portal page"""
    try:
        possible_paths = [
            Path("../admin.html"),
            Path("admin.html"),
            Path("./admin.html"),
            Path(__file__).parent / "admin.html",
            Path(__file__).parent.parent / "admin.html"
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return HTMLResponse(content=f.read())
        
        raise HTTPException(status_code=404, detail="Admin page not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving admin.html: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/login.html", response_class=HTMLResponse)
async def serve_login():
    """Serve the login page"""
    try:
        possible_paths = [
            Path("../login.html"),
            Path("login.html"),
            Path("./login.html"),
            Path(__file__).parent / "login.html",
            Path(__file__).parent.parent / "login.html"
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return HTMLResponse(content=f.read())

        raise HTTPException(status_code=404, detail="Login page not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving login.html: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check including RAG components and Phase 1 features"""
    status = app_state.get_system_status()
    
    return HealthResponse(
        status="healthy" if status["startup_complete"] else "starting",
        timestamp=time.time(),
        service="agentic-rag-pipeline-phase1",
        version="2.2.0",
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
                "provider": "OpenAI GPT-4o-mini"
            },
            "websocket": {
                "status": "healthy",
                "connections": str(status["active_connections"])
            },
            "conversations": {
                "status": "healthy",
                "total": str(status["total_conversations"])
            },
            # ✨ Phase 1 components
            "analytics": {
                "status": "healthy" if status["analytics_enabled"] else "disabled"
            },
            "citations": {
                "status": "healthy" if status["citations_enabled"] else "disabled"
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
            "phase_1_status": {
                "analytics_enabled": app_state.analytics_db is not None,
                "citations_enabled": app_state.citation_builder is not None
            },
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

# =============================================================================
# 🔐 AUTHENTICATION ENDPOINTS (PHASE 2)
# =============================================================================

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user account"""
    if not app_state.auth_manager:
        raise HTTPException(status_code=503, detail="Authentication not available")

    try:
        # Create user
        user = app_state.auth_manager.create_user(user_data)

        # Generate token
        token = app_state.auth_manager.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    """Authenticate user and return access token"""
    if not app_state.auth_manager:
        raise HTTPException(status_code=503, detail="Authentication not available")

    # Get client IP
    client_ip = request.client.host if request.client else None

    # Authenticate user
    user_dict = app_state.auth_manager.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )

    if not user_dict:
        # Log failed login attempt
        if app_state.audit_logger:
            app_state.audit_logger.log_auth_event(
                action=app_state.audit_logger.ACTION_LOGIN_FAILED,
                user_email=credentials.email,
                ip_address=client_ip,
                status="failure",
                error_message="Incorrect email or password"
            )

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    # Log successful login
    if app_state.audit_logger:
        app_state.audit_logger.log_auth_event(
            action=app_state.audit_logger.ACTION_LOGIN,
            user_id=user_dict['id'],
            user_email=user_dict['email'],
            ip_address=client_ip,
            status="success"
        )

    # Generate token
    token = app_state.auth_manager.create_access_token(
        user_id=user_dict['id'],
        email=user_dict['email'],
        role=user_dict['role']
    )

    # Create user response
    user = UserResponse(
        id=user_dict['id'],
        email=user_dict['email'],
        full_name=user_dict['full_name'],
        role=user_dict['role'],
        created_at=user_dict['created_at'],
        last_login=user_dict['last_login']
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user


@app.get("/api/auth/users", response_model=List[UserResponse])
async def list_users(current_user: UserResponse = Depends(require_admin)):
    """List all users (admin only)"""
    if not app_state.auth_manager:
        raise HTTPException(status_code=503, detail="Authentication not available")

    return app_state.auth_manager.get_all_users()


# =============================================================================
# 📤 DOCUMENT UPLOAD
# =============================================================================

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(require_editor)
):
    """Enhanced document upload with Phase 1 analytics logging (requires editor role)"""
    start_time = time.time()
    logger.info(f"📤 Upload request received: {file.filename} by {current_user.email}")
    
    try:
        # Validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_path = Path(file.filename)
        supported_types = {'.pdf', '.docx', '.txt', '.xlsx', '.xls'}
        file_extension = file_path.suffix.lower()
        
        if file_extension not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type '{file_extension}'. Supported: {supported_types}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File size exceeds 100MB limit")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Check RAG system status
        if not app_state.rag_status.get('initialized', False):
            return UploadResponse(
                message=f"Document '{file.filename}' uploaded but NOT processed. RAG system unavailable.",
                filename=file.filename,
                size=file_size,
                processed=False,
                chunks_created=None
            )
        
        # Process document
        processed = await app_state.rag_system.process_document(file_path, content)
        
        if processed:
            status = await app_state.rag_system.get_system_status()
            chunks_created = status.get('total_chunks', 0)
            
            # ✨ PHASE 1: Log document upload to analytics
            if app_state.analytics_db:
                try:
                    app_state.analytics_db.log_document_upload(
                        filename=file.filename,
                        file_size=file_size,
                        chunks_created=chunks_created,
                        success=True
                    )
                except Exception as e:
                    logger.warning(f"Failed to log upload to analytics: {e}")

            # ✨ PHASE 2: Log document upload to audit log
            if app_state.audit_logger:
                try:
                    app_state.audit_logger.log_document_event(
                        action=app_state.audit_logger.ACTION_UPLOAD,
                        user_id=current_user.id,
                        user_email=current_user.email,
                        document_name=file.filename,
                        metadata={
                            'file_size': file_size,
                            'chunks_created': chunks_created,
                            'file_extension': file_extension
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to log upload to audit: {e}")

            message = f"Document '{file.filename}' uploaded and successfully processed for RAG search!"
        else:
            message = f"Document '{file.filename}' uploaded but processing failed. Check server logs."
        
        return UploadResponse(
            message=message,
            filename=file.filename,
            size=file_size,
            processed=processed,
            chunks_created=chunks_created if processed else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Upload error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

# =============================================================================
# 📄 DOCUMENT MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/api/documents/list", response_model=DocumentListResponse)
async def list_documents():
    """Get list of all indexed documents with metadata"""
    try:
        documents = await app_state.rag_system.get_all_documents()
        document_responses = [DocumentResponse(**doc) for doc in documents]
        
        return DocumentListResponse(
            documents=document_responses,
            total=len(document_responses)
        )
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@app.get("/api/documents/{doc_id}", response_model=DocumentResponse)
async def get_document_details(doc_id: str):
    """Get detailed information about a specific document"""
    try:
        doc_details = await app_state.rag_system.get_document_details(doc_id)
        
        if not doc_details:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(**doc_details)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@app.delete("/api/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str):
    """Delete a document and all its associated chunks from the vector store"""
    try:
        result = await app_state.rag_system.delete_document(doc_id)
        
        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            raise HTTPException(
                status_code=404 if "not found" in error_msg.lower() else 500, 
                detail=error_msg
            )
        
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
    """Enhanced chat endpoint with RAG capabilities and Phase 1 analytics"""
    start_time = time.time()
    
    try:
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        # Query RAG system
        if app_state.rag_status.get('initialized', False):
            rag_result = await app_state.rag_system.query(message.message)
            
            response_text = rag_result['response']
            sources = rag_result['sources']
            using_rag = rag_result['using_rag']
            context_found = rag_result.get('context_found', 0)
            confidence = rag_result.get('confidence', 0.8)
            
            # ✨ PHASE 1: Build enhanced citations
            citations = []
            if app_state.citation_builder and context_found > 0:
                try:
                    # Get search results for citation building
                    search_results = await app_state.rag_system.vector_store.search(
                        message.message,
                        limit=context_found
                    )
                    citations = app_state.citation_builder.build_citations(search_results)
                except Exception as e:
                    logger.warning(f"Citation building failed: {e}")
        else:
            response_text = await generate_demo_response(message.message)
            sources = ["demo_responses"]
            using_rag = False
            context_found = 0
            confidence = 0.5
            citations = []
        
        response_time = time.time() - start_time
        
        # Store conversation in memory
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
        
        # ✨ PHASE 1: Log to analytics database with proper metrics
        if app_state.analytics_db:
            try:
                from analytics_database import QueryMetrics, calculate_openai_cost
                import uuid as uuid_lib
                
                # Extract token usage from RAG result if available
                token_usage = rag_result.get('token_usage', {})
                input_tokens = token_usage.get('input_tokens', 0)
                output_tokens = token_usage.get('output_tokens', 0)
                
                # If no token usage, estimate (rough approximation)
                if input_tokens == 0:
                    input_tokens = int(len(message.message.split()) * 1.3)
                if output_tokens == 0:
                    output_tokens = int(len(response_text.split()) * 1.3)
                
                # Calculate cost
                cost = calculate_openai_cost(input_tokens, output_tokens, "gpt-4o-mini")
                
                # Create metrics object
                metrics = QueryMetrics(
                    query_id=str(uuid_lib.uuid4()),
                    conversation_id=conversation_id,
                    query_text=message.message,
                    response_text=response_text,
                    timestamp=datetime.now(),
                    response_time=response_time,
                    using_rag=using_rag,
                    context_found=context_found,
                    confidence=confidence,
                    sources=sources,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    model_used="gpt-4o-mini",
                    success=True
                )
                
                # Record metrics
                app_state.analytics_db.record_query_metrics(metrics)
            except Exception as e:
                logger.warning(f"Failed to log to analytics: {e}")
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            response_time=response_time,
            intent="informational",
            confidence=confidence,
            sources=sources,
            using_rag=using_rag,
            context_found=context_found,
            citations=citations  # ✨ Phase 1: Enhanced citations
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
        return f"🤖 I received your message: '{user_message}'. For document-based responses, please upload documents and ensure the RAG system is running."

# =============================================================================
# 🔌 WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with RAG capabilities and Phase 1 analytics"""
    client_info = {
        "client_host": websocket.client.host if websocket.client else "unknown",
        "connected_at": time.time()
    }
    
    try:
        await app_state.connection_manager.connect(websocket, client_info)
        
        # Send welcome message
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
                    
                    # Query RAG system
                    if app_state.rag_status.get('initialized', False):
                        rag_result = await app_state.rag_system.query(message)
                        response_text = rag_result['response']
                        sources = rag_result['sources']
                        using_rag = rag_result['using_rag']
                        context_found = rag_result.get('context_found', 0)
                        confidence = rag_result.get('confidence', 0.8)
                        
                        # ✨ PHASE 1: Build citations
                        citations = []
                        if app_state.citation_builder and context_found > 0:
                            try:
                                search_results = await app_state.rag_system.vector_store.search(
                                    message,
                                    limit=context_found
                                )
                                citations = app_state.citation_builder.build_citations(search_results)
                            except Exception as e:
                                logger.warning(f"Citation building failed: {e}")
                    else:
                        response_text = await generate_demo_response(message)
                        sources = ["demo_responses"]
                        using_rag = False
                        context_found = 0
                        confidence = 0.5
                        citations = []
                    
                    response_time = time.time() - start_time
                    
                    # ✨ PHASE 1: Log to analytics with proper metrics
                    if app_state.analytics_db:
                        try:
                            from analytics_database import QueryMetrics, calculate_openai_cost
                            import uuid as uuid_lib
                            
                            # Extract token usage from RAG result if available
                            token_usage = rag_result.get('token_usage', {})
                            input_tokens = token_usage.get('input_tokens', 0)
                            output_tokens = token_usage.get('output_tokens', 0)
                            
                            # If no token usage, estimate
                            if input_tokens == 0:
                                input_tokens = int(len(message.split()) * 1.3)
                            if output_tokens == 0:
                                output_tokens = int(len(response_text.split()) * 1.3)
                            
                            # Calculate cost
                            cost = calculate_openai_cost(input_tokens, output_tokens, "gpt-4o-mini")
                            
                            # Create and record metrics
                            metrics = QueryMetrics(
                                query_id=str(uuid_lib.uuid4()),
                                conversation_id=conversation_id,
                                query_text=message,
                                response_text=response_text,
                                timestamp=datetime.now(),
                                response_time=response_time,
                                using_rag=using_rag,
                                context_found=context_found,
                                confidence=confidence,
                                sources=sources,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                cost=cost,
                                model_used="gpt-4o-mini",
                                success=True
                            )
                            app_state.analytics_db.record_query_metrics(metrics)
                        except Exception as e:
                            logger.warning(f"Failed to log to analytics: {e}")
                    
                    # Send response with both field names for compatibility
                    await websocket.send_json({
                        "type": "response",
                        "message": response_text,
                        "response": response_text,
                        "conversation_id": conversation_id,
                        "response_time": response_time,
                        "timestamp": time.time(),
                        "using_rag": using_rag,
                        "sources": sources,
                        "context_found": context_found,
                        "intent": "conversational",
                        "confidence": confidence,
                        "citations": citations  # ✨ Phase 1
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


@app.websocket("/ws/chat/stream")
async def websocket_streaming_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint with STREAMING responses - FIXED ASYNC VERSION
    """
    client_info = {
        "client_host": websocket.client.host if websocket.client else "unknown",
        "connected_at": time.time()
    }
    
    try:
        await app_state.connection_manager.connect(websocket, client_info)
        
        # Send welcome message
        rag_available = app_state.rag_status.get('initialized', False)
        welcome_msg = "🚀 Streaming chat connected! Responses will appear in real-time." + (
            " RAG system ready." if rag_available 
            else " RAG system not available."
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
                    
                    # Step 1: Send "thinking" indicator
                    await websocket.send_json({
                        "type": "thinking",
                        "conversation_id": conversation_id,
                        "timestamp": time.time()
                    })
                    
                    # Step 2: Get context from RAG (if available)
                    search_results = []
                    context_texts = []
                    sources = []
                    citations = []
                    using_rag = False
                    context_found = 0
                    
                    if app_state.rag_status.get('initialized', False):
                        # Search for relevant context
                        search_results = await app_state.rag_system.vector_store.search(
                            message,
                            limit=app_state.rag_system.config.max_context_chunks,
                            score_threshold=app_state.rag_system.config.confidence_threshold
                        )
                        
                        if search_results:
                            context_texts = [r["text"] for r in search_results]
                            sources = [r["source"] for r in search_results]
                            context_found = len(search_results)
                            using_rag = True
                            
                            # Build citations (with error handling)
                            if app_state.citation_builder:
                                try:
                                    citations = app_state.citation_builder.build_citations(search_results)
                                except Exception as e:
                                    logger.warning(f"Citation building failed: {e}")
                    
                    # Step 3: Build the prompt
                    if context_texts:
                        context_block = "\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(context_texts)])
                        prompt = f"""You are a helpful AI assistant. Use the following context to answer the user's question.

CONTEXT:
{context_block}

USER QUESTION: {message}

Provide a clear, accurate answer based on the context. If the context doesn't contain relevant information, say so politely."""
                    else:
                        prompt = f"You are a helpful AI assistant. Answer this question: {message}"
                    
                    # Step 4: Stream the response - FIXED ASYNC VERSION
                    full_response = ""
                    
                    try:
                        # Create the streaming request in a thread executor
                        def create_stream():
                            return app_state.rag_system.llm_manager.client.chat.completions.create(
                                model=app_state.rag_system.config.openai_model,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=app_state.rag_system.config.max_tokens,
                                temperature=app_state.rag_system.config.temperature,
                                stream=True
                            )
                        
                        # Get the stream object
                        stream = await asyncio.get_event_loop().run_in_executor(None, create_stream)
                        
                        # Stream tokens to client
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                token = chunk.choices[0].delta.content
                                full_response += token
                                
                                # Send token immediately
                                await websocket.send_json({
                                    "type": "stream_token",
                                    "token": token,
                                    "conversation_id": conversation_id,
                                    "timestamp": time.time()
                                })
                                
                                # Small delay for smooth visual effect
                                await asyncio.sleep(0.01)
                    
                    except Exception as e:
                        logger.error(f"Streaming failed: {e}")
                        full_response = "I encountered an error processing your request. Please try again."
                        await websocket.send_json({
                            "type": "stream_token",
                            "token": full_response,
                            "conversation_id": conversation_id,
                            "timestamp": time.time()
                        })
                    
                    response_time = time.time() - start_time
                    
                    # Step 5: Generate follow-up questions - FIXED ASYNC VERSION
                    follow_ups = []
                    if app_state.rag_status.get('initialized', False) and search_results:
                        try:
                            follow_ups = await app_state.rag_system.generate_follow_up_questions(
                                message, full_response, search_results
                            )
                        except Exception as e:
                            logger.warning(f"Follow-up generation failed: {e}")
                            # Provide default follow-ups
                            follow_ups = [
                                "Can you tell me more about this?",
                                "What else should I know?",
                                "Are there any related topics?"
                            ]
                    
                    # Step 6: Send completion message
                    await websocket.send_json({
                        "type": "stream_complete",
                        "conversation_id": conversation_id,
                        "response_time": response_time,
                        "timestamp": time.time(),
                        "using_rag": using_rag,
                        "sources": list(set(sources)),
                        "context_found": context_found,
                        "confidence": 0.8 if context_found > 0 else 0.5,
                        "citations": citations,
                        "follow_up_questions": follow_ups
                    })
                    
                    # Step 7: Log to analytics
                    if app_state.analytics_db:
                        try:
                            from analytics_database import QueryMetrics, calculate_openai_cost
                            
                            input_tokens = int(len(message.split()) * 1.3) + int(sum(len(ctx.split()) for ctx in context_texts) * 1.3)
                            output_tokens = int(len(full_response.split()) * 1.3)
                            cost = calculate_openai_cost(input_tokens, output_tokens, "gpt-4o-mini")
                            
                            metrics = QueryMetrics(
                                query_id=str(uuid.uuid4()),
                                conversation_id=conversation_id,
                                query_text=message,
                                response_text=full_response,
                                timestamp=datetime.now(),
                                response_time=response_time,
                                using_rag=using_rag,
                                context_found=context_found,
                                confidence=0.8 if context_found > 0 else 0.5,
                                sources=sources,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                cost=cost,
                                model_used="gpt-4o-mini",
                                success=True
                            )
                            app_state.analytics_db.record_query_metrics(metrics)
                        except Exception as e:
                            logger.warning(f"Analytics logging failed: {e}")
                    
                except Exception as e:
                    logger.error(f"WebSocket streaming failed: {e}\n{traceback.format_exc()}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "I encountered an error processing your request. Please try again.",
                        "timestamp": time.time()
                    })
    
    except WebSocketDisconnect:
        app_state.connection_manager.disconnect(websocket)
        logger.info("Streaming WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        app_state.connection_manager.disconnect(websocket)

# =============================================================================
# ✨ PHASE 1: ANALYTICS & CONVERSATION ENDPOINTS
# =============================================================================


@app.post("/api/transcribe")
async def transcribe_audio(request: Request):
    """
    Transcribe audio to text (for voice input feature)
    Note: This endpoint receives audio data and returns transcribed text
    In production, you'd use OpenAI Whisper or similar service
    """
    try:
        # For now, return a placeholder response
        # In production, integrate with OpenAI Whisper API:
        # audio_file = await request.body()
        # transcript = openai.Audio.transcribe("whisper-1", audio_file)
        # return {"text": transcript.text}
        
        return JSONResponse({
            "text": "Voice transcription endpoint ready (integrate Whisper API for production)",
            "status": "placeholder"
        })
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations", response_model=ConversationHistoryResponse)
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    current_user: UserResponse = Depends(require_viewer)
):
    """Get conversation history from analytics database (requires authentication)"""
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")

    try:
        conversations = app_state.analytics_db.get_all_conversations(limit=limit, offset=offset)
        total = app_state.analytics_db.get_total_conversations()

        return ConversationHistoryResponse(
            conversations=conversations,
            total=total
        )
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversations: {str(e)}")

@app.get("/api/conversations/search")
async def search_conversations(
    query: Optional[str] = None,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Search conversations by various criteria"""
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")

    try:
        result = app_state.analytics_db.search_conversations(
            query=query,
            conversation_id=conversation_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        return result
    except Exception as e:
        logger.error(f"Failed to search conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search conversations: {str(e)}")

@app.get("/api/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(current_user: UserResponse = Depends(require_viewer)):
    """Get analytics summary (requires authentication)"""
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        # Get analytics summary (returns AnalyticsSummary dataclass)
        summary_obj = app_state.analytics_db.get_analytics_summary(days=30)
        
        # Get RAG system stats
        rag_status = await app_state.rag_system.get_system_status()
        
        return AnalyticsSummaryResponse(
            total_queries=summary_obj.total_queries,
            total_conversations=summary_obj.total_conversations,
            avg_response_time=summary_obj.avg_response_time,
            total_cost=summary_obj.total_cost,
            total_documents=rag_status.get('documents_indexed', 0),
            total_chunks=rag_status.get('total_chunks', 0),
            success_rate=summary_obj.success_rate
        )
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")

@app.get("/api/analytics/budget-alert")
async def get_budget_alert(
    daily_budget: float = 10.0,
    monthly_budget: float = 300.0,
    current_user: UserResponse = Depends(require_viewer)
):
    """
    Get budget alert status (requires authentication)
    Checks current spending against daily and monthly budgets
    """
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        alert = app_state.analytics_db.get_budget_alert(daily_budget, monthly_budget)
        return JSONResponse(content=alert)
    except Exception as e:
        logger.error(f"Failed to get budget alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/cost-breakdown")
async def get_cost_breakdown(days: int = 30, current_user: UserResponse = Depends(require_viewer)):
    """
    Get detailed cost breakdown by model and time period (requires authentication)
    Provides granular cost analysis for the specified number of days
    """
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")

    try:
        breakdown = app_state.analytics_db.get_cost_breakdown(days=days)
        return JSONResponse(content=breakdown)
    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/daily-stats")
async def get_daily_stats(days: int = 30, current_user: UserResponse = Depends(require_viewer)):
    """
    Get daily statistics for time-series charts (requires authentication)
    """
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")

    try:
        stats = app_state.analytics_db.get_daily_stats(days=days)
        return JSONResponse(content={"daily_stats": stats, "days": days})
    except Exception as e:
        logger.error(f"Failed to get daily stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str, format: str = "json"):
    """
    Export individual conversation in JSON or CSV format
    """
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        if format.lower() == "csv":
            data = app_state.analytics_db.export_conversation(conversation_id, format="csv")
            return Response(
                content=data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=conversation_{conversation_id}.csv"}
            )
        else:
            data = app_state.analytics_db.export_conversation(conversation_id, format="json")
            return JSONResponse(content=json.loads(data))
    except Exception as e:
        logger.error(f"Failed to export conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/export")
async def export_analytics(format: str = "json"):
    """Export analytics data"""
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        if format.lower() == "csv":
            data = app_state.analytics_db.export_to_csv()
            return Response(
                content=data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
        else:
            data = app_state.analytics_db.export_to_json()
            return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Failed to export analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")

# =============================================================================
# 📋 AUDIT LOG ENDPOINTS (PHASE 2)
# =============================================================================

@app.get("/api/audit/logs")
async def get_audit_logs(
    user_id: Optional[int] = None,
    category: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: UserResponse = Depends(require_admin)
):
    """Get audit logs with filters (admin only)"""
    if not app_state.audit_logger:
        raise HTTPException(status_code=503, detail="Audit logging not available")

    try:
        result = app_state.audit_logger.get_logs(
            user_id=user_id,
            category=category,
            action=action,
            start_date=start_date,
            end_date=end_date,
            status=status,
            limit=limit,
            offset=offset
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/statistics")
async def get_audit_statistics(
    days: int = 30,
    current_user: UserResponse = Depends(require_admin)
):
    """Get audit log statistics (admin only)"""
    if not app_state.audit_logger:
        raise HTTPException(status_code=503, detail="Audit logging not available")

    try:
        stats = app_state.audit_logger.get_statistics(days=days)
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Failed to get audit statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/user/{user_id}")
async def get_user_audit_logs(
    user_id: int,
    days: int = 30,
    current_user: UserResponse = Depends(require_admin)
):
    """Get audit logs for a specific user (admin only)"""
    if not app_state.audit_logger:
        raise HTTPException(status_code=503, detail="Audit logging not available")

    try:
        logs = app_state.audit_logger.get_user_activity(user_id=user_id, days=days)
        return JSONResponse(content={'logs': logs, 'user_id': user_id, 'days': days})
    except Exception as e:
        logger.error(f"Failed to get user audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/failed-logins")
async def get_failed_logins(
    hours: int = 24,
    current_user: UserResponse = Depends(require_admin)
):
    """Get recent failed login attempts (admin only)"""
    if not app_state.audit_logger:
        raise HTTPException(status_code=503, detail="Audit logging not available")

    try:
        logs = app_state.audit_logger.get_failed_logins(hours=hours)
        return JSONResponse(content={'logs': logs, 'hours': hours})
    except Exception as e:
        logger.error(f"Failed to get failed logins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 🚀 DEVELOPMENT SERVER
# =============================================================================

if __name__ == "__main__":
    logger.info("🚀 Starting RAG-enabled development server with Phase 1 Features...")
    logger.info("📊 Features: Analytics ✅, Citations ✅, Conversation History ✅")
    uvicorn.run(
        "main_production_with_rag:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        access_log=True,
        log_level="info",
        reload_dirs=["../"]
    )