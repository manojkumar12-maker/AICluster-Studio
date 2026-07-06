# Migration Strategy

**AICluster v2.0.0 â†’ v2.0 â€” Native Desktop Edition | Phase 10**
**Date:** 2026-07-05
**Status:** Design Only â€” No Implementation

---

## 1. Migration Principles

| Principle | Description |
|-----------|-------------|
| **Zero breaking changes** | All APIs, databases, configs, and protocols remain compatible |
| **Seamless upgrade** | Install v2.0 over v2.0.0 â€” config, database, models preserved |
| **No data migration** | SQLite schema unchanged â€” existing databases work |
| **No configuration changes** | All v2.0.0 config files work as-is |
| **Backward compatible EXEs** | Old `AIClusterRuntime.exe --mode master` can run alongside v2.0 Studio |
| **Gradual adoption** | Users can continue using v2.0.0 workflow while v2.0 is prepared |

---

## 2. What Changes

### 2.1 Changes Summary

| Component | v2.0.0 | v2.0 | Breaking? |
|-----------|--------|------|-----------|
| **Primary UI** | Multiple apps (Studio, MCC, WCC) | **Studio only** | No (additive) |
| **EXE locations** | `dist/`, `studio/`, `master-control-center/` | `runtime/` | No (copies moved) |
| **Entry scripts** | `build/modules/*_entry.py` | `runtime/*-entry.py` | No (paths updated) |
| **Build output dir** | `dist/` + `release/` | `release/` only | No (build config change) |
| **Config dir** | `config/` | `config/` (same) | No (backward compat) |
| **Role config** | Not present | `config/role.json` | Additive â€” new file |
| **Secrets** | `data/secret.key` | `config/secrets.enc` | Backward compat |
| **Logs** | `backend/logs/`, `logs/` | `logs/` (consolidated) | Soft (old paths still work) |
| **MCC/WCC** | Separate apps | **Deprecated** | No (still functional) |

### 2.2 What Does NOT Change

| Component | Guarantee |
|-----------|-----------|
| REST API (all 131 endpoints) | 100% backward compatible |
| WebSocket protocol | 100% backward compatible |
| Worker registration protocol | 100% backward compatible |
| Database schema | 100% unchanged |
| Configuration file format | 100% compatible |
| Authentication (JWT format) | 100% compatible |
| Plugin API | 100% compatible |
| Audit event format | 100% compatible |
| CLI commands | 100% compatible |

---

## 3. Migration Steps

### Step 0: Pre-Migration Checklist

```powershell
# Before upgrading, verify current state
Write-Host "AICluster v2.0.0 â†’ v2.0 Pre-Migration Check" -ForegroundColor Cyan

# 1. Stop all AICluster services
Get-Process AIClusterMaster, AIClusterWorker, "AICluster Studio" -ErrorAction SilentlyContinue |
    Stop-Process -Force

# 2. Backup database
Copy-Item "data/aicluster.db" "data/aicluster.db.v2.0.0-backup"

# 3. Backup configuration
Copy-Item "config" "config.v2.0.0-backup" -Recurse

# 4. Note current version
$version = Get-Content VERSION
Write-Host "Current version: $version" -ForegroundColor Yellow
Write-Host "Ready to upgrade to v2.0" -ForegroundColor Green
```

### Step 1: Install v2.0 (Over Existing Installation)

```
Run: AIClusterSetup-2.0.0.exe

Installer behavior:
  â”Œâ”€ Detect previous installation?
  â”‚  â”œâ”€ YES â†’ Preserve:
  â”‚  â”‚        â”œâ”€ config/  (all user settings, role.json, secrets.enc)
  â”‚  â”‚        â”œâ”€ data/    (aicluster.db, secret.key)
  â”‚  â”‚        â”œâ”€ models/  (all LLM model files)
  â”‚  â”‚        â”œâ”€ plugins/ (all installed plugins)
  â”‚  â”‚        â””â”€ logs/    (existing log files)
  â”‚  â”‚
  â”‚  â”‚         Update:
  â”‚  â”‚         â”œâ”€ runtime/ (new AIClusterRuntime.exe --mode master, Worker.exe, CLI)
  â”‚  â”‚         â”œâ”€ AICluster Studio.exe (new launcher)
  â”‚  â”‚         â””â”€ assets/, licenses/ (updated)
  â”‚  â”‚
  â”‚  â””â”€ NO  â†’ Fresh install (full layout)
  â”‚
  â””â”€ Create shortcuts (Start Menu, Desktop)
  â””â”€ Configure firewall (if selected)
  â””â”€ Launch AICluster Studio after install
```

