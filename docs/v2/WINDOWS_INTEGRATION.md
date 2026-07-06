# Windows Integration Design

**AICluster v2.0 â€” Native Desktop Edition | Phase 7**
**Date:** 2026-07-05
**Status:** Design Only â€” No Implementation

---

## 1. Windows Shell Integration

### 1.1 Feature Map

| Feature | Status v2.0.0 | Target v2.0 |
|---------|--------------|-------------|
| Start Menu shortcut | Via installer | âœ“ Auto-created |
| Desktop shortcut | Via installer (optional) | âœ“ Auto-created |
| System Tray | Not implemented | âœ“ Always present |
| Apps & Features entry | Via installer | âœ“ Proper metadata |
| Automatic startup | Not implemented | âœ“ Optional, configurable |
| High DPI support | Basic | âœ“ Per-monitor DPI aware |
| Dark Mode | Fixed dark theme | âœ“ Follows Windows theme |
| File Associations | Not implemented | âœ“ `.aicluster` project files |
| Windows Notifications | Not implemented | âœ“ Job complete, errors, updates |
| Protocol handler | Not implemented | âœ“ `aicluster://` deep links |

### 1.2 Application Metadata

```xml
<!-- Embedded in AICluster Studio.exe via Tauri -->
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    name="AICluster.Studio"
    version="2.0.0.0"
    processorArchitecture="amd64"
    type="win32"/>
  <description>AICluster Studio - AI-Powered Software Engineering Platform</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <!-- High DPI support -->
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
    </windowsSettings>
  </application>
</assembly>
```

---

## 2. System Tray

### 2.1 Tauri Configuration

```json
{
  "tauri": {
    "systemTray": {
      "iconPath": "assets/icons/tray-icon.ico",
      "iconAsTemplate": true,
      "menuOnLeftClick": false,
      "menu": [
        { "id": "show", "text": "Show AICluster Studio" },
        { "id": "dashboard", "text": "Open Dashboard" },
        { "id": "separator" },
        { "id": "restart_services", "text": "Restart Services" },
        { "id": "separator" },
        { "id": "master_status", "text": "Master: Running", "disabled": true },
        { "id": "worker_status", "text": "Worker: Running", "disabled": true },
        { "id": "separator" },
        { "id": "settings", "text": "Settings" },
        { "id": "separator" },
        { "id": "quit", "text": "Quit AICluster" }
      ]
    }
  }
}
```

### 2.2 Tray Behavior

| User Action | System Behavior |
|-------------|-----------------|
| Click window close button | Minimize to tray (app keeps running) |
| Double-click tray icon | Show/hide main window |
| Right-click tray icon | Show context menu |
| "Show AICluster Studio" | Bring window to foreground |
| "Open Dashboard" | Open dashboard in default browser |
| "Restart Services" | Stop + start master/worker |
| "Quit AICluster" | Stop all services + exit |
| System shutdown/logoff | Graceful stop all services |

### 2.3 Tray Icon States

```
Normal:        [A]  (default icon, services running)
Warning:       [A!] (service degraded, e.g. worker offline)
Error:         [Ax] (critical, e.g. master not responding)
Updating:      [Aâ†»] (update in progress)
Idle:          [A ] (no services running, tray only)
```

---

## 3. Windows Notifications

### 3.1 Notification Types

| Event | Notification | Priority |
|-------|-------------|----------|
| Master started | "Master Server is running on port 8000" | Low |
| Worker connected | "Worker 'PC-Name' has connected" | Low |
| Worker disconnected | "Worker 'PC-Name' went offline" | Medium |
| Job completed | "Job 'scan-repo' completed successfully" | Low |
| Job failed | "Job 'deploy' failed: connection refused" | Medium |
| Update available | "AICluster v2.0.1 is available" | Medium |
| Update downloaded | "Update ready to install. Restart to apply." | High |
| Error | "Master Server crashed. Restarting..." | High |

### 3.2 Implementation

