# AICluster Build System Discovery

## Overview

The build system produces 7 executable targets + 1 installer from a unified Python orchestration framework.

**Entry point**: `python -m build.build` or `build-all.bat`
**Location**: `build/` directory (16 Python modules + subpackages)

---

## Build Targets

| # | Target | EXE Name | Packager | Size (est.) |
|---|--------|----------|----------|-------------|
| 1 | Master Server | `AIClusterMaster.exe` | PyInstaller | ~80 MB |
| 2 | Worker Service | `AIClusterWorker.exe` | PyInstaller | ~40 MB |
| 3 | CLI | `aicluster.exe` | PyInstaller | ~10 MB |
| 4 | Master Control Center | `MasterControlCenter.exe` | Tauri v2 | ~8-12 MB |
| 5 | Worker Control Center | `WorkerControlCenter.exe` | Tauri v2 | ~8-12 MB |
| 6 | AICluster Studio | `AIClusterStudio.exe` | Tauri v2 | ~8-12 MB |
| 7 | AIClusterSetup | `AIClusterSetup-<ver>.exe` | Inno Setup 6 | ~500 MB |

---

## Pipeline (12 Stages)

```
build.py: run(cfg) 
  │
  ├── 1. Environment Verification (verify.py)
  │   ├── Check Python 3.12+ 
  │   ├── Check Node.js 18+
  │   ├── Check Rust/Cargo 1.70+
  │   ├── Check Tauri CLI 2.0+
  │   ├── Check PyInstaller
  │   ├── Check Inno Setup 6
  │   └── Check 7-Zip, signtool (optional)
  │
  ├── 2. Clean (clean.py)
  │   └── Remove temp/, dist/, artifacts/, checksums/, optionally release/, logs/, __pycache__
  │
  ├── 3. Build Frontends (frontend.py)
  │   ├── Master Dashboard (frontend/ -> npm run build -> .next/)
  │   ├── MCC Web (master-control-center/frontend/ -> npm run build -> dist/)
  │   ├── WCC Web (worker-control-center/frontend/ -> npm run build -> dist/)
  │   └── Studio Web (studio/ -> npm run build -> dist/)
  │
  ├── 4. Build PyInstaller Targets (pyinstaller_builder.py)
  │   ├── AIClusterMaster.exe
  │   │   ├── Entry: modules/master_entry.py
  │   │   ├── Method: --collect-all (captures fastapi/uvicorn/sqlalchemy sub-modules)
  │   │   └── VSVersionInfo embedded
  │   ├── AIClusterWorker.exe
  │   │   ├── Entry: modules/worker_entry.py
  │   │   └── Method: --collect-all
  │   └── aicluster.exe
  │       ├── Entry: modules/cli_entry.py
  │       └── Method: .spec file
  │
  ├── 5. Build Tauri Targets (tauri_builder.py)
  │   ├── Scaffold src-tauri/ (Cargo.toml, build.rs, main.rs, lib.rs, tauri.conf.json)
  │   ├── npm install + npm run build (frontend)
  │   └── cargo tauri build --no-bundle
  │
  ├── 6. Sign Executables (sign.py) [OPTIONAL]
  │   └── signtool.exe sign /sha1 /fd sha256 /tr http://timestamp.digicert.com
  │
  ├── 7. Pre-Installer Gate (build.py)
  │   └── Validate every EXE is a real PE before staging
  │
  ├── 8. Package (package.py)
  │   ├── Create release/ directory layout
  │   ├── ZIP each executable into versioned portable archive
  │   ├── Generate SHA-256 checksums (checksums.txt)
  │   ├── Generate manifest.json (machine-readable)
  │   └── Generate top-level release/manifest.json
  │
  ├── 9. Generate Installers + Reports (release.py)
  │   ├── Write per-app .iss (Inno Setup) scripts
  │   ├── Write per-app .nsi (NSIS) scripts
  │   ├── Compile Inno Setup scripts (if ISCC available)
  │   ├── Write RELEASE_NOTES.md (changelog excerpt + artifact table)
  │   └── Write build-report.md (tooling, artifacts, checksums, warnings, errors)
  │
  ├── 10. Build AIClusterSetup.exe (setup_builder.py)
  │   ├── Stage Python 3.12 installer (downloaded)
  │   ├── Stage VC++ redist (downloaded)
  │   ├── Copy release/ binaries to payload
  │   ├── Compile setup.iss with ISCC
  │   └── Publish to dist/ and artifacts/
  │
  ├── 11. Final Verification (verify.py)
  │   └── Check all artifacts present and non-empty
  │
  └── 12. Release Verification (verification/ package)
      ├── (1) Build presence & exit code
      ├── (2) Executable PE validation (6 EXEs)
      ├── (3) Release folder layout (10 subdirs)
      ├── (4) Config file verification
      ├── (5) Python runtime check
      ├── (6) Frontend bundle + Tauri smoke tests
      ├── (7) Checksum regeneration + comparison
      ├── (8) Installer verification
      ├── (9) Backend launch + health (live HTTP)
      └── (10) API endpoint probes
```

