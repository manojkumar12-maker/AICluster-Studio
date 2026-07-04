# AICluster v1.3.1 — Building Your First Cluster

## Overview

This guide walks through building a multi-machine AICluster from scratch. You will set up a master server and connect 3 worker machines.

### Architecture

```
                    ┌─────────────────────────────────────┐
                    │         MASTER MACHINE               │
                    │     Intel i5-12400, 32GB RAM         │
                    │  ┌───────────────────────────────┐  │
                    │  │  Master Server (:8000)         │  │
                    │  │  Web Dashboard (:3000)         │  │
                    │  │  Master Control Center (:8800) │  │
                    │  └───────────────────────────────┘  │
                    │        192.168.1.100                │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────┼──────────────────────┐
                    │              │                      │
                    ▼              ▼                      ▼
           ┌────────────┐  ┌────────────┐      ┌────────────┐
           │ WORKER 1   │  │ WORKER 2   │      │ WORKER 3   │
           │ Core Ultra5│  │ Core Ultra7│      │ Core i5    │
           │ 32GB RAM   │  │ 64GB RAM   │      │ 16GB RAM   │
           │ :8001      │  │ :8001      │      │ :8001      │
           │ 192.168.1.101│ │ 192.168.1.102│   │ 192.168.1.103│
           └────────────┘  └────────────┘      └────────────┘
```

### Prerequisites

- 4 Windows machines on the same LAN
- All machines have Python 3.12 installed
- All machines have .NET VC++ redist installed
- Administrator access on all machines
- Network: All machines can ping each other

## Step 1: Set Up the Master Machine

### 1.1 Install AICluster

On the master machine (192.168.1.100):

```powershell
# Option A: Installer
# Download and run AIClusterSetup-1.3.1.exe
# Select: Full installation

# Option B: From source
git clone https://github.com/manojkumar12-maker/AICluster-Studio.git
cd AICluster-Studio
pip install -r backend/requirements.txt
```

### 1.2 Configure the Master

Edit `config/default.yaml` or set environment variables:

```powershell
# Set a fixed JWT secret (important: share this with workers)
$env:AICLUSTER_SECRET_KEY = "your-32-byte-random-secret-key-here"

# Set an admin password
$env:AICLUSTER_ADMIN_PASSWORD = "StrongAdminPassword123!"
```

> **⚠️ Important**: The `AICLUSTER_SECRET_KEY` must be the SAME on the master and ALL workers. Workers authenticate using the master's secret key.

### 1.3 Configure Firewall

```powershell
# Open port 8000 for workers to connect
netsh advfirewall firewall add rule name="AICluster Master" `
  dir=in action=allow protocol=TCP localport=8000
```

### 1.4 Start the Master

```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify it's running:
```powershell
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","database":"connected","worker_count":0,...}
```

### 1.5 Get the Master's Secret Key

```powershell
# The master generates a secret key on first start
Get-Content "data\secret.key"
# Copy this value — you'll need it for every worker
```

> Screenshot: Master terminal showing secret key location

## Step 2: Set Up Worker Machines

Repeat these steps for each worker machine (192.168.1.101, .102, .103).

### 2.1 Install AICluster Worker

```powershell
# Option A: Installer (select only "Worker Service" component)
# Or download portable and extract

# Option B: From source
git clone https://github.com/manojkumar12-maker/AICluster-Studio.git
cd AICluster-Studio
pip install -r worker/requirements.txt
```

### 2.2 Configure the Worker

Create or edit `worker/config.json`:

```json
{
  "master_url": "http://192.168.1.100:8000",
  "worker_name": "WORKER-1",
  "worker_port": 8001,
  "worker_secret": "paste-master-secret-key-here",
  "cpu_limit": 80,
  "ram_limit_gb": 16,
  "log_level": "INFO"
}
```

Or use environment variables:
```powershell
$env:AICLUSTER_MASTER_SECRET = "paste-master-secret-key-here"
```

### 2.3 Configure Worker Firewall

```powershell
# Open worker port (needed if master initiates connections)
netsh advfirewall firewall add rule name="AICluster Worker" `
  dir=in action=allow protocol=TCP localport=8001
```

### 2.4 Start the Worker

```powershell
cd worker
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 2.5 Verify Worker Connection

On the master machine, check that the worker appears:

