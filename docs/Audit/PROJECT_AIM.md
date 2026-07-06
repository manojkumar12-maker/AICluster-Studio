# PROJECT AIM â€” AICluster

## 1. Executive Summary

AICluster is a private, offline-first AI compute platform that transforms idle Windows PCs on a local network into a unified, intelligent compute cluster. It enables distributed AI workloads â€” code analysis, repository intelligence, multi-agent software engineering, workflow orchestration, and LLM-powered assistance â€” entirely within a LAN environment, with no cloud dependency, no subscriptions, and no data leaving the network.

The project is currently at version 1.3.0, having progressed through 11 development phases from initial scaffolding (v0.1.0) through to a production-ready platform with a comprehensive audit system, Studio IDE, plugin system, AI runtime, repository intelligence, and multi-agent orchestration.

## 2. Core Purpose

AICluster exists to solve a specific, practical problem: modern organizations have dozens or hundreds of Windows workstations sitting idle for significant portions of the day. These machines collectively represent substantial compute capacity â€” CPU cycles, RAM, and disk â€” that is entirely wasted. Simultaneously, these same organizations increasingly need AI compute for code analysis, documentation generation, bug detection, and software engineering automation.

The central insight is that these two problems are complementary: the idle compute capacity of office workstations can be harnessed to run AI workloads, provided the solution respects the primary user's experience (no slowdowns, no interference) and operates entirely within the organization's network (no data exfiltration, no cloud dependency).

## 3. Vision

The long-term vision of AICluster is to become the standard private AI compute layer for every organization that develops software. AICluster aims to provide:

**A unified AI compute fabric** spanning all Windows workstations in an organization, automatically discovered, self-registering, and self-healing. Workers join the cluster, report their capabilities, execute tasks, and disappear gracefully when their human user needs the machine.

**An autonomous software engineering platform** that can accept high-level natural language goals ("add user authentication", "refactor the payment module", "generate API documentation") and decompose them into parallel tasks executed by specialized AI agents across the distributed worker fleet.

**A local-first AI development environment** where every component â€” the LLM inference, the repository analysis, the workflow engine, the agent communication â€” runs on local hardware using local models. No internet connection required after initial setup.

**An extensible platform** where plugins can add new job types, analysis pipelines, notification hooks, deployment targets, and LLM providers without modifying core code.

## 4. Design Philosophy

### 4.1 Offline-First Philosophy

AICluster is designed from the ground up to operate without internet connectivity. This is not an afterthought or a feature toggle â€” it is a fundamental architectural constraint. Every subsystem must function fully offline:

- **Database**: SQLite, no external database server required
- **LLM Inference**: Local providers only (Ollama, llama.cpp, OpenAI-compatible local endpoints)
- **Repository Intelligence**: Local scanning, parsing, and indexing â€” no GitHub API dependency
- **Agent Communication**: In-process message passing via database, no external message broker
- **Plugin System**: Local file-based discovery and loading, no package registry dependency
- **Authentication**: Local JWT with bcrypt, no OAuth provider dependency

The only internet dependencies are during initial setup (pip install, npm install) and optional model downloads. Once configured, AICluster runs fully disconnected.

**Why offline-first matters**: Enterprise software development involves proprietary source code, internal architecture discussions, and sensitive business logic. Sending this data to cloud APIs is unacceptable for many organizations. AICluster eliminates this concern entirely â€” the code never leaves the LAN.

### 4.2 Why Distributed Computing

Modern codebases are too large for single-machine analysis. A 500,000-line monorepo with dozens of microservices requires significant compute for parsing, indexing, dependency analysis, and AI-powered code generation. Distributing this work across multiple machines provides:

- **Parallel execution**: Repository scanning, symbol parsing, and test execution can be parallelized across workers
- **Resource isolation**: Heavy AI workloads run on worker machines, not the developer's primary workstation
- **Horizontal scaling**: Adding compute capacity means adding more worker machines, not upgrading hardware
- **Fault tolerance**: If one worker goes offline (user leaves, machine sleeps), other workers continue processing

The architecture targets 4-100 worker nodes â€” the typical range for a mid-size engineering organization. It explicitly does not target cloud-scale (10,000+ nodes) to avoid the complexity of Kubernetes-style orchestration.

### 4.3 Why Windows Workers

The vast majority of enterprise workstations run Windows. AICluster targets Windows workers because:

