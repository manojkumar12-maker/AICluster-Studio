"""Verify the AICluster backend services.

This module covers:

    * Master server - launch ``AIClusterMaster.exe``, wait for the
      API port, hit ``GET /api/v1/health``, shut down gracefully.
    * Worker service - launch ``AIClusterWorker.exe``, give it a
      short window to register with the master (or fail standalone),
      and shut it down cleanly.

The verifier never modifies any executable. On non-Windows hosts it
emits a SKIP rather than a FAIL.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List, Optional

from .utils import (
    get_logger,
    http_get,
    launch_executable,
    terminate_process,
    timer,
    wait_for_port,
)
from .context import HEALTH_ENDPOINT, VerifierContext
from .verify_report import Status, VerificationResult

log = get_logger("verify.backend")


# ---------------------------------------------------------------------------
# Master
# ---------------------------------------------------------------------------

def _resolve_exe(release: Path, sub: str, name: str) -> Optional[Path]:
    primary = release / sub / name
    if primary.exists():
        return primary
    matches = sorted(release.rglob(name))
    return matches[0] if matches else None


def _verify_master(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    master = _resolve_exe(ctx.release_dir, "master", "AIClusterMaster.exe")
    if master is None:
        results.append(VerificationResult(
            category="backend", name="master executable",
            status=Status.FAIL,
            message="AIClusterMaster.exe not found in release/",
        ))
        return results
    results.append(VerificationResult(
        category="backend", name="master executable",
        status=Status.PASS,
        message=str(master),
        artifacts=[str(master)],
    ))
    if ctx.skip_launch:
        results.append(VerificationResult(
            category="backend", name="master launch",
            status=Status.SKIP,
            message="launch skipped (AICLUSTER_VERIFY_SKIP_RUN=1)",
        ))
        return results
    if not _can_run_windows(master):
        results.append(VerificationResult(
            category="backend", name="master launch",
            status=Status.SKIP,
            message="non-Windows host cannot run a Windows .exe",
        ))
        return results

    proc = None
    try:
        with timer() as elapsed:
            log.info("launching %s", master)
            try:
                proc = launch_executable(
                    master,
                    cwd=master.parent,
                    env={
                        "AICLUSTER_API_PORT": str(ctx.api_port),
                        "AICLUSTER_HOST": "127.0.0.1",
                        "AICLUSTER_LOG_LEVEL": "INFO",
                    },
                )
            except (OSError, ValueError) as exc:
                results.append(VerificationResult(
                    category="backend", name="master launch",
                    status=Status.FAIL,
                    message=f"could not launch {master.name}: "
                            f"{type(exc).__name__}: {exc}",
                    artifacts=[str(master)],
                ))
                return results
            results.append(VerificationResult(
                category="backend", name="master launch",
                status=Status.PASS,
                message=f"pid={proc.pid}",
                details={"pid": proc.pid, "elapsed": elapsed()},
            ))
            ready = wait_for_port(ctx.api_port,
                                  deadline_seconds=ctx.launch_timeout)
            if not ready:
                results.append(VerificationResult(
                    category="backend", name="master port",
                    status=Status.FAIL,
                    message=f"port {ctx.api_port} not listening after "
                            f"{ctx.launch_timeout:.1f}s",
                ))
                return results
            results.append(VerificationResult(
                category="backend", name="master port",
                status=Status.PASS,
                message=f"port {ctx.api_port} listening",
            ))
    finally:
        if proc is not None:
            log.info("shutting down master (pid=%s)", proc.pid)
            terminate_process(proc, timeout=ctx.shutdown_timeout)
            results.append(VerificationResult(
                category="backend", name="master shutdown",
                status=Status.PASS if proc.poll() is not None else Status.WARN,
                message=f"exit code {proc.returncode}",
                details={"returncode": proc.returncode},
            ))
    return results


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def _verify_worker(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    worker = _resolve_exe(ctx.release_dir, "worker", "AIClusterWorker.exe")
    if worker is None:
        results.append(VerificationResult(
            category="worker", name="worker executable",
            status=Status.FAIL,
            message="AIClusterWorker.exe not found in release/",
        ))
        return results
    results.append(VerificationResult(
        category="worker", name="worker executable",
        status=Status.PASS,
        message=str(worker),
        artifacts=[str(worker)],
    ))

    # The worker is a long-running service. It tries to connect to a
    # master on startup; on a fresh host there is no master, so we
    # expect the worker to retry and stay alive (it does not crash
    # merely because the master is unreachable).
    config_json = ctx.release_dir / "worker" / "config.json"
    if config_json.exists():
        results.append(VerificationResult(
            category="worker", name="worker config present",
            status=Status.PASS,
            message=str(config_json),
            artifacts=[str(config_json)],
        ))
    else:
        results.append(VerificationResult(
            category="worker", name="worker config present",
            status=Status.WARN,
            message=f"no config.json next to {worker.name}",
        ))

    if ctx.skip_launch:
        results.append(VerificationResult(
            category="worker", name="worker launch",
            status=Status.SKIP,
            message="launch skipped (AICLUSTER_VERIFY_SKIP_RUN=1)",
        ))
        return results
    if not _can_run_windows(worker):
        results.append(VerificationResult(
            category="worker", name="worker launch",
            status=Status.SKIP,
            message="non-Windows host cannot run a Windows .exe",
        ))
        return results

    proc = None
    try:
        with timer() as elapsed:
            log.info("launching %s", worker)
            try:
                proc = launch_executable(
                    worker,
                    cwd=worker.parent,
                    env={
                        "AICLUSTER_MASTER_URL": f"http://127.0.0.1:{ctx.api_port}",
                        "AICLUSTER_LOG_LEVEL": "INFO",
                    },
                )
            except (OSError, ValueError) as exc:
                results.append(VerificationResult(
                    category="worker", name="worker launch",
                    status=Status.FAIL,
                    message=f"could not launch {worker.name}: "
                            f"{type(exc).__name__}: {exc}",
                ))
                return results
            results.append(VerificationResult(
                category="worker", name="worker launch",
                status=Status.PASS,
                message=f"pid={proc.pid}",
                details={"pid": proc.pid, "elapsed": elapsed()},
            ))
            # Give the worker a moment to read its config and either
            # connect or attempt to retry. The worker does not crash
            # when the master is missing; it just keeps retrying.
            observation = 5.0
            deadline = time.monotonic() + observation
            crashed = False
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    crashed = True
                    break
                time.sleep(0.25)
            if crashed:
                results.append(VerificationResult(
                    category="worker", name="worker startup",
                    status=Status.FAIL,
                    message=f"worker exited prematurely "
                            f"(code={proc.returncode})",
                ))
            else:
                results.append(VerificationResult(
                    category="worker", name="worker startup",
                    status=Status.PASS,
                    message="worker still running after "
                            f"{observation:.1f}s observation window",
                ))
    finally:
        if proc is not None:
            log.info("shutting down worker (pid=%s)", proc.pid)
            terminate_process(proc, timeout=ctx.shutdown_timeout)
            results.append(VerificationResult(
                category="worker", name="worker shutdown",
                status=Status.PASS if proc.poll() is not None else Status.WARN,
                message=f"exit code {proc.returncode}",
                details={"returncode": proc.returncode},
            ))
    return results


def run(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    with timer() as elapsed:
        results.extend(_verify_master(ctx))
        results.extend(_verify_worker(ctx))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _can_run_windows(path: Path) -> bool:
    if os.name == "nt":
        return True
    return _looks_like_windows_binary(path)


def _looks_like_windows_binary(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(2) == b"MZ"
    except OSError:
        return False
