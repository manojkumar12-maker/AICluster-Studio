# AICluster API Inventory

## Master Server API (port 8000)

All endpoints are under `/api/v1/` unless otherwise noted.

### Health
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| GET | `/api/v1/health` | Server health + DB status + worker count | No | `app/api/v1/health.py` |

### Auth
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/auth/login` | Authenticate user, return JWT | No | `app/api/v1/auth.py` |

### Workers
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/workers/register` | Register a new worker | No | `app/api/v1/workers.py` |
| POST | `/api/v1/workers/heartbeat` | Worker heartbeat with metrics | No | `app/api/v1/workers.py` |
| GET | `/api/v1/workers` | List all workers | Yes | `app/api/v1/workers.py` |
| GET | `/api/v1/workers/{id}` | Get worker by ID | Yes | `app/api/v1/workers.py` |
| POST | `/api/v1/workers/{id}/pause` | Pause a worker | Yes | `app/api/v1/workers.py` |
| POST | `/api/v1/workers/{id}/resume` | Resume a paused worker | Yes | `app/api/v1/workers.py` |
| GET | `/api/v1/workers/{id}/next-job` | Get next assigned job (poll) | Yes | `app/api/v1/workers.py` |
| POST | `/api/v1/workers/{id}/progress` | Report job progress | Yes | `app/api/v1/workers.py` |
| POST | `/api/v1/workers/{id}/result` | Report job result | Yes | `app/api/v1/workers.py` |

