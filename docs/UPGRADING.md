# AICluster v1.3.1 — Upgrade Guide

## Overview

This guide covers upgrading from AICluster v1.3.0 to v1.3.1.

**Version**: v1.3.1
**Previous**: v1.3.0
**Upgrade type**: Security & Stability (breaking changes to authentication)

---

## What Changed

### Breaking Changes

| Change | Impact | Details |
|--------|--------|---------|
| **JWT auth required** | ALL API consumers | Every API request needs `Authorization: Bearer <token>` header |
| **Worker registration requires auth** | Existing workers | Workers must include `worker_secret` in configuration |
| **WebSocket requires token** | Real-time clients | Connection URL must include `?token=<jwt>` |
| **CORS restricted** | Cross-origin frontends | Only configured origins are allowed |
| **Rate limiting active** | High-frequency clients | 100 requests/minute default limit |
| **Admin password randomized** | Automated setups | Password is now generated on first run |

### New Features

- JWT secret auto-generation (`data/secret.key`)
- Rate limiting (slowapi middleware)
- Authentication on all 131 API endpoints
- Worker path traversal protection
- Async IO for worker handlers (non-blocking)
- No-op reporter prevents worker crashes
- Event-based scheduler shutdown
- Job duration (`duration_ms`) now persisted

---

## Pre-Upgrade Checklist

Before upgrading, complete these steps:

- [ ] **Back up the database**: `Copy-Item "data\aicluster.db" "data\aicluster.db.v130.bak"`
- [ ] **Back up the secret key** (if manually set): `Copy-Item "data\secret.key" "data\secret.key.v130.bak"`
- [ ] **Back up configuration**: `Copy-Item "config\default.yaml" "config\default.yaml.v130.bak"`
- [ ] **Note all worker IP addresses**: You'll need to update worker configurations
- [ ] **Download the v1.3.1 installer or source**
- [ ] **Plan for downtime**: Authentication changes may require client updates

---

## Upgrade Paths

### Path A: Fresh Install (Recommended for Production)

1. Back up existing data
2. Uninstall v1.3.0
3. Install v1.3.1
4. Restore data (if needed)

### Path B: In-Place Upgrade (Development/Testing)

1. Stop all services
2. Install v1.3.1 over existing installation
3. Update configurations
4. Restart services

### Path C: Source Upgrade

```powershell
cd AICluster-Studio
git fetch --tags
git checkout v1.3.1
pip install -r backend/requirements.txt
pip install slowapi
```

---

## Upgrade Steps

### Step 1: Prepare

```powershell
# 1. Note the current admin password
# If you don't know it, set it via env var before starting v1.3.1:
$env:AICLUSTER_ADMIN_PASSWORD = "YourKnownPassword"

# 2. Back up the database
Copy-Item "C:\Program Files\AICluster\data\aicluster.db" "C:\Backup\aicluster.db.v130"

# 3. Back up configuration
Copy-Item "C:\Program Files\AICluster\config" "C:\Backup\config.v130" -Recurse

# 4. Note the existing JWT secret (if you set one manually)
Get-Content "C:\Program Files\AICluster\data\secret.key"
```

### Step 2: Stop Services

```powershell
# Stop the master
Stop-Process -Name "AIClusterMaster" -Force -ErrorAction SilentlyContinue

# Stop all workers
Stop-Process -Name "AIClusterWorker" -Force -ErrorAction SilentlyContinue

# Stop the dashboard
Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
```

### Step 3: Install v1.3.1

**Using the installer**:
```powershell
# Run AIClusterSetup-1.3.1.exe
# The installer will upgrade over the existing installation
```

**Using source**:
```powershell
git fetch --tags
git checkout v1.3.1
pip install -r backend/requirements.txt
pip install slowapi
```

### Step 4: Preserve the Existing Database

The v1.3.1 installer should preserve your existing `data\` and `config\` directories. If not:

```powershell
# Restore database
Copy-Item "C:\Backup\aicluster.db.v130" "C:\Program Files\AICluster\data\aicluster.db" -Force

