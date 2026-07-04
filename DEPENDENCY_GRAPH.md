# AICluster Dependency Graph

## 1. Python Package Dependencies

### Backend (backend/requirements.txt)
```
fastapi==0.115.4
  ├── starlette (ASGI framework)
  ├── pydantic>=2.0 (data validation)
  └── uvicorn[standard]==0.32.0 (ASGI server)
      ├── httptools
      └── uvloop

sqlalchemy==2.0.36 (ORM)
  └── aiosqlite (async SQLite driver)

alembic==1.14.0 (migrations)
  └── sqlalchemy

pydantic==2.10.2
pydantic-settings==2.6.1 (env config)

python-jose[cryptography]==3.3.0 (JWT)
  └── cryptography

passlib[bcrypt]==1.7.4 (password hashing)
  └── bcrypt

websockets==14.1 (WebSocket protocol)
httpx==0.28.0 (async HTTP client)
PyYAML==6.0.2 (YAML config)
python-multipart==0.0.17 (form data)

pytest==8.3.4 (testing)
pytest-asyncio==0.24.0 (async tests)
```

### Worker (worker/requirements.txt)
```
fastapi==0.115.4
uvicorn[standard]==0.32.0
pydantic==2.10.2
pydantic-settings==2.6.1
httpx==0.28.0
psutil==6.1.0 (system monitoring)
```

### Master Control Center Backend (master-control-center/backend/requirements.txt)
```
fastapi==0.115.4
uvicorn[standard]==0.32.0
pydantic==2.10.2
pydantic-settings==2.6.1
httpx==0.28.0
psutil==6.1.0
```

### Worker Control Center Backend (worker-control-center/backend/requirements.txt)
```
fastapi==0.115.4
uvicorn[standard]==0.32.0
pydantic==2.10.2
pydantic-settings==2.6.1
httpx==0.28.0
psutil==6.1.0
```

---

## 2. TypeScript/Node.js Dependencies

### Frontend (frontend/package.json)
```
Framework:
  next@15.0.3 → react@18.3.1, react-dom@18.3.1

UI:
  @radix-ui/* (20 packages) → headless UI primitives
  lucide-react@0.460 → icons
  framer-motion@11.11 → animations

Styling:
  tailwindcss@3.4.15 → utility CSS
  tailwindcss-animate@1.0.7 → animation utilities
  clsx@2.1.1 + tailwind-merge@2.5.5 → class utilities
  class-variance-authority@0.7.1 → component variants

State/Data:
  @tanstack/react-query@5.60 → server state
  zustand@5.0.1 → client state
  react-hook-form@7.53.2 → forms

Utilities:
  zod@3.23.8 → validation
  react-markdown@9.0.1 → markdown
  recharts@2.13.3 → charts

Dev:
  typescript@5.6.3
  eslint@8.57.1 + eslint-config-next@15.0.3
  prettier@3.4.1
  postcss@8.4.49 + autoprefixer@10.4.20
```

### Studio / MCC / WCC (common pattern)
```
Framework:
  react@^19.2.7 + react-dom@^19.2.7
  @vitejs/plugin-react@^6.0.3 → vite@^8.1.1

UI:
  lucide-react@^1.23.0
  framer-motion@^12.42.2
  react-resizable-panels (studio only)

Styling:
  @tailwindcss/vite@^4.3.2 → tailwindcss@^4.3.2
  clsx + tailwind-merge

State/Data:
  @tanstack/react-query@^5.101.2
  zustand@^5.0.14
  react-router-dom@^7.18.1 (MCC, WCC)

Dev:
  typescript@~6.0.2
  oxlint@^1.71.0 (Rust-based linter)
```

---

## 3. Rust/Cargo Dependencies

### All Tauri apps (Studio, MCC, WCC)
```toml
[dependencies]
tauri = "2.0"
serde = { version = "1", features = ["derive"] }
serde_json = "1"

[build-dependencies]
tauri-build = "2.0"
```

---

