# API Change Matrix

## Overview

v1.3.1 introduces authentication requirements to every API endpoint. This is the single largest API change in the release. All other changes are internal and do not affect the API contract.

---

## Authentication Changes

| Endpoint | Before | After | Auth Type |
|----------|--------|-------|-----------|
| `GET /api/v1/health` | Public | Public (unchanged) | None |
| `POST /api/v1/auth/login` | Public | Public (unchanged) | None |
| `GET /docs` | Public | Public (unchanged) | None |
| `GET /openapi.json` | Public | Public (unchanged) | None |
| `GET /redoc` | Public | Public (unchanged) | None |
| `GET /` | Public | Public (unchanged) | None |
| `GET /static/*` | Public | Public (unchanged) | None |
| `POST /api/v1/auth/*` (other) | Public | JWT Required | Bearer Token |
| `POST /api/v1/workers/register` | Public | Worker Secret | Bearer (worker_secret) |
| `POST /api/v1/workers/heartbeat` | Public | Worker Secret | Bearer (worker_secret) |
| `POST /api/v1/workers/{id}/progress` | Public | Worker Secret | Bearer (worker_secret) |
| `POST /api/v1/workers/{id}/result` | Public | Worker Secret | Bearer (worker_secret) |
| `GET /api/v1/workers/{id}/next-job` | Public | Worker Secret | Bearer (worker_secret) |
| `GET /api/v1/workers` | Public | JWT Required | Bearer Token |
| `GET /api/v1/workers/{id}` | Public | JWT Required | Bearer Token |
| `POST /api/v1/workers/{id}/pause` | Public | JWT + Admin | Bearer Token |
| `POST /api/v1/workers/{id}/resume` | Public | JWT + Admin | Bearer Token |
| `POST /api/v1/jobs*` | Public | JWT Required | Bearer Token |
| `GET /api/v1/dashboard` | Public | JWT Required | Bearer Token |
| `GET /api/v1/logs` | Public | JWT Required | Bearer Token |
| `POST /api/v1/workflow*` | Public | JWT + Admin | Bearer Token |
| `GET /api/v1/workflow*` | Public | JWT Required | Bearer Token |
| `POST /api/v1/repositories*` | Public | JWT Required | Bearer Token |
| `GET /api/v1/repositories*` | Public | JWT Required | Bearer Token |
| `DELETE /api/v1/repositories*` | Public | JWT Required | Bearer Token |
| `POST /api/v1/ai/*` | Public | JWT Required | Bearer Token |
| `GET /api/v1/ai/*` | Public | JWT Required | Bearer Token |
| `POST /api/v1/agents*` | Public | JWT + Admin | Bearer Token |
| `GET /api/v1/agents*` | Public | JWT Required | Bearer Token |
| `POST /api/v1/engineering*` | Public | JWT + Admin | Bearer Token |
| `GET /api/v1/engineering*` | Public | JWT Required | Bearer Token |
| `GET /api/v1/production*` | Public | JWT + Admin | Bearer Token |
| `POST /api/v1/plugins*` | Public | JWT + Admin | Bearer Token |
| `GET /api/v1/plugins*` | Public | JWT Required | Bearer Token |
| `POST /api/v1/studio/workspaces` | Public | JWT Required | Bearer Token |
| `GET /api/v1/studio/workspaces` | Public | JWT Required | Bearer Token |
| `GET /api/v1/studio/workspaces/{id}` | Public | JWT Required | Bearer Token |
| `DELETE /api/v1/studio/workspaces/{id}` | Public | JWT Required | Bearer Token |
| `GET /api/v1/studio/projects` | Public | JWT Required | Bearer Token |
| `POST /api/v1/studio/projects` | Public | JWT Required | Bearer Token |
| `DELETE /api/v1/studio/projects/{id}` | Public | JWT Required | Bearer Token |
| `POST /api/v1/studio/bookmarks` | Public | JWT Required | Bearer Token |
| `GET /api/v1/studio/bookmarks` | Public | JWT Required | Bearer Token |
| `GET /api/v1/studio/layout` | Public | JWT Required | Bearer Token |
| `POST /api/v1/studio/layout` | Public | JWT Required | Bearer Token |
| `GET /api/v1/studio/history` | Public | JWT Required | Bearer Token |
| `POST /api/v1/studio/preferences` | Public | JWT Required | Bearer Token |
| `GET /api/v1/studio/preferences/{id}` | Public | JWT Required | Bearer Token |
| `GET /api/v1/audit/*` | Public | JWT + Admin | Bearer Token |
| `POST /api/v1/audit/*` | Public | JWT + Admin | Bearer Token |
| `WS /ws` | Public | JWT Required | Query param `?token=` |