- **Existing infrastructure**: IT departments already manage Windows fleets with Group Policy, SCCM, and Intune
- **User familiarity**: Office workers and developers are comfortable with Windows, reducing adoption friction
- **Resource constraints**: Windows provides process priority, CPU affinity, and memory limits that AICluster uses to ensure workers are invisible to the primary user
- **No agent overhead**: Workers run as native Windows processes with BELOW_NORMAL priority, consuming only spare cycles
- **Network integration**: Windows domain-joined machines provide consistent authentication, DNS resolution, and network discovery

The master node can run on any platform FastAPI supports (Windows, Linux, macOS), but workers are Windows-only in v1.0. macOS/Linux worker support is a future consideration.

### 4.4 Why Plugins

A plugin system was chosen over a monolithic architecture because:

- **Domain separation**: Different teams need different capabilities â€” security teams need SAST plugins, DevOps needs deployment plugins, QA needs test automation plugins
- **Release independence**: Plugins can be developed, tested, and deployed independently of the core platform
- **Ecosystem growth**: A plugin marketplace enables community contributions without core code access
- **Customization**: Organizations can write internal plugins for proprietary tools, workflows, and integrations
- **Stability**: Plugin failures are isolated â€” a crashing plugin does not bring down the master server

The plugin system provides 16 plugin types, 15 platform hooks, a manifest specification, and a lifecycle manager. Plugins are Python packages with a `Plugin` class that registers hook callbacks.

### 4.5 Why Repository Intelligence

Repository Intelligence is the foundation upon which all AI-powered features are built. Without understanding the codebase, AI agents cannot generate accurate code, find relevant files, or reason about architecture. AICluster's Repository Intelligence subsystem provides:

- **Code understanding**: Parsed symbols (classes, functions, interfaces), their signatures, docstrings, and relationships
- **Dependency analysis**: Import graphs and dependency edges between files and modules
- **Knowledge graphs**: High-level concepts, patterns, and architectural relationships extracted from the codebase
- **Search capabilities**: Symbol lookup, file search, full-text search, and reference tracking
- **Code metrics**: Complexity, lines of code, language distribution, and maintainability indices

This intelligence is the substrate for the AI Runtime (context building), the Multi-Agent system (task planning), the Workflow Engine (dependency resolution), and the Engineering Engine (impact analysis).

### 4.6 Why Multi-Agent

Software engineering is inherently multi-disciplinary. A feature addition typically requires changes to backend APIs, frontend UI, database schema, tests, and documentation. A single monolithic AI cannot effectively handle all these domains simultaneously.

AICluster's multi-agent architecture addresses this through:

- **Specialization**: Each agent has a defined role (Architect, Backend Engineer, Frontend Engineer, QA, Docs Writer) with corresponding capabilities and tool access
- **Parallel execution**: Multiple agents work simultaneously on different aspects of the same task
- **Review and merge**: Outputs are reviewed by specialized Reviewer agents and merged by a Merger agent
- **Task decomposition**: Complex goals are automatically decomposed into subtasks by a Planner agent
- **Scalability**: Adding more agents (by role or by worker) increases throughput linearly

The architecture provides 12 default agents covering the full software development lifecycle, from planning through implementation, review, and documentation.

### 4.7 Why Local LLMs

Local LLMs are chosen over cloud APIs for four fundamental reasons:

1. **Data privacy**: Source code, engineering plans, and architectural discussions never leave the LAN
2. **Latency**: Local inference eliminates network round-trips, providing sub-second response for small prompts
3. **Cost**: No per-token pricing â€” local models run on existing hardware with no marginal cost
4. **Reliability**: No API rate limits, no service outages, no vendor lock-in

AICluster supports three provider interfaces: Ollama (easiest setup, broadest model support), llama.cpp (lightweight, CPU-optimized), and OpenAI-compatible endpoints (for vLLM, LM Studio, or hybrid deployments). The Model Router selects the optimal provider based on task type, context size, and quality requirements.

A key design choice is that the AI Runtime is interface-driven rather than implementation-driven. The `ModelProvider` abstract base class defines `load()`, `generate()`, `stream()`, `token_count()`, and `health()` methods. Any provider implementing this interface can be registered at runtime. This means AICluster is not locked into any specific model or provider â€” it can adapt as the local LLM ecosystem evolves.

### 4.8 Architectural Principles

**Workers are invisible**: The office worker on an HP Core Ultra 7 never knows AICluster is running. No slowdowns, no popups, no interference. Workers use 25% CPU maximum, 8GB RAM maximum, and BELOW_NORMAL process priority. They auto-pause on user activity and auto-resume after 5 minutes of idle.

**Master is lightweight**: A single Python process with SQLite database. No external dependencies beyond Python 3.12+ and Node.js 20+. No Kubernetes, no Docker, no message brokers.

