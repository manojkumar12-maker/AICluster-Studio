# v2.0 Architecture Review

**AICluster v2.0 â€” Native Desktop Edition | Phase 14**
**Date:** 2026-07-05
**Status:** Design Review â€” No Implementation

---

## 1. Key Questions Answered

### Q1: Can AICluster become ONE executable without redesigning the backend?

**Answer: YES**

The backend already works as a standalone service (`AIClusterRuntime.exe --mode master`). The only change needed is for the Studio to launch it on demand rather than requiring the user to launch it manually. This is a **packaging and process management change**, not an architectural change.

**How:**
- `AICluster Studio.exe` becomes the launcher (already exists as Tauri app)
- Studio uses `CreateProcess` to launch `AIClusterRuntime.exe --mode master` from `runtime/`
- Studio polls `GET /health` until the master is ready
- Studio opens its WebView to the dashboard

**What doesn't change:**
- `AIClusterRuntime.exe --mode master` runs identically to v2.0.0
- All 131 API endpoints remain unchanged
- Database schema unchanged
- All engines unchanged
- Worker protocol unchanged

**Result:**
- User sees ONE executable
- Backend sees ZERO changes
- Win-win.

---

### Q2: Can Master remain an internal service?

**Answer: YES**

The Master has no user interface requirements â€” it's a headless REST API server. It already runs as a background process (windowed mode in v1.4). Making it "internal" means:

- No Start Menu shortcut for Master
- No desktop shortcut for Master
- Studio manages its lifecycle
- User never interacts with it directly

**What's needed:**
- Launcher in Studio (Rust sidecar) to start/stop/monitor
- Health check polling
- Crash recovery logic
- All of this is new code in Studio only â€” no backend changes

**v2.0.0 users can still launch Master directly** (backward compatible).

---

### Q3: Can Workers remain unchanged?

**Answer: YES**

Workers register with the Master via HTTP protocol. They don't care whether the Master was launched manually or by Studio. The worker EXE is already an internal service (windowed mode in v1.4).

**What's needed:**
- In Standalone mode, Studio launches Worker after Master is healthy
- Watchdog restarts Worker if it crashes
- No changes to `worker/app/` or the worker EXE

**v2.0.0 workers can connect to v2.0 Master** (protocol unchanged).
**V2.0 workers can connect to v2.0.0 Master** (protocol unchanged).

---

### Q4: Can APIs remain unchanged?

**Answer: YES**

APIs are the contract between Studio (and other clients) and Master. Changing them would break:
- Web dashboard (Next.js)
- CLI tool
- Worker registration
- Third-party integrations
- Studio itself

**Guarantee:** ZERO API changes in v2.0.

---

### Q5: Can the installer remain compatible?

**Answer: YES**

The v2.0 installer must:
- Detect existing v2.0.0 installation
- Preserve `data/`, `config/`, `models/`, `plugins/`, `logs/`
- Replace `runtime/` executables
- Update shortcuts (remove Master, Worker, MCC, WCC; keep only Studio)

This is a standard Inno Setup upgrade pattern. No breaking changes.

---

## 2. Architecture Verification

### 2.1 Structural Comparison

```
                    v2.0.0                              v2.0
                    â”€â”€â”€â”€â”€â”€â”€                             â”€â”€â”€â”€
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”               â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
            â”‚  User launches:  â”‚               â”‚  User launches:  â”‚
            â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚               â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
            â”‚  â”‚  Studio    â”‚  â”‚               â”‚  â”‚  Studio    â”‚  â”‚
            â”‚  â”‚  Master    â”‚  â”‚               â”‚  â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜  â”‚
            â”‚  â”‚  Worker    â”‚  â”‚               â”‚        â”‚          â”‚
            â”‚  â”‚  MCC       â”‚  â”‚               â”‚  â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”  â”‚
            â”‚  â”‚  WCC       â”‚  â”‚               â”‚  â”‚  Launcher  â”‚  â”‚
            â”‚  â”‚  CLI       â”‚  â”‚               â”‚  â”‚  Service   â”‚  â”‚
            â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚               â”‚  â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜  â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜               â”‚        â”‚          â”‚
                  â”‚                            â”‚  â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”  â”‚
                  â–¼                            â”‚  â”‚  Master    â”‚  â”‚
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”               â”‚  â”‚  (auto)    â”‚  â”‚
            â”‚  Master Server   â”‚               â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
            â”‚  (manual start)  â”‚               â”‚        â”‚          â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜               â”‚  â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”  â”‚
                  â”‚                            â”‚  â”‚  Worker    â”‚  â”‚
            â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”                     â”‚  â”‚  (auto)    â”‚  â”‚
            â”‚  Worker(s)  â”‚                     â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
            â”‚  (manual)   â”‚                     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                     
```

