# Migration Report

**AICluster v2.0.0 â†’ v1.4.0 â€” Enterprise Packaging & Native Windows Architecture**
**Date:** 2026-07-05
**Status:** Proposed Plan â€” Not Yet Implemented

---

## 1. Migration Overview

### 1.1 Scope

This migration transforms AICluster from a development repository into a professional Windows desktop product. All changes are **additive or packaging-related**. No backend APIs are modified, no database schema changes occur, no existing functionality is removed.

### 1.2 Migration Principles

| Principle | Description |
|-----------|-------------|
| **Zero breaking changes** | All existing APIs, database schemas, and configurations remain valid |
| **Backward compatible** | v2.0.0 configurations and databases work with v1.4 |
| **Additive only** | No removal of working functionality |
| **No architecture redesign** | Backend, worker, and engine architectures unchanged |
| **Gradual migration** | Each objective can be implemented independently |

---

## 2. Migration Steps

### Step 1: Repository Cleanup

**Duration:** 1-2 hours
**Risk:** Low

#### Actions:

```
1. Delete development artifacts:
   rm nul
   rm -rf build/hello build/hello2 build/main_master build/test_pkg build/test_spec
   rm -rf backend/app/build
   rm -f backend/app/main_master_version.txt
   rm -f build/modules/*.spec build/modules/*_version.txt

2. Update .gitignore:
   Add: build/modules/build/, build/modules/dist/, dist/
   Add: **/__pycache__/, **/.pytest_cache/, **/.ruff_cache/
   Add: .env, .env.local, .env.example
   Add: data/*, logs/* (except .gitkeep)
   Add: **/src-tauri/target/

3. Run cleanup script:
   PowerShell -File scripts/clean.ps1
```

#### Verification:
- [ ] `git status` shows only intentional deletions
- [ ] `python -m build.build --verify-only` passes
- [ ] Backend tests pass: `pytest backend/tests/ -v`

---

### Step 2: Documentation Restructure

**Duration:** 2-3 hours
**Risk:** Low (links may break temporarily)

#### Actions:

```
1. Create documentation directory structure:
   mkdir -p docs/Architecture docs/Installation docs/Security
   mkdir -p docs/Development docs/Audit docs/Release
   mkdir -p docs/API docs/UserGuide docs/Migration

2. Move files to new locations (see REPOSITORY_RESTRUCTURE_REPORT.md Â§3.3)

3. Update internal links in all .md files

4. Create docs/README.md as documentation index

5. Update root README.md to reference new doc locations
```

#### Link Update Map:

| Old Path | New Path | Files to Update |
|----------|----------|-----------------|
| `docs/INSTALLATION.md` | `docs/Installation/INSTALLATION.md` | README.md, CHANGELOG.md |
| `docs/QUICK_START.md` | `docs/Installation/QUICK_START.md` | README.md |
| `docs/FIRST_CLUSTER.md` | `docs/UserGuide/FIRST_CLUSTER.md` | README.md |
| `docs/DEPLOYMENT.md` | `docs/Deployment/DEPLOYMENT.md` | README.md |
| `docs/TROUBLESHOOTING.md` | `docs/UserGuide/TROUBLESHOOTING.md` | README.md |
| `docs/FAQ.md` | `docs/UserGuide/FAQ.md` | README.md |
| `docs/UPGRADING.md` | `docs/Migration/UPGRADING.md` | README.md, CHANGELOG.md |
| `SECURITY.md` | `docs/Security/SECURITY.md` | Root level keep symlink |
| `CONTRIBUTING.md` | `docs/Development/CONTRIBUTING.md` | Root level keep symlink |

#### Verification:
- [ ] All internal links resolve correctly
- [ ] `docs/README.md` renders properly on GitHub
- [ ] Root README.md is clean and minimal
- [ ] No broken anchors in navigation

---

### Step 3: Create Runtime Directory & Update Entry Points

**Duration:** 2-3 hours
**Risk:** Medium (entry point changes affect build)

#### Actions:

