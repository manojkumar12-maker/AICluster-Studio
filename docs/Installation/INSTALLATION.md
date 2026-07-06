# AICluster v2.0.0 Installation Guide

## Introduction

### What is AICluster?

AICluster transforms a local area network (LAN) of Windows computers into a unified AI compute cluster. It runs entirely offline â€” no internet connection is required after initial setup.

> **Key Principle**: AICluster is designed for organizations that need AI compute power without cloud dependency. All communication stays on your LAN.

### What Can You Do With It?

- Run large language models (LLMs) across multiple machines
- Distribute AI workloads across available workers
- Execute computational jobs (file scanning, hashing, counting)
- Run multi-agent AI collaboration workflows
- Index and search code repositories with AI context
- Build autonomous engineering pipelines

### Architecture Overview

```
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚         YOUR LAN (192.168.1.x)          â”‚
                    â”‚                                         â”‚
                    â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
                    â”‚  â”‚       MASTER SERVER (:8000)       â”‚   â”‚
                    â”‚  â”‚  FastAPI + SQLite + WebSocket     â”‚   â”‚
                    â”‚  â”‚  AI Runtime + Scheduler + API     â”‚   â”‚
                    â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
                    â”‚               â”‚                         â”‚
                    â”‚     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”               â”‚
                    â”‚     â”‚         â”‚         â”‚               â”‚
                    â”‚     â–¼         â–¼         â–¼               â”‚
                    â”‚  â”Œâ”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”                â”‚
                    â”‚  â”‚ W1 â”‚  â”‚ W2 â”‚  â”‚ W3 â”‚  ...           â”‚
                    â”‚  â”‚    â”‚  â”‚    â”‚  â”‚    â”‚                 â”‚
                    â”‚  â””â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”˜                â”‚
                    â”‚     Worker Fleet (:8001+)               â”‚
                    â”‚                                         â”‚
                    â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
                    â”‚  â”‚  Web     â”‚  â”‚  Studio  â”‚            â”‚
                    â”‚  â”‚Dashboard â”‚  â”‚ (Tauri)  â”‚            â”‚
                    â”‚  â”‚ :3000    â”‚  â”‚ :5174    â”‚            â”‚
                    â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Components

| Component | Description | Default Port |
|-----------|-------------|-------------|
| **Master Server** | Central coordinator. REST API, WebSocket, scheduler, AI runtime, database. | 8000 |
| **Worker** | Compute node. Registers with master, executes jobs, reports results. | 8001+ |
| **Web Dashboard** | Browser-based UI for monitoring the cluster. | 3000 |
| **Master Control Center** | Desktop app for cluster management. | 8800 |
| **Worker Control Center** | Desktop app for worker setup and monitoring. | 8900 |
| **AICluster Studio** | Desktop IDE with AI-assisted development. | 5174 |
| **CLI** | Command-line tools for scripting and automation. | â€” |
| **Installer** | Single-file setup wizard (Inno Setup). | â€” |

## System Requirements

### Minimum Requirements (Single Machine, Development)

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10 22H2, Windows 11 23H2+ |
| **CPU** | Intel Core i5-8400 / AMD Ryzen 5 2600 (4+ cores) |
| **RAM** | 16 GB |
| **Disk** | 10 GB free (SSD recommended) |
| **Python** | 3.12 or 3.13 |
| **Network** | Local network with DHCP |

### Recommended Requirements (4-Worker Cluster)

| Component | Master | Per Worker |
|-----------|--------|------------|
| **OS** | Windows 11 Pro | Windows 11 Pro |
| **CPU** | Intel Core i5-12400 (6+ cores) | Intel Core Ultra 5 (8+ cores) |
| **RAM** | 32 GB | 32 GB |
| **Disk** | 50 GB SSD | 50 GB SSD |
| **Python** | 3.12 | 3.12 |
| **Network** | 1 Gbps LAN | 1 Gbps LAN |

### Production Requirements (8+ Worker Cluster)

| Component | Master | Per Worker |
|-----------|--------|------------|
| **OS** | Windows 11 Pro / Windows Server 2022 | Windows 11 Pro |
| **CPU** | Intel Core i7-13700 / AMD Ryzen 7 7700 | Intel Core Ultra 7 / AMD Ryzen 7 |
| **RAM** | 64 GB | 64 GB |
| **Disk** | 200 GB NVMe | 100 GB NVMe |
| **Python** | 3.12 | 3.12 |
| **Network** | 2.5 Gbps LAN | 1 Gbps LAN |
| **Firewall** | Port 8000 open (inbound) | Port 8001+ open (inbound) |

### Software Prerequisites

| Software | Version | Required For | Notes |
|----------|---------|-------------|-------|
| **Python** | 3.12.x or 3.13.x | Master, Worker | Auto-installed by setup |
| **Node.js** | 20.x LTS | Web Dashboard | Only for source build |
| **Rust/Cargo** | 1.70+ | Tauri desktop apps | Only for source build |
| **Visual C++ Redistributable** | 2015-2022 | PyInstaller binaries | Auto-installed by setup |
| **PowerShell** | 5.1+ | Scripts | Built into Windows |
| **Git** | 2.x | Source installation | Optional |

> **Important**: AICluster does NOT require a GPU. Workers can contribute CPU-only compute. For AI model inference, GPU acceleration is beneficial but not mandatory.

## Download

### Option 1: Installer (Recommended)

Download `AIClusterSetup-2.0.0.exe` from the [GitHub Releases page](https://github.com/manojkumar12-maker/AICluster-Studio/releases).

**Size**: ~500 MB
**Contents**: Master Server, Worker, Web Dashboard, desktop apps, Python 3.12, VC++ redist

### Option 2: Portable ZIP

Download `AICluster-2.0.0-portable.zip` from the releases page.

**Size**: ~400 MB
**Contents**: All binaries, no installer. Extract to any folder.

### Option 3: Source Code

```powershell
git clone https://github.com/manojkumar12-maker/AICluster-Studio.git
cd AICluster-Studio
git checkout v2.0.0
```

**Size**: ~50 MB (source)
**Contents**: Full source code. Requires Python, Node.js, Rust to build.

## Installation Methods

### Method 1: Installer (Easiest â€” Recommended for Most Users)

**Advantages**:
- One-click setup
- Automatic Python installation if missing
- Automatic VC++ Redist installation if missing
- Firewall rules configured automatically
- Start Menu shortcuts created
- All components in one place

**Disadvantages**:
- Large download (~500 MB)
- Requires admin rights
- Less control over individual components

### Method 2: Portable ZIP

**Advantages**:
- No installation required
- Runs from USB drive
- No admin rights needed (for runtime)
- Easy to uninstall (delete folder)

**Disadvantages**:
- Python must be installed separately
- No automatic firewall configuration
- No Start Menu shortcuts
- Manual configuration required

### Method 3: Source Build

**Advantages**:
- Full control over build options
- Can modify source code
- Latest changes on develop branch
- Smaller initial download

**Disadvantages**:
- Requires Python, Node.js, Rust toolchain
- Build takes 15-30 minutes
- Complex setup process
- Requires Git

### Method 4: Developer Mode

**Advantages**:
- Hot-reload for frontend development
- Debug mode with detailed logging
- Can run without building
- Best for contributors

**Disadvantages**:
- Requires all development toolchains
- Slower than compiled binaries
- Not suitable for production

## Installer Walkthrough

### Step 1: Launch the Installer

Double-click `AIClusterSetup-2.0.0.exe`.

> Screenshot: Installer Welcome Screen

**Expected behavior**: Windows SmartScreen may show a warning. Click "More info" then "Run anyway".

**Duration**: 5-10 seconds

### Step 2: Welcome Page

Click **Next** to continue.

### Step 3: License Agreement

Read the license terms. Select **I accept the agreement** and click **Next**.

### Step 4: Select Components

Choose installation type:

| Option | Description | Disk Space |
|--------|-------------|------------|
| **Full** (recommended) | All components | ~500 MB |
| **Compact** | Master + Dashboard only | ~200 MB |
| **Custom** | Choose individual components | Varies |

Individual components:

| Component | Default | Description |
|-----------|---------|-------------|
| Master Server | Required | Central coordinator (required) |
| Web Dashboard | Yes | Browser-based monitoring UI |
| Worker Service | No | Compute node (install on every machine) |
| Master Control Center | Yes | Desktop app for cluster management |
| Worker Control Center | No | Desktop app for worker setup |
| AICluster Studio | No | Desktop IDE |
| CLI Tools | No | Command-line utilities |

> **Tip**: For a first-time installation, select **Full**. You can always add or remove components later.

### Step 5: Select Destination Location

Default: `C:\Program Files\AICluster`

> **Note**: This requires admin privileges. If installing as a standard user, choose a location in your user folder (e.g., `C:\Users\YourName\AICluster`).

### Step 6: Preflight Check

The installer will scan your system for:

| Check | What It Verifies | If Missing |
|-------|-----------------|------------|
| Python 3.12+ | Python interpreter installed | Installer will download and install Python |
| VC++ Redist | Visual C++ runtime | Installer will download and install |
| Disk space | Enough free space | Warning shown |
| Windows version | 10/11 compatible | Warning shown for unsupported versions |

> **Screenshot**: Preflight check screen

**Duration**: 10-30 seconds

### Step 7: Firewall Configuration

The installer will prompt to add Windows Firewall rules:

- **Port 8000** (Master Server) â€” Inbound rule
- **Port 3000** (Web Dashboard) â€” Optional inbound rule

> **Important**: If you select "No" during installation, you must manually add firewall rules. Workers will not be able to connect to the master without port 8000 open.

### Step 8: Installation

The installer copies all files to the destination folder.

**Progress indicators**:
- Files being extracted
- Python installer progress (if downloading)
- VC++ redist progress (if downloading)

**Duration**: 2-5 minutes

> **Screenshot**: Installation progress

### Step 9: Post-Installation Verification

The installer runs automated verification:

- Master binary is a valid PE file
- Worker binary is a valid PE file
- Desktop apps are valid
- Configuration files exist
- Python version check

### Step 10: Finish

Options on completion:

- [x] Launch Master Server
- [x] Open Web Dashboard
- [ ] Show README

Click **Finish**.

> **Screenshot**: Finish screen

## Installed Folder Layout

After installation, the folder structure looks like:

```
C:\Program Files\AICluster\
â”œâ”€â”€ master\
â”‚   â””â”€â”€ AIClusterRuntime.exe --mode master          # Master server executable
â”œâ”€â”€ worker\
â”‚   â””â”€â”€ AIClusterRuntime.exe --mode worker          # Worker executable
â”œâ”€â”€ studio\
â”‚   â””â”€â”€ AIClusterStudio.exe          # Desktop IDE
â”œâ”€â”€ master-control\
â”‚   â””â”€â”€ MasterControlCenter.exe      # Cluster management desktop app
â”œâ”€â”€ worker-control\
â”‚   â””â”€â”€ WorkerControlCenter.exe      # Worker management desktop app
â”œâ”€â”€ cli\
â”‚   â””â”€â”€ aicluster.exe                # Command-line tools
â”œâ”€â”€ plugins\                         # User-installed plugins (empty initially)
â”œâ”€â”€ models\                          # Local LLM models (empty initially)
â”œâ”€â”€ logs\                            # Runtime logs (created on first run)
â”œâ”€â”€ config\
â”‚   â”œâ”€â”€ default.yaml                 # Default configuration
â”‚   â”œâ”€â”€ development.yaml             # Development overrides
â”‚   â””â”€â”€ production.yaml              # Production overrides
â”œâ”€â”€ data\                            # Runtime data (SQLite DB, secrets)
â”œâ”€â”€ assets\
â”‚   â”œâ”€â”€ manifest.json                # App manifest
â”‚   â””â”€â”€ icons\                       # Application icons
â”œâ”€â”€ AIClusterRuntime.exe --mode master              # Convenience shortcut
â”œâ”€â”€ AIClusterRuntime.exe --mode worker              # Convenience shortcut
â””â”€â”€ unins000.exe                     # Uninstaller
```

### Folder Details

| Folder | Purpose | Contents |
|--------|---------|----------|
| `master/` | Master server binary and dependencies | EXE, DLLs, Python runtime |
| `worker/` | Worker binary and dependencies | EXE, DLLs, Python runtime |
| `studio/` | Studio desktop app | EXE, frontend bundle |
| `master-control/` | Cluster management app | EXE, frontend bundle |
| `worker-control/` | Worker management app | EXE, frontend bundle |
| `cli/` | Command-line tools | EXE |
| `plugins/` | Plugin storage | Plugin directories, manifests |
| `models/` | LLM model storage | Model files (gguf, etc.) |
| `logs/` | Runtime logs | Rotating log files |
| `config/` | Configuration files | YAML configuration |
| `data/` | Persistent data | SQLite database, secret keys |
| `assets/` | Static resources | Icons, manifests |

## First Startup

### Launching the Master Server

**From the installer completion screen**: Check "Launch Master Server" and click Finish.

**From Start Menu**: Start > AICluster > AICluster Master

**From command line**:
```powershell
& "C:\Program Files\AICluster\AIClusterRuntime.exe --mode master"
```

**From source**:
```powershell
cd AICluster\backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### What Happens on First Start

