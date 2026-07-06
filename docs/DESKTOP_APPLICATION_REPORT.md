# Desktop Application Report

**AICluster v1.4 â€” Enterprise Packaging & Native Windows Architecture**
**Date:** 2026-07-05

---

## 1. Architecture: Studio as Unified Launcher

### 1.1 Current State (v2.0.0)

```
User launches:
  AIClusterRuntime.exe --mode master        [Console/GUI - backend service]
  AIClusterRuntime.exe --mode worker         [Console/GUI - backend service]
  AICluster Studio.exe        [Separate Tauri desktop app]
  MasterControlCenter.exe     [Separate Tauri desktop app]
  WorkerControlCenter.exe     [Separate Tauri desktop app]
  
  User must manually start master before Studio works.
  User must know which EXE to launch.
```

### 1.2 Target State (v1.4)

```
User launches:
  AICluster Studio.exe        [ONLY entry point - everything else is managed]

Studio internally manages:
  runtime/AIClusterRuntime.exe --mode master   [Started/stopped by Studio launcher]
  runtime/AIClusterRuntime.exe --mode worker   [Started/stopped by Studio launcher]
  
  Role: Master     -> Master + Studio
  Role: Worker     -> Worker + Studio (connects to remote master)
  Role: Standalone -> Master + Worker + Studio (all-in-one)
```

---

## 2. Launcher Component Design

### 2.1 Launcher Responsibilities

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    AICluster Studio.exe                      â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚  Tauri v2 Shell (Rust)                                â”‚  â”‚
â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚  â”‚
â”‚  â”‚  â”‚  Launcher Service (Rust sidecar)                 â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Process management                            â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Health monitoring                             â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Auto-restart on crash                         â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Duplicate instance prevention                 â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Firewall configuration                        â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - System tray integration                       â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Automatic startup                             â”‚  â”‚  â”‚
â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚  â”‚
â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚  â”‚
â”‚  â”‚  â”‚  First Run Wizard (React)                       â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Role selection                               â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Configuration setup                          â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Network discovery                            â”‚  â”‚  â”‚
â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚  â”‚
â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚  â”‚
â”‚  â”‚  â”‚  Main Application (React)                       â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Dashboard                                     â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - AI Chat                                       â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Repository Intelligence                       â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Workflow Designer                             â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Agent Designer                                â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Plugin Manager                                â”‚  â”‚  â”‚
â”‚  â”‚  â”‚  - Settings                                      â”‚  â”‚  â”‚
â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 2.2 Launcher Service API

The Rust sidecar exposes a local IPC API that the React frontend calls:

```rust
// studio/src-tauri/src/launcher.rs

#[tauri::command]
async fn get_role() -> Result<Role, String> {
    // Read config/role.json - returns Master | Worker | Standalone | Unconfigured
}

#[tauri::command]
async fn set_role(role: Role, master_url: Option<String>) -> Result<(), String> {
    // Write config/role.json
    // If Master: start AIClusterRuntime.exe --mode master
    // If Worker: start AIClusterRuntime.exe --mode worker
    // If Standalone: start both
}

#[tauri::command]
async fn start_services() -> Result<ServiceStatus, String> {
    // Launch required backend services based on role
    // Wait for health check before returning
}

#[tauri::command]
async fn stop_services() -> Result<(), String> {
    // Gracefully stop all managed processes
}

#[tauri::command]
async fn get_service_status() -> Result<HashMap<String, ProcessStatus>, String> {
    // Report status of each managed process
}

#[tauri::command]
async fn open_dashboard() -> Result<(), String> {
    // Open the web dashboard in Studio's webview
}

#[tauri::command]
async fn is_first_run() -> Result<bool, String> {
    // Check if config/role.json exists
}

#[tauri::command]
async fn get_master_url() -> Result<String, String> {
    // Return the master URL (local or remote based on role)
}

#[tauri::command]
async fn restart_service(name: String) -> Result<(), String> {
    // Restart a specific service
}
```

---

## 3. First Run Wizard

### 3.1 Flow

