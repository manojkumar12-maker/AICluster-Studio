# AICluster Build System

A single-command, production-grade packaging pipeline for the entire
AICluster platform. Generates every Windows executable, installer
script, portable ZIP, checksum file, and release manifest.

> **Never modifies application source.** The build system only reads
> from `backend/`, `worker/`, the control centers, and `studio/`. The
> only files it writes are build artifacts in `dist/`, `release/`,
> `artifacts/`, `temp/`, `logs/`, and `checksums/`.

---

## Quick start

From the repository root:

```bat
build\build-all.bat
```

or, equivalently:

```bash
python -m build.build
```

That's it. No manual steps, no missing dependencies â€” the orchestrator
detects the toolchain, builds every frontend and backend, packages
each app, generates installer scripts, and produces a build report.

---

## What it builds

| App                       | Output exe                  | Packager     |
|---------------------------|-----------------------------|--------------|
| Master Server             | `AIClusterRuntime.exe --mode master`       | PyInstaller  |
| Worker Service            | `AIClusterRuntime.exe --mode worker`       | PyInstaller  |
| Master Control Center     | `MasterControlCenter.exe`   | Tauri v2     |
| Worker Control Center     | `WorkerControlCenter.exe`   | Tauri v2     |
| AICluster Studio          | `AIClusterStudio.exe`       | Tauri v2     |
| CLI                       | `aicluster.exe`             | PyInstaller  |
| AIClusterSetup (wizard)   | `AIClusterSetup.exe`        | Inno Setup 6 |

Each artifact is placed under `release/<app>/` and a portable ZIP is
written to `release/zip/`.

---

## Directory layout

```
build/
â”œâ”€â”€ build.py             master orchestrator
â”œâ”€â”€ build-all.bat        Windows entry point
â”œâ”€â”€ clean.py             wipe build artifacts
â”œâ”€â”€ verify.py            environment + artifact verification
â”œâ”€â”€ checksum.py          SHA-256 / MD5 / SHA-1 digests
â”œâ”€â”€ sign.py              Authenticode signing (opt-in)
â”œâ”€â”€ package.py           ZIP + manifest + checksums
â”œâ”€â”€ release.py           Inno Setup, NSIS, build report, release notes
â”œâ”€â”€ config.py            target definitions and paths
â”œâ”€â”€ version.py           version resolution + Windows version info
â”œâ”€â”€ toolchain.py         tool detection (Python, Node, Rust, â€¦)
â”œâ”€â”€ pyinstaller_builder.py
â”œâ”€â”€ tauri_builder.py
â”œâ”€â”€ frontend.py
â”œâ”€â”€ modules/
â”‚   â”œâ”€â”€ cli_entry.py     bundled into aicluster.exe
â”‚   â””â”€â”€ make_default_icon.py
â””â”€â”€ README.md            this file

release/
â”œâ”€â”€ master/              AIClusterRuntime.exe --mode master
â”œâ”€â”€ worker/              AIClusterRuntime.exe --mode worker
â”œâ”€â”€ master-control/      MasterControlCenter.exe
â”œâ”€â”€ worker-control/      WorkerControlCenter.exe
â”œâ”€â”€ studio/              AIClusterStudio.exe
â”œâ”€â”€ cli/                 aicluster.exe
â”œâ”€â”€ checksums/           checksums.txt + manifest.json
â”œâ”€â”€ installer/           per-app installer.iss / installer.nsi
â”œâ”€â”€ zip/                 portable ZIPs
â”œâ”€â”€ reports/             build-report.md
â””â”€â”€ manifest.json        top-level release manifest
```

---

## CLI flags

`build.py` (and `build-all.bat`) accept the following flags:

| Flag                  | Description |
|-----------------------|-------------|
| `--clean`             | Wipe `release/`, `dist/`, `artifacts/`, `temp/`, `checksums/` before building. |
| `--skip-verify`       | Skip the environment check (not recommended). |
| `--verify-only`       | Only run the environment check and exit. |
| `--skip-frontend`     | Skip building the web frontends. |
| `--skip-pyinstaller`  | Skip the three Python targets. |
| `--skip-tauri`        | Skip the three Tauri desktop apps. |
| `--skip-package`      | Skip ZIP, checksums, and manifest generation. |
| `--skip-release`      | Skip installer scripts, build report, and release notes. |
| `--skip-installer`    | Generate installer scripts but do not compile them. |
| `--skip-zip`          | Do not produce portable ZIPs. |
| `--skip-setup`        | Skip `AIClusterSetup.exe` (the single-file wizard installer). |
| `--skip-release-verify` | Skip the post-build release verification stage. |
| `--sign`              | Enable Authenticode signing (requires `AICLUSTER_CERT_PATH`). |

