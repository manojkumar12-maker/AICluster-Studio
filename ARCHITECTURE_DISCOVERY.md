# AICluster Architecture Discovery

## System Architecture Overview

AICluster is a distributed AI cluster management platform with a **Master-Worker** topology, multiple desktop applications, and a comprehensive build system.

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Web Dashboard│  │Master Control│  │Worker Control│          │
│  │ (Next.js 15) │  │Center (Tauri)│  │Center (Tauri)│          │
│  │ :3000        │  │ :8800        │  │ :8900        │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         └─────────────────┼──────────────────┘                  │
│                           │ HTTP/REST + WebSocket               │
├───────────────────────────┼─────────────────────────────────────┤
│                    MASTER SERVER LAYER                           │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  FastAPI ASGI (uvicorn) :8000                           │     │
│  │  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │     │
│  │  │REST API   │ │WebSocket │ │Scheduler │ │Audit    │  │     │
│  │  │(19 routes)│ │Manager   │ │(bg loop) │ │Middleware│  │     │
│  │  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └─────────┘  │     │
│  │        │             │            │                     │     │
│  │  ┌─────┴─────────────┴────────────┴────────────────┐   │     │
│  │  │  AI Runtime  │  Agents  │  Workflow  │  Plugin  │   │     │
│  │  │  (providers, │  (multi- │  (DAG      │  (SDK,   │   │     │
│  │  │   routing,   │   agent) │   engine)  │   hooks) │   │     │
│  │  │   sessions)  │          │            │          │   │     │
│  │  └──────────────┴──────────┴────────────┴──────────┘   │     │
│  │  ┌────────────────────────────────────────────────┐     │     │
│  │  │  Repository Intelligence │ Engineering Engine  │     │     │
│  │  └────────────────────────────────────────────────┘     │     │
│  │  ┌────────────────────────────────────────────────┐     │     │
│  │  │  SQLAlchemy Async + SQLite (aiosqlite)         │     │     │
│  │  └────────────────────────────────────────────────┘     │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │ HTTP/REST                           │
├───────────────────────────┼─────────────────────────────────────┤
│                    WORKER FLEET LAYER                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Worker Agent x N (FastAPI) :8001+                      │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │Registrar │ │Heartbeat │ │Job Poller│ │Reporter  │  │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │     │
│  │  ┌────────────────────────────────────────────────┐    │     │
│  │  │  Job Executor (Handler Registry)                │    │     │
│  │  │  echo │ sleep │ dir_scan │ hash_file │ count   │    │     │
│  │  └────────────────────────────────────────────────┘    │     │
│  │  ┌────────────────────────────────────────────────┐    │     │
│  │  │  SystemMonitor (psutil: CPU/RAM/disk/network)  │    │     │
│  │  └────────────────────────────────────────────────┘    │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Master Subsystem

**Role**: Central coordinator and API gateway
**Tech**: Python 3.12+, FastAPI, SQLAlchemy 2.0 Async, SQLite, WebSockets
**Port**: 8000

### Components:
- **REST API** (19 route groups): Health, Auth, Workers, Jobs, Dashboard, Logs, Workflows, Repositories, AI, Agents, Engineering, Production, Plugins, Studio, Audit
- **WebSocket Manager**: Real-time broadcast to all connected clients
- **Scheduler**: Background job queue processor with round-robin worker assignment
- **Auth Service**: JWT-based (python-jose) with bcrypt password hashing
- **Audit Middleware**: Automatic HTTP request auditing (17 categories, 30+ event types)
- **AI Runtime**: Multi-provider (Ollama, llama.cpp, OpenAI-compatible), model routing, context optimization, prompt building, tool execution
- **Multi-Agent Engine**: 12 default agents, orchestrator, planner, reviewer, merger
- **Workflow Engine**: DAG-based task orchestration with parallel execution
- **Repository Intelligence**: Multi-language parser, incremental indexer, dependency graph, full-text search
- **Engineering Engine**: Goal analysis, automated planning, quality gates, self-repair
- **Plugin SDK**: Plugin manifest, loader, hook registry, sandboxed execution

### Dependencies:
- `backend/` depends on `shared/py/` and `shared/protocol/`
- `backend/app/main.py` imports all route modules, services, WebSocket manager

