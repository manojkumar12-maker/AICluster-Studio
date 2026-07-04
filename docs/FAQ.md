# AICluster v1.3.1 — Frequently Asked Questions

---

## 1. General

### Q1: What is AICluster?
AICluster is an offline-first AI cluster management platform that turns a LAN of Windows computers into a unified AI compute cluster. It includes a master server (FastAPI + SQLite), a worker fleet, desktop apps (Tauri), a web dashboard, and an AI runtime that supports Ollama, llama.cpp, and OpenAI-compatible providers.

### Q2: Does AICluster require internet access?
No. AICluster is designed for 100% offline LAN operation. All communication stays on your local network — no internet is required after initial setup and model downloads.

### Q3: What is the license?
AICluster is copyright © 2026 Manoj Kumar Mathangi. All rights reserved. A formal open-source license has not yet been determined and will be announced in a future release. See NOTICE.md for details.

### Q4: Is AICluster open source?
The source code is publicly available on GitHub, but it is not yet released under an open-source license. All rights are reserved pending a final license decision.

### Q5: What are the main features?
AI runtime with multi-provider support, DAG-based workflow engine, 12 default multi-agent roles, plugin system with 16 plugin types, repository intelligence (code indexer/search/metrics), autonomous engineering engine, audit system with 17 categories, Tauri desktop IDE (Studio), Master/Worker Control Centers, LAN discovery, and JWT-authenticated security.

### Q6: What operating systems are supported?
Windows 10 21H2+ and Windows 11 23H2+ are the primary targets. Linux and macOS are experimental and not officially supported for production use.

### Q7: What technology stack does AICluster use?
Backend: Python 3.12+, FastAPI, SQLAlchemy 2.0, SQLite, Pydantic V2. Frontend: Next.js 15, React 18, TypeScript. Desktop: Tauri v2 (Rust). AI Providers: Ollama, llama.cpp, OpenAI-compatible.

### Q8: Can I use AICluster on a single machine?
Yes. AICluster runs perfectly on a single machine — the master server, worker, dashboard, and AI runtime can all run on one PC. This is the recommended way to evaluate the platform.

### Q9: How is AICluster different from running Ollama directly?
AICluster adds distributed job scheduling, multi-agent orchestration, workflow automation, repository intelligence, a cluster management UI, plugin system, audit logging, and the ability to pool compute across multiple machines. Ollama is just one of three supported AI providers.

### Q10: Is AICluster production-ready?
Yes. v1.3.1 includes production hardening: JWT auth on all 131 endpoints, rate limiting, CORS restrictions, auto-generated secrets, path traversal prevention, 44+ backend tests, 14+ worker tests, health checks, diagnostics, monitoring, and automated build verification.

---

## 2. Installation

### Q11: What are the minimum system requirements?
Windows 10 21H2+, Intel Core i5 / Ryzen 5 (4+ cores), 8 GB RAM (16 GB recommended), 10 GB free disk (SSD recommended), Python 3.12+, and a LAN with DHCP.

### Q12: What installation methods are available?
(1) Inno Setup installer (AIClusterSetup-1.3.1.exe, ~500 MB, recommended). (2) Portable ZIP (~400 MB, no admin needed). (3) Source build from GitHub (~50 MB, requires Python/Node/Rust). (4) Developer mode with hot-reload.

### Q13: Do I need admin rights to install?
The installer requires admin rights because it installs to Program Files, configures firewall rules, and optionally installs Python/VC++ redist. The portable ZIP can be extracted and run without admin rights (Python must be pre-installed).

### Q14: Does the installer include Python?
Yes. The Inno Setup installer includes Python 3.12 and will auto-install it if not detected. It also includes the Visual C++ Redistributable.

### Q15: How do I install from source?
Clone the repo, checkout v1.3.1, create a Python venv, install backend requirements, install frontend dependencies (npm), then run `uvicorn app.main:app` in the backend directory. See INSTALLATION.md for full steps.

### Q16: Which Python version is required?
Python 3.12.x or 3.13.x. Older versions are not supported.

### Q17: Do I need Node.js and Rust?
Only for source builds. The installer and portable ZIP include pre-compiled binaries for all components.

### Q18: Can I install only specific components?
Yes. The installer offers Full, Compact (Master + Dashboard only), and Custom installation types where you can select individual components (Worker, Control Centers, Studio, CLI).

---

## 3. Configuration

