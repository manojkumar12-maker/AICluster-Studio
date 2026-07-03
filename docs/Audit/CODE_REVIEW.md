# CODE REVIEW — AICluster v1.3.0

## Scope

This code review covers the entire Python backend (`backend/app/`), worker agent (`worker/app/`), and shared modules (`shared/`). Each finding references exact file paths and line numbers. Categories: CRITICAL (must fix), MAJOR (should fix), MINOR (nice to fix).

---

## CRITICAL Findings (12 items)

### C1. No Authentication Enforced on Any API Endpoint
**Files**: All `backend/app/api/v1/*.py`
**Lines**: Route definitions throughout
**Issue**: The `get_current_user` dependency is defined in `services/auth.py:64-98` but is never applied to any route. All endpoints are publicly accessible.
**Impact**: Anyone on the network can access all cluster operations.

### C2. JWT Secret Hardcoded with Well-Known Default
**File**: `backend/app/config.py:14`
**Lines**: 14
**Issue**: `secret_key: str = "aicluster-secret-key-change-in-production"` — this default is published in the README and source code, making it possible to forge arbitrary JWT tokens.
**Impact**: Complete authentication bypass.

### C3. Plugin Upload Allows Arbitrary Code Execution
**File**: `backend/app/api/v1/plugins.py:53-66`
**Lines**: 53-66
**Issue**: ZIP file is extracted without validation, then the extracted Python module is imported and executed. No authentication, no sandboxing, no validation of plugin contents.
**Impact**: Full remote code execution on the master server.

### C4. Blocking IO in Async Worker Handlers
**Files**:
- `worker/app/executor/handlers/dir_scan.py:15` — `os.walk()` is synchronous and blocking
- `worker/app/executor/handlers/hash_file.py:16` — `open(filepath, "rb")` and `f.read()` are synchronous
- `worker/app/executor/handlers/count_files.py:14` — `os.walk()` is synchronous and blocking
- `worker/app/executor/handlers/dir_scan.py:21` — `os.path.getsize()` is synchronous
**Issue**: All these handlers run in the async event loop. Blocking operations freeze the event loop, preventing heartbeat sending, job polling, and graceful shutdown. For large directories or files, this blocks the worker entirely.
**Impact**: Worker becomes unresponsive during job execution. Heartbeats stop, master marks worker offline, jobs time out.

### C5. Dead Code in Scheduler — Duration Never Stored
**File**: `backend/app/services/scheduler.py:191-192`
**Lines**: 191-192
**Issue**: The `duration_ms` parameter is captured but the code does `pass` instead of storing it in the job record. This means job execution times are never persisted.
**Code**:
```python
if duration_ms is not None:
    pass  # Should be: job.duration_ms = duration_ms
```
**Impact**: Dashboard cannot display job execution times. Analytics/metrics are broken.

### C6. No async Wrapping for Heavy CPU Operations
**File**: `backend/app/repository/search/service.py:72-88`
**Lines**: 72-88
**Issue**: `search_text()` opens files with `open()` and reads them line by line inside an async endpoint. This is blocking IO that will hang the event loop for large repositories.
**Impact**: API endpoint blocks the event loop during text search, affecting all concurrent requests.

### C7. Double-Commit in `get_next_for_worker`
**File**: `backend/app/services/scheduler.py:147-175`
**Lines**: 166-174
**Issue**: The method calls `await self.db.commit()` at line 166 after assigning the job, then again at line 174 after adding a log entry. The second commit is redundant but also means the log entry is only persisted after the second commit. If the first commit succeeds but the second fails, the job is running but the log is lost.
**Impact**: Inconsistent state between job assignments and log entries.

### C8. Worker HTTP Client Sends No Authentication
**File**: `worker/app/utils/http_client.py:14-20`
**Lines**: 14-20
**Issue**: The HTTP client sends requests to the master API without any authentication headers. Any machine on the LAN can impersonate a worker.
**Impact**: Complete lack of worker identity verification.

### C9. `complete_job` Doesn't Validate `status` Parameter
**File**: `backend/app/services/scheduler.py:177-209`
**Lines**: 177-178
**Issue**: The `status` parameter accepts any string value and stores it directly in the database. There is no validation that the status is one of the allowed values ("completed", "failed", "cancelled", "timeout"). The worker could report arbitrary status values.
**Impact**: Data integrity issue — workers can report arbitrary statuses, breaking dashboard aggregations.

### C10. Broadcast Loop Can Block WebSocket Endpoint
**File**: `backend/app/websocket/manager.py:28-39`
**Lines**: 33-37
**Issue**: `broadcast()` iterates all active connections and sends messages sequentially. A slow or disconnected client causes the loop to block, delaying messages to all other clients. The dead connection cleanup happens after the loop, not during.
**Impact**: A single slow WebSocket client can delay broadcasts to all other connected clients.

### C11. Default Rate Limiting Not Implemented Despite Claim
**File**: `backend/app/main.py`
**Issue**: PROJECT_STATE.md line 44 claims "Rate limiting on API endpoints" as completed, but no rate limiting middleware or logic exists anywhere in the codebase.
**Impact**: No protection against brute force or DoS attacks.

