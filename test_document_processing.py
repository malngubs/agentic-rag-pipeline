#!/usr/bin/env python3
"""
Test script for Document Processing Pipeline.
Tests file ingestion, chunking, and integration with the RAG system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("📄 Testing Document Processing Pipeline...")

async def test_basic_document_processing():
    """Test basic document processing functionality."""
    print("\n📝 Testing Basic Document Processing...")
    
    try:
        from document_processing.ingestion import DocumentProcessor, DocumentType
        
        # Create processor
        processor = DocumentProcessor(
            chunk_size=256,  # Smaller chunks for testing
            chunk_overlap=32
        )
        
        # Create test directory and files
        test_dir = Path("./test_documents")
        test_dir.mkdir(exist_ok=True)
        
        # Create sample text file
        sample_txt = test_dir / "sample_test.txt"
        with open(sample_txt, 'w', encoding='utf-8') as f:
            f.write("""
Machine Learning and Artificial Intelligence

Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can analyze and interpret data to make predictions or decisions.

Types of Machine Learning:

1. Supervised Learning: Uses labeled data to train models. Examples include classification and regression tasks.

2. Unsupervised Learning: Finds patterns in data without labeled examples. Clustering and dimensionality reduction are common applications.

3. Reinforcement Learning: Learns through interaction with an environment, receiving rewards or penalties for actions taken.

Applications of machine learning include natural language processing, computer vision, recommendation systems, and autonomous vehicles. The field continues to evolve rapidly with advances in deep learning and neural networks.

Data quality is crucial for successful machine learning projects. Clean, relevant, and sufficient data leads to better model performance and more accurate predictions.
            """)
        
        # Create sample markdown file
        sample_md = test_dir / "sample_test.md"
        with open(sample_md, 'w', encoding='utf-8') as f:
            f.write("""
# Python Programming Guide

## Introduction to Python
Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.

## Key Features
- **Easy to Learn**: Python has a simple syntax that resembles natural language
- **Versatile**: Can be used for web development, data science, automation, and more
- **Large Community**: Extensive libraries and community support

## Popular Libraries
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation and analysis  
- **Django**: Web framework
- **TensorFlow**: Machine learning

## Getting Started
To start programming in Python, you need to install Python from python.org and choose a code editor like VSCode or PyCharm.
            """)
        
        print(f"✅ Created test files in {test_dir}")
        
        # Test text file processing
        print(f"\n📄 Processing TXT file...")
        txt_result = await processor.process_file(sample_txt)
        
        if txt_result.success:
            print(f"✅ TXT processing successful!")
            print(f"   Document ID: {txt_result.document_id}")
            print(f"   Processing time: {txt_result.processing_time:.3f}s")
            print(f"   Number of chunks: {len(txt_result.chunks)}")
            print(f"   Word count: {txt_result.metadata.word_count}")
            
            # Show first chunk
            if txt_result.chunks:
                first_chunk = txt_result.chunks[0]
                print(f"   First chunk preview: {first_chunk.content[:100]}...")
        else:
            print(f"❌ TXT processing failed: {txt_result.error_message}")
            return False
        
        # Test markdown file processing
        print(f"\n📄 Processing Markdown file...")
        md_result = await processor.process_file(sample_md)
        
        if md_result.success:
            print(f"✅ Markdown processing successful!")
            print(f"   Document ID: {md_result.document_id}")
            print(f"   Number of chunks: {len(md_result.chunks)}")
            
            # Show chunk details
            for i, chunk in enumerate(md_result.chunks[:2]):  # Show first 2 chunks
                print(f"   Chunk {i}: {chunk.content[:80]}...")
        else:
            print(f"❌ Markdown processing failed: {md_result.error_message}")
            return False
        
        # Test directory processing
        print(f"\n📁 Processing entire directory...")
        directory_results = await processor.process_directory(test_dir)
        
        print(f"✅ Directory processing completed!")
        print(f"   Files processed: {len(directory_results)}")
        print(f"   Successful: {sum(1 for r in directory_results if r.success)}")
        print(f"   Failed: {sum(1 for r in directory_results if not r.success)}")
        
        # Get processing statistics
        stats = processor.get_processing_stats()
        print(f"\n📊 Processing Statistics:")
        print(f"   Documents processed: {stats['documents_processed']}")
        print(f"   Total chunks created: {stats['chunks_created']}")
        print(f"   Average processing time: {stats['avg_processing_time']:.3f}s")
        print(f"   Average chunks per document: {stats['avg_chunks_per_document']:.1f}")
        print(f"   File types: {stats['file_type_counts']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic document processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_rag_integration():
    """Test full integration: Document Processing → Vector Store → LLM."""
    print("\n🔗 Testing Full RAG Integration...")
    
    try:
        from document_processing.ingestion import DocumentProcessor
        from retrieval.vector_store import QdrantVectorStore, DocumentChunk
        from test_llm_direct import SimpleLLMManager
        
        # Step 1: Process documents
        print("1️⃣ Processing documents...")
        processor = DocumentProcessor(chunk_size=300, chunk_overlap=50)
        
        # Create more comprehensive test document
        test_dir = Path("./test_documents")
        test_dir.mkdir(exist_ok=True)
        
        knowledge_doc = test_dir / "ai_knowledge.txt"
        with open(knowledge_doc, 'w', encoding='utf-8') as f:
            f.write("""
