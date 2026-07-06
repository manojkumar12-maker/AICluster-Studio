# Mermaid.js Architecture Diagrams

This document contains all system architecture diagrams for AICluster, rendered via [Mermaid.js](https://mermaid.js.org/). Paste any diagram block into a Mermaid-compatible viewer (GitHub markdown, [Mermaid Live Editor](https://mermaid.live/), or documentation tool).

---

## Table of Contents

| # | Diagram | Description |
|---|---------|-------------|
| a | Overall System Architecture | Master server with Workers, Desktop apps, Web frontend, CLI |
| b | Master Internal Components | FastAPI, WebSocket, SQLite, Workflow, AI, Agents, Plugins |
| c | Worker State Machine | Full lifecycle from STARTING to EXIT |
| d | Worker Registration Sequence | Worker â†’ Master â†’ ID storage |
| e | Heartbeat Sequence | Worker â†’ Master â†’ WebSocket broadcast |
| f | Job Execution Flow | Queue â†’ Poll â†’ Execute â†’ Report |
| g | AI Runtime Architecture | Prompt â†’ Router â†’ Provider â†’ Response |
| h | Multi-Agent Flow | Request â†’ Plan â†’ Execute â†’ Review â†’ Merge |
| i | Workflow DAG Execution | Create â†’ Plan â†’ Dispatch â†’ Execute |
| j | Build Pipeline | Source â†’ PyInstaller/Tauri â†’ Release |
| k | Database Schema Relationships | All master tables with relationships |
| l | Startup Sequence | Installer â†’ Master â†’ Workers â†’ UI â†’ Ready |

---

## a. Overall System Architecture

```mermaid
flowchart TD
    subgraph Internet["Internet / LAN"]
        direction LR
        CLI["CLI Tool\n(aicluster.exe)"]
        WEB["Web Frontend\n(Next.js 15)"]
    end

    subgraph DesktopApps["Desktop Applications"]
        MCC["Master Control Center\n(Tauri)"]
        STUDIO["AICluster Studio\n(Tauri)"]
    end

    subgraph ServerHost["Master Server (Windows PC)"]
        MASTER["AICluster Master\n(FastAPI + Uvicorn)"]
        DB[("SQLite Database\ndata/aicluster.db")]
        WS["WebSocket Manager"]
        MASTER --- DB
        MASTER --- WS
    end

    subgraph WorkerNodes["Worker Nodes (N Ã— Windows PCs)"]
        W1["Worker 1\n(Python async)"]
        W2["Worker 2\n(Python async)"]
        WN["Worker N\n(Python async)"]
    end

    CLI -->|HTTP :8000| MASTER
    WEB -->|HTTP :8000| MASTER
    MCC -->|HTTP :8000| MASTER
    STUDIO -->|HTTP :3001| MASTER
    MASTER -->|REST API :8000| W1
    MASTER -->|REST API :8000| W2
    MASTER -->|REST API :8000| WN
    WS -->|WebSocket /ws| WEB
    WS -->|WebSocket /ws| MCC
```

---

## b. Master Internal Components

```mermaid
flowchart TD
    subgraph FastAPI["FastAPI Application (backend/app/main.py)"]
        API["API Routes\n/api/v1/*"]
        AUTH["Auth Middleware\nJWT Validation"]
        CORS["CORS Middleware"]
    end

    subgraph Services["Service Layer"]
        SCHED["SchedulerService\nJob Queue Processing"]
        WMGR["WorkerManagerService\nRegistration & Heartbeats"]
        AUTH_SVC["AuthService\nLogin & Token Management"]
        WSMGR["WebSocketManager\nReal-Time Broadcasting"]
        LOG_SVC["LoggingService\nStructured Logs"]
    end

    subgraph DataLayer["Data Layer"]
        DB[("SQLite Database\n(SQLAlchemy Async)")]
        MODELS["SQLAlchemy Models\nWorker, Job, User, ..."]
        SESSION["AsyncSession Factory"]
    end

    subgraph WorkflowEngine["Workflow Engine"]
        PLANNER["WorkflowPlanner\nDAG Generation"]
        DISPATCH["WorkflowDispatcher\nTask Assignment"]
        EXEC["WorkflowExecutor\nState Machine"]
        ARTIFACTS["ArtifactManager\nSHA256 Checksums"]
        CACHE["CacheService\nTTL Caching"]
    end

    subgraph AIRuntime["AI Runtime"]
        REG["ModelRegistry"]
        ROUTER["Router\nModel Selection"]
        PROV["Providers\nllama.cpp / Ollama / Custom"]
        SESS["SessionManager\nContext Tracking"]
        TOOLS["ToolRegistry\nCode, File, Search, Git"]
        MEM["MemoryManager\nLong-Term Memory"]
        PROMPT["PromptEngine\nTemplate Rendering"]
    end

    subgraph Agents["Multi-Agent System"]
        AGENT_MGR["AgentManager"]
        PLANNER_AG["AgentPlanner"]
        REVIEW["AgentReviewer"]
        MERGE["AgentMerge"]
    end

    subgraph Plugins["Plugin System"]
        PLOADER["PluginLoader\nDirectory Scanner"]
        PHOOKS["Hook Registry\non_workflow_finish, ..."]
        PSANDBOX["Sandbox\nRestricted API"]
    end

    API --> AUTH
    API --> SERVICES
    SERVICES --> DataLayer
    WorkflowEngine --> DataLayer
    AIRuntime --> DataLayer
    Agents --> AIRuntime
    Agents --> WorkflowEngine
    Plugins --> WorkflowEngine
    Plugins --> AIRuntime
```

---

## c. Worker State Machine

```mermaid
flowchart TD
    STARTING -->|"_run_worker() invoked"| LOADING_CONFIG
    LOADING_CONFIG -->|"Config parsed, HTTP client created"| CONNECTING
    CONNECTING -->|"HTTP client ready"| REGISTERING
    REGISTERING -->|"POST /workers/register returns 200"| ONLINE
    REGISTERING -->|"Registration fails"| RETRY

    ONLINE -->|"First heartbeat cycle"| HEARTBEAT

    HEARTBEAT -->|"After heartbeat_interval"| POLL_JOB
    HEARTBEAT -->|"Network failure"| RETRY

    POLL_JOB -->|"204 No Content"| NO_JOB
    POLL_JOB -->|"200 with job data"| HAS_JOB
    POLL_JOB -->|"Network failure"| RETRY
    POLL_JOB -->|"429 Rate limited"| NO_JOB

    NO_JOB -->|"Next loop iteration"| HEARTBEAT

    HAS_JOB -->|"Handler found in registry"| EXECUTING

    EXECUTING -->|"Progress >=5% or >=5s elapsed"| REPORT_PROGRESS
    REPORT_PROGRESS -->|"Continue execution"| EXECUTING
    EXECUTING -->|"Job completes/fails/cancelled"| REPORT_RESULT

    REPORT_RESULT -->|"Result reported, loop continues"| HEARTBEAT

    RETRY -->|"Backoff complete"| REGISTERING

    STARTING -->|"SIGINT/SIGTERM"| SHUTDOWN
    LOADING_CONFIG -->|"SIGINT/SIGTERM"| SHUTDOWN
    CONNECTING -->|"SIGINT/SIGTERM"| SHUTDOWN
    REGISTERING -->|"SIGINT/SIGTERM"| SHUTDOWN
    ONLINE -->|"SIGINT/SIGTERM"| SHUTDOWN
    HEARTBEAT -->|"SIGINT/SIGTERM"| SHUTDOWN
    POLL_JOB -->|"SIGINT/SIGTERM"| SHUTDOWN
    NO_JOB -->|"SIGINT/SIGTERM"| SHUTDOWN
    HAS_JOB -->|"SIGINT/SIGTERM"| SHUTDOWN
    EXECUTING -->|"SIGINT/SIGTERM"| SHUTDOWN
    REPORT_PROGRESS -->|"SIGINT/SIGTERM"| SHUTDOWN
    REPORT_RESULT -->|"SIGINT/SIGTERM"| SHUTDOWN
    RETRY -->|"SIGINT/SIGTERM"| SHUTDOWN

    SHUTDOWN -->|"Cleanup begins"| STOPPING
    STOPPING -->|"All resources released"| EXIT
```

---

## d. Worker Registration Sequence

```mermaid
sequenceDiagram
    participant Worker as Worker Process
    participant Client as WorkerHttpClient
    participant Master as Master API
    participant DB as SQLite Database

    Worker->>Client: Registrar.register()
    Client->>Master: POST /api/v1/workers/register
    Note right of Master: {name, hostname, ip}
    Master->>DB: SELECT worker WHERE name = ?
    alt Worker exists (re-registration)
        DB-->>Master: Existing worker record
        Master->>DB: UPDATE ip, hostname, status='online', last_seen=now
    else New worker
        Master->>DB: INSERT new worker record
    end
    DB-->>Master: Worker saved
    Master-->>Client: 200 OK { "id": "abc-123-..." }
    Client-->>Worker: Return worker_id
    Worker->>Worker: Store self._worker_id = "abc-123-..."
    Worker->>Worker: State = ONLINE
    Worker->>Worker: Start heartbeat loop
    Worker->>Worker: Start job poll loop
```

---

## e. Heartbeat Sequence

```mermaid
sequenceDiagram
    participant Worker as Worker
    participant Monitor as SystemMonitor
    participant Master as Master API
    participant DB as SQLite Database
    participant WS as WebSocket Manager
    participant UI as Dashboard / MCC

    loop Every 5 seconds
        Worker->>Monitor: Collect metrics
        Monitor-->>Worker: cpu%, ram%, disk%, network
        Worker->>Master: POST /api/v1/workers/heartbeat
        Note right of Master: {id, cpu, ram, disk, busy, ...}
        Master->>DB: UPDATE worker SET cpu_percent=..., ram_percent=..., last_seen=now
        DB-->>Master: Updated
        Master-->>Worker: 200 OK { "status": "ok" }
        Master->>WS: Broadcast worker_update
        WS->>UI: WebSocket message: worker metrics
    end

    par Offline Checker (every 10s)
        Master->>DB: SELECT workers WHERE last_seen < now - 15s
        DB-->>Master: Offline workers
        Master->>DB: UPDATE status = 'offline'
        Master->>WS: Broadcast worker_status = 'offline'
        WS->>UI: WebSocket message: worker offline
    end
```

---

## f. Job Execution Flow

```mermaid
sequenceDiagram
    participant User as User / Scheduler
    participant Master as Master API
    participant DB as SQLite Database
    participant Worker as Worker
    participant Handler as JobHandler

    User->>Master: Create job (queued)
    Master->>DB: INSERT job (status='queued')
    DB-->>Master: Job saved

    loop Poll cycle
        Worker->>Master: GET /api/v1/workers/{id}/next-job
        Master->>DB: SELECT queued job ORDER BY priority, created_at
        DB-->>Master: Job found
        Master->>DB: UPDATE job status='running', assigned_worker=id
        Master-->>Worker: 200 OK { job: { id, type, payload } }
    end

    Worker->>Worker: Lookup handler in JobRegistry
    Worker->>Handler: handler.execute_with_progress(job_id, payload)

    loop Progress reporting (>=5% or >=5s)
        Handler-->>Worker: progress = 50%
        Worker->>Master: POST /api/v1/workers/{id}/progress
        Note right of Master: {job_id, progress: 50.0}
        Master->>DB: UPDATE job SET progress = 50.0
        Master-->>Worker: 200 OK
    end

    Handler-->>Worker: Execution complete
    Worker->>Master: POST /api/v1/workers/{id}/result
    Note right of Master: {job_id, status: "completed", result, duration_ms}
    Master->>DB: UPDATE job status='completed', finished_at=now
    Master->>DB: UPDATE worker status='online', current_job=NULL
    Master-->>Worker: 200 OK
    Worker->>Worker: State = ONLINE, loop back to HEARTBEAT
```

---

## g. AI Runtime Architecture

```mermaid
flowchart TD
    USER["User / Application"] -->|"Prompt + Context"| ROUTER["AI Router\n(backend/app/ai/routing/)"]

    ROUTER -->|"Task classification"| MODEL_SEL["Model Selection\nby capability & load"]

    MODEL_SEL -->|"Code/Logic"| PROV_LLAMA["llama.cpp Provider\nLocal LLM Inference"]
    MODEL_SEL -->|"General Chat"| PROV_OLLAMA["Ollama Provider\nRemote Model"]
    MODEL_SEL -->|"Custom"| PROV_CUSTOM["Custom Provider\nAPI Gateway"]

    PROV_LLAMA --> MODEL["Model Instance\nInference Engine"]
    PROV_OLLAMA --> MODEL
    PROV_CUSTOM --> MODEL

    MODEL -->|"Token Stream"| STREAM["Streaming Manager\n(SSE)"]
    MODEL -->|"Full Response"| SESS_MGR["SessionManager\nContext Tracking"]

    subgraph ToolsAndMemory["Tool Integration"]
        TOOL_REG["ToolRegistry\nCode Analysis, File Read,\nSearch, Git Operations"]
        TOOL_EXEC["ToolExecutor\nSafety Checks & Sandbox"]
        MEM_MGR["MemoryManager\nLong-Term Storage &\nSemantic Retrieval"]
    end

    SESS_MGR --> TOOL_REG
    TOOL_REG --> TOOL_EXEC
    SESS_MGR --> MEM_MGR

    subgraph Security["Security Layer"]
        INJECT_DET["Prompt Injection\nDetection"]
        CONTENT_FILTER["Content Filter\nPolicy Enforcement"]
        VALIDATORS["Output Schema\nValidators"]
    end

    MODEL --> Security
    Security -->|"Filtered Response"| OUTPUT["Formatted Response\nâ†’ User"]

    subgraph Support["Support Layers"]
        PROMPT_ENG["PromptEngine\nTemplate Rendering"]
        CACHE_AI["CacheService\nResponse Caching (TTL)"]
        EMBED["Embeddings\nSemantic Search"]
        TELE["Telemetry\nLatency & Usage Metrics"]
    end

    ROUTER --> PROMPT_ENG
    SESS_MGR --> CACHE_AI
    MEM_MGR --> EMBED
    MODEL --> TELE
```

---

## h. Multi-Agent Flow

```mermaid
flowchart TD
    REQ["User Request"] --> PLANNER["AgentPlanner\n(backend/app/agents/planner/)"]

    PLANNER -->|"Decompose into sub-tasks"| TASK_LIST["Task List\n[Task 1, Task 2, ..., Task N]"]

    TASK_LIST --> AGENT1["Agent 1\nCode Analysis"]
    TASK_LIST --> AGENT2["Agent 2\nFile Operations"]
    TASK_LIST --> AGENT3["Agent 3\nResearch / Search"]
    TASK_LIST --> AGENTN["Agent N\nCustom Task"]

    AGENT1 -->|"Result A"| REVIEWER["AgentReviewer\nCross-Check & Validation"]
    AGENT2 -->|"Result B"| REVIEWER
    AGENT3 -->|"Result C"| REVIEWER
    AGENTN -->|"Result N"| REVIEWER

    REVIEWER -->|"Validated"| MERGER["AgentMerge\nConflict Resolution &\nOutput Assembly"]
    REVIEWER -->|"Failed"| PLANNER

    MERGER --> FINAL["Final Output\nâ†’ User"]

    subgraph AgentServices["Shared Agent Infrastructure"]
        AGENT_MGR["AgentManager\nLifecycle & State"]
        AGENT_DB[("Agent Database\nTasks, Messages, Sessions")]
        TOOL_AG["Tool Access Layer\nSandboxed Execution"]
    end

    PLANNER --- AGENT_MGR
    AGENT1 --- AGENT_MGR
    AGENT2 --- AGENT_MGR
    AGENT3 --- AGENT_MGR
    AGENTN --- AGENT_MGR
    AGENT_MGR --- AGENT_DB
    AGENT1 --- TOOL_AG
    AGENT2 --- TOOL_AG
    AGENT3 --- TOOL_AG
    AGENTN --- TOOL_AG
```

---

## i. Workflow DAG Execution

```mermaid
flowchart TD
    CREATE["Create Workflow\nPOST /api/v1/workflows"] --> PLAN["WorkflowPlanner\n(backend/app/workflow/planner/)"]

    PLAN -->|"Topological Sort"| DAG["Dependency Graph\n(Directed Acyclic Graph)"]

    DAG -->|"Queue ready tasks"| QUEUE["Task Queue\nWorkflowTask Table"]

    QUEUE --> DISPATCH["WorkflowDispatcher\n(backend/app/workflow/dispatcher/)"]

    DISPATCH -->|"Assign to worker"| TASK_A["Task A\n(dependency: none)"]
    DISPATCH -->|"Assign to worker"| TASK_B["Task B\n(dependency: A)"]
    DISPATCH -->|"Assign to worker"| TASK_C["Task C\n(dependency: A)"]
    DISPATCH -->|"Assign to worker"| TASK_D["Task D\n(dependency: B, C)"]

    TASK_A -->|"Execute"| COMPLETE_A["Task A Complete"]
    COMPLETE_A --> UNLOCK_B["Unlock B & C"]
    UNLOCK_B --> TASK_B
    UNLOCK_B --> TASK_C

    TASK_B -->|"Execute"| COMPLETE_B["Task B Complete"]
    TASK_C -->|"Execute"| COMPLETE_C["Task C Complete"]
    COMPLETE_B --> UNLOCK_D["Unlock D"]
    COMPLETE_C --> UNLOCK_D
    UNLOCK_D --> TASK_D

    TASK_D -->|"Execute"| COMPLETE_D["Task D Complete"]
    COMPLETE_D --> FINAL_WF["Workflow Complete"]

    subgraph StateMachine["WorkflowTask State Machine"]
        PENDING["PENDING"] --> QUEUED["QUEUED"]
        QUEUED -->|"dependencies met"| RUNNING["RUNNING"]
        RUNNING --> COMPLETED["COMPLETED"]
        RUNNING --> FAILED["FAILED"]
        FAILED -->|"retry < 3"| QUEUED
    end

    subgraph Artifacts["Artifact Storage"]
        ART_STORE["data/artifacts/{wf_id}/{task_id}/"]
        ART_DB[("artifacts table\nSHA256, metadata)")]
    end

    WORKER["Worker executes task"] --> ART_STORE
    ART_STORE --- ART_DB
```

---

## j. Build Pipeline

```mermaid
flowchart TD
    SOURCE["Source Code\nbackend/ worker/ studio/ frontend/ cli/"] --> BUILD["Build Script\npython -m build.build"]

    subgraph Builder["Build Process"]
        PYINSTALLER["PyInstaller\nPython â†’ .exe"]
        TAURI["Tauri v2\nRust â†’ .exe"]
        FE_BUILD["Next.js 15\nnpm run build â†’ static/"]
    end

    BUILD --> PYINSTALLER
    BUILD --> TAURI
    BUILD --> FE_BUILD

    PYINSTALLER -->|"Master + Worker +\nCLI + Control Centers"| RELEASE_DIR["release/\nversioned output directory"]
    TAURI -->|"Studio +\nControl Centers"| RELEASE_DIR
    FE_BUILD -->|"Static files"| RELEASE_DIR

    RELEASE_DIR --> PE_GATE["PE Gate\n(pefile analysis)"]
    PE_GATE -->|"Verify PE headers\n& Authenticode"| SIG["Code Signing\n(sign.py)"]

    SIG -->|"Timestamp + Sign"| PKG["Package\nInno Setup 6 Installer"]

    PKG --> VERIFY["Verification\n(setup_validator.py)"]
    VERIFY -->|"SHA256 checksums\nInstall test\nContent audit"| FINAL_VERIFIED["Verified Release"]

    FINAL_VERIFIED --> RELEASE_TAG["Git Tag\nv2.0.0"]
    RELEASE_TAG --> GITHUB["GitHub Release\nAssets: .exe, .sha256, Release Notes"]

    subgraph Checks["Quality Gates"]
        LINT["ruff lint\n0 errors"]
        TYPE["mypy typecheck\n0 errors"]
        TEST["pytest\nall pass"]
    end

    SOURCE --> Checks
    Checks --> BUILD
```

---

## k. Database Schema Relationships

```mermaid
erDiagram
    WORKERS ||--o{ JOBS : "assigned_worker"
    WORKERS {
        string id PK
        string worker_name UK
        string hostname
        string ip
        string status
        float cpu_percent
        float ram_percent
        float disk_percent
        float temperature
        float network_speed
        string current_job FK
        string version
        float cpu_limit
        float ram_limit
        int priority
        bool is_paused
        datetime last_seen
        datetime registered_at
    }

    JOBS ||--|| WORKERS : "assigned_worker references"
    JOBS {
        string id PK
        string type
        string status
        string assigned_worker FK
        float progress
        json payload
        json result
        text error
        text logs
        int priority
        int retry_count
        int max_retries
        datetime created_at
        datetime started_at
        datetime finished_at
    }

    USERS {
        string id PK
        string username UK
        string hashed_password
        string role
        bool is_active
        datetime created_at
    }

    SYSTEM_LOGS {
        string id PK
        string level
        string message
        string source
        datetime created_at
    }

    WORKFLOWS ||--o{ WORKFLOW_TASKS : "contains"
    WORKFLOWS {
        string id PK
        string name
        string status
        string created_by FK
        datetime created_at
    }

    WORKFLOW_TASKS ||--o{ TASK_DEPENDENCIES : "depends_on"
    WORKFLOW_TASKS {
        string id PK
        string workflow_id FK
        string type
        string status
        string assigned_worker FK
        json payload
        json result
        int retry_count
        int max_retries
    }

    TASK_DEPENDENCIES {
        string id PK
        string task_id FK
        string depends_on_task_id FK
    }

    AI_SESSIONS ||--o{ AI_MESSAGES : "contains"
    AI_SESSIONS {
        string id PK
        string user_id FK
        string model_id
        string context
        datetime created_at
    }

    AI_MESSAGES {
        string id PK
        string session_id FK
        string role
        text content
        json metadata
        datetime created_at
    }

    AGENTS ||--o{ AGENT_TASKS : "executes"
    AGENTS {
        string id PK
        string name
        string model_id
        string tools
        json config
    }

    AGENT_TASKS ||--o{ AGENT_MESSAGES : "contains"
    AGENT_TASKS {
        string id PK
        string agent_id FK
        string session_id FK
        string status
        json input
        json output
    }

    AGENT_MESSAGES {
        string id PK
        string task_id FK
        string role
        text content
    }

    STUDIO_WORKSPACES ||--o{ STUDIO_PROJECTS : "contains"
    STUDIO_WORKSPACES {
        string id PK
        string name
        string user_id FK
        json layout
    }

    STUDIO_PROJECTS {
        string id PK
        string workspace_id FK
        string name
        string path
    }

    REPOSITORIES ||--o{ REPOSITORY_FILES : "contains"
    REPOSITORIES {
        string id PK
        string name
        string url
    }

    REPOSITORY_FILES ||--o{ SYMBOLS : "defines"
    REPOSITORY_FILES {
        string id PK
        string repo_id FK
        string path
        string language
    }

    SYMBOLS {
        string id PK
        string file_id FK
        string name
        string kind
        int line_start
        int line_end
    }

    ENGINEERING_PLANS ||--o{ ENGINEERING_TASKS : "contains"
    ENGINEERING_PLANS {
        string id PK
        string title
        string status
        string user_id FK
    }

    ENGINEERING_TASKS {
        string id PK
        string plan_id FK
        string type
        string status
        json implementation
    }

    USERS ||--o{ WORKFLOWS : "created_by"
    USERS ||--o{ AI_SESSIONS : "owns"
    USERS ||--o{ STUDIO_WORKSPACES : "owns"
    USERS ||--o{ ENGINEERING_PLANS : "creates"
```

---

## l. Startup Sequence

```mermaid
flowchart TD
    INSTALL["Installer Launched\nsetup_builder.exe"] -->|"T+0s"| EXTRACT["Extract Binaries\nC:\\Program Files\\AICluster\\"]
    EXTRACT -->|"T+5s"| MASTER_START["AIClusterRuntime.exe --mode master\nState: STARTING"]

    MASTER_START -->|"T+6s"| DB_INIT["Database Init\ninit_db() called"]
    DB_INIT -->|"CREATE ALL TABLES"| DB_TABLES["30+ Tables Created\nworkers, jobs, users, ..."]

    DB_TABLES -->|"T+7s"| SEED_ADMIN["Seed Admin User\nadmin / admin123"]
    SEED_ADMIN -->|"T+8s"| OFFLINE_CHECK["Offline Worker Checker\nBackground task every 10s"]
    OFFLINE_CHECK -->|"T+9s"| WS_READY["WebSocket Manager\nReady for /ws connections"]
    WS_READY -->|"T+10s"| SCHED_START["SchedulerService\nQueue loop every 2s"]
    SCHED_START -->|"T+11s"| WF_ENGINE["Workflow Engine Initialized\nPlanner, Dispatcher, Executor"]
    WF_ENGINE -->|"T+12s"| AI_INIT["AI Runtime Initialized\nModel Registry, Router, Providers"]
    AI_INIT -->|"T+13s"| PLUGINS["Plugin Loader\nScan plugins/ directory"]
    PLUGINS -->|"T+14s"| HTTP_BIND["Uvicorn Listening\n0.0.0.0:8000"]

    HTTP_BIND -->|"T+15s"| DASHBOARD["Dashboard Loads\nhttp://localhost:3000"]
    DASHBOARD -->|"T+16s"| STUDIO["AIClusterStudio.exe\nTauri App Launches"]

    subgraph WorkerConnect["Worker Connection (Parallel)"]
        direction LR
        W_START["Worker Starts\nSTARTING"] --> W_REG["Registration\nPOST /register"]
        W_REG --> W_ONLINE["ONLINE\nHeartbeat + Poll"]
    end

    HTTP_BIND --> WorkerConnect
    WorkerConnect --> W_ONLINE

    DASHBOARD -->|"T+17s"| LOGIN["User Login\nPOST /auth/login"]
    LOGIN -->|"JWT Token"| AUTH_WS["WebSocket Connected\nLive Dashboard"]

    STUDIO -->|"REST API"| STUDIO_CONN["Studio Connected"]
    W_ONLINE -->|"Heartbeat + Poll"| WORKERS_READY["Workers Operational"]

    AUTH_WS -->|"T+18s"| READY["SYSTEM READY\nOPERATIONAL"]
    STUDIO_CONN --> READY
    WORKERS_READY --> READY
```
