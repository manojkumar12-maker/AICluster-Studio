"""AICluster Setup - master installer builder.

This module produces ``AIClusterSetup.exe`` from the contents of
``release/`` plus the bundled runtime payloads.

Pipeline
========

1.  Verify that the Inno Setup 6 compiler (``ISCC.exe``) is installed.
2.  Stage the payload under ``build/setup/payload/``:
        * python-3.12.x-amd64.exe  (downloaded from python.org if missing)
        * vc_redist.x64.exe        (downloaded from Microsoft if missing)
        * aicluster/               (copied from release/ - the prebuilt
                                    AIClusterMaster / Worker / Studio / etc.)
3.  Copy default configuration and assets from the repo into the payload.
4.  Render ``setup.iss`` with the current version + paths and pass the
    #define values to the Inno Setup compiler.
5.  Run ISCC, producing ``AIClusterSetup-<version>.exe``.

The output is placed in ``dist/`` (the build system's primary deliverable
folder) and copied to ``artifacts/`` for archival.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from .config import (
    ARTIFACTS_DIR,
    BUILD_DIR,
    DIST_DIR,
    REPO_ROOT,
    BuildConfig,
    is_windows,
)
from .logger import setup_logging, get_logger
from .version import resolve_version

log = get_logger("aicluster.build.setup")


SETUP_DIR = BUILD_DIR / "setup"
PAYLOAD_DIR = SETUP_DIR / "payload"
PAYLOAD_AICLUSTER = PAYLOAD_DIR / "aicluster"
PAYLOAD_PYTHON = PAYLOAD_DIR / "python"
PAYLOAD_VCREDIST = PAYLOAD_DIR / "vcredist"
PAYLOAD_CONFIG = PAYLOAD_DIR / "config"
PAYLOAD_ASSETS = PAYLOAD_DIR / "assets"

# Default URLs - the build system downloads these when missing.
PYTHON_DOWNLOAD_URL = (
    "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
)
VCREDIST_DOWNLOAD_URL = (
    "https://aka.ms/vs/17/release/vc_redist.x64.exe"
)

# Minimum Inno Setup version we depend on. ISCC 6.4+ ships all the
# features we use (`CreateCustomPage`, modern wizard, TArrayOfString,
# `Exec` with `ewNoWait`).
ISCC_MIN_VERSION = (6, 4)


def _iscc_path() -> Optional[Path]:
    """Return the ISCC.exe path, looking at common install locations."""
    on_path = shutil.which("iscc") or shutil.which("ISCC")
    if on_path:
        return Path(on_path)
    candidates: List[Path] = []
    for env in ("ProgramFiles(x86)", "ProgramFiles"):
        base = Path(os.environ.get(env, str(Path.home() / env)))
        if not base.exists():
            continue
        # Inno Setup 6.x installs to either "Inno Setup 6" or "Inno Setup".
        for sub in ("Inno Setup 6", "Inno Setup"):
            target = base / sub
            if target.exists():
                for cand in target.glob("ISCC.exe"):
                    candidates.append(cand)
    if candidates:
        return candidates[0]
    return None


def _run(cmd: List[str], cwd: Optional[Path] = None,
         timeout: int = 300) -> Tuple[int, str, str]:
    """Execute a command and return (returncode, stdout, stderr)."""
    log.info("$ %s", " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=cmd[0].lower().endswith(".cmd") if is_windows() else False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _download(url: str, dest: Path, *, force: bool = False) -> bool:
    """Stream a URL to ``dest``. Returns True on success."""
    if dest.exists() and not force and dest.stat().st_size > 1024:
        log.info("cached: %s", dest)
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("downloading %s -> %s", url, dest)
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=120) as response:
            dest.write_bytes(response.read())
        return dest.exists() and dest.stat().st_size > 1024
    except Exception as exc:  # network or SSL errors
        log.error("download failed: %s", exc)
        return False


def _stage_python() -> Optional[Path]:
    """Ensure the Python 3.12 embedded installer is in the payload."""
    PAYLOAD_PYTHON.mkdir(parents=True, exist_ok=True)
    # Skip the "use existing" shortcut if the cached file is just a stub
    # (size < 1 KiB). This prevents stale zero-byte or test-only files
    # from being bundled into the installer.
    for existing in sorted(PAYLOAD_PYTHON.glob("python-3.12*-amd64.exe")):
        if existing.stat().st_size > 1024:
            return existing
        else:
            log.warning("discarding stub python installer: %s", existing)
            existing.unlink()
    target = PAYLOAD_PYTHON / "python-3.12.7-amd64.exe"
    if _download(PYTHON_DOWNLOAD_URL, target):
        return target
    return None


def _stage_vcredist() -> Optional[Path]:
    """Ensure the VC++ 2015-2022 x64 redist installer is in the payload."""
    PAYLOAD_VCREDIST.mkdir(parents=True, exist_ok=True)
    target = PAYLOAD_VCREDIST / "vc_redist.x64.exe"
    if target.exists() and target.stat().st_size > 1024:
        return target
    if _download(VCREDIST_DOWNLOAD_URL, target):
        return target
    return None


def _is_real_pe(path: Path) -> bool:
    """Return True if ``path`` looks like a real Windows PE binary.

    Rejects placeholders, empty files, text blobs and any other
    non-executable content. The installer must never bundle a
    non-PE file as an AICluster EXE.
    """
    if not path.exists() or path.stat().st_size < 1024:
        return False
    try:
        with path.open("rb") as fh:
            if fh.read(2) != b"MZ":
                return False
            fh.seek(0x3C)
            pe_offset_bytes = fh.read(4)
            if len(pe_offset_bytes) != 4:
                return False
            import struct
            pe_offset = struct.unpack("<I", pe_offset_bytes)[0]
            fh.seek(pe_offset)
            sig = fh.read(4)
            return sig == b"PE\x00\x00"
    except OSError:
        return False


def _stage_aicluster() -> bool:
    """Copy the contents of ``release/`` into the setup payload.

    The setup expects subfolders ``master``, ``worker``, ``studio``,
    ``master-control``, ``worker-control``, ``cli`` directly under
    ``payload/aicluster/``. Every expected executable must exist
    and be a real Windows PE - the build aborts otherwise.
    """
    from .config import PYINSTALLER_TARGETS, TAURI_TARGETS

    PAYLOAD_AICLUSTER.mkdir(parents=True, exist_ok=True)
    release = REPO_ROOT / "release"

    # Verify every required executable is present and a real PE.
    required = []
    for t in list(PYINSTALLER_TARGETS) + list(TAURI_TARGETS):
        required.append((t.output_subdir, t.output_name))
    missing = []
    not_pe = []
    for sub, name in required:
        src = release / sub / name
        if not src.exists():
            missing.append(str(src.relative_to(release)))
            continue
        if not _is_real_pe(src):
            not_pe.append(str(src.relative_to(release)))
    if missing:
        raise RuntimeError(
            "the release/ tree is missing the following required "
            "executables:\n  " + "\n  ".join(missing) + "\n"
            "Run `python -m build.build` to produce them."
        )
    if not_pe:
        raise RuntimeError(
            "the following release executables are not real Windows PE "
            "binaries (placeholders or stubs were detected):\n  "
            + "\n  ".join(not_pe) + "\n"
            "Placeholder mode has been removed; rebuild the application."
        )

    for sub in ("master", "worker", "studio",
                "master-control", "worker-control", "cli"):
        src = release / sub
        dst = PAYLOAD_AICLUSTER / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        log.info("staged release/%s -> payload/aicluster/%s", sub, sub)
    return True


def _stage_config() -> None:
    """Stage the default configuration and assets into the payload."""
    if PAYLOAD_CONFIG.exists():
        shutil.rmtree(PAYLOAD_CONFIG)
    if PAYLOAD_ASSETS.exists():
        shutil.rmtree(PAYLOAD_ASSETS)
    PAYLOAD_CONFIG.mkdir(parents=True)
    PAYLOAD_ASSETS.mkdir(parents=True)
    cfg_src = REPO_ROOT / "config"
    assets_src = REPO_ROOT / "assets"
    if cfg_src.exists():
        for child in cfg_src.iterdir():
            target = PAYLOAD_CONFIG / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)
    if assets_src.exists():
        for child in assets_src.iterdir():
            target = PAYLOAD_ASSETS / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)

    # Drop a launch instructions file so users (and demo installers
    # built without real binaries) know how to start the cluster.
    instructions = (
        "# Launching AICluster\n\n"
        "After this installation completes, the AICluster binaries are "
        "in:\n\n"
        "  * Master Server     : `C:\\\\Program Files\\\\AICluster\\\\master\\\\AIClusterMaster.exe`\n"
        "  * Worker Service    : `C:\\\\Program Files\\\\AICluster\\\\worker\\\\AIClusterWorker.exe`\n"
        "  * Studio            : `C:\\\\Program Files\\\\AICluster\\\\studio\\\\AIClusterStudio.exe`\n"
        "  * Master CC         : `C:\\\\Program Files\\\\AICluster\\\\master-control\\\\MasterControlCenter.exe`\n"
        "  * Worker CC         : `C:\\\\Program Files\\\\AICluster\\\\worker-control\\\\WorkerControlCenter.exe`\n"
        "  * CLI               : `C:\\\\Program Files\\\\AICluster\\\\cli\\\\aicluster.exe`\n\n"
        "Start the cluster with the Master service:\n\n"
        "```cmd\n"
        "\"C:\\\\Program Files\\\\AICluster\\\\master\\\\AIClusterMaster.exe\"\n"
        "```\n\n"
        "Once it is running, open http://localhost:8000/docs for the API or\n"
        "use the Start Menu shortcuts the installer created.\n"
    )
    (PAYLOAD_AICLUSTER / ".." / "LAUNCH_INSTRUCTIONS.md").parent.mkdir(
        parents=True, exist_ok=True
    )
    (PAYLOAD_DIR / "LAUNCH_INSTRUCTIONS.md").write_text(
        instructions, encoding="utf-8"
    )


def _iscc_compile(iss_path: Path, *, app_version: str,
                  app_id: str, app_source_dir: str,
                  launch_master: bool = True) -> int:
    """Run the Inno Setup compiler on the rendered .iss script."""
    iscc = _iscc_path()
    if not iscc:
        log.error("Inno Setup compiler (ISCC.exe) was not found.")
        log.error("Install Inno Setup 6 from https://jrsoftware.org/isdownload.php")
        return 1

    defines = {
        "AppVersion": app_version,
        "AppId": app_id,
        "AppSourceDir": app_source_dir,
        "BundlePython": "1",
        "BundleVCRedist": "1",
        "ConfigureFirewall": "1",
        "LaunchMaster": "1" if launch_master else "0",
    }
    cmd: List[str] = [str(iscc), str(iss_path)]
    for k, v in defines.items():
        cmd.append(f"/D{k}={v}")
    rc, out, err = _run(cmd, cwd=iss_path.parent)
    if out.strip():
        log.info(out.strip())
    if err.strip():
        log.warning(err.strip())
    return rc


def _publish_output(compiled: Path) -> List[Path]:
    """Copy the compiled installer to dist/ and artifacts/."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    targets: List[Path] = []
    for folder in (DIST_DIR, ARTIFACTS_DIR):
        target = folder / compiled.name
        shutil.copy2(compiled, target)
        log.info("published: %s", target)
        targets.append(target)
    return targets


