param(
    [string]$Port = "8000",
    [string]$PythonVersion = "3.12"
)

Write-Host "=== AICluster Master Installer ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "ERROR: Python not found. Install Python $PythonVersion first." -ForegroundColor Red
    exit 1
}
$pyVersion = python --version 2>&1
Write-Host "Python: $pyVersion" -ForegroundColor Green

# Create venv
$backendDir = Join-Path $PSScriptRoot ".." "backend"
Set-Location $backendDir
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if (-not (Test-Path ".venv")) {
    Write-Host "ERROR: Failed to create venv" -ForegroundColor Red
    exit 1
}

# Install deps
Write-Host "Installing dependencies..." -ForegroundColor Yellow
.venv\Scripts\pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Verify
Write-Host "Verifying installation..." -ForegroundColor Yellow
.venv\Scripts\python -c "from app.main import app; print('Master imports OK')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Installation verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host "Start Master: .venv\Scripts\uvicorn app.main:app --port $Port"
Write-Host "Open Dashboard: http://localhost:$Port"
