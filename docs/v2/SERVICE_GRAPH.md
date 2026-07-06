# Service Dependency Graph

**AICluster v2.0 â€” Native Desktop Edition | Phase 3**
**Date:** 2026-07-05
**Status:** Analysis Only â€” No Implementation

---

## 1. Complete Service Map

### 1.1 Services Within AIClusterRuntime.exe --mode master

```
AIClusterRuntime.exe --mode master
â”œâ”€â”€ FastAPI Application
â”‚   â”œâ”€â”€ REST API (131 endpoints)
â”‚   â”‚   â”œâ”€â”€ /api/v1/auth        [AuthService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/workers     [WorkerManagerService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/jobs        [SchedulerService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/dashboard   [WorkerManagerService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/health      [HealthService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/logs        [LogService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/workflows   [WorkflowEngine]
â”‚   â”‚   â”œâ”€â”€ /api/v1/repositories [RepositoryIndexer, SearchService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/ai          [SessionManager, ModelRouter]
â”‚   â”‚   â”œâ”€â”€ /api/v1/agents      [Orchestrator, AgentRegistry]
â”‚   â”‚   â”œâ”€â”€ /api/v1/engineering [EngineeringPlanner, GoalAnalyzer]
â”‚   â”‚   â”œâ”€â”€ /api/v1/plugins     [PluginRegistry]
â”‚   â”‚   â”œâ”€â”€ /api/v1/production  [HealthService, DiagnosticsService]
â”‚   â”‚   â”œâ”€â”€ /api/v1/studio      [Studio service endpoints]
â”‚   â”‚   â””â”€â”€ /api/v1/audit       [AuditService]
â”‚   â”‚
â”‚   â”œâ”€â”€ WebSocket (/ws)         [ws_manager]
â”‚   â”‚
â”‚   â”œâ”€â”€ Middleware
â”‚   â”‚   â”œâ”€â”€ CORSMiddleware
â”‚   â”‚   â”œâ”€â”€ AuthMiddleware (get_current_user)
â”‚   â”‚   â”œâ”€â”€ SlowAPIMiddleware (rate limiting)
â”‚   â”‚   â””â”€â”€ AuditMiddleware (HTTP request capture)
â”‚   â”‚
â”‚   â””â”€â”€ Background Tasks
â”‚       â”œâ”€â”€ offline_checker_task  (10s loop)
â”‚       â””â”€â”€ scheduler_loop        (2s loop, inside SchedulerService)
â”‚
â”œâ”€â”€ Database
â”‚   â””â”€â”€ SQLite (aiosqlite)
â”‚       â”œâ”€â”€ workers, jobs, system_logs, users
â”‚       â”œâ”€â”€ workflows, workflow_tasks, task_dependencies, artifacts
â”‚       â”œâ”€â”€ repositories, repository_files, symbols, dependencies
â”‚       â”œâ”€â”€ ai_models, ai_sessions, ai_messages, prompts, tools
â”‚       â”œâ”€â”€ agents, agent_tasks, agent_messages, reviews, merges
â”‚       â”œâ”€â”€ engineering_plans, patches, validations, repairs
â”‚       â”œâ”€â”€ studio_workspaces, projects, layouts
â”‚       â””â”€â”€ audit_logs, audit_settings, audit_exports, audit_retention
â”‚
â””â”€â”€ Engines
    â”œâ”€â”€ WorkflowEngine
    â”‚   â”œâ”€â”€ WorkflowPlanner (DAG generation)
    â”‚   â”œâ”€â”€ TaskDispatcher (worker assignment)
    â”‚   â”œâ”€â”€ ArtifactStore (file storage)
    â”‚   â”œâ”€â”€ CacheService (result cache)
    â”‚   â””â”€â”€ MetricsService (execution metrics)
    â”‚
    â”œâ”€â”€ RepositoryEngine
    â”‚   â”œâ”€â”€ FileScanner (directory walk)
    â”‚   â”œâ”€â”€ SymbolParser (AST extraction)
    â”‚   â”œâ”€â”€ RepositoryIndexer (DB population)
    â”‚   â”œâ”€â”€ SearchService (symbol/file/text/reference search)
    â”‚   â””â”€â”€ CodeMetricsService (complexity, maintainability)
    â”‚
    â”œâ”€â”€ AIRuntime
    â”‚   â”œâ”€â”€ SessionManager (chat sessions)
    â”‚   â”œâ”€â”€ ConversationManager (message history)
    â”‚   â”œâ”€â”€ ModelRegistry (provider registration)
    â”‚   â”œâ”€â”€ ModelRouter (task-based routing)
    â”‚   â”œâ”€â”€ PromptBuilder (prompt construction)
    â”‚   â”œâ”€â”€ ContextBuilder (repo-aware context)
    â”‚   â”œâ”€â”€ ContextOptimizer (compression, sliding window)
    â”‚   â”œâ”€â”€ ToolRegistry (tool execution)
    â”‚   â””â”€â”€ Providers: Ollama, LlamaCpp, OpenAICompat
    â”‚
    â”œâ”€â”€ MultiAgentEngine
    â”‚   â”œâ”€â”€ AgentRegistry (12 default agents)
    â”‚   â”œâ”€â”€ PlanningService (task decomposition)
    â”‚   â”œâ”€â”€ Orchestrator (workflow execution)
    â”‚   â”œâ”€â”€ CommunicationService (agent messaging)
    â”‚   â”œâ”€â”€ ReviewService (quality checks)
    â”‚   â””â”€â”€ MergeService (output combining)
    â”‚
    â”œâ”€â”€ EngineeringEngine
    â”‚   â”œâ”€â”€ GoalAnalyzer (intent + risk)
    â”‚   â”œâ”€â”€ EngineeringPlanner (implementation plans)
    â”‚   â”œâ”€â”€ ValidationService (7 checks)
    â”‚   â”œâ”€â”€ RepairService (3-iteration fix loop)
    â”‚   â”œâ”€â”€ QualityGatesService (9 gates)
    â”‚   â”œâ”€â”€ RiskEngine (risk classification)
    â”‚   â””â”€â”€ DocumentationService (auto-docs)
    â”‚
    â”œâ”€â”€ PluginSystem
    â”‚   â”œâ”€â”€ PluginRegistry (lifecycle management)
    â”‚   â”œâ”€â”€ PluginLoader (dynamic loading)
    â”‚   â”œâ”€â”€ ManifestService (validation)
    â”‚   â””â”€â”€ HookRegistry (15 platform hooks)
    â”‚
    â”œâ”€â”€ AuditSystem
    â”‚   â”œâ”€â”€ EventBus (pub/sub)
    â”‚   â”œâ”€â”€ AuditService (log/search/export/purge)
    â”‚   â””â”€â”€ AuditMiddleware (auto-capture)
    â”‚
    â””â”€â”€ ProductionServices
        â”œâ”€â”€ HealthService (subsystem health checks)
        â”œâ”€â”€ MonitoringService (psutil metrics)
        â””â”€â”€ DiagnosticsService (system checks)
```

