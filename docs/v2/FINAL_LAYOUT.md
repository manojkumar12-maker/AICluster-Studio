# Final Distribution Layout

**AICluster v2.0 â€” Native Desktop Edition | Phase 9**
**Date:** 2026-07-05
**Status:** Design Only â€” No Implementation

---

## 1. Installed Application Layout

### 1.1 Target Directory Structure

```
%ProgramFiles%\AICluster\
â”‚
â”œâ”€â”€ AICluster Studio.exe              [PRIMARY ENTRY POINT - Tauri v2]
â”‚   Size: ~80 MB
â”‚   Manifest: PerMonitorV2 DPI aware
â”‚   Signed: Authenticode SHA-256
â”‚
â”œâ”€â”€ runtime\                           [Backend services - managed by Studio]
â”‚   â”œâ”€â”€ AIClusterRuntime.exe --mode master           [FastAPI master server - 263 MB]
â”‚   â”œâ”€â”€ AIClusterRuntime.exe --mode worker           [Worker agent - 55 MB]
â”‚   â”œâ”€â”€ aicluster.exe                 [CLI tool - 31 MB, console]
â”‚   â””â”€â”€ runtime.json                  [Service manifest: ports, versions, health endpoints]
â”‚
â”œâ”€â”€ config\                            [Runtime configuration]
â”‚   â”œâ”€â”€ default.yaml                  [Factory defaults - read-only]
â”‚   â”œâ”€â”€ user.yaml                     [User overrides - created by wizard/settings]
â”‚   â”œâ”€â”€ cluster.yaml                  [Cluster topology]
â”‚   â”œâ”€â”€ models.yaml                   [LLM provider settings]
â”‚   â”œâ”€â”€ workers.yaml                  [Worker fleet configuration]
â”‚   â”œâ”€â”€ role.json                     [Role selection - created by wizard]
â”‚   â””â”€â”€ secrets.enc                   [Encrypted secrets - auto-generated]
â”‚
â”œâ”€â”€ assets\                            [Static resources]
â”‚   â”œâ”€â”€ icons\                        [Application icons]
â”‚   â”‚   â”œâ”€â”€ default.ico               [Main app icon]
â”‚   â”‚   â”œâ”€â”€ tray.ico                  [System tray icon]
â”‚   â”‚   â”œâ”€â”€ warning.ico               [Warning state icon]
â”‚   â”‚   â””â”€â”€ error.ico                 [Error state icon]
â”‚   â””â”€â”€ splash.png                    [Splash screen image]
â”‚
â”œâ”€â”€ licenses\                          [Third-party licenses]
â”‚   â”œâ”€â”€ NOTICE.txt                    [AICluster license and notice]
â”‚   â””â”€â”€ THIRD_PARTY.txt              [Third-party dependency licenses]
â”‚
â”œâ”€â”€ data\                              [Runtime databases (created at runtime)]
â”‚   â”œâ”€â”€ aicluster.db                  [Main SQLite database]
â”‚   â”œâ”€â”€ secret.key                    [Auto-generated JWT secret]
â”‚   â””â”€â”€ backups\                      [Database backups]
â”‚
â”œâ”€â”€ logs\                              [Runtime logs (created at runtime)]
â”‚   â”œâ”€â”€ master.log                    [Master server log]
â”‚   â”œâ”€â”€ worker.log                    [Worker agent log]
â”‚   â””â”€â”€ studio.log                    [Studio launcher log]
â”‚
â”œâ”€â”€ models\                            [LLM model files (user-managed)]
â”‚   â””â”€â”€ .gitkeep                       [Directory placeholder]
â”‚
â”œâ”€â”€ plugins\                           [User-installed plugins]
â”‚   â””â”€â”€ (installed plugin directories)
â”‚
â””â”€â”€ updates\                           [Update download cache]
    â””â”€â”€ (downloaded update files)
```

### 1.2 Directory Permissions