**Everything is observable**: Every heartbeat, every job, every error is logged and visible in the dashboard. Three logging layers exist: database-backed structured logs, audit events with 17 categories, and real-time WebSocket broadcasts.

**Failure is expected**: Workers go offline, jobs fail, network connections drop. The system handles all of this gracefully â€” workers auto-reconnect with exponential backoff, jobs retry up to 3 times, the master detects offline workers within 15 seconds.

**Security by default**: JWT authentication, bcrypt password hashing, CORS restrictions, input validation. The default configuration is secure â€” users must explicitly weaken security settings.

**Scales down, not up**: Designed for 4-100 workers, not 10,000. Simplicity over complexity. SQLite instead of PostgreSQL, simple file-based artifacts instead of S3, in-process scheduling instead of Celery.

### 4.9 Quality Bar

The project maintains a strict quality bar:

- All tests pass: 44 backend unit tests, 14 worker unit tests, 40 integration tests
- Zero build errors: next build, tsc --noEmit, and all Python imports produce zero errors and zero warnings
- API responses under 200ms at p95 under normal load
- Dashboard updates every 2 seconds via polling + WebSocket push
- Worker failure does not cascade â€” master continues operating when any worker disconnects

## 5. Long-Term Goals

### 5.1 Version Roadmap

| Phase | Version | Focus |
|-------|---------|-------|
| 1-2 | v0.1-v0.2 | Project structure, Master server, REST API, WebSocket, scheduler |
| 3 | v0.3.0 | Real worker service, resource limits, auto pause/resume |
| 4 | v0.4.0 | Full dashboard UI, analytics charts, file manager |
| 5 | v0.5.0 | AI chat integration, distributed code analysis |
| 6 | v0.6.0 | Repository intelligence, multi-agent orchestration |
| 7 | v0.7.0 | Plugin system, production hardening |
| 8 | v1.0.0 | Production release |
| 9+ | v1.1+ | Studio IDE, Engineering Engine, Audit System |

### 5.2 Future Directions

**GPU Compute Support (v2.0)**: Extend worker capabilities to include GPU-accelerated workloads. Workers with NVIDIA GPUs would be discovered during registration and assigned GPU-intensive tasks (model training, fine-tuning, large-batch inference).

**macOS/Linux Workers**: Extend the worker agent to support macOS and Linux, enabling heterogeneous clusters that span operating systems.

**Cross-Cluster Federation**: Enable multiple AICluster masters to communicate, allowing workload distribution across physical sites or organizational boundaries.

**Advanced Resource Management**: Implement predictive scheduling based on historical usage patterns, office hour awareness, and machine learning-driven resource allocation.

**Plugin Marketplace**: Create a public plugin registry where community-contributed plugins can be discovered, reviewed, and installed from within the Studio interface.

**Continuous Learning**: Implement a feedback loop where agent outputs, code review results, and engineering outcomes are used to improve model routing, prompt templates, and agent behavior over time.

**Compliance and Audit Integration**: Extend the audit system to support SIEM integration, compliance reporting (SOC2, HIPAA, GDPR), and automated evidence collection for software engineering audits.

### 5.3 Non-Goals (What AICluster Will Not Be)

- **Public cloud platform**: AICluster does not run on AWS, Azure, or GCP. It runs on your LAN.
- **Multi-tenant SaaS**: No signup pages, no billing, no org management. One cluster, one team.
- **Container orchestrator**: This is not Kubernetes. AICluster manages Windows processes, not Docker containers.
- **General-purpose compute**: AICluster focuses on AI-assisted software engineering workloads. It is not a general-purpose distributed compute platform.
- **Replacement for developer workstations**: AICluster augments developer workstations with distributed compute â€” it does not replace local development environments.

## 6. Detailed Architecture Breakdown

### 6.1 Master Server Architecture

The master server is the central coordination point of the AICluster cluster. It runs on a dedicated machine (or any machine with Python 3.12+) and provides:

**REST API Layer** (FastAPI on port 8000): 50+ endpoints organized under `/api/v1/` covering workers, jobs, dashboard, health, logs, auth, workflows, repositories, AI, agents, engineering, production, plugins, studio, and audit. Each endpoint uses FastAPI's dependency injection for database sessions and (optionally) authentication.

**WebSocket Layer** (`/ws` on port 8000): Real-time broadcast for worker updates, job progress, dashboard metrics, workflow events, and system alerts. The WebSocket manager maintains a set of active connections (max 100 by default) and broadcasts JSON-encoded events to all connected clients.

**Service Layer**: Business logic is encapsulated in service classes: `WorkerManagerService` (worker lifecycle), `SchedulerService` (job queue management), `AuthService` (authentication), `LogService` (structured logging), and domain-specific services for workflow, repository, AI, agents, engineering, plugins, and audit.

