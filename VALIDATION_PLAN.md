# Validation Plan

## Per-Commit Validation

Each commit must pass the following before being merged:

### Minimum Requirements
- [ ] Code compiles (Python: `python -c "import ast; ast.parse(open(f).read())"` for each file)
- [ ] Linter passes: `ruff check` (backend), `oxlint` (frontend)
- [ ] Type check passes: `mypy --ignore-missing-imports` (backend), `tsc --noEmit` (frontend)
- [ ] Existing tests still pass
- [ ] New tests pass for the changed code
- [ ] No hardcoded secrets introduced (`grep -r "secret.*=" backend/` review)

### Sprint 1 Specific Validation

| Commit | Additional Validation |
|--------|----------------------|
| 1.1 (JWT Secret) | Delete `data/secret.key`, restart → verify new key created. Env var override works. |
| 1.2 (Admin Creds) | Fresh DB → verify password printed. Login with printed password. |
| 1.3 (Scheduler) | Create job → verify assigned. Cancel job → verify. Shutdown within 1s. |
| 1.4 (CORS) | `curl -H "Origin: http://evil.com" -I` → no `Access-Control-Allow-Origin`. |
| 1.5 (Auth) | Automated endpoint scanner: 0 unprotected endpoints. Worker endpoints accept worker secret. |
| 1.6 (Rate Limit) | Send 11 requests to `/auth/login` in 1 minute → 11th returns 429. |
| 1.7 (WS Auth) | Connect without token → close code 4001. Connect with valid token → successful. |
| 1.8 (Worker Auth) | Register without secret → 401. Register with valid secret → 200. |

### Sprint 2 Specific Validation

| Commit | Additional Validation |
|--------|----------------------|
| 2.1 (Dead Code) | `grep -r "services.executor" worker/` → no matches. |
| 2.2 (Worker Crashes) | Kill master while worker starting → worker logs "could not register" but doesn't crash. |
| 2.3 (Blocking IO) | Start dir_scan on large directory → heartbeat still arrives at expected interval. |
| 2.4 (Path Validation) | Submit job with `"directory": "../../etc/passwd"` → error returned. |
| 2.5 (SQL Injection) | Submit search with `"'; DROP TABLE jobs; --"` → error, table still exists. |

### Sprint 3 Specific Validation

| Commit | Additional Validation |
|--------|----------------------|
| 3.1 (Empty Except) | `grep -rn "except.*:.*pass" backend/ worker/` → no matches. |
| 3.2 (Plugin Sandbox) | Install plugin with `network_access: false` → cannot make HTTP requests. |
| 3.3 (HTTPS) | `curl -k https://localhost:8000/api/v1/health` → 200. |
| 3.4 (Info Disclosure) | Set `APP_ENV=production` → 500 returns generic message. |
| 3.5 (Cookie Auth) | Login → response sets `Set-Cookie: aicluster_token=...; HttpOnly`. |
| 3.6 (Frontend WS) | Dashboard receives worker_update events within 1s of worker heartbeat. |

### Sprint 4 Specific Validation

| Commit | Additional Validation |
|--------|----------------------|
| 4.1 (Dashboard) | Each page loads without console errors. API calls succeed. |
| 4.2 (Studio) | Studio loads, workspace list appears. |
| 4.3 (Tests) | `pytest backend/tests/ -v --cov=app --cov-report=term-missing` → >60% coverage. |
| 4.4 (Frontend Tests) | `npx vitest --run` → all pass. |
| 4.7 (CI/CD) | Push to PR → CI triggers. All stages green. |
| 4.8 (Release) | `python -m build.build` → all 12 stages pass. |

---

## Integration Validation Gates

### Gate 1: After Sprint 1
```
Required checks:
├── python -m build.build --skip-tauri --skip-installer --skip-sign
├── pytest backend/tests/ -v
├── pytest worker/tests/ -v
├── python scripts/run-integration-test.py
├── Manual: Endpoint security scan
│   ├── 10 public endpoints → no auth required (200)
│   ├── 50 protected endpoints → auth required (401 without)
│   ├── 5 admin endpoints → admin role required (403 for developer)
│   └── 5 worker endpoints → worker secret required (401 without)
└── All pass → Sprint 2 can start
```

### Gate 2: After Sprint 2
```
Required checks:
├── pytest backend/tests/ -v
├── pytest worker/tests/ -v
├── python scripts/run-integration-test.py
├── Manual: Worker stability
│   ├── Worker starts without master → retries, doesn't crash
│   ├── Worker executes all 5 handler types
│   ├── Path traversal attempts fail
│   └── Worker connects with secret
└── All pass → Sprint 3 can start
```

### Gate 3: After Sprint 3
```
Required checks:
├── pytest backend/tests/ -v
├── pytest worker/tests/ -v
├── python scripts/run-integration-test.py
├── Manual:
│   ├── Rate limit exceeded → 429
│   ├── Plugin sandbox test
│   ├── Cookie auth works
│   └── Dashboard receives WebSocket events
└── All pass → Sprint 4 can start
```

### Gate 4: After Sprint 4 (Release Gate)
```
Required checks:
├── python -m build.build (full build, all targets)
├── Build verification (10 stages) → ALL PASS
├── pytest backend/tests/ -v --cov=app → >60%
├── pytest worker/tests/ -v --cov=worker/app → >70%
├── npx vitest --run --coverage → >30%
├── python scripts/run-integration-test.py → 40/40 PASS
├── Manual security scan:
│   ├── No hardcoded secrets (grep check)
│   ├── All endpoints auth-gated (automated scan)
│   ├── No path traversal (attempt test)
│   └── No SQL injection (attempt test)
├── All 8 new dashboard pages load without errors
├── VERSION = 1.3.1
└── CHANGELOG.md updated
```

---

## Validation Automation

### Pre-Commit Hook Script
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Running pre-commit validation..."

# Check for hardcoded secrets
if grep -r "aicluster-secret-key" backend/app/ --include="*.py" > /dev/null 2>&1; then
    echo "ERROR: Hardcoded JWT secret found!"
    exit 1
fi

if grep -r "admin123" backend/app/services/auth.py > /dev/null 2>&1; then
    echo "ERROR: Default admin password found!"
    exit 1
fi

# Check for empty except blocks
if grep -rn "except.*:.*pass" backend/app/ worker/app/ --include="*.py" > /dev/null 2>&1; then
    echo "WARNING: Empty except blocks found"
    # Don't fail, just warn
fi

# Run linter
ruff check backend/app/ --quiet || exit 1

echo "Pre-commit checks passed."
```

### CI Validation (GitHub Actions)
```yaml
# Each job runs validation specific to its scope

lint-backend:
  steps:
    - run: ruff check backend/app/
    - run: mypy backend/app/ --ignore-missing-imports

test-backend:
  steps:
    - run: pytest backend/tests/ -v --cov=app --cov-report=xml
    - run: pytest worker/tests/ -v

test-frontend:
  steps:
    - run: npx vitest --run --coverage

security-scan:
  steps:
    - run: python scripts/security-scan.py  # Custom security scanner
```
