# Executable Analysis

**AICluster v2.0 â€” Native Desktop Edition | Phase 2**
**Date:** 2026-07-05
**Status:** Analysis Only â€” No Implementation

---

## 1. Executable Inventory

### 1.1 Current Executables

| # | Executable | Type | Size | Console | Source | Status |
|---|------------|------|------|---------|--------|--------|
| E1 | `AICluster Studio.exe` | Tauri v2 | ~80 MB | No | `studio/` | **Primary UI** |
| E2 | `AIClusterRuntime.exe --mode master` | PyInstaller | ~263 MB | No (v1.4+) | `build/modules/master_entry.py` | **Backend service** |
| E3 | `AIClusterRuntime.exe --mode worker` | PyInstaller | ~55 MB | No (v1.4+) | `build/modules/worker_entry.py` | **Backend service** |
| E4 | `aicluster.exe` | PyInstaller | ~31 MB | Yes | `build/modules/cli_entry.py` | **CLI tool** |
| E5 | `MasterControlCenter.exe` | Tauri v2 | ~60 MB | No | `master-control-center/` | **Desktop app (redundant)** |
| E6 | `WorkerControlCenter.exe` | Tauri v2 | ~60 MB | No | `worker-control-center/` | **Desktop app (redundant)** |
| E7 | `AIClusterSetup-2.0.0.exe` | Inno Setup | ~350 MB | No | `build/setup/` | **Installer** |

### 1.2 Total Distribution Size

| Component | Est. Size | % of Total |
|-----------|-----------|------------|
| Studio (E1) | ~80 MB | 13% |
| Master (E2) | ~263 MB | 43% |
| Worker (E3) | ~55 MB | 9% |
| CLI (E4) | ~31 MB | 5% |
| MCC (E5) | ~60 MB | 10% |
| WCC (E6) | ~60 MB | 10% |
| Support files | ~60 MB | 10% |
| **Total** | **~609 MB** | 100% |

---

## 2. Per-Executable Deep Analysis

### 2.1 E1 â€” AICluster Studio.exe

| Attribute | Value |
|-----------|-------|
| **Role** | Primary desktop user interface |
| **Technology** | Tauri v2 (Rust shell + React/TypeScript frontend) |
| **Source** | `studio/` |
| **Output path** | `studio/src-tauri/target/release/AICluster Studio.exe` |
| **Build command** | `cd studio && npm run tauri build` |
| **Dependencies** | WebView2 (system), Rust runtime (linked) |
| **API dependencies** | Master REST API at localhost:8000 |
| **Startup** | Launches webview pointing to local React app |
| **Can become internal?** | No â€” this is the primary user-facing executable |
| **Should user ever see it?** | **YES** â€” This is the only EXE users should launch |
| **Duplicate prevention** | Not implemented â†’ needs named mutex |
| **System tray** | Not implemented â†’ needs Tauri system tray API |
| **v2.0 target** | Add launcher features directly into this EXE |

### 2.2 E2 â€” AIClusterRuntime.exe --mode master

| Attribute | Value |
|-----------|-------|
| **Role** | Backend server â€” REST API, WebSocket, services, engines, database |
| **Technology** | PyInstaller (Python 3.13 + FastAPI + uvicorn) |
| **Source** | `build/modules/master_entry.py` â†’ `backend/app/` |
| **Output path** | `dist/master/AIClusterRuntime.exe --mode master` |
| **Build command** | `python -m build.pyinstaller_builder` |
| **Port** | 8000 (configurable via `AICLUSTER_API_PORT`) |
| **Dependencies** | SQLite (bundled), Python libraries (all bundled) |
| **Startup time** | ~5-10 seconds (Python interpreter + imports + DB init) |
| **Startup order** | 1st (must be running before Studio can connect) |
| **Shutdown order** | Last (after all workers disconnect, after Studio disconnects) |
| **Can become internal?** | **YES** â€” Launch on demand from Studio launcher |
| **Should user ever see it?** | **NO** â€” Should be launched and managed by Studio |
| **v2.0 target** | Move to `runtime/AIClusterRuntime.exe --mode master`, launch via Studio |

