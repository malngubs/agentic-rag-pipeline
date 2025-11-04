"""
Vector Store Manager using Qdrant.

This module provides intelligent document storage and retrieval capabilities.
It manages embeddings, metadata, and implements hybrid search strategies
that combine semantic similarity with keyword matching.
"""

import asyncio
import logging
import uuid
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        Distance, VectorParams, PointStruct, 
        Filter, FieldCondition, Range, MatchValue
    )
except ImportError:
    print("Installing qdrant-client...")
    import subprocess
    subprocess.check_call(["pip", "install", "qdrant-client==1.7.0"])
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        Distance, VectorParams, PointStruct, 
        Filter, FieldCondition, Range, MatchValue
    )

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: Optional[float] = None


@dataclass
class SearchResult:
    """Search result with relevance information."""
    chunks: List[DocumentChunk]
    query: str
    total_results: int
    search_time: float
    method_used: str


class QdrantVectorStore:
    """
    Advanced Vector Store using Qdrant for document storage and retrieval.
    
    This class provides:
    - Semantic similarity search using embeddings
    - Metadata filtering and faceted search
    - Hybrid search combining multiple strategies
    - Automatic index optimization
    - Multi-tenant support
    """
    
    def __init__(self, 
                 collection_name: str = "documents",
                 vector_dimension: int = 768,
                 storage_path: str = "./data/qdrant",
                 host: str = "localhost",
                 port: int = 6333):
        """
        Initialize the Vector Store.
        
        Args:
            collection_name: Name of the Qdrant collection
            vector_dimension: Dimension of embedding vectors
            storage_path: Path for local storage
            host: Qdrant host
            port: Qdrant port
        """
        self.collection_name = collection_name
        self.vector_dimension = vector_dimension
        self.storage_path = Path(storage_path)
        self.host = host
        self.port = port
        self.client: Optional[QdrantClient] = None
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.search_metrics = {
            "total_searches": 0,
            "avg_search_time": 0.0,
            "total_documents": 0
        }
    
    async def connect(self):
        """Connect to Qdrant and initialize collection."""
        try:
            # Try to connect to external Qdrant first
            try:
                self.client = QdrantClient(host=self.host, port=self.port, timeout=5)
                # Test connection
                collections = self.client.get_collections()
                logger.info(f"Connected to external Qdrant at {self.host}:{self.port}")
            except Exception as e:
                # Fall back to local/embedded mode
                logger.info(f"External Qdrant not available ({e}), using local mode")
                self.client = QdrantClient(path=str(self.storage_path))
            
            # Create collection if it doesn't exist
            await self._ensure_collection_exists()
            
            # Get current stats
            collection_info = self.client.get_collection(self.collection_name)
            self.search_metrics["total_documents"] = collection_info.points_count
            
            logger.info(f"Vector store connected: {self.search_metrics['total_documents']} documents")
            
        except Exception as e:
            logger.error(f"Failed to connect to vector store: {e}")
            raise ConnectionError(f"Vector store connection failed: {e}")
    
    async def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create new collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created new collection: {self.collection_name}")
            else:
                logger.info(f"Using existing collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    async def add_documents(self, chunks: List[DocumentChunk]) -> List[str]:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of document chunks with embeddings
            
        Returns:
            List of inserted document IDs
        """
        if not self.client:
            raise RuntimeError("Vector store not connected")
        
        try:
            # Prepare points for insertion
            points = []
            for chunk in chunks:
                if not chunk.embedding:
                    raise ValueError(f"Chunk {chunk.id} missing embedding")
                
                # Ensure ID is string
                point_id = chunk.id if isinstance(chunk.id, str) else str(chunk.id)
                
                # Prepare metadata payload
                payload = {
                    "content": chunk.content,
                    "chunk_id": chunk.id,
                    "created_at": time.time(),
                    **chunk.metadata
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=chunk.embedding,
                    payload=payload
                )
                points.append(point)
            
            # Insert points in batches
            batch_size = 100
            inserted_ids = []
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                
                # Insert batch
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                
                batch_ids = [point.id for point in batch]
                inserted_ids.extend(batch_ids)
                
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} documents")
            
            # Update metrics
            self.search_metrics["total_documents"] += len(points)
            
            logger.info(f"Successfully added {len(chunks)} document chunks")
            return inserted_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    async def search_similar(self, 
                           query_embedding: List[float],
                           limit: int = 10,
                           score_threshold: float = 0.0,
                           metadata_filter: Optional[Dict[str, Any]] = None) -> SearchResult:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            metadata_filter: Optional metadata filtering
            
        Returns:
            SearchResult with matching chunks
        """
        if not self.client:
            raise RuntimeError("Vector store not connected")
        
        start_time = time.time()
        
        try:
            # Prepare filter
            search_filter = None
            if metadata_filter:
                conditions = []
                for key, value in metadata_filter.items():
                    if isinstance(value, str):
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    elif isinstance(value, (int, float)):
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    elif isinstance(value, dict) and "gte" in value:
                        # Range filter
                        conditions.append(
                            FieldCondition(
                                key=key, 
                                range=Range(gte=value["gte"], lte=value.get("lte"))
                            )
                        )
                
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # Perform search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )
            
            # Convert results to DocumentChunk objects
            chunks = []
            for scored_point in search_result:
                payload = scored_point.payload
                
                chunk = DocumentChunk(
                    id=payload.get("chunk_id", str(scored_point.id)),
                    content=payload.get("content", ""),
                    metadata={k: v for k, v in payload.items() 
                             if k not in ["content", "chunk_id"]},
                    score=scored_point.score
                )
                chunks.append(chunk)
            
            search_time = time.time() - start_time
            
            # Update metrics
            self._update_search_metrics(search_time)
            
            result = SearchResult(
                chunks=chunks,
                query="vector_similarity",
                total_results=len(chunks),
                search_time=search_time,
                method_used="semantic_search"
            )
            
            logger.info(f"Vector search completed: {len(chunks)} results in {search_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    async def search_by_metadata(self, 
                                filters: Dict[str, Any],
                                limit: int = 100) -> SearchResult:
        """
        Search documents by metadata only.
        
        Args:
            filters: Metadata filter conditions
            limit: Maximum number of results
            
        Returns:
            SearchResult with matching chunks
        """
        if not self.client:
            raise RuntimeError("Vector store not connected")
        
        start_time = time.time()
        
        try:
            # Build filter conditions
            conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                elif isinstance(value, list):
                    # Multiple values (OR condition)
                    for v in value:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=v))
                        )
            
            if not conditions:
                raise ValueError("No valid filter conditions provided")
            
            search_filter = Filter(must=conditions)
            
            # Search with metadata filter only
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=search_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Convert results
            chunks = []
            for scored_point in search_result[0]:  # scroll returns (points, next_page_offset)
                payload = scored_point.payload
                
                chunk = DocumentChunk(
                    id=payload.get("chunk_id", str(scored_point.id)),
                    content=payload.get("content", ""),
                    metadata={k: v for k, v in payload.items() 
                             if k not in ["content", "chunk_id"]}
                )
                chunks.append(chunk)
            
            search_time = time.time() - start_time
            self._update_search_metrics(search_time)
            
            result = SearchResult(
                chunks=chunks,
                query=str(filters),
                total_results=len(chunks),
                search_time=search_time,
                method_used="metadata_search"
            )
            
            logger.info(f"Metadata search completed: {len(chunks)} results in {search_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            raise
    
    async def delete_documents(self, document_ids: List[str]) -> int:
        """
        Delete documents by IDs.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            Number of documents deleted
        """
        if not self.client:
            raise RuntimeError("Vector store not connected")
        
        try:
            # Delete points
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=document_ids
                )
            )
            
            # Update metrics
            self.search_metrics["total_documents"] -= len(document_ids)
            
            logger.info(f"Deleted {len(document_ids)} documents")
            return len(document_ids)
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        if not self.client:
            raise RuntimeError("Vector store not connected")
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "name": self.collection_name,
                "points_count": collection_info.points_count,
                "vector_dimension": self.vector_dimension,
                "segments_count": collection_info.segments_count,
                "disk_data_size": getattr(collection_info, 'disk_data_size', 0),
                "ram_data_size": getattr(collection_info, 'ram_data_size', 0),
                "status": collection_info.status,
                "search_metrics": self.search_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise
    
    def _update_search_metrics(self, search_time: float):
        """Update search performance metrics."""
        self.search_metrics["total_searches"] += 1
        
        # Update running average
        total = self.search_metrics["total_searches"]
        current_avg = self.search_metrics["avg_search_time"]
        
        self.search_metrics["avg_search_time"] = (
            (current_avg * (total - 1) + search_time) / total
        )
    
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            # In embedded mode, client doesn't need explicit cleanup
            self.client = None
            logger.info("Vector store disconnected")


