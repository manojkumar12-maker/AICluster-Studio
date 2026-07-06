# Project Structure Analysis

**AICluster v2.0 — Native Desktop Edition | Phase 1**
**Date:** 2026-07-05
**Status:** Analysis Only — No Implementation

---

## 1. Repository Overview

### 1.1 Top-Level Directory Map

```
AICluster/                    [Repository root - 28 entries]
├── .git/                     [Version control - 204 MB, EXCLUDE from release]
├── .github/                  [CI/CD workflows - DEVELOPMENT ONLY]
├── .gitignore                [Version control config - DEVELOPMENT ONLY]
├── assets/                   [Static assets - RUNTIME: icons, manifest]
├── backend/                  [Master server - APPLICATION CORE]
├── build/                    [Build system - DEVELOPMENT: source + intermediates]
├── CHANGELOG.md              [Documentation - KEEP at root]
├── config/                   [Configuration - RUNTIME: YAML files]
├── CONTRIBUTING.md           [Documentation - MOVE to docs/]
├── data/                     [Runtime data - RUNTIME: SQLite DB, keys]
├── dist/                     [Packaged EXEs - DISTRIBUTION (duplicate)]
├── docs/                     [Documentation - KEEP]
├── frontend/                 [Web dashboard - APPLICATION: Next.js]
├── logs/                     [Runtime logs - RUNTIME OUTPUT]
├── master-control-center/    [Desktop app - MERGE into Studio]
├── models/                   [AI model storage - RUNTIME: model files]
├── NOTICE.md                 [Legal - KEEP at root]
├── nul                       [Stray artifact - DELETE]
├── plugins/                  [Plugin packages - RUNTIME: example plugin]
├── README.md                 [Documentation - KEEP at root]
├── release/                  [Build output - DISTRIBUTION (gitignored)]
├── scripts/                  [Utility scripts - DEVELOPMENT]
├── SECURITY.md               [Documentation - MOVE to docs/]
├── shared/                   [Shared code - APPLICATION: protocol, types]
├── studio/                   [Desktop app - APPLICATION: primary UI]
├── VERSION                   [Version string - KEEP at root]
├── worker/                   [Worker agent - APPLICATION CORE]
└── worker-control-center/    [Desktop app - MERGE into Studio]
```

---

## 2. Folder Classification

### 2.1 Application Core (Must Ship)

| Folder | Purpose | Type | Size | Can Relocate? |
|--------|---------|------|------|---------------|
| `backend/app/` | Master server: API, services, engines, models, database | Python source | ~5 MB | No — core logic |
| `worker/app/` | Worker agent: state machine, executors, services | Python source | ~200 KB | No — core logic |
| `shared/` | Shared protocols, models, schemas (py + ts) | Python + TypeScript source | ~50 KB | No — cross-cutting |
| `studio/` | Primary desktop UI (Tauri v2 + React) | Rust + TypeScript source | ~500 KB | No — primary UX |
| `frontend/` | Web dashboard (Next.js 15) | TypeScript source | ~2 MB | Optional — keep as web UI |

### 2.2 Desktop Apps (To Merge into Studio)

| Folder | Purpose | Type | Est. Size | Disposition |
|--------|---------|------|-----------|-------------|
| `master-control-center/` | Cluster management desktop app | Tauri + Rust + React | ~1 MB source | MERGE into Studio |
| `worker-control-center/` | Worker management desktop app | Tauri + Rust + React | ~1 MB source | MERGE into Studio |

### 2.3 Build System (Development Only — Not Shipped)

| Folder | Purpose | Size | Disposition |
|--------|---------|------|-------------|
| `build/*.py` | Build orchestrator, config, packaging | ~150 KB | Keep in dev repo; exclude from release |
| `build/modules/` | Entry point scripts + PyInstaller intermediates | ~350 MB (intermediates) | Clean intermediates; ship entry scripts |
| `build/verification/` | Build verification scripts | ~150 KB | Dev only |
| `build/setup/` | Installer scripts | ~50 KB | Dev only |
| `build/hello/` | Test build artifacts | 9.6 MB | DELETE |
| `build/hello2/` | Test build artifacts | 35 MB | DELETE |
| `build/main_master/` | Empty | 0 | DELETE |
| `build/test_pkg/` | Empty | 0 | DELETE |
| `build/test_spec/` | Empty | 0 | DELETE |
| `backend/app/build/` | Build intermediate | 113 MB | DELETE |

### 2.4 Runtime Data (Created at Runtime — Not Shipped)

