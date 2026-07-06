# Implementation Roadmap

**AICluster v2.0 â€” Native Desktop Edition | Phase 13**
**Date:** 2026-07-05
**Status:** Design Only â€” No Implementation

---

## 1. Phase Overview

| Phase | Name | Duration | Dependencies | Risk | Effort |
|-------|------|----------|--------------|------|--------|
| A | Repository Cleanup | 1-2 days | None | Low | Cleanup |
| B | Runtime Directory | 1-2 days | Phase A | Low | Move files |
| C | Studio Launcher (Rust) | 3-5 days | Phase B | Medium | New code |
| D | Role Wizard (React) | 2-3 days | Phase C | Medium | New code |
| E | Service Manager | 2-3 days | Phase C | Medium | New code |
| F | System Tray | 1-2 days | Phase C | Low | New code |
| G | Windows Integration | 2-3 days | Phase C, F | Medium | Config + code |
| H | Feature Migration (MCC/WCC) | 3-5 days | Phase C | Medium | Code move |
| I | Configuration Restructure | 2-3 days | Phase A | Low | Config files |
| J | Security Hardening | 2-4 days | Phase A | Medium | Code changes |
| K | Installer Update | 1-2 days | Phase B, G | Low | ISS script |
| L | Documentation | 2-3 days | All phases | Low | Markdown |
| M | Validation & Testing | 3-5 days | All phases | Medium | Testing |
| **Total** | | **~25-42 days** | | | |

---

## 2. Phase Details

### Phase A â€” Repository Cleanup

**Duration:** 1-2 days | **Dependencies:** None | **Risk:** Low

#### Tasks:
```
[ ] Run scripts/clean.ps1 to delete stale artifacts
[ ] Update .gitignore with all new patterns
[ ] Remove virtual environments (prompted)
[ ] Remove Rust build caches (prompted)
[ ] Remove node_modules (prompted)
[ ] Remove duplicate EXE directories (dist/, release/)
[ ] Remove .env files with secrets
[ ] Verify essential files still exist
[ ] Run tests to confirm nothing broken
[ ] Commit cleanup to git
```

#### Files to Modify:
- `nul` â†’ DELETE
- `build/hello/`, `build/hello2/` â†’ DELETE
- `build/modules/build/`, `build/modules/dist/` â†’ DELETE
- `dist/`, `release/` â†’ DELETE
- `backend/app/build/` â†’ DELETE
- `.gitignore` â†’ UPDATE
- `scripts/clean.ps1` â†’ CREATE

#### Rollback:
```
git checkout -- .   # Revert all changes
```

#### Verification:
- [ ] `python -m build.build --verify-only` passes
- [ ] `pytest backend/tests/ -v` passes
- [ ] `pytest worker/tests/ -v` passes
- [ ] Repository size reduced by ~5 GB

---

### Phase B â€” Runtime Directory

**Duration:** 1-2 days | **Dependencies:** Phase A | **Risk:** Low

#### Tasks:
```
[ ] Create runtime/ directory at repository root
[ ] Copy entry scripts from build/modules/ to runtime/
[ ] Rename for consistency: master_entry.py â†’ master-entry.py, etc.
[ ] Create runtime/runtime.json manifest
[ ] Update build/config.py to point entries to runtime/
[ ] Update build/pyinstaller_builder.py output_subdir to "runtime"
[ ] Rebuild all EXEs
[ ] Verify EXEs launch correctly
```

#### Files to Create:
- `runtime/master-entry.py` (copy from `build/modules/master_entry.py`)
- `runtime/worker-entry.py` (copy from `build/modules/worker_entry.py`)
- `runtime/cli-entry.py` (copy from `build/modules/cli_entry.py`)
- `runtime/runtime.json`

#### Files to Modify:
- `build/config.py` â†’ Update entry paths, output_subdir
- `build/pyinstaller_builder.py` â†’ Update output paths

#### Rollback:
```
git checkout -- runtime/ build/config.py build/pyinstaller_builder.py
```

#### Verification:
- [ ] `python -m build.pyinstaller_builder` produces all 3 EXEs
- [ ] `runtime/AIClusterRuntime.exe --mode master` starts on :8000
- [ ] `runtime/AIClusterRuntime.exe --mode worker` starts on :8001
- [ ] `runtime/runtime.json` contains correct version info
- [ ] All tests pass

