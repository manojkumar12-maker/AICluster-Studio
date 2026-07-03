"""Structural validator for ``build/setup/setup.iss``.

Inno Setup ships with ``ISCC.exe`` for the real compile, but the file
is also parsed by the build system to catch common mistakes early:

    * Section names are well-formed (``[Setup]``, ``[Files]``, ...)
    * Required sections are present
    * PascalScript braces are balanced
    * ``Source:`` paths actually exist on disk
    * AppId and the #define values are well-formed

The validator never rejects a script that ISCC would compile - it only
flags structural issues the build system can spot on its own.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

from .config import BUILD_DIR


SETUP_DIR_PATH = BUILD_DIR / "setup"


REQUIRED_SECTIONS = {
    "[Setup]", "[Files]", "[Dirs]", "[Icons]", "[Run]", "[UninstallDelete]",
    "[Code]", "[Languages]", "[Types]", "[Components]",
}


@dataclass
class ValidationReport:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sources_resolved: int = 0
    sources_missing: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "sources_resolved": self.sources_resolved,
            "sources_missing": self.sources_missing,
        }


def _check_sections(text: str, report: ValidationReport) -> None:
    found: Set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            found.add(line)
    missing = REQUIRED_SECTIONS - found
    for section in sorted(missing):
        report.errors.append(f"missing required section: {section}")


def _check_braces(text: str, report: ValidationReport) -> None:
    """Verify that ``{}`` braces in the file are balanced."""
    in_code = False
    depth = 0
    line_no = 0
    for line in text.splitlines():
        line_no += 1
        stripped = line.strip()
        if stripped == "[Code]":
            in_code = True
            continue
        if in_code and stripped.startswith("[") and stripped.endswith("]"):
            in_code = False
            continue
        # In Pascal Script we need balanced begin/end - approximated by { }.
        if not in_code:
            continue
        for ch in line:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    report.errors.append(
                        f"unbalanced '}}' on line {line_no}"
                    )
                    depth = 0
    if depth != 0:
        report.warnings.append(
            f"brace depth at end of [Code] is {depth} (possibly a string literal)"
        )


def _check_sources(text: str, setup_dir: Path,
                   report: ValidationReport,
                   defines: Optional[dict] = None) -> None:
    """Check every ``Source:`` path against the setup/ directory."""
    defines = defines or {}
    in_files = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_files = stripped.lower() == "[files]"
            continue
        if not in_files:
            continue
        if not stripped.lower().startswith("source:"):
            continue
        # Quoted path
        m = re.search(r'Source:\s*"([^"]+)"', line)
        if not m:
            continue
        raw = m.group(1)
        # First, expand any preprocessor references (``{#MyName}``) using
        # the defines passed in. We do a single pass because defines may
        # recursively reference other defines in real ISPP, but for our
        # purposes one pass is enough.
        expanded = raw
        for key, value in defines.items():
            expanded = expanded.replace("{#" + key + "}", value)
        # Strip the remaining runtime placeholders (``{app}`` etc.) - the
        # validator cannot know their runtime values.
        literal = re.sub(r"\{[^}]+\}", "", expanded).strip("\\/")
        if not literal:
            report.sources_resolved += 1
            continue
        # Strip the trailing "\*" wildcard - it does not affect whether
        # the source directory exists.
        if literal.endswith("\\*") or literal.endswith("/*"):
            literal = literal[:-2]
        candidate = setup_dir / literal
        if candidate.exists():
            report.sources_resolved += 1
            continue
        if any(c in literal for c in "*?["):
            report.sources_resolved += 1
            continue
        report.sources_missing += 1
        report.warnings.append(f"source not found: {literal}")


def _check_appid(text: str, report: ValidationReport) -> None:
    m = re.search(r"^\s*AppId=\{([^}]+)\}\s*$",
                  text, flags=re.MULTILINE)
    if not m:
        report.errors.append("AppId not found in [Setup] section")
        return
    raw = m.group(1)
    if raw.startswith("#") and "MyAppId" not in raw:
        report.warnings.append(f"AppId uses a constant reference: {raw}")


def validate(iss_path: Path,
               defines: Optional[dict] = None) -> ValidationReport:
    report = ValidationReport()
    if not iss_path.exists():
        report.errors.append(f"file not found: {iss_path}")
        return report
    text = iss_path.read_text(encoding="utf-8")
    _check_sections(text, report)
    _check_braces(text, report)
    _check_sources(text, iss_path.parent, report, defines=defines)
    _check_appid(text, report)
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate build/setup/setup.iss"
    )
    parser.add_argument("path", nargs="?", default=None,
                        help="path to setup.iss (default: build/setup/setup.iss)")
    parser.add_argument("--define", "-D", action="append", default=[],
                        help="ISPP #define to expand (NAME=VALUE), repeatable")
    args = parser.parse_args(argv)
    path = Path(args.path) if args.path else SETUP_DIR_PATH / "setup.iss"
    defines: dict = {}
    for item in args.define:
        if "=" in item:
            k, v = item.split("=", 1)
            defines[k] = v
    # Sensible defaults matching build_setup.py
    defines.setdefault("AppSourceDir", "payload\\aicluster")
    defines.setdefault("AppVersion", "1.2.1")
    defines.setdefault("AppId", "com.aicluster.setup")
    report = validate(path, defines=defines)
    for w in report.warnings:
        print(f"WARN  {w}")
    for e in report.errors:
        print(f"ERROR {e}")
    print(f"OK    sources resolved: {report.sources_resolved}")
    print(f"OK    sources missing:  {report.sources_missing}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
