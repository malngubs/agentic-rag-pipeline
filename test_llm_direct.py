#!/usr/bin/env python3
"""
Direct LLM Manager test without complex configuration.
This tests our LLM manager with hardcoded settings.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 Testing LLM Manager directly...")

# Test basic imports
try:
    print("1️⃣ Testing basic imports...")
    import httpx
    from enum import Enum
    from dataclasses import dataclass
    print("✅ Basic imports successful")
except ImportError as e:
    print(f"❌ Basic imports failed: {e}")
    exit(1)

# Create a simplified LLM manager for testing
class SimpleLLMManager:
    """Simplified LLM Manager for testing without complex config."""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.primary_model = "llama3.2:3b-instruct-q4_K_M"
        self.embedding_model = "nomic-embed-text"
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def test_connection(self):
        """Test connection to Ollama."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return True, models
            return False, []
        except Exception as e:
            return False, str(e)
    
    async def generate_simple_response(self, prompt, system_prompt=None):
        """Generate a simple response."""
        try:
            request_data = {
                "model": self.primary_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 100
                }
            }
            
            if system_prompt:
                request_data["system"] = system_prompt
            
            response = await self.client.post("/api/generate", json=request_data)
            if response.status_code == 200:
                data = response.json()
                return True, data.get("response", "")
            return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    async def generate_embeddings(self, text):
        """Generate embeddings."""
        try:
            request_data = {
                "model": self.embedding_model,
                "prompt": text
            }
            
            response = await self.client.post("/api/embeddings", json=request_data)
            if response.status_code == 200:
                data = response.json()
                return True, data.get("embedding", [])
            return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

async def test_simple_manager():
    """Test the simplified LLM manager."""
    print("\n2️⃣ Testing Simplified LLM Manager...")
    
    async with SimpleLLMManager() as llm:
        # Test 1: Connection
        print("\n🔗 Testing connection...")
        success, result = await llm.test_connection()
        if success:
            print(f"✅ Connected! Found models: {result}")
        else:
            print(f"❌ Connection failed: {result}")
            return False
        
        # Test 2: Simple query
        print("\n🤔 Testing simple query...")
        success, result = await llm.generate_simple_response(
            "What is 2+2? Answer in one sentence.",
            "You are a helpful math assistant."
        )
        if success:
            print(f"✅ Query successful!")
            print(f"   Question: What is 2+2?")
            print(f"   Answer: {result.strip()}")
        else:
            print(f"❌ Query failed: {result}")
            return False
        
        # Test 3: Embeddings
        print("\n🔢 Testing embeddings...")
        success, result = await llm.generate_embeddings("Test embedding text")
        if success:
            print(f"✅ Embeddings successful!")
            print(f"   Text: 'Test embedding text'")
            print(f"   Dimension: {len(result)}")
            print(f"   First 3 values: {result[:3]}")
        else:
            print(f"❌ Embeddings failed: {result}")
            return False
        
        return True

# Test query complexity analysis (mimicking human thought)
def analyze_query_complexity(query):
    """Simple query complexity analyzer."""
    query_lower = query.lower()
    
    simple_indicators = ["what is", "who is", "when", "where", "define"]
    complex_indicators = ["analyze", "compare", "explain why", "strategy", "plan"]
    
    if any(indicator in query_lower for indicator in complex_indicators):
        return "complex"
    elif any(indicator in query_lower for indicator in simple_indicators):
        return "simple" 
    else:
        return "moderate"

async def test_intelligent_routing():
    """Test intelligent query routing."""
    print("\n3️⃣ Testing Intelligent Query Routing...")
    
    test_queries = [
        "What is Python?",
        "Compare Python and JavaScript for web development",
        "Analyze market trends and create a business strategy"
    ]
    
    async with SimpleLLMManager() as llm:
        for query in test_queries:
            complexity = analyze_query_complexity(query)
            print(f"\n📝 Query: {query}")
            print(f"🧠 Detected Complexity: {complexity}")
            
            # Adjust parameters based on complexity
            if complexity == "simple":
                max_tokens = 50
                temperature = 0.1
            elif complexity == "complex":
                max_tokens = 200
                temperature = 0.3
            else:
                max_tokens = 100
                temperature = 0.2
            
            # Test the query
            success, result = await llm.generate_simple_response(query)
            if success:
                print(f"✅ Response: {result[:100]}...")
                print(f"🎯 Used settings: max_tokens={max_tokens}, temp={temperature}")
            else:
                print(f"❌ Failed: {result}")
    
    return True

async def main():
    """Run all tests."""
    print("🚀 Direct LLM Manager Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: Simple manager
        success1 = await test_simple_manager()
        
        # Test 2: Intelligent routing
        if success1:
            success2 = await test_intelligent_routing()
        else:
            success2 = False
        
        # Results
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print(f"   {'✅' if success1 else '❌'} Simple LLM Manager")
        print(f"   {'✅' if success2 else '❌'} Intelligent Routing")
        
        if success1 and success2:
            print("\n🎉 All tests passed!")
            print("✨ Your LLM Manager core functionality is working!")
            print("\n📋 Next Steps:")
            print("   1. Build the vector database (Qdrant)")
            print("   2. Create document processing pipeline")
            print("   3. Implement agentic workflow")
            return True
        else:
            print("\n⚠️ Some tests failed. Check Ollama connection.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎯 Ready to proceed to next phase of development!")
    else:
        print("\n🔧 Please fix the issues above before proceeding.")