### 2.2 Data Flow Comparison

```
v2.0.0 Data Flow:
  User â†’ Launch Master (manually)
  User â†’ Launch Studio (manually)
  Studio â†’ Master (API calls)
  Worker â†’ Master (auto)

v2.0 Data Flow:
  User â†’ Launch Studio (only action needed)
  Studio â†’ Launch Master (auto)
  Studio â†’ Wait for Master health (auto)
  Studio â†’ Launch Worker (auto, if Standalone)
  Studio â†’ Open Dashboard (auto)
  Worker â†’ Master (auto)
```

### 2.3 Component Impact Matrix

| Component | v2.0.0 | v2.0 | Change Required? |
|-----------|--------|------|------------------|
| `backend/app/` | Master server | Master server | **NONE** |
| `worker/app/` | Worker agent | Worker agent | **NONE** |
| `shared/` | Protocols + types | Protocols + types | **NONE** |
| `frontend/` | Web dashboard | Web dashboard | **NONE** |
| `config/` | YAML config | YAML config + secrets | Additive (backward compat) |
| `studio/` | Desktop UI | Desktop UI + Launcher | **Add launcher module** |
| `master-control-center/` | Desktop app | Deprecated | **Mark deprecated** |
| `worker-control-center/` | Desktop app | Deprecated | **Mark deprecated** |
| `build/` | Build system | Build system (updated paths) | **Path updates** |
| `build/setup/` | Installer | Installer (new layout) | **Layout updates** |
| `runtime/` | N/A | NEW | **Create directory** |
| `.github/` | CI/CD | CI/CD (+ security) | **Add security workflow** |

---

## 3. Backward Compatibility Guarantee

### 3.1 What v2.0 Preserves

| Feature | Guarantee |
|---------|-----------|
| REST API | 100% compatible â€” same endpoints, same request/response formats |
| WebSocket protocol | 100% compatible â€” same events, same format |
| Worker registration | 100% compatible â€” same HTTP endpoints, same payload |
| Heartbeat format | 100% compatible â€” same fields, same intervals |
| Job protocol | 100% compatible â€” same create/poll/progress/result flow |
| Authentication | 100% compatible â€” same JWT format, same header |
| Database schema | 100% compatible â€” no migrations needed |
| Configuration files | 100% compatible â€” old config works, new config is additive |
| Plugin API | 100% compatible â€” same hook system, same SDK |
| Audit events | 100% compatible â€” same categories, same format |
| CLI commands | 100% compatible â€” same arguments, same output |
| Environment variables | 100% compatible â€” same variable names |

### 3.2 What Changes (and Why It's Safe)

| Change | Type | Why Safe |
|--------|------|----------|
| Studio launches Master | Behavioral | Master EXE unchanged; just started differently |
| Studio manages Worker | Behavioral | Worker EXE unchanged; just started differently |
| MCC/WCC deprecated | Informational | Still works; no code removed |
| New `runtime/` directory | Structural | Old EXEs still work from any location |
| New `config/role.json` | Additive | Old config still loaded; role is optional |
| New `config/secrets.enc` | Additive | Old `data/secret.key` still read as fallback |
| Consolidated `logs/` | Structural | Old log paths still written (soft compat) |

---

## 4. Architecture Review Summary

### 4.1 Strengths of the v2.0 Plan

