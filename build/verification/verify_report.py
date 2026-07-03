"""Result data classes and report rendering for the verification layer.

Every verifier returns a :class:`VerificationResult` (or a list of
them). The :class:`VerificationReport` aggregates the whole run and
is responsible for writing ``release/reports/verification-report.md``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from .utils import get_logger, short_path

log = get_logger("verify.report")


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"

    @property
    def ok(self) -> bool:
        return self in (Status.PASS, Status.SKIP, Status.WARN)


@dataclass
class VerificationResult:
    """The outcome of a single check."""

    category: str
    name: str
    status: Status
    message: str = ""
    duration_seconds: float = 0.0
    artifacts: List[str] = field(default_factory=list)
    details: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "category": self.category,
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_seconds": round(self.duration_seconds, 3),
            "artifacts": list(self.artifacts),
            "details": dict(self.details),
        }

    @classmethod
    def make(cls, category: str, name: str, status: Status,
             message: str = "", **kwargs) -> "VerificationResult":
        return cls(category=category, name=name, status=status,
                   message=message, **kwargs)


@dataclass
class VerificationReport:
    """Aggregated result of the whole verification run."""

    version: str
    build_number: str
    build_date: str
    duration_seconds: float
    results: List[VerificationResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def overall(self) -> Status:
        if any(r.status == Status.FAIL for r in self.results):
            return Status.FAIL
        if any(r.status == Status.WARN for r in self.results):
            return Status.WARN
        return Status.PASS

    @property
    def artifacts(self) -> List[str]:
        seen: List[str] = []
        for r in self.results:
            for art in r.artifacts:
                if art and art not in seen:
                    seen.append(art)
        return seen

    def add(self, result: VerificationResult) -> None:
        self.results.append(result)
        if result.status == Status.FAIL:
            self.errors.append(f"{result.category}: {result.name}: "
                               f"{result.message}")
        elif result.status == Status.WARN:
            self.warnings.append(f"{result.category}: {result.name}: "
                                 f"{result.message}")
        log.info("[%s] %s/%s: %s",
                 result.status.value, result.category, result.name,
                 result.message or "ok")

    def by_category(self, category: str) -> List[VerificationResult]:
        return [r for r in self.results if r.category == category]

    def category_status(self, category: str) -> Status:
        rows = self.by_category(category)
        if not rows:
            return Status.SKIP
        if any(r.status == Status.FAIL for r in rows):
            return Status.FAIL
        if any(r.status == Status.WARN for r in rows):
            return Status.WARN
        return Status.PASS

    def to_dict(self) -> Dict[str, object]:
        return {
            "version": self.version,
            "build_number": self.build_number,
            "build_date": self.build_date,
            "duration_seconds": round(self.duration_seconds, 3),
            "overall": self.overall.value,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "artifacts": self.artifacts,
            "results": [r.to_dict() for r in self.results],
        }

    def to_markdown(self) -> str:
        lines: List[str] = []
        lines.append(f"# AICluster Release Verification")
        lines.append("")
        lines.append(f"**Version:** {self.version}")
        lines.append(f"**Build Number:** {self.build_number}")
        lines.append(f"**Build Date:** {self.build_date}")
        lines.append(f"**Duration:** {self.duration_seconds:.1f} s")
        lines.append(f"**Overall Status:** {self.overall.value}")
        lines.append("")
        lines.append("-------------------------------------------------------------------------------")
        lines.append("")
        lines.append("## Build")
        lines.append("")
        lines.append(self._status_line("build"))
        lines.append("")
        lines.append("## Executables")
        lines.append("")
        lines.append(self._status_line("executables"))
        lines.append("")
        lines.append("## Installer")
        lines.append("")
        lines.append(self._status_line("installer"))
        lines.append("")
        lines.append("## Backend")
        lines.append("")
        lines.append(self._status_line("backend"))
        lines.append("")
        lines.append("## Worker")
        lines.append("")
        lines.append(self._status_line("worker"))
        lines.append("")
        lines.append("## Studio")
        lines.append("")
        lines.append(self._status_line("studio"))
        lines.append("")
        lines.append("## CLI")
        lines.append("")
        lines.append(self._status_line("cli"))
        lines.append("")
        lines.append("## Checksums")
        lines.append("")
        lines.append(self._status_line("checksums"))
        lines.append("")
        lines.append("## Configuration")
        lines.append("")
        lines.append(self._status_line("config"))
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"- {w}")
        else:
            lines.append("None")
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        if self.errors:
            for e in self.errors:
                lines.append(f"- {e}")
        else:
            lines.append("None")
        lines.append("")
        lines.append("## Artifacts Verified")
        lines.append("")
        if self.artifacts:
            for art in self.artifacts:
                lines.append(f"- `{art}`")
        else:
            lines.append("None")
        lines.append("")
        lines.append("-------------------------------------------------------------------------------")
        lines.append("")
        lines.append("## Per-check details")
        lines.append("")
        for r in self.results:
            lines.append(f"### {r.category} / {r.name}")
            lines.append("")
            lines.append(f"- Status: **{r.status.value}**")
            if r.message:
                lines.append(f"- Message: {r.message}")
            if r.duration_seconds:
                lines.append(f"- Duration: {r.duration_seconds:.3f} s")
            if r.artifacts:
                lines.append(f"- Artifacts:")
                for a in r.artifacts:
                    lines.append(f"  - `{short_path(Path(a))}`")
            if r.details:
                try:
                    rendered = json.dumps(r.details, indent=2,
                                          default=str, sort_keys=True)
                except (TypeError, ValueError):
                    rendered = str(r.details)
                lines.append(f"- Details:")
                lines.append("")
                lines.append("```json")
                lines.append(rendered)
                lines.append("```")
            lines.append("")
        return "\n".join(lines) + "\n"

    def _status_line(self, category: str) -> str:
        status = self.category_status(category)
        rows = self.by_category(category)
        if not rows:
            return f"{status.value} (no checks)"
        summary = ", ".join(f"{r.name}: {r.status.value}" for r in rows)
        return f"{status.value} ({len(rows)} checks: {summary})"

    def write_markdown(self, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(self.to_markdown(), encoding="utf-8")
        log.info("wrote %s", dest)
        return dest

    def write_json(self, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(self.to_dict(), indent=2),
                        encoding="utf-8")
        log.info("wrote %s", dest)
        return dest

    def write_release_summary(self, dest: Path) -> Path:
        """Write a top-level ``RELEASE_SUMMARY.md`` for tagging."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        lines: List[str] = []
        lines.append(f"# AICluster v{self.version} - Release Summary")
        lines.append("")
        lines.append(f"**Build date:** {self.build_date}")
        lines.append(f"**Build number:** {self.build_number}")
        lines.append(f"**Duration:** {self.duration_seconds:.1f} s")
        lines.append(f"**Verification:** {self.overall.value}")
        lines.append("")
        lines.append("## Artifacts")
        lines.append("")
        for art in self.artifacts:
            lines.append(f"- `{art}`")
        lines.append("")
        lines.append("## Status breakdown")
        lines.append("")
        for category in ("build", "executables", "installer", "backend",
                         "worker", "studio", "cli", "checksums", "config"):
            status = self.category_status(category)
            lines.append(f"- **{category}**: {status.value}")
        lines.append("")
        lines.append("## Tag")
        lines.append("")
        lines.append(f"`AICluster v{self.version}`")
        lines.append("")
        lines.append(f"Generated by AICluster Release Verification System v1.2.3")
        lines.append("")
        dest.write_text("\n".join(lines), encoding="utf-8")
        log.info("wrote %s", dest)
        return dest

    def write_build_summary(self, dest: Path) -> Path:
        """Write a ``BUILD_SUMMARY.md`` alongside the build report."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        lines: List[str] = []
        lines.append(f"# AICluster v{self.version} - Build Summary")
        lines.append("")
        lines.append(f"**Build date:** {self.build_date}")
        lines.append(f"**Build number:** {self.build_number}")
        lines.append(f"**Duration:** {self.duration_seconds:.1f} s")
        lines.append(f"**Verification:** {self.overall.value}")
        lines.append("")
        lines.append("## Tag")
        lines.append("")
        lines.append(f"`AICluster v{self.version}`")
        lines.append("")
        lines.append("## Categories")
        lines.append("")
        for category in ("build", "executables", "installer", "backend",
                         "worker", "studio", "cli", "checksums", "config"):
            status = self.category_status(category)
            rows = self.by_category(category)
            lines.append(f"- **{category}**: {status.value} "
                         f"({len(rows)} check(s))")
        lines.append("")
        lines.append("## Verified artifacts")
        lines.append("")
        for art in self.artifacts:
            lines.append(f"- `{art}`")
        lines.append("")
        dest.write_text("\n".join(lines), encoding="utf-8")
        log.info("wrote %s", dest)
        return dest
