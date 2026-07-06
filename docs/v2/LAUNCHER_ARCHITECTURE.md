# Launcher Architecture

**AICluster v2.0 â€” Native Desktop Edition | Phase 4**
**Date:** 2026-07-05
**Status:** Design Only â€” No Implementation

---

## 1. Overview

The Studio becomes the unified launcher for all AICluster services. Users interact only with `AICluster Studio.exe`. The launcher manages the lifecycle of all backend services internally.

### 1.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Single entry point** | `AICluster Studio.exe` is the only EXE users launch |
| **Zero backend interaction** | Users never manually start Master or Worker |
| **Idempotent startup** | Safe to launch repeatedly â€” detects existing services |
| **Self-healing** | Auto-restart crashed services within 30 seconds |
| **Graceful degradation** | If Master is down, Studio shows connection screen (not crash) |
| **No backend changes** | All launcher logic lives in Studio (Rust sidecar) |

### 1.2 Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    AICluster Studio.exe                          â”‚
â”‚                                                                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”‚
â”‚  â”‚  Tauri v2 Shell (Rust)                                   â”‚    â”‚
â”‚  â”‚                                                          â”‚    â”‚
â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚    â”‚
â”‚  â”‚  â”‚  Launcher Service (Rust Module)                   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚                                                   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  RoleManager         ServiceManager               â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”‚ read role.jsonâ”‚   â”‚ start/stop master       â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”‚ detect config â”‚   â”‚ start/stop worker       â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”‚ first run?    â”‚   â”‚ health checks           â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚ process watchdog         â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚                      â”‚ crash recovery           â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚                      â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚                                                     â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  TrayManager          UpdateChecker                 â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”‚ system tray   â”‚   â”‚ check for updates       â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”‚ notifications â”‚   â”‚ download + install      â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â”‚ minimize/max  â”‚   â”‚ verify signatures       â”‚   â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚   â”‚    â”‚
â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚    â”‚
â”‚  â”‚                                                          â”‚    â”‚
â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚    â”‚
â”‚  â”‚  â”‚  Tauri Commands (IPC Bridge)                      â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  get_role | set_role | start_services |           â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  stop_services | get_status | is_first_run |      â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  open_dashboard | get_master_url | set_autostart  â”‚   â”‚    â”‚
â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚    â”‚
â”‚  â”‚                                                          â”‚    â”‚
â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚    â”‚
â”‚  â”‚  â”‚  WebView (React Frontend)                         â”‚   â”‚    â”‚
â”‚  â”‚  â”‚  Dashboard | AI Chat | Workflows | Settings       â”‚   â”‚    â”‚
â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚    â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 2. Launcher Service Design

### 2.1 Module Structure (Rust)

```
studio/src-tauri/src/
â”œâ”€â”€ main.rs                        # Tauri entry point
â”œâ”€â”€ lib.rs                         # Plugin registration + command handlers
â”‚
â”œâ”€â”€ launcher/
â”‚   â”œâ”€â”€ mod.rs                     # Launcher service (re-exports)
â”‚   â”œâ”€â”€ config.rs                  # RoleConfig: read/write role.json
â”‚   â”œâ”€â”€ process.rs                 # ProcessManager: start/stop/monitor EXEs
â”‚   â”œâ”€â”€ health.rs                  # HealthChecker: HTTP health polling
â”‚   â”œâ”€â”€ watchdog.rs                # Watchdog: monitor + auto-restart
â”‚   â”œâ”€â”€ tray.rs                    # TrayManager: system tray integration
â”‚   â”œâ”€â”€ autostart.rs               # Windows auto-start registration
â”‚   â””â”€â”€ updates.rs                 # UpdateChecker: self-update logic
â”‚
â””â”€â”€ commands.rs                    # Tauri command definitions
```

### 2.2 Data Structures