1. The master server starts on port 8000
2. A SQLite database is created at `data/aicluster.db`
3. An admin user is created with a **random password**
4. The initial password is printed to the console:

```
ADMIN PASSWORD: X7k9mP2qR4vW8nJ3
```

> **âš ï¸ CRITICAL**: Save this password. You will need it to log in. The password is shown only once on the first startup. If you lose it, delete the database and restart to generate a new password.

5. A JWT secret key is auto-generated and stored in `data/secret.key`
6. The scheduler starts (processes job queue every 2 seconds)
7. The offline worker checker starts (marks workers offline after 30s of no heartbeat)
8. The WebSocket server is ready for real-time connections

### Open the Dashboard

Open your browser and navigate to:

```
http://localhost:3000
```

> **Note**: The Web Dashboard runs on port 3000 (Next.js). If you see a blank page, ensure the dashboard server is running. From source: `cd frontend && npm run dev`

**Login**:
- Username: `admin`
- Password: (the password printed on first startup)

> **Screenshot**: Login page

### Verify the Master is Running

```powershell
# Health check (no authentication required)
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"ok","database":"connected","worker_count":0,"version":"1.0.0"}
```

```powershell
# Login (save the token for subsequent requests)
$login = curl.exe -s -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'

# Extract token
$token = ($login | ConvertFrom-Json).access_token

# Dashboard (requires authentication)
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/dashboard
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AICLUSTER_SECRET_KEY` | Auto-generated | JWT signing key |
| `AICLUSTER_ADMIN_PASSWORD` | Auto-generated | Initial admin password |
| `AICLUSTER_MASTER_SECRET` | â€” | Shared secret for worker authentication |
| `HOST` | `0.0.0.0` | Master server bind address |
| `PORT` | `8000` | Master server port |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/aicluster.db` | Database connection string |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

### Configuration Files

**`config/default.yaml`** â€” Base configuration:
```yaml
server:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000