### Entry Points:
```python
# Primary: uvicorn app.main:app --port 8000
app = FastAPI(lifespan=lifespan)  # in main.py
# Lifespan: init_db() -> seed_admin() -> start offline checker -> serve -> shutdown
```

---

## 2. Worker Subsystem

**Role**: Distributed compute node
**Tech**: Python 3.12+, FastAPI, httpx, psutil
**Port**: 8001 (configurable)

### State Machine (21 states):
```
STARTING -> LOADING_CONFIG -> CONNECTING -> REGISTERING -> ONLINE
  -> HEARTBEAT -> POLL_JOB -> NO_JOB | HAS_JOB -> EXECUTING
  -> REPORT_PROGRESS -> REPORT_RESULT -> HEARTBEAT (loop)
  NETWORK_FAILURE -> RETRY -> REGISTERING (reconnect)
  SHUTDOWN -> STOPPING -> EXIT
```

### Components:
- **Registrar**: POST to master `/api/v1/workers/register`, get worker ID
- **HeartbeatService**: Periodic (5s) CPU/RAM/disk/network reporting
- **JobPoller**: Long-poll `/api/v1/workers/{id}/next-job`
- **Reporter**: Post progress/result back to master
- **SystemMonitor**: psutil-based resource collection
- **JobRegistry**: Maps job_type to handler (echo, sleep, dir_scan, hash_file, count_files)

### Communication Protocol:
```
Worker -> Master:
  POST /api/v1/workers/register   {name, hostname, ip}
  POST /api/v1/workers/heartbeat  {id, cpu, ram, disk, temperature, busy}
  GET  /api/v1/workers/{id}/next-job
  POST /api/v1/workers/{id}/progress  {job_id, progress, logs}
  POST /api/v1/workers/{id}/result    {job_id, status, result, error, duration_ms}
```

---

## 3. Studio Subsystem

**Role**: Desktop IDE for AI-assisted development
**Tech**: Tauri v2 (Rust + React + TypeScript + Vite)
**Status**: Early development (frontend is still starter template)

### Architecture:
- **Rust backend**: `src-tauri/src/lib.rs` — minimal Tauri builder (no custom commands)
- **React frontend**: Vite + React 19 + TypeScript 6 + Tailwind CSS 4
- **Dependencies installed but unused**: zustand, tanstack/react-query, react-resizable-panels, framer-motion
- **Bundle**: NSIS Windows installer, single window 1280x800

### Intended Features (from dependencies):
- Split-panel IDE layout (react-resizable-panels)
- Server state management (tanstack/react-query)
- Client state management (zustand)
- Animations (framer-motion)

---

## 4. Workflow Engine

**Role**: DAG-based task orchestration
**Tech**: Python (in `backend/app/workflow/`)

### Components:
- **WorkflowPlanner**: Validates DAG structure, checks for cycles
- **TaskDispatcher**: Assigns tasks to available workers considering capabilities
- **Executor**: Runs workflow tasks, handles retries (exponential backoff)
- **ArtifactStore**: Manages task output artifacts
- **CacheService**: Caches workflow results (keyed by task inputs)
- **MetricsService**: Tracks execution time, resource usage per task

### Data Model (9 tables):
- `workflows` — workflow metadata and status
- `workflow_tasks` — individual DAG steps with resource tracking
- `task_dependencies` — DAG edges
- `workflow_results` — final workflow output
- `artifacts` — file/data artifacts
- `execution_metrics` — per-task performance data
- `cache` — result caching
- `workflow_events` — event log
- `worker_capabilities` — per-worker capability declarations

---

## 5. Repository Intelligence

**Role**: Code scanning and analysis
**Tech**: Python (in `backend/app/repository/`)

### Components:
- **RepositoryIndexer**: Incremental file system indexer
- **Scanner**: Walks directories, detects file types by extension
- **Parser**: Multi-language symbol extraction (Python, JS/TS, Rust, Java, Go, C/C++, etc.)
- **SearchService**: Full-text search with regex support
- **CodeMetricsService**: Lines of code, complexity, comment ratio

### Data Model (11 tables):
- `repositories`, `repository_files`, `symbols`, `symbol_imports`, `symbol_references`
- `dependency_edges`, `code_metrics`, `knowledge_nodes`, `knowledge_edges`
- `repository_cache`, `repository_events`