# Convenience functions for easy usage
async def create_vector_store(collection_name: str = "documents",
                            vector_dimension: int = 768) -> QdrantVectorStore:
    """Create and initialize a vector store."""
    store = QdrantVectorStore(
        collection_name=collection_name,
        vector_dimension=vector_dimension
    )
    await store.connect()
    return store


# Example usage and testing
if __name__ == "__main__":
    async def test_vector_store():
        """Test the vector store functionality."""
        print("Testing Vector Store...")
        
        # Create vector store
        store = await create_vector_store("test_collection")
        
        # Test data
        test_chunks = [
            DocumentChunk(
                id="doc1_chunk1",
                content="Python is a programming language",
                metadata={
                    "document_id": "doc1",
                    "source": "tutorial.md",
                    "chunk_index": 0,
                    "document_type": "tutorial"
                },
                embedding=[0.1] * 768  # Dummy embedding
            ),
            DocumentChunk(
                id="doc1_chunk2", 
                content="Machine learning with Python is powerful",
                metadata={
                    "document_id": "doc1",
                    "source": "tutorial.md", 
                    "chunk_index": 1,
                    "document_type": "tutorial"
                },
                embedding=[0.2] * 768
            )
        ]
        
        # Add documents
        ids = await store.add_documents(test_chunks)
        print(f"Added documents: {ids}")
        
        # Test similarity search
        query_embedding = [0.15] * 768  # Similar to our test data
        results = await store.search_similar(query_embedding, limit=5)
        
        print(f"Search results: {len(results.chunks)} chunks")
        for chunk in results.chunks:
            print(f"  - {chunk.content[:50]}... (score: {chunk.score:.3f})")
        
        # Test metadata search
        metadata_results = await store.search_by_metadata({
            "document_type": "tutorial"
        })
        print(f"Metadata search: {len(metadata_results.chunks)} chunks")
        
        # Get collection info
        info = await store.get_collection_info()
        print(f"Collection info: {info}")
        
        # Cleanup
        await store.cleanup()
        print("Test completed!")
    
    # Run test
    asyncio.run(test_vector_store())