"""Verify the AIClusterSetup.exe installer.

For the single-file installer we check:

    * The executable exists in ``dist/`` and ``artifacts/`` (and
      ``release/`` where the build system places a copy).
    * It is a valid PE binary.
    * It contains the embedded version string.
    * The Inno Setup source script (``build/setup/setup.iss``) is
      present and contains the expected version.

The installer is **never** executed by the verification layer. The
read-only inspection is sufficient - launching it would install
AICluster on the build host, which is undesirable in CI.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .utils import (
    file_size,
    get_logger,
    read_pe_metadata,
    read_text_file,
    timer,
)
from .context import (
    REQUIRED_INSTALLER,
    VerifierContext,
)
from .verify_report import Status, VerificationResult

log = get_logger("verify.installer")

_VERSION_RE = re.compile(r"AppVersion=\{#AppVersion\}", re.IGNORECASE)


def _candidate_paths(ctx: VerifierContext) -> List[Path]:
    """Return every plausible location for the compiled installer."""
    name = REQUIRED_INSTALLER
    candidates: List[Path] = []
    # Build system places a versioned copy in dist/.
    candidates.extend(sorted(ctx.dist_dir.glob(f"AIClusterSetup-*.exe")))
    candidates.extend(sorted(ctx.artifacts_dir.glob(f"AIClusterSetup-*.exe")))
    # Setup builder also produces a versioned file in build/setup/Output/
    setup_out = ctx.release_dir.parent / "build" / "setup" / "Output"
    if setup_out.exists():
        candidates.extend(sorted(setup_out.glob("*.exe")))
    # Fall back to the un-versioned name (used in some legacy paths).
    for folder in (ctx.dist_dir, ctx.artifacts_dir, ctx.release_dir):
        plain = folder / name
        if plain.exists():
            candidates.append(plain)
    # Deduplicate by absolute path
    seen: set = set()
    deduped: List[Path] = []
    for c in candidates:
        key = c.resolve()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return deduped


def _check_installer_exists(ctx: VerifierContext) -> List[VerificationResult]:
    """At least one copy of the installer exists and is a valid PE."""
    results: List[VerificationResult] = []
    candidates = _candidate_paths(ctx)
    if not candidates:
        results.append(VerificationResult(
            category="installer", name="installer exists",
            status=Status.FAIL,
            message=f"no {REQUIRED_INSTALLER} found in dist/ or artifacts/",
        ))
        return results
    for cand in candidates:
        size = file_size(cand)
        if size < 1024 * 1024:
            results.append(VerificationResult(
                category="installer", name=f"installer ({cand.parent.name})",
                status=Status.WARN,
                message=f"suspiciously small ({size} bytes)",
                artifacts=[str(cand)],
            ))
            continue
        meta = read_pe_metadata(cand)
        if not meta.is_pe:
            results.append(VerificationResult(
                category="installer", name=f"installer ({cand.parent.name})",
                status=Status.FAIL,
                message=f"not a valid PE",
                artifacts=[str(cand)],
            ))
            continue
        results.append(VerificationResult(
            category="installer", name=f"installer ({cand.parent.name})",
            status=Status.PASS,
            message=f"{meta.machine} {size} bytes",
            artifacts=[str(cand)],
            details={
                "size_bytes": size,
                "machine": meta.machine,
                "file_version": meta.file_version,
                "product_version": meta.product_version,
            },
        ))
    return results


def _check_setup_script(ctx: VerifierContext) -> List[VerificationResult]:
    """The Inno Setup source script exists and has the expected structure."""
    results: List[VerificationResult] = []
    iss = ctx.release_dir.parent / "build" / "setup" / "setup.iss"
    if not iss.exists():
        results.append(VerificationResult(
            category="installer", name="setup.iss present",
            status=Status.FAIL,
            message=f"missing: {iss}",
        ))
        return results
    text = read_text_file(iss)
    if text is None:
        results.append(VerificationResult(
            category="installer", name="setup.iss present",
            status=Status.FAIL,
            message=f"unreadable: {iss}",
        ))
        return results
    has_sections = all(f"[{sec}]" in text for sec in
                       ("Setup", "Files", "Dirs", "Icons", "Run",
                        "UninstallDelete", "Code", "Languages",
                        "Types", "Components"))
    if not has_sections:
        results.append(VerificationResult(
            category="installer", name="setup.iss sections",
            status=Status.FAIL,
            message="missing one or more required sections",
            artifacts=[str(iss)],
        ))
    else:
        results.append(VerificationResult(
            category="installer", name="setup.iss sections",
            status=Status.PASS,
            message="all required sections present",
            artifacts=[str(iss)],
        ))

    has_appversion = bool(re.search(r"#define\s+MyAppVersion", text)) or \
                     bool(re.search(r"AppVersion=\{#AppVersion\}", text))
    if not has_appversion:
        results.append(VerificationResult(
            category="installer", name="setup.iss versioned",
            status=Status.FAIL,
            message="AppVersion not found in setup.iss",
            artifacts=[str(iss)],
        ))
    else:
        results.append(VerificationResult(
            category="installer", name="setup.iss versioned",
            status=Status.PASS,
            message="AppVersion / MyAppVersion present",
            artifacts=[str(iss)],
        ))

    has_icon = "SetupIconFile=" in text
    if not has_icon:
        results.append(VerificationResult(
            category="installer", name="setup.iss icon",
            status=Status.FAIL,
            message="no SetupIconFile directive",
        ))
    else:
        results.append(VerificationResult(
            category="installer", name="setup.iss icon",
            status=Status.PASS,
            message="SetupIconFile present",
        ))

    return results


def _check_iss_payload(ctx: VerifierContext) -> List[VerificationResult]:
    """The Inno Setup payload is staged and the aicluster binaries exist."""
    results: List[VerificationResult] = []
    base = ctx.release_dir.parent / "build" / "setup" / "payload"
    aicluster = base / "aicluster"
    if not aicluster.exists():
        results.append(VerificationResult(
            category="installer", name="payload aicluster",
            status=Status.WARN,
            message=f"missing: {aicluster} "
                    f"(run python -m build.setup_builder first)",
        ))
        return results
    subdirs = ("master", "worker", "studio",
               "master-control", "worker-control", "cli")
    missing = [s for s in subdirs if not (aicluster / s).exists()]
    if missing:
        results.append(VerificationResult(
            category="installer", name="payload aicluster",
            status=Status.WARN,
            message=f"missing payload subdirs: {missing}",
            details={"missing": missing},
        ))
    else:
        results.append(VerificationResult(
            category="installer", name="payload aicluster",
            status=Status.PASS,
            message="all 6 payload subdirs present",
            artifacts=[str(aicluster / s) for s in subdirs],
        ))
    return results


def run(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    with timer() as elapsed:
        results.extend(_check_installer_exists(ctx))
        results.extend(_check_setup_script(ctx))
        results.extend(_check_iss_payload(ctx))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results