---

## 6. AI Runtime

**Role**: Multi-provider LLM integration
**Tech**: Python (in `backend/app/ai/`)

### Components:
- **ModelRegistry**: Central provider registry (Ollama, llama.cpp, OpenAI-compatible)
- **ModelRouter**: Task-based routing (code_generation -> Ollama, summarization -> OpenAI, etc.)
- **SessionManager**: Chat session lifecycle with expiry
- **ConversationManager**: Message history management
- **ContextBuilder**: Repository context assembly for prompts
- **ContextOptimizer**: Token-aware context ranking and compression
- **PromptBuilder**: Structured prompt with system template + context + history
- **ToolRegistry**: Tool definition and execution
- **StreamingService**: Streaming response handling
- **MemoryService**: Session key-value memory
- **MetricsService**: Token usage, latency tracking

### Provider Support:
| Provider | File | Features |
|----------|------|----------|
| Ollama | `providers/ollama.py` | Chat, completion, streaming, embeddings |
| llama.cpp | `providers/llamacpp.py` | Chat, completion, streaming |
| OpenAI-compatible | `providers/openai.py` | Chat, completion, streaming |

---

## 7. Multi-Agent Engine

**Role**: Multi-agent AI collaboration
**Tech**: Python (in `backend/app/agents/`)

### Default Agents (12):
From `roles/definitions.py`: Architect, Developer, Reviewer, Tester, DevOps, Security, Documentation, Project Manager, Data Scientist, UX Designer, QA Engineer, Tech Writer

### Components:
- **AgentRegistry**: Maps agent names to classes
- **Orchestrator**: Runs agent pipeline with plan, execute, review, merge steps
- **Planner**: Generates execution plan from task description
- **CommunicationService**: Inter-agent messaging
- **ReviewService**: Quality review of agent outputs
- **MergeService**: Merge reviewed outputs into final result
- **MemoryService**: Per-agent persistent memory

### Data Model (7 tables):
- `agents`, `agent_tasks`, `agent_messages`, `agent_reviews`, `agent_merges`, `agent_memory_store`, `agent_metrics`

---

## 8. Engineering Engine

**Role**: AI-driven software engineering pipeline
**Tech**: Python (in `backend/app/engineering/`)

### Pipeline Stages:
1. **Goal Analysis**: Parse requirements -> structured goals
2. **Planning**: Goals -> execution plan with tasks
3. **Risk Assessment**: Identify risks in plan
4. **Task Execution**: Execute each task (plan/implement)
5. **Validation**: Validate patches against quality gates
6. **Repair**: Auto-repair failed validations
7. **Quality Gates**: Code quality, test coverage, security scans
8. **Approval**: Submit for human approval
9. **Documentation**: Generate documentation

### Data Model (9 tables):
- `engineering_plans`, `engineering_tasks`, `engineering_patches`, `engineering_validations`
- `engineering_repairs`, `engineering_quality`, `engineering_approvals`, `engineering_metrics`, `engineering_reports`

---

## 9. Audit System

**Role**: Comprehensive event capture and auditing
**Tech**: Python (in `backend/app/audit/`)

### Components:
- **AuditMiddleware**: FastAPI middleware intercepting all HTTP requests
- **EventBus**: Publisher/subscriber pattern for async auditing
- **AuditService**: Log, search, export (CSV/JSON), purge
- **17 categories**: auth, worker, job, workflow, repository, ai, agent, engineering, plugin, production, studio, system, security, data, config, network, custom

### Data Model (4 tables):
- `audit_logs` — 30+ fields for full audit trail
- `audit_settings` — retention, purge, export configuration
- `audit_exports` — export job records
- `audit_retention` — purge history

---

## 10. Plugin SDK

**Role**: Extensible plugin system
**Tech**: Python (in `backend/app/plugins/`)

### Components:
- **ManifestService**: Parse/validate `plugin.json`
- **PluginRegistry**: Track installed plugins
- **PluginLoader**: Dynamic import of plugin modules
- **HookRegistry**: 16 plugin hook types