### Jobs
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/jobs` | Create a new job | Yes | `app/api/v1/jobs.py` |
| GET | `/api/v1/jobs` | List all jobs | Yes | `app/api/v1/jobs.py` |
| GET | `/api/v1/jobs/{id}` | Get job by ID | Yes | `app/api/v1/jobs.py` |
| DELETE | `/api/v1/jobs/{id}` | Cancel a job | Yes | `app/api/v1/jobs.py` |

### Dashboard
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| GET | `/api/v1/dashboard` | Aggregated cluster statistics | Yes | `app/api/v1/dashboard.py` |

### Logs
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| GET | `/api/v1/logs` | Get system logs (filtered, paginated) | Yes | `app/api/v1/logs.py` |

### Workflows (13 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/workflow` | Create a new workflow | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow` | List workflows (filterable) | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow/{id}` | Get workflow by ID | Yes | `app/api/v1/workflows.py` |
| DELETE | `/api/v1/workflow/{id}` | Delete a workflow | Yes | `app/api/v1/workflows.py` |
| POST | `/api/v1/workflow/{id}/pause` | Pause a workflow | Yes | `app/api/v1/workflows.py` |
| POST | `/api/v1/workflow/{id}/resume` | Resume a workflow | Yes | `app/api/v1/workflows.py` |
| POST | `/api/v1/workflow/{id}/cancel` | Cancel a workflow | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow/{id}/tasks` | Get workflow tasks | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow/{id}/artifacts` | Get workflow artifacts | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow/{id}/metrics` | Get workflow metrics | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow/queue` | Get queue stats | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow/history` | Get workflow history | Yes | `app/api/v1/workflows.py` |
| GET | `/api/v1/workflow/workers/capabilities` | List worker capabilities | Yes | `app/api/v1/workflows.py` |

### Repositories (14 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/repositories` | Create/register repository | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories` | List repositories | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}` | Get repository details | Yes | `app/api/v1/repositories.py` |
| DELETE | `/api/v1/repositories/{id}` | Delete repository | Yes | `app/api/v1/repositories.py` |
| POST | `/api/v1/repositories/{id}/scan` | Scan repository | Yes | `app/api/v1/repositories.py` |
| POST | `/api/v1/repositories/{id}/rescan` | Rescan repository | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}/symbols` | Get symbols | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}/dependencies` | Get dependency graph | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}/metrics` | Get code metrics | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}/health` | Get repository health | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}/files` | List repository files | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}/file/{file_id}/metrics` | Get file metrics | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/{id}/knowledge` | Get knowledge graph | Yes | `app/api/v1/repositories.py` |
| GET | `/api/v1/repositories/search` | Full-text search | Yes | `app/api/v1/repositories.py` |

### AI Runtime (18 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/ai/chat` | Session-based chat | Yes | `app/api/v1/ai.py` |
| POST | `/api/v1/ai/chat/llm` | Direct LLM provider call | Yes | `app/api/v1/ai.py` |
| POST | `/api/v1/ai/complete` | Text completion | Yes | `app/api/v1/ai.py` |
| POST | `/api/v1/ai/session` | Create chat session | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/session` | List sessions | Yes | `app/api/v1/ai.py` |
| DELETE | `/api/v1/ai/session/{id}` | Delete session | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/session/{id}/history` | Get session history | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/models` | List AI models | Yes | `app/api/v1/ai.py` |
| POST | `/api/v1/ai/models/register` | Register a model | Yes | `app/api/v1/ai.py` |
| POST | `/api/v1/ai/models/load` | Load a model | Yes | `app/api/v1/ai.py` |
| POST | `/api/v1/ai/models/unload` | Unload a model | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/runtime` | Get runtime status | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/runtime/status` | Runtime status (alt) | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/metrics` | Get runtime metrics | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/tools` | List available tools | Yes | `app/api/v1/ai.py` |
| POST | `/api/v1/ai/tool/execute` | Execute a tool | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/context` | Get repository context | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/prompt` | Get prompt info | Yes | `app/api/v1/ai.py` |
| GET | `/api/v1/ai/providers` | List LLM providers | Yes | `app/api/v1/ai.py` |

### Agents (13 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/agents/run` | Run agents async | Yes | `app/api/v1/agents.py` |
| POST | `/api/v1/agents/run/sync` | Run agents sync | Yes | `app/api/v1/agents.py` |
| GET | `/api/v1/agents` | List agents | Yes | `app/api/v1/agents.py` |
| GET | `/api/v1/agents/{id}` | Get agent details | Yes | `app/api/v1/agents.py` |
| POST | `/api/v1/agents/register` | Register a new agent | Yes | `app/api/v1/agents.py` |
| POST | `/api/v1/agents/seed` | Seed default agents (12) | Yes | `app/api/v1/agents.py` |
| POST | `/api/v1/agents/{id}/pause` | Pause an agent | Yes | `app/api/v1/agents.py` |
| POST | `/api/v1/agents/{id}/resume` | Resume an agent | Yes | `app/api/v1/agents.py` |
| POST | `/api/v1/agents/{id}/disable` | Disable an agent | Yes | `app/api/v1/agents.py` |
| GET | `/api/v1/agents/messages` | Get agent messages | Yes | `app/api/v1/agents.py` |
| GET | `/api/v1/agents/tasks` | Get agent tasks | Yes | `app/api/v1/agents.py` |
| GET | `/api/v1/agents/memory` | Get agent memory | Yes | `app/api/v1/agents.py` |
| GET | `/api/v1/agents/metrics` | Get agent metrics | Yes | `app/api/v1/agents.py` |

### Engineering (11 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| POST | `/api/v1/engineering/plan` | Create engineering plan | Yes | `app/api/v1/engineering.py` |
| POST | `/api/v1/engineering/execute` | Execute plan | Yes | `app/api/v1/engineering.py` |
| POST | `/api/v1/engineering/validate` | Validate plan | Yes | `app/api/v1/engineering.py` |
| POST | `/api/v1/engineering/repair` | Repair task | Yes | `app/api/v1/engineering.py` |
| POST | `/api/v1/engineering/review` | Review plan | Yes | `app/api/v1/engineering.py` |
| POST | `/api/v1/engineering/document` | Update documentation | Yes | `app/api/v1/engineering.py` |
| GET | `/api/v1/engineering/tasks` | Get engineering tasks | Yes | `app/api/v1/engineering.py` |
| GET | `/api/v1/engineering/reports` | Get engineering reports | Yes | `app/api/v1/engineering.py` |
| GET | `/api/v1/engineering/metrics` | Get engineering metrics | Yes | `app/api/v1/engineering.py` |
| GET | `/api/v1/engineering/quality` | Get quality gate results | Yes | `app/api/v1/engineering.py` |
| POST | `/api/v1/engineering/approve` | Approve plan | Yes | `app/api/v1/engineering.py` |

