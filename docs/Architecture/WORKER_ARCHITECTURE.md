# WORKER ARCHITECTURE — Subsystem Design & Protocol Reference

## 1. Overview

The AICluster Worker is a **Python-async service** that runs on every Windows PC in the cluster. It connects to the master, registers itself, sends periodic heartbeats with resource metrics, polls for jobs, executes them under strict resource limits, and reports results. The worker is designed to be **invisible** to the PC user — it runs at `BELOW_NORMAL` priority, caps CPU at 25%, caps RAM at 8 GB, and auto-pauses on user activity.

This document covers the complete architecture: state machine, every protocol, every retry strategy, and every failure mode.

---

## 2. Worker State Machine

The worker lifecycle is governed by the `WorkerState` enum defined in `worker/app/core/state.py`:

```python
class WorkerState(str, Enum):
    STARTING       = "STARTING"
    LOADING_CONFIG = "LOADING_CONFIG"
    CONNECTING     = "CONNECTING"
    REGISTERING    = "REGISTERING"
    ONLINE         = "ONLINE"
    HEARTBEAT      = "HEARTBEAT"
    POLL_JOB       = "POLL_JOB"
    NO_JOB         = "NO_JOB"
    HAS_JOB        = "HAS_JOB"
    EXECUTING      = "EXECUTING"
    REPORT_PROGRESS = "REPORT_PROGRESS"
    REPORT_RESULT  = "REPORT_RESULT"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    RETRY          = "RETRY"
    SHUTDOWN       = "SHUTDOWN"
    STOPPING       = "STOPPING"
    EXIT           = "EXIT"
```

### 2.1 State Diagram

```
                                  ┌──────────────┐
                                  │   STARTING   │
                                  └──────┬───────┘
                                         │
                                  ┌──────▼───────┐
                     ┌───────────│LOADING_CONFIG │
                     │           └──────┬───────┘
                     │                  │
                     │           ┌──────▼───────┐
                     │           │  CONNECTING   │
                     │           └──────┬───────┘
                     │                  │
                     │           ┌──────▼───────┐
                     │           │  REGISTERING  │◄───────────────────────┐
                     │           └──────┬───────┘                        │
                     │                  │  success                       │
                     │           ┌──────▼───────┐                        │
                     │           │    ONLINE     │                        │
                     │           └──────┬───────┘                        │
                     │                  │                                │
                     │           ┌──────▼───────┐                        │
                     │           │   HEARTBEAT   │───failure──┐           │
                     │           └──────┬───────┘            │           │
                     │                  │                    │           │
                     │           ┌──────▼───────┐            │           │
                     │           │   POLL_JOB   │───failure──┼─────┐     │
                     │           └──┬───┬───┬───┘            │     │     │
                     │              │   │   │                │     │     │
                     │         ┌────┘   │   └────┐           │     │     │
                     │    ┌────▼──┐  ┌──▼──┐ ┌───▼──┐       │     │     │
                     │    │NO_JOB │  │HAS_ │ │RATE  │       │     │     │
                     │    │       │  │JOB  │ │LIMIT │       │     │     │
                     │    └───┬───┘  └──┬──┘ └───┬──┘       │     │     │
                     │        │         │        │          │     │     │
                     │    ◄───┘    ┌────▼───┐   ◄──┘          │     │     │
                     │             │EXECUTING│                │     │     │
                     │             └──┬───┬──┘                │     │     │
                     │                │   │                   │     │     │
                     │          ┌─────┘   └──────┐            │     │     │
                     │    ┌─────▼─────┐   ┌──────▼──────┐     │     │     │
                     │    │REPORT     │   │ REPORT      │     │     │     │
                     │    │PROGRESS   │   │ RESULT      │     │     │     │
                     │    │(per 5% or │   │(complete/   │     │     │     │
                     │    │ per 5s)   │   │ fail/cancel) │     │     │     │
                     │    └─────┬─────┘   └──────┬──────┘     │     │     │
                     │          │                 │           │     │     │
                     │          └──────┬──────────┘           │     │     │
                     │                 │                      │     │     │
                     │                 ▼                      │     │     │
                     │           ┌──────────┐                 │     │     │
                     │           │ loop to  │─────────────────┘     │     │
                     │           │ HEARTBEAT│                       │     │
                     │           └──────────┘                       │     │
                     │                                              │     │
                     │           ┌──────────┐                       │     │
                     │           │  RETRY   │◄──────────────────────┘     │
                     │           └────┬─────┘                             │
                     │                │ backoff complete                  │
                     │                └───────────────────────────────────┘
                     │
                     │           ┌──────────┐
                     └──────────►│ SHUTDOWN │
                                └────┬─────┘
                                     │
                                ┌────▼─────┐
                                │ STOPPING │
                                └────┬─────┘
                                     │
                                ┌────▼─────┐
                                │   EXIT   │
                                └──────────┘
```

### 2.2 State Transition Rules

