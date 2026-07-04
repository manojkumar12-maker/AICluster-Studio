# AICluster v1.3.1 Sprint Plan

## Sprint 1: Authentication & Authorization (Weeks 1-2)

### Objectives
- Remove all hardcoded secrets
- Enforce authentication on all API endpoints
- Fix critical scheduler bugs
- Restrict CORS

### Issues
| ID | Title | Effort | Risk |
|----|-------|--------|------|
| S-001 | JWT Secret Hardcoded | 4h | LOW |
| S-002 | Default Admin Credentials | 3h | LOW |
| S-003 | Auth Enforcement (all routes) | 16h | MEDIUM |
| S-005 | CORS Restriction | 1h | LOW |
| C-005 | Double Commit in Scheduler | 1h | LOW |
| C-006 | duration_ms Not Stored | 1h | LOW |
| C-008 | Scheduler Not Stoppable | 2h | LOW |

### Files Modified
```
backend/app/config.py              — JWT secret management
backend/app/services/auth.py       — Password generation, cookie auth
backend/app/api/v1/auth.py         — Login response with cookie
backend/app/api/dependencies.py    — NEW: auth middleware, role checker
backend/app/api/v1/*.py            — ALL 15 route files: add Depends
backend/app/main.py                — CORS config, error handlers
backend/app/services/scheduler.py  — Fix commits, event-based stop
backend/app/models/job.py          — Add duration_ms column
config/default.yaml                — CORS origins
config/production.yaml             — CORS origins
```

### Acceptance Criteria
- [ ] No hardcoded secrets in source code
- [ ] Admin password generated randomly on first run
- [ ] All API endpoints return 401 without valid JWT (except whitelist)
- [ ] Worker endpoints accept worker_secret
- [ ] Admin-only endpoints return 403 for non-admin users
- [ ] CORS restricted to configured origins
- [ ] Single commit in `get_next_for_worker`
- [ ] `duration_ms` stored in job record
- [ ] Scheduler stops within 1s of `stop()`

### Tests Added
```
backend/tests/test_auth.py                 — Auth unit tests
backend/tests/test_auth_integration.py     — Auth integration tests
```

### Expected Result
Master server is now secure: all API calls require authentication, no hardcoded secrets, CORS is properly configured.

---

## Sprint 2: Worker & Data Stability (Weeks 3-4)

### Objectives
- Fix all worker bugs (None crashes, dead code, blocking IO)
- Add path traversal protection
- Add WebSocket and worker authentication
- Fix SQL injection risk

### Issues
| ID | Title | Effort | Risk |
|----|-------|--------|------|
| S-006 | Path Traversal Protection | 3h | LOW |
| S-008 | WebSocket Authentication | 4h | LOW |
| S-009 | Worker Registration Auth | 4h | LOW |
| S-012 | SQL Injection Prevention | 2h | LOW |
| C-001 | Remove Dead Code (executor.py) | 0.5h | LOW |
| C-002 | Fix execute_with_progress | 2h | LOW |
| C-003 | Fix reporter None | 2h | LOW |
| C-004 | Fix poll() Type Handling | 1h | LOW |
| C-007 | Fix Blocking IO in Handlers | 3h | LOW |

### Files Modified
```
worker/app/main.py                          — Fix reporter, remove dead code, type-safe poll
worker/app/services/executor.py             — DELETE
worker/app/executor/base.py                 — Remove execute_with_progress contract
worker/app/executor/handlers/path_utils.py  — NEW: path validation utility
worker/app/executor/handlers/dir_scan.py    — Path validation, async IO
worker/app/executor/handlers/hash_file.py   — Path validation, async IO
worker/app/executor/handlers/count_files.py — Path validation, async IO
worker/app/utils/http_client.py             — Worker secret auth header
worker/app/config.py                        — worker_secret field
worker/app/utils/retry.py                   — Add jitter
backend/app/websocket/manager.py            — Token validation
backend/app/main.py                         — WS token query param
backend/app/api/v1/workers.py               — Worker secret validation
backend/app/repository/search/service.py    — SQL injection protection
backend/app/api/v1/repositories.py          — Search input validation
```

