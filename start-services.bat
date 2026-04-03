@echo off
REM Synapse Complete Startup Script (Windows)
REM Starts API server and Dashboard

echo.
echo ============================================
echo 🧠 SYNAPSE - AI Workspace Engine
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

echo ✓ Python found

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js/npm is not installed or not in PATH
    pause
    exit /b 1
)

echo ✓ Node.js found

echo.
echo Starting services...
echo.

REM Start API Server
echo Starting API Server (port 8000)...
start "Synapse API" cmd /k "python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak

REM Start Dashboard
echo Starting Dashboard (port 3000)...
cd dashboard
start "Synapse Dashboard" cmd /k "npm run dev"

echo.
echo ============================================
echo ✓ Services Starting
echo ============================================
echo API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Dashboard: http://localhost:3000
echo ============================================
echo.
echo Services are starting in separate windows.
echo Press Ctrl+C in each window to stop.
echo.
pause