```
1. Create runtime/ directory:
   mkdir runtime
   
2. Move entry scripts from build/modules/ to runtime/:
   cp build/modules/master_entry.py runtime/master-entry.py
   cp build/modules/worker_entry.py runtime/worker-entry.py
   cp build/modules/cli_entry.py runtime/cli-entry.py

3. Update build/config.py to point entries to runtime/:
   entry=RUNTIME_DIR / "master-entry.py"
   entry=RUNTIME_DIR / "worker-entry.py"
   entry=RUNTIME_DIR / "cli-entry.py"

4. Update output_subdir from "master"/"worker"/"cli" to "runtime":
   output_subdir="runtime"
   output_subdir="runtime"
   output_subdir="runtime"

5. Create runtime/runtime.json manifest:
   {
     "version": "1.4.0",
     "services": {
       "master": {
         "executable": "AIClusterRuntime.exe --mode master",
         "description": "AICluster Master Server",
         "default_port": 8000,
         "health_endpoint": "/health",
         "startup_timeout_seconds": 30
       },
       "worker": {
         "executable": "AIClusterRuntime.exe --mode worker",
         "description": "AICluster Worker Agent",
         "default_port": 8001,
         "startup_timeout_seconds": 15
       },
       "cli": {
         "executable": "aicluster.exe",
         "description": "AICluster Command Line Interface"
       }
     }
   }
```

#### Build Config Changes:

```python
# build/config.py â€” Updated paths

REPO_ROOT = _detect_repo_root()
BUILD_DIR = REPO_ROOT / "build"
RUNTIME_DIR = REPO_ROOT / "runtime"  # NEW
ASSETS_DIR = REPO_ROOT / "assets"
RELEASE_DIR = REPO_ROOT / "release"

def _make_pyinstaller_targets():
    return [
        PyInstallerTarget(
            key="master",
            entry=RUNTIME_DIR / "master-entry.py",
            output_name="AIClusterRuntime.exe --mode master",
            output_subdir="runtime",     # Changed from "master"
            console=False,
            ...
        ),
        PyInstallerTarget(
            key="worker",
            entry=RUNTIME_DIR / "worker-entry.py",
            output_name="AIClusterRuntime.exe --mode worker",
            output_subdir="runtime",     # Changed from "worker"
            console=False,
            ...
        ),
        PyInstallerTarget(
            key="cli",
            entry=RUNTIME_DIR / "cli-entry.py",
            output_name="aicluster.exe",
            output_subdir="runtime",     # Changed from "cli"
            console=True,
            ...
        ),
    ]
```

#### Verification:
- [ ] `python -m build.pyinstaller_builder` produces all 3 EXEs
- [ ] Each EXE runs and reports correct version
- [ ] `runtime/runtime.json` is bundled with master EXE as add_data
- [ ] Master EXE starts on :8000 successfully
- [ ] Worker EXE starts on :8001 successfully

---

### Step 4: Add Studio Launcher Service

**Duration:** 1-2 days
**Risk:** Medium (new Rust/Tauri code)

#### Actions:

```
1. Create launcher service module in studio:
   studio/src-tauri/src/launcher/
     mod.rs         â€” Launcher service module
     process.rs     â€” Process management (start/stop/monitor)
     config.rs      â€” Role configuration
     wizard.rs      â€” First-run wizard state
     tray.rs        â€” System tray integration
     autostart.rs   â€” Windows auto-start registration

2. Add Tauri commands:
   get_role, set_role, start_services, stop_services,
   restart_service, get_service_status, is_first_run,
   open_dashboard, get_master_url, set_autostart

3. Create React components:
   frontend/src/components/FirstRunWizard.tsx
   frontend/src/components/ServiceManager.tsx
   frontend/src/components/RoleIndicator.tsx
   frontend/src/components/ServiceStatusBar.tsx
   frontend/src/components/SetupProgress.tsx

4. Add system tray configuration to tauri.conf.json

5. Add named mutex for duplicate instance prevention
```

#### Tauri Command Signature:

```rust
// studio/src-tauri/src/launcher/mod.rs

#[tauri::command]
pub async fn get_role() -> Result<Role, String> {
    let config = RoleConfig::load()?;
    Ok(config.role)
}

#[tauri::command]
pub async fn set_role(role: Role, settings: RoleSettings) -> Result<(), String> {
    let config = RoleConfig { role, settings, configured: true };
    config.save()?;
    Ok(())
}

#[tauri::command]
pub async fn start_services() -> Result<ServiceStatus, String> {
    let config = RoleConfig::load()?;
    let manager = ServiceManager::new(&config);
    manager.start_all().await
}

#[tauri::command]
pub async fn get_service_status() -> Result<Vec<ServiceInfo>, String> {
    let manager = ServiceManager::new(&RoleConfig::load()?);
    manager.get_status().await
}
```

