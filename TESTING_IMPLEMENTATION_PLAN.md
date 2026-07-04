# AICluster v1.3.1 Testing Implementation Plan

## Current Test Coverage

| Location | Tests | Coverage |
|----------|-------|----------|
| `backend/tests/` | ~44 | Auth, workers, jobs, dashboard, health |
| `worker/tests/` | 14 | Config, executor, reconnect, registrar |
| Integration | 40 | E2E cluster simulation |
| Frontend | 0 | None |
| MCC/WCC/Studio | 0 | None |

**Untested Subsystems**: Workflow, Repository, AI, Agents, Engineering, Plugins, Audit, WebSocket

---

## T-001: Subsystem Unit Tests

### Workflow Engine Tests
**File**: `backend/tests/test_workflow.py`

| Test | Description | Type |
|------|-------------|------|
| `test_create_workflow` | Create workflow, verify DAG stored | Unit |
| `test_create_workflow_invalid_dag` | Cyclic DAG rejected | Unit |
| `test_create_workflow_empty` | Empty DAG rejected | Unit |
| `test_get_workflow` | Retrieve by ID | Unit |
| `test_list_workflows` | Filter by status | Unit |
| `test_delete_workflow` | Delete existing | Unit |
| `test_delete_workflow_running` | Cannot delete running | Unit |
| `test_pause_resume_workflow` | Lifecycle | Unit |
| `test_cancel_workflow` | Cancel during execution | Unit |
| `test_queue_workflow` | Queue processing | Integration |

### Repository Intelligence Tests
**File**: `backend/tests/test_repository.py`

| Test | Description | Type |
|------|-------------|------|
| `test_create_repository` | Register new repo | Unit |
| `test_scan_repository` | Scan files | Integration |
| `test_symbol_extraction` | Parse symbols | Unit |
| `test_search_fulltext` | Search indexed content | Integration |
| `test_search_regex` | Regex search | Unit |
| `test_get_dependencies` | Dependency graph | Integration |
| `test_get_metrics` | Code metrics | Unit |
| `test_knowledge_graph` | Knowledge graph | Integration |
| `test_delete_repository` | Remove and cleanup | Unit |
| `test_rescan_updates` | Rescan detects changes | Integration |

### AI Runtime Tests
**File**: `backend/tests/test_ai.py`

| Test | Description | Type |
|------|-------------|------|
| `test_create_session` | New chat session | Unit |
| `test_session_expiry` | Session expires | Unit |
| `test_add_message` | Message persistence | Unit |
| `test_get_history` | Message history | Unit |
| `test_register_model` | Model registration | Unit |
| `test_model_loading` | Load/unload lifecycle | Unit |
| `test_context_building` | Context from repo | Unit |
| `test_prompt_template` | Template rendering | Unit |
| `test_tool_registry` | Tool registration | Unit |
| `test_provider_registry` | Provider management | Unit |
| `test_model_routing` | Task-based routing | Unit |

### Multi-Agent Tests
**File**: `backend/tests/test_agents.py`

| Test | Description | Type |
|------|-------------|------|
| `test_register_agent` | Agent registration | Unit |
| `test_seed_default_agents` | Default 12 agents | Unit |
| `test_agent_pause_resume` | Lifecycle | Unit |
| `test_agent_disable` | Disable agent | Unit |
| `test_agent_metrics` | Metrics collection | Unit |
| `test_agent_memory` | Memory CRUD | Unit |
| `test_agent_messages` | Inter-agent messaging | Unit |
| `test_get_tasks` | Task filtering | Unit |
| `test_agent_persistence` | DB persistence | Unit |

### Engineering Engine Tests
**File**: `backend/tests/test_engineering.py`

| Test | Description | Type |
|------|-------------|------|
| `test_create_plan` | Create engineering plan | Unit |
| `test_get_tasks` | Task listing | Unit |
| `test_get_reports` | Report generation | Unit |
| `test_get_metrics` | Metrics | Unit |
| `test_get_quality` | Quality gates | Unit |
| `test_approve_plan` | Approval flow | Unit |
| `test_create_patch` | Patch creation | Unit |
| `test_validation` | Validation checks | Unit |
| `test_repair_flow` | Repair cycle | Integration |

### Plugin System Tests
**File**: `backend/tests/test_plugins.py`

| Test | Description | Type |
|------|-------------|------|
| `test_list_plugins` | Empty list | Unit |
| `test_install_plugin` | Plugin installation | Integration |
| `test_install_invalid_manifest` | Bad manifest rejected | Unit |
| `test_enable_disable` | Lifecycle | Unit |
| `test_uninstall` | Clean removal | Unit |
| `test_list_hooks` | Hook enumeration | Unit |
| `test_plugin_execution` | Hook execution | Integration |

