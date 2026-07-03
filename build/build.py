"""AICluster master build orchestrator.

Running this module produces every distributable artifact:

    1. Verify the build environment (Python / Node / npm / Rust / Tauri /
       PyInstaller / Inno Setup / 7-Zip / signtool).
    2. Clean previous outputs (configurable).
    3. Build every web frontend with ``npm run build``.
    4. Build every PyInstaller target (master, worker, CLI).
    5. Build every Tauri target (master-control, worker-control, studio).
    6. Sign executables when a code-signing certificate is configured.
    7. Generate per-app ZIPs, checksums, and the release manifest.
    8. Generate Inno Setup and NSIS installer scripts (and compile them
       if a compiler is available).
    9. Emit a Markdown build report and ``RELEASE_NOTES.md``.
   10. Verify the produced artifacts.

Usage::

    python -m build.build            # full build
    python -m build.build --clean    # wipe release/ first
    python -m build.build --verify-only
    python -m build.build --skip-tauri
    python -m build.build --skip-installer
    python -m build.build --sign
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from . import clean as clean_module
from . import frontend as frontend_module
from . import package as package_module
from . import pyinstaller_builder
from . import release as release_module
from . import sign as sign_module
from . import tauri_builder
from . import verify as verify_module
from .config import BuildConfig, ICONS_DIR, RELEASE_DIR
from .logger import setup_logging, get_logger
from .modules.make_default_icon import make_icon
from .version import resolve_version

log = get_logger("aicluster.build")


def _ensure_default_icon() -> None:
    """Generate ``default.ico`` when the user has not supplied one.

    The other icon files (master, worker, …) are optional. When
    missing, the build falls back to this default.
    """
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    default = ICONS_DIR / "default.ico"
    if not default.exists():
        default.write_bytes(make_icon())
        log.info("generated default icon: %s", default)


def _step(name: str) -> None:
    log.info("=" * 70)
    log.info("STEP: %s", name)
    log.info("=" * 70)


def _is_real_pe(path: Path) -> bool:
    """Return True if ``path`` is a valid Windows PE binary."""
    if not path.exists() or path.stat().st_size < 1024:
        return False
    try:
        with path.open("rb") as fh:
            if fh.read(2) != b"MZ":
                return False
            fh.seek(0x3C)
            pe_offset_bytes = fh.read(4)
            if len(pe_offset_bytes) != 4:
                return False
            import struct
            pe_offset = struct.unpack("<I", pe_offset_bytes)[0]
            fh.seek(pe_offset)
            return fh.read(4) == b"PE\x00\x00"
    except OSError:
        return False


def _verify_executables_gate() -> list:
    """Verify every required EXE exists, is non-empty and is a real PE.

    Returns a list of dicts with ``name``, ``path``, ``status`` (PASS /
    FAIL / WARN) and ``message``. Used as a hard gate before the
    installer is built: any FAIL is propagated to the build's error
    list, which short-circuits the rest of the pipeline.
    """
    results: list = []
    release = Path(RELEASE_DIR)
    required = [
        ("master", "AIClusterMaster.exe"),
        ("worker", "AIClusterWorker.exe"),
        ("studio", "AIClusterStudio.exe"),
        ("master-control", "MasterControlCenter.exe"),
        ("worker-control", "WorkerControlCenter.exe"),
        ("cli", "aicluster.exe"),
    ]
    for sub, name in required:
        path = release / sub / name
        if not path.exists():
            results.append({
                "name": f"release/{sub}/{name}",
                "path": str(path),
                "status": "FAIL",
                "message": "required executable is missing",
            })
            continue
        if not _is_real_pe(path):
            results.append({
                "name": f"release/{sub}/{name}",
                "path": str(path),
                "status": "FAIL",
                "message": "file is not a valid Windows PE binary "
                           "(placeholder mode has been removed)",
            })
            continue
        results.append({
            "name": f"release/{sub}/{name}",
            "path": str(path),
            "status": "PASS",
            "message": f"{path.stat().st_size:,} bytes, real PE",
        })
    return results


def _sign_each(results: Dict[str, dict], cfg: BuildConfig) -> List[str]:
    """Sign every successfully produced artifact. Returns signed paths."""
    if cfg.skip_sign:
        return []
    signed: List[str] = []
    for _, info in results.items():
        if not info.get("ok") or not info.get("path"):
            continue
        res = sign_module.sign_file(Path(info["path"]), cfg)
        if res.signed:
            signed.append(str(res.file))
    return signed


def run(cfg: Optional[BuildConfig] = None,
        *,
        clean: bool = False,
        skip_verify: bool = False,
        verify_only: bool = False,
        skip_frontend: bool = False,
        skip_pyinstaller: bool = False,
        skip_tauri: bool = False,
        skip_package: bool = False,
        skip_release: bool = False,
        skip_setup: bool = False,
        skip_release_verify: bool = False) -> int:
    cfg = cfg or BuildConfig()
    setup_logging(cfg.log_level)
    version = resolve_version()
    log.info("AICluster v%s — production build starting", version.version)

    _ensure_default_icon()

    start = time.monotonic()
    warnings: List[str] = []
    errors: List[str] = []
    pyinstaller_results: Dict[str, dict] = {}
    tauri_results: Dict[str, dict] = {}

    # 1) Environment
    if not skip_verify:
        _step("Verify environment")
        env_report = verify_module.verify_environment(cfg)
        warnings.extend(env_report.warnings)
        errors.extend(env_report.errors)
        if env_report.errors:
            log.error("environment verification failed; aborting build")
            return _finish(start, errors, warnings, signed=[],
                            env_report=env_report.to_dict(),
                            package_report={},
                            rel_report=None)
    else:
        env_report = verify_module.VerifyReport(version=version.version)

    if verify_only:
        return _finish(start, errors, warnings, signed=[],
                        env_report=env_report.to_dict(),
                        package_report={},
                        rel_report=None)

    # 2) Clean
    if clean:
        _step("Clean previous artifacts")
        clean_module.run(include_release=True, include_pyc=False, include_logs=False)

    # 3) Frontend
    if not skip_frontend:
        _step("Build frontends")
        if not frontend_module.build_all(cfg):
            warnings.append("one or more frontend builds failed")
    else:
        log.info("skipping frontend build (--skip-frontend)")

    # 4) PyInstaller
    if not skip_pyinstaller:
        _step("Build PyInstaller targets")
        pyinstaller_results = pyinstaller_builder.build_all(cfg)
        for k, v in pyinstaller_results.items():
            if not v.get("ok"):
                errors.append(
                    f"pyinstaller target failed: {k} - {v.get('error', '')}"
                )
    else:
        log.info("skipping PyInstaller build (--skip-pyinstaller)")

    # 5) Tauri
    if not cfg.skip_tauri:
        _step("Build Tauri targets")
        tauri_results = tauri_builder.build_all(cfg)
        for k, v in tauri_results.items():
            if not v.get("ok"):
                errors.append(
                    f"tauri target failed: {k} - {v.get('error', '')}"
                )
    else:
        log.info("skipping Tauri build (config)")

    # If any binary failed, stop now - the rest of the pipeline
    # depends on having real executables in release/.
    if errors:
        log.error("binary build failed; aborting before packaging")
        return _finish(start, errors, warnings, signed=[],
                       env_report=env_report.to_dict(),
                       package_report={},
                       rel_report=None)

    # 6) Sign
    _step("Sign executables")
    signed = _sign_each(pyinstaller_results, cfg) + _sign_each(tauri_results, cfg)

    # 7) Pre-installer gate: verify every required executable is a
    # real Windows PE binary. If any is missing or not a real PE
    # (placeholder, text blob, etc.), the installer must not be
    # built - it would otherwise ship a broken installer.
    _step("Pre-installer gate")
    pre_gate = _verify_executables_gate()
    for r in pre_gate:
        if r["status"] == "FAIL":
            errors.append(
                f"pre-installer gate failed: {r['name']} - {r['message']}"
            )
        elif r["status"] == "WARN":
            warnings.append(
                f"pre-installer gate warning: {r['name']} - {r['message']}"
            )
    if errors:
        log.error("pre-installer gate failed; aborting before installer build")
        return _finish(start, errors, warnings, signed=[],
                       env_report=env_report.to_dict(),
                       package_report={},
                       rel_report=None)

    # 8) Package
    _step("Package release")
    if not skip_package:
        package_report = package_module.package_all(cfg)
    else:
        package_report = package_module.PackageReport(version=version.version)

    # 9) Installers + release notes + build report
    _step("Generate installers and release notes")
    rel_report = None
    if not skip_release:
        rel_report = release_module.release(
            env_report=env_report.to_dict(),
            artifacts={"pyinstaller": pyinstaller_results,
                       "tauri": tauri_results},
            package_report=package_report.to_dict(),
            duration_seconds=time.monotonic() - start,
            signed=signed,
            warnings=warnings,
            errors=errors,
            cfg=cfg,
        )

    # 8b) AIClusterSetup.exe (single-file wizard installer)
    _step("Build AIClusterSetup.exe")
    if not skip_setup and not skip_release:
        try:
            from . import setup_builder
            setup_rc = setup_builder.build_setup(cfg, skip_compile=False)
            if setup_rc != 0:
                errors.append(
                    f"AIClusterSetup.exe was not produced "
                    f"(rc={setup_rc}). Install Inno Setup 6 or run with "
                    f"--skip-setup to skip this step."
                )
        except Exception as exc:
            errors.append(f"AIClusterSetup stage failed: {exc}")
    else:
        log.info("skipping AIClusterSetup.exe (config)")

    # 9) Final verification
    _step("Final verification")
    final_verify = verify_module.verify_artifacts(cfg)
    warnings.extend(final_verify.warnings)
    errors.extend(final_verify.errors)

    # 10) Release verification system (strictly additive)
    _step("Release verification")
    if not skip_release and not skip_release_verify:
        try:
            from .verification import verify as verify_pkg
            from .verification.context import VerifierContext
            from .verification.verify_report import Status as VerStatus
            ctx = VerifierContext(version=version.version)
            report = verify_pkg.verify_all(ctx=ctx, build_exit_code=0)
            if report.overall == VerStatus.FAIL:
                errors.append(
                    f"release verification FAILED: "
                    f"{len(report.errors)} check(s) failed - "
                    f"see release/reports/verification-report.md"
                )
            else:
                log.info("release verification: %s (%d checks)",
                         report.overall.value, len(report.results))
        except Exception as exc:
            warnings.append(f"release verification crashed: {exc}")
    else:
        log.info("skipping release verification (--skip-release-verify "
                 "or --skip-release)")

    return _finish(start, errors, warnings, signed=signed,
                    env_report=env_report.to_dict(),
                    package_report=package_report.to_dict(),
                    rel_report=rel_report)


def _finish(start: float,
            errors: List[str],
            warnings: List[str],
            *,
            signed: List[str],
            env_report: dict,
            package_report: dict,
            rel_report) -> int:
    duration = time.monotonic() - start
    log.info("=" * 70)
    log.info("BUILD COMPLETE in %.1f s", duration)
    log.info("WARNINGS: %d", len(warnings))
    log.info("ERRORS:   %d", len(errors))
    log.info("SIGNED:   %d", len(signed))
    for w in warnings:
        log.warning(" - %s", w)
    for e in errors:
        log.error(" - %s", e)
    log.info("release/: %s", package_report.get("release_manifest", "<not generated>"))
    if rel_report and rel_report.build_report:
        log.info("report:   %s", rel_report.build_report)
    return 0 if not errors else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AICluster master build orchestrator",
    )
    parser.add_argument("--clean", action="store_true",
                        help="wipe release/ before building")
    parser.add_argument("--skip-verify", action="store_true",
                        help="skip environment verification")
    parser.add_argument("--verify-only", action="store_true",
                        help="only verify the environment and exit")
    parser.add_argument("--skip-frontend", action="store_true",
                        help="skip building web frontends")
    parser.add_argument("--skip-pyinstaller", action="store_true",
                        help="skip building PyInstaller targets")
    parser.add_argument("--skip-tauri", action="store_true",
                        help="skip building Tauri targets")
    parser.add_argument("--no-launch", action="store_true",
                        help="do not auto-launch AICluster Master after install")
    parser.add_argument("--skip-package", action="store_true",
                        help="skip packaging / checksums / ZIPs")
    parser.add_argument("--skip-release", action="store_true",
                        help="skip installer scripts and release notes")
    parser.add_argument("--skip-installer", action="store_true",
                        help="only generate installer scripts (no compile)")
    parser.add_argument("--skip-zip", action="store_true",
                        help="skip portable ZIP generation")
    parser.add_argument("--skip-setup", action="store_true",
                        help="skip AIClusterSetup.exe (wizard installer)")
    parser.add_argument("--skip-release-verify", action="store_true",
                        help="skip the post-build release verification stage")
    parser.add_argument("--sign", action="store_true",
                        help="enable Authenticode signing")
    args = parser.parse_args(argv)

    cfg = BuildConfig()
    if args.skip_tauri:
        cfg.skip_tauri = True
    if args.skip_installer:
        cfg.skip_installer = True
    if args.skip_zip:
        cfg.skip_zip = True
    if args.no_launch:
        cfg.launch_master = False
    if args.sign:
        cfg.skip_sign = False

    return run(
        cfg,
        clean=args.clean,
        skip_verify=args.skip_verify,
        verify_only=args.verify_only,
        skip_frontend=args.skip_frontend,
        skip_pyinstaller=args.skip_pyinstaller,
        skip_tauri=args.skip_tauri,
        skip_package=args.skip_package,
        skip_release=args.skip_release,
        skip_setup=args.skip_setup,
        skip_release_verify=args.skip_release_verify,
    )


if __name__ == "__main__":
    sys.exit(main())
