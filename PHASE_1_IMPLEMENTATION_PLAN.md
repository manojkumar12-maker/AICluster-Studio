# AICluster v1.3.1 Implementation Plan

## Overview

| Field | Value |
|-------|-------|
| **Version** | 1.3.0 → 1.3.1 |
| **Release Name** | Security & Stability Release |
| **Theme** | Production Readiness |
| **Scope** | No new features. Fix all security, stability, and code quality issues. |
| **Sprints** | 4 (2 weeks each = 8 weeks total) |
| **Current Score** | 7.5/10 |
| **Target Score** | 9.2/10 |

---

## Issue Inventory

| ID | Title | Category | Severity | Sprint |
|----|-------|----------|----------|--------|
| S-001 | JWT secret hardcoded in source code | Security | CRITICAL | 1 |
| S-002 | Default admin credentials (admin/admin123) | Security | CRITICAL | 1 |
| S-003 | No authentication enforcement on API endpoints | Security | CRITICAL | 1 |
| S-004 | Plugin upload allows arbitrary code execution | Security | CRITICAL | 3 |
| S-005 | CORS allows all origins | Security | HIGH | 1 |
| S-006 | Path traversal in worker handlers (dir_scan, hash_file) | Security | HIGH | 2 |
| S-007 | No rate limiting on any API endpoint | Security | HIGH | 3 |
| S-008 | WebSocket endpoint without authentication | Security | HIGH | 2 |
| S-009 | Worker registration without authentication | Security | HIGH | 2 |
| S-010 | No HTTPS support | Security | HIGH | 3 |
| S-011 | JWT token stored in localStorage | Security | MEDIUM | 3 |
| S-012 | SQL injection risk in repository search | Security | HIGH | 2 |
| S-013 | Information disclosure via error messages | Security | MEDIUM | 3 |
| C-001 | Worker `services/executor.py` is dead code | Code Quality | MEDIUM | 2 |
| C-002 | `execute_with_progress` called but not defined on BaseJobHandler | Bug | HIGH | 2 |
| C-003 | `report_result` called on None (worker main.py) | Bug | HIGH | 2 |
| C-004 | `poll()` result not properly awaited/checked | Bug | MEDIUM | 2 |
| C-005 | Double commit in `get_next_for_worker` | Bug | HIGH | 1 |
| C-006 | `duration_ms` never stored in `complete_job` | Bug | MEDIUM | 1 |
| C-007 | Blocking `os.walk()` in async worker handlers | Performance | HIGH | 2 |
| C-008 | Scheduler loop not properly stoppable | Code Quality | MEDIUM | 1 |
| C-009 | Empty except blocks throughout codebase | Code Quality | MEDIUM | 3 |
| C-010 | Duplicate IP resolution logic | Code Quality | LOW | 4 |
| F-001 | 8 of 10 dashboard pages are placeholders | UI | MEDIUM | 4 |
| F-002 | Studio IDE is starter template | UI | LOW | 4 |
| F-003 | Frontend doesn't connect to WebSocket | UI | MEDIUM | 3 |
| T-001 | No tests for 8 subsystems (workflow, repo, AI, agents, etc.) | Testing | HIGH | 4 |
| T-002 | No integration tests for auth flow | Testing | HIGH | 4 |
| T-003 | No frontend component tests | Testing | MEDIUM | 4 |
| B-001 | PyInstaller binary sizes (80MB+) | Build | LOW | 4 |
| B-002 | No CI/CD pipeline | Build | MEDIUM | 4 |

---

## Sprint Plan

### Sprint 1: Authentication & Authorization (Weeks 1-2)

**Theme**: Lock down the API. Every endpoint must require authentication.

**Issues**: S-001, S-002, S-003, S-005, C-005, C-006, C-008

#### S-001: JWT Secret Hardcoded
- Move secret to environment variable with generated fallback
- Add `AICLUSTER_SECRET_KEY` env var to `.env`, config.py
- Generate random 32-byte key on first run if not set
- Store generated key in `data/secret.key` file
- **Files**: `backend/app/config.py`, `backend/.env`
- **Tests**: Verify key generation, verify key persistence, verify key rotation

