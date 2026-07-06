$ErrorActionPreference = "Stop"

Write-Host "=== Dashboard Test ===" -ForegroundColor Cyan

$body = '{"username":"admin","password":"admin"}'
$login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
Write-Host "Login OK, token: $($login.access_token.Substring(0,20))..."

$dash = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/dashboard" -Headers @{Authorization="Bearer $($login.access_token)"} -TimeoutSec 10
Write-Host "Dashboard:" -ForegroundColor Green
ConvertTo-Json $dash
