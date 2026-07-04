# Commit Plan

## Sprint 1 Commits

### Commit 1.1: JWT Secret Management
```
Message: fix(security): replace hardcoded JWT secret with auto-generated key

- Generate 32-byte random secret on first run
- Store in data/secret.key
- Support AICLUSTER_SECRET_KEY env var override
- Log warning if using auto-generated key

Files:
  M backend/app/config.py
  A .env.example (document AICLUSTER_SECRET_KEY)

Tests:
  A backend/tests/test_auth.py:
    - test_jwt_secret_generation
    - test_jwt_secret_persistence
    - test_jwt_secret_env_override

Rollback: Revert config.py, delete data/secret.key
```

### Commit 1.2: Default Admin Credentials
```
Message: fix(security): generate random admin password on first run

- Replace hardcoded "admin123" with secrets.token_urlsafe(16)
- Print generated password to stderr
- Support AICLUSTER_ADMIN_PASSWORD env var
- Add --reset-admin-password CLI flag

Files:
  M backend/app/services/auth.py
  M backend/app/main.py

Tests:
  A backend/tests/test_auth.py:
    - test_admin_password_generated
    - test_admin_password_env_override

Rollback: Revert auth.py seed_default_admin()
```

### Commit 1.3: Fix Scheduler Bugs
```
Message: fix(scheduler): resolve double commit, duration_ms loss, and stop mechanism

- Remove double commit in get_next_for_worker
- Store duration_ms instead of pass in complete_job
- Replace _running flag with asyncio.Event for clean shutdown

Files:
  M backend/app/services/scheduler.py
  M backend/app/models/job.py (+duration_ms column)

Tests:
  A backend/tests/test_scheduler_fixes.py:
    - test_single_commit_on_assign
    - test_duration_stored
    - test_clean_shutdown_within_1s

Rollback: Revert scheduler.py, revert job.py
```

### Commit 1.4: Restrict CORS
```
Message: fix(security): restrict CORS to configured origins

- Replace allow_origins=["*"] with config-driven origins
- Default to ["http://localhost:3000"]
- Production config uses explicit list

Files:
  M backend/app/main.py
  M backend/app/config.py (+cors_origins)
  M config/default.yaml
  M config/production.yaml

Tests:
  A backend/tests/test_auth_integration.py:
    - test_cors_allowed_origin
    - test_cors_blocked_origin

Rollback: Revert to ["*"]
```

### Commit 1.5: Authentication Enforcement
```
Message: feat(auth): enforce JWT authentication on all API endpoints

- Create api/dependencies.py with get_current_user, require_role, verify_worker_token
- PUBLIC whitelist: health, login, docs, openapi, redoc, static
- Add Depends(get_current_user) to all 15 route modules
- Add Depends(require_role("admin")) to admin-only endpoints
- Add Depends(verify_worker_token) to worker endpoints

WARNING: This is a BREAKING CHANGE. All API clients must now include
Authorization: Bearer <token> header.

Files:
  A backend/app/api/dependencies.py
  M backend/app/api/v1/health.py (+1 line)
  M backend/app/api/v1/auth.py
  M backend/app/api/v1/workers.py (+worker token)
  M backend/app/api/v1/jobs.py
  M backend/app/api/v1/dashboard.py
  M backend/app/api/v1/logs.py
  M backend/app/api/v1/workflows.py (+admin for mutations)
  M backend/app/api/v1/repositories.py
  M backend/app/api/v1/ai.py
  M backend/app/api/v1/agents.py (+admin for management)
  M backend/app/api/v1/engineering.py (+admin)
  M backend/app/api/v1/production.py (+admin)
  M backend/app/api/v1/plugins.py (+admin)
  M backend/app/api/v1/studio/workspaces.py
  M backend/app/api/v1/studio/projects.py
  M backend/app/api/v1/studio/layout.py
  M backend/app/audit/api.py (+admin)

Tests:
  A backend/tests/test_auth_integration.py:
    - test_all_endpoints_scan (automated scan)
    - test_role_enforcement
    - test_public_routes_whitelist
    - test_worker_token_endpoints

Rollback: Remove Depends() from all route files
```

### Commit 1.6: Rate Limiting
```
Message: feat(security): add rate limiting middleware

- Add slowapi dependency
- Configurable per-endpoint limits
- 10/min for login, 60/min for worker, 100/min general

Files:
  A backend/app/middleware/rate_limit.py
  M backend/app/main.py (+rate limiter)
  M backend/app/config.py (+rate limit settings)
  M backend/requirements.txt (+slowapi)

Tests:
  A backend/tests/test_rate_limit.py

Rollback: Remove rate limiter middleware
```