### 1.2 Services Within AIClusterRuntime.exe --mode worker

```
AIClusterRuntime.exe --mode worker
â”œâ”€â”€ FastAPI Application
â”‚   â””â”€â”€ Health endpoint (port 8001)
â”‚
â”œâ”€â”€ Worker Lifecycle (21-state machine)
â”‚   â”œâ”€â”€ STATE: STARTING
â”‚   â”œâ”€â”€ STATE: LOADING_CONFIG
â”‚   â”œâ”€â”€ STATE: CONNECTING       [HTTP client to master]
â”‚   â”œâ”€â”€ STATE: REGISTERING      [RegistrarService]
â”‚   â”œâ”€â”€ STATE: ONLINE
â”‚   â”œâ”€â”€ STATE: HEARTBEAT        [HeartbeatService - 5s interval]
â”‚   â”œâ”€â”€ STATE: POLL_JOB         [PollerService - 5s interval]
â”‚   â”œâ”€â”€ STATE: EXECUTING        [JobExecutor - 5 handlers]
â”‚   â”œâ”€â”€ STATE: REPORT_PROGRESS  [ReporterService]
â”‚   â”œâ”€â”€ STATE: REPORT_RESULT
â”‚   â””â”€â”€ STATE: SHUTDOWN
â”‚
â”œâ”€â”€ Services
â”‚   â”œâ”€â”€ RegistrarService (registration with retry)
â”‚   â”œâ”€â”€ HeartbeatService (psutil metrics)
â”‚   â”œâ”€â”€ PollerService (job polling)
â”‚   â”œâ”€â”€ ReporterService (progress + results)
â”‚   â””â”€â”€ MonitorService (resource monitoring)
â”‚
â”œâ”€â”€ Job Handlers
â”‚   â”œâ”€â”€ EchoHandler
â”‚   â”œâ”€â”€ SleepHandler
â”‚   â”œâ”€â”€ DirScanHandler
â”‚   â”œâ”€â”€ HashFileHandler
â”‚   â””â”€â”€ CountFilesHandler
â”‚
â””â”€â”€ Utilities
    â”œâ”€â”€ HttpClient (httpx to master)
    â””â”€â”€ RetryHandler (exponential backoff)
```

