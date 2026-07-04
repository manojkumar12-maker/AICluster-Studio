# Implementation Order

## Sprint 1: Authentication & Authorization

### Execution Order

```
 1  S-001   JWT Secret Management        [NO DEPS]          config.py
 2  S-002   Admin Credentials            [NO DEPS]          auth.py, main.py
 3  C-005   Double Commit Fix            [NO DEPS]          scheduler.py
 4  C-006   duration_ms Storage          [NO DEPS]          scheduler.py, job.py
 5  C-008   Scheduler Stoppable          [NO DEPS]          scheduler.py
 6  S-005   CORS Restriction             [NO DEPS]          main.py, config.py
 7  S-003   Auth Enforcement             [S-001, S-002]     dependencies.py + 15 route files
 8  === MILESTONE: Auth gates active ===
 9  S-007   Rate Limiting                [S-001]            middleware, main.py
10  S-008   WebSocket Auth               [S-001]            main.py, ws/manager.py
11  S-009   Worker Auth                  [S-001]            workers.py, http_client.py
12  === SPRINT 1 COMPLETE ===
```

### Dependency Justification
- **S-003 blocked by S-001, S-002**: Auth enforcement needs JWT to work (S-001) and an admin user to exist (S-002).
- **S-007 blocked by S-001**: Rate limiter needs config for secret validation on auth endpoints.
- **S-008 blocked by S-001**: WebSocket auth needs JWT validation.
- **S-009 blocked by S-001**: Worker secret follows same pattern as JWT secret.
- **C-005, C-006, C-008**: Independent bug fixes, can be done in parallel.

### Verification Gate (after issue 8)
Before proceeding to Sprint 1 issue 9-11:
- [ ] All tests in `test_auth.py` pass
- [ ] All tests in `test_auth_integration.py` pass
- [ ] Manual: hit 10 protected endpoints without auth → 401
- [ ] Manual: hit 5 public endpoints without auth → 200
- [ ] Manual: admin-only endpoints with developer role → 403
- [ ] Manual: worker endpoints with valid worker_secret → 200

---

## Sprint 2: Worker & Data Stability

### Execution Order

```
 1  C-001   Remove Dead Code             [NO DEPS]          executor.py DELETE
 2  C-003   Reporter None Fix            [NO DEPS]          main.py
 3  C-002   execute_with_progress Fix    [NO DEPS]          main.py, base.py
 4  C-004   poll() Type Fix              [NO DEPS]          main.py, poller.py
 5  C-007   Async IO Wrapping            [NO DEPS]          handlers/*.py
 6  === MILESTONE: Worker stable ===
 7  S-006   Path Traversal Protection    [C-002]            path_utils.py, handlers/*.py
 8  S-012   SQL Injection Prevention     [NO DEPS]          search, repositories
 9  S-008   WebSocket Auth               [S-001]            main.py, ws/manager.py
10  S-009   Worker Auth                  [S-001]            workers.py, http_client.py
11  === SPRINT 2 COMPLETE ===
```

### Dependency Justification
- **S-006 blocked by C-002**: Path validation requires stable handler contract first.
- **S-008 blocked by S-001**: WebSocket auth requires JWT working.
- **S-009 blocked by S-001**: Worker auth requires secret pattern established.
- **C-001 through C-007**: Worker stability fixes are independent of each other.

### Verification Gate (after issue 6)
- [ ] Worker starts and registers with master
- [ ] All 5 handlers execute correctly
- [ ] No AttributeError crashes on startup
- [ ] Event loop responsive during long scans

---

## Sprint 3: Hardening & Infrastructure

### Execution Order

```
 1  C-009   Fix Empty Except Blocks      [NO DEPS]          global audit
 2  === MILESTONE: Error handling stable ===
 3  S-004   Plugin Sandbox               [C-009]            plugins/*
 4  S-007   Rate Limiting                [S-001]            middleware
 5  S-010   HTTPS Support                [S-001]            config, main.py
 6  S-013   Info Disclosure              [NO DEPS]          main.py
 7  S-011   Cookie Auth                  [S-003]            auth.py, frontend
 8  F-003   Frontend WebSocket           [S-008]            frontend
 9  === SPRINT 3 COMPLETE ===
```

### Dependency Justification
- **S-004 blocked by C-009**: Plugin sandbox needs proper error handling first.
- **S-007 blocked by S-001**: Rate limiter knows about auth.
- **S-010 blocked by S-001**: TLS setup needs config pattern.
- **S-011 blocked by S-003**: Cookie auth builds on JWT auth enforcement.
- **F-003 blocked by S-008**: WebSocket client auth depends on server supporting it.

### Verification Gate (after issue 2)
- [ ] No `except: pass` blocks remain in codebase
- [ ] All caught exceptions are logged

---

## Sprint 4: Testing & Polish

### Execution Order

```
Parallel Track A (UI):
 1  F-001   Dashboard Pages              [NO DEPS]          frontend/*.tsx
 2  F-002   Studio Basic Implementation  [NO DEPS]          studio/App.tsx

Parallel Track B (Testing):
 3  T-001   Subsystem Tests              [Sprint 1-3 fixes]   backend/tests/*
 4  T-002   Auth Integration Tests       [S-003]            backend/tests/
 5  T-003   Frontend Tests               [F-001]            frontend/__tests__/

Parallel Track C (Build):
 6  C-010   Deduplicate IP Logic         [NO DEPS]          shared/py/
 7  B-001   Binary Size Optimization     [NO DEPS]          pyinstaller_builder.py
 8  B-002   CI/CD Pipeline               [T-001, T-002, T-003]  .github/

Final:
 9  === SPRINT 4 COMPLETE ===
10  Release: version bump, changelog, tag
```

### Dependency Justification
- **T-001 blocked by Sprint 1-3 fixes**: Tests must test the fixed behavior.
- **T-002 blocked by S-003**: Auth tests need auth enforcement live.
- **T-003 blocked by F-001**: Component tests need components to exist.
- **B-002 blocked by T-001, T-002, T-003**: CI runs all tests.

---

## Blocking Path Summary

```
S-001 ──→ S-003 ──→ S-011
                  └──→ T-002
       ──→ S-007
       ──→ S-008 ──→ F-003
       ──→ S-009
       ──→ S-010

C-002 ──→ S-006

C-009 ──→ S-004

F-001 ──→ T-003

T-001 ─┐
T-002 ─┼──→ B-002
T-003 ─┘
```

## Critical Path (minimum time to release)

```
S-001 → S-003 → S-011 → F-001 → T-003 → B-002
                                (parallel T-001, T-002)
```

Minimum 6 sequential dependencies if all parallel work is optimized.