### Production (8 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| GET | `/api/v1/production/monitoring` | Monitoring overview | Yes | `app/api/v1/production.py` |
| GET | `/api/v1/production/monitoring/system` | System metrics | Yes | `app/api/v1/production.py` |
| GET | `/api/v1/production/monitoring/cluster` | Cluster metrics | Yes | `app/api/v1/production.py` |
| GET | `/api/v1/production/health` | Health overview | Yes | `app/api/v1/production.py` |
| GET | `/api/v1/production/health/{subsystem}` | Subsystem health | Yes | `app/api/v1/production.py` |
| GET | `/api/v1/production/diagnostics` | Run diagnostics | Yes | `app/api/v1/production.py` |
| GET | `/api/v1/production/diagnostics/{check}` | Specific diagnostic | Yes | `app/api/v1/production.py` |

### Plugins (8 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| GET | `/api/v1/plugins` | List installed plugins | Yes | `app/api/v1/plugins.py` |
| POST | `/api/v1/plugins/install` | Install plugin (URL/JSON) | Yes | `app/api/v1/plugins.py` |
| POST | `/api/v1/plugins/install/upload` | Upload plugin file | Yes | `app/api/v1/plugins.py` |
| POST | `/api/v1/plugins/{id}/enable` | Enable plugin | Yes | `app/api/v1/plugins.py` |
| POST | `/api/v1/plugins/{id}/disable` | Disable plugin | Yes | `app/api/v1/plugins.py` |
| POST | `/api/v1/plugins/{id}/uninstall` | Uninstall plugin | Yes | `app/api/v1/plugins.py` |
| GET | `/api/v1/plugins/hooks` | List registered hooks | Yes | `app/api/v1/plugins.py` |
| POST | `/api/v1/plugins/hooks/{hook}/trigger` | Trigger a hook | Yes | `app/api/v1/plugins.py` |

### Studio (7 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| GET | `/api/v1/studio/workspaces` | List workspaces | Yes | `app/api/v1/studio/workspaces.py` |
| POST | `/api/v1/studio/workspaces` | Create workspace | Yes | `app/api/v1/studio/workspaces.py` |
| GET | `/api/v1/studio/workspaces/{id}` | Get workspace | Yes | `app/api/v1/studio/workspaces.py` |
| DELETE | `/api/v1/studio/workspaces/{id}` | Delete workspace | Yes | `app/api/v1/studio/workspaces.py` |
| GET | `/api/v1/studio/projects` | List projects (by workspace) | Yes | `app/api/v1/studio/projects.py` |
| POST | `/api/v1/studio/projects` | Create project | Yes | `app/api/v1/studio/projects.py` |
| DELETE | `/api/v1/studio/projects/{id}` | Delete project | Yes | `app/api/v1/studio/projects.py` |
| POST | `/api/v1/studio/bookmarks` | Add bookmark | Yes | `app/api/v1/studio/projects.py` |
| GET | `/api/v1/studio/bookmarks` | Get bookmarks | Yes | `app/api/v1/studio/projects.py` |
| GET | `/api/v1/studio/layout` | Get panel layout | Yes | `app/api/v1/studio/layout.py` |
| POST | `/api/v1/studio/layout` | Save panel layout | Yes | `app/api/v1/studio/layout.py` |
| GET | `/api/v1/studio/history` | Get action history | Yes | `app/api/v1/studio/workspaces.py` |
| POST | `/api/v1/studio/preferences` | Set preference | Yes | `app/api/v1/studio/workspaces.py` |
| GET | `/api/v1/studio/preferences/{id}` | Get preferences | Yes | `app/api/v1/studio/workspaces.py` |

