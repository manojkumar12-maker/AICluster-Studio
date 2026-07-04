# AICluster Execution Flow

## 1. Application Startup Sequence

### Timeline (T+0s to T+18s)

```
T+0.0s  User launches AIClusterSetup.exe
T+0.5s  Inno Setup wizard: Python/VC++ detection
T+2.0s  Binary extraction to Program Files
T+3.0s  Python 3.12+ installed (if missing)
T+4.0s  VC++ Redist installed (if missing)
T+5.0s  Firewall rules created
T+6.0s  Start Menu shortcuts created
T+7.0s  First launch triggered

T+7.5s  AIClusterMaster.exe starts
        ├── Load Python interpreter from bundle
        ├── Import app.main
        ├── Lifespan context manager enters
        │   ├── setup_logging() → console + rotating file
        │   ├── init_db() → create_all() for 50+ tables
        │   ├── seed_default_admin() → insert admin/admin123
        │   ├── start background tasks:
        │   │   ├── check_offline_workers() loop (10s interval)
        │   │   └── scheduler.start() loop (2s interval)
        │   └── WebSocket manager ready
        ├── CORS middleware registered
        ├── 19 route groups mounted under /api/v1
        ├── Audit middleware registered
        ├── Uvicorn binds port 8000
        └── ASGI server ready

T+9.0s  Web Dashboard (Next.js) starts
        ├── node server on port 3000
        ├── SSR renders login page
        ├── Client-side JS hydrates
        └── Auth check → redirect to /login or /dashboard

T+10s   AIClusterWorker.exe (on worker machines) starts
        ├── Load config (config.json → .env → defaults)
        ├── WorkerState = STARTING → LOADING_CONFIG → CONNECTING
        ├── POST /api/v1/workers/register → get worker_id
        ├── WorkerState = REGISTERING → ONLINE
        ├── Spawn heartbeat loop (5s interval)
        └── Spawn poll loop → GET /next-job

T+12s   User opens Master Control Center
        ├── Tauri window loads React SPA
        ├── Polls GET /api/health (port 8800 backend)
        ├── Backend proxies to GET /api/v1/health (port 8000 master)
        └── Dashboard shows cluster overview

T+15s   User logs in via Web Dashboard
        ├── POST /api/v1/auth/login (admin/admin123)
        ├── JWT token returned
        ├── Stored in localStorage via Zustand persist
        ├── Redirected to /dashboard
        ├── React Query starts polling:
        │   ├── GET /api/v1/dashboard (2s interval)
        │   └── GET /api/v1/workers (3s interval)
        └── WebSocket connects to /ws

T+18s   System fully operational
        ├── Master serving REST + WebSocket on :8000
        ├── Worker(s) registered, heartbeating, polling
        ├── Dashboard showing live metrics
        ├── Scheduler processing job queue
        └── All background tasks running
```

---

## 2. Master Startup (Detailed)