### Step 2: Post-Install Verification

```powershell
Write-Host "AICluster v2.0 Post-Install Verification" -ForegroundColor Cyan

# Verify new layout
$layoutChecks = @(
    "AICluster Studio.exe",
    "runtime\AIClusterRuntime.exe --mode master",
    "runtime\AIClusterRuntime.exe --mode worker",
    "runtime\aicluster.exe",
    "runtime\runtime.json",
    "config\default.yaml",
    "licenses\NOTICE.txt"
)

foreach ($file in $layoutChecks) {
    $path = Join-Path $env:ProgramFiles "AICluster\$file"
    if (Test-Path $path) {
        Write-Host "[OK] $file" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $file" -ForegroundColor Red
    }
}

# Verify old data preserved
$dataChecks = @(
    "data\aicluster.db",
    "data\secret.key"
)

foreach ($file in $dataChecks) {
    $path = Join-Path $env:ProgramFiles "AICluster\$file"
    if (Test-Path $path) {
        Write-Host "[OK] $file preserved" -ForegroundColor Green
    } else {
        Write-Host "[NOT FOUND] $file (will be created on first run)" -ForegroundColor Yellow
    }
}

# Verify config preserved
if (Test-Path "$env:ProgramFiles\AICluster\config\role.json") {
    Write-Host "[OK] Role configuration preserved" -ForegroundColor Green
}
```

---

## 4. Data Preservation

### 4.1 What Is Preserved During Upgrade

| Data | Location | Preserved? | Method |
|------|----------|-----------|--------|
| SQLite database | `data/aicluster.db` | YES | Installer leaves in place |
| JWT secret | `data/secret.key` | YES | Installer leaves in place |
| User config overrides | `config/user.yaml` | YES | Installer leaves in place |
| Cluster config | `config/cluster.yaml` | YES | Installer leaves in place |
| Model files | `models/*` | YES | Installer leaves in place |
| Plugins | `plugins/*` | YES | Installer leaves in place |
| Logs | `logs/*` | YES | Installer preserves |
| Role selection | `config/role.json` | YES | Created by wizard, preserved |

### 4.2 What Is Replaced During Upgrade

| Item | Old Location | New Location | Method |
|------|-------------|-------------|--------|
| Master EXE | `dist/master/AIClusterRuntime.exe --mode master` | `runtime/AIClusterRuntime.exe --mode master` | New installer copy |
| Worker EXE | `dist/worker/AIClusterRuntime.exe --mode worker` | `runtime/AIClusterRuntime.exe --mode worker` | New installer copy |
| CLI EXE | `dist/aicluster.exe` | `runtime/aicluster.exe` | New installer copy |
| Studio EXE | `studio/` build output | `AICluster Studio.exe` | New installer copy |
| Config defaults | `config/default.yaml` | `config/default.yaml` | Updated version |
| Assets | `assets/` | `assets/` | Updated version |
| Licenses | Scattered | `licenses/` | Consolidated |

---

## 5. Backward Compatibility Matrix

### 5.1 Cross-Version Compatibility

| Client | Server v2.0.0 | Server v2.0 | Notes |
|--------|---------------|-------------|-------|
| Studio v2.0.0 | âœ“ Works | âœ“ Works | Studio is just a UI |
| Studio v2.0 | âœ“ Works | âœ“ Works | Studio connects via REST API |
| Master v2.0.0 | N/A | N/A | Internal |
| Master v2.0 | N/A | N/A | Backward compatible API |
| Worker v2.0.0 | âœ“ Works | âœ“ Works | Protocol unchanged |
| Worker v2.0 | âœ“ Works | âœ“ Works | Protocol unchanged |
| CLI v2.0.0 | âœ“ Works | âœ“ Works | CLI just calls API |
| CLI v2.0 | âœ“ Works | âœ“ Works | CLI just calls API |