#### S-002: Default Admin Credentials
- Generate random admin password on first run
- Print to console/stderr on first startup
- Store bcrypt hash in database
- Add `--seed-admin-password` CLI override
- **Files**: `backend/app/services/auth.py`, `backend/app/main.py`
- **Tests**: Verify random password generation, verify login with generated password

#### S-003: Authentication Enforcement
- Add `get_current_user` dependency to every protected route
- Create `require_role("admin")` dependency for admin-only endpoints
- Add public endpoint whitelist: `/api/v1/health`, `/api/v1/auth/login`, `/docs`, `/openapi.json`
- All other endpoints require valid JWT
- Workers register with pre-shared token (new config field)
- **Files**: ALL route files in `backend/app/api/v1/`
- **Tests**: 401 on unauthorized, 200 on authorized, role enforcement, token expiry

#### S-005: CORS Restriction
- Configure CORS from config file instead of `["*"]`
- Add `cors_origins` to `default.yaml` config
- Default to `["http://localhost:3000"]` for development
- Production config must be explicit
- **Files**: `backend/app/main.py`, `config/default.yaml`, `config/production.yaml`
- **Tests**: Verify CORS headers, verify origin restriction

#### C-005: Double Commit in get_next_for_worker
- Remove first `await self.db.commit()` after worker update
- Keep second commit after SystemLog insert
- Or restructure to single commit
- **Files**: `backend/app/services/scheduler.py`
- **Tests**: Verify job assignment works, verify no integrity errors

#### C-006: duration_ms Not Stored
- Add `Job.duration_ms` column or store in `execution_metrics`
- Actually set `job.duration_ms = duration_ms` in `complete_job`
- **Files**: `backend/app/services/scheduler.py`, `backend/app/models/job.py`
- **Tests**: Verify duration is persisted

#### C-008: Scheduler Loop Not Properly Stoppable
- Replace `_running` flag with `asyncio.Event` for cancellation
- Add timeout to `_process_queue()` to prevent hangs
- **Files**: `backend/app/services/scheduler.py`
- **Tests**: Verify scheduler stops within 1s, verify clean shutdown

### Sprint 2: Worker & Data Stability (Weeks 3-4)

**Theme**: Fix all worker bugs, prevent data corruption, add path validation.

**Issues**: S-006, S-008, S-009, S-012, C-001, C-002, C-003, C-004, C-007

#### S-006: Path Traversal in Worker Handlers
- Add `_validate_path(path)` to all file-based handlers
- Reject paths with `..`, absolute paths not in allowed roots
- Add `allowed_directories` config option
- **Files**: `worker/app/executor/handlers/dir_scan.py`, `worker/app/executor/handlers/hash_file.py`, `worker/app/executor/handlers/count_files.py`
- **Tests**: Path traversal attempt rejected, valid paths work

#### S-008: WebSocket Authentication
- Require JWT token as query parameter or during handshake
- Validate token on connect
- Reject unauthenticated connections
- **Files**: `backend/app/websocket/manager.py`, `backend/app/main.py`
- **Tests**: Verified token connects, invalid token rejected

#### S-009: Worker Registration Auth
- Add `worker_secret` to config (pre-shared key per worker or globally)
- Workers include `Authorization: Bearer <worker_secret>` in all requests
- Master validates worker_secret for register/heartbeat/progress/result
- **Files**: `backend/app/api/v1/workers.py`, `backend/app/services/worker_manager.py`, `worker/app/config.py`, `worker/app/utils/http_client.py`
- **Tests**: Valid worker registers, invalid worker rejected

#### S-012: SQL Injection in Repository Search
- Use parameterized queries (already using SQLAlchemy, verify)
- Validate regex input with timeout
- Restrict search to indexed fields only
- **Files**: `backend/app/repository/search/service.py`, `backend/app/api/v1/repositories.py`
- **Tests**: Regex injection attempt, long-running regex timeout

#### C-001: Remove Dead Code (services/executor.py)
- Remove `worker/app/services/executor.py`
- Remove any imports referencing it
- **Files**: `worker/app/services/executor.py`, `worker/app/services/__init__.py`
- **Tests**: Verify imports still work, verify JobRegistry path still works

