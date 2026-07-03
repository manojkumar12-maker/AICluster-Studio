# STARTUP SEQUENCE — Full System Boot Timeline

## 1. Overview

AICluster is a multi-process, multi-machine distributed system. Its startup sequence spans multiple subsystems across the master PC and each worker PC, culminating in a fully operational cluster where users can submit jobs, run workflows, chat with AI agents, and manage the fleet from a web dashboard.

This document chronicles every step from the moment the installer runs to the moment `System Ready` is declared, including the state of every component, the data flowing between them, and the failure modes at each stage.

---

## 2. Startup Sequence Diagram

```
Legend:
  [Component]    Running process/service
  {Action}       System operation
  (State)        Component state
  ~~~network~~~  Network communication


TIME  COMPONENT                          STATE / ACTION
────  ───────────────────────────────────────────────────────────────────────────

T+0s  [Installer]                        {Launched by user}
        │
        ├── Extract Python 3.12          {Install Python if absent}
        ├── Install VC++ Redist          {Install VC++ redistributable}
        ├── Create dirs                  {C:\Program Files\AICluster\*}
        ├── Extract binaries             {master/, worker/, studio/, cli/}
        ├── Configure firewall           {Open ports 8000, 8001, 3000}
        ├── Create shortcuts             {Start Menu items}
        └── Launch AIClusterMaster.exe   {Auto-launch on install complete}

T+5s  [AIClusterMaster.exe]             {STARTING}
        │
        ├── Load environment config      {config/*.yaml, .env}
        ├── Initialize SQLAlchemy engine  {sqlite+aiosqlite:///data/aicluster.db}
        ├── Create data/log directories  {mkdir data/, logs/}
        ├── Set up structured logging    {logging_config.py}
        ├── Load route tables            {import api.v1.router}
        └── Start FastAPI lifespan       {lifespan() async context manager}

T+6s  [Database Init]                   {INIT_DB}
        │
        ├── Create engine                {create_async_engine(sqlite)}
        ├── Import all model classes
        │     ├── worker (Worker)
        │     ├── job (Job)
        │     ├── log (SystemLog)
        │     ├── user (User)
        │     ├── workflow (Workflow, WorkflowTask, TaskDependency, ...)
        │     ├── repository (Repository, RepositoryFile, Symbol, ...)
        │     ├── ai (AIModel, AISession, AIMessage, ...)
        │     ├── agent (Agent, AgentTask, AgentMessage, ...)
        │     ├── engineering (EngineeringPlan, EngineeringTask, ...)
        │     └── studio (StudioWorkspace, StudioProject, ...)
        ├── Run Base.metadata.create_all  {CREATE TABLE IF NOT EXISTS}
        └── Session factory ready         {async_sessionmaker bound}

T+7s  [Auth Bootstrap]                  {SEED_ADMIN}
        │
        ├── Check if admin user exists   {SELECT FROM users}
        ├── Create default admin         {admin / admin123 (bcrypt hashed)}
        ├── Assign admin role            {role = "admin"}
        └── Log: "Default admin user seeded"

T+8s  [Offline Worker Checker]          {STARTING}
        │
        ├── asyncio.create_task(check_offline_workers)
        ├── Loop every 10 seconds
        │     ├── SELECT workers WHERE last_seen < now - 15s
        │     ├── UPDATE status = 'offline'
        │     └── Broadcast worker update via WebSocket
        └── Log: "Offline worker checker started"

T+9s  [WebSocket Manager]               {READY}
        │
        ├── FastAPI accepts /ws connections
        ├── ws_manager.active_connections = []
        ├── broadcast functions ready
        └── Log: "WebSocket endpoint ready"

T+10s [Scheduler Starts]                {STARTING}
        │
        ├── SchedulerService.__init__
        │     ├── db: AsyncSession reference
        │     └── self._running = False
        ├── scheduler.start()
        │     ├── self._running = True
        │     └── asyncio.create_task(_scheduler_loop)
        ├── _scheduler_loop:
        │     └── while _running:
        │           ├── _process_queue()
        │           │     ├── SELECT * FROM jobs WHERE status='queued'
        │           │     │     ORDER BY priority DESC, created_at ASC
        │           │     ├── For each job: _find_available_worker(job)
        │           │     │     ├── SELECT * FROM workers
        │           │     │     │     WHERE status='online' AND is_paused=0
        │           │     │     │     ORDER BY cpu_percent ASC LIMIT 1
        │           │     │     └── If worker found: _assign_job(job, worker)
        │           │     │           ├── job.status = 'running'
        │           │     │           ├── job.assigned_worker = worker.id
        │           │     │           ├── job.started_at = now
        │           │     │           ├── worker.status = 'busy'
        │           │     │           ├── worker.current_job = job.id
        │           │     │           └── Broadcast job update via WebSocket
        │           │     └── If no worker: skip (job stays queued)
        │           └── await asyncio.sleep(2)
        └── Log: "Scheduler started"

T+11s [Workflow Engine]                 {STARTING}
        │
        ├── WorkflowPlanner ready
        │     ├── DAG generation from task list
        │     └── Dependency resolution (topological sort)
        ├── WorkflowDispatcher ready
        │     ├── Task-to-worker assignment by capability
        │     └── Worker capability matching
        ├── WorkflowExecutor ready
        │     ├── State machine: PENDING → RUNNING → COMPLETED/FAILED
        │     ├── Parallel task execution within DAG constraints
        │     └── Error handling with retry
        ├── ArtifactManager ready
        │     ├── SHA256-checksummed artifact storage
        │     ├── Path: data/artifacts/{workflow_id}/{task_id}/
        │     └── Metadata stored in `artifacts` table
        ├── CacheService ready
        │     ├── TTL-based result caching
        │     └── Cache key = (task_type, input_hash)
        └── Log: "Workflow engine initialized"

T+12s [AI Runtime]                      {STARTING}
        │
        ├── ModelRegistry loaded
        │     ├── Scan configured providers (llama.cpp, Ollama, custom)
        │     ├── Validate model availability
        │     └── Register each model with capabilities
        ├── PromptTemplateEngine ready
        │     ├── Load templates from backend/app/ai/prompt/
        │     └── Template rendering with Jinja2-like syntax
        ├── SessionManager ready
        │     ├── Conversation session tracking
        │     ├── Context window management
        │     └── History persistence to AISession/AIMessage tables
        ├── ToolRegistry ready
        │     ├── Registered tools: code_analysis, file_read, search, git
        │     └── Each tool: name, description, input_schema, handler
        ├── Router ready
        │     ├── Model selection based on task complexity
        │     └── Load balancing across available model instances
        └── Log: "AI Runtime initialized"

T+13s [Plugin Loader]                   {STARTING}
        │
        ├── Scan plugins/ directory
        │     ├── For each subdirectory:
        │     │     ├── Read plugin.json
        │     │     ├── Validate: plugin_id, version, permissions, entry_point
        │     │     ├── Check min_platform_version compatibility
        │     │     ├── Verify requested permissions against whitelist
        │     │     └── Import entry_point module
        │     └── Example: plugins/example-metrics-reporter/
        │           ├── plugin_id: "example-metrics-reporter"
        │           ├── hooks: ["on_workflow_finish"]
        │           └── permissions: ["read_metrics"]
        ├── Register plugin hooks
        │     ├── on_workflow_finish → metrics_reporter.handle()
        │     └── Hook registry: dict[str, list[callable]]
        ├── Sandbox initialization
        │     ├── Restricted API surface
        │     └── Permission enforcement on plugin calls
        └── Log: "Loaded N plugins"

T+14s [HTTP Server Bind]                {LISTENING}
        │
        ├── uvicorn.bind(host="0.0.0.0", port=8000)
        ├── Start accepting HTTP connections
        ├── Start accepting WebSocket upgrades at /ws
        ├── OpenAPI docs at /docs (Swagger), /redoc (ReDoc)
        ├── Static file serving for frontend build
        └── Log: "Uvicorn running on http://0.0.0.0:8000"

T+15s [Dashboard Loads]                 {CONNECTING}
        │
        ├── User opens http://localhost:3000
        │     (or localhost:8000 if static build served by FastAPI)
        ├── Next.js 15 App Router initializes
        ├── Dark glassmorphism theme renders
        ├── Zustand auth store checks for persisted JWT
        │     ├── If JWT exists: validate with GET /api/v1/health
        │     └── If invalid/missing: redirect to /login
        └── Loading skeletons appear on dashboard cards

T+16s [Studio Loads]                    {CONNECTING}
        │
        ├── AIClusterStudio.exe (Tauri app) launches
        ├── Tauri window: 1280x800, frameless/chrome per config
        ├── Rust backend binds to port 3001
        ├── Load workspace list from GET /api/v1/studio/workspaces
        ├── Load project list from GET /api/v1/studio/projects
        ├── Layout engine restores saved layout
        │     ├── Grid/panel positions from StudioLayout table
        │     └── Bookmark restoration
        └── Editor panels initialize

T+17s [User Login]                      {AUTHENTICATING}
        │
        ├── User submits credentials (username + password)
        ├── POST /api/v1/auth/login
        │     ├── Validate input via LoginRequest schema
        │     ├── SELECT * FROM users WHERE username = ?
        │     ├── bcrypt.verify(password, hashed_password)
        │     └── Generate JWT (python-jose)
        │           ├── Payload: {sub: user.id, role: user.role, exp: now+60min}
        │           └── Sign with SECRET_KEY (HS256)
        ├── Frontend receives JWT
        │     ├── Store in Zustand auth store
        │     ├── Persist to localStorage
        │     └── Set Authorization: Bearer <token> header
        ├── Redirect to / (dashboard)
        ├── Establish WebSocket connection to /ws
        │     ├── ws_manager.connect(websocket)
        │     └── Receive initial cluster snapshot
        └── Dashboard renders live data
              ├── Worker cards with status indicators
              ├── Job queue table
              ├── Cluster metrics (CPU, RAM, worker count)
              └── Real-time updates via WebSocket

T+18s [System Ready]                    {OPERATIONAL}
        │
        ├── All subsystems running
        ├── Dashboard shows live cluster state
        ├── WebSocket broadcasting updates every 2s
        ├── Scheduler processing jobs
        ├── Workers can register and receive jobs
        ├── AI Runtime ready for inference
        ├── Workflow Engine ready for orchestration
        ├── Plugins active and listening for hooks
        ├── Studio connected and ready
        └── ──── SYSTEM READY ────
```

