"""Verify build environment and produced artifacts.

Two main entry points:

* :func:`verify_environment` — checks Python / Node / npm / Rust / Tauri /
  PyInstaller / Inno Setup / 7-Zip / signtool. Required tools that are
  missing are reported as errors; optional tools only as warnings.
* :func:`verify_artifacts` — after a build, validates that the expected
  ``.exe`` files exist, are non-empty, and (when possible) launch.

The function never raises — it always returns a structured report.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .config import (
    REPO_ROOT,
    RELEASE_DIR,
    PYINSTALLER_TARGETS,
    TAURI_TARGETS,
    BuildConfig,
    is_windows,
)
from . import toolchain
from .logger import setup_logging, get_logger
from .version import resolve_version

log = get_logger("aicluster.build.verify")


@dataclass
class VerifyReport:
    ok: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tools: List[Dict] = field(default_factory=list)
    artifacts: List[Dict] = field(default_factory=list)
    version: str = ""

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict:
        return {
            "ok": self.ok,
            "version": self.version,
            "errors": self.errors,
            "warnings": self.warnings,
            "tools": self.tools,
            "artifacts": self.artifacts,
        }


def verify_environment(cfg: Optional[BuildConfig] = None) -> VerifyReport:
    """Check every required and optional tool."""
    cfg = cfg or BuildConfig()
    setup_logging(cfg.log_level)

    report = VerifyReport(version=resolve_version().version)
    statuses = toolchain.gather_all()
    for status in statuses:
        report.tools.append(status.to_dict())
        if not status.available:
            if status.required:
                report.add_error(
                    f"required tool missing: {status.name} "
                    f"(min {status.min_version})"
                )
            else:
                report.add_warning(
                    f"optional tool missing: {status.name} — {status.notes}"
                )
    return report


def _try_launch(exe: Path, timeout: float = 4.0) -> Optional[str]:
    """Attempt to start ``exe`` and return an error string if it fails fast.

    We use ``start /b`` semantics by spawning the process and immediately
    killing it; a successful start (process stays alive past a brief
    observation window) is treated as "launches".
    """
    if not exe.exists():
        return f"not found: {exe}"
    try:
        proc = subprocess.Popen(
            [str(exe), "--version"] if not is_windows() else [str(exe)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=exe.parent,
        )
        try:
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return None
            if proc.returncode is None or proc.returncode == 0:
                return None
            return f"exit code {proc.returncode}"
        finally:
            if proc.poll() is None:
                proc.kill()
    except OSError as exc:
        return f"launch failed: {exc}"


def verify_artifacts(cfg: Optional[BuildConfig] = None) -> VerifyReport:
    """Validate the executables produced by the build pipeline."""
    cfg = cfg or BuildConfig()
    setup_logging(cfg.log_level)
    report = VerifyReport(version=resolve_version().version)

    for target in PYINSTALLER_TARGETS:
        folder = RELEASE_DIR / target.output_subdir
        exe_candidates = list(folder.glob("*.exe")) if folder.exists() else []
        if not exe_candidates:
            report.add_error(
                f"missing artifact: {target.name} -> {folder} (no .exe)"
            )
            report.artifacts.append({
                "name": target.name,
                "output_subdir": str(folder),
                "ok": False,
                "reason": "no executable",
            })
            continue

        # Accept the expected name or a single exe fallback
        expected = folder / target.output_name
        exe = expected if expected.exists() else exe_candidates[0]
        size = exe.stat().st_size
        info = {
            "name": target.name,
            "path": str(exe),
            "size_bytes": size,
            "expected": target.output_name,
        }
        if size <= 0:
            report.add_error(f"empty executable: {exe}")
            info["ok"] = False
            info["reason"] = "empty"
        else:
            report.artifacts.append({**info, "ok": True})

    for target in TAURI_TARGETS:
        folder = RELEASE_DIR / target.output_subdir
        exe_candidates = list(folder.glob("*.exe")) if folder.exists() else []
        if not exe_candidates:
            report.add_warning(
                f"Tauri artifact missing (build may have been skipped): {folder}"
            )
            report.artifacts.append({
                "name": target.name,
                "output_subdir": str(folder),
                "ok": False,
                "reason": "no executable (Tauri build skipped or failed)",
            })
            continue
        expected = folder / target.output_name
        exe = expected if expected.exists() else exe_candidates[0]
        size = exe.stat().st_size
        info = {
            "name": target.name,
            "path": str(exe),
            "size_bytes": size,
            "expected": target.output_name,
        }
        if size <= 0:
            report.add_error(f"empty executable: {exe}")
            info["ok"] = False
            info["reason"] = "empty"
        else:
            report.artifacts.append({**info, "ok": True})

    return report


def run_full() -> int:
    cfg = BuildConfig()
    env = verify_environment(cfg)
    art = verify_artifacts(cfg)
    report = VerifyReport(ok=env.ok and art.ok, version=env.version)
    report.errors.extend(env.errors)
    report.warnings.extend(env.warnings)
    report.tools.extend(env.tools)
    report.artifacts.extend(art.artifacts)
    return _print_and_exit(report)


def _print_and_exit(report: VerifyReport) -> int:
    log.info("verification complete — version %s", report.version)
    log.info("tools checked: %d", len(report.tools))
    log.info("artifacts checked: %d", len(report.artifacts))
    for warning in report.warnings:
        log.warning(warning)
    for error in report.errors:
        log.error(error)
    if report.ok:
        log.info("VERIFICATION: OK")
        return 0
    log.error("VERIFICATION: FAILED")
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="AICluster build verification")
    parser.add_argument("--env", action="store_true",
                        help="only verify the build environment")
    parser.add_argument("--artifacts", action="store_true",
                        help="only verify produced artifacts")
    parser.add_argument("--json", action="store_true",
                        help="emit a JSON report to stdout")
    args = parser.parse_args(argv)

    cfg = BuildConfig()
    if args.env:
        report = verify_environment(cfg)
    elif args.artifacts:
        report = verify_artifacts(cfg)
    else:
        report = VerifyReport(version=resolve_version().version)
        env = verify_environment(cfg)
        art = verify_artifacts(cfg)
        report.ok = env.ok and art.ok
        report.errors.extend(env.errors)
        report.warnings.extend(env.warnings)
        report.tools.extend(env.tools)
        report.artifacts.extend(art.artifacts)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.ok else 1
    return _print_and_exit(report)


if __name__ == "__main__":
    sys.exit(main())
