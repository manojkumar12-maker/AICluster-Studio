# Release Packaging Report

**AICluster v1.4 â€” Enterprise Packaging & Native Windows Architecture**
**Date:** 2026-07-05

---

## 1. Distribution Philosophy

The release package must contain only files required to run AICluster. No tests, no developer scripts, no intermediate build artifacts, no editor configuration, no source code (except where required by the runtime).

**Target user experience:**
1. Download `AIClusterSetup-1.4.0.exe`
2. Run the installer
3. Launch AICluster Studio from Start Menu / Desktop
4. Choose role (Master / Worker / Standalone)
5. Dashboard opens â€” no further setup required

---

## 2. Target Distribution Layout

```
AICluster/                              [Installation root]
  AICluster Studio.exe                  [Primary entry point - users only see this]
  
  runtime/                              [Backend services - managed by Studio]
    AIClusterRuntime.exe --mode master                 [Master server - launched on demand]
    AIClusterRuntime.exe --mode worker                 [Worker agent - launched on demand]
    aicluster.exe                       [CLI tool - optional]
    runtime.json                        [Service manifest: paths, ports, versions]
    
  config/                               [Runtime configuration]
    default.yaml                        [Default settings]
    user.yaml                           [User overrides (created by wizard)]
    cluster.yaml                        [Cluster settings]
    models.yaml                         [Model provider settings]
    workers.yaml                        [Worker fleet settings]
    secrets.enc                         [Encrypted secrets (JWT key, etc.)]
    
  models/                               [LLM model storage]
    (downloaded model files)
    
  plugins/                              [User-installed plugins]
    (plugin packages)
    
  logs/                                 [Runtime logs]
    master.log
    worker.log
    studio.log
    
  data/                                 [Runtime databases]
    aicluster.db                        [SQLite database]
    secret.key                          [Auto-generated JWT secret]
    
  assets/                               [Static resources]
    icons/                              [Application icons]
    default.ico                         [Fallback icon]
    
  licenses/                             [Third-party licenses]
    MIT.txt
    Apache-2.0.txt
    NOTICE.txt                          [AICluster notice]
```

### 2.1 What End Users See

| Entry | Visibility | Notes |
|-------|-----------|-------|
| `AICluster Studio.exe` | **Visible** | Start Menu shortcut, Desktop shortcut |
| `runtime/` | Hidden | Managed by Studio launcher |
| `config/` | Visible (admin) | Configuration files |
| `models/` | Visible (admin) | Model storage |
| `plugins/` | Visible (admin) | Plugin directory |
| `logs/` | Hidden | Runtime logs for troubleshooting |
| `data/` | Hidden | Runtime databases |
| `assets/` | Hidden | Application resources |
| `licenses/` | Visible | Legal information |

---

## 3. Executable Build Pipeline

### 3.1 PyInstaller Targets

| Target | Entry Script | Output | GUI | Notes |
|--------|-------------|--------|-----|-------|
| Master Server | `runtime/master-entry.py` | `AIClusterRuntime.exe --mode master` | Windowed | No console window |
| Worker Agent | `runtime/worker-entry.py` | `AIClusterRuntime.exe --mode worker` | Windowed | No console window |
| CLI | `build/modules/cli_entry.py` | `aicluster.exe` | Console | CLI needs console |

### 3.2 Tauri Targets

| Target | Frontend Dir | Output | Notes |
|--------|-------------|--------|-------|
| AICluster Studio | `studio/` | `AICluster Studio.exe` | Primary UI |
| Master Control Center | `master-control-center/` | `MasterControlCenter.exe` | Legacy (merged into Studio) |
| Worker Control Center | `worker-control-center/` | `WorkerControlCenter.exe` | Legacy (merged into Studio) |

### 3.3 Build Configuration

```python
# build/config.py â€” Updated PyInstaller targets for v1.4

PyInstallerTarget(
    key="master",
    name="Master Server",
    entry=RUNTIME_DIR / "master-entry.py",
    output_name="AIClusterRuntime.exe --mode master",
    output_subdir="runtime",
    console=False,
    ...
)

PyInstallerTarget(
    key="worker",
    name="Worker Service",
    entry=RUNTIME_DIR / "worker-entry.py",
    output_name="AIClusterRuntime.exe --mode worker",
    output_subdir="runtime",
    console=False,
    ...
)

PyInstallerTarget(
    key="cli",
    name="AICluster CLI",
    entry=BUILD_DIR / "modules" / "cli_entry.py",
    output_name="aicluster.exe",
    output_subdir="runtime",
    console=True,
    ...
)
```

