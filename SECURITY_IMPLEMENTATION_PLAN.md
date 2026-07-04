# AICluster v1.3.1 Security Implementation Plan

## Current Security Posture

| Severity | Count | Key Issues |
|----------|-------|------------|
| CRITICAL | 4 | JWT hardcoded, default creds, no auth, plugin RCE |
| HIGH | 5 | CORS, path traversal, no rate limit, WS auth, worker auth |
| MEDIUM | 6 | localStorage token, info disclosure, SQL injection, worker no auth, sensitive logging, input validation |
| LOW | 2 | Weak cipher, no CSRF |

---

## Issue S-001: JWT Secret Hardcoded

**Root Cause**: `config.py` has `secret_key = "aicluster-secret-key-change-in-production"` as default.

**Fix**:
1. Remove hardcoded default from `Settings` class
2. On first run, generate `os.urandom(32).hex()` and save to `data/secret.key`
3. Add `AICLUSTER_SECRET_KEY` env var override
4. Fall back to reading `data/secret.key` if env var not set
5. Log warning if using generated key (not explicitly configured)

**Files**: `backend/app/config.py`
**Risk**: LOW — key generation is deterministic from random source
**Tests**: Verify key persists across restarts, verify env var override, verify missing key creates new

---

## Issue S-002: Default Admin Credentials

**Root Cause**: `auth.py:seed_default_admin()` uses `pwd_context.hash("admin123")`.

**Fix**:
1. Generate random 16-char password on first run: `secrets.token_urlsafe(16)`
2. Print to stderr: `ADMIN PASSWORD: <generated>`
3. Hash and store in database
4. Add `AICLUSTER_ADMIN_PASSWORD` env var override for automated deployment
5. Add `--reset-admin-password` CLI flag

**Files**: `backend/app/services/auth.py`, `backend/app/main.py`
**Risk**: LOW — generated password is cryptographically random
**Tests**: Verify password printed on first run, verify login with printed password

---

## Issue S-003: Authentication Enforcement

**Root Cause**: `get_current_user` dependency exists but is NOT applied to any route.

**Fix**:
1. Create `auth_dependency.py` with public route whitelist:

```python
PUBLIC_ROUTES = {
    "/api/v1/health",
    "/api/v1/auth/login",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/",
}

PUBLIC_PREFIXES = {
    "/static/",
    "/openapi/",
}
```

2. Create `require_auth` FastAPI middleware that checks whitelist first
3. Add `Depends(get_current_user)` to every protected route
4. Create `require_role(role: str)` dependency for admin routes
5. Worker endpoints get `Depends(verify_worker_token)` instead

**Route Protection Map**:

| Route Group | Protection | Notes |
|-------------|------------|-------|
| `/health` | PUBLIC | |
| `/auth/login` | PUBLIC | |
| `/auth/*` (other) | AUTH | Reserved for future |
| `/workers/register` | WORKER_TOKEN | |
| `/workers/heartbeat` | WORKER_TOKEN | |
| `/workers/*` (other) | AUTH | Admin |
| `/jobs/*` | AUTH | |
| `/dashboard` | AUTH | |
| `/logs` | AUTH | |
| `/workflow/*` | AUTH | Admin |
| `/repositories/*` | AUTH | |
| `/ai/*` | AUTH | |
| `/agents/*` | AUTH | Admin |
| `/engineering/*` | AUTH | Admin |
| `/production/*` | AUTH | Admin |
| `/plugins/*` | AUTH | Admin |
| `/studio/*` | AUTH | |
| `/audit/*` | AUTH | Admin |
| `/ws` | AUTH (token in query) | |

**Files**: ALL files in `backend/app/api/v1/*.py`, new `backend/app/api/dependencies.py`
**Risk**: MEDIUM — must ensure no endpoint is accidentally left unprotected
**Tests**: Hit every endpoint without auth → 401. Hit with valid auth → 200. Hit admin endpoint with developer role → 403.

---

## Issue S-004: Plugin Upload RCE

**Root Cause**: `PluginLoader.load_plugin()` does `importlib.import_module(manifest.entry_point)` with no sandbox.

**Fix**:
1. Add plugin manifest validation: `plugin_id` alphanumeric only, `entry_point` must be `.py` file in plugin dir
2. Restrict plugin filesystem access via `os.chroot()`-like approach (or `Subprocess` with restricted token on Windows)
3. Add plugin permissions system:
   - `read_metrics` — can read system metrics
   - `read_audit` — can read audit logs
   - `write_workflow` — can create/modify workflows
   - `network_access` — can make HTTP requests
4. Plugin runs in subprocess with timeouts
5. Default: all permissions denied

**Files**: `backend/app/plugins/loader/service.py`, `backend/app/plugins/manifest/service.py`, `backend/app/plugins/registry/service.py`, `config/plugin_policy.yaml`
**Risk**: HIGH — sandboxing is complex. Mitigation: run plugins in separate process with resource limits.
**Tests**: Plugin cannot access files outside its directory, plugin timeouts after 30s, plugin cannot fork bombs

---

## Issue S-005: CORS Misconfiguration

**Root Cause**: `main.py` has `CORSMiddleware(allow_origins=["*"])`.

**Fix**:
1. Add `cors_origins: list[str]` to `config.py:Settings`
2. Default to `["http://localhost:3000"]` for development
3. `config/production.yaml` sets to `["http://dashboard.internal:3000"]`
4. `CORSMiddleware(allow_origins=settings.cors_origins)`

