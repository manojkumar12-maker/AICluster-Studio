# AICluster Database Schema

**Engine:** SQLite via SQLAlchemy Async
**File:** `backend/data/aicluster.db`

---

## Table: `workers`

Stores registered worker node information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PK, UUID | Unique worker identifier |
| worker_name | String(255) | NOT NULL, UNIQUE, INDEX | Human-readable name (e.g. HP-01) |
| hostname | String(255) | NOT NULL | Network hostname |
| ip | String(45) | NOT NULL | IP address |
| status | String(32) | DEFAULT 'offline' | online, offline, busy, paused, error |
| cpu_percent | Float | DEFAULT 0.0 | Current CPU usage % |
| ram_percent | Float | DEFAULT 0.0 | Current RAM usage % |
| disk_percent | Float | DEFAULT 0.0 | Current disk usage % |
| temperature | Float | NULLABLE | CPU temperature in Celsius |
| network_speed | Float | DEFAULT 0.0 | Network throughput |
| current_job | String(36) | NULLABLE | ID of currently assigned job |
| version | String(32) | DEFAULT '1.0.0' | Worker agent version |
| cpu_limit | Float | DEFAULT 25.0 | Max CPU % allowed |
| ram_limit | Float | DEFAULT 8.0 | Max RAM in GB |
| priority | Integer | DEFAULT 0 | Worker selection priority |
| is_paused | Boolean | DEFAULT FALSE | Whether worker is paused |
| last_seen | DateTime | NOT NULL | Last heartbeat timestamp |
| registered_at | DateTime | NOT NULL | Registration timestamp |

**Indexes:** `worker_name` (unique), `status`, `last_seen`, `is_paused`

---

## Table: `jobs`

Stores the job queue and history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PK, UUID | Unique job identifier |
| type | String(64) | DEFAULT 'custom', INDEX | Job type classification |
| status | String(32) | DEFAULT 'queued', INDEX | queued, running, completed, failed, cancelled, retrying |
| assigned_worker | String(36) | NULLABLE, INDEX | Worker executing this job |
| progress | Float | DEFAULT 0.0 | Completion percentage (0–100) |
| payload | JSON | DEFAULT {} | Job input data |
| result | JSON | NULLABLE | Job output data |
| error | Text | NULLABLE | Error message on failure |
| logs | Text | NULLABLE | Execution logs |
| priority | Integer | DEFAULT 2 | 1=low, 2=medium, 3=high, 4=critical, 5=emergency |
| retry_count | Integer | DEFAULT 0 | Number of retries attempted |
| max_retries | Integer | DEFAULT 3 | Maximum retries allowed |
| created_at | DateTime | NOT NULL, INDEX | Job creation timestamp |
| started_at | DateTime | NULLABLE | Job start timestamp |
| finished_at | DateTime | NULLABLE | Job completion/failure timestamp |

**Indexes:** `status`, `type`, `assigned_worker`, `created_at`; Composite: `(priority, created_at)`

---

## Table: `system_logs`

Stores structured application log entries.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PK, UUID | Unique log entry identifier |
| level | String(16) | DEFAULT 'INFO', INDEX | Log level (INFO, WARNING, ERROR) |
| message | Text | NOT NULL | Log message text |
| source | String(64) | NULLABLE, INDEX | Component that generated the log |
| created_at | DateTime | NOT NULL, INDEX | Timestamp |

**Indexes:** `level`, `source`, `created_at`; Composite: `(level, created_at)`

---

## Table: `users`

Stores authentication users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PK, UUID | Unique user identifier |
| username | String(50) | UNIQUE, INDEX, NOT NULL | Login username |
| hashed_password | String(255) | NOT NULL | bcrypt-hashed password |
| role | String(32) | DEFAULT 'developer', INDEX | admin, developer, viewer |
| is_active | Boolean | DEFAULT TRUE | Whether user is active |
| created_at | DateTime | NOT NULL | Creation timestamp |

**Indexes:** `username` (unique), `role`

---

## Entity Relationship

```
┌──────────┐       ┌──────────┐       ┌─────────────┐
│  users   │       │ workers  │       │    jobs     │
├──────────┤       ├──────────┤       ├─────────────┤
│ id (PK)  │       │ id (PK)  │       │ id (PK)     │
│ username │       │ name     │◄──────┤ assigned_wk │
│ password │       │ status   │  FK   │ type        │
│ role     │       │ cpu%     │       │ status      │
│ is_active│       │ ram%     │       │ progress    │
└──────────┘       │ disk%    │       │ priority    │
                   │ temp     │       │ payload     │
                   │ paused   │       │ result      │
                   │ last_seen│       │ error       │
                   │ reg_at   │       │ created_at  │
                   └──────────┘       │ started_at  │
                                       │ finished_at │
                  ┌────────────┐       └─────────────┘
                  │system_logs │
                  ├────────────┤
                  │ id (PK)    │
                  │ level      │
                  │ message    │
                  │ source     │
                  │ created_at │
                  └────────────┘
```

## Migration

Alembic is installed but not configured. For schema changes:

```powershell
cd AICluster/backend
.venv\Scripts\alembic init alembic
.venv\Scripts\alembic revision --autogenerate -m "description"
.venv\Scripts\alembic upgrade head
```