---

## 3. Detailed Component Startup

### 3.1 Installer (T+0s – T+5s)

The installer is produced by `build/setup_builder.py` using Inno Setup 6. It bundles:
- `python-3.12.7-amd64.exe` — embedded Python installer
- `vc_redist.x64.exe` — Visual C++ redistributable
- Prebuilt executables (PyInstaller + Tauri): master, worker, studio, master-control-center, worker-control-center, CLI
- Default configuration files from `config/`
- Assets (icons, manifest, branding)

The installer writes to `C:\Program Files\AICluster\` with subdirectories:

```
C:\Program Files\AICluster\
├── master\              AIClusterMaster.exe + Python runtime
├── worker\              AIClusterWorker.exe + Python runtime
├── studio\              AIClusterStudio.exe (Tauri)
├── master-control\      MasterControlCenter.exe (Tauri)
├── worker-control\      WorkerControlCenter.exe (Tauri)
├── cli\                 aicluster.exe (CLI tool)
├── config\              Default YAML config files
└── data\                SQLite database, logs, artifacts
```

**Failure modes:**
- Python download fails → installer aborts with network error
- VC++ redist installation fails → log warning, continue (system may already have it)
- Disk space insufficient → Inno Setup reports before extraction
- Antivirus blocks binary → installer exits with code 2

### 3.2 Master Starts (T+5s)

`AIClusterMaster.exe` bootstraps with:

```python
# backend/app/main.py — FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # seed default admin
    # start offline checker background task
    yield
    # cleanup on shutdown
