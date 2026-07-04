# AICluster v1.3.1 Change Impact Matrix

## Overview

This document defines the complete impact analysis for every planned change in v1.3.1. Each issue is analyzed across 28 dimensions to ensure zero surprises during implementation.

---

## S-001: JWT Secret Not Hardcoded

| Field | Value |
|-------|-------|
| **Priority** | P0 (CRITICAL) |
| **Subsystem** | Backend Core |
| **Root Cause** | Prototype shortcut: `config.py` has hardcoded "aicluster-secret-key-change-in-production" |
| **Current Behaviour** | Secret is hardcoded in source, identical across all deployments |
| **Desired Behaviour** | Secret generated on first run, stored in `data/secret.key`, overridable via `AICLUSTER_SECRET_KEY` env var |
| **Reason** | Hardcoded secret means anyone who reads the source can forge JWTs |
| **Business Impact** | CRITICAL: data breach, unauthorized access to all cluster operations |
| **Technical Impact** | Secret management becomes env-var + file based |
| **Security Impact** | CRITICAL: removes #1 attack vector |
| **Performance Impact** | None |
| **Files Modified** | `backend/app/config.py`, `backend/.env` (documentation) |
| **Classes Modified** | `Settings` — add `_load_secret()` method |
| **Functions Modified** | None new; `Settings.__init__` implicit via pydantic |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | `AICLUSTER_SECRET_KEY` env var; `data/secret.key` auto-created |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | `.env.example`, deployment docs |
| **Estimated LOC** | +15, -1 |
| **Regression Risk** | LOW — purely config change |
| **Rollback Strategy** | Revert `config.py`, delete `secret.key`, restart |
| **Testing Required** | Unit: key generation, key persistence, env override |
| **Owner** | Security Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | S-003, S-008, S-009 |
| **Acceptance Criteria** | No hardcoded secret in source; secret persists across restarts; env var overrides file |
| **Release Criteria** | `grep "aicluster-secret-key" backend/app/` returns no matches |

---

## S-002: Default Admin Credentials

| Field | Value |
|-------|-------|
| **Priority** | P0 (CRITICAL) |
| **Subsystem** | Auth Service |
| **Root Cause** | Prototype shortcut: `seed_default_admin()` hashes "admin123" |
| **Current Behaviour** | Admin password is always "admin123" |
| **Desired Behaviour** | Random 16-char password generated on first run, printed to stderr |
| **Reason** | Default password enables trivial unauthorized access |
| **Business Impact** | CRITICAL: anyone who deploys gets same default password |
| **Technical Impact** | Password generation + storage in DB remains bcrypt |
| **Security Impact** | CRITICAL: removes well-known default credential |
| **Performance Impact** | None |
| **Files Modified** | `backend/app/services/auth.py`, `backend/app/main.py` |
| **Classes Modified** | `AuthService` — modify `seed_default_admin()` |
| **Functions Modified** | `seed_default_admin()` |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | `AICLUSTER_ADMIN_PASSWORD` env var for automated deploy |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | Admin setup docs |
| **Estimated LOC** | +10, -1 |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Revert `auth.py`, re-run seed with old password |
| **Testing Required** | Unit: password generation, login with generated password |
| **Owner** | Security Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | S-003 (auth enforcement needs admin to exist) |
| **Acceptance Criteria** | Random password printed on first run; login works; env var override works |
| **Release Criteria** | `grep "admin123" backend/app/` returns no matches (test file exceptions OK) |

---

## S-003: Authentication Enforcement