#### C-002: execute_with_progress on BaseJobHandler
- Add `execute_with_progress` to `BaseJobHandler` as async generator
- Default implementation yields progress 0, then calls `execute`
- Update `EchoJobHandler`, `SleepJobHandler`, etc. if needed
- Or simplify: remove the `execute_with_progress` branch from `main.py`
- **Files**: `worker/app/executor/base.py`, `worker/app/main.py`
- **Tests**: Verify handler execution still works

#### C-003: report_result Called on None
- Initialize `reporter` before worker loop
- Add null checks before calling reporter methods
- Or create no-op reporter instance early
- **Files**: `worker/app/main.py`
- **Tests**: Verify early failure doesn't crash

#### C-004: poll() Result Handling
- Ensure `poller.poll()` returns proper type (dict or None)
- Add explicit type checks
- **Files**: `worker/app/services/poller.py`, `worker/app/main.py`
- **Tests**: Verify poll returns/None handled

#### C-007: Blocking os.walk() in Async
- Wrap `os.walk()` calls in `asyncio.to_thread()` or `run_in_executor`
- Or use async directory walk (`aiofiles` / `anyio`)
- **Files**: `worker/app/executor/handlers/dir_scan.py`, `worker/app/executor/handlers/count_files.py`
- **Tests**: Verify handlers don't block event loop

### Sprint 3: Hardening & Infrastructure (Weeks 5-6)

**Theme**: Rate limiting, HTTPS, plugin security, WebSocket frontend.

**Issues**: S-004, S-007, S-010, S-011, S-013, C-009, F-003

#### S-004: Plugin Upload RCE
- Add sandboxed execution for plugins
- Restrict plugin permissions (read-only filesystem, no subprocess, no network by default)
- Validate plugin manifest against allowlist
- Run plugins in subprocess with restricted token (Windows)
- Add plugin permission review UI
- **Files**: `backend/app/plugins/loader/service.py`, `backend/app/plugins/registry/service.py`, `backend/app/api/v1/plugins.py`, `config/plugin_policy.yaml`
- **Tests**: Plugin can't access files outside plugins dir, plugin can't spawn processes

#### S-007: Rate Limiting
- Add `slowapi` or custom rate limiter middleware
- Per-IP rate limits: 100 req/min for general, 10 req/min for auth
- Per-worker rate limits: 60 req/min for heartbeat, 10 req/min for register
- Configurable via settings
- **Files**: `backend/app/main.py`, `backend/app/config.py`, `backend/app/middleware/rate_limit.py`
- **Tests**: Rate limit exceeded returns 429, normal usage works

#### S-010: HTTPS Support
- Add TLS configuration to settings
- Support cert/key file paths
- Document self-signed cert generation for LAN
- Optional: auto-generate self-signed cert on first run
- **Files**: `backend/app/config.py`, `backend/app/main.py`
- **Tests**: HTTPS works with valid cert, HTTP redirects to HTTPS (optional)

#### S-011: JWT Token Storage
- Implement httpOnly cookie-based auth for web frontend
- Keep Bearer token for programmatic/worker access
- Add CSRF token for cookie-based auth
- **Files**: `backend/app/services/auth.py`, `backend/app/api/v1/auth.py`, `frontend/src/stores/auth-store.ts`
- **Tests**: Cookie auth works, CSRF protection works

#### S-013: Info Disclosure
- Sanitize error messages in production mode
- Return generic error messages to clients
- Log full details server-side
- **Files**: ALL route files, `backend/app/config.py`
- **Tests**: 500 errors return generic message, full error in logs

#### C-009: Empty Except Blocks
- Audit all `except: pass` blocks
- Add proper error handling (log, re-raise, or handle)
- **Files**: Global audit of all Python files
- **Tests**: Verify errors are logged

#### F-003: Frontend WebSocket Connection
- Connect frontend to `/ws` endpoint with JWT auth
- Replace React Query polling with WebSocket events where appropriate
- Add reconnection logic
- **Files**: `frontend/src/stores/`, new `frontend/src/lib/websocket.ts`
- **Tests**: WebSocket connects, receives events, reconnects on disconnect

### Sprint 4: Testing & Polish (Weeks 7-8)

**Theme**: Comprehensive tests, frontend placeholders, build improvements.

