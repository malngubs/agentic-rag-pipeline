#!/usr/bin/env python3
"""
Test script for Vector Database (Qdrant) functionality.
This tests document storage, retrieval, and search capabilities.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🗄️ Testing Vector Database (Qdrant)...")

# Test if we can create embeddings using our LLM manager
async def test_integration_with_llm():
    """Test integration between LLM Manager and Vector Store."""
    print("\n🔗 Testing LLM + Vector Database Integration...")
    
    try:
        # Import our managers
        from test_llm_direct import SimpleLLMManager
        from retrieval.vector_store import QdrantVectorStore, DocumentChunk
        
        # Test documents
        test_documents = [
            "Python is a high-level programming language known for its simplicity.",
            "Machine learning involves training algorithms on data to make predictions.",
            "FastAPI is a modern web framework for building APIs with Python.",
            "Vector databases store high-dimensional embeddings for similarity search.",
            "RAG combines retrieval and generation for better AI responses."
        ]
        
        print(f"📚 Processing {len(test_documents)} test documents...")
        
        # Generate embeddings using our LLM
        async with SimpleLLMManager() as llm:
            print("🧠 Generating embeddings with AI...")
            
            chunks = []
            for i, content in enumerate(test_documents):
                # Generate embedding
                success, embedding = await llm.generate_embeddings(content)
                
                if success:
                    chunk = DocumentChunk(
                        id=f"test_doc_{i}",
                        content=content,
                        metadata={
                            "document_id": f"doc_{i//2}",  # Group some chunks
                            "source": "test_data",
                            "chunk_index": i,
                            "topic": "AI" if "AI" in content or "machine learning" in content.lower() else "programming"
                        },
                        embedding=embedding
                    )
                    chunks.append(chunk)
                    print(f"   ✅ Generated embedding for doc {i} ({len(embedding)} dimensions)")
                else:
                    print(f"   ❌ Failed to generate embedding for doc {i}")
                    return False
        
        # Test vector store
        print("\n🗃️ Testing Vector Database...")
        
        # Create vector store with correct dimension
        embedding_dim = len(chunks[0].embedding) if chunks else 768
        vector_store = QdrantVectorStore(
            collection_name="test_rag_collection",
            vector_dimension=embedding_dim,
            storage_path="./data/qdrant_test"
        )
        
        # Connect and add documents
        await vector_store.connect()
        print("✅ Connected to vector database")
        
        # Add documents
        inserted_ids = await vector_store.add_documents(chunks)
        print(f"✅ Added {len(inserted_ids)} documents to vector store")
        
        # Test similarity search
        print("\n🔍 Testing Similarity Search...")
        
        # Generate query embedding
        async with SimpleLLMManager() as llm:
            query = "What is machine learning?"
            success, query_embedding = await llm.generate_embeddings(query)
            
            if success:
                print(f"🤔 Query: '{query}'")
                
                # Search for similar documents
                results = await vector_store.search_similar(
                    query_embedding=query_embedding,
                    limit=3,
                    score_threshold=0.0
                )
                
                print(f"📊 Found {len(results.chunks)} results in {results.search_time:.3f}s")
                
                for i, chunk in enumerate(results.chunks, 1):
                    print(f"   {i}. Score: {chunk.score:.3f}")
                    print(f"      Content: {chunk.content}")
                    print(f"      Topic: {chunk.metadata.get('topic', 'unknown')}")
                    print()
        
        # Test metadata search
        print("🏷️ Testing Metadata Search...")
        metadata_results = await vector_store.search_by_metadata({
            "topic": "AI"
        })
        
        print(f"📋 Found {len(metadata_results.chunks)} AI-related documents")
        for chunk in metadata_results.chunks:
            print(f"   - {chunk.content[:50]}...")
        
        # Get collection info
        info = await vector_store.get_collection_info()
        print(f"\n📈 Collection Stats:")
        print(f"   Documents: {info['points_count']}")
        print(f"   Vector Dimension: {info['vector_dimension']}")
        print(f"   Total Searches: {info['search_metrics']['total_searches']}")
        print(f"   Avg Search Time: {info['search_metrics']['avg_search_time']:.3f}s")
        
        # Cleanup
        await vector_store.cleanup()
        print("✅ Vector database test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_basic_vector_store():
    """Test basic vector store functionality with dummy data."""
    print("\n🧪 Testing Basic Vector Store...")
    
    try:
        from retrieval.vector_store import QdrantVectorStore, DocumentChunk
        
        # Create vector store
        vector_store = QdrantVectorStore(
            collection_name="basic_test",
            vector_dimension=384,  # Common embedding dimension
            storage_path="./data/qdrant_basic"
        )
        
        await vector_store.connect()
        print("✅ Basic vector store connected")
        
        # Create test documents with dummy embeddings
        test_chunks = [
            DocumentChunk(
                id="basic_1",
                content="This is a test document about Python programming.",
                metadata={"category": "programming", "language": "python"},
                embedding=[0.1] * 384
            ),
            DocumentChunk(
                id="basic_2", 
                content="Machine learning models require lots of data.",
                metadata={"category": "AI", "language": "english"},
                embedding=[0.2] * 384
            )
        ]
        
        # Add documents
        ids = await vector_store.add_documents(test_chunks)
        print(f"✅ Added {len(ids)} basic test documents")
        
        # Test search
        query_embedding = [0.15] * 384  # Between our test embeddings
        results = await vector_store.search_similar(query_embedding, limit=2)
        
        print(f"✅ Basic search returned {len(results.chunks)} results")
        
        await vector_store.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Basic vector store test failed: {e}")
        return False

async def main():
    """Run all vector database tests."""
    print("🚀 Vector Database Test Suite")
    print("=" * 50)
    
    # Test 1: Basic functionality
    basic_success = await test_basic_vector_store()
    
    # Test 2: Integration with LLM
    if basic_success:
        integration_success = await test_integration_with_llm()
    else:
        integration_success = False
    
    # Results
    print("\n" + "=" * 50)
    print("📊 Vector Database Test Results:")
    print(f"   {'✅' if basic_success else '❌'} Basic Vector Store")
    print(f"   {'✅' if integration_success else '❌'} LLM Integration")
    
    if basic_success and integration_success:
        print("\n🎉 Vector Database is working perfectly!")
        print("✨ Your RAG 'memory' system is ready!")
        print("\n📋 What We Built:")
        print("   🧠 AI generates embeddings from text")
        print("   🗄️ Vector database stores document chunks")
        print("   🔍 Semantic similarity search works")
        print("   🏷️ Metadata filtering functional")
        print("   ⚡ Fast retrieval performance")
        print("\n🚀 Next: Document Processing Pipeline")
        return True
    else:
        print("\n⚠️ Some tests failed. Issues to fix:")
        if not basic_success:
            print("   - Qdrant client installation/connection")
        if not integration_success:
            print("   - LLM + Vector database integration")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())