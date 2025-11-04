"""
🧠 ADVANCED AGENTIC RAG PIPELINE - PRODUCTION READY
=====================================================
A comprehensive Retrieval-Augmented Generation system that mimics human thought processes
through multi-layered cognitive architecture, adaptive reasoning, and memory systems.

Key Features:
- Human-like cognitive reasoning with multi-step strategies
- Advanced vector search with semantic understanding
- Adaptive LLM management with fallback mechanisms
- Real-time document processing and chunking
- Production-grade error handling and monitoring
- Confidence-based response generation

Author: Advanced AI Systems
Version: 2.0 Production
"""

import os
import sys
import asyncio
import logging
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import uuid

# Core ML/AI Libraries
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.conversions import common_types

# Document Processing
import PyPDF2
import docx
from pathlib import Path
import mimetypes

# Web Framework
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# HTTP Client
import httpx
import requests

# Text Processing
import re
from nltk.tokenize import sent_tokenize
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# =============================================================================
# 🏗️ CORE CONFIGURATION & ENUMS
# =============================================================================

class ReasoningStrategy(Enum):
    """
    Human-like reasoning strategies that mirror cognitive approaches:
    
    DIRECT: Like immediate recall from memory
    ANALYTICAL: Like careful step-by-step thinking
    CREATIVE: Like lateral thinking and association
    CONSERVATIVE: Like cautious, minimal-risk responses
    """
    DIRECT = "direct"
    ANALYTICAL = "analytical"  
    CREATIVE = "creative"
    CONSERVATIVE = "conservative"

class ConfidenceLevel(Enum):
    """
    Confidence levels that mirror human certainty levels
    """
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class RAGConfig:
    """
    🎛️ Central configuration for the RAG system
    Mimics human learning preferences and cognitive settings
    """
    # Vector Database Settings
    vector_collection_name: str = "knowledge_base"
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_size: int = 384
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Chunking Strategy (like human memory segmentation)
    chunk_size: int = 1000  # Characters per chunk
    chunk_overlap: int = 200  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum viable chunk
    
    # Reasoning Parameters (cognitive processing)
    max_context_chunks: int = 5  # Working memory limit
    reasoning_depth: int = 3  # How many reasoning steps
    confidence_threshold: float = 0.6  # When to trust a response
    
    # LLM Settings
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    max_tokens: int = 2048
    temperature: float = 0.7  # Balance between creativity and consistency

class ThoughtProcess:
    """
    Simple thought process implementation for decision making
    """
    
    def __init__(self, agent_name: str = "RAG_Agent"):
        self.agent_name = agent_name
        self.thought_history = []
    
    def think(self, situation: str, options: List[str], context: Dict = None) -> Dict[str, Any]:
        """Simple decision making"""
        # Just return the first option for now - can be enhanced later
        return {
            "decision": options[0] if options else "default",
            "confidence": 0.8,
            "reasoning": f"Selected {options[0] if options else 'default'} for {situation}"
        }

# =============================================================================
# 🧠 COGNITIVE MEMORY SYSTEMS
# =============================================================================

@dataclass
class MemoryChunk:
    """
    Represents a piece of knowledge in our long-term memory system
    Similar to how humans store episodic and semantic memories
    """
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    confidence_score: float = 0.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data

class WorkingMemory:
    """
    🧠 Working Memory System
    
    Mimics human working memory - the active processing space where we:
    - Hold current conversation context
    - Maintain reasoning state
    - Track cognitive strategies being used
    """
    
    def __init__(self, capacity: int = 7):  # Miller's Magic Number
        self.capacity = capacity
        self.active_chunks: List[MemoryChunk] = []
        self.reasoning_trace: List[Dict[str, Any]] = []
        self.current_strategy: ReasoningStrategy = ReasoningStrategy.DIRECT
        self.confidence_history: List[float] = []
    
    def add_chunk(self, chunk: MemoryChunk):
        """Add a chunk to working memory, respecting capacity limits"""
        self.active_chunks.append(chunk)
        if len(self.active_chunks) > self.capacity:
            # Remove least recently accessed (like human memory decay)
            self.active_chunks.sort(key=lambda x: x.last_accessed or datetime.min)
            self.active_chunks = self.active_chunks[-self.capacity:]
    
    def get_context_summary(self) -> str:
        """Generate a summary of current working memory state"""
        if not self.active_chunks:
            return "No active context"
        
        content_pieces = [chunk.content[:200] + "..." if len(chunk.content) > 200 
                         else chunk.content for chunk in self.active_chunks]
        return " | ".join(content_pieces)
    
    def update_reasoning_trace(self, step: str, result: Any, confidence: float):
        """Track the reasoning process like human metacognition"""
        self.reasoning_trace.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "result": str(result),
            "confidence": confidence,
            "strategy": self.current_strategy.value
        })
        self.confidence_history.append(confidence)
    
    def clear(self):
        """Reset working memory (like focusing on a new task)"""
        self.active_chunks.clear()
        self.reasoning_trace.clear()
        self.confidence_history.clear()

