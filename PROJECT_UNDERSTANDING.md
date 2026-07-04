# AICluster Project Understanding

## What is AICluster?

AICluster is an **offline-first AI cluster management platform** for distributed computing across Windows machines. It turns a LAN of Windows PCs into a unified AI compute cluster.

Key capabilities:
- **Distributed job execution** — Master assigns tasks to worker nodes across LAN
- **AI model hosting** — Runs local LLMs (Ollama, llama.cpp, OpenAI-compatible)
- **Multi-agent collaboration** — 12 AI agents that plan, implement, review, and merge code
- **Workflow orchestration** — DAG-based task pipelines with parallel execution
- **Code intelligence** — Multi-language symbol parsing, dependency analysis, full-text search
- **Autonomous engineering** — AI-driven software development pipeline with quality gates
- **Desktop applications** — 3 Tauri desktop apps + 1 web dashboard

---

## How Does It Work?

### Architecture
```
Master Server (FastAPI :8000)
  ├── REST API (140+ endpoints)
  ├── WebSocket (/ws) for real-time updates
  ├── SQLite database (50+ tables)
  ├── Background job scheduler
  └── AI runtime + agents + workflows + plugins

Worker Fleet (FastAPI :8001+)
  └── Register → Heartbeat → Poll Jobs → Execute → Report

Desktop Apps:
  ├── Master Control Center (:8800) — Cluster management
  ├── Worker Control Center (:8900) — Worker setup & monitoring
  └── Studio IDE — AI-assisted development

Web Dashboard (Next.js :3000) — Cluster overview & monitoring
```

---

## How Does a Request Travel?

```
1. Browser → http://localhost:3000/api/v1/health
2. Next.js proxies → http://localhost:8000/api/v1/health
3. FastAPI middleware: CORS → Audit (logs event) → Router
4. Route handler: queries DB or calls service
5. Optional: WebSocket broadcast to connected clients
6. Response returned through chain
```

---

## How Do Workers Communicate?

```
Protocol: HTTP REST (JSON)

Registration:
  Worker → Master: POST /api/v1/workers/register {name, hostname, ip}
  Master → Worker: {id: "uuid"}

Heartbeat (every 5s):
  Worker → Master: POST /api/v1/workers/heartbeat {id, cpu, ram, disk, busy}
  Master → Worker: {status: "ok"}

Job Polling (every 5s):
  Worker → Master: GET /api/v1/workers/{id}/next-job
  Master → Worker: {job: {id, type, payload}} or 204 No Content

Progress Reporting:
  Worker → Master: POST /api/v1/workers/{id}/progress {job_id, progress, logs}

Result Reporting:
  Worker → Master: POST /api/v1/workers/{id}/result {job_id, status, result, error}
```

---

## How Are Workflows Created?

```
1. POST /api/v1/workflow with DAG definition
2. WorkflowPlanner validates DAG (cycle check, topological sort)
3. WorkflowEngine starts execution
4. TaskDispatcher assigns tasks to capable workers
5. Workers execute tasks → report progress/result
6. ArtifactStore collects outputs
7. CacheService caches results
8. On completion: workflow_result + metrics recorded
```

---

## How Are Jobs Executed?

```
1. POST /api/v1/jobs {type, payload, priority}
2. SchedulerService creates job (status='queued')
3. Background scheduler loop (2s interval):
   a. Select queued jobs (ordered by priority)
   b. Find available worker (online, not paused, under load limit)
   c. Assign job to worker (status='running')
   d. WebSocket broadcast
4. Worker polls GET /next-job → receives assignment
5. Worker dispatches to handler by job_type:
   - echo → EchoJobHandler
   - sleep → SleepJobHandler
   - dir_scan → DirectoryScanHandler
   - hash_file → HashFileHandler
   - count_files → CountFilesHandler
6. Handler executes (async)
7. Worker reports progress periodically
8. Worker reports final result
9. Master updates job status, frees worker
```

---

