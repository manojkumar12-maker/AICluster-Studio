param(
    [string]$MasterUrl = "http://localhost:8000",
    [int]$Port = 8001,
    [string]$Name = "",
    [switch]$Background = $false
)

$ErrorActionPreference = "Stop"
$rootDir = Split-Path $PSScriptRoot -Parent
$workerDir = Join-Path $rootDir "worker"

Write-Host "Starting AICluster Worker..." -ForegroundColor Cyan
Set-Location $workerDir

if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

$env:MASTER_URL = $MasterUrl
$env:WORKER_PORT = $Port
$env:WORKER_NAME = $Name

if ($Background) {
    $logFile = Join-Path $rootDir "logs\worker-$Port.log"
    Start-Process -WindowStyle Hidden -FilePath (Get-Command "python").Source -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $Port --log-level info" -RedirectStandardOutput $logFile -RedirectStandardError $logFile
    Write-Host "Worker started in background on port $Port" -ForegroundColor Green
} else {
    & ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
}

Set-Location $rootDir