#### Verification:
- [ ] Studio builds and launches successfully
- [ ] First Run Wizard appears on first launch
- [ ] Role selection persists across restarts
- [ ] Master service starts when role=Master
- [ ] Worker service starts when role=Worker
- [ ] Both start when role=Standalone
- [ ] Services stop when Studio closes
- [ ] Duplicate instance prevention works
- [ ] System tray icon appears

---

### Step 5: Configuration Restructure

**Duration:** 4-6 hours
**Risk:** Low (additive, backward compatible)

#### Actions:

```
1. Create config/secrets.yaml.enc infrastructure:
   - Windows DPAPI encryption/decryption module
   - Auto-generation of secrets on first run
   - Migration of existing secret.key to new format

2. Split config/default.yaml into focused files:
   config/default.yaml          â€” Core settings (unchanged)
   config/cluster.yaml          â€” Cluster topology
   config/models.yaml           â€” LLM provider settings
   config/workers.yaml          â€” Worker fleet settings
   config/secrets.enc           â€” Encrypted secrets (new)

3. Update config loading in backend/app/config.py:
   - Load default.yaml first
   - Load cluster/models/workers as overrides
   - Decrypt secrets.enc for sensitive values
   - Apply environment variable overrides

4. Add launcher configuration:
   config/role.json             â€” Role selection (written by wizard)
```

#### Backward Compatibility:

```python
# backend/app/config.py â€” Backward-compatible config loading

class Settings(BaseSettings):
    """Settings with backward-compatible loading."""
    
    # Existing settings (unchanged)
    app_name: str = "AICluster"
    app_version: str = "1.4.0"
    secret_key: str = Field(default="", alias="AICLUSTER_SECRET_KEY")
    # ... all existing settings ...
    
    # New settings (additive, defaults maintain old behavior)
    config_dir: Path = REPO_ROOT / "config"
    cluster_config: Path = REPO_ROOT / "config" / "cluster.yaml"
    model_config: Path = REPO_ROOT / "config" / "models.yaml"
    secrets_file: Path = REPO_ROOT / "config" / "secrets.enc"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Backward compatibility: if old secret.key exists, use it
        legacy_secret = REPO_ROOT / "data" / "secret.key"
        if legacy_secret.exists() and not self.secret_key:
            self.secret_key = legacy_secret.read_text().strip()
        
        # Load new config files if they exist
        if self.cluster_config.exists():
            self._load_yaml(self.cluster_config)
        if self.model_config.exists():
            self._load_yaml(self.model_config)
```

#### Verification:
- [ ] All existing settings work without change
- [ ] New config files are optional (not required)
- [ ] Secrets encrypted with DPAPI
- [ ] Legacy secret.key is still read for backward compatibility
- [ ] Environment variables still override everything
- [ ] All 131 API endpoints receive correct config

---

### Step 6: Release Packaging

**Duration:** 4-6 hours
**Risk:** Low (automated by build system)

#### Actions:

```
1. Update build/package.py for new layout:
   - Output to release/v1.4.0/
   - Organize by target: studio, runtime, config, assets, licenses
   - Generate checksums
   - Create portable ZIP

2. Create release/v1.4.0/runtime.json manifest

3. Generate SHA-256 checksums for all files

4. Update build/setup_builder.py:
   - New directory structure
   - Firewall rules for runtime/*.exe
   - Desktop shortcut to AICluster Studio.exe
   - Start menu entries

5. Create release/v1.4.0/licenses/ with third-party notices
```

#### Directory Structure:

```
release/
  v1.4.0/
    AICluster Studio.exe          [Tauri build]
    runtime/
      AIClusterRuntime.exe --mode master          [PyInstaller build]
      AIClusterRuntime.exe --mode worker          [PyInstaller build]
      aicluster.exe                [PyInstaller build]
      runtime.json                 [Service manifest]
    config/
      default.yaml                 [Default settings]
    assets/
      icons/
        default.ico
        (other icons)
    licenses/
      NOTICE.txt                   [AICluster license]
      THIRD_PARTY.txt             [Third-party licenses]
    checksums/
      sha256sums.txt              [File checksums]
      sha256sums.txt.asc          [GPG signature]
    AIClusterSetup-1.4.0.exe      [Inno Setup installer]
    AICluster-1.4.0-portable.zip  [Portable version]
```