database:
  url: sqlite+aiosqlite:///./data/aicluster.db

auth:
  algorithm: HS256
  access_token_expire_minutes: 60

worker:
  timeout_seconds: 15
  max_workers: 100
  heartbeat_interval: 5

logging:
  level: INFO
```

**`config/production.yaml`** â€” Production overrides:
```yaml
server:
  cors_origins:
    - http://dashboard.internal:3000
```

## Starting a Worker

### On the Same Machine

```powershell
# From source
cd AICluster\worker
pip install -r requirements.txt
set AICLUSTER_MASTER_SECRET=YOUR_MASTER_SECRET_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The master's secret key is stored in `data/secret.key`.

### On a Different Machine

1. Install AICluster on the worker machine (using the installer or portable)
2. Configure the worker:
   - Edit `worker\config.json`:
     ```json
     {
       "master_url": "http://MASTER_IP:8000",
       "worker_name": "WORKER-PC-NAME",
       "worker_secret": "SAME_SECRET_AS_MASTER"
     }
     ```
   - Or set environment variable:
     ```powershell
     set AICLUSTER_MASTER_SECRET=SAME_SECRET_AS_MASTER
     ```
3. Start the worker:
   ```powershell
   & "C:\Program Files\AICluster\AIClusterRuntime.exe --mode worker"
   ```