# =============================================================================
# 🔤 ADVANCED TEXT PROCESSING SYSTEM
# =============================================================================

class DocumentProcessor:
    """
    🔤 Intelligent Document Processing System
    
    Processes documents like a human reader:
    - Understands document structure and context
    - Breaks content into meaningful semantic chunks
    - Preserves important relationships between ideas
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def process_file(self, file_path: str, content: bytes = None) -> List[MemoryChunk]:
        """
        Process a file into memory chunks with human-like understanding
        
        Args:
            file_path: Path to the file
            content: Raw file content (optional)
        
        Returns:
            List of processed memory chunks
        """
        try:
            # Determine file type and extract text
            if content is not None:
                text = await self._extract_text_from_bytes(content, file_path)
            else:
                text = await self._extract_text_from_file(file_path)
            
            if not text or len(text.strip()) < self.config.min_chunk_size:
                self.logger.warning(f"Insufficient content in {file_path}")
                return []
            
            # Create semantic chunks (like human reading comprehension)
            chunks = await self._create_semantic_chunks(text, file_path)
            
            self.logger.info(f"Processed {file_path}: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return []
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types"""
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        try:
            if extension == '.pdf':
                return await self._extract_from_pdf(file_path)
            elif extension == '.docx':
                return await self._extract_from_docx(file_path)
            elif extension in ['.txt', '.md']:
                return await self._extract_from_text(file_path)
            else:
                # Try as plain text
                return await self._extract_from_text(file_path)
        except Exception as e:
            self.logger.error(f"Text extraction failed for {file_path}: {str(e)}")
            return ""
    
    async def _extract_text_from_bytes(self, content: bytes, filename: str) -> str:
        """Extract text from raw bytes based on filename"""
        extension = Path(filename).suffix.lower()
        
        try:
            if extension == '.pdf':
                # For PDF bytes processing
                from io import BytesIO
                pdf_reader = PyPDF2.PdfReader(BytesIO(content))
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                return "\n\n".join(text_parts)
            
            elif extension == '.docx':
                # For DOCX bytes processing
                from io import BytesIO
                doc = docx.Document(BytesIO(content))
                paragraphs = [paragraph.text for paragraph in doc.paragraphs]
                return "\n\n".join(paragraphs)
            
            else:
                # Try as plain text
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            self.logger.error(f"Bytes extraction failed for {filename}: {str(e)}")
            return content.decode('utf-8', errors='ignore')
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text_parts = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
        return "\n\n".join(text_parts)
    
    async def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(file_path)
        paragraphs = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                paragraphs.append(paragraph.text)
        
        return "\n\n".join(paragraphs)
    
    async def _extract_from_text(self, file_path: str) -> str:
        """Extract text from plain text files"""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, read as bytes and ignore errors
        with open(file_path, 'rb') as file:
            return file.read().decode('utf-8', errors='ignore')
    
    async def _create_semantic_chunks(self, text: str, source: str) -> List[Dict[str, Any]]:
        """
        Create semantically meaningful chunks (returns list of dicts as required)
        """
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Simple chunking by paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for paragraph in paragraphs:
            # Simple chunking logic
            if len(current_chunk) + len(paragraph) > self.config.chunk_size:
                if current_chunk:
                    chunk_dict = {
                        "id": f"{Path(source).stem}_chunk_{chunk_id}",
                        "text": current_chunk.strip(),
                        "source_file": source,
                        "chunk_index": chunk_id,
                        "word_count": len(current_chunk.split())
                    }
                    chunks.append(chunk_dict)
                    chunk_id += 1
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += f"\n\n{paragraph}"
                else:
                    current_chunk = paragraph
        
        # Handle final chunk
        if current_chunk and len(current_chunk.strip()) >= self.config.min_chunk_size:
            chunk_dict = {
                "id": f"{Path(source).stem}_chunk_{chunk_id}",
                "text": current_chunk.strip(),
                "source_file": source,
                "chunk_index": chunk_id,
                "word_count": len(current_chunk.split())
            }
            chunks.append(chunk_dict)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'\n\[Page \d+\]\n', '\n\n', text)
        
        return text.strip()
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of previous chunk"""
        if len(text) <= self.config.chunk_overlap:
            return text
        
        # Try to get overlap at sentence boundary
        overlap_text = text[-self.config.chunk_overlap:]
        sentences = sent_tokenize(overlap_text)
        
        if len(sentences) > 1:
            # Keep complete sentences
            return ' '.join(sentences[1:]) + ' '
        else:
            return overlap_text + ' '
    
    async def _create_memory_chunk(self, content: str, source: str, chunk_id: int) -> MemoryChunk:
        """Create a memory chunk with metadata"""
        # Generate unique ID
        content_hash = hashlib.md5(content.encode()).hexdigest()
        chunk_uuid = f"{Path(source).stem}_{chunk_id}_{content_hash[:8]}"
        
        # Extract key information for metadata
        word_count = len(content.split())
        char_count = len(content)
        
        metadata = {
            "source": source,
            "chunk_id": chunk_id,
            "word_count": word_count,
            "char_count": char_count,
            "created_at": datetime.now().isoformat(),
            "content_type": Path(source).suffix.lower() or "unknown"
        }
        
        return MemoryChunk(
            id=chunk_uuid,
            content=content,
            metadata=metadata,
            last_accessed=datetime.now()
        )

# =============================================================================
# 🔍 ADVANCED VECTOR SEARCH SYSTEM
# =============================================================================

class VectorStoreManager:
    """
    🔍 Intelligent Vector Search System
    
    Manages our long-term memory (vector database) like the human brain:
    - Stores knowledge as semantic embeddings
    - Enables associative recall and memory retrieval
    - Maintains relationship between concepts
    - Supports forgetting and memory consolidation
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client: Optional[QdrantClient] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model for semantic understanding"""
        try:
            self.logger.info(f"Loading embedding model: {self.config.embedding_model}")
            self.embedding_model = SentenceTransformer(self.config.embedding_model)
            self.logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    async def initialize(self):
        """Initialize connection to vector database"""
        try:
            self.logger.info(f"Connecting to Qdrant at {self.config.qdrant_host}:{self.config.qdrant_port}")
            self.client = QdrantClient(
                host=self.config.qdrant_host,
                port=self.config.qdrant_port
            )
            
            # Test connection
            collections = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_collections
            )
            
            await self._ensure_collection_exists()
            self.logger.info("✅ Vector store initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
    
    async def _ensure_collection_exists(self):
        """Ensure our knowledge collection exists"""
        try:
            collections = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_collections
            )
            
            collection_names = [col.name for col in collections.collections]
            
            if self.config.vector_collection_name not in collection_names:
                self.logger.info(f"Creating collection: {self.config.vector_collection_name}")
                
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.client.create_collection(
                        collection_name=self.config.vector_collection_name,
                        vectors_config=VectorParams(
                            size=self.config.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                )
                self.logger.info("✅ Collection created successfully")
            else:
                self.logger.info(f"Collection '{self.config.vector_collection_name}' already exists")
                
        except Exception as e:
            self.logger.error(f"Failed to ensure collection exists: {str(e)}")
            raise
    
    async def store_chunks(self, chunks: List[MemoryChunk]) -> bool:
        """
        Store memory chunks in long-term memory (vector database)
        
        Like how humans encode experiences into long-term memory:
        - Convert to semantic embeddings
        - Store with rich metadata
        - Enable future retrieval
        """
        if not chunks:
            return True
        
        try:
            points = []
            
            for chunk in chunks:
                # Generate embedding (semantic encoding)
                if not chunk.embedding:
                    chunk.embedding = await self._generate_embedding(chunk.content)
                
                # Create point for storage
                point = PointStruct(
                    id=chunk.id,
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "confidence_score": chunk.confidence_score,
                        "access_count": chunk.access_count,
                        "last_accessed": chunk.last_accessed.isoformat() if chunk.last_accessed else None
                    }
                )
                points.append(point)
            
            # Store in batch (efficient bulk storage)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.upsert(
                    collection_name=self.config.vector_collection_name,
                    points=points
                )
            )
            
            self.logger.info(f"✅ Stored {len(chunks)} chunks in vector store")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store chunks: {str(e)}")
            return False
    
    async def index_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> Dict[str, Any]:
        """
        Index chunks with their embeddings into the vector store
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors corresponding to each chunk
        
        Returns:
            Dictionary with success status and any error information
        """
        try:
            if len(chunks) != len(embeddings):
                return {
                    "success": False,
                    "error": f"Mismatch between chunks ({len(chunks)}) and embeddings ({len(embeddings)})"
                }
            
            points = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Create point for storage
                point = PointStruct(
                    id=chunk["id"],
                    vector=embedding,
                    payload={
                        "content": chunk["text"],
                        "source_file": chunk.get("source_file", ""),
                        "chunk_index": chunk.get("chunk_index", i),
                        "word_count": chunk.get("word_count", 0),
                        "created_at": datetime.now().isoformat()
                    }
                )
                points.append(point)
            
            # Store in batch (efficient bulk storage)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.upsert(
                    collection_name=self.config.vector_collection_name,
                    points=points
                )
            )
            
            self.logger.info(f"✅ Successfully indexed {len(chunks)} chunks")
            return {
                "success": True,
                "chunks_indexed": len(chunks),
                "message": f"Successfully indexed {len(chunks)} chunks"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to index chunks: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_vector(self, query_text: str, limit: int = 5, score_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Search the vector store using query text
        
        Args:
            query_text: The search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
        
        Returns:
            Dictionary with search results
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query_text)
            
            # Perform search
            search_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.search(
                    collection_name=self.config.vector_collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    score_threshold=score_threshold
                )
            )
            
            # Format results
            results = []
            for hit in search_result:
                result = {
                    "text": hit.payload["content"],
                    "source_file": hit.payload.get("source_file", ""),
                    "chunk_id": hit.id,
                    "score": hit.score,
                    "chunk_index": hit.payload.get("chunk_index", 0)
                }
                results.append(result)
            
            return {
                "success": True,
                "results": results,
                "total_found": len(results)
            }
            
        except Exception as e:
            self.logger.error(f"Vector search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
# ...existing code...

class LLMManager:
    """
    🧠 LLM Manager for Adaptive Reasoning and Response Generation
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.available_models: List[Dict[str, Any]] = []
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize available models for response generation"""
        # For now, just add a default model - this can be expanded
        self.available_models.append({
            "name": "gpt-4o-mini",
            "provider": "openai",
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        })
        
        self.logger.info(f"Available models: {self.available_models}")
    
    async def generate_response(self, query: str, context_chunks: List[str]) -> Dict[str, Any]:
        """
        Generate response using query and context chunks
        
        Args:
            query: User query
            context_chunks: List of relevant text chunks
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Prepare context
            context = "\n\n".join(context_chunks) if context_chunks else ""
            
            # Create messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": """You are an intelligent assistant with access to relevant documents. 
                    Use the provided context to answer questions accurately and helpfully. 
                    If the context doesn't contain enough information to answer the question, say so clearly.
                    Always base your responses on the provided context."""
                },
                {
                    "role": "user", 
                    "content": f"""Context information:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the context above."""
                }
            ]
            
            # Try to generate response with best available model
            response, confidence, metadata = await self.generate_response_internal(
                messages=messages,
                strategy=ReasoningStrategy.ANALYTICAL
            )
            
            return {
                "success": True,
                "response": response,
                "confidence": confidence,
                "model_used": metadata.get("model", "unknown"),
                "context_chunks_used": len(context_chunks),
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while generating a response. Please try again."
            }

    async def generate_response_internal(self, messages: List[Dict[str, str]], strategy: ReasoningStrategy = ReasoningStrategy.DIRECT) -> Tuple[str, float, Dict[str, Any]]:
        """
        Internal method for generating responses - this is the actual implementation
        that was already in your code as generate_response, just renamed for clarity
        """
        # This should use your existing generate_response logic
        # Just call the original method you already have
        return await self.generate_response_original(messages, strategy)
    
    async def generate_response_original(self, 
                              messages: List[Dict[str, str]], 
                              strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
                              max_attempts: int = 3) -> Tuple[str, float, Dict[str, Any]]:
        """
        Generate response using best available model with human-like reasoning
        
        Args:
            messages: Conversation messages
            strategy: Reasoning strategy to use
            max_attempts: Maximum retry attempts
        
        Returns:
            (response_text, confidence_score, metadata)
        """
        
        # Select best model for this strategy
        selected_model = await self._select_model_for_strategy(strategy)
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"🧠 Generation attempt {attempt + 1} using {selected_model['name']} (strategy: {strategy.value})")
                
                start_time = time.time()
                
                if selected_model["provider"] == "openai":
                    response, confidence = await self._generate_openai_response(
                        selected_model, messages, strategy
                    )
                elif selected_model["provider"] == "ollama":
                    response, confidence = await self._generate_ollama_response(
                        selected_model, messages, strategy
                    )
                else:
                    raise ValueError(f"Unknown provider: {selected_model['provider']}")
                
                response_time = time.time() - start_time
                
                # Update model performance tracking
                self._update_model_performance(selected_model["name"], response_time, confidence, True)
                
                metadata = {
                    "model": selected_model["name"],
                    "provider": selected_model["provider"],
                    "strategy": strategy.value,
                    "attempt": attempt + 1,
                    "response_time": response_time,
                    "success": True
                }
                
                self.logger.info(f"✅ Response generated ({len(response)} chars) using strategy {strategy.value}")
                return response, confidence, metadata
                
            except Exception as e:
                self.logger.error(f"❌ Generation attempt {attempt + 1} failed: {str(e)}")
                
                # Update performance tracking for failure
                self._update_model_performance(selected_model["name"], 0, 0, False)
                
                if attempt < max_attempts - 1:
                    # Try different model or strategy for next attempt
                    selected_model = await self._select_fallback_model(selected_model)
                    if strategy != ReasoningStrategy.CONSERVATIVE:
                        strategy = self._get_fallback_strategy(strategy)
        
        # All attempts failed
        return ("I apologize, but I'm experiencing technical difficulties generating a response. Please try again later.", 
                0.1, 
                {"error": "All generation attempts failed", "attempts": max_attempts})

    @property 
    def current_model(self) -> Optional[str]:
        """Get the current model name"""
        if self.available_models:
            return self.available_models[0]["name"]
        return None

# =============================================================================
# 🚀 RAG SYSTEM - COORDINATOR FOR AGENTIC LEARNING
# =============================================================================

class RAGSystem:
    """
    🚀 Advanced RAG System - Orchestrates the entire Retrieval-Augmented Generation process
    
    Components:
    - Document Processing & Chunking
    - Semantic Vector Search
    - Adaptive Reasoning & Response Generation
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        
        # Components
        self.document_processor = DocumentProcessor(config)
        self.vector_store = VectorStoreManager(config)
        self.llm_manager = LLMManager(config)
        
        # Statistics
        self.documents_indexed = 0
        self.total_chunks = 0
    
    async def initialize(self):
        """Initialize all components of the RAG system"""
        try:
            self.logger.info("🚀 Initializing RAG System...")
            
            await self.vector_store.initialize()
            self.logger.info("✅ Vector store initialized")
            
            # Preload some data or perform warm-up tasks if needed
            # Example: await self.preload_knowledge_base()
            
            self.initialized = True
            self.logger.info("🎉 RAG System initialization complete")
            
        except Exception as e:
            self.logger.error(f"❌ RAG System initialization failed: {str(e)}")
            self.initialized = False
    
    async def process_document(self, file_path: str, content: bytes) -> bool:
        """Process document with comprehensive error handling and logging"""
        if not self.initialized:
            self.logger.error("❌ RAG System not initialized - cannot process document")
            return False

        file_path_obj = Path(file_path)
        self.logger.info(f"📋 Processing document: {file_path_obj.name} ({len(content)} bytes)")

        try:
            # Step 1: Process document into chunks
            self.logger.info("🔍 Step 1: Extracting and chunking document...")

            # Debug: Check content
            self.logger.info(f"DEBUG: Content length: {len(content)} bytes")
            if len(content) < 50:
                self.logger.warning(f"DEBUG: Content preview: {content[:100]}")

            # The process_file method returns a list of chunk dictionaries
            chunks_list = await self.document_processor.process_file(str(file_path_obj), content)

            self.logger.info(f"DEBUG: process_file returned {len(chunks_list) if chunks_list else 0} chunks")
            if chunks_list:
                self.logger.info(f"DEBUG: First chunk preview: {str(chunks_list[0])[:200]}...")

            if not chunks_list:
                self.logger.error("❌ Document processing failed: No chunks created")
                self.logger.error("DEBUG: This could mean:")
                self.logger.error("  - Document content is too small")
                self.logger.error("  - File format not supported properly")
                self.logger.error("  - Chunking logic failed")
                return False

            # Convert to the format expected by the rest of the pipeline
            chunks = []
            for i, chunk_dict in enumerate(chunks_list):
                if isinstance(chunk_dict, dict):
                    # It's already a dictionary
                    chunk = {
                        "id": chunk_dict.get("id", f"chunk_{i}"),
                        "text": chunk_dict.get("text", ""),
                        "source_file": chunk_dict.get("source_file", str(file_path_obj)),
                        "chunk_index": chunk_dict.get("chunk_index", i),
                        "word_count": chunk_dict.get("word_count", 0)
                    }
                else:
                    # It might be a MemoryChunk object
                    chunk = {
                        "id": getattr(chunk_dict, 'id', f"chunk_{i}"),
                        "text": getattr(chunk_dict, 'content', str(chunk_dict)),
                        "source_file": str(file_path_obj),
                        "chunk_index": i,
                        "word_count": len(str(chunk_dict).split())
                    }
                chunks.append(chunk)

            self.logger.info(f"✅ Created {len(chunks)} chunks for processing")

            # Step 2: Generate embeddings for chunks
            self.logger.info("🔤 Step 2: Generating embeddings...")
            chunk_texts = [chunk["text"] for chunk in chunks]

            self.logger.info(f"DEBUG: Generating embeddings for {len(chunk_texts)} texts")
            self.logger.info(f"DEBUG: Sample text: {chunk_texts[0][:100]}..." if chunk_texts else "No texts to process")

            try:
                embeddings = await asyncio.to_thread(
                    self.embedding_model.encode, 
                    chunk_texts,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                embeddings = embeddings.tolist()
                self.logger.info(f"✅ Generated {len(embeddings)} embeddings (dimension: {len(embeddings[0]) if embeddings else 0})")

            except Exception as e:
                self.logger.error(f"❌ Embedding generation failed: {str(e)}")
                return False

            # Step 3: Index chunks in vector store
            self.logger.info("🗂️ Step 3: Indexing chunks in vector store...")
            index_result = await self.vector_store.index_chunks(chunks, embeddings)

            self.logger.info(f"DEBUG: index_chunks returned: {index_result}")

            if not index_result.get("success", False):
                self.logger.error(f"❌ Vector indexing failed: {index_result.get('error', 'Unknown error')}")
                return False

            # Update system statistics
            self.documents_indexed += 1
            self.total_chunks += len(chunks)

            self.logger.info(f"🎉 Document successfully processed and indexed!")
            self.logger.info(f"📊 System stats: {self.documents_indexed} documents, {self.total_chunks} total chunks")

            return True

        except Exception as e:
            self.logger.error(f"❌ Document processing pipeline failed: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False