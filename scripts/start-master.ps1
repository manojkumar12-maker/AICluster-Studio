param(
    [switch]$Background = $false,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$rootDir = Split-Path $PSScriptRoot -Parent
$backendDir = Join-Path $rootDir "backend"
$frontendDir = Join-Path $rootDir "frontend"

function Start-Backend {
    Write-Host "Starting AICluster Master Backend..." -ForegroundColor Cyan
    Set-Location $backendDir

    if (-not (Test-Path ".venv")) {
        Write-Host "Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
        exit 1
    }

    $env:AICLUSTER_PORT = $Port

    if ($Background) {
        $logFile = Join-Path $rootDir "logs\backend.log"
        Start-Process -WindowStyle Hidden -FilePath (Get-Command "python").Source -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $Port --log-level info" -RedirectStandardOutput $logFile -RedirectStandardError $logFile
        Write-Host "Backend started in background (PID: $((Get-Process -Name python -ErrorAction SilentlyContinue | Select-Object -Last 1).Id))" -ForegroundColor Green
    } else {
        & ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
    }
}

function Start-Frontend {
    Write-Host "Starting AICluster Frontend..." -ForegroundColor Cyan
    Set-Location $frontendDir

    if (-not (Test-Path "node_modules")) {
        Write-Host "node_modules not found. Run setup.ps1 first." -ForegroundColor Red
        exit 1
    }

    if ($Background) {
        $logFile = Join-Path $rootDir "logs\frontend.log"
        Start-Process -WindowStyle Hidden -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory $frontendDir -RedirectStandardOutput $logFile -RedirectStandardError $logFile
        Write-Host "Frontend started in background" -ForegroundColor Green
    } else {
        npm run dev
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AICluster Master - Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Start-Backend
Start-Frontend

Set-Location $rootDir
Write-Host "`nAICluster is running:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:$Port" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:$Port/docs" -ForegroundColor Green