| Directory | Permissions | Created By | Purpose |
|-----------|-------------|------------|---------|
| `AICluster Studio.exe` | Read/Execute | Installer | Primary app |
| `runtime\` | Read/Execute | Installer | Backend services |
| `config\` | Read (default.yaml) / Read-Write (others) | Installer + Runtime | Configuration |
| `assets\` | Read | Installer | Static resources |
| `licenses\` | Read | Installer | Legal |
| `data\` | Read-Write (app only) | Installer (create) + Runtime | Databases, secrets |
| `logs\` | Read-Write (app only) | Installer (create) + Runtime | Logs |
| `models\` | Read-Write (user) | Installer (create) | LLM files |
| `plugins\` | Read-Write (user) | Installer (create) | Plugins |
| `updates\` | Read-Write (app only) | Runtime | Update cache |

---

## 2. Source Repository Layout

### 2.1 Development Repository (for developers)

```
AICluster\                              [Git repository root]
â”‚
â”œâ”€â”€ README.md                           [Project overview]
â”œâ”€â”€ CHANGELOG.md                        [Version history]
â”œâ”€â”€ CONTRIBUTING.md                     [How to contribute]
â”œâ”€â”€ SECURITY.md                         [Security policy]
â”œâ”€â”€ NOTICE.md                           [Legal notice]
â”œâ”€â”€ VERSION                             [Version string: "2.0.0"]
â”‚
â”œâ”€â”€ backend\                            [Master server source]
â”‚   â”œâ”€â”€ app\                            [Application code]
â”‚   â”œâ”€â”€ tests\                          [Test suite]
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â””â”€â”€ pyproject.toml
â”‚
â”œâ”€â”€ worker\                             [Worker agent source]
â”‚   â”œâ”€â”€ app\                            [Application code]
â”‚   â”œâ”€â”€ tests\                          [Test suite]
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â””â”€â”€ pyproject.toml
â”‚
â”œâ”€â”€ studio\                             [Desktop Studio source]
â”‚   â”œâ”€â”€ src\                            [React frontend]
â”‚   â”œâ”€â”€ src-tauri\                      [Rust shell]
â”‚   â””â”€â”€ package.json
â”‚
â”œâ”€â”€ frontend\                           [Web dashboard source]
â”‚   â”œâ”€â”€ src\                            [Next.js app]
â”‚   â”œâ”€â”€ public\                         [Static assets]
â”‚   â””â”€â”€ package.json
â”‚
â”œâ”€â”€ master-control-center\              [Legacy - will be deprecated]
â”‚   â”œâ”€â”€ frontend\                       [React UI]
â”‚   â””â”€â”€ backend\                        [Helper API]
â”‚
â”œâ”€â”€ worker-control-center\              [Legacy - will be deprecated]
â”‚   â”œâ”€â”€ frontend\                       [React UI]
â”‚   â””â”€â”€ backend\                        [Helper API]
â”‚
â”œâ”€â”€ runtime\                            [Entry point scripts]
â”‚   â”œâ”€â”€ master-entry.py                 [Master PyInstaller entry]
â”‚   â”œâ”€â”€ worker-entry.py                 [Worker PyInstaller entry]
â”‚   â”œâ”€â”€ cli-entry.py                    [CLI PyInstaller entry]
â”‚   â””â”€â”€ runtime.json                    [Service manifest]
â”‚
â”œâ”€â”€ shared\                             [Shared code]
â”‚   â”œâ”€â”€ py\                             [Python models]
â”‚   â”œâ”€â”€ ts\                             [TypeScript types]
â”‚   â””â”€â”€ protocol\                       [Wire protocol]
â”‚
â”œâ”€â”€ config\                             [Configuration templates]
â”‚   â”œâ”€â”€ default.yaml
â”‚   â”œâ”€â”€ production.yaml
â”‚   â”œâ”€â”€ cluster.yaml
â”‚   â”œâ”€â”€ models.yaml
â”‚   â””â”€â”€ workers.yaml
â”‚
â”œâ”€â”€ build\                              [Build system (source only)]
â”‚   â”œâ”€â”€ build.py                        [Orchestrator]
â”‚   â”œâ”€â”€ config.py                       [Build config]
â”‚   â”œâ”€â”€ pyinstaller_builder.py
â”‚   â”œâ”€â”€ tauri_builder.py
â”‚   â”œâ”€â”€ package.py
â”‚   â”œâ”€â”€ sign.py
â”‚   â”œâ”€â”€ verify.py
â”‚   â”œâ”€â”€ version.py
â”‚   â”œâ”€â”€ setup_builder.py
â”‚   â”œâ”€â”€ modules\                        [Source entry scripts - copied to runtime/]
â”‚   â”œâ”€â”€ setup\                          [Installer assets]
â”‚   â””â”€â”€ verification\                   [Verification scripts]
â”‚
â”œâ”€â”€ assets\                             [Static assets]
â”‚   â”œâ”€â”€ icons\
â”‚   â””â”€â”€ manifest.json
â”‚
â”œâ”€â”€ scripts\                            [Development/CI scripts]
â”‚   â”œâ”€â”€ build.ps1                       [Production build script]
â”‚   â”œâ”€â”€ clean.ps1                       [Repository cleanup]
â”‚   â”œâ”€â”€ setup.ps1                       [Dev environment setup]
â”‚   â””â”€â”€ worker-simulator.py
â”‚
â”œâ”€â”€ docs\                               [Documentation]
â”‚   â”œâ”€â”€ Architecture\
â”‚   â”œâ”€â”€ Installation\
â”‚   â”œâ”€â”€ Security\
â”‚   â”œâ”€â”€ Development\
â”‚   â”œâ”€â”€ Audit\
â”‚   â”œâ”€â”€ Release\
â”‚   â”œâ”€â”€ API\
â”‚   â”œâ”€â”€ UserGuide\
â”‚   â”œâ”€â”€ Migration\
â”‚   â””â”€â”€ v2\                             [v2.0 architecture documents]
â”‚
â”œâ”€â”€ tests\                              [Integration tests]
â”‚   â””â”€â”€ integration\
â”‚
â”œâ”€â”€ .github\                            [CI/CD workflows]
â”‚   â””â”€â”€ workflows\
â”‚       â”œâ”€â”€ ci.yml
â”‚       â”œâ”€â”€ security.yml
â”‚       â””â”€â”€ release.yml
â”‚
â”œâ”€â”€ .gitignore
â””â”€â”€ .pre-commit-config.yaml
```

---

## 3. Visual Comparison

### 3.1 Before (v2.0.0 Dev Layout)

```
AICluster/
â”œâ”€â”€ .git/                204 MB
â”œâ”€â”€ .github/
â”œâ”€â”€ assets/
â”œâ”€â”€ backend/              +.venv 101 MB
â”œâ”€â”€ build/                +build outputs 400+ MB
â”œâ”€â”€ CHANGELOG.md
â”œâ”€â”€ config/
â”œâ”€â”€ CONTRIBUTING.md
â”œâ”€â”€ data/                 (empty)
â”œâ”€â”€ dist/                 335 MB  â† DUPLICATE
â”œâ”€â”€ docs/
â”œâ”€â”€ frontend/             +node_modules + .next
â”œâ”€â”€ logs/
â”œâ”€â”€ master-control-center/+venv + node_modules + target
â”œâ”€â”€ models/               (empty)
â”œâ”€â”€ NOTICE.md
â”œâ”€â”€ nul                   â† STRAY
â”œâ”€â”€ plugins/
â”œâ”€â”€ README.md
â”œâ”€â”€ release/              334 MB  â† DUPLICATE
â”œâ”€â”€ scripts/
â”œâ”€â”€ SECURITY.md
â”œâ”€â”€ shared/
â”œâ”€â”€ studio/               +node_modules + target
â”œâ”€â”€ VERSION
â”œâ”€â”€ worker/               +.venv 49 MB
â””â”€â”€ worker-control-center/+venv + node_modules + target
```

### 3.2 After (v2.0 Clean Layout)

```
AICluster/
â”œâ”€â”€ .github/                    CI/CD
â”œâ”€â”€ assets/                     Static assets (< 1 MB)
â”œâ”€â”€ backend/                    Source only (no .venv)
â”œâ”€â”€ build/                      Source scripts only (no intermediates)
â”œâ”€â”€ CHANGELOG.md
â”œâ”€â”€ config/                     YAML templates
â”œâ”€â”€ CONTRIBUTING.md
â”œâ”€â”€ docs/
â”œâ”€â”€ frontend/                   Source only (no node_modules, no .next)
â”œâ”€â”€ master-control-center/      Source only (legacy, marked deprecated)
â”œâ”€â”€ NOTICE.md
â”œâ”€â”€ plugins/                    Example plugin
â”œâ”€â”€ README.md
â”œâ”€â”€ runtime/                    Entry point scripts
â”œâ”€â”€ scripts/
â”œâ”€â”€ SECURITY.md
â”œâ”€â”€ shared/
â”œâ”€â”€ studio/                     Source only (no node_modules, no target)
â”œâ”€â”€ tests/
â”œâ”€â”€ VERSION
â”œâ”€â”€ worker/                     Source only (no .venv)
â”œâ”€â”€ worker-control-center/      Source only (legacy, marked deprecated)
â”œâ”€â”€ .gitignore
â””â”€â”€ .pre-commit-config.yaml
```

**Repository size reduction: ~7 GB â†’ ~50 MB (source only)**

---

## 4. Release Package Comparison

### 4.1 Before (v2.0.0 Release)

```
AIClusterSetup-2.0.0.exe (~609 MB)
â”œâ”€â”€ AICluster Studio.exe
â”œâ”€â”€ AIClusterRuntime.exe --mode master
â”œâ”€â”€ AIClusterRuntime.exe --mode worker
â”œâ”€â”€ MasterControlCenter.exe      â† REDUNDANT
â”œâ”€â”€ WorkerControlCenter.exe      â† REDUNDANT
â”œâ”€â”€ aicluster.exe
â”œâ”€â”€ config/
â”œâ”€â”€ assets/
â”œâ”€â”€ licenses/
â”œâ”€â”€ data/                        (empty)
â”œâ”€â”€ logs/                        (empty)
â””â”€â”€ models/                      (empty)
```

### 4.2 After (v2.0 Release)

```
AIClusterSetup-2.0.0.exe (~430 MB)
â”œâ”€â”€ AICluster Studio.exe         [80 MB - ONLY visible EXE]
â”œâ”€â”€ runtime/                     [349 MB - hidden services]
â”‚   â”œâ”€â”€ AIClusterRuntime.exe --mode master      [263 MB]
â”‚   â”œâ”€â”€ AIClusterRuntime.exe --mode worker      [55 MB]
â”‚   â”œâ”€â”€ aicluster.exe            [31 MB]
â”‚   â””â”€â”€ runtime.json
â”œâ”€â”€ config/                      [10 KB]
â”‚   â”œâ”€â”€ default.yaml
â”‚   â”œâ”€â”€ cluster.yaml
â”‚   â”œâ”€â”€ models.yaml
â”‚   â””â”€â”€ workers.yaml
â”œâ”€â”€ assets/                      [1 MB]
â”‚   â””â”€â”€ icons/
â”œâ”€â”€ licenses/                    [50 KB]
â”‚   â”œâ”€â”€ NOTICE.txt
â”‚   â””â”€â”€ THIRD_PARTY.txt
â””â”€â”€ updates/                     (empty)
```

**Release size reduction: ~609 MB â†’ ~430 MB (29% smaller)**
**User-facing EXEs: 4 â†’ 1 (75% reduction)**

---

## 5. Success Criteria

| Criterion | Current (v2.0.0) | Target (v2.0) |
|-----------|-----------------|---------------|
| User-facing executables | 4 | **1** (Studio only) |
| Total EXEs in package | 6 | **4** (Studio + 3 runtime) |
| Repository size (source) | ~50 MB + ~7 GB dev artifacts | **~50 MB** (source only) |
| Release package size | ~609 MB | **~430 MB** |
| Start Menu entries | 4+ | **1** (Studio) |
| Config locations | 1 directory | **1 directory** |
| Runtime data locations | Scattered | **Consolidated under data/** |
| Log locations | Scattered | **Consolidated under logs/** |
| Documentation structure | Flat | **Hierarchical under docs/** |
