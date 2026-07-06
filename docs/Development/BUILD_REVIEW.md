# AICluster â€” Build Pipeline Review

**Version:** 1.2.1  
**Last Updated:** 2026-07-03  
**Review Scope:** `build/` directory â€” full build, packaging, and release pipeline

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [build.py â€” Master Orchestrator](#2-buildpy--master-orchestrator)
3. [pyinstaller_builder.py â€” Python Binary Builder](#3-pyinstaller_builderpy--python-binary-builder)
4. [tauri_builder.py â€” Desktop App Builder](#4-tauri_builderpy--desktop-app-builder)
5. [setup_builder.py â€” Installer Builder](#5-setup_builderpy--installer-builder)
6. [package.py â€” Release Packaging](#6-packagepy--release-packaging)
7. [release.py â€” Installer Scripts & Reports](#7-releasepy--installer-scripts--reports)
8. [verify.py â€” Build Verification](#8-verifypy--build-verification)
9. [clean.py â€” Artifact Cleanup](#9-cleanpy--artifact-cleanup)
10. [Verification Pipeline](#10-verification-pipeline)
11. [Checksums & Integrity](#11-checksums--integrity)
12. [Installer Generation](#12-installer-generation)
13. [Build Reports](#13-build-reports)
14. [Component Scores Summary](#14-component-scores-summary)
15. [Strengths](#15-strengths)
16. [Weaknesses & Recommendations](#16-weaknesses--recommendations)

---

## 1. Pipeline Overview

The AICluster build system lives entirely in `build/` and is a Python-based production pipeline that produces all distribution artifacts. It is invoked via `python -m build.build` or `python build/build.py`.

### Pipeline Stages (In Order)

```
 1. Environment Verification  â”€â”€â–º  verify.py (Python, Node, Rust, Tauri, PyInstaller, Inno Setup, etc.)
 2. Clean Previous Outputs    â”€â”€â–º  clean.py (if --clean)
 3. Build Frontends           â”€â”€â–º  frontend.py (npm run build for all web UIs)
 4. Build PyInstaller Targets â”€â”€â–º  pyinstaller_builder.py (master, worker, CLI)
 5. Build Tauri Targets       â”€â”€â–º  tauri_builder.py (master-control, worker-control, studio)
 6. Sign Executables          â”€â”€â–º  sign.py (Authenticode â€” opt-in)
 7. Pre-Installer Gate        â”€â”€â–º  Verify every .exe is a real Windows PE binary
 8. Package Release           â”€â”€â–º  package.py (ZIPs, checksums, manifest)
 9. Build Installer           â”€â”€â–º  setup_builder.py (AIClusterSetup.exe via Inno Setup)
10. Generate Release Notes    â”€â”€â–º  release.py (build report, RELEASE_NOTES.md)
11. Final Verification        â”€â”€â–º  verify.py (artifact integrity + release verification suite)
12. Emit Build Report         â”€â”€â–º  Markdown report + exit code
```

### Build Targets

| Target | Type | Output | Size (approx) |
|--------|------|--------|---------------|
| Master Server | PyInstaller | `AIClusterRuntime.exe --mode master` | ~80 MB |
| Worker Service | PyInstaller | `AIClusterRuntime.exe --mode worker` | ~40 MB |
| CLI | PyInstaller | `aicluster.exe` | ~10 MB |
| Master Control Center | Tauri v2 | `MasterControlCenter.exe` | ~8 MB |
| Worker Control Center | Tauri v2 | `WorkerControlCenter.exe` | ~8 MB |
| AICluster Studio | Tauri v2 | `AIClusterStudio.exe` | ~12 MB |
| AICluster Setup | Inno Setup | `AIClusterSetup-<version>.exe` | ~500 MB |

### Key Design Decisions

- **No placeholder executables**: The pipeline has a hard PE gate â€” every `.exe` must be a real Windows PE or the build aborts. This prevents shipping broken binaries.
- **PyInstaller for Python apps**: Master, Worker, and CLI are self-contained EXEs. No Python runtime needed on target machines.
- **Tauri v2 for desktop apps**: Uses the system WebView. Each desktop app is ~8-12 MB (vs. Electron's ~150 MB).
- **Inno Setup for installer**: Single-file wizard installer bundles Python 3.12 runtime, VC++ redist, and all AICluster binaries.
- **Opt-in code signing**: Authenticode signing only if certificate and signtool are available. Never fails the build.
- **Async pipeline**: All build steps are sequential within a synchronous Python process. No parallelization.

---

## 2. build.py â€” Master Orchestrator

**File:** `build/build.py` (431 lines)  
**Role:** Entry point that orchestrates every build stage.  
**Score: 9/10**

### What It Does

`build.py` defines the `run()` function that walks through each stage sequentially, collecting errors and warnings into lists. At each stage:

1. Calls the responsible module (e.g., `pyinstaller_builder.build_all(cfg)`)
2. Checks the return value for errors
3. If errors exist and the stage is critical (binary builds), aborts immediately
4. Otherwise continues, collecting warnings

The `main()` function parses CLI arguments (`--clean`, `--skip-tauri`, `--verify-only`, etc.) and maps them to `BuildConfig` fields, then calls `run()`.

### CLI Arguments (17 flags)

```bash
python -m build.build --clean --skip-tauri --skip-installer --sign
```

All flags are supported: `--clean`, `--skip-verify`, `--verify-only`, `--skip-frontend`, `--skip-pyinstaller`, `--skip-tauri`, `--no-launch`, `--skip-package`, `--skip-release`, `--skip-installer`, `--skip-zip`, `--skip-setup`, `--skip-release-verify`, `--sign`. This provides fine-grained control for CI/CD and development builds.

### Strengths

- **Clean separation of concerns**: Each stage is its own module with a well-defined interface.
- **Hard gates at critical points**: The binary build (PyInstaller + Tauri) produces errors that abort before packaging. The pre-installer PE gate runs before setup_builder.
- **Comprehensive error/warning tracking**: Two lists (`errors`, `warnings`) accumulate across the entire build and are included in the final report.
- **CLI flag parity with config**: Every skip flag maps to `BuildConfig` fields. Environment variables (`AICLUSTER_BUILD_*`) also work, enabling CI/CD overrides.
- **`_verify_executables_gate()`** is a particularly strong design: it checks every required EXE is a real PE before building the installer, preventing a broken installer from being generated.
- **Version resolution** (`resolve_version()`) chains 4 sources: env var â†’ VERSION file â†’ CHANGELOG.md â†’ hard-coded default.

### Weaknesses

- **Sequential only**: No parallel stage execution. Building PyInstaller targets sequentially (master â†’ worker â†’ CLI) takes longer than necessary. These are independent.
- **No build cache**: Every full build recompiles everything. There is no incremental build support (e.g., skip Tauri if its frontend hasn't changed).
- **Error collection is append-only**: If a stage succeeds on retry (e.g., user fixes a tool path), previous errors remain in the list.
- **No build graph**: The `_step()` logging is linear; there is no DAG or dependency graph representing stage relationships.

### Suggested Improvements

1. Add `concurrent.futures.ThreadPoolExecutor` for independent stages (PyInstaller targets, Tauri targets).
2. Implement content-based caching: skip Tauri build if `frontend/dist` already exists and is newer than source.
3. Add `--retry` flag that clears error/warning lists before reattempting.

---

## 3. pyinstaller_builder.py â€” Python Binary Builder

**File:** `build/pyinstaller_builder.py` (402 lines)  
**Role:** Compiles Python applications into self-contained Windows executables.  
**Score: 9/10**

### What It Does

Generates `.spec` files and runs PyInstaller to produce three executables:

1. **AIClusterRuntime.exe --mode master** â€” Full FastAPI backend with all subsystems (AI, Workflow, Agents, Repository, Engineering, Audit, Plugins). Uses `--collect-all` for `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `aiosqlite`, `alembic`, `jose`, `passlib`, `bcrypt`, `httpx`, `anyio`, `starlette`, `websockets`, `python_multipart`, `sniffio`.
2. **AIClusterRuntime.exe --mode worker** â€” Worker agent with FastAPI health endpoint, job executor, and monitoring. Uses `--collect-all` for `uvicorn`, `psutil`, `httpx`.
3. **aicluster.exe** â€” CLI tool with `httpx` and `rich`.

### Key Design Decisions

- **Two build paths**: Complex packages (master, worker) use `--collect-all` CLI mode to pull in all submodules without listing them. Simpler packages (CLI) use a generated `.spec` file. This is explained in code comments and is the correct approach for PyInstaller 6.x.
- **No placeholder/mock EXEs**: The docstring explicitly states "there are no placeholder executables, no mock binaries, and no fallback."
- **Windows version info**: The `_write_version_info()` method generates proper `VSVersionInfo` blocks using PyInstaller's own classes, ensuring round-trip compatibility.
- **Hidden imports**: Each target has a curated list of `hidden_imports` and `EXTRA_COLLECTS` to catch dynamically imported modules.
- **Spec template**: The Python `SPEC_TEMPLATE` string uses f-string formatting to generate valid `.spec` files with correct paths.

### Output Discovery

The `_pyinstaller_outputs()` method checks four candidate paths for the produced EXE. This is needed because PyInstaller 6.x places outputs differently depending on CLI vs. spec mode:

```python
def _pyinstaller_outputs(target) -> List[Path]:
    candidates: List[Path] = []
    name = target.output_name.replace(".exe", "")
    candidates.append(target.entry.parent / "dist" / target.output_name)
    candidates.append(target.entry.parent / "dist" / target.entry.parent.name / target.output_name)
    candidates.append(target.entry.parent / "dist" / name / target.output_name)
    candidates.append(target.entry.parent / "dist" / name / f"{name}.exe")
    return candidates
```

### Strengths

- Clean distinction between the two build paths (CLI `--collect-all` vs. spec file).
- Comprehensive hidden imports list prevents runtime import errors.
- Version info generation is correct and thorough.
- No placeholder fallback â€” if PyInstaller fails or doesn't produce output, the build correctly raises `RuntimeError`.
- `_resolve_pyinstaller()` checks both PATH and `python -m PyInstaller`, handling edge cases.

### Weaknesses

- **No UPX compression**: `upx=False` is hard-coded in the EXE template. UPX could reduce EXE size by 30-50%. The comment says "UPX is intentionally disabled for stability" but there is no config flag to enable it.
- **`_publish` uses `shutil.copy2`**: For large EXEs (~80 MB for master), a copy is slow on HDDs. A hardlink or move would be faster (but copy is safer for retries).
- **`--collect-all` is aggressive**: Pulling in every sub-module of FastAPI, SQLAlchemy, etc. bloats the EXE. A more targeted approach could reduce size.
- **No UPX config**: UPX is a common optimization for PyInstaller. It should be configurable.

---

## 4. tauri_builder.py â€” Desktop App Builder

**File:** `build/tauri_builder.py` (389 lines)  
**Role:** Builds three Tauri v2 desktop applications.  
**Score: 8/10**

### What It Does

Scaffolds a complete Tauri v2 Rust project from templates, installs frontend dependencies, builds the frontend with Vite, and runs `cargo tauri build`.

### Scaffold Templates

The module generates 6 files per target:
- `Cargo.toml` â€” Rust project configuration with version
- `build.rs` â€” Standard Tauri build script
- `src/main.rs` â€” Application entry point
- `src/lib.rs` â€” Library with `tauri::Builder::default()`
- `src-tauri/capabilities/default.json` â€” Security capabilities
- `src-tauri/tauri.conf.json` â€” Window configuration, bundle settings, icons
- `.gitignore` â€” Standard Rust gitignore

### Key Design Decisions

- **Full scaffold, no stubs**: The build generates real Rust source code and compiles it. No placeholder binaries.
- **npm resolution**: The `_resolve_npm()` function handles Windows-specific npm invocation (`npm.cmd` through `cmd.exe`) to avoid the common "npm is not recognized" error after cache clears.
- **Cargo bin injection**: `_run()` appends `~/.cargo/bin` to the command path on Windows, handling rustup-style toolchains.
- **Icon handling**: `_ensure_icons()` copies required PNG sizes and ICO from the assets directory, with fallback to `default.ico`.
- **Minimum size check**: `_required_exe()` rejects executables under 1024 bytes as likely stubs.

### Strengths

- Generates correct `Cargo.toml` with version from the build system
- Handles the tricky Windows npm PATH issue
- Proper PE size validation
- Clean separation: `scaffold()` creates the project, `build_target()` compiles it

### Weaknesses

- **No Tauri bundle step**: The build uses `--no-bundle`, meaning the NSIS installer Tauri would normally produce is skipped. The NSIS generation is left to `release.py` instead. This is intentional (AICluster uses Inno Setup as primary installer), but worth noting.
- **Icons required**: If `default.ico` is missing, the build does not degrade gracefully (raises `RuntimeError`).
- **All Tauri targets build sequentially**: Each target runs `npm install`, `npm run build`, and `cargo tauri build` in sequence. For three targets, this takes 15-30 minutes.
- **No incremental build**: Even if the frontend hasn't changed, the full Rust build runs.

---

## 5. setup_builder.py â€” Installer Builder

**File:** `build/setup_builder.py` (401 lines)  
**Role:** Produces `AIClusterSetup-<version>.exe` â€” the single-file Windows installer.  
**Score: 8/10`

### What It Does

1. Stages the payload: Python 3.12 embedded installer, VC++ redist, AICluster binaries, configuration, and assets
2. Downloads missing payloads from official URLs
3. Verifies every staged executable is a real Windows PE
4. Renders `setup.iss` with current version and paths
5. Compiles with Inno Setup's `ISCC.exe`
6. Publishes to `dist/` and `artifacts/`

### Payload Download

```python
PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
VCREDIST_DOWNLOAD_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
```

Downloads cache to `build/setup/payload/` and skip re-download if the file exists and is > 1 KB. This is correct and efficient.

### ISCC Discovery

```python
def _iscc_path() -> Optional[Path]:
    # Checks PATH, then ProgramFiles(x86)/Inno Setup 6, ProgramFiles(x86)/Inno Setup,
    # ProgramFiles/Inno Setup 6, ProgramFiles/Inno Setup
```

This is thorough and handles the common install locations on Windows.

### Strengths

- **PE verification gate**: Every AICluster EXE is validated as a real PE before being bundled into the installer. This is a critical safety check.
- **Download with caching**: Payloads are downloaded once and cached. Size validation prevents stale stub files.
- **Dual publish**: Output goes to both `dist/` and `artifacts/` for distribution flexibility.
- **Inno Setup version check**: Minimum ISCC version (6.4) is verified.

### Weaknesses

- **Download from internet**: The build downloads Python and VC++ redist during the build. In air-gapped environments, this will fail. There is no `--offline` flag.
- **Hard-coded Python version**: `python-3.12.7-amd64.exe` is hard-coded. When Python releases a new minor version, this URL becomes stale.
- **No installer signing**: The produced installer is not Authenticode-signed (unless external tooling is used).
- **`_stage_python()` only checks for `python-3.12*-amd64.exe`**: The glob pattern is helpful for version flexibility but may pick up stale cached versions.
- **Launcher instructions are hard-coded strings**: The `LAUNCH_INSTRUCTIONS.md` is generated as a raw string in Python rather than as a template file.

---

## 6. package.py â€” Release Packaging

**File:** `build/package.py` (188 lines)  
**Role:** Generates checksums, manifests, and portable ZIPs for the release.  
**Score: 9/10`

### What It Produces

1. `release/checksums/checksums.txt` â€” Classic `sha256sum`-style file (one hash per line)
2. `release/checksums/manifest.json` â€” Machine-readable JSON manifest with SHA-256, MD5, SHA-1 per file
3. `release/zip/<app>_<version>.zip` â€” Per-app portable ZIP archives
4. `release/manifest.json` â€” Top-level release manifest with version, build date, app info

### Key Design Decisions

- **Three hash algorithms**: SHA-256 (primary), MD5 (backward compatibility), SHA-1 (legacy support). This is more than most projects provide.
- **Per-app ZIPs**: Each app is packaged separately, enabling selective downloads.
- **Top-level manifest**: Includes git tag, build date, company, copyright â€” enabling automated release tooling.
- **Missing target detection**: If any release subdirectory is missing, the build aborts with a clear error message. No silent failures.

### FileDigest Data Class

```python
@dataclass
class FileDigest:
    path: Path
    size: int
    sha256: str
    md5: str
    sha1: str
```

This is used throughout the packaging pipeline and serialized to JSON.

### Strengths

- Comprehensive checksum generation (3 algorithms).
- Per-app ZIPs are useful for selective deployment.
- Top-level manifest is CI/CD-friendly.
- Clear error messages for missing targets.
- Configurable ZIP creation (`skip_zip` flag).

### Weaknesses

- **ZIP compression is not configurable**: Uses `ZIP_DEFLATED` (standard deflate). No option for LZMA or store-only.
- **No parallel ZIP creation**: Multiple ZIPs are created sequentially.
- **Manifest `path` fields are filesystem paths**: When deploying to different machines, these paths will be incorrect. Should use relative paths within the release.
- **No GPG signatures**: Only checksums, no detached cryptographic signatures.

---

## 7. release.py â€” Installer Scripts & Reports

**File:** `build/release.py` (469 lines)  
**Role:** Generates Inno Setup and NSIS installer scripts, build reports, and release notes.  
**Score: 8/10`

### What It Does

1. Generates `installer.iss` (Inno Setup) and `installer.nsi` (NSIS) per app target
2. Attempts to compile them with ISCC/makensis if available
3. Writes `RELEASE_NOTES.md` from CHANGELOG excerpt
4. Writes a comprehensive Markdown build report

### Installer Script Templates

Two templates are provided:
- `INNO_SETUP_TEMPLATE` â€” Modern wizard-style with desktop icon, Start Menu, license file, LZMA compression, per-user installation, x64 support.
- `NSIS_TEMPLATE` â€” Minimal NSIS script with MUI2, same features.

### Build Report Format

The report includes:
- Version, build date, duration, company
- Tooling table (name, version, path)
- Artifact table (app, output, size, SHA-256)
- Checksums section (links to checksum files)
- Installers section (paths to generated scripts/binaries)
- Signed artifacts list
- Warnings and errors

### Strengths

- Dual installer support (Inno Setup + NSIS) provides flexibility.
- Build report is comprehensive and machine-readable (Markdown).
- Tooling table includes version and path for debugging.
- Changelog excerpt extraction for release notes.
- Graceful handling when compilers are not available (skips with log message).

### Weaknesses

- **NSIS template is minimal**: Lacks uninstaller logic, language support, and component selection of the Inno Setup template.
- **No installer verification**: After compiling, there's no smoke test that the installer actually works.
- **Inno Setup `PrivilegesRequired=lowest`**: This requires per-user installation, which may not be appropriate for enterprise deployment.
- **Build report path is hard-coded** to `RELEASE_LAYOUT["reports"] / "build-report.md"`.

---

## 8. verify.py â€” Build Verification

**File:** `build/verify.py` (257 lines)  
**Role:** Verifies the build environment and produced artifacts.  
**Score: 9/10`

### What It Does

Two main entry points:

1. **`verify_environment(cfg)`**: Checks every required and optional tool using `toolchain.gather_all()`. Missing required tools = errors. Missing optional tools = warnings.

2. **`verify_artifacts(cfg)`**: After a build, validates that the expected `.exe` files exist, are non-empty, and (on Windows) can be launched.

### Tool Checking

The `toolchain` module (called by `verify_environment`) checks:
- **Required**: Python, PyInstaller, Node.js, npm
- **Optional**: Rust, Cargo, Tauri CLI, Inno Setup (ISCC), 7-Zip, signtool

### Artifact Verification

```python
def _try_launch(exe: Path, timeout: float = 4.0) -> Optional[str]:
    # Spawn the EXE, wait briefly, kill it
    # If it stays alive â†’ "launches"
    # If it exits with error â†’ report error
```

This is a pragmatic approach that catches obviously broken executables without requiring complex launch-testing infrastructure.

### Strengths

- Thorough tool checking with version minimums.
- Structured `VerifyReport` dataclass with errors, warnings, tools, and artifacts.
- `_try_launch()` provides real execution validation beyond static analysis.
- Clean separation: `verify_environment()` for pre-build, `verify_artifacts()` for post-build.
- JSON output mode (`--json`) for CI/CD integration.

### Weaknesses

- **`_try_launch()` only tests if the EXE starts, not if it functions**: An EXE that crashes after accepting a network connection would still pass.
- **No performance verification**: No checks that the built EXE meets any performance baseline.
- **Artifact verification doesn't cross-reference checksums**: It checks existence and size but doesn't verify that checksums match.

---

## 9. clean.py â€” Artifact Cleanup

**File:** `build/clean.py` (120 lines)  
**Role:** Removes transient build artifacts.  
**Score: 8/10`

### What It Does

- Removes build output directories: `temp/`, `dist/`, `artifacts/`, `checksums/`
- With `--all`: also removes `release/` and all release subdirectories
- With `--pyc`: removes `__pycache__` folders and `.pyc` files
- With `--logs`: removes `logs/` directory
- Always removes per-target PyInstaller `.spec` files, `build/`, and `__pycache__` directories

### Strengths

- Safe: `shutil.rmtree(path, ignore_errors=True)` prevents crashes on permission issues.
- Targeted: Always cleans per-target build artifacts even without `--all`.
- Helpful logging: "removing X", "clean complete".

### Weaknesses

- **No dry-run mode**: No way to see what would be deleted without deleting.
- **Windows file locking**: `shutil.rmtree` may fail on Windows if files are locked by antivirus. The `ignore_errors=True` mitigates this but could leave partial state.

---

## 10. Verification Pipeline

The build has a multi-stage verification system:

### Stage 1: Pre-Build Environment Check

`verify.verify_environment()` at the start of `build.py` checks all required and optional tools are present. If required tools are missing, the build aborts immediately.

### Stage 2: Pre-Installer PE Gate

`build.py` calls `_verify_executables_gate()` before packaging. Every required executable is checked:
1. File exists
2. File size > 1024 bytes
3. File starts with `MZ` (PE header)
4. PE signature (`PE\x00\x00`) is present at the correct offset

Any FAIL causes the build to abort before the installer is built. This is a hard gate.

### Stage 3: Post-Build Artifact Verification

`verify.verify_artifacts()` checks every PyInstaller and Tauri target for existence, non-emptiness, and (on Windows) can launch the EXE.

### Stage 4: Release Verification

The `build/verification/` package (separate from `verify.py`) runs after the build completes. It includes 10+ verification modules:

| Module | Checks |
|--------|--------|
| `verify_build.py` | Build artifact integrity |
| `verify_backend.py` | Backend health check |
| `verify_frontend.py` | Frontend build output |
| `verify_api.py` | API endpoint responses |
| `verify_executables.py` | PE binary validation |
| `verify_installer.py` | Installer smoke test |
| `verify_checksums.py` | Checksum file validation |
| `verify_artifacts.py` | Artifact integrity |
| `verify_config.py` | Configuration validation |
| `verify_report.py` | Report generation |

The orchestrator in `verification/verify.py` runs all checks and produces a consolidated report.

---

## 11. Checksums & Integrity

### Checksum Generation

`checksum.py` provides three hash functions via `hashlib`:

| Algorithm | Usage |
|-----------|-------|
| SHA-256 | Primary checksum. Used in `checksums.txt` and as the main ID in manifests. |
| MD5 | Legacy compatibility. Included for users with MD5-based tooling. |
| SHA-1 | Extra verification. |

### Checksum Files

**`release/checksums/checksums.txt`:**
```
a1b2c3d4...  AIClusterRuntime.exe --mode master
e5f6g7h8...  AIClusterRuntime.exe --mode worker
```

**`release/checksums/manifest.json`:**
```json
[
    {"path": "...", "size": 12345, "sha256": "...", "md5": "...", "sha1": "..."}
]
```

**`release/manifest.json`:**
```json
{
    "product": "AICluster",
    "version": "1.2.1",
    "build_date": "2026-07-03 12:00:00",
    "apps": { ... },
    "checksums": { "txt": "...", "json": "..." }
}
```

### Security Notes

- Checksums provide integrity verification but not authenticity. Users should verify checksums over a trusted channel.
- No GPG signing of manifest files. Adding detached GPG signatures would enable authenticity verification.
- SHA-256 is the recommended primary hash. MD5 and SHA-1 are provided for legacy compatibility.

---

## 12. Installer Generation

### Inno Setup Installer (`AIClusterSetup.exe`)

The primary installer:
- **Technology**: Inno Setup 6 (ISCC.exe compiler)
- **Size**: ~500 MB (includes Python 3.12 runtime, VC++ redist, all AICluster binaries)
- **Features**:
  - Wizard-style installation (modern UI)
  - Component selection (install Master, Worker, or both)
  - Desktop shortcut, Start Menu shortcut
  - Auto-launch Master after installation
  - Firewall configuration
  - LZMA compression
  - Per-user installation (no admin required)

### NSIS Installer (Fallback)

Generated but not compiled by default. Simpler script with MUI2 interface, desktop shortcut, Start Menu folder.

### Installer Flow

```
setup.iss template
    â†’ _stage_config() copies config/ and assets/
    â†’ _stage_python() downloads Python 3.12 installer
    â†’ _stage_vcredist() downloads VC++ redist
    â†’ _stage_aicluster() verifies PE + copies release/ â†’ payload/aicluster/
    â†’ _iscc_compile() renders setup.iss with version defines
    â†’ ISCC.exe compiles â†’ AIClusterSetup-<version>.exe
    â†’ _publish_output() copies to dist/ and artifacts/
```

---

## 13. Build Reports

### Build Report (`release/reports/build-report.md`)

Generated by `release.py:write_build_report()`. Contains:
- Version, build date, duration
- Tooling table
- Per-app artifact sizes and SHA-256
- Checksums section
- Installer paths
- Signed artifacts
- Warnings and errors

### Release Notes (`release/RELEASE_NOTES.md`)

Generated by `release.py:write_release_notes()`. Contains:
- Version heading
- Changelog excerpt (parsed from `CHANGELOG.md`)
- Artifact listing with sizes and truncated SHA-256

### Verification Report (`release/reports/verification-report.md`)

Generated by `verification/verify_report.py`. Contains results of all 10+ verification checks.

---

## 14. Component Scores Summary

| Component | Score | Rationale |
|-----------|-------|-----------|
| `build.py` (Orchestrator) | 9/10 | Clean stages, hard gates, comprehensive flags. Lacks parallel execution. |
| `pyinstaller_builder.py` | 9/10 | Correct spec gen, proper version info, no placeholders. No UPX, aggressive collect-all. |
| `tauri_builder.py` | 8/10 | Full scaffold, proper npm handling. Sequential builds, no bundling. |
| `setup_builder.py` | 8/10 | PE gate, download caching, dual publish. Internet-dependent, hard-coded Python version. |
| `package.py` | 9/10 | Triple-hash checksums, per-app ZIPs, top-level manifest. No parallel ZIP, no GPG. |
| `release.py` | 8/10 | Dual installer scripts, comprehensive report. NSIS template is minimal, no installer smoke test. |
| `verify.py` | 9/10 | Thorough env checking, artifact validation, launch test. No cross-reference checksums. |
| `clean.py` | 8/10 | Safe rmtree, per-target cleaning. No dry-run. |
| `verification/` package | 8/10 | 10+ modules, structured output. Some modules are thin wrappers. |
| `checksum.py` | 9/10 | Clean API, three algorithms, streaming hash (1 MB chunks). |
| `sign.py` | 7/10 | Clean API, proper signtool invocation. Opt-in-only, env var config. |
| `config.py` | 9/10 | Well-structured target definitions, env overrides, frozen dataclasses. |
| `version.py` | 9/10 | Correct version resolution chain, Windows version info generation. |
| `frontend.py` | 7/10 | (Not reviewed in depth) Appears to handle npm build orchestration. |
| **Overall Build System** | **8.4/10** | Professional-grade build pipeline with strong verification gates. |

---

## 15. Strengths

1. **No placeholder executables**: The most important design decision. Every EXE is real, verified, and validated at multiple stages.
2. **Multi-gate verification**: Environment â†’ build â†’ PE gate â†’ packaging â†’ verification â†’ release verification. Six layers of checks.
3. **Comprehensive CLI flags**: 17 flags for fine-grained control of the pipeline.
4. **Structured reporting**: Build reports, verification reports, and release notes are all generated automatically.
5. **Dual installer support**: Both Inno Setup and NSIS scripts are generated.
6. **Triple-hash checksums**: SHA-256, MD5, and SHA-1 for maximum compatibility.
7. **Windows-aware design**: Proper handling of npm.cmd, Rustup paths, PE validation, VSVersionInfo.
8. **Code signing support**: Authenticode integration with DigiCert timestamping.
9. **Clean error propagation**: Errors and warnings are collected and reported at every stage.

---

## 16. Weaknesses & Recommendations

| Issue | Impact | Recommendation |
|-------|--------|---------------|
| Sequential build stages | Build time 2-3x longer than necessary | Use `ThreadPoolExecutor` for independent stages (PyInstaller targets, Tauri targets) |
| No incremental caching | Full rebuild every time | Implement content-addressable cache (hash source inputs, skip if unchanged) |
| No UPX compression | EXEs 30-50% larger than necessary | Add `--upx` flag, make `upx` configurable in `BuildConfig` |
| Internet-dependent installer build | Fails in air-gapped environments | Add `--offline` flag with pre-staged payload paths |
| NSIS template is minimal | NSIS users get a degraded experience | Add full NSIS template with uninstaller, languages, component selection |
| No GPG signing | Authenticity cannot be verified | Add `--gpg-sign` flag with GPG key configuration |
| No parallel ZIP creation | Packaging is sequential | Use `ThreadPoolExecutor` for ZIP creation |
| Hard-coded Python 3.12.7 in setup_builder | Will need updates | Read version from config, make download URL configurable |
| Build report path hard-coded | Cannot customize output location | Add `--report-dir` flag |