```
User launches AICluster Studio.exe (first time)
                    â”‚
                    â–¼
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚  Welcome Screen        â”‚
        â”‚  "Welcome to AICluster"â”‚
        â”‚  [Get Started]         â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â”‚
                    â–¼
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚  Role Selection        â”‚
        â”‚                        â”‚
        â”‚  [â—] Master            â”‚
        â”‚      Run the cluster   â”‚
        â”‚      controller        â”‚
        â”‚                        â”‚
        â”‚  [ ] Worker            â”‚
        â”‚      Join a cluster    â”‚
        â”‚                        â”‚
        â”‚  [ ] Standalone        â”‚
        â”‚      All-in-one mode   â”‚
        â”‚                        â”‚
        â”‚  [Continue]             â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â”‚
                    â–¼
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚  Configuration         â”‚
        â”‚                        â”‚
        â”‚  Master:               â”‚
        â”‚    Port: [8000]        â”‚
        â”‚    Dashboard: [3000]   â”‚
        â”‚                        â”‚
        â”‚  Worker:               â”‚
        â”‚    Master URL: [______]â”‚
        â”‚    Worker Name: [_____]â”‚
        â”‚                        â”‚
        â”‚  [Continue]             â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â”‚
                    â–¼
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚  Setup Progress        â”‚
        â”‚                        â”‚
        â”‚  [====>       ] 40%    â”‚
        â”‚  - Generating secrets  â”‚
        â”‚  - Starting services   â”‚
        â”‚  - Verifying health    â”‚
        â”‚                        â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â”‚
                    â–¼
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚  Complete!             â”‚
        â”‚                        â”‚
        â”‚  AICluster is ready    â”‚
        â”‚                        â”‚
        â”‚  Master: localhost:8000â”‚
        â”‚  Admin password: â€¢â€¢â€¢â€¢  â”‚
        â”‚                        â”‚
        â”‚  [Open Dashboard]      â”‚
        â”‚                        â”‚
        â”‚  â–¡ Don't show again    â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 3.2 Configuration File

```json
// config/role.json â€” Created by first-run wizard
{
  "role": "master",
  "configured": true,
  "version": "1.4.0",
  "settings": {
    "master": {
      "host": "127.0.0.1",
      "port": 8000,
      "dashboard_port": 3000
    },
    "worker": {
      "master_url": "",
      "worker_name": "",
      "port": 8001
    }
  },
  "created_at": "2026-07-05T12:00:00Z"
}
```

### 3.3 Role Behaviors

| Role | Master Starts | Worker Starts | Web Dashboard | Studio Features |
|------|---------------|---------------|---------------|-----------------|
| **Master** | Yes | No | Local | Full cluster management |
| **Worker** | No | Yes | Remote | Local monitoring |
| **Standalone** | Yes | Yes | Local | All features |

---

## 4. Launcher Process Management

### 4.1 Startup Sequence

```
Studio Launch
    â”‚
    â”œâ”€â”€ Check role.json exists?
    â”‚   â”œâ”€â”€ No  â†’ Show First Run Wizard
    â”‚   â””â”€â”€ Yes â†’ Continue
    â”‚
    â”œâ”€â”€ Check for duplicate instance (named mutex)
    â”‚   â”œâ”€â”€ Found â†’ Focus existing window, exit
    â”‚   â””â”€â”€ Not found â†’ Continue
    â”‚
    â”œâ”€â”€ Read role from role.json
    â”‚
    â”œâ”€â”€ Start required services:
    â”‚   â”œâ”€â”€ Master:
    â”‚   â”‚   â”œâ”€â”€ Launch: runtime\AIClusterRuntime.exe --mode master
    â”‚   â”‚   â”œâ”€â”€ Port: config.port (default 8000)
    â”‚   â”‚   â”œâ”€â”€ Wait: HTTP GET /health (up to 30s, 1s interval)
    â”‚   â”‚   â””â”€â”€ Fail: Show error, offer retry
    â”‚   â”‚
    â”‚   â”œâ”€â”€ Worker:
    â”‚   â”‚   â”œâ”€â”€ Launch: runtime\AIClusterRuntime.exe --mode worker
    â”‚   â”‚   â”œâ”€â”€ Master URL: config.master_url
    â”‚   â”‚   â”œâ”€â”€ Wait: Process started
    â”‚   â”‚   â””â”€â”€ Fail: Log error, continue (non-critical)
    â”‚   â”‚
    â”‚   â””â”€â”€ Services healthy?
    â”‚       â””â”€â”€ Yes â†’ Open dashboard webview
    â”‚
    â””â”€â”€ Enter main event loop
