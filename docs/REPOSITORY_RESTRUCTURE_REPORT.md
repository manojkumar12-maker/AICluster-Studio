# Repository Restructure Report

**AICluster v1.4 â€” Enterprise Packaging & Native Windows Architecture**
**Date:** 2026-07-05
**Current Version:** v2.0.0
**Target Version:** v1.4.0

---

## 1. Current State Assessment

### 1.1 Top-Level Layout (Current)

```
AICluster/
  .git/                    [204 MB]  Git history
  .github/                          CI/CD workflows
  .gitignore
  assets/                           Icons, manifest
  backend/                          FastAPI master server (source + venv + caches)
  build/                            Build system source + intermediate outputs
  CHANGELOG.md
  config/                           YAML configuration files
  CONTRIBUTING.md
  data/                             Runtime database (empty)
  dist/                             Packaged executables (335 MB)
  docs/                             Documentation
  frontend/                         Next.js dashboard (source + node_modules + .next)
  logs/                             Build logs
  master-control-center/            Tauri desktop app (source + Rust target 1.3 GB)
  models/                           AI model storage (empty)
  NOTICE.md
  nul                               Stray artifact
  plugins/                          Example plugin
  README.md
  release/                          Release executables (334 MB)
  scripts/                          PowerShell/Python scripts
  SECURITY.md
  shared/                           Shared protocol code
  studio/                           Tauri desktop app (source + Rust target 1.3 GB)
  VERSION
  worker/                           Worker agent (source + venv)
  worker-control-center/            Tauri desktop app (source + venv + Rust target)
```

### 1.2 Development Artifacts Identified

| Category | Paths | Est. Size | Disposition |
|----------|-------|-----------|-------------|
| Git metadata | `.git/` | 204 MB | Exclude from release |
| Virtual envs | `backend/.venv/`, `worker/.venv/`, `master-control-center/backend/.venv/`, `worker-control-center/backend/.venv/` | 218 MB | Exclude; use pip install |
| Rust build cache | `master-control-center/frontend/src-tauri/target/`, `studio/src-tauri/target/` | 2.6 GB | Exclude; clean build |
| Node modules | `frontend/node_modules/`, `studio/node_modules/`, `master-control-center/frontend/node_modules/`, `worker-control-center/frontend/node_modules/` | 800+ MB | Exclude; npm install |
| Frontend build | `frontend/.next/` | 69 MB | Exclude; npm run build |
| PyInstaller intermediates | `build/modules/build/`, `build/modules/dist/` | 350+ MB | Exclude; clean build |
| Test build artifacts | `build/hello/`, `build/hello2/` | 45 MB | Delete |
| Backend build artifact | `backend/app/build/main_master` | 113 MB | Delete |
| Bytecode caches | All `__pycache__/` dirs | ~100 MB | Exclude |
| Python cache dirs | `.pytest_cache/`, `.ruff_cache/` | 25 KB | Exclude |
| Environment files | `backend/.env`, `worker/.env`, `frontend/.env.local` | < 1 KB | Exclude (secrets) |
| Runtime logs | `logs/build.log`, `backend/logs/aicluster.log`, `dist/master/logs/aicluster.log` | 105 KB | Exclude |
| Stray artifact | `nul` | 155 B | Delete |
| Duplicate EXEs | `build/modules/dist/` == `dist/` == `release/` | ~1 GB total | Consolidate |

### 1.3 Source Code That Must Remain

All source code in the following directories is required:
- `backend/app/` â€” Master server application
- `worker/app/` â€” Worker agent application
- `frontend/src/` â€” Web dashboard source
- `studio/src/` + `studio/src-tauri/` â€” Studio IDE
- `master-control-center/frontend/` â€” Master control center
- `worker-control-center/frontend/` â€” Worker control center
- `shared/` â€” Shared protocol definitions
- `config/` â€” YAML configuration
- `plugins/` â€” Plugin packages
- `build/*.py` â€” Build system source (not outputs)
- `scripts/` â€” Utility scripts
- `docs/` â€” Documentation
- `assets/` â€” Icons and assets

---

## 2. Target Repository Structure

### 2.1 Proposed Production Layout