| Field | Value |
|-------|-------|
| **Priority** | P0 (CRITICAL) |
| **Subsystem** | API Layer (all 15 route files) |
| **Root Cause** | Missing implementation: `get_current_user` dependency exists but never applied to routes |
| **Current Behaviour** | All API endpoints are accessible without any authentication |
| **Desired Behaviour** | All endpoints require valid JWT (except public whitelist: health, login, docs) |
| **Reason** | Without auth enforcement, the entire system is open to anyone on the network |
| **Business Impact** | CRITICAL: any LAN user can control the cluster |
| **Technical Impact** | Every route handler gains `Depends(get_current_user)` or `Depends(verify_worker_token)` |
| **Security Impact** | CRITICAL: closes the #1 security gap |
| **Performance Impact** | Negligible (JWT decode is sub-millisecond) |
| **Files Modified** | All 15 route files in `backend/app/api/v1/*.py` + new `backend/app/api/dependencies.py` |
| **Classes Modified** | None new |
| **Functions Modified** | Every route handler gains auth dependency parameter |
| **API Changes** | Public endpoints: health, auth/login, docs, openapi.json. All others: require `Authorization: Bearer <token>` |
| **Database Changes** | None |
| **Worker Changes** | Worker routes require `worker_secret` instead of JWT |
| **Studio Changes** | Studio API calls need JWT |
| **Plugin Changes** | Plugin API calls need JWT |
| **Configuration Changes** | `AICLUSTER_PUBLIC_ROUTES` optional override |
| **Build Changes** | Verification stages must test auth |
| **Installer Changes** | None |
| **Documentation Updates** | API reference: auth headers required |
| **Estimated LOC** | ~100 (15 files × ~6 lines each for dependency injection) |
| **Regression Risk** | MEDIUM — must ensure public routes still work without auth |
| **Rollback Strategy** | Remove `Depends(get_current_user)` from routes; keep dependency available |
| **Testing Required** | Every endpoint tested: 401 without auth, 200 with auth, role enforcement |
| **Owner** | Security Team |
| **Dependencies** | S-001 (JWT secret), S-002 (admin creds) |
| **Blocked By** | S-001, S-002 |
| **Blocks** | Nothing directly; prerequisite for S-011 (cookie auth) |
| **Acceptance Criteria** | All endpoints authenticated; public whitelist works; role enforcement works; worker token works |
| **Release Criteria** | Automated endpoint scan: 0 unprotected endpoints |

---

## S-004: Plugin Upload RCE

| Field | Value |
|-------|-------|
| **Priority** | P0 (CRITICAL) |
| **Subsystem** | Plugin System |
| **Root Cause** | Missing implementation: `PluginLoader.load_plugin()` does `importlib.import_module()` without sandbox |
| **Current Behaviour** | Plugin code executes with full process privileges |
| **Desired Behaviour** | Plugin runs in sandboxed subprocess with restricted permissions |
| **Reason** | Installed plugins can execute arbitrary code on the master server |
| **Business Impact** | CRITICAL: any installed plugin can compromise the entire cluster |
| **Technical Impact** | Plugin execution moves from in-process to subprocess |
| **Security Impact** | CRITICAL: prevents arbitrary code execution via plugins |
| **Performance Impact** | Subprocess overhead for plugin execution |
| **Files Modified** | `backend/app/plugins/loader/service.py`, `backend/app/plugins/manifest/service.py`, `backend/app/plugins/registry/service.py`, new `config/plugin_policy.yaml` |
| **Classes Modified** | `PluginLoader`, `PluginManifest`, `PluginRegistry` |
| **Functions Modified** | `load_plugin()`, `discover_plugins()`, new `_validate_manifest()` |
| **API Changes** | Plugin install validates permissions against policy |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | Plugins must declare permissions in manifest |
| **Configuration Changes** | New `config/plugin_policy.yaml` for global plugin restrictions |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | Plugin development guide: permissions system |
| **Estimated LOC** | ~200 |
| **Regression Risk** | HIGH — sandboxing is complex; existing plugins may break |
| **Rollback Strategy** | Revert plugin loader to non-sandboxed version |
| **Testing Required** | Plugin cannot access files outside plugin dir, cannot spawn processes, timeout enforcement |
| **Owner** | Security Team |
| **Dependencies** | C-009 (empty except blocks — must have proper error handling before sandboxing) |
| **Blocked By** | C-009 |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Plugin denied filesystem access outside plugin dir; plugin timeout enforced; permission declaration required |
| **Release Criteria** | Plugin security test suite passes |

---

