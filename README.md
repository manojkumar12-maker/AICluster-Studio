<div align="center">

# ðŸš€ AICluster v2.0.0

**Offline-first AI cluster management platform for distributed computing across Windows machines**

[![Version](https://img.shields.io/badge/Version-2.0.0-blue?style=flat&logo=github&color=blue)](https://github.com/manojkumar12-maker/AICluster-Studio/releases)
[![Security](https://img.shields.io/badge/Security-Hardened-brightgreen?style=flat)](SECURITY.md)
[![Tests](https://img.shields.io/badge/Tests-74/74-green?style=flat)](backend/tests/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat&logo=python&logoColor=white)](https://python.org)
[![Build](https://img.shields.io/badge/Build-Passing-success?style=flat)](build/)
[![Windows](https://img.shields.io/badge/Windows-10/11-blue?style=flat&logo=windows&logoColor=white)](INSTALLATION.md)

**v2.0.0: Unified runtime architecture, single-click installer, auto-configured first run. Production ready.**

</div>

---

## âœ¨ Features

| Area | Capabilities |
|------|-------------|
| **ðŸ” Security** | JWT auth on all 131 endpoints, bcrypt passwords, rate limiting, CORS enforcement |
| **ðŸ§  AI Runtime** | Multi-provider (Ollama, llama.cpp, OpenAI-compatible), model routing, context optimization, chat sessions |
| **ðŸ“¦ Workflow Engine** | DAG-based task orchestration, parallel execution, exponential backoff retry, artifact store |
| **ðŸ¤ Multi-Agent** | 12 default agents, orchestrated pipelines, inter-agent communication, code review & merge |
| **ðŸ”Œ Plugin System** | Plugin SDK with 16 hook types, lifecycle management, dynamic loading |
| **ðŸ“Š Repository Intelligence** | Multi-language symbol parser, dependency graph, code metrics, full-text search |
| **ðŸ› ï¸ Engineering Engine** | Goal analysis, automated planning, quality gates, self-repair, documentation generation |
| **ðŸ“‹ Audit System** | Event capture middleware, 17 categories, search, CSV/JSON export, retention policies |
| **ðŸ‘· Worker Fleet** | Distributed job execution, 21-state machine, auto-reconnect, async handlers |
| **ðŸŒ Offline-First** | 100% LAN operation, no internet required after initial setup |

---

## ðŸ—ï¸ Architecture

```
Master (FastAPI :8000)          Workers (FastAPI :8001+)
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ REST API (131 routes)â”‚        â”‚ State Machine       â”‚
â”‚ WebSocket (JWT auth) â”‚â—„â”€â”€â”€â”€â”€â”€â–ºâ”‚ Job Execution       â”‚
â”‚ Scheduler            â”‚        â”‚ Path Validation     â”‚
â”‚ AI Runtime           â”‚        â”‚ Async IO            â”‚
â”‚ SQLite Database      â”‚        â”‚ Auto-Reconnect      â”‚
â”‚ Rate Limiter         â”‚        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Web Dashboard (:3000)â”‚
â”‚ Desktop Apps (Tauri) â”‚
â”‚ CLI (aicluster.exe)  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## ðŸš€ Quick Start

```powershell
# 1. Install Python 3.12+
# 2. Clone
git clone https://github.com/manojkumar12-maker/AICluster-Studio.git
cd AICluster-Studio

# 3. Install dependencies
pip install -r backend/requirements.txt
pip install slowapi pytest pytest-asyncio httpx

# 4. Start the Master
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Note the admin password printed to console
# 6. Open http://localhost:3000 and log in
```

ðŸ“– **[Full Installation Guide](docs/INSTALLATION.md)** â€” covers installer, portable, source, and production deployment.

---

## ðŸ” Security Posture

| Severity | v2.0.0 | v2.0.0 |
|----------|--------|--------|
| CRITICAL | 4 | **0** |
| HIGH | 5 | **0** |
| Authentication | None | JWT on all endpoints |
| Worker Auth | None | Worker secret required |
| Rate Limiting | None | 100/min default |
| CORS | `*` allowed | Restricted to configured origins |

---

## ðŸ“¸ Documentation

| Guide | Description |
|-------|-------------|
| [INSTALLATION.md](docs/INSTALLATION.md) | Complete installation guide |
| [QUICK_START.md](docs/QUICK_START.md) | 5-minute setup |
| [FIRST_CLUSTER.md](docs/FIRST_CLUSTER.md) | Multi-worker cluster setup |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production hardening |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 45 common problems |
| [FAQ.md](docs/FAQ.md) | Frequently asked questions |
| [UPGRADING.md](docs/UPGRADING.md) | Upgrade from v2.0.0 |

---

## ðŸ› ï¸ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic V2 |
| **Database** | SQLite (via aiosqlite) |
| **Frontend** | Next.js 15, React 18, TypeScript, TailwindCSS |
| **Desktop** | Tauri v2 (Rust + React) |
| **State** | Zustand, TanStack React Query |
| **AI** | Ollama, llama.cpp, OpenAI-compatible |
| **Auth** | JWT (python-jose), bcrypt |
| **Packaging** | PyInstaller, Inno Setup 6 |
| **Testing** | pytest (74 tests), Vitest |

---

## ðŸ“ Directory Structure

```
AICluster/
â”œâ”€â”€ backend/              # FastAPI master server (Python)
â”‚   â”œâ”€â”€ app/              # Application code (15+ subsystems)
â”‚   â”œâ”€â”€ tests/            # 60 pytest tests
â”‚   â””â”€â”€ data/             # Runtime database & secrets
â”œâ”€â”€ worker/               # Worker agent (Python)
â”‚   â”œâ”€â”€ app/              # Worker application code
â”‚   â””â”€â”€ tests/            # 14 pytest tests
â”œâ”€â”€ frontend/             # Next.js 15 dashboard
â”œâ”€â”€ studio/               # Tauri v2 desktop IDE
â”œâ”€â”€ master-control-center/# Tauri cluster management app
â”œâ”€â”€ worker-control-center/# Tauri worker management app
â”œâ”€â”€ build/                # Build system & verification
â”œâ”€â”€ scripts/              # PowerShell & Python tools
â”œâ”€â”€ config/               # YAML configuration
â”œâ”€â”€ shared/               # Shared types & protocols
â”œâ”€â”€ docs/                 # Documentation (8 guides)
â”œâ”€â”€ dist/                 # Built executables
â”œâ”€â”€ VERSION               # 1.3.1
â””â”€â”€ CHANGELOG.md          # Release history
```

---

## âœ… Build

Executables are built using PyInstaller:

| File | Size | For |
|------|------|-----|
| `AIClusterRuntime.exe` | ~53 MB | Unified Master + Worker service |
| `aicluster.exe` | ~29 MB | CLI |
| `AIClusterStudio.exe` | ~12 MB | Desktop IDE |

All in `release/` organized by role.

---

## ðŸ“‹ Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 22H2 | Windows 11 Pro |
| **CPU** | 4 cores (i5) | 8+ cores (i7/Ultra) |
| **RAM** | 16 GB | 32-64 GB |
| **Disk** | 10 GB SSD | 50 GB NVMe |
| **Python** | 3.12 | 3.12 |

---

## ðŸ¤ Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

---

## ðŸ“„ License

AICluster is Â© 2026 Manoj Kumar Mathangi. All rights reserved. See [NOTICE.md](NOTICE.md).

---

<div align="center">
Made with â¤ï¸ by the AICluster Contributors
</div>