### Commit 1.7: WebSocket Authentication
```
Message: fix(security): require JWT token for WebSocket connections

- Validate ?token= query parameter on connect
- Reject with 4001 if invalid
- Support worker tokens

Files:
  M backend/app/main.py
  M backend/app/websocket/manager.py (+authenticate())

Tests:
  A backend/tests/test_websocket.py

Rollback: Remove auth check from websocket_endpoint()
```

### Commit 1.8: Worker Authentication
```
Message: fix(security): require worker_secret for worker communication

- Worker generates random secret on first run
- All worker → master requests include Authorization header
- Master validates worker_secret on register/heartbeat/progress/result

Files:
  M worker/app/utils/http_client.py (+auth header)
  M worker/app/config.py (+worker_secret)
  M worker/app/main.py (+pass secret to http_client)
  M backend/app/api/v1/workers.py (+verify_worker_token)

Tests:
  A worker/tests/test_worker_auth.py
  M backend/tests/test_auth_integration.py

Rollback: Remove auth header from http_client, remove Depends from worker routes
```

---

## Sprint 2 Commits

### Commit 2.1: Remove Dead Code
```
Message: chore(worker): remove unused services/executor.py

Files:
  D worker/app/services/executor.py

Rollback: Restore file
```

### Commit 2.2: Fix Worker Crashes
```
Message: fix(worker): prevent AttributeError crashes on reporter calls

- Add _NoOpReporter as default before worker loop starts
- Remove dead execute_with_progress branch
- Add type guard for poll() result

Files:
  M worker/app/main.py

Tests:
  M worker/tests/

Rollback: Revert main.py
```

### Commit 2.3: Fix Blocking IO in Handlers
```
Message: fix(worker): wrap blocking os.walk() in asyncio.to_thread()

- Move synchronous IO to thread pool
- Prevents event loop blocking during long scans

Files:
  M worker/app/executor/handlers/dir_scan.py
  M worker/app/executor/handlers/count_files.py
  M worker/app/executor/handlers/hash_file.py

Tests:
  A worker/tests/test_handlers.py

Rollback: Revert to synchronous IO
```

### Commit 2.4: Add Path Validation
```
Message: fix(security): prevent path traversal in worker file handlers

- Add shared path_utils.py with validate_path()
- Reject paths with .. or outside allowed directories

Files:
  A worker/app/executor/handlers/path_utils.py
  M worker/app/executor/handlers/dir_scan.py
  M worker/app/executor/handlers/hash_file.py
  M worker/app/executor/handlers/count_files.py
  M worker/app/config.py (+allowed_directories)

Tests:
  M worker/tests/test_handlers.py

Rollback: Remove path validation calls
```

### Commit 2.5: Fix SQL Injection Risk
```
Message: fix(security): add input validation and regex timeout to search

- Limit search term to 200 chars
- Add 2s regex timeout
- Restrict searchable fields

Files:
  M backend/app/repository/search/service.py
  M backend/app/api/v1/repositories.py

Tests:
  A backend/tests/test_repository.py

Rollback: Revert search changes
```

---

## Sprint 3 Commits

### Commit 3.1: Fix Empty Except Blocks
```
Message: fix: replace empty except blocks with proper error logging

Audit and fix all except:pass patterns across the codebase.

Files:
  M multiple files in backend/app/ and worker/app/

Rollback: Per-file revert
```

### Commit 3.2: Plugin Sandbox
```
Message: feat(security): add sandboxed plugin execution with permissions

- Validate plugin manifest strictly
- Enforce filesystem/network/timeout restrictions
- Add plugin_policy.yaml configuration

Files:
  M backend/app/plugins/loader/service.py
  M backend/app/plugins/manifest/service.py
  M backend/app/plugins/registry/service.py
  A config/plugin_policy.yaml

Tests:
  M backend/tests/test_plugins.py

Rollback: Revert plugin loader to non-sandboxed
```

### Commit 3.3: HTTPS Support
```
Message: feat: add optional HTTPS support with TLS configuration

Files:
  M backend/app/config.py (+tls settings)
  M backend/app/main.py (+TLS uvicorn)

Tests:
  A backend/tests/test_auth.py

Rollback: Remove TLS config
```

### Commit 3.4: Info Disclosure Protection
```
Message: fix(security): sanitize production error messages

- Return generic {"detail": "Internal server error"} in production
- Log full details server-side

Files:
  M backend/app/main.py (+error handlers)

Rollback: Remove error handlers
```

