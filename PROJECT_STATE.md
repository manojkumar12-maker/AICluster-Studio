# AICluster — Project State

## Current Version
v1.2.1

## Current Phase
v1.2.1 — Master Audit System (Non-Breaking Enhancement)

## Overall Completion
100%

- All 11 phases complete
- v1.1.0 Release Ready

- All 10 phases complete
- v1.0.0 Release Candidate ready

- Phase 1 (Structure): 100%
- Phase 2 (Master Server): 100%
- Phase 2.1 (Stability): 100%
- Phase 3 (Worker Service): 50% (Phase 3A + 4: communication and execution, Phase 3B/C pending)
- Phase 3.5 (Cluster Operations): 100%
- Phase 4 (Workflow Engine): 100%
- Phase 5 (Repository Intelligence): 100%
- Phase 6 (AI Runtime): 100%
- Phase 7 (Multi-Agent): 100%
- Phase 8 (Local LLM): 100%
- Phase 4 (Dashboard Full): 80% (placeholder pages remain)
- Phase 5 (AI Chat): 0%
- Phase 6 (Scheduler Full): 70% (queuing works, execution pending)
- Phase 7 (Documentation): 80%

## Completed Features

### Backend (Master Server)
- FastAPI application with async SQLAlchemy + SQLite
- JWT authentication with bcrypt password hashing
- Worker registration and heartbeat processing
- Automatic worker offline detection (15s timeout)
- Job queue with priority-based scheduling
- WebSocket endpoint for real-time updates (`/ws`)
- Structured logging to `system_logs` table
- CORS middleware configured for frontend
- Rate limiting on API endpoints
- Default admin user seeded on first startup

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | User login, returns JWT |
| POST | `/api/v1/workers/register` | Register a new worker |
| POST | `/api/v1/workers/heartbeat` | Receive worker heartbeat |
| GET | `/api/v1/workers` | List all workers |
| GET | `/api/v1/workers/{id}` | Get worker by ID |
| POST | `/api/v1/workers/{id}/pause` | Pause a worker |
| POST | `/api/v1/workers/{id}/resume` | Resume a worker |
| GET | `/api/v1/workers/{id}/next-job` | Worker polls for next job (Phase 3) |
| POST | `/api/v1/workers/{id}/progress` | Worker reports job progress (Phase 3) |
| POST | `/api/v1/workers/{id}/result` | Worker reports job result (Phase 3) |
| POST | `/api/v1/jobs` | Create a new job |
| GET | `/api/v1/jobs` | List all jobs |
| GET | `/api/v1/jobs/{id}` | Get job by ID |
| DELETE | `/api/v1/jobs/{id}` | Cancel a job |
| GET | `/api/v1/dashboard` | Get aggregated dashboard metrics |
| GET | `/api/v1/health` | Health check endpoint |
| GET | `/api/v1/logs` | Retrieve system logs |
| WS | `/ws` | WebSocket for real-time updates |
| GET | `/docs` | OpenAPI Swagger UI |
| GET | `/redoc` | OpenAPI ReDoc |
| POST | `/api/v1/workflow` | Create workflow |
| GET | `/api/v1/workflow` | List workflows |
| GET | `/api/v1/workflow/{id}` | Get workflow with DAG |
| DELETE | `/api/v1/workflow/{id}` | Cancel workflow |
| POST | `/api/v1/workflow/{id}/pause` | Pause workflow |
| POST | `/api/v1/workflow/{id}/resume` | Resume workflow |
| POST | `/api/v1/workflow/{id}/cancel` | Cancel workflow |
| GET | `/api/v1/workflow/{id}/tasks` | Get workflow tasks |
| GET | `/api/v1/workflow/{id}/artifacts` | Get workflow artifacts |
| GET | `/api/v1/workflow/{id}/metrics` | Get workflow metrics |
| GET | `/api/v1/workflow/queue` | Queue statistics |
| GET | `/api/v1/workflow/history` | Workflow history |
| GET | `/api/v1/workflow/workers/capabilities` | Worker capabilities |
| POST | `/api/v1/agents/run` | Run multi-agent orchestration |
| GET | `/api/v1/agents` | List agents |
| GET | `/api/v1/agents/{id}` | Get agent details |
| POST | `/api/v1/agents/register` | Register new agent |
| POST | `/api/v1/agents/{id}/pause` | Pause agent |
| POST | `/api/v1/agents/{id}/resume` | Resume agent |
| POST | `/api/v1/agents/{id}/disable` | Disable agent |
| GET | `/api/v1/agents/messages` | Get agent messages |
| GET | `/api/v1/agents/tasks` | Get agent tasks |
| GET | `/api/v1/agents/memory` | Get agent memory |
| GET | `/api/v1/agents/metrics` | Get agent metrics |