---

## 4. Release Packaging

### 4.1 Package Layout

```
release/
  v1.4.0/
    AICluster Studio.exe
    runtime/
      AIClusterRuntime.exe --mode master
      AIClusterRuntime.exe --mode worker
      aicluster.exe
      runtime.json
    config/
      default.yaml
    assets/
      icons/
    licenses/
    checksums/
      sha256sums.txt
      sha256sums.txt.asc          [GPG signature]
    reports/
      build-report.md
      verification-report.md
    AIClusterSetup-1.4.0.exe      [Inno Setup installer]
    AICluster-1.4.0-portable.zip  [Portable version]
```

### 4.2 Checksum Generation

```python
# build/checksum.py
import hashlib, json
from pathlib import Path

def generate_checksums(release_dir: Path) -> dict:
    sums = {}
    for f in sorted(release_dir.rglob("*")):
        if f.is_file() and f.suffix != ".asc":
            sums[str(f.relative_to(release_dir))] = hashlib.sha256(f.read_bytes()).hexdigest()
    (release_dir / "checksums" / "sha256sums.txt").write_text(
        "\n".join(f"{v}  {k}" for k, v in sums.items())
    )
    return sums
```

### 4.3 Code Signing

```python
# build/sign.py
def sign_file(path: Path, cfg: BuildConfig) -> SignResult:
    """Sign a PE executable with Authenticode certificate."""
    if cfg.skip_sign:
        return SignResult(file=path, signed=False)
    
    # signtool sign /fd SHA256 /a /f <cert> /p <password> <file>
    cmd = [
        cfg.signtool_path or "signtool",
        "sign", "/fd", "SHA256", "/a",
        "/f", str(cfg.certificate_path),
        "/p", cfg.certificate_password,
        "/t", "http://timestamp.digicert.com",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return SignResult(file=path, signed=result.returncode == 0)
```

---

## 5. Minimal Distribution Checklist

### 5.1 Files to Exclude

| Glob Pattern | Reason |
|-------------|--------|
| `**/*.pyc` | Bytecode â€” regenerated at runtime |
| `**/__pycache__/` | Python cache |
| `**/.pytest_cache/` | Test cache |
| `**/.ruff_cache/` | Linter cache |
| `**/.venv/` | Virtual environment |
| `**/node_modules/` | npm packages |
| `**/.next/` | Next.js build cache |
| `**/src-tauri/target/` | Rust build cache |
| `**/*.spec` | PyInstaller spec (regenerated) |
| `**/*_version.txt` | Build byproduct |
| `.git/` | Version control |
| `.github/` | CI/CD config (dev only) |
| `.gitignore` | Version control config |
| `scripts/*.ps1` | Developer scripts |
| `scripts/*.py` | Developer/test scripts |
| `backend/tests/` | Test suite (dev only) |
| `worker/tests/` | Test suite (dev only) |
| `tests/` | Integration tests |
| `docs/` | Documentation (distributed separately) |
| `build/` | Build system source (dev only) |
| `nul` | Stray artifact |
| `*.log` | Runtime logs |

### 5.2 Files to Include

| Path | Purpose |
|------|---------|
| `AICluster Studio.exe` | Primary application |
| `runtime/AIClusterRuntime.exe --mode master` | Master service |
| `runtime/AIClusterRuntime.exe --mode worker` | Worker service |
| `runtime/aicluster.exe` | CLI tool |
| `runtime/runtime.json` | Service manifest |
| `config/default.yaml` | Default configuration |
| `assets/icons/` | Application icons |
| `licenses/` | Third-party licenses |
| `models/.gitkeep` | Model directory placeholder |

---

## 6. Portable ZIP Packaging

A portable ZIP release must be provided for users who prefer not to use the installer.

```python
# build/package.py
def create_portable_zip(cfg: BuildConfig):
    import zipfile
    
    zip_path = RELEASE_DIR / f"AICluster-{cfg.version}-portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add all release files
        for f in (RELEASE_DIR / "v" + cfg.version).rglob("*"):
            if f.is_file():
                arcname = str(f.relative_to(RELEASE_DIR))
                zf.write(f, arcname)
    
    # Generate checksum
    sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (RELEASE_DIR / "checksums" / f"{zip_path.name}.sha256").write_text(sha256)
```

---

## 7. Installer Build Process

### 7.1 Inno Setup Script (Conceptual)

