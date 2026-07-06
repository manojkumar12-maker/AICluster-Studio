# AICluster v2.0.0 Quick Start Guide

## 5-Minute Setup

This guide gets AICluster running on a single machine in under 5 minutes.

### Prerequisites

- Windows 10 or 11
- Python 3.12 installed (`python --version`)
- Administrator access

### Step 1: Install

Choose one method:

**A: Download the installer**
```powershell
# Download from GitHub Releases
# Run: AIClusterSetup-2.0.0.exe
# Select "Full" installation
```

**B: From source (if you have git)**
```powershell
git clone https://github.com/manojkumar12-maker/AICluster-Studio.git
cd AICluster-Studio
git checkout v2.0.0
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio httpx slowapi
```

### Step 2: Start the Master

**If using the installer**:
Start > AICluster > AICluster Master

**If using source**:
```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> Screenshot: Master starting in terminal

**Look for the admin password in the output:**
```
ADMIN PASSWORD: X7k9mP2qR4vW8nJ3
```
**Copy this password â€” you will need it to log in.**

### Step 3: Log In

Open your browser to: **http://localhost:3000**

If the dashboard isn't running, start it:
```powershell
cd frontend
npm install
npm run dev
```

Login with:
- **Username**: `admin`
- **Password**: (the password from Step 2)

> Screenshot: Dashboard after login

### Step 4: Verify

Run these commands in a new terminal:

```powershell
# Check master health
curl http://localhost:8000/api/v1/health

# Get a token (replace PASSWORD with your admin password)
$body = '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'
$login = curl.exe -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d $body
$token = ($login | ConvertFrom-Json).access_token

# View the dashboard
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/dashboard

# Expected: worker counts, job counts, system metrics
```

### Step 5: Start a Worker (Optional)

```powershell
cd worker
pip install -r requirements.txt
set AICLUSTER_MASTER_SECRET=<master_secret_from_data\secret.key>
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Step 6: Create Your First Job

```powershell
# Create an echo job
curl.exe -s -X POST http://localhost:8000/api/v1/jobs `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"type":"echo","payload":{"message":"Hello AICluster!"},"priority":2}'

# List jobs
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/jobs
```

### What's Next?

- **Add more workers**: Install AICluster on other machines and configure them as workers
- **Run AI models**: Install Ollama or llama.cpp on any worker
- **Build workflows**: Use the API to create DAG-based task pipelines
- **Explore the API**: Full documentation at `http://localhost:8000/docs`

### Need Help?

- See [INSTALLATION.md](INSTALLATION.md) for full installation guide
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- See [FAQ.md](FAQ.md) for frequently asked questions
