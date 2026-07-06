$ErrorActionPreference = "Stop"
Write-Host "=== Testing Backend ===" -ForegroundColor Cyan

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 10
    Write-Host "Health: OK" -ForegroundColor Green
    Write-Host ($health | ConvertTo-Json)
} catch {
    Write-Host "Health FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Testing Login ===" -ForegroundColor Cyan

try {
    $body = @{username="admin";password="admin"} | ConvertTo-Json
    $login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "Login: OK" -ForegroundColor Green
    Write-Host "Token: $($login.access_token.Substring(0,30))..."
    Write-Host "User:" ($login.user | ConvertTo-Json)
} catch {
    Write-Host "Login FAILED: $($_.Exception.Message)" -ForegroundColor Red
    try {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "Response: $($reader.ReadToEnd())" -ForegroundColor Yellow
        $reader.Close()
    } catch {}
}