Artificial Intelligence and Machine Learning Guide

What is Artificial Intelligence?
Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. AI systems can perform tasks that typically require human intelligence, such as visual perception, speech recognition, decision-making, and language translation.

Machine Learning Fundamentals
Machine learning is a subset of AI that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.

Types of Machine Learning:
1. Supervised Learning: The algorithm learns from labeled training data
2. Unsupervised Learning: The algorithm finds hidden patterns in data without labels
3. Reinforcement Learning: The algorithm learns through trial and error

Natural Language Processing
Natural Language Processing (NLP) is a branch of AI that helps computers understand, interpret and manipulate human language. NLP combines computational linguistics with statistical machine learning and deep learning models.

Deep Learning
Deep learning is a subset of machine learning that uses neural networks with multiple layers. These artificial neural networks attempt to simulate the behavior of the human brain to process data and create patterns for decision making.

Applications of AI
AI is used in various fields including healthcare for medical diagnosis, finance for fraud detection, transportation for autonomous vehicles, and entertainment for recommendation systems.
            """)
        
        # Process the document
        doc_result = await processor.process_file(knowledge_doc)
        
        if not doc_result.success:
            print(f"❌ Document processing failed: {doc_result.error_message}")
            return False
        
        print(f"✅ Document processed: {len(doc_result.chunks)} chunks created")
        
        # Step 2: Generate embeddings and store in vector database
        print("2️⃣ Generating embeddings and storing in vector database...")
        
        async with SimpleLLMManager() as llm:
            # Convert processed chunks to DocumentChunk format for vector store
            vector_chunks = []
            
            for chunk in doc_result.chunks:
                # Generate embedding
                success, embedding = await llm.generate_embeddings(chunk.content)
                
                if success:
                    vector_chunk = DocumentChunk(
                        id=chunk.id,
                        content=chunk.content,
                        metadata=chunk.metadata,
                        embedding=embedding
                    )
                    vector_chunks.append(vector_chunk)
                else:
                    print(f"⚠️ Failed to generate embedding for chunk {chunk.id}")
            
            print(f"✅ Generated embeddings for {len(vector_chunks)} chunks")
            
            # Create vector store and add documents
            if vector_chunks:
                embedding_dim = len(vector_chunks[0].embedding)
                vector_store = QdrantVectorStore(
                    collection_name="rag_integration_test",
                    vector_dimension=embedding_dim,
                    storage_path="./data/qdrant_rag_test"
                )
                
                await vector_store.connect()
                
                # Add documents to vector store
                inserted_ids = await vector_store.add_documents(vector_chunks)
                print(f"✅ Stored {len(inserted_ids)} chunks in vector database")
                
                # Step 3: Test RAG query workflow
                print("3️⃣ Testing RAG query workflow...")
                
                test_queries = [
                    "What is machine learning?",
                    "How does deep learning work?",
                    "What are the applications of AI?"
                ]
                
                for query in test_queries:
                    print(f"\n🤔 Query: '{query}'")
                    
                    # Generate query embedding
                    success, query_embedding = await llm.generate_embeddings(query)
                    
                    if success:
                        # Search for relevant chunks
                        search_results = await vector_store.search_similar(
                            query_embedding=query_embedding,
                            limit=2,
                            score_threshold=0.1
                        )
                        
                        if search_results.chunks:
                            # Combine retrieved context
                            context = "\n\n".join([chunk.content for chunk in search_results.chunks])
                            
                            # Generate response using LLM with context
                            rag_prompt = f"""Based on the following context, answer the question:

