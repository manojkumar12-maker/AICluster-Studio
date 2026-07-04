# AICluster Project Map

## 1. Folder Tree

```
AICluster/
├── backend/                         # FastAPI Master Server
│   ├── app/
│   │   ├── main.py                  # Entry point, lifespan, WS endpoint
│   │   ├── config.py                # Pydantic Settings
│   │   ├── database.py              # SQLAlchemy async engine
│   │   ├── logging_config.py        # Logging setup
│   │   ├── static/dashboard.html    # SPA dashboard HTML
│   │   ├── models/                  # ORM models (11 files, 50+ tables)
│   │   ├── schemas/                 # Pydantic schemas
│   │   ├── services/                # Auth, Scheduler, Worker Manager, Logs
│   │   ├── api/v1/                  # REST API routes (19 groups)
│   │   ├── ai/                      # AI Runtime (providers, routing, sessions)
│   │   ├── agents/                  # Multi-Agent Engine
│   │   ├── workflow/                # DAG Workflow Engine
│   │   ├── repository/              # Code Intelligence
│   │   ├── engineering/             # Engineering Pipeline
│   │   ├── plugins/                 # Plugin SDK
│   │   ├── production/              # Monitoring, Health, Diagnostics
│   │   ├── audit/                   # Audit System
│   │   └── websocket/               # WebSocket Manager
│   └── tests/                       # 44 pytest tests
│
├── worker/                          # Distributed Worker Agent
│   ├── app/
│   │   ├── main.py                  # Entry point, state machine, orchestration
│   │   ├── config.py                # Layered config
│   │   ├── core/                    # Constants, state enum
│   │   ├── logging/                 # Structured logging
│   │   ├── utils/                   # HTTP client, retry
│   │   ├── services/                # Registrar, Heartbeat, Poller, Reporter, Monitor
│   │   └── executor/                # Job handlers (echo, sleep, dir_scan, etc.)
│   └── tests/                       # 14 pytest tests
│
├── frontend/                        # Next.js 15 Web Dashboard
│   └── src/
│       ├── app/                     # App Router pages (layout, login, dashboard, etc.)
│       ├── components/layout/       # Sidebar, Topbar, providers
│       ├── stores/                  # Zustand auth store
│       ├── types/                   # TypeScript interfaces
│       └── lib/                     # Utilities
│
├── studio/                          # Tauri v2 Desktop IDE
│   ├── src/                         # React + Vite frontend (starter template)
│   └── src-tauri/                   # Rust backend (minimal)
│
├── master-control-center/           # Tauri v2 Cluster Management
│   ├── backend/                     # FastAPI proxy (:8800)
│   │   └── app/api/router.py        # 19 endpoints
│   └── frontend/                    # React SPA
│       └── src/
│           ├── pages/               # 11 pages
│           ├── components/layout/   # Sidebar
│           ├── stores/              # Zustand state
│           └── lib/api.ts           # API client
│
├── worker-control-center/           # Tauri v2 Worker Management
│   ├── backend/                     # FastAPI (:8900)
│   │   └── app/api/router.py        # 16 endpoints
│   └── frontend/                    # React SPA
│       └── src/
│           ├── pages/               # 9 pages
│           ├── components/layout/   # Sidebar
│           ├── stores/              # Zustand state
│           └── lib/api.ts           # API client
│
├── shared/                          # Cross-component contracts
│   ├── protocol/                    # Wire DTOs (register, heartbeat, jobs)
│   ├── py/                          # Domain enums + API schemas
│   └── ts/                          # TypeScript mirror
│
├── build/                           # Build system
│   ├── build.py                     # Master orchestrator (12 stages)
│   ├── config.py                    # Target definitions
│   ├── frontend.py                  # npm build orchestration
│   ├── pyinstaller_builder.py       # PyInstaller builds
│   ├── tauri_builder.py             # Tauri builds
│   ├── package.py                   # ZIP + checksums
│   ├── release.py                   # Installer scripts + reports
│   ├── setup_builder.py             # AIClusterSetup.exe
│   ├── sign.py                      # Authenticode signing
│   ├── version.py                   # Version discovery
│   ├── toolchain.py                 # Tool detection
│   ├── verify.py                    # Environment + artifact verification
│   ├── setup/setup.iss              # Inno Setup script (595 lines)
│   ├── modules/                     # PyInstaller entry points
│   └── verification/                # 10-stage release verification
│
├── scripts/                         # PowerShell + Python utilities
│   ├── setup.ps1                    # Global environment setup
│   ├── install-master.ps1           # Master installer
│   ├── install-worker.ps1           # Worker installer
│   ├── start-master.ps1             # Start master + frontend
│   ├── start-worker.ps1             # Start worker
│   ├── run-integration-test.py      # 40-test integration suite
│   └── worker-simulator.py          # Interactive 4-worker TUI
│
├── config/                          # YAML configuration
│   ├── default.yaml                 # Base config
│   ├── development.yaml             # Dev overrides
│   └── production.yaml              # Production overrides
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE_SUMMARY.md
│   ├── API_REFERENCE.md
│   ├── DATABASE.md
│   ├── UI_ARCHITECTURE.md
│   ├── STARTUP_SEQUENCE.md
│   ├── WORKER_ARCHITECTURE.md
│   ├── MERMAID_DIAGRAMS.md
│   ├── PROJECT_REVIEW.md
│   ├── DOCUMENT_INDEX.md
│   └── Audit/                       # Code review, security, validation reports
│       ├── CODE_REVIEW.md
│       ├── SECURITY_REVIEW.md
│       ├── PROJECT_SCORE.md (7.5/10)
│       ├── PROJECT_AIM.md
│       ├── FILE_TEST_REPORT.md
│       └── MASTER_VALIDATION_REPORT.md
│
├── assets/                          # Icons, manifests
│   ├── manifest.json
│   ├── icons/default.ico
│   └── README.md
│
├── plugins/                         # User-installed plugins
│   └── example-metrics-reporter/    # Example plugin
│
├── data/                            # Runtime SQLite DB (empty)
├── models/                          # Local LLM storage (empty)
├── logs/                            # Runtime logs (gitignored)
├── VERSION                          # Current version: 1.3.0
├── CHANGELOG.md                     # Release history
├── README.md                        # Project README
├── CONTRIBUTING.md                  # Contribution guide
├── SECURITY.md                      # Security policy
└── NOTICE.md                        # Copyright notice
```

