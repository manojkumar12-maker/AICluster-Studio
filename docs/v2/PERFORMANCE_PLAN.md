# Performance Plan

**AICluster v2.0 â€” Native Desktop Edition | Phase 12**
**Date:** 2026-07-05
**Status:** Analysis Only â€” No Implementation

---

## 1. Startup Performance

### 1.1 Startup Sequence Timing Estimates

```
Cold Start (first run after install/boot):
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Step 1: OS launches Studio.exe                    0.5 - 1s  â”‚
â”‚   - Tauri shell init                                        â”‚
â”‚   - WebView creation                                        â”‚
â”‚   - React app load + render                                 â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Step 2: Launcher detects first run                 0.1 - 0.3sâ”‚
â”‚   - Check config/role.json exists                          â”‚
â”‚   - No â†’ Show wizard                                        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Step 3: User completes wizard                     10 - 30s  â”‚
â”‚   - User reads screens, enters config                       â”‚
â”‚   - SUBJECTIVE â€” user-dependent                             â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Step 4: Launcher starts Master                     3 - 8s   â”‚
â”‚   - CreateProcess AIClusterRuntime.exe --mode master                      â”‚
â”‚   - Python runtime init (~2s)                               â”‚
â”‚   - Import all modules (~2s)                                â”‚
â”‚   - SQLite init + table creation (~1s)                      â”‚
â”‚   - Lifespan startup (~1s)                                  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Step 5: Health check                                1 - 5s  â”‚
â”‚   - Poll GET /health every 1s                               â”‚
â”‚   - First attempt often fails (not ready)                   â”‚
â”‚   - Typically succeeds at 3-5s                              â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Step 6: Start Worker (if Standalone)                2 - 4s  â”‚
â”‚   - After Master is healthy                                 â”‚
â”‚   - CreateProcess AIClusterRuntime.exe --mode worker                       â”‚
â”‚   - Worker registers with Master                            â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Step 7: Open dashboard                              0.5 - 2sâ”‚
â”‚   - Navigate WebView to localhost:3000                      â”‚
â”‚   - React Query first poll (2s interval)                    â”‚
â”‚   - Dashboard renders                                       â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ TOTAL (cold, no wizard):                          ~8 - 15s  â”‚
â”‚ TOTAL (cold, with wizard):                     ~20 - 45s    â”‚
â”‚ TOTAL (warm, services cached):                    ~2 - 5s    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 1.2 Optimization Opportunities

| Step | Current | Target | Optimization |
|------|---------|--------|-------------|
| Python import time | ~2s | ~1s | Reduce unused imports, lazy-load engines |
| SQLite init | ~1s | ~0.3s | Skip table creation if DB already exists |
| Health check polling | 1s interval | 0.5s interval | Faster detection of readiness |
| WebView creation | ~0.5s | ~0.3s | Pre-create WebView before services ready |
| Dashboard render | ~1s | ~0.5s | Show loading skeleton immediately |

---

## 2. Runtime Memory Usage

### 2.1 Per-Service Memory Estimates

| Service | Idle RAM | Loaded RAM | Peak RAM | Notes |
|---------|----------|------------|----------|-------|
| Studio (Tauri) | 80-120 MB | 150-200 MB | 300 MB | WebView + React app |
| Master (Python) | 120-180 MB | 200-400 MB | 600 MB | Python runtime + imports + DB |
| Worker (Python) | 30-50 MB | 50-100 MB | 200 MB | Python runtime + psutil |
| CLI | 0 MB | 30 MB | 30 MB | Short-lived |
| **Total (Standalone)** | **230-350 MB** | **400-700 MB** | **1.1 GB** | |

### 2.2 Memory Breakdown â€” Master

```
Component                    Memory (Idle)     Memory (Loaded)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Python 3.13 runtime          45-60 MB          45-60 MB
FastAPI + uvicorn            10-15 MB          15-20 MB
SQLAlchemy + aiosqlite       5-10 MB           10-15 MB
SQLite (in-memory cache)     5-10 MB           20-50 MB
Pydantic models              5-10 MB           10-15 MB
Jinja2 templates             2-5 MB            2-5 MB
WebSocket manager            1-2 MB            2-5 MB
Slowapi (rate limiting)      1-2 MB            2-3 MB
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Subtotal (core):             74-114 MB         106-173 MB
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Engines (loaded on demand):
  Workflow Engine            0 MB (lazy)       10-20 MB
  Repository Intelligence    0 MB (lazy)       20-50 MB
  AI Runtime                 0 MB (lazy)       15-30 MB
  Multi-Agent Engine         0 MB (lazy)       10-20 MB
  Engineering Engine         0 MB (lazy)       10-20 MB
  Plugin System              0 MB (lazy)       5-10 MB
  Audit System               5-10 MB           10-20 MB
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Total (all engines loaded):  79-124 MB         176-323 MB
```

### 2.3 Memory Optimization for v2.0

| Optimization | Est. Savings | Effort | Notes |
|-------------|-------------|--------|-------|
| Lazy-load engines on first use | 50-100 MB | Medium | Already partially done |
| Reduce Pydantic model duplication | 5-10 MB | High | Shared schemas across engines |
| SQLite WAL mode for concurrent reads | 0 MB (perf) | Low | Already using aiosqlite |
| Database connection pooling | 0 MB (perf) | Medium | Single connection is fine for SQLite |
| Profile Python imports on startup | 10-20 MB | Medium | Remove unused imports |
| WebView recycling | 20-30 MB | Medium | Tauri manages this |

---

## 3. CPU Usage

### 3.1 Steady-State CPU Estimates

| Service | Idle CPU | Active CPU (job) | Active CPU (AI) |
|---------|----------|------------------|-----------------|
| Studio (Tauri) | 0-2% | 2-5% | 2-5% |
| Master (Python) | 1-3% | 5-15% | 10-30% |
| Worker (Python) | 1-2% | 5-25% | N/A |
| **Total** | **2-7%** | **12-45%** | **12-37%** |

### 3.2 Background Task CPU Costs

| Task | Interval | CPU Cost | Duration |
|------|----------|----------|----------|
| Offline checker | 10s | < 1% | 50-100ms |
| Scheduler loop | 2s | < 1% | 10-50ms |
| Heartbeat processing | per worker 5s | 1-2% per 10 workers | 10ms each |
| Audit event logging | per event | < 1% | 5-20ms |
| Dashboard aggregation | 2s (polled) | 1-2% | 20-100ms |
| WebSocket broadcasts | per state change | < 1% | 5-50ms |
| Health check polling | per requester | < 1% | 5ms |

---

## 4. Disk Usage

### 4.1 Installation Size

| Component | v2.0.0 (Current) | v2.0 (Target) | Change |
|-----------|-----------------|---------------|--------|
| AICluster Studio.exe | ~80 MB | ~80 MB | Same |
| AIClusterRuntime.exe --mode master | 263 MB | 263 MB | Same |
| AIClusterRuntime.exe --mode worker | 55 MB | 55 MB | Same |
| aicluster.exe | 31 MB | 31 MB | Same |
| MasterControlCenter.exe | ~60 MB | REMOVED | -60 MB |
| WorkerControlCenter.exe | ~60 MB | REMOVED | -60 MB |
| Config + assets | ~1 MB | ~1 MB | Same |
| **Total installed** | **~550 MB** | **~430 MB** | **-22%** |

### 4.2 Runtime Disk Usage

| Data | Typical Size | Growth Rate | Location |
|------|-------------|-------------|----------|
| SQLite database | 1-50 MB | 1 MB/month | `data/aicluster.db` |
| Audit logs | 10-100 MB | 10 MB/month | `data/aicluster.db` (same DB) |
| Application logs | 1-10 MB | 5 MB/month | `logs/*.log` |
| Artifacts (workflow) | 10-100 MB | Per usage | `data/artifacts/` |
| AI model files | 5-50 GB (user-managed) | Per download | `models/` |
| **Total (no models)** | **50-200 MB** | | |
| **Total (with models)** | **5-50 GB** | | |

---

## 5. Network Performance

### 5.1 Traffic Estimates

| Traffic Type | Frequency | Payload Size | Bandwidth | Latency |
|-------------|-----------|-------------|-----------|---------|
| Worker heartbeat | Every 5s per worker | ~200 bytes | 320 bps/worker | < 10ms LAN |
| Job poll | Every 5s per worker | ~100 bytes | 160 bps/worker | < 10ms LAN |
| Job progress | Every 5% or 5s | ~150 bytes | 240 bps/job | < 10ms LAN |
| Job result | Per job | 1-100 KB | Transient | < 10ms LAN |
| Dashboard poll | Every 2s (Studio) | ~500 bytes | 2 kbps | < 10ms LAN |
| WebSocket broadcast | Per state change | 200-2000 bytes | Transient | < 10ms LAN |
| AI inference | On demand | 1-100 KB req/resp | Transient | 100ms-10s (local LLM) |

### 5.2 Studio â†’ Master Traffic (Worst Case)

```
100 workers Ã— 2 requests/5s =      40 requests/second (heartbeat + job poll)
Studio dashboard polls:             0.5 requests/second
AI chat requests:                   0.1-1 requests/second (on demand)
WebSocket events:                   1-10 events/second (state changes)

Total:                              ~42 requests/second
Bandwidth (50 workers):            ~50 kbps (negligible on LAN)
```

---

## 6. Recovery Performance

### 6.1 Service Recovery Timing

| Failure | Detection Time | Recovery Time | Total Downtime |
|---------|---------------|---------------|----------------|
| Master crash | 1-5s (watchdog) | 3-8s (restart) | 4-13s |
| Master hang | 3-15s (health poll) | 3-8s (kill + restart) | 6-23s |
| Worker crash | 1-5s (watchdog) | 2-4s (restart) | 3-9s |
| Worker hang | 15s (master heartbeat) | 2-4s (restart) | 17-19s |
| Database error | 5s (health check) | Manual (UI) | User-dependent |
| Network partition | 15s (master offline) | Immediate (reconnect) | 15s + retry |

### 6.2 Max Restart Limits

| Service | Max Restarts (before cooldown) | Cooldown Period |
|---------|-------------------------------|-----------------|
| Master | 3 | 60 seconds |
| Worker | Unlimited | 10 seconds |
| Studio | N/A (user-managed) | N/A |

---

## 7. Scalability Limits

### 7.1 v2.0 Estimated Limits

| Dimension | Limit | Bottleneck |
|-----------|-------|------------|
| Workers per master | 100 (target), 200 (max) | SQLite write contention |
| Concurrent jobs | 1 per worker | Worker single-threaded |
| Queued jobs | 10,000 | Scheduler O(n) fetch |
| Concurrent WebSocket | 100 | Configurable limit |
| Database size | 2 GB (SQLite practical limit) | SQLite |
| Studio instances | 1 per machine | Named mutex |
| Dashboard polling | 1 session | Studio only |

### 7.2 Performance Regression Prevention

```powershell
# Performance regression tests
# Run before every release

# 1. Startup time
$start = Get-Date
Start-Process "AICluster Studio.exe" -Wait -Timeout 30
$elapsed = (Get-Date) - $start
if ($elapsed.TotalSeconds -gt 15) {
    Write-Warning "Startup time exceeded 15s: $($elapsed.TotalSeconds)s"
}

# 2. Memory usage
$process = Get-Process "AIClusterMaster"
$memMB = $process.WorkingSet64 / 1MB
if ($memMB -gt 500) {
    Write-Warning "Master memory exceeded 500 MB: ${memMB}MB"
}

# 3. API response time
$results = 1..100 | ForEach-Object {
    $start = Get-Date
    Invoke-WebRequest -Uri "http://localhost:8000/api/v1/dashboard"
    (Get-Date) - $start
}
$avgMs = ($results | Measure-Object -Average TotalMilliseconds).Average
if ($avgMs -gt 200) {
    Write-Warning "API response time exceeded 200ms: ${avgMs}ms"
}

# 4. Health check time
$start = Get-Date
Invoke-WebRequest -Uri "http://localhost:8000/health"
$healthMs = ((Get-Date) - $start).TotalMilliseconds
if ($healthMs -gt 100) {
    Write-Warning "Health check exceeded 100ms: ${healthMs}ms"
}

Write-Host "Performance check complete" -ForegroundColor Green
```

---

## 8. Success Criteria

| Metric | v2.0.0 (Baseline) | v2.0 Target | Measurement |
|--------|-------------------|-------------|-------------|
| Cold startup (no wizard) | ~15s | **< 10s** | From double-click to dashboard |
| Warm startup | ~5s | **< 3s** | Second launch |
| Master startup | ~8s | **< 5s** | Process start to health=200 |
| Worker startup | ~4s | **< 3s** | Process start to registration |
| Idle memory (Standalone) | ~400 MB | **< 350 MB** | 5 minutes after startup |
| API response (p50) | ~100ms | **< 100ms** | GET /api/v1/dashboard |
| API response (p95) | ~200ms | **< 200ms** | Under normal load |
| Health check | ~50ms | **< 50ms** | GET /health |
| Crash recovery (Master) | ~15s | **< 10s** | Crash â†’ health=200 |
| Master process restarts | 3 | **3 (max)** | Window before cooldown |
| Installation size | ~550 MB | **< 450 MB** | Full installation |
