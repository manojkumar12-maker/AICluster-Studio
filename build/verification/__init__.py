"""AICluster Release Verification System.

This package is the post-build verification layer for AICluster.
It runs after every successful build and verifies that every
executable, installer and required artifact is valid before a release
is accepted. The verification layer is **strictly additive** - it
never modifies application code, packaging logic, or the artifacts
it inspects.

Public entry points
===================

* :func:`verify_all`   - run every verifier and return a report
* :func:`main`         - CLI entry point
* :data:`REPORT_DIR`   - default location for verification-report.md
"""

from __future__ import annotations

from .context import (
    REPORT_DIR,
    VerifierContext,
)
from .verify_report import (
    Status,
    VerificationReport,
    VerificationResult,
)
from .verify import verify_all, main

__all__ = [
    "REPORT_DIR",
    "Status",
    "VerifierContext",
    "VerificationReport",
    "VerificationResult",
    "main",
    "verify_all",
]