### Acceptance Criteria
- [ ] Worker no longer crashes on reporter calls
- [ ] No AttributeError for execute_with_progress
- [ ] Blocking IO moved to thread pool
- [ ] Path traversal attempts rejected
- [ ] WebSocket rejects invalid tokens
- [ ] Worker registration requires secret
- [ ] SQL injection attempts fail
- [ ] Retry has jitter
- [ ] Dead code removed

### Tests Added
```
worker/tests/test_handlers.py     — Path validation, async IO tests
worker/tests/test_worker_auth.py  — Worker secret auth tests
backend/tests/test_websocket.py   — WS auth tests
```

### Expected Result
Worker is stable: no null-pointer risks, no blocking IO, no path traversal vulnerabilities. All worker-master communication is authenticated.

---

## Sprint 3: Hardening & Infrastructure (Weeks 5-6)

### Objectives
- Sandbox plugin execution
- Add rate limiting
- Support HTTPS
- Implement cookie-based auth for frontend
- Connect frontend WebSocket
- Fix empty except blocks
- Sanitize error messages

### Issues
| ID | Title | Effort | Risk |
|----|-------|--------|------|
| S-004 | Plugin Sandbox | 12h | HIGH |
| S-007 | Rate Limiting | 6h | LOW |
| S-010 | HTTPS Support | 3h | LOW |
| S-011 | Cookie-Based Auth | 6h | MEDIUM |
| S-013 | Info Disclosure Protection | 2h | LOW |
| C-009 | Fix Empty Except Blocks | 8h | MEDIUM |
| F-003 | Frontend WebSocket | 4h | MEDIUM |

### Files Modified
```
backend/app/plugins/loader/service.py           — Sandboxed execution
backend/app/plugins/manifest/service.py          — Stricter validation
backend/app/plugins/registry/service.py          — Permission enforcement
config/plugin_policy.yaml                        — NEW: plugin permissions
backend/app/main.py                              — Rate limiter, TLS, error handlers
backend/app/config.py                            — Rate limit, TLS settings
backend/app/middleware/rate_limit.py             — NEW: rate limiter
backend/requirements.txt                         — Add slowapi
backend/app/services/auth.py                     — Cookie-based auth
backend/app/api/v1/auth.py                       — Cookie endpoint + CSRF
frontend/src/stores/auth-store.ts                — Cookie-based auth
frontend/src/lib/api.ts                          — CSRF token handling
frontend/src/lib/websocket.ts                    — NEW: WebSocket client
frontend/src/app/(dashboard)/dashboard/page.tsx  — WS integration
frontend/src/app/(dashboard)/workers/page.tsx    — WS integration
ALL Python files                                 — Fix empty except blocks
```

### Acceptance Criteria
- [ ] Plugins cannot access files outside plugin directory
- [ ] Rate limiting returns 429 on excess requests
- [ ] HTTPS works with cert/key files
- [ ] Frontend uses httpOnly cookies instead of localStorage for auth
- [ ] CSRF protection works
- [ ] Dashboard receives real-time WebSocket updates
- [ ] Error messages in production are generic
- [ ] No `except: pass` blocks remain

### Tests Added
```
backend/tests/test_plugins.py     — Plugin sandbox tests
backend/tests/test_rate_limit.py  — Rate limiting tests
backend/tests/test_auth.py        — Cookie auth tests
```

### Expected Result
System is hardened: plugins are sandboxed, API is rate-limited, HTTPS is available, frontend auth is XSS-resistant, and errors don't leak information.

---

## Sprint 4: Testing & Polish (Weeks 7-8)

### Objectives
- Comprehensive test coverage for all subsystems
- Implement all dashboard placeholder pages
- Basic Studio IDE implementation
- CI/CD pipeline
- Binary size optimization
- Code deduplication

### Issues
| ID | Title | Effort | Risk |
|----|-------|--------|------|
| T-001 | Subsystem Tests (8 subsystems) | 24h | LOW |
| T-002 | Auth Integration Tests | 6h | LOW |
| T-003 | Frontend Tests | 8h | LOW |
| F-001 | Dashboard Pages (8 pages) | 19h | LOW |
| F-002 | Studio Improvements | 6h | LOW |
| C-010 | Deduplicate IP Logic | 1h | LOW |
| B-001 | Binary Size Optimization | 4h | MEDIUM |
| B-002 | CI/CD Pipeline | 8h | LOW |

