# AICluster v1.3.1 Worker Implementation Plan

## Current Worker State

The worker is largely functional but has several bugs and gaps identified in Discovery and CODE_REVIEW.md.

| Issue | Severity | Location | Sprint |
|-------|----------|----------|--------|
| `reporter` can be None when called | HIGH | `worker/app/main.py:129,150,151,160,168` | 2 |
| `execute_with_progress` not defined | HIGH | `worker/app/main.py:139` | 2 |
| `poll()` return type handling | MEDIUM | `worker/app/main.py:105` | 2 |
| `services/executor.py` dead code | MEDIUM | `worker/app/services/executor.py` | 2 |
| Blocking `os.walk()` in async handlers | HIGH | `worker/app/executor/handlers/*.py` | 2 |
| Path traversal in file handlers | HIGH | `worker/app/executor/handlers/*.py` | 2 |
| No worker auth for master communication | HIGH | `worker/app/utils/http_client.py` | 2 |
| Retry handler lacks jitter | LOW | `worker/app/utils/retry.py` | 2 |
| No progress granularity for handlers | MEDIUM | `worker/app/executor/base.py` | 2 |
| Duplicate IP resolution logic | LOW | `worker/app/config.py` | 4 |

---

## C-002: execute_with_progress Handler Contract

**Recommended Fix**: Simplify by removing the `execute_with_progress` branch.

**Rationale**: The branch is never reached (no handler implements it). Keeping it adds complexity and confusion. For v1.3.1 (stability), remove the dead code path.

**Changes to `worker/app/main.py`**:

Replace lines 139-151 with:
```python
try:
    result = await handler.execute(job_id, payload)
    duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    await reporter.report_result(job_id, "completed", result=result, duration_ms=duration_ms)
```

**Files**: `worker/app/main.py`, `worker/app/executor/base.py`
**Tests**: All 5 handlers execute and report correctly

---

## C-003: Reporter None Guard

**Fix**: Initialize reporter as no-op before the worker loop starts.

**Changes to `worker/app/main.py`**:

```python
class _NoOpReporter:
    async def report_progress(self, job_id=None, progress=None, logs=None):
        pass
    async def report_result(self, job_id=None, status=None, result=None, error=None, duration_ms=None, logs=None):
        pass

reporter: Reporter = _NoOpReporter()  # type: ignore
```

Then replace in `_run_worker()`:
```python
reporter = Reporter(worker_id, http_client)  # Real instance
```

**Files**: `worker/app/main.py`
**Tests**: Early failure doesn't crash on reporter calls

---

## C-004: Poll Result Type Handling

**Fix**: Add explicit type checks in `_worker_loop()`.

```python
job_data = await poller.poll()

if job_data is None:
    state = WorkerState.NO_JOB
    continue

if not isinstance(job_data, dict):
    logger.warning(f"Unexpected poll response type: {type(job_data)}")
    continue

state = WorkerState.HAS_JOB
await _execute_job(worker_id, job_data)
```

**Files**: `worker/app/main.py`, `worker/app/services/poller.py`
**Tests**: Various poll responses handled correctly

---

## C-001: Remove Dead Code

**Changes**:
1. Delete `worker/app/services/executor.py` (88 lines, completely unused)
2. Update `worker/app/services/__init__.py` if it imports from executor

**Files**: `worker/app/services/executor.py`
**Impact**: Removes 88 lines of dead code. No functional change.
**Tests**: Worker starts and runs jobs normally

---

## S-006: Path Traversal Protection

**Changes to `worker/app/executor/handlers/`**:

Add shared validation function to all file-based handlers:

```python
import os

ALLOWED_DIRECTORIES = ["C:\\", "D:\\"]  # From config

def validate_path(path: str) -> str:
    """Validate and resolve path, preventing traversal."""
    if not path:
        raise ValueError("Path is required")
    
    # Must be absolute
    if not os.path.isabs(path):
        raise ValueError("Path must be absolute")
    
    # No directory traversal
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.sep):
        raise ValueError("Directory traversal not allowed")
    
    # Must be in allowed directory
    allowed = False
    for allowed_dir in ALLOWED_DIRECTORIES:
        if normalized.startswith(os.path.normpath(allowed_dir)):
            allowed = True
            break
    if not allowed:
        raise ValueError(f"Path must be within allowed directories: {ALLOWED_DIRECTORIES}")
    
    return normalized
```

Apply to:
- `dir_scan.py`: Validate `payload["directory"]`
- `hash_file.py`: Validate `payload["filepath"]`
- `count_files.py`: Validate `payload["directory"]`

