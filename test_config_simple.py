#!/usr/bin/env python3
"""
Simple configuration test that bypasses .env file issues
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_with_manual_env_vars():
    """Test by manually setting environment variables"""
    print("Testing Configuration with Manual Environment Variables...")
    
    # Manually set the required environment variables
    os.environ["JWT_SECRET_KEY"] = "agentic-rag-super-secret-jwt-key-for-development-change-in-production"
    os.environ["ENCRYPTION_KEY"] = "12345678901234567890123456789012"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    
    print("✅ Environment variables set manually")
    
    # Now test our configuration
    try:
        from config.settings import get_settings
        
        settings = get_settings()
        
        print("✅ Configuration loaded successfully!")
        print(f"   App: {settings.app.app_name}")
        print(f"   Environment: {settings.app.environment}")
        print(f"   Debug: {settings.app.debug}")
        print(f"   JWT Key: {'Set' if settings.app.jwt_secret_key else 'Missing'}")
        print(f"   Encryption Key: {'Set' if settings.app.encryption_key else 'Missing'}")
        print(f"   Ollama URL: {settings.ollama.ollama_base_url}")
        print(f"   Primary Model: {settings.ollama.primary_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_simple_test():
    """Run simple configuration test"""
    print("Simple Configuration Test (Bypassing .env)")
    print("=" * 50)
    
    success = test_with_manual_env_vars()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SUCCESS: Configuration system is working!")
        print("   The issue is with .env file loading, not the configuration system itself.")
        print("   We can proceed with building the next components.")
    else:
        print("❌ FAILED: There's an issue with the configuration system.")
    
    return success

if __name__ == "__main__":
    success = run_simple_test()