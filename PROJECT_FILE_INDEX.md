# AICluster Project File Index

## Overview

Total source files: ~200+ across 10+ directories
Primary languages: Python, TypeScript, Rust, CSS, HTML, PowerShell

---

## 1. Backend (`backend/`) — FastAPI Master Server

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `app/main.py` | Python | 101 | ASGI entry point, lifespan, WebSocket, routes |
| `app/config.py` | Python | 39 | Pydantic Settings from .env |
| `app/database.py` | Python | 87 | Async SQLAlchemy engine, session factory, init_db |
| `app/logging_config.py` | Python | 37 | Rotating file + console logging |
| `app/models/user.py` | Python | 24 | User ORM (id, username, password, role) |
| `app/models/worker.py` | Python | 41 | Worker ORM (status, resources, heartbeat) |
| `app/models/job.py` | Python | 40 | Job ORM (type, status, payload, result) |
| `app/models/log.py` | Python | 27 | SystemLog ORM |
| `app/models/workflow.py` | Python | 148 | Workflow DAG ORM (9 tables) |
| `app/models/repository.py` | Python | 166 | Code intelligence ORM (11 tables) |
| `app/models/ai.py` | Python | 131 | AI subsystem ORM (9 tables) |
| `app/models/agent.py` | Python | 120 | Multi-agent ORM (7 tables) |
| `app/models/engineering.py` | Python | 133 | Engineering pipeline ORM (9 tables) |
| `app/models/studio.py` | Python | 79 | Studio IDE ORM (6 tables) |
| `app/schemas/__init__.py` | Python | 124 | Pydantic request/response schemas |
| `app/services/auth.py` | Python | 98 | JWT auth with bcrypt |
| `app/services/worker_manager.py` | Python | 156 | Worker lifecycle management |
| `app/services/scheduler.py` | Python | 214 | Job queue + background scheduler loop |
| `app/services/log_service.py` | Python | 44 | System log CRUD |
| `app/api/v1/health.py` | Python | 21 | GET /api/v1/health |
| `app/api/v1/auth.py` | Python | 20 | POST /api/v1/auth/login |
| `app/api/v1/workers.py` | Python | 207 | Worker register/heartbeat/pause/resume/jobs |
| `app/api/v1/jobs.py` | Python | 81 | Job CRUD + cancel |
| `app/api/v1/logs.py` | Python | 26 | Log retrieval with filtering |
| `app/api/v1/dashboard.py` | Python | 29 | Aggregated cluster stats |
| `app/api/v1/ai.py` | Python | 325 | 18 AI endpoints (chat, sessions, models, tools) |
| `app/api/v1/agents.py` | Python | 152 | 12 agent endpoints (run, register, messages) |
| `app/api/v1/engineering.py` | Python | 214 | 11 engineering pipeline endpoints |
| `app/api/v1/production.py` | Python | 57 | 8 monitoring/health/diagnostics endpoints |
| `app/api/v1/plugins.py` | Python | 113 | 8 plugin lifecycle endpoints |
| `app/api/v1/repositories.py` | Python | 187 | 14 code intelligence endpoints |
| `app/api/v1/workflows.py` | Python | 156 | 12 workflow orchestration endpoints |
| `app/api/v1/studio/workspaces.py` | Python | 68 | Studio workspace CRUD |
| `app/api/v1/studio/projects.py` | Python | 61 | Studio project/bookmark CRUD |
| `app/api/v1/studio/layout.py` | Python | 38 | Studio layout save/load |
| `app/audit/api.py` | Python | 83 | Audit log API (9 endpoints) |
| `app/audit/events.py` | Python | 62 | AuditEvent + EventBus pub/sub |
| `app/audit/middleware.py` | Python | 67 | Request auditing middleware |
| `app/audit/models.py` | Python | 71 | Audit ORM (4 tables) |
| `app/audit/service.py` | Python | 223 | Audit service (log, search, export, purge) |
| `app/audit/middleware.py` | Python | 67 | HTTP audit middleware |
| `app/ai/context/optimizer.py` | Python | 81 | Token-aware context ranking/compression |
| `app/ai/context/service.py` | Python | 50 | Context builder for repository info |
| `app/ai/conversation/service.py` | Python | 48 | Chat message history manager |
| `app/ai/prompt/service.py` | Python | 63 | Prompt builder with templates |
| `app/ai/registry/service.py` | Python | 44 | ModelProvider registry |
| `app/ai/routing/router.py` | Python | 79 | Task-based model router (code gen, review, etc.) |
| `app/ai/sessions/service.py` | Python | 65 | Session lifecycle manager |
| `app/ai/providers/interface.py` | Python | 26 | ModelProvider ABC |
| `app/ai/providers/ollama.py` | Python | 175 | Ollama provider implementation |
| `app/ai/providers/llamacpp.py` | Python | 131 | llama.cpp provider implementation |
| `app/ai/providers/openai.py` | Python | 75 | OpenAI-compatible provider |
| `app/ai/tools/registry.py` | Python | 42 | Tool definition registry |
| `app/ai/streaming/service.py` | Python | 145 | Streaming response handler |
| `app/ai/memory/service.py` | Python | 12 | Session memory KV store |
| `app/ai/metrics/service.py` | Python | 37 | Runtime metrics collector |
| `app/agents/registry/service.py` | Python | 43 | Agent class registry |
| `app/agents/orchestrator/service.py` | Python | 115 | Agent orchestration pipeline |
| `app/agents/planner/service.py` | Python | 73 | Agent plan generation |
| `app/agents/roles/definitions.py` | Python | 35 | 12 default agent role definitions |
| `app/agents/communication/service.py` | Python | 78 | Inter-agent messaging |
| `app/agents/review/service.py` | Python | 28 | Agent review service |
| `app/agents/merge/service.py` | Python | 25 | Agent merge service |
| `app/agents/memory/service.py` | Python | 20 | Agent memory persistence |
| `app/agents/coordinator/messages.py` | Python | 30 | Agent coordinator routing |
| `app/engineering/goal/analyzer.py` | Python | 77 | Goal analysis from requirements |
| `app/engineering/planner/service.py` | Python | 68 | Engineering plan generation |
| `app/engineering/validator/service.py` | Python | 63 | Plan validation service |
| `app/engineering/repair/service.py` | Python | 39 | Auto-repair service |
| `app/engineering/quality/service.py` | Python | 39 | Quality gate checks |
| `app/engineering/documentation/service.py` | Python | 21 | Documentation generation |
| `app/engineering/risk/engine.py` | Python | 48 | Risk assessment engine |
| `app/engineering/approvals/service.py` | Python | 23 | Approval workflow |
| `app/plugins/manifest/service.py` | Python | 39 | Plugin manifest parsing/validation |
| `app/plugins/registry/service.py` | Python | 17 | Plugin instance registry |
| `app/plugins/loader/service.py` | Python | 18 | Plugin dynamic loading |
| `app/plugins/hooks/registry.py` | Python | 10 | Hook registration |
| `app/production/monitoring/service.py` | Python | 178 | Cluster monitoring service |
| `app/production/health/service.py` | Python | 58 | Health check service |
| `app/production/diagnostics/service.py` | Python | 54 | Diagnostics service |
| `app/production/audit/service.py` | Python | 8 | Production audit service |
| `app/production/benchmark/service.py` | Python | 22 | Benchmark service |
| `app/production/deployment/service.py` | Python | 8 | Deployment service |
| `app/production/security/service.py` | Python | 10 | Security scanning service |
| `app/repository/indexer/service.py` | Python | 52 | Repository indexing |
| `app/repository/scanner/service.py` | Python | 65 | File system scanner |
| `app/repository/parser/service.py` | Python | 87 | Multi-language parser |
| `app/repository/search/service.py` | Python | 62 | Full-text search service |
| `app/repository/metrics/service.py` | Python | 38 | Code metrics computation |
| `app/workflow/engine/service.py` | Python | 42 | Workflow execution engine |
| `app/workflow/planner/service.py` | Python | 32 | DAG planner |
| `app/workflow/dispatcher/service.py` | Python | 30 | Task dispatcher |
| `app/workflow/executor/service.py` | Python | 28 | Task executor |
| `app/workflow/artifacts/service.py` | Python | 26 | Artifact store manager |
| `app/workflow/cache/service.py` | Python | 20 | Workflow result cache |
| `app/workflow/state/service.py` | Python | 27 | Workflow state machine |
| `app/workflow/metrics/service.py` | Python | 36 | Workflow metrics |
| `app/websocket/manager.py` | Python | 51 | WebSocket connection manager |
| `static/dashboard.html` | HTML | - | Single-page dashboard UI |