4. Verify the worker appears on the master:
   ```powershell
   curl.exe -s -H "Authorization: Bearer $token" http://MASTER_IP:8000/api/v1/workers
   ```

> **Screenshot**: Worker connected in dashboard

## Verification

### Verify the Master

```powershell
# Health check
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","database":"connected","worker_count":0,...}

# API Documentation (OpenAPI)
curl http://localhost:8000/openapi.json
# Expected: OpenAPI specification in JSON
```

### Verify Authentication

```powershell
# Without token (should fail)
curl.exe -s -o nul -w "%{http_code}" http://localhost:8000/api/v1/dashboard
# Expected: 401

# With valid token
curl.exe -s -o nul -w "%{http_code}" -H "Authorization: Bearer $token" http://localhost:8000/api/v1/dashboard
# Expected: 200
```

### Verify Worker Connection

```powershell
# List all workers
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/workers
# Expected: JSON array with registered workers
```

### Verify Job Execution

```powershell
# Create a test job
curl.exe -s -X POST http://localhost:8000/api/v1/jobs `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"type":"echo","payload":{"message":"hello world"},"priority":2}'

# List jobs
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/jobs
```

### Verify WebSocket

```powershell
# Using a WebSocket client (wscat, or browser console)
# Connect with token:
# ws://localhost:8000/ws?token=YOUR_JWT_TOKEN
# You should receive dashboard updates periodically
```

## Logs

### Log Location

```
C:\Program Files\AICluster\logs\
â”œâ”€â”€ aicluster.log          # Main log file
â”œâ”€â”€ aicluster.log.1        # Rotated log
â”œâ”€â”€ aicluster.log.2        # Rotated log
â”œâ”€â”€ aicluster.log.3        # Rotated log
â”œâ”€â”€ aicluster.log.4        # Rotated log
â””â”€â”€ aicluster.log.5        # Rotated log
```

### Log Format

```
2026-07-04 14:35:26,529 [INFO] app.scheduler: Job 'abc123' created
2026-07-04 14:35:27,102 [WARNING] app.worker_manager: Worker offline: HP-01
2026-07-04 14:35:28,045 [ERROR] app.scheduler: Failed to assign job: timeout
```

### Log Levels

| Level | Description | Color |
|-------|-------------|-------|
| `DEBUG` | Detailed diagnostic information | Gray |
| `INFO` | Normal operational messages | Green |
| `WARNING` | Unexpected but handled situations | Yellow |
| `ERROR` | Failures that don't stop the application | Red |
| `CRITICAL` | Failures that stop the application | Red/Bold |

### Log Rotation

- Maximum file size: 10 MB
- Maximum backup files: 5
- Oldest log is automatically deleted

### Reading Logs

```powershell
# View the last 50 lines
Get-Content "C:\Program Files\AICluster\logs\aicluster.log" -Tail 50