| From | To | Condition |
|---|---|---|
| `STARTING` | `LOADING_CONFIG` | `_run_worker()` invoked |
| `LOADING_CONFIG` | `CONNECTING` | Config parsed, HTTP client created |
| `CONNECTING` | `REGISTERING` | HTTP client ready |
| `REGISTERING` | `ONLINE` | `POST /workers/register` returns 200 with worker_id |
| `REGISTERING` | `RETRY` | Registration fails or times out |
| `RETRY` | `REGISTERING` | Backoff wait complete |
| `ONLINE` | `HEARTBEAT` | First heartbeat cycle starts |
| `HEARTBEAT` | `POLL_JOB` | After `asyncio.sleep(heartbeat_interval)` |
| `POLL_JOB` | `NO_JOB` | `GET /next-job` returns 204 (no job) |
| `POLL_JOB` | `HAS_JOB` | `GET /next-job` returns 200 with job data |
| `POLL_JOB` | `RETRY` | Network failure during poll |
| `POLL_JOB` | `NO_JOB` | Rate limited (429); waits retry-after |
| `HAS_JOB` | `EXECUTING` | Job handler found in registry |
| `EXECUTING` | `REPORT_PROGRESS` | Progress update triggers (≥5% or ≥5s elapsed) |
| `EXECUTING` | `REPORT_RESULT` | Job completes, fails, or is cancelled |
| `NO_JOB` | `HEARTBEAT` | Next loop iteration |
| `REPORT_RESULT` | `HEARTBEAT` | After result reported, loop continues |
| Any | `SHUTDOWN` | SIGINT/SIGTERM received, or `shutdown_event.set()` |
| `SHUTDOWN` | `STOPPING` | Cleanup begins |
| `STOPPING` | `EXIT` | All resources released |

---

## 3. Registration Protocol

### 3.1 Purpose

The worker introduces itself to the master, obtains a unique `worker_id`, and enters the cluster. The master uses this registration to track the worker across its lifetime (even across reconnections).

### 3.2 Protocol Flow

```
Worker                               Master
  │                                    │
  │  POST /api/v1/workers/register     │
  │  {                                 │
  │    "name": "DESKTOP-ABC123",       │
  │    "hostname": "DESKTOP-ABC123",   │
  │    "ip": "192.168.1.42"            │
  │  }                                 │
  │ ───────────────────────────────►   │
  │                                    │
  │  200 OK                            │
  │  { "id": "abc-123-..." }          │
  │ ◄────────────────────────────────  │
  │                                    │
  │  Worker ID stored in memory        │
  │  (self._worker_id)                 │
  │  State → ONLINE                    │
  │  Start heartbeat loop              │
  │  Start job poll loop               │
```

### 3.3 Registration Logic

From `worker/app/services/registrar.py`:

```python
class Registrar:
    def __init__(self, http_client: WorkerHttpClient):
        self.http_client = http_client
        self._worker_id: str | None = None

    async def register(self) -> str | None:
        hostname = settings.get_worker_name()
        ip = self._get_ip_address()

        payload = {
            "name": hostname,
            "hostname": hostname,
            "ip": ip,
        }

        response = await self.http_client.post("/workers/register", json=payload)
        if response.status_code == 200:
            data = response.json()
            self._worker_id = data.get("id")
            return self._worker_id
        return None
```

### 3.4 Master-Side Registration

From `backend/app/services/worker_manager.py`:

```python
class WorkerManagerService:
    async def register(self, name, hostname, ip) -> Worker:
        # Check if worker name already exists (re-registration)
        existing = await self.db.execute(
            select(Worker).where(Worker.worker_name == name)
        )
        worker = existing.scalar_one_or_none()

        if worker:
            # Re-registration: update IP, hostname, set status to online
            worker.ip = ip
            worker.hostname = hostname
            worker.status = "online"
            worker.last_seen = datetime.now(timezone.utc)
        else:
            # First registration: create new Worker record
            worker = Worker(
                worker_name=name,
                hostname=hostname,
                ip=ip,
                status="online",
                last_seen=datetime.now(timezone.utc),
            )
            self.db.add(worker)

        await self.db.commit()
        await self.db.refresh(worker)

        # Log the registration event
        log = SystemLog(level="INFO",
            message=f"Worker '{name}' registered from {ip}",
            source="worker_manager")
        self.db.add(log)
        await self.db.commit()

        return worker
```

### 3.5 Failure Modes

| Error | Worker Behavior | Master Behavior |
|---|---|---|
| Master unreachable | Retry with backoff (1s, 2s, 5s, 10s, 30s, 60s) | N/A |
| 500 Internal Server Error | Retry indefinitely | Log error, return 500 |
| Duplicate name (different host) | Treated as re-registration | Update existing worker record |
| Invalid payload (missing field) | Pydantic validation fails → 422 | Return 422 with error detail |
| Network timeout (10s default) | `httpx.TimeoutException` → None returned → retry | N/A |

---

## 4. Heartbeat Mechanism

### 4.1 Purpose

Heartbeats keep the master informed of every worker's liveness and resource utilization. The master uses heartbeat data for three things:

1. **Failure detection** — If no heartbeat received within `WORKER_TIMEOUT_SECONDS` (default: 15), the worker is marked offline.
2. **Load balancing** — `cpu_percent` and `ram_percent` determine which worker is "least loaded" for the next job assignment.
3. **Dashboard display** — Real-time cluster metrics are sourced from heartbeat data.

### 4.2 Protocol Flow

```
Worker (every 5s)                    Master
  │                                    │
  │  POST /api/v1/workers/heartbeat    │
  │  {                                 │
  │    "id": "abc-123-...",           │
  │    "cpu": 12.5,                   │
  │    "ram": 34.2,                   │
  │    "disk": 55.1,                  │
  │    "temperature": null,           │
  │    "busy": false,                 │
  │    "network_speed": 1024.5,       │
  │    "version": "1.0.0"             │
  │  }                                 │
  │ ───────────────────────────────►   │
  │                                    │
  │  200 OK { "status": "ok" }        │
  │ ◄────────────────────────────────  │
  │                                    │
  │  If 404: worker unknown → re-register
  │  If timeout: continue, log warning
```

### 4.3 Heartbeat Service

From `worker/app/services/heartbeat.py`:

```python
class HeartbeatService:
    def __init__(self, worker_id: str, http_client: WorkerHttpClient):
        self.worker_id = worker_id
        self.http_client = http_client
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        self._running = False

    async def _heartbeat_loop(self):
        while self._running:
            await self._send_heartbeat()
            await asyncio.sleep(settings.heartbeat_interval)  # default: 5s

    async def _send_heartbeat(self):
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        payload = {
            "id": self.worker_id,
            "cpu": round(cpu, 1),
            "ram": round(mem.percent, 1),
            "disk": round(disk.percent, 1),
            "temperature": None,
            "busy": False,
            "network_speed": round((net.bytes_sent + net.bytes_recv) / 1024, 1),
            "version": "1.0.0",
        }

        response = await self.http_client.post("/workers/heartbeat", json=payload)
```

### 4.4 Master-Side Heartbeat Processing

From `backend/app/services/worker_manager.py`:

```python
class WorkerManagerService:
    async def process_heartbeat(self, worker_id, cpu, ram, disk,
                                temperature, busy, network_speed) -> Worker:
        worker = await self.db.get(Worker, worker_id)
        if not worker:
            raise ValueError(f"Worker {worker_id} not found")

        worker.cpu_percent = cpu
        worker.ram_percent = ram
        worker.disk_percent = disk
        worker.temperature = temperature
        worker.network_speed = network_speed
        worker.status = "busy" if busy else "online"
        worker.last_seen = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(worker)
        return worker
```

### 4.5 Offline Detection

A background task runs every 10 seconds on the master:

```python
async def check_offline_workers():
    while True:
        async for db in get_db():
            manager = WorkerManagerService(db)
            marked = await manager.mark_offline_workers()
            if marked:
                logger.info(f"Marked {marked} workers offline")
            break
        await asyncio.sleep(10)

# WorkerManagerService.mark_offline_workers():
def mark_offline_workers(self):
    cutoff = datetime.now(timezone.utc) - timedelta(
        seconds=settings.worker_timeout_seconds  # default: 15
    )
    result = await self.db.execute(
        select(Worker).where(
            Worker.last_seen < cutoff,
            Worker.status.notin_(["offline", "disabled"]),
        )
    )
    workers = result.scalars().all()
    for w in workers:
        w.status = "offline"
        w.current_job = None
    # ... commit and log
```

If a worker's `last_seen` timestamp is more than 15 seconds ago, the master marks it `offline`, clears its `current_job`, logs a WARNING, and broadcasts via WebSocket. The job is NOT automatically retried — it remains in the running state until a scheduler sweep reassigns it (future enhancement).

### 4.6 Heartbeat Timing Diagram

```
Worker                         Master
  │                              │
  ├─ hb(0s) ───────────────────► │ last_seen = T+0s
  ├─ hb(5s) ───────────────────► │ last_seen = T+5s
  ├─ hb(10s) ──────────────────► │ last_seen = T+10s
  │   (worker crashes)
  │                              │ T+15s: offline checker runs
  │                              │ last_seen(T+10s) < cutoff(T+15 - 15 = T+0s)?
  │                              │ NO → still within window
  │                              │ T+20s: offline checker runs
  │                              │ last_seen(T+10s) < cutoff(T+20 - 15 = T+5s)?
  │                              │ NO → still within window
  │                              │ T+25s: offline checker runs
  │                              │ last_seen(T+10s) < cutoff(T+25 - 15 = T+10s)?
  │                              │ NO → exactly at boundary
  │                              │ T+26s: last_seen < cutoff(T+26-15=T+11s)?
  │                              │ YES → marked OFFLINE
  │                              │ broadcast: worker_status = "offline"
  │                              │ log: WARNING "marked offline"
```

**Result:** A worker crash is detected within 11–16 seconds (3–4 missed heartbeats at 5s interval, checked by offline checker every 10s).

---

## 5. Job Polling

### 5.1 Purpose

Workers poll for new jobs when they are idle. The master returns the highest-priority job that has not yet been assigned.

### 5.2 Protocol Flow