---

### Phase C â€” Studio Launcher (Rust)

**Duration:** 3-5 days | **Dependencies:** Phase B | **Risk:** Medium

#### Tasks:
```
[ ] Create launcher/ module in studio/src-tauri/src/
[ ] Implement RoleConfig (read/write role.json)
[ ] Implement ProcessManager (start/stop processes)
[ ] Implement HealthChecker (HTTP polling)
[ ] Implement Watchdog (monitor + restart)
[ ] Add duplicate instance prevention (named mutex)
[ ] Register Tauri commands: get_role, set_role, start_services, etc.
[ ] Build and test Studio with launcher
```

#### Files to Create:
- `studio/src-tauri/src/launcher/mod.rs`
- `studio/src-tauri/src/launcher/config.rs`
- `studio/src-tauri/src/launcher/process.rs`
- `studio/src-tauri/src/launcher/health.rs`
- `studio/src-tauri/src/launcher/watchdog.rs`
- `studio/src-tauri/src/launcher/tray.rs`
- `studio/src-tauri/src/launcher/autostart.rs`
- `studio/src-tauri/src/launcher/updates.rs`
- `studio/src-tauri/src/commands.rs`

#### Files to Modify:
- `studio/src-tauri/Cargo.toml` â†’ Add dependencies (reqwest, serde, etc.)
- `studio/src-tauri/src/lib.rs` â†’ Register launcher plugins
- `studio/src-tauri/src/main.rs` â†’ Register commands
- `studio/src-tauri/tauri.conf.json` â†’ System tray config

#### Rollback:
```
git checkout -- studio/src-tauri/
cd studio && npm install && npm run tauri build
```

#### Verification:
- [ ] Studio builds without errors
- [ ] Launcher reads/writes role.json
- [ ] ProcessManager starts Master.exe
- [ ] HealthChecker detects running service
- [ ] Watchdog detects crash and restarts
- [ ] Duplicate instance prevention works
- [ ] All Tauri commands respond correctly

---

### Phase D â€” Role Wizard (React)

**Duration:** 2-3 days | **Dependencies:** Phase C | **Risk:** Medium

#### Tasks:
```
[ ] Create WizardContainer component with stepper
[ ] Create WelcomeScreen component (Screen 1)
[ ] Create RoleSelectionScreen component (Screen 2)
[ ] Create MasterConfigScreen component (Screen 3a)
[ ] Create WorkerConfigScreen component (Screen 3b)
[ ] Create StandaloneConfigScreen component (Screen 3c)
[ ] Create SetupProgressScreen component (Screen 4)
[ ] Create CompleteScreen component (Screen 5)
[ ] Create wizard-store with Zustand
[ ] Implement wizard flow: detect first run â†’ show â†’ save â†’ start
```

#### Files to Create:
- `studio/src/components/wizard/WizardContainer.tsx`
- `studio/src/components/wizard/WelcomeScreen.tsx`
- `studio/src/components/wizard/RoleSelectionScreen.tsx`
- `studio/src/components/wizard/MasterConfigScreen.tsx`
- `studio/src/components/wizard/WorkerConfigScreen.tsx`
- `studio/src/components/wizard/StandaloneConfigScreen.tsx`
- `studio/src/components/wizard/SetupProgressScreen.tsx`
- `studio/src/components/wizard/CompleteScreen.tsx`
- `studio/src/stores/wizard-store.ts`
- `studio/src/lib/launcher.ts`

#### Files to Modify:
- `studio/src/App.tsx` â†’ Add wizard route/condition
- `studio/src/index.css` â†’ Wizard styles

#### Rollback:
```
git checkout -- studio/src/
```

#### Verification:
- [ ] Wizard appears on first launch
- [ ] All 3 role paths complete successfully
- [ ] Config saved correctly
- [ ] Services start after wizard completes
- [ ] Wizard does not appear on subsequent launches
- [ ] Reset in Settings re-shows wizard

---

### Phase E â€” Service Manager

**Duration:** 2-3 days | **Dependencies:** Phase C | **Risk:** Medium

#### Tasks:
```
[ ] Create ServiceManager component (React)
[ ] Create ServiceStatusBar component (React)
[ ] Create RoleIndicator component (React)
[ ] Implement service start/stop/restart UI
[ ] Implement service status display
[ ] Implement auto-restart indicator
[ ] Add service controls to Settings page
```

