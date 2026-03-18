@echo off
REM ============================================
REM Macrocomm AI Assistant - Stop All Services
REM ============================================

title Stopping Macrocomm Services
color 0C
echo.
echo  ========================================
echo   STOPPING MACROCOMM SERVICES
echo  ========================================
echo.

REM Kill Backend (port 8000)
echo [1/3] Stopping backend server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo       Backend stopped.

REM Kill Frontend (port 3000)
echo [2/3] Stopping React frontend...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo       Frontend stopped.

REM Kill Electron app
echo [3/3] Stopping desktop chatbot...
taskkill /F /IM "Macrocomm AI Assistant.exe" >nul 2>&1
taskkill /F /IM electron.exe >nul 2>&1
echo       Chatbot stopped.

echo.
echo  ========================================
echo   ALL SERVICES STOPPED
echo  ========================================
echo.
timeout /t 3 /nobreak >nul
exit
