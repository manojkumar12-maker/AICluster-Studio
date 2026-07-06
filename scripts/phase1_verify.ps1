$ErrorActionPreference = "Stop"
$root = "C:\Users\a2dpo\AICluster"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AICluster v2.0.0 - Phase 1: Artifact Verification" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$artifacts = @(
    @{Name="Installer";       Path="dist\AIClusterSetup-2.0.0.exe"},
    @{Name="Runtime EXE";     Path="release\runtime\AIClusterRuntime.exe"},
    @{Name="CLI EXE";         Path="release\runtime\aicluster.exe"},
    @{Name="Studio EXE";      Path="release\studio\AIClusterStudio.exe"},
    @{Name="Runtime JSON";    Path="release\runtime\runtime.json"},
    @{Name="VERSION";         Path="VERSION"},
    @{Name="CHANGELOG.md";    Path="CHANGELOG.md"},
    @{Name="README.md";       Path="README.md"},
    @{Name="SECURITY.md";     Path="SECURITY.md"},
    @{Name="NOTICE.md";       Path="NOTICE.md"},
    @{Name="CONTRIBUTING.md"; Path="CONTRIBUTING.md"}
)

$allPresent = $true
foreach ($a in $artifacts) {
    $fullPath = Join-Path $root $a.Path
    if (Test-Path $fullPath) {
        $size = (Get-Item $fullPath).Length
        $mb = "{0:N2}" -f ($size / 1MB)
        Write-Host "  [OK] $($a.Name): $mb MB" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $($a.Name): $($a.Path)" -ForegroundColor Red
        $allPresent = $false
    }
}

Write-Host ""
Write-Host "=== SHA256 Checksums ===" -ForegroundColor Yellow
$exeFiles = @(
    "dist\AIClusterSetup-2.0.0.exe",
    "release\runtime\AIClusterRuntime.exe",
    "release\runtime\aicluster.exe",
    "release\studio\AIClusterStudio.exe"
)
$checksums = @{}
foreach ($f in $exeFiles) {
    $fullPath = Join-Path $root $f
    if (Test-Path $fullPath) {
        $hash = (Get-FileHash -Path $fullPath -Algorithm SHA256).Hash
        $name = Split-Path $f -Leaf
        $checksums[$name] = $hash
        Write-Host "  $hash  $name"
    }
}

Write-Host ""
Write-Host "=== Metadata ===" -ForegroundColor Yellow
$version = Get-Content (Join-Path $root "VERSION") -Raw
Write-Host "  Version: $version".Trim()
$commit = git -C $root log -1 --format="%H" 2>$null
if ($commit) { Write-Host "  Git Commit: $commit" }
Write-Host "  Build Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

Write-Host ""
if ($allPresent) {
    Write-Host "PHASE 1 RESULT: ALL ARTIFACTS PRESENT" -ForegroundColor Green
} else {
    Write-Host "PHASE 1 RESULT: MISSING ARTIFACTS" -ForegroundColor Red
}
