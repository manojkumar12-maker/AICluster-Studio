# AICluster — Comprehensive Project Review & Architecture Document

**Version:** 1.2.1  
**Status:** Production Release (v1.2.1 — Master Audit System)  
**Last Updated:** 2026-07-03  
**Platform:** Windows (primary), master supports any OS with Python 3.12+  
**License:** Proprietary

---

## Table of Contents

1. [What AICluster Is](#1-what-aicluster-is)
2. [Why It Exists](#2-why-it-exists)
3. [Who Should Use It](#3-who-should-use-it)
4. [Architecture Overview](#4-architecture-overview)
5. [Subsystems in Detail](#5-subsystems-in-detail)
6. [Folder Layout](#6-folder-layout)
7. [Data Flow](#7-data-flow)
8. [Worker Flow](#8-worker-flow)
9. [Master Flow](#9-master-flow)
10. [AI Flow](#10-ai-flow)
11. [Plugin Flow](#11-plugin-flow)
12. [Workflow Flow](#12-workflow-flow)
13. [Repository Flow](#13-repository-flow)
14. [Engineering Flow](#14-engineering-flow)
15. [Studio Flow](#15-studio-flow)
16. [Audit Flow](#16-audit-flow)
17. [Release Flow](#17-release-flow)
18. [Dependency Graph](#18-dependency-graph)
19. [API Surface Summary](#19-api-surface-summary)
20. [Database Schema Overview](#20-database-schema-overview)

---

## 1. What AICluster Is

AICluster is an **offline-first AI cluster management platform** that turns idle Windows PCs on a local area network into a unified, intelligent compute cluster. It distributes AI workloads — code generation, repository analysis, multi-agent software engineering, and general-purpose compute tasks — across worker machines with strict resource limits (25% CPU, 8 GB RAM) to ensure office workers never experience performance degradation.

The platform is delivered as a suite of applications:

- **AICluster Master** (FastAPI backend + SQLite + WebSocket) — the central orchestrator
- **AICluster Worker** (FastAPI agent) — runs on each worker PC
- **Web Dashboard** (Next.js 15) — browser-based cluster management
- **Master Control Center** (Tauri v2 desktop app) — master PC cluster management
- **Worker Control Center** (Tauri v2 desktop app) — worker PC status and control
- **AICluster Studio** (Tauri v2 desktop app) — visual IDE for project management
- **AICluster CLI** (command-line tool) — headless cluster interaction
- **AIClusterSetup.exe** (single-file Inno Setup installer) — one-click installation

---

## 2. Why It Exists

Modern AI development increasingly requires substantial compute resources. Cloud-based solutions introduce data privacy concerns, recurring costs, internet dependency, and latency. Many organizations have dozens of Windows workstations sitting idle for large portions of the day. AICluster exists to:

- **Eliminate cloud dependency** — all compute happens on the local LAN, fully offline after initial setup
- **Monetize idle hardware** — office workstations with modern CPUs (Intel Core Ultra 7, etc.) are used during idle periods
- **Enable private AI** — sensitive codebases never leave the network
- **Provide distributed intelligence** — AI code analysis, repository understanding, multi-agent software engineering, all running on local hardware
- **Lower the barrier to entry** — one-click installers, PowerShell setup scripts, no DevOps knowledge required
- **Scale horizontally** — add workers by running the installer on any Windows PC; the master auto-discovers them

---

## 3. Who Should Use It

| Role | Use Case |
|------|----------|
| **Software Engineers** | Distributed code analysis, automated refactoring, test generation, documentation |
| **AI/ML Engineers** | Private LLM inference using local models via Ollama/llama.cpp/OpenAI-compatible endpoints |
| **DevOps / IT** | Cluster management, health monitoring, backup/restore, maintenance |
| **Technical Teams** | Multi-agent software engineering — decompose features into parallel agent tasks |
| **Small-to-Medium Businesses** | Private AI compute without cloud subscriptions or data leaving the network |
| **Educational Institutions** | Teach distributed computing concepts on existing lab hardware |

---

## 4. Architecture Overview

AICluster follows a **master-worker** topology. A single master PC runs the FastAPI backend, SQLite database, web frontend, and optional desktop control center. One or more worker PCs register with the master, send heartbeats, and execute assigned jobs.

```
                          ┌─────────────────────────────────────┐
                          │           MASTER PC                 │
                          │                                     │
                          │  ┌──────────────────────────────┐   │
                          │  │  Web Frontend                │   │
                          │  │  Next.js 15 / React 18 / TS  │   │
                          │  │  Port 3000                   │   │
                          │  └──────────┬───────────────────┘   │
                          │             │ REST + WebSocket       │
                          │  ┌──────────▼───────────────────┐   │
                          │  │  FastAPI Backend (Port 8000)  │   │
                          │  │                               │   │
                          │  │  API Layer    WebSocket /ws   │   │
                          │  │  Services    Background Tasks │   │
                          │  │  SQLAlchemy  SQLite (aiosqlite)│  │
                          │  │  Audit       Plugins          │   │
                          │  │  Repository  AI Runtime       │   │
                          │  │  Workflow    Multi-Agent      │   │
                          │  │  Engineering Production       │   │
                          │  └───────────────────────────────┘   │
                          │                                     │
                          │  ┌──────────────────────────────┐   │
                          │  │  Master Control Center       │   │
                          │  │  Tauri v2 Desktop App        │   │
                          │  │  Port 8800 (backend)         │   │
                          │  └──────────────────────────────┘   │
                          └──────────────┬──────────────────────┘
                                         │ HTTP (port 8000)
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
     ┌────────▼────────┐       ┌────────▼────────┐       ┌────────▼────────┐
     │   WORKER PC 1   │       │   WORKER PC 2   │       │   WORKER PC N   │
     │   Ultra 7        │       │   Ultra 7        │       │   Ultra 7        │
     │   Port 8001      │       │   Port 8001      │       │   Port 8001      │
     │                  │       │                  │       │                  │
     │  FastAPI Worker  │       │  FastAPI Worker  │       │  FastAPI Worker  │
     │  psutil Monitor  │       │  psutil Monitor  │       │  psutil Monitor  │
     │  25% CPU limit   │       │  25% CPU limit   │       │  25% CPU limit   │
     │  8 GB RAM limit  │       │  8 GB RAM limit  │       │  8 GB RAM limit  │
     │                  │       │                  │       │                  │
     │  Worker Control  │       │  Worker Control  │       │  Worker Control  │
     │  Center (Tauri)  │       │  Center (Tauri)  │       │  Center (Tauri)  │
     └──────────────────┘       └──────────────────┘       └──────────────────┘

              ┌─────────────────────────────────────┐
              │       AICluster Studio              │
              │  Tauri v2 Desktop App               │
              │  Visual IDE & Workspace Manager     │
              │  Monaco Editor, Terminal, AI Chat   │
              │  Workflow Designer, Agent Designer  │
              │  Repository Viewer, Plugin Center   │
              └─────────────────────────────────────┘
```

### Component Layering

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  Next.js 15 Web App  ·  Tauri v2 Desktop Apps  ·  CLI      │
├─────────────────────────────────────────────────────────────┤
│                      API Layer                               │
│  REST: /api/v1/*  ·  WebSocket: /ws  ·  WebDAV: /static    │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                             │
│  WorkerManager · Scheduler · AuthService · LogService       │
│  AuditService · PluginRegistry · EngineeringService         │
├─────────────────────────────────────────────────────────────┤
│                    Domain Engines                            │
│  Workflow · Repository · AI Runtime · Multi-Agent           │
│  Engineering · Production · Studio                           │
├─────────────────────────────────────────────────────────────┤
│                 Data Access Layer                            │
│  SQLAlchemy AsyncSession · Alembic Migrations               │
├─────────────────────────────────────────────────────────────┤
│                    Storage Layer                             │
│  SQLite (aiosqlite) · File System · Artifact Store          │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SQLite** | Zero-config, no server process. Suitable for LAN-scale (100 workers, 1000s of jobs). Migratable to PostgreSQL via SQLAlchemy. |
| **Async everywhere** | FastAPI + async SQLAlchemy + asyncio. Single process handles all connections via async I/O. |
| **Polling + WebSocket** | Frontend uses 2s React Query polling. WebSocket adds real-time broadcasts for status changes. |
| **15-second offline timeout** | Workers missing 3 consecutive heartbeats (5 s × 3) are marked offline. Configurable. |
| **PyInstaller packaging** | Produces single .exe files per component; no Python runtime required on target machines. |
| **Tauri v2** | Lightweight desktop apps using system WebView, no Electron overhead. |
| **Offline-first** | No internet required after initial npm/PyPI installs. All LLM providers run on localhost. |

---

## 5. Subsystems in Detail

### 5.1 Master Server

The master server is the central nervous system of AICluster. It is a FastAPI application running on the master PC.

**Location:** `backend/app/`

**Technology Stack:**
- Python 3.12+ with FastAPI
- SQLAlchemy 2.0 async + SQLite (via aiosqlite)
- Pydantic v2 for schema validation
- python-jose for JWT authentication
- passlib + bcrypt for password hashing
- WebSockets for real-time push

**Core Modules:**

| Module | File(s) | Responsibility |
|--------|---------|----------------|
| API Routes | `api/v1/*.py` | REST endpoints for all subsystems |
| WebSocket | `websocket/manager.py` | Connection management, broadcasting |
| Worker Manager | `services/worker_manager.py` | Registration, heartbeat, offline detection |
| Scheduler | `services/scheduler.py` | Job queue, priority assignment, dispatch |
| Auth Service | `services/auth.py` | JWT creation/validation, bcrypt, admin seeding |
| Log Service | `services/log_service.py` | Structured database logging |
| Database | `database.py` | Async engine, session factory, `init_db()` |

**Key Features:**
- 15-second heartbeat timeout → automatic offline marking
- Priority-based job scheduling (1–5)
- WebSocket broadcasts on every worker/job state change
- Rate limiting (200 req/min/IP)
- CORS restricted to configured origins
- Swagger UI at `/docs`, ReDoc at `/redoc`

### 5.2 Worker Service

The worker service runs on each worker PC and communicates with the master.

**Location:** `worker/app/`

**Technology Stack:**
- Python 3.12+ with FastAPI (for health endpoints)
- httpx for async HTTP to master
- psutil for system resource monitoring
- Custom state machine for lifecycle management

**State Machine:**

```
STARTING → LOADING_CONFIG → CONNECTING → REGISTERING → ONLINE
                                                              │
              ┌───────────────────────────────────────────────┘
              │
        HEARTBEAT → POLL_JOB → HAS_JOB → EXECUTING → REPORT_PROGRESS
              │                  │                           │
              │                  └── NO_JOB                  │
              │                                              │
              └────────────────── REPORT_RESULT ←────────────┘
                                        │
                                   SHUTDOWN → EXIT
                                        ↑
                                  RETRY (on failure)
```

**Job Handlers:**

| Handler | Description |
|---------|-------------|
| `echo` | Echoes payload back (testing) |
| `sleep` | Sleeps for specified duration (testing) |
| `dir_scan` | Recursively scans a directory |
| `hash_file` | Computes SHA-256 hash of a file |
| `count_files` | Counts files matching a pattern |

**Resource Constraints:**
- CPU: 25% maximum utilization (throttled via process priority and sleep)
- RAM: 8 GB maximum usage
- Process priority: `BELOW_NORMAL`
- Auto-pause on user activity detection
- Auto-resume after 5 minutes idle

### 5.3 Workflow Engine

The workflow engine provides DAG-based task execution across workers.

**Location:** `backend/app/workflow/`

**Submodules:**

| Module | Responsibility |
|--------|----------------|
| `planner/` | DAG generation, dependency resolution, duration estimation |
| `dispatcher/` | Worker assignment (load-based, round-robin) |
| `executor/` | Workflow orchestration — create, plan, dispatch, execute, retry, cancel |
| `artifacts/` | File-based artifact storage with SHA-256 checksums |
| `cache/` | TTL-based result caching keyed by workflow/task/input hash |
| `metrics/` | Execution metrics recording, queue stats, worker utilization |
| `state/` | State machine definitions (Workflow: PENDING→COMPLETED/FAILED, Task: CREATED→SUCCESS/CANCELLED) |
| `queue/` | Priority queue management |
| `validators/` | Workflow and task validation |

**Retry Engine:**
- Exponential backoff: 5 s, 30 s, 60 s
- Maximum 3 attempts per task
- Automatic delayed requeue on transient failure

**Workflow Types:** sequential, parallel, fan-out, fan-in

### 5.4 Repository Intelligence

The repository intelligence subsystem ingests git repositories and provides deep code understanding.

**Location:** `backend/app/repository/`

**Submodules:**

| Module | Responsibility |
|--------|----------------|
| `scanner/` | File system scanner, language detection, .gitignore-aware, binary detection |
| `parser/` | Symbol extraction — Python AST parser, TypeScript/JS regex parser, generic fallback |
| `indexer/` | Incremental indexing via file hash comparison, stores files/symbols/imports in DB |
| `search/` | Symbol search, file search, text search (regex), reference search |
| `metrics/` | LOC, cyclomatic complexity, symbol counts, maintainability index |
| `analysis/` | Deeper code analysis pipelines |
| `dependency/` | File dependency graph construction |
| `symbols/` | Symbol resolution and cross-referencing |
| `knowledge/` | Knowledge graph construction and querying |
| `embeddings/` | Code embedding generation for semantic search |
| `language/` | Per-language parser registration (Python, TS, JS +20 more) |
| `watcher/` | File system watcher for live indexing |

**Supported Languages:**
- **Full AST parsing:** Python, TypeScript, JavaScript
- **Generic regex parsing:** JSON, Markdown, YAML, HTML, CSS, SQL, Go, Rust, Java, Kotlin, Swift, Ruby, PHP, C, C++, C#, Shell, Batch, PowerShell, Vue, Svelte, Astro
- **Respects:** `.gitignore`, `node_modules`, `venv`, `dist`, `build`, `__pycache__`, `.git`, `.cache`

### 5.5 AI Runtime

The AI runtime abstracts LLM providers behind a common interface and provides routing, context management, and prompt building.

**Location:** `backend/app/ai/`

**Submodules:**

| Module | Responsibility |
|--------|----------------|
| `providers/` | Concrete provider implementations |
| `registry/` | Provider registration and discovery |
| `routing/` | Task-based model routing with fallback chains |
| `sessions/` | Session management with 24h expiry |
| `conversation/` | Message history with token tracking |
| `prompt/` | Prompt building with system prompt, context, token estimation |
| `context/` | Repository-aware context retrieval (symbols, files, metrics) |
| `models/` | Model registry, capability tracking |
| `tool_registry/` | Tool registration with schema and execution |
| `tool_executor/` | Tool execution engine |
| `streaming/` | Streaming response handling |
| `memory/` | AI memory management |
| `embeddings/` | Embedding generation and similarity search |
| `cache/` | Response caching |
| `metrics/` | Runtime performance metrics |
| `config/` | Provider configuration management |
| `security/` | Input sanitization and permission checks |
| `reasoning/` | Chain-of-thought and reasoning pipelines |

**Concrete LLM Providers:**

| Provider | Connection | Features |
|----------|------------|----------|
| **OllamaProvider** | HTTP to local Ollama | Load, generate, stream, token_count, health, auto-discover models via `/api/tags` |
| **LlamaCppProvider** | HTTP to llama.cpp server | Load, generate, stream, tokenize, health, SSE streaming |
| **OpenAICompatibleProvider** | HTTP to any OpenAI-compatible endpoint | API key auth, model auto-discovery, works with vLLM/LM Studio/NVIDIA NIM |

**Model Profiles:**
- `fast` — low max_tokens, high temperature
- `balanced` — moderate values
- `maximum_quality` — high max_tokens, low temperature
- `offline_low_ram` — minimized memory footprint
- `custom` — user-configurable

**Fallback Chain:** Preferred provider → alternate provider → any loaded provider → clear error message

### 5.6 Multi-Agent Engine

The multi-agent engine orchestrates collaborative AI agents to solve complex software engineering tasks.

**Location:** `backend/app/agents/`

**Submodules:**

| Module | Responsibility |
|--------|----------------|
| `registry/` | Agent registration with role, capabilities, permissions, model preference |
| `planner/` | Task decomposition by request type, creates execution DAG |
| `orchestrator/` | Central coordinator — receives request, plans, assigns, monitors, triggers review |
| `communication/` | Structured message passing with 9 message types |
| `review/` | 7 quality gates: correctness, architecture, security, performance, style, tests, documentation |
| `merge/` | Collects all agent outputs, resolves conflicts, produces unified result |
| `memory/` | Per-agent working/session/repository memory with importance scoring |
| `roles/` | Role definitions and capability mappings |
| `coordinator/` | Inter-agent coordination logic |
| `events/` | Agent lifecycle event management |
| `sessions/` | Agent session management |
| `evaluation/` | Agent output evaluation and scoring |
| `delegation/` | Task delegation between agents |
| `policies/` | Agent behavior policies |
| `reasoning/` | Agent reasoning pipelines |
| `telemetry/` | Agent performance tracking |
| `artifacts/` | Agent output artifact management |

**Default 12 Agents:**

| Agent | Role | Capabilities |
|-------|------|--------------|
| Planner | planner | planning, decomposition, dag_creation |
| Architect | architect | architecture, design, code_review |
| Backend Engineer | engineer | backend, api, database, python, sql |
| Frontend Engineer | engineer | frontend, ui, react, typescript |
| Database Engineer | engineer | database, sql, schema_design, migrations |
| DevOps Engineer | engineer | devops, deployment, ci_cd, docker |
| Security Engineer | engineer | security, audit, vulnerability_scan |
| QA Engineer | qa | testing, quality, test_creation |
| Documentation Writer | writer | documentation, writing, technical_writing |
| Reviewer | reviewer | review, code_review, quality_assurance |
| Merger | merger | merge, integration, conflict_resolution |
| Project Manager | manager | management, coordination, planning |

### 5.7 Engineering Engine

The engineering engine provides autonomous software engineering capabilities — goal analysis, planning, validation, repair, quality gating, and documentation.

**Location:** `backend/app/engineering/`

**Submodules:**

| Module | Responsibility |
|--------|----------------|
| `goal/analyzer.py` | Intent classification (feature, bug_fix, refactor, update, documentation), risk detection |
| `planner/service.py` | Implementation plans from natural language goals, task chains, effort estimation |
| `validator/service.py` | 7 automated checks: architecture, security, syntax, formatting, lint, types, tests |
| `repair/service.py` | Self-repair loop (max 3 iterations), automatic fix generation, escalation |
| `quality/gates.py` | 9 quality gates: architecture_review, static_analysis, security_review, formatting, lint, type_check, unit_tests, integration_tests, documentation_check |
| `risk/engine.py` | Keyword-based risk classification, dangerous operation detection, approval creation |
| `documentation/service.py` | Auto-updates README, CHANGELOG, PROJECT_STATE, API docs, architecture docs |
| `executor/` | Plan execution engine |
| `approvals/` | Approval workflow (pending/approved/rejected) |
| `changes/` | Change tracking and patch management |
| `git/` | Git integration for patch application |
| `reports/` | Engineering report generation |
| `sessions/` | Engineering session management |
| `policies/` | Engineering behavior policies |
| `review/` | Engineering review workflows |
| `architecture/` | Architecture validation |

**Pipeline:**
```
User Goal → Goal Analyzer (risk/type) → Planner (tasks/files)
  → Validate (7 checks) → Execute (patch) → Quality Gates (9 checks)
  → Self-Repair (max 3 iterations) → Documentation → Report
```

### 5.8 Audit System

The audit system provides comprehensive event logging, search, export, retention management, and middleware-based HTTP request capture.

**Location:** `backend/app/audit/`

**Modules:**

| Module | File | Responsibility |
|--------|------|----------------|
| Service | `service.py` | Core `AuditService` — log(), search(), export(), purge(), statistics(), settings management |
| Events | `events.py` | `AuditEvent` data class, `EventBus` pub/sub for decoupled event distribution |
| Middleware | `middleware.py` | FastAPI middleware capturing HTTP method, URL, status code, duration, IP, safe headers |
| Models | `models.py` | 4 SQLAlchemy tables: `audit_logs`, `audit_settings`, `audit_exports`, `audit_retention` |
| Schemas | `schemas.py` | Pydantic models for search, statistics, settings |
| API | `api.py` | 9 REST endpoints under `/api/v1/audit/` |

**17 Event Categories:**
authentication, worker, workflow, repository, ai_runtime, engineering, plugin, studio, settings, backup, restore, deployment, monitoring, system, security, user, scheduler

**33 Event Types:**
LOGIN, LOGOUT, LOGIN_FAILED, TOKEN_REFRESH, WORKFLOW_CREATED/STARTED/COMPLETED/FAILED/CANCELLED, WORKER_REGISTERED/DISCONNECTED/RECONNECTED/RESTARTED/UPDATED, PLUGIN_INSTALLED/UPDATED/ENABLED/DISABLED/REMOVED, MODEL_LOADED/UNLOADED/SWITCHED, AI_CHAT, TOOL_CALL, TOOL_RESULT, REPOSITORY_SCANNED, REPOSITORY_INDEXED, ENGINEERING_PLAN, PATCH_CREATED/APPLIED, VALIDATION_STARTED/COMPLETED, BACKUP_CREATED/RESTORED, CONFIG_CHANGED, SYSTEM_STARTED/STOPPED, ERROR, WARNING, CUSTOM_EVENT

### 5.9 Plugin SDK

The plugin system allows extending AICluster without modifying core code.

**Location:** `backend/app/plugins/`

**Submodules:**

| Module | Responsibility |
|--------|----------------|
| `registry/` | In-memory plugin registry, lifecycle management |
| `manifest/` | `plugin.json` validation (plugin_id, version, hooks, permissions, entry_point) |
| `loader/` | Dynamic Python module loading from `plugins/` directory |
| `hooks/` | Hook registry — register callbacks for 15 platform hooks |
| `sdk/` | Plugin API — logger, config, database, workflow/repository/AI/agent APIs |
| `permissions/` | Permission model (read/write repository, run workflow, execute tool, access LLM, etc.) |
| `sandbox/` | Isolated execution with file/network/tool/memory/CPU restrictions |
| `validation/` | Manifest validation, platform compatibility, dependency checking |
| `installer/` | Plugin installation from directory or ZIP upload |
| `events/` | Plugin lifecycle events |
| `cli/` | Plugin CLI commands |
| `marketplace/` | Plugin marketplace interface |
| `signing/` | Plugin signature verification |
| `examples/` | Example plugin implementations |

**15 Platform Hooks:**
on_startup, on_shutdown, on_workflow_start, on_workflow_finish, on_task_start, on_task_finish, on_repository_scan, on_repository_indexed, on_agent_created, on_llm_response, on_tool_execution, on_worker_connected, on_worker_disconnected, on_backup, on_restore

**Plugin Lifecycle:**
Install → Validate → Load → Initialize → Register Hooks → Run → Pause → Resume → Unload → Uninstall

### 5.10 Web Frontend (Next.js Dashboard)

The browser-based dashboard for cluster management.

**Location:** `frontend/`

**Technology Stack:**
- Next.js 15 App Router with TypeScript
- React 18 with TailwindCSS 3.4
- shadcn/ui component library (Radix primitives)
- Zustand 5 for auth state with persist middleware
- TanStack React Query for API data fetching (2s polling)
- Framer Motion for animations
- Recharts for analytics charts
- Lucide React for icons

**Pages:**
- Login (JWT authentication)
- Dashboard (live cluster metrics)
- Workers (live cards, pause/resume)
- Jobs (queue, status, cancel)
- Chat (AI chat interface)
- Projects (repository management)
- Files (file browser)
- Analytics (charts and trends)
- Logs (structured log viewer)
- Settings (cluster configuration)

**Build:** `npm run build` produces zero errors, zero warnings. `npm run lint` passes with zero warnings.

### 5.11 Desktop Apps (Tauri v2)

Three Tauri v2 desktop applications provide native experiences:

| App | Location | Purpose |
|-----|----------|---------|
| **Master Control Center** | `master-control-center/` | Cluster management on master PC (dashboard, workers, jobs, cluster map, discovery, backups, diagnostics, notifications, logs, settings) |
| **Worker Control Center** | `worker-control-center/` | Worker PC status, local monitoring, pause/resume, log viewer |
| **AICluster Studio** | `studio/` | Visual IDE: workspace management, project explorer, Monaco editor, terminal, AI chat, workflow/agent designer, prompt studio, plugin center, model manager, repository viewer |

All three use:
- Rust + Tauri v2 for the native shell
- React + TypeScript + Vite for the frontend
- TanStack React Query + Zustand + Framer Motion
- `react-resizable-panels` for Studio layout management

### 5.12 CLI

The command-line interface for headless cluster operations.

**Location:** `build/modules/cli_entry.py` → produces `aicluster.exe`

**Features:**
- Cluster status (`aicluster status`)
- Job submission (`aicluster job submit`)
- Worker management (`aicluster worker list`)
- Health checks (`aicluster health`)

### 5.13 Installer

Single-file Windows installer for one-click deployment.

**Location:** `build/setup/`

**Technology:**
- Inno Setup script (`setup.iss`)
- NSIS fallback
- Compiles to `AIClusterSetup-{version}.exe`
- SHA-256 checksum verification post-install
- Optional installation of Master, Worker, or both components

### 5.14 Build System

The build system is a Python-based orchestrator that produces all distribution artifacts.

**Location:** `build/`

**Pipeline Steps:**
1. Verify environment (Python, Node, npm, Rust, Tauri, PyInstaller, Inno Setup, 7-Zip, signtool)
2. Clean previous outputs
3. Build all web frontends (`npm run build`)
4. Build PyInstaller targets (master, worker, CLI)
5. Build Tauri targets (master-control, worker-control, studio)
6. Sign executables (Authenticode, if certificate configured)
7. Verify PE authenticity gate (every .exe must be a real Windows PE binary)
8. Package release (ZIPs, checksums, manifest)
9. Build Inno Setup `AIClusterSetup.exe`
10. Final verification (artifact integrity, checksums)
11. Release verification (comprehensive multi-check pipeline)
12. Emit build report and RELEASE_NOTES.md

**PyInstaller Targets:**
- `AIClusterMaster.exe` — Master Server (FastAPI + all subsystems)
- `AIClusterWorker.exe` — Worker Service (FastAPI agent)
- `aicluster.exe` — CLI tool

**Tauri Targets:**
- `MasterControlCenter.exe` — Desktop cluster management
- `WorkerControlCenter.exe` — Desktop worker management
- `AIClusterStudio.exe` — Visual IDE

---

## 6. Folder Layout

```
AICluster/
│
├── README.md                     # Project overview and quick start
├── VISION.md                     # North star vision document
├── PROJECT_STATE.md              # Current state, completion, known issues
├── CHANGELOG.md                  # Full version history (v0.1.0 → v1.2.1)
├── RESUME.md                     # Development resume point
├── NEXT_PHASE.md                 # Next development phase specification
├── TODO.md                       # Task list
├── TEST_REPORT.md                # Test results summary
├── VERSION                       # Current version string ("1.2.1")
│
├── backend/                      # FastAPI master server
│   ├── app/
│   │   ├── main.py               # FastAPI entry point, lifespan, WebSocket
│   │   ├── config.py             # Pydantic settings from .env
│   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   ├── logging_config.py     # Rotating file handler config
│   │   ├── api/v1/               # REST API route handlers
│   │   │   ├── auth.py           # Login, JWT
│   │   │   ├── workers.py        # Register, heartbeat, CRUD
│   │   │   ├── jobs.py           # Create, list, cancel
│   │   │   ├── dashboard.py      # Cluster metrics
│   │   │   ├── health.py         # Health check
│   │   │   ├── logs.py           # System log queries
│   │   │   ├── workflows.py      # Workflow CRUD and execution
│   │   │   ├── repositories.py   # Repository management
│   │   │   ├── ai.py             # AI chat and completion
│   │   │   ├── agents.py         # Agent orchestration
│   │   │   ├── engineering.py    # Autonomous engineering
│   │   │   ├── plugins.py        # Plugin lifecycle
│   │   │   ├── production.py     # Monitoring, health, diagnostics
│   │   │   └── studio/           # Studio workspace/project APIs
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── worker.py         # Worker node
│   │   │   ├── job.py            # Job queue
│   │   │   ├── log.py            # System log
│   │   │   ├── user.py           # Auth user
│   │   │   ├── workflow.py       # Workflow engine (9 tables)
│   │   │   ├── repository.py     # Repository intelligence (18 tables)
│   │   │   ├── ai.py             # AI runtime (16 tables)
│   │   │   ├── agent.py          # Multi-agent (10 tables)
│   │   │   ├── engineering.py    # Engineering engine (10 tables)
│   │   │   └── studio.py         # Studio workspace (6 tables)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Business logic
│   │   │   ├── worker_manager.py # Registration, heartbeat, offline
│   │   │   ├── scheduler.py      # Job queue, assignment, retry
│   │   │   ├── auth.py           # JWT, bcrypt, admin seeding
│   │   │   └── log_service.py    # Structured database logging
│   │   ├── websocket/            # WebSocket manager
│   │   ├── workflow/             # DAG-based workflow engine
│   │   ├── repository/           # Code intelligence engine
│   │   ├── ai/                   # AI runtime + LLM providers
│   │   ├── agents/               # Multi-agent orchestration
│   │   ├── engineering/          # Autonomous engineering engine
│   │   ├── audit/                # Audit event system
│   │   ├── plugins/              # Plugin SDK and registry
│   │   └── production/           # Monitoring, health, diagnostics
│   ├── tests/                    # pytest test suite (44+ tests)
│   ├── alembic/                  # Database migrations (installed, configured)
│   ├── data/                     # SQLite database file location
│   ├── logs/                     # Backend log files
│   ├── requirements.txt          # Python dependencies
│   └── pyproject.toml            # Project metadata
│
├── frontend/                     # Next.js 15 web dashboard
│   ├── src/
│   │   ├── app/                  # Pages (App Router)
│   │   ├── components/           # React components (shadcn/ui)
│   │   ├── lib/                  # Utility functions
│   │   ├── stores/               # Zustand stores
│   │   ├── types/                # TypeScript type definitions
│   │   └── styles/               # Global styles
│   ├── public/                   # Static assets
│   └── package.json              # Node dependencies
│
├── worker/                       # Worker agent service
│   ├── app/
│   │   ├── main.py               # FastAPI entry with worker lifecycle
│   │   ├── config.py             # Three-tier configuration
│   │   ├── core/                 # State machine, constants
│   │   ├── services/             # Registrar, heartbeat, poller, reporter, executor, monitor
│   │   ├── executor/             # Job handler framework + 5 handlers
│   │   └── utils/                # HTTP client, retry handler
│   ├── tests/                    # 14 worker unit tests
│   ├── scripts/                  # Worker runner
│   └── pyproject.toml
│
├── master-control-center/        # Tauri desktop app for master management
│   ├── frontend/                 # React + Vite + TailwindCSS
│   │   ├── src/                  # Pages (11 pages)
│   │   └── src-tauri/            # Tauri v2 Rust shell
│   └── backend/                  # FastAPI helper service (port 8800)
│       └── app/
│           ├── main.py           # Entry point
│           └── api/router.py     # Cluster management endpoints
│
├── worker-control-center/        # Tauri desktop app for worker management
│   ├── frontend/                 # React + Vite + TailwindCSS
│   │   └── src-tauri/            # Tauri v2 Rust shell
│   └── backend/                  # FastAPI helper service
│       └── app/
│           ├── main.py
│           └── api/router.py
│
├── studio/                       # AICluster Studio (visual IDE)
│   ├── src/                      # React + Vite + TailwindCSS 4
│   ├── src-tauri/                # Tauri v2 Rust shell
│   └── package.json
│
├── shared/                       # Shared code across components
│   ├── protocol/                 # Python protocol definitions
│   │   ├── registration.py       # RegisterRequest/Response
│   │   ├── heartbeat.py          # HeartbeatRequest/Response
│   │   ├── jobs.py               # NextJob, Progress, Result
│   │   └── errors.py             # ErrorResponse
│   ├── py/                       # Shared Python modules
│   │   ├── models.py             # Shared data models
│   │   └── schemas.py            # Shared Pydantic schemas
│   └── ts/                       # Shared TypeScript types
│       ├── types.ts              # Enums and interfaces
│       └── index.ts              # Re-exports
│
├── plugins/                      # Plugin packages
│   └── example-metrics-reporter/ # Reference plugin implementation
│       ├── plugin.json           # Manifest (id, version, hooks, permissions)
│       └── main.py               # Plugin class with on_workflow_finish hook
│
├── build/                        # Build system (Python orchestrator)
│   ├── build.py                  # Master build orchestrator
│   ├── config.py                 # Build config, PyInstaller/Tauri target definitions
│   ├── version.py                # Version resolution
│   ├── frontend.py               # Frontend build runner
│   ├── pyinstaller_builder.py    # PyInstaller spec generation + execution
│   ├── tauri_builder.py          # Tauri build runner
│   ├── package.py                # Release packaging, ZIPs, checksums
│   ├── release.py                # Installer generation + release notes
│   ├── sign.py                   # Authenticode code signing
│   ├── checksum.py               # SHA-256 checksum generation
│   ├── clean.py                  # Build artifact cleanup
│   ├── verify.py                 # Build verification
│   ├── setup_builder.py          # Inno Setup script generation + compilation
│   ├── setup_validator.py        # Installer validation
│   ├── modules/                  # Entry scripts for PyInstaller
│   │   ├── master_entry.py       # Master executable entry point
│   │   ├── worker_entry.py       # Worker executable entry point
│   │   ├── cli_entry.py          # CLI executable entry point
│   │   └── make_default_icon.py  # Default icon generator
│   ├── setup/                    # Installer assets and scripts
│   │   ├── setup.iss             # Inno Setup script
│   │   ├── payload/              # Installer payload directory
│   │   ├── config/               # Installer configuration
│   │   └── assets/               # Installer assets
│   └── verification/             # Post-build release verification
│       ├── verify.py             # Verification orchestrator
│       ├── verify_build.py       # Build artifact verification
│       ├── verify_backend.py     # Backend health verification
│       ├── verify_frontend.py    # Frontend build verification
│       ├── verify_api.py         # API endpoint verification
│       ├── verify_executables.py # PE binary verification
│       ├── verify_installer.py   # Installer verification
│       ├── verify_checksums.py   # Checksum verification
│       ├── verify_artifacts.py   # Artifact integrity verification
│       ├── verify_config.py      # Configuration verification
│       ├── verify_report.py      # Report generation
│       ├── verify_python.py      # Python environment verification
│       └── context.py            # Verifier context
│
├── config/                       # YAML configuration files
│   ├── default.yaml              # Default configuration
│   ├── development.yaml          # Development overrides
│   └── production.yaml           # Production overrides
│
├── docs/                         # Documentation
│   ├── architecture.md           # Architecture document
│   ├── API_REFERENCE.md          # API endpoint reference
│   ├── DATABASE.md               # Database schema documentation
│   ├── release-checklist.md      # Release verification checklist
│   └── phase-*-validation-report.md  # Phase validation reports
│
├── scripts/                      # Utility scripts
│   ├── setup.ps1                 # Environment setup (venv, npm install)
│   ├── start-master.ps1          # Start master server
│   ├── start-worker.ps1          # Start worker agent
│   ├── install-master.ps1        # One-click master installation
│   ├── install-worker.ps1        # One-click worker installation
│   ├── run-integration-test.py   # 40 end-to-end integration tests
│   └── worker-simulator.py       # TUI worker simulator (4 workers)
│
├── assets/                       # Static assets
│   ├── icons/                    # Application icons (ICO, PNG)
│   ├── manifest.json             # Asset manifest
│   └── README.md
│
├── data/                         # Runtime data directory
├── models/                       # Local LLM model storage
├── logs/                         # Application logs directory
│   ├── aicluster.log
│   ├── master.log
│   ├── worker.log
│   ├── build.log
│   └── verification.log
│
├── artifacts/                    # Build artifacts
│   └── AIClusterSetup-1.2.1.exe # Single-file installer
│
├── release/                      # Release output directory
│   ├── master/                   # AIClusterMaster.exe + support files
│   ├── worker/                   # AIClusterWorker.exe + support files
│   ├── cli/                      # aicluster.exe
│   ├── master-control/           # MasterControlCenter.exe
│   ├── worker-control/           # WorkerControlCenter.exe
│   ├── studio/                   # AIClusterStudio.exe
│   └── ...                       # ZIPs, checksums, reports
│
├── checksums/                    # Checksum storage
├── temp/                         # Temporary build files
└── dist/                         # PyInstaller dist output
```

---

## 7. Data Flow

The data flow between workers and master is the primary communication channel.

```
┌──────────┐         ┌──────────┐
│  Worker   │         │  Master  │
│  Service  │         │  Server  │
└─────┬────┘         └─────┬────┘
      │                     │
      │  POST /api/v1/workers/register
      │  {name, hostname, ip, version}
      ├────────────────────►│
      │                     ├── Store/update worker in DB
      │                     ├── Log registration event
      │  {id: "uuid", status: "ok"}
      │◄────────────────────┤
      │                     │
      │  ── Heartbeat Loop (5s interval) ──
      │                     │
      │  POST /api/v1/workers/heartbeat
      │  {id, cpu, ram, disk, temp, busy}
      ├────────────────────►│
      │                     ├── Update worker record
      │                     ├── Broadcast WebSocket update
      │  {status: "ok"}
      │◄────────────────────┤
      │                     │
      │  GET /api/v1/workers/{id}/next-job
      ├────────────────────►│
      │                     ├── Check scheduler for pending jobs
      │                     ├── If job available: assign, return job
      │  {job: {id, type, payload, ...}} OR 204 No Content
      │◄────────────────────┤
      │                     │
      │  ── Job Execution ──
      │                     │
      │  POST /api/v1/workers/{id}/progress
      │  {job_id, progress: 45}
      ├────────────────────►│
      │                     ├── Update job progress in DB
      │                     ├── Broadcast WebSocket progress
      │                     │
      │  POST /api/v1/workers/{id}/result
      │  {job_id, status: "completed", result: {...}}
      ├────────────────────►│
      │                     ├── Mark job complete in DB
      │                     ├── Store result
      │                     ├── Broadcast WebSocket result
      │  {status: "ok"}
      │◄────────────────────┤
```

### Flow Details

**Registration:**
- Worker sends name, hostname, IP on startup
- Master creates or updates worker record (re-registration updates IP/hostname)
- Master logs the event and broadcasts via WebSocket
- Worker receives UUID identifier

**Heartbeat:**
- Worker sends every 5 seconds with CPU%, RAM%, disk%, temperature
- Master updates the worker's `last_seen` timestamp
- If `last_seen` > 15 seconds old, master marks worker offline (background task runs every 10 s)
- WebSocket broadcasts on every heartbeat for real-time dashboard

**Job Polling:**
- Worker calls `/next-job` after each heartbeat
- Master's scheduler picks the highest-priority queued job, assigns to requesting worker
- Returns job data or 204 (no job available)
- Worker executes the job and reports progress

**Progress & Results:**
- Progress: reported at ≥5% changes or ≥2 second intervals
- Result: status (completed/failed/cancelled), result data or error, duration in ms
- Master updates DB and broadcasts WebSocket events

---

## 8. Worker Flow

The complete worker lifecycle, from startup to shutdown:

```
   START
     │
     ▼
┌─────────────┐
│   STARTING   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│LOADING_CONFIG│  Read three-tier config (env > config.json > .env > defaults)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  CONNECTING  │  Create HTTP client to master URL
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ REGISTERING  │  POST /api/v1/workers/register
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
  OK      FAIL
   │       │
   │       ▼
   │   ┌─────────┐
   │   │  RETRY   │  Exponential backoff: 1, 2, 5, 10, 30, 60 s
   │   └────┬────┘
   │        │
   │        └──────────► (loop back to REGISTERING)
   │
   ▼
┌─────────┐
│  ONLINE  │
└────┬────┘
     │
     ▼
┌───────────┐
│ HEARTBEAT  │  POST /api/v1/workers/heartbeat (every 5 s)
└────┬──────┘
     │
     ▼
┌───────────┐
│ POLL_JOB   │  GET /api/v1/workers/{id}/next-job
└────┬──────┘
     │
   ┌─┴──┐
   │    │
  JOB  NONE
   │    │
   │    └──────► (loop back to HEARTBEAT)
   │
   ▼
┌───────────┐
│ EXECUTING  │  Run handler.execute() with job payload
└────┬──────┘
     │
     ▼
┌──────────────┐
│REPORT_PROGRESS│  POST /api/v1/workers/{id}/progress (async generator)
└──────┬───────┘
       │
       ▼
┌─────────────┐
│REPORT_RESULT │  POST /api/v1/workers/{id}/result
└──────┬──────┘
       │
       └──────► (loop back to HEARTBEAT)

FAILURE AT ANY POINT:
       │
       ▼
   ┌─────────┐
   │  RETRY   │  Exponential backoff, auto-reconnect
   └────┬────┘
        │
        └──────► (loop back to REGISTERING or CONNECTING)

SHUTDOWN SIGNAL (SIGINT/SIGTERM):
       │
       ▼
   ┌──────────┐
   │ SHUTDOWN  │  Stop heartbeat, close HTTP client, flush logs
   └────┬─────┘
        │
        ▼
   ┌────────┐
   │  EXIT   │
   └────────┘
```

### Job Handler Execution

```
execute_job(worker_id, job_data):
  │
  ├── Determine job_type from job_data
  ├── Look up handler in JobRegistry
  │
  ├── IF handler has execute_with_progress:
  │     for progress in handler.execute_with_progress(payload):
  │         if progress changed ≥ 5% OR 2s elapsed:
  │             POST /progress
  │     result = handler.execute(payload)
  │
  ├── ELSE:
  │     result = handler.execute(payload)
  │
  ├── POST /result (completed, result data)
  │
  └── On error: POST /result (failed, error message)
```

---

## 9. Master Flow

The flow of a request through the master server:

```
CLIENT (Browser / Worker / CLI)
        │
        ▼
┌─────────────────┐
│   CORS Check    │  Allow configured origins, methods, headers
├─────────────────┤
│  Rate Limiter   │  200 requests/minute/IP
├─────────────────┤
│ Audit Middleware │  Capture method, URL, status, duration, IP
├─────────────────┤
│  Auth Check     │  JWT Bearer token validation (except /health, /login, /docs)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Router    │  Route to appropriate handler
│   /api/v1/*     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pydantic       │  Request validation (types, constraints, defaults)
│  Validation     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Service Layer   │
│                 │
│  WorkerManager  │  Register, heartbeat, CRUD, offline detection
│  Scheduler      │  Queue, priority, assign, retry
│  AuthService    │  Login, JWT create/verify
│  LogService     │  Structured logging
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Layer     │  SQLAlchemy async session
│  SQLite DB      │  CRUD operations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response       │  Pydantic response model serialization
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WebSocket      │  Broadcast state changes to all connected clients
│  Broadcast      │  (workers, jobs, dashboard events)
└─────────────────┘
```

### Background Tasks

The master runs two critical background tasks:

**Offline Checker (every 10 s):**
```
1. Query: SELECT * FROM workers WHERE last_seen < (now - 15s) AND status NOT IN ('offline', 'disabled')
2. For each expired worker:
   a. Set status = 'offline'
   b. Clear current_job
   c. Log WARNING event
3. Broadcast offline event via WebSocket
```

**Scheduler Loop (every 2 s):**
```
1. Query: SELECT * FROM jobs WHERE status = 'queued' ORDER BY priority DESC, created_at ASC
2. For each queued job:
   a. Find available worker (online, not paused, lowest CPU %)
   b. If worker found:
      - Set job status = 'running'
      - Assign worker_id
      - Set started_at = now
      - Broadcast assignment via WebSocket
   c. If no worker available, leave queued
```

---

## 10. AI Flow

The flow from user prompt to LLM response:

```
USER
  │
  │ POST /api/v1/ai/chat
  │ {message, session_id?, context?, stream?}
  ▼
┌──────────────────┐
│  Session Manager  │  Create/get session (24h expiry)
│                   │  Restore conversation history
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Prompt Builder   │  Build prompt with:
│                   │  - System prompt (role, constraints)
│                   │  - Repository context (if available)
│                   │  - Session history (last N messages)
│                   │  - Current user message
│                   │  - Token estimation & compression
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Context Builder  │  If repository_id provided:
│                   │  - Retrieve relevant symbols/files
│                   │  - Score by relevance to query
│                   │  - Enforce token budget
│                   │  - Attach to prompt
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Model Router     │  Select provider based on:
│                   │  - Task type (code, chat, analysis)
│                   │  - Model profile (fast/balanced/quality)
│                   │  - Availability
│                   │  - Fallback chain
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Provider Layer   │  One of:
│                   │  - OllamaProvider
│                   │  - LlamaCppProvider
│                   │  - OpenAICompatibleProvider
│                   │
│  generate(prompt) │  → tokens → stream → complete
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│ Conversation     │  Store user message + assistant response
│ Manager          │  Update token counts
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Response         │  Return {message, session_id,
│                   │          tokens_used, execution_ms}
└──────────────────┘
```

### Provider Architecture

```
                    ┌─────────────────┐
                    │  ModelRegistry   │
                    │  (singleton)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼──────┐  ┌─────▼────────┐
     │  Ollama     │  │  LlamaCpp   │  │  OpenAI      │
     │  Provider   │  │  Provider   │  │  Compatible  │
     └────────┬───┘  └──────┬──────┘  └─────┬────────┘
              │             │                │
     HTTP POST /api/chat    │       POST /v1/chat/completions
                            │                │
                   HTTP POST /completion     │
                                     POST /v1/completions
```

---

## 11. Plugin Flow

The complete plugin lifecycle:

```
┌──────────────────┐
│   1. INSTALL      │  Plugin directory or ZIP uploaded
│                   │  → Validate manifest (plugin.json)
│                   │  → Check dependencies
│                   │  → Check platform compatibility
│                   │  → Copy to plugins/<plugin_id>/
│                   │  → Log: PLUGIN_INSTALLED
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   2. VALIDATE     │  → Verify entry_point exists
│                   │  → Verify declared hooks are valid
│                   │  → Verify permissions are recognized
│                   │  → Check min/max platform version
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   3. LOAD         │  → Dynamic import of entry_point module
│                   │  → Instantiate Plugin class
│                   │  → Call plugin.on_load() if exists
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   4. INITIALIZE   │  → Pass SDK to plugin
│                   │  → logger, config, DB access
│                   │  → workflow/repository/AI/agent APIs
│                   │  → Call plugin.on_init() if exists
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. REGISTER HOOKS │  → For each hook in manifest.hooks:
│                   │     Register callback in HookRegistry
│                   │  → Call plugin.on_register() if exists
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 6. ACTIVATE       │  → Set plugin status = active
│                   │  → Call plugin.on_activate() if exists
│                   │  → Plugin now receives hook callbacks
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 7. HOOK EXECUTION │  When a platform event fires:
│                   │  → HookRegistry looks up all callbacks
│                   │  → Sorts by priority
│                   │  → Executes each async callback
│                   │  → Error isolation per callback
│                   │  → Results collected and returned
└────────┬─────────┘
         │
         ├── DISABLE → Call plugin.on_disable(), skip hooks
         ├── ENABLE  → Call plugin.on_enable(), resume hooks
         └── UNINSTALL → Call plugin.on_uninstall()
                         Remove plugin directory
                         Log: PLUGIN_REMOVED
```

### Hook Execution Model

```
Event: WORKFLOW_COMPLETED
       │
       ▼
HookRegistry.get_callbacks("on_workflow_finish")
       │
       ├── Plugin A (priority 10)
       │     └── on_workflow_finish(workflow_id, status)
       │         └── {"reported": true}
       │
       ├── Plugin B (priority 20)
       │     └── on_workflow_finish(workflow_id, status)
       │         └── {"notified": true}
       │
       └── Collect results → return aggregated
```

---

## 12. Workflow Flow

The workflow lifecycle from creation to completion:

```
USER / API CALLER
       │
       │ POST /api/v1/workflow
       │ {name, type, tasks, dependencies, ...}
       ▼
┌──────────────────┐
│  1. CREATE        │  → Validate workflow definition
│                   │  → Store in DB (status: pending)
│                   │  → Create individual task records
│                   │  → Create dependency edges
│                   │  → Broadcast workflow_created
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. PLAN          │  → WorkflowPlanner analyzes DAG
│                   │  → Resolve dependencies
│                   │  → Estimate durations
│                   │  → Determine execution order
│                   │  → Organize into stages (sequential/parallel)
│                   │  → Set workflow status: planned
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. QUEUE         │  → Enqueue ready tasks
│                   │  → A task is "ready" when all
│                   │    dependencies are satisfied
│                   │  → Set workflow status: running
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  4. DISPATCH      │  → TaskDispatcher finds best worker
│                   │  → Criteria: load, status, capabilities
│                   │  → Fallback: round-robin
│                   │  → Assign task to worker
│                   │  → Set task status: assigned
│                   │  → Broadcast task_assigned
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  5. EXECUTE       │  → Worker picks up task
│                   │  → Worker reports progress
│                   │  → On success: store result
│                   │  → On failure:
│                   │      Check retry count < max
│                   │      Yes: exponential backoff, requeue
│                   │      No: mark task failed
│                   │  → Broadcast task_started/finished
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  6. COMPLETE      │  → All tasks completed successfully
│                   │  → Store workflow result
│                   │  → Store artifacts (SHA-256, size, path)
│                   │  → Record execution metrics
│                   │  → Set workflow status: completed
│                   │  → Broadcast workflow_completed
│                   │  → Cache results if applicable
│                   │  → Trigger plugin hook: on_workflow_finish
└──────────────────┘
```

### State Machines

```
Workflow States:
PENDING → PLANNED → RUNNING → COMPLETED
                              → FAILED
                              → CANCELLED
                    → PAUSED → RUNNING
                              → CANCELLED

Task States:
CREATED → ASSIGNED → RUNNING → SUCCESS
                               → FAILED (retry → ASSIGNED)
                     → CANCELLED
```

---

## 13. Repository Flow

The repository intelligence pipeline:

```
USER / AI RUNTIME
       │
       │ POST /api/v1/repositories
       │ {path, name}
       ▼
┌──────────────────┐
│  1. REGISTER      │  → Validate path exists
│                   │  → Detect VCS type (git)
│                   │  → Store repository record in DB
│                   │  → Set status: registered
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. SCAN          │  → POST /api/v1/repositories/{id}/scan
│                   │  → Traverse file tree
│                   │  → Respect .gitignore
│                   │  → Detect language per file
│                   │  → Skip binary files (null-byte check)
│                   │  → Compute SHA-256 hash per file
│                   │  → Compare with cached hash
│                   │  → Only process changed files
│                   │  → Store file records
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. INDEX         │  → For each changed file:
│                   │     Select parser by language
│                   │     → Python: AST parser
│                   │     → TS/JS: regex parser
│                   │     → Other: generic regex fallback
│                   │  → Extract symbols:
│                   │     classes, functions, async functions,
│                   │     variables, decorators, annotations,
│                   │     interfaces, types, imports
│                   │  → Store symbol records
│                   │  → Extract imports and references
│                   │  → Update dependency graph
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  4. ANALYZE       │  → Compute code metrics:
│                   │     LOC, complexity, symbol counts
│                   │  → Compute maintainability index
│                   │  → Detect large/complex files
│                   │  → Build knowledge graph
│                   │  → Generate embeddings (optional)
│                   │  → Update repository health
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  5. SEARCH        │  → GET /api/v1/repositories/search
│                   │  → Symbol search (by name/type/lang)
│                   │  → File search (by path/language)
│                   │  → Text search (regex, full content)
│                   │  → Reference search (cross-symbol)
│                   │  → Results ranked by relevance
└──────────────────┘
```

---

## 14. Engineering Flow

The autonomous engineering pipeline:

```
USER GOAL
  │ "Add user authentication to the backend"
  ▼
┌──────────────────┐
│  1. GOAL ANALYZER │  → Classify intent:
│                    │     feature / bug_fix / refactor /
│                    │     update / documentation
│                    │  → Detect risk level:
│                    │     low / medium / high / critical
│                    │  → Determine auto-approval requirement
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. PLANNER       │  → Decompose goal into task chain
│                    │  → Assign roles to tasks
│                    │  → Estimate effort (files affected)
│                    │  → Create implementation plan
│                    │  → Store plan in DB
│                    │  → Broadcast plan_ready
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. VALIDATOR     │  → 7 validation checks:
│                    │     architecture, security, syntax,
│                    │     formatting, lint, types, tests
│                    │  → Record all results
│                    │  → If validation passes, proceed
│                    │  → If not, route to repair
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
  PASS       FAIL
    │         │
    │         ▼
    │    ┌──────────────────┐
    │    │  4. REPAIR        │  → Self-repair loop
    │    │                   │  → Max 3 iterations
    │    │                   │  → Auto-generate fix
    │    │                   │  → Re-run validation
    │    │                   │  → Escalate if persistent
    │    └────────┬─────────┘
    │             │
    │         ┌───┴───┐
    │         │       │
    │       FIXED   FAILED
    │         │       │
    │         │       └──→ Report failure
    │         │
    └─────────┘
         │
         ▼
┌──────────────────┐
│  5. EXECUTE       │  → Apply patches to files
│                   │  → Track changes in patches table
│                   │  → If git repository, create commits
│                   │  → Broadcast patch_created
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  6. QUALITY GATES │  → 9 gates must pass:
│                    │     architecture_review
│                    │     static_analysis
│                    │     security_review
│                    │     formatting
│                    │     lint
│                    │     type_check
│                    │     unit_tests
│                    │     integration_tests
│                    │     documentation_check
│                    │  → All must pass for completion
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
  PASS       FAIL
    │         │
    │         └──→ Route to repair (self-repair loop)
    │
    ▼
┌──────────────────┐
│  7. DOCUMENTATION │  → Auto-update README
│                   │  → Update CHANGELOG
│                   │  → Update PROJECT_STATE
│                   │  → Update API documentation
│                   │  → Update architecture docs
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  8. APPROVAL      │  → If risk = high/critical:
│                   │     Create approval request
│                   │     Wait for approval/rejection
│                   │  → If risk = low/medium:
│                   │     Auto-approve
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  9. REPORT        │  → Generate engineering report
│                   │  → Record metrics (duration, iterations)
│                   │  → Broadcast workflow_completed
│                   │  → Return final result
└──────────────────┘
```

---

## 15. Studio Flow

The AICluster Studio user flow through workspaces, projects, and tools:

```
USER OPENS STUDIO
       │
       ▼
┌─────────────────────┐
│  Workspace Manager   │  → List workspaces
│                      │  → Select or create workspace
│                      │  → Load layout (saved panel arrangement)
│                      │  → Load preferences (theme, keybindings)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Project Explorer    │  → List projects in workspace
│                      │  → Select project
│                      │  → Load repository view
│                      │  → Load bookmarks
│                      │  → Restore open files/tabs
└──────────┬──────────┘
           │
           ▼
   ┌───────┴───────┐
   │               │
   ▼               ▼
┌──────────┐  ┌──────────┐
│  Editor   │  │ Terminal │
│  Monaco   │  │  CMD     │
│  Code     │  │  PS      │
│  Editing  │  │  Git     │
└──────────┘  └──────────┘
   │               │
   ▼               ▼
┌──────────┐  ┌──────────┐
│ AI Chat  │  │ Workflow │
│ Panel    │  │ Designer │
│ (repo-   │  │ (React   │
│  aware)  │  │  Flow)   │
└──────────┘  └──────────┘
   │               │
   ▼               ▼
┌──────────┐  ┌──────────┐
│ Plugin   │  │ Model    │
│ Center   │  │ Manager  │
└──────────┘  └──────────┘
   │
   ▼
┌──────────┐
│ Settings  │
│ (theme,   │
│  language,│
│  AI,      │
│  cluster) │
└──────────┘
```

### Workspace API Flow

```
GET /api/v1/studio/workspaces  → List all workspaces
POST /api/v1/studio/workspaces → Create workspace {name}
GET /api/v1/studio/workspaces/{id} → Get workspace details
DELETE /api/v1/studio/workspaces/{id} → Delete workspace

POST /api/v1/studio/projects → Create project {workspace_id, name, path}
GET /api/v1/studio/projects → List projects (filter by workspace_id)

POST /api/v1/studio/layout → Save layout {workspace_id, panels, sizes}
GET /api/v1/studio/layout → Load layout (filter by workspace_id)

POST /api/v1/studio/bookmarks → Add bookmark {project_id, path, name}
GET /api/v1/studio/history → Get action history (filter by workspace_id)
POST /api/v1/studio/preferences → Set preference {workspace_id, key, value}
GET /api/v1/studio/preferences/{id} → Get all preferences for workspace
```

---

## 16. Audit Flow

The complete audit event lifecycle from capture to query:

```
EVENT SOURCE                  AUDIT SYSTEM
     │                             │
     │  HTTP REQUEST                │
     │  ──────────────► AuditMiddleware
     │                    │
     │                    ├── Capture: method, URL, status code,
     │                    │   duration, client IP, safe headers
     │                    ├── Mask sensitive headers (auth, cookie, API key)
     │                    ├── Skip sensitive paths (/login, /auth)
     │                    │
     │                    ├── Status ≥ 500 → severity ERROR
     │                    ├── Status ≥ 400 → severity WARNING
     │                    └── Status < 400 → severity INFO
     │                         │
     │                         ├── Create AuditEvent
     │                         ├── Publish to EventBus
     │                         │
     │  INTERNAL EVENT          │
     │  (workflow, worker, etc.)│
     │  ──────────────► EventBus│
     │                    │     │
     │                    ├── All listeners receive event
     │                    │   (AuditService.subscribe)
     │                    │
     │                    ▼
     │              ┌──────────────┐
     │              │ AuditService │
     │              │              │
     │              │ log() /      │
     │              │ log_event()  │
     │              │              │
     │              ├── Validate event fields
     │              ├── Create AuditLog record
     │              ├── DB: INSERT INTO audit_logs
     │              │   (26 columns)
     │              └── Commit
     │
     │  LATER, QUERY              │
     │  ──────────────► GET /api/v1/audit/logs
     │                    │       POST /api/v1/audit/search
     │                    │       GET /api/v1/audit/statistics
     │                    │
     │                    ├── AuditService.search()
     │                    │   Filters: date range, category,
     │                    │   severity, event type, username,
     │                    │   worker/workflow/repository/plugin,
     │                    │   status, full-text
     │                    │
     │                    ├── AuditService.export()
     │                    │   Format: CSV or JSON
     │                    │   Compression: ZIP
     │                    │   Filename: audit_YYYYMMDD_HHMMSS.ext
     │                    │
     │                    ├── AuditService.purge()
     │                    │   Retention: 30/90/180/365 days or forever
     │                    │   Auto-purge background task
     │                    │
     │                    └── AuditService.get_statistics()
     │                        Total, today, this week
     │                        Critical/error/warning counts
     │                        Success rate, by category, by severity
```

### Audit Database Tables

```
audit_logs (26 columns):
  id, timestamp, event_type, category, severity,
  user_id, username, worker_id, workflow_id,
  repository_id, plugin_id, agent_id, session_id,
  ip_address, hostname, resource_type, resource_id,
  action, status, duration_ms, message,
  extra (JSON), old_value (JSON), new_value (JSON),
  request_id, trace_id, created_at

audit_settings:
  id, retention_days, auto_purge_enabled,
  export_format, max_log_size_mb, notification_on_critical

audit_exports:
  id, format, filename, size_bytes, status, filters (JSON), record_count, created_at

audit_retention:
  id, purged_before, records_purged, status, created_at
```

---

## 17. Release Flow

The complete build and release pipeline:

```
DEVELOPER TRIGGER
       │
       │ python -m build.build [--clean] [--sign]
       ▼
┌──────────────────────┐
│  1. ENVIRONMENT       │  Verify:
│     VERIFICATION      │  ✔ Python 3.12+ available
│                       │  ✔ Node.js 20+ available
│                       │  ✔ npm available
│                       │  ✔ Rust 1.70+ available (if not --skip-tauri)
│                       │  ✔ Tauri CLI 2.0+ available
│                       │  ✔ PyInstaller installed
│                       │  ✔ Inno Setup 6+ available (if not --skip-installer)
│                       │  ✔ 7-Zip available
│                       │  ✔ signtool available (if --sign)
│                       │  → Report PASS/FAIL/WARN for each
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  2. CLEAN             │  (if --clean)
│                       │  Remove release/, dist/ from all targets
│                       │  Remove temp/ build artifacts
│                       │  Remove old log files
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  3. BUILD FRONTENDS   │  For each frontend:
│                       │  ✔ frontend/ → npm run build → .next/
│                       │  ✔ master-control-center/ → npm run build
│                       │  ✔ worker-control-center/ → npm run build
│                       │  ✔ studio/ → npm run build (tsc -b && vite build)
│                       │  → Zero errors required
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  4. BUILD PYINSTALLER │  For each target:
│                       │  master → AIClusterMaster.exe
│                       │  worker → AIClusterWorker.exe
│                       │  cli    → aicluster.exe
│                       │
│                       │  Steps per target:
│                       │  ✔ Write VSVersionInfo file
│                       │  ✔ Generate .spec or --collect-all args
│                       │  ✔ Run pyinstaller <spec> or pyinstaller <args>
│                       │  ✔ Real PE verification (MZ + PE headers)
│                       │  ✔ Publish to release/<subdir>/
│                       │  → Any failure aborts entire build
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  5. BUILD TAURI       │  For each target:
│                       │  master-control → MasterControlCenter.exe
│                       │  worker-control → WorkerControlCenter.exe
│                       │  studio → AIClusterStudio.exe
│                       │
│                       │  Steps per target:
│                       │  ✔ cd frontend && npm run tauri build
│                       │  ✔ Copy .exe from src-tauri/target/release/
│                       │  ✔ Publish to release/<subdir>/
│                       │  → Any failure aborts entire build
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  6. SIGN              │  (if --sign and certificate configured)
│                       │  For every built .exe:
│                       │  ✔ signtool sign /fd SHA256 /a
│                       │  ✔ Verify signature
│                       │  → Non-fatal if signing fails
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  7. PRE-INSTALLER     │  Verify every required .exe:
│     GATE              │  ✔ release/master/AIClusterMaster.exe
│                       │  ✔ release/worker/AIClusterWorker.exe
│                       │  ✔ release/cli/aicluster.exe
│                       │  ✔ release/master-control/MasterControlCenter.exe
│                       │  ✔ release/worker-control/WorkerControlCenter.exe
│                       │  ✔ release/studio/AIClusterStudio.exe
│                       │  → Each must be a real PE binary
│                       │  → Any FAIL aborts before installer
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  8. PACKAGE           │  ✔ Create portable ZIPs per component
│                       │  ✔ Generate SHA-256 checksums
│                       │  ✔ Create release manifest (JSON)
│                       │  ✔ Copy to artifacts/ directory
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  9. INSTALLER         │  ✔ Generate Inno Setup .iss script
│                       │  ✔ Populate payload directory
│                       │  ✔ Compile AIClusterSetup.exe
│                       │  ✔ Generate NSIS fallback installer
│                       │  ✔ Verify installer authenticity
│                       │  ✔ Copy to artifacts/AIClusterSetup-{version}.exe
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 10. FINAL VERIFY      │  ✔ Verify artifact integrity
│                       │  ✔ Verify checksums match
│                       │  ✔ Verify installer runs
│                       │  ✔ Verify all .exe sizes are reasonable
│                       │  → Generate final verification report
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 11. RELEASE VERIFY    │  Run comprehensive verification suite:
│                       │  ✔ verify_build.py — build artifacts
│                       │  ✔ verify_backend.py — backend startup
│                       │  ✔ verify_frontend.py — frontend build
│                       │  ✔ verify_api.py — API endpoint health
│                       │  ✔ verify_executables.py — PE validation
│                       │  ✔ verify_installer.py — installer smoke test
│                       │  ✔ verify_checksums.py — hash verification
│                       │  ✔ verify_artifacts.py — artifact integrity
│                       │  ✔ verify_config.py — config validation
│                       │  ✔ verify_python.py — Python env check
│                       │  → Overall: PASS / FAIL
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 12. REPORT            │  ✔ Generate build report (Markdown)
│                       │  ✔ Generate RELEASE_NOTES.md
│                       │  ✔ Print summary:
│                       │     Duration, warnings count, errors count
│                       │     Signed files, release manifest path
│                       │  → Exit code 0 (success) or 1 (failure)
└──────────────────────┘
```

---

## 18. Dependency Graph

The following diagram shows subsystem relationships. An arrow A → B means "A depends on B" or "A uses B."

```
                        ┌──────────────────┐
                        │  Web Frontend    │
                        │  (Next.js 15)    │
                        └────────┬─────────┘
                                 │ REST + WebSocket
                                 ▼
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│  Master CC   │◄──────►│  Master Server   │◄──────►│  Worker CC   │
│  (Tauri v2)  │  HTTP  │  (FastAPI)       │  HTTP  │  (Tauri v2)  │
└──────────────┘        └────────┬─────────┘        └──────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  AICluster       │
                        │  Studio (Tauri)  │
                        └────────┬─────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│  Worker      │        │  Plugin System   │        │  Audit       │
│  Service     │        │  (SDK + Hooks)   │        │  System      │
│  (httpx/     │        └────────┬─────────┘        └──────┬───────┘
│   psutil)    │                 │                         │
└──────────────┘                 │                         │
                                 │                         │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│  Workflow    │        │  Engineering     │        │  Repository  │
│  Engine      │◄──────►│  Engine          │◄──────►│  Intelligence│
│  (DAG-based) │        │  (Auto SWE)      │        │  (Symbols)   │
└──────┬───────┘        └────────┬─────────┘        └──────┬───────┘
       │                         │                         │
       ▼                         ▼                         │
┌──────────────┐        ┌──────────────────┐               │
│  Multi-Agent │◄──────►│  AI Runtime      │◄──────────────┘
│  Engine      │        │  (Ollama/Llama/  │
│  (12 Agents) │        │   OpenAI)        │
└──────────────┘        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  LLM Providers   │
                        │  (3 backends)    │
                        └──────────────────┘

   DEPENDENCY KEY:
   ─────────────────────────────────────────────────────
   Master Server          → Worker Service, Web Frontend, All Engines
   Worker Service         → Master Server (HTTP)
   Workflow Engine        → Worker Service, AI Runtime, Repository
   Repository Intelligence → File System, Database
   AI Runtime             → Repository Intelligence, LLM Providers
   Multi-Agent Engine     → AI Runtime, Workflow Engine
   Engineering Engine     → AI Runtime, Repository Intelligence
   Plugin System          → Master Server, All Engines
   Audit System           → Master Server, All Engines
   AICluster Studio       → Master Server, Repository Intelligence, AI Runtime
   Build System           → All Components (build-time only)
   CLI                    → Master Server (HTTP)
```

---

## 19. API Surface Summary

The total API surface covers **135+ REST endpoints** across all subsystems:

| Subsystem | Endpoints | Prefix |
|-----------|-----------|--------|
| Auth | 2 | `/api/v1/auth/` |
| Workers | 9 | `/api/v1/workers/` |
| Jobs | 3 | `/api/v1/jobs/` |
| Dashboard | 1 | `/api/v1/dashboard/` |
| Health | 1 | `/api/v1/health/` |
| Logs | 1 | `/api/v1/logs/` |
| Workflows | 13 | `/api/v1/workflow/` |
| Repositories | 14 | `/api/v1/repositories/` |
| AI Runtime | 16 | `/api/v1/ai/` |
| Multi-Agent | 14 | `/api/v1/agents/` |
| Engineering | 10 | `/api/v1/engineering/` |
| Plugins | 8 | `/api/v1/plugins/` |
| Production | 8 | `/api/v1/production/` |
| Studio | 11 | `/api/v1/studio/` |
| Audit | 9 | `/api/v1/audit/` |
| WebSocket | 1 | `/ws` |
| Docs | 2 | `/docs`, `/redoc` |

---

## 20. Database Schema Overview

The SQLite database contains **60+ tables** across all subsystems:

| Subsystem | Tables | Count |
|-----------|--------|-------|
| Core | workers, jobs, system_logs, users | 4 |
| Workflow | workflows, workflow_tasks, task_dependencies, workflow_results, artifacts, execution_metrics, cache, workflow_events, worker_capabilities | 9 |
| Repository | repositories, repository_files, symbols, symbol_imports, symbol_references, dependency_edges, code_metrics, knowledge_nodes, knowledge_edges, repository_cache, repository_events | 11 |
| AI Runtime | ai_models, ai_sessions, ai_messages, prompt_templates, tool_definitions, tool_calls, ai_memory, ai_provider_config, runtime_metrics | 9 |
| Multi-Agent | agents, agent_tasks, agent_messages, agent_reviews, agent_merges, agent_memory_store, agent_metrics | 7 |
| Engineering | engineering_plans, engineering_tasks, engineering_patches, engineering_validations, engineering_repairs, engineering_quality, engineering_approvals, engineering_metrics, engineering_reports | 9 |
| Studio | studio_workspaces, studio_projects, studio_layouts, studio_bookmarks, studio_preferences, studio_history | 6 |
| Audit | audit_logs, audit_settings, audit_exports, audit_retention | 4 |
| **Total** | | **~59** |

---

*This document is a living architectural reference for the AICluster project. It should be updated whenever significant architectural changes are made.*
