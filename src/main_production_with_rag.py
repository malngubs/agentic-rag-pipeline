#!/usr/bin/env python3
"""
Production FastAPI server with Real RAG capabilities + Phase 1 Analytics
Integrates document processing, vector search, LLM generation, conversation history, and analytics
Version 2.2 - Phase 1 Complete: Analytics, Citations, Conversation History
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import logging
import os
import time
import uuid
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import json

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict, EmailStr

# Import data analyst module with fallback
try:
    from data_analyst import (
        AnalystOrchestrator,
        FileIngestor,
        DataProfiler,
        StatisticalEngine,
        ChartRecommender,
        ChartGenerator,
        InsightGenerator,
    )
    DATA_ANALYST_AVAILABLE = True
except ImportError:
    try:
        from .data_analyst import (
            AnalystOrchestrator,
            FileIngestor,
            DataProfiler,
            StatisticalEngine,
            ChartRecommender,
            ChartGenerator,
            InsightGenerator,
        )
        DATA_ANALYST_AVAILABLE = True
    except ImportError:
        DATA_ANALYST_AVAILABLE = False
        AnalystOrchestrator = None
        FileIngestor = None
        DataProfiler = None
        StatisticalEngine = None
        ChartRecommender = None
        ChartGenerator = None
        InsightGenerator = None
        logging.warning("⚠️ data_analyst module not available")

# Import our RAG system
from rag_components import RAGSystem, RAGConfig

# ✨ PHASE 5 IMPORTS - Configuration & Advanced Features
try:
    from config_manager import ConfigurationManager, set_config_manager, get_config_manager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("⚠️ config_manager.py not found - configuration features disabled")

# ✨ PHASE 3 IMPORTS - Advanced Document Management
try:
    from document_versions import DocumentVersionManager, set_version_manager, get_version_manager
    VERSIONS_AVAILABLE = True
except ImportError:
    VERSIONS_AVAILABLE = False
    logging.warning("⚠️ document_versions.py not found - version control disabled")

try:
    from document_tags import DocumentTagManager
    TAGS_AVAILABLE = True
except ImportError:
    TAGS_AVAILABLE = False
    logging.warning("⚠️ document_tags.py not found - document tagging disabled")

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

# ✨ MULTI-TENANT IMPORTS - Tenant isolation and document scoping
try:
    from tenant_manager import (
        TenantManager, Tenant, TenantStatus, TenantTier, TenantUsage,
        set_tenant_manager, get_tenant_manager, require_tenant_manager
    )
    TENANT_AVAILABLE = True
except ImportError:
    TENANT_AVAILABLE = False
    logging.warning("⚠️ tenant_manager.py not found - multi-tenant disabled")

try:
    from document_scopes import (
        DocumentScopeManager, DocumentScope, DocumentStatus as DocScopeStatus,
        ScopedDocument, DocumentAccessFilter,
        set_scope_manager, get_scope_manager, require_scope_manager
    )
    SCOPES_AVAILABLE = True
except ImportError:
    SCOPES_AVAILABLE = False
    logging.warning("⚠️ document_scopes.py not found - document scopes disabled")

# ✨ UNIFIED DATASET MANAGER - Upload once, use everywhere
try:
    from dataset_manager import DatasetManager, get_dataset_manager
    DATASET_MANAGER_AVAILABLE = True
except ImportError:
    DATASET_MANAGER_AVAILABLE = False
    DatasetManager = None
    get_dataset_manager = None
    logging.warning("⚠️ dataset_manager.py not found - unified datasets disabled")

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

# ✨ MULTI-TENANT MODELS

class TenantCreate(BaseModel):
    """Request to create a new tenant (client company)"""
    name: str = Field(..., min_length=2, max_length=100, description="Company name")
    domain: Optional[str] = Field(None, description="Primary email domain (e.g., acme.com)")
    tier: str = Field(default="starter", description="Subscription tier: starter, professional, enterprise")


class TenantResponse(BaseModel):
    """Tenant information response"""
    id: str
    name: str
    slug: str
    domain: Optional[str]
    status: str
    tier: str
    created_at: str
    qdrant_collection: str
    limits: Dict[str, int]


class TenantCreateResponse(BaseModel):
    """Response after creating a tenant - includes API key (shown only once!)"""
    tenant: TenantResponse
    api_key: str  # ⚠️ Only returned once at creation!
    message: str


class ScopedDocumentUpload(BaseModel):
    """Document upload request with scope"""
    scope: str = Field(default="personal", description="Document scope: 'company' or 'personal'")
    tags: Optional[List[str]] = Field(default=[], description="Document tags")
    description: Optional[str] = Field(default="", description="Document description")


class ScopedDocumentResponse(BaseModel):
    """Scoped document response"""
    id: str
    filename: str
    scope: str
    status: str
    file_size: int
    chunk_count: int
    created_at: str
    is_searchable: bool

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

        # ✨ PHASE 5: Configuration manager
        self.config_manager = None
        if CONFIG_AVAILABLE:
            try:
                self.config_manager = ConfigurationManager(config_path="data/system_config.json")
                set_config_manager(self.config_manager)  # Set global instance
                logger.info("✅ Configuration manager initialized: data/system_config.json")

                # Update RAG config with saved settings
                saved_config = self.config_manager.get_config()
                if saved_config.get('llm_model'):
                    config.openai_model = saved_config['llm_model']
                    logger.info(f"✅ LLM model set to: {config.openai_model}")
                if saved_config.get('temperature'):
                    config.temperature = saved_config['temperature']
                if saved_config.get('max_tokens'):
                    config.max_tokens = saved_config['max_tokens']
            except Exception as e:
                logger.error(f"❌ Configuration manager initialization failed: {e}")
                self.config_manager = None

        # ✨ PHASE 3: Document version manager
        self.version_manager = None
        if VERSIONS_AVAILABLE:
            try:
                self.version_manager = DocumentVersionManager(
                    db_path="data/document_versions.db",
                    storage_path="data/document_versions"
                )
                set_version_manager(self.version_manager)  # Set global instance
                logger.info("✅ Document version manager initialized")
            except Exception as e:
                logger.error(f"❌ Document version manager initialization failed: {e}")
                self.version_manager = None

        # ✨ PHASE 4: Document tag manager
        self.tag_manager = None
        if TAGS_AVAILABLE:
            try:
                self.tag_manager = DocumentTagManager(storage_path="data/document_tags.json")
                logger.info("✅ Document tag manager initialized")
            except Exception as e:
                logger.error(f"❌ Document tag manager initialization failed: {e}")
                self.tag_manager = None

        # ✨ PHASE 2: Authentication & Audit (Disabled for testing)
        self.auth_manager = None
        self.audit_logger = None
        # Note: Authentication is disabled for testing purposes

        # ✨ MULTI-TENANT: Tenant manager for client isolation
        self.tenant_manager = None
        if TENANT_AVAILABLE:
            try:
                self.tenant_manager = TenantManager(db_path="data/tenants.db")
                set_tenant_manager(self.tenant_manager)
                logger.info("✅ Tenant manager initialized: data/tenants.db")
            except Exception as e:
                logger.error(f"❌ Tenant manager initialization failed: {e}")
                self.tenant_manager = None

        # ✨ MULTI-TENANT: Document scope manager for company vs personal docs
        self.scope_manager = None
        if SCOPES_AVAILABLE:
            try:
                self.scope_manager = DocumentScopeManager(db_path="data/document_scopes.db")
                set_scope_manager(self.scope_manager)
                logger.info("✅ Document scope manager initialized")
            except Exception as e:
                logger.error(f"❌ Document scope manager initialization failed: {e}")
                self.scope_manager = None

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
            "citations_enabled": self.citation_builder is not None,
            # ✨ Multi-tenant status
            "multi_tenant_enabled": self.tenant_manager is not None,
            "document_scopes_enabled": self.scope_manager is not None,
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

    # Initialize Unified Dataset Manager
    if DATASET_MANAGER_AVAILABLE:
        dataset_mgr = get_dataset_manager()
        if app_state.rag_status.get('initialized', False):
            dataset_mgr.set_rag_system(app_state.rag_system)
            logger.info("📊 Dataset Manager connected to RAG system")
        app.state.dataset_manager = dataset_mgr

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
            "cost_tracking",          # ✨ Phase 1
            "multi_tenant",           # ✨ Multi-Tenant
            "document_scopes",        # ✨ Multi-Tenant
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
            # ✨ Multi-Tenant endpoints
            "tenants_create": "/api/tenants",
            "tenants_list": "/api/tenants",
            "tenant_get": "/api/tenants/{tenant_id}",
            "tenant_usage": "/api/tenants/{tenant_id}/usage",
            "validate_api_key": "/api/auth/validate-key",
            "documents_scoped": "/api/documents/scoped",
            "upload_scoped": "/api/documents/upload-scoped",
            # Frontend endpoints
            "workspace": "/workspace",
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

@app.get("/workspace", response_class=HTMLResponse)
@app.get("/workspace.html", response_class=HTMLResponse)
async def workspace():
    """Serve the Data Analysis Workspace"""
    possible_paths = [
        Path("../workspace.html"),
        Path("workspace.html"),
        Path("./workspace.html"),
        Path(__file__).parent / "workspace.html",
        Path(__file__).parent.parent / "workspace.html"
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Serving workspace.html from: {path}")
            return HTMLResponse(content=path.read_text(), status_code=200)

    logger.warning("workspace.html not found in any expected location")
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Workspace Not Found</title>
            <style>
                body { font-family: -apple-system, sans-serif; padding: 60px; text-align: center; background: #f5f5f5; }
                .container { background: white; padding: 40px; border-radius: 12px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #FF6E00; }
                p { color: #666; margin: 15px 0; }
                a { color: #FF6E00; text-decoration: none; font-weight: 600; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Data Analysis Workspace</h1>
                <p>workspace.html not found in project root.</p>
                <p>Download it from Claude and place it in the same folder as admin.html</p>
                <p><a href="/admin.html">← Back to Admin Dashboard</a></p>
            </div>
        </body>
        </html>
        """,
        status_code=404
    )


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
            },
            # ✨ Multi-tenant components
            "multi_tenant": {
                "status": "healthy" if status.get("multi_tenant_enabled") else "disabled"
            },
            "document_scopes": {
                "status": "healthy" if status.get("document_scopes_enabled") else "disabled"
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
# 🔐 AUTHENTICATION ENDPOINTS (PHASE 2) - DISABLED FOR TESTING
# =============================================================================
# Authentication endpoints are commented out for testing purposes
# Uncomment and configure properly when ready for production

# @app.post("/api/auth/register", response_model=TokenResponse)
# async def register(user_data: UserCreate):
#     """Register a new user account"""
#     if not app_state.auth_manager:
#         raise HTTPException(status_code=503, detail="Authentication not available")
#
#     try:
#         # Create user
#         user = app_state.auth_manager.create_user(user_data)
#
#         # Generate token
#         token = app_state.auth_manager.create_access_token(
#             user_id=user.id,
#             email=user.email,
#             role=user.role
#         )
#
#         return TokenResponse(
#             access_token=token,
#             token_type="bearer",
#             user=user
#         )
#     except Exception as e:
#         logger.error(f"Registration failed: {e}")
#         raise
#
#
# @app.post("/api/auth/login", response_model=TokenResponse)
# async def login(credentials: UserLogin, request: Request):
#     """Authenticate user and return access token"""
#     if not app_state.auth_manager:
#         raise HTTPException(status_code=503, detail="Authentication not available")
#
#     # Get client IP
#     client_ip = request.client.host if request.client else None
#
#     # Authenticate user
#     user_dict = app_state.auth_manager.authenticate_user(
#         email=credentials.email,
#         password=credentials.password
#     )
#
#     if not user_dict:
#         # Log failed login attempt
#         if app_state.audit_logger:
#             app_state.audit_logger.log_auth_event(
#                 action=app_state.audit_logger.ACTION_LOGIN_FAILED,
#                 user_email=credentials.email,
#                 ip_address=client_ip,
#                 status="failure",
#                 error_message="Incorrect email or password"
#             )
#
#         raise HTTPException(
#             status_code=401,
#             detail="Incorrect email or password"
#         )
#
#     # Log successful login
#     if app_state.audit_logger:
#         app_state.audit_logger.log_auth_event(
#             action=app_state.audit_logger.ACTION_LOGIN,
#             user_id=user_dict['id'],
#             user_email=user_dict['email'],
#             ip_address=client_ip,
#             status="success"
#         )
#
#     # Generate token
#     token = app_state.auth_manager.create_access_token(
#         user_id=user_dict['id'],
#         email=user_dict['email'],
#         role=user_dict['role']
#     )
#
#     # Create user response
#     user = UserResponse(
#         id=user_dict['id'],
#         email=user_dict['email'],
#         full_name=user_dict['full_name'],
#         role=user_dict['role'],
#         created_at=user_dict['created_at'],
#         last_login=user_dict['last_login']
#     )
#
#     return TokenResponse(
#         access_token=token,
#         token_type="bearer",
#         user=user
#     )
#
#
# @app.get("/api/auth/me", response_model=UserResponse)
# async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
#     """Get current authenticated user info"""
#     return current_user
#
#
# @app.get("/api/auth/users", response_model=List[UserResponse])
# async def list_users():
#     """List all users"""
#     if not app_state.auth_manager:
#         raise HTTPException(status_code=503, detail="Authentication not available")
#
#     return app_state.auth_manager.get_all_users()


# =============================================================================
# 📤 DOCUMENT UPLOAD
# =============================================================================

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...)
):
    """Enhanced document upload with Phase 1 analytics logging"""
    start_time = time.time()
    logger.info(f"📤 Upload request received: {file.filename}")
    
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
        
        # Save file temporarily for version storage
        import tempfile
        temp_file = None
        document_id = None

        try:
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            temp_file.write(content)
            temp_file.close()

            # Generate document ID from filename
            import hashlib
            document_id = hashlib.md5(file.filename.encode()).hexdigest()[:16]

            # Process document
            processed = await app_state.rag_system.process_document(file_path, content)

            if processed:
                status = await app_state.rag_system.get_system_status()
                chunks_created = status.get('total_chunks', 0)

                # ✨ PHASE 3: Create document version
                if app_state.version_manager:
                    try:
                        version = app_state.version_manager.create_version(
                            document_id=document_id,
                            file_path=temp_file.name,
                            file_name=file.filename,
                            file_size=file_size,
                            uploaded_by=None,  # TODO: Get from auth context
                            chunks_count=chunks_created,
                            metadata={
                                'file_extension': file_extension,
                                'original_name': file.filename
                            },
                            change_description="New upload"
                        )
                        logger.info(f"✅ Created version {version.version_number} for document {document_id}")
                    except Exception as e:
                        logger.warning(f"Failed to create document version: {e}")

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

                message = f"Document '{file.filename}' uploaded and successfully processed for RAG search!"
            else:
                message = f"Document '{file.filename}' uploaded but processing failed. Check server logs."
        finally:
            # Cleanup temp file
            if temp_file and Path(temp_file.name).exists():
                try:
                    Path(temp_file.name).unlink()
                except:
                    pass
        
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
# 📊 UNIFIED DATASET MANAGEMENT (Upload Once, Use Everywhere)
# =============================================================================