```
main.py: FastAPI app created with lifespan=lifespan
  │
  ├── lifespan() called on startup:
  │   ├── setup_logging()
  │   │   ├── Console handler (INFO+)
  │   │   └── RotatingFileHandler (10MB, 5 backups)
  │   │
  │   ├── init_db()
  │   │   ├── Import all model classes (user, worker, job, log, workflow,
  │   │   │   repository, ai, agent, engineering, studio, audit)
  │   │   └── Base.metadata.create_all(engine)
  │   │       ├── Creates 50+ tables
  │   │       └── Creates indexes (jobs.priority_created_at, logs.level_created_at, etc.)
  │   │
  │   ├── AuthService.seed_default_admin()
  │   │   ├── Check if admin user exists
  │   │   └── If not: insert User(admin, bcrypt("admin123"), role="admin")
  │   │
  │   ├── asyncio.create_task(check_offline_workers())
  │   │   └── Every 10s:
  │   │       └── WorkerManagerService.mark_offline_workers()
  │   │           ├── SELECT * FROM workers WHERE last_seen < now - 30s
  │   │           └── UPDATE status = 'offline' for stale workers
  │   │
  │   ├── SchedulerService.start()
  │   │   └── asyncio.create_task(_scheduler_loop())
  │   │       └── Every 2s: process_queue()
  │   │           ├── SELECT * FROM jobs WHERE status = 'queued' ORDER BY priority, created_at LIMIT 10
  │   │           ├── For each job:
  │   │           │   ├── _find_available_worker()
  │   │           │   │   ├── SELECT * FROM workers WHERE status = 'online' AND NOT is_paused
  │   │           │   │   └── Pick least-loaded (round-robin or lowest cpu_percent)
  │   │           │   ├── _assign_job(worker, job)
  │   │           │   │   ├── UPDATE job SET status='running', assigned_worker=worker.id, started_at=now
  │   │           │   │   └── UPDATE worker SET status='busy', current_job=job.id
  │   │           │   └── ws_manager.broadcast_job_update(job)
  │   │           └── ws_manager.broadcast_dashboard(dashboard_data)
  │   │
  │   └── yield (application is ready to serve)
  │
  ├── FastAPI middleware stack:
  │   ├── CORSMiddleware (allows all origins)
  │   ├── AuditMiddleware (captures all requests)
  │   └── Router middleware (route handling)
  │
  ├── Route mounting:
  │   ├── /api/v1/health → health.py
  │   ├── /api/v1/auth → auth.py
  │   ├── /api/v1/workers → workers.py
  │   ├── /api/v1/jobs → jobs.py
  │   ├── /api/v1/dashboard → dashboard.py
  │   ├── /api/v1/logs → logs.py
  │   ├── /api/v1/workflow → workflows.py
  │   ├── /api/v1/repositories → repositories.py
  │   ├── /api/v1/ai → ai.py
  │   ├── /api/v1/agents → agents.py
  │   ├── /api/v1/engineering → engineering.py
  │   ├── /api/v1/production → production.py
  │   ├── /api/v1/plugins → plugins.py
  │   ├── /api/v1/studio → studio/ (workspaces, projects, layout)
  │   └── /api/v1/audit → audit/api.py
  │
  ├── WebSocket endpoint: /ws
  │   └── Accepts connection, adds to ws_manager
  │       ├── Handles ping/pong keepalive
  │       └── Receives broadcasts on worker/job/dashboard events
  │
  ├── Static files: /static/
  │   └── Serves dashboard.html at /
  │
  └── Uvicorn serves ASGI app on 0.0.0.0:8000
```

---

## 3. Database Initialization

```
init_db() called in lifespan
  │
  ├── Step 1: Import all model files
  │   ├── app.models.__init__ → Worker, Job, SystemLog, User
  │   ├── app.models.workflow → Workflow, WorkflowTask, TaskDependency, Artifact, etc.
  │   ├── app.models.repository → Repository, RepositoryFile, Symbol, etc.
  │   ├── app.models.ai → AIModel, AISession, AIMessage, PromptTemplate, etc.
  │   ├── app.models.agent → Agent, AgentTask, AgentMessage, etc.
  │   ├── app.models.engineering → EngineeringPlan, EngineeringTask, etc.
  │   ├── app.models.studio → StudioWorkspace, StudioProject, etc.
  │   ├── app.models.audit → AuditLog, AuditSetting, AuditExport, AuditRetention
  │
  ├── Step 2: Base.metadata.create_all(engine)
  │   ├── Creates tables if they don't exist
  │   ├── Creates indexes
  │   └── Idempotent (IF NOT EXISTS)
  │
  └── Step 3: AuthService.seed_default_admin()
      ├── SELECT * FROM users WHERE username = 'admin'
      └── If not found: INSERT INTO users (...)
```

---

## 4. Scheduler Execution Flow