### Commit 3.5: Cookie-Based Auth
```
Message: feat(auth): add httpOnly cookie authentication for frontend

- Add /auth/login-cookie, /auth/csrf, /auth/logout endpoints
- Frontend uses cookie instead of localStorage
- CSRF protection for mutations

Files:
  M backend/app/services/auth.py
  M backend/app/api/v1/auth.py
  M frontend/src/stores/auth-store.ts
  M frontend/src/lib/api.ts

Tests:
  M backend/tests/test_auth.py
  A frontend/src/__tests__/auth-store.test.ts

Rollback: Revert cookie endpoints and frontend auth
```

### Commit 3.6: Frontend WebSocket
```
Message: feat(ui): connect dashboard to WebSocket for real-time updates

- New WebSocket client with reconnection
- Dashboard and Workers pages receive live events
- Polling as fallback

Files:
  A frontend/src/lib/websocket.ts
  M frontend/src/app/(dashboard)/dashboard/page.tsx
  M frontend/src/app/(dashboard)/workers/page.tsx

Rollback: Revert WS code, restore polling
```

---

## Sprint 4 Commits

### Commit 4.1: Dashboard Pages
```
Message: feat(ui): implement all placeholder dashboard pages

Implement 8 pages: Jobs, Logs, Chat, Projects, Files, Analytics, Settings

Files:
  M frontend/src/app/(dashboard)/jobs/page.tsx
  M frontend/src/app/(dashboard)/logs/page.tsx
  M frontend/src/app/(dashboard)/chat/page.tsx
  M frontend/src/app/(dashboard)/projects/page.tsx
  M frontend/src/app/(dashboard)/files/page.tsx
  M frontend/src/app/(dashboard)/analytics/page.tsx
  M frontend/src/app/(dashboard)/settings/page.tsx

Rollback: Revert per-page
```

### Commit 4.2: Studio Basic Implementation
```
Message: feat(studio): implement workspace/project listing and AI chat

Files:
  M studio/src/App.tsx
  A studio/src/components/*.tsx

Rollback: Revert studio files
```

### Commit 4.3: Subsystem Tests
```
Message: test: add comprehensive tests for all untested subsystems

- Workflow Engine (12 tests)
- Repository Intelligence (12 tests)
- AI Runtime (12 tests)
- Multi-Agent Engine (10 tests)
- Engineering Engine (10 tests)
- Plugin System (8 tests)
- Audit System (10 tests)
- WebSocket (6 tests)
- Auth Integration (12 tests)

Files:
  A backend/tests/test_workflow.py
  A backend/tests/test_repository.py
  A backend/tests/test_ai.py
  A backend/tests/test_agents.py
  A backend/tests/test_engineering.py
  A backend/tests/test_plugins.py
  A backend/tests/test_audit.py
  A backend/tests/test_websocket.py
  A backend/tests/test_auth_integration.py

Rollback: N/A (additive)
```

### Commit 4.4: Frontend Tests
```
Message: test: add frontend component tests

Files:
  A frontend/src/__tests__/*.test.tsx

Rollback: N/A (additive)
```

### Commit 4.5: IP Resolution Dedup
```
Message: refactor: consolidate IP resolution logic into shared module

Files:
  M worker/app/config.py
  M shared/py/schemas.py

Rollback: Revert shared and worker config
```

### Commit 4.6: Binary Size Optimization
```
Message: build: reduce PyInstaller binary size with exclusions and UPX

Files:
  M build/pyinstaller_builder.py
  M build/config.py

Rollback: Revert build config
```

### Commit 4.7: CI/CD Pipeline
```
Message: ci: add GitHub Actions workflow for testing and release

Files:
  A .github/workflows/ci.yml

Rollback: Remove workflow file
```

### Commit 4.8: Version 1.3.1 Release
```
Message: release: v1.3.1

Security & Stability Release
- Fixed 13 security issues (4 CRITICAL, 5 HIGH)
- Fixed 10 stability/code quality issues
- Implemented 8 dashboard pages
- Added comprehensive test suite
- Added CI/CD pipeline

Files:
  M VERSION (1.3.0 → 1.3.1)
  M CHANGELOG.md

Rollback: Revert version and changelog
```

---

## Commit Statistics

| Sprint | Commits | Files Created | Files Modified | Files Deleted | Total LOC |
|--------|---------|---------------|----------------|---------------|-----------|
| Sprint 1 | 8 | 5 | ~30 | 0 | ~500 |
| Sprint 2 | 5 | 2 | ~12 | 1 | ~200 |
| Sprint 3 | 6 | 4 | ~20 | 0 | ~400 |
| Sprint 4 | 8 | ~20 | ~15 | 0 | ~2500 |
| **Total** | **27** | **~31** | **~77** | **1** | **~3600** |