class DatasetUploadResponse(BaseModel):
    """Response for dataset upload"""
    success: bool
    dataset_id: str
    filename: str
    file_size: int
    file_type: str
    row_count: int = 0
    column_count: int = 0
    columns: List[Dict[str, Any]] = []
    vector_chunks: int = 0
    is_active: bool = False
    message: str = ""


class DatasetListResponse(BaseModel):
    """Response for listing datasets"""
    datasets: List[Dict[str, Any]]
    total: int
    active_dataset_id: Optional[str] = None


class SetActiveDatasetRequest(BaseModel):
    """Request to set active dataset"""
    dataset_id: str


@app.post("/api/datasets/upload", response_model=DatasetUploadResponse, tags=["Datasets"])
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a dataset for use across all BI Platform features.
    The dataset will be:
    - Parsed into a DataFrame (for Analysis, Statistics, Forecasting)
    - Indexed into vector store (for Chat/RAG queries)
    - Set as active dataset if first upload
    """
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()

    try:
        # Validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        supported_types = {'.pdf', '.docx', '.txt', '.xlsx', '.xls', '.csv', '.json'}
        extension = Path(file.filename).suffix.lower()

        if extension not in supported_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{extension}'. Supported: {supported_types}"
            )

        # Read file content
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File size exceeds 100MB limit")

        # Upload and process dataset
        metadata = await dataset_mgr.upload_dataset(content, file.filename)

        return DatasetUploadResponse(
            success=metadata.status.value == "ready",
            dataset_id=metadata.id,
            filename=metadata.original_filename,
            file_size=metadata.file_size,
            file_type=metadata.file_type,
            row_count=metadata.row_count,
            column_count=metadata.column_count,
            columns=[c.__dict__ for c in metadata.columns[:20]],  # Limit columns in response
            vector_chunks=metadata.vector_chunks,
            is_active=dataset_mgr._active_dataset_id == metadata.id,
            message=f"Dataset '{file.filename}' uploaded successfully. Ready for all features!"
            if metadata.status.value == "ready"
            else f"Upload failed: {metadata.error_message}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset upload error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Dataset upload failed: {str(e)}")


@app.get("/api/datasets", response_model=DatasetListResponse, tags=["Datasets"])
async def list_datasets():
    """List all uploaded datasets"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()
    datasets = dataset_mgr.list_datasets()

    return DatasetListResponse(
        datasets=datasets,
        total=len(datasets),
        active_dataset_id=dataset_mgr._active_dataset_id
    )


