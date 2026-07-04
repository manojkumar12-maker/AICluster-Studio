# Database Change Matrix

## Overview

v1.3.1 makes minimal database changes. Only one column addition is required.

---

## Changes

### Table: `jobs`

| Change | Type | Detail |
|--------|------|--------|
| New column | ADD | `duration_ms: Float, nullable=True` |

**Purpose**: Store job execution duration (fixes C-006 where `duration_ms` was received but discarded with `pass`).

**Migration**: 
```sql
ALTER TABLE jobs ADD COLUMN duration_ms FLOAT;
```

**SQLite note**: SQLite supports `ALTER TABLE ADD COLUMN` but cannot add constraints after creation. The column is nullable, so no default value is needed.

---

## Indexes Added

| Table | Index | Columns | Reason |
|-------|-------|---------|--------|
| `workers` | `idx_workers_status_paused` | `(status, is_paused)` | Scheduler worker lookup |
| `jobs` | `idx_jobs_assigned_worker` | `(assigned_worker)` | Worker job lookup |
| `jobs` | `idx_jobs_status` | `(status)` | Queue processing |
| `workflow_tasks` | `idx_wftasks_workflow_status` | `(workflow_id, status)` | Task status queries |
| `repository_files` | `idx_repofiles_repo_path` | `(repository_id, path)` | File lookup |
| `symbols` | `idx_symbols_repo_type` | `(repository_id, symbol_type)` | Symbol queries |
| `ai_messages` | `idx_aimsgs_session_ts` | `(session_id, timestamp)` | History retrieval |
| `audit_logs` | `idx_auditlogs_cat_sev_ts` | `(category, severity, timestamp)` | Audit queries |

**Migration**:
```sql
CREATE INDEX IF NOT EXISTS idx_workers_status_paused ON workers(status, is_paused);
CREATE INDEX IF NOT EXISTS idx_jobs_assigned_worker ON jobs(assigned_worker);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_wftasks_workflow_status ON workflow_tasks(workflow_id, status);
CREATE INDEX IF NOT EXISTS idx_repofiles_repo_path ON repository_files(repository_id, path);
CREATE INDEX IF NOT EXISTS idx_symbols_repo_type ON symbols(repository_id, symbol_type);
CREATE INDEX IF NOT EXISTS idx_aimsgs_session_ts ON ai_messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_auditlogs_cat_sev_ts ON audit_logs(category, severity, timestamp);
```

---

## Impact Analysis

| Concern | Assessment |
|---------|------------|
| **Migration required** | YES — simple ALTER TABLE + CREATE INDEX. No data loss. |
| **Startup impact** | `init_db()` uses `create_all()` which is idempotent. Indexes created on first startup after migration. |
| **Rollback plan** | `ALTER TABLE jobs DROP COLUMN duration_ms` (SQLite 3.35+). Indexes: `DROP INDEX IF EXISTS idx_*`. |
| **Downtime required** | None — schema changes are backward compatible. |
| **Data migration** | None — `duration_ms` is nullable, existing jobs get NULL. |
| **Write performance** | Indexes add overhead on INSERT/UPDATE. Negligible for SQLite workload. |
| **Read performance** | **IMPROVED** — queries use indexes instead of full table scans. |
| **Storage impact** | ~2-5 MB for all indexes combined (depends on table sizes). |

---

## Unchanged Tables

The following tables have NO schema changes in v1.3.1:
- `users` (unchanged)
- `workers` (unchanged — worker_secret stored in config, not DB)
- `system_logs` (unchanged)
- All workflow tables (unchanged)
- All repository tables (unchanged)
- All AI tables (unchanged)
- All agent tables (unchanged)
- All engineering tables (unchanged)
- All studio tables (unchanged)
- All audit tables (unchanged)