---

## Release Directory Layout

```
release/
├── master/          → AIClusterMaster.exe
├── worker/          → AIClusterWorker.exe
├── cli/             → aicluster.exe
├── master-control/  → MasterControlCenter.exe
├── worker-control/  → WorkerControlCenter.exe
├── studio/          → AIClusterStudio.exe
├── checksums/       → checksums.txt, manifest.json
├── installer/       → *.iss, *.nsi
├── zip/             → *-portable.zip
└── reports/         → build-report.md, verification-report.md, RELEASE_SUMMARY.md
```

---

## Version Management (version.py)

```
Resolution order:
  1. AICLUSTER_BUILD_VERSION env var
  2. VERSION file at repo root
  3. CHANGELOG.md first heading
  4. Default: 1.2.2

Windows VSVersionInfo:
  - FileVersion: <major>.<minor>.<patch>.0
  - ProductVersion: <major>.<minor>.<patch>.0
  - CompanyName: AICluster
  - LegalCopyright: Copyright (c) 2026 AICluster
  - FileDescription: per-target (AICluster Master, Worker, CLI, etc.)
```

---

## Installer (AIClusterSetup.exe)

**Technology**: Inno Setup 6 with Pascal Script (595 lines)
**Source**: `build/setup/setup.iss`

### Wizard Pages:
1. **Welcome** — License, intro
2. **Components** — Select: Full / Compact / Custom
   - Master Server (required)
   - Worker Service, Web Dashboard, MCC, WCC, Studio, CLI (optional)
3. **Preflight** — Scan for Python 3.12+, VC++ Redist
4. **Firewall** — Add Windows Firewall rules for master port 8000
5. **Install** — Copy files, create shortcuts
6. **Verify** — Run post-install verification
7. **Finished** — Launch options

### Components (7):
| Component | Default | Type |
|-----------|---------|------|
| Master Server | Yes | Required |
| Worker Service | No | Optional |
| Web Dashboard | Yes | Optional |
| Master Control Center | Yes | Optional |
| Worker Control Center | No | Optional |
| AICluster Studio | No | Optional |
| CLI Tools | No | Optional |

---

## Key Design Principles

1. **No mock binaries** — Every produced EXE is a real PyInstaller or Tauri build
2. **Regenerated every build** — Specs, manifests, configs, installer scripts all generated
3. **PE validation gates** — Installer pipeline aborts if any EXE is not a valid Windows PE
4. **Opt-in signing** — Authenticode only runs when cert + signtool are configured
5. **Additive verification** — Verification package never modifies artifacts, only reads
6. **Content-addressed** — All outputs SHA-256 hashed in `checksums/`
7. **Version chain** — Single version source propagates through all artifacts

---

## CLI Flags (build.py)

```
--skip-verify       Skip environment verification
--skip-clean        Skip cleanup
--skip-frontend     Skip frontend builds
--skip-pyinstaller  Skip PyInstaller builds
--skip-tauri        Skip Tauri builds
--skip-sign         Skip code signing
--skip-package      Skip packaging
--skip-installer    Skip installer generation
--skip-setup        Skip AIClusterSetup.exe
--skip-final-verify Skip final verification
--skip-release      Skip release verification
--clean             Clean before building
--verify-only       Only run verification
```

## Toolchain Requirements

| Tool | Minimum | Optional |
|------|---------|----------|
| Python | 3.12 | — |
| Node.js | 18 | — |
| npm | — | — |
| Rust | 1.70 | — |
| Cargo | 1.70 | — |
| rustc | 1.70 | — |
| Tauri CLI | 2.0 | — |
| PyInstaller | — | Yes |
| Inno Setup 6 | — | Yes |
| 7-Zip | — | Yes |
| signtool | — | Yes |