### 2.3 E3 â€” AIClusterRuntime.exe --mode worker

| Attribute | Value |
|-----------|-------|
| **Role** | Worker agent â€” registers with master, executes jobs |
| **Technology** | PyInstaller (Python 3.13 + FastAPI + httpx) |
| **Source** | `build/modules/worker_entry.py` â†’ `worker/app/` |
| **Output path** | `dist/worker/AIClusterRuntime.exe --mode worker` |
| **Build command** | `python -m build.pyinstaller_builder` |
| **Port** | 8001 (configurable) |
| **Dependencies** | Master server (must be reachable) |
| **Startup time** | ~3-5 seconds |
| **Startup order** | 2nd (after master is ready) |
| **Shutdown order** | 1st (before master) |
| **Can become internal?** | **YES** â€” Launch on demand from Studio (Standalone/Master role) |
| **Should user ever see it?** | **NO** â€” Should be launched and managed by Studio |
| **v2.0 target** | Move to `runtime/AIClusterRuntime.exe --mode worker`, launch via Studio |

### 2.4 E4 â€” aicluster.exe (CLI)

| Attribute | Value |
|-----------|-------|
| **Role** | Command-line interface for headless operations |
| **Technology** | PyInstaller (Python 3.13) |
| **Source** | `build/modules/cli_entry.py` |
| **Output path** | `dist/aicluster.exe` |
| **Build command** | `python -m build.pyinstaller_builder` |
| **Dependencies** | Master server (for most commands) |
| **Console** | Yes â€” CLI needs console I/O |
| **Can become internal?** | No â€” CLI is inherently a separate tool |
| **Should user ever see it?** | **Optional** â€” Only for advanced users, scripting |
| **v2.0 target** | Keep as `runtime/aicluster.exe`, not exposed in Start Menu |

### 2.5 E5 â€” MasterControlCenter.exe

| Attribute | Value |
|-----------|-------|
| **Role** | Cluster management desktop application |
| **Technology** | Tauri v2 (Rust + React/TypeScript) + Python FastAPI backend |
| **Source** | `master-control-center/` |
| **Features** | Dashboard, Workers, Jobs, Cluster, Discovery, Backups, Notifications, Logs, Diagnostics, Settings, About |
| **Can become internal?** | **YES** â€” All features should merge into Studio |
| **Should user ever see it?** | **NO** â€” Studio replaces this entirely |
| **v2.0 target** | Mark deprecated; migrate unique features to Studio |

### 2.6 E6 â€” WorkerControlCenter.exe

| Attribute | Value |
|-----------|-------|
| **Role** | Worker PC management desktop application |
| **Technology** | Tauri v2 (Rust + React/TypeScript) + Python FastAPI backend |
| **Source** | `worker-control-center/` |
| **Features** | Dashboard, Configuration, ConnectionTest, Diagnostics, Installation, Logs, Settings, Welcome, About |
| **Can become internal?** | **YES** â€” All features should merge into Studio |
| **Should user ever see it?** | **NO** â€” Studio replaces this entirely |
| **v2.0 target** | Mark deprecated; migrate unique features to Studio |

### 2.7 E7 â€” AIClusterSetup-2.0.0.exe

| Attribute | Value |
|-----------|-------|
| **Role** | Windows installer â€” one-click installation |
| **Technology** | Inno Setup 6 |
| **Source** | `build/setup/setup.iss` |
| **Size** | ~350 MB (includes all EXEs + support files) |
| **Can become internal?** | N/A â€” installer is not an application |
| **v2.0 target** | Update to install to `AICluster/` layout, create shortcuts to Studio only |

---

## 3. Executable Dependency Graph

