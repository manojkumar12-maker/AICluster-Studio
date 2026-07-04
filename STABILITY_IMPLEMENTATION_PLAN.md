# AICluster v1.3.1 Stability Implementation Plan

## Current Stability Issues

| Issue | Location | Impact |
|-------|----------|--------|
| Worker reports `report_result` on None | `worker/app/main.py:129,150,151,160,168` | Runtime crash |
| `execute_with_progress` not on BaseJobHandler | `worker/app/main.py:139` | AttributeError |
| `poll()` result type uncertainty | `worker/app/main.py:105` | Potential crash |
| Double commit in `get_next_for_worker` | `backend/app/services/scheduler.py:172,187` | Integrity risk |
| `duration_ms` never stored | `backend/app/services/scheduler.py:227` | Lost data |
| Scheduler loop not stoppable | `backend/app/services/scheduler.py:30` | Shutdown delay |
| Empty except blocks | Multiple files | Silent failures |
| No graceful DB failure handling | `backend/app/services/` | Connection drops crash |

---

## C-001: Remove Dead Code

**Root Cause**: `worker/app/services/executor.py` is a duplicate job executor that's never used. `main.py` uses `executor/registry.py` instead.

**Fix**:
1. Delete `worker/app/services/executor.py`
2. Remove `from .services.executor import JobExecutor` from `services/__init__.py` if present
3. Verify no imports reference it

**Files**: `worker/app/services/executor.py`, `worker/app/services/__init__.py`
**Risk**: LOW — fully unused code
**Tests**: Worker starts and runs jobs normally

---

## C-002: execute_with_progress Not on BaseJobHandler

**Root Cause**: `main.py:139` checks `hasattr(handler, "execute_with_progress")` but `BaseJobHandler` only defines `execute()`. No handler defines this method.

**Fix Options**:

**Option A** (Simplify): Remove the `execute_with_progress` branch entirely. `BaseJobHandler` and all handlers only implement `execute()`. Workers report progress at start/end only.

**Option B** (Implement): Add `execute_with_progress` to `BaseJobHandler` as async generator that yields `execute()` result at end. Handlers can override for granular progress.

**Recommendation**: Option A for v1.3.1 (stability release). Option B for future enhancement.

**Files**: `worker/app/main.py` (lines 139-148), `worker/app/executor/base.py`
**Risk**: LOW
**Tests**: All handlers execute and report results correctly

---

## C-003: report_result/progress Called on None

**Root Cause**: `reporter` is a module-level `Optional[Reporter]` initialized to `None`. It's set inside `_run_worker()`, but `_execute_job()` could be called before initialization if state machine has a bug.

**Fix**:
1. Initialize `reporter` to a no-op implementation early in `_run_worker()`
2. Or add null checks before every reporter call
3. Or restructure to create reporter before worker loop starts

**Best Fix**: Create no-op reporter at module level:

```python
class _NoOpReporter:
    async def report_progress(self, *args, **kwargs): pass
    async def report_result(self, *args, **kwargs): pass

reporter: Reporter = _NoOpReporter()  # type: ignore
```

Then replace with real instance in `_run_worker()`.

**Files**: `worker/app/main.py`
**Risk**: LOW
**Tests**: Early failure (before registration) doesn't crash on reporter calls

---

## C-004: poll() Result Handling

**Root Cause**: `poller.poll()` is typed to return `dict | None`, but `job_data` is used without type narrowing.

**Fix**:
1. Ensure `poller.poll()` has clear type annotations
2. Add explicit check: `if not isinstance(job_data, dict): continue`
3. Handle `job_data.get("id", "unknown")` safely (already done)

**Files**: `worker/app/services/poller.py`, `worker/app/main.py`
**Risk**: LOW
**Tests**: Various poll responses handled correctly

---

## C-005: Double Commit in get_next_for_worker

**Root Cause**:
```python
# Line 172
await self.db.commit()  # FIRST COMMIT
# ... SystemLog created ...
# Line 187
await self.db.commit()  # SECOND COMMIT
```

**Fix**: Remove the first commit. Only commit once after all changes.