```powershell
# Get a token
$login = curl.exe -s -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"StrongAdminPassword123!"}'
$token = ($login | ConvertFrom-Json).access_token

# List workers
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/workers
```

Expected output shows the registered worker with status "online".

> Screenshot: Worker list in dashboard

## Step 3: Verify the Cluster

### 3.1 Check All Workers

```powershell
# After all 3 workers are registered
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/workers

# Expected: Array with 3 worker objects, all with status "online"
```

### 3.2 Check Dashboard Metrics

```powershell
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/dashboard

# Expected:
# {
#   "total_workers": 3,
#   "online": 3,
#   "offline": 0,
#   "idle": 3,
#   "busy": 0,
#   "average_cpu": <average>,
#   "average_ram": <average>,
#   "running_jobs": 0
# }
```

### 3.3 Test Job Distribution

Create jobs and verify they're assigned to workers:

```powershell
# Create 3 jobs
for ($i = 1; $i -le 3; $i++) {
  curl.exe -s -X POST http://localhost:8000/api/v1/jobs `
    -H "Authorization: Bearer $token" `
    -H "Content-Type: application/json" `
    -d "{\"type\":\"echo\",\"payload\":{\"message\":\"Job $i\"},\"priority\":2}"
}

# Check job status
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/jobs
```

## Step 4: Add AI Models

### 4.1 Install Ollama (on any worker)

```powershell
# Download from https://ollama.com/download/windows
# Install and run Ollama

# Pull a model
ollama pull deepseek-coder:6.7b
ollama pull llama3.2:3b
```

### 4.2 Configure AI Runtime

On the master, register the AI provider:

```powershell
curl.exe -s -X POST http://localhost:8000/api/v1/ai/models/register `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"name":"deepseek-coder","provider":"ollama","model_type":"chat","context_window":16384,"max_tokens":4096,"api_url":"http://WORKER_IP:11434"}'
```

## Step 5: Monitor the Cluster

### 5.1 Using the Dashboard

Open `http://localhost:3000` in a browser. The dashboard shows:

- Total workers online/offline
- Average CPU and RAM usage across the cluster
- Running and queued jobs
- System logs

> Screenshot: Cluster dashboard

### 5.2 Using the API

```powershell
# Get system logs
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/api/v1/logs?level=INFO"

# Get production monitoring
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/production/monitoring
```

## Step 6: Test Failure Recovery

### 6.1 Worker Disconnect

Stop a worker process. Within 30 seconds, the master marks it as "offline":

```powershell
# The worker should auto-reconnect when restarted
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/workers
# Status shows "offline" for disconnected worker
```

### 6.2 Worker Reconnect

Restart the worker. It re-registers and returns to "online" status within seconds.

### 6.3 Master Restart

Stop and restart the master. Workers detect the connection loss and automatically retry registration:

```
Worker log:
[INFO] Connection to master lost. Retrying in 5s...
[INFO] Re-registering with master...
[INFO] Worker registered successfully. ID: abc-123
```

## Configuration Reference

### Worker config.json

```json
{
  "master_url": "http://MASTER_IP:8000",
  "worker_name": "FRIENDLY-NAME",
  "worker_port": 8001,
  "worker_secret": "MASTER_SECRET_KEY",
  "cpu_limit": 80,
  "ram_limit_gb": 16,
  "heartbeat_interval": 5,
  "poll_interval": 5,
  "log_level": "INFO"
}
```

### Master Environment Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `AICLUSTER_SECRET_KEY` | `a1b2c3d4...` | JWT signing key (shared with workers) |
| `AICLUSTER_ADMIN_PASSWORD` | `MyP@ssw0rd!` | Initial admin password |
| `CORS_ORIGINS` | `http://localhost:3000,http://192.168.1.100:3000` | Allowed browser origins |

## Troubleshooting Cluster

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Worker shows "offline" | No heartbeat received in 30s | Check network connectivity |
| Worker can't register | Port 8000 blocked on master | Check Windows Firewall |
| Worker gets 401 | Worker secret mismatch | Copy master's `data/secret.key` to worker config |
| Master won't start | Port conflict | Change port via `PORT` env var |
| Jobs not assigned | No online workers | Check worker status, restart worker |
| High CPU on master | Too many workers | Reduce heartbeat frequency, add workers gradually |
