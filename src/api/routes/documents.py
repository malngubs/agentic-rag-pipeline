"""
Document management routes.
"""

import uuid
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from pydantic import BaseModel

from api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_created: int
    processing_time: float


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Upload and process a document."""
    try:
        # Validate file type
        allowed_types = ["text/plain", "application/pdf", 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not supported"
            )
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process document
            processor = request.app.state.document_processor
            result = await processor.process_file(temp_file_path)
            
            if not result.success:
                raise HTTPException(
                    status_code=400,
                    detail=f"Document processing failed: {result.error_message}"
                )
            
            # Generate embeddings and store in vector database
            llm_manager = request.app.state.llm_manager
            vector_store = request.app.state.vector_store
            
            vector_chunks = []
            for chunk in result.chunks:
                success, embedding = await llm_manager.generate_embeddings(chunk.content)
                if success:
                    from retrieval.vector_store import DocumentChunk
                    vector_chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        content=chunk.content,
                        metadata=chunk.metadata,
                        embedding=embedding
                    )
                    vector_chunks.append(vector_chunk)
            
            # Store in vector database
            if vector_chunks:
                await vector_store.add_documents(vector_chunks)
            
            return DocumentResponse(
                document_id=result.document_id,
                filename=file.filename,
                status="processed",
                chunks_created=len(vector_chunks),
                processing_time=result.processing_time
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Document processing failed")


@router.get("/list")
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List uploaded documents."""
    # For now, return empty list
    # In production, implement document storage and retrieval
    return {"documents": [], "total": 0}