```
SchedulerService._scheduler_loop() runs every 2 seconds
  │
  ├── _process_queue()
  │   ├── BEGIN (implicit SQLite transaction)
  │   │
  │   ├── Fetch queued jobs:
  │   │   SELECT * FROM jobs
  │   │   WHERE status = 'queued'
  │   │   ORDER BY priority ASC, created_at ASC
  │   │   LIMIT max_queued_jobs
  │   │
  │   ├── For each job:
  │   │   ├── Find available worker:
  │   │   │   SELECT * FROM workers
  │   │   │   WHERE status = 'online'
  │   │   │     AND NOT is_paused
  │   │   │     AND cpu_percent < cpu_limit
  │   │   │   ORDER BY cpu_percent ASC
  │   │   │   LIMIT 1
  │   │   │
  │   │   ├── If worker found:
  │   │   │   ├── UPDATE jobs SET
  │   │   │   │   status = 'running',
  │   │   │   │   assigned_worker = worker.id,
  │   │   │   │   started_at = now
  │   │   │   │   WHERE id = job.id
  │   │   │   │
  │   │   │   ├── UPDATE workers SET
  │   │   │   │   status = 'busy',
  │   │   │   │   current_job = job.id
  │   │   │   │   WHERE id = worker.id
  │   │   │   │
  │   │   │   ├── SystemLog.info(f"Job {job.id} assigned to worker {worker.id}")
  │   │   │   └── ws_manager.broadcast_job_update(job)
  │   │   │
  │   │   └── If no worker found:
  │   │       └── break (stop iterating, no workers available)
  │   │
  │   ├── COMMIT
  │   │
  │   └── Broadcast dashboard update via WebSocket
  │
  └── sleep(2) → repeat
```

---

## 5. Worker Execution Flow

```
Worker startup:
  │
  ├── 1. Load settings: config.json → .env → defaults
  │   ├── master_url = "http://localhost:8000"
  │   ├── worker_name = socket.gethostname()
  │   ├── worker_port = 8001
  │   └── ...
  │
  ├── 2. Setup logging (console + rotating file)
  │
  ├── 3. Create HTTP client (httpx.AsyncClient)
  │
  ├── 4. Create RetryHandler (exponential backoff: 1,2,5,10,30,60s)
  │
  ├── 5. Register job handlers:
  │   ├── "echo" → EchoJobHandler
  │   ├── "sleep" → SleepJobHandler
  │   ├── "dir_scan" → DirectoryScanHandler
  │   ├── "hash_file" → HashFileHandler
  │   └── "count_files" → CountFilesHandler
  │
  ├── 6. Main worker loop (in _run_worker):
  │   ├── While state not SHUTDOWN:
  │   │   ├── state = REGISTERING
  │   │   ├── POST /api/v1/workers/register
  │   │   │   ├── On success → state = ONLINE, worker_id received
  │   │   │   └── On failure → state = NETWORK_FAILURE → RETRY → wait → repeat
  │   │   │
  │   │   ├── While state == ONLINE:
  │   │   │   ├── state = HEARTBEAT
  │   │   │   ├── Send heartbeat (CPU, RAM, disk, network)
  │   │   │   │   └── POST /api/v1/workers/heartbeat
  │   │   │   │
  │   │   │   ├── state = POLL_JOB
  │   │   │   ├── GET /api/v1/workers/{id}/next-job
  │   │   │   │   ├── 200 + job → state = HAS_JOB
  │   │   │   │   ├── 204 (no job) → state = NO_JOB → sleep → continue
  │   │   │   │   ├── 404 (unknown worker) → state = REGISTERING (re-register)
  │   │   │   │   └── Connection error → NETWORK_FAILURE → RETRY
  │   │   │   │
  │   │   │   ├── If HAS_JOB:
  │   │   │   │   ├── state = EXECUTING
  │   │   │   │   ├── handler = registry.get_handler(job.type)
  │   │   │   │   ├── Execute handler (async)
  │   │   │   │   │   ├── Periodic progress reporting
  │   │   │   │   │   │   └── POST /api/v1/workers/{id}/progress
  │   │   │   │   │   └── On completion:
  │   │   │   │   │       └── POST /api/v1/workers/{id}/result
  │   │   │   │   └── state = ONLINE → continue loop
  │   │   │   │
  │   │   │   └── Sleep(HEARTBEAT_INTERVAL) between iterations
  │   │   │
  │   │   └── On SIGINT/SIGTERM:
  │   │       ├── state = SHUTDOWN
  │   │       ├── Cancel current job if executing
  │   │       ├── Stop heartbeat service
  │   │       ├── Close HTTP client
  │   │       └── Exit
```

---

## 6. Job Execution Lifecycle

