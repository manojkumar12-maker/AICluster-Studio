# AICluster AI Discovery

## 1. Repository Intelligence

**Location**: `backend/app/repository/`
**Purpose**: Scan, parse, and index source code repositories for code intelligence

### Components
| Component | File | Purpose |
|-----------|------|---------|
| RepositoryIndexer | `indexer/service.py` | Incremental file indexer, tracks changed files |
| Scanner | `scanner/service.py` | Directory walker, detects file types by extension |
| Parser | `parser/service.py` | Multi-language symbol extraction (Python, JS/TS, Rust, Java, Go, C/C++, etc.) |
| SearchService | `search/service.py` | Full-text search with regex mode |
| CodeMetricsService | `metrics/service.py` | LOC, complexity, comment ratio, etc. |

### Data Flow
```
User adds repository
  → POST /api/v1/repositories
  → RepositoryFile records created
  → POST /api/v1/repositories/{id}/scan
  → Scanner walks directory
  → Parser extracts symbols, imports, references
  → Indexer builds dependency edges + knowledge graph
  → SearchService indexes for full-text search
  → CodeMetricsService computes metrics
```

### 11 Database Tables
- `repositories`, `repository_files`, `symbols`, `symbol_imports`, `symbol_references`
- `dependency_edges`, `code_metrics`, `knowledge_nodes`, `knowledge_edges`
- `repository_cache`, `repository_events`

---

## 2. Workflow Engine

**Location**: `backend/app/workflow/`
**Purpose**: DAG-based task orchestration across worker fleet

### Components
| Component | File | Purpose |
|-----------|------|---------|
| WorkflowEngine | `engine/service.py` | Main orchestration entry point |
| WorkflowPlanner | `planner/service.py` | DAG validation (cycle detection, topological sort) |
| TaskDispatcher | `dispatcher/service.py` | Assign tasks to workers based on capabilities |
| Executor | `executor/service.py` | Run workflow tasks, handle retries |
| ArtifactStore | `artifacts/service.py` | Manage task output artifacts |
| CacheService | `cache/service.py` | Cache workflow results |
| StateManager | `state/service.py` | Workflow state machine |
| MetricsService | `metrics/service.py` | Track execution time, resource usage |

### Execution Flow
```
1. POST /api/v1/workflow — create workflow with DAG definition
2. WorkflowPlanner validates DAG
3. WorkflowEngine starts execution
4. TaskDispatcher assigns tasks to workers (considering capabilities)
5. Workers execute tasks, report progress/result
6. ArtifactStore collects outputs
7. CacheService caches results (keyed by input hash)
8. On completion: workflow_result created
9. MetricsService records execution data
```

### Retry Strategy
- Exponential backoff: 1s, 2s, 5s, 10s, 30s, 60s
- Configurable max_retries (default 3)
- Failed tasks can trigger repair via Engineering Engine

---

## 3. Multi-Agent Engine

**Location**: `backend/app/agents/`
**Purpose**: Multi-agent AI collaboration system

### Default Agents (12)
From `roles/definitions.py`:
1. **Architect** — System design, architecture decisions
2. **Developer** — Code implementation
3. **Reviewer** — Code review, quality checks
4. **Tester** — Test creation, test execution
5. **DevOps** — Deployment, infrastructure
6. **Security** — Security review, vulnerability scanning
7. **Documentation** — Doc generation, README writing
8. **Project Manager** — Task breakdown, planning
9. **Data Scientist** — Data analysis, ML modeling
10. **UX Designer** — UI/UX design
11. **QA Engineer** — Quality assurance
12. **Tech Writer** — Technical documentation

### Orchestration Flow
```
POST /api/v1/agents/run {task, agents: [...]}
  → Orchestrator receives task description
  → Planner generates execution plan
  → For each step:
     → Selected agent executes
     → Agent messages logged
     → Output sent to next agent (chain)
     → ReviewService reviews output
     → If review fails: repair/retry
  → MergeService merges all outputs
  → Final result returned
```

### Inter-Agent Communication
- Agents communicate via `agent_messages` table
- Directed messages (sender → receiver)
- Message types: task, result, review, question, approval
- Full threading via `parent_message_id`

---

## 4. LLM Runtime

**Location**: `backend/app/ai/`
**Purpose**: Multi-provider LLM integration with routing, sessions, tools

### Architecture
```
AI Runtime
├── ModelRegistry — Provider class registry
├── ModelRouter — Task-based routing
├── SessionManager — Chat session lifecycle
├── ConversationManager — Message history
├── ContextBuilder — Repository context
├── ContextOptimizer — Token-aware compression
├── PromptBuilder — Structured prompt construction
├── ToolRegistry — Tool definitions
├── ToolExecutor — Tool call execution
├── StreamingService — Streaming response handling
├── MemoryService — Session KV memory
└── MetricsService — Token/latency tracking
```

### Provider Architecture

**Abstract Base** (`providers/interface.py`):
```python
class ModelProvider(ABC):
    async def chat(self, messages, **kwargs) -> str
    async def complete(self, prompt, **kwargs) -> str
    async def stream_chat(self, messages, **kwargs) -> AsyncIterator[str]
    async def stream_complete(self, prompt, **kwargs) -> AsyncIterator[str]
    async def embed(self, texts) -> list[list[float]]
```

