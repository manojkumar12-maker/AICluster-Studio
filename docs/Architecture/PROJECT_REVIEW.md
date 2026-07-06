# AICluster â€” Comprehensive Project Review & Architecture Document

**Version:** 1.2.1  
**Status:** Production Release (v1.2.1 â€” Master Audit System)  
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

AICluster is an **offline-first AI cluster management platform** that turns idle Windows PCs on a local area network into a unified, intelligent compute cluster. It distributes AI workloads â€” code generation, repository analysis, multi-agent software engineering, and general-purpose compute tasks â€” across worker machines with strict resource limits (25% CPU, 8 GB RAM) to ensure office workers never experience performance degradation.

The platform is delivered as a suite of applications:

- **AICluster Master** (FastAPI backend + SQLite + WebSocket) â€” the central orchestrator
- **AICluster Worker** (FastAPI agent) â€” runs on each worker PC
- **Web Dashboard** (Next.js 15) â€” browser-based cluster management
- **Master Control Center** (Tauri v2 desktop app) â€” master PC cluster management
- **Worker Control Center** (Tauri v2 desktop app) â€” worker PC status and control
- **AICluster Studio** (Tauri v2 desktop app) â€” visual IDE for project management
- **AICluster CLI** (command-line tool) â€” headless cluster interaction
- **AIClusterSetup.exe** (single-file Inno Setup installer) â€” one-click installation

---

## 2. Why It Exists

Modern AI development increasingly requires substantial compute resources. Cloud-based solutions introduce data privacy concerns, recurring costs, internet dependency, and latency. Many organizations have dozens of Windows workstations sitting idle for large portions of the day. AICluster exists to:

- **Eliminate cloud dependency** â€” all compute happens on the local LAN, fully offline after initial setup
- **Monetize idle hardware** â€” office workstations with modern CPUs (Intel Core Ultra 7, etc.) are used during idle periods
- **Enable private AI** â€” sensitive codebases never leave the network
- **Provide distributed intelligence** â€” AI code analysis, repository understanding, multi-agent software engineering, all running on local hardware
- **Lower the barrier to entry** â€” one-click installers, PowerShell setup scripts, no DevOps knowledge required
- **Scale horizontally** â€” add workers by running the installer on any Windows PC; the master auto-discovers them

---

## 3. Who Should Use It

| Role | Use Case |
|------|----------|
| **Software Engineers** | Distributed code analysis, automated refactoring, test generation, documentation |
| **AI/ML Engineers** | Private LLM inference using local models via Ollama/llama.cpp/OpenAI-compatible endpoints |
| **DevOps / IT** | Cluster management, health monitoring, backup/restore, maintenance |
| **Technical Teams** | Multi-agent software engineering â€” decompose features into parallel agent tasks |
| **Small-to-Medium Businesses** | Private AI compute without cloud subscriptions or data leaving the network |
| **Educational Institutions** | Teach distributed computing concepts on existing lab hardware |

---

## 4. Architecture Overview

AICluster follows a **master-worker** topology. A single master PC runs the FastAPI backend, SQLite database, web frontend, and optional desktop control center. One or more worker PCs register with the master, send heartbeats, and execute assigned jobs.

```
                          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                          â”‚           MASTER PC                 â”‚
                          â”‚                                     â”‚
                          â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
                          â”‚  â”‚  Web Frontend                â”‚   â”‚
                          â”‚  â”‚  Next.js 15 / React 18 / TS  â”‚   â”‚
                          â”‚  â”‚  Port 3000                   â”‚   â”‚
                          â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
                          â”‚             â”‚ REST + WebSocket       â”‚
                          â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
                          â”‚  â”‚  FastAPI Backend (Port 8000)  â”‚   â”‚
                          â”‚  â”‚                               â”‚   â”‚
                          â”‚  â”‚  API Layer    WebSocket /ws   â”‚   â”‚
                          â”‚  â”‚  Services    Background Tasks â”‚   â”‚
                          â”‚  â”‚  SQLAlchemy  SQLite (aiosqlite)â”‚  â”‚
                          â”‚  â”‚  Audit       Plugins          â”‚   â”‚
                          â”‚  â”‚  Repository  AI Runtime       â”‚   â”‚
                          â”‚  â”‚  Workflow    Multi-Agent      â”‚   â”‚
                          â”‚  â”‚  Engineering Production       â”‚   â”‚
                          â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
                          â”‚                                     â”‚
                          â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
                          â”‚  â”‚  Master Control Center       â”‚   â”‚
                          â”‚  â”‚  Tauri v2 Desktop App        â”‚   â”‚
                          â”‚  â”‚  Port 8800 (backend)         â”‚   â”‚
                          â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
                          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                         â”‚ HTTP (port 8000)
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚                          â”‚                          â”‚
     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”
     â”‚   WORKER PC 1   â”‚       â”‚   WORKER PC 2   â”‚       â”‚   WORKER PC N   â”‚
     â”‚   Ultra 7        â”‚       â”‚   Ultra 7        â”‚       â”‚   Ultra 7        â”‚
     â”‚   Port 8001      â”‚       â”‚   Port 8001      â”‚       â”‚   Port 8001      â”‚
     â”‚                  â”‚       â”‚                  â”‚       â”‚                  â”‚
     â”‚  FastAPI Worker  â”‚       â”‚  FastAPI Worker  â”‚       â”‚  FastAPI Worker  â”‚
     â”‚  psutil Monitor  â”‚       â”‚  psutil Monitor  â”‚       â”‚  psutil Monitor  â”‚
     â”‚  25% CPU limit   â”‚       â”‚  25% CPU limit   â”‚       â”‚  25% CPU limit   â”‚
     â”‚  8 GB RAM limit  â”‚       â”‚  8 GB RAM limit  â”‚       â”‚  8 GB RAM limit  â”‚
     â”‚                  â”‚       â”‚                  â”‚       â”‚                  â”‚
     â”‚  Worker Control  â”‚       â”‚  Worker Control  â”‚       â”‚  Worker Control  â”‚
     â”‚  Center (Tauri)  â”‚       â”‚  Center (Tauri)  â”‚       â”‚  Center (Tauri)  â”‚
     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚       AICluster Studio              â”‚
              â”‚  Tauri v2 Desktop App               â”‚
              â”‚  Visual IDE & Workspace Manager     â”‚
              â”‚  Monaco Editor, Terminal, AI Chat   â”‚
              â”‚  Workflow Designer, Agent Designer  â”‚
              â”‚  Repository Viewer, Plugin Center   â”‚
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Component Layering

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     Presentation Layer                       â”‚
â”‚  Next.js 15 Web App  Â·  Tauri v2 Desktop Apps  Â·  CLI      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                      API Layer                               â”‚
â”‚  REST: /api/v1/*  Â·  WebSocket: /ws  Â·  WebDAV: /static    â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                    Service Layer                             â”‚
â”‚  WorkerManager Â· Scheduler Â· AuthService Â· LogService       â”‚
â”‚  AuditService Â· PluginRegistry Â· EngineeringService         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                    Domain Engines                            â”‚
â”‚  Workflow Â· Repository Â· AI Runtime Â· Multi-Agent           â”‚
â”‚  Engineering Â· Production Â· Studio                           â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                 Data Access Layer                            â”‚
â”‚  SQLAlchemy AsyncSession Â· Alembic Migrations               â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                    Storage Layer                             â”‚
â”‚  SQLite (aiosqlite) Â· File System Â· Artifact Store          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SQLite** | Zero-config, no server process. Suitable for LAN-scale (100 workers, 1000s of jobs). Migratable to PostgreSQL via SQLAlchemy. |
| **Async everywhere** | FastAPI + async SQLAlchemy + asyncio. Single process handles all connections via async I/O. |
| **Polling + WebSocket** | Frontend uses 2s React Query polling. WebSocket adds real-time broadcasts for status changes. |
| **15-second offline timeout** | Workers missing 3 consecutive heartbeats (5 s Ã— 3) are marked offline. Configurable. |
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
- 15-second heartbeat timeout â†’ automatic offline marking
- Priority-based job scheduling (1â€“5)
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
STARTING â†’ LOADING_CONFIG â†’ CONNECTING â†’ REGISTERING â†’ ONLINE
                                                              â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚
        HEARTBEAT â†’ POLL_JOB â†’ HAS_JOB â†’ EXECUTING â†’ REPORT_PROGRESS
              â”‚                  â”‚                           â”‚
              â”‚                  â””â”€â”€ NO_JOB                  â”‚
              â”‚                                              â”‚
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ REPORT_RESULT â†â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                        â”‚
                                   SHUTDOWN â†’ EXIT
                                        â†‘
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
| `executor/` | Workflow orchestration â€” create, plan, dispatch, execute, retry, cancel |
| `artifacts/` | File-based artifact storage with SHA-256 checksums |
| `cache/` | TTL-based result caching keyed by workflow/task/input hash |
| `metrics/` | Execution metrics recording, queue stats, worker utilization |
| `state/` | State machine definitions (Workflow: PENDINGâ†’COMPLETED/FAILED, Task: CREATEDâ†’SUCCESS/CANCELLED) |
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
| `parser/` | Symbol extraction â€” Python AST parser, TypeScript/JS regex parser, generic fallback |
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
- `fast` â€” low max_tokens, high temperature
- `balanced` â€” moderate values
- `maximum_quality` â€” high max_tokens, low temperature
- `offline_low_ram` â€” minimized memory footprint
- `custom` â€” user-configurable

**Fallback Chain:** Preferred provider â†’ alternate provider â†’ any loaded provider â†’ clear error message

### 5.6 Multi-Agent Engine

The multi-agent engine orchestrates collaborative AI agents to solve complex software engineering tasks.

**Location:** `backend/app/agents/`

**Submodules:**

| Module | Responsibility |
|--------|----------------|
| `registry/` | Agent registration with role, capabilities, permissions, model preference |
| `planner/` | Task decomposition by request type, creates execution DAG |
| `orchestrator/` | Central coordinator â€” receives request, plans, assigns, monitors, triggers review |
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

The engineering engine provides autonomous software engineering capabilities â€” goal analysis, planning, validation, repair, quality gating, and documentation.

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
User Goal â†’ Goal Analyzer (risk/type) â†’ Planner (tasks/files)
  â†’ Validate (7 checks) â†’ Execute (patch) â†’ Quality Gates (9 checks)
  â†’ Self-Repair (max 3 iterations) â†’ Documentation â†’ Report
```