```
Worker                              Master
  │                                   │
  │  GET /api/v1/workers/{id}/next-job│
  │ ─────────────────────────────►    │
  │                                   │
  │  Case 1: Job available            │
  │  200 OK                          │
  │  { "job": { "id": "...",         │
  │             "type": "echo",       │
  │             "status": "queued",   │
  │             "priority": 5,        │
  │             "payload": {} } }     │
  │ ◄────────────────────────────    │
  │                                   │
  │  Case 2: No jobs                  │
  │  204 No Content                   │
  │ ◄────────────────────────────    │
  │                                   │
  │  Case 3: Worker paused            │
  │  429 Too Many Requests            │
  │  retry-after: 30                  │
  │ ◄────────────────────────────    │
  │                                   │
  │  Case 4: Worker unknown           │
  │  404 Not Found                    │
  │ → Triggers re-registration        │
  │                                   │
  │  Case 5: Rate limited             │
  │  429 Too Many Requests            │
  │  retry-after: 10                  │
  │ → Waits 10s before next poll      │
```

### 5.3 Poller Service

From `worker/app/services/poller.py`:

```python
class JobPoller:
    def __init__(self, worker_id: str, http_client: WorkerHttpClient):
        self.worker_id = worker_id
        self.http_client = http_client
        self._running = False

    async def start(self):
        self._running = True

    async def poll(self) -> dict | None:
        response = await self.http_client.get(
            f"/workers/{self.worker_id}/next-job"
        )

        if response.status_code == 200:
            return response.json().get("job")
        elif response.status_code == 204:
            return None    # No jobs available
        elif response.status_code == 404:
            # Worker not found → will re-register on next loop
            return None
        elif response.status_code == 429:
            retry_after = response.headers.get("retry-after", "10")
            await asyncio.sleep(int(retry_after))
            return None

        return None
```

### 5.4 Master-Side Job Assignment

From `backend/app/services/scheduler.py`:

```python
class SchedulerService:
    async def get_next_for_worker(self, worker_id: str) -> Job | None:
        # Find highest-priority queued job
        result = await self.db.execute(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if job:
            # Assign job to this worker atomically
            job.status = "running"
            job.assigned_worker = worker_id
            job.started_at = datetime.now(timezone.utc)
            # Mark worker as busy
            worker = await self.db.get(Worker, worker_id)
            worker.status = "busy"
            worker.current_job = job.id
            await self.db.commit()
        return job
```

### 5.5 Polling Timing

```
Worker Lifecycle: Idle → Job
─────────────────────────────────────────────────────

Heartbeat (T+0s)  ──►  POST /heartbeat
Poll (T+0s)       ──►  GET /next-job → 204 (no jobs)
    sleep 5s
Heartbeat (T+5s)  ──►  POST /heartbeat
Poll (T+5s)       ──►  GET /next-job → 200 (job assigned!)
    execute job
    ...
Result (T+12s)    ──►  POST /result → "completed"
Heartbeat (T+10s) ──►  POST /heartbeat (status=busy → online)
Poll (T+15s)      ──►  GET /next-job → 204 (no jobs)
```

---

## 6. Execution Flow

### 6.1 Job Handler Registry

When a job is received, the worker looks up a handler by job type. Handlers are registered at startup:

```python
# worker/app/main.py
job_registry = JobRegistry()
job_registry.register("echo", EchoJobHandler())
job_registry.register("sleep", SleepJobHandler())
job_registry.register("dir_scan", DirectoryScanHandler())
job_registry.register("hash_file", HashFileHandler())
job_registry.register("count_files", CountFilesHandler())
```

The `JobRegistry` (`worker/app/executor/registry.py`) provides lookup:

```python
class JobRegistry:
    def __init__(self):
        self._handlers: dict[str, BaseJobHandler] = {}

    def register(self, job_type: str, handler: BaseJobHandler):
        self._handlers[job_type] = handler

    def get_handler(self, job_type: str) -> BaseJobHandler | None:
        return self._handlers.get(job_type)
```

### 6.2 Execution Sequence

```
Received job { id: "job-1", type: "echo", payload: { "message": "hello" } }
  │
  ├── Lookup handler for "echo" → EchoJobHandler
  │
  ├── Call handler.execute_with_progress(job_id, payload)
  │     (if handler supports streaming progress)
  │     └── async for progress in handler.execute_with_progress():
  │           ├── progress = 10% → REPORT_PROGRESS
  │           ├── progress = 50% → REPORT_PROGRESS  
  │           └── progress = 100% → done
  │
  ├── Call handler.execute(job_id, payload) → result
  │
  ├── REPORT_PROGRESS(100%)
  ├── REPORT_RESULT("completed", result, duration_ms)
  │
  └── State → loop back to HEARTBEAT
```

### 6.3 Execution with Progress Reporting

From `worker/app/main.py`:

