"""Version discovery and stamping for the AICluster build system.

Resolves the current product version by checking (in order):
    1. ``AICLUSTER_BUILD_VERSION`` environment variable (build override)
    2. ``VERSION`` file at the repository root
    3. Most recent ``## vX.Y.Z`` heading in ``CHANGELOG.md``
    4. Hard-coded default

The same module produces Windows ``FILEVERSION`` / ``PRODUCTVERSION`` tuples
that can be embedded into PyInstaller spec files and Tauri ``tauri.conf.json``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from .config import REPO_ROOT


DEFAULT_VERSION = "1.2.2"
DEFAULT_COMPANY = "AICluster"
DEFAULT_COPYRIGHT = "Copyright (c) 2026 AICluster"
DEFAULT_DESCRIPTION = "AICluster - Offline AI Cluster Management Platform"
DEFAULT_PRODUCT_NAME = "AICluster"
BUILD_SYSTEM_VERSION = "1.2.2"

_CHANGELOG_RE = re.compile(r"^##\s*v?(\d+\.\d+\.\d+)", re.MULTILINE)
_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class VersionInfo:
    """Resolved version metadata used across all build steps."""

    version: str
    major: int
    minor: int
    patch: int
    company: str
    copyright: str
    description: str
    product_name: str
    build_date: str
    git_tag: Optional[str] = None

    @property
    def tuple(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    @property
    def dotted(self) -> str:
        return f"{self.major},{self.minor},{self.patch},{self.patch}"

    def as_windows_version_info(self) -> str:
        """Format the version as a Windows resource block (VS_FIXEDFILEINFO).

        Returns the canonical PyInstaller text-based VSVersionInfo, which
        the loader parses with ``eval()``. We build the structure with
        PyInstaller's own classes so the output is guaranteed to round-trip.
        """
        try:
            from PyInstaller.utils.win32.versioninfo import (
                FixedFileInfo,
                StringFileInfo,
                StringStruct,
                StringTable,
                VarFileInfo,
                VarStruct,
                VSVersionInfo,
            )
        except ImportError as exc:  # pragma: no cover - PyInstaller is required
            raise RuntimeError(
                "PyInstaller is required to embed Windows version info. "
                "Install it with `pip install pyinstaller`."
            ) from exc
        parts = self.version.split(".")
        while len(parts) < 4:
            parts.append("0")
        filevers = tuple(int(p) for p in parts[:4])
        ffi = FixedFileInfo(filevers=filevers, prodvers=filevers)
        strtab = StringTable(
            "040904B0",
            [
                StringStruct("CompanyName", self.company),
                StringStruct("FileDescription", self.description),
                StringStruct("FileVersion", self.version),
                StringStruct("InternalName", self.product_name),
                StringStruct("LegalCopyright", self.copyright),
                StringStruct("OriginalFilename", f"{self.product_name}.exe"),
                StringStruct("ProductName", self.product_name),
                StringStruct("ProductVersion", self.version),
            ],
        )
        info = VSVersionInfo(
            ffi=ffi,
            kids=[
                StringFileInfo([strtab]),
                VarFileInfo([VarStruct("Translation", [1033, 1200])]),
            ],
        )
        return str(info)

def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _parse_semver(text: str) -> Optional[Tuple[int, int, int]]:
    m = _SEMVER_RE.match(text.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _from_changelog() -> Optional[str]:
    text = _read_text(REPO_ROOT / "CHANGELOG.md")
    if not text:
        return None
    m = _CHANGELOG_RE.search(text)
    if not m:
        return None
    return m.group(1)


def _git_tag() -> Optional[str]:
    try:
        import subprocess

        out = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out.lstrip("v") or None
    except Exception:
        return None


def resolve_version() -> VersionInfo:
    """Build a :class:`VersionInfo` using every available source."""
    raw = (
        os.environ.get("AICLUSTER_BUILD_VERSION")
        or _read_text(REPO_ROOT / "VERSION")
        or _from_changelog()
        or DEFAULT_VERSION
    ).strip()

    parsed = _parse_semver(raw) or _parse_semver(DEFAULT_VERSION) or (1, 0, 0)
    major, minor, patch = parsed
    return VersionInfo(
        version=f"{major}.{minor}.{patch}",
        major=major,
        minor=minor,
        patch=patch,
        company=os.environ.get("AICLUSTER_BUILD_COMPANY", DEFAULT_COMPANY),
        copyright=os.environ.get("AICLUSTER_BUILD_COPYRIGHT", DEFAULT_COPYRIGHT),
        description=os.environ.get(
            "AICLUSTER_BUILD_DESCRIPTION", DEFAULT_DESCRIPTION
        ),
        product_name=os.environ.get(
            "AICLUSTER_BUILD_PRODUCT_NAME", DEFAULT_PRODUCT_NAME
        ),
        build_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        git_tag=_git_tag(),
    )


if __name__ == "__main__":
    import json

    v = resolve_version()
    print(json.dumps(v.__dict__, indent=2))