@app.get("/api/datasets/active", tags=["Datasets"])
async def get_active_dataset():
    """Get the currently active dataset"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()
    active = dataset_mgr.get_active_dataset()

    if not active:
        return JSONResponse(content={"active": False, "message": "No dataset uploaded yet"})

    return JSONResponse(content={
        "active": True,
        "dataset": active.to_dict(),
        "is_tabular": active.file_type in ['excel', 'csv', 'json', 'parquet']
    })


@app.post("/api/datasets/active", tags=["Datasets"])
async def set_active_dataset(request: SetActiveDatasetRequest):
    """Set the active dataset for all features"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()
    success = dataset_mgr.set_active_dataset(request.dataset_id)

    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")

    active = dataset_mgr.get_active_dataset()
    return JSONResponse(content={
        "success": True,
        "active_dataset": active.to_dict() if active else None
    })


@app.get("/api/datasets/{dataset_id}", tags=["Datasets"])
async def get_dataset(dataset_id: str):
    """Get details for a specific dataset"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()
    dataset = dataset_mgr.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return JSONResponse(content=dataset.to_dict())


@app.delete("/api/datasets/{dataset_id}", tags=["Datasets"])
async def delete_dataset(dataset_id: str):
    """Delete a dataset"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()
    success = dataset_mgr.delete_dataset(dataset_id)

    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return JSONResponse(content={"success": True, "deleted": dataset_id})


@app.get("/api/datasets/{dataset_id}/data", tags=["Datasets"])
async def get_dataset_data(
    dataset_id: str,
    offset: int = 0,
    limit: int = 100,
    columns: Optional[str] = None
):
    """Get the actual data from a dataset (paginated)"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()
    df = dataset_mgr.get_dataframe(dataset_id)

    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found or is not tabular")

    # Filter columns if specified
    if columns:
        col_list = [c.strip() for c in columns.split(",")]
        available_cols = [c for c in col_list if c in df.columns]
        if available_cols:
            df = df[available_cols]

    # Paginate
    total_rows = len(df)
    df_slice = df.iloc[offset:offset + limit]

    # Convert to JSON-serializable format
    data = df_slice.replace({np.nan: None}).to_dict(orient='records')

    return JSONResponse(content={
        "data": data,
        "total_rows": total_rows,
        "offset": offset,
        "limit": limit,
        "columns": list(df.columns)
    })


@app.get("/api/datasets/stats", tags=["Datasets"])
async def get_dataset_stats():
    """Get dataset manager statistics"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    dataset_mgr = get_dataset_manager()
    return JSONResponse(content=dataset_mgr.get_stats())


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
# ✨ PHASE 4: DOCUMENT TAGGING ENDPOINTS
# =============================================================================

@app.post("/api/documents/{doc_id}/tags")
async def add_document_tags(doc_id: str, tags: List[str]):
    """Add tags to a document"""
    if not app_state.tag_manager:
        raise HTTPException(status_code=503, detail="Tag manager not available")

    try:
        updated_tags = app_state.tag_manager.add_tags(doc_id, tags)
        return JSONResponse(content={"success": True, "doc_id": doc_id, "tags": updated_tags})
    except Exception as e:
        logger.error(f"Failed to add tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{doc_id}/tags/{tag}")
async def remove_document_tag(doc_id: str, tag: str):
    """Remove a tag from a document"""
    if not app_state.tag_manager:
        raise HTTPException(status_code=503, detail="Tag manager not available")

    try:
        updated_tags = app_state.tag_manager.remove_tag(doc_id, tag)
        return JSONResponse(content={"success": True, "doc_id": doc_id, "tags": updated_tags})
    except Exception as e:
        logger.error(f"Failed to remove tag: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{doc_id}/tags")
async def get_document_tags(doc_id: str):
    """Get all tags for a document"""
    if not app_state.tag_manager:
        raise HTTPException(status_code=503, detail="Tag manager not available")

    try:
        tags = app_state.tag_manager.get_tags(doc_id)
        return JSONResponse(content={"doc_id": doc_id, "tags": tags})
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tags")
async def get_all_tags():
    """Get all unique tags in the system"""
    if not app_state.tag_manager:
        raise HTTPException(status_code=503, detail="Tag manager not available")

    try:
        tags = app_state.tag_manager.get_all_tags()
        tag_stats = app_state.tag_manager.get_tag_stats()
        return JSONResponse(content={"tags": tags, "tag_stats": tag_stats, "total_tags": len(tags)})
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tags/autocomplete")
async def autocomplete_tags(prefix: str = "", limit: int = 10):
    """Get tag suggestions for autocomplete"""
    if not app_state.tag_manager:
        raise HTTPException(status_code=503, detail="Tag manager not available")

    try:
        suggestions = app_state.tag_manager.autocomplete_tags(prefix, limit)
        return JSONResponse(content={"prefix": prefix, "suggestions": suggestions})
    except Exception as e:
        logger.error(f"Failed to autocomplete tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tags/search")