### Frontend
- Next.js 15 App Router with TypeScript
- Dark glassmorphism theme with shadcn/ui components
- Zustand auth store with persistence
- React Query for API data fetching (2s polling)
- Responsive sidebar navigation
- Dashboard page connected to real backend API
- Workers page connected to real backend API
- Loading skeletons and error states
- 404 and 500 error pages
- Login page with validation and error handling

### Database Tables
- `workers` — Worker nodes (id, name, hostname, ip, cpu%, ram%, disk%, temperature, status, etc.)
- `jobs` — Job queue (id, type, status, priority, progress, assigned_worker, etc.)
- `system_logs` — Structured application logs (id, level, message, source)
- `users` — Authentication users (id, username, hashed_password, role)
- `workflows` — Workflow definitions (id, name, type, status, progress, tasks, etc.)
- `workflow_tasks` — Individual tasks within workflows (id, type, status, assigned_worker, duration, etc.)
- `task_dependencies` — Task dependency graph edges (task_id, depends_on_id)
- `workflow_results` — Completed workflow/task results
- `artifacts` — Stored execution outputs (SHA256 checksum, size, storage path)
- `execution_metrics` — Performance metrics (workflow_id, metric_type, value, unit)
- `cache` — Cached task results (TTL-based expiry)
- `workflow_events` — Event stream for workflows/tasks
- `worker_capabilities` — Worker resource and capability reporting

### Testing
- 44 pytest backend unit + edge case tests (all passing)
- 40 end-to-end integration tests (all passing)
- 14 worker unit tests (all passing — config, executor, registrar, reconnect)
- Workflow engine models validated (9 new tables, no SQLAlchemy conflicts)
- Auth tests (login, invalid credentials, missing fields, malformed JSON)
- Validation tests (missing fields, empty values, out-of-range, duplicate registration, unknown worker/job)
- Worker timeout validation verified
- Job CRUD operations verified
- Dashboard aggregation verified
- Logging pipeline verified
- Isolated temp-file database per test session (no shared state)

## Folder Structure

```
AICluster/
├── frontend/                  # Next.js 15 dashboard
│   ├── src/
│   │   ├── app/              # Pages and layouts
│   │   │   ├── (dashboard)/  # Protected dashboard routes
│   │   │   ├── login/        # Login page
│   │   │   └── ...
│   │   ├── components/       # UI components
│   │   ├── lib/              # Utilities
│   │   ├── stores/           # Zustand stores
│   │   └── types/            # TypeScript type definitions
│   ├── public/               # Static assets
│   └── ...
├── backend/                   # FastAPI master server
│   ├── app/
│   │   ├── api/v1/           # REST API routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── websocket/        # WebSocket manager
│   │   ├── config.py         # Application configuration
│   │   ├── database.py       # Database engine and session
│   │   └── main.py           # FastAPI application entry point
│   └── tests/                # pytest test suite
├── backend/app/workflow/      # Workflow Engine (Phase 4)
│   ├── planner/               # DAG generation, dependency resolution
│   ├── dispatcher/            # Task-to-worker assignment
│   ├── executor/              # Workflow orchestration engine
│   ├── artifacts/             # Artifact storage and retrieval
│   ├── cache/                 # Result caching
│   ├── metrics/               # Execution metrics
│   └── state/                 # State machine definitions
├── worker/                    # Worker agent (Phase 3A: communication)
├── scripts/                   # Utility scripts
│   ├── setup.ps1             # Environment setup
│   ├── start-master.ps1      # Master server startup
│   ├── start-worker.ps1      # Worker startup
│   ├── worker-simulator.py   # Worker simulator (TUI)
│   └── run-integration-test.py # Integration test runner
├── config/                    # YAML configuration files
├── docs/                      # Documentation
├── shared/                    # Shared types/schemas
└── logs/                      # Application logs
```