---

## New Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/api/v1/auth/login-cookie` | Login returning httpOnly cookie + CSRF token | Public |
| POST | `/api/v1/auth/csrf` | Get CSRF token (requires cookie) | Cookie |
| POST | `/api/v1/auth/logout` | Clear auth cookie | JWT or Cookie |

---

## Response Changes

### Rate Limiting (S-007)
| Change | Detail |
|--------|--------|
| New status code | `429 Too Many Requests` |
| Response header | `Retry-After: <seconds>` |
| Response body | `{"detail": "Rate limit exceeded", "retry_after": <seconds>}` |

### Authentication Errors (S-003)
| Change | Detail |
|--------|--------|
| `401 Unauthorized` | Returned when: no token, invalid token, expired token |
| Response body | `{"detail": "Not authenticated"}` or `{"detail": "Invalid token"}` |
| `403 Forbidden` | Returned when: valid token but insufficient role |
| Response body | `{"detail": "Insufficient permissions"}` |

### Generic Errors (S-013)
| Environment | 500 Error Response |
|-------------|-------------------|
| Development | Full traceback (unchanged) |
| Production | `{"detail": "Internal server error"}` |

### Pagination (Performance)
| Change | Endpoints |
|--------|-----------|
| New query params | `?limit=N&offset=N` on all list endpoints |
| Default limit | 50 |
| Max limit | 500 |
| Response header | `X-Total-Count: <count>` |
| Response wrapper | `{"items": [...], "total": N, "page": N, "page_size": N}` |

---

## Backward Compatibility

| Change | Breaking? | Mitigation |
|--------|-----------|------------|
| Auth required on all endpoints | **YES** — existing clients without auth break | All clients must add `Authorization: Bearer <token>` header |
| Worker auth required | **YES** — existing workers without secret rejected | Workers must have `worker_secret` in config |
| WS auth required | **YES** — existing WS clients without token rejected | Clients must include `?token=<jwt>` in WS URL |
| Pagination response wrapper | **YES** — list endpoints return wrapped response | Clients must handle `items` wrapper |
| CORS restriction | **MAYBE** — non-localhost clients blocked | Clients must be on allowed origin list |
| Rate limiting | **NO** — existing usage within limits | No action needed |
| Error message changes | **NO** — production only | Development mode unchanged |
| Duration in response | **NO** — additive field | Optional field, ignored by existing clients |

### Client Migration Path
1. Frontend: login → store JWT → include in all requests (already done for dashboard/workers)
2. Workers: configure `worker_secret` in `config.json`
3. Studio: login → store JWT → include in API calls
4. MCC/WCC: login → store JWT → include in proxy calls to master

---

## OpenAPI/Swagger Updates

- Add security scheme: `BearerAuth` (JWT)
- Add security scheme: `WorkerBearerAuth` (worker secret)
- Tag all endpoints with required security
- Public endpoints tagged with `security: []`
- Rate limit 429 response documented
- Pagination parameters documented
- Role requirements documented

---

## WebSocket Protocol

| Change | Detail |
|--------|--------|
| Connection | `ws://host:8000/ws?token=<jwt>` |
| Rejection | Close code `4001` with reason "Authentication required" |
| Periodic auth | Server may request re-auth after token expiry |
| Supported token types | JWT (users), worker_secret (workers) |