## S-005: CORS Restriction

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Backend Core |
| **Root Cause** | Prototype shortcut: `allow_origins=["*"]` |
| **Current Behaviour** | All origins allowed |
| **Desired Behaviour** | Origins restricted to configured list (default: localhost:3000) |
| **Reason** | Wide-open CORS enables cross-origin attacks from any website on the LAN |
| **Business Impact** | MEDIUM: attack vector for XSS/CSRF |
| **Technical Impact** | CORS middleware reads from config |
| **Security Impact** | HIGH: prevents unauthorized cross-origin requests |
| **Performance Impact** | None |
| **Files Modified** | `backend/app/main.py`, `backend/app/config.py`, `config/default.yaml`, `config/production.yaml` |
| **Classes Modified** | `Settings` — add `cors_origins: list[str]` |
| **Functions Modified** | `main.py` CORS middleware init |
| **API Changes** | CORS headers restricted |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | `cors_origins` in YAML config |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | Config reference |
| **Estimated LOC** | +5, -1 |
| **Regression Risk** | LOW — only affects cross-origin requests |
| **Rollback Strategy** | Revert to `["*"]` |
| **Testing Required** | CORS headers for allowed/disallowed origins |
| **Owner** | Security Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Allowed origin gets CORS headers; disallowed origin blocked |
| **Release Criteria** | CORS test passes |

---

## S-006: Path Traversal Prevention

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Worker Handlers |
| **Root Cause** | Missing implementation: worker handlers accept arbitrary file paths without validation |
| **Current Behaviour** | `dir_scan`, `hash_file`, `count_files` accept any path from job payload |
| **Desired Behaviour** | Paths validated against allowed directories; `..` rejected |
| **Reason** | Attacker can submit job that reads/writes arbitrary files on worker machine |
| **Business Impact** | HIGH: worker machines can be compromised |
| **Technical Impact** | Path validation added to file-based handlers |
| **Security Impact** | HIGH: prevents filesystem traversal attack |
| **Performance Impact** | Negligible |
| **Files Modified** | `worker/app/executor/handlers/dir_scan.py`, `worker/app/executor/handlers/hash_file.py`, `worker/app/executor/handlers/count_files.py`, new `worker/app/executor/handlers/path_utils.py` |
| **Classes Modified** | `DirectoryScanHandler`, `HashFileHandler`, `CountFilesHandler` |
| **Functions Modified** | `execute()` in each handler |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | New shared `validate_path()` utility |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | `allowed_directories` in worker config.json |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | Worker config reference |
| **Estimated LOC** | ~60 |
| **Regression Risk** | LOW — validated paths still work |
| **Rollback Strategy** | Remove path validation |
| **Testing Required** | Path traversal attempt rejected; valid paths accepted |
| **Owner** | Worker Team |
| **Dependencies** | C-002 (handler contract must be stable first) |
| **Blocked By** | C-002 |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Paths with `..` rejected; absolute paths outside allowed dirs rejected; valid paths work |
| **Release Criteria** | Path traversal test suite passes |

---

## S-007: Rate Limiting

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Backend Middleware |
| **Root Cause** | Missing implementation: no rate limiter exists |
| **Current Behaviour** | Any client can send unlimited requests |
| **Desired Behaviour** | Rate limits applied per-IP and per-endpoint group |
| **Reason** | Without rate limiting, the API is vulnerable to DoS and brute force |
| **Business Impact** | MEDIUM: system can be overwhelmed |
| **Technical Impact** | New middleware + config |
| **Security Impact** | HIGH: prevents brute force and DoS |
| **Performance Impact** | Negligible (in-memory counters) |
| **Files Modified** | `backend/app/middleware/rate_limit.py` (NEW), `backend/app/main.py`, `backend/app/config.py`, `backend/requirements.txt` |
| **Classes Modified** | None new |
| **Functions Modified** | `main.py` — add middleware |
| **API Changes** | 429 responses for exceeded limits |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | Rate limit config in settings |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | API reference: rate limit headers |
| **Estimated LOC** | ~80 |
| **Regression Risk** | LOW — limits are generous |
| **Rollback Strategy** | Remove rate limiter middleware |
| **Testing Required** | Exceed limit → 429; normal usage succeeds |
| **Owner** | Backend Team |
| **Dependencies** | S-001 (needs JWT for IP extraction on authenticated routes) |
| **Blocked By** | S-001 |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Auth login limited to 10/min; general API limited to 100/min; 429 returned on exceed |
| **Release Criteria** | Rate limit tests pass |