**Issues**: T-001, T-002, T-003, F-001, F-002, C-010, B-001, B-002

#### T-001: Subsystem Tests
- Add pytest tests for: Workflow Engine, Repository Intelligence, AI Runtime, Multi-Agent Engine, Engineering Engine, Plugin System, Audit System, WebSocket
- Minimum 5 tests per subsystem
- Cover: create, read, update, delete, error paths
- **Files**: New `backend/tests/test_workflow.py`, etc.
- **Tests**: These ARE the tests

#### T-002: Auth Integration Tests
- Test full auth flow: login, token validation, expiry, refresh
- Test role-based access
- Test unauthenticated access rejection
- **Files**: `backend/tests/test_auth_integration.py`
- **Tests**: These ARE the tests

#### T-003: Frontend Tests
- Add Vitest tests for components
- Test: Sidebar navigation, Login page, Dashboard page, Workers page
- Test: Auth store actions, API client
- **Files**: New `frontend/src/**/*.test.tsx`
- **Tests**: These ARE the tests

#### F-001: Dashboard Placeholder Pages
- Implement remaining 8 pages: Jobs, Analytics, Chat, Files, Logs, Projects, Settings, Chat
- Each page should at minimum display data from API (even if read-only)
- **Files**: `frontend/src/app/(dashboard)/jobs/page.tsx`, etc.
- **Tests**: Pages render without errors

#### F-002: Studio IDE
- Implement workspace/project listing from API
- Set up basic panel layout (sidebar + main area)
- Connect to AI chat API
- This is a MINIMAL implementation — not a full IDE
- **Files**: `studio/src/App.tsx`, new component files
- **Tests**: App renders, API calls work

#### C-010: Deduplicate IP Logic
- Consolidate IP resolution into `shared/py/schemas.py` or utility
- Remove duplicate from worker `config.py`
- **Files**: `worker/app/config.py`, `backend/app/schemas/__init__.py`
- **Tests**: IP resolution still works

#### B-001: Binary Size Optimization
- Audit PyInstaller hidden imports
- Remove unnecessary dependencies
- Consider UPX compression
- **Files**: `build/pyinstaller_builder.py`, `build/config.py`
- **Tests**: Verify all functionality preserved

#### B-002: CI/CD Pipeline
- Add GitHub Actions workflow
- Stages: lint, typecheck, test (backend + worker), test (frontend), build (dry-run on PR)
- **Files**: New `.github/workflows/ci.yml`
- **Tests**: Pipeline passes

---

## Dependency Chains

```
Sprint 1                    Sprint 2                  Sprint 3                  Sprint 4
─────────                   ─────────                 ─────────                 ─────────
S-001 (JWT Secret)          S-006 (Path Traversal)    S-004 (Plugin RCE)        T-001 (Subsystem Tests)
  └── prerequisite for        └── depends on C-002    └── depends on C-009      └── depends on Sprint 1-3 fixes
      S-003 and S-008                                                             
                              S-008 (WS Auth)          S-007 (Rate Limiting)     T-002 (Auth Integration Tests)
S-002 (Admin Creds)           └── depends on S-001    └── depends on S-001      └── depends on S-003
  └── prerequisite for        └── prerequisite for                               
      S-003                       F-003                S-010 (HTTPS)             T-003 (Frontend Tests)
                                                       └── depends on S-001     └── depends on F-001
S-003 (Auth Enforce)         S-009 (Worker Auth)                               
  ⇧ ALL SPRINT 1 depends     └── depends on S-001      S-011 (Cookie Auth)       F-001 (Dashboard Pages)
  on this                                            └── depends on S-003      └── depends on nothing
                              C-001 (Dead Code)                                 
S-005 (CORS)                 C-002 (execute_w_prog)    S-013 (Info Disclosure)   F-002 (Studio Pages)
  └── independent            C-003 (report_result)    └── depends on nothing    └── depends on nothing
                              C-004 (poll handling)                             
C-005 (Double Commit)        C-007 (Blocking IO)      C-009 (Empty Except)      C-010 (Dedup IP)
  └── independent                                      └── global audit         └── depends on nothing
                              S-012 (SQL Injection)                             
C-006 (duration_ms)          └── depends on nothing    F-003 (Frontend WS)       B-001 (Binary Size)
  └── independent                                      └── depends on S-008     └── depends on nothing
                                                                                
C-008 (Scheduler Stop)                                                     B-002 (CI/CD)
  └── independent                                                     └── depends on all tests
```

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Hardcoded secrets | 2 (JWT, admin password) | 0 | Grep for hardcoded secrets |
| API endpoints with auth | 0 of ~140 | 100% | Automated endpoint scan |
| CRITICAL security issues | 4 | 0 | Security audit |
| HIGH security issues | 5 | 0 | Security audit |
| Worker null-pointer risks | 3 | 0 | Type checker |
| Blocking IO in async | 2 | 0 | Code review |
| Test coverage (backend) | ~10% | >60% | pytest --cov |
| Test coverage (frontend) | 0% | >30% | vitest --coverage |
| Dashboard placeholder pages | 8 of 10 | 0 of 10 | Visual inspection |
| Build success rate | Manual | CI/CD gated | CI pipeline |
| Console warnings | Unknown | 0 | Lint + typecheck |
| Double commits | 1 | 0 | Code review |
| Binary size (master) | ~80 MB | <60 MB | File size measurement |