```rust
// studio/src-tauri/src/launcher/config.rs

#[derive(Debug, Serialize, Deserialize)]
pub struct RoleConfig {
    pub role: Role,
    pub configured: bool,
    pub version: String,
    pub settings: RoleSettings,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum Role {
    Master,
    Worker,
    Standalone,
    Unconfigured,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RoleSettings {
    pub master: MasterSettings,
    pub worker: WorkerSettings,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MasterSettings {
    pub host: String,
    pub port: u16,
    pub dashboard_port: u16,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WorkerSettings {
    pub master_url: Option<String>,
    pub worker_name: Option<String>,
    pub port: u16,
}

// studio/src-tauri/src/launcher/process.rs

#[derive(Debug, Clone, Serialize)]
pub enum ServiceStatus {
    Stopped,
    Starting,
    Running { pid: u32, uptime_seconds: u64 },
    Stopping,
    Crashed { exit_code: i32, restarts: u32 },
    Unhealthy { reason: String },
}

#[derive(Debug, Clone, Serialize)]
pub struct ServiceInfo {
    pub name: String,
    pub executable: String,
    pub status: ServiceStatus,
    pub port: Option<u16>,
    pub health_endpoint: Option<String>,
}

// studio/src-tauri/src/launcher/health.rs

#[derive(Debug, Clone, Serialize)]
pub enum HealthStatus {
    Healthy,
    Degraded { issues: Vec<String> },
    Unreachable { error: String },
}
```

### 2.3 Tauri Commands

```rust
// studio/src-tauri/src/commands.rs

#[tauri::command]
async fn get_role() -> Result<Role, String> {
    RoleConfig::load().map(|c| c.role)
}

#[tauri::command]
async fn set_role(role: Role, settings: Option<RoleSettings>) -> Result<(), String> {
    let config = RoleConfig {
        role,
        configured: true,
        version: env!("CARGO_PKG_VERSION").to_string(),
        settings: settings.unwrap_or_default(),
        created_at: chrono::Utc::now().to_rfc3339(),
    };
    config.save()
}

#[tauri::command]
async fn start_services(app_handle: tauri::AppHandle) -> Result<Vec<ServiceInfo>, String> {
    let config = RoleConfig::load()?;
    let mut results = vec![];
    
    match config.role {
        Role::Master | Role::Standalone => {
            // Start master
            let status = start_master(&config).await?;
            results.push(ServiceInfo {
                name: "Master Server".into(),
                executable: "AIClusterRuntime.exe --mode master".into(),
                status,
                port: Some(config.settings.master.port),
                health_endpoint: Some("/health".into()),
            });
        }
        _ => {}
    }
    
    match config.role {
        Role::Worker | Role::Standalone => {
            // Start worker (after master is healthy for Standalone)
            if config.role == Role::Standalone {
                wait_for_master_health(&config).await?;
            }
            let status = start_worker(&config).await?;
            results.push(ServiceInfo {
                name: "Worker Agent".into(),
                executable: "AIClusterRuntime.exe --mode worker".into(),
                status,
                port: Some(config.settings.worker.port),
                health_endpoint: None,
            });
        }
        _ => {}
    }
    
    Ok(results)
}

#[tauri::command]
async fn stop_services() -> Result<(), String> {
    // Stop worker first (if running)
    if let Some(worker) = get_worker_process() {
        stop_process(worker, 10_000).await?;  // 10s timeout
    }
    // Stop master (if running)
    if let Some(master) = get_master_process() {
        stop_process(master, 10_000).await?;  // 10s timeout
    }
    Ok(())
}

#[tauri::command]
async fn get_service_status() -> Result<Vec<ServiceInfo>, String> {
    let config = RoleConfig::load()?;
    let mut services = vec![];
    
    match config.role {
        Role::Master | Role::Standalone => {
            services.push(check_master_status(&config).await);
        }
        _ => {}
    }
    
    match config.role {
        Role::Worker | Role::Standalone => {
            services.push(check_worker_status(&config).await);
        }
        _ => {}
    }
    
    Ok(services)
}

#[tauri::command]
async fn is_first_run() -> bool {
    RoleConfig::exists().map(|e| !e).unwrap_or(true)
}

#[tauri::command]
async fn open_dashboard(window: tauri::Window) -> Result<(), String> {
    let config = RoleConfig::load()?;
    let url = format!("http://{}:{}/", 
        config.settings.master.host,
        config.settings.master.dashboard_port,
    );
    // Navigate WebView to dashboard URL
    window.eval(&format!("window.location.href = '{}'", url))
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_master_url() -> Result<String, String> {
    let config = RoleConfig::load()?;
    Ok(format!("http://{}:{}", 
        config.settings.master.host,
        config.settings.master.port,
    ))
}
```

