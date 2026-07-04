# Rollback Plan

## Rollback Triggers

A rollback should be triggered if any of the following occur:
- **Critical regression**: An existing feature stops working
- **Build failure**: Release pipeline fails after the change
- **Performance degradation**: Response times increase >50%
- **Security regression**: A security fix introduces a worse vulnerability
- **Worker failure**: Workers cannot register or execute jobs
- **Database corruption**: Schema changes cause data loss

---

## Sprint 1 Rollback

### Per-Change Rollback

| Issue | Rollback Trigger | Steps | Files to Restore | Verification |
|-------|------------------|-------|------------------|--------------|
| S-001 | JWT validation fails after restart | 1. Revert `config.py` to use hardcoded secret<br>2. Delete `data/secret.key`<br>3. Restart master | `backend/app/config.py` | Auth login works |
| S-002 | Cannot log in with generated password | 1. Revert `auth.py` seed_default_admin()<br>2. Manually insert admin user with known hash<br>3. Restart master | `backend/app/services/auth.py`, `backend/app/main.py` | Login with admin/admin123 works |
| S-003 | Legitimate clients blocked | 1. Revert all 15 route files<br>2. Revert `dependencies.py`<br>3. Restart master | All `api/v1/*.py` files, `app/api/dependencies.py` | All endpoints accessible without auth |
| S-005 | Frontend CORS errors | 1. Revert `main.py` CORS config to `["*"]`<br>2. Restart master | `backend/app/main.py` | Frontend loads |
| C-005 | Job assignment fails | 1. Revert `scheduler.py` to double-commit<br>2. Restart master | `backend/app/services/scheduler.py` | Jobs assigned to workers |
| C-006 | No impact on functionality | 1. Revert `pass` in complete_job<br>2. Revert model change | `backend/app/services/scheduler.py`, `backend/app/models/job.py` | Jobs complete normally |
| C-008 | Scheduler stops responding | 1. Revert to `_running` flag<br>2. Restart master | `backend/app/services/scheduler.py` | Scheduler processes queue |

### Sprint 1 Full Rollback

```bash
# If multiple issues need rollback, restore from git:
git checkout -- backend/app/config.py
git checkout -- backend/app/services/auth.py
git checkout -- backend/app/services/scheduler.py
git checkout -- backend/app/models/job.py
git checkout -- backend/app/main.py
git checkout -- backend/app/api/
git checkout -- backend/app/middleware/
git checkout -- config/

# Delete generated files
rm -f backend/data/secret.key

# Restart master
# (restart process)
```

---

## Sprint 2 Rollback

### Per-Change Rollback

| Issue | Rollback Trigger | Steps | Files to Restore | Verification |
|-------|------------------|-------|------------------|--------------|
| C-001 | No impact (dead code) | 1. Restore `executor.py` | `worker/app/services/executor.py` | - |
| C-002 | Handler execution fails | 1. Restore `execute_with_progress` branch<br>2. Restore `BaseJobHandler` | `worker/app/main.py`, `worker/app/executor/base.py` | Handlers execute |
| C-003 | Worker crashes | 1. Restore `Optional[Reporter] = None` | `worker/app/main.py` | Worker starts |
| C-004 | Poll loop fails | 1. Remove type guard | `worker/app/main.py`, `worker/app/services/poller.py` | Worker polls jobs |
| C-007 | Handler results wrong | 1. Revert to synchronous `os.walk()` | `worker/app/executor/handlers/*.py` | Handlers return correct results |
| S-006 | Valid paths rejected | 1. Remove path validation calls<br>2. Delete `path_utils.py` | `worker/app/executor/handlers/*.py` | All paths accepted |
| S-009 | Worker won't connect | 1. Remove auth header from http_client<br>2. Remove worker_secret validation | `worker/app/utils/http_client.py`, `backend/app/api/v1/workers.py` | Worker registers |
| S-012 | Search broken | 1. Remove input validation<br>2. Revert search service | `backend/app/api/v1/repositories.py`, `backend/app/repository/search/service.py` | Search works |

