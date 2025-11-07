"""
Import Diagnostics - Run this to check your setup
================================================

Run this from your agentic-rag-pipeline directory:
python diagnose_imports.py
"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("🔍 RAG PIPELINE IMPORT DIAGNOSTICS")
print("=" * 70)

# Check current directory
print(f"\n1️⃣  Current Directory: {os.getcwd()}")

# Check if key files exist
print("\n2️⃣  Checking for key files:")

files_to_check = [
    "rag_components.py",
    "src/rag_components.py",
    "src/config/settings.py",
    "src/main_production_with_rag.py",
    "src/main.py"
]

for file in files_to_check:
    exists = "✅" if Path(file).exists() else "❌"
    print(f"   {exists} {file}")

# Check Python path
print("\n3️⃣  Python sys.path:")
for i, path in enumerate(sys.path[:5], 1):
    print(f"   {i}. {path}")

# Try importing rag_components
print("\n4️⃣  Testing imports:")

# Test 1: Direct import
try:
    import rag_components
    print("   ✅ 'import rag_components' works!")
    print(f"      Location: {rag_components.__file__}")
except ModuleNotFoundError as e:
    print(f"   ❌ 'import rag_components' failed: {e}")

# Test 2: From src
sys.path.insert(0, "src")
try:
    import rag_components
    print("   ✅ 'import rag_components' works from src!")
except ModuleNotFoundError:
    print("   ❌ 'import rag_components' failed from src too")

# Test 3: Check config.settings
sys.path.insert(0, os.getcwd())
try:
    from config.settings import get_settings
    print("   ✅ 'from config.settings import get_settings' works!")
except (ModuleNotFoundError, ImportError) as e:
    print(f"   ❌ 'from config.settings import get_settings' failed: {e}")

print("\n" + "=" * 70)
print("📋 RECOMMENDATIONS:")
print("=" * 70)

# Provide recommendations
if not Path("rag_components.py").exists() and not Path("src/rag_components.py").exists():
    print("\n❌ PROBLEM: rag_components.py not found!")
    print("   Solution: Make sure rag_components.py is in either:")
    print("   - Root directory (agentic-rag-pipeline/rag_components.py)")
    print("   - OR src directory (agentic-rag-pipeline/src/rag_components.py)")

if Path("src/rag_components.py").exists():
    print("\n✅ rag_components.py found in src/")
    print("   No path modifications needed when running from src/")

elif Path("rag_components.py").exists():
    print("\n✅ rag_components.py found in root")
    print("   Add this to top of main_production_with_rag.py:")
    print("   ```python")
    print("   import sys")
    print("   from pathlib import Path")
    print("   sys.path.insert(0, str(Path(__file__).parent.parent))")
    print("   ```")

if not Path("src/config/settings.py").exists():
    print("\n⚠️  WARNING: src/config/settings.py not found")
    print("   Options:")
    print("   1. Remove/comment out 'from config.settings import get_settings'")
    print("   2. OR create src/config/settings.py with get_settings function")

print("\n" + "=" * 70)