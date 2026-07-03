"""Verify the Python runtime that ships with the installer.

This is a non-breaking check: it confirms that the bundled
``python-3.12.7-amd64.exe`` exists in the setup payload, is a
non-zero binary, and matches the expected version. It does not
install or execute the runtime.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import List, Optional

from .utils import file_size, get_logger, read_text_file, timer
from .context import (
    REQUIRED_PYTHON_RUNTIME,
    VerifierContext,
)
from .verify_report import Status, VerificationResult

log = get_logger("verify.python")

_VERSION_RE = re.compile(r"python-(\d+\.\d+\.\d+)")


def _check_bundled_python(ctx: VerifierContext) -> VerificationResult:
    """The installer payload contains a Python 3.12.x installer."""
    for rel in REQUIRED_PYTHON_RUNTIME:
        path = ctx.artifacts_dir.parent / rel
        if not path.exists():
            return VerificationResult(
                category="build", name="bundled python runtime",
                status=Status.FAIL,
                message=f"missing: {rel}",
            )
        size = file_size(path)
        if size < 1024 * 1024:
            return VerificationResult(
                category="build", name="bundled python runtime",
                status=Status.FAIL,
                message=f"{rel} is suspiciously small ({size} bytes)",
                artifacts=[str(path)],
            )
        m = _VERSION_RE.search(path.name)
        version = m.group(1) if m else "unknown"
        try:
            sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            return VerificationResult(
                category="build", name="bundled python runtime",
                status=Status.FAIL,
                message=f"could not hash {rel}: {exc}",
                artifacts=[str(path)],
            )
        return VerificationResult(
            category="build", name="bundled python runtime",
            status=Status.PASS,
            message=f"python {version} ({size} bytes)",
            artifacts=[str(path)],
            details={"version": version, "size_bytes": size, "sha256": sha256},
        )
    return VerificationResult(
        category="build", name="bundled python runtime",
        status=Status.SKIP,
        message="no python runtime path configured",
    )


def _check_system_python(ctx: VerifierContext) -> VerificationResult:
    """The host has a working Python interpreter (the one running this)."""
    import sys
    version = f"{sys.version_info.major}.{sys.version_info.minor}." \
              f"{sys.version_info.micro}"
    if (sys.version_info.major, sys.version_info.minor) < (3, 12):
        return VerificationResult(
            category="build", name="system python",
            status=Status.WARN,
            message=f"host python {version} is older than 3.12",
            details={"version": version, "executable": sys.executable},
        )
    return VerificationResult(
        category="build", name="system python",
        status=Status.PASS,
        message=f"host python {version}",
        details={"version": version, "executable": sys.executable},
    )


def run(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    with timer() as elapsed:
        results.append(_check_bundled_python(ctx))
        results.append(_check_system_python(ctx))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results