#### Files to Create:
- `studio/src/components/services/ServiceManager.tsx`
- `studio/src/components/services/ServiceStatusBar.tsx`
- `studio/src/components/services/RoleIndicator.tsx`
- `studio/src/stores/service-store.ts`

#### Files to Modify:
- `studio/src/App.tsx` â†’ Add service status bar
- `studio/src/components/Settings.tsx` â†’ Add service management

#### Verification:
- [ ] Service status displays correctly
- [ ] Start/stop/restart buttons work
- [ ] Auto-restart count shown after crashes
- [ ] Status bar shows master/worker health

---

### Phase F â€” System Tray

**Duration:** 1-2 days | **Dependencies:** Phase C | **Risk:** Low

#### Tasks:
```
[ ] Configure system tray in tauri.conf.json
[ ] Implement tray menu with actions
[ ] Implement minimize-to-tray on close
[ ] Implement double-click to show/hide
[ ] Add tray icon state changes (normal/warning/error)
[ ] Handle quit from tray menu
```

#### Files to Modify:
- `studio/src-tauri/tauri.conf.json` â†’ System tray config
- `studio/src-tauri/src/launcher/tray.rs` â†’ Tray logic (create in Phase C)
- `studio/src-tauri/src/lib.rs` â†’ Register tray
- `studio/src/App.tsx` â†’ Handle window close â†’ minimize

#### Verification:
- [ ] Tray icon appears on launch
- [ ] Closing window minimizes to tray
- [ ] Double-click tray shows window
- [ ] Right-click menu works
- [ ] "Quit" stops all services and exits
- [ ] Tray icon changes state when service is down

---

### Phase G â€” Windows Integration

**Duration:** 2-3 days | **Dependencies:** Phase C, F | **Risk:** Medium

#### Tasks:
```
[ ] Implement Windows notifications for key events
[ ] Implement auto-start on login (HKCU\...\Run)
[ ] Implement dark mode detection (registry)
[ ] Implement high DPI awareness (PerMonitorV2)
[ ] Configure file associations (.aicluster)
[ ] Implement deep link handler (aicluster://)
[ ] Add application metadata (version info, manifest)
[ ] Implement firewall configuration
```

#### Files to Modify:
- `studio/src-tauri/src/launcher/autostart.rs` â†’ Complete implementation
- `studio/src-tauri/src/launcher/notifications.rs` â†’ Create
- `studio/src-tauri/src/launcher/deeplink.rs` â†’ Create
- `studio/src-tauri/src/launcher/theme.rs` â†’ Create
- `studio/src-tauri/tauri.conf.json` â†’ File associations, deep links
- `studio/src-tauri/Cargo.toml` â†’ Add winreg crate

#### Verification:
- [ ] Notifications appear for service events
- [ ] Auto-start registers correctly
- [ ] App respects Windows dark/light mode
- [ ] High DPI displays correctly at 150%, 200%
- [ ] `.aicluster` files open in Studio
- [ ] `aicluster://` URIs resolve correctly
- [ ] Firewall rules created (via installer)

---

### Phase H â€” Feature Migration (MCC/WCC)

**Duration:** 3-5 days | **Dependencies:** Phase C | **Risk:** Medium

#### Tasks:
```
[ ] Audit MCC features not in Studio
[ ] Audit WCC features not in Studio
[ ] Implement Worker Details page in Studio
[ ] Implement Cluster Map in Studio
[ ] Implement Node Discovery in Studio
[ ] Implement Local Worker Monitoring in Studio
[ ] Add navigation entries for new pages
[ ] Mark MCC/WCC as deprecated in README
```

#### Files to Create:
- `studio/src/pages/Workers/WorkerDetails.tsx`
- `studio/src/pages/Cluster/ClusterMap.tsx`
- `studio/src/pages/Discovery/NodeDiscovery.tsx`
- `studio/src/pages/Monitoring/LocalMonitor.tsx`

#### Files to Modify:
- `studio/src/components/layout/Sidebar.tsx` â†’ Add new navigation
- `studio/src/App.tsx` â†’ Add routes
- `README.md` â†’ Deprecation notice

#### Verification:
- [ ] All MCC/WCC unique features available in Studio
- [ ] MCC/WCC still work for backward compat
- [ ] Navigation includes all pages