---

## 2. Subsystem Tree

```
AICluster Platform
├── Master Server (:8000)
│   ├── REST API (140+ endpoints)
│   ├── WebSocket (/ws)
│   ├── Authentication (JWT + bcrypt)
│   ├── Job Scheduler (background loop)
│   ├── AI Runtime (3 providers)
│   ├── Multi-Agent Engine (12 agents)
│   ├── Workflow Engine (DAG)
│   ├── Repository Intelligence
│   ├── Engineering Pipeline
│   ├── Plugin System (16 hooks)
│   ├── Audit System (17 categories)
│   └── Production Monitoring
│
├── Worker Fleet (:8001+)
│   ├── State Machine (21 states)
│   ├── Registration Protocol
│   ├── Heartbeat Reporting
│   ├── Job Polling & Execution
│   └── 5 Built-in Handlers
│
├── Web Dashboard (:3000)
│   ├── 2 Live Pages + 8 Placeholders
│   ├── Real-time Polling (React Query)
│   └── Auth-based Routing
│
├── Master Control Center (:8800)
│   ├── Cluster Status & Monitoring
│   ├── LAN Discovery & Registration
│   ├── Backup/Restore
│   └── Diagnostics
│
├── Worker Control Center (:8900)
│   ├── Worker Lifecycle Management
│   ├── Configuration Editor
│   ├── Connection Testing
│   └── Installation Wizard
│
├── Studio IDE (Tauri)
│   ├── [Planned] Monaco Editor
│   ├── [Planned] AI Chat
│   └── [Planned] Workflow Designer
│
└── Shared Contracts
    ├── Wire Protocol (Python DTOs)
    ├── Domain Schemas (Python)
    └── TypeScript Types
```

---

## 3. Dependency Tree