### Audit (9 endpoints)
| Method | Path | Purpose | Auth | Module |
|--------|------|---------|------|--------|
| GET | `/api/v1/audit/logs` | Get audit logs (filtered) | Yes | `app/audit/api.py` |
| POST | `/api/v1/audit/search` | Search audit logs | Yes | `app/audit/api.py` |
| GET | `/api/v1/audit/statistics` | Audit statistics | Yes | `app/audit/api.py` |
| GET | `/api/v1/audit/categories` | List audit categories | Yes | `app/audit/api.py` |
| GET | `/api/v1/audit/timeline` | Audit timeline | Yes | `app/audit/api.py` |
| POST | `/api/v1/audit/export` | Export logs (CSV/JSON) | Yes | `app/audit/api.py` |
| POST | `/api/v1/audit/purge` | Purge old logs | Yes | `app/audit/api.py` |
| GET | `/api/v1/audit/settings` | Get audit settings | Yes | `app/audit/api.py` |
| POST | `/api/v1/audit/settings` | Update audit settings | Yes | `app/audit/api.py` |

---

## Master Control Center Backend API (port 8800)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/cluster/status` | Master + cluster status |
| GET | `/api/cluster/discovery` | List discovered workers |
| POST | `/api/cluster/discovery` | Scan LAN for workers |
| POST | `/api/cluster/discovery/register` | Register discovered worker |
| POST | `/api/cluster/discovery/register-all` | Register all discovered |
| GET | `/api/cluster/workers` | List all workers from master |
| POST | `/api/cluster/workers/maintenance` | Toggle maintenance mode |
| GET | `/api/cluster/health` | Cluster health metrics |
| GET | `/api/cluster/map` | Cluster topology |
| POST | `/api/cluster/backup` | Create backup ZIP |
| POST | `/api/cluster/restore` | Restore from backup |
| GET | `/api/backups` | List backups |
| GET | `/api/alerts` | List alerts |
| POST | `/api/alerts/read` | Mark alerts read |
| GET | `/api/diagnostics` | Run system diagnostics |
| GET | `/api/system/version` | System version info |
| POST | `/api/system/restart` | Request restart |
| GET | `/api/logs` | Get master logs |
| GET | `/api/workers/{id}/logs` | Get worker logs |
| GET | `/api/health` | Health check |

---

## Worker Control Center Backend API (port 8900)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/status` | Worker status + metrics |
| GET | `/api/config` | Get worker configuration |
| POST | `/api/config` | Update worker configuration |
| POST | `/api/config/reset` | Reset to default config |
| POST | `/api/start` | Start worker process |
| POST | `/api/stop` | Stop worker process |
| POST | `/api/restart` | Restart worker process |
| POST | `/api/register` | Register worker with master |
| POST | `/api/test-connection` | Test master connectivity |
| GET | `/api/logs` | Get worker logs |
| POST | `/api/logs/export` | Export logs to file |
| POST | `/api/logs/clear` | Clear log file |
| GET | `/api/system-info` | System information |
| GET | `/api/install/steps` | Installation step status |
| POST | `/api/install/run` | Run installation |
| GET | `/api/health` | Health check |

---

## WebSocket Endpoints

| Path | Purpose | Protocol |
|------|---------|----------|
| `/ws` | Real-time dashboard updates (worker, job, dashboard events) | JSON over WebSocket |

---

## Frontend API Proxy

The Next.js frontend proxies all `/api/*` requests to `http://localhost:8000` (master server) via rewrite rules in `next.config.ts`.

```
/api/* → http://localhost:8000/api/*
```

Total master API endpoints: ~140+
Total MCC backend endpoints: 20
Total WCC backend endpoints: 16