```python
async def _execute_job(worker_id: str, job_data: dict):
    job_id = job_data.get("id")
    job_type = job_data.get("type")
    payload = job_data.get("payload", {})

    handler = job_registry.get_handler(job_type)
    if handler is None:
        await reporter.report_result(job_id, "failed",
            error=f"Unknown job type: {job_type}")
        return

    state = WorkerState.EXECUTING

    try:
        # Handler may support streaming progress
        if hasattr(handler, "execute_with_progress"):
            async for progress in handler.execute_with_progress(job_id, payload):
                if _should_report_progress(progress, last_progress, last_report_time):
                    await reporter.report_progress(job_id, progress)

        # Execute and get result
        result = await handler.execute(job_id, payload)

        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        await reporter.report_progress(job_id, 100.0)
        await reporter.report_result(job_id, "completed",
            result=result, duration_ms=duration_ms)

    except asyncio.CancelledError:
        await reporter.report_result(job_id, "cancelled", duration_ms=duration_ms)
    except Exception as e:
        await reporter.report_result(job_id, "failed",
            error=str(e), duration_ms=duration_ms)
```

### 6.4 Progress Reporting Throttle

From `worker/app/main.py`:

```python
def _should_report_progress(
    current: float, last_reported: float, last_report_time: float
) -> bool:
    # Report if progress changed by ≥5%
    if current - last_reported >= PROGRESS_PERCENT_THRESHOLD:  # 5%
        return True
    # Report if ≥5s since last report
    if now - last_report_time >= PROGRESS_INTERVAL:  # 5s
        return True
    return False
```

This prevents flooding the master with progress updates for fast-moving jobs while ensuring at least one update every 5 seconds for slow jobs.

---

## 7. Result Reporting

### 7.1 Protocol

```
Worker                              Master
  │                                   │
  │  POST /workers/{id}/progress     │
  │  { "job_id": "job-1",            │
  │    "progress": 50.0 }            │
  │ ─────────────────────────────►    │
  │  200 OK                          │
  │ ◄────────────────────────────    │
  │                                   │
  │  POST /workers/{id}/progress     │
  │  { "job_id": "job-1",            │
  │    "progress": 100.0 }           │
  │ ─────────────────────────────►    │
  │  200 OK                          │
  │ ◄────────────────────────────    │
  │                                   │
  │  POST /workers/{id}/result       │
  │  { "job_id": "job-1",            │
  │    "status": "completed",         │
  │    "result": { ... },            │
  │    "duration_ms": 1234.5 }       │
  │ ─────────────────────────────►    │
  │  200 OK                          │
  │ ◄────────────────────────────    │
```

### 7.2 Reporter Service

From `worker/app/services/reporter.py`:

```python
class Reporter:
    def __init__(self, worker_id: str, http_client: WorkerHttpClient):
        self.worker_id = worker_id
        self.http_client = http_client

    async def report_progress(self, job_id: str, progress: float,
                              logs: str | None = None) -> bool:
        payload = {
            "job_id": job_id,
            "progress": min(progress, 100.0),
        }
        if logs:
            payload["logs"] = logs

        response = await self.http_client.post(
            f"/workers/{self.worker_id}/progress",
            json=payload,
        )
        return response.status_code == 200

    async def report_result(self, job_id: str, status: str,
                            result: dict | None = None,
                            error: str | None = None,
                            duration_ms: float | None = None,
                            logs: str | None = None) -> bool:
        payload = {"job_id": job_id, "status": status}
        if result: payload["result"] = result
        if error: payload["error"] = error
        if duration_ms: payload["duration_ms"] = duration_ms
        if logs: payload["logs"] = logs

        response = await self.http_client.post(
            f"/workers/{self.worker_id}/result",
            json=payload,
        )
        return response.status_code == 200
```

### 7.3 Master-Side Result Handling

From `backend/app/services/scheduler.py`:

```python
async def complete_job(self, job_id, status, result_data=None,
                       error=None, duration_ms=None) -> Job | None:
    job = await self.db.get(Job, job_id)
    if not job:
        return None

    job.status = status
    job.finished_at = datetime.now(timezone.utc)
    if result_data: job.result = result_data
    if error: job.error = error

    # Free the worker
    if job.assigned_worker:
        worker = await self.db.get(Worker, job.assigned_worker)
        if worker:
            worker.status = "online"
            worker.current_job = None

    await self.db.commit()
    await self.db.refresh(job)
    return job
```

---

## 8. Reconnection Strategy

### 8.1 When Reconnection Occurs

The worker reconnects when:
1. **Registration fails** — Master returns 404 for worker ID on heartbeat or poll.
2. **Network partition** — HTTP requests to master timeout repeatedly.
3. **Master restarts** — Worker gets connection refused.
4. **Worker restart** — Worker process was killed and restarted.

### 8.2 Reconnection Flow

```
Worker detects connection loss (heartbeat/poll failure)
  │
  ├── State → RETRY
  ├── RetryHandler.wait() → exponential backoff
  │     ├── attempt 1: wait 1s
  │     ├── attempt 2: wait 2s
  │     ├── attempt 3: wait 5s
  │     ├── attempt 4: wait 10s
  │     ├── attempt 5: wait 30s
  │     └── attempt 6+: wait 60s (cap)
  ├── Clear worker_id (Registrar.clear())
  ├── State → REGISTERING
  ├── POST /workers/register → new worker_id
  ├── On success:
  │     ├── Reset RetryHandler (attempt = 0)
  │     ├── State → ONLINE
  │     └── Restart heartbeat + poll loops
  └── On failure:
        └── Continue retry loop
```

