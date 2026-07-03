"""Build-output presence and sanity check.

This is the very first verification stage. It runs *after* the
build orchestrator finishes and only inspects the static shape of
the output:

    * the build command exited with code 0 (supplied by the caller)
    * the release folder exists and is non-empty
    * the manifest parses and has the expected keys
    * the build report exists and parses

It does not launch anything. A failure here is the most severe
kind: the build is structurally broken.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from .utils import get_logger, read_text_file, timer
from .context import VerifierContext
from .verify_report import Status, VerificationResult

log = get_logger("verify.build")


def _check_release_dir(ctx: VerifierContext) -> VerificationResult:
    """The release directory exists and contains at least one subdir."""
    if not ctx.release_dir.exists():
        return VerificationResult(
            category="build", name="release dir",
            status=Status.FAIL,
            message=f"missing: {ctx.release_dir}",
        )
    if not ctx.release_dir.is_dir():
        return VerificationResult(
            category="build", name="release dir",
            status=Status.FAIL,
            message=f"not a directory: {ctx.release_dir}",
        )
    subdirs = [p for p in ctx.release_dir.iterdir() if p.is_dir()]
    if not subdirs:
        return VerificationResult(
            category="build", name="release dir",
            status=Status.FAIL,
            message=f"{ctx.release_dir} is empty",
        )
    return VerificationResult(
        category="build", name="release dir",
        status=Status.PASS,
        message=f"{ctx.release_dir} has {len(subdirs)} entries",
    )


def _check_build_report(ctx: VerifierContext) -> VerificationResult:
    """The build report exists and contains the expected sections."""
    candidates = [
        ctx.report_dir / "build-report.md",
        ctx.release_dir / "reports" / "build-report.md",
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = read_text_file(path)
        if not text:
            return VerificationResult(
                category="build", name="build report",
                status=Status.FAIL,
                message=f"unreadable: {path}",
                artifacts=[str(path)],
            )
        required = ("# ", "## Tooling", "## Artifacts")
        missing = [s for s in required if s not in text]
        if missing:
            return VerificationResult(
                category="build", name="build report",
                status=Status.WARN,
                message=f"{path} missing sections: {missing}",
                artifacts=[str(path)],
            )
        return VerificationResult(
            category="build", name="build report",
            status=Status.PASS,
            message=f"parsed {path.name}",
            artifacts=[str(path)],
        )
    return VerificationResult(
        category="build", name="build report",
        status=Status.WARN,
        message="no build-report.md found in expected locations",
    )


def _check_top_level_manifest(ctx: VerifierContext) -> VerificationResult:
    """``release/manifest.json`` parses and has the required keys."""
    path = ctx.release_dir / "manifest.json"
    if not path.exists():
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.FAIL,
            message=f"missing: {path}",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.FAIL,
            message=f"invalid JSON: {exc}",
        )
    if not isinstance(data, dict):
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.FAIL,
            message="top-level value is not an object",
        )
    required = {"product", "version", "apps", "checksums"}
    missing = required - set(data.keys())
    if missing:
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.WARN,
            message=f"manifest is missing keys: {sorted(missing)}",
            details={"missing": sorted(missing)},
        )
    return VerificationResult(
        category="build", name="release manifest",
        status=Status.PASS,
        message=f"version {data.get('version')!r} "
                f"({len(data.get('apps', {}))} apps)",
    )


def run(ctx: VerifierContext, *,
        build_exit_code: int = 0) -> List[VerificationResult]:
    """Run every build-output check."""
    results: List[VerificationResult] = []
    with timer() as elapsed:
        if build_exit_code != 0:
            results.append(VerificationResult(
                category="build", name="build exit code",
                status=Status.FAIL,
                message=f"build exited with {build_exit_code}",
            ))
        else:
            results.append(VerificationResult(
                category="build", name="build exit code",
                status=Status.PASS,
                message="build exited cleanly",
            ))
        results.append(_check_release_dir(ctx))
        results.append(_check_top_level_manifest(ctx))
        results.append(_check_build_report(ctx))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results