**Database Layer**: SQLite via aiosqlite + SQLAlchemy 2.0 async. 50+ database tables across all domains. Lazy engine initialization with `get_engine()` and test isolation via `reset_engine()`. Composite indexes on common query patterns.

**Background Tasks**: Offline worker checker (10-second loop), scheduler loop (2-second loop), audit event bus listeners.

### 6.2 Worker Agent Architecture

The worker agent runs on each Windows machine in the cluster. It is a FastAPI application that serves two purposes:

**Worker API** (port 8001): Provides a health endpoint for local monitoring. The primary work happens in the background, not through the API.

**Worker Lifecycle** (background asyncio task):
1. STARTING â€” Application starts, imports are loaded
2. LOADING_CONFIG â€” Configuration loaded from env vars, config.json, .env, and defaults
3. CONNECTING â€” HTTP client created, connecting to master URL
4. REGISTERING â€” POST to `/workers/register` with hostname and IP. Retries with exponential backoff on failure
5. ONLINE â€” Successfully registered. Heartbeat service and job poller started
6. HEARTBEAT â€” Every 5 seconds, sends CPU, RAM, disk, network metrics to master
7. POLL_JOB â€” Every 5 seconds, polls master for next job assignment
8. EXECUTING â€” Job received, handler invoked with job payload
9. REPORT_RESULT â€” Job completed, result sent to master

**State Machine**: The worker implements a 21-state state machine covering normal operation, network failure recovery, registration retry, and graceful shutdown. States are mutually exclusive and transitions are validated.

**Resource Monitoring**: Uses psutil to collect CPU percent, memory usage, disk usage, network I/O. Resource data is sent with every heartbeat (5-second interval). The monitoring service also tracks temperature (where available) and provides data for the auto-pause/resume system.

**Job Execution Framework**: 5 built-in handlers (echo, sleep, dir_scan, hash_file, count_files). Each handler implements the `BaseJobHandler` interface with an `async def execute()` method. The framework provides progress reporting with configurable thresholds (every 5% or every 5 seconds).

**Retry and Recovery**: The `RetryHandler` implements exponential backoff with delays of 1, 2, 5, 10, 30, and 60 seconds. Registration failures trigger retries indefinitely (never crashes). Heartbeat failures are logged but do not affect the worker state machine.

### 6.3 Frontend Architecture

**Main Dashboard** (Next.js 15, port 3000): The primary user interface for cluster management. Uses App Router, TypeScript, Tailwind CSS, and shadcn/ui components. Dark glassmorphism theme. State management via Zustand with persist middleware for auth tokens. Data fetching via React Query with 2-second polling for dashboard metrics.

**Master Control Center** (React + Vite, port 5173): A desktop-oriented dashboard for cluster administrators. 11 pages covering all cluster operations. FastAPI backend on port 8800.

**Worker Control Center** (React + Vite): A worker-specific interface for monitoring and configuring individual worker nodes.

**AICluster Studio** (React + Vite + Tauri): A full-featured IDE for AI-assisted software development. Includes Monaco Editor, terminal emulator, workflow designer, agent designer, prompt studio, and plugin center. Packaged as a Tauri v2 desktop application.

### 6.4 Key Design Patterns

**Service Pattern**: All business logic is encapsulated in service classes. Services accept database sessions via constructor injection. This enables request-scoped transactions and testability through session mocking.

**Repository Pattern (Implicit)**: SQLAlchemy models serve as both ORM entities and data access objects. The database module provides session management but there are no formal repository interfaces.

**Observer Pattern**: WebSocket broadcasts implement a push-based observer pattern. The EventBus in the audit system implements a pub/sub variant with subscriber registration and asynchronous dispatch.

**Strategy Pattern**: The ModelProvider interface enables pluggable LLM backends. Each provider implements the same interface but uses different underlying technologies (Ollama HTTP API, llama.cpp server, OpenAI-compatible API).

**Template Method Pattern**: The worker's `_execute_job` method defines the skeleton of job execution while delegating the actual work to handler-specific `execute()` methods.

**State Pattern**: The WorkerState enum and the worker lifecycle loop implement a state machine where state transitions determine available actions and error recovery strategies.

## 7. Detailed Database Schema

### 7.1 Core Tables (Phase 2)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| workers | Worker node registry | id, worker_name, hostname, ip, status, cpu_percent, ram_percent, disk_percent, temperature, last_seen |
| jobs | Job queue | id, type, status, priority, assigned_worker, progress, payload, result, error, retry_count |
| system_logs | Application logs | id, level, message, source, created_at |
| users | Authentication | id, username, hashed_password, role, is_active |