### C12. Search Service Opens Arbitrary Files
**File**: `backend/app/repository/search/service.py:72-84`
**Lines**: 72-84
**Issue**: The file search opens files on the file system using paths from the database. If the repository path has been manipulated or contains a symbolic link, an attacker could read arbitrary files on the server.
**Impact**: Path traversal vulnerability — arbitrary file read on the master server.

---

## MAJOR Findings (35 items)

### M1. Unused Import in workers.py
**File**: `backend/app/api/v1/workers.py`
**Line**: 7 (import `ws_manager`)
**Issue**: `ws_manager` is used in the route handlers, so this is not actually unused. But the `Response` import (line 1) is only used in one place (line 156). This is fine.

### M2. Unused Imports in scheduler.py
**File**: `backend/app/services/scheduler.py`
**Lines**: 1, 4
**Issue**: `import asyncio` (line 1) is used. `from typing import Optional` (line 4) is used in the type annotation. Both are used.

### M3. Unused Imports in base.py (Worker Executor)
**File**: `worker/app/executor/base.py`
**Line**: 1
**Issue**: `import logging` — the logger is defined but never used in the base class.
**Impact**: Minor dead code, but suggests incomplete implementation.

### M4. Unused Imports in worker_register.py
**File**: `worker/app/services/registrar.py`
**Line**: 3
**Issue**: `import socket` is imported but the method `self._get_ip_address()` uses it. Actually checking — it IS used at line 50. Fine.

### M5. Unused Import in worker heartbeat.py
**File**: `worker/app/services/heartbeat.py`
**Line**: 7
**Issue**: `from ..core.constants import HEARTBEAT_INTERVAL` is imported but never used — `settings.heartbeat_interval` is used instead (line 35).

### M6. Unused Import in worker poller.py
**File**: `worker/app/services/poller.py`
**Line**: 5
**Issue**: `from ..core.constants import POLL_INTERVAL` imported but never used.

### M7. Empty Except in websocket manager
**File**: `backend/app/websocket/manager.py`
**Line**: 36
**Issue**: `except Exception:` without any logging or handling. Failed sends are silently ignored after adding to the dead list.
**Impact**: Silent failures — operators have no visibility into WebSocket delivery failures.

### M8. Empty Except in main.py WebSocket handler
**File**: `backend/app/main.py`
**Line**: 93
**Issue**: `except Exception: pass` — the WebSocket handler silently swallows all exceptions during message processing.
**Impact**: Bugs in the WebSocket handler are invisible to operators.

### M9. Duplicate IP Address Logic
**Files**:
- `worker/app/config.py:41-49` — `get_ip_address()` method
- `worker/app/services/registrar.py:49-57` — `_get_ip_address()` method
**Issue**: Both methods implement identical IP address resolution logic (UDP connect to 8.8.8.8:80). This duplicates code and increases maintenance burden.
**Impact**: If the IP resolution strategy changes, both locations must be updated.

### M10. Missing `__init__.py` in workflow/artifacts
**File**: `backend/app/workflow/artifacts/`
**Issue**: The `artifacts/` directory has `service.py` but no `__init__.py`. The import in `workflows.py:11` works because Python 3.3+ supports namespace packages, but this is inconsistent with all other modules.
**Impact**: Inconsistent module structure.

### M11. Dead `pass` in complete_job
**File**: `backend/app/services/scheduler.py:192`
**Line**: 192
**Issue**: `if duration_ms is not None: pass` — the duration is never stored in the job model. See C5.

### M12. incorrect Type Annotation for `payload`
**File**: `backend/app/services/scheduler.py:78`
**Line**: 78
**Issue**: `payload: dict | None = None` is correct, but the method then does `job_payload: dict = payload if payload is not None else {}` instead of using a proper default or Optional type.
**Impact**: Works correctly but is unnecessarily defensive.

### M13. Storage of Payload as Mutable Default
**File**: `backend/app/models/job.py`
**Lines**: 23-25
**Issue**: `payload: Mapped[dict] = mapped_column(JSON, default=dict)` — the default is a callable (`dict`), not a mutable instance. This is correct, but similar patterns elsewhere use `default_factory=dict` which is the recommended approach for Pydantic.
**Impact**: Not technically a bug, but inconsistent with best practices.

### M14. `result` field uses mutable default
**File**: `backend/app/schemas/__init__.py`
**Lines**: Various
**Issue**: Several Pydantic models use `Field(default_factory=dict)` which is correct. However, `JobCreateRequest` uses `payload: dict = Field(default_factory=dict)` which is also correct.
**Impact**: No actual bug, but worth noting the pattern is correctly applied.

### M15. Race Condition in Job Assignment
**File**: `backend/app/services/scheduler.py:44-47`
**Lines**: 44-47
**Issue**: `_process_queue` fetches all queued jobs, then iterates them and assigns them to workers. Between the fetch and the assignment, another request could modify the job or worker state. There is no locking.
**Impact**: A job could be assigned to two workers simultaneously if the timing is right. However, in practice with SQLite's serialized writes, the second assignment will fail.

