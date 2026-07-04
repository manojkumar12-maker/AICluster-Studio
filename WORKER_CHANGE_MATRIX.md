# Worker Change Matrix

## Current Worker Architecture

```
Worker Process
  ├── config.json + .env → WorkerSettings
  ├── WorkerHttpClient → httpx.AsyncClient → Master API
  ├── Registrar → POST /register → worker_id
  ├── HeartbeatService → POST /heartbeat (5s)
  ├── JobPoller → GET /next-job (5s)
  ├── Reporter → POST /progress, /result
  ├── JobRegistry → handler_map
  │   ├── EchoJobHandler
  │   ├── SleepJobHandler
  │   ├── DirectoryScanHandler
  │   ├── HashFileHandler
  │   └── CountFilesHandler
  └── State Machine (21 states)
```

## Changes

### C-001: Remove Dead Code

| Field | Value |
|-------|-------|
| **File** | `worker/app/services/executor.py` |
| **Impact** | Removes 88 lines of unused code. No functional impact. |
| **Risk** | ZERO — code not imported by `main.py` |
| **Verification** | Worker starts, registers, executes jobs |

### C-002: Remove execute_with_progress Branch

| Field | Value |
|-------|-------|
| **File** | `worker/app/main.py` (lines 139-148) |
| **Impact** | Simplifies execution path. All handlers use `execute()` only. |
| **Risk** | LOW — branch was never reached |
| **Verification** | All 5 handlers execute correctly |

### C-003: No-Op Reporter

| Field | Value |
|-------|-------|
| **File** | `worker/app/main.py` |
| **Impact** | `reporter` never None. Prevents AttributeError crash. |
| **Risk** | LOW |
| **Verification** | Worker startup crash doesn't cascade |

### C-004: Type-Safe Poll Handling

| Field | Value |
|-------|-------|
| **File** | `worker/app/main.py`, `worker/app/services/poller.py` |
| **Impact** | Explicit `isinstance` check before using poll result |
| **Risk** | LOW |
| **Verification** | Non-dict response handled gracefully |

### C-007: Async IO Wrapping

| Field | Value |
|-------|-------|
| **Files** | `worker/app/executor/handlers/dir_scan.py`, `count_files.py`, `hash_file.py` |
| **Impact** | `os.walk()` and file reads moved to thread pool via `asyncio.to_thread()` |
| **Risk** | LOW |
| **Verification** | Event loop responsive during long scans |

### S-006: Path Validation

| Field | Value |
|-------|-------|
| **Files** | New `path_utils.py` + modified handlers |
| **Impact** | `..` rejected, absolute paths validated against allowed directories |
| **Risk** | LOW |
| **Verification** | Path traversal attempts fail |

### S-009: Worker Authentication

| Field | Value |
|-------|-------|
| **Files** | `worker/app/utils/http_client.py`, `worker/app/config.py`, `worker/app/main.py` |
| **Impact** | All requests to master include `Authorization: Bearer <worker_secret>` |
| **Risk** | LOW |
| **Verification** | Worker registers and communicates with master |

## Worker Process After Changes

```
Worker Process (v1.3.1)
  ├── config.json + .env → WorkerSettings
  │   └── NEW: worker_secret, allowed_directories
  ├── WorkerHttpClient → httpx.AsyncClient
  │   └── NEW: Authorization header on all requests
  ├── Registrar → POST /register → worker_id
  ├── HeartbeatService → POST /heartbeat (5s)
  ├── JobPoller → GET /next-job (5s)
  │   └── IMPROVED: type-safe result handling
  ├── Reporter → POST /progress, /result
  │   └── FIXED: no-op until real instance created
  ├── JobRegistry → handler_map
  │   ├── EchoJobHandler
  │   ├── SleepJobHandler
  │   ├── DirectoryScanHandler → FIXED: async IO + path validation
  │   ├── HashFileHandler → FIXED: async IO + path validation
  │   └── CountFilesHandler → FIXED: async IO + path validation
  ├── path_utils.py → NEW: shared path validation
  └── State Machine (21 states) → IMPROVED: type-safe transitions
```

## Worker Test Impact

| Test File | Tests Added | Tests Modified | Purpose |
|-----------|-------------|----------------|---------|
| `worker/tests/test_config.py` | +2 | 0 | Worker secret, allowed directories |
| `worker/tests/test_executor.py` | +6 | +2 | Path validation, async IO, handler cleanup |
| `worker/tests/test_reconnect.py` | +2 | 0 | Jitter verification |
| `worker/tests/test_registrar.py` | +4 | +2 | Auth header verification |
| `worker/tests/test_handlers.py` | NEW | — | Path traversal, async IO non-blocking |
| `worker/tests/test_worker_auth.py` | NEW | — | Worker secret auth flow |
