"""
Quick fix for config/settings.py
=================================

This adds the missing get_settings() function to your config/settings.py file.

Run this from your agentic-rag-pipeline directory:
python fix_settings.py
"""

from pathlib import Path

settings_file = Path("src/config/settings.py")

# Code to add
get_settings_code = '''

def get_settings():
    """
    Get RAG configuration settings.
    
    Returns:
        RAGConfig: Configuration object with all settings
    """
    from rag_components import RAGConfig
    return RAGConfig()
'''

if settings_file.exists():
    # Read current content
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if get_settings already exists
    if 'def get_settings' in content:
        print("✅ get_settings() already exists in config/settings.py")
    else:
        # Add get_settings function at the end
        with open(settings_file, 'a', encoding='utf-8') as f:
            f.write(get_settings_code)
        print("✅ Added get_settings() to config/settings.py")
        print("\nYou can now import it with:")
        print("    from config.settings import get_settings")
else:
    print(f"❌ File not found: {settings_file}")
    print("Make sure you're running this from the agentic-rag-pipeline directory")