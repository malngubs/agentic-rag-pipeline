"""
Simple test script for the basic FastAPI backend.
"""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"

async def test_basic_endpoints():
    """Test basic API endpoints."""
    
    print("🧪 Testing Basic FastAPI Backend...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test root endpoint
            print("\n1. Testing root endpoint...")
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Root endpoint: {data.get('service')}")
            else:
                print(f"   ❌ Root endpoint failed: {response.status_code}")
            
            # Test health endpoint
            print("\n2. Testing health endpoint...")
            response = await client.get(f"{BASE_URL}/health/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health check: {data.get('status')}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
            
            # Test detailed health
            print("\n3. Testing detailed health...")
            response = await client.get(f"{BASE_URL}/health/detailed")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Detailed health: {data.get('status')}")
            else:
                print(f"   ❌ Detailed health failed: {response.status_code}")
            
            # Test chat endpoint
            print("\n4. Testing chat endpoint...")
            chat_message = {"message": "Hello, this is a test!"}
            response = await client.post(f"{BASE_URL}/v1/chat/", json=chat_message)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Chat response: {data.get('response')[:50]}...")
                print(f"   ✅ Response time: {data.get('response_time'):.3f}s")
            else:
                print(f"   ❌ Chat endpoint failed: {response.status_code}")
            
            # Test OpenAPI docs
            print("\n5. Testing API documentation...")
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print("   ✅ API docs available at http://localhost:8000/docs")
            else:
                print(f"   ❌ API docs failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
            print("   Make sure the FastAPI server is running on localhost:8000")

async def main():
    """Run all tests."""
    print("🚀 Simple FastAPI Backend Test")
    print("Make sure you've started the server with: python src/main_simple.py")
    
    # Wait for server
    print("\nWaiting 2 seconds for server...")
    await asyncio.sleep(2)
    
    await test_basic_endpoints()
    
    print("\n🎯 Testing completed!")
    print("\nIf all tests passed, your basic FastAPI backend is working!")

if __name__ == "__main__":
    asyncio.run(main())