#### Verification:
- [ ] Release ZIP contains only required files
- [ ] No source code, tests, or dev artifacts in release
- [ ] All executables are valid PE32+ binaries
- [ ] Checksums match after extraction
- [ ] Installer builds and runs
- [ ] Portable ZIP equals installer contents

---

### Step 7: Installer Update

**Duration:** 2-4 hours
**Risk:** Low

#### Actions:

```
1. Update build/setup/setup.iss:
   - New directory layout
   - Install to %ProgramFiles%\AICluster
   - Create data/, logs/, models/, plugins/ dirs
   - Register firewall rules
   - Create shortcuts (Start Menu, Desktop)
   - Launch Studio after installation

2. Test all install modes:
   - Fresh install (no previous version)
   - Upgrade (v2.0.0 â†’ v1.4.0)
   - Repair (over existing installation)
   - Uninstall (complete removal)
```

#### Verification:
- [ ] Fresh install completes without errors
- [ ] All shortcuts created correctly
- [ ] Firewall rules applied
- [ ] Upgrade preserves existing configuration
- [ ] Repair fixes corrupted installation
- [ ] Uninstall removes all files and shortcuts
- [ ] No reboot required

---

### Step 8: Security Hardening

**Duration:** 1-2 days
**Risk:** Medium (plugin fix affects plugin system)

#### Actions:

```
1. Fix plugin upload RCE (V-001):
   - Implement sandbox extraction
   - Add file extension whitelist
   - Add size limits
   - Add zip slip protection

2. Add HTTPS support (V-002):
   - SSL context configuration
   - TLS 1.3 only
   - Auto-cert generation (optional)

3. Secure token storage (V-003):
   - Change from localStorage to sessionStorage
   - Add Tauri secure store integration

4. Error message sanitization (V-004):
   - Add error handler middleware
   - Sanitize production error messages

5. Input size limits (V-008):
   - Add configuration for max sizes
   - Enforce limits in middleware

6. Log security:
   - Add sensitive data redaction
   - Audit path/header sanitization
```

#### Verification:
- [ ] Plugin upload rejects malicious ZIP files
- [ ] HTTPS works with valid certificate
- [ ] Tokens not persisted in localStorage
- [ ] Error messages don't leak internals
- [ ] Large payloads rejected with clear error
- [ ] Logs don't contain sensitive data
- [ ] All existing security tests pass

---

### Step 9: Master Control Center / Worker Control Center Migration

**Duration:** 2-3 days
**Risk:** Medium (feature migration)

#### Actions:

```
1. Identify all unique features in MCC and WCC not in Studio

2. Implement missing features in Studio:
   - Cluster map visualization (from MCC)
   - Node discovery (from MCC)
   - Local process monitoring (from WCC)
   - Per-worker log viewer (from WCC)

3. Update Studio navigation to include new pages

4. Mark MCC/WCC as deprecated in documentation
```

#### Feature Migration Matrix:

| Feature | MCC | WCC | Studio | Action |
|---------|-----|-----|--------|--------|
| Cluster dashboard | Yes | No | Partial | Enhance |
| Worker list | Yes | No | Yes | No change |
| Worker details | Yes | Yes | Yes | No change |
| Job management | Yes | No | Yes | No change |
| Cluster map | Yes | No | No | Implement |
| Node discovery | Yes | No | No | Implement |
| Backups | Yes | No | Yes | No change |
| Diagnostics | Yes | Yes | Partial | Enhance |
| Notifications | Yes | No | Yes | No change |
| Local monitoring | No | Yes | No | Implement |
| Per-worker logs | No | Yes | No | Implement |
| Worker pause/resume | Yes | Yes | Yes | No change |
| Settings | Yes | Yes | Yes | No change |

#### Verification:
- [ ] All MCC/WCC features available in Studio
- [ ] MCC and WCC still work (backward compatible)
- [ ] Studio navigation includes all pages
- [ ] Users guided to use Studio instead of MCC/WCC

---

### Step 10: Validation & Testing

**Duration:** 1-2 days
**Risk:** Low (non-functional changes)

#### Actions:

