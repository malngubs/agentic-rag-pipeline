@echo off
REM ============================================================================
REM Start Macrocomm BI Platform Backend
REM ============================================================================

echo.
echo ========================================
echo   Starting Backend (Port 8000)
echo ========================================
echo.

REM Check if Qdrant is running
echo [1/2] Checking Qdrant connection...
curl -s http://localhost:6333 >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARNING] Qdrant not responding on port 6333
    echo   Make sure Qdrant is running:
    echo   docker run -p 6333:6333 qdrant/qdrant
    echo.
    pause
)

REM Start backend
echo [2/2] Starting FastAPI backend...
echo.
echo ========================================
echo   Backend will start on:
echo   http://localhost:8000
echo   Health: http://localhost:8000/health
echo   API Docs: http://localhost:8000/docs
echo ========================================
echo.

python src\main_production_with_rag.py

pause