## 2. Worker (`worker/`) — Distributed Worker Agent

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `app/main.py` | Python | 211 | Entry point, state machine, job orchestration |
| `app/config.py` | Python | 52 | Layered config (JSON + .env + defaults) |
| `app/core/constants.py` | Python | 18 | Timeouts, retry delays, version |
| `app/core/state.py` | Python | 21 | 21-state enum (STARTING to EXIT) |
| `app/logging/setup.py` | Python | 63 | Structured logging with adapter |
| `app/utils/http_client.py` | Python | 23 | Async HTTP wrapper for master API |
| `app/utils/retry.py` | Python | 30 | Exponential backoff retry |
| `app/services/registrar.py` | Python | 60 | Worker registration protocol |
| `app/services/heartbeat.py` | Python | 74 | Periodic resource reporting |
| `app/services/poller.py` | Python | 69 | Long-poll job retrieval |
| `app/services/reporter.py` | Python | 91 | Progress/result reporting |
| `app/services/monitor.py` | Python | 71 | System resource collection (psutil) |
| `app/services/executor.py` | Python | 88 | Legacy job executor (unused) |
| `app/executor/base.py` | Python | 10 | BaseJobHandler ABC |
| `app/executor/registry.py` | Python | 21 | Job type -> handler mapping |
| `app/executor/handlers/echo.py` | Python | 10 | Echo payload back |
| `app/executor/handlers/sleep.py` | Python | 14 | Async sleep (test handler) |
| `app/executor/handlers/dir_scan.py` | Python | 40 | Directory tree walk |
| `app/executor/handlers/hash_file.py` | Python | 34 | File hash computation |
| `app/executor/handlers/count_files.py` | Python | 37 | File count with filter |
| `scripts/run.py` | Python | 9 | PyInstaller entry wrapper |
| `tests/test_config.py` | Python | 30 | Config unit tests |
| `tests/test_executor.py` | Python | 56 | Handler + registry tests |
| `tests/test_reconnect.py` | Python | 39 | RetryHandler tests |
| `tests/test_registrar.py` | Python | 24 | Registration tests |

