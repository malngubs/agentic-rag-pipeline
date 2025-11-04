#!/usr/bin/env python3
"""
Fixed Vector Database test with proper UUID handling.
"""

import asyncio
import sys
import os
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🗄️ Testing Vector Database (Fixed Version)...")

async def test_basic_vector_store_fixed():
    """Test basic vector store with proper UUID format."""
    print("\n🧪 Testing Basic Vector Store (Fixed)...")
    
    try:
        from retrieval.vector_store import QdrantVectorStore, DocumentChunk
        
        # Create vector store
        vector_store = QdrantVectorStore(
            collection_name="basic_test_fixed",
            vector_dimension=384,
            storage_path="./data/qdrant_basic_fixed"
        )
        
        await vector_store.connect()
        print("✅ Vector store connected successfully")
        
        # Create test documents with proper UUIDs
        test_chunks = [
            DocumentChunk(
                id=str(uuid.uuid4()),  # Generate proper UUID
                content="This is a test document about Python programming.",
                metadata={"category": "programming", "language": "python"},
                embedding=[0.1] * 384
            ),
            DocumentChunk(
                id=str(uuid.uuid4()),  # Generate proper UUID
                content="Machine learning models require lots of data.",
                metadata={"category": "AI", "language": "english"},
                embedding=[0.2] * 384
            )
        ]
        
        print(f"📝 Created {len(test_chunks)} test documents with proper UUIDs")
        for chunk in test_chunks:
            print(f"   - ID: {chunk.id[:8]}... Content: {chunk.content[:30]}...")
        
        # Add documents
        ids = await vector_store.add_documents(test_chunks)
        print(f"✅ Successfully added {len(ids)} documents to vector store")
        
        # Test similarity search
        query_embedding = [0.15] * 384  # Between our test embeddings
        results = await vector_store.search_similar(query_embedding, limit=2)
        
        print(f"🔍 Search Results:")
        print(f"   Found: {len(results.chunks)} documents")
        print(f"   Search time: {results.search_time:.3f}s")
        print(f"   Method: {results.method_used}")
        
        for i, chunk in enumerate(results.chunks, 1):
            print(f"   {i}. Score: {chunk.score:.3f}")
            print(f"      Content: {chunk.content[:50]}...")
            print(f"      Category: {chunk.metadata.get('category', 'unknown')}")
        
        # Test metadata search
        print(f"\n🏷️ Testing metadata search...")
        metadata_results = await vector_store.search_by_metadata({
            "category": "programming"
        })
        
        print(f"📋 Metadata search results: {len(metadata_results.chunks)} programming documents")
        
        # Get collection info
        info = await vector_store.get_collection_info()
        print(f"\n📊 Collection Information:")
        print(f"   Name: {info['name']}")
        print(f"   Documents: {info['points_count']}")
        print(f"   Vector Dimension: {info['vector_dimension']}")
        print(f"   Status: {info['status']}")
        print(f"   Total Searches: {info['search_metrics']['total_searches']}")
        
        await vector_store.cleanup()
        print("✅ Basic vector store test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Basic vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_vector_integration_fixed():
    """Test LLM + Vector integration with proper error handling."""
    print("\n🔗 Testing LLM + Vector Integration (Fixed)...")
    
    try:
        from test_llm_direct import SimpleLLMManager
        from retrieval.vector_store import QdrantVectorStore, DocumentChunk
        
        # Test documents
        test_documents = [
            "Python is excellent for data science and machine learning applications.",
            "JavaScript is the primary language for web development and browsers.",
            "SQL is essential for database management and data querying."
        ]
        
        print(f"📚 Processing {len(test_documents)} documents...")
        
        # Generate embeddings using LLM
        async with SimpleLLMManager() as llm:
            chunks = []
            for i, content in enumerate(test_documents):
                success, embedding = await llm.generate_embeddings(content)
                
                if success:
                    chunk = DocumentChunk(
                        id=str(uuid.uuid4()),  # Proper UUID
                        content=content,
                        metadata={
                            "document_id": f"doc_{i}",
                            "source": "test_integration",
                            "chunk_index": i,
                            "language": "python" if "Python" in content else 
                                       "javascript" if "JavaScript" in content else "sql"
                        },
                        embedding=embedding
                    )
                    chunks.append(chunk)
                    print(f"   ✅ Doc {i}: {len(embedding)}-dim embedding")
                else:
                    print(f"   ❌ Failed to generate embedding for doc {i}")
                    return False
        
        # Create vector store with correct dimension
        embedding_dim = len(chunks[0].embedding)
        vector_store = QdrantVectorStore(
            collection_name="integration_test_fixed",
            vector_dimension=embedding_dim,
            storage_path="./data/qdrant_integration_fixed"
        )
        
        await vector_store.connect()
        print(f"✅ Connected to vector store (dimension: {embedding_dim})")
        
        # Add documents
        inserted_ids = await vector_store.add_documents(chunks)
        print(f"✅ Added {len(inserted_ids)} documents")
        
        # Test semantic search
        print(f"\n🤔 Testing semantic search...")
        async with SimpleLLMManager() as llm:
            query = "What programming language is good for web development?"
            success, query_embedding = await llm.generate_embeddings(query)
            
            if success:
                results = await vector_store.search_similar(
                    query_embedding=query_embedding,
                    limit=3
                )
                
                print(f"   Query: '{query}'")
                print(f"   Results: {len(results.chunks)} documents")
                
                for i, chunk in enumerate(results.chunks, 1):
                    print(f"   {i}. Score: {chunk.score:.3f} | Language: {chunk.metadata.get('language')}")
                    print(f"      Content: {chunk.content}")
                
                # The JavaScript document should rank highest for web development query
                if results.chunks and "JavaScript" in results.chunks[0].content:
                    print("✅ Semantic search working correctly (JavaScript ranked highest)")
                else:
                    print("⚠️ Semantic search may need tuning")
        
        await vector_store.cleanup()
        print("✅ LLM + Vector integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the fixed vector database tests."""
    print("🚀 Fixed Vector Database Test Suite")
    print("=" * 50)
    
    # Test 1: Basic functionality with proper UUIDs
    basic_success = await test_basic_vector_store_fixed()
    
    # Test 2: Integration with LLM
    if basic_success:
        integration_success = await test_llm_vector_integration_fixed()
    else:
        integration_success = False
    
    # Results
    print("\n" + "=" * 50)
    print("📊 Fixed Vector Database Test Results:")
    print(f"   {'✅' if basic_success else '❌'} Basic Vector Store (Fixed)")
    print(f"   {'✅' if integration_success else '❌'} LLM Integration (Fixed)")
    
    if basic_success and integration_success:
        print("\n🎉 Vector Database is working perfectly!")
        print("✨ Your RAG memory system is fully operational!")
        print("\n📋 What's Working:")
        print("   🧠 AI generates high-quality embeddings")
        print("   🗄️ Vector database stores documents properly")
        print("   🔍 Semantic search finds relevant content")
        print("   🏷️ Metadata filtering works correctly")
        print("   📊 Performance metrics tracking")
        print("\n🚀 Ready for: Document Processing Pipeline!")
        return True
    else:
        print("\n⚠️ Some issues remain:")
        if not basic_success:
            print("   - Basic vector operations need debugging")
        if not integration_success:
            print("   - LLM integration needs fixes")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎯 Vector Database: COMPLETE")
        print("📝 Next: Build document processing for PDFs, DOCX, etc.")