# Restore secret key
Copy-Item "C:\Backup\secret.key.v130" "C:\Program Files\AICluster\data\secret.key" -Force
```

### Step 5: Configure Authentication

**Set the admin password** (if restoring an existing DB, the old password persists):
```powershell
$env:AICLUSTER_ADMIN_PASSWORD = "YourExistingPassword"
```

**Set the JWT secret** (must match what workers expect):
```powershell
$env:AICLUSTER_SECRET_KEY = "YourExistingSecretKey"
```

Or copy the backed-up secret key:
```powershell
Copy-Item "C:\Backup\secret.key.v130" "C:\Program Files\AICluster\data\secret.key" -Force
```

### Step 6: Update Worker Configurations

Every worker's `config.json` must include the `worker_secret`:

```json
{
  "master_url": "http://MASTER_IP:8000",
  "worker_name": "WORKER-1",
  "worker_secret": "SAME_AS_MASTER_SECRET_KEY"
}
```

Or set the environment variable:
```powershell
$env:AICLUSTER_MASTER_SECRET = "SAME_AS_MASTER_SECRET_KEY"
```

### Step 7: Start Services

```powershell
# Start the master
& "C:\Program Files\AICluster\AIClusterMaster.exe"

# Start workers
& "C:\Program Files\AICluster\AIClusterWorker.exe"
```

### Step 8: Verify

```powershell
# 1. Health check
curl http://localhost:8000/api/v1/health
# Expected: 200 OK

# 2. Login
$login = curl.exe -s -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'
# Expected: 200 with access_token

# 3. Check workers
$token = ($login | ConvertFrom-Json).access_token
curl.exe -s -H "Authorization: Bearer $token" http://localhost:8000/api/v1/workers
# Expected: Workers listed with status "online"

# 4. Run integration tests
python scripts/run-integration-test.py
# Expected: 40/40 tests pass
```

---

## Database Migration

v1.3.1 adds a `duration_ms` column to the `jobs` table. The `create_all()` method in SQLAlchemy does NOT modify existing tables. If upgrading an existing v1.3.0 database:

```powershell
# Run this SQL against your existing database
python -c "
import aiosqlite
import asyncio

async def migrate():
    db = await aiosqlite.connect('data/aicluster.db')
    try:
        await db.execute('ALTER TABLE jobs ADD COLUMN duration_ms FLOAT')
        await db.commit()
        print('Migration: added duration_ms column')
    except Exception as e:
        print(f'Migration skipped (column may already exist): {e}')
    finally:
        await db.close()

asyncio.run(migrate())
"
```

---

## Rollback

### Rollback from v1.3.1 to v1.3.0

```powershell
# 1. Stop all services
Stop-Process -Name "AIClusterMaster" -Force
Stop-Process -Name "AIClusterWorker" -Force

# 2. Restore v1.3.0 binaries
# Either reinstall v1.3.0 or restore from backup

# 3. Restore database (v1.3.1 DB is forward-compatible)
# Remove the duration_ms column if causing issues

# 4. Restore configuration
Copy-Item "C:\Backup\config.v130" "C:\Program Files\AICluster\config" -Recurse -Force

# 5. Start v1.3.0 (authentication is no longer enforced)
```

> **Note**: Downgrading disables all security fixes in v1.3.1. Only roll back if absolutely necessary. The breaking changes (auth required) are fundamental to v1.3.1.

---

## Post-Upgrade Verification Checklist

- [ ] Master starts without errors
- [ ] Login returns JWT token
- [ ] All workers appear as "online"
- [ ] Worker heartbeats are received
- [ ] Jobs can be created and assigned
- [ ] Dashboard shows correct data
- [ ] WebSocket connects with token
- [ ] Rate limiting returns 429 on excess requests
- [ ] All 40 integration tests pass
- [ ] No new error messages in logs