---

### Phase I â€” Configuration Restructure

**Duration:** 2-3 days | **Dependencies:** Phase A | **Risk:** Low

#### Tasks:
```
[ ] Split config/default.yaml into cluster.yaml, models.yaml, workers.yaml
[ ] Implement encrypted secrets (secrets.enc)
[ ] Update Settings to write focused config files
[ ] Ensure backward compat with old config
```

#### Files to Create:
- `config/cluster.yaml`
- `config/models.yaml`
- `config/workers.yaml`
- `config/secrets.enc` (auto-generated)

#### Files to Modify:
- `config/default.yaml` â†’ Keep minimal base
- `backend/app/config.py` â†’ Add multi-file loading
- `studio/src/pages/Settings.tsx` â†’ Update settings UI

#### Verification:
- [ ] Old config files still load
- [ ] New config files created on first run
- [ ] Secrets encrypted correctly
- [ ] Settings UI writes to correct files

---

### Phase J â€” Security Hardening

**Duration:** 2-4 days | **Dependencies:** Phase A | **Risk:** Medium

#### Tasks:
```
[ ] Fix plugin upload RCE (sandbox extraction)
[ ] Implement Tauri command input validation
[ ] Implement update signature verification
[ ] Implement deep link URI validation
[ ] Add process whitelist for launcher
[ ] Add error message sanitization middleware
```

#### Files to Modify:
- `backend/app/plugins/installer.py` â†’ Sandbox extraction
- `studio/src-tauri/src/launcher/process.rs` â†’ Input validation
- `studio/src-tauri/src/launcher/updates.rs` â†’ Signature verification
- `studio/src-tauri/src/launcher/deeplink.rs` â†’ URI validation
- `backend/app/middleware/error_handler.py` â†’ Sanitize errors

#### Verification:
- [ ] Plugin upload RCE test passes
- [ ] Tauri command injection test passes
- [ ] Deep link injection test passes
- [ ] Unsigned updates rejected
- [ ] Error messages don't leak internals

---

### Phase K â€” Installer Update

**Duration:** 1-2 days | **Dependencies:** Phase B, G | **Risk:** Low

#### Tasks:
```
[ ] Update build/setup/setup.iss for v2.0 layout
[ ] Add firewall configuration to installer
[ ] Update Start Menu shortcuts (Studio only)
[ ] Add upgrade detection (v2.0.0 â†’ v2.0)
[ ] Add data/config preservation
[ ] Build and test installer
```

#### Files to Modify:
- `build/setup/setup.iss` â†’ New layout, new shortcuts
- `build/setup_builder.py` â†’ Updated paths

#### Verification:
- [ ] Fresh install creates correct layout
- [ ] Upgrade preserves config/data/models/plugins
- [ ] Start Menu has only one entry (Studio)
- [ ] Desktop shortcut works
- [ ] Uninstall removes everything
- [ ] Firewall configured (if selected)

---

### Phase L â€” Documentation

**Duration:** 2-3 days | **Dependencies:** All phases | **Risk:** Low

#### Tasks:
```
[ ] Create docs/v2/ARCHITECTURE_REVIEW.md
[ ] Update README.md for v2.0 workflow
[ ] Update CHANGELOG.md with v2.0 changes
[ ] Create User Guide for first-run experience
[ ] Create Admin Guide for configuration
[ ] Update API documentation if needed
```

#### Files to Modify:
- `README.md` â†’ v2.0 quick start
- `CHANGELOG.md` â†’ v2.0 release notes

#### Files to Create:
- `docs/UserGuide/FIRST_RUN.md`
- `docs/UserGuide/ADMIN_GUIDE.md`

#### Verification:
- [ ] README describes Studio as single entry point
- [ ] CHANGELOG lists all v2.0 changes
- [ ] User guide covers first-run wizard
- [ ] Admin guide covers configuration

---

### Phase M â€” Validation & Testing

**Duration:** 3-5 days | **Dependencies:** All phases | **Risk:** Medium

