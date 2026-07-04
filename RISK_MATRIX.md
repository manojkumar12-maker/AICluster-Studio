# AICluster v1.3.1 Risk Matrix

| # | Issue | Probability | Impact | Priority | Owner | Rollback | Testing Required |
|---|-------|-------------|--------|----------|-------|----------|------------------|
| S-001 | JWT Secret Hardcoded | 100% | CRITICAL | P0 | Security | Revert config.py, delete secret.key | Validate key generation, persistence, override |
| S-002 | Default Admin Credentials | 100% | CRITICAL | P0 | Security | Revert auth.py | Validate password generated, login works |
| S-003 | No Auth Enforcement | 100% | CRITICAL | P0 | Security | Remove Depends from routes | Every endpoint tested with/without auth |
| S-004 | Plugin Upload RCE | 80% | CRITICAL | P0 | Security | Revert plugin loader | Plugin sandbox bypass tested |
| S-005 | CORS Misconfiguration | 100% | HIGH | P1 | Security | Revert main.py CORS | Cross-origin requests validated |
| S-006 | Path Traversal | 60% | HIGH | P1 | Worker | Revert handler validation | Traversal attempts tested |
| S-007 | No Rate Limiting | 100% | HIGH | P1 | Backend | Remove rate limiter middleware | Rate limit exceeded tested |
| S-008 | WebSocket Without Auth | 100% | HIGH | P1 | Backend | Revert WS auth check | Invalid token rejected |
| S-009 | Worker Registration Without Auth | 100% | HIGH | P1 | Worker | Remove worker_secret validation | Registration with/without secret |
| S-010 | No HTTPS | 100% | HIGH | P2 | Backend | Remove TLS config | HTTPS connection works |
| S-011 | JWT in localStorage | 100% | MEDIUM | P2 | Frontend | Revert cookie auth | Cookie set/read correctly |
| S-012 | SQL Injection Risk | 40% | HIGH | P1 | Backend | Revert search validation | SQL injection attempts fail |
| S-013 | Info Disclosure | 80% | MEDIUM | P2 | Backend | Revert error handler | Production errors are generic |
| C-001 | Dead Code (executor.py) | 100% | MEDIUM | P2 | Worker | Restore deleted file | Worker works without it |
| C-002 | execute_with_progress Missing | 100% | HIGH | P1 | Worker | Keep or remove branch | All handlers execute correctly |
| C-003 | reporter Called on None | 100% | HIGH | P1 | Worker | Use no-op reporter | Early worker failures handled |
| C-004 | poll() Type Handling | 40% | MEDIUM | P2 | Worker | Remove type check | Various poll responses work |
| C-005 | Double Commit | 100% | HIGH | P1 | Backend | Restore original code | Job assignment succeeds |
| C-006 | duration_ms Not Stored | 100% | MEDIUM | P2 | Backend | Revert complete_job | Duration persisted correctly |
| C-007 | Blocking IO in Async | 100% | HIGH | P1 | Worker | Revert to synchronous | Event loop not blocked |
| C-008 | Scheduler Not Stoppable | 60% | MEDIUM | P2 | Backend | Revert scheduler | Scheduler stops promptly |
| C-009 | Empty Except Blocks | 80% | MEDIUM | P3 | Backend | Manual per-file revert | Errors are logged |
| C-010 | Duplicate IP Logic | 100% | LOW | P4 | Worker | Revert dedup | IP resolution works |
| F-001 | Dashboard Placeholders | 100% | MEDIUM | P3 | Frontend | Revert page changes | Pages render with data |
| F-002 | Studio Starter Template | 100% | LOW | P4 | Studio | Revert App.tsx | Studio loads without errors |
| F-003 | Frontend No WebSocket | 100% | MEDIUM | P3 | Frontend | Revert WS code, keep polling | Dashboard updates work |
| T-001 | No Subsystem Tests | 100% | HIGH | P3 | QA | N/A (additive) | Tests pass |
| T-002 | No Auth Integration Tests | 100% | HIGH | P3 | QA | N/A (additive) | Tests pass |
| T-003 | No Frontend Tests | 100% | MEDIUM | P3 | QA | N/A (additive) | Tests pass |
| B-001 | Binary Size | 100% | LOW | P4 | Build | Revert build config | All verification passes |
| B-002 | No CI/CD | 100% | MEDIUM | P4 | DevOps | Remove workflow file | CI passes |

## Risk Legend

- **Probability**: Likelihood the issue causes a problem in production
- **Impact**: Severity if exploited/manifested
- **Priority**: P0=Immediate, P1=This sprint, P2=Next sprint, P3=This release, P4=Future
- **Rollback**: How to undo the change