```

The master loads environment from:
1. `.env` file (database URL, secret key, CORS origins, worker timeout, log level)
2. `config/*.yaml` for cluster-level settings

The application state at this point is `STARTING`. The FastAPI router is constructed from all endpoints under `api/v1/`, including workers, jobs, auth, health, dashboard, logs, workflows, agents, AI, plugins, repositories, engineering, and studio.

### 3.3 Database Init (T+6s)

`init_db()` in `backend/app/database.py` performs:

```python
async def init_db():
    # Import all model classes to register with Base.metadata
    from .models.worker import Worker
    from .models.job import Job
    from .models.log import SystemLog
    from .models.user import User
    from .models.workflow import (Workflow, WorkflowTask, ...)
    from .models.repository import (Repository, RepositoryFile, ...)
    from .models.ai import (AIModel, AISession, ...)
    from .models.agent import (Agent, AgentTask, ...)
    from .models.engineering import (EngineeringPlan, EngineeringTask, ...)
    from .models.studio import (StudioWorkspace, StudioProject, ...)

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

This creates all 30+ tables in a single transaction. The database is stored at `data/aicluster.db` (SQLite via aiosqlite). No migrations are run — Alembic is installed but not configured; schema changes in v1.x are additive only.

**Failure modes:**
- Database file is locked → retry with exponential backoff
- Disk full → SQLite raises `sqlite3.OperationalError: database or disk is full`
- Schema conflict → `create_all` with `IF NOT EXISTS` semantics, no-op on existing

### 3.4 Scheduler Starts (T+10s)

The scheduler (`backend/app/services/scheduler.py`) is the job distribution engine:

```python
class SchedulerService:
    async def start(self):
        self._running = True
        asyncio.create_task(self._scheduler_loop())

    async def _scheduler_loop(self):
        while self._running:
            await self._process_queue()
            await asyncio.sleep(2)
```

Its responsibilities:
1. **Queue processing** — Every 2 seconds, scan for `status='queued'` jobs ordered by priority (descending) and creation time (ascending).
2. **Worker assignment** — For each queued job, find the least-loaded online worker (lowest CPU percentage), or use the job's `assigned_worker` if pre-assigned.
3. **Job dispatch** — Update job status to `running`, set `started_at`, mark worker as `busy`, broadcast via WebSocket.

**Worker selection algorithm:**
```
1. If job has assigned_worker:
     → Use that worker if online and not paused
2. If no assigned_worker:
     → SELECT * FROM workers 
       WHERE status = 'online' AND is_paused = false 
       ORDER BY cpu_percent ASC 
       LIMIT 1
```

This ensures workloads are spread evenly across the cluster.

### 3.5 Workflow Engine (T+11s)

The workflow engine (`backend/app/workflow/`) processes complex multi-step tasks as directed acyclic graphs:

```
Subsystem               Path                          Purpose
─────────────────────────────────────────────────────────────────────
WorkflowPlanner        workflow/planner/             DAG generation, topological sort
WorkflowDispatcher     workflow/dispatcher/          Task-to-worker assignment
WorkflowExecutor       workflow/executor/            Orchestration engine, state machine
ArtifactManager        workflow/artifacts/           SHA256-checksummed output storage
CacheService           workflow/cache/               TTL-based result caching
MetricsCollector       workflow/metrics/             Execution metrics (duration, throughput)
StateManager           workflow/state/               WorkflowTask state machine
DependencyResolver     workflow/dependencies/        Task dependency graph resolution
```

The workflow state machine:

```
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ QUEUED   │
                    └────┬─────┘
                         │ (dependencies met)
                    ┌────▼─────┐
                    │ RUNNING  │
                    └────┬─────┘
                    ┌────┴────┐
                    │         │
               ┌────▼──┐ ┌───▼────┐
               │COMPLETE│ │ FAILED │
               │  D     │ │        │
               └────────┘ └───┬────┘
                              │ (retry allowed)
                         ┌────▼─────┐
                         │  QUEUED  │ (max 3 retries)
                         └──────────┘
```

### 3.6 AI Runtime (T+12s)

The AI runtime (`backend/app/ai/`) is the intelligence layer:

| Component | Module | Purpose |
|---|---|---|
| ModelRegistry | `ai/registry/` | Register & query available models |
| Provider abstraction | `ai/providers/` | llama.cpp, Ollama, Custom API |
| PromptEngine | `ai/prompt/` | Template rendering |
| SessionManager | `ai/sessions/` | Conversation context tracking |
| ToolRegistry | `ai/tool_registry/` | Available tool definitions |
| ToolExecutor | `ai/tool_executor/` | Execute tool calls with safety checks |
| Router | `ai/routing/` | Model selection by task type and load |
| ContextManager | `ai/context/` | Context window tracking & truncation |
| MemoryManager | `ai/memory/` | Long-term memory storage & retrieval |
| Streaming | `ai/streaming/` | SSE-based streaming responses |
| Security | `ai/security/` | Prompt injection detection, content filtering |
| Telemetry | `ai/telemetry/` | Usage metrics, latency tracking |
| Validators | `ai/validators/` | Output schema validation |
| Embeddings | `ai/embeddings/` | Text embedding for semantic search |
| Cache | `ai/cache/` | LLM response caching |
| Config | `ai/config/` | Provider configuration |
| Planner | `ai/planner/` | Decompose high-level tasks into steps |
| Reasoning | `ai/reasoning/` | Chain-of-thought, ReAct, tree-of-thought |

### 3.7 Plugins Load (T+13s)

The plugin loader scans `plugins/` for subdirectories containing `plugin.json`:

```python
# Pseudocode for plugin loading
for plugin_dir in plugins.iterdir():
    manifest = json.loads(plugin_dir / "plugin.json")
    validate_manifest(manifest)
    check_permissions(manifest["permissions"])
    check_version_compatibility(manifest["min_platform_version"])
    module = import_module(plugin_dir / manifest["entry_point"])
    register_hooks(manifest["hooks"], module)
    log.info(f"Loaded plugin: {manifest['name']} v{manifest['version']}")
```

**Plugin isolation model:**
- Each plugin runs in a sub-interpreter with restricted globals.
- Hook invocations are wrapped in try/except — a plugin exception does not crash the master.
- Permission checks are enforced at hook dispatch time.
- Plugins cannot import arbitrary modules; only the allowed API surface is exposed.

### 3.8 Workers Connect (T+15s onward)

Worker startup is documented in full in `WORKER_ARCHITECTURE.md`. At a high level:

```
1. Worker process starts → state = STARTING
2. Load config from config.json → state = LOADING_CONFIG
3. Connect to master HTTP API → state = CONNECTING
4. POST /api/v1/workers/register → state = REGISTERING
5. Receive worker_id → state = ONLINE
6. Start heartbeat loop (POST /api/v1/workers/heartbeat every 5s)
7. Start job poll loop (GET /api/v1/workers/{id}/next-job every 5s)
8. Execute assigned jobs
9. Report progress (POST /api/v1/workers/{id}/progress)
10. Report result (POST /api/v1/workers/{id}/result)
```

### 3.9 Dashboard Loads (T+15s)

The frontend (`frontend/`) is a Next.js 15 App Router application with:

- **Zustand** for client state (auth store persisted to localStorage)
- **React Query** (@tanstack/react-query) for server state with 2-second polling
- **shadcn/ui** component library with dark glassmorphism theme
- **Recharts** for real-time charts
- **Framer Motion** for animations

Page load sequence:
1. HTML shell renders immediately (server-side rendered)
2. Zustand auth store hydrates from localStorage
3. If no JWT: redirect to `/login`
4. If JWT present: `GET /api/v1/health` to validate
5. React Query initiates: `GET /api/v1/workers`, `GET /api/v1/jobs`, `GET /api/v1/dashboard`
6. WebSocket connects to `/ws`
7. Skeleton components display while data loads
8. Full dashboard renders with live-updating metrics

### 3.10 Studio Loads (T+16s)

AIClusterStudio (in `studio/`) is a Tauri v2 application:

- Rust backend handles filesystem access, process spawning, native dialogs
- Frontend is a Svelte/React single-page app (per studio's `vite.config.ts`)
- Connects to master's API for workspace and project management
- Restores last-used layout from `StudioLayout` table
- Provides code editor, file browser, terminal, AI chat panel

### 3.11 User Logs In (T+17s)

Authentication flow:
1. User submits `POST /api/v1/auth/login` with `{username, password}`
2. Backend validates via `LoginRequest` Pydantic schema
3. `SELECT * FROM users WHERE username = :username`
4. `passlib.hash.bcrypt.verify(password, user.hashed_password)`
5. On success: generate JWT with `python-jose`:
   ```python
   payload = {
       "sub": user.id,
       "role": user.role,
       "exp": datetime.utcnow() + timedelta(minutes=60)
   }
   token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
   ```
6. Frontend stores token, redirects to `/`
7. Dashboard renders full cluster state

### 3.12 System Ready (T+18s)

The system is declared `OPERATIONAL` when:

- [x] Master HTTP server is accepting connections on port 8000
- [x] Database is initialized with all tables
- [x] Default admin user is seeded
- [x] Offline worker checker is running in background
- [x] Scheduler loop is processing the job queue
- [x] Workflow engine is ready for DAG-based orchestration
- [x] AI Runtime is initialized with model registry and providers
- [x] Plugins are loaded and hooks registered
- [x] WebSocket endpoint is accepting connections
- [x] Dashboard is serving and rendering live data
- [x] Studio is connected to the master API

---

## 4. Component Dependency Graph

```
                    ┌──────────────┐
                    │  Installer   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  SQLite DB   │
                    │  (data dir)  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
        │ Auth       │ │ Worker │ │ Scheduler │
        │ Service    │ │ Manager│ │ Service   │
        └─────┬──────┘ └───┬────┘ └────┬─────┘
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
        │ WebSocket │ │ Master │ │ Job Queue │
        │ Manager   │ │ API    │ │           │
        └─────┬──────┘ └───┬────┘ └──────────┘
              │            │
        ┌─────▼─────┐ ┌───▼──────────────┐
        │ Dashboard │ │ Workflow Engine  │
        │ (Frontend)│ │ ┌──────────────┐ │
        └───────────┘ │ │ Planner      │ │
                      │ │ Dispatcher   │ │
              ┌───────┤ │ Executor     │ │
              │       │ │ Artifacts    │ │
        ┌─────▼─────┐ │ │ Cache        │ │
        │ AI Runtime│ │ └──────────────┘ │
        │ ┌───────┐ │ └──────────────────┘
        │ │Models │ │
        │ │Router │ │
        │ │Tools  │ │
        │ │Memory │ │
        │ └───────┘ │
        └───────────┘
```

---

## 5. Startup Failure Scenarios

| Failure | Detection | Recovery |
|---|---|---|
| Database file corrupt | SQLAlchemy error on `create_all` | Delete or restore `data/aicluster.db` |
| Port 8000 in use | `uvicorn` binding error | Log error; user must free port or change config |
| Secret key missing | RuntimeWarning on JWT decode | Generate random key; log warning |
| Plugin import error | `ImportError` during plugin load | Skip plugin, log error, continue startup |
| Model provider unreachable | Connection refused on provider URL | Log warning; run without AI until provider available |
| Worker timeout during registration | HTTP request timeout | Worker retries with backoff (1s, 2s, 5s, 10s, 30s, 60s) |
| Disk space low | SQLite `disk full` error | Suspend job scheduling; alert dashboard |

---

## 6. Startup Performance Targets

| Metric | Target | Measurement |
|---|---|---|
| Installer execution | <60s | From double-click to completion |
| Master cold start | <3s | From `AIClusterMaster.exe` to `Uvicorn running` |
| Database init | <500ms | Table creation on empty DB |
| Scheduler ready | <100ms | From `start()` to first queue poll |
| AI Runtime init | <2s | Model registry + provider validation |
| Plugin loading | <200ms per plugin | Import + hook registration |
| First dashboard paint | <1.5s | From URL enter to interactive |
| WebSocket connection | <500ms | From client connect to first broadcast |
| Studio launch | <3s | From EXE launch to UI render |
| System Ready | <20s total | From installer Finish to full operation |

---

*End of STARTUP_SEQUENCE.md — This document covers the complete boot timeline from installer to system-ready for the AICluster distributed compute platform.*
