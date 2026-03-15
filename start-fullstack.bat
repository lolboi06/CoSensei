@echo off
REM Start CoSensei Full Stack (Backend + Frontend)

echo.
echo ======================================================================
echo CoSensei Full Stack Startup
echo ======================================================================
echo.
echo This script will start:
echo   1. Python Flask API Server (http://localhost:5000)
echo   2. React Vite Frontend (http://localhost:3000)
echo.
echo Press Ctrl+C in each terminal when done
echo.
echo ======================================================================
echo.

REM Get the base directory
cd /d "%~dp0"

REM Start Python backend in a new terminal
echo Starting Python API Server...
start cmd /k "cd /d "%~dp0\terminal_stress_ai" && .venv\Scripts\activate.bat && python app/risk_api_server.py"

REM Wait a moment for backend to start
timeout /t 3

REM Start React frontend in a new terminal
echo Starting React Frontend...
start cmd /k "cd /d "%~dp0\cosensei-web" && npm run dev"

echo.
echo ======================================================================
echo Servers starting...
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo ======================================================================