```
1. Run all existing tests:
   pytest backend/tests/ -v
   pytest worker/tests/ -v
   python scripts/run-integration-test.py

2. Test all EXE builds:
   python -m build.pyinstaller_builder

3. Test Studio build:
   cd studio && npm run build && npm run tauri build

4. Test installer:
   python -m build.setup_builder

5. Manual smoke tests:
   - Fresh install on Windows 10
   - Fresh install on Windows 11
   - Upgrade from v2.0.0
   - Master role operation
   - Worker role operation
   - Standalone role operation
   - Studio launcher (first run, subsequent runs)
   - System tray
   - Service auto-start/stop
   - Crash recovery
```

#### Test Plan:

| Test Case | Expected Result | Priority |
|-----------|----------------|----------|
| Clean install | No errors, all files present | Critical |
| Launch Studio (first run) | Wizard appears | Critical |
| Select Master role | Master starts, dashboard opens | Critical |
| Close Studio | Services stop, no orphaned processes | Critical |
| Launch Studio again | No wizard, dashboard opens directly | Critical |
| Kill Master process | Auto-restart within 30s | High |
| System tray | Icon visible, menu works | High |
| Upgrade from v2.0.0 | Config preserved, all features work | High |
| Uninstall | All files removed | High |
| Duplicate launch | Focus existing window, no new process | Medium |
| Worker role | Connects to master, heartbeat works | High |
| Standalone role | Both master and worker start | High |
| All API endpoints | 200/401 responses (not 500) | Critical |
| All tests | 98/98 passing | Critical |

---

## 3. Rollback Plan

### 3.1 If build fails

```powershell
# Rollback to v2.0.0 build
git checkout v2.0.0
python -m build.build
```

### 3.2 If installer fails

```powershell
# Use the v2.0.0 installer
# Or rebuild with --skip-setup and use portable ZIP
python -m build.build --skip-setup --skip-installer
```

### 3.3 If Studio launcher has issues

- Users can still launch `runtime/AIClusterRuntime.exe --mode master` directly (backward compatible)
- Web dashboard at `http://localhost:3000` still works independently
- CLI at `runtime/aicluster.exe` still works

---

## 4. Migration Timeline

| Step | Duration | Dependencies | Parallel |
|------|----------|--------------|----------|
| 1. Repository Cleanup | 1-2h | None | Yes |
| 2. Documentation Restructure | 2-3h | None | Yes (w/ Step 1) |
| 3. Runtime Directory | 2-3h | Step 1 | No |
| 4. Studio Launcher | 1-2d | Step 3 | No |
| 5. Configuration Restructure | 4-6h | None | Yes (w/ Step 1) |
| 6. Release Packaging | 4-6h | Steps 3, 5 | No |
| 7. Installer Update | 2-4h | Step 6 | No |
| 8. Security Hardening | 1-2d | Step 5 | Yes (w/ Step 4) |
| 9. MCC/WCC Migration | 2-3d | Step 4 | No |
| 10. Validation & Testing | 1-2d | All steps | No |

**Total estimated time: 10-15 days**

---

## 5. Backward Compatibility Guarantees

| Component | v2.0.0 â†’ v1.4 | Notes |
|-----------|----------------|-------|
| REST API | Fully compatible | All endpoints unchanged |
| Database schema | Fully compatible | No migration needed |
| Configuration format | Fully compatible | New files are additive |
| Plugin API | Fully compatible | Plugin SDK unchanged |
| Worker protocol | Fully compatible | Registration/heartbeat unchanged |
| WebSocket protocol | Fully compatible | Message format unchanged |
| Authentication | Fully compatible | JWT token format unchanged |
| Audit event format | Fully compatible | Event categories unchanged |
| Studio API | Fully compatible | Tauri commands unchanged |

---

## 6. Success Criteria

- [ ] Repository root contains only 7-8 files
- [ ] All documentation under `docs/` with proper index
- [ ] `runtime/` directory contains all service EXEs + manifest
- [ ] `config/` directory has focused config files + encrypted secrets
- [ ] Studio is the only user-facing EXE
- [ ] First Run Wizard works correctly
- [ ] Services auto-start based on role
- [ ] Plugin upload RCE vulnerability fixed
- [ ] HTTPS support available (optional)
- [ ] No sensitive data in logs
- [ ] Release package contains only production files
- [ ] Installer creates proper Windows integration
- [ ] All 98 existing tests pass
- [ ] All v2.0.0 configurations work without changes
- [ ] Rollback to v2.0.0 is straightforward