## 3. Frontend (`frontend/`) — Next.js 15 Dashboard

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `src/app/layout.tsx` | TSX | 36 | Root layout, providers |
| `src/app/page.tsx` | TSX | 19 | Auth-based redirect |
| `src/app/login/page.tsx` | TSX | 116 | Login form |
| `src/app/error.tsx` | TSX | 22 | Error boundary |
| `src/app/not-found.tsx` | TSX | 16 | 404 page |
| `src/app/(dashboard)/layout.tsx` | TSX | 49 | Dashboard shell (sidebar + topbar) |
| `src/app/(dashboard)/dashboard/page.tsx` | TSX | 183 | Cluster metrics dashboard |
| `src/app/(dashboard)/workers/page.tsx` | TSX | 125 | Worker cards grid |
| `src/app/(dashboard)/jobs/page.tsx` | TSX | 18 | Placeholder |
| `src/app/(dashboard)/analytics/page.tsx` | TSX | 18 | Placeholder |
| `src/app/(dashboard)/chat/page.tsx` | TSX | 18 | Placeholder |
| `src/app/(dashboard)/files/page.tsx` | TSX | 18 | Placeholder |
| `src/app/(dashboard)/logs/page.tsx` | TSX | 18 | Placeholder |
| `src/app/(dashboard)/projects/page.tsx` | TSX | 18 | Placeholder |
| `src/app/(dashboard)/settings/page.tsx` | TSX | 18 | Placeholder |
| `src/app/(dashboard)/about/page.tsx` | TSX | 31 | App info |
| `src/components/layout/sidebar.tsx` | TSX | 73 | Navigation sidebar |
| `src/components/layout/topbar.tsx` | TSX | 54 | Search, notifications, user menu |
| `src/components/layout/query-provider.tsx` | TSX | 23 | TanStack React Query provider |
| `src/components/layout/theme-provider.tsx` | TSX | 11 | next-themes wrapper |
| `src/stores/auth-store.ts` | TS | 53 | Zustand auth store (persisted) |
| `src/types/index.ts` | TS | 211 | TypeScript interfaces + enums |
| `src/lib/utils.ts` | TS | 55 | Utility functions |
| `src/app/globals.css` | CSS | 169 | Global styles + dark theme |