### 8.3 Retry Handler

From `worker/app/utils/retry.py`:

```python
class RetryHandler:
    def __init__(self, delays: list[int] | None = None):
        self.delays = delays or RETRY_DELAYS  # [1, 2, 5, 10, 30, 60]
        self._attempt = 0

    @property
    def current_delay(self) -> int:
        idx = min(self._attempt, len(self.delays) - 1)
        return self.delays[idx]

    async def wait(self):
        delay = self.current_delay
        logger.info(f"Retry attempt {self._attempt + 1}, waiting {delay}s")
        await asyncio.sleep(delay)
        self._attempt += 1

    def reset(self):
        self._attempt = 0
```

### 8.4 Master-Side Reconnection Handling

The master supports reconnection transparently. When a worker re-registers with the same `name`, the `WorkerManagerService.register()` method finds the existing record and updates it (IP, status, last_seen). The worker keeps the same ID, and any previously assigned job remains in place (the scheduler will detect the orphaned job if the worker does not resume it).

```
Initial Registration:
  Worker "DESKTOP-1" → INSERT INTO workers (id="X", name="DESKTOP-1")
  Worker ID = "X"

Reconnection (same name, same or different IP):
  Worker "DESKTOP-1" → SELECT WHERE name="DESKTOP-1"
                     → UPDATE ip, status="online", last_seen=now
                     → Returns SAME ID "X"
```

---

## 9. Retry Logic

### 9.1 Retry Chain

The worker has two levels of retry:

| Level | Scope | Max Attempts | Backoff | Resets When |
|---|---|---|---|---|
| 1. Network request | Single HTTP request | 1 (no internal retry) | None | N/A |
| 2. Registration | Full registration flow | Infinite (until shutdown) | 1, 2, 5, 10, 30, 60s cap | Registration succeeds |
| 3. Job execution | Individual job | 1 catch (pass/fail result) | None | Next job |

Network request retries are NOT built into the HTTP client. Instead, the outer loop in `_run_worker()` retries the full registration cycle on any failure. This is a deliberate design choice: if the master is unavailable, individual HTTP request retries are wasted; the worker should back off at the registration level.

### 9.2 Key Retry Constants

From `worker/app/core/constants.py`:

```python
RETRY_DELAYS = [1, 2, 5, 10, 30, 60]     # seconds
HTTP_TIMEOUT = 10                           # seconds
REGISTRATION_TIMEOUT = 10
HEARTBEAT_TIMEOUT = 10
POLL_TIMEOUT = 10
PROGRESS_TIMEOUT = 10
RESULT_TIMEOUT = 10
```

### 9.3 Backoff Pattern

```
Attempt 1: wait 1s    → total elapsed: 1s
Attempt 2: wait 2s    → total elapsed: 3s
Attempt 3: wait 5s    → total elapsed: 8s
Attempt 4: wait 10s   → total elapsed: 18s
Attempt 5: wait 30s   → total elapsed: 48s
Attempt 6: wait 60s   → total elapsed: 108s (1m48s)
Attempt 7: wait 60s   → total elapsed: 168s (2m48s)
...
```

The cap at 60 seconds means the worker never polls the master more frequently than once per minute during extended outages.

---

## 10. Timeout Handling

### 10.1 Timeout Constants

All HTTP operations have a 10-second timeout configured in `WorkerHttpClient`:

```python
class WorkerHttpClient:
    def __init__(self, master_url: str, timeout: int = HTTP_TIMEOUT):
        self._client = httpx.AsyncClient(timeout=timeout)
```

Individual operations share the same timeout value, but there are separate named constants for clarity:

| Operation | Timeout | Constant |
|---|---|---|
| Any HTTP request | 10s | `HTTP_TIMEOUT` |
| Registration | 10s | `REGISTRATION_TIMEOUT` |
| Heartbeat | 10s | `HEARTBEAT_TIMEOUT` |
| Job poll | 10s | `POLL_TIMEOUT` |
| Progress report | 10s | `PROGRESS_TIMEOUT` |
| Result report | 10s | `RESULT_TIMEOUT` |

### 10.2 Timeout Behavior

- **Connect timeout** — If the master is unreachable (no SYN-ACK), httpx raises `ConnectError` after 10s.
- **Read timeout** — If the master accepts the connection but does not respond, httpx raises `ReadTimeout` after 10s.
- **Pool timeout** — If all connections are busy, httpx raises `PoolTimeout`.

All timeouts are caught in the calling code:

```python
# In heartbeat, poll, reporter, registrar:
try:
    response = await self.http_client.post(...)
except Exception as e:
    logger.error(f"Heartbeat error: {e}")
    # Outer loop handles retry
```

**Design note:** There is no separate job execution timeout at the worker level. Job handlers are expected to complete in a reasonable timeframe. The master does not enforce a timeout on running jobs (future enhancement: configurable `job_timeout_seconds`).