### 5.8 Audit System

The audit system provides comprehensive event logging, search, export, retention management, and middleware-based HTTP request capture.

**Location:** `backend/app/audit/`

**Modules:**

| Module | File | Responsibility |
|--------|------|----------------|
| Service | `service.py` | Core `AuditService` â€” log(), search(), export(), purge(), statistics(), settings management |
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
| `hooks/` | Hook registry â€” register callbacks for 15 platform hooks |
| `sdk/` | Plugin API â€” logger, config, database, workflow/repository/AI/agent APIs |
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
Install â†’ Validate â†’ Load â†’ Initialize â†’ Register Hooks â†’ Run â†’ Pause â†’ Resume â†’ Unload â†’ Uninstall

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

**Location:** `build/modules/cli_entry.py` â†’ produces `aicluster.exe`

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
- `AIClusterRuntime.exe --mode master` â€” Master Server (FastAPI + all subsystems)
- `AIClusterRuntime.exe --mode worker` â€” Worker Service (FastAPI agent)
- `aicluster.exe` â€” CLI tool

**Tauri Targets:**
- `MasterControlCenter.exe` â€” Desktop cluster management
- `WorkerControlCenter.exe` â€” Desktop worker management
- `AIClusterStudio.exe` â€” Visual IDE

---

## 6. Folder Layout

