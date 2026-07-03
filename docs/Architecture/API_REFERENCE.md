# AICluster API Reference

Base URL: `http://localhost:8000/api/v1`

Authentication: `Authorization: Bearer <jwt_token>`

---

## Authentication

### POST /auth/login

Authenticate a user and receive a JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:** 401 Invalid credentials, 422 Validation error (missing/invalid fields)

---

## Workers

### POST /workers/register

Register a new worker node. No auth required (workers register autonomously).

**Request:**
```json
{
  "name": "HP-01",
  "hostname": "HP-01",
  "ip": "192.168.1.50"
}
```

**Response (200):**
```json
{
  "id": "dd86404c-1234-5678-9abc-def012345678"
}
```

**Errors:** 422 Validation error (name min 1 char, ip max 45 chars)

---

### POST /workers/heartbeat

Receive worker heartbeat with current metrics. No auth required.

**Request:**
```json
{
  "id": "dd86404c-...",
  "cpu": 18.5,
  "ram": 24.1,
  "disk": 41.3,
  "temperature": 52.0,
  "busy": false,
  "network_speed": 100.0
}
```

**Response (200):**
```json
{
  "status": "ok"
}
```

**Errors:** 404 Worker not found, 422 Validation error (cpu/ram/disk 0-100 range, id required)

### GET /workers

List all registered workers.

**Response (200):**
```json
[
  {
    "id": "dd86404c-...",
    "worker_name": "HP-01",
    "hostname": "HP-01",
    "ip": "192.168.1.50",
    "status": "online",
    "cpu_percent": 12.3,
    "ram_percent": 24.1,
    "disk_percent": 41.3,
    "temperature": 52.0,
    "network_speed": 100.0,
    "current_job": null,
    "version": "1.0.0",
    "cpu_limit": 25.0,
    "ram_limit": 8.0,
    "priority": 0,
    "is_paused": false,
    "last_seen": "2026-07-02T00:12:00",
    "registered_at": "2026-07-02T00:10:00"
  }
]
```

### GET /workers/{id}

Get a specific worker by ID.

**Errors:** 404 Worker not found

### POST /workers/{id}/pause

Pause a worker. Prevents job assignment.

**Response (200):** `{"status": "paused", "worker_id": "..."}`

### POST /workers/{id}/resume

Resume a paused worker.

**Response (200):** `{"status": "resumed", "worker_id": "..."}`

### GET /workers/{id}/next-job

Poll for the next available job. Used by worker agents.

**Response (200):**
```json
{
  "job": {
    "id": "fd5d18c8-...",
    "type": "echo",
    "status": "running",
    "assigned_worker": "dd86404c-...",
    "progress": 0.0,
    "priority": 2,
    "payload": {},
    "created_at": "2026-07-03T00:00:00",
    "started_at": "2026-07-03T00:00:00"
  }
}
```

**Response (204):** No job available

**Errors:** 404 Worker not found, 429 Worker is paused

### POST /workers/{id}/progress

Report job progress from worker to master.

**Request:**
```json
{
  "job_id": "fd5d18c8-...",
  "progress": 50.0,
  "logs": "Processing file 5 of 10..."
}
```

**Response (200):** `{"status": "ok"}`

**Errors:** 404 Worker not found

### POST /workers/{id}/result

Report job result from worker to master.

**Request:**
```json
{
  "job_id": "fd5d18c8-...",
  "status": "completed",
  "result": {"output": "success"},
  "duration_ms": 1234.5
}
```

**Response (200):** `{"status": "ok"}`

**Errors:** 404 Worker/job not found

---

## Dashboard

### GET /dashboard

Get aggregated cluster metrics.

**Response (200):**
```json
{
  "total_workers": 4,
  "online": 3,
  "offline": 0,
  "idle": 2,
  "busy": 1,
  "average_cpu": 12.2,
  "average_ram": 21.4,
  "running_jobs": 0
}
```

---

## Jobs

### POST /jobs

Create a new job in the queue.

**Request:**
```json
{
  "type": "code_analysis",
  "payload": {"repo": "/path/to/repo"},
  "priority": 2
}
```

**Response (200):**
```json
{
  "id": "fd5d18c8-...",
  "type": "code_analysis",
  "status": "queued",
  "assigned_worker": null,
  "progress": 0.0,
  "priority": 2,
  "error": null,
  "created_at": "2026-07-02T00:12:00",
  "started_at": null,
  "finished_at": null
}
```

### GET /jobs

List all jobs, ordered by creation date descending.

**Response (200):** Array of job objects.

### GET /jobs/{id}

Get a specific job by ID.

**Errors:** 404 Job not found

### DELETE /jobs/{id}

Cancel a queued or running job.

**Response (200):** `{"status": "cancelled", "job_id": "..."}`

**Errors:** 404 not found, 400 already finished

---

## Health

### GET /health

Server health check. No auth required.

**Response (200):**
```json
{
  "status": "ok",
  "database": "connected",
  "worker_count": 4,
  "version": "1.0.0"
}
```

---

## Logs

### GET /logs

Retrieve system logs. Supports filtering.

**Query Parameters:**
- `level` — Filter by log level (INFO, WARNING, ERROR)
- `limit` — Max entries to return (default: 100, max: 500)
- `offset` — Pagination offset

**Response (200):**
```json
[
  {
    "id": "uuid",
    "level": "INFO",
    "message": "Worker 'HP-01' registered from 192.168.1.50",
    "source": "worker_manager",
    "created_at": "2026-07-02T00:10:00"
  }
]
```

---

## WebSocket

### WS /ws

Connect to receive real-time updates.

**Messages received:**
```json
{"type": "worker_update", "data": {"id": "...", "status": "online", ...}}
{"type": "job_update", "data": {"id": "...", "status": "running", ...}}
{"type": "dashboard", "data": {"total_workers": 4, "online": 3, ...}}
```

---

## OpenAPI Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
