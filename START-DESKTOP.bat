@echo off
REM ============================================================================
REM Start Macrocomm Desktop App
REM ============================================================================

echo.
echo ========================================
echo   Starting Desktop App
echo ========================================
echo.

cd desktop-app

echo [1/1] Starting Electron app...
echo.
echo   - Press Ctrl+Shift+M to toggle window
echo   - Double-click tray icon to show
echo   - Right-click tray icon for menu
echo.

npm start

pause
