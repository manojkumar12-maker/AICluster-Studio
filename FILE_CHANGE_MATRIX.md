# File Change Matrix

## Files Modified in Sprint 1

| File | Reason | Issues | Risk | LOC | Tests |
|------|--------|--------|------|-----|-------|
| `backend/app/config.py` | JWT secret management, CORS config, rate limit settings, TLS settings | S-001, S-005, S-007, S-010 | LOW | +30 | test_config.py |
| `backend/app/services/auth.py` | Random password generation, cookie-based auth | S-002, S-011 | LOW | +25 | test_auth.py |
| `backend/app/api/v1/auth.py` | Login returns httpOnly cookie (optional) | S-011 | LOW | +15 | test_auth.py |
| `backend/app/api/dependencies.py` | NEW: auth middleware, role checker, public route whitelist | S-003 | MEDIUM | +80 | test_auth_integration.py |
| `backend/app/api/v1/health.py` | Add `Depends()` — no auth required (public) | S-003 | LOW | +2 | test_auth_integration.py |
| `backend/app/api/v1/workers.py` | Add `Depends(verify_worker_token)` for all routes | S-003, S-009 | MEDIUM | +15 | test_auth_integration.py |
| `backend/app/api/v1/jobs.py` | Add `Depends(get_current_user)` | S-003 | LOW | +6 | test_auth_integration.py |
| `backend/app/api/v1/dashboard.py` | Add `Depends(get_current_user)` | S-003 | LOW | +3 | test_auth_integration.py |
| `backend/app/api/v1/logs.py` | Add `Depends(get_current_user)` | S-003 | LOW | +3 | test_auth_integration.py |
| `backend/app/api/v1/workflows.py` | Add `Depends(get_current_user)` + admin role | S-003 | LOW | +15 | test_auth_integration.py |
| `backend/app/api/v1/repositories.py` | Add `Depends(get_current_user)` + input validation | S-003, S-012 | LOW | +15 | test_auth_integration.py |
| `backend/app/api/v1/ai.py` | Add `Depends(get_current_user)` | S-003 | LOW | +20 | test_auth_integration.py |
| `backend/app/api/v1/agents.py` | Add `Depends(get_current_user)` + admin role | S-003 | LOW | +15 | test_auth_integration.py |
| `backend/app/api/v1/engineering.py` | Add `Depends(get_current_user)` + admin role | S-003 | LOW | +12 | test_auth_integration.py |
| `backend/app/api/v1/production.py` | Add `Depends(get_current_user)` + admin role | S-003 | LOW | +10 | test_auth_integration.py |
| `backend/app/api/v1/plugins.py` | Add `Depends(get_current_user)` + admin role | S-003 | LOW | +10 | test_auth_integration.py |
| `backend/app/api/v1/studio/workspaces.py` | Add `Depends(get_current_user)` | S-003 | LOW | +8 | test_auth_integration.py |
| `backend/app/api/v1/studio/projects.py` | Add `Depends(get_current_user)` | S-003 | LOW | +6 | test_auth_integration.py |
| `backend/app/api/v1/studio/layout.py` | Add `Depends(get_current_user)` | S-003 | LOW | +4 | test_auth_integration.py |
| `backend/app/main.py` | CORS config, rate limiter, TLS, error handlers, WS auth | S-005, S-007, S-008, S-010, S-013 | MEDIUM | +30 | test_auth_integration.py |
| `backend/app/services/scheduler.py` | Fix double commit, event-based stop, duration_ms | C-005, C-006, C-008 | LOW | +10, -5 | test_scheduler.py |
| `backend/app/models/job.py` | Add `duration_ms` column | C-006 | LOW | +2 | test_scheduler.py |
| `backend/app/websocket/manager.py` | Token validation on connect | S-008 | LOW | +15 | test_websocket.py |
| `backend/app/middleware/rate_limit.py` | NEW: rate limiter | S-007 | LOW | +80 | test_rate_limit.py |
| `backend/requirements.txt` | Add slowapi | S-007 | LOW | +1 | — |
| `config/default.yaml` | CORS origins, rate limit config | S-005, S-007 | LOW | +5 | — |
| `config/production.yaml` | CORS origins, rate limit config | S-005, S-007 | LOW | +5 | — |

## Files Modified in Sprint 2

| File | Reason | Issues | Risk | LOC | Tests |
|------|--------|--------|------|-----|-------|
| `worker/app/main.py` | No-op reporter, remove dead branch, type-safe poll | C-002, C-003, C-004 | MEDIUM | +15, -12 | test_worker.py |
| `worker/app/services/executor.py` | DELETE (dead code) | C-001 | ZERO | -88 | — |
| `worker/app/executor/base.py` | Remove execute_with_progress contract | C-002 | LOW | -3 | test_executor.py |
| `worker/app/executor/handlers/path_utils.py` | NEW: path validation utility | S-006 | LOW | +40 | test_handlers.py |
| `worker/app/executor/handlers/dir_scan.py` | Path validation, async IO | S-006, C-007 | LOW | +15, -5 | test_handlers.py |
| `worker/app/executor/handlers/hash_file.py` | Path validation, async IO | S-006, C-007 | LOW | +15, -5 | test_handlers.py |
| `worker/app/executor/handlers/count_files.py` | Path validation, async IO | S-006, C-007 | LOW | +15, -5 | test_handlers.py |
| `worker/app/utils/http_client.py` | Worker secret auth header | S-009 | LOW | +10 | test_worker_auth.py |
| `worker/app/config.py` | worker_secret field | S-009, C-010 | LOW | +5 | test_config.py |
| `worker/app/utils/retry.py` | Add jitter | — | LOW | +5 | test_reconnect.py |
| `backend/app/repository/search/service.py` | SQL injection prevention | S-012 | LOW | +10 | test_repository.py |
| `backend/app/api/v1/repositories.py` | Input validation for search | S-012 | LOW | +5 | test_repository.py |
| `shared/py/schemas.py` | IP resolution utility | C-010 | LOW | +10 | — |
| `backend/tests/` | New test files for auth, WS, scheduler | S-003, S-008, C-005, C-006, C-008 | LOW | +300 | — |
| `worker/tests/` | New test files for handlers, auth | S-006, S-009, C-002, C-003, C-007 | LOW | +200 | — |