```
AICluster/
  README.md                         Minimal top-level README
  CHANGELOG.md                      Release history
  CONTRIBUTING.md                   Contribution guide
  SECURITY.md                       Security policy
  NOTICE.md                         Legal notice
  VERSION                           Version string
  LICENSE                           License file (if applicable)

  backend/                          Master server source
    app/                              Application code
    tests/                            Test suite
    requirements.txt                  Python dependencies
    pyproject.toml

  worker/                           Worker agent source
    app/                              Application code
    tests/                            Test suite
    requirements.txt
    pyproject.toml

  studio/                           AICluster Studio (primary UI)
    src/                              React frontend source
    src-tauri/                        Tauri v2 Rust shell
    package.json

  shared/                           Shared code
    py/                               Python shared modules
    ts/                               TypeScript shared types
    protocol/                         Protocol definitions

  runtime/                          Runtime support
    master-entry.py                   PyInstaller entry point
    worker-entry.py                   PyInstaller entry point
    launcher/                         Studio launcher service

  config/                           Runtime configuration
    default.yaml                      Default configuration
    production.yaml                   Production overrides

  assets/                           Static assets
    icons/                            Application icons
    installer/                        Installer assets
    manifest.json                     Asset manifest

  docs/                             All documentation
    Architecture/                     Architecture docs
    Installation/                     Installation guides
    Security/                         Security documentation
    Development/                      Developer guides
    Audit/                            Audit reports
    Release/                          Release notes
    API/                              API reference
    UserGuide/                        User documentation
    Migration/                        Migration guides

  tests/                            Integration and E2E tests
    integration/                      Integration test suite
    fixtures/                         Test fixtures

  scripts/                          Build and CI scripts
    build.ps1                         Production build script
    clean.ps1                         Cleanup script

  build/                            Build system source
    build.py                          Build orchestrator
    config.py                         Build configuration
    pyinstaller_builder.py            PyInstaller builder
    tauri_builder.py                  Tauri builder
    package.py                        Release packaging
    sign.py                           Code signing
    verify.py                         Build verification
    version.py                        Version management
    modules/                          Entry point scripts (source only)
    setup/                            Installer assets
    verification/                     Verification scripts

  release/                          Build output (gitignored)
    AICluster Studio.exe              Primary executable
    AIClusterRuntime.exe --mode master               Master service executable
    AIClusterRuntime.exe --mode worker               Worker service executable
    aicluster.exe                     CLI tool
    AIClusterSetup-1.4.0.exe          Installer
    checksums/                        SHA-256 checksums
    reports/                          Build reports

  data/                             Runtime data (gitignored)
  logs/                             Runtime logs (gitignored)
  models/                           AI model storage (gitignored)
  plugins/                          User plugins (gitignored, except examples)
```

### 2.2 Directory Classification

| Category | Directories |
|----------|-------------|
| **Application** | `backend/`, `worker/`, `studio/`, `shared/`, `runtime/` |
| **Build** | `build/`, `scripts/` |
| **Documentation** | `docs/` |
| **Assets** | `assets/` |
| **Configuration** | `config/` |
| **Runtime** | `data/`, `logs/`, `models/`, `plugins/` (all gitignored) |
| **Tests** | `tests/`, `backend/tests/`, `worker/tests/` |
| **Release** | `release/` (gitignored) |

---

## 3. Cleanup Action Plan

### 3.1 Files to Delete

| # | Path | Reason |
|---|------|--------|
| 1 | `nul` | Stray artifact from failed command |
| 2 | `build/hello/` | Test build artifacts |
| 3 | `build/hello2/` | Test build artifacts |
| 4 | `build/main_master/` | Empty directory |
| 5 | `build/test_pkg/` | Empty directory |
| 6 | `build/test_spec/` | Empty directory |
| 7 | `backend/app/build/` | Build intermediate (113 MB) |
| 8 | `backend/app/main_master_version.txt` | Build byproduct |
| 9 | `build/modules/*.spec` | Regenerated on build |
| 10 | `build/modules/*_version.txt` | Regenerated on build |
| 11 | `backend/.env.example` | Documented elsewhere |

### 3.2 Directories to Add to .gitignore

```
# Build intermediates
build/modules/build/
build/modules/dist/
build/hello/
build/hello2/
build/main_master/
build/test_pkg/
build/test_spec/

# Duplicate EXE directories (consolidated into release/)
dist/

# Backend build artifacts
backend/app/build/

# Environment files
.env
.env.local
.env.example

# Runtime data
data/*
logs/*
models/*
!models/.gitkeep

# OS metadata
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Rust build cache
**/src-tauri/target/
```

### 3.3 Files to Move to docs/