---

## 11. Graceful Shutdown

### 11.1 Shutdown Trigger

The worker shuts down on:
1. **SIGINT** (Ctrl+C in terminal)
2. **SIGTERM** (sent by Windows service manager or Task Manager)
3. **Corner case:** `shutdown_event.set()` inside the FastAPI lifespan `yield` cleanup

### 11.2 Shutdown Sequence

```python
def _signal_handler(sig, frame):
    state = WorkerState.SHUTDOWN
    shutdown_event.set()

# In main:
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
```

When the signal handler sets `state = SHUTDOWN` and fires `shutdown_event`:

```
SIGINT/SIGTERM received
  │
  ├── state = WorkerState.SHUTDOWN
  ├── shutdown_event.set()
  │
  ├── _worker_loop detects state == SHUTDOWN → exits
  ├── _run_worker stops outer loop
  │
  ├── _cleanup():
  │     ├── heartbeat_service.stop()
  │     ├── http_client.close()
  │     └── logger.info("Worker shutdown complete")
  │
  ├── state = WorkerState.EXIT
  └── FastAPI lifespan yields → uvicorn stops
```

### 11.3 Cleanup Sequence

```python
async def _cleanup():
    if heartbeat_service:
        await heartbeat_service.stop()
    if http_client:
        await http_client.close()
    logger.info("Worker shutdown complete")
```

The `HeartbeatService.stop()` sets `self._running = False`, which causes the heartbeat loop to exit on its next iteration. No final heartbeat is sent — the master will detect the worker as offline via the offline checker.

The HTTP client is closed gracefully (draining pending requests), but the worker does not wait for any in-flight requests to complete — it cancels them.

### 11.4 In-Flight Job Handling

If a worker is shutting down while executing a job:

1. The job execution is **not explicitly cancelled** — it is abandoned.
2. The master will detect the worker offline (missed heartbeats → 15s timeout).
3. The job remains in `running` status with the now-offline worker assigned.
4. The scheduler does **not** automatically reassign it (current limitation — the job stays in limbo until manually re-queued).

**Future enhancement:** The worker's `_execute_job` catches `CancelledError` and reports a "cancelled" result. The cleanup sequence should cancel the current job handler.

---

## 12. Recovery After Crash

### 12.1 Worker Crash Recovery

When a worker crashes (process killed, power loss, segfault) and restarts:

1. **New process starts** — `WorkerState.STARTING`
2. **Registration** — Worker re-registers with the same name, gets the same or new ID:
   - Same name → master does `UPDATE` (reuses existing DB record)
   - New ID → master creates new record
3. **Job state** — Any job that was assigned to the previous incarnation is still `running` on the master. The worker does not know about it and will not automatically resume it.
4. **Heartbeat** — Worker starts fresh heartbeat cycle. Master updates `last_seen`, sets status back to `online`.

### 12.2 Master Crash Recovery

If the master crashes (process killed, system restart):

1. **Workers detect** — All HTTP requests timeout. Workers enter `RETRY` state with exponential backoff.
2. **Workers wait** — Workers retry registration every 1–60 seconds indefinitely.
3. **Master restarts** — SQLite database persists (unless disk corruption). All worker records, jobs, and logs are intact.
4. **Workers re-register** — As master comes back online, workers succeed in registration. They get their original IDs back (matched by name).
5. **Job resumption** — Jobs that were `running` at time of master crash remain `running`. Workers will NOT automatically resume them — they will request the next job via `/next-job`, which returns the next `queued` job, not the still-`running` one.
6. **Session persistence** — AI sessions, agent conversations, and workflow state are all persisted in SQLite. They survive master restart.

### 12.3 Network Partition Recovery

If the network between workers and master is partitioned:

- **Workers cannot reach master** → Registration/heartbeat failures → `RETRY` state → exponential backoff
- **Master cannot reach workers** → Heartbeats stop → `MARK_OFFLINE` after 15s
- **Partition heals** → Workers succeed on next retry → Re-register → Resume normal operation

During a network partition, all in-flight jobs on the partitioned workers continue executing but cannot report progress or results. When the partition heals, the results may be stale; the master treats them as new results for the given job ID.

---