### Plugin Hooks:
`on_startup`, `on_shutdown`, `before_request`, `after_request`, `on_worker_register`, `on_worker_heartbeat`, `on_worker_disconnect`, `on_job_created`, `on_job_completed`, `on_job_failed`, `on_workflow_start`, `on_workflow_finish`, `on_agent_message`, `on_engineering_plan`, `on_audit_event`, `on_repository_scan`

---

## 11. Build System

**Role**: Produce 7 executables + installer
**Tech**: Python orchestration, PyInstaller, Tauri v2, Inno Setup

### Pipeline (12 stages):
1. Verify environment (toolchain)
2. Clean artifacts
3. Build 4 frontends (npm run build)
4. Build 3 PyInstaller targets (master, worker, CLI)
5. Build 3 Tauri targets (MCC, WCC, Studio)
6. Sign executables (opt-in Authenticode)
7. Pre-installer PE validation gate
8. Package: ZIP + checksums (SHA-256) + manifest
9. Generate installer scripts + release notes + build report
10. Build AIClusterSetup.exe (Inno Setup)
11. Final verification
12. Release verification (10 stages)

### Targets:
| EXE | Packager | Size |
|-----|----------|------|
| AIClusterMaster.exe | PyInstaller | ~80 MB |
| AIClusterWorker.exe | PyInstaller | ~40 MB |
| aicluster.exe | PyInstaller | ~10 MB |
| MasterControlCenter.exe | Tauri | ~8-12 MB |
| WorkerControlCenter.exe | Tauri | ~8-12 MB |
| AIClusterStudio.exe | Tauri | ~8-12 MB |
| AIClusterSetup-*.exe | Inno Setup | ~500 MB |

---

## 12. Installer

**Role**: Single-file wizard installer for end users
**Tech**: Inno Setup 6 + Pascal Script

### Wizard Pages:
1. Welcome
2. Components (Full/Compact/Custom)
3. Preflight — Detect Python 3.12+, VC++ Redist
4. Firewall — Configure Windows Firewall rules
5. Install — Copy binaries, create shortcuts
6. Verify — Run verification pass
7. Finished — Launch options

### Components:
- Master Server (required)
- Worker Service (optional)
- Web Dashboard (optional)
- Master Control Center (optional)
- Worker Control Center (optional)
- AICluster Studio (optional)
- CLI Tools (optional)

---

## Subsystem Interactions

```
User Browser ──HTTP──> Master API ──SQL──> SQLite DB
                    │
                    ├──> WebSocket ──> Dashboard clients
                    │
                    ├──> Scheduler ──> Worker Assignment
                    │       │
                    │       └──> Worker Fleet
                    │              ├──> Registration
                    │              ├──> Heartbeat
                    │              ├──> Job Execution
                    │              └──> Progress/Result
                    │
                    ├──> AI Runtime ──> LLM Providers (Ollama, Llama.cpp, OpenAI)
                    │       │
                    │       └──> Model Router -> Provider -> Response
                    │
                    ├──> Multi-Agent Engine
                    │       │
                    │       └──> Orchestrator -> Agents -> Review -> Merge
                    │
                    ├──> Workflow Engine
                    │       │
                    │       └──> DAG Planner -> Dispatcher -> Workers -> Artifacts
                    │
                    ├──> Engineering Engine
                    │       │
                    │       └──> Goal -> Plan -> Tasks -> Validate -> Repair -> Approve
                    │
                    ├──> Repository Intelligence
                    │       │
                    │       └──> Scanner -> Indexer -> Parser -> Search
                    │
                    └──> Plugin System
                            │
                            └──> Manifest -> Loader -> Hooks -> Registry
```

## Studio (Desktop IDE)
```
Tauri App (Rust shell)
  └── React SPA (Vite)
       └── (Planned) Monaco Editor, Workspace, AI Chat, Workflow Designer
```

## Master Control Center (Desktop)
```
Tauri App (Rust shell)
  └── React SPA (Vite)
       └── FastAPI Backend (port 8800)
            └── HTTP -> Master API (port 8000)
```

## Worker Control Center (Desktop)
```
Tauri App (Rust shell)
  └── React SPA (Vite)
       └── FastAPI Backend (port 8900)
            ├── Local worker process management
            ├── Configuration read/write
            └── HTTP -> Master API (port 8000)
```
