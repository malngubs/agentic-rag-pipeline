#!/usr/bin/env python3
"""
Automatic Patch Script for main_production_with_rag.py
Adds HTML serving routes and fixes static file mounting
"""

def patch_backend_file(filepath):
    """
    Patches the main_production_with_rag.py file with necessary fixes
    """
    print(f"🔧 Patching {filepath}...")
    
    # Read the existing file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already patched
    if '@app.get("/", response_class=HTMLResponse)' in content:
        print("✅ File already patched! No changes needed.")
        return
    
    # PATCH 1: Update setup_static_files function
    old_setup = '''def setup_static_files():
    """Setup static file serving"""
    try:
        possible_paths = [
            Path("../frontend"),
            Path("frontend"), 
            Path("./frontend"),
            Path(__file__).parent.parent / "frontend"
        ]
        
        frontend_path = None
        for path in possible_paths:
            if path.exists():
                frontend_path = path
                break
        
        if frontend_path:
            app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")
            logger.info(f"✅ Static files mounted from: {frontend_path.absolute()}")
            return True
        else:
            logger.warning("⚠️ Frontend directory not found")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Static file mounting failed: {e}")
        return False'''
    
    new_setup = '''def setup_static_files():
    """Setup static file serving for frontend assets"""
    try:
        # Mount frontend directory for HTML files
        possible_frontend_paths = [
            Path("../frontend"),
            Path("frontend"), 
            Path("./frontend"),
            Path(__file__).parent.parent / "frontend"
        ]
        
        frontend_path = None
        for path in possible_frontend_paths:
            if path.exists():
                frontend_path = path
                break
        
        if frontend_path:
            app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")
            logger.info(f"✅ Frontend files mounted from: {frontend_path.absolute()}")
        
        # Mount static directory for JavaScript files
        possible_static_paths = [
            Path("../static"),
            Path("static"),
            Path("./static"),
            Path(__file__).parent.parent / "static",
        ]
        
        static_path = None
        for path in possible_static_paths:
            if path.exists():
                static_path = path
                break
        
        if static_path:
            app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
            logger.info(f"✅ Static files mounted from: {static_path.absolute()}")
            return True
        else:
            logger.warning("⚠️ Static directory not found - creating it now")
            static_dir = Path("./static")
            static_dir.mkdir(exist_ok=True)
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            logger.info(f"📁 Created and mounted static directory: {static_dir.absolute()}")
            logger.info("⚠️ Please place macrocomm-bubble.js in the static/ directory")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Static file mounting failed: {e}")
        return False'''
    
    content = content.replace(old_setup, new_setup)
    
    # PATCH 2: Add HTML serving routes after favicon route
    html_routes = '''@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors"""
    return Response(status_code=204)

# =============================================================================
# 🌐 HTML SERVING ROUTES - Production Frontend
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main index.html page"""
    try:
        possible_paths = [
            Path("../frontend/index.html"),
            Path("frontend/index.html"),
            Path("./frontend/index.html"),
            Path("index.html"),
            Path("./index.html"),
            Path(__file__).parent / "index.html",
            Path(__file__).parent.parent / "frontend" / "index.html"
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return HTMLResponse(content=f.read())
        
        # Fallback landing page
        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Macrocomm AI Assistant</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #FF6E00 0%, #FF923F 100%);
                        color: white;
                    }
                    .container { text-align: center; }
                    h1 { font-size: 48px; margin-bottom: 20px; }
                    p { font-size: 20px; margin-bottom: 30px; }
                    a {
                        color: white;
                        text-decoration: none;
                        padding: 15px 30px;
                        background: rgba(255,255,255,0.2);
                        border-radius: 8px;
                        margin: 0 10px;
                        display: inline-block;
                    }
                    a:hover { background: rgba(255,255,255,0.3); }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🟠 Macrocomm AI Assistant</h1>
                    <p>Advanced Agentic RAG Pipeline - Version 2.2</p>
                    <p>
                        <a href="/admin.html">Admin Portal</a>
                        <a href="/docs">API Documentation</a>
                    </p>
                    <p style="font-size: 14px; margin-top: 40px;">
                        Note: index.html not found. Place it in the root or frontend directory.
                    </p>
                </div>
            </body>
            </html>
        """)
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        raise HTTPException(status_code=500, detail="Error serving index page")

@app.get("/admin.html", response_class=HTMLResponse)
async def serve_admin():
    """Serve the admin portal HTML page"""
    try:
        possible_paths = [
            Path("../frontend/admin.html"),
            Path("frontend/admin.html"),
            Path("./frontend/admin.html"),
            Path("admin.html"),
            Path("./admin.html"),
            Path(__file__).parent / "admin.html",
            Path(__file__).parent.parent / "frontend" / "admin.html"
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return HTMLResponse(content=f.read())
        
        raise HTTPException(status_code=404, detail="Admin page not found. Please ensure admin.html is in the root or frontend directory.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving admin.html: {e}")
        raise HTTPException(status_code=500, detail="Error serving admin page")

@app.get("/health", response_model=HealthResponse)'''
    
    # Replace the favicon route with the new routes
    content = content.replace(
        '''@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors"""
    return Response(status_code=204)

@app.get("/health", response_model=HealthResponse)''',
        html_routes
    )
    
    # Write the patched file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ File patched successfully!")
    print("\nChanges made:")
    print("  1. ✅ Updated setup_static_files() to mount /static directory")
    print("  2. ✅ Added HTML serving route for / (index.html)")
    print("  3. ✅ Added HTML serving route for /admin.html")
    print("\n🎉 Backend is now ready! Restart the server to apply changes.")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    print("🚀 Macrocomm AI Assistant - Backend Patcher")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Default path
        file_path = Path("main_production_with_rag.py")
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} <path_to_main_production_with_rag.py>")
        print("\nOr place this script in the same directory as main_production_with_rag.py")
        sys.exit(1)
    
    # Backup the original file
    backup_path = file_path.with_suffix('.py.backup')
    import shutil
    shutil.copy2(file_path, backup_path)
    print(f"📦 Backup created: {backup_path}")
    
    try:
        patch_backend_file(file_path)
        print(f"\n✨ All done! Original file backed up to: {backup_path}")
    except Exception as e:
        print(f"\n❌ Error patching file: {e}")
        print(f"Original file backed up to: {backup_path}")
        sys.exit(1)