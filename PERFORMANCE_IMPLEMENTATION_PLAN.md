# AICluster v1.3.1 Performance Implementation Plan

## Current Performance Issues

| Issue | Location | Impact | Sprint |
|-------|----------|--------|--------|
| Blocking `os.walk()` in async handlers | `worker/app/executor/handlers/*.py` | Event loop blocked | 2 |
| Dashboard polling (2s) | `frontend/src/app/(dashboard)/dashboard/page.tsx` | Unnecessary DB load | 3 |
| No pagination on list endpoints | `backend/app/api/v1/*.py` | Memory pressure | 3 |
| Scheduler full-table scan | `backend/app/services/scheduler.py` | O(n) on job queue | 1 |
| Missing DB indexes | `backend/app/models/*.py` | Slow queries | 3 |
| PyInstaller binary size | `build/pyinstaller_builder.py` | ~80 MB downloads | 4 |
| Worker polling (every 5s) | `worker/app/services/poller.py` | Network overhead | 4 |

---

## C-007: Blocking IO in Async Handlers

**Root Cause**: `os.walk()` in `dir_scan.py` and `count_files.py` is synchronous and blocks the async event loop.

**Fix**: Wrap all blocking calls in `asyncio.to_thread()`:

```python
import asyncio

def _scan_directory(directory: str) -> dict:
    """Synchronous directory scan (runs in thread pool)."""
    file_count = 0
    dir_count = 0
    total_size = 0
    for root, dirs, files in os.walk(directory):
        dir_count += len(dirs)
        for f in files:
            file_count += 1
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
            if file_count > 10000:
                return {"error": "Too many files (>10000)", "file_count": file_count}
    return {"file_count": file_count, "dir_count": dir_count, "total_size": total_size}

async def execute(self, job_id, payload):
    directory = payload.get("directory", ".")
    result = await asyncio.to_thread(self._scan_directory, directory)
    return result
```

**Files**: `worker/app/executor/handlers/dir_scan.py`, `worker/app/executor/handlers/count_files.py`
**Performance Gain**: Event loop no longer blocked during directory scans
**Risk**: LOW
**Tests**: Verify handlers return correct results, verify event loop remains responsive

---

## Dashboard Polling Optimization

**Issue**: Frontend polls `/api/v1/dashboard` every 2 seconds.

**Fix**:
1. Transition to WebSocket for real-time updates (see F-003)
2. While WebSocket not available, increase poll interval to 5s
3. Add ETag/If-Modified-Since support to dashboard endpoint
4. Cache dashboard data in memory with 2s TTL

```python
from functools import lru_cache
from datetime import datetime, timedelta

_dashboard_cache = {}
_dashboard_cache_time = {}

async def get_dashboard(db):
    # Return cached version if fresh
    if "dashboard" in _dashboard_cache:
        if datetime.now() - _dashboard_cache_time["dashboard"] < timedelta(seconds=2):
            return _dashboard_cache["dashboard"]
    # Compute fresh
    data = await compute_dashboard(db)
    _dashboard_cache["dashboard"] = data
    _dashboard_cache_time["dashboard"] = datetime.now()
    return data
```

**Files**: `backend/app/api/v1/dashboard.py`, `frontend/src/app/(dashboard)/dashboard/page.tsx`
**Performance Gain**: 2x reduction in dashboard DB queries
**Risk**: LOW

---

## Add Pagination to List Endpoints

**Issue**: Endpoints like `GET /api/v1/workers`, `GET /api/v1/jobs`, `GET /api/v1/logs` return all records without pagination.

**Fix**:
1. Add `limit` and `offset` query parameters to all list endpoints
2. Default `limit=50`, max `limit=500`
3. Return `PaginatedResponse` wrapper
4. Add `X-Total-Count` response header

**Endpoints requiring pagination**:
- `GET /api/v1/workers`
- `GET /api/v1/jobs`
- `GET /api/v1/logs`
- `GET /api/v1/workflow`
- `GET /api/v1/repositories`
- `GET /api/v1/repositories/{id}/files`
- `GET /api/v1/ai/session`
- `GET /api/v1/agents`
- `GET /api/v1/agents/messages`
- `GET /api/v1/repositories/search`
- `GET /api/v1/audit/logs`

**Files**: ALL route files in `backend/app/api/v1/`, `shared/py/schemas.py`
**Performance Gain**: Prevents OOM on large datasets
**Risk**: LOW — API change may affect clients

---

## Add Missing Database Indexes

**Issue**: Some tables lack indexes on frequently queried columns.

**Current Indexes**:
- `jobs`: (priority, created_at)
- `system_logs`: (level, created_at)

**Missing Indexes**:
| Table | Missing Index | Reason |
|-------|---------------|--------|
| `workers` | (status, is_paused) | Scheduler worker lookup |
| `jobs` | (assigned_worker) | Worker job lookup |
| `jobs` | (status) | Queue processing |
| `workflow_tasks` | (workflow_id, status) | Task status queries |
| `repository_files` | (repository_id, path) | File lookup |
| `symbols` | (repository_id, symbol_type) | Symbol queries |
| `ai_messages` | (session_id, timestamp) | History retrieval |
| `agent_messages` | (receiver_id, unread) | Unread message check |
| `audit_logs` | (category, severity, timestamp) | Audit queries |

**Files**: `backend/app/models/*.py`
**Performance Gain**: Query speed improvement for indexed columns
**Risk**: LOW — indexes add write overhead but minimal for SQLite
**Tests**: Verify indexes created, verify query plans use indexes

---

## Scheduler Optimization

**Issue**: `_process_queue()` does `SELECT * FROM jobs WHERE status = 'queued'` and iterates all queued jobs.

**Fix**:
1. Add `LIMIT` to queued job query (process max 10 per cycle)
2. Add `status` index (see above)
3. Consider batch assignment: assign multiple jobs in one transaction

**Files**: `backend/app/services/scheduler.py`
**Performance Gain**: Bounded iteration prevents unbounded processing
**Risk**: LOW

---

## Worker Polling Optimization

**Issue**: Workers poll `GET /next-job` every 5 seconds even when idle.

**Fix**:
1. Increase poll interval to 10s during idle periods
2. Use exponential backoff: start at 2s, max 30s
3. Reset to 2s after receiving a job
4. Alternatively: use WebSocket for job notifications, polling as fallback

**Files**: `worker/app/services/poller.py`, `worker/app/core/constants.py`
**Performance Gain**: Up to 6x reduction in polling traffic during idle
**Risk**: LOW — slight increase in job assignment latency

---

## PyInstaller Binary Size

**Issue**: AIClusterMaster.exe is ~80 MB due to bundling full Python runtime.

**Fix** (out of scope for v1.3.1 — document as v1.4.0 concern):
1. Audit hidden imports: remove unnecessary packages
2. Use UPX compression for PyInstaller builds
3. Consider `--exclude-module` for unused stdlib modules
4. Investigate Nuitka as alternative (better compression, faster execution)

**Files**: `build/pyinstaller_builder.py`, `build/config.py`
**Target**: Reduce master binary from ~80 MB to <50 MB
**Risk**: MEDIUM — UPX may cause false positive virus detections