# Watch logs in real-time
Get-Content "C:\Program Files\AICluster\logs\aicluster.log" -Wait

# Filter by level
Select-String -Path "C:\Program Files\AICluster\logs\aicluster.log" -Pattern "ERROR"
```

## Uninstall

### Using the Uninstaller

1. Open **Settings > Apps > Installed Apps**
2. Find **AICluster** in the list
3. Click **Uninstall**
4. Follow the uninstaller prompts

Or run the uninstaller directly:
```powershell
& "C:\Program Files\AICluster\unins000.exe"
```

### What Remains After Uninstall

| Item | Location | Persistent? |
|------|----------|-------------|
| Database | `C:\Program Files\AICluster\data\` | **Yes** |
| Models | `C:\Program Files\AICluster\models\` | **Yes** |
| Config files | `C:\Program Files\AICluster\config\` | **Yes** |
| Logs | `C:\Program Files\AICluster\logs\` | **Yes** |
| Firewall rules | Windows Firewall | **No** |
| Start Menu shortcuts | Start Menu | **No** |

### Complete Removal

To completely remove AICluster including all data:

```powershell
# Stop any running processes
Stop-Process -Name "AIClusterMaster" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "AIClusterWorker" -Force -ErrorAction SilentlyContinue

# Run the uninstaller
& "C:\Program Files\AICluster\unins000.exe" /SILENT