| Strength | Reason |
|----------|--------|
| **Zero backend changes** | Studio launcher is entirely new code in Studio |
| **Backward compatible** | Every existing integration continues to work |
| **Gradual migration** | Each phase is independent and reversible |
| **No data migration** | SQLite schema untouched |
| **Reduced complexity** | 6 EXEs â†’ 1 visible; 3 desktop apps â†’ 1 |
| **Professional UX** | System tray, notifications, auto-start, dark mode |
| **Security improvements** | Plugin RCE fix, input validation, encrypted secrets |
| **Smaller footprint** | ~5 GB of dev artifacts removed; release ~22% smaller |

### 4.2 Risks

| Risk | Mitigation |
|------|------------|
| Rust/Tauri API compatibility | Pin Tauri v2 version; test on all Windows targets |
| Process management edge cases | Thorough testing of start/stop/crash scenarios |
| User adaptation | Deprecate MCC/WCC gradually; keep backward compat |
| Installer upgrade path | Test upgrade from v2.0.0 repeatedly |
| Permission issues | Administrator rights for install; user rights for runtime |

### 4.3 Final Verdict

```
Can AICluster become one executable?         YES
Can Master remain internal?                   YES
Can Workers remain unchanged?                 YES
Can APIs remain unchanged?                    YES
Can installer remain compatible?              YES
Can existing data survive upgrade?            YES
Can existing plugins survive upgrade?         YES
Can existing models survive upgrade?          YES

Is any backend redesign needed?               NO
Is any database migration needed?             NO
Is any API versioning needed?                 NO
Is any protocol change needed?                NO
Is any configuration reformat needed?         NO

Estimated implementation time:                7 weeks
Estimated risk level:                         LOW-MEDIUM
Backward compatibility:                       100%
```

---

## 5. The End State

### 5.1 User Experience

```
DOWNLOAD â†’ INSTALL â†’ LAUNCH â†’ CHOOSE ROLE â†’ READY

No manual service startup.
No PowerShell commands.
No command prompt windows.
No developer knowledge required.
No configuration files to edit.
```

### 5.2 What the User Sees

```
Start Menu:
  AICluster Studio                   â† The only entry

Desktop:
  AICluster Studio.exe               â† The only shortcut

System Tray:
  [A] AICluster Studio               â† Status at a glance

Apps & Features:
  AICluster Studio v2.0.0            â† Clean uninstall
```

### 5.3 What the User Does NOT See

```
Hidden (managed by Studio):
  runtime/AIClusterRuntime.exe --mode master        â† Auto-started
  runtime/AIClusterRuntime.exe --mode worker        â† Auto-started (Standalone)
  config/role.json                   â† Created by wizard
  config/secrets.enc                 â† Auto-generated
  data/aicluster.db                  â† Auto-created
  logs/*.log                         â† Auto-managed
  updates/*                          â† Auto-downloaded
```

### 5.4 What Remains Compatible

```
Existing v2.0.0 workers              â†’ Connect to v2.0 Master âœ“
Existing v2.0.0 plugins              â†’ Run on v2.0 Master âœ“
Existing v2.0.0 database             â†’ Loaded by v2.0 Master âœ“
Existing v2.0.0 configuration        â†’ Read by v2.0 Master âœ“
Existing v2.0.0 CLI                  â†’ Works with v2.0 Master âœ“
Existing v2.0.0 web dashboard        â†’ Works with v2.0 Master âœ“
Existing v2.0.0 MCC/WCC              â†’ Works with v2.0 Master âœ“
```

---

## 6. Conclusion

**AICluster v2.0 is achievable with zero backend changes.**

The migration is a **packaging and desktop integration project**, not an architecture redesign. All the hard work â€” the distributed compute engine, the AI runtime, the repository intelligence, the multi-agent system, the workflow engine â€” is already built and stable in v2.0.0.

v2.0 wraps this proven backend in a professional desktop shell that feels like:

- **Docker Desktop** (local services managed by one app)
- **GitHub Desktop** (focused, polished single-purpose tool)
- **Slack / Discord** (system tray, notifications, auto-start)

The plan is phased, low-risk, backward-compatible, and estimated at **7 weeks** for a single developer.

**Ready for Phase A â€” Repository Cleanup â€” upon approval.**