---

## S-008: WebSocket Authentication

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | WebSocket |
| **Root Cause** | Missing implementation: `websocket_endpoint()` accepts all connections |
| **Current Behaviour** | Any client can connect to `/ws` |
| **Desired Behaviour** | JWT token required as query parameter |
| **Reason** | Unauthenticated WebSocket allows eavesdropping on cluster events |
| **Business Impact** | HIGH: real-time cluster data exposed |
| **Technical Impact** | Token validation on connect |
| **Security Impact** | HIGH: prevents unauthorized real-time data access |
| **Performance Impact** | Negligible |
| **Files Modified** | `backend/app/main.py`, `backend/app/websocket/manager.py` |
| **Classes Modified** | `WebSocketManager` — add `authenticate()` |
| **Functions Modified** | `websocket_endpoint()`, `connect()` |
| **API Changes** | WS endpoint now requires `?token=` query param |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | Studio WS client must send token |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | Verification stage tests WS auth |
| **Installer Changes** | None |
| **Documentation Updates** | WebSocket API reference |
| **Estimated LOC** | +20 |
| **Regression Risk** | LOW — existing clients must update to include token |
| **Rollback Strategy** | Remove auth check from `websocket_endpoint()` |
| **Testing Required** | Valid token connects; invalid token rejected (4001) |
| **Owner** | Backend Team |
| **Dependencies** | S-001 (JWT secret) |
| **Blocked By** | S-001 |
| **Blocks** | F-003 (frontend WebSocket needs auth) |
| **Acceptance Criteria** | WS rejects invalid tokens; WS accepts valid tokens; WS accepts worker tokens |
| **Release Criteria** | WebSocket auth tests pass |

---

## S-009: Worker Authentication

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Worker + Master API |
| **Root Cause** | Missing implementation: worker endpoints have no auth |
| **Current Behaviour** | Anyone can register a worker or send heartbeats |
| **Desired Behaviour** | Workers authenticate using pre-shared worker_secret |
| **Reason** | Unauthenticated worker registration allows rogue workers to join the cluster |
| **Business Impact** | HIGH: fake workers can consume jobs or return false data |
| **Technical Impact** | `worker_secret` added to worker config; master validates it |
| **Security Impact** | HIGH: prevents rogue worker injection |
| **Performance Impact** | Negligible |
| **Files Modified** | `backend/app/api/v1/workers.py`, `backend/app/services/worker_manager.py`, `worker/app/config.py`, `worker/app/utils/http_client.py`, `worker/app/main.py` |
| **Classes Modified** | `WorkerHttpClient`, `WorkerSettings`, `Registrar` |
| **Functions Modified** | `register_worker()`, `worker_heartbeat()`, `report_progress()`, `report_result()`, `HttpClient.post()/get()` |
| **API Changes** | Worker endpoints require `Authorization: Bearer <worker_secret>` |
| **Database Changes** | None (secret validated against config, not DB) |
| **Worker Changes** | Worker sends auth header on all requests |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | `worker_secret` in worker `config.json` |
| **Build Changes** | None |
| **Installer Changes** | Worker secret generated during installation |
| **Documentation Updates** | Worker deployment guide |
| **Estimated LOC** | +40 |
| **Regression Risk** | LOW — secrets are generated, not hardcoded |
| **Rollback Strategy** | Remove worker_secret validation from master worker routes |
| **Testing Required** | Valid worker registers; invalid worker rejected (401) |
| **Owner** | Worker Team |
| **Dependencies** | S-001 (JWT secret pattern for worker_secret) |
| **Blocked By** | S-001 |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Worker sends auth header; master validates; bad secret rejected |
| **Release Criteria** | Worker auth tests pass |

---

## C-001: Remove Dead Code (services/executor.py)

