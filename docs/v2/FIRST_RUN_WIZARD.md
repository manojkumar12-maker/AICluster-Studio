# First Run Wizard Design

**AICluster v2.0 — Native Desktop Edition | Phase 5**
**Date:** 2026-07-05
**Status:** Design Only — No Implementation

---

## 1. Overview

The First Run Wizard appears once — on the very first launch after installation. It collects the user's role preference and basic configuration, then never shows again unless the user explicitly resets.

### 1.1 Trigger

```
┌──────────────────────────────────────────┐
│  Studio launches                          │
│                                          │
│  ┌─ Does config/role.json exist? ──┐     │
│  │  YES → Skip wizard, start       │     │
│  │         services, open dashboard │     │
│  │                                  │     │
│  │  NO  → Show First Run Wizard    │     │
│  └──────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

---

## 2. Wizard Screens

### 2.1 Screen 1: Welcome

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │              Welcome to AICluster                     │  │
│  │                                                       │  │
│  │     AICluster turns idle Windows PCs into a           │  │
│  │     private AI compute cluster for software           │  │
│  │     engineering.                                      │  │
│  │                                                       │  │
│  │     Everything runs on your local network —           │  │
│  │     no cloud, no subscriptions, no data leaving       │  │
│  │     your machines.                                    │  │
│  │                                                       │  │
│  │     ┌─────────────────────────────────────────────┐   │  │
│  │     │           [Get Started]                      │   │  │
│  │     └─────────────────────────────────────────────┘   │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Screen 2: Role Selection

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │             Choose Your Role                          │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ ○ Master (Recommended)                          │  │  │
│  │  │   Run the cluster controller. Your PC hosts      │  │  │
│  │  │   the master server, database, web dashboard,    │  │  │
│  │  │   and AI runtime. Other PCs can connect as       │  │  │
│  │  │   workers.                                       │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ ○ Worker                                         │  │  │
│  │  │   Join an existing cluster. Your PC contributes  │  │  │
│  │  │   compute capacity to a master on another        │  │  │
│  │  │   machine.                                       │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ ○ Standalone                                     │  │  │
│  │  │   All-in-one mode. Run everything on this PC —   │  │  │
│  │  │   master, worker, and Studio. No network setup   │  │  │
│  │  │   needed.                                        │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │              [Back]        [Continue]                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Screen 3: Configuration (Master)

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │             Configure Master                          │  │
│  │                                                       │  │
│  │  Master Server                                        │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Host:       [127.0.0.1             ]             │  │  │
│  │  │ Port:       [8000                   ]             │  │  │
│  │  │ Dashboard:  [3000                   ]             │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  Worker Discovery                                     │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ □ Allow LAN workers to register automatically   │  │  │
│  │  │ Worker Secret: [━━━━━━━━━━━━━━━━━━] [Generate]  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │              [Back]        [Continue]                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Screen 3: Configuration (Worker)

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │             Connect to Cluster                        │  │
│  │                                                       │  │
│  │  Master Connection                                    │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Master URL: [http://                 ]:8000      │  │  │
│  │  │ Worker Name: [My-PC                  ]           │  │  │
│  │  │ Worker Secret: [━━━━━━━━━━━━━━━━━━━━]           │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ [Test Connection]                                │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  Connection Status: Not tested                        │  │
│  │                                                       │  │
│  │              [Back]        [Continue]                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 Screen 3: Configuration (Standalone)

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │             Configure Standalone                      │  │
│  │                                                       │  │
│  │  Standalone mode runs everything on this PC.          │  │
│  │  No network configuration is required.                │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Master Port:  [8000               ]              │  │  │
│  │  │ Worker Port:  [8001               ]              │  │  │
│  │  │ Dashboard:    [3000               ]              │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │              [Back]        [Continue]                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.6 Screen 4: Setup Progress

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │             Setting Up AICluster                      │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ✓ Configuration saved                                │  │
│  │  ✓ Generating security keys                          │  │
│  │  ✓ Starting Master Server                            │  │
│  │  ✓ Waiting for health check                          │  │
│  │  ◌ Starting Worker Agent                             │  │
│  │  ◌ Opening Dashboard                                 │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.7 Screen 5: Complete

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │             You're All Set!                           │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │              ✅ AICluster is ready               │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  Role:     Master                                     │  │
│  │  URL:      http://localhost:8000                      │  │
│  │  Dashboard: http://localhost:3000                     │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Admin Password: aB3x-K9mQ-pL2r (save this!)    │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  □ Show on startup (disable to skip wizard)           │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │           [Open Dashboard]                       │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. React Component Structure

```
studio/src/
├── components/
│   ├── wizard/
│   │   ├── WizardContainer.tsx       # Stepper/wizard container
│   │   ├── WelcomeScreen.tsx         # Screen 1
│   │   ├── RoleSelectionScreen.tsx   # Screen 2
│   │   ├── MasterConfigScreen.tsx    # Screen 3 (Master)
│   │   ├── WorkerConfigScreen.tsx    # Screen 3 (Worker)
│   │   ├── StandaloneConfigScreen.tsx# Screen 3 (Standalone)
│   │   ├── SetupProgressScreen.tsx   # Screen 4
│   │   └── CompleteScreen.tsx        # Screen 5
│   │
│   └── common/
│       ├── PasswordDisplay.tsx       # Admin password display
│       └── ConnectionTest.tsx        # Worker connection test
```

### 3.1 State Management

```typescript
// studio/src/stores/wizard-store.ts
import { create } from 'zustand';