## 4. Studio (`studio/`) — Tauri v2 Desktop IDE

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `src/main.tsx` | TSX | 10 | Vite entry point |
| `src/App.tsx` | TSX | 122 | Root component (starter template) |
| `src/index.css` | CSS | 111 | Global styles |
| `src/App.css` | CSS | 184 | Component styles |
| `src-tauri/src/main.rs` | Rust | 3 | Binary entry |
| `src-tauri/src/lib.rs` | Rust | 7 | Tauri builder setup |
| `src-tauri/Cargo.toml` | TOML | 23 | Rust manifest |
| `src-tauri/tauri.conf.json` | JSON | 42 | Tauri config (NSIS, window) |

## 5. Master Control Center (`master-control-center/`)

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `backend/app/main.py` | Python | 38 | FastAPI entry point |
| `backend/app/api/router.py` | Python | 444 | 19 REST endpoints |
| `frontend/src/App.tsx` | TSX | 43 | Root component + page routing |
| `frontend/src/App.css` | CSS | 184 | Vite template styles |
| `frontend/src/index.css` | CSS | 27 | Dark theme global styles |
| `frontend/src/lib/api.ts` | TS | 32 | API client (16 endpoints) |
| `frontend/src/stores/app-store.ts` | TS | 15 | Zustand page/sidebar state |
| `frontend/src/components/layout/Sidebar.tsx` | TSX | 46 | 11-item nav sidebar |
| `frontend/src/pages/Dashboard.tsx` | TSX | 54 | Cluster status overview |
| `frontend/src/pages/Workers.tsx` | TSX | 40 | Worker card grid |
| `frontend/src/pages/Cluster.tsx` | TSX | 45 | Topology map |
| `frontend/src/pages/Discovery.tsx` | TSX | 46 | LAN scan + register |
| `frontend/src/pages/Jobs.tsx` | TSX | 20 | Job summary |
| `frontend/src/pages/Backups.tsx` | TSX | 35 | Backup management |
| `frontend/src/pages/Diagnostics.tsx` | TSX | 26 | System health checks |
| `frontend/src/pages/Notifications.tsx` | TSX | 28 | Alerts view |
| `frontend/src/pages/Logs.tsx` | TSX | 30 | Log viewer |
| `frontend/src/pages/Settings.tsx` | TSX | 26 | Settings (static) |
| `frontend/src/pages/About.tsx` | TSX | 19 | App info |
| `frontend/src-tauri/src/main.rs` | Rust | 3 | Binary entry |
| `frontend/src-tauri/src/lib.rs` | Rust | 7 | Tauri builder |

## 6. Worker Control Center (`worker-control-center/`)

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `backend/app/main.py` | Python | 51 | FastAPI entry + worker process mgmt |
| `backend/app/api/router.py` | Python | 453 | 16 REST endpoints |
| `backend/app/schemas/__init__.py` | Python | 99 | 10 Pydantic schemas |
| `frontend/src/App.tsx` | TSX | 69 | Root + routing + health polling |
| `frontend/src/index.css` | CSS | 57 | Dark theme + utility classes |
| `frontend/src/lib/api.ts` | TS | 111 | Typed API client (17 methods) |
| `frontend/src/stores/app-store.ts` | TS | 19 | Zustand state |
| `frontend/src/components/layout/Sidebar.tsx` | TSX | 52 | 8-item nav sidebar |
| `frontend/src/pages/Welcome.tsx` | TSX | 36 | Welcome screen |
| `frontend/src/pages/Installation.tsx` | TSX | 112 | Multi-step install wizard |
| `frontend/src/pages/Configuration.tsx` | TSX | 98 | Config editor |
| `frontend/src/pages/ConnectionTest.tsx` | TSX | 86 | Master connectivity test |
| `frontend/src/pages/Dashboard.tsx` | TSX | 120 | Live worker monitoring |
| `frontend/src/pages/Logs.tsx` | TSX | 75 | Log viewer |
| `frontend/src/pages/Diagnostics.tsx` | TSX | 71 | System health |
| `frontend/src/pages/Settings.tsx` | TSX | 44 | App preferences |
| `frontend/src/pages/About.tsx` | TSX | 37 | App info |
| `frontend/src-tauri/src/main.rs` | Rust | 3 | Binary entry |
| `frontend/src-tauri/src/lib.rs` | Rust | 7 | Tauri builder |