---

## 3. Startup Flow

### 3.1 Detailed Sequence

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  User     â”‚    â”‚  Rust Shell  â”‚    â”‚  Process Manager â”‚    â”‚  HTTP Client â”‚
â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚  Launch Studio  â”‚                      â”‚                     â”‚
     â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                      â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚                 â”‚  Check role.json     â”‚                     â”‚
     â”‚                 â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º    â”‚                     â”‚
     â”‚                 â”‚  â—„â”€â”€ exists/false    â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚                 â”‚  if first run:       â”‚                     â”‚
     â”‚                 â”‚  Show wizard UI       â”‚                     â”‚
     â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”‚                      â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚  Choose role    â”‚                      â”‚                     â”‚
     â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                      â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚                 â”‚  Save role.json      â”‚                     â”‚
     â”‚                 â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º    â”‚                     â”‚
     â”‚                 â”‚  â—„â”€â”€ OK              â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚                 â”‚  if role needs       â”‚                     â”‚
     â”‚                 â”‚  master:             â”‚                     â”‚
     â”‚                 â”‚  â”€â”€â–º Start Master     â”‚                     â”‚
     â”‚                 â”‚    CreateProcess(     â”‚                     â”‚
     â”‚                 â”‚      "runtime\        â”‚                     â”‚
     â”‚                 â”‚       AIClusterMaster â”‚                     â”‚
     â”‚                 â”‚       .exe")          â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚                 â”‚  Health loop:        â”‚                     â”‚
     â”‚                 â”‚  â”€â”€â–º GET /health     â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
     â”‚                 â”‚  â—„â”€â”€ 200 OK          â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”‚
     â”‚                 â”‚  (repeat every 1s)   â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚                 â”‚  if role needs       â”‚                     â”‚
     â”‚                 â”‚  worker:             â”‚                     â”‚
     â”‚                 â”‚  â”€â”€â–º Start Worker     â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚                 â”‚  Open dashboard      â”‚                     â”‚
     â”‚                 â”‚  â”€â”€â–º navigate:       â”‚                     â”‚
     â”‚                 â”‚    localhost:3000     â”‚                     â”‚
     â”‚                 â”‚                      â”‚                     â”‚
     â”‚  Dashboard      â”‚                      â”‚                     â”‚
     â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”‚                      â”‚                     â”‚
```

### 3.2 Idempotent Startup (Safe to Call Repeatedly)

```rust
async fn ensure_services_running(config: &RoleConfig) -> Result<(), String> {
    match config.role {
        Role::Master | Role::Standalone => {
            // Check if master process exists
            if let Some(process) = find_process("AIClusterRuntime.exe --mode master") {
                if process_healthy(process.pid).await {
                    return Ok(());  // Already running, no action needed
                }
                // Process exists but unhealthy â€” kill and restart
                kill_process(process.pid).await?;
            }
            // Start fresh
            start_process("runtime/AIClusterRuntime.exe --mode master", &[]).await?;
            wait_for_health("http://127.0.0.1:8000/health", 30_000).await?;
        }
        _ => {}
    }
    Ok(())
}
```

---

## 4. Watchdog Service

### 4.1 Background Monitor

```rust
pub struct Watchdog {
    check_interval: Duration,       // 5 seconds
    max_restarts: u32,              // 3 per service
    restart_delay: Duration,         // 2 seconds between restarts
}

impl Watchdog {
    pub async fn run(&self, config: &RoleConfig) {
        let mut master_restarts = 0u32;
        let mut worker_restarts = 0u32;
        
        loop {
            tokio::time::sleep(self.check_interval).await;
            
            match config.role {
                Role::Master | Role::Standalone => {
                    let status = check_master_health().await;
                    match status {
                        HealthStatus::Unreachable { .. } => {
                            if master_restarts < self.max_restarts {
                                restart_master().await;
                                master_restarts += 1;
                            } else {
                                notify_frontend("Master: max restarts reached");
                            }
                        }
                        HealthStatus::Healthy => {
                            master_restarts = 0;  // Reset on success
                        }
                        _ => {}
                    }
                }
                _ => {}
            }
        }
    }
}
```

### 4.2 Error Recovery Matrix

| Failure | Detection | Recovery | Max Attempts | User Notification |
|---------|-----------|----------|--------------|-------------------|
| Master process crash | Process handle signals exit | Auto-restart | 3 | Toast notification |
| Master hangs (no 200) | Health poll fails 3x | SIGTERM + restart | 3 | Toast + status bar |
| Worker process crash | Process handle signals exit | Auto-restart | Unlimited | Toast notification |
| Worker hangs | Master marks offline | Restart worker | Unlimited | Status bar indicator |
| Database error | Health returns 503 | Show error dialog | N/A | Full-screen error |
| Port conflict | Bind error on launch | Show port config | N/A | Settings dialog |
| Studio crash | Process exits | User re-launches | N/A | N/A |

---

## 5. Configuration Storage

### 5.1 role.json Location

```
%APPDATA%/AICluster/role.json    [User-scoped, persists across installs]
```

Or, in the installation directory:

```
{install}/config/role.json        [Machine-scoped, used by launcher]
```

### 5.2 role.json Format

```json
{
  "role": "master",
  "configured": true,
  "version": "2.0.0",
  "settings": {
    "master": {
      "host": "127.0.0.1",
      "port": 8000,
      "dashboard_port": 3000
    },
    "worker": {
      "master_url": null,
      "worker_name": null,
      "port": 8001
    }
  },
  "created_at": "2026-07-05T12:00:00Z"
}
```

---

## 6. Duplicate Instance Prevention

```rust
// Prevent multiple Studio instances using Windows named mutex

use windows::Win32::System::Threading::{
    CreateMutexW, OpenMutexW, CloseHandle,
};
use windows::Win32::Foundation::{
    HANDLE, ERROR_ALREADY_EXISTS,
};

pub struct SingletonGuard {
    handle: HANDLE,
}

impl SingletonGuard {
    pub fn new() -> Result<Self, String> {
        let name = "AIClusterStudio-Instance";
        let handle = unsafe {
            CreateMutexW(
                std::ptr::null(),
                false,
                name,
            )
        };
        
        if handle.is_invalid() {
            return Err("Failed to create mutex".into());
        }
        
        let err = unsafe { windows::Win32::Foundation::GetLastError() };
        if err == ERROR_ALREADY_EXISTS {
            unsafe { CloseHandle(handle) };
            return Err("Another instance is already running".into());
        }
        
        Ok(Self { handle })
    }
}

impl Drop for SingletonGuard {
    fn drop(&mut self) {
        unsafe { CloseHandle(self.handle) };
    }
}
```

---

## 7. Summary

| Component | Responsibility | Implementation |
|-----------|---------------|----------------|
| RoleManager | Read/write role config, detect first run | Rust module, reads `config/role.json` |
| ProcessManager | Start/stop/monitor EXEs | Rust `std::process::Command` |
| HealthChecker | HTTP health polling | Rust `reqwest` client |
| Watchdog | Crash detection + auto-restart | Rust async loop |
| TrayManager | System tray icon + menu | Tauri `SystemTray` API |
| SingletonGuard | Duplicate instance prevention | Windows named mutex |
| Tauri Commands | IPC bridge to React frontend | `#[tauri::command]` macros |
