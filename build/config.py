"""AICluster Build System Configuration.

Central configuration for all build targets. Values can be overridden by
environment variables (prefix AICLUSTER_BUILD_*) before invoking the build.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _detect_repo_root() -> Path:
    """Locate the AICluster repository root.

    Walks upward from this file until it finds a directory that contains
    both ``backend`` and ``worker`` (the two long-standing core packages).
    Falls back to the parent of ``build/`` if discovery fails.
    """
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "backend").is_dir() and (candidate / "worker").is_dir():
            return candidate
    return here.parent


REPO_ROOT: Path = _detect_repo_root()
BUILD_DIR: Path = REPO_ROOT / "build"
ASSETS_DIR: Path = REPO_ROOT / "assets"
DIST_DIR: Path = REPO_ROOT / "dist"
RELEASE_DIR: Path = REPO_ROOT / "release"
ARTIFACTS_DIR: Path = REPO_ROOT / "artifacts"
TEMP_DIR: Path = REPO_ROOT / "temp"
LOGS_DIR: Path = REPO_ROOT / "logs"
CHECKSUMS_DIR: Path = REPO_ROOT / "checksums"
ICONS_DIR: Path = ASSETS_DIR / "icons"

FRONTEND_DIST: Path = REPO_ROOT / "frontend" / ".next"
MASTER_FRONTEND_DIST: Path = REPO_ROOT / "master-control-center" / "frontend" / "dist"
WORKER_CC_FRONTEND_DIST: Path = REPO_ROOT / "worker-control-center" / "frontend" / "dist"
STUDIO_FRONTEND_DIST: Path = REPO_ROOT / "studio" / "dist"


@dataclass(frozen=True)
class PyInstallerTarget:
    """Definition of a Python application packaged with PyInstaller."""

    key: str
    name: str  # human readable
    entry: Path  # python entry script (relative to repo root)
    output_name: str  # exe name (e.g. AIClusterMaster.exe)
    output_subdir: str  # path under release/
    console: bool = True
    icon: Optional[Path] = None
    add_data: List[tuple] = field(default_factory=list)  # (src, dest)
    hidden_imports: List[str] = field(default_factory=list)
    extra_args: List[str] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class TauriTarget:
    """Definition of a Tauri v2 desktop application."""

    key: str
    name: str
    frontend_dir: Path
    tauri_config_dir: Path
    output_name: str
    output_subdir: str
    icon: Optional[Path] = None
    description: str = ""


@dataclass
class BuildConfig:
    """Runtime build configuration."""

    product_name: str = "AICluster"
    company: str = "AICluster"
    copyright: str = "Copyright (c) 2026 AICluster"
    version: str = "1.2.2"
    description: str = "AICluster - Offline AI Cluster Management Platform"
    python_min_version: tuple = (3, 12)
    node_min_version: tuple = (18, 0)
    rust_min_version: tuple = (1, 70)
    tauri_min_version: tuple = (2, 0)
    skip_sign: bool = True
    skip_tauri: bool = False
    skip_installer: bool = False
    skip_zip: bool = False
    launch_master: bool = True
    signtool_path: Optional[str] = None
    certificate_path: Optional[str] = None
    certificate_password: Optional[str] = None
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        # env overrides
        if v := os.environ.get("AICLUSTER_BUILD_VERSION"):
            self.version = v
        if v := os.environ.get("AICLUSTER_BUILD_SKIP_SIGN"):
            self.skip_sign = v.lower() in ("1", "true", "yes")
        if v := os.environ.get("AICLUSTER_BUILD_SKIP_TAURI"):
            self.skip_tauri = v.lower() in ("1", "true", "yes")
        if v := os.environ.get("AICLUSTER_BUILD_SKIP_INSTALLER"):
            self.skip_installer = v.lower() in ("1", "true", "yes")
        if v := os.environ.get("AICLUSTER_BUILD_SKIP_ZIP"):
            self.skip_zip = v.lower() in ("1", "true", "yes")
        if v := os.environ.get("AICLUSTER_BUILD_NO_LAUNCH"):
            self.launch_master = v.lower() not in ("1", "true", "yes")


def _make_pyinstaller_targets() -> List[PyInstallerTarget]:
    icons = ICONS_DIR
    return [
        PyInstallerTarget(
            key="master",
            name="Master Server",
            entry=REPO_ROOT / "build" / "modules" / "master_entry.py",
            output_name="AIClusterMaster.exe",
            output_subdir="master",
            console=True,
            icon=icons / "master.ico",
            add_data=[
                (str(REPO_ROOT / "backend" / "app"), "app"),
                (str(REPO_ROOT / "backend" / "alembic"), "alembic"),
                (str(REPO_ROOT / "shared" / "py"), "shared"),
                (str(REPO_ROOT / "config"), "config"),
            ],
            hidden_imports=[
                "uvicorn.logging",
                "uvicorn.loops",
                "uvicorn.loops.auto",
                "uvicorn.protocols",
                "uvicorn.protocols.http",
                "uvicorn.protocols.http.auto",
                "uvicorn.protocols.websockets",
                "uvicorn.protocols.websockets.auto",
                "uvicorn.lifespan",
                "uvicorn.lifespan.on",
                "aiosqlite",
                "sqlalchemy.dialects.sqlite",
                "alembic",
            ],
            extra_args=[],
            description="AICluster Master Server (FastAPI)",
        ),
        PyInstallerTarget(
            key="worker",
            name="Worker Service",
            entry=REPO_ROOT / "build" / "modules" / "worker_entry.py",
            output_name="AIClusterWorker.exe",
            output_subdir="worker",
            console=True,
            icon=icons / "worker.ico",
            add_data=[
                (str(REPO_ROOT / "worker" / "app"), "app"),
                (str(REPO_ROOT / "worker" / "config.json"), "config.json"),
                (str(REPO_ROOT / "shared" / "py"), "shared"),
            ],
            hidden_imports=[
                "uvicorn.logging",
                "uvicorn.loops",
                "uvicorn.loops.auto",
                "uvicorn.protocols",
                "uvicorn.protocols.http",
                "uvicorn.protocols.http.auto",
                "uvicorn.protocols.websockets",
                "uvicorn.protocols.websockets.auto",
                "uvicorn.lifespan",
                "uvicorn.lifespan.on",
                "psutil",
            ],
            description="AICluster Worker Service",
        ),
        PyInstallerTarget(
            key="cli",
            name="AICluster CLI",
            entry=BUILD_DIR / "modules" / "cli_entry.py",
            output_name="aicluster.exe",
            output_subdir="cli",
            console=True,
            icon=icons / "cli.ico",
            add_data=[
                (str(REPO_ROOT / "shared" / "py"), "shared"),
                (str(REPO_ROOT / "config"), "config"),
            ],
            hidden_imports=["httpx", "rich"],
            description="AICluster Command Line Interface",
        ),
    ]


def _make_tauri_targets() -> List[TauriTarget]:
    icons = ICONS_DIR
    return [
        TauriTarget(
            key="master-control",
            name="Master Control Center",
            frontend_dir=REPO_ROOT / "master-control-center" / "frontend",
            tauri_config_dir=REPO_ROOT / "master-control-center" / "frontend" / "src-tauri",
            output_name="MasterControlCenter.exe",
            output_subdir="master-control",
            icon=icons / "master-control.ico",
            description="AICluster Master Control Center desktop app",
        ),
        TauriTarget(
            key="worker-control",
            name="Worker Control Center",
            frontend_dir=REPO_ROOT / "worker-control-center" / "frontend",
            tauri_config_dir=REPO_ROOT / "worker-control-center" / "frontend" / "src-tauri",
            output_name="WorkerControlCenter.exe",
            output_subdir="worker-control",
            icon=icons / "worker-control.ico",
            description="AICluster Worker Control Center desktop app",
        ),
        TauriTarget(
            key="studio",
            name="AICluster Studio",
            frontend_dir=REPO_ROOT / "studio",
            tauri_config_dir=REPO_ROOT / "studio" / "src-tauri",
            output_name="AIClusterStudio.exe",
            output_subdir="studio",
            icon=icons / "studio.ico",
            description="AICluster Studio - Visual IDE & Workspace",
        ),
    ]


PYINSTALLER_TARGETS: List[PyInstallerTarget] = _make_pyinstaller_targets()
TAURI_TARGETS: List[TauriTarget] = _make_tauri_targets()

RELEASE_LAYOUT: Dict[str, Path] = {
    "master": RELEASE_DIR / "master",
    "worker": RELEASE_DIR / "worker",
    "master-control": RELEASE_DIR / "master-control",
    "worker-control": RELEASE_DIR / "worker-control",
    "studio": RELEASE_DIR / "studio",
    "cli": RELEASE_DIR / "cli",
    "checksums": RELEASE_DIR / "checksums",
    "installer": RELEASE_DIR / "installer",
    "zip": RELEASE_DIR / "zip",
    "reports": RELEASE_DIR / "reports",
}


def all_release_subdirs() -> List[Path]:
    return sorted({p for p in RELEASE_LAYOUT.values()})


def find_exe_in_dir(directory: Path, name_hint: str) -> Optional[Path]:
    """Return the first .exe in ``directory`` whose stem matches ``name_hint``.

    Falls back to the first .exe found if no stem match exists.
    """
    if not directory.is_dir():
        return None
    candidates = sorted(directory.glob("*.exe"))
    if not candidates:
        return None
    stem = name_hint.lower().replace(".exe", "")
    for c in candidates:
        if c.stem.lower() == stem:
            return c
    return candidates[0]


def is_windows() -> bool:
    return sys.platform.startswith("win")
