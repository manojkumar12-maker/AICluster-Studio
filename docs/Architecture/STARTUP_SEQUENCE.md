# STARTUP SEQUENCE â€” Full System Boot Timeline

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
â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

T+0s  [Installer]                        {Launched by user}
        â”‚
        â”œâ”€â”€ Extract Python 3.12          {Install Python if absent}
        â”œâ”€â”€ Install VC++ Redist          {Install VC++ redistributable}
        â”œâ”€â”€ Create dirs                  {C:\Program Files\AICluster\*}
        â”œâ”€â”€ Extract binaries             {master/, worker/, studio/, cli/}
        â”œâ”€â”€ Configure firewall           {Open ports 8000, 8001, 3000}
        â”œâ”€â”€ Create shortcuts             {Start Menu items}
        â””â”€â”€ Launch AIClusterRuntime.exe --mode master   {Auto-launch on install complete}

T+5s  [AIClusterRuntime.exe --mode master]             {STARTING}
        â”‚
        â”œâ”€â”€ Load environment config      {config/*.yaml, .env}
        â”œâ”€â”€ Initialize SQLAlchemy engine  {sqlite+aiosqlite:///data/aicluster.db}
        â”œâ”€â”€ Create data/log directories  {mkdir data/, logs/}
        â”œâ”€â”€ Set up structured logging    {logging_config.py}
        â”œâ”€â”€ Load route tables            {import api.v1.router}
        â””â”€â”€ Start FastAPI lifespan       {lifespan() async context manager}

T+6s  [Database Init]                   {INIT_DB}
        â”‚
        â”œâ”€â”€ Create engine                {create_async_engine(sqlite)}
        â”œâ”€â”€ Import all model classes
        â”‚     â”œâ”€â”€ worker (Worker)
        â”‚     â”œâ”€â”€ job (Job)
        â”‚     â”œâ”€â”€ log (SystemLog)
        â”‚     â”œâ”€â”€ user (User)
        â”‚     â”œâ”€â”€ workflow (Workflow, WorkflowTask, TaskDependency, ...)
        â”‚     â”œâ”€â”€ repository (Repository, RepositoryFile, Symbol, ...)
        â”‚     â”œâ”€â”€ ai (AIModel, AISession, AIMessage, ...)
        â”‚     â”œâ”€â”€ agent (Agent, AgentTask, AgentMessage, ...)
        â”‚     â”œâ”€â”€ engineering (EngineeringPlan, EngineeringTask, ...)
        â”‚     â””â”€â”€ studio (StudioWorkspace, StudioProject, ...)
        â”œâ”€â”€ Run Base.metadata.create_all  {CREATE TABLE IF NOT EXISTS}
        â””â”€â”€ Session factory ready         {async_sessionmaker bound}

T+7s  [Auth Bootstrap]                  {SEED_ADMIN}
        â”‚
        â”œâ”€â”€ Check if admin user exists   {SELECT FROM users}
        â”œâ”€â”€ Create default admin         {admin / admin123 (bcrypt hashed)}
        â”œâ”€â”€ Assign admin role            {role = "admin"}
        â””â”€â”€ Log: "Default admin user seeded"

T+8s  [Offline Worker Checker]          {STARTING}
        â”‚
        â”œâ”€â”€ asyncio.create_task(check_offline_workers)
        â”œâ”€â”€ Loop every 10 seconds
        â”‚     â”œâ”€â”€ SELECT workers WHERE last_seen < now - 15s
        â”‚     â”œâ”€â”€ UPDATE status = 'offline'
        â”‚     â””â”€â”€ Broadcast worker update via WebSocket
        â””â”€â”€ Log: "Offline worker checker started"

T+9s  [WebSocket Manager]               {READY}
        â”‚
        â”œâ”€â”€ FastAPI accepts /ws connections
        â”œâ”€â”€ ws_manager.active_connections = []
        â”œâ”€â”€ broadcast functions ready
        â””â”€â”€ Log: "WebSocket endpoint ready"

T+10s [Scheduler Starts]                {STARTING}
        â”‚
        â”œâ”€â”€ SchedulerService.__init__
        â”‚     â”œâ”€â”€ db: AsyncSession reference
        â”‚     â””â”€â”€ self._running = False
        â”œâ”€â”€ scheduler.start()
        â”‚     â”œâ”€â”€ self._running = True
        â”‚     â””â”€â”€ asyncio.create_task(_scheduler_loop)
        â”œâ”€â”€ _scheduler_loop:
        â”‚     â””â”€â”€ while _running:
        â”‚           â”œâ”€â”€ _process_queue()
        â”‚           â”‚     â”œâ”€â”€ SELECT * FROM jobs WHERE status='queued'
        â”‚           â”‚     â”‚     ORDER BY priority DESC, created_at ASC
        â”‚           â”‚     â”œâ”€â”€ For each job: _find_available_worker(job)
        â”‚           â”‚     â”‚     â”œâ”€â”€ SELECT * FROM workers
        â”‚           â”‚     â”‚     â”‚     WHERE status='online' AND is_paused=0
        â”‚           â”‚     â”‚     â”‚     ORDER BY cpu_percent ASC LIMIT 1
        â”‚           â”‚     â”‚     â””â”€â”€ If worker found: _assign_job(job, worker)
        â”‚           â”‚     â”‚           â”œâ”€â”€ job.status = 'running'
        â”‚           â”‚     â”‚           â”œâ”€â”€ job.assigned_worker = worker.id
        â”‚           â”‚     â”‚           â”œâ”€â”€ job.started_at = now
        â”‚           â”‚     â”‚           â”œâ”€â”€ worker.status = 'busy'
        â”‚           â”‚     â”‚           â”œâ”€â”€ worker.current_job = job.id
        â”‚           â”‚     â”‚           â””â”€â”€ Broadcast job update via WebSocket
        â”‚           â”‚     â””â”€â”€ If no worker: skip (job stays queued)
        â”‚           â””â”€â”€ await asyncio.sleep(2)
        â””â”€â”€ Log: "Scheduler started"

T+11s [Workflow Engine]                 {STARTING}
        â”‚
        â”œâ”€â”€ WorkflowPlanner ready
        â”‚     â”œâ”€â”€ DAG generation from task list
        â”‚     â””â”€â”€ Dependency resolution (topological sort)
        â”œâ”€â”€ WorkflowDispatcher ready
        â”‚     â”œâ”€â”€ Task-to-worker assignment by capability
        â”‚     â””â”€â”€ Worker capability matching
        â”œâ”€â”€ WorkflowExecutor ready
        â”‚     â”œâ”€â”€ State machine: PENDING â†’ RUNNING â†’ COMPLETED/FAILED
        â”‚     â”œâ”€â”€ Parallel task execution within DAG constraints
        â”‚     â””â”€â”€ Error handling with retry
        â”œâ”€â”€ ArtifactManager ready
        â”‚     â”œâ”€â”€ SHA256-checksummed artifact storage
        â”‚     â”œâ”€â”€ Path: data/artifacts/{workflow_id}/{task_id}/
        â”‚     â””â”€â”€ Metadata stored in `artifacts` table
        â”œâ”€â”€ CacheService ready
        â”‚     â”œâ”€â”€ TTL-based result caching
        â”‚     â””â”€â”€ Cache key = (task_type, input_hash)
        â””â”€â”€ Log: "Workflow engine initialized"

T+12s [AI Runtime]                      {STARTING}
        â”‚
        â”œâ”€â”€ ModelRegistry loaded
        â”‚     â”œâ”€â”€ Scan configured providers (llama.cpp, Ollama, custom)
        â”‚     â”œâ”€â”€ Validate model availability
        â”‚     â””â”€â”€ Register each model with capabilities
        â”œâ”€â”€ PromptTemplateEngine ready
        â”‚     â”œâ”€â”€ Load templates from backend/app/ai/prompt/
        â”‚     â””â”€â”€ Template rendering with Jinja2-like syntax
        â”œâ”€â”€ SessionManager ready
        â”‚     â”œâ”€â”€ Conversation session tracking
        â”‚     â”œâ”€â”€ Context window management
        â”‚     â””â”€â”€ History persistence to AISession/AIMessage tables
        â”œâ”€â”€ ToolRegistry ready
        â”‚     â”œâ”€â”€ Registered tools: code_analysis, file_read, search, git
        â”‚     â””â”€â”€ Each tool: name, description, input_schema, handler
        â”œâ”€â”€ Router ready
        â”‚     â”œâ”€â”€ Model selection based on task complexity
        â”‚     â””â”€â”€ Load balancing across available model instances
        â””â”€â”€ Log: "AI Runtime initialized"

T+13s [Plugin Loader]                   {STARTING}
        â”‚
        â”œâ”€â”€ Scan plugins/ directory
        â”‚     â”œâ”€â”€ For each subdirectory:
        â”‚     â”‚     â”œâ”€â”€ Read plugin.json
        â”‚     â”‚     â”œâ”€â”€ Validate: plugin_id, version, permissions, entry_point
        â”‚     â”‚     â”œâ”€â”€ Check min_platform_version compatibility
        â”‚     â”‚     â”œâ”€â”€ Verify requested permissions against whitelist
        â”‚     â”‚     â””â”€â”€ Import entry_point module
        â”‚     â””â”€â”€ Example: plugins/example-metrics-reporter/
        â”‚           â”œâ”€â”€ plugin_id: "example-metrics-reporter"
        â”‚           â”œâ”€â”€ hooks: ["on_workflow_finish"]
        â”‚           â””â”€â”€ permissions: ["read_metrics"]
        â”œâ”€â”€ Register plugin hooks
        â”‚     â”œâ”€â”€ on_workflow_finish â†’ metrics_reporter.handle()
        â”‚     â””â”€â”€ Hook registry: dict[str, list[callable]]
        â”œâ”€â”€ Sandbox initialization
        â”‚     â”œâ”€â”€ Restricted API surface
        â”‚     â””â”€â”€ Permission enforcement on plugin calls
        â””â”€â”€ Log: "Loaded N plugins"

T+14s [HTTP Server Bind]                {LISTENING}
        â”‚
        â”œâ”€â”€ uvicorn.bind(host="0.0.0.0", port=8000)
        â”œâ”€â”€ Start accepting HTTP connections
        â”œâ”€â”€ Start accepting WebSocket upgrades at /ws
        â”œâ”€â”€ OpenAPI docs at /docs (Swagger), /redoc (ReDoc)
        â”œâ”€â”€ Static file serving for frontend build
        â””â”€â”€ Log: "Uvicorn running on http://0.0.0.0:8000"

T+15s [Dashboard Loads]                 {CONNECTING}
        â”‚
        â”œâ”€â”€ User opens http://localhost:3000
        â”‚     (or localhost:8000 if static build served by FastAPI)
        â”œâ”€â”€ Next.js 15 App Router initializes
        â”œâ”€â”€ Dark glassmorphism theme renders
        â”œâ”€â”€ Zustand auth store checks for persisted JWT
        â”‚     â”œâ”€â”€ If JWT exists: validate with GET /api/v1/health
        â”‚     â””â”€â”€ If invalid/missing: redirect to /login
        â””â”€â”€ Loading skeletons appear on dashboard cards

T+16s [Studio Loads]                    {CONNECTING}
        â”‚
        â”œâ”€â”€ AIClusterStudio.exe (Tauri app) launches
        â”œâ”€â”€ Tauri window: 1280x800, frameless/chrome per config
        â”œâ”€â”€ Rust backend binds to port 3001
        â”œâ”€â”€ Load workspace list from GET /api/v1/studio/workspaces
        â”œâ”€â”€ Load project list from GET /api/v1/studio/projects
        â”œâ”€â”€ Layout engine restores saved layout
        â”‚     â”œâ”€â”€ Grid/panel positions from StudioLayout table
        â”‚     â””â”€â”€ Bookmark restoration
        â””â”€â”€ Editor panels initialize

T+17s [User Login]                      {AUTHENTICATING}
        â”‚
        â”œâ”€â”€ User submits credentials (username + password)
        â”œâ”€â”€ POST /api/v1/auth/login
        â”‚     â”œâ”€â”€ Validate input via LoginRequest schema
        â”‚     â”œâ”€â”€ SELECT * FROM users WHERE username = ?
        â”‚     â”œâ”€â”€ bcrypt.verify(password, hashed_password)
        â”‚     â””â”€â”€ Generate JWT (python-jose)
        â”‚           â”œâ”€â”€ Payload: {sub: user.id, role: user.role, exp: now+60min}
        â”‚           â””â”€â”€ Sign with SECRET_KEY (HS256)
        â”œâ”€â”€ Frontend receives JWT
        â”‚     â”œâ”€â”€ Store in Zustand auth store
        â”‚     â”œâ”€â”€ Persist to localStorage
        â”‚     â””â”€â”€ Set Authorization: Bearer <token> header
        â”œâ”€â”€ Redirect to / (dashboard)
        â”œâ”€â”€ Establish WebSocket connection to /ws
        â”‚     â”œâ”€â”€ ws_manager.connect(websocket)
        â”‚     â””â”€â”€ Receive initial cluster snapshot
        â””â”€â”€ Dashboard renders live data
              â”œâ”€â”€ Worker cards with status indicators
              â”œâ”€â”€ Job queue table
              â”œâ”€â”€ Cluster metrics (CPU, RAM, worker count)
              â””â”€â”€ Real-time updates via WebSocket

T+18s [System Ready]                    {OPERATIONAL}
        â”‚
        â”œâ”€â”€ All subsystems running
        â”œâ”€â”€ Dashboard shows live cluster state
        â”œâ”€â”€ WebSocket broadcasting updates every 2s
        â”œâ”€â”€ Scheduler processing jobs
        â”œâ”€â”€ Workers can register and receive jobs
        â”œâ”€â”€ AI Runtime ready for inference
        â”œâ”€â”€ Workflow Engine ready for orchestration
        â”œâ”€â”€ Plugins active and listening for hooks
        â”œâ”€â”€ Studio connected and ready
        â””â”€â”€ â”€â”€â”€â”€ SYSTEM READY â”€â”€â”€â”€
```

---

## 3. Detailed Component Startup

### 3.1 Installer (T+0s â€“ T+5s)

The installer is produced by `build/setup_builder.py` using Inno Setup 6. It bundles:
- `python-3.12.7-amd64.exe` â€” embedded Python installer
- `vc_redist.x64.exe` â€” Visual C++ redistributable
- Prebuilt executables (PyInstaller + Tauri): master, worker, studio, master-control-center, worker-control-center, CLI
- Default configuration files from `config/`
- Assets (icons, manifest, branding)

The installer writes to `C:\Program Files\AICluster\` with subdirectories:

```
C:\Program Files\AICluster\
â”œâ”€â”€ master\              AIClusterRuntime.exe --mode master + Python runtime
â”œâ”€â”€ worker\              AIClusterRuntime.exe --mode worker + Python runtime
â”œâ”€â”€ studio\              AIClusterStudio.exe (Tauri)
â”œâ”€â”€ master-control\      MasterControlCenter.exe (Tauri)
â”œâ”€â”€ worker-control\      WorkerControlCenter.exe (Tauri)
â”œâ”€â”€ cli\                 aicluster.exe (CLI tool)
â”œâ”€â”€ config\              Default YAML config files
â””â”€â”€ data\                SQLite database, logs, artifacts
```

**Failure modes:**
- Python download fails â†’ installer aborts with network error
- VC++ redist installation fails â†’ log warning, continue (system may already have it)
- Disk space insufficient â†’ Inno Setup reports before extraction
- Antivirus blocks binary â†’ installer exits with code 2

### 3.2 Master Starts (T+5s)

`AIClusterRuntime.exe --mode master` bootstraps with:

```python
# backend/app/main.py â€” FastAPI lifespan
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

This creates all 30+ tables in a single transaction. The database is stored at `data/aicluster.db` (SQLite via aiosqlite). No migrations are run â€” Alembic is installed but not configured; schema changes in v1.x are additive only.

**Failure modes:**
- Database file is locked â†’ retry with exponential backoff
- Disk full â†’ SQLite raises `sqlite3.OperationalError: database or disk is full`
- Schema conflict â†’ `create_all` with `IF NOT EXISTS` semantics, no-op on existing

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
1. **Queue processing** â€” Every 2 seconds, scan for `status='queued'` jobs ordered by priority (descending) and creation time (ascending).
2. **Worker assignment** â€” For each queued job, find the least-loaded online worker (lowest CPU percentage), or use the job's `assigned_worker` if pre-assigned.
3. **Job dispatch** â€” Update job status to `running`, set `started_at`, mark worker as `busy`, broadcast via WebSocket.

**Worker selection algorithm:**
```
1. If job has assigned_worker:
     â†’ Use that worker if online and not paused
2. If no assigned_worker:
     â†’ SELECT * FROM workers 
       WHERE status = 'online' AND is_paused = false 
       ORDER BY cpu_percent ASC 
       LIMIT 1
```

This ensures workloads are spread evenly across the cluster.

### 3.5 Workflow Engine (T+11s)

The workflow engine (`backend/app/workflow/`) processes complex multi-step tasks as directed acyclic graphs:

```
Subsystem               Path                          Purpose
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚ PENDING  â”‚
                    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
                         â”‚
                    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”
                    â”‚ QUEUED   â”‚
                    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
                         â”‚ (dependencies met)
                    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”
                    â”‚ RUNNING  â”‚
                    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
                    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”
                    â”‚         â”‚
               â”Œâ”€â”€â”€â”€â–¼â”€â”€â” â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”
               â”‚COMPLETEâ”‚ â”‚ FAILED â”‚
               â”‚  D     â”‚ â”‚        â”‚
               â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
                              â”‚ (retry allowed)
                         â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”
                         â”‚  QUEUED  â”‚ (max 3 retries)
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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
- Hook invocations are wrapped in try/except â€” a plugin exception does not crash the master.
- Permission checks are enforced at hook dispatch time.
- Plugins cannot import arbitrary modules; only the allowed API surface is exposed.

### 3.8 Workers Connect (T+15s onward)

Worker startup is documented in full in `WORKER_ARCHITECTURE.md`. At a high level:

```
1. Worker process starts â†’ state = STARTING
2. Load config from config.json â†’ state = LOADING_CONFIG
3. Connect to master HTTP API â†’ state = CONNECTING
4. POST /api/v1/workers/register â†’ state = REGISTERING
5. Receive worker_id â†’ state = ONLINE
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
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚  Installer   â”‚
                    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚  SQLite DB   â”‚
                    â”‚  (data dir)  â”‚
                    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚            â”‚            â”‚
        â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”
        â”‚ Auth       â”‚ â”‚ Worker â”‚ â”‚ Scheduler â”‚
        â”‚ Service    â”‚ â”‚ Managerâ”‚ â”‚ Service   â”‚
        â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”¬â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
              â”‚            â”‚            â”‚
        â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”
        â”‚ WebSocket â”‚ â”‚ Master â”‚ â”‚ Job Queue â”‚
        â”‚ Manager   â”‚ â”‚ API    â”‚ â”‚           â”‚
        â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”¬â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚            â”‚
        â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚ Dashboard â”‚ â”‚ Workflow Engine  â”‚
        â”‚ (Frontend)â”‚ â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚ â”‚ Planner      â”‚ â”‚
                      â”‚ â”‚ Dispatcher   â”‚ â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”¤ â”‚ Executor     â”‚ â”‚
              â”‚       â”‚ â”‚ Artifacts    â”‚ â”‚
        â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â” â”‚ â”‚ Cache        â”‚ â”‚
        â”‚ AI Runtimeâ”‚ â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
        â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â” â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚ â”‚Models â”‚ â”‚
        â”‚ â”‚Router â”‚ â”‚
        â”‚ â”‚Tools  â”‚ â”‚
        â”‚ â”‚Memory â”‚ â”‚
        â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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
| Master cold start | <3s | From `AIClusterRuntime.exe --mode master` to `Uvicorn running` |
| Database init | <500ms | Table creation on empty DB |
| Scheduler ready | <100ms | From `start()` to first queue poll |
| AI Runtime init | <2s | Model registry + provider validation |
| Plugin loading | <200ms per plugin | Import + hook registration |
| First dashboard paint | <1.5s | From URL enter to interactive |
| WebSocket connection | <500ms | From client connect to first broadcast |
| Studio launch | <3s | From EXE launch to UI render |
| System Ready | <20s total | From installer Finish to full operation |

---

*End of STARTUP_SEQUENCE.md â€” This document covers the complete boot timeline from installer to system-ready for the AICluster distributed compute platform.*
