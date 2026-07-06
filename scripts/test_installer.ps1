$ErrorActionPreference = "Stop"
$tmpDir = "C:\Users\a2dpo\AppData\Local\Temp\AIClusterTest"
$installer = "C:\Users\a2dpo\AICluster\dist\AIClusterSetup-2.0.0.exe"

Write-Host "=== AICluster Installer Verification ===" -ForegroundColor Cyan

if (Test-Path $tmpDir) {
    Write-Host "Removing existing test dir: $tmpDir"
    Remove-Item $tmpDir -Recurse -Force
}

Write-Host "Running silent install..."
$proc = Start-Process -FilePath $installer -ArgumentList "/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART","/DIR=$tmpDir" -Wait -PassThru

Write-Host "Exit code: $($proc.ExitCode)"
Write-Host ""

Write-Host "=== Installed Files (top-level) ===" -ForegroundColor Green
Get-ChildItem $tmpDir -Depth 2 | ForEach-Object { 
    $rel = $_.FullName.Replace($tmpDir, "[APP]")
    if ($_.PSIsContainer) {
        Write-Host "  $rel/" -ForegroundColor Yellow
    } else {
        Write-Host "  $rel ($('{0:N0}' -f $_.Length) bytes)"
    }
}

Write-Host ""
Write-Host "=== Checking Critical Files ===" -ForegroundColor Green
$checks = @(
    @{Path="runtime\AIClusterRuntime.exe"; Desc="Runtime EXE"},
    @{Path="studio\AIClusterStudio.exe"; Desc="Studio EXE"},
    @{Path="config\default.yaml"; Desc="Config YAML"},
    @{Path="config\role.json"; Desc="Role JSON"}
)

foreach ($check in $checks) {
    $fullPath = Join-Path $tmpDir $check.Path
    if (Test-Path $fullPath) {
        Write-Host "  [OK] $($check.Desc): $($check.Path)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $($check.Desc): $($check.Path) NOT FOUND" -ForegroundColor Red
    }
}

if (Test-Path (Join-Path $tmpDir "config\role.json")) {
    Write-Host ""
    Write-Host "=== role.json Contents ===" -ForegroundColor Cyan
    Get-Content (Join-Path $tmpDir "config\role.json") | Write-Host
}

Write-Host ""
Write-Host "=== Runtime Test ===" -ForegroundColor Cyan
$runtimePath = Join-Path $tmpDir "runtime\AIClusterRuntime.exe"
if (Test-Path $runtimePath) {
    $rtProc = Start-Process -FilePath $runtimePath -ArgumentList "--mode","master" -WindowStyle Hidden -PassThru
    Start-Sleep 5
    
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 10
        Write-Host "  [OK] Runtime started. Health: $($health.status), Version: $($health.version)" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    $rtProc | Stop-Process -Force
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
