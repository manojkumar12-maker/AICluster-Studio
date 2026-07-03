"""Top-level orchestrator for the release verification pipeline.

Calling :func:`verify_all` runs every individual verifier in the
correct order and returns an aggregated :class:`VerificationReport`.

The orchestrator is **read-only** with respect to every artifact it
inspects. The only files it writes are:

    * ``logs/verification.log``            rotating log file
    * ``release/reports/verification-report.md``  the report
    * ``release/reports/verification-report.json`` machine-readable copy
    * ``release/RELEASE_SUMMARY.md``       top-level release summary
    * ``release/BUILD_SUMMARY.md``         top-level build summary

Order of execution (matches the spec):

    1. Build presence / manifest            (verify_build)
    2. Required executables                 (verify_executables)
    3. Artifact folder layout               (verify_artifacts)
    4. Configuration files                  (verify_config)
    5. Python runtime                       (verify_python)
    6. Frontends                            (verify_frontend)
    7. Checksums                            (verify_checksums)
    8. Installer                            (verify_installer)
    9. Backend (Master + Worker)            (verify_backend)
   10. API endpoints (live HTTP)            (verify_api)

Any FAIL anywhere aborts the verification with exit code 1.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import (
    verify_artifacts,
    verify_backend,
    verify_build,
    verify_checksums,
    verify_config,
    verify_executables,
    verify_frontend,
    verify_installer,
    verify_python,
    verify_api,
    verify_report,
)
from .context import REPORT_DIR, RELEASE_DIR, VerifierContext
from .utils import get_logger, timer

log = get_logger("verify")


def verify_all(*,
              ctx: Optional[VerifierContext] = None,
              build_exit_code: int = 0) -> verify_report.VerificationReport:
    """Run every verifier in order and return the aggregated report."""
    ctx = ctx or VerifierContext()
    started = time.monotonic()
    now = datetime.now()
    build_number = os.environ.get(
        "AICLUSTER_BUILD_NUMBER",
        now.strftime("%Y%m%d.%H%M%S"),
    )

    report = verify_report.VerificationReport(
        version=ctx.version or os.environ.get("AICLUSTER_VERSION", "1.2.3"),
        build_number=build_number,
        build_date=now.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=0.0,
    )

    stages = [
        ("build",       verify_build.run),
        ("executables", verify_executables.run),
        ("artifacts",   verify_artifacts.run),
        ("config",      verify_config.run),
        ("python",      verify_python.run),
        ("frontend",    verify_frontend.run),
        ("checksums",   verify_checksums.run),
        ("installer",   verify_installer.run),
        ("backend",     verify_backend.run),
        ("api",         verify_api.run),
    ]
    for label, fn in stages:
        log.info("=== stage: %s ===", label)
        with timer() as elapsed:
            try:
                if label in ("executables", "artifacts"):
                    results = fn(ctx, report)
                else:
                    results = fn(ctx)
            except Exception as exc:
                log.exception("stage %s crashed: %s", label, exc)
                results = [verify_report.VerificationResult(
                    category=label,
                    name="exception",
                    status=verify_report.Status.FAIL,
                    message=f"{type(exc).__name__}: {exc}",
                )]
        for r in results:
            r.duration_seconds = (r.duration_seconds or 0.0) + elapsed() / max(1, len(results))
            report.add(r)

    report.duration_seconds = time.monotonic() - started

    # Write outputs
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORT_DIR / "verification-report.md"
    json_path = REPORT_DIR / "verification-report.json"
    report.write_markdown(md_path)
    report.write_json(json_path)
    summary = ctx.release_dir / "RELEASE_SUMMARY.md"
    build_summary = ctx.release_dir / "BUILD_SUMMARY.md"
    if summary.parent.exists() or summary.parent == ctx.release_dir:
        report.write_release_summary(summary)
        report.write_build_summary(build_summary)

    log.info("verification complete: overall=%s, results=%d",
             report.overall.value, len(report.results))
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AICluster release verification"
    )
    parser.add_argument("--release-dir", type=Path, default=None,
                        help="path to release/ (default: ./release)")
    parser.add_argument("--dist-dir", type=Path, default=None,
                        help="path to dist/ (default: ./dist)")
    parser.add_argument("--artifacts-dir", type=Path, default=None,
                        help="path to artifacts/ (default: ./artifacts)")
    parser.add_argument("--report-dir", type=Path, default=None,
                        help="directory for verification-report.md")
    parser.add_argument("--version", default=None,
                        help="override product version")
    parser.add_argument("--build-number", default=None,
                        help="override build number")
    parser.add_argument("--skip-run", action="store_true",
                        help="skip launching any executable")
    parser.add_argument("--api-port", type=int, default=None,
                        help="override the master API port")
    parser.add_argument("--json", action="store_true",
                        help="emit a JSON summary to stdout")
    parser.add_argument("--build-exit-code", type=int, default=0,
                        help="exit code of the preceding build command")
    args = parser.parse_args(argv)

    overrides: dict = {}
    if args.release_dir:
        overrides["release_dir"] = args.release_dir
    if args.dist_dir:
        overrides["dist_dir"] = args.dist_dir
    if args.artifacts_dir:
        overrides["artifacts_dir"] = args.artifacts_dir
    if args.report_dir:
        overrides["report_dir"] = args.report_dir
    if args.skip_run:
        overrides["skip_launch"] = True
    if args.api_port:
        overrides["api_port"] = args.api_port

    ctx = VerifierContext(**overrides)
    if args.version:
        ctx.version = args.version
    if args.build_number:
        os.environ["AICLUSTER_BUILD_NUMBER"] = args.build_number
    report = verify_all(ctx=ctx, build_exit_code=args.build_exit_code)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.overall != verify_report.Status.FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