```rust
// studio/src-tauri/src/launcher/notifications.rs

use tauri::api::notification::Notification;

pub fn notify_master_started(app: &tauri::AppHandle) {
    Notification::new(app.config().tauri.bundle.identifier.clone())
        .title("AICluster")
        .body("Master Server is running on port 8000")
        .icon("assets/icons/tray-icon.ico")
        .show()
        .unwrap();
}

pub fn notify_service_crashed(app: &tauri::AppHandle, service: &str) {
    Notification::new(app.config().tauri.bundle.identifier.clone())
        .title("AICluster - Service Alert")
        .body(&format!("{} crashed. Auto-restarting...", service))
        .icon("assets/icons/warning.ico")
        .show()
        .unwrap();
}
```

---

## 4. Start Menu & Shortcuts

### 4.1 Inno Setup Configuration

```iss
; Start Menu
[Icons]
Name: "{group}\AICluster Studio"; Filename: "{app}\AICluster Studio.exe"; 
    WorkingDir: "{app}"; Comment: "AICluster Studio - AI Software Engineering"
Name: "{group}\AICluster Dashboard"; Filename: "http://localhost:3000"; 
    Comment: "Open AICluster Web Dashboard"
Name: "{group}\AICluster Logs"; Filename: "{app}\logs"; 
    Comment: "View AICluster log files"
Name: "{group}\Uninstall AICluster"; Filename: "{uninstallexe}"

; Desktop
[Icons]
Name: "{commondesktop}\AICluster Studio"; Filename: "{app}\AICluster Studio.exe";
    WorkingDir: "{app}"; Tasks: desktopicon; Comment: "AICluster Studio"
```

### 4.2 Shortcut Properties

| Property | Value |
|----------|-------|
| Target | `%ProgramFiles%\AICluster\AICluster Studio.exe` |
| Start in | `%ProgramFiles%\AICluster` |
| Run | Normal window |
| Comment | "AICluster Studio - AI-Powered Software Engineering Platform" |
| AppUserModelID | `AICluster.Studio` |
| AppUserModelToastActivator | `{CLSID}` |

---

## 5. Apps & Features

### 5.1 Registry Entries

```reg
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AICluster]
"DisplayName"="AICluster Studio"
"DisplayVersion"="2.0.0"
"Publisher"="AICluster"
"DisplayIcon"="C:\\Program Files\\AICluster\\AICluster Studio.exe"
"InstallLocation"="C:\\Program Files\\AICluster"
"UninstallString"="C:\\Program Files\\AICluster\\unins000.exe"
"EstimatedSize"=dword:000f4240      ; ~1 GB
"URLInfoAbout"="https://aicluster.local"
"HelpLink"="https://aicluster.local/support"
"NoModify"=dword:00000001
"NoRepair"=dword:00000000           ; Allow repair
"InstallDate"="20260705"
"Language"=dword:00000409           ; en-US
```

---

## 6. Auto-Start

### 6.1 Implementation

```rust
// studio/src-tauri/src/launcher/autostart.rs

use std::io;
use winreg::enums::*;
use winreg::RegKey;

const AUTOSTART_KEY: &str = 
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
const APP_NAME: &str = "AICluster Studio";

pub fn set_autostart(enabled: bool, exe_path: &str) -> io::Result<()> {
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let run_key = hkcu.open_subkey_with_flags(
        AUTOSTART_KEY, 
        KEY_SET_VALUE | KEY_QUERY_VALUE
    )?;
    
    if enabled {
        run_key.set_value(APP_NAME, &exe_path)?;
    } else {
        run_key.delete_value(APP_NAME)?;
    }
    
    Ok(())
}

pub fn is_autostart_enabled() -> io::Result<bool> {
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let run_key = hkcu.open_subkey_with_flags(
        AUTOSTART_KEY, 
        KEY_QUERY_VALUE
    )?;
    
    match run_key.get_value::<String, _>(APP_NAME) {
        Ok(_) => Ok(true),
        Err(ref e) if e.kind() == io::ErrorKind::NotFound => Ok(false),
        Err(e) => Err(e),
    }
}
```

