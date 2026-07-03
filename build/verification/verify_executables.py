"""Verify that every required executable exists and is a valid PE.

For each of the six required executables this verifier:

    1. Confirms the file is present in the expected release subdir.
    2. Confirms the file size is non-zero.
    3. Reads the PE header to confirm the file is a real Windows
       executable (the ``MZ`` magic + a valid ``PE\\0\\0`` header).
    4. Extracts the embedded version info when available.
    5. Captures a SHA-256 of the file for the verification report.

The CLI executable (``aicluster.exe``) is also smoke-tested by
running it with ``--help``. The smoke test only runs when the host
is Windows and ``ctx.skip_launch`` is False.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import List

from .utils import (
    file_size,
    get_logger,
    read_pe_metadata,
    timer,
)
from .context import (
    REQUIRED_EXECUTABLES,
    VerifierContext,
)
from .verify_report import Status, VerificationResult, VerificationReport

log = get_logger("verify.executables")

CHUNK = 1024 * 1024


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _subdir_for(name: str) -> str:
    if name == "AIClusterMaster.exe":
        return "master"
    if name == "AIClusterWorker.exe":
        return "worker"
    if name == "AIClusterStudio.exe":
        return "studio"
    if name == "MasterControlCenter.exe":
        return "master-control"
    if name == "WorkerControlCenter.exe":
        return "worker-control"
    if name == "aicluster.exe":
        return "cli"
    return ""


def _find_exe(release: Path, name: str) -> List[Path]:
    """Return every plausible path to ``name`` under ``release/``."""
    sub = _subdir_for(name)
    candidates: List[Path] = []
    seen: set = set()
    if sub:
        candidate = release / sub / name
        if candidate.exists():
            key = str(candidate.resolve()).lower()
            if key not in seen:
                candidates.append(candidate)
                seen.add(key)
    for candidate in sorted(release.rglob(name)):
        key = str(candidate.resolve()).lower()
        if key not in seen:
            candidates.append(candidate)
            seen.add(key)
    return candidates


def _check_executable(release: Path, name: str,
                      report: VerificationReport) -> VerificationResult:
    found = _find_exe(release, name)
    if not found:
        return VerificationResult(
            category="executables", name=name,
            status=Status.FAIL,
            message=f"missing executable: {name}",
        )
    path = found[0]
    if len(found) > 1:
        log.warning("multiple copies of %s found: %s",
                    name, [str(p) for p in found])
    size = file_size(path)
    if size <= 0:
        return VerificationResult(
            category="executables", name=name,
            status=Status.FAIL,
            message=f"empty executable: {path}",
            artifacts=[str(path)],
        )
    meta = read_pe_metadata(path)
    if not meta.is_pe:
        return VerificationResult(
            category="executables", name=name,
            status=Status.FAIL,
            message=f"not a valid PE: {path}",
            artifacts=[str(path)],
            details=meta.to_dict(),
        )
    return VerificationResult(
        category="executables", name=name,
        status=Status.PASS,
        message=f"{meta.machine} {size} bytes",
        artifacts=[str(path)],
        details={
            "size_bytes": size,
            "machine": meta.machine,
            "file_version": meta.file_version,
            "product_version": meta.product_version,
            "company": meta.company,
            "description": meta.description,
            "sha256": _sha256(path),
        },
    )


def _check_all_present(release: Path,
                       report: VerificationReport) -> VerificationResult:
    """Single PASS/FAIL summary covering every required executable."""
    missing = [n for n in REQUIRED_EXECUTABLES
               if not _find_exe(release, n)]
    if missing:
        return VerificationResult(
            category="executables", name="required set",
            status=Status.FAIL,
            message=f"missing: {', '.join(missing)}",
        )
    return VerificationResult(
        category="executables", name="required set",
        status=Status.PASS,
        message=f"all {len(REQUIRED_EXECUTABLES)} executables present",
    )


def _check_cli_smoke(release: Path,
                     ctx: VerifierContext) -> List[VerificationResult]:
    """Run ``aicluster.exe --help`` and confirm it exits 0 with output."""
    results: List[VerificationResult] = []
    candidates = _find_exe(release, "aicluster.exe")
    if not candidates:
        return results
    cli = candidates[0]
    if ctx.skip_launch:
        results.append(VerificationResult(
            category="cli", name="cli launch",
            status=Status.SKIP,
            message="launch skipped (AICLUSTER_VERIFY_SKIP_RUN=1)",
        ))
        return results
    if os.name != "nt":
        results.append(VerificationResult(
            category="cli", name="cli launch",
            status=Status.SKIP,
            message="non-Windows host cannot run a Windows .exe",
        ))
        return results
    try:
        proc = subprocess.run(
            [str(cli), "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        results.append(VerificationResult(
            category="cli", name="cli launch",
            status=Status.FAIL,
            message=f"could not launch {cli}: {exc}",
        ))
        return results
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0 and output.strip():
        results.append(VerificationResult(
            category="cli", name="cli --help",
            status=Status.PASS,
            message=f"exit 0, {len(output)} bytes of output",
            details={"output_excerpt": output[:160]},
        ))
    else:
        results.append(VerificationResult(
            category="cli", name="cli --help",
            status=Status.FAIL,
            message=f"exit {proc.returncode}, output: {output[:160]!r}",
            details={"returncode": proc.returncode,
                     "output": output[:160]},
        ))
    return results


def run(ctx: VerifierContext, parent: VerificationReport) -> List[VerificationResult]:
    """Verify every required executable in the release tree."""
    results: List[VerificationResult] = []
    with timer() as elapsed:
        results.append(_check_all_present(ctx.release_dir, parent))
        for name in REQUIRED_EXECUTABLES:
            results.append(_check_executable(ctx.release_dir, name, parent))
        results.extend(_check_cli_smoke(ctx.release_dir, ctx))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    log.info("executable verification complete: %d checks", len(results))
    return results