### Q19: How do I configure the master server?
Edit `config/default.yaml` or set environment variables like `HOST`, `PORT`, `DATABASE_URL`, `AICLUSTER_SECRET_KEY`, `AICLUSTER_ADMIN_PASSWORD`, `CORS_ORIGINS`, and `LOG_LEVEL`.

### Q20: How do I configure a worker?
Create or edit `worker/config.json` with fields: `master_url`, `worker_name`, `worker_port`, `worker_secret`, `cpu_limit`, `ram_limit_gb`, `heartbeat_interval`, `poll_interval`, `log_level`. Alternatively, set the `AICLUSTER_MASTER_SECRET` environment variable.

### Q21: How are secrets handled?
In v1.3.1, all secrets are auto-generated on first run. The JWT signing key is stored in `data/secret.key` (32-byte random key). The admin password is randomly generated and printed once to the console. Worker secrets must match the master's secret key.

### Q22: What ports does AICluster use?
Master Server: 8000 (HTTP/WebSocket). Web Dashboard: 3000. Master Control Center: 8800. Worker Control Center: 8900. Studio: 5174. Workers: 8001+.

### Q23: How do I change the master port?
Set the `PORT` environment variable or change `server.port` in `config/default.yaml`.

### Q24: What environment variables are available?
Key variables: `AICLUSTER_SECRET_KEY`, `AICLUSTER_ADMIN_PASSWORD`, `AICLUSTER_MASTER_SECRET`, `HOST`, `PORT`, `DATABASE_URL`, `CORS_ORIGINS`, `LOG_LEVEL`.

### Q25: How do I configure CORS for a remote dashboard?
Set `CORS_ORIGINS` to a comma-separated list of allowed origins, e.g., `http://192.168.1.100:3000,http://dashboard.internal:3000`.

### Q26: Can I use a custom database path?
Yes. Set `DATABASE_URL` to any SQLite path, e.g., `DATABASE_URL=sqlite+aiosqlite:///D:/data/aicluster.db`.

---

## 4. Workers

### Q27: How many workers can I connect?
The default maximum is 100 workers. This is configurable via `workers.max_workers` in `config/default.yaml`.

### Q28: What are the worker system requirements?
Minimum: 4 CPU cores, 8 GB RAM, 5 GB free disk, Windows 10/11, Python 3.12. Recommended: 8+ cores, 32 GB RAM, SSD, 1 Gbps LAN.

### Q29: Can I run workers on laptops?
Yes. Workers enforce resource limits (default: 25% CPU, 8 GB RAM) and run at BELOW_NORMAL process priority to avoid interfering with user tasks.

### Q30: How does the worker communicate with the master?
Workers communicate over HTTP/HTTPS to the master's REST API and WebSocket endpoints. They register, send heartbeats every 5 seconds, poll for jobs every 5 seconds, and report progress/results.

### Q31: What happens if a worker disconnects?
The master marks the worker as "offline" after 30 seconds without a heartbeat. The worker automatically retries connection with exponential backoff (1s, 2s, 5s, 10s, 30s, 60s) and re-registers when it reconnects.

### Q32: Can workers run AI models?
Workers are general-purpose compute agents (file scanning, hashing, counting, etc.). AI model inference runs on the master or on machines running Ollama/llama.cpp. However, you can configure the master's AI runtime to use remote providers running on worker machines via the OpenAI-compatible provider.

### Q33: What job types do workers support?
Built-in handlers: echo, sleep, dir_scan, hash_file, count_files. Custom job handlers can be added via the plugin system.

### Q34: Can I pause and resume workers remotely?
Yes. The Master Control Center and API support pausing/resuming individual workers. Paused workers stop polling for jobs but continue sending heartbeats.

---

## 5. AI / Models

### Q35: Do I need a GPU for AICluster?
No. AICluster works entirely on CPU. A GPU significantly accelerates AI inference (3-5x for 7B models), but it is not required. CPU-only systems can run 1-3B models comfortably and 7B models at ~5-15 tokens/second depending on CPU.

### Q36: How do I set up Ollama for AICluster?
Install Ollama from ollama.com, pull models (e.g., `ollama pull qwen3-coder`), and ensure it runs at `http://localhost:11434`. AICluster auto-discovers Ollama on first AI API call.

### Q37: What AI providers are supported?
Three providers: Ollama (recommended, broadest model support), llama.cpp (lightweight, CPU-first), and any OpenAI-compatible endpoint (vLLM, LM Studio, NVIDIA NIM, DeepSeek API, etc.).