### Sprint 2 Full Rollback

```bash
git checkout -- worker/app/main.py
git checkout -- worker/app/services/
git checkout -- worker/app/executor/
git checkout -- worker/app/utils/
git checkout -- worker/app/config.py
git checkout -- backend/app/api/v1/workers.py
git checkout -- backend/app/repository/
```

---

## Sprint 3 Rollback

### Per-Change Rollback

| Issue | Rollback Trigger | Steps | Files to Restore | Verification |
|-------|------------------|-------|------------------|--------------|
| S-004 | Plugin installation fails | 1. Revert loader to non-sandboxed<br>2. Remove permission checks | `backend/app/plugins/` | Plugin install works |
| S-007 | Legitimate traffic rate-limited | 1. Remove rate limiter middleware | `backend/app/main.py`, `backend/app/middleware/rate_limit.py` | No 429 errors |
| S-010 | TLS fails to start | 1. Remove TLS config from settings<br>2. Remove TLS from uvicorn | `backend/app/config.py`, `backend/app/main.py` | HTTP works |
| S-011 | Cookie auth breaks | 1. Revert cookie endpoints<br>2. Revert frontend auth | `backend/app/services/auth.py`, `frontend/src/stores/auth-store.ts` | Bearer auth works |
| S-013 | Debug info lost | 1. Remove production error handler | `backend/app/main.py` | Errors show details |
| F-003 | Dashboard stops updating | 1. Revert WS client<br>2. Restore polling | `frontend/src/lib/websocket.ts`, `frontend/src/app/(dashboard)/` pages | Dashboard polling works |
| C-009 | No impact (additive) | 1. Per-file revert | Affected files | - |

---

## Sprint 4 Rollback

### Per-Change Rollback

| Issue | Rollback Trigger | Steps | Files to Restore | Verification |
|-------|------------------|-------|------------------|--------------|
| F-001 | Page errors | 1. Revert individual page files | `frontend/src/app/(dashboard)/*.tsx` | Placeholder restored |
| T-001 | Test instability | 1. Remove/modify individual test files | `backend/tests/test_*.py` | Existing tests pass |
| B-001 | Build fails | 1. Revert pyinstaller config | `build/pyinstaller_builder.py`, `build/config.py` | Full build succeeds |
| B-002 | CI pipeline issues | 1. Remove `.github/workflows/ci.yml` | `.github/workflows/ci.yml` | - |

---

## Database Rollback

If the `duration_ms` column or indexes cause issues:

```sql
-- Remove duration_ms column (SQLite 3.35+)
ALTER TABLE jobs DROP COLUMN duration_ms;

-- Drop indexes
DROP INDEX IF EXISTS idx_workers_status_paused;
DROP INDEX IF EXISTS idx_jobs_assigned_worker;
DROP INDEX IF EXISTS idx_jobs_status;
DROP INDEX IF EXISTS idx_wftasks_workflow_status;
DROP INDEX IF EXISTS idx_repofiles_repo_path;
DROP INDEX IF EXISTS idx_symbols_repo_type;
DROP INDEX IF EXISTS idx_aimsgs_session_ts;
DROP INDEX IF EXISTS idx_auditlogs_cat_sev_ts;
```

**Note**: SQLite `DROP COLUMN` requires SQLite 3.35.0+. In older versions, the workaround is to create a new table without the column and copy data.

---

## Rollback Verification

After any rollback, verify:

1. **Master starts**: `curl http://localhost:8000/api/v1/health` → 200
2. **Workers connect**: `python scripts/run-integration-test.py` → 40/40 PASS
3. **Frontend loads**: Browser → http://localhost:3000 → dashboard renders
4. **Tests pass**: `pytest backend/tests/ && pytest worker/tests/`
5. **Security**: At minimum, reverted to pre-v1.3.1 security posture (known risk)