### Files Modified
```
backend/tests/test_workflow.py      — NEW: workflow tests
backend/tests/test_repository.py     — NEW: repository tests
backend/tests/test_ai.py             — NEW: AI tests
backend/tests/test_agents.py         — NEW: agent tests
backend/tests/test_engineering.py    — NEW: engineering tests
backend/tests/test_plugins.py        — NEW: plugin tests (continued)
backend/tests/test_audit.py          — NEW: audit tests
backend/tests/test_websocket.py      — NEW: WS tests
backend/tests/test_auth_integration.py — Auth integration tests

frontend/src/app/(dashboard)/jobs/page.tsx        — Implement
frontend/src/app/(dashboard)/logs/page.tsx        — Implement
frontend/src/app/(dashboard)/chat/page.tsx        — Implement
frontend/src/app/(dashboard)/projects/page.tsx    — Implement
frontend/src/app/(dashboard)/files/page.tsx       — Implement
frontend/src/app/(dashboard)/analytics/page.tsx   — Implement
frontend/src/app/(dashboard)/settings/page.tsx    — Implement
frontend/src/__tests__/*.test.tsx                 — NEW: frontend tests

studio/src/App.tsx                                — Implement basic layout
studio/src/components/*.tsx                       — NEW: workspace/project/chat pages

worker/app/config.py                              — Remove duplicate IP logic (use shared)
shared/py/schemas.py                              — Add IP resolution utility

build/pyinstaller_builder.py                      — Binary size optimizations
.github/workflows/ci.yml                          — NEW: CI/CD pipeline
```

### Acceptance Criteria
- [ ] Every subsystem has minimum 5 tests
- [ ] Auth flow fully tested (login, token, roles, expiry)
- [ ] Frontend components have tests
- [ ] All 10 dashboard pages show real data from API
- [ ] Studio shows workspace/project list and basic chat
- [ ] CI/CD pipeline passes on every PR
- [ ] Master binary size reduced (80MB → <60MB)
- [ ] IP resolution logic is in shared/
- [ ] All tests pass: `pytest backend/tests/ && pytest worker/tests/ && npx vitest --run`

### Expected Result
AICluster v1.3.1 is ready for release: fully tested, no placeholder pages, CI/CD gated, auditable, and production-ready.

---

## Execution Order Within Sprints

### Sprint 1 Order
1. **S-001**: JWT Secret (prerequisite for S-003, S-008, S-009)
2. **S-002**: Admin Credentials (prerequisite for S-003)
3. **S-003**: Auth Enforcement (all routes)
4. **S-005**: CORS Restriction (independent)
5. **C-005**: Double Commit Fix (independent)
6. **C-006**: duration_ms Fix (independent)
7. **C-008**: Scheduler Stoppable (independent)

### Sprint 2 Order
1. **C-001**: Dead Code Removal (independent, quick win)
2. **C-003**: Reporter None Fix (critical bug)
3. **C-002**: execute_with_progress Fix (critical bug)
4. **C-004**: poll() Type Fix (critical bug)
5. **C-007**: Blocking IO Fix (performance bug)
6. **S-006**: Path Traversal (depends on C-002 for handler contract)
7. **S-012**: SQL Injection (independent)
8. **S-008**: WebSocket Auth (depends on S-001 from Sprint 1)
9. **S-009**: Worker Auth (depends on S-001 from Sprint 1)

### Sprint 3 Order
1. **C-009**: Empty Except Blocks (prerequisite for S-004 stability)
2. **S-007**: Rate Limiting (depends on S-001)
3. **S-013**: Info Disclosure (independent)
4. **S-004**: Plugin Sandbox (depends on C-009)
5. **S-010**: HTTPS (depends on S-001)
6. **S-011**: Cookie Auth (depends on S-003)
7. **F-003**: Frontend WebSocket (depends on S-008 from Sprint 2)

### Sprint 4 Order
1. **F-001**: Dashboard Pages (can run in parallel with testing)
2. **C-010**: IP Dedup (quick fix)
3. **B-001**: Binary Size (independent)
4. **T-001**: Subsystem Tests (after all fixes stable)
5. **T-002**: Auth Tests (after S-003 stable)
6. **T-003**: Frontend Tests (after F-001 stable)
7. **B-002**: CI/CD (after all tests stable)
8. **F-002**: Studio (nice-to-have, flexible timing)