**OllamaProvider** (`providers/ollama.py`):
- HTTP API to local Ollama instance (default: localhost:11434)
- Supports: chat, completion, streaming, embeddings
- Model management: pull, list, delete

**LlamaCppProvider** (`providers/llamacpp.py`):
- HTTP API to llama.cpp server
- Supports: chat, completion, streaming
- Lighter weight, CPU-friendly

**OpenAIProvider** (`providers/openai.py`):
- OpenAI-compatible API (vLLM, LM Studio, etc.)
- Supports: chat, completion, streaming
- Configurable base URL

### Model Routing

**Task-based routing** (`routing/router.py`):
```python
TASK_ROUTING = {
    "code_generation": {"provider": "ollama", "model": "codellama"},
    "architecture_review": {"provider": "openai", "model": "gpt-4"},
    "documentation": {"provider": "ollama", "model": "llama3"},
    "summarization": {"provider": "ollama", "model": "mistral"},
    "default": {"provider": "ollama", "model": "llama3"},
}

PROFILES = {
    "fast": {"max_tokens": 512, "temperature": 0.3},
    "balanced": {"max_tokens": 2048, "temperature": 0.7},
    "maximum_quality": {"max_tokens": 4096, "temperature": 0.9},
    "offline_low_ram": {"max_tokens": 256, "temperature": 0.5},
}
```

### Chat Session Flow
```
POST /api/v1/ai/chat {session_id, message}
  → SessionManager: validate session, update last_active
  → ConversationManager: add user message to history
  → ContextBuilder: build repository context (if repo_id provided)
  → PromptBuilder: assemble system prompt + context + history
  → ModelRouter: select provider based on task_type + profile
  → ModelProvider: send to LLM, get response
  → ConversationManager: add assistant message to history
  → Return response
```

### Context Optimization
```
ContextBuilder.build_context(repository_id, query):
  → Get repository info (name, language, file_count)
  → Get relevant symbols (matching query)
  → Get key files (recently modified, important)
  → Return formatted context string

ContextOptimizer.rank_context(query, symbols, files):
  → Score symbols/files by relevance to query
  → Compress to token budget
  → Return ranked set
```

---

## 5. Prompt Builder

**Location**: `backend/app/ai/prompt/service.py`

### Structure
```
System Prompt (from template)
Repository Context (from ContextBuilder)
Conversation History (last N messages)
User Message (current input)
```

### Token Estimation
- Simple 4-char-per-token heuristic
- Used for context window management

---

## 6. Plugin SDK

**Location**: `backend/app/plugins/`
**Purpose**: Extensible hook-based plugin system

### Plugin Lifecycle
```
1. Install: POST /api/v1/plugins/install (URL or Upload)
2. ManifestService: validate plugin.json (id, name, version, hooks, permissions)
3. PluginLoader: dynamic import of entry_point module
4. PluginRegistry: track installed plugins
5. Enable/Disable: toggle plugin active state
6. Uninstall: remove plugin files, deregister hooks
```

### 16 Hook Types
| Hook | Trigger |
|------|---------|
| `on_startup` | Server startup |
| `on_shutdown` | Server shutdown |
| `before_request` | Before each HTTP request |
| `after_request` | After each HTTP request |
| `on_worker_register` | Worker registers |
| `on_worker_heartbeat` | Worker heartbeat received |
| `on_worker_disconnect` | Worker goes offline |
| `on_job_created` | Job created |
| `on_job_completed` | Job completed |
| `on_job_failed` | Job failed |
| `on_workflow_start` | Workflow starts |
| `on_workflow_finish` | Workflow finishes |
| `on_agent_message` | Agent sends message |
| `on_engineering_plan` | Engineering plan created |
| `on_audit_event` | Audit event captured |
| `on_repository_scan` | Repository scanned |

### Example Plugin
```python
# plugin.json
{
  "plugin_id": "example-metrics-reporter",
  "name": "Metrics Reporter",
  "hooks": ["on_workflow_finish"]
}

# main.py
class Plugin:
    async def on_workflow_finish(self, workflow_id, status):
        logger.info(f"Workflow {workflow_id} finished with status {status}")
        return {"reported": True}
```

---

## 7. Engineering Engine

**Location**: `backend/app/engineering/`
**Purpose**: AI-driven software engineering pipeline

### Pipeline Stages
```
1. Goal Analysis (goal/analyzer.py)
   └─ Parse user requirements → structured goals
   
2. Planning (planner/service.py)
   └─ Goals → execution plan with ordered tasks

3. Risk Assessment (risk/engine.py)
   └─ Identify risks, dependencies, blockers

4. Task Execution
   └─ Each task: plan → implement → test

5. Validation (validator/service.py)
   └─ Syntax check, lint, test run, security scan

6. Auto-Repair (repair/service.py)
   └─ If validation fails: analyze error → generate fix → re-run

7. Quality Gates (quality/service.py)
   └─ Code quality score, test coverage, security score

8. Approval (approvals/service.py)
   └─ Submit for human approval

9. Documentation (documentation/service.py)
   └─ Generate README, API docs, changelog
```

### Data Model (9 tables)
- `engineering_plans`, `engineering_tasks`, `engineering_patches`
- `engineering_validations`, `engineering_repairs`, `engineering_quality`
- `engineering_approvals`, `engineering_metrics`, `engineering_reports`