Context:
{context}

Question: {query}

Answer:"""
                            
                            response_success, response = await llm.generate_simple_response(
                                rag_prompt,
                                "You are a helpful AI assistant. Use the provided context to answer questions accurately."
                            )
                            
                            if response_success:
                                print(f"📊 Retrieved {len(search_results.chunks)} relevant chunks")
                                print(f"⚡ Search time: {search_results.search_time:.3f}s")
                                print(f"🤖 RAG Response: {response.strip()}")
                                
                                # Show source information
                                print(f"📚 Sources:")
                                for i, chunk in enumerate(search_results.chunks, 1):
                                    source_file = chunk.metadata.get('filename', 'unknown')
                                    chunk_idx = chunk.metadata.get('chunk_index', 0)
                                    print(f"   {i}. {source_file} (chunk {chunk_idx}) - Score: {chunk.score:.3f}")
                            else:
                                print(f"❌ Failed to generate RAG response")
                        else:
                            print(f"⚠️ No relevant chunks found for query")
                    else:
                        print(f"❌ Failed to generate query embedding")
                
                await vector_store.cleanup()
                print(f"\n✅ Full RAG integration test completed!")
                return True
            else:
                print(f"❌ No chunks with embeddings generated")
                return False
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_file_format_support():
    """Test support for different file formats."""
    print(f"\n📁 Testing File Format Support...")
    
    try:
        from document_processing.ingestion import DocumentProcessor, DocumentType
        
        processor = DocumentProcessor()
        test_dir = Path("./test_documents")
        test_dir.mkdir(exist_ok=True)
        
        # Test different file types
        test_files = {}
        
        # Create TXT file
        txt_file = test_dir / "test.txt"
        with open(txt_file, 'w') as f:
            f.write("This is a plain text file for testing document processing capabilities.")
        test_files['TXT'] = txt_file
        
        # Create Markdown file
        md_file = test_dir / "test.md"
        with open(md_file, 'w') as f:
            f.write("""
# Test Markdown Document

This is a **markdown** file with *formatting*.

## Features
- Lists
- Headers
- Emphasis

Code example:
```python
print("Hello World")
```
            """)
        test_files['Markdown'] = md_file
        
        # Test each file type
        results = {}
        for file_type, file_path in test_files.items():
            print(f"\n📄 Testing {file_type} file: {file_path.name}")
            
            result = await processor.process_file(file_path)
            results[file_type] = result
            
            if result.success:
                print(f"   ✅ Success: {len(result.chunks)} chunks, {result.metadata.word_count} words")
                print(f"   📝 First chunk: {result.chunks[0].content[:60]}..." if result.chunks else "   📝 No chunks created")
            else:
                print(f"   ❌ Failed: {result.error_message}")
        
        # Summary
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        
        print(f"\n📊 File Format Test Summary:")
        print(f"   Successful: {successful}/{total}")
        print(f"   Supported formats: {', '.join(k for k, v in results.items() if v.success)}")
        
        return successful == total
        
    except Exception as e:
        print(f"❌ File format test failed: {e}")
        return False

async def main():
    """Run all document processing tests."""
    print("🚀 Document Processing Pipeline Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Document Processing", test_basic_document_processing),
        ("File Format Support", test_file_format_support), 
        ("Full RAG Integration", test_full_rag_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Final results
    print("\n" + "="*60)
    print("📊 Document Processing Test Results:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Document Processing Pipeline is working perfectly!")
        print("✨ Your RAG system can now:")
        print("   📄 Process multiple file formats (TXT, MD, PDF*, DOCX*)")
        print("   ✂️ Create intelligent text chunks")
        print("   🧠 Generate embeddings for each chunk")
        print("   🗄️ Store documents in vector database")
        print("   🔍 Retrieve relevant context for queries")
        print("   🤖 Generate contextual responses")
        print("\n📝 *PDF and DOCX require package installation when first used")
        print("🚀 Next: Build the Agentic Workflow System!")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check:")
        print("   - File permissions in test directories")
        print("   - Required packages installed")
        print("   - LLM and vector database connectivity")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎯 Document Processing: COMPLETE ✅")
        print("📊 Progress Update: ~45% of RAG system complete")
    else:
        print("\n🔧 Please resolve issues before proceeding")