Examples:

```bash
python -m build.build --clean                 # full clean build
python -m build.build --skip-tauri            # Python apps only
python -m build.build --verify-only           # toolchain check
python -m build.build --sign                  # sign and package
```

---

## Environment variables

| Variable                          | Purpose |
|-----------------------------------|---------|
| `AICLUSTER_BUILD_VERSION`         | Override the product version. |
| `AICLUSTER_BUILD_COMPANY`         | Override the company name. |
| `AICLUSTER_BUILD_PRODUCT_NAME`    | Override the product name. |
| `AICLUSTER_BUILD_DESCRIPTION`     | Override the description. |
| `AICLUSTER_BUILD_COPYRIGHT`       | Override the copyright string. |
| `AICLUSTER_BUILD_SKIP_TAURI`      | `1`/`true` to skip Tauri. |
| `AICLUSTER_BUILD_SKIP_INSTALLER`  | `1`/`true` to skip installer compilation. |
| `AICLUSTER_BUILD_SKIP_SIGN`       | `1`/`true` to disable signing. |
| `AICLUSTER_SIGNTOOL_PATH`         | Path to `signtool.exe`. |
| `AICLUSTER_CERT_PATH`             | Path to `.pfx` / `.p12` certificate. |
| `AICLUSTER_CERT_PASSWORD`         | Certificate password. |

---

## Versioning

`build/version.py` discovers the current version from the first source
that yields a valid SemVer triple, in this order:

1. `AICLUSTER_BUILD_VERSION` env var
2. `VERSION` file at the repository root
3. First `## vX.Y.Z` heading in `CHANGELOG.md`
4. The hard-coded default (`1.2.2`)

The resolved version is embedded into:

* the PyInstaller-generated Windows resource (`VSVersionInfo`)
* `tauri.conf.json` (Tauri apps)
* the release manifest
* every installer script
* the build report

---

## Installer scripts

Two flavours of installer source are produced for every app:

* **Inno Setup** (`release/installer/<app>/installer.iss`) â€” primary
  Windows installer. Compiled automatically if `ISCC.exe` is on
  `PATH` or in `C:\Program Files*\Inno Setup\`.
* **NSIS** (`release/installer/<app>/installer.nsi`) â€” alternative
  Windows installer. Compiled automatically if `makensis.exe` is
  available.

Both scripts include desktop + Start-Menu shortcuts, an uninstaller,
the version metadata, and the license file.

---

## Checksums

`release/checksums/` contains:

* `checksums.txt` â€” classic `sha256sum` format
* `manifest.json` â€” machine-readable digest manifest with file size,
  SHA-256, MD5, and SHA-1

The top-level `release/manifest.json` ties the per-app digests
together and references the checksum files.

---

## Build report

After every build, `release/reports/build-report.md` is written. It
includes:

* duration, version, company, copyright
* detected toolchain (name, version, path)
* per-app table (size, SHA-256)
* list of produced installer scripts
* signed artifacts (if any)
* warnings and errors

---

## Code signing

Signing is **opt-in** and only runs when `--sign` is passed *and*:

* `signtool.exe` is on `PATH` (or in the Windows SDK), **and**
* `AICLUSTER_CERT_PATH` points to an existing `.pfx`/`.p12`, **and**
* (optionally) `AICLUSTER_CERT_PASSWORD` is set.

Unsigned builds are perfectly valid â€” the build never fails just
because a certificate is missing.

---

## Required / optional toolchain

| Tool            | Required | Min version | Used for                |
|-----------------|----------|-------------|-------------------------|
| Python          | yes      | 3.12        | orchestrator, PyInstaller |
| Node.js         | yes      | 18          | frontends               |
| npm             | yes      | bundled     | frontends               |
| PyInstaller     | yes      | 6.x         | master / worker / CLI   |
| Rust            | no       | 1.70        | Tauri apps              |
| Tauri CLI       | no       | 2.0         | Tauri apps              |
| Inno Setup      | no       | 6           | installer compilation   |
| NSIS            | no       | 3           | installer compilation   |
| 7-Zip           | no       | â€”           | portable ZIPs (fallback) |
| signtool        | no       | â€”           | Authenticode signing    |

The orchestrator stops only on missing *required* tools.

---

## Reproducibility

* Every spec, manifest, config file, and installer script is
  regenerated on every build â€” there is no hand-edited state.
* Build outputs are content-addressed via SHA-256 in
  `release/checksums/manifest.json`.
* The build is fully driven by `build/config.py` â€” adding a new app
  is a single dataclass entry.

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | Build succeeded (warnings allowed). |
| 1    | Build failed (missing required tool, missing executable, etc.). |
| 2+  | Subprocess failure with the same code. |
