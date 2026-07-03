param(
    [string]$MasterUrl = "http://localhost:8000",
    [string]$WorkerName = "",
    [string]$WorkerPort = "8001"
)

Write-Host "=== AICluster Worker Installer ===" -ForegroundColor Cyan
Write-Host ""

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    exit 1
}

$workerDir = Join-Path $PSScriptRoot ".." "worker"
Set-Location $workerDir

Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv

Write-Host "Installing dependencies..." -ForegroundColor Yellow
.venv\Scripts\pip install -q -r requirements.txt

if ($WorkerName) {
    $config = @{master_url=$MasterUrl; worker_name=$WorkerName; worker_port=$WorkerPort}
    $config | ConvertTo-Json | Set-Content config.json
    Write-Host "Config saved with worker name: $WorkerName" -ForegroundColor Green
}

Write-Host "Verifying worker..." -ForegroundColor Yellow
.venv\Scripts\python -c "from app.main import app; print('Worker imports OK')"

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host "Start: .venv\Scripts\uvicorn app.main:app --port $WorkerPort"
Write-Host "Master: $MasterUrl"