### M16. Logging Without Exception Info
**Files**: Multiple
**Lines**: Various
**Issue**: Several `except` blocks log the error message but not the traceback:
- `backend/app/services/scheduler.py:33` — `logger.error(f"Scheduler error: {e}")`
- `backend/app/services/worker_manager.py:48` — `logger.error(f"Offline checker error: {e}")`
- `backend/app/api/v1/plugins.py:34` — `logger.error(f"Failed to load plugin {plugin_id}: {e}")`
**Impact**: Debugging production issues is harder without full tracebacks.

### M17. Audit Middleware Catches All Paths
**File**: `backend/app/audit/middleware.py:29-31`
**Lines**: 29-31
**Issue**: The middleware skips audit logging for `/api/v1/audit` paths to avoid recursion, but catches ALL other paths including static files, Swagger docs, and the root `/` path. This generates audit events for non-API requests.
**Impact**: Audit log noise from static file requests.

### M18. No Validation on Plugin Manifest Entry Point
**File**: `backend/app/plugins/manifest/service.py`
**Issue**: The plugin manifest's `entry_point` field is loaded from the plugin.json file and passed directly to `importlib.import_module()`. There is no validation that the entry point is a safe module name (no path traversal, no system module import).
**Impact**: A plugin with `entry_point: "../../../etc/passwd"` could attempt path traversal imports.

### M19. Plugin Loader sys.path Pollution
**File**: `backend/app/plugins/loader/service.py:22`
**Line**: 22
**Issue**: `sys.path.insert(0, str(plugin_path))` modifies the global Python module search path. If a module name conflicts with a system module, the plugin's module takes precedence. After plugin unload, the sys.path modification is not reverted.
**Impact**: Module resolution conflicts and sys.path pollution.

### M20. Missing `loging_config.py` Reference
**File**: `backend/app/main.py:17`
**Line**: 17
**Issue**: `from .logging_config import setup_logging` — this file does not exist at the expected path. The actual file is at `backend/app/logging_config.py` (note: "loging" vs "logging"). The import works because the module was likely moved or renamed but the import path was updated.
**Impact**: Minor naming inconsistency.

### M21. Worker Monitor Uses Non-Existent psutil API
**File**: `worker/app/services/monitor.py:25`
**Line**: 25
**Issue**: `psutil.sensors_temperatures()` may not exist on all platforms (particularly Windows without WMI). The method is called without checking if it's available.
**Impact**: Worker crashes on machines without thermal sensor support.

### M22. Scheduler Loop Not Properly Stopped
**File**: `backend/app/services/scheduler.py:21-26`
**Lines**: 21-26
**Issue**: The `_scheduler_loop` is created with `asyncio.create_task()` but is never awaited or managed. If the scheduler is stopped and restarted, the old loop continues running.
**Impact**: Multiple scheduler loops can run simultaneously, causing duplicate job assignments.

### M23. Missing Timeout in Worker HTTP Client
**File**: `worker/app/utils/http_client.py:12`
**Line**: 12
**Issue**: The HTTP client uses a default timeout but does not set per-request timeouts. If the master hangs on a request, the worker hangs indefinitely.
**Impact**: Worker can become stuck waiting for master response.

