@echo off
REM ============================================
REM Macrocomm AI Assistant - Premium Launcher
REM Starts: Backend (hidden) + React Frontend (hidden) + Desktop Chatbot
REM ============================================

title Macrocomm AI Launcher
color 0A
echo.
echo  ========================================
echo   MACROCOMM AI ASSISTANT - PREMIUM
echo  ========================================
echo.

set "PROJECT_DIR=%~dp0"

REM ---- STEP 1: Start Backend (hidden) ----
echo [1/3] Checking backend server...
netstat -ano | findstr :8001 >nul 2>&1
if %errorlevel%==0 (
    echo       Backend already running on port 8001
) else (
    echo       Starting backend server (hidden)...
    powershell -WindowStyle Hidden -Command "Start-Process -FilePath 'python' -ArgumentList '-m uvicorn src.main_production_with_rag:app --host 0.0.0.0 --port 8001' -WorkingDirectory '%PROJECT_DIR%' -WindowStyle Hidden"
    timeout /t 2 /nobreak >nul
    echo       Backend started!
)

REM ---- STEP 2: Start React Frontend (hidden) ----
echo.
echo [2/3] Checking React frontend...
netstat -ano | findstr :3000 >nul 2>&1
if %errorlevel%==0 (
    echo       Frontend already running on port 3000
) else (
    echo       Starting React frontend (hidden)...
    powershell -WindowStyle Hidden -Command "Start-Process -FilePath 'npm' -ArgumentList 'run dev' -WorkingDirectory '%PROJECT_DIR%frontend' -WindowStyle Hidden"
    timeout /t 3 /nobreak >nul
    echo       Frontend started!
)

REM ---- STEP 3: Start Desktop Chatbot ----
echo.
echo [3/3] Launching Macrocomm AI Chatbot...
cd /d "%PROJECT_DIR%desktop-app"
start "" npm start

echo.
echo  ========================================
echo   ALL SERVICES STARTED SUCCESSFULLY!
echo  ========================================
echo.
echo   Backend:   http://localhost:8001
echo   Frontend:  http://localhost:3000
echo   Chatbot:   Press Ctrl+Shift+M to toggle
echo.
echo   The chatbot is now in your system tray
echo   with the orange Macrocomm icon.
echo.
echo  ========================================
echo.
echo  This window will close in 5 seconds...
timeout /t 5 /nobreak >nul
exit
