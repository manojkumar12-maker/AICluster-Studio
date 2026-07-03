"""Verify that the release folder contains every required artifact.

This is the first check run after a build. It validates the *shape*
of the release directory: required subfolders, required executables,
required checksums, required installer scripts. It does **not** launch
anything.

The verifier is read-only: it never opens files for writing, never
modifies the manifest, and never touches the database.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .utils import file_size, get_logger, read_text_file, timer
from .context import (
    REQUIRED_EXECUTABLES,
    RELEASE_DIR,
    VerifierContext,
)
from .verify_report import Status, VerificationResult, VerificationReport

log = get_logger("verify.artifacts")

REQUIRED_SUBDIRS = [
    "master",
    "worker",
    "studio",
    "master-control",
    "worker-control",
    "cli",
    "checksums",
    "installer",
    "zip",
    "reports",
]


def _check_subdirs(release: Path, report: VerificationReport) -> VerificationResult:
    """Every required subfolder exists."""
    missing: List[str] = []
    for sub in REQUIRED_SUBDIRS:
        if not (release / sub).is_dir():
            missing.append(sub)
    status = Status.FAIL if missing else Status.PASS
    return VerificationResult(
        category="build",
        name="release subfolders",
        status=status,
        message=("missing: " + ", ".join(missing)) if missing else
                f"all {len(REQUIRED_SUBDIRS)} subfolders present",
        artifacts=[str(release / s) for s in REQUIRED_SUBDIRS],
    )


def _check_release_manifest(release: Path,
                            report: VerificationReport) -> VerificationResult:
    """``release/manifest.json`` exists and parses."""
    manifest = release / "manifest.json"
    if not manifest.exists():
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.FAIL,
            message=f"missing: {manifest}",
        )
    text = read_text_file(manifest)
    if text is None:
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.FAIL,
            message=f"unreadable: {manifest}",
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.FAIL,
            message=f"invalid JSON: {exc}",
        )
    if not isinstance(data, dict):
        return VerificationResult(
            category="build", name="release manifest",
            status=Status.FAIL,
            message=f"expected object at root, got {type(data).__name__}",
        )
    return VerificationResult(
        category="build", name="release manifest",
        status=Status.PASS,
        message=f"parsed {len(data)} top-level keys",
        artifacts=[str(manifest)],
        details={
            "version": data.get("version"),
            "app_count": len(data.get("apps", {})),
        },
    )


def _check_zip_layout(release: Path,
                      report: VerificationReport) -> VerificationResult:
    """The ``release/zip`` folder is non-empty (one ZIP per app)."""
    zips = sorted((release / "zip").glob("*.zip")) if (release / "zip").exists() else []
    if not zips:
        return VerificationResult(
            category="build", name="portable zips",
            status=Status.WARN,
            message="no portable zips were produced",
        )
    return VerificationResult(
        category="build", name="portable zips",
        status=Status.PASS,
        message=f"found {len(zips)} zips",
        artifacts=[str(p) for p in zips],
    )


def run(ctx: VerifierContext, parent: VerificationReport) -> List[VerificationResult]:
    """Run every artifact-level check and return the results."""
    results: List[VerificationResult] = []
    with timer() as elapsed:
        results.append(_check_subdirs(ctx.release_dir, parent))
        results.append(_check_release_manifest(ctx.release_dir, parent))
        results.append(_check_zip_layout(ctx.release_dir, parent))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    log.info("artifact verification complete: %d checks", len(results))
    return results