```
AICluster/
â”‚
â”œâ”€â”€ README.md                     # Project overview and quick start
â”œâ”€â”€ VISION.md                     # North star vision document
â”œâ”€â”€ PROJECT_STATE.md              # Current state, completion, known issues
â”œâ”€â”€ CHANGELOG.md                  # Full version history (v0.1.0 â†’ v1.2.1)
â”œâ”€â”€ RESUME.md                     # Development resume point
â”œâ”€â”€ NEXT_PHASE.md                 # Next development phase specification
â”œâ”€â”€ TODO.md                       # Task list
â”œâ”€â”€ TEST_REPORT.md                # Test results summary
â”œâ”€â”€ VERSION                       # Current version string ("1.2.1")
â”‚
â”œâ”€â”€ backend/                      # FastAPI master server
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ main.py               # FastAPI entry point, lifespan, WebSocket
â”‚   â”‚   â”œâ”€â”€ config.py             # Pydantic settings from .env
â”‚   â”‚   â”œâ”€â”€ database.py           # Async SQLAlchemy engine + session
â”‚   â”‚   â”œâ”€â”€ logging_config.py     # Rotating file handler config
â”‚   â”‚   â”œâ”€â”€ api/v1/               # REST API route handlers
â”‚   â”‚   â”‚   â”œâ”€â”€ auth.py           # Login, JWT
â”‚   â”‚   â”‚   â”œâ”€â”€ workers.py        # Register, heartbeat, CRUD
â”‚   â”‚   â”‚   â”œâ”€â”€ jobs.py           # Create, list, cancel
â”‚   â”‚   â”‚   â”œâ”€â”€ dashboard.py      # Cluster metrics
â”‚   â”‚   â”‚   â”œâ”€â”€ health.py         # Health check
â”‚   â”‚   â”‚   â”œâ”€â”€ logs.py           # System log queries
â”‚   â”‚   â”‚   â”œâ”€â”€ workflows.py      # Workflow CRUD and execution
â”‚   â”‚   â”‚   â”œâ”€â”€ repositories.py   # Repository management
â”‚   â”‚   â”‚   â”œâ”€â”€ ai.py             # AI chat and completion
â”‚   â”‚   â”‚   â”œâ”€â”€ agents.py         # Agent orchestration
â”‚   â”‚   â”‚   â”œâ”€â”€ engineering.py    # Autonomous engineering
â”‚   â”‚   â”‚   â”œâ”€â”€ plugins.py        # Plugin lifecycle
â”‚   â”‚   â”‚   â”œâ”€â”€ production.py     # Monitoring, health, diagnostics
â”‚   â”‚   â”‚   â””â”€â”€ studio/           # Studio workspace/project APIs
â”‚   â”‚   â”œâ”€â”€ models/               # SQLAlchemy ORM models
â”‚   â”‚   â”‚   â”œâ”€â”€ worker.py         # Worker node
â”‚   â”‚   â”‚   â”œâ”€â”€ job.py            # Job queue
â”‚   â”‚   â”‚   â”œâ”€â”€ log.py            # System log
â”‚   â”‚   â”‚   â”œâ”€â”€ user.py           # Auth user
â”‚   â”‚   â”‚   â”œâ”€â”€ workflow.py       # Workflow engine (9 tables)
â”‚   â”‚   â”‚   â”œâ”€â”€ repository.py     # Repository intelligence (18 tables)
â”‚   â”‚   â”‚   â”œâ”€â”€ ai.py             # AI runtime (16 tables)
â”‚   â”‚   â”‚   â”œâ”€â”€ agent.py          # Multi-agent (10 tables)
â”‚   â”‚   â”‚   â”œâ”€â”€ engineering.py    # Engineering engine (10 tables)
â”‚   â”‚   â”‚   â””â”€â”€ studio.py         # Studio workspace (6 tables)
â”‚   â”‚   â”œâ”€â”€ schemas/              # Pydantic request/response schemas
â”‚   â”‚   â”œâ”€â”€ services/             # Business logic
â”‚   â”‚   â”‚   â”œâ”€â”€ worker_manager.py # Registration, heartbeat, offline
â”‚   â”‚   â”‚   â”œâ”€â”€ scheduler.py      # Job queue, assignment, retry
â”‚   â”‚   â”‚   â”œâ”€â”€ auth.py           # JWT, bcrypt, admin seeding
â”‚   â”‚   â”‚   â””â”€â”€ log_service.py    # Structured database logging
â”‚   â”‚   â”œâ”€â”€ websocket/            # WebSocket manager
â”‚   â”‚   â”œâ”€â”€ workflow/             # DAG-based workflow engine
â”‚   â”‚   â”œâ”€â”€ repository/           # Code intelligence engine
â”‚   â”‚   â”œâ”€â”€ ai/                   # AI runtime + LLM providers
â”‚   â”‚   â”œâ”€â”€ agents/               # Multi-agent orchestration
â”‚   â”‚   â”œâ”€â”€ engineering/          # Autonomous engineering engine
â”‚   â”‚   â”œâ”€â”€ audit/                # Audit event system
â”‚   â”‚   â”œâ”€â”€ plugins/              # Plugin SDK and registry
â”‚   â”‚   â””â”€â”€ production/           # Monitoring, health, diagnostics
â”‚   â”œâ”€â”€ tests/                    # pytest test suite (44+ tests)
â”‚   â”œâ”€â”€ alembic/                  # Database migrations (installed, configured)
â”‚   â”œâ”€â”€ data/                     # SQLite database file location
â”‚   â”œâ”€â”€ logs/                     # Backend log files
â”‚   â”œâ”€â”€ requirements.txt          # Python dependencies
â”‚   â””â”€â”€ pyproject.toml            # Project metadata
â”‚
â”œâ”€â”€ frontend/                     # Next.js 15 web dashboard
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ app/                  # Pages (App Router)
â”‚   â”‚   â”œâ”€â”€ components/           # React components (shadcn/ui)
â”‚   â”‚   â”œâ”€â”€ lib/                  # Utility functions
â”‚   â”‚   â”œâ”€â”€ stores/               # Zustand stores
â”‚   â”‚   â”œâ”€â”€ types/                # TypeScript type definitions
â”‚   â”‚   â””â”€â”€ styles/               # Global styles
â”‚   â”œâ”€â”€ public/                   # Static assets
â”‚   â””â”€â”€ package.json              # Node dependencies
â”‚
â”œâ”€â”€ worker/                       # Worker agent service
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ main.py               # FastAPI entry with worker lifecycle
â”‚   â”‚   â”œâ”€â”€ config.py             # Three-tier configuration
â”‚   â”‚   â”œâ”€â”€ core/                 # State machine, constants
â”‚   â”‚   â”œâ”€â”€ services/             # Registrar, heartbeat, poller, reporter, executor, monitor
â”‚   â”‚   â”œâ”€â”€ executor/             # Job handler framework + 5 handlers
â”‚   â”‚   â””â”€â”€ utils/                # HTTP client, retry handler
â”‚   â”œâ”€â”€ tests/                    # 14 worker unit tests
â”‚   â”œâ”€â”€ scripts/                  # Worker runner
â”‚   â””â”€â”€ pyproject.toml
â”‚
â”œâ”€â”€ master-control-center/        # Tauri desktop app for master management
â”‚   â”œâ”€â”€ frontend/                 # React + Vite + TailwindCSS
â”‚   â”‚   â”œâ”€â”€ src/                  # Pages (11 pages)
â”‚   â”‚   â””â”€â”€ src-tauri/            # Tauri v2 Rust shell
â”‚   â””â”€â”€ backend/                  # FastAPI helper service (port 8800)
â”‚       â””â”€â”€ app/
â”‚           â”œâ”€â”€ main.py           # Entry point
â”‚           â””â”€â”€ api/router.py     # Cluster management endpoints
â”‚
â”œâ”€â”€ worker-control-center/        # Tauri desktop app for worker management
â”‚   â”œâ”€â”€ frontend/                 # React + Vite + TailwindCSS
â”‚   â”‚   â””â”€â”€ src-tauri/            # Tauri v2 Rust shell
â”‚   â””â”€â”€ backend/                  # FastAPI helper service
â”‚       â””â”€â”€ app/
â”‚           â”œâ”€â”€ main.py
â”‚           â””â”€â”€ api/router.py
â”‚
â”œâ”€â”€ studio/                       # AICluster Studio (visual IDE)
â”‚   â”œâ”€â”€ src/                      # React + Vite + TailwindCSS 4
â”‚   â”œâ”€â”€ src-tauri/                # Tauri v2 Rust shell
â”‚   â””â”€â”€ package.json
â”‚
â”œâ”€â”€ shared/                       # Shared code across components
â”‚   â”œâ”€â”€ protocol/                 # Python protocol definitions
â”‚   â”‚   â”œâ”€â”€ registration.py       # RegisterRequest/Response
â”‚   â”‚   â”œâ”€â”€ heartbeat.py          # HeartbeatRequest/Response
â”‚   â”‚   â”œâ”€â”€ jobs.py               # NextJob, Progress, Result
â”‚   â”‚   â””â”€â”€ errors.py             # ErrorResponse
â”‚   â”œâ”€â”€ py/                       # Shared Python modules
â”‚   â”‚   â”œâ”€â”€ models.py             # Shared data models
â”‚   â”‚   â””â”€â”€ schemas.py            # Shared Pydantic schemas
â”‚   â””â”€â”€ ts/                       # Shared TypeScript types
â”‚       â”œâ”€â”€ types.ts              # Enums and interfaces
â”‚       â””â”€â”€ index.ts              # Re-exports
â”‚
â”œâ”€â”€ plugins/                      # Plugin packages
â”‚   â””â”€â”€ example-metrics-reporter/ # Reference plugin implementation
â”‚       â”œâ”€â”€ plugin.json           # Manifest (id, version, hooks, permissions)
â”‚       â””â”€â”€ main.py               # Plugin class with on_workflow_finish hook
â”‚
â”œâ”€â”€ build/                        # Build system (Python orchestrator)
â”‚   â”œâ”€â”€ build.py                  # Master build orchestrator
â”‚   â”œâ”€â”€ config.py                 # Build config, PyInstaller/Tauri target definitions
â”‚   â”œâ”€â”€ version.py                # Version resolution
â”‚   â”œâ”€â”€ frontend.py               # Frontend build runner
â”‚   â”œâ”€â”€ pyinstaller_builder.py    # PyInstaller spec generation + execution
â”‚   â”œâ”€â”€ tauri_builder.py          # Tauri build runner
â”‚   â”œâ”€â”€ package.py                # Release packaging, ZIPs, checksums
â”‚   â”œâ”€â”€ release.py                # Installer generation + release notes
â”‚   â”œâ”€â”€ sign.py                   # Authenticode code signing
â”‚   â”œâ”€â”€ checksum.py               # SHA-256 checksum generation
â”‚   â”œâ”€â”€ clean.py                  # Build artifact cleanup
â”‚   â”œâ”€â”€ verify.py                 # Build verification
â”‚   â”œâ”€â”€ setup_builder.py          # Inno Setup script generation + compilation
â”‚   â”œâ”€â”€ setup_validator.py        # Installer validation
â”‚   â”œâ”€â”€ modules/                  # Entry scripts for PyInstaller
â”‚   â”‚   â”œâ”€â”€ master_entry.py       # Master executable entry point
â”‚   â”‚   â”œâ”€â”€ worker_entry.py       # Worker executable entry point
â”‚   â”‚   â”œâ”€â”€ cli_entry.py          # CLI executable entry point
â”‚   â”‚   â””â”€â”€ make_default_icon.py  # Default icon generator
â”‚   â”œâ”€â”€ setup/                    # Installer assets and scripts
â”‚   â”‚   â”œâ”€â”€ setup.iss             # Inno Setup script
â”‚   â”‚   â”œâ”€â”€ payload/              # Installer payload directory
â”‚   â”‚   â”œâ”€â”€ config/               # Installer configuration
â”‚   â”‚   â””â”€â”€ assets/               # Installer assets
â”‚   â””â”€â”€ verification/             # Post-build release verification
â”‚       â”œâ”€â”€ verify.py             # Verification orchestrator
â”‚       â”œâ”€â”€ verify_build.py       # Build artifact verification
â”‚       â”œâ”€â”€ verify_backend.py     # Backend health verification
â”‚       â”œâ”€â”€ verify_frontend.py    # Frontend build verification
â”‚       â”œâ”€â”€ verify_api.py         # API endpoint verification
â”‚       â”œâ”€â”€ verify_executables.py # PE binary verification
â”‚       â”œâ”€â”€ verify_installer.py   # Installer verification
â”‚       â”œâ”€â”€ verify_checksums.py   # Checksum verification
â”‚       â”œâ”€â”€ verify_artifacts.py   # Artifact integrity verification
â”‚       â”œâ”€â”€ verify_config.py      # Configuration verification
â”‚       â”œâ”€â”€ verify_report.py      # Report generation
â”‚       â”œâ”€â”€ verify_python.py      # Python environment verification
â”‚       â””â”€â”€ context.py            # Verifier context
â”‚
â”œâ”€â”€ config/                       # YAML configuration files
â”‚   â”œâ”€â”€ default.yaml              # Default configuration
â”‚   â”œâ”€â”€ development.yaml          # Development overrides
â”‚   â””â”€â”€ production.yaml           # Production overrides
â”‚
â”œâ”€â”€ docs/                         # Documentation
â”‚   â”œâ”€â”€ architecture.md           # Architecture document
â”‚   â”œâ”€â”€ API_REFERENCE.md          # API endpoint reference
â”‚   â”œâ”€â”€ DATABASE.md               # Database schema documentation
â”‚   â”œâ”€â”€ release-checklist.md      # Release verification checklist
â”‚   â””â”€â”€ phase-*-validation-report.md  # Phase validation reports
â”‚
â”œâ”€â”€ scripts/                      # Utility scripts
â”‚   â”œâ”€â”€ setup.ps1                 # Environment setup (venv, npm install)
â”‚   â”œâ”€â”€ start-master.ps1          # Start master server
â”‚   â”œâ”€â”€ start-worker.ps1          # Start worker agent
â”‚   â”œâ”€â”€ install-master.ps1        # One-click master installation
â”‚   â”œâ”€â”€ install-worker.ps1        # One-click worker installation
â”‚   â”œâ”€â”€ run-integration-test.py   # 40 end-to-end integration tests
â”‚   â””â”€â”€ worker-simulator.py       # TUI worker simulator (4 workers)
â”‚
â”œâ”€â”€ assets/                       # Static assets
â”‚   â”œâ”€â”€ icons/                    # Application icons (ICO, PNG)
â”‚   â”œâ”€â”€ manifest.json             # Asset manifest
â”‚   â””â”€â”€ README.md
â”‚
â”œâ”€â”€ data/                         # Runtime data directory
â”œâ”€â”€ models/                       # Local LLM model storage
â”œâ”€â”€ logs/                         # Application logs directory
â”‚   â”œâ”€â”€ aicluster.log
â”‚   â”œâ”€â”€ master.log
â”‚   â”œâ”€â”€ worker.log
â”‚   â”œâ”€â”€ build.log
â”‚   â””â”€â”€ verification.log
â”‚
â”œâ”€â”€ artifacts/                    # Build artifacts
â”‚   â””â”€â”€ AIClusterSetup-1.2.1.exe # Single-file installer
â”‚
â”œâ”€â”€ release/                      # Release output directory
â”‚   â”œâ”€â”€ master/                   # AIClusterRuntime.exe --mode master + support files
â”‚   â”œâ”€â”€ worker/                   # AIClusterRuntime.exe --mode worker + support files
â”‚   â”œâ”€â”€ cli/                      # aicluster.exe
â”‚   â”œâ”€â”€ master-control/           # MasterControlCenter.exe
â”‚   â”œâ”€â”€ worker-control/           # WorkerControlCenter.exe
â”‚   â”œâ”€â”€ studio/                   # AIClusterStudio.exe
â”‚   â””â”€â”€ ...                       # ZIPs, checksums, reports
â”‚
â”œâ”€â”€ checksums/                    # Checksum storage
â”œâ”€â”€ temp/                         # Temporary build files
â””â”€â”€ dist/                         # PyInstaller dist output
```