| Field | Value |
|-------|-------|
| **Priority** | P2 (MEDIUM) |
| **Subsystem** | Worker |
| **Root Cause** | Architecture drift: duplicate executor implementation never used |
| **Current Behaviour** | `worker/app/services/executor.py` exists but is not imported by `main.py` |
| **Desired Behaviour** | File deleted |
| **Reason** | Dead code increases maintenance burden and confuses developers |
| **Business Impact** | None |
| **Technical Impact** | Removes 88 lines of unused code |
| **Security Impact** | None |
| **Performance Impact** | None |
| **Files Modified** | `worker/app/services/executor.py` (DELETE) |
| **Classes Modified** | None (deleted) |
| **Functions Modified** | None |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | None functional |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | -88 |
| **Regression Risk** | ZERO — code is not referenced anywhere |
| **Rollback Strategy** | Restore deleted file |
| **Testing Required** | Worker starts and runs jobs normally |
| **Owner** | Worker Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Worker works without this file |
| **Release Criteria** | Worker tests pass |

---

## C-002: execute_with_progress Handler Contract

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Worker Execution |
| **Root Cause** | Missing implementation: `BaseJobHandler` doesn't define `execute_with_progress` but `main.py` calls it |
| **Current Behaviour** | `main.py:139` checks `hasattr(handler, "execute_with_progress")` — always False |
| **Desired Behaviour** | Remove the dead branch; all handlers only implement `execute()` |
| **Reason** | Dead code path that can never execute; adds confusion and risk |
| **Business Impact** | None |
| **Technical Impact** | Removes ~10 lines from `main.py` |
| **Security Impact** | None |
| **Performance Impact** | None |
| **Files Modified** | `worker/app/main.py` (lines 139-148), `worker/app/executor/base.py` |
| **Classes Modified** | `BaseJobHandler` |
| **Functions Modified** | `_execute_job()` in main.py |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | Simplified execution path |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | -10 |
| **Regression Risk** | LOW — branch was never reached |
| **Rollback Strategy** | Restore the branch |
| **Testing Required** | All handlers execute and report results correctly |
| **Owner** | Worker Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | S-006 (path traversal depends on stable handler contract) |
| **Acceptance Criteria** | Workers execute all 5 handlers without error |
| **Release Criteria** | Worker execution tests pass |

---

## C-003: reporter Called on None

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Worker Core |
| **Root Cause** | Type design flaw: `reporter` is `Optional[Reporter]` initialized to `None`, used before guaranteed assignment |
| **Current Behaviour** | If `_execute_job()` is called before `_run_worker()` sets `reporter`, the worker crashes with AttributeError: `'NoneType' object has no attribute 'report_result'` |
| **Desired Behaviour** | No-op reporter instance created at module load time |
| **Reason** | This is a latent crash bug; any state machine edge case triggers it |
| **Business Impact** | MEDIUM: worker can crash during startup |
| **Technical Impact** | `_NoOpReporter` class added; `reporter` type changed from `Optional[Reporter]` to `Reporter` |
| **Security Impact** | None |
| **Performance Impact** | None |
| **Files Modified** | `worker/app/main.py` |
| **Classes Modified** | None new; `_NoOpReporter` inner class added |
| **Functions Modified** | Module-level `reporter` initialization |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | No-op reporter prevents crashes |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | +8 |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Revert to `reporter: Optional[Reporter] = None` |
| **Testing Required** | Early worker failure doesn't crash on reporter calls |
| **Owner** | Worker Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Worker startup crash doesn't cascade; reporter calls before registration succeed silently |
| **Release Criteria** | Worker crash-resilience tests pass |

---

## C-004: poll() Type Handling

| Field | Value |
|-------|-------|
| **Priority** | P2 (MEDIUM) |
| **Subsystem** | Worker Polling |
| **Root Cause** | Missing type guard: `poller.poll()` returns `dict | None` but result used without narrowing |
| **Current Behaviour** | If `poll()` returns unexpected type, downstream code may fail |
| **Desired Behaviour** | Explicit `isinstance(job_data, dict)` check before use |
| **Reason** | Type safety: ensure robust handling of unexpected poll responses |
| **Business Impact** | LOW |
| **Technical Impact** | Type guard added |
| **Security Impact** | None |
| **Performance Impact** | None |
| **Files Modified** | `worker/app/main.py`, `worker/app/services/poller.py` |
| **Classes Modified** | `JobPoller` — ensure return type is well-defined |
| **Functions Modified** | `_worker_loop()`, `poll()` |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | Type-safe poll handling |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | +5 |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Remove type guard |
| **Testing Required** | Various poll responses handled correctly |
| **Owner** | Worker Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Non-dict poll response logged and skipped; dict poll response processed |
| **Release Criteria** | Worker poll tests pass |

