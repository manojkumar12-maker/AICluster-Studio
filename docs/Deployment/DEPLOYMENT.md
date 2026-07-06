# AICluster v2.0.0 â€” Production Deployment Guide

---

## Table of Contents

1. [Production Architecture](#1-production-architecture)
2. [Security Hardening](#2-security-hardening)
3. [Network Configuration](#3-network-configuration)
4. [Backup Strategy](#4-backup-strategy)
5. [Monitoring](#5-monitoring)
6. [High Availability](#6-high-availability)
7. [Performance Tuning](#7-performance-tuning)
8. [Windows Service Configuration](#8-windows-service-configuration)
9. [Update Strategy](#9-update-strategy)
10. [Disaster Recovery](#10-disaster-recovery)
11. [Security Checklist](#11-security-checklist)
12. [Maintenance](#12-maintenance)

---

## 1. Production Architecture

```
                         Internet
                            |
                      [Firewall]
                            |
                   [Load Balancer]
                     /            \
                    /              \
            [Master Node]      [Master Node]       (Active/Passive HA pair)
               |                    |
         [Shared Storage]     [Shared Storage]     (SQLite DB + models on DFS/NFS)
               |                    |
     +---------+---------+    +-----+------+
     |         |         |    |     |      |
  [Worker1] [Worker2] [Worker3] ...  [WorkerN]
     |         |         |    |     |      |
  [GPU:0]   [GPU:1]   [GPU:2]     [GPU:N]
```

### Component Description

| Component | Role | Spec (Minimum) |
|-----------|------|----------------|
| **Master** | Scheduler, API gateway, job queue | 8 vCPU, 16 GB RAM, 200 GB SSD |
| **Worker** | Executes training/inference tasks | 16 vCPU, 64 GB RAM, 500 GB SSD, 1+ GPU |
| **Shared Storage** | Model artifacts, dataset cache, DB | 10 GbE, 2 TB+ NVMe, replicated |
| **Load Balancer** | TLS termination, routing | HAProxy / Nginx / F5 |

### Port Map

| Port | Service | Bind | Protocol |
|------|---------|------|----------|
| 443 | Master API (TLS) | 0.0.0.0 | TCP |
| 6443 | Master gRPC (TLS) | Master internal | TCP |
| 9090 | Metrics (Prometheus) | 127.0.0.1 | TCP |
| 9091 | Health check | 0.0.0.0 | TCP |
| 9876 | Worker â†” Master heartbeat | Workers | TCP |
| 9877 | Worker task stream | Workers | TCP |

---

## 2. Security Hardening

### 2.1 Windows Defender Exclusions

Run on **every node** (master and worker):

```powershell
# AICluster directories
Add-MpPreference -ExclusionPath "C:\Program Files\AICluster"
Add-MpPreference -ExclusionPath "C:\ProgramData\AICluster"
Add-MpPreference -ExclusionPath "C:\AIClusterData"

# Process exclusions
Add-MpPreference -ExclusionProcess "aicluster-master.exe"
Add-MpPreference -ExclusionProcess "aicluster-worker.exe"
Add-MpPreference -ExclusionProcess "aicluster-scheduler.exe"

# File extension exclusions for model artifacts
Add-MpPreference -ExclusionExtension ".pt"
Add-MpPreference -ExclusionExtension ".pth"
Add-MpPreference -ExclusionExtension ".onnx"
Add-MpPreference -ExclusionExtension ".gguf"
Add-MpPreference -ExclusionExtension ".bin"
```

Verify exclusions:

```powershell
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
```

### 2.2 Windows Firewall Rules

```powershell
# Allow master API (443)
New-NetFirewallRule -DisplayName "AICluster Master API" `
  -Direction Inbound -Protocol TCP -LocalPort 443 `
  -Action Allow -Profile Domain,Private

# Allow master gRPC internal
New-NetFirewallRule -DisplayName "AICluster Master gRPC" `
  -Direction Inbound -Protocol TCP -LocalPort 6443 `
  -Action Allow -Profile Private -RemoteAddress "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

# Allow worker heartbeat (management subnet only)
New-NetFirewallRule -DisplayName "AICluster Worker Heartbeat" `
  -Direction Inbound -Protocol TCP -LocalPort 9876 `
  -Action Allow -Profile Private -RemoteAddress "10.10.0.0/24"

# Allow worker task stream (management subnet only)
New-NetFirewallRule -DisplayName "AICluster Worker Task" `
  -Direction Inbound -Protocol TCP -LocalPort 9877 `
  -Action Allow -Profile Private -RemoteAddress "10.10.0.0/24"

# Block all other inbound by default (if not already)
Set-NetFirewallProfile -Profile Domain,Private,Public -DefaultInboundAction Block
```

### 2.3 TLS Certificate Deployment

```powershell
# Import certificate into LocalMachine\My
Import-PfxCertificate -FilePath "C:\Program Files\AICluster\certs\aicluster.pfx" `
  -CertStoreLocation "Cert:\LocalMachine\My" -Password (ConvertTo-SecureString -String "YOUR_PASSWORD" -AsPlainText -Force)

# Grant read access to NETWORK SERVICE
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*aicluster*"
$rsaCert = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
$keyFile = Get-ChildItem -Recurse "$env:ALLUSERSPROFILE\Microsoft\Crypto\RSA\MachineKeys" | Where-Object Name -match $rsaCert.Key.UniqueName
icacls $keyFile.FullName /grant "NETWORK SERVICE:R"
```

### 2.4 Additional Hardening

```powershell
# Disable weak TLS protocols
Disable-TlsCipherSuite -Name "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256"
Disable-TlsCipherSuite -Name "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA"
Disable-TlsCipherSuite -Name "TLS_RSA_WITH_AES_128_GCM_SHA256"

# Enable only strong ciphers
Enable-TlsCipherSuite -Name "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"
Enable-TlsCipherSuite -Name "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"

# Restrict local administrator group on workers
Remove-LocalGroupMember -Group "Administrators" -Member "Domain Users" -ErrorAction SilentlyContinue
```

---

## 3. Network Configuration

### 3.1 Static IP Assignment

```powershell
# Example: Master node static IP
New-NetIPAddress -InterfaceAlias "Ethernet0" `
  -IPAddress 10.10.0.10 -PrefixLength 24 `
  -DefaultGateway 10.10.0.1

Set-DnsClientServerAddress -InterfaceAlias "Ethernet0" `
  -ServerAddresses ("10.10.0.1", "10.10.0.2")
```

### 3.2 DNS Records

| Record | Type | Value | TTL |
|--------|------|-------|-----|
| master.aicluster.internal | A | 10.10.0.10 | 300 |
| master-dr.aicluster.internal | A | 10.10.0.11 | 300 |
| api.aicluster.example.com | CNAME | master.aicluster.internal | 60 |
| worker-ns.aicluster.internal | SRV | 0 10 9876 workers | 300 |

### 3.3 Switch / VLAN Configuration

| VLAN | Subnet | Purpose | Access |
|------|--------|---------|-------|
| VLAN 100 | 10.10.0.0/24 | Management (master + workers) | IT/admin only |
| VLAN 101 | 10.10.1.0/24 | Storage backend (NAS/DFS) | Master nodes |
| VLAN 102 | 10.10.2.0/24 | GPU direct (worker peer-to-peer) | Workers only |

### 3.4 Port Forwarding (Edge Router)

```text
External :443  â†’  LB internal :443  (AICluster API)
External :22   â†’  Jump box :22      (SSH admin â€” disable password auth)
```

### 3.5 Network Performance Tuning

```powershell
# Enable Receive Side Scaling (RSS) on GPU workers
Get-NetAdapterRss -Name "Ethernet*" | Set-NetAdapterRss -Enabled $true -NumberOfQueues 8

# Increase TCP window size
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global chimney=enabled
netsh int tcp set global rss=enabled

# Jumbo frames for storage VLAN
Set-NetAdapterAdvancedProperty -Name "Ethernet1" -DisplayName "Jumbo Packet" -DisplayValue "9014 Bytes"
```

---

## 4. Backup Strategy

### 4.1 Backup Schedule

| Asset | Tool | Frequency | Retention | Destination |
|-------|------|-----------|-----------|-------------|
| SQLite database (`cluster.db`) | `sqlite3 .backup` | Every 4 hours | 14 days | NFS share + off-site |
| Master config (`config.yaml`) | Robocopy | Daily | 30 versions | S3-compatible / DFS |
| Worker config | Automated git push | On change | Git history | Internal git server |
| Model artifacts | `rclone` | After training | Per-model policy | S3 / GCS / Azure Blob |
| Logs | Logrotate + S3 sync | Hourly | 90 days | Cold storage |
| TLS certs | Export-PfxCertificate | Monthly + on renew | 3 generations | Vault / HSM |

### 4.2 Database Backup Script

```powershell
# C:\Program Files\AICluster\scripts\backup-db.ps1
param(
  [string]$DbPath = "C:\ProgramData\AICluster\cluster.db",
  [string]$BackupRoot = "\\nas01\backups\aicluster\db"
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $BackupRoot $timestamp
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Hot backup via sqlite3 (no downtime)
$backupDb = Join-Path $backupDir "cluster.db"
& "C:\Program Files\AICluster\tools\sqlite3.exe" $DbPath ".backup '$backupDb'"

# Compress
Compress-Archive -Path $backupDb -DestinationPath "$backupDb.zip" -CompressionLevel Optimal
Remove-Item $backupDb

# Prune backups older than 14 days
Get-ChildItem $BackupRoot -Directory | Where-Object { $_.Name -lt (Get-Date).AddDays(-14).ToString("yyyyMMdd") } | Remove-Item -Recurse -Force

Write-Output "Backup complete: $backupDir"
```

### 4.3 Config Backup

```powershell
# Scheduled task: daily config backup
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-File `"C:\Program Files\AICluster\scripts\backup-config.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 03:00
Register-ScheduledTask -TaskName "AICluster Config Backup" -Action $action -Trigger $trigger -RunLevel Highest
```

### 4.4 Model Artifact Backup (rclone)

```powershell
# Install rclone
winget install rclone

# Configure S3 remote
rclone config create s3_models s3 provider AWS env_auth true region us-east-1

# Sync models hourly
rclone sync C:\AIClusterData\models\ s3_models:aicluster-models-prod --progress --checksum
```

---

## 5. Monitoring

### 5.1 Metrics Exposed

All nodes expose Prometheus metrics on `127.0.0.1:9090/metrics`:

| Metric | Type | Labels |
|--------|------|--------|
| `aicluster_jobs_total` | Counter | status, queue |
| `aicluster_job_duration_seconds` | Histogram | model, worker |
| `aicluster_workers_online` | Gauge | worker_id, gpu_count |
| `aicluster_gpu_utilization` | Gauge | worker_id, gpu_index |
| `aicluster_queue_depth` | Gauge | queue_name |
| `aicluster_memory_bytes` | Gauge | worker_id |
| `aicluster_heartbeat_missed_total` | Counter | worker_id |

### 5.2 Prometheus Scrape Config

```yaml
# /etc/prometheus/prometheus.yml  (on monitoring host)
scrape_configs:
  - job_name: 'aicluster-master'
    static_configs:
      - targets: ['10.10.0.10:9090', '10.10.0.11:9090']
    scheme: http
    metrics_path: /metrics

  - job_name: 'aicluster-workers'
    scrape_interval: 15s
    scheme: http
    metrics_path: /metrics
    dns_sd_configs:
      - names: ['_aicluster._tcp.aicluster.internal']
        type: 'SRV'
        port: 9090
```

### 5.3 Grafana Dashboard

Import the official AICluster dashboard from `C:\Program Files\AICluster\monitoring\grafana-dashboard.json`:

- **Quick status**: Worker count (live), queue depth, job success rate
- **Resource panel**: Per-worker GPU util, memory, disk I/O
- **Throughput**: Jobs/min, avg duration, p99 latency
- **Errors**: 5xx rate, worker disconnect events, scheduler backpressure

### 5.4 Log Monitoring

```powershell
# Forward Windows Event Log + AICluster logs to a centralized SIEM
# Example using Winlogbeat + Elastic stack:

# C:\Program Files\AICluster\scripts\install-winlogbeat.ps1
Invoke-WebRequest -Uri "https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-8.12.0-windows-x86_64.zip" -OutFile "$env:TEMP\winlogbeat.zip"
Expand-Archive -Path "$env:TEMP\winlogbeat.zip" -DestinationPath "C:\Program Files\Winlogbeat" -Force

# Configure winlogbeat to ship AICluster logs
@"
winlogbeat.event_logs:
  - name: Application
    event_id: 1000-2000
    tags: ["aicluster"]
output.elasticsearch:
  hosts: ["https://elastic.internal:9200"]
  username: "winlogbeat"
  password: "${ELASTIC_PASSWORD}"
"@ | Out-File -Encoding UTF8 "C:\Program Files\Winlogbeat\winlogbeat.yml"
```

### 5.5 Alerting Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: aicluster
    rules:
      - alert: WorkerDown
        expr: aicluster_workers_online < 3
        for: 2m
        labels: { severity: critical }
        annotations:
          summary: "Less than 3 workers online"

      - alert: QueueBacklog
        expr: aicluster_queue_depth > 100
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Job queue depth exceeds 100"

      - alert: HeartbeatMissed
        expr: rate(aicluster_heartbeat_missed_total[5m]) > 0.1
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "Workers missing heartbeats"

      - alert: HighJobFailureRate
        expr: rate(aicluster_jobs_total{status="failed"}[15m]) / rate(aicluster_jobs_total[15m]) > 0.05
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Job failure rate exceeds 5%"
```

---

## 6. High Availability

### 6.1 Master Failover

AICluster supports active/passive master failover:

```yaml
# C:\Program Files\AICluster\config.yaml  (both masters)
ha:
  mode: active-passive
  peer: "10.10.0.11:6443"  # other master
  virtual_ip: "10.10.0.20"
  health_check_interval_ms: 5000
  failover_timeout_ms: 15000
  shared_storage: "\\\\nas01\\aicluster\\data"
```

Failover behavior:
1. Passive master monitors active via heartbeat + health endpoint (`/health` on port 9091).
2. If active is unreachable for 15 seconds, passive promotes itself.
3. Passive assigns the virtual IP (`10.10.0.20`) and starts accepting API calls.
4. Workers automatically reconnect to the VIP.
5. Failed active master does **not** auto-rejoin â€” operator intervention required.

```powershell
# Promote passive master manually (while active is still up, for maintenance):
Invoke-RestMethod -Uri "http://localhost:9091/failover" -Method Post
```

### 6.2 Worker Redundancy

- Deploy **minimum 2x** the required worker count for critical queues.
- Workers are interchangeable â€” no worker holds exclusive state.
- If a worker disconnects mid-job, the scheduler re-queues the job after `heartbeat_timeout_ms` (default: 30s).
- Idempotent job execution is enforced via job IDs â€” duplicates are discarded.

```powershell
# Register a new worker pool (up to 32 workers per pool)
& "C:\Program Files\AICluster\aicluster-admin.exe" pool create `
  --name "gpu-pool-1" --min 2 --max 16 `
  --constraint "gpu.vendor=nvidia;gpu.memory>=16000"
```

### 6.3 Load Balancer Configuration (HAProxy example)

```haproxy
# /etc/haproxy/haproxy.cfg
frontend aicluster
  bind *:443 ssl crt /etc/ssl/certs/aicluster.pem
  mode tcp
  default_backend masters

backend masters
  mode tcp
  balance leastconn
  option tcp-check
  tcp-check connect port 6443
  server master1 10.10.0.10:6443 check inter 5s fall 3 rise 2
  server master2 10.10.0.11:6443 check inter 5s fall 3 rise 2 backup
```

---

## 7. Performance Tuning

### 7.1 Scheduler Settings

```yaml
# config.yaml â€” scheduler section
scheduler:
  max_concurrent_jobs: 64
  queue_depth_warning: 100
  queue_depth_critical: 500
  worker_assignment_timeout_ms: 10000
  backpressure_threshold: 0.85     # refuse new jobs when workers >85% utilized
  job_retry_limit: 3
  gang_scheduling: true             # all-or-nothing multi-worker jobs
  priority_classes:
    - name: critical
      weight: 100
      max_concurrent: 8
    - name: default
      weight: 50
      max_concurrent: 32
    - name: batch
      weight: 10
      max_concurrent: 64
```

### 7.2 Worker Limits

```yaml
# config.yaml â€” worker section
worker:
  max_parallel_tasks: 4             # per GPU
  gpu_memory_fraction: 0.90         # reserve 10% for system
  task_timeout_minutes: 120
  log_upload_concurrency: 2
  resource_limits:
    cpu_max: 0.80                   # do not exceed 80% CPU
    memory_max_gb: 56               # leave 8 GB for OS
    disk_min_free_gb: 50
```

### 7.3 Database Optimization

```powershell
# SQLite pragma tuning â€” applied at service start
# These are set automatically by aicluster-master.exe, but can be verified:
& "C:\Program Files\AICluster\tools\sqlite3.exe" "C:\ProgramData\AICluster\cluster.db" "
  PRAGMA journal_mode=WAL;
  PRAGMA synchronous=NORMAL;
  PRAGMA cache_size=-8000;          -- 8 MB cache
  PRAGMA busy_timeout=5000;
  PRAGMA temp_store=MEMORY;
  PRAGMA mmap_size=268435456;       -- 256 MB memory-mapped I/O
  PRAGMA page_size=4096;
"

# VACUUM monthly to reclaim space:
& "C:\Program Files\AICluster\tools\sqlite3.exe" "C:\ProgramData\AICluster\cluster.db" "VACUUM;"
```

### 7.4 Windows System Tuning

```powershell
# Power scheme: High performance
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

# Disable Nagle's algorithm for low-latency worker communication
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{GUID}" `
  -Name "TCPNoDelay" -Value 1 -PropertyType DWORD -Force

# Increase I/O priority for AICluster processes
$workers = Get-Process -Name "aicluster-worker" -ErrorAction SilentlyContinue
foreach ($w in $workers) { $w.PriorityClass = "High" }

# GPU compute mode (NVIDIA only)
& "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe" -pm 1   # persistence mode
& "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe" -pl 250  # power limit (watts, adjust per card)
```

---

## 8. Windows Service Configuration

### 8.1 Install NSSM

```powershell
# Download NSSM (Non-Sucking Service Manager)
$nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
$nssmZip = "$env:TEMP\nssm.zip"
Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
Expand-Archive -Path $nssmZip -DestinationPath "C:\Program Files\AICluster\tools" -Force
# Result: C:\Program Files\AICluster\tools\nssm-2.24\win64\nssm.exe
```

### 8.2 Register AICluster Master as a Service

```powershell
$nssm = "C:\Program Files\AICluster\tools\nssm-2.24\win64\nssm.exe"
$masterPath = "C:\Program Files\AICluster\bin\aicluster-master.exe"

& $nssm install AIClusterMaster $masterPath "--config" "C:\Program Files\AICluster\config.yaml"
& $nssm set AIClusterMaster DisplayName "AICluster Master Service"
& $nssm set AIClusterMaster Description "Handles job scheduling, queue management, and API serving for AICluster."
& $nssm set AIClusterMaster Start SERVICE_AUTO_START
& $nssm set AIClusterMaster AppDirectory "C:\Program Files\AICluster"
& $nssm set AIClusterMaster AppStdout "C:\ProgramData\AICluster\logs\master-stdout.log"
& $nssm set AIClusterMaster AppStderr "C:\ProgramData\AICluster\logs\master-stderr.log"
& $nssm set AIClusterMaster AppRotateFiles 1
& $nssm set AIClusterMaster AppRotateSeconds 86400
& $nssm set AIClusterMaster AppRotateBytes 10485760
& $nssm set AIClusterMaster ObjectName "NT AUTHORITY\NETWORK SERVICE"
& $nssm set AIClusterMaster AppRestartDelay 5000

Start-Service AIClusterMaster
```

### 8.3 Register AICluster Worker as a Service

```powershell
$workerPath = "C:\Program Files\AICluster\bin\aicluster-worker.exe"

& $nssm install AIClusterWorker $workerPath "--master" "https://master.aicluster.internal:443" "--worker-id" "$env:COMPUTERNAME"
& $nssm set AIClusterWorker DisplayName "AICluster Worker Service"
& $nssm set AIClusterWorker Description "Executes ML training and inference tasks assigned by the AICluster master."
& $nssm set AIClusterWorker Start SERVICE_AUTO_START
& $nssm set AIClusterWorker AppDirectory "C:\Program Files\AICluster"
& $nssm set AIClusterWorker AppStdout "C:\ProgramData\AICluster\logs\worker-stdout.log"
& $nssm set AIClusterWorker AppStderr "C:\ProgramData\AICluster\logs\worker-stderr.log"
& $nssm set AIClusterWorker AppRotateFiles 1
& $nssm set AIClusterWorker AppRotateSeconds 86400
& $nssm set AIClusterWorker AppRotateBytes 10485760
& $nssm set AIClusterWorker ObjectName "NT AUTHORITY\NETWORK SERVICE"
& $nssm set AIClusterWorker AppRestartDelay 5000
& $nssm set AIClusterWorker AppPriority HIGH_PRIORITY_CLASS

Start-Service AIClusterWorker
```

### 8.4 Service Management Commands

```powershell
# Status check
Get-Service AIClusterMaster, AIClusterWorker

# Restart (zero-downtime if HA is configured)
Restart-Service AIClusterMaster -Force
Restart-Service AIClusterWorker -Force

# View logs
Get-Content "C:\ProgramData\AICluster\logs\master-stdout.log" -Tail 100
Get-Content "C:\ProgramData\AICluster\logs\worker-stderr.log" -Tail 100

# Remove service
& $nssm remove AIClusterMaster confirm
& $nssm remove AIClusterWorker confirm
```

### 8.5 Service Recovery (Windows built-in)

```powershell
# Configure automatic restart on crash (NSSM handles this, but set OS fallback)
sc.exe failure AIClusterMaster reset=86400 actions=restart/5000/restart/10000/restart/30000
sc.exe failure AIClusterWorker  reset=86400 actions=restart/5000/restart/10000/restart/30000
```

---

## 9. Update Strategy

### 9.1 Version Compatibility

| From | To | Rolling Update | Downtime |
|------|----|----------------|----------|
| v2.0.0 | v2.0.0 | Yes | None |
| v1.2.x | v1.3.x | Workers first, then master | â‰¤ 30s |
| < v1.2 | v1.3 | Full redeployment | Planned |

### 9.2 Rolling Worker Update

```powershell
# 1. Drain one worker at a time
& "C:\Program Files\AICluster\aicluster-admin.exe" worker drain --worker-id "worker-01" --timeout 120

# 2. Wait until all running jobs complete (check dashboard or CLI)
& "C:\Program Files\AICluster\aicluster-admin.exe" worker status --worker-id "worker-01"

# 3. Stop the service
Stop-Service AIClusterWorker -Force

# 4. Replace binaries
Copy-Item "\\nas01\deploy\aicluster-v2.0.0\worker\*" "C:\Program Files\AICluster\bin\" -Recurse -Force

# 5. Start the service
Start-Service AIClusterWorker

# 6. Verify registration
& "C:\Program Files\AICluster\aicluster-admin.exe" worker list

# 7. Repeat for remaining workers (at most 50% of pool drained simultaneously)
```

### 9.3 Master Update Procedure

```powershell
# 1. Verify HA pair is healthy
& "C:\Program Files\AICluster\aicluster-admin.exe" ha status

# 2. Fail over to passive master (zero-downtime)
Invoke-RestMethod -Uri "http://10.10.0.10:9091/failover" -Method Post

# 3. Verify standby master is now active
Invoke-RestMethod -Uri "https://10.10.0.20:443/health"

# 4. Stop former active master
Stop-Service AIClusterMaster

# 5. Replace binaries
Copy-Item "\\nas01\deploy\aicluster-v2.0.0\master\*" "C:\Program Files\AICluster\bin\" -Recurse -Force

# 6. Migrate config (check for new/removed settings)
Copy-Item "\\nas01\deploy\aicluster-v2.0.0\config.yaml" "C:\Program Files\AICluster\config.yaml" -Confirm

# 7. Start former active master
Start-Service AIClusterMaster

# 8. Confirm it rejoins as passive
& "C:\Program Files\AICluster\aicluster-admin.exe" ha status

# 9. Repeat steps 2-8 on the other master when ready
```

### 9.4 Rollback Procedure

```powershell
# If update causes issues, redeploy previous version:
Copy-Item "\\nas01\deploy\aicluster-v2.0.0\bin\*" "C:\Program Files\AICluster\bin\" -Recurse -Force
Restart-Service AIClusterMaster
Restart-Service AIClusterWorker

# Revert database schema if needed:
& "C:\Program Files\AICluster\tools\sqlite3.exe" "C:\ProgramData\AICluster\cluster.db" ".read 'C:\Program Files\AICluster\migrations\rollback-v2.0.0.sql'"
```

---

## 10. Disaster Recovery

### 10.1 Recovery Prerequisites

```powershell
# Verify backup availability before starting recovery:
$backupDate = "2026-07-03-180000"
$backupPath = "\\nas01\backups\aicluster\db\$backupDate"
if (Test-Path $backupPath) {
    Write-Output "Backup found: $backupPath"
} else {
    throw "Backup not found at $backupPath"
}
```

### 10.2 Full Recovery Steps

```powershell
# 1. Provision replacement hardware (or rebuild from image)
# 2. Install Windows Server + prerequisites (VC++ redist, CUDA drivers)
# 3. Deploy AICluster binaries from backup share
Copy-Item "\\nas01\backups\aicluster\binaries\v2.0.0\*" "C:\Program Files\AICluster\" -Recurse -Force

# 4. Restore configuration
Copy-Item "\\nas01\backups\aicluster\config\v2.0.0\config.yaml" "C:\Program Files\AICluster\config.yaml"

# 5. Restore database
$restorePath = "\\nas01\backups\aicluster\db\2026-07-03-180000\cluster.db.zip"
Expand-Archive -Path $restorePath -DestinationPath "C:\ProgramData\AICluster\" -Force

# 6. Restore TLS certificates
Import-PfxCertificate -FilePath "\\nas01\backups\aicluster\certs\aicluster.pfx" `
  -CertStoreLocation "Cert:\LocalMachine\My" -Exportable

# 7. Restore model artifacts (selective â€” only latest production models)
rclone copy "s3_models:aicluster-models-prod/" "C:\AIClusterData\models\" --progress

# 8. Register services (see Section 8)
# 9. Start master
Start-Service AIClusterMaster

# 10. Verify health
Invoke-RestMethod -Uri "https://localhost:443/health"

# 11. Register workers â€” for each worker node:
Start-Service AIClusterWorker
```

### 10.3 Partial Recovery Scenarios

| Scenario | RPO | RTO | Steps |
|----------|-----|-----|-------|
| Single worker disk failure | 0 (no state) | 15 min | Replace disk, reinstall worker, re-register |
| DB corruption | â‰¤4 hours (backup interval) | 30 min | Restore DB from latest backup, replay logs |
| Full rack failure | â‰¤4 hours | 4 hours | Provision new nodes, restore DB + config |
| Region outage | â‰¤24 hours (off-site backup) | 8 hours | Cross-region deployment, restore from S3 backup |
| Accidental model deletion | Depends on backup | 1 hour | `rclone copy` from S3 backup |

### 10.4 DR Testing

```powershell
# Quarterly DR test checklist:
# 1. Fail over master manually
# 2. Restore DB from backup on a staging environment
# 3. Verify all workers reconnect
# 4. Submit a test job and verify output
# 5. Document RTO achieved

& "C:\Program Files\AICluster\aicluster-admin.exe" dr test --plan "Q3-2026" --output "C:\ProgramData\AICluster\dr-report-Q3-2026.html"
```

---

## 11. Security Checklist

### Pre-Flight Checklist (run on every node before going live)

```powershell
# Run as Administrator on each node
Write-Output "=== AICluster Security Checklist ==="
$passed = 0
$failed = 0

# 1. Verify Windows Defender exclusions
$exclusions = Get-MpPreference
$expectedPaths = @(
  "C:\Program Files\AICluster",
  "C:\ProgramData\AICluster",
  "C:\AIClusterData"
)
foreach ($p in $expectedPaths) {
  if ($exclusions.ExclusionPath -contains $p) {
    Write-Output "[PASS] Exclusion: $p"; $passed++
  } else {
    Write-Output "[FAIL] Exclusion: $p"; $failed++
  }
}

# 2. Verify TLS certificate
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.Subject -like "*aicluster*" }
if ($cert) {
  $expiry = $cert.NotAfter
  Write-Output "[PASS] TLS cert valid until $expiry"; $passed++
  if ($expiry -lt (Get-Date).AddDays(30)) { Write-Output "[WARN] TLS cert expires within 30 days" }
} else {
  Write-Output "[FAIL] No TLS certificate found"; $failed++
}

# 3. Verify firewall rules
$rules = Get-NetFirewallRule -DisplayName "AICluster*" | Where-Object Enabled -eq True
if ($rules.Count -ge 4) {
  Write-Output "[PASS] $($rules.Count) firewall rules enabled"; $passed++
} else {
  Write-Output "[FAIL] Expected >=4 firewall rules, found $($rules.Count)"; $failed++
}

# 4. Verify services are running
$services = Get-Service "AIClusterMaster", "AIClusterWorker" -ErrorAction SilentlyContinue
foreach ($s in $services) {
  if ($s.Status -eq "Running") {
    Write-Output "[PASS] $($s.Name) is running"; $passed++
  } else {
    Write-Output "[FAIL] $($s.Name) is $($s.Status)"; $failed++
  }
}

# 5. Check disk space
$disk = Get-PSDrive C | Select-Object Used, Free
$freeGB = [math]::Round($disk.Free / 1GB, 2)
if ($freeGB -gt 20) {
  Write-Output "[PASS] Disk free: ${freeGB}GB"; $passed++
} else {
  Write-Output "[FAIL] Low disk space: ${freeGB}GB free"; $failed++
}

# 6. Verify Windows updates
$updates = Get-WmiObject -Class "Win32_QuickFixEngineering" | Sort-Object InstalledOn -Descending | Select-Object -First 1
Write-Output "[INFO] Last update: $($updates.HotFixID) on $($updates.InstalledOn)"

# 7. Check password policy
$policy = Get-ADDefaultDomainPasswordPolicy -ErrorAction SilentlyContinue
if ($policy) {
  Write-Output "[INFO] Min password length: $($policy.MinPasswordLength)"
}

# 8. Verify backup is recent
$latestBackup = Get-ChildItem "\\nas01\backups\aicluster\db" -Directory | Sort-Object Name -Descending | Select-Object -First 1
if ($latestBackup -and ($latestBackup.Name -gt (Get-Date).AddDays(-1).ToString("yyyyMMdd"))) {
  Write-Output "[PASS] Backup: $($latestBackup.Name)"; $passed++
} else {
  Write-Output "[FAIL] No backup within 24 hours"; $failed++
}

Write-Output "=== Result: $passed passed, $failed failed ==="
```

### Manual Checklist Items

| # | Item | Verified | Notes |
|---|------|----------|-------|
| 1 | Production config uses TLS (port 443, not 8080) | â˜ | Edit `config.yaml` `listen.tls` |
| 2 | Default admin password changed | â˜ | `aicluster-admin.exe user change-password` |
| 3 | API rate limiting enabled | â˜ | `config.yaml` â†’ `rate_limit: 100/1m` |
| 4 | Worker communication uses TLS | â˜ | `config.yaml` â†’ `worker.tls.enabled: true` |
| 5 | Audit logging enabled | â˜ | `config.yaml` â†’ `audit.log_all_requests: true` |
| 6 | Backups verified by restore test | â˜ | Quarterly DR test |
| 7 | Windows Firewall enabled on all profiles | â˜ | `Get-NetFirewallProfile` |
| 8 | No shared accounts used for services | â˜ | Use gMSA or NETWORK SERVICE |
| 9 | SMB signing enabled on storage share | â˜ | `Set-SmbServerConfiguration -RequireSecuritySignature $true` |
| 10 | BitLocker enabled on all data drives | â˜ | `Get-BitLockerVolume` |
| 11 | Log shipping to SIEM configured | â˜ | Winlogbeat / NXLog |
| 12 | Emergency break-glass account exists | â˜ | Local admin with complex password, stored in vault |

---

## 12. Maintenance

### 12.1 Log Rotation

NSSM handles automatic log rotation (see Section 8), but verify:

```powershell
# Check log sizes
Get-ChildItem "C:\ProgramData\AICluster\logs" -Recurse | Select-Object Name, Length, LastWriteTime | Sort-Object Length -Descending

# Manual rotation (if needed)
& "C:\Program Files\AICluster\tools\nssm-2.24\win64\nssm.exe" rotate AIClusterMaster
& "C:\Program Files\AICluster\tools\nssm-2.24\win64\nssm.exe" rotate AIClusterWorker

# Archive and purge logs older than 90 days
$cutoff = (Get-Date).AddDays(-90)
Get-ChildItem "C:\ProgramData\AICluster\logs" -Recurse -File | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force
```

### 12.2 Database Maintenance

```powershell
# Scheduled task: weekly VACUUM + reindex
$action = New-ScheduledTaskAction -Execute "C:\Program Files\AICluster\tools\sqlite3.exe" `
  -Argument "C:\ProgramData\AICluster\cluster.db VACUUM;"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 04:00
Register-ScheduledTask -TaskName "AICluster DB VACUUM" -Action $action -Trigger $trigger -RunLevel Highest

# Reindex (run after large deletions):
& "C:\Program Files\AICluster\tools\sqlite3.exe" "C:\ProgramData\AICluster\cluster.db" "REINDEX;"

# Integrity check (run monthly):
& "C:\Program Files\AICluster\tools\sqlite3.exe" "C:\ProgramData\AICluster\cluster.db" "PRAGMA integrity_check;"
```

### 12.3 Model Lifecycle & Cleanup

```powershell
# Remove unused models from workers (free disk space)
& "C:\Program Files\AICluster\aicluster-admin.exe" model prune --keep-last 5 --pool "gpu-pool-1"

# Archive old models to cold storage
rclone move "C:\AIClusterData\models\archived" "s3_models:aicluster-models-archive/" --progress
```

### 12.4 Database Cleanup Policy

```yaml
# config.yaml â€” retention section
retention:
  completed_jobs: 30 days      # delete job records after 30 days
  failed_jobs: 7 days           # keep failed jobs for debugging
  worker_heartbeats: 24 hours   # purge heartbeat history daily
  audit_logs: 90 days           # retain audit trail per compliance
  model_versions: 5             # keep at most 5 versions per model
```

```powershell
# Manual purge:
& "C:\Program Files\AICluster\aicluster-admin.exe" db purge --older-than 30d --type completed
& "C:\Program Files\AICluster\aicluster-admin.exe" db purge --older-than 7d --type failed
```

### 12.5 Model Updates (Hot-swap)

```powershell
# Deploy a new model version without restarting workers:
# 1. Upload model artifact to shared storage
Copy-Item "\\build-server\models\v2\model.gguf" "\\nas01\aicluster\models\production\"

# 2. Register with master (workers pick it up on next task assignment)
& "C:\Program Files\AICluster\aicluster-admin.exe" model register `
  --name "llm-v2" --path "\\nas01\aicluster\models\production\model.gguf" `
  --runtime "llama.cpp" --gpu-memory 8000

# 3. Point the default alias to the new version
& "C:\Program Files\AICluster\aicluster-admin.exe" model alias --name "llm-prod" --target "llm-v2"

# 4. Verify workers are using new model:
& "C:\Program Files\AICluster\aicluster-admin.exe" model status --name "llm-prod"
```

### 12.6 Routine Maintenance Schedule

| Frequency | Task | Owner |
|-----------|------|-------|
| Daily | Check dashboard: queue depth, worker count, error rate | Ops |
| Daily | Verify backups completed (check last-modified timestamps) | Automated |
| Weekly | Review audit logs for suspicious activity | Security |
| Weekly | Run DB integrity check | Scheduled task |
| Bi-weekly | Apply Windows security patches (staggered across workers) | IT |
| Monthly | DR test (staging environment) | SRE |
| Monthly | Rotate API keys and review access | Security |
| Quarterly | Full DR failover test (production â€” planned window) | SRE |
| Quarterly | Review TLS certificate expiry, renew if <30 days | Ops |
| Semi-annual | Clean up stale model artifacts from S3 | ML-Platform |
| Annual | Security audit / penetration test | Security |

---

*Document version 1.3.1 â€” Last updated: 2026-07-04*
*Maintainers: AICluster SRE Team <sre@aicluster.example.com>*
