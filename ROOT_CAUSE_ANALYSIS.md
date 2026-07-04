# Root Cause Analysis

## S-001: JWT Secret Hardcoded

**Root Cause**: Prototype shortcut

**Evidence**: `backend/app/config.py:22` — `secret_key = "aicluster-secret-key-change-in-production"`

The `"CHANGE-ME"` comment pattern (also seen as "change-in-production") is a well-known developer placeholder. The developer intended to make it configurable but never implemented the mechanism.

**Why it exists**: The auth system was built for a demo/prototype. The developer knew the secret should be changed but prioritized getting the system working first. This pattern is common in early-stage projects where "we'll fix it later" becomes permanent.

**Fix category**: Missing implementation (of secret management)

---

## S-002: Default Admin Credentials

**Root Cause**: Prototype shortcut

**Evidence**: `backend/app/services/auth.py:40` — `pwd_context.hash("admin123")`

Same pattern as S-001. The seed function was written with a hardcoded password for convenience during development. The comment in `config/production.yaml` (`auth.secret_key: CHANGE_ME_TO_A_SECURE_RANDOM_KEY`) shows awareness that this is a problem.

**Why it exists**: Developer convenience during testing. Every time the database is reset, the admin user needs to exist. Hardcoding the password avoids the need for a user management UI during development.

**Fix category**: Missing implementation (of password generation)

---

## S-003: No Authentication Enforcement

**Root Cause**: Missing implementation (architecture gap)

**Evidence**: `backend/app/services/auth.py:48-74` defines `get_current_user()` FastAPI dependency with full JWT validation. `backend/app/api/v1/auth.py` defines login endpoint. **No route uses `Depends(get_current_user)`**.

The auth infrastructure (JWT creation, validation, password hashing, user lookup) is 100% complete. The only missing piece is adding the `Depends()` call to each route.

**Why it exists**: The developer built the auth service first, then implemented all the routes. Adding `Depends(get_current_user)` to every route was planned but never executed — possibly because it would break all existing clients and testing would become harder.

**Fix category**: Missing implementation (of route protection)

---

## S-004: Plugin Upload RCE

**Root Cause**: Missing implementation (security gap)

**Evidence**: `backend/app/plugins/loader/service.py:27` — `importlib.import_module(manifest.entry_point)` with no sandboxing, no permission checks, no timeout.

The plugin loader trusts the plugin manifest completely. Any installed plugin can:
- Import any Python module
- Access any file the master process can access
- Execute arbitrary system commands
- Make network requests
- Fork bomb or resource-exhaust the server

**Why it exists**: The plugin system was designed for extensibility without considering security. The focus was on making plugins easy to write (`class Plugin` + async hook methods) rather than making them safe to run.

**Fix category**: Missing implementation (of sandboxing/permissions)

---

## S-005: CORS Misconfiguration

**Root Cause**: Prototype shortcut

**Evidence**: `backend/app/main.py` — `CORSMiddleware(allow_origins=["*"])`

During development, allowing all origins is convenient (no CORS errors in browser). The developer never updated this for production.

**Why it exists**: Same pattern as S-001/S-002. Developer convenience during development never hardened for production.

**Fix category**: Prototype shortcut

---

## S-006: Path Traversal in Worker Handlers

**Root Cause**: Missing implementation (input validation)

**Evidence**: `worker/app/executor/handlers/dir_scan.py:17` — `directory = payload.get("directory", ".")` passed directly to `os.walk()`.

The worker handlers were written as simple utilities with no consideration of adversarial input. The job payload is assumed to be trustworthy because only the master assigns jobs — but nothing prevents a user from creating a job with a malicious payload via the API.

**Why it exists**: The handlers were written as internal tools. The threat model assumed jobs only come from trusted sources (the master scheduler). The API vulnerability (S-003) compounds this — since anyone can create jobs, anyone can trigger path traversal.

**Fix category**: Missing implementation (input validation)

---

## S-007: No Rate Limiting

**Root Cause**: Missing implementation

**Evidence**: No rate limiting middleware exists anywhere in the codebase.

The project has a custom audit middleware but no rate limiting. The `default.yaml` config has no rate limit settings.

**Why it exists**: Rate limiting was likely on the roadmap but never prioritized. The API was designed for a local network environment where abuse was not considered a primary threat.

**Fix category**: Missing implementation

---

## S-008: WebSocket Without Authentication

**Root Cause**: Missing implementation

**Evidence**: `backend/app/main.py:77-101` — `websocket_endpoint()` accepts all connections, only validates message format (ping/pong).

The WebSocket manager is designed for broadcasting, not for authenticated connections. The JWT auth pattern existed for REST endpoints but was never extended to WebSocket.

**Why it exists**: The WebSocket endpoint was added for real-time dashboard updates. Authentication was skipped because the REST API didn't enforce it either (S-003), so there was no established pattern to follow.

**Fix category**: Missing implementation

---

## S-009: Worker Registration Without Auth

**Root Cause**: Missing implementation

**Evidence**: `backend/app/api/v1/workers.py:15` — `register_worker()` accepts any request. No authentication check.

Worker endpoints were designed as open endpoints because the original design assumed the master and workers were on a trusted LAN. With no auth enforcement on the API (S-003), there was no pattern for authenticating workers differently from users.

