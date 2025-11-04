#!/usr/bin/env python3
"""
Debug script to test .env file loading
"""

import os
from pathlib import Path

def test_env_file_exists():
    """Check if .env file exists and can be read"""
    print("1. Testing .env file existence...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print(f"   ✅ .env file exists at: {env_file.absolute()}")
        
        # Check file size
        size = env_file.stat().st_size
        print(f"   📊 File size: {size} bytes")
        
        # Try to read first few lines
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
            print(f"   📄 First 5 lines:")
            for i, line in enumerate(lines, 1):
                print(f"      {i}: {line.strip()}")
            return True
        except Exception as e:
            print(f"   ❌ Cannot read .env file: {e}")
            return False
    else:
        print(f"   ❌ .env file does not exist at: {env_file.absolute()}")
        return False

def test_direct_env_vars():
    """Test reading environment variables directly"""
    print("\n2. Testing direct environment variable access...")
    
    # Check if variables are already in environment
    jwt_key = os.getenv("JWT_SECRET_KEY")
    encryption_key = os.getenv("ENCRYPTION_KEY")
    environment = os.getenv("ENVIRONMENT")
    
    print(f"   JWT_SECRET_KEY: {'Found' if jwt_key else 'Not found'}")
    print(f"   ENCRYPTION_KEY: {'Found' if encryption_key else 'Not found'}")
    print(f"   ENVIRONMENT: {environment if environment else 'Not found'}")
    
    return bool(jwt_key and encryption_key)

def test_dotenv_loading():
    """Test python-dotenv library"""
    print("\n3. Testing python-dotenv loading...")
    
    try:
        from dotenv import load_dotenv
        print("   ✅ python-dotenv library imported successfully")
        
        # Load .env file explicitly
        loaded = load_dotenv()
        print(f"   📝 load_dotenv() returned: {loaded}")
        
        # Check if variables are now available
        jwt_key = os.getenv("JWT_SECRET_KEY")
        encryption_key = os.getenv("ENCRYPTION_KEY")
        environment = os.getenv("ENVIRONMENT")
        
        print(f"   After loading:")
        print(f"     JWT_SECRET_KEY: {'Found' if jwt_key else 'Not found'}")
        print(f"     ENCRYPTION_KEY: {'Found' if encryption_key else 'Not found'}")
        print(f"     ENVIRONMENT: {environment if environment else 'Not found'}")
        
        return bool(jwt_key and encryption_key)
        
    except ImportError:
        print("   ❌ python-dotenv library not installed")
        print("   💡 Run: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"   ❌ Error loading .env: {e}")
        return False

def test_manual_env_parsing():
    """Manually parse .env file to see its content"""
    print("\n4. Testing manual .env parsing...")
    
    try:
        env_vars = {}
        with open('.env', 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
                        
        print(f"   📊 Found {len(env_vars)} variables in .env file:")
        for key, value in list(env_vars.items())[:5]:  # Show first 5
            display_value = value[:20] + "..." if len(value) > 20 else value
            print(f"     {key}: {display_value}")
            
        # Check our required variables
        jwt_in_file = "JWT_SECRET_KEY" in env_vars
        encryption_in_file = "ENCRYPTION_KEY" in env_vars
        
        print(f"   Required variables in file:")
        print(f"     JWT_SECRET_KEY: {'✅ Found' if jwt_in_file else '❌ Missing'}")
        print(f"     ENCRYPTION_KEY: {'✅ Found' if encryption_in_file else '❌ Missing'}")
        
        return jwt_in_file and encryption_in_file
        
    except Exception as e:
        print(f"   ❌ Cannot parse .env file: {e}")
        return False

def run_complete_diagnosis():
    """Run complete diagnosis of environment variable issues"""
    print("🔍 Environment Variable Diagnosis")
    print("=" * 50)
    
    # Get current working directory
    print(f"📁 Current directory: {Path.cwd()}")
    print(f"📁 Files in directory: {list(Path('.').glob('*env*'))}")
    
    results = {
        "file_exists": test_env_file_exists(),
        "direct_access": test_direct_env_vars(), 
        "dotenv_loading": test_dotenv_loading(),
        "manual_parsing": test_manual_env_parsing()
    }
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS RESULTS")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    # Provide recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not results["file_exists"]:
        print("   1. ❌ Create .env file with correct content")
    elif not results["manual_parsing"]:
        print("   1. ❌ Fix .env file format - check for syntax errors")
    elif not results["dotenv_loading"]:
        print("   1. ❌ Install python-dotenv: pip install python-dotenv")
    elif results["dotenv_loading"] and not results["direct_access"]:
        print("   1. ✅ Everything looks good! The issue might be in settings.py")
    else:
        print("   1. ✅ Environment variables should be working now!")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_complete_diagnosis()
    
    if success:
        print("\n🎉 All tests passed! Environment variables should work now.")
    else:
        print("\n⚠️ Issues found. Follow the recommendations above.")