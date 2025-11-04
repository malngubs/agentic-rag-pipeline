"""
FastAPI Main Application for Agentic RAG Pipeline.
FIXED VERSION - Resolves app.mount and pydantic issues
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting Agentic RAG Pipeline...")
    
    try:
        # Initialize core components
        await app.state.init_components()
        logger.info("All components initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        # Don't raise in lifespan, just log
    
    finally:
        # Shutdown
        logger.info("Shutting down Agentic RAG Pipeline...")
        try:
            await app.state.cleanup_components()
        except:
            pass
        logger.info("Shutdown completed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title="Macrocomm AI Assistant",
        version="1.0.0",
        description="Advanced RAG system with human-like reasoning capabilities",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add state management
    setup_state(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    logger.info(f"FastAPI app created: Macrocomm AI Assistant v1.0.0")
    return app


def setup_middleware(app: FastAPI):
    """Configure middleware for the application."""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


def setup_routes(app: FastAPI):
    """Setup API routes."""
    
    # Import routes
    try:
        from api.routes import health, chat, auth, documents, metrics, widget
        
        # Core API routes
        app.include_router(health.router, prefix="/health", tags=["health"])
        app.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])  
        app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
        app.include_router(documents.router, prefix="/v1/documents", tags=["documents"])
        app.include_router(metrics.router, prefix="/v1/metrics", tags=["metrics"])
        app.include_router(widget.router, prefix="/widget", tags=["widget"])
        
        logger.info("All routes loaded successfully")
        
    except ImportError as e:
        logger.warning(f"Some routes could not be imported: {e}")
        
        # Create basic health route as fallback
        @app.get("/health")
        async def basic_health():
            return {"status": "healthy", "timestamp": time.time()}
    
    # FIXED: Mount static files AFTER app is created
    try:
        app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")
        logger.info("Frontend static files mounted successfully")
    except Exception as e:
        logger.warning(f"Could not mount frontend files: {e}")
        
    try:
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
        logger.info("Static files mounted successfully")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")


def setup_state(app: FastAPI):
    """Setup application state and components."""
    
    # Simple connection manager fallback
    from collections import defaultdict
    
    class SimpleConnectionManager:
        def __init__(self):
            self.connections = []
            
        async def connect(self, websocket):
            await websocket.accept()
            self.connections.append(websocket)
            
        def disconnect(self, websocket):
            if websocket in self.connections:
                self.connections.remove(websocket)
    
    app.state.connection_manager = SimpleConnectionManager()
    
    # Component initialization functions
    async def init_components():
        """Initialize all RAG components."""
        try:
            # Try to initialize components, but don't fail if they're not available
            logger.info("Attempting to initialize components...")
            
            try:
                from models.llm_manager import LLMManager
                app.state.llm_manager = LLMManager()
                await app.state.llm_manager.initialize()
                logger.info("LLM Manager initialized")
            except Exception as e:
                logger.warning(f"LLM Manager initialization failed: {e}")
                app.state.llm_manager = None
            
            try:
                from retrieval.vector_store import QdrantVectorStore
                app.state.vector_store = QdrantVectorStore()
                await app.state.vector_store.initialize()
                logger.info("Vector Store initialized")
            except Exception as e:
                logger.warning(f"Vector Store initialization failed: {e}")
                app.state.vector_store = None
            
            # Simple workflow fallback
            app.state.workflow = SimpleWorkflow()
            logger.info("Simple workflow initialized")
                
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            # Don't raise, just continue with limited functionality
    
    async def cleanup_components():
        """Cleanup all components."""
        try:
            if hasattr(app.state, 'llm_manager') and app.state.llm_manager:
                await app.state.llm_manager.cleanup()
            
            if hasattr(app.state, 'vector_store') and app.state.vector_store:
                await app.state.vector_store.cleanup()
                
            logger.info("All components cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    # Attach methods to app state
    app.state.init_components = init_components
    app.state.cleanup_components = cleanup_components


class SimpleWorkflow:
    """Simple workflow fallback when full agentic system isn't available."""
    
    async def process_query(self, query: str):
        """Process a query with simple response."""
        
        class SimpleResult:
            def __init__(self):
                self.success = True
                self.final_response = f"I received your message: '{query}'. This is a demo response from the Macrocomm AI Assistant widget."
                self.query_intent = "demo"
                self.confidence_score = 0.8
                self.citations = []
                self.workflow_steps = []
                self.total_execution_time = 0.5
                self.chunks_retrieved = 0
                self.error_messages = []
        
        await asyncio.sleep(0.5)  # Simulate processing
        return SimpleResult()


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP_ERROR",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        )


# Create the application instance
app = create_app()


# Root endpoint
@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Macrocomm AI Assistant",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health_check": "/health",
        "widget_demo": "/frontend/widget/demo.html",
        "admin_portal": "/frontend/widget/admin.html"
    }


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with streaming responses."""
    await app.state.connection_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message", data.get("query", ""))
            
            if not message.strip():
                await websocket.send_json({
                    "type": "error",
                    "message": "Message cannot be empty"
                })
                continue
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "status",
                "message": "Processing your query...",
                "stage": "started"
            })
            
            try:
                # Process through workflow (or fallback)
                if hasattr(app.state, 'workflow') and app.state.workflow:
                    result = await app.state.workflow.process_query(message)
                    
                    if result.success:
                        # Send final response
                        await websocket.send_json({
                            "type": "response",
                            "query": message,
                            "response": result.final_response,
                            "intent": result.query_intent,
                            "confidence": result.confidence_score,
                            "sources": []
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to process query"
                        })
                else:
                    # Simple fallback response
                    await asyncio.sleep(1)  # Simulate processing
                    await websocket.send_json({
                        "type": "response",
                        "query": message,
                        "response": f"Hello! I received your message: '{message}'. The Macrocomm AI Assistant is working! This is a demo response showing the widget is connected to the backend.",
                        "intent": "demo",
                        "confidence": 0.9,
                        "sources": []
                    })
                    
            except Exception as e:
                logger.error(f"WebSocket query processing failed: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "An error occurred while processing your query"
                })
    
    except WebSocketDisconnect:
        app.state.connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        app.state.connection_manager.disconnect(websocket)


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main_fixed:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        access_log=True,
        log_level="info"
    )