interface WizardState {
  step: number;                    // 0-4
  role: 'master' | 'worker' | 'standalone' | null;
  masterConfig: {
    host: string;
    port: number;
    dashboardPort: number;
    allowLan: boolean;
    workerSecret: string;
  };
  workerConfig: {
    masterUrl: string;
    workerName: string;
    workerSecret: string;
  };
  setupProgress: {
    currentStep: string;
    progress: number;              // 0-100
    errors: string[];
  };
  completed: boolean;
  
  // Actions
  setRole: (role: string) => void;
  setMasterConfig: (config: Partial<WizardState['masterConfig']>) => void;
  setWorkerConfig: (config: Partial<WizardState['workerConfig']>) => void;
  nextStep: () => void;
  prevStep: () => void;
  saveAndStart: () => Promise<void>;
}
```

### 3.2 Tauri IPC Calls

```typescript
// studio/src/lib/launcher.ts
import { invoke } from '@tauri-apps/api/core';

export interface RoleConfig {
  role: 'master' | 'worker' | 'standalone';
  settings: {
    master: { host: string; port: number; dashboardPort: number };
    worker: { masterUrl: string | null; workerName: string | null; port: number };
  };
}

export const launcher = {
  getRole: () => invoke<string | null>('get_role'),
  setRole: (role: string, settings?: any) => invoke('set_role', { role, settings }),
  startServices: () => invoke('start_services'),
  stopServices: () => invoke('stop_services'),
  getServiceStatus: () => invoke('get_service_status'),
  isFirstRun: () => invoke<boolean>('is_first_run'),
  openDashboard: () => invoke('open_dashboard'),
  getMasterUrl: () => invoke<string>('get_master_url'),
  setAutostart: (enabled: boolean) => invoke('set_autostart', { enabled }),
};
```

---

## 4. Reset Behavior

### 4.1 When Wizard Shows Again

| Condition | Wizard Shows? |
|-----------|---------------|
| Fresh install, first launch | YES |
| After "Show on startup" unchecked | NO (unless reset) |
| Config file deleted manually | YES |
| User clicks "Reset Configuration" in Settings | YES |
| Version upgrade from v1.x to v2.0 | YES (major version change) |
| After "Run Wizard Again" button | YES |

### 4.2 Reset Detection

```rust
fn should_show_wizard(config_path: &Path) -> bool {
    if !config_path.exists() {
        return true;  // No config yet
    }
    
    let config = read_config(config_path);
    if !config.configured {
        return true;  // Config exists but incomplete
    }
    
    // Check version upgrade
    let current_version = env!("CARGO_PKG_VERSION");
    let config_version = &config.version;
    if major_version_changed(current_version, config_version) {
        return true;  // Major version upgrade
    }
    
    false
}
```

---

## 5. Success Criteria

- [ ] Wizard appears on first launch after installation
- [ ] Wizard never appears again unless config is reset
- [ ] All 3 role paths (Master, Worker, Standalone) are functional
- [ ] Role selection persists across application restarts
- [ ] Master configuration allows custom port/host
- [ ] Worker configuration allows connection test
- [ ] Setup progress screen shows real-time status
- [ ] Admin password is displayed once, never again
- [ ] Reset from Settings re-shows the wizard
- [ ] Major version upgrade re-shows the wizard
- [ ] All text is user-friendly (no technical jargon)
- [ ] Keyboard navigation (Tab, Enter, Escape) works
- [ ] Back button preserves all entered data