---

## C-005: Double Commit in get_next_for_worker

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Scheduler |
| **Root Cause** | Implementation bug: `get_next_for_worker()` commits twice (lines 172 and 187) |
| **Current Behaviour** | First commit after worker update; second commit after SystemLog insert. First commit may flush incomplete state. |
| **Desired Behaviour** | Single commit after all changes |
| **Reason** | Double commit risks partial state persistence if second commit fails |
| **Business Impact** | MEDIUM: potential data inconsistency |
| **Technical Impact** | Restructured to single commit |
| **Security Impact** | None |
| **Performance Impact** | None |
| **Files Modified** | `backend/app/services/scheduler.py` |
| **Classes Modified** | `SchedulerService` |
| **Functions Modified** | `get_next_for_worker()` |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | -1, +3 |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Restore original double-commit code |
| **Testing Required** | Job assignment works; no integrity errors |
| **Owner** | Backend Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Job assigned with single commit; worker status updated; SystemLog created |
| **Release Criteria** | Scheduler tests pass |

---

## C-006: duration_ms Not Stored

| Field | Value |
|-------|-------|
| **Priority** | P2 (MEDIUM) |
| **Subsystem** | Scheduler |
| **Root Cause** | Implementation bug: `complete_job()` has `if duration_ms is not None: pass` — value discarded |
| **Current Behaviour** | Job execution duration is never persisted |
| **Desired Behaviour** | `duration_ms` stored in job record |
| **Reason** | Execution duration is valuable for performance monitoring and billing |
| **Business Impact** | LOW-MEDIUM: lost telemetry data |
| **Technical Impact** | `job.duration_ms = duration_ms` replaces `pass` |
| **Security Impact** | None |
| **Performance Impact** | None |
| **Files Modified** | `backend/app/services/scheduler.py`, `backend/app/models/job.py` |
| **Classes Modified** | `Job` ORM model |
| **Functions Modified** | `complete_job()` |
| **API Changes** | `JobResponse` may include `duration_ms` |
| **Database Changes** | `jobs.duration_ms` column added (Float, nullable) |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | API reference for JobResponse |
| **Estimated LOC** | +1, -1 |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Revert to `pass` |
| **Testing Required** | Duration is stored and retrievable |
| **Owner** | Backend Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | `job.duration_ms` contains execution time after completion |
| **Release Criteria** | Duration test passes |

---

## C-007: Blocking IO in Async Handlers

| Field | Value |
|-------|-------|
| **Priority** | P1 (HIGH) |
| **Subsystem** | Worker Handlers |
| **Root Cause** | Design flaw: `os.walk()` and file reads in async handlers block the event loop |
| **Current Behaviour** | `dir_scan`, `hash_file`, `count_files` execute blocking IO on the async event loop |
| **Desired Behaviour** | Blocking IO moved to thread pool via `asyncio.to_thread()` |
| **Reason** | Blocking the event loop prevents heartbeats and polling during long operations |
| **Business Impact** | MEDIUM: large directory scans cause worker to miss heartbeats |
| **Technical Impact** | Each handler splits into sync function + async wrapper |
| **Security Impact** | None |
| **Performance Impact** | POSITIVE: event loop remains responsive |
| **Files Modified** | `worker/app/executor/handlers/dir_scan.py`, `worker/app/executor/handlers/count_files.py`, `worker/app/executor/handlers/hash_file.py` |
| **Classes Modified** | `DirectoryScanHandler`, `CountFilesHandler`, `HashFileHandler` |
| **Functions Modified** | `execute()` in each handler |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | Non-blocking execution |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | ~30 (10 per handler) |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Revert to synchronous calls |
| **Testing Required** | Event loop remains responsive during long scans |
| **Owner** | Worker Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | Heartbeat continues during directory scan; handler returns correct results |
| **Release Criteria** | Worker non-blocking tests pass |

