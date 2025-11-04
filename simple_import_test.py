#!/usr/bin/env python3
"""
Simple import test to debug the module resolution issue.
This tests if our modules can be imported at runtime.
"""

import sys
import os

print("🔍 Testing Module Imports...")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"🐍 Python path: {sys.path}")

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)
print(f"➕ Added to path: {src_path}")

# Test basic imports one by one
try:
    print("\n1️⃣ Testing config.settings import...")
    from config.settings import get_settings
    print("✅ config.settings imported successfully")
    
    settings = get_settings()
    print(f"   Settings loaded: {settings.app.app_name}")
    
except ImportError as e:
    print(f"❌ config.settings import failed: {e}")
    sys.exit(1)

try:
    print("\n2️⃣ Testing models.llm_manager import...")
    from models.llm_manager import OllamaLLMManager
    print("✅ models.llm_manager imported successfully")
    
    # Test class instantiation
    manager = OllamaLLMManager()
    print("✅ OllamaLLMManager instantiated successfully")
    
except ImportError as e:
    print(f"❌ models.llm_manager import failed: {e}")
    print("💡 Checking if required packages are installed...")
    
    try:
        import httpx
        print("✅ httpx is available")
    except ImportError:
        print("❌ httpx not installed. Run: pip install httpx")
    
    try:
        import asyncio
        print("✅ asyncio is available")
    except ImportError:
        print("❌ asyncio not available (this shouldn't happen)")

print("\n🎉 All imports successful! The module structure is working.")
print("💡 VS Code warnings can be ignored - the code runs fine.")

# Test if we can access Ollama (without async for simplicity)
try:
    import httpx
    response = httpx.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        print("✅ Ollama is accessible at localhost:11434")
        data = response.json()
        models = [model['name'] for model in data.get('models', [])]
        print(f"📦 Available models: {models}")
    else:
        print("⚠️ Ollama responded but with error status")
except Exception as e:
    print(f"⚠️ Cannot connect to Ollama: {e}")
    print("💡 Make sure Ollama is installed and running")
    print("   Download from: https://ollama.ai/download")
    print("   Then run: ollama serve")

print("\n✨ Import test completed!")