---

## 7. Data Flow

The data flow between workers and master is the primary communication channel.

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Worker   â”‚         â”‚  Master  â”‚
â”‚  Service  â”‚         â”‚  Server  â”‚
â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜         â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
      â”‚                     â”‚
      â”‚  POST /api/v1/workers/register
      â”‚  {name, hostname, ip, version}
      â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
      â”‚                     â”œâ”€â”€ Store/update worker in DB
      â”‚                     â”œâ”€â”€ Log registration event
      â”‚  {id: "uuid", status: "ok"}
      â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
      â”‚                     â”‚
      â”‚  â”€â”€ Heartbeat Loop (5s interval) â”€â”€
      â”‚                     â”‚
      â”‚  POST /api/v1/workers/heartbeat
      â”‚  {id, cpu, ram, disk, temp, busy}
      â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
      â”‚                     â”œâ”€â”€ Update worker record
      â”‚                     â”œâ”€â”€ Broadcast WebSocket update
      â”‚  {status: "ok"}
      â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
      â”‚                     â”‚
      â”‚  GET /api/v1/workers/{id}/next-job
      â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
      â”‚                     â”œâ”€â”€ Check scheduler for pending jobs
      â”‚                     â”œâ”€â”€ If job available: assign, return job
      â”‚  {job: {id, type, payload, ...}} OR 204 No Content
      â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
      â”‚                     â”‚
      â”‚  â”€â”€ Job Execution â”€â”€
      â”‚                     â”‚
      â”‚  POST /api/v1/workers/{id}/progress
      â”‚  {job_id, progress: 45}
      â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
      â”‚                     â”œâ”€â”€ Update job progress in DB
      â”‚                     â”œâ”€â”€ Broadcast WebSocket progress
      â”‚                     â”‚
      â”‚  POST /api/v1/workers/{id}/result
      â”‚  {job_id, status: "completed", result: {...}}
      â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
      â”‚                     â”œâ”€â”€ Mark job complete in DB
      â”‚                     â”œâ”€â”€ Store result
      â”‚                     â”œâ”€â”€ Broadcast WebSocket result
      â”‚  {status: "ok"}
      â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
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
- Progress: reported at â‰¥5% changes or â‰¥2 second intervals
- Result: status (completed/failed/cancelled), result data or error, duration in ms
- Master updates DB and broadcasts WebSocket events

---

## 8. Worker Flow

The complete worker lifecycle, from startup to shutdown:

```
   START
     â”‚
     â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   STARTING   â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â”‚
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚LOADING_CONFIGâ”‚  Read three-tier config (env > config.json > .env > defaults)
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â”‚
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  CONNECTING  â”‚  Create HTTP client to master URL
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â”‚
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ REGISTERING  â”‚  POST /api/v1/workers/register
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â”‚
   â”Œâ”€â”€â”€â”´â”€â”€â”€â”
   â”‚       â”‚
  OK      FAIL
   â”‚       â”‚
   â”‚       â–¼
   â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚   â”‚  RETRY   â”‚  Exponential backoff: 1, 2, 5, 10, 30, 60 s
   â”‚   â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
   â”‚        â”‚
   â”‚        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º (loop back to REGISTERING)
   â”‚
   â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  ONLINE  â”‚
â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
     â”‚
     â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ HEARTBEAT  â”‚  POST /api/v1/workers/heartbeat (every 5 s)
â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
     â”‚
     â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ POLL_JOB   â”‚  GET /api/v1/workers/{id}/next-job
â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
     â”‚
   â”Œâ”€â”´â”€â”€â”
   â”‚    â”‚
  JOB  NONE
   â”‚    â”‚
   â”‚    â””â”€â”€â”€â”€â”€â”€â–º (loop back to HEARTBEAT)
   â”‚
   â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ EXECUTING  â”‚  Run handler.execute() with job payload
â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
     â”‚
     â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚REPORT_PROGRESSâ”‚  POST /api/v1/workers/{id}/progress (async generator)
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
       â”‚
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚REPORT_RESULT â”‚  POST /api/v1/workers/{id}/result
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â”‚
       â””â”€â”€â”€â”€â”€â”€â–º (loop back to HEARTBEAT)

FAILURE AT ANY POINT:
       â”‚
       â–¼
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚  RETRY   â”‚  Exponential backoff, auto-reconnect
   â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
        â”‚
        â””â”€â”€â”€â”€â”€â”€â–º (loop back to REGISTERING or CONNECTING)

SHUTDOWN SIGNAL (SIGINT/SIGTERM):
       â”‚
       â–¼
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚ SHUTDOWN  â”‚  Stop heartbeat, close HTTP client, flush logs
   â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚  EXIT   â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Job Handler Execution

```
execute_job(worker_id, job_data):
  â”‚
  â”œâ”€â”€ Determine job_type from job_data
  â”œâ”€â”€ Look up handler in JobRegistry
  â”‚
  â”œâ”€â”€ IF handler has execute_with_progress:
  â”‚     for progress in handler.execute_with_progress(payload):
  â”‚         if progress changed â‰¥ 5% OR 2s elapsed:
  â”‚             POST /progress
  â”‚     result = handler.execute(payload)
  â”‚
  â”œâ”€â”€ ELSE:
  â”‚     result = handler.execute(payload)
  â”‚
  â”œâ”€â”€ POST /result (completed, result data)
  â”‚
  â””â”€â”€ On error: POST /result (failed, error message)
