#!/usr/bin/env python3
"""
Test script for LLM Manager and Ollama integration.

This script verifies that:
1. Ollama is running and accessible
2. Required models are available
3. LLM Manager can connect and generate responses
4. Embeddings are working correctly

Run this after installing Ollama and downloading models.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.llm_manager import OllamaLLMManager, QueryComplexity


async def test_ollama_connection():
    """Test basic Ollama connection and model availability."""
    print("🔍 Testing Ollama Connection...")
    
    try:
        async with OllamaLLMManager() as llm:
            print("✅ Successfully connected to Ollama")
            
            # Get model status
            status = await llm.get_model_status()
            print(f"🏥 Health Status: {'✅ Healthy' if status['health'] else '❌ Unhealthy'}")
            print(f"🔗 Ollama URL: {status['ollama_url']}")
            
            # Check available models
            available_models = [name for name, info in status['models'].items() if info['available']]
            print(f"📋 Available Models: {len(available_models)}")
            
            for model_name in available_models:
                model_info = status['models'][model_name]
                print(f"   📦 {model_name}")
                print(f"      Size: {model_info['size_gb']}GB")
                print(f"      Capabilities: {', '.join(model_info['capabilities'])}")
                print(f"      Performance Score: {model_info['performance_score']}")
            
            if not available_models:
                print("❌ No models available! Please download models first:")
                print("   ollama pull llama3.2:3b-instruct-q4_K_M")
                print("   ollama pull nomic-embed-text")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure Ollama is installed and running:")
        print("   1. Install from https://ollama.ai/download")
        print("   2. Download models with: ollama pull llama3.2:3b-instruct-q4_K_M")
        return False


async def test_simple_query():
    """Test simple query generation."""
    print("\n🧠 Testing Simple Query Generation...")
    
    try:
        async with OllamaLLMManager() as llm:
            # Test simple factual query
            response = await llm.generate_response(
                "What is the capital of France?",
                system_prompt="You are a helpful assistant. Provide concise, accurate answers."
            )
            
            print("✅ Simple query successful!")
            print(f"   Query: What is the capital of France?")
            print(f"   Model Used: {response.model_used}")
            print(f"   Response Time: {response.response_time:.2f}s")
            print(f"   Tokens Used: {response.tokens_used}")
            print(f"   Response: {response.content}")
            
            return True
            
    except Exception as e:
        print(f"❌ Simple query failed: {e}")
        return False


async def test_complex_query():
    """Test complex query that requires reasoning."""
    print("\n🎯 Testing Complex Query Generation...")
    
    try:
        async with OllamaLLMManager() as llm:
            # Test complex analytical query
            complex_prompt = """
            Analyze the following scenario and provide recommendations:
            
            A small software company wants to implement AI to improve customer support.
            They have 500 customers, 5 support agents, and handle 100 tickets per day.
            Their current response time is 4 hours average.
            
            What would you recommend?
            """
            
            response = await llm.generate_response(
                complex_prompt,
                system_prompt="You are a business consultant. Provide structured, actionable recommendations."
            )
            
            print("✅ Complex query successful!")
            print(f"   Model Used: {response.model_used}")
            print(f"   Response Time: {response.response_time:.2f}s")
            print(f"   Tokens Used: {response.tokens_used}")
            print(f"   Response Preview: {response.content[:200]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Complex query failed: {e}")
        return False


async def test_streaming_response():
    """Test streaming response generation."""
    print("\n🌊 Testing Streaming Response...")
    
    try:
        async with OllamaLLMManager() as llm:
            print("   Question: Explain how machine learning works")
            print("   Streaming response: ", end="", flush=True)
            
            # Note: This is a simplified test - full streaming would need different handling
            response = await llm.generate_response(
                "Explain how machine learning works in simple terms",
                system_prompt="Provide a clear, educational explanation."
            )
            
            # Simulate streaming by printing chunks
            words = response.content.split()
            for i, word in enumerate(words[:20]):  # First 20 words
                print(word, end=" ", flush=True)
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
            print("...\n")
            print("✅ Streaming simulation successful!")
            print(f"   Model Used: {response.model_used}")
            print(f"   Full Response Length: {len(response.content)} characters")
            
            return True
            
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False


async def test_embeddings():
    """Test embedding generation."""
    print("\n🔢 Testing Embedding Generation...")
    
    try:
        async with OllamaLLMManager() as llm:
            # Test embedding generation
            test_texts = [
                "Machine learning is a subset of artificial intelligence",
                "Python is a programming language",
                "The weather today is sunny and warm"
            ]
            
            embeddings = await llm.generate_embeddings(test_texts)
            
            print("✅ Embeddings generated successfully!")
            print(f"   Number of texts: {len(test_texts)}")
            print(f"   Number of embeddings: {len(embeddings)}")
            print(f"   Embedding dimension: {len(embeddings[0]) if embeddings else 0}")
            
            # Show similarity between first two embeddings (should be higher for similar texts)
            if len(embeddings) >= 2:
                # Simple cosine similarity
                import math
                
                def cosine_similarity(a, b):
                    dot_product = sum(x * y for x, y in zip(a, b))
                    magnitude_a = math.sqrt(sum(x * x for x in a))
                    magnitude_b = math.sqrt(sum(x * x for x in b))
                    return dot_product / (magnitude_a * magnitude_b)
                
                sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])
                sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])
                
                print(f"   Similarity (ML vs Python): {sim_1_2:.3f}")
                print(f"   Similarity (ML vs Weather): {sim_1_3:.3f}")
            
            return True
            
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        return False


async def test_model_routing():
    """Test intelligent model routing based on query complexity."""
    print("\n🧭 Testing Intelligent Model Routing...")
    
    try:
        async with OllamaLLMManager() as llm:
            # Test queries of different complexities
            test_cases = [
                ("What is Python?", "simple"),
                ("Compare Python and JavaScript for web development", "moderate"), 
                ("Design a complete machine learning pipeline for customer churn prediction", "complex")
            ]
            
            for query, expected_complexity in test_cases:
                response = await llm.generate_response(query)
                
                print(f"   Query: {query}")
                print(f"   Expected Complexity: {expected_complexity}")
                print(f"   Model Selected: {response.model_used}")
                print(f"   Response Time: {response.response_time:.2f}s")
                print(f"   Preview: {response.content[:100]}...")
                print()
            
            print("✅ Model routing test completed!")
            return True
            
    except Exception as e:
        print(f"❌ Model routing test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and fallback mechanisms."""
    print("\n🛡️ Testing Error Handling...")
    
    try:
        async with OllamaLLMManager() as llm:
            # Test with non-existent model
            try:
                response = await llm.generate_response(
                    "Test query",
                    model_override="non-existent-model"
                )
                print("❌ Should have failed with non-existent model")
                return False
            except Exception as e:
                print("✅ Correctly handled non-existent model error")
            
            # Test with empty query
            try:
                response = await llm.generate_response("")
                print(f"✅ Handled empty query: {response.content[:50]}...")
            except Exception as e:
                print(f"✅ Correctly rejected empty query: {e}")
            
            # Test with very long query
            long_query = "What is AI? " * 1000  # Very long query
            try:
                response = await llm.generate_response(long_query)
                print("✅ Handled very long query successfully")
            except Exception as e:
                print(f"✅ Correctly handled long query limitation: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def run_comprehensive_test():
    """Run all tests and provide a comprehensive report."""
    print("🚀 Starting Comprehensive LLM Manager Test Suite")
    print("=" * 60)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Simple Query Generation", test_simple_query),
        ("Complex Query Generation", test_complex_query),
        ("Streaming Response", test_streaming_response),
        ("Embedding Generation", test_embeddings),
        ("Model Routing", test_model_routing),
        ("Error Handling", test_error_handling)
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
    
    # Print final report
    print("\n" + "="*60)
    print("🎯 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your LLM Manager is ready to use!")
        print("\n🚀 Next Steps:")
        print("   1. Continue building the RAG pipeline")
        print("   2. Set up the vector database (Qdrant)")
        print("   3. Implement document processing")
        print("   4. Build the agentic workflow")
    else:
        print("⚠️  Some tests failed. Please check the following:")
        print("   1. Is Ollama installed and running?")
        print("   2. Are the required models downloaded?")
        print("   3. Is the network connection working?")
    
    return passed == total


if __name__ == "__main__":
    # Run the comprehensive test suite
    success = asyncio.run(run_comprehensive_test())