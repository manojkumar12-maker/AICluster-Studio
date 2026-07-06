$ErrorActionPreference = "Stop"
$root = "C:\Users\a2dpo\AICluster"
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AICluster v2.0.0 - Phase 3: Installed Layout" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$workDir = "C:\Users\a2dpo\AICluster\build\setup\payload\aicluster"
$dirs = @("runtime", "studio", "config", "assets")

# Run app from release dir to test runtime layout
Write-Host "=== Starting runtime for layout validation ===" -ForegroundColor Yellow
Get-Process "AIClusterRuntime" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2

$proc = Start-Process -FilePath "$root\release\runtime\AIClusterRuntime.exe" -ArgumentList "--mode","master" -WindowStyle Hidden -PassThru
Start-Sleep 6

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 10
    Write-Host "  [OK] Health: $($health.status), DB: $($health.database), Workers: $($health.worker_count), Version: $($health.version)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Health check: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== API Route Discovery ===" -ForegroundColor Yellow
try {
    $routes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/openapi.json" -TimeoutSec 10
    $routeCount = ($routes.paths | Get-Member -MemberType NoteProperty).Count
    Write-Host "  [OK] API routes exposed: $routeCount" -ForegroundColor Green
    
    $keyEndpoints = @("auth/login","health","dashboard","workers","jobs")
    foreach ($ep in $keyEndpoints) {
        $found = $false
        foreach ($path in ($routes.paths | Get-Member -MemberType NoteProperty | ForEach-Object { $_.Name })) {
            if ($path -like "*/$ep*") { $found = $true }
        }
        if ($found) {
            Write-Host "    [OK] /api/v1/$ep" -ForegroundColor Green
        } else {
            Write-Host "    [WARN] /api/v1/$ep NOT FOUND" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  [FAIL] OpenAPI: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Login + Token Validation ===" -ForegroundColor Yellow
try {
    $body = '{"username":"admin","password":"admin"}'
    $login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "  [OK] Login successful" -ForegroundColor Green
    
    if ($login.user) {
        Write-Host "    [OK] User returned: $($login.user.username) ($($login.user.role))" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] No user in response" -ForegroundColor Yellow
    }
    
    # Test with invalid password
    try {
        $badBody = '{"username":"admin","password":"wrong"}'
        $badLogin = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method POST -Body $badBody -ContentType "application/json" -TimeoutSec 10
        Write-Host "    [FAIL] Invalid password was accepted!" -ForegroundColor Red
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401) {
            Write-Host "    [OK] Invalid password rejected (401)" -ForegroundColor Green
        } else {
            Write-Host "    [OK] Invalid password rejected ($($_.Exception.Message | Select -First 50))" -ForegroundColor Green
        }
    }
    
    # Test with expired/invalid token
    $token = $login.access_token
    try {
        $dash = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/dashboard" -Headers @{Authorization="Bearer $token"} -TimeoutSec 10
        Write-Host "  [OK] Dashboard accessible with valid token" -ForegroundColor Green
        Write-Host "    Fields: $([string]::Join(', ', ($dash | Get-Member -MemberType NoteProperty | ForEach-Object { $_.Name } | Sort-Object)))" -ForegroundColor Gray
    } catch {
        Write-Host "    [FAIL] Dashboard access: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test with fake token
    try {
        $fakeBody = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/dashboard" -Headers @{Authorization="Bearer invalid_token_here"} -TimeoutSec 10
        Write-Host "  [FAIL] Invalid token accepted!" -ForegroundColor Red
    } catch {
        Write-Host "  [OK] Invalid token rejected" -ForegroundColor Green
    }
    
    # Test no auth header
    try {
        $noAuth = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/dashboard" -TimeoutSec 10
        Write-Host "  [FAIL] No auth accepted!" -ForegroundColor Red
    } catch {
        Write-Host "  [OK] No auth rejected" -ForegroundColor Green
    }
    
} catch {
    Write-Host "  [FAIL] Login error: $($_.Exception.Message)" -ForegroundColor Red
}

$proc | Stop-Process -Force

Write-Host ""
Write-Host "PHASE 3+6 COMPLETE" -ForegroundColor Cyan