```
User/System creates job via API:
  │
  ├── POST /api/v1/jobs {type, payload, priority}
  │
  ├── SchedulerService.create_job()
  │   ├── INSERT INTO jobs (id, type, status='queued', payload, priority, created_at)
  │   ├── SystemLog.info(f"Job created: {id}")
  │   └── Broadcast via WebSocket
  │
  ├── SchedulerService._process_queue() (background, 2s interval)
  │   ├── SELECT queued jobs
  │   ├── For each: find available worker
  │   ├── UPDATE job: status='running', assigned_worker=X
  │   ├── UPDATE worker: status='busy', current_job=job.id
  │   └── WebSocket broadcast
  │
  ├── Worker polls GET /api/v1/workers/{id}/next-job
  │   └── Returns job assignment {id, type, payload}
  │
  ├── Worker executes job:
  │   ├── handler = JobRegistry.get_handler(job.type)
  │   ├── result = await handler.execute(job.id, job.payload)
  │   │   ├── While executing, periodically:
  │   │   │   └── POST /api/v1/workers/{id}/progress {job_id, progress, logs}
  │   │   │
  │   │   ├── On success:
  │   │   │   └── POST /api/v1/workers/{id}/result
  │   │   │       {job_id, status='completed', result={...}, duration_ms}
  │   │   │
  │   │   └── On failure:
  │   │       └── POST /api/v1/workers/{id}/result
  │   │           {job_id, status='failed', error="...", duration_ms}
  │   │
  │   ├── Master receives result:
  │   │   ├── UPDATE jobs SET status='completed'|'failed', result/error, finished_at=now
  │   │   ├── UPDATE workers SET status='online', current_job=NULL
  │   │   ├── SystemLog.info/error(...)
  │   │   └── WebSocket broadcast
  │   │
  │   └── Loop back to polling for next job
```

---

## 7. WebSocket Communication

```
Client connects to ws://localhost:8000/ws
  │
  ├── WebSocketManager.connect(websocket)
  │   ├── Accept connection
  │   ├── Check max connections limit
  │   ├── Add to active connections set
  │   └── Log new connection
  │
  ├── Ping/pong keepalive:
  │   ├── Client sends ping every N seconds
  │   ├── Server responds with pong
  │   └── Disconnect on timeout
  │
  ├── Server broadcasts:
  │   ├── broadcast_worker_update(worker_data)
  │   │   └── JSON: {"type": "worker_update", "data": {...}}
  │   │
  │   ├── broadcast_job_update(job_data)
  │   │   └── JSON: {"type": "job_update", "data": {...}}
  │   │
  │   └── broadcast_dashboard(dashboard_data)
  │       └── JSON: {"type": "dashboard", "data": {...}}
  │
  └── Client disconnects:
      ├── WebSocketManager.disconnect(websocket)
      ├── Remove from active connections
      └── Log disconnection
```

---

## 8. Shutdown Sequence

```
SIGINT/SIGTERM received (Ctrl+C, service stop, OS shutdown)
  │
  ├── 1. FastAPI lifespan shutdown phase begins
  │   ├── asyncio.sleep(0) yields to allow pending tasks
  │   │
  │   ├── 2. Cancel background tasks:
  │   │   ├── check_offline_workers task cancelled
  │   │   └── SchedulerService.stop()
  │   │       ├── Set _running = False
  │   │       ├── Cancel _scheduler_loop task
  │   │       └── Wait for task to complete
  │   │
  │   ├── 3. WebSocket connections:
  │   │   └── All active WebSocket connections closed
  │   │
  │   ├── 4. Database:
  │   │   └── Engine disposed
  │   │
  │   └── 5. Lifespan context manager exits → cleanup complete
  │
  ├── 6. Uvicorn shuts down ASGI server
  │
  └── 7. Process exits
```

Worker shutdown:
```
SIGINT/SIGTERM → signal handler sets WorkerState = SHUTDOWN
  │
  ├── Worker loop detects SHUTDOWN state
  │   ├── Cancel current job if executing
  │   │   └── Report result as 'cancelled'
  │   ├── Stop heartbeat service
  │   ├── Close HTTP client
  │   └── FastAPI lifespan handler exits
  │
  └── Clean exit
```
