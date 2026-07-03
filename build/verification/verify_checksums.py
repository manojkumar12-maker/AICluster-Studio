"""Verify the ``release/checksums/`` outputs.

Regenerates SHA-256 hashes for every file under ``release/`` and
compares them against ``release/checksums/checksums.txt`` and
``release/checksums/manifest.json``. Any mismatch is a FAIL.

The verification is read-only - the regenerated hashes are computed
in memory and never written to disk.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

from .utils import get_logger, timer
from .context import VerifierContext
from .verify_report import Status, VerificationResult

log = get_logger("verify.checksums")

CHUNK = 1024 * 1024


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _walk_release(release: Path) -> Dict[str, str]:
    """Return ``{relpath: sha256}`` for every file under ``release/``."""
    out: Dict[str, str] = {}
    for p in sorted(release.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(release).as_posix()
        try:
            out[rel] = _hash_file(p)
        except OSError as exc:
            log.warning("could not hash %s: %s", p, exc)
    return out


def _parse_checksums_txt(path: Path) -> Dict[str, str]:
    """Parse a ``sha256sum`` style file. Lines look like::

        <hash>  <filename>

    Returns ``{filename: hash}``.
    """
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, name = parts
        out[name.strip()] = digest.strip()
    return out


def _parse_manifest_json(path: Path) -> Dict[str, str]:
    """Parse ``release/checksums/manifest.json`` and return ``{path: sha256}``."""
    if not path.exists():
        return {}
    import json
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    out: Dict[str, str] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        p = entry.get("path")
        digest = entry.get("sha256")
        if isinstance(p, str) and isinstance(digest, str):
            try:
                rel = Path(p).relative_to(".").as_posix()
            except ValueError:
                rel = p
            out[rel] = digest
    return out


def run(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    release = ctx.release_dir
    with timer() as elapsed:
        actual = _walk_release(release)
        result = VerificationResult(
            category="checksums", name="regenerated sha-256",
            status=Status.PASS,
            message=f"hashed {len(actual)} files",
            details={"file_count": len(actual)},
        )
        results.append(result)

        # 1. checksums.txt
        txt_path = release / "checksums" / "checksums.txt"
        txt = _parse_checksums_txt(txt_path)
        if not txt:
            results.append(VerificationResult(
                category="checksums", name="checksums.txt present",
                status=Status.FAIL,
                message=f"missing or empty: {txt_path}",
            ))
        else:
            mismatches: List[Tuple[str, str, str]] = []
            missing: List[str] = []
            for name, expected in txt.items():
                if name not in actual:
                    missing.append(name)
                elif actual[name] != expected:
                    mismatches.append((name, expected, actual[name]))
            if mismatches or missing:
                results.append(VerificationResult(
                    category="checksums", name="checksums.txt matches",
                    status=Status.FAIL,
                    message=f"{len(mismatches)} mismatches, "
                            f"{len(missing)} missing",
                    details={
                        "mismatches": mismatches[:10],
                        "missing": missing[:10],
                    },
                ))
            else:
                results.append(VerificationResult(
                    category="checksums", name="checksums.txt matches",
                    status=Status.PASS,
                    message=f"all {len(txt)} hashes match",
                ))

        # 2. manifest.json
        manifest_path = release / "checksums" / "manifest.json"
        manifest = _parse_manifest_json(manifest_path)
        if not manifest:
            results.append(VerificationResult(
                category="checksums", name="manifest.json present",
                status=Status.FAIL,
                message=f"missing or empty: {manifest_path}",
            ))
        else:
            mismatches = []
            missing = []
            for name, expected in manifest.items():
                if name not in actual:
                    missing.append(name)
                elif actual[name] != expected:
                    mismatches.append((name, expected, actual[name]))
            if mismatches or missing:
                results.append(VerificationResult(
                    category="checksums", name="manifest.json matches",
                    status=Status.FAIL,
                    message=f"{len(mismatches)} mismatches, "
                            f"{len(missing)} missing",
                    details={
                        "mismatches": mismatches[:10],
                        "missing": missing[:10],
                    },
                ))
            else:
                results.append(VerificationResult(
                    category="checksums", name="manifest.json matches",
                    status=Status.PASS,
                    message=f"all {len(manifest)} hashes match",
                ))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results