### Audit System Tests
**File**: `backend/tests/test_audit.py`

| Test | Description | Type |
|------|-------------|------|
| `test_log_event` | Log creation | Unit |
| `test_search_logs` | Filtered search | Unit |
| `test_statistics` | Stats aggregation | Unit |
| `test_export_csv` | CSV export | Integration |
| `test_export_json` | JSON export | Integration |
| `test_purge_logs` | Retention policy | Unit |
| `test_settings_crud` | Settings management | Unit |
| `test_middleware_capture` | HTTP audit capture | Integration |

### WebSocket Tests
**File**: `backend/tests/test_websocket.py`

| Test | Description | Type |
|------|-------------|------|
| `test_connect` | Basic connect | Integration |
| `test_disconnect` | Graceful disconnect | Integration |
| `test_broadcast` | Message broadcast | Integration |
| `test_broadcast_worker` | Worker event format | Unit |
| `test_broadcast_job` | Job event format | Unit |
| `test_broadcast_dashboard` | Dashboard event format | Unit |
| `test_multiple_clients` | Concurrent connections | Integration |
| `test_max_connections` | Connection limit | Integration |

---

## T-002: Auth Integration Tests

**File**: `backend/tests/test_auth_integration.py`

| Test | Description |
|------|-------------|
| `test_login_success` | Valid credentials → 200 + token |
| `test_login_invalid_password` | Wrong password → 401 |
| `test_login_inactive_user` | Disabled user → 401 |
| `test_login_nonexistent_user` | Unknown user → 401 |
| `test_protected_route_no_auth` | No token → 401 |
| `test_protected_route_valid_token` | Valid token → 200 |
| `test_protected_route_expired_token` | Expired token → 401 |
| `test_protected_route_invalid_token` | Malformed token → 401 |
| `test_admin_route_dev_role` | Developer → 403 |
| `test_admin_route_admin_role` | Admin → 200 |
| `test_public_routes_no_auth` | Health login → 200 |
| `test_worker_endpoints` | Worker token flow |

---

## T-003: Frontend Tests

**Framework**: Vitest + @testing-library/react

**File**: `frontend/src/stores/__tests__/auth-store.test.ts`

| Test | Description |
|------|-------------|
| `test_initial_state` | No token, no user |
| `test_login_success` | Store updated on login |
| `test_login_failure` | Error handled on failure |
| `test_logout` | State cleared |
| `test_persistence` | Token persists in localStorage |

**File**: `frontend/src/components/layout/__tests__/sidebar.test.tsx`

| Test | Description |
|------|-------------|
| `test_renders_all_nav_items` | 10 items displayed |
| `test_active_item_highlighted` | Current page highlighted |
| `test_navigation` | Click changes page |

**File**: `frontend/src/app/login/__tests__/page.test.tsx`

| Test | Description |
|------|-------------|
| `test_renders_login_form` | Form elements present |
| `test_submit_valid` | Login called with credentials |
| `test_submit_invalid` | Error message displayed |
| `test_redirect_on_auth` | Redirected if already logged in |

**File**: `frontend/src/app/(dashboard)/dashboard/__tests__/page.test.tsx`

| Test | Description |
|------|-------------|
| `test_renders_loading` | Skeleton shown while loading |
| `test_renders_metrics` | Cards displayed with data |
| `test_renders_error` | Error state handled |

---

## Test Infrastructure

### Backend Test Configuration
```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_data/test.db"

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Test Commands
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Worker tests
cd worker
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npx vitest --coverage

# All tests
cd backend && pytest && cd ../worker && pytest && cd ../frontend && npx vitest
```

### CI Integration (for B-002)
```yaml
# .github/workflows/test.yml
jobs:
  backend:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: pytest backend/tests/ -v --cov=backend/app

  frontend:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npx vitest --run
```

---

## Test Coverage Targets

| Area | Current | Sprint 4 Target |
|------|---------|-----------------|
| Backend (core) | ~10% | >70% |
| Backend (workflow) | 0% | >60% |
| Backend (AI) | 0% | >60% |
| Backend (agents) | 0% | >60% |
| Backend (engineering) | 0% | >50% |
| Backend (plugins) | 0% | >60% |
| Backend (audit) | 0% | >70% |
| Backend (WebSocket) | 0% | >50% |
| Worker | ~40% | >70% |
| Frontend | 0% | >30% |
| Integration (E2E) | 40 tests | >60 tests |
