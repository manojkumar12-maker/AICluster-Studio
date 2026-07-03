<div align="center">

# 🤖 AICluster

**Offline-first AI cluster management platform for distributed computing across Windows machines**

[![GitHub Release](https://img.shields.io/github/v/release/aicluster/aicluster?style=flat&logo=github&color=blue)](https://github.com/aicluster/aicluster/releases)
[![GitHub Stars](https://img.shields.io/github/stars/aicluster/aicluster?style=flat&logo=github&color=yellow)](https://github.com/aicluster/aicluster/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/aicluster/aicluster?style=flat&logo=github&color=red)](https://github.com/aicluster/aicluster/issues)
[![License](https://img.shields.io/github/license/aicluster/aicluster?style=flat&logo=open-source-initiative&color=brightgreen)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat&logo=python&logoColor=white)](https://python.org)
[![Node](https://img.shields.io/badge/Node-20+-green?style=flat&logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![Rust](https://img.shields.io/badge/Rust-1.80+-orange?style=flat&logo=rust&logoColor=white)](https://rust-lang.org)
[![Tauri](https://img.shields.io/badge/Tauri-v2-purple?style=flat&logo=tauri&logoColor=white)](https://tauri.app)
[![Build](https://img.shields.io/badge/Build-Passing-success?style=flat&logo=githubactions&logoColor=white)](https://github.com/aicluster/aicluster/actions)

</div>

---

## ✨ Features

| Area | Capabilities |
|------|-------------|
| **🧠 AI Runtime** | Multi-provider (Ollama, llama.cpp, OpenAI-compatible), model routing, context optimization, chat sessions, tool execution |
| **📦 Workflow Engine** | DAG-based task orchestration, parallel/fan-out/fan-in execution, exponential backoff retry, artifact store |
| **🤝 Multi-Agent** | 12 default agents, planning engine, orchestrator, inter-agent communication, review & merge pipelines |
| **🔌 Plugin System** | Plugin SDK, hook registry, 16 plugin types, lifecycle management, sandboxed execution |
| **📊 Repository Intelligence** | Multi-language symbol parser, incremental indexer, code metrics, dependency graph, full-text search |
| **🔧 Engineering Engine** | Goal analysis, automated planning, quality gates, self-repair loop, documentation generation |
| **📋 Audit System** | Event capture middleware, 17 categories, full-text search, CSV/JSON export, retention policies |
| **🖥️ Studio IDE** | Tauri v2 desktop IDE, workspace management, Monaco editor, AI chat, workflow designer |
| **🎮 Control Centers** | Master & Worker desktop apps, cluster topology, live dashboard, maintenance mode |
| **📡 Cluster Operations** | LAN discovery, auto-registration, backup/restore, alert center, diagnostics |
| **🔐 Security** | JWT auth with bcrypt, audit trails, plugin permissions, role-based access |
| **🌐 Offline-First** | 100% LAN operation, no internet required after setup, all features work disconnected |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AICluster Platform                            │
├──────────────────────┬──────────────────────┬───────────────────────┤
│    Master Server      │   Worker Fleet       │   Desktop Apps        │
│  ┌────────────────┐  │  ┌────────────────┐  │  ┌─────────────────┐  │
│  │ FastAPI + ASGI  │  │  │ Worker Agent   │  │  │ Studio (Tauri)   │  │
│  │ SQLAlchemy/SQLite│  │  │ State Machine  │  │  │ Workspace Mgmt   │  │
│  │ WebSocket Broker │  │  │ Job Executor   │  │  │ Monaco Editor    │  │
│  └────────┬───────┘  │  │ Resource Limits │  │  │ Workflow Designer│  │
│           │          │  └────────┬───────┘  │  └─────────────────┘  │
│  ┌────────┴───────┐  │           │          │  ┌─────────────────┐  │
│  │  REST + WebSocket   │           │          │  │ Master Control  │  │
│  │  (HTTP/WS)     │  │           │          │  │ Center (Tauri)   │  │
│  └────────────────┘  │           │          │  │ Cluster Mgmt     │  │
│           │          │           │          │  └─────────────────┘  │
│  ┌────────┴───────┐  │           │          │  ┌─────────────────┐  │
│  │ Subsystems:     │  │           │          │  │ Worker Control  │  │
│  │ AI Runtime      │◄─┼───────────┼──────────┼──┤ Center (Tauri)  │  │
│  │ Agents          │  │           │          │  │ Local Monitoring│  │
│  │ Workflow        │  │           │          │  └─────────────────┘  │
│  │ Repository      │  │           │          │                       │
│  │ Engineering     │  │           │          │  ┌─────────────────┐  │
│  │ Plugins         │  │           │          │  │ CLI (aicluster)  │  │
│  │ Audit           │  │           │          │  │ PyInstaller EXE  │  │
│  │ Production      │  │           │          │  └─────────────────┘  │
│  └────────────────┘  │           │          │                       │
└──────────────────────┴───────────┴──────────┴───────────────────────┘
```

---

## 🚀 Quick Start

```powershell
# One-command setup
git clone https://github.com/aicluster/aicluster.git
cd aicluster
python -m build.build
```

### Prerequisites

- **Python** 3.12+
- **Node.js** 20+ (LTS)
- **Rust** 1.80+ (for Tauri desktop apps)
- **Windows 10/11** (primary target; Linux/macOS experimental)

The build script handles:
- Virtual environment creation & dependency installation
- Frontend (Next.js) build
- Studio (Vite + Tauri) build
- Master Control Center & Worker Control Center builds
- Database initialization
- PyInstaller EXE packaging
- Inno Setup installer generation

---

## 📸 Screenshots

| Dashboard | Studio IDE | Cluster Map |
|:---------:|:----------:|:-----------:|
| ![Dashboard](docs/Images/dashboard.png) | ![Studio](docs/Images/studio.png) | ![Cluster](docs/Images/cluster-map.png) |
| **Worker Manager** | **Workflow Designer** | **AI Chat** |
| ![Workers](docs/Images/workers.png) | ![Workflow](docs/Images/workflow-designer.png) | ![AI Chat](docs/Images/ai-chat.png) |

> Screenshots are generated during the build process and stored in `docs/Images/`.

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic V2 |
| **Database** | SQLite (via aiosqlite + greenlet async) |
| **Frontend** | Next.js 15, React 18, TypeScript, TailwindCSS, shadcn/ui |
| **Studio IDE** | Tauri v2, Rust, Vite, React 19, TypeScript 6, TailwindCSS v4 |
| **Desktop Apps** | Tauri v2 (Master Control Center, Worker Control Center, Studio) |
| **State** | Zustand, TanStack React Query |
| **AI Providers** | Ollama, llama.cpp, OpenAI-compatible (vLLM, LM Studio, etc.) |
| **Auth** | JWT (python-jose), bcrypt/passlib |
| **Packaging** | PyInstaller (--onefile), Inno Setup, Tauri bundler |
| **Real-time** | WebSockets (websockets 14.x) |
| **Testing** | pytest (backend), Vitest (frontend) |

---

## 📁 Directory Structure

<details>
<summary>Click to expand</summary>

```
AICluster/
├── backend/                  # FastAPI master server
│   ├── app/
│   │   ├── agents/           # Multi-agent orchestration engine
│   │   ├── ai/               # AI runtime (providers, routing, sessions)
│   │   ├── api/              # REST API route handlers
│   │   ├── audit/            # Event capture & audit system
│   │   ├── engineering/      # Autonomous software engineering engine
│   │   ├── plugins/          # Plugin SDK, loader, registry
│   │   ├── production/       # Monitoring, health, diagnostics
│   │   ├── repository/       # Code intelligence & search
│   │   ├── services/         # Auth, scheduler, worker manager
│   │   ├── workflow/         # DAG-based workflow execution
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── static/           # Static assets & dashboard HTML
│   ├── tests/                # 44+ pytest tests
│   └── dist/                 # PyInstaller output
├── frontend/                 # Next.js 15 dashboard
│   └── src/                  # React components, pages, hooks
├── studio/                   # Tauri v2 desktop IDE
│   ├── src-tauri/            # Rust/Tauri backend
│   └── src/                  # React + Vite frontend
├── master-control-center/    # Tauri v2 cluster management app
├── worker-control-center/    # Tauri v2 worker monitoring app
├── worker/                   # Worker agent (FastAPI)
├── build/                    # Build system (PyInstaller, Tauri, Inno Setup)
│   └── verification/         # Post-build validation pipeline
├── scripts/                  # Setup, simulator, installers
├── config/                   # YAML configuration (dev/prod)
├── shared/                   # Shared types & protocols
│   ├── py/                   # Python shared schemas
│   └── ts/                   # TypeScript shared types
├── docs/                     # Documentation & screenshots
├── plugins/                  # User-installed plugins
├── data/                     # Runtime data (DB, artifacts, logs)
├── models/                   # Local AI model files
│   └── assets/               # App icons, branding
├── VERSION                   # Current version (1.3.0)
├── CHANGELOG.md              # Release history
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
├── PROJECT_STATE.md          # Project status document
└── SECURITY.md               # Security policy
```
</details>

---

## 📋 Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 21H2 | Windows 11 23H2 |
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16+ GB |
| **Disk** | 5 GB free | 20+ GB (with models) |
| **Python** | 3.12 | 3.13 |
| **Node.js** | 20 LTS | 22 LTS |
| **Rust** | 1.80 | 1.85+ |
| **Network** | LAN (100 Mbps) | LAN (1 Gbps) |

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](SECURITY.md) before submitting pull requests.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
Made with ❤️ by the AICluster Contributors
</div>