| Folder | Purpose | Initial State | Permissions |
|--------|---------|---------------|-------------|
| `data/` | SQLite database, secret keys | Empty | Read/write by app |
| `logs/` | Application logs | Empty | Read/write by app |
| `models/` | LLM model files | Empty (gitkeep) | Read/write by user |
| `plugins/` | Installed plugins | Example plugin | Read/write by user |

### 2.5 Distribution Artifacts (Not in Source Control, Regenerated)

| Folder | Purpose | Size | Disposition |
|--------|---------|------|-------------|
| `dist/` | PyInstaller output (duplicate of build/modules/dist/) | 335 MB | DELETE — regenerated |
| `release/` | Release packaging output | 334 MB | DELETE — regenerated |
| `build/modules/dist/` | PyInstaller output | 333 MB | CLEAN — intermediate |

### 2.6 Development Infrastructure (Not Shipped)

| Folder | Purpose | Size | Disposition |
|--------|---------|------|-------------|
| `.git/` | Git version control | 204 MB | Dev only |
| `.github/` | GitHub Actions workflows | < 1 MB | Dev only |
| `backend/.venv/` | Python virtual env | 101 MB | Dev only |
| `worker/.venv/` | Python virtual env | 49 MB | Dev only |
| `master-control-center/backend/.venv/` | Python virtual env | 34 MB | Dev only |
| `worker-control-center/backend/.venv/` | Python virtual env | 34 MB | Dev only |
| `frontend/node_modules/` | npm packages | ~400 MB | Dev only |
| `studio/node_modules/` | npm packages | ~200 MB | Dev only |
| `master-control-center/frontend/node_modules/` | npm packages | ~200 MB | Dev only |
| `worker-control-center/frontend/node_modules/` | npm packages | ~200 MB | Dev only |
| `frontend/.next/` | Next.js build cache | 69 MB | Dev only |
| `master-control-center/frontend/src-tauri/target/` | Rust build cache | 1.3 GB | Dev only |
| `studio/src-tauri/target/` | Rust build cache | 1.3 GB | Dev only |

### 2.7 Stale/Orphan Items

| Item | Size | Problem | Action |
|------|------|---------|--------|
| `nul` | 155 B | Stray artifact from redirected command | DELETE |
| `backend/.env` | 237 B | Contains secrets — should not be committed | GITIGNORE + DELETE |
| `worker/.env` | 180 B | Contains secrets | GITIGNORE + DELETE |
| `frontend/.env.local` | 142 B | Contains secrets | GITIGNORE + DELETE |
| `settings.json` | N/A | VSCode settings — gitignored but present | No action needed |

---

## 3. Dependency Analysis

### 3.1 Python Dependencies (backend/requirements.txt)

```
fastapi==0.115.4           Web framework
uvicorn[standard]==0.32.0  ASGI server
sqlalchemy==2.0.36         ORM
alembic==1.14.0            Migrations (not configured)
pydantic==2.10.2           Validation
pydantic-settings==2.6.1   Settings management
python-jose[cryptography]==3.3.0  JWT
bcrypt<4.1                Password hashing
passlib[bcrypt]==1.7.4    Password library
python-multipart==0.0.16  Form parsing
websockets==14.1          WebSocket support
aiosqlite==0.20.0         Async SQLite
greenlet==3.1.1           Async context
httpx==0.28.0             HTTP client
slowapi==0.1.10           Rate limiting
```

### 3.2 Worker Dependencies (worker/requirements.txt)

```
fastapi>=0.100.0           Web framework (health endpoint only)
uvicorn[standard]>=0.20.0  ASGI server
httpx>=0.25.0              HTTP client to master
psutil>=5.9.0              System monitoring
pydantic>=2.0.0            Validation
pydantic-settings>=2.0.0   Settings
```

### 3.3 Studio Dependencies (studio/package.json)

```
@tauri-apps/api@^2         Tauri API bindings
react@^18                  UI framework
react-dom@^18              React DOM
typescript@^5.6            TypeScript
vite@^6                    Build tool
@tauri-apps/cli@^2         Tauri CLI (dev)
```

### 3.4 Frontend Dependencies (frontend/package.json)

```
next@15.0.3                React framework
react@^18                  UI framework
zustand@^5                 State management
@tanstack/react-query@^5   Data fetching
tailwindcss@^3.4           Styling
framer-motion@^11          Animation
recharts@^2                Charts
lucide-react@^0.460        Icons
shadcn/ui                  Component library
```

---

## 4. Unused / Empty Directories