async def search_by_tags(tags: str, match_all: bool = False):
    """Find documents that have specific tags"""
    if not app_state.tag_manager:
        raise HTTPException(status_code=503, detail="Tag manager not available")

    try:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        matching_docs = app_state.tag_manager.search_by_tags(tag_list, match_all)
        return JSONResponse(content={"tags": tag_list, "matching_documents": matching_docs, "count": len(matching_docs)})
    except Exception as e:
        logger.error(f"Failed to search by tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
                    
                    # Step 4: Stream the response - ASYNC OPENAI VERSION
                    full_response = ""

                    try:
                        # Create the streaming request - AsyncOpenAI returns a coroutine
                        stream = await app_state.rag_system.llm_manager.client.chat.completions.create(
                            model=app_state.rag_system.config.openai_model,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=app_state.rag_system.config.max_tokens,
                            temperature=app_state.rag_system.config.temperature,
                            stream=True
                        )

                        # Stream tokens to client - using async for since AsyncOpenAI stream is async
                        async for chunk in stream:
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
    offset: int = 0
):
    """Get conversation history from analytics database"""
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
    q: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Search conversations by keyword and/or date range

    Args:
        q: Search query (searches in both query and response text)
        start_date: Filter by start date (YYYY-MM-DD format)
        end_date: Filter by end date (YYYY-MM-DD format)
        limit: Maximum results to return (default 50)
        offset: Offset for pagination (default 0)

    Returns:
        Dictionary with conversations list, total count, and pagination info
    """
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")

    try:
        result = app_state.analytics_db.search_conversations(
            search_query=q,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Failed to search conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary():
    """Get analytics summary"""
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
    monthly_budget: float = 300.0
):
    """
    Get budget alert status
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
async def get_cost_breakdown(days: int = 30):
    """
    Get detailed cost breakdown by model and time period
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

@app.get("/api/analytics/trends")
async def get_analytics_trends(days: int = 30):
    """
    Get daily analytics trends for charting
    Returns time-series data for queries, costs, response times, and success rates
    """
    if not app_state.analytics_db:
        raise HTTPException(status_code=503, detail="Analytics not available")

    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        with app_state.analytics_db._get_connection() as conn:
            cursor = conn.cursor()

            # Get daily stats for the time period
            cursor.execute("""
                SELECT
                    date,
                    total_queries,
                    total_cost,
                    avg_response_time,
                    success_count,
                    failure_count,
                    rag_queries,
                    total_input_tokens,
                    total_output_tokens
                FROM daily_stats
                WHERE date >= date(?)
                ORDER BY date ASC
            """, (cutoff_date,))

            rows = cursor.fetchall()

            # Format data for charting
            dates = []
            queries = []
            costs = []
            response_times = []
            success_rates = []
            rag_usage = []

            for row in rows:
                dates.append(row[0])
                queries.append(row[1])
                costs.append(float(row[2]) if row[2] else 0)
                response_times.append(float(row[3]) if row[3] else 0)

                # Calculate success rate
                total = row[4] + row[5]
                success_rate = (row[4] / total * 100) if total > 0 else 0
                success_rates.append(round(success_rate, 2))

                # Calculate RAG usage percentage
                rag_percentage = (row[6] / row[1] * 100) if row[1] > 0 else 0
                rag_usage.append(round(rag_percentage, 2))

            return JSONResponse(content={
                "dates": dates,
                "queries": queries,
                "costs": costs,
                "response_times": response_times,
                "success_rates": success_rates,
                "rag_usage": rag_usage
            })

    except Exception as e:
        logger.error(f"Failed to get analytics trends: {e}")
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
# 🏢 MULTI-TENANT API ENDPOINTS
# =============================================================================

@app.post("/api/tenants", response_model=TenantCreateResponse, tags=["Multi-Tenant"])
async def create_tenant(request: TenantCreate):
    """
    Create a new tenant (client company).

    Returns tenant info AND the API key.
    ⚠️ IMPORTANT: The API key is only shown ONCE - save it securely!

    The API key is used for widget authentication.
    """
    if not app_state.tenant_manager:
        raise HTTPException(status_code=503, detail="Multi-tenant system not available")

    # Validate tier
    try:
        tier = TenantTier(request.tier) if request.tier else TenantTier.STARTER
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {request.tier}. Use: starter, professional, enterprise"
        )

    try:
        tenant, api_key = await app_state.tenant_manager.create_tenant(
            name=request.name,
            domain=request.domain.lower() if request.domain else None,
            tier=tier
        )

        logger.info(f"✅ Created tenant: {tenant.name} (ID: {tenant.id})")

        return TenantCreateResponse(
            tenant=TenantResponse(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                domain=tenant.domain,
                status=tenant.status.value,
                tier=tenant.tier.value,
                created_at=tenant.created_at,
                qdrant_collection=tenant.qdrant_collection_name,
                limits={
                    "max_users": tenant.max_users,
                    "max_documents": tenant.max_documents,
                    "max_storage_mb": tenant.max_storage_mb,
                    "max_queries_per_day": tenant.max_queries_per_day,
                }
            ),
            api_key=api_key,
            message="🎉 Tenant created! Save the API key now - it won't be shown again!"
        )
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tenants/{tenant_id}", tags=["Multi-Tenant"])
async def get_tenant(tenant_id: str):
    """Get tenant information by ID."""
    if not app_state.tenant_manager:
        raise HTTPException(status_code=503, detail="Multi-tenant system not available")

    tenant = await app_state.tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant.to_dict()


@app.get("/api/tenants", tags=["Multi-Tenant"])
async def list_tenants(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all tenants with optional filtering.

    In production, this should be restricted to super admins only.
    """
    if not app_state.tenant_manager:
        raise HTTPException(status_code=503, detail="Multi-tenant system not available")

    try:
        status_enum = TenantStatus(status) if status else None
        tier_enum = TenantTier(tier) if tier else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    tenants = await app_state.tenant_manager.list_tenants(
        status=status_enum,
        tier=tier_enum,
        limit=limit,
        offset=offset
    )

    return {
        "tenants": [t.to_dict() for t in tenants],
        "count": len(tenants),
        "limit": limit,
        "offset": offset
    }


@app.get("/api/tenants/{tenant_id}/usage", tags=["Multi-Tenant"])
async def get_tenant_usage(tenant_id: str):
    """Get current resource usage for a tenant."""
    if not app_state.tenant_manager:
        raise HTTPException(status_code=503, detail="Multi-tenant system not available")

    tenant = await app_state.tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    usage = await app_state.tenant_manager.get_usage(tenant_id)
    if not usage:
        raise HTTPException(status_code=404, detail="Usage data not found")

    return {
        "tenant_id": tenant_id,
        "user_count": usage.user_count,
        "document_count": usage.document_count,
        "storage_mb": round(usage.storage_mb, 2),
        "queries_today": usage.queries_today,
        "queries_this_month": usage.queries_this_month,
        "limits": {
            "max_users": tenant.max_users,
            "max_documents": tenant.max_documents,
            "max_storage_mb": tenant.max_storage_mb,
            "max_queries_per_day": tenant.max_queries_per_day,
        }
    }


