# Test Impact Matrix

## Overview

v1.3.1 adds approximately 1500+ lines of new test code across backend, worker, and frontend. Every fix must include corresponding tests.

---

## Test Inventory by Issue

| Issue | Unit Tests | Integration | Security | Performance | Manual |
|-------|-----------|-------------|----------|-------------|--------|
| S-001 | 3 | 1 | 1 | — | — |
| S-002 | 2 | 1 | 1 | — | — |
| S-003 | — | 1 (endpoint scan) | 1 | — | — |
| S-004 | 4 | 2 | 2 | 1 | — |
| S-005 | 1 | 1 | 1 | — | — |
| S-006 | 3 | 1 | 1 | — | — |
| S-007 | 2 | 1 | 1 | — | — |
| S-008 | 2 | 1 | 1 | — | — |
| S-009 | 3 | 1 | 1 | — | — |
| S-010 | 1 | 1 | — | — | — |
| S-011 | 2 | 1 | 1 | — | — |
| S-012 | 2 | 1 | 1 | — | — |
| S-013 | 1 | — | 1 | — | — |
| C-001 | — | 1 | — | — | — |
| C-002 | 3 | 1 | — | — | — |
| C-003 | 2 | 1 | — | — | — |
| C-004 | 2 | 1 | — | — | — |
| C-005 | 1 | 1 | — | — | — |
| C-006 | 1 | 1 | — | — | — |
| C-007 | 2 | 1 | — | 1 | — |
| C-008 | 2 | — | — | — | — |
| C-009 | — | — | — | — | 1 (code review) |
| C-010 | 1 | — | — | — | — |
| F-001 | — | — | — | — | 8 (visual) |
| F-002 | — | — | — | — | 1 (visual) |
| F-003 | — | 1 | — | — | 1 (visual) |
| T-001 | ~80 | ~10 | — | — | — |
| T-002 | ~12 | ~6 | ~4 | — | — |
| T-003 | ~12 | — | — | — | — |
| B-001 | — | — | — | — | 1 (measurement) |
| B-002 | — | — | — | — | 1 (CI check) |

---

## New Test Files

### Backend Tests (Sprint 1-3)

| File | Tests | Issues Covered |
|------|-------|----------------|
| `backend/tests/test_auth.py` | ~10 | S-001, S-002, S-011 |
| `backend/tests/test_auth_integration.py` | ~12 | S-003, S-005, S-011 |
| `backend/tests/test_rate_limit.py` | ~4 | S-007 |
| `backend/tests/test_websocket.py` | ~6 | S-008 |
| `backend/tests/test_scheduler_fixes.py` | ~5 | C-005, C-006, C-008 |

### Backend Tests (Sprint 4 — T-001)

| File | Tests | Subsystem |
|------|-------|-----------|
| `backend/tests/test_workflow.py` | ~12 | Workflow Engine |
| `backend/tests/test_repository.py` | ~12 | Repository Intelligence |
| `backend/tests/test_ai.py` | ~12 | AI Runtime |
| `backend/tests/test_agents.py` | ~10 | Multi-Agent Engine |
| `backend/tests/test_engineering.py` | ~10 | Engineering Engine |
| `backend/tests/test_plugins.py` | ~8 | Plugin System |
| `backend/tests/test_audit.py` | ~10 | Audit System |

### Worker Tests (Sprint 2)

| File | Tests | Issues Covered |
|------|-------|----------------|
| `worker/tests/test_handlers.py` | ~8 | S-006, C-007 |
| `worker/tests/test_worker_auth.py` | ~6 | S-009 |
| `worker/tests/test_worker_core.py` | ~6 | C-002, C-003, C-004 |

### Frontend Tests (Sprint 4)

| File | Tests | Issues Covered |
|------|-------|----------------|
| `frontend/src/__tests__/auth-store.test.ts` | ~4 | S-011 |
| `frontend/src/__tests__/api.test.ts` | ~3 | — |
| `frontend/src/app/login/__tests__/page.test.tsx` | ~3 | — |
| `frontend/src/components/layout/__tests__/sidebar.test.tsx` | ~3 | — |
| `frontend/src/app/(dashboard)/dashboard/__tests__/page.test.tsx` | ~3 | — |

---

## Test Execution Plan

### Per-Sprint Testing

**Sprint 1**: Run after each commit
```bash
cd backend && pytest tests/test_auth.py tests/test_auth_integration.py tests/test_scheduler_fixes.py -v
```

**Sprint 2**: Run after each commit
```bash
cd worker && pytest tests/ -v
cd backend && pytest tests/test_websocket.py -v
```

**Sprint 3**: Run after each commit
```bash
cd backend && pytest tests/test_rate_limit.py tests/test_plugins.py tests/test_auth.py -v
```

**Sprint 4**: Run full suite
```bash
cd backend && pytest tests/ -v --cov=app
cd worker && pytest tests/ -v --cov=app
cd frontend && npx vitest --run --coverage
python scripts/run-integration-test.py
```

### Regression Test Suite

| Test Suite | Command | Expected Time |
|-----------|---------|---------------|
| Backend unit | `pytest backend/tests/ -v` | ~30s |
| Worker unit | `pytest worker/tests/ -v` | ~10s |
| Frontend unit | `npx vitest --run` | ~20s |
| Integration | `python scripts/run-integration-test.py` | ~60s |
| Full build | `python -m build.build` | ~15min |
| Verification | (included in build) | ~5min |

---

## Long-Running Tests

| Test | Duration | Run Frequency |
|------|----------|---------------|
| Integration test (40 checks) | ~60s | Per PR |
| Full build verification | ~20min | Per release |
| Plugin sandbox breach | ~35s | Per PR |
| Path traversal suite | ~10s | Per PR |
| Rate limit exceed | ~65s | Per PR (wait for reset) |
| Worker load test | ~120s | Weekly |