## Files Modified in Sprint 3

| File | Reason | Issues | Risk | LOC | Tests |
|------|--------|--------|------|-----|-------|
| `backend/app/plugins/loader/service.py` | Sandboxed execution | S-004 | HIGH | +60 | test_plugins.py |
| `backend/app/plugins/manifest/service.py` | Stricter validation | S-004 | LOW | +20 | test_plugins.py |
| `backend/app/plugins/registry/service.py` | Permission enforcement | S-004 | LOW | +15 | test_plugins.py |
| `config/plugin_policy.yaml` | NEW: plugin permissions | S-004 | LOW | +20 | test_plugins.py |
| `backend/app/main.py` | Error handlers (production mode) | S-013 | LOW | +10 | — |
| `backend/app/services/auth.py` | Cookie-based auth | S-011 | MEDIUM | +30 | test_auth.py |
| `backend/app/api/v1/auth.py` | Cookie endpoint + CSRF | S-011 | MEDIUM | +20 | test_auth.py |
| `frontend/src/stores/auth-store.ts` | Cookie-based auth | S-011 | MEDIUM | +20 | auth-store.test.ts |
| `frontend/src/lib/api.ts` | CSRF token handling | S-011 | LOW | +10 | api.test.ts |
| `frontend/src/lib/websocket.ts` | NEW: WebSocket client | F-003 | MEDIUM | +80 | — |
| `frontend/src/app/(dashboard)/dashboard/page.tsx` | WS integration | F-003 | MEDIUM | +20 | dashboard.test.tsx |
| `frontend/src/app/(dashboard)/workers/page.tsx` | WS integration | F-003 | LOW | +10 | — |
| ALL Python files | Fix empty except blocks | C-009 | LOW | ~50 | — |
| `backend/tests/` | New tests for plugins, rate limit, auth | S-004, S-007, S-011 | LOW | +200 | — |

## Files Modified in Sprint 4

| File | Reason | Issues | Risk | LOC | Tests |
|------|--------|--------|------|-----|-------|
| `frontend/src/app/(dashboard)/jobs/page.tsx` | Implement from placeholder | F-001 | LOW | +80 | — |
| `frontend/src/app/(dashboard)/logs/page.tsx` | Implement from placeholder | F-001 | LOW | +80 | — |
| `frontend/src/app/(dashboard)/chat/page.tsx` | Implement from placeholder | F-001 | LOW | +100 | — |
| `frontend/src/app/(dashboard)/projects/page.tsx` | Implement from placeholder | F-001 | LOW | +50 | — |
| `frontend/src/app/(dashboard)/files/page.tsx` | Implement from placeholder | F-001 | LOW | +120 | — |
| `frontend/src/app/(dashboard)/analytics/page.tsx` | Implement from placeholder | F-001 | LOW | +150 | — |
| `frontend/src/app/(dashboard)/settings/page.tsx` | Implement from placeholder | F-001 | LOW | +80 | — |
| `studio/src/App.tsx` | Basic layout | F-002 | LOW | +100 | — |
| `studio/src/components/*.tsx` | NEW: workspace/project/chat | F-002 | LOW | +200 | — |
| `backend/tests/test_workflow.py` | NEW | T-001 | LOW | +200 | — |
| `backend/tests/test_repository.py` | NEW | T-001 | LOW | +200 | — |
| `backend/tests/test_ai.py` | NEW | T-001 | LOW | +200 | — |
| `backend/tests/test_agents.py` | NEW | T-001 | LOW | +150 | — |
| `backend/tests/test_engineering.py` | NEW | T-001 | LOW | +150 | — |
| `backend/tests/test_plugins.py` | NEW | T-001 | LOW | +100 | — |
| `backend/tests/test_audit.py` | NEW | T-001 | LOW | +150 | — |
| `backend/tests/test_websocket.py` | NEW | T-001 | LOW | +100 | — |
| `frontend/src/__tests__/*.test.tsx` | NEW | T-003 | LOW | +200 | — |
| `build/pyinstaller_builder.py` | Binary size optimization | B-001 | MEDIUM | +20 | — |
| `.github/workflows/ci.yml` | NEW: CI/CD | B-002 | LOW | +100 | — |

## Summary

| Sprint | Files Created | Files Modified | Files Deleted | Est. LOC |
|--------|---------------|----------------|---------------|----------|
| Sprint 1 | 2 | ~28 | 0 | ~350 |
| Sprint 2 | 1 | ~14 | 1 | ~200 |
| Sprint 3 | 2 | ~15 | 0 | ~400 |
| Sprint 4 | ~15 | ~10 | 0 | ~2000 |
| **Total** | **~20** | **~67** | **1** | **~2950** |