## 7. Shared (`shared/`) — Cross-Component Contracts

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `protocol/registration.py` | Python | 11 | RegisterRequest/Response |
| `protocol/heartbeat.py` | Python | 17 | HeartbeatRequest/Response |
| `protocol/jobs.py` | Python | 37 | Job lifecycle DTOs |
| `protocol/errors.py` | Python | 7 | ErrorResponse |
| `py/models.py` | Python | 68 | Enums (WorkerStatus, JobStatus, etc.) + WorkerInfo |
| `py/schemas.py` | Python | 192 | 18 Pydantic API schemas |
| `ts/types.ts` | TS | 215 | 5 enums + 16 interfaces mirroring Python |

## 8. Build System (`build/`)

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `build.py` | Python | 431 | Master orchestrator (12 stages) |
| `config.py` | Python | 273 | Central config + target definitions |
| `frontend.py` | Python | 139 | npm build orchestration |
| `pyinstaller_builder.py` | Python | 402 | PyInstaller spec + build |
| `tauri_builder.py` | Python | 389 | Tauri v2 build |
| `package.py` | Python | 188 | ZIP + checksums + manifest |
| `release.py` | Python | 469 | Installer scripts + release notes |
| `setup_builder.py` | Python | 401 | AIClusterSetup.exe builder |
| `setup_validator.py` | Python | 205 | setup.iss validator |
| `sign.py` | Python | 100 | Authenticode signing |
| `checksum.py` | Python | 104 | SHA-256/MD5/SHA-1 generation |
| `clean.py` | Python | 120 | Artifact cleanup |
| `version.py` | Python | 180 | Version discovery + VSVersionInfo |
| `toolchain.py` | Python | 281 | Tool detection (10 tools) |
| `verify.py` | Python | 257 | Environment + artifact verification |
| `logger.py` | Python | 63 | Build logging |
| `setup/setup.iss` | Inno | 595 | Master installer script (Pascal) |
| `modules/cli_entry.py` | Python | 81 | CLI entry point |
| `modules/master_entry.py` | Python | 44 | Master bootstrap |
| `modules/worker_entry.py` | Python | 25 | Worker bootstrap |
| `modules/make_default_icon.py` | Python | 65 | Programmatic ICO generation |
| `verification/verify.py` | Python | 183 | 10-stage orchestrator |
| `verification/verify_build.py` | Python | 160 | Build output check |
| `verification/verify_executables.py` | Python | 221 | PE validation |
| `verification/verify_artifacts.py` | Python | 130 | Release folder layout |
| `verification/verify_config.py` | Python | 193 | Config file check |
| `verification/verify_python.py` | Python | 98 | Python runtime check |
| `verification/verify_frontend.py` | Python | 307 | Frontend + Tauri smoke tests |
| `verification/verify_checksums.py` | Python | 183 | Checksum regeneration |
| `verification/verify_installer.py` | Python | 227 | Installer validation |
| `verification/verify_backend.py` | Python | 281 | Launch + health tests |
| `verification/verify_api.py` | Python | 79 | Live HTTP API probes |
| `verification/utils.py` | Python | 404 | Shared helpers |
| `verification/context.py` | Python | 141 | Tunables + paths |
| `verification/verify_report.py` | Python | 317 | Result dataclasses + rendering |

## 9. Scripts (`scripts/`)

| File | Lang | Lines | Purpose |
|------|------|-------|---------|
| `setup.ps1` | PS | ~60 | Global environment setup |
| `install-master.ps1` | PS | ~35 | Master server installer |
| `install-worker.ps1` | PS | ~30 | Worker node installer |
| `start-master.ps1` | PS | ~60 | Start backend + frontend |
| `start-worker.ps1` | PS | ~25 | Start worker process |
| `run-integration-test.py` | Python | ~300 | 40-test integration suite |
| `worker-simulator.py` | Python | ~600 | Interactive 4-worker TUI simulator |

## 10. Config (`config/`)

| File | Lines | Purpose |
|------|-------|---------|
| `default.yaml` | ~40 | Base config (DB, auth, worker, scheduler, monitoring) |
| `development.yaml` | ~10 | Dev overrides (debug, CORS, log level) |
| `production.yaml` | ~12 | Production overrides (hardened) |

## 11. Tests

| Location | Files | Tests | Coverage |
|----------|-------|-------|----------|
| `backend/tests/` | ~44 | pytest | Auth, workers, jobs, dashboard, health |
| `worker/tests/` | 4 files | 14 tests | Config, executor, reconnect, registrar |
| `scripts/run-integration-test.py` | 1 file | 40 tests | End-to-end cluster simulation |
