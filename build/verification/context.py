"""Configuration constants for the release verification system.

The defaults match the production build layout, but every value can be
overridden with environment variables for ad-hoc test runs:

    AICLUSTER_VERIFY_RELEASE_DIR    default: <repo>/release
    AICLUSTER_VERIFY_DIST_DIR       default: <repo>/dist
    AICLUSTER_VERIFY_ARTIFACTS_DIR  default: <repo>/artifacts
    AICLUSTER_VERIFY_PORT           default: 8000  (master API port)
    AICLUSTER_VERIFY_WORKER_PORT    default: 8001  (worker port)
    AICLUSTER_VERIFY_TIMEOUT        default: 20.0  (seconds)
    AICLUSTER_VERIFY_REPORT_DIR     default: <repo>/release/reports
    AICLUSTER_VERIFY_SKIP_RUN       default: false  (when set, skip launching)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..config import REPO_ROOT


RELEASE_DIR: Path = Path(
    os.environ.get("AICLUSTER_VERIFY_RELEASE_DIR",
                   str(REPO_ROOT / "release"))
)
DIST_DIR: Path = Path(
    os.environ.get("AICLUSTER_VERIFY_DIST_DIR",
                   str(REPO_ROOT / "dist"))
)
ARTIFACTS_DIR: Path = Path(
    os.environ.get("AICLUSTER_VERIFY_ARTIFACTS_DIR",
                   str(REPO_ROOT / "artifacts"))
)
REPORT_DIR: Path = Path(
    os.environ.get("AICLUSTER_VERIFY_REPORT_DIR",
                   str(RELEASE_DIR / "reports"))
)

MASTER_API_PORT: int = int(os.environ.get("AICLUSTER_VERIFY_PORT", "8000"))
WORKER_PORT: int = int(os.environ.get("AICLUSTER_VERIFY_WORKER_PORT", "8001"))
STUDIO_PORT: int = int(os.environ.get("AICLUSTER_VERIFY_STUDIO_PORT", "5174"))
STUDIO_W_PORT: int = int(os.environ.get("AICLUSTER_VERIFY_STUDIO_W_PORT", "5175"))

LAUNCH_TIMEOUT: float = float(os.environ.get("AICLUSTER_VERIFY_TIMEOUT", "20.0"))
STUDIO_TIMEOUT: float = float(os.environ.get("AICLUSTER_VERIFY_STUDIO_TIMEOUT", "10.0"))
SHUTDOWN_TIMEOUT: float = float(os.environ.get("AICLUSTER_VERIFY_SHUTDOWN_TIMEOUT", "5.0"))


REQUIRED_EXECUTABLES: List[str] = [
    "AIClusterMaster.exe",
    "AIClusterWorker.exe",
    "AIClusterStudio.exe",
    "MasterControlCenter.exe",
    "WorkerControlCenter.exe",
    "aicluster.exe",
]

REQUIRED_INSTALLER: str = "AIClusterSetup.exe"

REQUIRED_CONFIG_FILES: List[str] = [
    "VERSION",
    "CHANGELOG.md",
    "README.md",
    "assets/manifest.json",
    "assets/icons/default.ico",
    "config/default.yaml",
]

EXPECTED_VERSION_SOURCES: List[str] = [
    "VERSION",
    "CHANGELOG.md",
    "build/version.py",
    "build/setup/setup.iss",
]

REQUIRED_PYTHON_RUNTIME: List[str] = [
    "build/setup/payload/python/python-3.12.7-amd64.exe",
]

REQUIRED_VC_RUNTIME: List[str] = [
    "build/setup/payload/vcredist/vc_redist.x64.exe",
]

SKIP_LAUNCH: bool = os.environ.get("AICLUSTER_VERIFY_SKIP_RUN", "").lower() in (
    "1", "true", "yes"
)

HEALTH_ENDPOINT: str = f"http://127.0.0.1:{MASTER_API_PORT}/api/v1/health"


@dataclass
class VerifierContext:
    """Per-run context handed to every verifier.

    Holds shared paths and tunables. The ``data`` dict is a free-form
    scratch space that verifiers can use to pass values downstream
    (for example the discovered master process handle).
    """

    release_dir: Path = RELEASE_DIR
    dist_dir: Path = DIST_DIR
    artifacts_dir: Path = ARTIFACTS_DIR
    report_dir: Path = REPORT_DIR
    version: str = ""
    build_number: str = ""
    skip_launch: bool = SKIP_LAUNCH
    api_port: int = MASTER_API_PORT
    worker_port: int = WORKER_PORT
    studio_port: int = STUDIO_PORT
    studio_w_port: int = STUDIO_W_PORT
    launch_timeout: float = LAUNCH_TIMEOUT
    studio_timeout: float = STUDIO_TIMEOUT
    shutdown_timeout: float = SHUTDOWN_TIMEOUT
    data: dict = field(default_factory=dict)

    def with_overrides(self, **kwargs) -> "VerifierContext":
        clone = VerifierContext(
            release_dir=self.release_dir,
            dist_dir=self.dist_dir,
            artifacts_dir=self.artifacts_dir,
            report_dir=self.report_dir,
            version=self.version,
            build_number=self.build_number,
            skip_launch=self.skip_launch,
            api_port=self.api_port,
            worker_port=self.worker_port,
            studio_port=self.studio_port,
            studio_w_port=self.studio_w_port,
            launch_timeout=self.launch_timeout,
            studio_timeout=self.studio_timeout,
            shutdown_timeout=self.shutdown_timeout,
            data=dict(self.data),
        )
        for key, value in kwargs.items():
            if hasattr(clone, key):
                setattr(clone, key, value)
        return clone