```
                     ┌─────────────────────┐
                     │   Build System       │
                     │  (build/)            │
                     └──────────┬──────────┘
                                │ produces
           ┌────────────────────┼────────────────────┐
           ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ AIClusterMaster  │  │ AIClusterWorker  │  │ aicluster.exe    │
│ (PyInstaller)    │  │ (PyInstaller)    │  │ (PyInstaller)    │
└────────┬─────────┘  └────────┬─────────┘  └──────────────────┘
         │ depends on          │ depends on
         ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│  backend/        │  │  worker/         │
│  shared/py       │  │  shared/protocol │
│  shared/protocol │  │  shared/py       │
└──────────────────┘  └──────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│MasterControlCenter│  │WorkerControlCenter│  │ AIClusterStudio  │
│ (Tauri)          │  │ (Tauri)          │  │ (Tauri)          │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │ depends on          │ depends on          │ depends on
         ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ master-control-  │  │ worker-control-  │  │  studio/         │
│ center/          │  │ center/          │  │  (React SPA)     │
│  backend→master  │  │  backend→master  │  │  shared/ts       │
│  shared/ts       │  │  shared/ts       │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘

┌──────────────────┐
│  Web Dashboard   │
│  (Next.js 15)    │
└────────┬─────────┘
         │ depends on
         ▼
┌──────────────────┐
│  frontend/       │
│  shared/ts       │
│  master API      │
└──────────────────┘
```

---

## 4. Execution Flow

```
STARTUP:
  Installer → Extract → Python/VC++ → DB Init → Admin Seed
  → Background Tasks → Uvicorn Bind → Dashboard Load → Worker Connect

REQUEST FLOW:
  Browser → Next.js Proxy → Master API → Service Layer → Database
  → Response (optionally WebSocket broadcast)

WORKER FLOW:
  Worker Start → Register → Heartbeat Loop → Poll Job → Execute → Report → Loop

WORKFLOW FLOW:
  Create Workflow → Validate DAG → Dispatch Tasks → Workers Execute
  → Collect Artifacts → Cache Results → Complete

REPOSITORY FLOW:
  Register Repo → Scan Files → Parse Symbols → Build Dependencies → Index Search
```

---

## 5. Data Flow

```
User Input → API Gateway → Auth Check → Business Logic → Database
                           ↓
                    WebSocket Broadcast → Connected Clients
                                          ↓
Worker Input → Master API → Scheduler → Job Queue → Worker Assignment
                            ↓
                     Dashboard Aggregation → WebSocket
```

---

## 6. Request Flow (Example: Create Job)

```
1. Client POST /api/v1/jobs {type: "echo", payload: {...}}
2. next.config.ts proxies /api/* → http://localhost:8000
3. CORSMiddleware → AuditMiddleware → Router
4. AuthService.get_current_user() → validate JWT
5. SchedulerService.create_job()
   ├── INSERT INTO jobs (status='queued', ...)
   ├── SystemLog.info("Job created")
   └── ws_manager.broadcast_job_update()
6. Return JobResponse
7. Background: SchedulerService._process_queue() assigns to worker
8. Worker polls GET /next-job → executes → reports result
```

---

## 7. Worker Flow

```
WorkerMachine
  ├── 1. Load config (JSON + .env + defaults)
  ├── 2. Create HTTP client (httpx)
  ├── 3. Register with master (POST /register) → get worker_id
  ├── 4. Start heartbeat loop (POST /heartbeat every 5s)
  ├── 5. Start poll loop (GET /next-job)
  │   ├── No job → sleep 5s → retry
  │   └── Job received → execute handler → POST /progress → POST /result
  └── 6. On shutdown → stop heartbeat → close client → exit
```

---

## 8. Repository Flow

```
1. POST /api/v1/repositories {path, name}
2. Scanner walks directory tree
3. Parser extracts symbols per file:
   ├── Python: classes, functions, imports
   ├── JS/TS: classes, functions, imports
   ├── Rust: structs, functions, impls
   └── ... (multi-language)
4. Indexer builds:
   ├── symbol_import graph
   ├── symbol_reference graph
   ├── dependency_edges (file-level)
   └── knowledge_graph (nodes + edges)
5. SearchService indexes for full-text search
6. CodeMetricsService computes LOC, complexity, etc.
```

---

## 9. Plugin Flow

```
1. POST /api/v1/plugins/install {url or file upload}
2. ManifestService validates plugin.json
3. PluginLoader imports entry_point module
4. PluginRegistry adds to active plugins
5. Plugins register hooks (e.g., on_workflow_finish)
6. When event occurs → HookRegistry calls registered plugins
7. POST /api/v1/plugins/{id}/disable → remove hook registrations
8. POST /api/v1/plugins/{id}/uninstall → delete files
```