### 7.2 Workflow Tables (Phase 4)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| workflows | Workflow definitions | id, name, status, workflow_type, priority, total_tasks, progress |
| workflow_tasks | Individual tasks | id, workflow_id, task_type, status, assigned_worker, position, duration_ms |
| task_dependencies | DAG edges | task_id, depends_on_id, type |
| artifacts | Execution outputs | id, name, type, size_bytes, checksum, storage_path |
| execution_metrics | Performance data | id, metric_type, value, unit |
| cache | Result cache | cache_key, workflow_type, task_type, input_hash, expires_at |
| workflow_events | Event stream | workflow_id, event_type, data |

### 7.3 Repository Intelligence Tables (Phase 5)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| repositories | Repository registry | name, path, language, total_files, total_symbols |
| repository_files | File inventory | path, language, lines, code_lines, complexity, hash |
| symbols | Code symbols | name, qualified_name, symbol_type, language, signature, line_start, complexity |
| symbol_imports | Import statements | source, imported_name, alias, is_relative |
| symbol_references | Cross-references | source_symbol_id, target_symbol_id, reference_type |
| dependency_edges | File dependencies | source_file_id, target_file_id, dependency_type, weight |
| code_metrics | Metric history | metric_type, value |
| knowledge_nodes/graph | Knowledge graph | node_type, name, data |
| repository_cache | Session cache | cache_key, data, expires_at |

### 7.4 AI Runtime Tables (Phase 6)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| ai_models | Model registry | name, provider, model_type, context_window, capabilities |
| ai_sessions | Chat sessions | user_id, model_id, status, total_tokens, expires_at |
| ai_messages | Conversation history | session_id, role, content, tokens, tool_calls |
| prompt_templates | Reusable prompts | name, system_prompt, template, variables |
| tool_definitions | Tool registry | name, description, schema, permissions |
| tool_calls | Tool execution log | session_id, tool_id, status, input, output, duration_ms |
| ai_memory | Per-session memory | session_id, memory_type, key, value, importance |
| ai_provider_config | Provider settings | provider, config, enabled |
| runtime_metrics | Performance data | session_id, metric_type, value, unit |

### 7.5 Multi-Agent Tables (Phase 7)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| agents | Agent registry | name, role, status, capabilities, permissions, model_preference |
| agent_tasks | Task assignments | workflow_id, assigned_agent, task_type, status, input, output |
| agent_messages | Inter-agent communication | sender, recipient, message_type, content, read |
| agent_reviews | Quality reviews | task_id, reviewer, score, checks, passed |
| agent_merges | Output merging | source_agents, status, input_artifacts, output, conflicts |
| agent_memory_store | Agent memory | agent_id, memory_type, key, value, importance |
| agent_metrics | Agent performance | metric_type, value, unit |

### 7.6 Engineering Engine Tables (Phase 9)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| engineering_plans | Implementation plans | goal, goal_type, status, risk_level, estimated_hours, requires_approval |
| engineering_tasks | Plan tasks | plan_id, agent_role, description, status, position |
| engineering_patches | Code changes | task_id, file_path, operation, old_content, new_content, validated |
| engineering_validations | Check results | plan_id, task_id, check_type, passed, details |
| engineering_repairs | Fix iterations | plan_id, task_id, iteration, failure, fix, success |
| engineering_quality | Gate results | plan_id, quality_type, passed, score |
| engineering_approvals | Approval workflow | plan_id, request_type, status, approved_by |
| engineering_metrics | Performance data | metric_type, value, unit |
| engineering_reports | Generated docs | plan_id, report_type, content |

## 8. Conclusion

AICluster represents a novel approach to AI-assisted software engineering: instead of sending code to cloud APIs, it brings AI compute to the code. By harnessing the idle compute capacity of existing Windows workstations, it provides a scalable, private, and cost-effective platform for distributed AI workloads. The architecture prioritizes simplicity, observability, and user invisibility over feature breadth. Every design decision â€” from offline-first operation to plugin extensibility â€” serves the central mission: turning idle Windows PCs into a private AI compute cluster.

The platform at v2.0.0 demonstrates comprehensive coverage across 11 development phases with 50+ database tables, 50+ API endpoints, 3 frontend applications, a fully functional worker agent, 3 LLM provider implementations, 12 default AI agents, 10 engineering validation checks, 15 plugin hook points, and a complete audit system. The primary areas for future investment are security hardening (authentication enforcement), scalability improvements (beyond 100 workers), and completing the partial implementations in the production monitoring subsystem.