@app.post("/api/tenants/{tenant_id}/rotate-key", tags=["Multi-Tenant"])
async def rotate_tenant_api_key(tenant_id: str):
    """
    Rotate the API key for a tenant.

    ⚠️ The new key is only shown ONCE!
    The old key stops working immediately.
    """
    if not app_state.tenant_manager:
        raise HTTPException(status_code=503, detail="Multi-tenant system not available")

    new_key = await app_state.tenant_manager.rotate_api_key(tenant_id)
    if not new_key:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "message": "✅ API key rotated successfully",
        "api_key": new_key,
        "warning": "⚠️ Save this key now - it won't be shown again!"
    }


@app.post("/api/auth/validate-key", tags=["Multi-Tenant"])
async def validate_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """
    Validate an API key and return tenant info.

    Used by the embeddable widget to authenticate.
    Send the API key in the X-API-Key header.
    """
    if not app_state.tenant_manager:
        raise HTTPException(status_code=503, detail="Multi-tenant system not available")

    tenant = await app_state.tenant_manager.validate_api_key(api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant account is suspended")

    return {
        "valid": True,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "tier": tenant.tier.value,
        "qdrant_collection": tenant.qdrant_collection_name
    }


# =============================================================================
# 📄 SCOPED DOCUMENT ENDPOINTS
# =============================================================================

@app.post("/api/documents/upload-scoped", tags=["Documents"])
async def upload_scoped_document(
    file: UploadFile = File(...),
    scope: str = "personal",
    tags: str = "",
    description: str = "",
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Upload a document with scope (company or personal).

    Required Headers:
    - X-Tenant-ID: The tenant uploading the document
    - X-User-ID: The user uploading (required for personal scope)

    Scope Rules:
    - 'company': Visible to ALL users in the tenant (admin upload only)
    - 'personal': Visible only to the uploading user
    """
    if not app_state.scope_manager:
        raise HTTPException(status_code=503, detail="Document scopes not available")

    # Validate scope
    try:
        doc_scope = DocumentScope(scope)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Scope must be 'company' or 'personal'"
        )

    # Personal docs require user_id
    if doc_scope == DocumentScope.PERSONAL and not user_id:
        raise HTTPException(
            status_code=400,
            detail="X-User-ID header required for personal documents"
        )

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    try:
        # Read file
        content = await file.read()
        file_size = len(content)

        # Register document in scope system
        scoped_doc = await app_state.scope_manager.register_document(
            tenant_id=tenant_id,
            user_id=user_id,
            filename=file.filename,
            scope=doc_scope,
            file_size=file_size,
            file_type=file.content_type or "",
            tags=tag_list,
            description=description
        )

        logger.info(f"📄 Registered scoped document: {file.filename} (scope={scope})")

        # TODO: Process with your existing RAG system
        # When storing in Qdrant, include these metadata fields:
        # {
        #     "doc_id": scoped_doc.id,
        #     "tenant_id": scoped_doc.tenant_id,
        #     "user_id": scoped_doc.user_id,
        #     "scope": scoped_doc.scope.value,
        #     "filename": scoped_doc.filename
        # }

        return {
            "message": "✅ Document uploaded successfully",
            "document": scoped_doc.to_dict(),
            "next_step": "Document will be processed and indexed"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/scoped", tags=["Documents"])
async def list_scoped_documents(
    scope: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user_id: str = Header(None, alias="X-User-ID"),
    limit: int = 50,
    offset: int = 0
):
    """
    List documents accessible to the current user.

    Access Control:
    - Company documents are visible to ALL users in the tenant
    - Personal documents are visible ONLY to their owner

    Required Headers:
    - X-Tenant-ID: Tenant context
    - X-User-ID: User making request (for access control)
    """
    if not app_state.scope_manager:
        raise HTTPException(status_code=503, detail="Document scopes not available")

    # Parse filters
    scope_enum = None
    if scope:
        try:
            scope_enum = DocumentScope(scope)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scope")

    status_enum = None
    if status:
        try:
            status_enum = DocScopeStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    docs = await app_state.scope_manager.get_accessible_documents(
        tenant_id=tenant_id,
        user_id=user_id or "",
        is_admin=False,  # TODO: Check from auth system
        scope=scope_enum,
        status=status_enum,
        limit=limit,
        offset=offset
    )

    return {
        "documents": [d.to_dict() for d in docs],
        "count": len(docs),
        "limit": limit,
        "offset": offset
    }


@app.delete("/api/documents/scoped/{doc_id}", tags=["Documents"])
async def delete_scoped_document(
    doc_id: str,
    hard_delete: bool = False,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user_id: str = Header(..., alias="X-User-ID")
):
    """
    Delete a scoped document.

    Access Control:
    - Users can only delete their own personal documents
    - Admins can delete any document in their tenant
    """
    if not app_state.scope_manager:
        raise HTTPException(status_code=503, detail="Document scopes not available")

    # Get document to check access
    doc = await app_state.scope_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check tenant match
    if doc.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check access (for now, only owner can delete personal docs)
    if doc.is_personal_doc and doc.user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's document")

    success = await app_state.scope_manager.delete_document(doc_id, hard_delete)

    if success:
        # TODO: Also delete from Qdrant and file system
        return {"message": "✅ Document deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete document")

# =============================================================================
# ✨ PHASE 5: CONFIGURATION API ENDPOINTS
# =============================================================================

@app.get("/api/config")
async def get_configuration():
    """Get current system configuration"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    try:
        config = app_state.config_manager.get_config()
        return JSONResponse(content=config)
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/config")
async def update_configuration(updates: Dict[str, Any]):
    """Update system configuration"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    try:
        # Update configuration
        updated_config = app_state.config_manager.update_config(updates)

        # If LLM model was updated, update the RAG system
        if 'llm_model' in updates:
            app_state.rag_system.config.openai_model = updates['llm_model']
            logger.info(f"✅ Updated RAG system LLM model to: {updates['llm_model']}")

        # If temperature or max_tokens were updated, update RAG system
        if 'temperature' in updates:
            app_state.rag_system.config.temperature = updates['temperature']
        if 'max_tokens' in updates:
            app_state.rag_system.config.max_tokens = updates['max_tokens']

        return JSONResponse(content=updated_config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/models")
async def get_available_models():
    """Get list of available LLM models"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    try:
        models = app_state.config_manager.get_available_models()
        current_model = app_state.config_manager.get_current_model()
        return JSONResponse(content={
            "models": models,
            "current_model": current_model
        })
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/model")
async def set_llm_model(model_data: Dict[str, str]):
    """Set LLM model"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    model_id = model_data.get('model_id')
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    try:
        updated_config = app_state.config_manager.set_model(model_id)

        # Update RAG system
        app_state.rag_system.config.openai_model = model_id
        logger.info(f"✅ Updated LLM model to: {model_id}")

        return JSONResponse(content=updated_config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/confidence-threshold")
async def set_confidence_threshold(threshold_data: Dict[str, float]):
    """Set confidence threshold"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    threshold = threshold_data.get('threshold')
    if threshold is None:
        raise HTTPException(status_code=400, detail="threshold is required")

    try:
        updated_config = app_state.config_manager.set_confidence_threshold(threshold)
        return JSONResponse(content=updated_config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set confidence threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/prompt-template")
async def get_prompt_template():
    """Get system prompt template"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    try:
        template = app_state.config_manager.get_prompt_template()
        return JSONResponse(content={"template": template})
    except Exception as e:
        logger.error(f"Failed to get prompt template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/prompt-template")
async def set_prompt_template(template_data: Dict[str, str]):
    """Set system prompt template"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    template = template_data.get('template')
    if not template:
        raise HTTPException(status_code=400, detail="template is required")

    try:
        updated_config = app_state.config_manager.set_prompt_template(template)
        return JSONResponse(content=updated_config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set prompt template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/reset")
async def reset_configuration():
    """Reset configuration to defaults"""
    if not app_state.config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not available")

    try:
        updated_config = app_state.config_manager.reset_to_defaults()

        # Update RAG system with defaults
        app_state.rag_system.config.openai_model = updated_config['llm_model']
        app_state.rag_system.config.temperature = updated_config['temperature']
        app_state.rag_system.config.max_tokens = updated_config['max_tokens']

        logger.info("✅ Configuration reset to defaults")
        return JSONResponse(content=updated_config)
    except Exception as e:
        logger.error(f"Failed to reset configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ✨ PHASE 3: DOCUMENT VERSION CONTROL API ENDPOINTS
# =============================================================================

@app.get("/api/documents/{document_id}/versions")
async def get_document_versions(document_id: str):
    """Get all versions of a specific document"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        versions = app_state.version_manager.get_versions(document_id)
        return JSONResponse(content={
            "document_id": document_id,
            "versions": [asdict(v) for v in versions],
            "total_versions": len(versions)
        })
    except Exception as e:
        logger.error(f"Failed to get versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/versions/{version_number}")
async def get_document_version(document_id: str, version_number: int):
    """Get specific version of a document"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        version = app_state.version_manager.get_version(document_id, version_number)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {version_number} not found")

        return JSONResponse(content=asdict(version))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/{document_id}/versions/{version_number}/revert")
async def revert_to_version(document_id: str, version_number: int):
    """Revert document to a specific version"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        # Revert to version (creates new version from old one)
        new_version = app_state.version_manager.revert_to_version(
            document_id=document_id,
            version_number=version_number,
            reverted_by=None  # TODO: Get from auth context
        )

        # TODO: Re-process document with RAG system to update embeddings
        logger.info(f"✅ Reverted document {document_id} to version {version_number}")

        return JSONResponse(content={
            "message": f"Successfully reverted to version {version_number}",
            "new_version": asdict(new_version)
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to revert version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}/versions/{version_number}")
async def delete_document_version(document_id: str, version_number: int):
    """Delete a specific version (cannot delete current version)"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        success = app_state.version_manager.delete_version(document_id, version_number)
        if success:
            return JSONResponse(content={
                "message": f"Version {version_number} deleted successfully"
            })
        else:
            raise HTTPException(status_code=404, detail=f"Version {version_number} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/with-versions")
async def get_all_documents_with_versions():
    """Get all documents with their version information"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        documents = app_state.version_manager.get_all_documents_with_versions()
        return JSONResponse(content={
            "documents": documents,
            "total": len(documents)
        })
    except Exception as e:
        logger.error(f"Failed to get documents with versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/versions/current")
async def get_current_version(document_id: str):
    """Get current version of a document"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        version = app_state.version_manager.get_current_version(document_id)
        if not version:
            raise HTTPException(status_code=404, detail="Document not found")

        return JSONResponse(content=asdict(version))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/preview")
async def preview_document(document_id: str, version: Optional[int] = None):
    """Serve document file for preview (current version or specific version)"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        # Get version to preview
        if version is not None:
            doc_version = app_state.version_manager.get_version(document_id, version)
        else:
            doc_version = app_state.version_manager.get_current_version(document_id)

        if not doc_version:
            raise HTTPException(status_code=404, detail="Document or version not found")

        # Serve file
        file_path = Path(doc_version.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found on disk")

        # Determine media type
        media_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel'
        }

        file_ext = file_path.suffix.lower()
        media_type = media_types.get(file_ext, 'application/octet-stream')

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=doc_version.file_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve document for preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/download")
async def download_document(document_id: str, version: Optional[int] = None):
    """Download document file (current version or specific version)"""
    if not app_state.version_manager:
        raise HTTPException(status_code=503, detail="Version control not available")

    try:
        # Get version to download
        if version is not None:
            doc_version = app_state.version_manager.get_version(document_id, version)
        else:
            doc_version = app_state.version_manager.get_current_version(document_id)

        if not doc_version:
            raise HTTPException(status_code=404, detail="Document or version not found")

        # Serve file for download
        file_path = Path(doc_version.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found on disk")

        return FileResponse(
            path=str(file_path),
            filename=doc_version.file_name,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve document for download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 📊 SESSION-BASED DATA ANALYSIS API (Tier 1 BI Features)
# =============================================================================

# Global session storage for data analysis
_analysis_sessions: Dict[str, Any] = {}
_session_orchestrators: Dict[str, Any] = {}

class SessionCreateRequest(BaseModel):
    user_id: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    created_at: str
    data_loaded: bool
    file_name: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None

class ForecastRequest(BaseModel):
    column: str
    periods: int = 30
    method: str = "auto"

class StatisticsRequest(BaseModel):
    test_type: str
    columns: List[str]
    options: Optional[Dict[str, Any]] = None

class ChartRequest(BaseModel):
    chart_type: str
    columns: List[str]
    options: Optional[Dict[str, Any]] = None

class ChartRecommendRequest(BaseModel):
    columns: Optional[List[str]] = None

class QueryRequest(BaseModel):
    query: str

class ExportRequest(BaseModel):
    format: str = "csv"


@app.post("/api/sessions", response_model=SessionResponse, tags=["Data Analysis"])
async def create_analysis_session(request: SessionCreateRequest = None):
    """Create a new data analysis session - auto-loads active dataset if available"""
    if not DATA_ANALYST_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data analyst module not available")

    try:
        session_id = str(uuid.uuid4())
        orchestrator = AnalystOrchestrator()
        session = orchestrator.create_session()

        _analysis_sessions[session_id] = {
            "id": session_id,
            "orchestrator_session_id": session.id,
            "created_at": datetime.now().isoformat(),
            "data_loaded": False,
            "file_name": None,
            "row_count": None,
            "column_count": None,
            "data": None,
            "profile": None,
        }
        _session_orchestrators[session_id] = orchestrator

        # Auto-load active dataset from DatasetManager if available
        if DATASET_MANAGER_AVAILABLE:
            dataset_mgr = get_dataset_manager()
            active_df = dataset_mgr.get_active_dataframe()
            active_meta = dataset_mgr.get_active_dataset()

            if active_df is not None and active_meta is not None:
                _analysis_sessions[session_id]["data"] = active_df
                _analysis_sessions[session_id]["data_loaded"] = True
                _analysis_sessions[session_id]["file_name"] = active_meta.original_filename
                _analysis_sessions[session_id]["row_count"] = len(active_df)
                _analysis_sessions[session_id]["column_count"] = len(active_df.columns)
                _analysis_sessions[session_id]["dataset_id"] = active_meta.id
                logger.info(f"📊 Auto-loaded active dataset '{active_meta.original_filename}' into session {session_id}")

        logger.info(f"📊 Created analysis session: {session_id}")

        return SessionResponse(
            id=session_id,
            created_at=_analysis_sessions[session_id]["created_at"],
            data_loaded=_analysis_sessions[session_id]["data_loaded"],
            file_name=_analysis_sessions[session_id].get("file_name"),
            row_count=_analysis_sessions[session_id].get("row_count"),
            column_count=_analysis_sessions[session_id].get("column_count"),
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}", response_model=SessionResponse, tags=["Data Analysis"])
async def get_analysis_session(session_id: str):
    """Get session information"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    return SessionResponse(
        id=session["id"],
        created_at=session["created_at"],
        data_loaded=session["data_loaded"],
        file_name=session.get("file_name"),
        row_count=session.get("row_count"),
        column_count=session.get("column_count"),
    )


@app.post("/api/sessions/{session_id}/load-active-dataset", tags=["Data Analysis"])
async def load_active_dataset_to_session(session_id: str):
    """Load the active dataset from DatasetManager into the session"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dataset manager not available")

    try:
        dataset_mgr = get_dataset_manager()
        active_df = dataset_mgr.get_active_dataframe()
        active_meta = dataset_mgr.get_active_dataset()

        if active_df is None or active_meta is None:
            raise HTTPException(status_code=404, detail="No active dataset available. Please upload a dataset first.")

        # Update session with active dataset
        _analysis_sessions[session_id]["data"] = active_df
        _analysis_sessions[session_id]["data_loaded"] = True
        _analysis_sessions[session_id]["file_name"] = active_meta.original_filename
        _analysis_sessions[session_id]["row_count"] = len(active_df)
        _analysis_sessions[session_id]["column_count"] = len(active_df.columns)
        _analysis_sessions[session_id]["dataset_id"] = active_meta.id

        logger.info(f"📊 Loaded active dataset '{active_meta.original_filename}' into session {session_id}")

        return JSONResponse(content={
            "success": True,
            "message": f"Loaded dataset '{active_meta.original_filename}'",
            "file_name": active_meta.original_filename,
            "rows": len(active_df),
            "columns": len(active_df.columns),
            "dataset_id": active_meta.id
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load active dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/upload", tags=["Data Analysis"])
async def upload_session_file(session_id: str, file: UploadFile = File(...)):
    """Upload a file to the analysis session - also adds to unified DatasetManager"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if not DATA_ANALYST_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data analyst module not available")

    try:
        import pandas as pd
        import io

        # Read file content
        content = await file.read()
        file_ext = file.filename.lower().split('.')[-1] if file.filename else 'csv'

        # Parse based on file type
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(content))
        elif file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(content))
        elif file_ext == 'json':
            df = pd.read_json(io.BytesIO(content))
        else:
            # Try CSV as default
            df = pd.read_csv(io.BytesIO(content))

        # Update session
        _analysis_sessions[session_id]["data"] = df
        _analysis_sessions[session_id]["data_loaded"] = True
        _analysis_sessions[session_id]["file_name"] = file.filename
        _analysis_sessions[session_id]["row_count"] = len(df)
        _analysis_sessions[session_id]["column_count"] = len(df.columns)

        # Also add to DatasetManager for cross-feature access
        dataset_id = None
        if DATASET_MANAGER_AVAILABLE:
            try:
                dataset_mgr = get_dataset_manager()
                metadata = await dataset_mgr.upload_dataset(content, file.filename)
                dataset_id = metadata.id
                _analysis_sessions[session_id]["dataset_id"] = dataset_id
                logger.info(f"📊 Also added to DatasetManager: {dataset_id}")
            except Exception as dm_err:
                logger.warning(f"Failed to add to DatasetManager: {dm_err}")

        logger.info(f"📊 Uploaded file to session {session_id}: {file.filename} ({len(df)} rows)")

        return {
            "success": True,
            "file_name": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dataset_id": dataset_id
        }
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/profile", tags=["Data Analysis"])
async def get_session_profile(session_id: str):
    """Get data profile for the session"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        df = session["data"]
        profiler = DataProfiler()
        profile = profiler.profile(df)

        logger.info(f"DEBUG: Profile created with {len(profile.columns)} columns")

        # Convert to dict for JSON response
        columns = []
        for col in profile.columns:
            logger.info(f"DEBUG: Processing column {col.name}, stats type: {type(col.statistics) if col.statistics else None}")
            # Get missing info from quality
            missing_count = col.quality.missing_count if hasattr(col, 'quality') else 0
            missing_pct = col.quality.missing_percent if hasattr(col, 'quality') else 0.0

            col_dict = {
                "name": col.name,
                "type": str(col.dtype.value) if hasattr(col.dtype, 'value') else str(col.dtype),
                "semantic_type": col.dtype.value if hasattr(col.dtype, 'value') else "unknown",
                "missing_count": int(missing_count),
                "missing_percentage": float(missing_pct),
                "unique_count": int(col.unique_count) if hasattr(col, 'unique_count') else 0,
                "sample_values": [str(v) for v in col.sample_values[:5]] if hasattr(col, 'sample_values') else [],
            }

            # Add statistics for numeric columns (ColumnStatistics is a dataclass, not dict)
            if hasattr(col, 'statistics') and col.statistics:
                stats = col.statistics
                col_dict["statistics"] = {
                    "min": float(stats.min) if stats.min is not None else None,
                    "max": float(stats.max) if stats.max is not None else None,
                    "mean": float(stats.mean) if stats.mean is not None else None,
                    "median": float(stats.median) if stats.median is not None else None,
                    "std": float(stats.std) if stats.std is not None else None,
                }
            columns.append(col_dict)

        # Get quality info
        quality_score = 0.8
        quality_level = "good"
        if hasattr(profile, 'quality') and profile.quality:
            quality_score = profile.quality.quality_score / 100.0 if profile.quality.quality_score else 0.8
            quality_level = profile.quality.quality_level.value if hasattr(profile.quality.quality_level, 'value') else "good"

        return {
            "columns": columns,
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "summary": profile.summary_text if hasattr(profile, 'summary_text') else f"Dataset with {profile.row_count} rows and {profile.column_count} columns"
        }
    except Exception as e:
        logger.error(f"Failed to profile data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/preview", tags=["Data Analysis"])
async def get_session_preview(session_id: str, limit: int = 100):
    """Get data preview (first N rows)"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        df = session["data"]
        preview_df = df.head(limit)

        return {
            "columns": df.columns.tolist(),
            "data": preview_df.values.tolist(),
            "total_rows": len(df)
        }
    except Exception as e:
        logger.error(f"Failed to get preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/forecast", tags=["Data Analysis"])