```
                          AIClusterSetup.exe
                                â”‚
                                â–¼ (installs)
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚   Installed Package    â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚  AICluster Studio.exe â”‚  â—„â”€â”€ USER LAUNCHES THIS
                    â”‚  (Tauri - React UI)   â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                â”‚ launches
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚  AIClusterRuntime.exe --mode master  â”‚  â—„â”€â”€ MANAGED (auto-start)
                    â”‚  (FastAPI backend)    â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                â”‚ health check
                                â–¼
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚   Studio WebView      â”‚
                    â”‚   Dashboard opens     â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    
                    Optional (Standalone mode):
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚  AIClusterRuntime.exe --mode worker  â”‚  â—„â”€â”€ MANAGED (auto-start)
                    â”‚  (Worker agent)       â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

                    Not exposed to user:
                    aicluster.exe            â—„â”€â”€ CLI (advanced users only)
                    MasterControlCenter.exe  â—„â”€â”€ DEPRECATED â†’ merged into Studio
                    WorkerControlCenter.exe  â—„â”€â”€ DEPRECATED â†’ merged into Studio
```

---

## 4. Startup Order

| Order | Executable | Action | Condition | Timeout |
|-------|-----------|--------|-----------|---------|
| 1 | `AICluster Studio.exe` | User launches | â€” | â€” |
| 2 | `AIClusterRuntime.exe --mode master` | Studio launches (if role=Master/Standalone) | Port 8000 free | 30s for health |
| 3 | Health check | Studio polls /health | Master ready | 30s total |
| 4 | `AIClusterRuntime.exe --mode worker` | Studio launches (if role=Worker/Standalone) | Master healthy | 15s |
| 5 | Dashboard | Studio opens WebView | Master healthy | â€” |

---

## 5. Shutdown Order

| Order | Executable | Action | Timeout |
|-------|-----------|--------|---------|
| 1 | `AIClusterRuntime.exe --mode worker` | Studio sends SIGTERM | 10s |
| 2 | Force kill worker | If not stopped | 1s |
| 3 | `AIClusterRuntime.exe --mode master` | Studio sends SIGTERM | 10s |
| 4 | Force kill master | If not stopped | 1s |
| 5 | Studio exits | â€” | â€” |

---

## 6. v2.0 Executable Architecture

### 6.1 Proposed Executable Set

| # | Executable | Location | Visibility | Managed By | Change |
|---|------------|----------|------------|------------|--------|
| 1 | `AICluster Studio.exe` | Root | **User-facing** | User | Add launcher features |
| 2 | `AIClusterRuntime.exe --mode master` | `runtime/` | Hidden | Studio | No change needed |
| 3 | `AIClusterRuntime.exe --mode worker` | `runtime/` | Hidden | Studio | No change needed |
| 4 | `aicluster.exe` | `runtime/` | Hidden (optional) | User/CLI | No change needed |
| 5 | `MasterControlCenter.exe` | REMOVED | N/A | N/A | Features merged into Studio |
| 6 | `WorkerControlCenter.exe` | REMOVED | N/A | N/A | Features merged into Studio |

### 6.2 What Users See

```
Before v2.0:
  AICluster Studio.exe           â† One of many
  AIClusterRuntime.exe --mode master            â† Confusing - which one do I run?
  AIClusterRuntime.exe --mode worker            â† Confusing
  MasterControlCenter.exe        â† Why are there 3 desktop apps?
  WorkerControlCenter.exe        â† Which one should I use?
  aicluster.exe                  â† What is this?

After v2.0:
  AICluster Studio.exe           â† ONLY thing in Start Menu
  (runtime/AIClusterRuntime.exe --mode master)  â† Hidden, managed by Studio
  (runtime/AIClusterRuntime.exe --mode worker)  â† Hidden, managed by Studio
  (runtime/aicluster.exe)        â† CLI only, not in Start Menu
```

---

## 7. Summary

| Question | Answer |
|----------|--------|
| How many EXEs do users see today? | **6** (Studio, Master, Worker, MCC, WCC, CLI) |
| How many EXEs should users see in v2.0? | **1** (AICluster Studio.exe) |
| Can Master become internal? | **Yes** â€” start on demand, no code changes |
| Can Worker become internal? | **Yes** â€” start on demand, no code changes |
| Can MCC be removed? | **Yes** â€” features merged to Studio |
| Can WCC be removed? | **Yes** â€” features merged to Studio |
| Does CLI stay? | **Yes** â€” but hidden in runtime/, not in Start Menu |
| Any backend changes needed? | **None** â€” all changes are in Studio launcher |
