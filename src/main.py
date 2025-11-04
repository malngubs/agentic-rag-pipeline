"""
FastAPI Main Application for Agentic RAG Pipeline.

This module provides the main FastAPI application with REST endpoints,
WebSocket streaming, and production-ready features like health monitoring,
authentication, and rate limiting.
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

# Import our components
from config.settings import get_settings
from api.routes import chat, documents, health, auth, metrics, widget
from api.websockets import ConnectionManager
from core.exceptions import RAGException
from utils.logging import setup_logging

# Configure logging
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
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Agentic RAG Pipeline...")
        await app.state.cleanup_components()
        logger.info("Shutdown completed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        level=settings.monitoring.log_level,
        log_path=settings.monitoring.log_path
    )
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app.app_name,
        version=settings.app.app_version,
        description="Advanced RAG system with human-like reasoning capabilities",
        docs_url="/docs" if settings.app.debug else None,
        redoc_url="/redoc" if settings.app.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app, settings)
    
    # Add routes
    setup_routes(app)
    
    # Add state management
    setup_state(app, settings)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    logger.info(f"FastAPI app created: {settings.app.app_name} v{settings.app.app_version}")
    return app


    
def setup_middleware(app: FastAPI, settings):
    """Configure middleware for the application."""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins if hasattr(settings.app, 'cors_origins') else ["*"],
        allow_credentials=getattr(settings.app, 'cors_allow_credentials', True),
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
    # Core API routes
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
    app.include_router(documents.router, prefix="/v1/documents", tags=["documents"])
    app.include_router(metrics.router, prefix="/v1/metrics", tags=["metrics"])
    app.include_router(widget.router, prefix="/widget", tags=["widget"])
    
    # Serve static files for the widget
    try:
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")

        # Add after creating the app
    app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")


def setup_state(app: FastAPI, settings):
    """Setup application state and components."""
    app.state.settings = settings
    app.state.connection_manager = ConnectionManager()
    
    # Component initialization functions
    async def init_components():
        """Initialize all RAG components."""
        from test_llm_direct import SimpleLLMManager
        from retrieval.vector_store import QdrantVectorStore
        from agents.simple_workflow import SimpleAgenticWorkflow
        from document_processing.ingestion import DocumentProcessor
        
        try:
            # Initialize LLM Manager
            app.state.llm_manager = SimpleLLMManager()
            await app.state.llm_manager.__aenter__()
            logger.info("LLM Manager initialized")
            
            # Initialize Vector Store
            app.state.vector_store = QdrantVectorStore(
                collection_name="production_rag",
                vector_dimension=768,  # Default dimension
                storage_path=settings.qdrant.qdrant_path
            )
            await app.state.vector_store.connect()
            logger.info("Vector Store initialized")
            
            # Initialize Document Processor
            app.state.document_processor = DocumentProcessor(
                chunk_size=settings.documents.max_chunk_size,
                chunk_overlap=settings.documents.chunk_overlap
            )
            logger.info("Document Processor initialized")
            
            # Initialize Agentic Workflow
            app.state.workflow = SimpleAgenticWorkflow(
                llm_manager=app.state.llm_manager,
                vector_store=app.state.vector_store,
                max_retrieval_chunks=settings.retrieval.retrieval_k,
                confidence_threshold=settings.retrieval.similarity_threshold
            )
            logger.info("Agentic Workflow initialized")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    async def cleanup_components():
        """Cleanup all components."""
        try:
            if hasattr(app.state, 'llm_manager'):
                await app.state.llm_manager.__aexit__(None, None, None)
            
            if hasattr(app.state, 'vector_store'):
                await app.state.vector_store.cleanup()
                
            logger.info("All components cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    # Attach methods to app state
    app.state.init_components = init_components
    app.state.cleanup_components = cleanup_components


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers."""
    
    @app.exception_handler(RAGException)
    async def rag_exception_handler(request, exc: RAGException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_type,
                "message": exc.message,
                "details": exc.details
            }
        )
    
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
    settings = get_settings()
    return {
        "name": settings.app.app_name,
        "version": settings.app.app_version,
        "status": "operational",
        "documentation": "/docs",
        "health_check": "/health",
        "widget_demo": "/widget/demo.html"
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
            
            query = data.get("query", "")
            user_id = data.get("user_id", "anonymous")
            session_id = data.get("session_id", "default")
            
            if not query.strip():
                await websocket.send_json({
                    "type": "error",
                    "message": "Query cannot be empty"
                })
                continue
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "status",
                "message": "Processing your query...",
                "stage": "started"
            })
            
            try:
                # Process through agentic workflow
                result = await app.state.workflow.process_query(query)
                
                if result.success:
                    # Send workflow steps as they complete
                    for i, step in enumerate(result.workflow_steps):
                        await websocket.send_json({
                            "type": "progress",
                            "stage": step.stage.value,
                            "step_number": i + 1,
                            "total_steps": len(result.workflow_steps),
                            "reasoning": step.reasoning,
                            "execution_time": step.execution_time
                        })
                        
                        # Small delay to show progress
                        await asyncio.sleep(0.1)
                    
                    # Send final response
                    await websocket.send_json({
                        "type": "response",
                        "query": query,
                        "response": result.final_response,
                        "intent": result.query_intent,
                        "confidence": result.confidence_score,
                        "citations": result.citations,
                        "execution_time": result.total_execution_time,
                        "chunks_retrieved": result.chunks_retrieved
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to process query",
                        "errors": result.error_messages
                    })
                    
            except Exception as e:
                logger.error(f"WebSocket query processing failed: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "An error occurred while processing your query"
                })
    
    except WebSocketDisconnect:
        app.state.connection_manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        app.state.connection_manager.disconnect(websocket)


if __name__ == "__main__":
    # Development server
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.app.api_host,
        port=settings.app.api_port,
        reload=settings.app.debug,
        access_log=True,
        log_level=settings.monitoring.log_level.lower()
    )