```

### 4.2 Shutdown Sequence

```
Studio Close (user or system)
    â”‚
    â”œâ”€â”€ Send SIGTERM to managed processes
    â”œâ”€â”€ Wait up to 10s for graceful shutdown
    â”œâ”€â”€ Force kill any remaining processes
    â”œâ”€â”€ Flush logs
    â””â”€â”€ Exit
```

### 4.3 Crash Recovery

```rust
// Process watchdog implementation

fn start_watchdog(rx: Receiver<ProcessEvent>) {
    loop {
        match rx.recv().unwrap() {
            ProcessEvent::Exited { pid, exit_code } => {
                log::warn!("Process {} exited with code {}", pid, exit_code);
                
                // Auto-restart master if crashed
                if is_master_process(pid) {
                    if should_restart(exit_code) {
                        start_master();
                        wait_for_health_check();
                        notify_frontend(ServiceStatus::Restarted { service: "master" });
                    }
                }
            }
            ProcessEvent::Hung { pid } => {
                log::error!("Process {} is not responding", pid);
                kill_process(pid);
                start_master(); // restart
            }
        }
    }
}
```

### 4.4 Duplicate Instance Prevention

```rust
// Windows named mutex for singleton enforcement
use tauri::Manager;

fn prevent_duplicate(app: &tauri::App) -> Result<(), String> {
    let mutex = CreateMutexW(
        null_mut(),
        FALSE,
        "AIClusterStudio-Instance-Mutex",
    );
    
    if GetLastError() == ERROR_ALREADY_EXISTS {
        // Focus existing window and exit
        let hwnd = FindWindowW(None, "AICluster Studio");
        SetForegroundWindow(hwnd);
        std::process::exit(0);
    }
    
    Ok(())
}
```

---

## 5. Windows Integration

### 5.1 Application Metadata

```xml
<!-- studio/src-tauri/tauri.conf.json â€” Windows config -->
{
  "tauri": {
    "bundle": {
      "windows": {
        "wix": {
          "language": "en-US",
          "template": "main.wxs"
        }
      },
      "icon": [
        "assets/icons/32x32.png",
        "assets/icons/128x128.png",
        "assets/icons/128x128@2x.png",
        "assets/icons/icon.icns",
        "assets/icons/icon.ico"
      ],
      "identifier": "com.aicluster.studio",
      "publisher": "AICluster",
      "category": "DeveloperTool",
      "shortDescription": "AICluster Studio",
      "longDescription": "AI-powered software engineering platform"
    },
    "systemTray": {
      "iconPath": "assets/icons/tray-icon.png",
      "menuOnLeftClick": false,
      "menu": [
        { "id": "show", "text": "Show AICluster" },
        { "id": "dashboard", "text": "Open Dashboard" },
        { "id": "separator" },
        { "id": "restart", "text": "Restart Services" },
        { "id": "separator" },
        { "id": "quit", "text": "Quit" }
      ]
    }
  }
}
```

### 5.2 System Tray Behavior

| Action | Behavior |
|--------|----------|
| Close window | Minimize to tray (don't exit) |
| Tray icon double-click | Show/hide main window |
| Tray right-click | Context menu: Show, Dashboard, Restart, Quit |
| System shutdown | Graceful stop of all services |
| User logout | Stop services, save state |

### 5.3 Auto-Start

```rust
// Register for automatic startup on login
#[tauri::command]
fn set_autostart(enabled: bool) -> Result<(), String> {
    let key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
    let hklm = RegKey::predef(HKEY_CURRENT_USER);
    
    let run_key = hklm.open_subkey_with_flags(
        key,
        KEY_SET_VALUE,
    ).map_err(|e| e.to_string())?;
    
    if enabled {
        let exe_path = std::env::current_exe()
            .map_err(|e| e.to_string())?;
        run_key.set_value(
            "AICluster Studio",
            &reg_value::REG_SZ,
            &exe_path.to_string_lossy().to_string(),
        ).map_err(|e| e.to_string())?;
    } else {
        run_key.delete_value("AICluster Studio")
            .map_err(|e| e.to_string())?;
    }
    
    Ok(())
}
```

### 5.4 High DPI Support

```rust
// studio/src-tauri/tauri.conf.json
{
  "tauri": {
    "windows": [
      {
        "title": "AICluster Studio",
        "width": 1400,
        "height": 900,
        "minWidth": 1024,
        "minHeight": 700,
        "center": true,
        "resizable": true,
        "decorations": true,
        "fullscreen": false,
        "skipTaskbar": false,
        "scaleFactor": true  // Enable High DPI scaling
      }
    ]
  }
}
```

### 5.5 Dark Mode

```css
/* Detect and follow Windows dark mode preference */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1a1b1e;
    --bg-secondary: #25262b;
    --text-primary: #c1c2c5;
    --text-secondary: #909296;
    --accent: #4c6ef5;
  }
}