## How Is AI Used?

AI is used in 5 subsystems:

### 1. AI Runtime (`backend/app/ai/`)
- Multi-provider chat (Ollama, llama.cpp, OpenAI)
- Smart model routing by task type
- Session management with conversation history
- Context building from repository data
- Tool execution framework

### 2. Multi-Agent Engine (`backend/app/agents/`)
- 12 default agent roles
- Orchestrated pipeline: plan → execute → review → merge
- Inter-agent messaging via database
- Persistent agent memory

### 3. Engineering Engine (`backend/app/engineering/`)
- Goal analysis from natural language requirements
- Automated planning and task breakdown
- Code implementation and validation
- Self-repair loop on failure
- Quality gates and approval workflow

### 4. Workflow Engine (`backend/app/workflow/`)
- Planning uses AI for task decomposition
- Worker capability matching

### 5. Repository Intelligence (`backend/app/repository/`)
- Multi-language code parsing
- Symbol extraction for context building

---

## How Is the UI Loaded?

### Web Dashboard (Next.js)
```
1. npm run dev → Next.js server on :3000
2. Browser loads page → SSR renders HTML
3. Client JS hydrates → React app mounts
4. Providers initialize: ThemeProvider, QueryProvider
5. Auth check: localStorage token → /dashboard or /login
6. Dashboard layout: Sidebar + Topbar + main content
7. React Query starts polling: dashboard (2s), workers (3s)
8. Components render with loading skeletons → data → live updates
```

### Desktop Apps (Tauri)
```
1. Tauri Rust binary starts
2. Opens native webview window (1280x800)
3. Loads frontend dist/index.html
4. React app mounts
5. Health check polling vs backend (FastAPI on :8800 or :8900)
6. On success: render sidebar + page content
7. React Query polling for live data
```

---

## How Is the Build System Organized?

### Process
```
build-all.bat or python -m build.build
  → 12 stages orchestrated by build.py
  → 7 executables + 1 installer produced
  → 10-stage release verification
```

### Targets (3 packagers)
| Packager | Targets |
|----------|---------|
| PyInstaller | AIClusterMaster.exe, AIClusterWorker.exe, aicluster.exe |
| Tauri v2 | MasterControlCenter.exe, WorkerControlCenter.exe, AIClusterStudio.exe |
| Inno Setup 6 | AIClusterSetup-<ver>.exe (bundles all above + Python + VC++) |

### Key files
- `build/build.py` — Main orchestrator (431 lines)
- `build/config.py` — Target definitions (273 lines)
- `build/pyinstaller_builder.py` — PyInstaller builds (402 lines)
- `build/tauri_builder.py` — Tauri builds (389 lines)
- `build/release.py` — Installer scripts + reports (469 lines)
- `build/setup_builder.py` — AIClusterSetup.exe (401 lines)
- `build/verification/` — 10 verification modules

---

## How Does Deployment Work?

### End-user deployment
```
1. User downloads AIClusterSetup-<version>.exe
2. Runs installer (Inno Setup wizard):
   a. Select components (Master, Worker, Dashboard, apps)
   b. Auto-installs Python 3.12+ if missing
   c. Auto-installs VC++ Redist if missing
   d. Configures Windows Firewall for port 8000
   e. Copies binaries to Program Files
   f. Creates Start Menu shortcuts
   g. Runs verification pass
3. Launch Master Server → dashboard available at http://localhost:3000
4. Install Worker on other machines → auto-connects to master
5. Deploy AI models via Ollama/llama.cpp
```

### Development setup
```
1. git clone
2. python -m build.build  OR  build-all.bat
3. Or manual: ./scripts/setup.ps1
4. Start master: ./scripts/start-master.ps1
5. Start worker: ./scripts/start-worker.ps1
```

### Network requirements
- Master server must be accessible on port 8000 (LAN)
- Workers discover master via configurable URL
- All communication is HTTP REST + WebSocket
- No internet required after initial setup