| Directory | Status | Notes |
|-----------|--------|-------|
| `backend/app/production/audit/` | EMPTY | `__init__.py` only |
| `backend/app/production/benchmark/` | EMPTY | `__init__.py` only |
| `backend/app/production/deployment/` | EMPTY | `__init__.py` only |
| `backend/app/production/security/` | EMPTY | `__init__.py` only |
| `backend/app/ai/metrics/` | EMPTY | `__init__.py` only |
| `backend/app/ai/streaming/` | EMPTY | `__init__.py` only |
| `backend/app/ai/memory/` | EMPTY | `__init__.py` only |
| `backend/app/agents/coordinator/` | EMPTY | `__init__.py` only |
| `backend/app/agents/memory/` | EMPTY | `__init__.py` only |
| `backend/app/agents/roles/` | EMPTY | `__init__.py` only |
| `backend/app/engineering/approvals/` | EMPTY | `__init__.py` only |
| `data/` | EMPTY | Runtime data directory |
| `models/` | EMPTY | `.gitkeep` only |
| `build/main_master/` | EMPTY | Should be deleted |
| `build/test_pkg/` | EMPTY | Should be deleted |
| `build/test_spec/` | EMPTY | Should be deleted |

---

## 5. Duplicate / Overlapping Directories

| Group | Paths | Issue |
|-------|-------|-------|
| **PyInstaller outputs** | `build/modules/dist/`, `dist/`, `release/master/`, `release/worker/`, `release/cli/` | 3 copies of same EXEs |
| **Desktop apps** | `studio/`, `master-control-center/`, `worker-control-center/` | 3 Tauri apps with overlapping features |
| **Entry scripts** | `build/modules/master_entry.py`, `worker_entry.py`, `cli_entry.py` | Currently in build/ module — should be in runtime/ |
| **Virtual environments** | 4 `.venv/` dirs across backend, worker, MCC, WCC | All separate, ~218 MB total |
| **Node modules** | 4 `node_modules/` dirs across frontend, studio, MCC, WCC | ~1 GB total |

---

## 6. Development-Only Directories Summary

| Directory | Est. Size | Reason |
|-----------|-----------|--------|
| `.git/` | 204 MB | Version control |
| `**/.venv/` | 218 MB | Python dev environments |
| `**/node_modules/` | ~1 GB | npm dev dependencies |
| `**/src-tauri/target/` | 2.6 GB | Rust build cache |
| `frontend/.next/` | 69 MB | Next.js build cache |
| `build/modules/build/` | 200 MB | PyInstaller intermediates |
| `backend/app/build/` | 113 MB | Build intermediate |
| `build/hello/`, `build/hello2/` | 45 MB | Test build artifacts |
| `**/__pycache__/` | ~100 MB | Python bytecode |
| `.pytest_cache/`, `.ruff_cache/` | < 1 MB | Test/lint caches |
| **Total dev-only** | **~4.5 GB** | |

---

## 7. Application Core Summary (What Ships)

| Component | Location | Est. Size (Source) | Type |
|-----------|----------|-------------------|------|
| Master backend | `backend/app/` | ~5 MB | Python source + requirements |
| Worker agent | `worker/app/` | ~200 KB | Python source + requirements |
| Shared code | `shared/` | ~50 KB | Python + TypeScript |
| Studio UI | `studio/` | ~500 KB | Rust + React + TypeScript |
| Web dashboard | `frontend/src/` | ~2 MB | Next.js + TypeScript |
| Configuration | `config/` | ~2 KB | YAML |
| Assets | `assets/` | ~10 KB | Icons, manifest |
| Build system | `build/` (source only) | ~150 KB | Python scripts |
| Documentation | `docs/` | ~500 KB | Markdown |
| **Total source** | | **~8 MB** | |

---

## 8. Recommendations for v2.0

| # | Recommendation | Rationale |
|---|---------------|-----------|
| 1 | Create `runtime/` directory for service executables | Separates application EXEs from source code |
| 2 | Merge MCC and WCC features into Studio | Eliminates 2 redundant Tauri apps |
| 3 | Consolidate PyInstaller outputs to `release/` only | Single source of truth for built EXEs |
| 4 | Move entry scripts from `build/modules/` to `runtime/` | Entry points are runtime, not build artifacts |
| 5 | Clean all build intermediates before release | Reduces repository size by ~4.5 GB |
| 6 | Delete empty placeholder directories | Removes 14 empty `__init__.py`-only dirs |
| 7 | Remove `.env` files from repository | Security — secrets should not be tracked |
| 8 | Delete `nul` stray artifact | Cleanup |