@media (prefers-color-scheme: light) {
  :root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --text-primary: #25262b;
    --text-secondary: #5c5f66;
    --accent: #4c6ef5;
  }
}
```

---

## 6. Distribution Binary Reorganization

### 6.1 Post-Migration Binary Layout

| Current (v2.0.0) | Target (v1.4) | Notes |
|------------------|---------------|-------|
| `AIClusterRuntime.exe --mode master` (in dist/) | `runtime/AIClusterRuntime.exe --mode master` | Managed by Studio |
| `AIClusterRuntime.exe --mode worker` (in dist/) | `runtime/AIClusterRuntime.exe --mode worker` | Managed by Studio |
| `aicluster.exe` (in dist/) | `runtime/aicluster.exe` | CLI only |
| `AICluster Studio.exe` (in studio/) | `AICluster Studio.exe` (root) | Primary entry point |
| `MasterControlCenter.exe` | Removed | Functionality merged into Studio |
| `WorkerControlCenter.exe` | Removed | Functionality merged into Studio |

### 6.2 Legacy App Migration

MasterControlCenter and WorkerControlCenter are separate Tauri apps whose functionality must be absorbed into Studio:

| Feature | Current Location | Target Location |
|---------|-----------------|-----------------|
| Cluster dashboard | MasterControlCenter | Studio â†’ Dashboard |
| Worker monitoring | WorkerControlCenter | Studio â†’ Workers |
| Job management | MasterControlCenter | Studio â†’ Jobs |
| Worker pause/resume | WorkerControlCenter | Studio â†’ Workers |
| Log viewer | Both | Studio â†’ Logs |
| Settings | Both | Studio â†’ Settings |

---

## 7. Studio UI Updates for Launcher Role

### 7.1 New Pages/Components

| Component | Purpose |
|-----------|---------|
| `FirstRunWizard` | Role selection, configuration, setup progress |
| `ServiceManager` | Start/stop/restart backend services |
| `SystemTrayMenu` | Tray icon with quick actions |
| `RoleIndicator` | Shows current role in status bar |
| `ServiceStatusBar` | Shows master/worker health status |
| `SetupProgress` | Animated progress during first-run setup |
| `AdminPasswordDisplay` | Shows generated admin password on first run |

### 7.2 New Tauri Commands (Rust Sidecar)

```rust
#[tauri::command]
get_role() -> Role
set_role(Role, Option<String>)
start_services() -> ServiceStatus
stop_services()
restart_service(String)
get_service_status() -> HashMap<String, ProcessStatus>
is_first_run() -> bool
open_dashboard()
get_master_url() -> String
set_autostart(bool)
get_autostart() -> bool
open_logs_directory()
open_data_directory()
```

---

## 8. Success Criteria

- [ ] Studio is the only EXE users need to launch
- [ ] First Run Wizard shows on first launch, never again unless reset
- [ ] Role is persisted securely in `config/role.json`
- [ ] Master/Worker services start automatically based on role
- [ ] Services restart automatically after crash (max 3 attempts)
- [ ] Duplicate instance prevention works (second launch focuses first)
- [ ] System tray shows on close, app doesn't exit
- [ ] Auto-start on login works
- [ ] Dark mode follows Windows theme
- [ ] High DPI displays correctly
- [ ] All 98 existing tests pass
- [ ] No console windows appear during normal operation
- [ ] Installer creates Start Menu and Desktop shortcuts
- [ ] Uninstall removes all shortcuts, services stop cleanly