### 1.3 Services Within AICluster Studio.exe

```
AICluster Studio.exe (Tauri v2)
â”œâ”€â”€ Rust Shell
â”‚   â”œâ”€â”€ WebView (React app)
â”‚   â”œâ”€â”€ Tauri Commands (IPC bridge)
â”‚   â””â”€â”€ System Tray (planned)
â”‚
â”œâ”€â”€ React Frontend
â”‚   â”œâ”€â”€ Dashboard (cluster metrics)
â”‚   â”œâ”€â”€ AI Chat (conversation UI)
â”‚   â”œâ”€â”€ Repository Browser
â”‚   â”œâ”€â”€ Workflow Designer
â”‚   â”œâ”€â”€ Agent Designer
â”‚   â”œâ”€â”€ Plugin Manager
â”‚   â”œâ”€â”€ Settings
â”‚   â””â”€â”€ First Run Wizard (planned)
â”‚
â””â”€â”€ Planned for v2.0
    â”œâ”€â”€ Launcher Service (process management)
    â”œâ”€â”€ Role Manager (Master/Worker/Standalone)
    â”œâ”€â”€ Service Watcher (health monitoring + restart)
    â””â”€â”€ Update Service (self-update)
```

---

## 2. Startup Order

### 2.1 Cold Start (First Run)

```
Step  Time    Action                          Service
â”€â”€â”€â”€  â”€â”€â”€â”€    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
 1    0.0s   User launches Studio             AICluster Studio.exe
 2    0.5s   Studio detects no config         Launcher â†’ FirstRunWizard
 3    5.0s   User completes wizard            Role selection saved
 4    5.5s   Studio starts Master             Process: runtime\AIClusterRuntime.exe --mode master
 5    5.5s   â””â”€ Master loads                  Python runtime init (~3s)
 6    8.5s   â””â”€ Master initializes DB         init_db() (~1s)
 7    9.5s   â””â”€ Master seeds admin user       AuthService.seed_default_admin()
 8   10.0s   â””â”€ Master starts services        Lifespan startup
 9   10.0s   â””â”€ Master starts offline checker offline_checker_task
10   10.0s   â””â”€ Master starts scheduler loop  SchedulerService.start()
11   10.5s   Master health check passes       Studio polls GET /health
12   11.0s   Studio opens dashboard           WebView â†’ http://localhost:3000

Total: ~11 seconds to usable dashboard
```

### 2.2 Warm Start (Subsequent Runs)

```
Step  Time    Action                          Service
â”€â”€â”€â”€  â”€â”€â”€â”€    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
 1    0.0s   User launches Studio             AICluster Studio.exe
 2    0.3s   Studio detects config exists     Launcher reads role.json
 3    0.5s   Studio checks port 8000           GET /health
 4a   0.5s   [If master already running]      â†’ Dashboard opens (0.5s total)
 4b   0.5s   [If master not running]          â†’ Launch master
 5b   3.0s   â””â”€ Master starts (warm DB)       ~3s (DB cache warm)
 6b   4.0s   â””â”€ Health check passes           â†’ Dashboard opens

Total (master running):   ~0.5 seconds
Total (cold master):      ~4.0 seconds
```

### 2.3 Full Cluster Start (Standalone Mode)

```
Order  Service               Dependency          Wait For
â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  1    AICluster Studio      None                User launches
  2    AIClusterRuntime.exe --mode master   None                Port 8000 free
  3    Health check          Master ready         GET /health (200)
  4    AIClusterRuntime.exe --mode worker   Master healthy       POST /register (200)
  5    Web Dashboard         Master healthy       WebView loads
```

---

## 3. Shutdown Order

### 3.1 Graceful Shutdown

```
Order  Service               Action                       Timeout
â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€
  1    Scheduler loop        SchedulerService.stop()      2s
  2    AIClusterRuntime.exe --mode worker   SIGTERM â†’ graceful stop      10s
  3    â””â”€ Force kill         If not stopped               1s
  4    AIClusterRuntime.exe --mode master   SIGTERM â†’ lifespan shutdown  10s
  5    â””â”€ offline_checker    Task cancelled + awaited     1s
  6    â””â”€ DB close           SQLite connection close      2s
  7    â””â”€ Force kill         If not stopped               1s
  8    AICluster Studio      Exit                         0s
```

### 3.2 Crash Recovery

```
Scenario                    Detection              Recovery Action
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Master process crashes      Studio watchdog        Auto-restart (max 3 attempts)
Worker process crashes      Studio watchdog        Auto-restart (no limit)
Master hangs (no health)    Studio health poll     SIGTERM â†’ restart
Worker hangs                Master marks offline   Studio restart worker
Studio crash                User re-launches       Check for orphaned services
System shutdown             Windows sends WM_QUERYENDSESSION  Graceful stop
```