```iss
; AIClusterSetup.iss â€” Inno Setup script for AICluster v1.4

[Setup]
AppName=AICluster
AppVersion=1.4.0
AppPublisher=AICluster
AppPublisherURL=https://aicluster.local
DefaultDirName={commonpf}\AICluster
DefaultGroupName=AICluster
OutputDir=release\v1.4.0
OutputBaseFilename=AIClusterSetup-1.4.0
SetupIconFile=assets\icons\default.ico
Compression=lzma2/max
SolidCompression=yes
PrivilegesRequired=admin
DisableProgramGroupPage=yes
DisableDirPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "autostart"; Description: "Start AICluster Studio on &login"; GroupDescription: "Startup options:"
Name: "firewall"; Description: "Allow AICluster through &Windows Firewall"; GroupDescription: "Network:"

[Files]
Source: "release\v1.4.0\AICluster Studio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\v1.4.0\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs
Source: "release\v1.4.0\config\*"; DestDir: "{app}\config"; Flags: ignoreversion
Source: "release\v1.4.0\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs
Source: "release\v1.4.0\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion

[Dirs]
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\models"; Permissions: users-modify
Name: "{app}\plugins"; Permissions: users-modify

[Icons]
Name: "{group}\AICluster Studio"; Filename: "{app}\AICluster Studio.exe"
Name: "{group}\Uninstall AICluster"; Filename: "{uninstallexe}"
Name: "{commondesktop}\AICluster Studio"; Filename: "{app}\AICluster Studio.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AICluster Studio.exe"; Description: "Launch AICluster Studio"; Flags: postinstall nowait skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
    if CurStep = ssPostInstall then
    begin
        // Configure Windows Firewall if selected
        if WizardIsTaskSelected('firewall') then
        begin
            Exec('netsh', 'advfirewall firewall add rule name="AICluster Master" dir=in action=allow program="' + ExpandConstant('{app}') + '\runtime\AIClusterRuntime.exe --mode master"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
            Exec('netsh', 'advfirewall firewall add rule name="AICluster Worker" dir=in action=allow program="' + ExpandConstant('{app}') + '\runtime\AIClusterRuntime.exe --mode worker"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        end;
    end;
end;
```

### 7.2 Installer Prerequisites

| Prerequisite | Check | Install |
|-------------|-------|---------|
| Windows 10 22H2+ | OS version check | Built into installer |
| VC++ Redistributable | Registry check | Included in installer |
| .NET Framework 4.8+ | Registry check | Windows Update |
| Python 3.12+ | Not required | Bundled in EXEs |

---

## 8. Release Verification

```powershell
# Verify release integrity
$errors = @()

# 1. All required files exist
$required = @(
    "AICluster Studio.exe",
    "runtime/AIClusterRuntime.exe --mode master",
    "runtime/AIClusterRuntime.exe --mode worker",
    "runtime/aicluster.exe",
    "runtime/runtime.json",
    "config/default.yaml",
    "licenses/NOTICE.txt",
    "checksums/sha256sums.txt"
)

foreach ($file in $required) {
    if (-not (Test-Path "release/v1.4.0/$file")) {
        $errors += "Missing: $file"
    }
}

# 2. Executables are valid PE files
foreach ($exe in Get-ChildItem "release/v1.4.0" -Filter "*.exe" -Recurse) {
    $bytes = [System.IO.File]::ReadAllBytes($exe.FullName)
    if ($bytes[0] -ne 0x4D -or $bytes[1] -ne 0x5A) {
        $errors += "Invalid PE: $($exe.Name)"
    }
}

# 3. Checksums match
$checksums = Get-Content "release/v1.4.0/checksums/sha256sums.txt"
foreach ($line in $checksums) {
    $hash, $file = $line -split "  ", 2
    $actual = (Get-FileHash "release/v1.4.0/$file" -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $hash) {
        $errors += "Checksum mismatch: $file"
    }
}

if ($errors.Count -eq 0) {
    Write-Host "All verifications passed!" -ForegroundColor Green
} else {
    $errors | ForEach-Object { Write-Host "FAIL: $_" -ForegroundColor Red }
}
```

---

## 9. Success Criteria

- [ ] Release ZIP contains only production-required files
- [ ] No `.pyc`, `__pycache__`, `.venv`, `node_modules` in release
- [ ] All executables are valid PE32+ binaries
- [ ] SHA-256 checksums generated and verified
- [ ] Installer builds without warnings
- [ ] Installer runs silently (no console windows)
- [ ] Portable ZIP equals installer contents
- [ ] Release is < 500 MB compressed
- [ ] All 98 existing tests pass
- [ ] Build system produces reproducible outputs