---

## 7. Dark Mode Support

### 7.1 Windows Theme Detection

```rust
// studio/src-tauri/src/launcher/theme.rs

use winreg::enums::*;
use winreg::RegKey;

const THEME_KEY: &str = 
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize";

pub fn is_windows_dark_mode() -> bool {
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    if let Ok(key) = hkcu.open_subkey(THEME_KEY) {
        if let Ok(value) = key.get_value::<u32, _>("AppsUseLightTheme") {
            return value == 0;  // 0 = dark, 1 = light
        }
    }
    false  // Default to light
}

#[tauri::command]
fn get_theme() -> String {
    if is_windows_dark_mode() { "dark".into() } else { "light".into() }
}
```

### 7.2 CSS Theme Switching

```typescript
// studio/src/hooks/useTheme.ts
import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

type Theme = 'dark' | 'light';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>('dark');
  
  useEffect(() => {
    // Get initial theme
    invoke<string>('get_theme').then(setTheme);
    
    // Listen for Windows theme changes (poll every 30s)
    const interval = setInterval(async () => {
      const current = await invoke<string>('get_theme');
      setTheme(current as Theme);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);
  
  return theme;
}
```

---

## 8. File Associations

### 8.1 AICluster Project Files

```json
{
  "tauri": {
    "bundle": {
      "windows": {
        "wix": {
          "fragments": [{
            "fileAssociation": {
              "ext": "aicluster",
              "description": "AICluster Project File",
              "progid": "AICluster.Project",
              "iconIndex": 0
            }
          }]
        }
      }
    }
  }
}
```

---

## 9. Protocol Handler

### 9.1 Deep Links

```json
{
  "tauri": {
    "plugins": {
      "deep-link": {
        "desktop": {
          "schemes": ["aicluster"]
        }
      }
    }
  }
}
```

Supported deep link actions:

| URL | Action |
|-----|--------|
| `aicluster://dashboard` | Open dashboard |
| `aicluster://workflows` | Open workflow designer |
| `aicluster://chat` | Open AI chat |
| `aicluster://settings` | Open settings |
| `aicluster://repositories/{id}` | Open specific repository |

---

## 10. Firewall Configuration

```iss
; Inno Setup â€” Firewall rules
[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
    if CurStep = ssPostInstall then
    begin
        if WizardIsTaskSelected('firewall') then
        begin
            // Allow master through firewall
            Exec('netsh', 
                'advfirewall firewall add rule name="AICluster Master" ' +
                'dir=in action=allow program="' + ExpandConstant('{app}') + 
                '\runtime\AIClusterRuntime.exe --mode master" enable=yes profile=private',
                '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
            
            // Allow worker through firewall  
            Exec('netsh',
                'advfirewall firewall add rule name="AICluster Worker" ' +
                'dir=in action=allow program="' + ExpandConstant('{app}') + 
                '\runtime\AIClusterRuntime.exe --mode worker" enable=yes profile=private',
                '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        end;
    end;
end;
```

---

## 11. Success Criteria

- [ ] System tray icon appears on launch
- [ ] Closing window minimizes to tray (doesn't exit)
- [ ] Tray menu shows correct service status
- [ ] Double-click tray icon shows/hides window
- [ ] Windows notifications appear for key events
- [ ] Start Menu shortcut created during install
- [ ] Desktop shortcut created (optional)
- [ ] App appears in Apps & Features
- [ ] Auto-start works (enabled in settings)
- [ ] Dark mode follows Windows theme
- [ ] High DPI displays correctly at 150%, 200%
- [ ] `.aicluster` files open in Studio
- [ ] `aicluster://` deep links work
- [ ] Firewall rules created during install
- [ ] Uninstall removes all shortcuts, tray does not persist