**Files**:
- `worker/app/executor/handlers/dir_scan.py`
- `worker/app/executor/handlers/hash_file.py`
- `worker/app/executor/handlers/count_files.py`
- New: `worker/app/executor/handlers/path_utils.py`

**Tests**: Path traversal attempt rejected, valid paths accepted

---

## C-007: Async Blocking IO

**Fix**: Wrap `os.walk()` in `asyncio.to_thread()`.

**Changes to `dir_scan.py`**:

```python
import asyncio

async def execute(self, job_id, payload):
    directory = payload.get("directory", ".")
    try:
        result = await asyncio.to_thread(self._scan_sync, directory)
        return result
    except Exception as e:
        return {"error": str(e)}

def _scan_sync(self, directory):
    """Synchronous scan running in thread pool."""
    file_count = 0
    dir_count = 0
    total_size = 0
    for root, dirs, files in os.walk(directory):
        dir_count += len(dirs)
        for f in files:
            file_count += 1
            if file_count > 10000:
                return {"error": "Too many files", "file_count": file_count}
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return {"file_count": file_count, "dir_count": dir_count, "total_size": total_size}
```

Apply same pattern to `count_files.py` and `hash_file.py` (file reading).

**Files**: `worker/app/executor/handlers/dir_scan.py`, `worker/app/executor/handlers/count_files.py`, `worker/app/executor/handlers/hash_file.py`
**Tests**: Event loop remains responsive during long scans

---

## S-009: Worker Authentication

**Changes to `worker/app/utils/http_client.py`**:

```python
class WorkerHttpClient:
    def __init__(self, master_url: str, worker_secret: str | None = None, timeout: int = 10):
        self.base_url = master_url.rstrip("/")
        self.worker_secret = worker_secret or ""
        self._client = httpx.AsyncClient(timeout=timeout)

    async def post(self, path: str, json: dict | None = None) -> httpx.Response:
        headers = {}
        if self.worker_secret:
            headers["Authorization"] = f"Bearer {self.worker_secret}"
        return await self._client.post(
            f"{self.base_url}/api/v1{path}",
            json=json,
            headers=headers,
        )

    async def get(self, path: str) -> httpx.Response:
        headers = {}
        if self.worker_secret:
            headers["Authorization"] = f"Bearer {self.worker_secret}"
        return await self._client.get(
            f"{self.base_url}/api/v1{path}",
            headers=headers,
        )
```

**Changes to `worker/app/config.py`**:
- Add `worker_secret: str` field (default empty string, generated on first run)

**Changes to `worker/app/main.py`**:
- Pass `worker_secret` to `WorkerHttpClient` constructor

**Files**: `worker/app/utils/http_client.py`, `worker/app/config.py`, `worker/app/main.py`
**Tests**: Valid worker connects, invalid worker rejected

---

## Retry Handler Improvement

**Issue**: Retry delays have no jitter, causing thundering herd after master restart.

**Fix**:
```python
import random

class RetryHandler:
    @property
    def current_delay(self) -> float:
        # Add ±25% jitter
        base = self._delays[min(self._attempt, len(self._delays) - 1)]
        jitter = base * 0.25
        return base + random.uniform(-jitter, jitter)
```

**Files**: `worker/app/utils/retry.py`
**Tests**: Workers reconnect with staggered timing

---

## Worker State Machine Health

**Issue**: Some state transitions are implicit and not logged.

**Fix**: Add state transition logging:
```python
state = WorkerState.REGISTERING
logger.info(f"State: {state.value}")
```

This is a low-priority improvement; include only if time allows in Sprint 2.

---

## Summary of Worker Changes

| File | Change | Risk | Est. Time |
|------|--------|------|-----------|
| `worker/app/main.py` | Fix reporter None, remove dead branch, type-safe poll | MEDIUM | 2h |
| `worker/app/services/executor.py` | Delete file | LOW | 5min |
| `worker/app/executor/base.py` | Remove `execute_with_progress` (optional) | LOW | 10min |
| `worker/app/executor/handlers/*.py` | Add path validation + async to_thread | LOW | 2h |
| `worker/app/utils/http_client.py` | Add worker secret auth header | LOW | 30min |
| `worker/app/config.py` | Add worker_secret field | LOW | 15min |
| `worker/app/utils/retry.py` | Add jitter | LOW | 10min |
| `worker/tests/` | Update tests for changes | LOW | 1h |