**Files**: `backend/app/config.py`, `backend/app/main.py`, `config/default.yaml`, `config/production.yaml`
**Risk**: LOW
**Tests**: Verify CORS headers for allowed origin, verify blocked for disallowed origin

---

## Issue S-006: Path Traversal in Worker Handlers

**Root Cause**: `dir_scan.py` does `os.walk(payload["directory"])` without validation.

**Fix**:
1. Add `_validate_path(path)` that checks:
   - `os.path.isabs(path)` — must be absolute
   - `".." not in path` — no directory traversal
   - `path.startswith(tuple(settings.allowed_directories))` — must be in allowed roots
2. Add `allowed_directories: list[str]` to worker config (default: `["C:\\", "D:\\"]` or `/home`, `/tmp`)
3. Apply to `dir_scan.py`, `hash_file.py`, `count_files.py`

**Files**: `worker/app/executor/handlers/dir_scan.py`, `worker/app/executor/handlers/hash_file.py`, `worker/app/executor/handlers/count_files.py`, `worker/app/config.py`
**Risk**: LOW
**Tests**: Path with `..` rejected, path outside allowed dir rejected, valid path accepted, symlink handling

---

## Issue S-007: Rate Limiting

**Fix**:
1. Add `slowapi` dependency to `requirements.txt`
2. Create `backend/app/middleware/rate_limit.py`
3. Configure limits per route group:

| Group | Limit |
|-------|-------|
| `/auth/login` | 10/min per IP |
| `/workers/register` | 5/min per IP |
| `/workers/heartbeat` | 60/min per worker |
| `/workers/*` | 30/min per worker |
| General API | 100/min per IP |
| `/ws` | 10 connections/min per IP |

**Files**: `backend/app/middleware/rate_limit.py`, `backend/app/main.py`, `backend/requirements.txt`
**Risk**: LOW
**Tests**: Exceed limit → 429, normal usage succeeds

---

## Issue S-008: WebSocket Authentication

**Root Cause**: `main.py:websocket_endpoint()` accepts all connections.

**Fix**:
1. Require JWT token as query parameter: `ws://host/ws?token=<jwt>`
2. Validate token on connect
3. Reject with 4001 close code if invalid
4. Add token refresh mechanism for long-lived connections

**Files**: `backend/app/main.py`, `backend/app/websocket/manager.py`
**Risk**: LOW
**Tests**: Valid token connects, invalid token rejected, expired token rejected

---

## Issue S-009: Worker Authentication

**Root Cause**: Workers register with just a name/hostname/IP — no authentication.

**Fix**:
1. Add `worker_secret` to worker config (`worker/config.json`)
2. On first run, generate and store a random worker secret
3. Workers send `Authorization: Bearer <worker_secret>` on all requests
4. Master stores hashed worker secrets in `workers` table or config
5. Worker routes validate the secret against the stored hash

**Files**: `backend/app/api/v1/workers.py`, `backend/app/services/worker_manager.py`, `worker/app/config.py`, `worker/app/utils/http_client.py`
**Risk**: LOW — secrets are generated, not hardcoded
**Tests**: Valid worker registers and heartbeats, invalid worker rejected

---

## Issue S-010: HTTPS Support

**Fix**:
1. Add `tls_enabled`, `tls_cert_path`, `tls_key_path` to Settings
2. If TLS enabled, Uvicorn uses cert/key files
3. Add documentation for generating self-signed certs
4. Optional: auto-generate self-signed cert on first run with `cryptography`

**Files**: `backend/app/config.py`, `backend/app/main.py`
**Risk**: LOW
**Tests**: HTTPS works, HTTP to same port fails

---

## Issue S-011: JWT Token Storage

**Root Cause**: Frontend stores JWT in `localStorage` (visible to JS, XSS vulnerable).

**Fix**:
1. Add `/api/v1/auth/login-cookie` endpoint that sets httpOnly cookie
2. Frontend login uses cookie endpoint
3. CSRF token endpoint for cookie-based auth
4. Keep Bearer token for programmatic/worker access

**Files**: `backend/app/api/v1/auth.py`, `backend/app/services/auth.py`, `frontend/src/stores/auth-store.ts`, `frontend/src/app/login/page.tsx`
**Risk**: MEDIUM — cookie auth requires CSRF protection
**Tests**: Cookie set on login, cookie sent on requests, CSRF required for mutations

---

## Issue S-012: SQL Injection in Repository Search

**Root Cause**: `search/service.py` may construct raw queries with user input.

**Fix**:
1. Audit all search queries for parameterized SQL
2. Add regex timeout for user-supplied regex patterns (ReDoS protection)
3. Restrict searchable fields to indexed columns only
4. Add max search term length (200 chars)

**Files**: `backend/app/repository/search/service.py`, `backend/app/api/v1/repositories.py`
**Risk**: LOW — SQLAlchemy is already parameterized
**Tests**: ReDoS attempt timed out, long query rejected

---

## Issue S-013: Information Disclosure

**Root Cause**: Server returns detailed error messages including tracebacks.

**Fix**:
1. In production mode, return generic 500 error message
2. Log full traceback server-side
3. Add custom exception handlers for common error types
4. Sanitize 400/404 messages to avoid revealing internals

**Files**: `backend/app/main.py`
**Risk**: LOW
**Tests**: 500 returns generic message, full error in log
