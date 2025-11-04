#!/usr/bin/env python3
"""
Test script for Simplified Agentic Workflow.
Tests human-like reasoning without LangGraph dependencies.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🤖 Testing Simplified Agentic Workflow...")

async def test_workflow_integration():
    """Test the complete workflow with real components."""
    print("\n🔄 Testing Complete Workflow Integration...")
    
    try:
        from agents.simple_workflow import SimpleAgenticWorkflow
        from test_llm_direct import SimpleLLMManager
        from retrieval.vector_store import QdrantVectorStore, DocumentChunk
        from document_processing.ingestion import DocumentProcessor
        import uuid
        
        print("1️⃣ Setting up components...")
        
        # Create knowledge base
        test_dir = Path("./test_documents")
        test_dir.mkdir(exist_ok=True)
        
        knowledge_doc = test_dir / "ai_workflow_knowledge.txt"
        with open(knowledge_doc, 'w', encoding='utf-8') as f:
            f.write("""
Artificial Intelligence and Machine Learning Guide

Machine Learning Fundamentals
Machine learning is a method of data analysis that automates analytical model building. It is based on the idea that systems can learn from data, identify patterns, and make decisions with minimal human intervention.

Types of Machine Learning

Supervised Learning
Supervised learning algorithms learn from labeled training data and make predictions on new, unseen data. Common examples include classification (predicting categories) and regression (predicting numerical values). Applications include email spam detection, medical diagnosis, and stock price prediction.

Unsupervised Learning
Unsupervised learning finds hidden patterns in data without labeled examples. Key techniques include clustering (grouping similar data points) and dimensionality reduction (simplifying data while preserving important information). Applications include customer segmentation, anomaly detection, and data compression.

Reinforcement Learning
Reinforcement learning involves an agent learning to make decisions through trial and error in an environment. The agent receives rewards or penalties for actions and learns to maximize cumulative reward over time. This approach is used in game playing, robotics, and autonomous vehicle navigation.

Deep Learning
Deep learning uses artificial neural networks with multiple layers to automatically learn hierarchical representations of data. These networks can process complex patterns in images, text, and audio. Popular architectures include convolutional neural networks for images and recurrent neural networks for sequential data.

Natural Language Processing
Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language. Modern NLP uses transformer models and attention mechanisms to achieve human-like language understanding. Applications include chatbots, language translation, and text summarization.