def build_setup(cfg: Optional[BuildConfig] = None,
                *,
                compile_only: bool = False,
                skip_payload: bool = False,
                skip_compile: bool = False,
                launch_master: Optional[bool] = None) -> int:
    cfg = cfg or BuildConfig()
    if launch_master is not None:
        cfg.launch_master = launch_master
    setup_logging(cfg.log_level)
    version = resolve_version()
    log.info("AIClusterSetup v%s - production installer build", version.version)

    if skip_payload:
        log.info("skipping payload staging (--skip-payload)")
    else:
        _stage_config()
        _stage_python()
        _stage_vcredist()
        _stage_aicluster()

    iss_source = SETUP_DIR / "setup.iss"
    if not iss_source.exists():
        log.error("missing template: %s", iss_source)
        return 1

    if compile_only or skip_compile:
        return 0

    rc = _iscc_compile(
        iss_source,
        app_version=version.version,
        app_id="com.aicluster.setup",
        app_source_dir=str(PAYLOAD_AICLUSTER.relative_to(SETUP_DIR)),
        launch_master=cfg.launch_master,
    )
    if rc != 0:
        return rc

    output_dir = iss_source.parent / "Output"
    if not output_dir.exists():
        log.error("Inno Setup did not produce the expected Output/ directory")
        return 1
    compiled = next(iter(output_dir.glob("*.exe")), None)
    if not compiled:
        log.error("Inno Setup did not produce an installer executable")
        return 1

    _publish_output(compiled)
    log.info("AIClusterSetup build SUCCEEDED: %s", compiled.name)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AIClusterSetup installer builder"
    )
    parser.add_argument("--skip-payload", action="store_true",
                        help="reuse the existing payload directory")
    parser.add_argument("--skip-compile", action="store_true",
                        help="stage the payload but do not call ISCC")
    parser.add_argument("--compile-only", action="store_true",
                        help="compile only (implies --skip-payload)")
    parser.add_argument("--no-launch", action="store_true",
                        help="do not auto-launch AICluster Master after install")
    args = parser.parse_args(argv)

    return build_setup(
        compile_only=args.compile_only,
        skip_payload=args.skip_payload or args.compile_only,
        skip_compile=args.skip_compile,
        launch_master=False if args.no_launch else None,
    )


if __name__ == "__main__":
    sys.exit(main())