### 5.2 Mixed-Version Cluster

```
Allowed:
  Master v2.0 + Workers v2.0.0   âœ“ (protocol unchanged)
  Master v2.0.0 + Workers v2.0   âœ“ (protocol unchanged)
  Studio v2.0 + Master v2.0.0    âœ“ (API unchanged)
  Studio v2.0.0 + Master v2.0    âœ“ (API unchanged)

Not Allowed:
  Master v2.0 + Master v2.0.0    âœ— (port conflict)
  Studio v2.0 + no Master        âœ— (cannot connect)
```

---

## 6. Rollback Plan

### 6.1 Rollback from v2.0 to v2.0.0

```powershell
# Rollback script
Write-Host "AICluster v2.0 â†’ v2.0.0 Rollback" -ForegroundColor Yellow

# 1. Stop all services
Get-Process AIClusterMaster, AIClusterWorker, "AICluster Studio" -ErrorAction SilentlyContinue |
    Stop-Process -Force

# 2. Restore v2.0.0 installer
# Run: AIClusterSetup-2.0.0.exe
#    â†’ Installer detects existing v2.0 installation
#    â†’ Preserves data/, config/, models/, plugins/, logs/
#    â†’ Replaces runtime/, AICluster Studio.exe

# 3. Verify rollback
$version = Get-Content "$env:ProgramFiles\AICluster\VERSION"
Write-Host "Rolled back to: $version" -ForegroundColor Yellow
```

### 6.2 Recovery Scenarios

| Scenario | Recovery Action | Data Loss? |
|----------|----------------|------------|
| Installer fails mid-way | Run installer again (repair mode) | No |
| v2.0 Studio crashes on launch | Run `runtime\AIClusterRuntime.exe --mode master` directly (old workflow) | No |
| Database not found | Studio creates new DB; old DB in `data/*.backup` | No (backup exists) |
| Role config lost | First Run Wizard appears â€” reconfigure | No (just role) |
| Worker won't connect | Check master URL; re-enter in Settings | No |
| Plugin compatibility | v2.0.0 plugins work unchanged | No |
| MCC/WCC users | Still available in `runtime/` as standalone | No |

---

## 7. Upgrade Path Diagram

```
v2.0.0
  â”‚
  â”œâ”€â”€ In-place upgrade: Run AIClusterSetup-2.0.0.exe
  â”‚     â””â”€â”€ Config preserved âœ“
  â”‚     â””â”€â”€ Database preserved âœ“
  â”‚     â””â”€â”€ Models preserved âœ“
  â”‚     â””â”€â”€ Plugins preserved âœ“
  â”‚     â””â”€â”€ First run: Wizard for role selection
  â”‚     â””â”€â”€ Dashboard opens: same as before + new features
  â”‚
  â”œâ”€â”€ Fresh install: Run AIClusterSetup-2.0.0.exe on new machine
  â”‚     â””â”€â”€ Full new layout
  â”‚     â””â”€â”€ First run: Full wizard
  â”‚     â””â”€â”€ Can connect to existing v2.0.0 cluster
  â”‚
  â””â”€â”€ Portable: Extract AICluster-2.0.0-portable.zip
        â””â”€â”€ Same layout, no installer
        â””â”€â”€ First run: Wizard for role
```

---

## 8. Success Criteria

- [ ] Install v2.0 over v2.0.0 â€” **all settings preserved**
- [ ] Install v2.0 over v2.0.0 â€” **database works without migration**
- [ ] Install v2.0 over v2.0.0 â€” **all plugins work**
- [ ] Fresh install â€” **wizard appears, role saved**
- [ ] Studio v2.0 connects to **Master v2.0.0** â€” **all API calls work**
- [ ] Worker v2.0.0 connects to **Master v2.0** â€” **all jobs execute**
- [ ] Rollback v2.0 â†’ v2.0.0 â€” **data preserved**
- [ ] No manual database migration scripts needed
- [ ] All environment variables still work (backward compatible)
- [ ] No user-facing breaking changes
