# AICluster Vision

## Purpose

A private AI compute platform that turns idle Windows PCs on a LAN into a unified, intelligent compute cluster. No cloud, no subscriptions, no data leaving your network. Just spare CPU cycles doing real work.

---

## Core Features (v1.0)

### Web Dashboard
A single-page dashboard that shows your entire cluster at a glance. Every worker's CPU, RAM, disk, temperature, status. Live-updating every 2 seconds. Jobs flowing through the queue. Alerts when a worker goes offline. Everything you need to know in one screen, no drilling required.

### Worker Management
Workers join the cluster automatically. They register themselves, send heartbeats, and self-report their resource usage. The master detects failures in 15 seconds and marks workers offline. You can pause, resume, restart, or shut down any worker from the dashboard — or let the system do it automatically based on resource limits and office hours.

### AI Coding Assistant
A ChatGPT-like chat interface where you type a request and AICluster executes it across the cluster. "Analyze this repository" splits the work across 4 workers: backend, frontend, tests, docs. Results merge back into a single coherent answer. Supports code generation, debugging, refactoring, documentation, testing — all distributed.

### Distributed Job Execution
Any job submitted to the queue gets assigned to the most available worker automatically. Priority system ensures critical jobs run first. Failed jobs retry up to 3 times. Progress streams back in real time. The scheduler guarantees no worker exceeds 25% CPU or 8GB RAM — office workers never notice.

### Repository Intelligence
Point AICluster at a git repository and it learns the codebase. It can answer questions about architecture, find bugs, generate tests, suggest refactors, and produce documentation. The work is distributed across all available workers and the results are merged.

### Multi-Agent Development
A single high-level task — "add user authentication" — is decomposed automatically into subtasks: backend API, frontend UI, database migration, tests. Each subtask runs on a different worker in parallel. The master coordinates and merges results.

### Live Monitoring
Every metric that matters is graphed in real time: CPU across the cluster, RAM usage per worker, job throughput, execution times, queue depth. Historical trends. Exportable reports. Alerts when thresholds are breached.

### Plugin System
Extend AICluster without modifying core code. Write a plugin for a new job type, a custom analysis pipeline, a notification hook, or a deployment target. Plugins are Python packages that register themselves with the master.

---

## Non-Goals

- **Public cloud**: AICluster does not run on AWS, Azure, or GCP. It runs on your LAN.
- **Multi-tenant SaaS**: No signup pages, no billing, no org management. One cluster, one team.
- **Internet dependency**: The cluster works fully offline. The only internet dependency is for PyPI/npm installs during setup.
- **Container orchestration**: This is not Kubernetes. AICluster manages Windows processes, not Docker containers.
- **GPU compute**: v1.0 targets CPU workloads. GPU support is a future consideration.
- **macOS/Linux workers**: v1.0 targets Windows workers only. The master can run on any platform FastAPI supports.

---

## Architectural Principles

1. **Workers are invisible**: The office worker on an HP Core Ultra 7 never knows AICluster is running. No slowdowns, no popups, no interference.
2. **Master is lightweight**: Single Python process, SQLite database, no external dependencies beyond Python and Node.js.
3. **Everything is observable**: Every heartbeat, every job, every error is logged and visible in the dashboard. No black boxes.
4. **Failure is expected**: Workers go offline, jobs fail, the network lags. The system handles all of this gracefully and auto-recovers.
5. **Security by default**: JWT auth, bcrypt passwords, CORS restrictions, input validation. No open access.
6. **Scales down, not up**: Designed for 4–100 workers, not 10,000. Simplicity over complexity.

---

## Quality Bar

- **All tests pass**: pytest, integration tests, E2E tests. No regressions.
- **Zero console errors**: Frontend has no runtime errors, no React warnings, no hydration mismatches.
- **Builds clean**: `next build` and `tsc --noEmit` produce zero errors and zero warnings.
- **Responds in <200ms**: API calls return in under 200ms at p95 under normal load.
- **Dashboard updates every 2 seconds**: Real-time feels real. Workers appear and disappear within 2 heartbeats.
- **Survives worker crashes**: Master continues operating when any worker disconnects. No cascading failures.

---

## Version Roadmap

| Phase | Version | Focus |
|-------|---------|-------|
| 1 | v0.1.0 | Project structure, scaffolding |
| 2 | v0.2.0 | Master server, REST API, WebSocket, scheduler |
| 3 | v0.3.0 | Real worker service, resource limits, auto pause/resume |
| 4 | v0.4.0 | Full dashboard UI, analytics charts, file manager |
| 5 | v0.5.0 | AI chat integration, distributed code analysis |
| 6 | v0.6.0 | Repository intelligence, multi-agent orchestration |
| 7 | v0.7.0 | Plugin system, production hardening |
| 8 | v1.0.0 | Release: tested, documented, deployable |

---

*This is the north star. When in doubt, ask: does this serve the purpose of turning idle Windows PCs into a private AI compute cluster? If not, it doesn't belong in v1.0.*