---

## Project Score Target

| Dimension | Current | Target | Delta | Key Contributors |
|-----------|---------|--------|-------|------------------|
| Architecture | 8.5 | 9.0 | +0.5 | S-003 (auth enforcement) |
| Maintainability | 7.5 | 9.0 | +1.5 | C-001 (dead code removal), C-010 (dedup), C-009 (handle excepts) |
| Scalability | 6.0 | 7.0 | +1.0 | S-007 (rate limiting), C-008 (scheduler) |
| Security | 5.5 | 9.5 | +4.0 | S-001 through S-013 (all security fixes) |
| Performance | 7.0 | 8.0 | +1.0 | C-007 (async IO), B-001 (binary size) |
| Testing | 6.5 | 8.5 | +2.0 | T-001, T-002, T-003 (comprehensive tests) |
| Documentation | 7.0 | 8.0 | +1.0 | All new planning docs + inline docs |
| Build System | 7.5 | 8.5 | +1.0 | B-002 (CI/CD) |
| Release System | 6.0 | 7.0 | +1.0 | B-001 (binary optimization) |
| Code Quality | 7.5 | 9.0 | +1.5 | C-001 through C-010 (all code quality fixes) |
| Developer Experience | 6.5 | 8.0 | +1.5 | B-002 (CI/CD), docs |
| User Experience | 7.0 | 8.5 | +1.5 | F-001 (dashboard), F-003 (WebSocket) |
| AI Integration | 7.5 | 7.5 | 0 | No changes planned |
| Plugins | 7.0 | 8.5 | +1.5 | S-004 (plugin sandbox) |
| Workers | 7.5 | 9.0 | +1.5 | C-002, C-003, C-004, C-007, S-006, S-009 |
| Repository Intelligence | 7.5 | 7.5 | 0 | No changes planned |
| Workflow Engine | 7.5 | 7.5 | 0 | No changes planned |
| **Weighted Overall** | **7.525** | **9.2** | **+1.7** | |

---

## Rollback Strategy

Every change must be:
1. **Reversible** — Each PR must include a rollback plan
2. **Non-breaking** — Config changes must have backward-compatible defaults
3. **Feature-flagged** where appropriate (e.g., auth enforcement can be toggled)

### Per-Issue Rollback

| Issue | Rollback Strategy |
|-------|-------------------|
| S-001 | Revert config.py, delete secret.key, restart |
| S-002 | Revert auth.py, delete admin seed logic, restart |
| S-003 | Remove `Depends(get_current_user)` from routes, keep dependency available |
| S-005 | Revert main.py CORS config |
| S-006 | Revert handler validation code |
| S-007 | Remove rate limiter middleware |
| S-008 | Revert WebSocket auth check |
| S-009 | Remove worker_secret validation in worker routes |
| S-010 | Remove TLS config |
| S-012 | Revert search validation |
| C-005 | Revert scheduler.py |
| C-006 | Revert complete_job changes |
| C-007 | Revert to synchronous os.walk |
| F-003 | Revert WebSocket code, keep polling |