### Q38: What models are recommended?
7B parameter models offer the best quality-to-resource ratio: qwen3-coder (code generation), deepseek-coder (architecture review), llama3.1 (general), gemma3 (documentation). For low-RAM systems: phi-3 (3.8B) or qwen3-coder:1.5b.

### Q39: How does model routing work?
The ModelRouter selects the best model based on task type. Code generation uses qwen3-coder, architecture review uses deepseek-coder, summarization uses phi-3, etc. Each task has a fallback chain if the preferred model is unavailable.

### Q40: Can I use remote AI providers on the network?
Yes. Register an OpenAI-compatible provider with the remote machine's URL, e.g., `base_url: "http://192.168.1.101:11434/v1"`. This allows worker machines with GPUs to serve models to the cluster.

### Q41: How much RAM do models need?
1-3B models: 2-4 GB RAM. 7-8B models (Q4): 6-8 GB RAM. 13-14B models: 12+ GB RAM. 33B models: 24+ GB RAM. Ollama and llama.cpp handle model quantization.

### Q42: Can I run multiple models simultaneously?
Yes. Configure `OLLAMA_MAX_LOADED_MODELS` (default varies by system). A 32 GB system can run 2-3 7B models simultaneously. Use the profiles system (fast/balanced/maximum_quality/offline_low_ram/custom) to control resource usage.

---

## 6. Security

### Q43: How is authentication handled?
AICluster uses JWT (JSON Web Tokens) with bcrypt password hashing. All 131 API endpoints require authentication (except public routes: health, login, docs). Tokens expire after 60 minutes (configurable). Admin users have elevated privileges.

### Q44: Are communications encrypted?
AICluster uses HTTP by default (LAN-only). For production, enable HTTPS via a reverse proxy (nginx, Caddy) with TLS certificates. WebSocket connections also require a valid JWT token.

### Q45: How are worker communications secured?
Workers authenticate using a shared secret (`worker_secret`) that must match the master's secret key from `data/secret.key`. Worker registration, heartbeat, and job polling all require this authentication.

### Q46: What firewall rules are needed?
Port 8000 (TCP inbound) must be open on the master for workers to connect. Port 3000 (TCP inbound) is optional for remote dashboard access. The installer configures these automatically.

### Q47: What security fixes were in v1.3.1?
Replaced hardcoded JWT secret with auto-generated 32-byte key, replaced hardcoded "admin123" with random password generation, enforced JWT auth on all endpoints, restricted CORS, added rate limiting (slower API, 100/min), added WebSocket auth, added worker secret authentication, added path traversal prevention, and validated SQL injection safety.

---

## 7. Troubleshooting

### Q48: Master won't start — "port already in use"
Run `netstat -ano | findstr ":8000"` to find the process, then `taskkill /F /PID <PID>`. Alternatively, change the master port via `set PORT=8001`.

### Q49: Worker shows "401 Unauthorized" when connecting
The worker secret does not match the master's secret key. Copy the contents of `data/secret.key` from the master machine to the worker's `config.json` as `worker_secret` or set the `AICLUSTER_MASTER_SECRET` environment variable.

### Q50: Worker shows as "offline" on the dashboard
The master automatically marks workers offline after 30 seconds without a heartbeat. Check network connectivity between the machines, ensure the worker process is running, and verify the firewall allows port 8000 inbound on the master.

### Q51: Where can I find logs?
Logs are stored in `C:\Program Files\AICluster\logs\aicluster.log` (installed) or `AICluster/logs/aicluster.log` (source). Logs rotate at 10 MB with 5 backups. Use `Get-Content` with `-Wait` for real-time monitoring.

### Q52: How do I report a bug or get help?
Open an issue on the GitHub repository (github.com/aicluster/aicluster). For security vulnerabilities, email security@aicluster.local. See CONTRIBUTING.md for contribution guidelines.

---

## 8. Upgrading

### Q53: How do I upgrade from v1.3.0 to v1.3.1?
If using the installer: download and run the new installer — it will upgrade the existing installation. If using source: `git pull && git checkout v1.3.1` and re-install dependencies. The SQLite database is forward-compatible within the 1.3.x line.

### Q54: Will I lose data when upgrading?
No. The SQLite database (`data/aicluster.db`), configuration files, and model files are preserved during upgrade. The v1.3.1 release contains zero breaking changes to the database schema.

### Q55: Can I roll back to a previous version?
Yes. Keep a backup of your `data/` directory and `config/` directory before upgrading. To roll back, stop the master, restore the previous version's binaries, and restore the backed-up data directory. If the schema has changed, restore the database from backup.