---

## 4. Health Dependencies

### 4.1 Health Check Matrix

| Service | Health Endpoint | Depends On | Failure Consequence |
|---------|----------------|------------|---------------------|
| Master | `GET /health` | SQLite connection | Studio cannot open dashboard |
| Master | `GET /api/v1/health/detailed` | All engine services | Degraded mode (some engines down) |
| Worker | FastAPI running + master reachable | Master at :8000 | Worker marked offline by master |
| Studio | Tauri WebView + master reachable | Master at :8000 | "Cannot connect" error screen |
| Database | SQLite file accessible | Filesystem | Master fails to start |

### 4.2 Health Check Intervals

| Check | Interval | Source | Action on Failure |
|-------|----------|--------|-------------------|
| Studio â†’ Master | 2s (polling) + WebSocket push | React Query | Reconnect dialog |
| Studio â†’ Master process | 5s (process alive check) | Rust watchdog | Auto-restart |
| Master â†’ Worker | 15s (3 missed heartbeats) | offline_checker_task | Mark offline |
| Worker â†’ Master | 5s (heartbeat) + 5s (job poll) | Worker services | Retry with backoff |
| Master â†’ Database | On every query | SQLAlchemy | HTTP 500 error |

---

## 5. Internal Service Communication

### 5.1 IPC Mechanisms

| From | To | Mechanism | Protocol | Authentication |
|------|----|-----------|----------|----------------|
| Studio | Master | HTTP REST | JSON over TCP | JWT token |
| Studio | Master | WebSocket | JSON over TCP | JWT token (query param) |
| Studio | Worker | HTTP REST (health only) | JSON over TCP | None (local) |
| Master | Worker | HTTP REST | JSON over TCP | Worker secret |
| Worker | Master | HTTP REST | JSON over TCP | Worker secret |
| Master | Database | SQLite | SQL via aiosqlite | File permissions |
| Studio (Rust) | Studio (React) | Tauri IPC | JSON via webview | WebView trust boundary |

### 5.2 Port Allocation

| Service | Port | Configurable | Protocol | Scope |
|---------|------|--------------|----------|-------|
| Master REST API | 8000 | `AICLUSTER_API_PORT` | HTTP | LAN (default localhost) |
| Master WebSocket | 8000 | (same port) | WS | LAN (default localhost) |
| Worker | 8001 | Config | HTTP | LAN (default localhost) |
| Studio Dashboard | 3000 | (hardcoded in Studio) | HTTP | Localhost only |
| MCC Backend | 8800 | â€” | HTTP | Localhost only (legacy) |

---

## 6. Recovery Dependencies

### 6.1 Service Recovery Chain

```
Master crash:
  Studio detects (health check fails)
    â†’ Studio kills any orphaned worker processes
    â†’ Studio restarts master
    â†’ Studio waits for health check (up to 30s)
    â†’ Studio reconnects dashboard
    â†’ Workers reconnect to master automatically
    â†’ Jobs in-flight are marked for retry by scheduler

Worker crash:
  Studio detects (process exit event)
    â†’ [Worker role: Studio restarts worker]
    â†’ [Master role: worker re-registers if running]
    â†’ [Standalone: Studio restarts worker]
  Master detects (heartbeat timeout)
    â†’ Master marks worker offline
    â†’ Jobs assigned to that worker are requeued

Database corruption:
  Master detects (SQLite integrity error on startup)
    â†’ Master fails health check
    â†’ Studio shows "Database error" dialog
    â†’ User can restore from backup or reset

Studio crash:
  User re-launches Studio
    â†’ Studio detects orphaned master/worker processes
    â†’ Studio adopts existing processes
    â†’ Studio checks health and reconnects
    â†’ If orphaned processes unhealthy: restart them
```

---

## 7. Summary for v2.0 Launcher Design

| Finding | Implication |
|---------|-------------|
| Master must start before anything else | Launcher must check port 8000 before opening dashboard |
| Worker depends on Master | In Standalone mode, start Master first, wait, then Worker |
| Studio depends on Master for all data | Without Master, Studio shows "offline" state |
| No circular dependencies | Startup is strictly linear: Studio â†’ Master â†’ Worker |
| All services can be killed/restarted independently | Clean separation enables robust recovery |
| Shutdown order is the reverse of startup | Worker first, Master last, Studio exits last |
| Health check is simple (HTTP GET) | Launcher can use basic HTTP polling |