## 4. Inter-Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                         BUILD SYSTEM                             │
│  build/build.py (orchestrator)                                   │
│  ├── build/config.py → shared by all build modules              │
│  ├── build/frontend.py → builds 4 frontends                     │
│  ├── build/pyinstaller_builder.py → 3 PyInstaller targets       │
│  ├── build/tauri_builder.py → 3 Tauri targets                   │
│  ├── build/package.py → ZIP + checksums                          │
│  ├── build/release.py → installer scripts + reports             │
│  ├── build/setup_builder.py → AIClusterSetup.exe                │
│  ├── build/sign.py → authenticode (opt-in)                      │
│  └── build/verification/ → 10-stage release verification        │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MASTER SERVER                               │
│  backend/app/main.py ──entry point──                            │
│  ├── backend/app/config.py    (settings)                        │
│  ├── backend/app/database.py  (SQLAlchemy async engine)         │
│  │   └── backend/app/models/* (50+ ORM tables)                  │
│  │       └── shared/py/       (enums, WorkerInfo)               │
│  ├── backend/app/api/v1/*     (19 route groups)                  │
│  │   ├── backend/app/schemas/ (Pydantic models)                  │
│  │   │   └── shared/py/       (shared schemas)                   │
│  │   └── backend/app/services/* (business logic)                 │
│  ├── backend/app/services/scheduler.py (background loop)         │
│  ├── backend/app/services/auth.py (JWT + bcrypt)                 │
│  ├── backend/app/websocket/manager.py (real-time)                │
│  ├── backend/app/audit/* (middleware + service)                  │
│  ├── backend/app/ai/* (runtime: providers, routing, sessions)    │
│  ├── backend/app/agents/* (multi-agent orchestrator)             │
│  ├── backend/app/workflow/* (DAG engine)                        │
│  ├── backend/app/repository/* (code intelligence)                │
│  ├── backend/app/engineering/* (software pipeline)               │
│  ├── backend/app/plugins/* (SDK + hooks)                        │
│  └── backend/app/production/* (monitoring)                      │
└──────────────┬──────────────────────────────────────────────────┘
               │ HTTP REST + WebSocket
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WORKER FLEET                                │
│  worker/app/main.py ──entry point──                             │
│  ├── worker/app/config.py (layered config)                      │
│  ├── worker/app/core/ (constants, state machine)                 │
│  ├── worker/app/services/                                       │
│  │   ├── registrar.py → POST /register to master                │
│  │   ├── heartbeat.py → POST /heartbeat to master               │
│  │   ├── poller.py → GET /next-job from master                  │
│  │   ├── reporter.py → POST /progress, /result to master        │
│  │   └── monitor.py → psutil system data                        │
│  ├── worker/app/executor/                                       │
│  │   ├── registry.py (jobs type → handler map)                  │
│  │   └── handlers/ (echo, sleep, dir_scan, hash_file, count)    │
│  └── worker/app/utils/ (HTTP client, retry)                     │
└─────────────────────────────────────────────────────────────────┘
               │ HTTP (API calls)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SHARED CONTRACTS                            │
│  shared/                                                         │
│  ├── protocol/ (wire-level DTOs: register, heartbeat, jobs)      │
│  ├── py/ (domain enums, API schemas, WorkerInfo)                 │
│  └── ts/ (TypeScript mirror of py/ schemas)                      │
│                                                                   │
│  Used by: backend, worker, frontend, MCC, WCC                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Web Dashboard)                    │
│  frontend/ (Next.js 15 App Router)                               │
│  ├── src/app/layout.tsx (root: ThemeProvider + QueryProvider)    │
│  ├── src/app/page.tsx (auth redirect)                            │
│  ├── src/app/login/page.tsx (login form)                         │
│  ├── src/app/(dashboard)/layout.tsx (sidebar + topbar shell)     │
│  │   └── src/components/layout/sidebar.tsx (10 nav items)        │
│  │   └── src/components/layout/topbar.tsx (search, user menu)    │
│  ├── src/app/(dashboard)/dashboard/page.tsx → GET /api/v1/dashboard
│  ├── src/app/(dashboard)/workers/page.tsx → GET /api/v1/workers
│  ├── src/stores/auth-store.ts → POST /api/v1/auth/login          │
│  └── src/types/index.ts (interfaces mirroring shared/ts/)        │
│                                                                   │
│  API calls proxied via next.config.ts rewrite:                    │
│    /api/* → http://localhost:8000 (master server)                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DESKTOP APPS                                │
│                                                                   │
│  Studio (Tauri v2):                                              │
│  ├── Rust shell (lib.rs: minimal Tauri builder)                  │
│  └── React SPA (Vite + React 19)                                 │
│      ├── Dependencies: zustand, react-query, resizable-panels     │
│      └── Status: Early dev (starter template)                     │
│                                                                   │
│  Master Control Center (Tauri v2):                                │
│  ├── Rust shell (lib.rs: minimal Tauri builder)                  │
│  ├── Frontend (React SPA):                                       │
│  │   ├── 11 pages (Dashboard, Workers, Cluster, Discovery, etc.) │
│  │   └── lib/api.ts → GET http://127.0.0.1:8800/api/*            │
│  └── Backend (FastAPI port 8800):                                │
│      ├── api/router.py → 19 endpoints                            │
│      └── HTTP proxy to http://localhost:8000 (master API)         │
│                                                                   │
│  Worker Control Center (Tauri v2):                                │
│  ├── Rust shell (lib.rs: minimal Tauri builder)                  │
│  ├── Frontend (React SPA):                                       │
│  │   ├── 9 pages (Welcome, Install, Config, Dashboard, etc.)     │
│  │   └── lib/api.ts → GET http://127.0.0.1:8900/api/*            │
│  └── Backend (FastAPI port 8900):                                │
│      ├── api/router.py → 16 endpoints                            │
│      ├── Worker process lifecycle management                     │
│      └── HTTP to http://localhost:8000 (master API)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Database Dependency Map

```
SQLite Database (aicluster.db)
  │
  ├── Core Tables (used by API services):
  │   ├── users → AuthService, auth routes
  │   ├── workers → WorkerManagerService, worker routes
  │   ├── jobs → SchedulerService, job routes
  │   └── system_logs → LogService, log routes
  │
  ├── Workflow Tables (used by WorkflowEngine):
  │   ├── workflows
  │   ├── workflow_tasks
  │   ├── task_dependencies
  │   ├── workflow_results
  │   ├── artifacts
  │   ├── execution_metrics
  │   ├── cache
  │   ├── workflow_events
  │   └── worker_capabilities
  │
  ├── Repository Tables (used by Repository Intelligence):
  │   ├── repositories
  │   ├── repository_files
  │   ├── symbols
  │   ├── symbol_imports
  │   ├── symbol_references
  │   ├── dependency_edges
  │   ├── code_metrics
  │   ├── knowledge_nodes
  │   ├── knowledge_edges
  │   ├── repository_cache
  │   └── repository_events
  │
  ├── AI Tables (used by AI Runtime):
  │   ├── ai_models
  │   ├── ai_sessions
  │   ├── ai_messages
  │   ├── prompt_templates
  │   ├── tool_definitions
  │   ├── tool_calls
  │   ├── ai_memory
  │   ├── ai_provider_config
  │   └── runtime_metrics
  │
  ├── Agent Tables (used by Multi-Agent Engine):
  │   ├── agents
  │   ├── agent_tasks
  │   ├── agent_messages
  │   ├── agent_reviews
  │   ├── agent_merges
  │   ├── agent_memory_store
  │   └── agent_metrics
  │
  ├── Engineering Tables (used by Engineering Engine):
  │   ├── engineering_plans
  │   ├── engineering_tasks
  │   ├── engineering_patches
  │   ├── engineering_validations
  │   ├── engineering_repairs
  │   ├── engineering_quality
  │   ├── engineering_approvals
  │   ├── engineering_metrics
  │   └── engineering_reports
  │
  ├── Studio Tables:
  │   ├── studio_workspaces
  │   ├── studio_projects
  │   ├── studio_layouts
  │   ├── studio_bookmarks
  │   ├── studio_preferences
  │   └── studio_history
  │
  └── Audit Tables:
      ├── audit_logs
      ├── audit_settings
      ├── audit_exports
      └── audit_retention
```

---

## 6. REST API Dependencies

```
Master API (:8000)
  │
  ├── POST /api/v1/auth/login ────────────── AuthService.authenticate()
  │
  ├── GET /api/v1/health ─────────────────── WorkerManagerService.count()
  │
  ├── GET /api/v1/dashboard ──────────────── WorkerManagerService.get_dashboard()
  │                                         SchedulerService.get_running_count()
  │
  ├── POST /api/v1/workers/register ──────── WorkerManagerService.register()
  ├── POST /api/v1/workers/heartbeat ─────── WorkerManagerService.process_heartbeat()
  ├── GET /api/v1/workers/{id}/next-job ──── SchedulerService.get_next_for_worker()
  ├── POST /api/v1/workers/{id}/progress ─── SchedulerService.update_progress()
  ├── POST /api/v1/workers/{id}/result ───── SchedulerService.complete_job()
  │
  ├── POST /api/v1/jobs ──────────────────── SchedulerService.create_job()
  ├── GET /api/v1/jobs ───────────────────── SchedulerService.get_all()
  ├── DELETE /api/v1/jobs/{id} ───────────── SchedulerService.cancel_job()
  │
  ├── GET /api/v1/logs ───────────────────── LogService.get_all()
  │
  ├── POST /api/v1/ai/chat ───────────────── SessionManager + ConversationManager
  │                                       + ModelRouter + PromptBuilder
  │
  ├── POST /api/v1/agents/run ────────────── AgentRegistry + Orchestrator
  │
  ├── POST /api/v1/engineering/plan ──────── GoalAnalyzer + Planner
  │
  ├── POST /api/v1/workflow ──────────────── WorkflowEngine + Planner
  │
  ├── POST /api/v1/repositories ──────────── RepositoryIndexer
  │
  ├── POST /api/v1/plugins/install ───────── ManifestService + PluginLoader
  │
  └── GET /api/v1/audit/logs ─────────────── AuditService.search()
```

---

## 7. WebSocket Dependencies

```
WebSocket /ws
  │
  ├── WorkerManagerService (worker updates)
  ├── SchedulerService (job updates)
  ├── Dashboard aggregation
  └── WebSocketManager (broadcast to all clients)
```

---

## 8. External Service Dependencies

```
AICluster Master (:8000)
  │
  ├── (Optional) Ollama API → http://localhost:11434
  │   └── Used by: AI Runtime OllamaProvider
  │
  ├── (Optional) llama.cpp → configurable URL
  │   └── Used by: AI Runtime LlamaCppProvider
  │
  └── (Optional) OpenAI-compatible API → configurable URL
      └── Used by: AI Runtime OpenAIProvider
```