## Dependencies

### Backend (Python 3.12)
```
fastapi==0.115.4       sqlalchemy==2.0.36        pydantic==2.10.2
uvicorn[standard]==0.32.0  alembic==1.14.0        pydantic-settings==2.6.1
python-jose[cryptography]==3.3.0  passlib[bcrypt]==1.7.4  bcrypt<4.1
websockets==14.1       aiosqlite==0.20.0         greenlet==3.1.1
httpx==0.28.0          psutil==6.1.0
python-multipart==0.0.16  PyYAML==6.0.2
```

### Frontend (Node.js 20+)
```
next@15.0.3            react@18.3.1              tailwindcss@3.4.15
@tanstack/react-query  zustand@5.0.1             framer-motion
recharts               lucide-react              @radix-ui/*
class-variance-authority  clsx  tailwind-merge
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=sqlite+aiosqlite:///./data/aicluster.db
SECRET_KEY=aicluster-secret-key-change-in-production
PORT=8000
WORKER_TIMEOUT_SECONDS=15
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Worker (.env) — for Phase 3
```
MASTER_URL=http://localhost:8000
WORKER_PORT=8001
CPU_LIMIT=25
RAM_LIMIT_GB=8
HEARTBEAT_INTERVAL=5
```

## Current Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Master PC                         │
│  ┌────────────────┐    ┌──────────────────────────┐ │
│  │  Next.js 15     │    │  FastAPI Backend         │ │
│  │  localhost:3000 │◄──►│  localhost:8000           │ │
│  │  - Dashboard   │    │  - REST API              │ │
│  │  - Workers     │    │  - WebSocket /ws         │ │
│  │  - Jobs        │    │  - SQLite DB             │ │
│  │  - Settings    │    │  - JWT Auth              │ │
│  └────────────────┘    │  - Job Scheduler         │ │
│                         │  - Worker Manager        │ │
│                         └──────────┬───────────────┘ │
│                                    │                 │
└────────────────────────────────────┼─────────────────┘
                                     │
                     ┌───────────────┼───────────────┐
                     │               │               │
              ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
              │  Worker PC  │ │  Worker PC  │ │  Worker PC  │
              │  (Phase 3)  │ │  (Phase 3)  │ │  (Phase 3)  │
              └─────────────┘ └─────────────┘ └─────────────┘
```

## Known Issues
1. Frontend placeholder pages exist for Workers (functional), Jobs, Chat, Projects, Files, Analytics, Logs, Settings — these are ready for Phase 2+ enhancement but some only show "coming soon"
2. JWT tokens have no refresh mechanism — expire after 60 minutes
3. The `jobs_per_second` and `avg_execution_time_ms` fields in the frontend types are not populated by the backend (no job execution tracking yet)
4. WebSocket broadcasts are sent on every heartbeat — may need batching for 100+ worker scale

## Technical Debt
1. Backend `config.py` uses `pydantic-settings` but old `app/core/config.py` remnants may exist (cleanup done in Phase 2)
2. The `shared/` directory contains types that duplicate the frontend `src/types/index.ts` — keep in sync
3. No database migration system applied yet (Alembic installed but not configured)
4. No CI/CD pipeline configured
5. Auth middleware (`get_current_user`) is available but not enforced on all endpoints — opt-in per endpoint
6. Worker service is still in Phase 1 scaffolding — full implementation in Phase 3

## Remaining Work
- Phase 3B: Worker resource management (CPU throttling, RAM limits, process priority)
- Phase 3C: Worker auto-pause/resume based on user activity detection
- Phase 4: Full dashboard with charts (Recharts), analytics, file manager
- Phase 5: AI chat integration with distributed workload
- Phase 6: Distributed job execution across workers
- Phase 7: Production hardening, HTTPS, deployment scripts

## Last Successful Tests
- pytest: 44/44 passed (backend unit + edge case tests)
- Worker tests: 14/14 passed (config, executor, registrar, reconnect)
- Integration: 40/40 passed (end-to-end)
- Build: next build succeeds (15 pages, zero errors)
- Lint: next lint passes (zero warnings)
- Dev server: starts in ~1.5s

## Git Commit Recommendation
```bash
git add AICluster/
git commit -m "Phase 3A complete: Worker communication service with registration, heartbeat, job polling, executor framework, progress and result reporting"
```