async def run_forecast(session_id: str, request: ForecastRequest):
    """Run forecast on a column"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        df = session["data"]

        if request.column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{request.column}' not found")

        engine = StatisticalEngine()
        # Get the column data as a pandas Series for forecasting
        column_data = df[request.column].dropna()
        result = engine.forecast(
            column_data,
            periods=request.periods,
            method=request.method if request.method != "auto" else None
        )

        # Helper to convert array-like to list
        def to_list(val):
            if val is None:
                return []
            if hasattr(val, 'tolist'):
                return val.tolist()
            if isinstance(val, list):
                return val
            return list(val) if hasattr(val, '__iter__') else []

        return {
            "method": result.method if hasattr(result, 'method') else request.method,
            "forecast_values": to_list(result.forecast if hasattr(result, 'forecast') else None),
            "forecast_dates": [],  # Would need date column for this
            "confidence_lower": to_list(result.lower_bound if hasattr(result, 'lower_bound') else None),
            "confidence_upper": to_list(result.upper_bound if hasattr(result, 'upper_bound') else None),
            "confidence_level": 0.95,
            "metrics": {
                "mae": float(result.mae) if hasattr(result, 'mae') and result.mae is not None else 0,
                "rmse": float(result.rmse) if hasattr(result, 'rmse') and result.rmse is not None else 0,
                "mape": float(result.mape) if hasattr(result, 'mape') and result.mape is not None else 0,
            },
            "trend_direction": result.trend if hasattr(result, 'trend') else "stable",
            "seasonality_detected": result.seasonality if hasattr(result, 'seasonality') else False,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/statistics", tags=["Data Analysis"])
async def run_statistics(session_id: str, request: StatisticsRequest):
    """Run statistical analysis"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        df = session["data"]
        engine = StatisticalEngine()

        # Validate columns exist
        for col in request.columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Column '{col}' not found")

        # Run appropriate statistical test
        test_type = request.test_type.lower()

        if test_type == "t_test" or test_type == "ttest":
            if len(request.columns) < 2:
                raise HTTPException(status_code=400, detail="T-test requires 2 columns")
            result = engine.t_test(df[request.columns[0]], df[request.columns[1]])
        elif test_type == "correlation":
            result = engine.correlation(df[request.columns])
        elif test_type == "chi_square" or test_type == "chi2":
            if len(request.columns) < 2:
                raise HTTPException(status_code=400, detail="Chi-square test requires 2 columns")
            result = engine.chi_square_test(df[request.columns[0]], df[request.columns[1]])
        elif test_type == "anova":
            result = engine.anova(df, request.columns[0], request.columns[1] if len(request.columns) > 1 else None)
        elif test_type == "regression":
            if len(request.columns) < 2:
                raise HTTPException(status_code=400, detail="Regression requires at least 2 columns")
            result = engine.linear_regression(df[request.columns[:-1]], df[request.columns[-1]])
        else:
            # Default to descriptive statistics
            result = engine.describe(df[request.columns])

        # Format response
        return {
            "test_type": request.test_type,
            "test_statistic": float(result.statistic) if hasattr(result, 'statistic') else 0,
            "p_value": float(result.p_value) if hasattr(result, 'p_value') else 0,
            "significant": bool(result.significant) if hasattr(result, 'significant') else False,
            "interpretation": result.interpretation if hasattr(result, 'interpretation') else "Analysis complete",
            "effect_size": float(result.effect_size) if hasattr(result, 'effect_size') else None,
            "confidence_interval": list(result.confidence_interval) if hasattr(result, 'confidence_interval') else None,
            "additional_info": result.details if hasattr(result, 'details') else {},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/insights", tags=["Data Analysis"])
async def get_insights(session_id: str):
    """Get AI-generated insights"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        df = session["data"]
        generator = InsightGenerator()
        result = generator.generate_insights(df)

        # Extract insights list from InsightCollection
        if hasattr(result, 'insights'):
            insights_list = result.insights
        elif isinstance(result, list):
            insights_list = result
        else:
            insights_list = [result]

        formatted_insights = []
        for insight in insights_list:
            # Get enum values safely
            insight_type = insight.insight_type.value if hasattr(insight.insight_type, 'value') else str(insight.insight_type) if hasattr(insight, 'insight_type') else "general"
            priority = insight.priority.value if hasattr(insight.priority, 'value') else str(insight.priority) if hasattr(insight, 'priority') else "medium"
            category = insight.category.value if hasattr(insight.category, 'value') else str(insight.category) if hasattr(insight, 'category') else "general"

            formatted_insights.append({
                "id": insight.id if hasattr(insight, 'id') else None,
                "type": insight_type,
                "priority": priority,
                "category": category,
                "text": insight.text if hasattr(insight, 'text') else str(insight),
                "metric_name": insight.metric_name if hasattr(insight, 'metric_name') else None,
                "metric_value": float(insight.metric_value) if hasattr(insight, 'metric_value') and insight.metric_value is not None else None,
                "change_value": float(insight.change_value) if hasattr(insight, 'change_value') and insight.change_value is not None else None,
                "change_percent": float(insight.change_percent) if hasattr(insight, 'change_percent') and insight.change_percent is not None else None,
                "confidence": float(insight.confidence) if hasattr(insight, 'confidence') else 0.8,
                "source": insight.source if hasattr(insight, 'source') else "rule-based",
            })

        return {
            "insights": formatted_insights,
            "total_count": result.total_count if hasattr(result, 'total_count') else len(formatted_insights),
            "critical_count": result.critical_count if hasattr(result, 'critical_count') else 0,
            "high_count": result.high_count if hasattr(result, 'high_count') else 0,
        }
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/recommend-charts", tags=["Data Analysis"])
async def recommend_charts(session_id: str, request: ChartRecommendRequest = None):
    """Get chart recommendations"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        df = session["data"]
        recommender = ChartRecommender()

        columns = request.columns if request and request.columns else None
        if columns:
            for col in columns:
                if col not in df.columns:
                    raise HTTPException(status_code=400, detail=f"Column '{col}' not found")
            recommendations = recommender.recommend(df[columns])
        else:
            recommendations = recommender.recommend(df)

        return [
            {
                "chart_type": rec.chart_type if hasattr(rec, 'chart_type') else str(rec),
                "score": float(rec.score) if hasattr(rec, 'score') else 0.8,
                "explanation": rec.explanation if hasattr(rec, 'explanation') else "Recommended chart type"
            }
            for rec in (recommendations if isinstance(recommendations, list) else [recommendations])
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to recommend charts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/chart", tags=["Data Analysis"])
async def generate_chart(session_id: str, request: ChartRequest):
    """Generate a chart"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        df = session["data"]

        # Validate columns
        for col in request.columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Column '{col}' not found")

        generator = ChartGenerator()
        chart = generator.generate(
            df,
            chart_type=request.chart_type,
            columns=request.columns,
            **(request.options or {})
        )

        return {
            "chart_data": chart.data if hasattr(chart, 'data') else chart,
            "chart_config": chart.layout if hasattr(chart, 'layout') else {}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/query", tags=["Data Analysis"])
async def query_session(session_id: str, request: QueryRequest):
    """Natural language query on session data"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        orchestrator = _session_orchestrators.get(session_id)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Session orchestrator not found")

        result = orchestrator.query(session["orchestrator_session_id"], request.query)

        return {
            "response": result.response if hasattr(result, 'response') else str(result),
            "chart": result.chart if hasattr(result, 'chart') else None,
            "table": result.table if hasattr(result, 'table') else None,
            "insights": result.insights if hasattr(result, 'insights') else [],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/export", tags=["Data Analysis"])
async def export_session_data(session_id: str, request: ExportRequest):
    """Export session data to various formats"""
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _analysis_sessions[session_id]
    if not session["data_loaded"] or session["data"] is None:
        raise HTTPException(status_code=400, detail="No data loaded in session")

    try:
        import io
        df = session["data"]

        if request.format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            content = output.getvalue()
            media_type = "text/csv"
            filename = "export.csv"
        elif request.format == "json":
            content = df.to_json(orient="records")
            media_type = "application/json"
            filename = "export.json"
        elif request.format == "excel":
            output = io.BytesIO()
            df.to_excel(output, index=False)
            content = output.getvalue()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "export.xlsx"
            return Response(content=content, media_type=media_type, headers={
                "Content-Disposition": f"attachment; filename={filename}"
            })
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        return Response(content=content, media_type=media_type, headers={
            "Content-Disposition": f"attachment; filename={filename}"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
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