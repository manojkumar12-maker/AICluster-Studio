"""Build every web frontend that ships in the AICluster release.

Apps built here:
    * Master dashboard      ``frontend/``           -> ``frontend/.next/``
    * Master Control Center ``master-control-center/frontend/`` -> ``dist/``
    * Worker Control Center ``worker-control-center/frontend/`` -> ``dist/``
    * AICluster Studio      ``studio/``             -> ``dist/``

If a frontend already has a built artifact in place (e.g. the user ran
``npm run build`` themselves) we still invoke ``npm run build`` so the
output is reproducible and up to date.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .config import (
    REPO_ROOT,
    BuildConfig,
)
from .logger import setup_logging, get_logger

log = get_logger("aicluster.build.frontend")


@dataclass
class FrontendTarget:
    key: str
    name: str
    directory: Path
    out_marker: Path  # path that should exist after a successful build
    install_required: bool = True


TARGETS: List[FrontendTarget] = [
    FrontendTarget(
        key="master-dashboard",
        name="Master Dashboard",
        directory=REPO_ROOT / "frontend",
        out_marker=REPO_ROOT / "frontend" / ".next",
    ),
    FrontendTarget(
        key="master-control",
        name="Master Control Center Web",
        directory=REPO_ROOT / "master-control-center" / "frontend",
        out_marker=REPO_ROOT / "master-control-center" / "frontend" / "dist",
    ),
    FrontendTarget(
        key="worker-control",
        name="Worker Control Center Web",
        directory=REPO_ROOT / "worker-control-center" / "frontend",
        out_marker=REPO_ROOT / "worker-control-center" / "frontend" / "dist",
    ),
    FrontendTarget(
        key="studio",
        name="AICluster Studio Web",
        directory=REPO_ROOT / "studio",
        out_marker=REPO_ROOT / "studio" / "dist",
    ),
]


def _run(cmd: List[str], cwd: Path, env: Optional[dict] = None) -> int:
    log.info("$ %s (cwd=%s)", " ".join(cmd), cwd)
    needs_shell = (
        os.name == "nt"
        and cmd
        and (
            cmd[0].lower().endswith((".cmd", ".bat"))
            or (not Path(cmd[0]).exists() and Path(cmd[0]).suffix == "")
        )
    )
    if needs_shell:
        proc = subprocess.run(
            " ".join(f'"{c}"' for c in cmd),
            cwd=cwd, shell=True,
            env={**os.environ, **(env or {})},
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    else:
        proc = subprocess.run(
            cmd, cwd=cwd,
            env={**os.environ, **(env or {})},
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    if proc.stdout:
        for line in proc.stdout.splitlines():
            log.info("  | %s", line)
    return proc.returncode


def build_one(target: FrontendTarget) -> bool:
    if not target.directory.exists():
        log.warning("frontend missing: %s", target.directory)
        return False

    node_modules = target.directory / "node_modules"
    if not node_modules.exists():
        log.info("[%s] installing dependencies", target.name)
        if _run(["npm", "ci"], cwd=target.directory) != 0 and \
           _run(["npm", "install"], cwd=target.directory) != 0:
            log.error("[%s] npm install failed", target.name)
            return False

    log.info("[%s] running production build", target.name)
    rc = _run(["npm", "run", "build"], cwd=target.directory)
    if rc != 0:
        log.error("[%s] build failed (exit %d)", target.name, rc)
        return False

    if not target.out_marker.exists():
        log.error(
            "[%s] build returned 0 but expected output %s is missing",
            target.name, target.out_marker,
        )
        return False
    log.info("[%s] OK -> %s", target.name, target.out_marker)
    return True


def build_all(cfg: Optional[BuildConfig] = None) -> bool:
    cfg = cfg or BuildConfig()
    setup_logging(cfg.log_level)
    ok = True
    for target in TARGETS:
        if not build_one(target):
            ok = False
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if build_all() else 1)
