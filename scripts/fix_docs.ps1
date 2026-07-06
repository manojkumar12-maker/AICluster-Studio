$root = "C:\Users\a2dpo\AICluster"
$updates = @{}
$updates['v1\.3\.1'] = 'v2.0.0'
$updates['v1\.3\.0'] = 'v2.0.0'
$updates['AIClusterMaster\.exe'] = 'AIClusterRuntime.exe --mode master'
$updates['AIClusterWorker\.exe'] = 'AIClusterRuntime.exe --mode worker'
$updates['AIClusterSetup-1\.3\.1\.exe'] = 'AIClusterSetup-2.0.0.exe'
$updates['AICluster-1\.3\.1-portable'] = 'AICluster-2.0.0-portable'

$docFiles = @()
$searchRoots = @("docs", "")
$searchPatterns = @("*.md")

foreach ($sr in $searchRoots) {
    $base = Join-Path $root $sr
    if (Test-Path $base) {
        $docFiles += Get-ChildItem $base -Include $searchPatterns -Recurse -File | Where-Object { 
            $_.FullName -notmatch '\\node_modules\\' -and $_.FullName -notmatch '\\target\\'
        }
    }
}

$updated = 0
foreach ($file in $docFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    $changed = $false
    foreach ($old in $updates.Keys) {
        if ($content -match $old) {
            $content = $content -replace $old, $updates[$old]
            $changed = $true
        }
    }
    if ($changed) {
        Set-Content $file.FullName -Value $content -Encoding UTF8 -NoNewline
        $relPath = $file.FullName.Replace($root, "").TrimStart("\")
        Write-Host "  [Updated] $relPath"
        $updated++
    }
}

Write-Host ""
Write-Host "Updated $updated documentation files."
