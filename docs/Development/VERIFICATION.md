# AICluster Release Verification System

The verification layer runs **after every successful build** and
confirms that every generated executable, installer and required
artifact is valid before a release is accepted.

This is a **strictly additive** subsystem. It never modifies
application code, the build system, the installer scripts or any
artifact it inspects. It only writes:

* `logs/verification.log`
* `release/reports/verification-report.md`
* `release/reports/verification-report.json`
* `release/RELEASE_SUMMARY.md`
* `release/BUILD_SUMMARY.md`

## What it verifies

| Stage        | What it checks |
|--------------|----------------|
| **build**        | release/ exists, `manifest.json` parses, `build-report.md` is present |
| **executables**  | every required `.exe` exists, has size > 0, valid PE header, embedded version info |
| **artifacts**    | every required subdir under `release/` exists (`master`, `worker`, `studio`, `master-control`, `worker-control`, `cli`, `checksums`, `installer`, `zip`, `reports`) |
| **config**       | `VERSION`, `CHANGELOG.md`, `README.md`, `assets/manifest.json`, default icon, version consistency across all sources |
| **python**       | bundled Python 3.12.x installer exists, host has Python 3.12+ |
| **frontend**     | every frontend's `package.json` parses, has a build script, built bundle is on disk, Tauri executables exist |
| **checksums**    | regenerated SHA-256 hashes match `release/checksums/checksums.txt` and `manifest.json` |
| **installer**    | `AIClusterSetup.exe` exists in `dist/` and `artifacts/`, is a valid PE; Inno Setup script has every required section |
| **backend**      | launches `AIClusterMaster.exe`, waits up to 20s for port 8000, hits `GET /api/v1/health`, shuts down; same for `AIClusterWorker.exe` |
| **api**          | live HTTP probes against `/api/v1/health`, `/openapi.json`, `/docs`, `/redoc` |

## Quick start

```bash
# Verify a release that has already been built into ./release/
python -m build.verification.verify

# Skip launching executables (offline / non-Windows host)
python -m build.verification.verify --skip-run

# Point at a different release folder
python -m build.verification.verify --release-dir /path/to/release

# Emit a JSON summary
python -m build.verification.verify --json
```

## Integration with `build.build`

`build/build.py` invokes the verification pipeline automatically
after the packaging stage:

```python
from . import setup_builder
from .verification import verify_all

# ... after packaging
report = verify_all(build_exit_code=0)
if report.overall == Status.FAIL:
    return 1
```

If verification fails, the orchestrator returns exit code 1 and the
build is considered **failed**. The build system still emits its own
`build-report.md`; the verification system adds
`release/reports/verification-report.md` on top.

To disable verification of an existing build (for example, when
iterating on the build system itself), pass `--skip-verify` to
`build.build`.

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | All checks PASS or WARN. |
| 1    | At least one FAIL. The build should be considered broken. |

## Configuration

All defaults are environment variables:

| Variable                          | Default                     | Purpose |
|-----------------------------------|-----------------------------|---------|
| `AICLUSTER_VERIFY_RELEASE_DIR`    | `<repo>/release`            | release folder to inspect |
| `AICLUSTER_VERIFY_DIST_DIR`       | `<repo>/dist`               | dist folder for the compiled installer |
| `AICLUSTER_VERIFY_ARTIFACTS_DIR`  | `<repo>/artifacts`          | artifacts folder for the archived installer |
| `AICLUSTER_VERIFY_PORT`           | `8000`                      | master API port (overridable) |
| `AICLUSTER_VERIFY_WORKER_PORT`    | `8001`                      | worker port (informational) |
| `AICLUSTER_VERIFY_TIMEOUT`        | `20.0`                      | seconds to wait for the master to listen |
| `AICLUSTER_VERIFY_SKIP_RUN`       | unset                       | when set, skip launching any executable |
| `AICLUSTER_BUILD_NUMBER`          | current timestamp           | build number written to the report |
| `AICLUSTER_VERSION`               | `1.2.3`                     | product version written to the report |

## Files

```
build/verification/
├── __init__.py
├── utils.py            shared logging, timing, process helpers
├── context.py          VerifierContext + tunables
├── verify_report.py    VerificationResult, VerificationReport, status enum
├── verify.py           top-level orchestrator
├── verify_build.py     stage 1 - build presence
├── verify_artifacts.py stage 2 - release folder layout
├── verify_executables.py  stage 3 - every required exe
├── verify_config.py    stage 4 - configuration files
├── verify_python.py    stage 5 - Python runtime
├── verify_frontend.py  stage 6 - frontend bundles + Tauri smoke tests
├── verify_checksums.py stage 7 - checksum regeneration
├── verify_installer.py stage 8 - AIClusterSetup.exe + Inno script
├── verify_backend.py   stage 9 - Master + Worker launch + health
├── verify_api.py       stage 10 - live HTTP probes
└── README.md           this file
```

## Report format

`release/reports/verification-report.md` is the human-readable
summary; `release/reports/verification-report.json` is the
machine-readable version. Both contain:

* date, version, build number, duration, overall status
* per-category PASS/FAIL/WARN lines
* per-check details (durations, hashes, sizes, response codes)
* full list of verified artifacts

`release/RELEASE_SUMMARY.md` and `release/BUILD_SUMMARY.md` are
top-level convenience files used for tagging the release.
