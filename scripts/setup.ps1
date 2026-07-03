param(
    [string]$Component = "all"
)

Write-Host "AICluster Setup Script" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan

function Install-Backend {
    Write-Host "`n[Backend] Setting up Python virtual environment..." -ForegroundColor Yellow
    $backendDir = Join-Path $PSScriptRoot "..\backend"
    Set-Location $backendDir

    if (-not (Test-Path ".venv")) {
        python -m venv .venv
        Write-Host "  Created virtual environment" -ForegroundColor Green
    }

    .\.venv\Scripts\pip.exe install -r requirements.txt
    Write-Host "  Backend dependencies installed" -ForegroundColor Green

    New-Item -ItemType Directory -Force -Path "data" | Out-Null
    New-Item -ItemType Directory -Force -Path "logs" | Out-Null
    Write-Host "  Data directories created" -ForegroundColor Green
    Set-Location $PSScriptRoot
}

function Install-Frontend {
    Write-Host "`n[Frontend] Setting up Node.js dependencies..." -ForegroundColor Yellow
    $frontendDir = Join-Path $PSScriptRoot "..\frontend"

    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Set-Location $frontendDir
        npm install
        Write-Host "  Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  node_modules exists, skipping install" -ForegroundColor Gray
    }
    Set-Location $PSScriptRoot
}

function Install-Worker {
    Write-Host "`n[Worker] Setting up Python virtual environment..." -ForegroundColor Yellow
    $workerDir = Join-Path $PSScriptRoot "..\worker"
    Set-Location $workerDir

    if (-not (Test-Path ".venv")) {
        python -m venv .venv
        Write-Host "  Created virtual environment" -ForegroundColor Green
    }

    .\.venv\Scripts\pip.exe install -r requirements.txt
    Write-Host "  Worker dependencies installed" -ForegroundColor Green
    Set-Location $PSScriptRoot
}

switch ($Component.ToLower()) {
    "backend" { Install-Backend }
    "frontend" { Install-Frontend }
    "worker" { Install-Worker }
    "all" {
        Install-Backend
        Install-Frontend
        Install-Worker
    }
    default {
        Write-Host "Unknown component: $Component" -ForegroundColor Red
        Write-Host "Usage: .\setup.ps1 [backend|frontend|worker|all]"
    }
}

Write-Host "`nSetup complete!" -ForegroundColor Cyan