| Current Location | Target Location |
|-----------------|-----------------|
| `docs/DEPLOYMENT.md` | `docs/Deployment/DEPLOYMENT.md` |
| `docs/INSTALLATION.md` | `docs/Installation/INSTALLATION.md` |
| `docs/QUICK_START.md` | `docs/Installation/QUICK_START.md` |
| `docs/FIRST_CLUSTER.md` | `docs/UserGuide/FIRST_CLUSTER.md` |
| `docs/TROUBLESHOOTING.md` | `docs/UserGuide/TROUBLESHOOTING.md` |
| `docs/UPGRADING.md` | `docs/Migration/UPGRADING.md` |
| `docs/FAQ.md` | `docs/UserGuide/FAQ.md` |
| `docs/README_INSTALL.md` | `docs/Installation/README_INSTALL.md` |
| `docs/DOCUMENT_INDEX.md` | `docs/README.md` |
| `docs/integration-test-report.txt` | `docs/Audit/integration-test-report.txt` |
| `docs/Architecture/PROJECT_REVIEW.md` | `docs/Architecture/ARCHITECTURE.md` |
| `docs/Architecture/MERMAID_DIAGRAMS.md` | `docs/Architecture/DIAGRAMS.md` |
| `SECURITY.md` | `docs/Security/SECURITY.md` (keep symlink at root) |
| `CONTRIBUTING.md` | `docs/Development/CONTRIBUTING.md` (keep symlink at root) |

### 3.4 Documentation Index Update

A `docs/README.md` will serve as the documentation index, replacing `docs/DOCUMENT_INDEX.md`:

```markdown
# AICluster Documentation

## Architecture
- [Architecture Overview](Architecture/ARCHITECTURE.md)
- [Diagrams](Architecture/DIAGRAMS.md)
- [Database Schema](Architecture/DATABASE.md)
- [API Reference](Architecture/API_REFERENCE.md)
- [Worker Architecture](Architecture/WORKER_ARCHITECTURE.md)
- [Startup Sequence](Architecture/STARTUP_SEQUENCE.md)
- [UI Architecture](Architecture/UI_ARCHITECTURE.md)

## Installation
- [Installation Guide](Installation/INSTALLATION.md)
- [Quick Start](Installation/QUICK_START.md)

## Security
- [Security Overview](Security/SECURITY.md)
- [Security Hardening](Security/SECURITY_HARDENING.md)
- [Security Review](Audit/SECURITY_REVIEW.md)

## Development
- [Contributing Guide](Development/CONTRIBUTING.md)
- [Build System](Development/BUILD_SYSTEM.md)
- [Installer Build](Development/INSTALLER_BUILD.md)
- [Verification](Development/VERIFICATION.md)
- [Build Review](Development/BUILD_REVIEW.md)

## Audit
- [Project Aim](Audit/PROJECT_AIM.md)
- [Project Score](Audit/PROJECT_SCORE.md)
- [Code Review](Audit/CODE_REVIEW.md)
- [Security Review](Audit/SECURITY_REVIEW.md)
- [Master Validation](Audit/MASTER_VALIDATION_REPORT.md)
- [File Test Report](Audit/FILE_TEST_REPORT.md)
- [Vision vs Completion](Audit/VISION_VS_COMPLETION_AUDIT.md)

## User Guide
- [First Cluster Setup](UserGuide/FIRST_CLUSTER.md)
- [Troubleshooting](UserGuide/TROUBLESHOOTING.md)
- [FAQ](UserGuide/FAQ.md)

## Migration
- [Upgrading from v1.3.x](Migration/UPGRADING.md)
- [v1.4 Migration Guide](Migration/MIGRATION_REPORT.md)

## Release
- [Packaging Guide](Release/PACKAGING_GUIDE.md)
- [Release Layout](Release/RELEASE_LAYOUT.md)
- [Desktop Architecture](Release/DESKTOP_ARCHITECTURE.md)
- [Repository Structure](Release/REPOSITORY_STRUCTURE.md)
- [First Run Wizard](Release/FIRST_RUN_WIZARD.md)
- [Launcher Design](Release/LAUNCHER_DESIGN.md)
```

---

## 4. Cleanup Script

A `scripts/clean.ps1` will be created to automate repository cleanup:

```powershell
# AICluster Repository Cleanup Script
# Run before production builds or packaging

Write-Host "AICluster Repository Cleanup v1.4" -ForegroundColor Cyan

# Delete stray artifacts
Remove-Item -Path "nul" -ErrorAction SilentlyContinue
Write-Host "[OK] Removed stray artifact: nul"

# Delete test build artifacts
Remove-Item -Path "build/hello" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build/hello2" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build/main_master" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build/test_pkg" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build/test_spec" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed test build artifacts"

# Delete backend build intermediate
Remove-Item -Path "backend/app/build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend/app/main_master_version.txt" -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed backend build artifacts"

# Delete PyInstaller intermediates
Remove-Item -Path "build/modules/build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build/modules/dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build/modules/*.spec" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build/modules/*_version.txt" -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed PyInstaller intermediates"

# Delete bytecode caches
Get-ChildItem -Path "." -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
Write-Host "[OK] Removed all Python bytecode caches"

# Delete pytest/ruff caches
Remove-Item -Path "backend/.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend/.ruff_cache" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "worker/.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed test/cache directories"

# Delete virtual environments (user confirmation required)
$confirm = Read-Host "Delete virtual environments (.venv)? (y/N)"
if ($confirm -eq "y") {
    Get-ChildItem -Path "." -Directory -Filter ".venv" -Recurse | Remove-Item -Recurse -Force
    Write-Host "[OK] Removed virtual environments"
} else {
    Write-Host "[SKIP] Virtual environments preserved"
}

# Delete Rust build caches
Remove-Item -Path "master-control-center/frontend/src-tauri/target" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "studio/src-tauri/target" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "worker-control-center/frontend/src-tauri/target" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed Rust build caches"

# Delete node_modules (user confirmation required)
$confirm = Read-Host "Delete node_modules directories? (y/N)"
if ($confirm -eq "y") {
    Get-ChildItem -Path "." -Directory -Filter "node_modules" -Recurse | Remove-Item -Recurse -Force
    Write-Host "[OK] Removed node_modules directories"
} else {
    Write-Host "[SKIP] node_modules preserved"
}

# Delete frontend build
Remove-Item -Path "frontend/.next" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed frontend build cache"

# Delete environment files (contains secrets)
Remove-Item -Path "backend/.env" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend/.env.example" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "worker/.env" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "frontend/.env.local" -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed environment files (secrets)"

# Delete runtime logs
Remove-Item -Path "logs/*.log" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend/logs/*.log" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist/master/logs/*.log" -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Removed runtime logs"

Write-Host "`nCleanup complete!" -ForegroundColor Green
```

---

## 5. Files to Keep at Repository Root

After restructuring, the repository root will contain only:

```
README.md          Project overview (brief)
CHANGELOG.md       Version history
CONTRIBUTING.md    How to contribute
SECURITY.md        Security policy
NOTICE.md          Legal notices
VERSION            Version string
LICENSE            License file
.gitignore         Updated ignore rules
.github/           CI/CD workflows (kept for development)
```

All other documentation files move under `docs/`.

---

## 6. Internal Link Update Requirements

When moving files, the following link references must be updated:

### 6.1 README.md Links
- `docs/INSTALLATION.md` â†’ `docs/Installation/INSTALLATION.md`
- `docs/QUICK_START.md` â†’ `docs/Installation/QUICK_START.md`
- `docs/FIRST_CLUSTER.md` â†’ `docs/UserGuide/FIRST_CLUSTER.md`
- `docs/DEPLOYMENT.md` â†’ `docs/Deployment/DEPLOYMENT.md`
- `docs/TROUBLESHOOTING.md` â†’ `docs/UserGuide/TROUBLESHOOTING.md`
- `docs/FAQ.md` â†’ `docs/UserGuide/FAQ.md`
- `docs/UPGRADING.md` â†’ `docs/Migration/UPGRADING.md`

### 6.2 CHANGELOG.md Links
- Any `docs/` references need updating per the mapping above.

### 6.3 Internal Cross-References
All `.md` files in `docs/` that reference other docs using relative paths must be updated.

---

## 7. Success Criteria

- [ ] Repository root contains only 7 files + 2 directories (`.github/`, `docs/`)
- [ ] All source code preserved â€” zero deletions of functional code
- [ ] All internal links verified and updated
- [ ] `scripts/clean.ps1` runs without errors and produces expected results
- [ ] `git status` shows only intentional changes
- [ ] `build/build.py --verify-only` passes
- [ ] All tests pass after restructuring
