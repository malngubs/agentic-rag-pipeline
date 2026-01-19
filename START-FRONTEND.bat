@echo off
REM ============================================================================
REM Start Macrocomm BI Platform Frontend
REM ============================================================================

echo.
echo ========================================
echo   Starting Frontend (Port 3000)
echo ========================================
echo.

cd frontend

REM Kill any process on port 3000
echo [1/3] Checking for processes on port 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo   - Found PID: %%a, killing...
    taskkill /PID %%a /F >nul 2>&1
)

REM Clean build folder
echo [2/3] Cleaning build folder...
if exist .next (
    rmdir /s /q .next
    echo   - Cleaned .next folder
)

REM Start dev server
echo [3/3] Starting development server...
echo.
echo ========================================
echo   Frontend will start on:
echo   http://localhost:3000
echo ========================================
echo.

set NODE_OPTIONS=--max-old-space-size=4096
npm run dev

pause