# Remove remaining data (WARNING: this deletes all databases and models!)
Remove-Item -Path "C:\Program Files\AICluster" -Recurse -Force

# Remove firewall rules
netsh advfirewall firewall delete rule name="AICluster Master (8000)"
netsh advfirewall firewall delete rule name="AICluster Dashboard (3000)"
```

> **âš ï¸ Warning**: Deleting the data folder permanently removes all databases, user accounts, and job history. Back up any important data first.

---

# Troubleshooting

## Master Won't Start

### Symptom: Port 8000 already in use

**Cause**: Another application is using port 8000.

**Solution**:
```powershell
# Find what's using port 8000
netstat -ano | findstr ":8000"

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>

# Or change the master port
set PORT=8001
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Symptom: "Database initialization failed"

**Cause**: Corrupted database or permission issue.

**Solution**:
```powershell
# Remove the database and restart (data will be lost)
Remove-Item "data\aicluster.db" -Force
```

### Symptom: Missing Python

**Cause**: Python is not installed.

**Solution**: Run the installer which includes Python, or install manually:
```powershell
# Check Python
python --version
# Expected: Python 3.12.x

# Install from python.org if missing
```

## Worker Won't Connect

### Symptom: "401 Unauthorized"

**Cause**: Worker secret mismatch.

**Solution**: The worker's `worker_secret` must match the master's `secret_key`:
```powershell
# Get the master's secret key
Get-Content "C:\Program Files\AICluster\data\secret.key"

# Set it on the worker
set AICLUSTER_MASTER_SECRET=<secret_from_master>
```

### Symptom: "Connection refused"

**Cause**: Master is not running or firewall is blocking.

**Solution**:
```powershell
# Verify master is running
curl http://MASTER_IP:8000/api/v1/health

# Check firewall
netsh advfirewall firewall show rule name="AICluster Master (8000)"
```

### Symptom: Worker shows as "offline"

**Cause**: Network interruption or worker process crashed.

**Solution**: The master automatically marks workers as offline after 30 seconds without a heartbeat. The worker will automatically retry and reconnect.

## Firewall

### Add Firewall Rule Manually

```powershell
# Open port 8000 for master
netsh advfirewall firewall add rule name="AICluster Master (8000)" `
  dir=in action=allow protocol=TCP localport=8000

# Open port 3000 for dashboard (if needed)
netsh advfirewall firewall add rule name="AICluster Dashboard (3000)" `
  dir=in action=allow protocol=TCP localport=3000
```

### Remove Firewall Rule

```powershell
netsh advfirewall firewall delete rule name="AICluster Master (8000)"
```

## JWT Issues

### "Invalid token" error

**Cause**: Expired token or incorrect secret key.

**Solution**:
```powershell
# Get a fresh token
$login = curl.exe -s -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'
$token = ($login | ConvertFrom-Json).access_token
```

### Token expires quickly

**Cause**: Default token expiration is 60 minutes. Can be configured:

```powershell
set ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 hours
```

## Worker Secret Issues

### "Invalid worker secret"

**Cause**: The worker_secret doesn't match the master's secret_key.

**Solution**: Copy the contents of `data/secret.key` from the master to the worker's `config.json` as `worker_secret`.

## Database

### Database is locked

