$ErrorActionPreference = "Stop"
$root = "C:\Users\a2dpo\AICluster"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AICluster v2.0.0 - REPOSITORY_STATUS.md" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "## Branch & Commits" -ForegroundColor Yellow
$branch = git -C $root branch --show-current 2>$null
Write-Host "  Branch: $branch"
$lastCommits = git -C $root log --oneline -5 2>$null
Write-Host "  Recent commits:"
$lastCommits.Split("`n") | ForEach-Object { Write-Host "    $_" }

Write-Host ""
Write-Host "## Git Status" -ForegroundColor Yellow
$status = git -C $root status --porcelain 2>$null
$changed = ($status | Where-Object { $_ -ne '' } | Measure-Object).Count
Write-Host "  Changed files: $changed"
if ($changed -gt 0) {
    Write-Host "  (Files with modifications from release preparation)"
}

Write-Host ""
Write-Host "## Version Consistency" -ForegroundColor Yellow
$version = (Get-Content "$root\VERSION" -Raw).Trim()
Write-Host "  VERSION: $version"

$checks = @(
    @{Name="README.md"; File="README.md"; Line=2; Match="v2.0.0"},
    @{Name="CHANGELOG.md"; File="CHANGELOG.md"; Line=2; Match="v2.0.0"},
    @{Name="RELEASE_NOTES.md"; File="RELEASE_NOTES.md"; Line=0; Match="v2.0.0"}
)

$allVersionOk = $true
foreach ($c in $checks) {
    $content = Get-Content "$root\$($c.File)" -Raw -ErrorAction SilentlyContinue
    if ($content -match $c.Match) {
        Write-Host "  [OK] $($c.Name): mentions 2.0.0" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $($c.Name): missing 2.0.0 reference" -ForegroundColor Red
        $allVersionOk = $false
    }
}

Write-Host ""
Write-Host "## Release Assets" -ForegroundColor Yellow
$assets = @(
    @{Name="Installer"; Path="dist\AIClusterSetup-2.0.0.exe"},
    @{Name="Runtime"; Path="release\runtime\AIClusterRuntime.exe"},
    @{Name="CLI"; Path="release\runtime\aicluster.exe"},
    @{Name="Studio"; Path="release\studio\AIClusterStudio.exe"},
    @{Name="License"; Path="LICENSE"},
    @{Name="VERSION"; Path="VERSION"},
    @{Name="SECURITY"; Path="SECURITY.md"},
    @{Name="CONTRIBUTING"; Path="CONTRIBUTING.md"},
    @{Name="README"; Path="README.md"},
    @{Name="CHANGELOG"; Path="CHANGELOG.md"},
    @{Name="RELEASE_NOTES"; Path="RELEASE_NOTES.md"}
)

$allAssets = $true
foreach ($a in $assets) {
    $fp = Join-Path $root $a.Path
    if (Test-Path $fp) {
        $sz = (Get-Item $fp).Length
        $mb = "{0:N2}" -f ($sz / 1MB)
        Write-Host "  [OK] $($a.Name): $mb MB" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $($a.Name): $($a.Path)" -ForegroundColor Red
        $allAssets = $false
    }
}

Write-Host ""
Write-Host "## GitHub Templates" -ForegroundColor Yellow
$templates = @(
    ".github\ISSUE_TEMPLATE\bug_report.md",
    ".github\ISSUE_TEMPLATE\feature_request.md",
    ".github\ISSUE_TEMPLATE\security_report.md",
    ".github\PULL_REQUEST_TEMPLATE.md"
)
$allTemplates = $true
foreach ($t in $templates) {
    $fp = Join-Path $root $t
    if (Test-Path $fp) {
        Write-Host "  [OK] $t" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $t" -ForegroundColor Red
        $allTemplates = $false
    }
}

Write-Host ""
Write-Host "## Secrets & Sensitive Files" -ForegroundColor Yellow
$secrets = Get-ChildItem $root -Include '.env','secret.key','*.pem','*.pfx','credentials.*' -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\node_modules\\' -and $_.FullName -notmatch '\\target\\' -and $_.FullName -notmatch '__pycache__' -and $_.FullName -notmatch '\\data\\' }
if ($secrets.Count -eq 0) {
    Write-Host "  [OK] No exposed secrets in tracked paths" -ForegroundColor Green
} else {
    foreach ($s in $secrets) {
        Write-Host "  [WARN] $($s.FullName)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "## Summary" -ForegroundColor Cyan
Write-Host "  Version: $version"
Write-Host "  Branch: $branch"
Write-Host "  All assets: $allAssets"
Write-Host "  All templates: $allTemplates"
Write-Host "  Version OK: $allVersionOk"

if ($allAssets -and $allTemplates -and $allVersionOk) {
    Write-Host ""
    Write-Host "  RESULT: READY FOR RELEASE" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  RESULT: BLOCKED - Fix issues above" -ForegroundColor Red
}