**Why it exists**: Architectural assumption that LAN = trusted. Combined with S-003 (no auth anywhere), worker auth was never built.

**Fix category**: Missing implementation

---

## C-001: Dead Code (services/executor.py)

**Root Cause**: Architecture drift

**Evidence**: `worker/app/services/executor.py` (88 lines) defines `JobExecutor` class. `worker/app/main.py:28-35` imports from `executor.registry` and `executor.handlers`, NOT from `services.executor`.

Two execution implementations exist: the early one in `services/executor.py` (legacy) and the current one in `executor/` (using registry + handlers). The legacy one was never removed.

**Why it exists**: The execution architecture was refactored from a monolithic executor to a registry-based handler system. The old file was left behind.

**Fix category**: Technical debt

---

## C-002: execute_with_progress Not on BaseJobHandler

**Root Cause**: Missing implementation

**Evidence**: `worker/app/main.py:139` — `if hasattr(handler, "execute_with_progress")` — always False. `worker/app/executor/base.py:7` — `BaseJobHandler` only defines `execute()`.

The developer planned a progress-reporting execution pattern but only implemented it in the caller, not in the contract or any handler.

**Why it exists**: The progress reporting requirement was identified but never fully implemented. The dead branch was left in main.py.

**Fix category**: Missing implementation → Simplification (remove the branch)

---

## C-003: reporter Called on None

**Root Cause**: Type design flaw

**Evidence**: `worker/app/main.py:47` — `reporter: Reporter | None = None`. Called at lines 129, 142, 150, 151, 160, 168 without null checks.

The module-level variable is typed as `Optional`, initialized to `None`, assigned in `_run_worker()`, but used in `_execute_job()` which can theoretically be called before assignment.

**Why it exists**: The developer used Python's `Optional` pattern for late initialization but didn't guard all call sites. This is a common Python pattern that introduces latent bugs.

**Fix category**: Technical debt (type safety gap)

---

## C-005: Double Commit

**Root Cause**: Implementation bug

**Evidence**: `backend/app/services/scheduler.py:172` — `await self.db.commit()` (first commit after worker update). Line 187 — `await self.db.commit()` (second commit after SystemLog insert).

The first commit was likely added during debugging and never removed. SQLAlchemy's session is flushed on commit, so the first commit writes incomplete data (no log entry) to the database.

**Why it exists**: Developer error during implementation, not caught in code review.

**Fix category**: Implementation bug

---

## C-006: duration_ms Not Stored

**Root Cause**: Implementation bug

**Evidence**: `backend/app/services/scheduler.py:227` — `if duration_ms is not None: pass`.

The `pass` indicates the developer got interrupted or forgot to implement the storage.

**Why it exists**: Simple oversight. The parameter was added to the function signature but the implementation was never completed.

**Fix category**: Implementation bug

---

## C-007: Blocking IO in Async Handlers

**Root Cause**: Design limitation

**Evidence**: `worker/app/executor/handlers/dir_scan.py` — `os.walk()` called directly in async `execute()` method.

The developer used synchronous file operations in async functions either because they didn't know about `asyncio.to_thread()` or because they prioritized simplicity.

**Why it exists**: Common mistake in Python async development. Synchronous blocking calls in async functions are a well-known anti-pattern.

**Fix category**: Technical debt (asynchronous design violation)

---

## C-008: Scheduler Not Stoppable

**Root Cause**: Design limitation

**Evidence**: `backend/app/services/scheduler.py:30-35` — `_running` flag with `asyncio.sleep(2)`. The loop only checks `_running` between sleep cycles.

The simple flag pattern doesn't allow interrupting the sleep. The shutdown can take up to 2 seconds.

**Why it exists**: Initial implementation favored simplicity. The 2-second delay was considered acceptable.

**Fix category**: Technical debt (inadequate shutdown mechanism)

---

## C-009: Empty Except Blocks

**Root Cause**: Technical debt (multiple origins)

**Evidence**: Multiple files have `except: pass` or `except Exception: pass` patterns.

Some were added during debugging to suppress errors temporarily. Others were copy-pasted from boilerplate. Some are in error handlers where the developer didn't know how to handle the error.

**Why it exists**: Accumulated shortcut over the development lifecycle. Each individual instance might have been "temporary" but collectively they've become permanent.

**Fix category**: Technical debt

---

## Summary

| Category | Count | Issues |
|----------|-------|--------|
| Prototype shortcut | 4 | S-001, S-002, S-005, (S-004 partial) |
| Missing implementation | 10 | S-003, S-004, S-006, S-007, S-008, S-009, S-010, S-011, S-012, S-013, C-002 |
| Implementation bug | 2 | C-005, C-006 |
| Design limitation | 2 | C-007, C-008 |
| Architecture drift | 1 | C-001 |
| Type design flaw | 1 | C-003 |
| Technical debt | 1 | C-004, C-009, C-010 |

**Primary finding**: The majority of issues (62%) are **missing implementations** — features that were designed but never completed. Only 4 of 31 issues are prototype shortcuts. This suggests the project is in a "functional but incomplete" state rather than "broken".

The security issues (S-001 through S-013) are particularly concerning because they're all missing implementations: the auth infrastructure exists but wasn't connected to routes, the plugin loader exists but wasn't secured, the worker handlers exist but weren't validated. Each fix is adding a missing piece rather than rebuilding something broken.
