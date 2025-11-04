#!/usr/bin/env python3
"""
Simple test to verify configuration is working after fixes.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_environment_variables():
    """Test that our .env file is being read correctly."""
    print("Testing Environment Variables...")
    
    # Test that we can read the variables we just set
    jwt_key = os.getenv("JWT_SECRET_KEY")
    encryption_key = os.getenv("ENCRYPTION_KEY")
    environment = os.getenv("ENVIRONMENT")
    
    print(f"   JWT_SECRET_KEY: {'Set' if jwt_key else 'Missing'}")
    print(f"   ENCRYPTION_KEY: {'Set' if encryption_key else 'Missing'}")  
    print(f"   ENVIRONMENT: {environment or 'Not set'}")
    
    if not jwt_key or not encryption_key:
        print("   ERROR: Missing required keys in .env file")
        return False
    
    print("   SUCCESS: All required environment variables found")
    return True

def test_configuration_loading():
    """Test that our settings.py can load without errors."""
    print("\nTesting Configuration Loading...")
    
    try:
        from config.settings import get_settings
        
        settings = get_settings()
        
        print("   SUCCESS: Settings loaded without errors")
        print(f"   App: {settings.app.app_name}")
        print(f"   Environment: {settings.app.environment}")
        print(f"   Ollama URL: {settings.ollama.ollama_base_url}")
        print(f"   Primary Model: {settings.ollama.primary_model}")
        
        return True
        
    except Exception as e:
        print(f"   ERROR: Settings loading failed: {e}")
        return False

def run_quick_test():
    """Run a quick configuration test."""
    print("Quick Configuration Test")
    print("=" * 40)
    
    # Test 1: Environment variables
    env_test = test_environment_variables()
    
    # Test 2: Configuration loading  
    config_test = test_configuration_loading()
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"   Environment Variables: {'PASS' if env_test else 'FAIL'}")
    print(f"   Configuration Loading: {'PASS' if config_test else 'FAIL'}")
    
    if env_test and config_test:
        print("\nSUCCESS: Configuration is working correctly!")
        print("Ready to proceed with fixing syntax errors.")
        return True
    else:
        print("\nFAILED: Please fix configuration issues first.")
        return False

if __name__ == "__main__":
    success = run_quick_test()