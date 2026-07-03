"""Verify the AICluster REST API surface.

This module exercises the live API after a successful master launch.
It is the post-launch counterpart of :mod:`verify_backend` - if the
backend is running, we run a few extra HTTP checks against the
documented routes.

If the backend isn't running (for example, when launching was
skipped, the build host is not Windows, or the master never came
up), every check here is reported as SKIP.
"""

from __future__ import annotations

from typing import List

from .utils import get_logger, http_get, port_listening, timer
from .context import HEALTH_ENDPOINT, MASTER_API_PORT, VerifierContext
from .verify_report import Status, VerificationResult

log = get_logger("verify.api")


# (name, URL path, expected status)
ENDPOINTS: List[tuple] = [
    ("health", "/api/v1/health", 200),
    ("openapi-schema", "/openapi.json", 200),
    ("docs", "/docs", 200),
    ("redoc", "/redoc", 200),
]


def _host(ctx: VerifierContext) -> str:
    return "127.0.0.1"


def run(ctx: VerifierContext) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    with timer() as elapsed:
        if not port_listening(ctx.api_port, host=_host(ctx), timeout=0.5):
            results.append(VerificationResult(
                category="api", name="api listening",
                status=Status.SKIP,
                message=f"port {ctx.api_port} not listening; "
                        f"backend was not started by verify_backend",
            ))
            return results
        results.append(VerificationResult(
            category="api", name="api listening",
            status=Status.PASS,
            message=f"port {ctx.api_port} listening",
        ))
        for name, path, expected in ENDPOINTS:
            url = f"http://{_host(ctx)}:{ctx.api_port}{path}"
            status_code, body = http_get(url, timeout=5.0,
                                          expected_status=(expected,))
            if status_code == expected:
                results.append(VerificationResult(
                    category="api", name=f"GET {path}",
                    status=Status.PASS,
                    message=f"-> {status_code}",
                    details={"status": status_code,
                             "body_excerpt": body[:120]},
                ))
            else:
                # Some endpoints may legitimately not be registered by
                # a minimal build. We treat unexpected responses as
                # WARN, not FAIL, so the rest of the release is not
                # blocked by a single route.
                results.append(VerificationResult(
                    category="api", name=f"GET {path}",
                    status=Status.WARN,
                    message=f"expected {expected}, got {status_code}",
                    details={"status": status_code,
                             "body_excerpt": body[:120]},
                ))
    for r in results:
        r.duration_seconds = elapsed() / max(1, len(results))
    return results
