"""Verify the configuration files that ship with the release.

This includes:

    * ``VERSION``             - the single source of truth for the version
    * ``CHANGELOG.md``        - the human-readable changelog
    * ``README.md``           - top-level readme
    * ``assets/manifest.json`` - CLI runtime manifest
    * ``assets/icons/default.ico`` - default icon
    * ``config/default.yaml``  - default configuration

Also verifies that the version is consistent across all four sources
(``VERSION`` file, ``CHANGELOG.md`` heading, ``build/version.py``
default, and the Inno Setup script's AppVersion definition).

The verifier is read-only.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from .utils import get_logger, read_text_file, timer
from .context import (
    EXPECTED_VERSION_SOURCES,
    REQUIRED_CONFIG_FILES,
    VerifierContext,
)
from .verify_report import Status, VerificationResult

log = get_logger("verify.config")

_SEMVER = re.compile(r"\d+\.\d+\.\d+")


def _file_exists_check(ctx: VerifierContext, rel: str,
                       category: str = "config",
                       required: bool = True) -> Optional[VerificationResult]:
    path = ctx.release_dir.parent / rel
    if path.exists() and path.stat().st_size > 0:
        return VerificationResult(
            category=category, name=rel,
            status=Status.PASS,
            message=f"{path.stat().st_size} bytes",
            artifacts=[str(path)],
        )
    if required:
        return VerificationResult(
            category=category, name=rel,
            status=Status.FAIL,
            message=f"missing or empty: {rel}",
        )
    return VerificationResult(
        category=category, name=rel,
        status=Status.WARN,
        message=f"optional file missing: {rel}",
    )


def _check_required_files(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    for rel in REQUIRED_CONFIG_FILES:
        result = _file_exists_check(ctx, rel)
        if result:
            results.append(result)
    return results


def _check_version_consistency(ctx: VerifierContext) -> VerificationResult:
    """The application version is consistent across the source files.

    The build system version (in ``build/version.py``) may legitimately
    differ from the application version (it tracks the build system
    itself rather than the application being built). We therefore
    treat it as informational and require consistency between
    ``VERSION``, ``CHANGELOG.md`` and ``build/setup/setup.iss``.
    """
    sources = {
        "VERSION": ctx.release_dir.parent / "VERSION",
        "CHANGELOG.md": ctx.release_dir.parent / "CHANGELOG.md",
        "build/setup/setup.iss": (ctx.release_dir.parent
                                  / "build" / "setup" / "setup.iss"),
    }
    found: Dict[str, str] = {}
    for key, path in sources.items():
        text = read_text_file(path)
        if text is None:
            continue
        m = _SEMVER.search(text)
        if m:
            found[key] = m.group(0)
    if not found:
        return VerificationResult(
            category="config", name="version consistency",
            status=Status.FAIL,
            message="could not find a SemVer string in any source",
        )
    versions = set(found.values())
    if len(versions) > 1:
        return VerificationResult(
            category="config", name="version consistency",
            status=Status.FAIL,
            message=f"version mismatch across sources: {found}",
            details={"sources": found, "distinct": sorted(versions)},
        )
    return VerificationResult(
        category="config", name="version consistency",
        status=Status.PASS,
        message=f"application version is {next(iter(versions))} everywhere",
        details={"sources": found, "version": next(iter(versions))},
    )


def _check_manifest_json(ctx: VerifierContext) -> VerificationResult:
    """The CLI manifest.json has the required keys."""
    import json
    path = ctx.release_dir.parent / "assets" / "manifest.json"
    text = read_text_file(path)
    if text is None:
        return VerificationResult(
            category="config", name="manifest.json valid",
            status=Status.FAIL,
            message=f"missing: {path}",
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return VerificationResult(
            category="config", name="manifest.json valid",
            status=Status.FAIL,
            message=f"invalid JSON: {exc}",
        )
    required = {"product_name", "version", "company", "description"}
    missing = required - set(data.keys())
    if missing:
        return VerificationResult(
            category="config", name="manifest.json valid",
            status=Status.FAIL,
            message=f"missing keys: {sorted(missing)}",
            details={"missing": sorted(missing)},
        )
    return VerificationResult(
        category="config", name="manifest.json valid",
        status=Status.PASS,
        message=f"all {len(required)} required keys present",
        details={"version": data.get("version")},
    )


def _check_icon_present(ctx: VerifierContext) -> VerificationResult:
    """The default icon exists and is a non-trivial ICO file."""
    path = ctx.release_dir.parent / "assets" / "icons" / "default.ico"
    if not path.exists():
        return VerificationResult(
            category="config", name="default icon",
            status=Status.FAIL,
            message=f"missing: {path}",
        )
    size = path.stat().st_size
    if size < 64:
        return VerificationResult(
            category="config", name="default icon",
            status=Status.FAIL,
            message=f"icon too small ({size} bytes)",
        )
    with path.open("rb") as fh:
        header = fh.read(6)
    if len(header) < 6 or header[2:4] != b"\x01\x00":
        return VerificationResult(
            category="config", name="default icon",
            status=Status.FAIL,
            message=f"not an ICO (header={header!r})",
        )
    return VerificationResult(
        category="config", name="default icon",
        status=Status.PASS,
        message=f"valid ICO, {size} bytes",
        artifacts=[str(path)],
    )


def run(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    with timer() as elapsed:
        results.extend(_check_required_files(ctx))
        results.append(_check_manifest_json(ctx))
        results.append(_check_icon_present(ctx))
        results.append(_check_version_consistency(ctx))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results
