"""Hash generation utilities.

Computes SHA-256, MD5, and SHA-1 checksums for files and folders. Used by
``package.py`` to populate ``release/checksums/``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


CHUNK = 1024 * 1024  # 1 MiB


@dataclass
class FileDigest:
    path: Path
    size: int
    sha256: str
    md5: str
    sha1: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": str(self.path),
            "size": self.size,
            "sha256": self.sha256,
            "md5": self.md5,
            "sha1": self.sha1,
        }


def _digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def file_digest(path: Path) -> FileDigest:
    return FileDigest(
        path=path,
        size=path.stat().st_size,
        sha256=_digest(path, "sha256"),
        md5=_digest(path, "md5"),
        sha1=_digest(path, "sha1"),
    )


def dir_digests(root: Path, patterns: Optional[Iterable[str]] = None) -> List[FileDigest]:
    """Recursively hash every file under ``root`` matching ``patterns``.

    ``patterns`` may be shell-style globs (e.g. ``*.exe``); when omitted
    every regular file is included.
    """
    import fnmatch

    if not root.exists():
        return []
    out: List[FileDigest] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if patterns:
            if not any(fnmatch.fnmatch(p.name, pat) for pat in patterns):
                continue
        try:
            out.append(file_digest(p))
        except OSError:
            continue
    return out


def write_checksums_txt(digests: Iterable[FileDigest], dest: Path) -> Path:
    """Write a classic ``sha256sum``-style file plus an extended manifest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{d.sha256}  {d.path.name}" for d in digests]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def write_manifest_json(digests: Iterable[FileDigest], dest: Path) -> Path:
    import json

    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = [d.to_dict() for d in digests]
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    digests = dir_digests(target)
    for d in digests:
        print(f"{d.sha256}  {d.path}")
