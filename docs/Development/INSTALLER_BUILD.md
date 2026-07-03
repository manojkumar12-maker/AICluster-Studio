# AIClusterSetup.exe — Build System

This module compiles `AIClusterSetup.exe`, the single-file wizard
installer that ships AICluster to end users. The installer is a
self-contained executable that walks the user through every step with
no terminal commands required.

## What the installer does

1. **Welcome page** — explains what will be installed.
2. **Components page** — Master / Worker / Studio / Python / VC++.
3. **Preflight page** — scans the system for Python 3.12+ and
   Microsoft Visual C++ 2015-2022 Redistributable. If anything is
   missing, the installer queues it for silent install.
4. **Firewall page** — lists every TCP port the cluster uses and lets
   the user opt in to registering Windows Firewall inbound rules.
5. **Install page** — copies the prebuilt binaries to
   `%ProgramFiles%\AICluster`, runs the Python and VC++ installers
   silently if needed, creates Start Menu + Desktop shortcuts, and
   creates the data directory at
   `%PUBLIC%\Documents\AICluster\`.
6. **Verify page** — smoke-tests the installation: every EXE present,
   configuration copied, data dir writable, runtimes available.
7. **Finished page** — summary + "Launch AICluster Master" checkbox.

The installer is fully reversible: the uninstaller removes the
binaries, drops the firewall rules, and (optionally) wipes the data
directory.

## Files

```
build/setup/
├── setup.iss           master Inno Setup script (Pascal Script logic)
├── assets/             installer icon
├── payload/            assembled installer payload (regenerated on demand)
│   ├── aicluster/      prebuilt binaries copied from release/
│   ├── python/         python-3.12.*-amd64.exe
│   ├── vcredist/       vc_redist.x64.exe
│   ├── config/         default configuration (copied from config/)
│   └── assets/         icons / manifest (copied from assets/)
├── README.md           this file
└── Output/             compiled installer (only after a successful build)
```

The Python module that drives the compile is
`build/setup_builder.py`. The structural validator is
`build/setup_validator.py`.

## Building

### Prerequisites

* **Inno Setup 6** (https://jrsoftware.org/isdownload.php). The build
  system auto-detects `ISCC.exe` on `PATH` or in the standard
  `C:\Program Files*\Inno Setup\` directories.
* **Internet access** (only on the first build, to download
  `python-3.12.x-amd64.exe` and `vc_redist.x64.exe`). After the first
  build, the payload is cached in `build/setup/payload/` and reused.

### Run

```bash
# Full build: stage payload + run ISCC
python -m build.setup_builder

# Stage the payload only (no compile)
python -m build.setup_builder --skip-compile

# Compile only (reuse staged payload)
python -m build.setup_builder --compile-only
```

The build system produces:

* `build/setup/Output/AIClusterSetup-<version>.exe` — the installer
* `dist/AIClusterSetup-<version>.exe` — copy of the same installer
* `artifacts/AIClusterSetup-<version>.exe` — archived copy

The same installer is also produced as a final stage of the master
build orchestrator (`python -m build.build`). To skip it, pass
`--skip-setup`.

### Validate without compiling

```bash
python -m build.setup_validator
```

The validator checks for:

* Every required section (`[Setup]`, `[Files]`, `[Code]`, ...)
* PascalScript brace balance
* Every `Source:` path resolves to a real file under `build/setup/`
* `AppId` is present and well-formed

It does not require Inno Setup to be installed.

## Customising

The script is templated with the build system's standard `#define`
values:

| Define               | Default                | Purpose |
|----------------------|------------------------|---------|
| `AppVersion`         | `VERSION` file         | The version baked into the installer metadata |
| `AppId`              | `com.aicluster.setup`  | Inno AppId used by the Windows uninstaller |
| `AppSourceDir`       | `payload\aicluster`    | Where to look for the prebuilt binaries |
| `BundlePython`       | `1`                    | Always include Python in the payload |
| `BundleVCRedist`     | `1`                    | Always include VC++ in the payload |
| `ConfigureFirewall`  | `1`                    | Register firewall rules by default |
| `LaunchMaster`       | `1`                    | Default value of the "Launch" checkbox |

Override any of them on the command line:

```bash
ISCC setup.iss /DAppVersion=2.0.0 /DAppId=com.example.aicluster
```

or via the Python builder:

```python
from build.setup_builder import build_setup
build_setup(compile_only=False)
```

## End-user experience

A user downloading `AIClusterSetup-1.2.1.exe` (≈ 80–120 MB) runs it
and sees a wizard that:

1. Greets them.
2. Lets them pick Full / Compact / Custom install.
3. Scans for Python and VC++ and lists what it will install.
4. Lists the TCP ports to be opened in the firewall.
5. Installs everything silently in the background.
6. Verifies the install.
7. Asks if they want to launch the Master server.

There is no terminal, no PowerShell window, no manual steps. The
uninstaller is registered in "Apps & Features" and removes everything
cleanly.