### M24. Hardcoded DNS Dependency in IP Resolution
**File**: `worker/app/config.py:43` and `worker/app/services/registrar.py:52`
**Lines**: 43, 52
**Issue**: Both IP resolution methods connect to `8.8.8.8` (Google's public DNS) to determine the local IP. This fails on networks that block outbound UDP traffic to external DNS servers. Also, this creates an external network dependency.
**Impact**: Worker cannot determine its IP on restricted networks.

### M25. WebSocket Broadcast Uses `default=str`
**File**: `backend/app/websocket/manager.py:31`
**Line**: 31
**Issue**: `json.dumps({"type": event_type, "data": data}, default=str)` — using `str` as a fallback serializer silently converts non-serializable objects (like datetimes) to their string representation. This is fine but could silently swallow serialization errors.
**Impact**: Debugging serialization issues is harder.

### M26. Inconsistent Schema Usage
**Files**: `backend/app/api/v1/workers.py` lines 72-93, and similar patterns throughout
**Issue**: Some routes construct response models manually (e.g., `WorkerResponse(id=w.id, ...)`) while others use `AuditLogResponse.model_validate(l).model_dump()`. These patterns should be consistent.
**Impact**: Inconsistent code style.

### M27. No Pagination on Large List Endpoints
**File**: `backend/app/api/v1/workers.py:68-94`
**Line**: 68
**Issue**: `GET /workers` returns ALL workers without pagination. With 100 workers, this returns ~100 records which is fine. But the job listing endpoint also has no pagination.
**Impact**: As the cluster grows, response sizes grow linearly.

### M28. Missing `__table_args__` on Worker Model
**File**: `backend/app/models/worker.py`
**Issue**: The Worker model has indexes on `worker_name`, `status`, and `last_seen` but no composite index for `(status, last_seen)` which is the most common query pattern for the offline checker.
**Impact**: The offline checker query (`WHERE status NOT IN ('offline', 'disabled') AND last_seen < cutoff`) performs a full table scan.

### M29. Log Service Not Used by Other Services
**File**: `backend/app/services/log_service.py`
**Issue**: `LogService` is defined but all other services write logs directly via `SystemLog(...)` model instantiation rather than using the LogService. This bypasses any centralized logging logic.
**Impact**: If LogService gains additional functionality (batched writes, async logging), existing code won't benefit.

### M30. Seed Admin Uses Plaintext Default Password
**File**: `backend/app/services/auth.py:51`
**Line**: 51
**Issue**: The default password `"admin123"` is in the source code as a plaintext string. While it is hashed with bcrypt before storage (line 51), the literal string itself is in the codebase.
**Impact**: Anyone with source access knows the default admin password.

### M31. No graceful handling for DB connection failure
**File**: `backend/app/database.py:12-16`
**Lines**: 12-16
**Issue**: If the database file is locked or the directory is not writable, `create_async_engine` raises an exception during `init_db()`. There is no fallback, no retry, and no graceful degradation.
**Impact**: Application fails to start with no helpful error message.

### M32. Audit Export Creates Files Outside Data Directory
**File**: `backend/app/audit/service.py:169-172`
**Lines**: 169-172
**Issue**: The export directory is `Path(__file__).resolve().parent.parent.parent / "exports"` — this is at the backend/ root level, not inside the configured `data_dir`. Exports are not cleaned up automatically.
**Impact**: Disk space can fill up with export files.

### M33. Missing Pydantic Validation on dict-based Routes
**File**: `backend/app/api/v1/workflows.py:20`
**Lines**: 20
**Issue**: `data: dict` — no Pydantic schema validation. Same pattern in `agents.py:20`, `engineering.py:21`, `ai.py:21`.
**Impact**: No request body validation — bad data reaches the service layer.

### M34. Worker not using `asyncio.to_thread` for blocking operations
**File**: `worker/app/executor/handlers/dir_scan.py:14-25`
**Lines**: 14-25
**Issue**: `os.walk()` is called directly in an async handler. Should use `asyncio.to_thread(os.walk, directory)` or `loop.run_in_executor(None, os.walk, directory)`.
**Impact**: Event loop blocked during directory scanning.

### M35. No test isolation for worker tests
**File**: `worker/tests/`
**Issue**: Worker tests test config, executor, registrar, and reconnect logic but do not use mocked HTTP clients. They require a running master server for integration tests.
**Impact**: Worker tests cannot run in isolation without a master.

---

## MINOR Findings (20 items)

### N1. Unused Import: `json` in auditors
**File**: `backend/app/audit/events.py`
**Line**: 1
**Issue**: `import logging` — used. No other unused imports.

### N2. Model `__repr__` Methods Missing
**Files**: All model files
**Issue**: None of the SQLAlchemy models implement `__repr__()` or `__str__()`. This makes debugging harder because model instances print as `<db.models.xxx.Worker object at 0x...>`.
**Impact**: Minor debugging inconvenience.

### N3. Inconsistent Line Spacing in Models
**Files**: `backend/app/models/user.py:11-12`, `backend/app/models/log.py:15-17`
**Issue**: Extra blank lines exist in some model files (user.py has blank lines at 11-12; log.py has blank lines at 15-17). These appear to be accidental.
**Impact**: Cosmetic.

### N4. `Optional` vs `| None` Inconsistency
**Files**: Multiple
**Issue**: Some files use `Optional[str]` (the old typing style) while others use `str | None` (the modern style). For example, `backend/app/services/scheduler.py:4` uses `Optional` while `backend/app/api/v1/logs.py:13` uses `str | None`.
**Impact**: Inconsistent style. Prefer `| None` for Python 3.10+.

### N5. No `__all__` in `__init__.py` Files
**Files**: All `__init__.py` files
**Issue**: None of the `__init__.py` files define `__all__`. While not required, this means `from module import *` imports everything.
**Impact**: Minor — can cause namespace pollution.

### N6. No Type Hints in `__init__.py` Re-exports
**Files**: `backend/app/api/v1/__init__.py`
**Issue**: Re-exports from submodules lack type annotations. This means IDE autocompletion may not work correctly for re-exported symbols.
**Impact**: IDE usability.

### N7. `datetime.now()` Without timezone in Audit Export
**File**: `backend/app/audit/service.py:170`
**Line**: 170
**Issue**: `timestamp = datetime.now().strftime(...)` — uses naive datetime instead of timezone-aware `datetime.now(timezone.utc)`.
**Impact**: Export filenames use local time, which is inconsistent with the rest of the codebase.

### N8. No `__init__.py` for `workflow/artifacts/`
**File**: `backend/app/workflow/artifacts/`
**Issue**: Missing `__init__.py` makes it a namespace package. All other `workflow/` subdirectories have `__init__.py`.
**Impact**: Inconsistency.

### N9. Schema re-exports in `__init__.py` not used
**File**: `backend/app/schemas/__init__.py`
**Issue**: All schemas are defined in `__init__.py` rather than separate files. This file is 124 lines.
**Impact**: Could be split into domain-specific schema files.

### N10. Missing `requirements.txt` for Worker
**File**: `worker/`
**Issue**: The backend has `requirements.txt` but the worker does not have its own. The worker's dependencies (fastapi, uvicorn, httpx, psutil, pydantic-settings) should be listed separately.
**Impact**: Manual dependency tracking.

### N11. Worker Config Uses Mixed Sources
**File**: `worker/app/config.py:23-32`
**Issue**: `WorkerSettings` reads from `json_config` (loaded from `config.json`) as default values, and also supports `.env` via Pydantic. This is confusing because some settings come from JSON while others from env vars.
**Impact**: Configuration is harder to reason about.

### N12. Worker Constants Duplicate Config
**File**: `worker/app/core/constants.py:1-3`
**Lines**: 1-3
**Issue**: `HEARTBEAT_INTERVAL = 5`, `POLL_INTERVAL = 5`, `PROGRESS_INTERVAL = 5` are defined in constants but the config settings are used instead. The constants serve no purpose.
**Impact**: Dead code. Should be removed.

### N13. `_should_report_progress` uses `asyncio.get_event_loop()`
**File**: `worker/app/main.py:174`
**Line**: 174
**Issue**: `asyncio.get_event_loop().time()` should be `asyncio.get_running_loop().time()` for Python 3.10+ to avoid deprecation warnings.
**Impact**: Future deprecation.

### N14. Import inside function in several places
**Files**: Multiple
**Issue**: Several routes import modules inside function bodies:
- `backend/app/api/v1/plugins.py:58` — `import zipfile`
- `backend/app/api/v1/ai.py:235-237` — imports inside `chat_with_llm`
- `backend/app/api/v1/repositories.py:151` — import inside function
**Impact**: Import time overhead on every request. Modules should be imported at the top level.

### N15. Audit Service's `export_logs` Loads All Records
**File**: `backend/app/audit/service.py:174`
**Line**: 174
**Issue**: `result = await self.db.execute(select(AuditLog).order_by(...).limit(10000))` — limits to 10,000 records but loads them all into memory.
**Impact**: For large audit tables, this could use significant memory.

### N16. No Input Validation on `search_text` Regex
**File**: `backend/app/repository/search/service.py:61`
**Line**: 61
**Issue**: `pattern = re.compile(query, re.IGNORECASE) if regex else None` — no regex timeout. An attacker could submit a ReDoS payload to cause CPU exhaustion.
**Impact**: Potential DoS vector.

### N17. No Content-Type Validation on Plugin Upload
**File**: `backend/app/api/v1/plugins.py:54`
**Line**: 54
**Issue**: `file: UploadFile = File(...)` accepts any file type. No validation that the uploaded file is actually a ZIP.
**Impact**: `zipfile.ZipFile` will fail gracefully on non-ZIP files, but the error message may leak information.

### N18. Workflow Pause/Resume Uses Raw Status Assignment
**File**: `backend/app/api/v1/workflows.py:83-84, 93-94`
**Lines**: 83-84, 93-94
**Issue**: Status is assigned directly (`wf.status = "WAITING"`) without state machine validation. There is no check that the current state allows the transition.
**Impact**: Invalid state transitions are possible.

### N19. Agent Pause/Resume No-ops
**File**: `backend/app/api/v1/agents.py:83-93`
**Lines**: 83-93
**Issue**: `pause_agent` and `resume_agent` just set a status field. There is no actual agent lifecycle management — agents are in-memory objects that cannot be paused or resumed.
**Impact**: These endpoints are effectively no-ops.

### N20. Empty Middleware Directories
**Files**: 
- `backend/app/production/benchmark/__init__.py`
- `backend/app/production/deployment/__init__.py`
- `backend/app/production/audit/__init__.py`
- `backend/app/production/security/__init__.py`
- `backend/app/ai/metrics/__init__.py`
- `backend/app/ai/streaming/__init__.py`
- `backend/app/ai/memory/__init__.py`
- `backend/app/agents/memory/__init__.py`
- `backend/app/agents/roles/__init__.py`
- `backend/app/agents/coordinator/__init__.py`
**Issue**: These directories exist but contain only empty `__init__.py` files. They appear to be planned but unimplemented modules.
**Impact**: Repository clutter and misleading navigation.

---

## Detailed Module Review

### Module: `backend/app/main.py` (101 lines)

**File Purpose**: FastAPI application entry point. Configures middleware, routes, lifespan events, and WebSocket endpoint.

**Strengths**:
- Clean lifespan pattern using modern `@asynccontextmanager` (not deprecated `on_event`)
- Proper logging setup before application creation
- Environment check `if websocket not in ws_manager.active_connections` to prevent processing rejected connections
- `try/finally` for WebSocket disconnect guarantees cleanup
- Ping/pong support in WebSocket handler prevents connection timeouts
- Background task for offline worker checking

**Issues Found**:
- **CRITICAL**: No authentication on WebSocket endpoint (line 80)
- **MAJOR**: Empty `except Exception: pass` at line 93 swallows all WebSocket errors silently
- **MAJOR**: CORS middleware allows `allow_credentials=True` with permissive origin list (line 72)
- **MINOR**: Offline checker task (line 51) is never awaited or managed — no way to stop it on shutdown
- **MINOR**: No rate limiting middleware configured despite PROJECT_STATE.md claiming it exists

**Recommendation**: Add WebSocket authentication via token query parameter. Log WebSocket exceptions instead of swallowing. Add task management for background tasks.

### Module: `backend/app/config.py` (39 lines)

**File Purpose**: Application settings using Pydantic BaseSettings with .env file support.

**Strengths**:
- Type-annotated settings with sensible defaults
- Environment variable override via Pydantic's env_file support
- Auto-creation of data and logs directories
- Comma-separated CORS origins parsed into list

**Issues Found**:
- **CRITICAL**: Hardcoded JWT secret at line 14 (`"aicluster-secret-key-change-in-production"`)
- **MAJOR**: No validation that critical settings (secret_key, cors_origins) are production-safe
- **MAJOR**: Default host is `0.0.0.0` which binds to all interfaces — should be `127.0.0.1` by default
- **MINOR**: No typing on `os.makedirs` calls at lines 38-39
- **MINOR**: No version validation (app_version accepts any string)

**Recommendation**: Remove default secret_key, add startup validation, default to localhost-only binding.

### Module: `backend/app/database.py` (87 lines)

**File Purpose**: Async SQLAlchemy engine and session management with lazy initialization.

**Strengths**:
- Lazy engine initialization pattern (`get_engine()`) avoids early connection attempts
- Clean `get_db()` async generator for FastAPI dependency injection
- `reset_engine()` for test isolation with full engine disposal
- Comprehensive `init_db()` that imports all model classes and creates all tables
- Proper `check_same_thread=False` for SQLite async access

**Issues Found**:
- **MAJOR**: No connection retry logic — if database file is locked, app fails to start
- **MAJOR**: `init_db()` imports ALL models from ALL modules at startup — unnecessary coupling
- **MAJOR**: No WAL mode configuration for SQLite — default rollback journal may cause contention
- **MINOR**: Global mutable state (`_engine`, `_async_session_factory`) with no locking
- **MINOR**: `engine = get_engine()` at module level means engine is created at import time, not first request

**Recommendation**: Add retry logic, lazy engine initialization on first use, enable WAL mode.

### Module: `backend/app/services/auth.py` (98 lines)

**File Purpose**: JWT authentication, bcrypt password hashing, user management.

**Strengths**:
- Clean separation: AuthService class handles business logic, `get_current_user` is a standalone FastAPI dependency
- Proper JWT token encoding with expiry and role claims
- bcrypt password hashing with CryptContext
- `seed_default_admin()` is idempotent (checks for existing admin)
- HTTPBearer security scheme with `auto_error=False` for optional auth

**Issues Found**:
- **CRITICAL**: Default admin password `"admin123"` is a well-known literal in source code (line 51)
- **CRITICAL**: `get_current_user` is never used on any API endpoint (see Module: api/v1/*)
- **MAJOR**: No token refresh mechanism — token expires after 60 minutes with no refresh flow
- **MAJOR**: No password complexity validation
- **MAJOR**: No rate limiting on failed login attempts
- **MINOR**: `get_user_by_id` does not validate the user_id format (UUID expected)
- **MINOR**: `authenticate` method returns a tuple — would be cleaner with a dedicated response object

**Recommendation**: Remove hardcoded password, apply auth to all endpoints, add refresh tokens.

### Module: `backend/app/services/scheduler.py` (214 lines)

**File Purpose**: Job queue management with priority-based scheduling and worker assignment.

**Strengths**:
- Complete job lifecycle: create, schedule, assign, progress, complete, cancel
- Priority-based ordering (descending priority, ascending creation time)
- Worker selection by load (lowest CPU first)
- Automatic worker status management during assignment
- Structured logging for all job lifecycle events
- Proper async sleep-based scheduler loop

**Issues Found**:
- **CRITICAL**: Lines 191-192: `if duration_ms is not None: pass` — duration is never stored
- **MAJOR**: `_process_queue` fetches ALL queued jobs before iteration (lines 37-43) — O(n) per tick
- **MAJOR**: Race condition: multiple scheduler instances could assign the same job (no locking)
- **MAJOR**: Scheduler loop (line 28) is created with `asyncio.create_task` but never managed — restarting creates duplicate loops
- **MAJOR**: Double commit at lines 166 and 174 — could cause inconsistent state
- **MAJOR**: No validation of `status` parameter in `complete_job` (line 178)
- **MAJOR**: `cancel_job` does not release worker if job was assigned (line 111-118 should always execute)
- **MINOR**: `complete_job` returns `Job | None` but callers don't handle None consistently
- **MINOR**: Scheduler service is instantiated per-request (no singleton) — state (`_running`) is not shared

**Recommendation**: Fix the dead `pass`, add job locking, manage scheduler lifecycle, validate status.

### Module: `backend/app/services/worker_manager.py` (156 lines)

**File Purpose**: Worker registration, heartbeat processing, offline detection, and dashboard aggregation.

**Strengths**:
- Clean CRUD operations for worker lifecycle
- Comprehensive dashboard metrics with SQL aggregation
- Proper datetime handling with timezone awareness
- Structured logging for all state changes
- Idempotent registration (re-registration updates existing worker)
- Efficient offline detection with single query and batch update

**Issues Found**:
- **MAJOR**: Offline checker query (lines 72-77) has no composite index on (status, last_seen) — full table scan on large worker sets
- **MAJOR**: Heartbeat creates a separate log entry via SystemLog model rather than using LogService (inconsistent)
- **MAJOR**: `process_heartbeat` writes to DB on every heartbeat (every 5 seconds per worker) — no batching
- **MINOR**: `get_dashboard` uses 5 separate SQL queries (count for total, online, offline, busy, avg_cpu, avg_ram) — could be 2-3 queries
- **MINOR**: No caching for dashboard metrics — every request hits the database
- **MINOR**: `pause` does not check if worker is already paused

**Recommendation**: Add composite index, batch heartbeat writes, reduce dashboard queries.

### Module: `backend/app/websocket/manager.py` (51 lines)

**File Purpose**: WebSocket connection management and event broadcasting.

**Strengths**:
- Clean `Set[WebSocket]` for active connection tracking
- Connection limit enforcement (max 100 with proper close code 1013)
- Dead connection cleanup during broadcast
- Specialized broadcast methods for worker/job/dashboard events
- Proper `json.dumps` with `default=str` for non-serializable types

**Issues Found**:
- **MAJOR**: Broadcast iterates connections sequentially (line 33-37) — one slow client delays all others
- **MAJOR**: Empty `except Exception:` at line 36 — sends to dead connections are silently ignored
- **MAJOR**: Dead connection cleanup happens AFTER the loop, not during — a slow dead connection blocks all messaging
- **MINOR**: No throttling — 100 workers each sending heartbeats every 5 seconds = 20 broadcasts/second
- **MINOR**: No send timeout per connection

**Recommendation**: Add concurrent broadcast with asyncio.gather, log send failures, add per-connection timeout.

### Module: `backend/app/repository/search/service.py` (105 lines)

**File Purpose**: Multi-mode search over repository content (symbols, files, text, references).

**Strengths**:
- Four search modes: symbol, file, text, reference
- ILIKE-based search for case-insensitive matching
- Regex support in text search
- Repository filtering and language filtering in all modes
- Proper pagination (limit parameter)
- Error handling for file read failures

**Issues Found**:
- **CRITICAL**: Lines 72-88: `open(fpath, encoding="utf-8")` is blocking IO in async handler
- **CRITICAL**: Line 61: `re.compile(query)` with user-provided query — ReDoS vulnerability, no regex timeout
- **MAJOR**: Lines 72-84: Opens arbitrary files from file system using paths from database — path traversal risk
- **MAJOR**: No FTS5 full-text search index — reads files line-by-line every search
- **MAJOR**: search_text loads ALL repository files first, then iterates (lines 64-69) — no pagination at file level
- **MINOR**: Search results include `line` number but no column offset
- **MINOR**: No search result ranking — results are in file iteration order, not relevance order

**Recommendation**: Use `asyncio.to_thread` for file reads, add regex timeout, validate file paths, implement FTS5.

### Module: `backend/app/api/v1/plugins.py` (113 lines)

**File Purpose**: Plugin installation, management, and hook system API.

**Strengths**:
- Complete plugin lifecycle: install, enable, disable, uninstall
- ZIP upload with automatic extraction
- Manifest validation and compatibility checking
- WebSocket broadcasts for plugin state changes
- Hook listing and manual triggering

**Issues Found**:
- **CRITICAL**: Lines 53-66: No authentication on plugin upload — arbitrary code execution via ZIP upload
- **CRITICAL**: Line 61: `zf.extractall(str(plugin_dir))` — no path traversal validation in ZIP contents
- **CRITICAL**: Lines 24-26: Import and instantiate plugin code without sandboxing
- **MAJOR**: Line 55: `file.filename.replace(".zip", "")` — filename injection risk
- **MAJOR**: Lines 60-61: `import zipfile` inside function body — unnecessary import overhead per request
- **MAJOR**: No size limit on uploaded files
- **MAJOR**: No content-type validation — accepts any file as ZIP
- **MINOR**: Plugin registry is in-memory only — restarts lose plugin state

**Recommendation**: Add authentication, extract to temp directory first, validate ZIP contents, implement plugin sandboxing.

### Module: `backend/app/audit/middleware.py` (67 lines)

**File Purpose**: FastAPI middleware for automatic HTTP request audit logging.

**Strengths**:
- Automatic capture of request method, path, status code, duration
- Sensitive header masking (authorization, cookie, x-api-key)
- Sensitive path filtering (login, auth, token)
- Request ID and trace ID generation
- Severity mapping based on status code (INFO/200, WARNING/400, ERROR/500)
- Safe from recursion — skips `/api/v1/audit` paths

**Issues Found**:
- **MAJOR**: Lines 29-31: Filter is too broad — catches ALL paths including static files, docs, and root
- **MAJOR**: Line 39: `request.client.host` may be None behind reverse proxies
- **MAJOR**: Middleware constructs AuditEvent directly rather than using AuditService
- **MINOR**: No configurable exclusion list for paths
- **MINOR**: `time.time()` used instead of `time.monotonic()` for duration measurement
- **MINOR**: No batching — every HTTP request creates a separate DB write

**Recommendation**: Narrow path filter, add proxy support, batch audit writes.

### Module: `worker/app/main.py` (211 lines)

**File Purpose**: Worker agent main entry point with state machine and job execution.

**Strengths**:
- Complete state machine with 21 states covering normal and error flows
- Robust retry loop with exponential backoff for registration
- Clean signal handling for graceful shutdown (SIGINT, SIGTERM)
- Clear separation: _run_worker, _worker_loop, _execute_job
- Proper job handler dispatch with error handling
- Progress reporting with configurable thresholds
- WebSocket broadcasts on worker events

**Issues Found**:
- **MAJOR**: Lines 105, 129, 142, 150, 151, 160, 168: LSP warns that `poller.poll()`, `reporter.report_result()`, etc. are called on `None` — these are initialized in `_run_worker()` but LSP cannot track cross-function initialization
- **MAJOR**: Line 139: `execute_with_progress` is called via `hasattr` check but is not defined on `BaseJobHandler`
- **MAJOR**: Line 129: `Reporter.report_result()` called with kwargs that don't match the method signature (payload dict vs string)
- **MAJOR**: Lines 190-194: `_signal_handler` modifies global `state` variable — not thread-safe (signals run in main thread, but still a concurrency concern)
- **MAJOR**: `_execute_job` uses `asyncio.get_event_loop().time()` instead of `asyncio.get_running_loop().time()` (deprecated in 3.10)
- **MINOR**: Signal handler imports uvicorn inside `run()` function (line 201) — unnecessary import delay
- **MINOR**: State transitions are not validated — any state can transition to any other state

**Recommendation**: Add type narrowing for global variables, implement execute_with_progress properly, fix deprecated API.

### Module: `worker/app/executor/handlers/dir_scan.py` (40 lines)

**File Purpose**: Directory scanning job handler.

**Strengths**:
- Simple implementation with clear return structure
- Error handling for os.walk failures
- File count limit (10,000) prevents infinite loops
- Returns both file count, directory count, and total size

**Issues Found**:
- **CRITICAL**: Line 15: `os.walk(directory)` is blocking IO in async handler — blocks event loop
- **HIGH**: Line 9: `payload.get("directory", ".")` — no path validation, path traversal risk
- **MAJOR**: Lines 14-25: All file operations are synchronous — no use of `asyncio.to_thread`
- **MINOR**: No progress reporting during long scans
- **MINOR**: Total size could overflow for very large directories (>2GB on 32-bit Python)

**Recommendation**: Use `asyncio.to_thread` for os.walk, validate and restrict directory paths, add periodic progress reporting.

---

## Category Totals

| Category | Count | Key Areas |
|----------|-------|-----------|
| CRITICAL | 12 | Authentication, RCE, blocking IO, data loss, dead code |
| MAJOR | 35 | Unused code, race conditions, missing validation, duplicate logic, performance |
| MINOR | 20 | Style inconsistencies, missing implementations, import hygiene, formatting |

**Most critical issues to address**:
1. Add authentication middleware to all API endpoints (C1)
2. Fix the hardcoded JWT secret (C2)
3. Add authentication to plugin upload endpoint (C3)
4. Migrate blocking IO in worker handlers to `asyncio.to_thread` (C4)
5. Fix the dead `pass` in `complete_job` that discards `duration_ms` (C5)
6. Add rate limiting to login endpoint (C11)
7. Add path validation to worker handlers (C12)
8. Fix the scheduler double-commit bug (C7)
9. Add WebSocket authentication (C10)
10. Fix all empty except blocks (M7, M8)

**Module-level trends**:
- **backend/app/services/**: High quality with consistent patterns but missing auth enforcement and has some data integrity bugs
- **backend/app/api/v1/**: Consistent routing patterns but missing Pydantic schemas on newer endpoints (workflows, agents, engineering, ai)
- **backend/app/models/**: Well-structured with proper typing but missing __repr__ methods and has some formatting inconsistencies
- **worker/app/executor/handlers/**: Simple and functional but all use blocking IO in async context without path validation
- **backend/app/audit/**: Well-structured new module with clean separation of concerns
- **backend/app/production/**: Mostly scaffolding with only 3 of 6 planned modules implemented