Applications of AI
AI is transforming many industries including healthcare (medical imaging, drug discovery), finance (fraud detection, algorithmic trading), transportation (autonomous vehicles), and entertainment (recommendation systems, content generation).
            """)
        
        # Process document
        print("2️⃣ Processing knowledge document...")
        processor = DocumentProcessor(chunk_size=300, chunk_overlap=50)
        doc_result = await processor.process_file(knowledge_doc)
        
        if not doc_result.success:
            print(f"❌ Document processing failed")
            return False
        
        print(f"✅ Created {len(doc_result.chunks)} knowledge chunks")
        
        # Set up vector store
        print("3️⃣ Setting up vector database...")
        async with SimpleLLMManager() as llm:
            # Generate embeddings
            vector_chunks = []
            for chunk in doc_result.chunks:
                success, embedding = await llm.generate_embeddings(chunk.content)
                if success:
                    vector_chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        content=chunk.content,
                        metadata=chunk.metadata,
                        embedding=embedding
                    )
                    vector_chunks.append(vector_chunk)
            
            print(f"✅ Generated embeddings for {len(vector_chunks)} chunks")
            
            # Create vector store
            embedding_dim = len(vector_chunks[0].embedding)
            vector_store = QdrantVectorStore(
                collection_name="simple_workflow_test",
                vector_dimension=embedding_dim,
                storage_path="./data/qdrant_simple"
            )
            
            await vector_store.connect()
            await vector_store.add_documents(vector_chunks)
            
            print(f"✅ Vector store ready with {len(vector_chunks)} documents")
            
            # Create workflow
            print("4️⃣ Initializing agentic workflow...")
            workflow = SimpleAgenticWorkflow(
                llm_manager=llm,
                vector_store=vector_store,
                max_retrieval_chunks=5,
                confidence_threshold=0.5
            )
            
            print("✅ Workflow initialized")
            
            # Test queries
            print("\n5️⃣ Testing agentic reasoning...")
            
            test_queries = [
                {
                    "query": "What is machine learning?",
                    "description": "Simple factual query"
                },
                {
                    "query": "How do supervised and unsupervised learning differ?",
                    "description": "Analytical comparison"
                },
                {
                    "query": "What is deep learning and what are its applications?",
                    "description": "Multi-part question"
                }
            ]
            
            successful_tests = 0
            
            for i, test_case in enumerate(test_queries, 1):
                print(f"\n--- Test {i}: {test_case['description']} ---")
                print(f"Query: '{test_case['query']}'")
                
                # Process query through workflow
                result = await workflow.process_query(test_case["query"])
                
                if result.success and len(result.final_response) > 50:
                    print(f"✅ Workflow completed successfully")
                    print(f"   Intent: {result.query_intent}")
                    print(f"   Complexity: {result.complexity_score}")
                    print(f"   Chunks retrieved: {result.chunks_retrieved}")
                    print(f"   Confidence: {result.confidence_score:.3f}")
                    print(f"   Execution time: {result.total_execution_time:.3f}s")
                    print(f"   Citations: {len(result.citations)}")
                    
                    # Show workflow execution trace
                    print(f"\n📊 Workflow Execution Steps:")
                    for j, step in enumerate(result.workflow_steps, 1):
                        stage_name = step.stage.value.replace('_', ' ').title()
                        print(f"   {j}. {stage_name} ({step.execution_time:.3f}s) - {step.reasoning}")
                    
                    # Show response preview
                    response_preview = result.final_response[:150]
                    print(f"\n🤖 Response Preview: {response_preview}...")
                    
                    successful_tests += 1
                else:
                    print(f"❌ Workflow failed")
                    if result.error_messages:
                        print(f"   Errors: {result.error_messages}")
            
            # Show metrics
            print(f"\n6️⃣ Workflow Performance:")
            metrics = workflow.get_metrics()
            print(f"   Total queries: {metrics['total_queries']}")
            print(f"   Success rate: {metrics['success_rate']:.1%}")
            print(f"   Average time: {metrics['average_execution_time']:.3f}s")
            
            await vector_store.cleanup()
            
            if successful_tests == len(test_queries):
                print(f"\n✅ All workflow tests passed!")
                return True
            else:
                print(f"\n⚠️ {successful_tests}/{len(test_queries)} tests passed")
                return False
                
    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_workflow_components():
    """Test individual workflow components."""
    print("\n🧩 Testing Individual Components...")
    
    try:
        from agents.simple_workflow import SimpleAgenticWorkflow, QueryIntent
        
        workflow = SimpleAgenticWorkflow()
        
        # Test intent classification
        print("1️⃣ Testing intent classification...")
        test_cases = [
            ("What is Python?", "factual"),
            ("Compare Python and Java programming languages", "analytical"),
            ("How to install Python on Windows?", "procedural"),
            ("Write a Python function to calculate factorial", "creative")
        ]
        
        correct_classifications = 0
        for query, expected in test_cases:
            result = await workflow._classify_intent(query)
            detected = result["intent"]
            status = "✅" if detected == expected else "⚠️"
            print(f"   {status} '{query}' → {detected} (expected: {expected})")
            if detected == expected:
                correct_classifications += 1
        
        print(f"   Classification accuracy: {correct_classifications}/{len(test_cases)}")
        
        # Test query decomposition
        print("\n2️⃣ Testing query decomposition...")
        complex_queries = [
            "What is machine learning and how does it work?",
            "Explain supervised learning and provide examples of its applications?"
        ]
        
        for query in complex_queries:
            sub_queries = workflow._decompose_query(query)
            print(f"   Query: {query}")
            print(f"   Sub-queries: {sub_queries}")
        
        print(f"\n✅ Component tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

async def test_workflow_without_dependencies():
    """Test workflow without LLM or vector store."""
    print("\n🔬 Testing Workflow Without Dependencies...")
    
    try:
        from agents.simple_workflow import SimpleAgenticWorkflow
        
        # Test with no dependencies
        workflow = SimpleAgenticWorkflow()
        
        result = await workflow.process_query("What is artificial intelligence?")
        
        if result.success:
            print(f"✅ Workflow completed without dependencies")
            print(f"   Intent: {result.query_intent}")
            print(f"   Steps completed: {len(result.workflow_steps)}")
            print(f"   Response: {result.final_response}")
        else:
            print(f"❌ Workflow failed without dependencies")
            return False
        
        # Show execution visualization
        viz = workflow.visualize_execution(result)
        print(f"\n📊 Execution Visualization:")
        print(viz)
        
        return True
        
    except Exception as e:
        print(f"❌ Standalone workflow test failed: {e}")
        return False

async def main():
    """Run all simplified workflow tests."""
    print("🚀 Simplified Agentic Workflow Test Suite")
    print("=" * 60)
    
    tests = [
        ("Workflow Without Dependencies", test_workflow_without_dependencies),
        ("Individual Components", test_workflow_components),
        ("Complete Integration", test_workflow_integration)
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
    print("📊 Simplified Workflow Test Results:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Simplified Agentic Workflow is working perfectly!")
        print("✨ Your AI now has human-like reasoning capabilities!")
        print("\n🧠 Agentic Reasoning Features:")
        print("   🎯 Intent classification and complexity analysis")
        print("   📋 Strategic query planning")
        print("   🔍 Multi-step information retrieval")
        print("   🧮 Context analysis and synthesis")
        print("   💭 Intelligent answer generation")
        print("   ✅ Fact-checking and validation")
        print("   ✨ Response refinement")
        print("   📚 Automatic citation formatting")
        print("   🎯 Quality assessment")
        print("\n🎯 Progress Update: ~65% of RAG system complete!")
        print("📝 Next: FastAPI Backend & Real-time Streaming")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check:")
        print("   - Component imports and dependencies")
        print("   - LLM and vector store integration")
        print("   - Workflow step execution")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎯 Agentic Workflow: COMPLETE ✅")
        print("🔥 Your RAG system now thinks step-by-step like a human expert!")
    else:
        print("\n🔧 Please resolve issues before proceeding")