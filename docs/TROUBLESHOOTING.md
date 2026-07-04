# AICluster v1.3.1 — Troubleshooting Guide

## Table of Contents

1. [Installation Issues](#1-installation-issues)
2. [Master Server Issues](#2-master-server-issues)
3. [Worker Issues](#3-worker-issues)
4. [Network Issues](#4-network-issues)
5. [AI Runtime Issues](#5-ai-runtime-issues)
6. [Database Issues](#6-database-issues)

---

## 1. Installation Issues

### 1.1 Installer Fails with "Fatal error during installation"

**Symptoms:** The installer exits early with a generic fatal error. No detailed message is shown.

**Cause:** Corrupted installer download, insufficient disk space, or a missing Windows Update (KB).

**Solution:**
1. Verify the installer checksum:
   ```
   certutil -hashfile AICluster-1.3.1-setup.exe SHA256
   ```
   Compare the output against the checksum published on the release page.
2. Ensure at least 4 GB of free disk space:
   ```
   fsutil volume diskfree C:
   ```
3. Install all pending Windows Updates, then reboot.
4. Re-download the installer from the official source.

**Verification:** The installer completes without error and the service binaries exist under `C:\Program Files\AICluster\`.

---

### 1.2 "Python 3.10+ is required" Error

**Symptoms:** The installer refuses to proceed, displaying a message that Python 3.10 or later is needed.

**Cause:** Python is not installed or the installed version is older than 3.10.

**Solution:**
```
python --version
```
If the version is missing or below 3.10, download Python 3.12 from https://www.python.org/downloads/. During installation, check "Add Python to PATH".

Alternatively, if Python is installed but not detected, verify the PATH entry:
```
echo %PATH%
```
Add Python's install directory to PATH if missing:
```
setx PATH "%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312"
```

**Verification:** Run `python --version` from a new terminal — it should return `Python 3.12.x`.

---

### 1.3 "Microsoft Visual C++ Redistributable Not Found"

**Symptoms:** Setup halts with a message about a missing VC++ redistributable.

**Cause:** The Visual C++ 2015–2022 Redistributable (x64) is not installed.

**Solution:**
Download and install the VC++ redistributable from:
https://aka.ms/vs/17/release/vc_redist.x64.exe

After installation, reboot the machine.

**Verification:** Run the AICluster installer again — the VC++ check passes.

---

### 1.4 Windows SmartScreen Blocks Installation

**Symptoms:** A blue dialog appears: "Windows protected your PC" — SmartScreen prevented an unrecognized app from starting.

**Cause:** The installer binary is new and has not yet built a reputation with Microsoft's SmartScreen.

**Solution:**
1. Click "More info" then "Run anyway".
2. For silent deployment, unblock the file from PowerShell:
   ```
   Unblock-File -Path "C:\path\to\AICluster-1.3.1-setup.exe"
   ```
3. Alternatively, run the installer from an administrative command prompt.

**Verification:** The installer launches without the SmartScreen prompt.

---

### 1.5 "Insufficient Disk Space"

**Symptoms:** A dialog reports that there is not enough room to install AICluster.

**Cause:** The installation drive has less than 4 GB free.

**Solution:**
1. Check free space on all drives:
   ```
   wmic logicaldisk get size,freespace,caption
   ```
2. Free space by running Disk Cleanup:
   ```
   cleanmgr /sageset:1
   cleanmgr /sagerun:1
   ```
3. Re-run the installer and select a drive with sufficient space.

**Verification:** `fsutil volume diskfree D:` (where D: is the target drive) shows at least 4 GB free.

---

### 1.6 Antivirus Quarantines Installer or Binaries

**Symptoms:** Antivirus software deletes or blocks the installer or key executables immediately after extraction.

**Cause:** Heuristic scanners may flag AICluster's network capabilities as suspicious.

**Solution:**
1. Restore the quarantined file from your antivirus quarantine.
2. Add the following folders to the antivirus exclusion list:
   - `C:\Program Files\AICluster`
   - `%APPDATA%\AICluster`
   - `%LOCALAPPDATA%\AICluster`
3. For Windows Defender, run:
   ```
   powershell -Command "Add-MpPreference -ExclusionPath 'C:\Program Files\AICluster'"
   ```

**Verification:** Re-run the installer — no files are quarantined.

---

### 1.7 "Access Denied" During Installation

**Symptoms:** The installer fails with "Access Denied" or "Error 5" when writing files.

**Cause:** The user account lacks administrator privileges.

**Solution:**
1. Right-click the installer and select "Run as administrator".
2. Alternatively, launch from an elevated command prompt:
   ```
   runas /user:Administrator "AICluster-1.3.1-setup.exe"
   ```

**Verification:** Installation proceeds past the file-copy phase.

---

### 1.8 "Network path was not found" During Online Installer

**Symptoms:** The web-based installer fails with "The network path was not found."

**Cause:** Corporate proxy, VPN, or firewall blocking outbound HTTPS connections.

**Solution:**
1. Verify internet connectivity:
   ```
   ping 8.8.8.8
   ```
2. Check proxy settings:
   ```
   netsh winhttp show proxy
   ```
3. Configure the system proxy:
   ```
   netsh winhttp set proxy proxy-server="http://your-proxy:8080"
   ```
4. If behind a corporate firewall, ask your network team to allow `*.aicluster.io` on port 443.

**Verification:** The installer successfully downloads required components.

---

### 1.9 Download Fails Midway / Checksum Mismatch

**Symptoms:** The download starts but stalls or completes with a file that fails hash verification.

**Cause:** Unstable internet connection, ISP throttling, or a misconfigured CDN edge.

**Solution:**
1. Use a download manager that supports resume (e.g., `curl -C -`):
   ```
   curl -C - -O https://releases.aicluster.io/v1.3.1/AICluster-1.3.1-setup.exe
   ```
2. Switch to a wired connection or different network.
3. Download via the BitTorrent magnet link if available on the releases page.

**Verification:** `certutil -hashfile AICluster-1.3.1-setup.exe SHA256` matches the published hash.

---

### 1.10 Corrupted Installer — "Setup file is damaged"

**Symptoms:** The installer immediately reports that the file is corrupted.

**Cause:** The binary was truncated during download or the file system has errors.

**Solution:**
1. Delete the existing file and re-download.
2. Check the file system for errors:
   ```
   chkdsk C: /scan
   ```
3. Download from a mirror site.

**Verification:** The installer starts normally after re-download.

---

## 2. Master Server Issues

### 2.1 Master Server Won't Start

**Symptoms:** Running `aicluster master start` exits with an error immediately.

**Cause:** Missing configuration file, corrupted installation, or a required port is already bound.

**Solution:**
1. Verify the config file exists:
   ```
   dir "C:\ProgramData\AICluster\master.yaml"
   ```
2. Check which process is using port 8443 (default):
   ```
   netstat -ano | findstr :8443
   ```
3. Kill the conflicting process or change the port in `master.yaml`:
   ```yaml
   server:
     port: 8444
   ```
4. Re-register the Windows service:
   ```
   aicluster master install
   ```

**Verification:** `aicluster master start` returns a PID and `sc query AIClusterMaster` shows `RUNNING`.

---

### 2.2 Port Already in Use

**Symptoms:** The log contains `bind: address already in use` or `EADDRINUSE`.

**Cause:** Another service (e.g., IIS, nginx, another AICluster instance) is listening on the same port.

**Solution:**
1. Identify the offending process:
   ```
   netstat -ano | findstr :8443
   tasklist /FI "PID eq <PID>"
   ```
2. Stop the conflicting service or change the AICluster port in `master.yaml`.
3. Restart the master server.

**Verification:** `netstat -ano | findstr :8443` shows only `aicluster.exe` listening.

---

### 2.3 Database Connection Error

**Symptoms:** The master log shows `could not connect to database` or `dial tcp: connection refused`.

**Cause:** PostgreSQL or SQLite is not running, credentials are wrong, or the connection string is malformed.

**Solution:**
1. Check database service status (PostgreSQL):
   ```
   sc query postgresql-x64-16
   ```
2. Test connectivity:
   ```
   psql -h 127.0.0.1 -U aicluster -d aicluster -c "SELECT 1"
   ```
3. Verify the connection string in `master.yaml`:
   ```yaml
   database:
     dsn: "postgres://aicluster:password@127.0.0.1:5432/aicluster?sslmode=disable"
   ```
4. If using SQLite, ensure the parent directory is writable.

**Verification:** The master server starts and the log confirms `database connected`.

---

### 2.4 JWT Secret Error on Startup

**Symptoms:** `invalid JWT secret` or `JWT secret must be at least 32 bytes` in the log.

**Cause:** The `jwt_secret` in `master.yaml` is missing, too short, or contains invalid characters.

**Solution:**
1. Generate a new 256-bit secret:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Set it in `master.yaml`:
   ```yaml
   auth:
     jwt_secret: "<generated-hex-string>"
   ```
3. Restart the master server.

**Verification:** The master starts without JWT errors. Existing tokens are invalidated — all workers must re-authenticate.

---

### 2.5 Admin Login Fails with "Invalid Credentials"

**Symptoms:** The web UI returns "Invalid username or password" for the admin account.

**Cause:** The default password was changed and forgotten, or the user database is corrupted.

**Solution:**
1. Reset the admin password via the CLI:
   ```
   aicluster master reset-admin --password NewStr0ng!
   ```
2. If the CLI tool itself is unavailable, truncate the `users` table in the database:
   ```
   psql -U aicluster -d aicluster -c "TRUNCATE users;"
   ```
   Then restart the master — a new admin account is created with defaults (admin / admin).

**Verification:** Log into the web UI at `https://localhost:8443` with the new credentials.

---

### 2.6 CORS Error in Web UI

**Symptoms:** Browser developer tools show `Access-Control-Allow-Origin` errors when the UI talks to the API.

**Cause:** The master server's `allowed_origins` list does not include the UI's origin.

**Solution:**
1. Determine the UI origin (e.g., `http://localhost:3000`).
2. Update `master.yaml`:
   ```yaml
   server:
     cors:
       allowed_origins:
         - "http://localhost:3000"
         - "https://dashboard.aicluster.io"
   ```
3. Restart the master server.

**Verification:** Reload the UI — all API requests succeed without CORS errors.

---

### 2.7 WebSocket Connection Fails

**Symptoms:** Workers report `WebSocket dial error` or the UI dashboard shows "Disconnected".

**Cause:** A reverse proxy (nginx, IIS ARR) is not configured to pass WebSocket `Upgrade` headers.

**Solution:**
1. If using nginx, ensure the following directives exist:
   ```nginx
   proxy_http_version 1.1;
   proxy_set_header Upgrade $http_upgrade;
   proxy_set_header Connection "upgrade";
   ```
2. If no reverse proxy, verify the master's `ws://` or `wss://` URL is correctly configured.
3. Check the firewall is not blocking port 8443.

**Verification:** Workers show `connected` status in the master UI.

---

### 2.8 High CPU Usage on Master

**Symptoms:** The master process consumes >80% CPU continuously. The UI is sluggish.

**Cause:** A runaway polling loop, excessive worker heartbeats, or an inefficient database query.

**Solution:**
1. Identify the hot loop from CPU profiling:
   ```
   aicluster master pprof --cpu 60 > cpu.pprof
   ```
2. Increase the heartbeat interval in `master.yaml`:
   ```yaml
   worker:
     heartbeat_interval: 15s
   ```
3. Check for slow queries and add database indexes:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_heartbeat ON workers (last_heartbeat);
   ```
4. Restart the master.

**Verification:** CPU usage drops below 30% under normal load.

---

### 2.9 Memory Leak on Master Server

**Symptoms:** Memory usage grows monotonically over hours or days until the process is OOM-killed.

**Cause:** A goroutine/thread leak, unbounded cache growth, or a database connection pool not releasing.

**Solution:**
1. Capture a heap dump:
   ```
   aicluster master pprof --heap > heap.pprof
   ```
2. Review the dump to identify growing allocations.
3. Restart the master server as a temporary mitigation.
4. Apply the hotfix patch from the AICluster v1.3.1 patch-1 release.

**Verification:** After the fix, memory usage stabilizes within 24 hours of continuous operation.

---

### 2.10 Master Shutdown Hangs

**Symptoms:** `aicluster master stop` or `sc stop AIClusterMaster` never returns, or takes >30 seconds.

**Cause:** In-flight worker connections or database transactions are not draining.

**Solution:**
1. Force-stop the process:
   ```
   taskkill /F /IM aicluster.exe
   ```
2. Increase the shutdown grace period in `master.yaml`:
   ```yaml
   server:
     shutdown_timeout: 30s
   ```
3. Ensure all workers are stopped before stopping the master.

**Verification:** `sc stop AIClusterMaster` returns within 10 seconds.

---

## 3. Worker Issues

### 3.1 Worker Won't Connect to Master

**Symptoms:** `aicluster worker start` hangs or logs `connection refused`.

**Cause:** The master URL is incorrect, the master is not running, or a firewall blocks the port.

**Solution:**
1. Verify the master is running:
   ```
   curl -k https://<master-ip>:8443/health
   ```
2. Check the worker config:
   ```
   type "C:\ProgramData\AICluster\worker.yaml"
   ```
   Ensure `master_url` is correct (e.g., `https://192.168.1.100:8443`).
3. Test connectivity from the worker to the master:
   ```
   Test-NetConnection <master-ip> -Port 8443
   ```

**Verification:** The worker log shows `connected to master`.

---

### 3.2 Worker Receives 401 Unauthorized

**Symptoms:** Worker log shows `HTTP 401` or `token rejected`.

**Cause:** The worker's authentication token is expired, revoked, or mismatched.

**Solution:**
1. Re-register the worker from the master UI or CLI:
   ```
   aicluster worker register --name worker-01
   ```
2. Copy the new token into `worker.yaml`:
   ```yaml
   auth:
     token: "<new-token>"
   ```
3. Restart the worker service.

**Verification:** The worker authenticates successfully — log shows `authenticated as worker-01`.

---

### 3.3 Worker Receives 404 on Registration

**Symptoms:** `POST /api/v1/workers/register` returns 404.

**Cause:** The worker is using an API path that does not exist — version mismatch between worker and master.

**Solution:**
1. Check the master version:
   ```
   aicluster master version
   ```
2. Check the worker version:
   ```
   aicluster worker version
   ```
3. Upgrade both to v1.3.1 so API paths align.

**Verification:** Registration succeeds — log shows `registered successfully`.

---

### 3.4 Worker Shows "Offline" in UI

**Symptoms:** The master UI lists the worker as offline, even though the process is running.

**Cause:** Heartbeat packets are not reaching the master due to a network issue or firewall.

**Solution:**
1. Verify the worker process is running:
   ```
   tasklist | findstr aicluster
   ```
2. Check the heartbeat interval — ensure it matches the master's expected interval.
3. Temporarily disable Windows Firewall for the private profile:
   ```
   netsh advfirewall set privateprofile state off
   ```
   (Re-enable after testing.)

**Verification:** The worker status changes to `online` in the master UI within two heartbeat intervals.

---

### 3.5 Heartbeat Fails Intermittently

**Symptoms:** Workers flip between online/offline every few minutes. The log shows `heartbeat timeout`.

**Cause:** Network latency spikes or the master's heartbeat timeout is set too low.

**Solution:**
1. Measure round-trip latency:
   ```
   ping <master-ip> -n 20
   ```
2. Increase the heartbeat interval on both sides:
   - Master `master.yaml`: `heartbeat_interval: 30s`
   - Worker `worker.yaml`: `heartbeat_interval: 30s`
3. Increase the master's timeout multiplier:
   ```yaml
   worker:
     heartbeat_timeout: 90s
   ```

**Verification:** Worker stays online for >1 hour without flapping.

---

### 3.6 Worker Does Not Receive Jobs

**Symptoms:** Jobs submitted to the master are queued but never dispatched to the worker.

**Cause:** The worker's `capabilities` filter excludes it from the job's requirements, or the worker has `drain` enabled.

**Solution:**
1. Check if drain mode is active:
   ```
   aicluster worker status
   ```
2. Disable drain mode:
   ```
   aicluster worker drain --off
   ```
3. Verify worker capabilities match the job's requirements:
   ```
   aicluster worker capabilities
   ```

**Verification:** New jobs are dispatched to the worker immediately.

---

### 3.7 Job Execution Fails on Worker

**Symptoms:** The job status shows `failed` and the worker log contains a non-zero exit code.

**Cause:** Missing runtime dependencies, insufficient permissions, or the job script has a bug.

**Solution:**
1. Examine the full job log:
   ```
   aicluster worker logs --job <job-id>
   ```
2. Run the job command manually on the worker to reproduce the error.
3. Install missing dependencies (e.g., Python packages, CUDA drivers).
4. Verify the worker user has execute permission on the job script.

**Verification:** Re-submit the job — it completes with exit code 0.

---

### 3.8 High CPU Usage on Worker

**Symptoms:** The worker process consumes all CPU cores, starving other applications.

**Cause:** A job with an infinite loop or a single job consuming all available cores.

**Solution:**
1. List running jobs:
   ```
   aicluster worker jobs
   ```
2. Set per-job CPU limits in the job submission payload:
   ```json
   {
     "resources": {
       "cpu": 2
     }
   }
   ```
3. Configure global worker limits in `worker.yaml`:
   ```yaml
   resources:
     max_cpu: 4
   ```

**Verification:** CPU usage is capped at the configured limit.

---

### 3.9 Worker Crashes on Startup

**Symptoms:** The worker process exits immediately with `panic` or `segmentation fault`.

**Cause:** Corrupted configuration file, incompatible GPU driver, or a corrupted binary.

**Solution:**
1. Validate the config file syntax:
   ```
   aicluster worker validate-config
   ```
2. Re-run the worker with verbose logging:
   ```
   aicluster worker start --log-level debug
   ```
3. Reinstall the worker component:
   ```
   aicluster worker uninstall
   aicluster worker install
   ```

**Verification:** The worker starts and remains running for >5 minutes.

---

### 3.10 Worker Reconnect Fails After Network Outage

**Symptoms:** After a network disruption, the worker cannot re-establish a connection to the master.

**Cause:** Exponential backoff reaches a maximum retry limit or the master has permanently banned the worker's IP.

**Solution:**
1. Check the master's banned IPs list:
   ```
   aicluster master banned-ips
   ```
2. Unban the worker's IP if present:
   ```
   aicluster master unban-ip <worker-ip>
   ```
3. Reduce reconnect backoff in `worker.yaml`:
   ```yaml
   network:
     reconnect_interval: 5s
     max_reconnect_interval: 60s
   ```
4. Restart the worker.

**Verification:** After a network interruption, the worker reconnects automatically within 60 seconds.

---

## 4. Network Issues

### 4.1 Firewall Blocking AICluster Traffic

**Symptoms:** Workers cannot reach the master, or the master cannot communicate with workers.

**Cause:** Windows Firewall or a third-party firewall is blocking port 8443 (or the configured port).

**Solution:**
1. Check the current firewall rules:
   ```
   netsh advfirewall firewall show rule name=all | findstr /i aicluster
   ```
2. Add an inbound rule for the AICluster port:
   ```
   netsh advfirewall firewall add rule name="AICluster Master" dir=in action=allow protocol=TCP localport=8443
   ```
3. Add an outbound rule on worker machines:
   ```
   netsh advfirewall firewall add rule name="AICluster Worker Outbound" dir=out action=allow protocol=TCP remoteport=8443
   ```

**Verification:** `Test-NetConnection <master-ip> -Port 8443` succeeds from the worker.

---

### 4.2 Wrong IP Address Configured

**Symptoms:** Workers try to connect to an IP that does not belong to the master.

**Cause:** The `master_url` in `worker.yaml` contains a stale or incorrect IP or hostname.

**Solution:**
1. Check the master's actual IP:
   ```
   ipconfig | findstr /i "IPv4"
   ```
2. Update `worker.yaml`:
   ```yaml
   master_url: "https://192.168.1.100:8443"
   ```
3. Use DNS names instead of raw IPs for resilience.

**Verification:** The worker resolves and connects to the correct master IP.

---

### 4.3 DNS Resolution Failure

**Symptoms:** `could not resolve host: master.aicluster.local` in worker logs.

**Cause:** DNS server does not have an A record for the hostname, or the worker's DNS settings are wrong.

**Solution:**
1. Test DNS resolution:
   ```
   nslookup master.aicluster.local
   ```
2. Flush the DNS cache:
   ```
   ipconfig /flushdns
   ```
3. Add a static hosts entry as a workaround:
   ```
   echo 192.168.1.100 master.aicluster.local >> %SystemRoot%\System32\drivers\etc\hosts
   ```

**Verification:** `ping master.aicluster.local` resolves to the correct IP.

---

### 4.4 Network Switch / Router Issues

**Symptoms:** Intermittent disconnections, packet loss, or high latency between workers and the master.

**Cause:** Faulty switch port, STP topology changes, or a saturated uplink.

**Solution:**
1. Run a continuous ping test:
   ```
   ping -t <master-ip>
   ```
2. Check for packet loss (any loss >0% is cause for investigation).
3. If on a managed switch, check port statistics for CRC errors or collisions.
4. Move the cable to a different switch port and replace the patch cable.

**Verification:** Ping test shows 0% loss over a 10-minute window.

---

### 4.5 WiFi Instability

**Symptoms:** Workers on wireless connections frequently flip between online and offline.

**Cause:** WiFi signal interference, channel congestion, or roaming between access points.

**Solution:**
1. Measure signal strength:
   ```
   netsh wlan show interfaces | findstr Signal
   ```
2. Move the worker machine closer to the access point or use a wired connection.
3. Change the WiFi channel on the access point to a less congested one (use 5 GHz band).
4. Configure the worker's network adapter to disable power saving:
   ```
   powercfg /change standby-timeout-ac 0
   ```

**Verification:** The worker stays connected for >1 hour without drops.

---

## 5. AI Runtime Issues

### 5.1 Model Not Found

**Symptoms:** Job logs contain `model not found` or `file not found: models/llama-2-7b.gguf`.

**Cause:** The model file is not present on the worker's filesystem or the path in the job config is wrong.

**Solution:**
1. List available models on the worker:
   ```
   aicluster worker models
   ```
2. Download the required model:
   ```
   aicluster worker model pull llama-2-7b
   ```
3. Verify the model path in the job configuration is an absolute or worker-relative path.

**Verification:** The job finds and loads the model successfully.

---

### 5.2 AI Provider Won't Load

**Symptoms:** `provider "openai" failed to initialize` or `provider not supported`.

**Cause:** The provider module is missing, the API key is invalid, or the provider binary is incompatible.

**Solution:**
1. List installed providers:
   ```
   aicluster worker providers
   ```
2. Install the missing provider:
   ```
   aicluster worker provider install openai
   ```
3. Verify the API key in the provider configuration:
   ```yaml
   provider:
     openai:
       api_key: "sk-..."
   ```

**Verification:** `aicluster worker providers` shows the provider as `loaded`.

---

### 5.3 Context Overflow Error

**Symptoms:** `context length exceeded` — the input text exceeds the model's maximum token limit.

**Cause:** The job sends more tokens than the model supports (e.g., 4096 tokens for Llama 2).

**Solution:**
1. Check the model's context window size:
   ```
   aicluster worker model info llama-2-7b
   ```
2. Truncate or chunk the input in the job script before submission.
3. Use a model with a larger context window (e.g., 32K or 128K).

**Verification:** The job processes the input without context overflow errors.

---

### 5.4 Slow Inference

**Symptoms:** Inference takes >10 seconds per request, far below expected throughput.

**Cause:** CPU-only execution (no GPU), insufficient GPU VRAM causing swapping, or thermal throttling.

**Solution:**
1. Check if the GPU is utilized:
   ```
   nvidia-smi
   ```
2. Ensure the model is loaded on the GPU (not CPU fallback).
3. Reduce batch size or use a smaller quantized model (e.g., Q4 instead of FP16).
4. Monitor GPU temperature:
   ```
   nvidia-smi --query-gpu=temperature.gpu --format=csv
   ```

**Verification:** Inference latency drops to expected levels (e.g., <2 seconds per request).

---

### 5.5 Out of Memory (OOM) During Inference

**Symptoms:** The worker process is killed, or `cudaErrorMemoryAllocation` appears in the logs.

**Cause:** The model requires more VRAM than available on the GPU.

**Solution:**
1. Check available VRAM:
   ```
   nvidia-smi --query-gpu=memory.free --format=csv
   ```
2. Use a smaller quantized model or reduce `gpu_layers`.
3. Enable memory offloading in `worker.yaml`:
   ```yaml
   inference:
     offload_layers: 16
   ```
4. Add `--no-kv-cache` flag to reduce memory usage.

**Verification:** Inference runs without OOM errors. `nvidia-smi` shows VRAM usage below 90%.

---

## 6. Database Issues

### 6.1 Database Is Locked

**Symptoms:** `database is locked` (SQLite) or `deadlock detected` (PostgreSQL) in master logs.

**Cause:** Concurrent write transactions from multiple master instances or a long-running migration.

**Solution (SQLite):**
1. Switch to WAL mode:
   ```sql
   PRAGMA journal_mode=WAL;
   ```
2. Reduce the busy timeout:
   ```sql
   PRAGMA busy_timeout=5000;
   ```

**Solution (PostgreSQL):**
1. Find and terminate blocking sessions:
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'idle in transaction' AND state_change < now() - interval '5 minutes';
   ```

**Verification:** The master starts without lock-related errors.

---

### 6.2 Corrupted Database

**Symptoms:** `database disk image is malformed` (SQLite) or `relation does not exist` (PostgreSQL) after a crash.

**Cause:** Unexpected power loss or disk I/O error during a write.

**Solution (SQLite):**
1. Create a backup of the corrupted file.
2. Run integrity check and dump:
   ```
   sqlite3 aicluster.db ".mode insert" ".output backup.sql" ".dump" ".exit"
   ```
3. Restore from the backup script into a fresh database.

**Solution (PostgreSQL):**
1. Restore from the latest pg_dump backup:
   ```
   pg_restore -d aicluster latest_backup.dump
   ```

**Verification:** The master connects and reads the database without errors.

---

### 6.3 Database Migration Fails

**Symptoms:** Master startup log shows `migration failed` or `dirty database version 7`.

**Cause:** A previous migration was interrupted, leaving the database in a dirty state.

**Solution:**
1. Check the current migration version:
   ```
   aicluster master db version
   ```
2. Force-set the schema version (only if you are certain the schema matches the target version):
   ```
   aicluster master db set-version 7
   ```
3. Run migrations manually:
   ```
   aicluster master db migrate
   ```
4. If all else fails, restore from backup and re-run migrations.

**Verification:** The master starts successfully — log shows `migrations completed`.

---

### 6.4 Permission Denied on Database

**Symptoms:** `permission denied for table workers` or `could not open database file`.

**Cause:** The database user lacks the necessary GRANTs, or the file's ACL does not include the service account.

**Solution (PostgreSQL):**
1. Grant the required privileges:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE aicluster TO aicluster_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aicluster_user;
   ```

**Solution (SQLite):**
1. Fix file permissions:
   ```
   icacls "C:\ProgramData\AICluster\aicluster.db" /grant "NETWORK SERVICE:(F)"
   ```

**Verification:** The master starts without permission errors.

---

### 6.5 Database Rollback Fails

**Symptoms:** `rollback failed: no transaction in progress` or the database state is inconsistent after a failed upgrade.

**Cause:** Attempting to roll back a migration that was already committed, or the migration version tracking table is corrupted.

**Solution:**
1. Check the migration log:
   ```
   aicluster master db history
   ```
2. If the migration was already committed, apply a new migration to revert the schema changes instead of rolling back.
3. Manually create a reversal migration script:
   ```sql
   ALTER TABLE workers DROP COLUMN IF EXISTS new_column;
   ```
4. Update the schema version:
   ```
   aicluster master db set-version 6
   ```

**Verification:** `aicluster master db version` returns the expected rollback version and the schema is consistent.

---

## Diagnostic Commands Reference

| Command | Purpose |
|---|---|
| `aicluster master logs --tail 100` | View last 100 master log lines |
| `aicluster worker logs --tail 100` | View last 100 worker log lines |
| `sc query AIClusterMaster` | Check master service status |
| `sc query AIClusterWorker` | Check worker service status |
| `nvidia-smi` | GPU memory and utilization |
| `netstat -ano \| findstr :8443` | Check which process owns port 8443 |
| `certutil -hashfile <file> SHA256` | Verify file integrity |

---

*Document version 1.0 — AICluster v1.3.1*
