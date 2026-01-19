' Macrocomm Backend - Hidden Starter
' This script starts the Python backend completely hidden (no window)
'
' Usage: Double-click this file or run from command line
' The backend will run on http://localhost:8001

Set WshShell = CreateObject("WScript.Shell")

' Get the project root directory (parent of scripts folder)
scriptPath = WScript.ScriptFullName
scriptsDir = Left(scriptPath, InStrRev(scriptPath, "\"))
projectDir = Left(scriptsDir, Len(scriptsDir) - 1)
projectDir = Left(projectDir, InStrRev(projectDir, "\") - 1)

' Build the command
pythonCmd = "python -m uvicorn src.main_production_with_rag:app --host 0.0.0.0 --port 8001"

' Run the command hidden (0 = hidden window)
WshShell.CurrentDirectory = projectDir
WshShell.Run pythonCmd, 0, False

' Show a brief notification (optional - comment out if not needed)
' MsgBox "Macrocomm backend started on port 8001", 64, "Macrocomm AI"