## 13. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        WORKER PROCESS                                 │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    MAIN LOOP (_run_worker)                 │      │
│  │                                                            │      │
│  │  ┌──────────┐   ┌───────────┐   ┌─────────────┐           │      │
│  │  │ Registrar│   │ Heartbeat │   │ JobPoller   │           │      │
│  │  │          │   │ Service   │   │             │           │      │
│  │  │ register │   │ _heartbeat│   │ poll()      │           │      │
│  │  │()        │   │ _loop()   │   │             │           │      │
│  │  └────┬─────┘   └─────┬─────┘   └──────┬──────┘           │      │
│  │       │               │                │                   │      │
│  │       └───────────────┼────────────────┘                   │      │
│  │                       │                                    │      │
│  │              ┌────────▼────────┐                           │      │
│  │              │  WorkerHttpClient│                          │      │
│  │              │  (httpx.Async   │                           │      │
│  │              │   Client)       │                           │      │
│  │              └────────┬────────┘                           │      │
│  │                       │                                    │      │
│  └───────────────────────┼────────────────────────────────────┘      │
│                          │                                           │
│  ┌───────────────────────┼────────────────────────────────────┐      │
│  │              ┌────────▼────────┐                           │      │
│  │              │  Job Execution  │                           │      │
│  │              │                 │                           │      │
│  │  ┌───────────▼─────┐   ┌──────▼─────────┐                 │      │
│  │  │   JobRegistry   │   │   Reporter     │                 │      │
│  │  │                 │   │                │                 │      │
│  │  │ register()      │   │ reportProgress │                 │      │
│  │  │ get_handler()   │   │ reportResult() │                 │      │
│  │  └───────────┬─────┘   └──────┬─────────┘                 │      │
│  │              │                │                           │      │
│  │     ┌────────▼────────┐      │                           │      │
│  │     │  Job Handlers   │      │                           │      │
│  │     │                 │      │                           │      │
│  │     │ EchoJobHandler  │      │                           │      │
│  │     │ SleepJobHandler │      │                           │      │
│  │     │ DirScanHandler  │      │                           │      │
│  │     │ HashFileHandler │      │                           │      │
│  │     │ CountFilesHndlr │      │                           │      │
│  │     └─────────────────┘      │                           │      │
│  └──────────────────────────────┼───────────────────────────┘      │
│                                 │                                   │
│  ┌──────────────────────────────▼───────────────────────────┐      │
│  │              SystemMonitor (psutil)                      │      │
│  │                                                          │      │
│  │  cpu_percent() │ ram_info() │ disk_usage() │ network_io()│      │
│  │  temperature() │ uptime()   │ system_info()             │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │              RetryHandler                                  │      │
│  │  Exponential backoff: 1s, 2s, 5s, 10s, 30s, 60s           │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │              WorkerState (state machine)                    │      │
│  │  STARTING → LOADING_CONFIG → CONNECTING → REGISTERING →    │      │
│  │  ONLINE → HEARTBEAT → POLL_JOB → (NO_JOB | HAS_JOB) →     │      │
│  │  EXECUTING → REPORT_PROGRESS → REPORT_RESULT → ...         │      │
│  └────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 14. Configuration Reference

### 14.1 Worker Config (config.json / environment)

| Key | Type | Default | Description |
|---|---|---|---|
| `master_url` | string | `http://localhost:8000` | Master server URL |
| `worker_host` | string | `0.0.0.0` | Worker HTTP server bind address |
| `worker_port` | integer | `8001` | Worker HTTP server port |
| `worker_name` | string | `socket.gethostname()` | Display name in cluster |
| `cpu_limit` | float | `25.0` | Maximum CPU utilization (%) |
| `ram_limit_gb` | float | `8.0` | Maximum RAM usage (GB) |
| `heartbeat_interval` | integer | `5` | Heartbeat interval (seconds) |
| `poll_interval` | integer | `5` | Job poll interval (seconds) |
| `log_level` | string | `"INFO"` | Logging level |

### 14.2 Worker Constants (constants.py)

| Constant | Value | Description |
|---|---|---|
| `HEARTBEAT_INTERVAL` | `5` | Seconds between heartbeats |
| `POLL_INTERVAL` | `5` | Seconds between job polls |
| `PROGRESS_INTERVAL` | `5` | Min seconds between progress updates |
| `PROGRESS_PERCENT_THRESHOLD` | `5` | Min progress change (%) to report |
| `RETRY_DELAYS` | `[1, 2, 5, 10, 30, 60]` | Exponential backoff schedule |
| `HTTP_TIMEOUT` | `10` | Default HTTP timeout (seconds) |

---

## 15. Key Files Reference

| File | Purpose |
|---|---|
| `worker/app/main.py` | Entry point, lifecycle, signal handling |
| `worker/app/core/state.py` | `WorkerState` enum — state machine definitions |
| `worker/app/core/constants.py` | Timeouts, intervals, retry delays |
| `worker/app/config.py` | `WorkerSettings` — configuration model |
| `worker/app/services/registrar.py` | `Registrar` — registration protocol |
| `worker/app/services/heartbeat.py` | `HeartbeatService` — heartbeat loop |
| `worker/app/services/poller.py` | `JobPoller` — job polling protocol |
| `worker/app/services/reporter.py` | `Reporter` — progress & result reporting |
| `worker/app/services/monitor.py` | `SystemMonitor` — system metrics collection |
| `worker/app/executor/registry.py` | `JobRegistry` — handler registry |
| `worker/app/executor/handlers/` | Built-in job handlers (echo, sleep, dir_scan, hash_file, count_files) |
| `worker/app/utils/retry.py` | `RetryHandler` — exponential backoff |
| `worker/app/utils/http_client.py` | `WorkerHttpClient` — HTTP transport layer |

---

*End of WORKER_ARCHITECTURE.md — This document covers the complete worker subsystem design for the AICluster distributed compute platform.*
