# Start CoSensei Full Stack (Backend + Frontend)
# PowerShell Script

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "CoSensei Full Stack Startup" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will start:"
Write-Host "  1. Python Flask API Server (http://localhost:5000)" -ForegroundColor Yellow
Write-Host "  2. React Vite Frontend (http://localhost:3000)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in each terminal when done"
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Get base directory
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start Python backend
Write-Host "Starting Python API Server..." -ForegroundColor Green
$pythonScript = @"
& "$baseDir\.venv\Scripts\Activate.ps1"
cd "$baseDir\terminal_stress_ai"
python app/risk_api_server.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $pythonScript

# Wait for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start React frontend
Write-Host "Starting React Frontend..." -ForegroundColor Green
$reactScript = @"
cd "$baseDir\cosensei-web"
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $reactScript

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Servers starting..." -ForegroundColor Green
Write-Host "  Backend:  http://localhost:5000" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
