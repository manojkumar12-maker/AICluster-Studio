"""Packaging helpers — checksums, manifests, portable ZIPs.

This module operates entirely on the contents of ``release/``. It runs
after the binary builders have finished, and is responsible for
producing:

    * ``release/checksums/checksums.txt``   classic sha256sum file
    * ``release/checksums/manifest.json``   machine-readable manifest
    * ``release/zip/<app>.zip``             portable ZIP per app
    * ``release/manifest.json``             top-level release manifest
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .checksum import (
    FileDigest,
    dir_digests,
    file_digest,
    write_checksums_txt,
    write_manifest_json,
)
from .config import (
    ARTIFACTS_DIR,
    CHECKSUMS_DIR,
    RELEASE_DIR,
    PYINSTALLER_TARGETS,
    TAURI_TARGETS,
    BuildConfig,
    RELEASE_LAYOUT,
)
from .logger import setup_logging, get_logger
from .version import VersionInfo, resolve_version

log = get_logger("aicluster.build.package")


@dataclass
class PackageReport:
    version: str
    apps: Dict[str, dict] = field(default_factory=dict)
    checksums_txt: Optional[Path] = None
    manifest_json: Optional[Path] = None
    release_manifest: Optional[Path] = None
    zips: List[Path] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "apps": self.apps,
            "checksums_txt": str(self.checksums_txt) if self.checksums_txt else None,
            "manifest_json": str(self.manifest_json) if self.manifest_json else None,
            "release_manifest": str(self.release_manifest) if self.release_manifest else None,
            "zips": [str(p) for p in self.zips],
        }


def _make_zip(source_dir: Path, dest_zip: Path) -> Optional[Path]:
    if not source_dir.exists():
        return None
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    if dest_zip.exists():
        dest_zip.unlink()
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for child in sorted(source_dir.rglob("*")):
            if child.is_dir():
                continue
            arc = child.relative_to(source_dir.parent)
            zf.write(child, arcname=str(arc))
    log.info("created zip: %s", dest_zip)
    return dest_zip


def package_all(cfg: Optional[BuildConfig] = None) -> PackageReport:
    cfg = cfg or BuildConfig()
    setup_logging(cfg.log_level)
    version = resolve_version()

    report = PackageReport(version=version.version)
    CHECKSUMS_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    # Build per-app ZIPs and collect per-app digests.
    all_digests: List[FileDigest] = []
    per_app: Dict[str, dict] = {}

    missing_targets: List[str] = []
    for target in list(PYINSTALLER_TARGETS) + list(TAURI_TARGETS):
        subdir = RELEASE_DIR / target.output_subdir
        if not subdir.exists():
            missing_targets.append(f"{target.output_subdir}/")
            continue

        digests = dir_digests(subdir)
        if not digests:
            missing_targets.append(f"{target.output_subdir}/ (empty)")
            continue

        primary = subdir / target.output_name
        if not primary.exists():
            raise RuntimeError(
                f"release/{target.output_subdir}/{target.output_name} is "
                f"missing; the build cannot package a partial release."
            )
        primary_digest = next(
            (d for d in digests if d.path == primary), digests[0]
        )

        zip_name = f"{target.output_name.replace('.exe', '')}_{version.version}.zip"
        zip_path = RELEASE_LAYOUT["zip"] / zip_name
        if not cfg.skip_zip:
            produced = _make_zip(subdir, zip_path)
            if produced:
                report.zips.append(produced)
                all_digests.append(file_digest(produced))
        else:
            log.info("skipping zip (config)")

        per_app[target.key] = {
            "name": target.name,
            "output": target.output_name,
            "subdir": target.output_subdir,
            "primary": {
                "path": str(primary_digest.path),
                "size": primary_digest.size,
                "sha256": primary_digest.sha256,
                "md5": primary_digest.md5,
                "sha1": primary_digest.sha1,
            },
            "files": [d.to_dict() for d in digests],
        }
        all_digests.extend(digests)

    if missing_targets:
        raise RuntimeError(
            "the following release subdirs are missing or empty - "
            "the build cannot package a partial release:\n  "
            + "\n  ".join(missing_targets)
        )

    # Write checksums
    txt = RELEASE_LAYOUT["checksums"] / "checksums.txt"
    write_checksums_txt(all_digests, txt)
    report.checksums_txt = txt
    log.info("wrote %s", txt)

    manifest_path = RELEASE_LAYOUT["checksums"] / "manifest.json"
    write_manifest_json(all_digests, manifest_path)
    report.manifest_json = manifest_path
    log.info("wrote %s", manifest_path)

    # Top-level release manifest
    release_manifest = {
        "product": version.product_name,
        "version": version.version,
        "build_date": version.build_date,
        "company": version.company,
        "copyright": version.copyright,
        "git_tag": version.git_tag,
        "apps": per_app,
        "total_files": len(all_digests),
        "checksums": {
            "txt": str(txt),
            "json": str(manifest_path),
        },
    }
    release_path = RELEASE_DIR / "manifest.json"
    release_path.write_text(json.dumps(release_manifest, indent=2), encoding="utf-8")
    report.release_manifest = release_path
    report.apps = per_app
    log.info("wrote %s", release_path)

    return report


if __name__ == "__main__":
    import sys
    rep = package_all()
    print(json.dumps(rep.to_dict(), indent=2))
    sys.exit(0)
