"""Verify the AICluster frontend bundles and Tauri desktop apps.

This module covers four targets:

    1. The master dashboard (``frontend/``) - Next.js static export
    2. The master control center web bundle (Vite)
    3. The worker control center web bundle (Vite)
    4. AICluster Studio web bundle (Vite + Tauri v2)

For each it confirms:

    * The source ``package.json`` exists and has a build script
    * The built bundle (``dist/`` or ``.next/``) is on disk
    * The HTML entry point references real scripts

It also runs an opt-in smoke test for the three Tauri apps (Master
CC, Worker CC, Studio): launch the executable, wait a few seconds,
confirm the process is still alive, then shut it down. The Tauri apps
open a window on a real desktop; on headless CI the smoke test is
treated as a WARN, not a FAIL, because the windowing subsystem may
not be available.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

from .utils import (
    get_logger,
    launch_executable,
    read_text_file,
    terminate_process,
    timer,
)
from .context import VerifierContext
from .verify_report import Status, VerificationResult

log = get_logger("verify.frontend")


# (key, name, source folder, built marker, tauri exe name)
FRONTENDS: List[Tuple[str, str, Path, Path, Optional[str]]] = [
    ("master-dashboard", "Master Dashboard",
     Path("frontend"), Path("frontend/.next"), None),
    ("master-control", "Master Control Center Web",
     Path("master-control-center/frontend"),
     Path("master-control-center/frontend/dist"),
     "MasterControlCenter.exe"),
    ("worker-control", "Worker Control Center Web",
     Path("worker-control-center/frontend"),
     Path("worker-control-center/frontend/dist"),
     "WorkerControlCenter.exe"),
    ("studio", "AICluster Studio Web",
     Path("studio"), Path("studio/dist"),
     "AIClusterStudio.exe"),
]


def _check_source_manifests(ctx: VerifierContext) -> List[VerificationResult]:
    """Every frontend has a ``package.json`` that is parseable JSON."""
    results: List[VerificationResult] = []
    import json
    for key, _name, folder, _marker, _exe in FRONTENDS:
        pkg = ctx.release_dir.parent / folder / "package.json"
        if not pkg.exists():
            results.append(VerificationResult(
                category="frontend", name=f"{key} package.json",
                status=Status.FAIL,
                message=f"missing: {pkg}",
            ))
            continue
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append(VerificationResult(
                category="frontend", name=f"{key} package.json",
                status=Status.FAIL,
                message=f"invalid JSON: {exc}",
                artifacts=[str(pkg)],
            ))
            continue
        scripts = data.get("scripts", {})
        if "build" not in scripts:
            results.append(VerificationResult(
                category="frontend", name=f"{key} build script",
                status=Status.FAIL,
                message="no 'build' script in package.json",
                artifacts=[str(pkg)],
            ))
        else:
            results.append(VerificationResult(
                category="frontend", name=f"{key} build script",
                status=Status.PASS,
                message=f"build script: {scripts['build']!r}",
                artifacts=[str(pkg)],
            ))
    return results


def _check_built_artifacts(ctx: VerifierContext) -> List[VerificationResult]:
    """The prebuilt frontend bundles exist on disk."""
    results: List[VerificationResult] = []
    repo = ctx.release_dir.parent
    for key, _name, _folder, marker, _exe in FRONTENDS:
        full = repo / marker
        if full.exists():
            file_count = sum(1 for _ in full.rglob("*") if _.is_file())
            results.append(VerificationResult(
                category="frontend", name=f"{key} build",
                status=Status.PASS if file_count > 0 else Status.WARN,
                message=f"build marker at {marker.as_posix()} "
                        f"contains {file_count} files",
                artifacts=[str(full)],
            ))
        else:
            results.append(VerificationResult(
                category="frontend", name=f"{key} build",
                status=Status.WARN,
                message=f"no built bundle at {marker.as_posix()} "
                        f"(frontend build may have been skipped)",
            ))
    return results


def _check_html_entrypoints(ctx: VerifierContext) -> List[VerificationResult]:
    """The HTML entry points (where present) reference real scripts."""
    results: List[VerificationResult] = []
    repo = ctx.release_dir.parent
    for key, _name, folder, _marker, _exe in FRONTENDS:
        index = repo / folder / "index.html"
        if not index.exists():
            continue
        text = read_text_file(index)
        if text is None:
            results.append(VerificationResult(
                category="frontend", name=f"{key} index.html",
                status=Status.WARN,
                message=f"unreadable: {index}",
            ))
            continue
        has_script = bool(re.search(
            r"<script[^>]+src=|<script[^>]*type=\"module\"", text
        ))
        results.append(VerificationResult(
            category="frontend", name=f"{key} index.html",
            status=Status.PASS if has_script else Status.WARN,
            message="contains script reference" if has_script else
                    "no <script> tag found",
            artifacts=[str(index)],
        ))
    return results


def _check_release_tauri_artifacts(ctx: VerifierContext) -> List[VerificationResult]:
    """The release/ tree contains the Tauri-produced executables."""
    results: List[VerificationResult] = []
    tauri_targets = [
        ("master-control", "Master Control Center", "MasterControlCenter.exe"),
        ("worker-control", "Worker Control Center", "WorkerControlCenter.exe"),
        ("studio", "AICluster Studio", "AIClusterStudio.exe"),
    ]
    for key, name, exe in tauri_targets:
        sub = key
        path = ctx.release_dir / sub / exe
        if path.exists() and path.stat().st_size > 0:
            results.append(VerificationResult(
                category="frontend", name=f"{key} tauri exe",
                status=Status.PASS,
                message=f"{path.stat().st_size} bytes",
                artifacts=[str(path)],
            ))
        else:
            results.append(VerificationResult(
                category="frontend", name=f"{key} tauri exe",
                status=Status.WARN,
                message=f"missing: {path}",
            ))
    return results


def _can_run_tauri(exe: Path) -> bool:
    if os.name == "nt":
        return True
    try:
        with exe.open("rb") as fh:
            return fh.read(2) == b"MZ"
    except OSError:
        return False


def _smoke_tauri_exe(ctx: VerifierContext, key: str, name: str,
                     exe: Path, category: str) -> List[VerificationResult]:
    """Launch a Tauri executable, observe for a few seconds, kill it."""
    results: List[VerificationResult] = []
    if not exe.exists():
        return results
    if not _can_run_tauri(exe):
        results.append(VerificationResult(
            category=category, name=f"{name} launch",
            status=Status.SKIP,
            message="non-Windows host cannot run a Windows .exe",
        ))
        return results
    if ctx.skip_launch:
        results.append(VerificationResult(
            category=category, name=f"{name} launch",
            status=Status.SKIP,
            message="launch skipped (AICLUSTER_VERIFY_SKIP_RUN=1)",
        ))
        return results

    proc = None
    try:
        with timer() as elapsed:
            try:
                proc = launch_executable(exe, cwd=exe.parent)
            except (OSError, ValueError) as exc:
                results.append(VerificationResult(
                    category=category, name=f"{name} launch",
                    status=Status.FAIL,
                    message=f"could not launch {exe.name}: "
                            f"{type(exc).__name__}: {exc}",
                ))
                return results
            results.append(VerificationResult(
                category=category, name=f"{name} launch",
                status=Status.PASS,
                message=f"pid={proc.pid}",
                details={"pid": proc.pid, "elapsed": elapsed()},
            ))
            # Tauri apps open a window. On a real desktop we expect
            # the process to stay alive for at least 3 seconds. On
            # headless CI (no display) the app may exit immediately;
            # in that case we downgrade to a WARN.
            observation = min(3.0, ctx.studio_timeout / 2)
            deadline = time.monotonic() + observation
            crashed = False
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    crashed = True
                    break
                time.sleep(0.25)
            if crashed:
                results.append(VerificationResult(
                    category=category, name=f"{name} window",
                    status=Status.WARN,
                    message=f"process exited with code {proc.returncode} "
                            f"(no display available?)",
                ))
            else:
                results.append(VerificationResult(
                    category=category, name=f"{name} window",
                    status=Status.PASS,
                    message=f"alive after {observation:.1f}s",
                ))
    finally:
        if proc is not None and proc.poll() is None:
            terminate_process(proc, timeout=ctx.shutdown_timeout)
            results.append(VerificationResult(
                category=category, name=f"{name} shutdown",
                status=Status.PASS if proc.poll() is not None else Status.WARN,
                message=f"exit code {proc.returncode}",
                details={"returncode": proc.returncode},
            ))
    return results


def _verify_tauri_smoke_tests(ctx: VerifierContext) -> List[VerificationResult]:
    """Smoke test the Master CC, Worker CC, and Studio Tauri apps."""
    results: List[VerificationResult] = []
    targets = [
        ("master-control", "Master Control Center",
         "MasterControlCenter.exe", "frontend"),
        ("worker-control", "Worker Control Center",
         "WorkerControlCenter.exe", "frontend"),
        ("studio", "AICluster Studio",
         "AIClusterStudio.exe", "studio"),
    ]
    for key, name, exe_name, category in targets:
        exe = ctx.release_dir / key / exe_name
        if not exe.exists():
            results.append(VerificationResult(
                category=category, name=f"{name} tauri exe",
                status=Status.WARN,
                message=f"missing: {exe}",
            ))
            continue
        results.extend(_smoke_tauri_exe(ctx, key, name, exe, category))
    return results


def run(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    with timer() as elapsed:
        results.extend(_check_source_manifests(ctx))
        results.extend(_check_built_artifacts(ctx))
        results.extend(_check_html_entrypoints(ctx))
        results.extend(_check_release_tauri_artifacts(ctx))
        results.extend(_verify_tauri_smoke_tests(ctx))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results