---

## C-008: Scheduler Not Stoppable

| Field | Value |
|-------|-------|
| **Priority** | P2 (MEDIUM) |
| **Subsystem** | Scheduler |
| **Root Cause** | Design flaw: `_running` boolean flag doesn't interrupt `asyncio.sleep()` |
| **Current Behaviour** | `stop()` sets `_running = False` but loop may sleep for up to 2s before checking |
| **Desired Behaviour** | `asyncio.Event` for cancellation; loop stops within 1s |
| **Reason** | Graceful shutdown should be prompt |
| **Business Impact** | LOW-MEDIUM: 2s shutdown delay |
| **Technical Impact** | `_running` → `_stop_event: asyncio.Event` |
| **Security Impact** | None |
| **Performance Impact** | None |
| **Files Modified** | `backend/app/services/scheduler.py` |
| **Classes Modified** | `SchedulerService` |
| **Functions Modified** | `start()`, `stop()`, `_scheduler_loop()` |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | +5, -3 |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Revert to `_running` flag |
| **Testing Required** | Scheduler stops within 1s of `stop()` |
| **Owner** | Backend Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | Nothing |
| **Acceptance Criteria** | `stop()` returns within 1s; no lingering tasks |
| **Release Criteria** | Scheduler shutdown test passes |

---

## C-009: Empty Except Blocks

| Field | Value |
|-------|-------|
| **Priority** | P3 (MEDIUM) |
| **Subsystem** | Global (all Python files) |
| **Root Cause** | Technical debt: developers used `except: pass` to silence errors during prototyping |
| **Current Behaviour** | Silent exception swallowing across codebase |
| **Desired Behaviour** | All exceptions are at minimum logged |
| **Reason** | Silent failures make debugging impossible |
| **Business Impact** | LOW-MEDIUM: delayed error detection |
| **Technical Impact** | Global audit and fix of ~20+ locations |
| **Security Impact** | LOW: prevents information leaks from unhandled errors |
| **Performance Impact** | None |
| **Files Modified** | Multiple files across `backend/app/` and `worker/app/` |
| **Classes Modified** | Various |
| **Functions Modified** | Various |
| **API Changes** | None |
| **Database Changes** | None |
| **Worker Changes** | None |
| **Studio Changes** | None |
| **Plugin Changes** | None |
| **Configuration Changes** | None |
| **Build Changes** | None |
| **Installer Changes** | None |
| **Documentation Updates** | None |
| **Estimated LOC** | ~50 |
| **Regression Risk** | LOW |
| **Rollback Strategy** | Revert per-file |
| **Testing Required** | Errors in handled blocks visible in logs |
| **Owner** | Backend Team |
| **Dependencies** | None |
| **Blocked By** | Nothing |
| **Blocks** | S-004 (plugin sandbox needs proper error handling) |
| **Acceptance Criteria** | No `except: pass` remains; all caught exceptions logged |
| **Release Criteria** | Linter check: `grep -r "except.*:.*pass" backend/ worker/` returns empty |

---

## Remaining Issues (Abbreviated)

For S-010 through S-013, F-001 through F-003, T-001 through T-003, B-001, B-002, C-010 — see the specialist impact matrices (API, Database, Security, Worker, Build, Test) for full detail. These follow the same pattern with appropriately lower risk and effort levels.

Key highlights:
- **S-010 (HTTPS)**: +20 LOC, low risk, adds TLS config options
- **S-011 (Cookie Auth)**: +80 LOC, medium risk (CSRF complexity), frontend + backend changes
- **S-012 (SQL Injection)**: +15 LOC, low risk, adds regex timeout + input validation
- **S-013 (Info Disclosure)**: +10 LOC, low risk, production error handler
- **F-001 (Dashboard Pages)**: ~500 LOC, low risk, 8 new page implementations
- **F-003 (WebSocket Frontend)**: ~100 LOC, medium risk, new WS client
- **T-001/T-002/T-003**: ~1500 LOC total, low risk, purely additive
- **B-001 (Binary Size)**: ~20 LOC, medium risk (UPX may cause false positives)
- **B-002 (CI/CD)**: ~100 LOC, low risk, new workflow file