#### Tasks:
```
[ ] Run all existing tests (98 total)
[ ] Test fresh install on Windows 10
[ ] Test fresh install on Windows 11
[ ] Test upgrade from v2.0.0 to v2.0
[ ] Test all 3 role paths (Master, Worker, Standalone)
[ ] Test system tray (minimize, restore, quit)
[ ] Test service auto-start/stop/restart
[ ] Test crash recovery
[ ] Test Windows notifications
[ ] Test dark mode switching
[ ] Test high DPI
[ ] Test deep links
[ ] Test performance benchmarks
[ ] Test security fixes
[ ] Run integration tests
```

#### Verification Checklist:
- [ ] 98/98 existing tests pass
- [ ] All new tests pass
- [ ] Fresh install: first-run wizard works
- [ ] Upgrade: data/config preserved
- [ ] Master role: services start correctly
- [ ] Worker role: connects to remote master
- [ ] Standalone: both services start
- [ ] System tray: minimize/restore/quit
- [ ] Crash recovery: auto-restart works
- [ ] Notifications: appear for key events
- [ ] Performance: startup < 15s, memory < 500 MB
- [ ] Security: all hardening measures in place

---

## 3. Dependency Graph

```
Phase A (Cleanup)
  â”‚
  â”œâ”€â”€â–º Phase B (Runtime Dir)
  â”‚       â”‚
  â”‚       â”œâ”€â”€â–º Phase C (Studio Launcher)
  â”‚       â”‚       â”‚
  â”‚       â”‚       â”œâ”€â”€â–º Phase D (Role Wizard)
  â”‚       â”‚       â”œâ”€â”€â–º Phase E (Service Manager)
  â”‚       â”‚       â”œâ”€â”€â–º Phase F (System Tray)
  â”‚       â”‚       â”œâ”€â”€â–º Phase G (Windows Integration)
  â”‚       â”‚       â””â”€â”€â–º Phase H (Feature Migration)
  â”‚       â”‚
  â”‚       â””â”€â”€â–º Phase K (Installer Update)
  â”‚
  â””â”€â”€â–º Phase I (Config Restructure)
  â””â”€â”€â–º Phase J (Security Hardening)
  â””â”€â”€â–º Phase L (Documentation)

All phases â†’ Phase M (Validation & Testing)
```

---

## 4. Timeline

```
Week 1:  AAAA BBBB
Week 2:  CCCC CCCC C
Week 3:  C DDD EEE
Week 4:  FFF GGG HHH
Week 5:  HH III JJJ
Week 6:  JJ KKK LLL
Week 7:  MMM MMM M
        (Buffer)
        
Total: ~7 weeks (35 working days)
```

---

## 5. Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| A (Cleanup) | Low | All deletions are reversible via git |
| B (Runtime) | Low | Only file moves and path updates |
| C (Launcher) | Medium | New Rust code; compile errors likely; Tauri API changes between versions |
| D (Wizard) | Medium | React state management complexity |
| E (Manager) | Medium | IPC between Rust and React |
| F (Tray) | Low | Well-documented Tauri API |
| G (Windows) | Medium | Registry operations; requires admin on some operations |
| H (Migration) | Medium | Duplicate features risk |
| I (Config) | Low | Backward compat ensures safety |
| J (Security) | Medium | Plugin sandbox is complex |
| K (Installer) | Low | Inno Setup is stable |
| L (Docs) | Low | No code changes |
| M (Testing) | Medium | Integration test complexity |

---

## 6. Release Checklist

```markdown
## v2.0.0 Release Checklist

### Pre-Release
- [ ] All phases A-M complete
- [ ] 98/98 existing tests pass
- [ ] All new v2.0 tests pass
- [ ] Security review complete
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Build
- [ ] Repository cleaned (Phase A)
- [ ] All EXEs rebuilt (Phase B)
- [ ] Studio built with launcher (Phase C)
- [ ] Installer built (Phase K)
- [ ] All EXEs Authenticode signed
- [ ] SHA-256 checksums generated
- [ ] Checksums GPG-signed

### Verification
- [ ] Fresh install on Windows 10 22H2
- [ ] Fresh install on Windows 11 24H2
- [ ] Upgrade from v2.0.0
- [ ] Repair install
- [ ] Uninstall (complete removal)
- [ ] All 3 role paths verified
- [ ] System tray verified
- [ ] Crash recovery verified

### Release
- [ ] CHANGELOG.md updated
- [ ] VERSION file updated to 2.0.0
- [ ] Release tagged in git
- [ ] Release artifacts uploaded
- [ ] Release notes published
```