```

---

## 9. Master Flow

The flow of a request through the master server:

```
CLIENT (Browser / Worker / CLI)
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   CORS Check    â”‚  Allow configured origins, methods, headers
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Rate Limiter   â”‚  200 requests/minute/IP
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Audit Middleware â”‚  Capture method, URL, status, duration, IP
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Auth Check     â”‚  JWT Bearer token validation (except /health, /login, /docs)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   API Router    â”‚  Route to appropriate handler
â”‚   /api/v1/*     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Pydantic       â”‚  Request validation (types, constraints, defaults)
â”‚  Validation     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Service Layer   â”‚
â”‚                 â”‚
â”‚  WorkerManager  â”‚  Register, heartbeat, CRUD, offline detection
â”‚  Scheduler      â”‚  Queue, priority, assign, retry
â”‚  AuthService    â”‚  Login, JWT create/verify
â”‚  LogService     â”‚  Structured logging
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Data Layer     â”‚  SQLAlchemy async session
â”‚  SQLite DB      â”‚  CRUD operations
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Response       â”‚  Pydantic response model serialization
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  WebSocket      â”‚  Broadcast state changes to all connected clients
â”‚  Broadcast      â”‚  (workers, jobs, dashboard events)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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
  â”‚
  â”‚ POST /api/v1/ai/chat
  â”‚ {message, session_id?, context?, stream?}
  â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Session Manager  â”‚  Create/get session (24h expiry)
â”‚                   â”‚  Restore conversation history
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Prompt Builder   â”‚  Build prompt with:
â”‚                   â”‚  - System prompt (role, constraints)
â”‚                   â”‚  - Repository context (if available)
â”‚                   â”‚  - Session history (last N messages)
â”‚                   â”‚  - Current user message
â”‚                   â”‚  - Token estimation & compression
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Context Builder  â”‚  If repository_id provided:
â”‚                   â”‚  - Retrieve relevant symbols/files
â”‚                   â”‚  - Score by relevance to query
â”‚                   â”‚  - Enforce token budget
â”‚                   â”‚  - Attach to prompt
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Model Router     â”‚  Select provider based on:
â”‚                   â”‚  - Task type (code, chat, analysis)
â”‚                   â”‚  - Model profile (fast/balanced/quality)
â”‚                   â”‚  - Availability
â”‚                   â”‚  - Fallback chain
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Provider Layer   â”‚  One of:
â”‚                   â”‚  - OllamaProvider
â”‚                   â”‚  - LlamaCppProvider
â”‚                   â”‚  - OpenAICompatibleProvider
â”‚                   â”‚
â”‚  generate(prompt) â”‚  â†’ tokens â†’ stream â†’ complete
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Conversation     â”‚  Store user message + assistant response
â”‚ Manager          â”‚  Update token counts
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Response         â”‚  Return {message, session_id,
â”‚                   â”‚          tokens_used, execution_ms}
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Provider Architecture

```
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚  ModelRegistry   â”‚
                    â”‚  (singleton)     â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                             â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚              â”‚              â”‚
     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”
     â”‚  Ollama     â”‚  â”‚  LlamaCpp   â”‚  â”‚  OpenAI      â”‚
     â”‚  Provider   â”‚  â”‚  Provider   â”‚  â”‚  Compatible  â”‚
     â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚             â”‚                â”‚
     HTTP POST /api/chat    â”‚       POST /v1/chat/completions
                            â”‚                â”‚
                   HTTP POST /completion     â”‚
                                     POST /v1/completions
```

---

## 11. Plugin Flow

The complete plugin lifecycle:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   1. INSTALL      â”‚  Plugin directory or ZIP uploaded
â”‚                   â”‚  â†’ Validate manifest (plugin.json)
â”‚                   â”‚  â†’ Check dependencies
â”‚                   â”‚  â†’ Check platform compatibility
â”‚                   â”‚  â†’ Copy to plugins/<plugin_id>/
â”‚                   â”‚  â†’ Log: PLUGIN_INSTALLED
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   2. VALIDATE     â”‚  â†’ Verify entry_point exists
â”‚                   â”‚  â†’ Verify declared hooks are valid
â”‚                   â”‚  â†’ Verify permissions are recognized
â”‚                   â”‚  â†’ Check min/max platform version
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   3. LOAD         â”‚  â†’ Dynamic import of entry_point module
â”‚                   â”‚  â†’ Instantiate Plugin class
â”‚                   â”‚  â†’ Call plugin.on_load() if exists
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   4. INITIALIZE   â”‚  â†’ Pass SDK to plugin
â”‚                   â”‚  â†’ logger, config, DB access
â”‚                   â”‚  â†’ workflow/repository/AI/agent APIs
â”‚                   â”‚  â†’ Call plugin.on_init() if exists
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 5. REGISTER HOOKS â”‚  â†’ For each hook in manifest.hooks:
â”‚                   â”‚     Register callback in HookRegistry
â”‚                   â”‚  â†’ Call plugin.on_register() if exists
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 6. ACTIVATE       â”‚  â†’ Set plugin status = active
â”‚                   â”‚  â†’ Call plugin.on_activate() if exists
â”‚                   â”‚  â†’ Plugin now receives hook callbacks
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 7. HOOK EXECUTION â”‚  When a platform event fires:
â”‚                   â”‚  â†’ HookRegistry looks up all callbacks
â”‚                   â”‚  â†’ Sorts by priority
â”‚                   â”‚  â†’ Executes each async callback
â”‚                   â”‚  â†’ Error isolation per callback
â”‚                   â”‚  â†’ Results collected and returned
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â”œâ”€â”€ DISABLE â†’ Call plugin.on_disable(), skip hooks
         â”œâ”€â”€ ENABLE  â†’ Call plugin.on_enable(), resume hooks
         â””â”€â”€ UNINSTALL â†’ Call plugin.on_uninstall()
                         Remove plugin directory
                         Log: PLUGIN_REMOVED
```

### Hook Execution Model

```
Event: WORKFLOW_COMPLETED
       â”‚
       â–¼
HookRegistry.get_callbacks("on_workflow_finish")
       â”‚
       â”œâ”€â”€ Plugin A (priority 10)
       â”‚     â””â”€â”€ on_workflow_finish(workflow_id, status)
       â”‚         â””â”€â”€ {"reported": true}
       â”‚
       â”œâ”€â”€ Plugin B (priority 20)
       â”‚     â””â”€â”€ on_workflow_finish(workflow_id, status)
       â”‚         â””â”€â”€ {"notified": true}
       â”‚
       â””â”€â”€ Collect results â†’ return aggregated
```

---

## 12. Workflow Flow

The workflow lifecycle from creation to completion:

```
USER / API CALLER
       â”‚
       â”‚ POST /api/v1/workflow
       â”‚ {name, type, tasks, dependencies, ...}
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  1. CREATE        â”‚  â†’ Validate workflow definition
â”‚                   â”‚  â†’ Store in DB (status: pending)
â”‚                   â”‚  â†’ Create individual task records
â”‚                   â”‚  â†’ Create dependency edges
â”‚                   â”‚  â†’ Broadcast workflow_created
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  2. PLAN          â”‚  â†’ WorkflowPlanner analyzes DAG
â”‚                   â”‚  â†’ Resolve dependencies
â”‚                   â”‚  â†’ Estimate durations
â”‚                   â”‚  â†’ Determine execution order
â”‚                   â”‚  â†’ Organize into stages (sequential/parallel)
â”‚                   â”‚  â†’ Set workflow status: planned
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  3. QUEUE         â”‚  â†’ Enqueue ready tasks
â”‚                   â”‚  â†’ A task is "ready" when all
â”‚                   â”‚    dependencies are satisfied
â”‚                   â”‚  â†’ Set workflow status: running
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  4. DISPATCH      â”‚  â†’ TaskDispatcher finds best worker
â”‚                   â”‚  â†’ Criteria: load, status, capabilities
â”‚                   â”‚  â†’ Fallback: round-robin
â”‚                   â”‚  â†’ Assign task to worker
â”‚                   â”‚  â†’ Set task status: assigned
â”‚                   â”‚  â†’ Broadcast task_assigned
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  5. EXECUTE       â”‚  â†’ Worker picks up task
â”‚                   â”‚  â†’ Worker reports progress
â”‚                   â”‚  â†’ On success: store result
â”‚                   â”‚  â†’ On failure:
â”‚                   â”‚      Check retry count < max
â”‚                   â”‚      Yes: exponential backoff, requeue
â”‚                   â”‚      No: mark task failed
â”‚                   â”‚  â†’ Broadcast task_started/finished
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  6. COMPLETE      â”‚  â†’ All tasks completed successfully
â”‚                   â”‚  â†’ Store workflow result
â”‚                   â”‚  â†’ Store artifacts (SHA-256, size, path)
â”‚                   â”‚  â†’ Record execution metrics
â”‚                   â”‚  â†’ Set workflow status: completed
â”‚                   â”‚  â†’ Broadcast workflow_completed
â”‚                   â”‚  â†’ Cache results if applicable
â”‚                   â”‚  â†’ Trigger plugin hook: on_workflow_finish
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### State Machines

```
Workflow States:
PENDING â†’ PLANNED â†’ RUNNING â†’ COMPLETED
                              â†’ FAILED
                              â†’ CANCELLED
                    â†’ PAUSED â†’ RUNNING
                              â†’ CANCELLED

Task States:
CREATED â†’ ASSIGNED â†’ RUNNING â†’ SUCCESS
                               â†’ FAILED (retry â†’ ASSIGNED)
                     â†’ CANCELLED
```

---

## 13. Repository Flow

The repository intelligence pipeline:

```
USER / AI RUNTIME
       â”‚
       â”‚ POST /api/v1/repositories
       â”‚ {path, name}
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  1. REGISTER      â”‚  â†’ Validate path exists
â”‚                   â”‚  â†’ Detect VCS type (git)
â”‚                   â”‚  â†’ Store repository record in DB
â”‚                   â”‚  â†’ Set status: registered
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  2. SCAN          â”‚  â†’ POST /api/v1/repositories/{id}/scan
â”‚                   â”‚  â†’ Traverse file tree
â”‚                   â”‚  â†’ Respect .gitignore
â”‚                   â”‚  â†’ Detect language per file
â”‚                   â”‚  â†’ Skip binary files (null-byte check)
â”‚                   â”‚  â†’ Compute SHA-256 hash per file
â”‚                   â”‚  â†’ Compare with cached hash
â”‚                   â”‚  â†’ Only process changed files
â”‚                   â”‚  â†’ Store file records
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  3. INDEX         â”‚  â†’ For each changed file:
â”‚                   â”‚     Select parser by language
â”‚                   â”‚     â†’ Python: AST parser
â”‚                   â”‚     â†’ TS/JS: regex parser
â”‚                   â”‚     â†’ Other: generic regex fallback
â”‚                   â”‚  â†’ Extract symbols:
â”‚                   â”‚     classes, functions, async functions,
â”‚                   â”‚     variables, decorators, annotations,
â”‚                   â”‚     interfaces, types, imports
â”‚                   â”‚  â†’ Store symbol records
â”‚                   â”‚  â†’ Extract imports and references
â”‚                   â”‚  â†’ Update dependency graph
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  4. ANALYZE       â”‚  â†’ Compute code metrics:
â”‚                   â”‚     LOC, complexity, symbol counts
â”‚                   â”‚  â†’ Compute maintainability index
â”‚                   â”‚  â†’ Detect large/complex files
â”‚                   â”‚  â†’ Build knowledge graph
â”‚                   â”‚  â†’ Generate embeddings (optional)
â”‚                   â”‚  â†’ Update repository health
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  5. SEARCH        â”‚  â†’ GET /api/v1/repositories/search
â”‚                   â”‚  â†’ Symbol search (by name/type/lang)
â”‚                   â”‚  â†’ File search (by path/language)
â”‚                   â”‚  â†’ Text search (regex, full content)
â”‚                   â”‚  â†’ Reference search (cross-symbol)
â”‚                   â”‚  â†’ Results ranked by relevance
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 14. Engineering Flow

The autonomous engineering pipeline:

```
USER GOAL
  â”‚ "Add user authentication to the backend"
  â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  1. GOAL ANALYZER â”‚  â†’ Classify intent:
â”‚                    â”‚     feature / bug_fix / refactor /
â”‚                    â”‚     update / documentation
â”‚                    â”‚  â†’ Detect risk level:
â”‚                    â”‚     low / medium / high / critical
â”‚                    â”‚  â†’ Determine auto-approval requirement
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  2. PLANNER       â”‚  â†’ Decompose goal into task chain
â”‚                    â”‚  â†’ Assign roles to tasks
â”‚                    â”‚  â†’ Estimate effort (files affected)
â”‚                    â”‚  â†’ Create implementation plan
â”‚                    â”‚  â†’ Store plan in DB
â”‚                    â”‚  â†’ Broadcast plan_ready
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  3. VALIDATOR     â”‚  â†’ 7 validation checks:
â”‚                    â”‚     architecture, security, syntax,
â”‚                    â”‚     formatting, lint, types, tests
â”‚                    â”‚  â†’ Record all results
â”‚                    â”‚  â†’ If validation passes, proceed
â”‚                    â”‚  â†’ If not, route to repair
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”
    â”‚         â”‚
  PASS       FAIL
    â”‚         â”‚
    â”‚         â–¼
    â”‚    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚    â”‚  4. REPAIR        â”‚  â†’ Self-repair loop
    â”‚    â”‚                   â”‚  â†’ Max 3 iterations
    â”‚    â”‚                   â”‚  â†’ Auto-generate fix
    â”‚    â”‚                   â”‚  â†’ Re-run validation
    â”‚    â”‚                   â”‚  â†’ Escalate if persistent
    â”‚    â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    â”‚             â”‚
    â”‚         â”Œâ”€â”€â”€â”´â”€â”€â”€â”
    â”‚         â”‚       â”‚
    â”‚       FIXED   FAILED
    â”‚         â”‚       â”‚
    â”‚         â”‚       â””â”€â”€â†’ Report failure
    â”‚         â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  5. EXECUTE       â”‚  â†’ Apply patches to files
â”‚                   â”‚  â†’ Track changes in patches table
â”‚                   â”‚  â†’ If git repository, create commits
â”‚                   â”‚  â†’ Broadcast patch_created
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  6. QUALITY GATES â”‚  â†’ 9 gates must pass:
â”‚                    â”‚     architecture_review
â”‚                    â”‚     static_analysis
â”‚                    â”‚     security_review
â”‚                    â”‚     formatting
â”‚                    â”‚     lint
â”‚                    â”‚     type_check
â”‚                    â”‚     unit_tests
â”‚                    â”‚     integration_tests
â”‚                    â”‚     documentation_check
â”‚                    â”‚  â†’ All must pass for completion
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”
    â”‚         â”‚
  PASS       FAIL
    â”‚         â”‚
    â”‚         â””â”€â”€â†’ Route to repair (self-repair loop)
    â”‚
    â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  7. DOCUMENTATION â”‚  â†’ Auto-update README
â”‚                   â”‚  â†’ Update CHANGELOG
â”‚                   â”‚  â†’ Update PROJECT_STATE
â”‚                   â”‚  â†’ Update API documentation
â”‚                   â”‚  â†’ Update architecture docs
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  8. APPROVAL      â”‚  â†’ If risk = high/critical:
â”‚                   â”‚     Create approval request
â”‚                   â”‚     Wait for approval/rejection
â”‚                   â”‚  â†’ If risk = low/medium:
â”‚                   â”‚     Auto-approve
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  9. REPORT        â”‚  â†’ Generate engineering report
â”‚                   â”‚  â†’ Record metrics (duration, iterations)
â”‚                   â”‚  â†’ Broadcast workflow_completed
â”‚                   â”‚  â†’ Return final result
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 15. Studio Flow

The AICluster Studio user flow through workspaces, projects, and tools:

```
USER OPENS STUDIO
       â”‚
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Workspace Manager   â”‚  â†’ List workspaces
â”‚                      â”‚  â†’ Select or create workspace
â”‚                      â”‚  â†’ Load layout (saved panel arrangement)
â”‚                      â”‚  â†’ Load preferences (theme, keybindings)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Project Explorer    â”‚  â†’ List projects in workspace
â”‚                      â”‚  â†’ Select project
â”‚                      â”‚  â†’ Load repository view
â”‚                      â”‚  â†’ Load bookmarks
â”‚                      â”‚  â†’ Restore open files/tabs
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”
   â”‚               â”‚
   â–¼               â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Editor   â”‚  â”‚ Terminal â”‚
â”‚  Monaco   â”‚  â”‚  CMD     â”‚
â”‚  Code     â”‚  â”‚  PS      â”‚
â”‚  Editing  â”‚  â”‚  Git     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
   â”‚               â”‚
   â–¼               â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ AI Chat  â”‚  â”‚ Workflow â”‚
â”‚ Panel    â”‚  â”‚ Designer â”‚
â”‚ (repo-   â”‚  â”‚ (React   â”‚
â”‚  aware)  â”‚  â”‚  Flow)   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
   â”‚               â”‚
   â–¼               â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Plugin   â”‚  â”‚ Model    â”‚
â”‚ Center   â”‚  â”‚ Manager  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
   â”‚
   â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Settings  â”‚
â”‚ (theme,   â”‚
â”‚  language,â”‚
â”‚  AI,      â”‚
â”‚  cluster) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Workspace API Flow

```
GET /api/v1/studio/workspaces  â†’ List all workspaces
POST /api/v1/studio/workspaces â†’ Create workspace {name}
GET /api/v1/studio/workspaces/{id} â†’ Get workspace details
DELETE /api/v1/studio/workspaces/{id} â†’ Delete workspace

POST /api/v1/studio/projects â†’ Create project {workspace_id, name, path}
GET /api/v1/studio/projects â†’ List projects (filter by workspace_id)

POST /api/v1/studio/layout â†’ Save layout {workspace_id, panels, sizes}
GET /api/v1/studio/layout â†’ Load layout (filter by workspace_id)

POST /api/v1/studio/bookmarks â†’ Add bookmark {project_id, path, name}
GET /api/v1/studio/history â†’ Get action history (filter by workspace_id)
POST /api/v1/studio/preferences â†’ Set preference {workspace_id, key, value}
GET /api/v1/studio/preferences/{id} â†’ Get all preferences for workspace
```

---

## 16. Audit Flow

The complete audit event lifecycle from capture to query:

```
EVENT SOURCE                  AUDIT SYSTEM
     â”‚                             â”‚
     â”‚  HTTP REQUEST                â”‚
     â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º AuditMiddleware
     â”‚                    â”‚
     â”‚                    â”œâ”€â”€ Capture: method, URL, status code,
     â”‚                    â”‚   duration, client IP, safe headers
     â”‚                    â”œâ”€â”€ Mask sensitive headers (auth, cookie, API key)
     â”‚                    â”œâ”€â”€ Skip sensitive paths (/login, /auth)
     â”‚                    â”‚
     â”‚                    â”œâ”€â”€ Status â‰¥ 500 â†’ severity ERROR
     â”‚                    â”œâ”€â”€ Status â‰¥ 400 â†’ severity WARNING
     â”‚                    â””â”€â”€ Status < 400 â†’ severity INFO
     â”‚                         â”‚
     â”‚                         â”œâ”€â”€ Create AuditEvent
     â”‚                         â”œâ”€â”€ Publish to EventBus
     â”‚                         â”‚
     â”‚  INTERNAL EVENT          â”‚
     â”‚  (workflow, worker, etc.)â”‚
     â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º EventBusâ”‚
     â”‚                    â”‚     â”‚
     â”‚                    â”œâ”€â”€ All listeners receive event
     â”‚                    â”‚   (AuditService.subscribe)
     â”‚                    â”‚
     â”‚                    â–¼
     â”‚              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
     â”‚              â”‚ AuditService â”‚
     â”‚              â”‚              â”‚
     â”‚              â”‚ log() /      â”‚
     â”‚              â”‚ log_event()  â”‚
     â”‚              â”‚              â”‚
     â”‚              â”œâ”€â”€ Validate event fields
     â”‚              â”œâ”€â”€ Create AuditLog record
     â”‚              â”œâ”€â”€ DB: INSERT INTO audit_logs
     â”‚              â”‚   (26 columns)
     â”‚              â””â”€â”€ Commit
     â”‚
     â”‚  LATER, QUERY              â”‚
     â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º GET /api/v1/audit/logs
     â”‚                    â”‚       POST /api/v1/audit/search
     â”‚                    â”‚       GET /api/v1/audit/statistics
     â”‚                    â”‚
     â”‚                    â”œâ”€â”€ AuditService.search()
     â”‚                    â”‚   Filters: date range, category,
     â”‚                    â”‚   severity, event type, username,
     â”‚                    â”‚   worker/workflow/repository/plugin,
     â”‚                    â”‚   status, full-text
     â”‚                    â”‚
     â”‚                    â”œâ”€â”€ AuditService.export()
     â”‚                    â”‚   Format: CSV or JSON
     â”‚                    â”‚   Compression: ZIP
     â”‚                    â”‚   Filename: audit_YYYYMMDD_HHMMSS.ext
     â”‚                    â”‚
     â”‚                    â”œâ”€â”€ AuditService.purge()
     â”‚                    â”‚   Retention: 30/90/180/365 days or forever
     â”‚                    â”‚   Auto-purge background task
     â”‚                    â”‚
     â”‚                    â””â”€â”€ AuditService.get_statistics()
     â”‚                        Total, today, this week
     â”‚                        Critical/error/warning counts
     â”‚                        Success rate, by category, by severity
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
       â”‚
       â”‚ python -m build.build [--clean] [--sign]
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  1. ENVIRONMENT       â”‚  Verify:
â”‚     VERIFICATION      â”‚  âœ” Python 3.12+ available
â”‚                       â”‚  âœ” Node.js 20+ available
â”‚                       â”‚  âœ” npm available
â”‚                       â”‚  âœ” Rust 1.70+ available (if not --skip-tauri)
â”‚                       â”‚  âœ” Tauri CLI 2.0+ available
â”‚                       â”‚  âœ” PyInstaller installed
â”‚                       â”‚  âœ” Inno Setup 6+ available (if not --skip-installer)
â”‚                       â”‚  âœ” 7-Zip available
â”‚                       â”‚  âœ” signtool available (if --sign)
â”‚                       â”‚  â†’ Report PASS/FAIL/WARN for each
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  2. CLEAN             â”‚  (if --clean)
â”‚                       â”‚  Remove release/, dist/ from all targets
â”‚                       â”‚  Remove temp/ build artifacts
â”‚                       â”‚  Remove old log files
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  3. BUILD FRONTENDS   â”‚  For each frontend:
â”‚                       â”‚  âœ” frontend/ â†’ npm run build â†’ .next/
â”‚                       â”‚  âœ” master-control-center/ â†’ npm run build
â”‚                       â”‚  âœ” worker-control-center/ â†’ npm run build
â”‚                       â”‚  âœ” studio/ â†’ npm run build (tsc -b && vite build)
â”‚                       â”‚  â†’ Zero errors required
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  4. BUILD PYINSTALLER â”‚  For each target:
â”‚                       â”‚  master â†’ AIClusterRuntime.exe --mode master
â”‚                       â”‚  worker â†’ AIClusterRuntime.exe --mode worker
â”‚                       â”‚  cli    â†’ aicluster.exe
â”‚                       â”‚
â”‚                       â”‚  Steps per target:
â”‚                       â”‚  âœ” Write VSVersionInfo file
â”‚                       â”‚  âœ” Generate .spec or --collect-all args
â”‚                       â”‚  âœ” Run pyinstaller <spec> or pyinstaller <args>
â”‚                       â”‚  âœ” Real PE verification (MZ + PE headers)
â”‚                       â”‚  âœ” Publish to release/<subdir>/
â”‚                       â”‚  â†’ Any failure aborts entire build
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  5. BUILD TAURI       â”‚  For each target:
â”‚                       â”‚  master-control â†’ MasterControlCenter.exe
â”‚                       â”‚  worker-control â†’ WorkerControlCenter.exe
â”‚                       â”‚  studio â†’ AIClusterStudio.exe
â”‚                       â”‚
â”‚                       â”‚  Steps per target:
â”‚                       â”‚  âœ” cd frontend && npm run tauri build
â”‚                       â”‚  âœ” Copy .exe from src-tauri/target/release/
â”‚                       â”‚  âœ” Publish to release/<subdir>/
â”‚                       â”‚  â†’ Any failure aborts entire build
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  6. SIGN              â”‚  (if --sign and certificate configured)
â”‚                       â”‚  For every built .exe:
â”‚                       â”‚  âœ” signtool sign /fd SHA256 /a
â”‚                       â”‚  âœ” Verify signature
â”‚                       â”‚  â†’ Non-fatal if signing fails
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  7. PRE-INSTALLER     â”‚  Verify every required .exe:
â”‚     GATE              â”‚  âœ” release/master/AIClusterRuntime.exe --mode master
â”‚                       â”‚  âœ” release/worker/AIClusterRuntime.exe --mode worker
â”‚                       â”‚  âœ” release/cli/aicluster.exe
â”‚                       â”‚  âœ” release/master-control/MasterControlCenter.exe
â”‚                       â”‚  âœ” release/worker-control/WorkerControlCenter.exe
â”‚                       â”‚  âœ” release/studio/AIClusterStudio.exe
â”‚                       â”‚  â†’ Each must be a real PE binary
â”‚                       â”‚  â†’ Any FAIL aborts before installer
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  8. PACKAGE           â”‚  âœ” Create portable ZIPs per component
â”‚                       â”‚  âœ” Generate SHA-256 checksums
â”‚                       â”‚  âœ” Create release manifest (JSON)
â”‚                       â”‚  âœ” Copy to artifacts/ directory
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  9. INSTALLER         â”‚  âœ” Generate Inno Setup .iss script
â”‚                       â”‚  âœ” Populate payload directory
â”‚                       â”‚  âœ” Compile AIClusterSetup.exe
â”‚                       â”‚  âœ” Generate NSIS fallback installer
â”‚                       â”‚  âœ” Verify installer authenticity
â”‚                       â”‚  âœ” Copy to artifacts/AIClusterSetup-{version}.exe
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 10. FINAL VERIFY      â”‚  âœ” Verify artifact integrity
â”‚                       â”‚  âœ” Verify checksums match
â”‚                       â”‚  âœ” Verify installer runs
â”‚                       â”‚  âœ” Verify all .exe sizes are reasonable
â”‚                       â”‚  â†’ Generate final verification report
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 11. RELEASE VERIFY    â”‚  Run comprehensive verification suite:
â”‚                       â”‚  âœ” verify_build.py â€” build artifacts
â”‚                       â”‚  âœ” verify_backend.py â€” backend startup
â”‚                       â”‚  âœ” verify_frontend.py â€” frontend build
â”‚                       â”‚  âœ” verify_api.py â€” API endpoint health
â”‚                       â”‚  âœ” verify_executables.py â€” PE validation
â”‚                       â”‚  âœ” verify_installer.py â€” installer smoke test
â”‚                       â”‚  âœ” verify_checksums.py â€” hash verification
â”‚                       â”‚  âœ” verify_artifacts.py â€” artifact integrity
â”‚                       â”‚  âœ” verify_config.py â€” config validation
â”‚                       â”‚  âœ” verify_python.py â€” Python env check
â”‚                       â”‚  â†’ Overall: PASS / FAIL
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 12. REPORT            â”‚  âœ” Generate build report (Markdown)
â”‚                       â”‚  âœ” Generate RELEASE_NOTES.md
â”‚                       â”‚  âœ” Print summary:
â”‚                       â”‚     Duration, warnings count, errors count
â”‚                       â”‚     Signed files, release manifest path
â”‚                       â”‚  â†’ Exit code 0 (success) or 1 (failure)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 18. Dependency Graph

The following diagram shows subsystem relationships. An arrow A â†’ B means "A depends on B" or "A uses B."

```
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                        â”‚  Web Frontend    â”‚
                        â”‚  (Next.js 15)    â”‚
                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                 â”‚ REST + WebSocket
                                 â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Master CC   â”‚â—„â”€â”€â”€â”€â”€â”€â–ºâ”‚  Master Server   â”‚â—„â”€â”€â”€â”€â”€â”€â–ºâ”‚  Worker CC   â”‚
â”‚  (Tauri v2)  â”‚  HTTP  â”‚  (FastAPI)       â”‚  HTTP  â”‚  (Tauri v2)  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                 â”‚
                                 â–¼
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                        â”‚  AICluster       â”‚
                        â”‚  Studio (Tauri)  â”‚
                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                 â”‚
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚                         â”‚                         â”‚
       â–¼                         â–¼                         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Worker      â”‚        â”‚  Plugin System   â”‚        â”‚  Audit       â”‚
â”‚  Service     â”‚        â”‚  (SDK + Hooks)   â”‚        â”‚  System      â”‚
â”‚  (httpx/     â”‚        â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
â”‚   psutil)    â”‚                 â”‚                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                 â”‚                         â”‚
                                 â”‚                         â”‚
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚                         â”‚                         â”‚
       â–¼                         â–¼                         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Workflow    â”‚        â”‚  Engineering     â”‚        â”‚  Repository  â”‚
â”‚  Engine      â”‚â—„â”€â”€â”€â”€â”€â”€â–ºâ”‚  Engine          â”‚â—„â”€â”€â”€â”€â”€â”€â–ºâ”‚  Intelligenceâ”‚
â”‚  (DAG-based) â”‚        â”‚  (Auto SWE)      â”‚        â”‚  (Symbols)   â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
       â”‚                         â”‚                         â”‚
       â–¼                         â–¼                         â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”               â”‚
â”‚  Multi-Agent â”‚â—„â”€â”€â”€â”€â”€â”€â–ºâ”‚  AI Runtime      â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â”‚  Engine      â”‚        â”‚  (Ollama/Llama/  â”‚
â”‚  (12 Agents) â”‚        â”‚   OpenAI)        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                 â”‚
                                 â–¼
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                        â”‚  LLM Providers   â”‚
                        â”‚  (3 backends)    â”‚
                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

   DEPENDENCY KEY:
   â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   Master Server          â†’ Worker Service, Web Frontend, All Engines
   Worker Service         â†’ Master Server (HTTP)
   Workflow Engine        â†’ Worker Service, AI Runtime, Repository
   Repository Intelligence â†’ File System, Database
   AI Runtime             â†’ Repository Intelligence, LLM Providers
   Multi-Agent Engine     â†’ AI Runtime, Workflow Engine
   Engineering Engine     â†’ AI Runtime, Repository Intelligence
   Plugin System          â†’ Master Server, All Engines
   Audit System           â†’ Master Server, All Engines
   AICluster Studio       â†’ Master Server, Repository Intelligence, AI Runtime
   Build System           â†’ All Components (build-time only)
   CLI                    â†’ Master Server (HTTP)
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