```python
job.status = "running"
job.assigned_worker = worker_id
job.started_at = datetime.now(timezone.utc)

worker_result = await self.db.execute(
    select(Worker).where(Worker.id == worker_id)
)
worker = worker_result.scalar_one_or_none()
if worker:
    worker.status = "busy"
    worker.current_job = job.id

log = SystemLog(level="INFO", message=f"Job '{job.id}' assigned to worker '{worker_id}'", source="scheduler")
self.db.add(log)

await self.db.commit()  # SINGLE COMMIT
await self.db.refresh(job)
```

**Files**: `backend/app/services/scheduler.py`
**Risk**: LOW
**Tests**: Job assignment works, log is created, no integrity errors

---

## C-006: duration_ms Never Stored

**Root Cause**: `complete_job` has `if duration_ms is not None: pass` — the value is received but discarded.

**Fix**:
1. Add `duration_ms` column to `Job` model if not present
2. Store: `job.duration_ms = duration_ms` instead of `pass`

**Files**: `backend/app/services/scheduler.py`, `backend/app/models/job.py`
**Risk**: LOW
**Tests**: Duration is stored and retrievable

---

## C-008: Scheduler Loop Not Properly Stoppable

**Root Cause**: `_scheduler_loop` uses a simple `_running` boolean flag. If the loop is sleeping, `stop()` may not be prompt.

**Fix**:
1. Replace `_running` with `asyncio.Event` for cancellation
2. Use `asyncio.wait_for` or `asyncio.sleep` with cancellation
3. Add timeout to DB operations to prevent hangs

```python
async def start(self):
    self._stop_event.clear()
    self._task = asyncio.create_task(self._scheduler_loop())

async def stop(self):
    self._stop_event.set()
    if self._task:
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

async def _scheduler_loop(self):
    while not self._stop_event.is_set():
        try:
            await asyncio.wait_for(self._process_queue(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("Scheduler queue processing timed out")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(2)
```

**Files**: `backend/app/services/scheduler.py`
**Risk**: LOW
**Tests**: Scheduler stops within 1s of stop() call

---

## C-009: Empty Except Blocks

**Root Cause**: Multiple files use `except: pass` which silently swallows exceptions.

**Audit Findings** (from CODE_REVIEW.md):
- Several empty except blocks in backend code
- Risk: debugging becomes impossible when errors are silently consumed

**Fix**:
1. Locate all `except: pass` and `except Exception: pass` blocks
2. Each should at minimum log the exception
3. Use `logger.exception()` or `logger.error()` with traceback
4. Consider whether the exception should be re-raised

**Files**: Global audit of all Python files in `backend/app/` and `worker/app/`
**Risk**: LOW
**Tests**: Errors in handled blocks are visible in logs

---

## Worker Startup Stability

### Issue: Graceful Shutdown on Early Failure

**Root Cause**: If worker fails during registration, signal handling may not work properly.

**Fix**:
1. Ensure `shutdown_event` is checked in all retry loops
2. Add timeout to registration attempt
3. Ensure cleanup runs even if registration never succeeded

**Files**: `worker/app/main.py`
**Tests**: SIGTERM during startup → clean exit within 2s

### Issue: Connection Loss Recovery

**Root Cause**: If master goes down, worker enters retry loop but may have stale state.

**Fix**:
1. Clear worker_id on registration failure (already in `registrar.clear()`)
2. Reset HTTP client on connection failure
3. Add jitter to retry delays to prevent thundering herd

**Files**: `worker/app/main.py`, `worker/app/utils/retry.py`
**Tests**: Master restart → workers reconnect within 30s

---

## Database Stability

### Issue: No Connection Pool Recycling

**Fix**: Add pool recycle to engine configuration to prevent stale connections.

```python
engine = create_async_engine(
    settings.database_url,
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True,  # Verify connection before use
)
```

**Files**: `backend/app/database.py`
**Tests**: Long-running connections don't fail

### Issue: No Migration Support

**Fix**: Configure Alembic for schema migrations (out of scope for v1.3.1, document as known issue).

**Note**: v1.3.1 does not change schema, so migrations not needed yet. But should be configured for v1.4.0.