**Cause**: Multiple connections or a long-running transaction.

**Solution**: Wait a few seconds and retry. If persistent, restart the master server.

### Database is corrupted

**Cause**: Unexpected shutdown during write.

**Solution**:
```powershell
# Stop the master
# Delete the database
Remove-Item "data\aicluster.db" -Force
# Restart the master (new database will be created)
```
> **Warning**: This deletes all users, jobs, and configuration stored in the database. Worker registrations and admin user will need to be re-created.

## Permissions

### "Access denied" when writing logs

**Cause**: The AICluster process doesn't have write permission to the logs directory.

**Solution**: Run the master as administrator, or grant write permission:
```powershell
icacls "C:\Program Files\AICluster\logs" /grant Users:(OI)(CI)W
```

## Port Conflicts

### Port 3000 in use

```powershell
# Find process
netstat -ano | findstr ":3000"
taskkill /F /PID <PID>
```

### Port 8000 in use

```powershell
# Use the cluster management UI or command line to change
set PORT=8001
```

## Missing DLL

### "VCRUNTIME140.dll not found"

**Cause**: Visual C++ Redistributable is not installed.

**Solution**: Run the installer which includes VC++ redist, or install manually:
```powershell
# Download from Microsoft
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

## Installer Failures

### SmartScreen blocks the installer

**Solution**: Click "More info" then "Run anyway". This is a new, unsigned application â€” SmartScreen will block it until enough users have run it.

### "Installation failed" during Python download

**Solution**: The installer needs internet access to download Python. If offline, pre-install Python 3.12 manually from python.org.

### "Disk space insufficient"

**Solution**: Free up disk space or choose a different installation drive.

---

# Reference

## Ports Summary

| Port | Component | Protocol | Direction |
|------|-----------|----------|-----------|
| 8000 | Master Server | HTTP/WebSocket | Inbound |
| 8001+ | Worker | HTTP | Inbound |
| 3000 | Web Dashboard | HTTP | Inbound |
| 8800 | Master Control Center | HTTP | Inbound |
| 8900 | Worker Control Center | HTTP | Inbound |
| 5174 | Studio | HTTP | Inbound |

## Executable Names

| Executable | Path | Purpose |
|------------|------|---------|
| `AIClusterRuntime.exe --mode master` | `master/` | Master server |
| `AIClusterRuntime.exe --mode worker` | `worker/` | Worker daemon |
| `AIClusterStudio.exe` | `studio/` | Desktop IDE |
| `MasterControlCenter.exe` | `master-control/` | Cluster management |
| `WorkerControlCenter.exe` | `worker-control/` | Worker management |
| `aicluster.exe` | `cli/` | CLI tools |
| `AIClusterSetup-2.0.0.exe` | â€” | Installer |

## Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `AICLUSTER_SECRET_KEY` | Master | JWT signing secret |
| `AICLUSTER_ADMIN_PASSWORD` | Master | Initial admin password |
| `AICLUSTER_MASTER_SECRET` | Worker | Worker authentication |
| `AICLUSTER_BUILD_VERSION` | Build | Version override |
| `DATABASE_URL` | Master | Database connection |
| `CORS_ORIGINS` | Master | Allowed origins |
| `HOST` | Master | Bind address |
| `PORT` | Master | Bind port |
| `LOG_LEVEL` | All | Logging level |

## Firewall Rules

| Rule Name | Port | Protocol |
|-----------|------|----------|
| `AICluster Master (8000)` | 8000 | TCP |
| `AICluster Dashboard (3000)` | 3000 | TCP |

## Default Paths

| Item | Path |
|------|------|
| Installation | `C:\Program Files\AICluster\` |
| Database | `C:\Program Files\AICluster\data\aicluster.db` |
| JWT Secret | `C:\Program Files\AICluster\data\secret.key` |
| Logs | `C:\Program Files\AICluster\logs\aicluster.log` |
| Config | `C:\Program Files\AICluster\config\default.yaml` |
| Worker Config | `C:\Program Files\AICluster\worker\config.json` |
