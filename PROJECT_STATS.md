# AICluster — Project Statistics

**Generated:** 2026-07-03  
**Version:** 1.3.0  

All values are **estimated** based on repository analysis (excluding `node_modules`, `.venv`, `__pycache__`, `.git`, `target`, `.next`, `dist`).

---

## File Counts

| Category | Count (estimated) |
|----------|-------------------|
| Total directories | ~80 |
| Total files | ~280 |
| Python files (`.py`) | ~180 |
| TypeScript/TSX files (`.ts`, `.tsx`) | ~63 |
| Markdown files (`.md`) | ~20 |
| Rust files (`.rs`) | ~10 |
| JSON config/lock files | ~44 |
| TOML/INI/cfg/mk files | ~5 |
| Shell/PowerShell scripts | ~6 |

---

## Lines of Code

| Subsystem | LOC (estimated) |
|-----------|-----------------|
| Backend (Python) — `backend/app/` | ~18,000 |
| Worker (Python) — `worker/app/` | ~2,500 |
| Frontend (TypeScript/TSX) — `frontend/src/` | ~8,000 |
| Tauri apps (Rust) — `studio/src-tauri/`, `master-control-center/frontend/src-tauri/`, `worker-control-center/frontend/src-tauri/` | ~500 |
| Build system — `build/`, `scripts/`, config files | ~4,000 |
| Tests (Python + TypeScript) — `backend/tests/`, `worker/tests/` | ~1,500 |

**Total estimated LOC:** ~34,500

---

## API Endpoints

| Application | Endpoints (estimated) |
|-------------|-----------------------|
| Master Backend (`/api/v1/*`) | ~90 |
| Master Control Center (`/api/*`) | ~18 |
| Worker Control Center | ~15 |
| Worker service | ~12 |
| **Total** | **~135** |

### Endpoint breakdown by subsystem

| Subsystem | Endpoints |
|-----------|-----------|
| Authentication | 2 |
| Workers | 10 |
| Jobs | 4 |
| Dashboard / Health | 3 |
| Logs | 1 |
| WebSocket | 1 |
| Workflow Engine | 13 |
| Repository Intelligence | 15 |
| AI Runtime / Chat | 16 |
| Multi-Agent | 14 |
| Engineering Engine | 11 |
| Studio | 7 |
| Audit | 10 |
| Production / Monitoring | 8 |
| Plugins | 8 |
| Cluster / MCC | 18 |

---

## Database Tables

| Subsystem | Tables (estimated) |
|-----------|--------------------|
| Core (workers, jobs, users, logs) | 4 |
| Workflow Engine | 9 |
| Repository Intelligence | 18 |
| AI Runtime | 16 |
| Multi-Agent | 10 |
| Engineering Engine | 10 |
| Studio | 6 |
| Audit | 4 |
| Master Control Center | variable |

**Total estimated tables:** ~59

---

## Workers

| Category | Count (estimated) |
|----------|-------------------|
| Worker service files | ~4 |
| Worker executable targets | 2 |

---

## Plugins

| Category | Count (estimated) |
|----------|-------------------|
| Example plugin | 1 (`example-metrics-reporter`) |
| Plugin SDK framework | Full lifecycle + hook system |

---

## Tests

| Category | Files (estimated) |
|----------|-------------------|
| Backend pytest tests | ~5 files, 44 unit tests, 40 integration tests |
| Worker tests | ~3 files, 14 unit tests |
| Frontend tests | ~2 files (scaffolding) |
| **Total test files** | **~10** |

---

## Executables

| Binary | Description |
|--------|-------------|
| `AIClusterSetup.exe` | Windows installer (NSIS) |
| `AIClusterStudio.exe` | Studio desktop app (Tauri) |
| `AIClusterMasterCC.exe` | Master Control Center (Tauri) |
| `AIClusterWorkerCC.exe` | Worker Control Center (Tauri) |
| Backend server | uvicorn-based FastAPI process |
| Worker agent | uvicorn-based worker service |

**Total: 6 release binaries + 1 installer**

---

## Build Artifacts

| Category | Files (estimated) |
|----------|-------------------|
| Build scripts and configs | ~20 |
| NSIS installer config | 1 |
| Verification scripts | 3 |
| Checksum manifests | 1 |

---

## Documentation

| Category | Pages (estimated) |
|----------|-------------------|
| Root-level documents | 11 (README, CHANGELOG, VISION, PROJECT_STATE, RELEASE_v1.3.0, PROJECT_STATS, HANDOVER_v1.3.1, CONTRIBUTING, SECURITY, LICENSE, VERSION) |
| Architecture docs | 6 |
| Development docs | 4 |
| Model docs | 1 |
| **Total documentation pages** | **~22** |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy Async, SQLite |
| Frontend | Next.js 15, TypeScript, TailwindCSS, shadcn/ui |
| Desktop Apps | Tauri v2 (Rust + React/TypeScript) |
| Worker | Python, FastAPI, psutil |
| Build | Python scripts, PyInstaller, NSIS, Tauri CLI |
| Testing | pytest, Playwright |
| Linting/Formatting | Black, ruff, ESLint, Prettier, rustfmt, clippy |

---

*This file is updated each release. For detailed project state, see `PROJECT_STATE.md`. For the full issue tracker, see `HANDOVER_v1.3.1.md`.*
