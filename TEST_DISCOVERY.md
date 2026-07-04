# AICluster Test Discovery

## Test Locations

Tests are distributed across the repository. There is no top-level `tests/` directory.

| Location | Type | Count | Framework |
|----------|------|-------|-----------|
| `backend/tests/` | Unit tests | ~44 tests | pytest + pytest-asyncio |
| `worker/tests/` | Unit tests | 14 tests | pytest |
| `scripts/run-integration-test.py` | Integration tests | 40 tests | Python script |
| `scripts/worker-simulator.py` | Interactive simulation | (manual) | Python + rich TUI |
| `docs/Audit/FILE_TEST_REPORT.md` | Static analysis | 187 files | Manual audit |

---

## 1. Backend Tests (`backend/tests/`)

### Test Categories
- **Auth tests**: Login, registration, token validation, default admin seeding
- **Worker tests**: Register, heartbeat, pause/resume, offline detection
- **Job tests**: Create, list, cancel, progress, result reporting
- **Dashboard tests**: Aggregated stats, worker counts, job counts
- **Health tests**: Endpoint response, DB connectivity
- **Validation tests**: Input validation, error handling, edge cases

### How to Run
```bash
cd backend
pytest -v
# or with coverage
pytest --cov=app tests/
```

### Coverage
- Tests exist for: auth, workers, jobs, dashboard, health
- **No tests for**: workflow, repository, AI, agents, engineering, plugins, audit, studio

---

## 2. Worker Tests (`worker/tests/`)

### Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_config.py` | `TestWorkerConfig` (3 tests) | Settings defaults, hostname fallback, IP resolution |
| `test_executor.py` | `TestExecutor` (5 tests) | EchoHandler, SleepHandler, CountFilesHandler, HashFileHandler, JobRegistry |
| `test_reconnect.py` | `TestReconnect` (4 tests) | RetryHandler initial state, increment, reset, delay progression |
| `test_registrar.py` | `TestRegistrar` (2 tests) | Registration failure returns None, initial state |

### Test Coverage Details
```
test_executor.py:
  ✓ test_echo_handler — EchoJobHandler returns correct structure
  ✓ test_sleep_handler — SleepJobHandler sleeps correct duration
  ✓ test_count_files_handler_nonexistent — Handles missing directory
  ✓ test_hash_file_handler_missing_path — Returns error on missing file
  ✓ test_registry — Register/lookup/registered_types

test_reconnect.py:
  ✓ test_retry_handler_initial_state — Attempt 0, delay 1
  ✓ test_retry_handler_increment — wait() increments attempt
  ✓ test_retry_handler_reset — reset() returns to 0
  ✓ test_retry_delays — Delay progression and capping

test_registrar.py:
  ✓ test_registration_failure_returns_none — Connection refused
  ✓ test_registrar_initial_state — worker_id is None
```

---

## 3. Integration Tests (`scripts/run-integration-test.py`)

### Test Phases (8 phases, 40 checks)

| Phase | Checks | What it tests |
|-------|--------|---------------|
| 1. Health Check | 3 | API responds, DB connected, valid JSON |
| 2. Worker Registration | 4 | Register 4 workers (HP-01 through HP-04) |
| 3. Worker List | 2 | List all workers, verify count = 4 |
| 4. Heartbeats | 12 | 6 rounds of heartbeats per worker |
| 5. Dashboard | 2 | Metrics populated (worker counts > 0) |
| 6. Jobs | 6 | Create 3 jobs, list jobs |
| 7. Logs | 6 | Log retrieval, level filtering |
| 8. Worker Timeout | 5 | Stop heartbeats → workers go offline |

### Latest Results
```
40/40 tests PASS

Sample output:
  ✓ Health Check: API responds, DB connected
  ✓ Worker Registration: 4 workers registered
  ✓ Worker List: Correct number of workers
  ✓ Heartbeats: 6 rounds processed
  ✓ Dashboard: Metrics populated
  ✓ Jobs: 3 created, listed successfully
  ✓ Logs: Filtered by level works
  ✓ Worker Timeout: Offline detection works
```

### How to Run
```bash
# Requires master server running on :8000
python scripts/run-integration-test.py
```

---

## 4. Interactive Simulator (`scripts/worker-simulator.py`)

A terminal-based TUI using the `rich` library that simulates 4 workers with:
- Live CPU/RAM/disk/temperature display
- Interactive controls: start, pause, resume, crash, kill
- Built-in validation test suite
- WebSocket event monitoring

### Controls
```
1-4         → Select worker
S           → Start worker
P           → Pause worker
R           → Resume worker
C           → Crash worker
K           → Kill worker
Space       → Run validation
Q           → Quit
```

---

## 5. Post-Build Verification (`build/verification/`)

### 10 Verification Stages

| # | Stage | File | What It Checks |
|---|-------|------|----------------|
| 1 | Build | `verify_build.py` | Exit code 0, release/ exists, manifest.json |
| 2 | Executables | `verify_executables.py` | 6 EXEs valid PE, version embedded, SHA-256 |
| 3 | Artifacts | `verify_artifacts.py` | 10 release subdirs, manifest |
| 4 | Config | `verify_config.py` | VERSION, CHANGELOG, README, icon, setup.iss |
| 5 | Python | `verify_python.py` | Bundled Python 3.12, host Python >= 3.12 |
| 6 | Frontend | `verify_frontend.py` | 4 frontends built, 3 Tauri smoke tests |
| 7 | Checksums | `verify_checksums.py` | SHA-256 matches checksums.txt + manifest.json |
| 8 | Installer | `verify_installer.py` | AIClusterSetup.exe valid PE, setup.iss sections |
| 9 | Backend | `verify_backend.py` | Launch master + worker, health check, shutdown |
| 10 | API | `verify_api.py` | HTTP GET /api/v1/health, /openapi.json, /docs |

---

## 6. Documentation-based Audits

### FILE_TEST_REPORT.md
- Static analysis of all 187 Python files
- 100% PASS rate
- Every file categorized by module with recommendations

### CODE_REVIEW.md
- 12 CRITICAL, 35 MAJOR, 20 MINOR findings
- Critical: no auth, hardcoded JWT secret, plugin upload RCE, blocking IO in async
- Major: unused imports, race conditions, missing validation, duplicate IP logic

### SECURITY_REVIEW.md
- 4 CRITICAL, 5 HIGH, 6 MEDIUM, 2 LOW findings
- Critical: JWT hardcoded secret, default admin creds, no auth on API, plugin upload RCE
- High: CORS misconfig, path traversal, no rate limiting, WebSocket without auth, no HTTPS

### MASTER_VALIDATION_REPORT.md
- 19 checks, all PASS
- Covers: build, frontend, backend, worker, installer, executables, APIs, workers, AI, studio,
  repository, workflow, agents, engineering, audit, plugins, production

---

## 7. Test Coverage Gaps

| Area | Tests | Risk |
|------|-------|------|
| Workflow Engine | None | HIGH |
| Repository Intelligence | None | HIGH |
| AI Runtime | None | HIGH |
| Multi-Agent Engine | None | HIGH |
| Engineering Engine | None | HIGH |
| Plugin System | None | MEDIUM |
| Audit System | None | MEDIUM |
| Studio API | None | LOW |
| WebSocket | None | MEDIUM |
| Frontend (unit) | None | MEDIUM |
| MCC/WCC/Studio (unit) | None | MEDIUM |
| Security/penetration | None | HIGH |
| Performance/load | None | HIGH |
