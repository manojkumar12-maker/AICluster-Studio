# AICluster v1.3.1 Build Implementation Plan

## Current Build System

The build system (`build/`) is already comprehensive with 12 stages. v1.3.1 build changes are minimal — focused on CI/CD and binary optimization.

---

## B-001: Binary Size Optimization

**Issue**: AIClusterMaster.exe is ~80 MB due to bundling full Python runtime and all dependencies.

**Analysis**:
- PyInstaller bundles Python interpreter + stdlib + all site-packages
- FastAPI, SQLAlchemy, uvicorn, and their transitive deps add significant size
- `--collect-all` captures sub-modules which may include unnecessary packages

**Fixes**:

1. **Audit hidden imports**: 
   - Review `build/config.py:PYINSTALLER_TARGETS` 
   - Remove unnecessary `--hidden-import` directives
   - Only include what's actually imported by the entry point

2. **Exclude unused stdlib modules**:
   ```python
   # In pyinstaller_builder.py
   EXCLUDED_MODULES = [
       "tkinter", "test", "unittest", "distutils", "ensurepip",
       "turtle", "idlelib", "pydoc", "http.server", "webbrowser",
       "sqlite3.test", "ctypes.test", "email.test",
   ]
   ```

3. **UPX compression**:
   - Add UPX to build pipeline (if available)
   - Compress: `--upx-dir` flag for PyInstaller
   - Expected reduction: ~40% (80 MB → ~48 MB)

4. **Consider `--onefile` vs `--onedir`**:
   - `--onefile`: Single EXE (slower startup, extracts to temp)
   - `--onedir`: Directory with EXE + DLLs (faster startup, ~same total size)
   - v1.3.1: Keep `--onefile`, optimize what's bundled

**Files**: `build/pyinstaller_builder.py`, `build/config.py`
**Estimated saving**: 80 MB → ~50 MB for master
**Risk**: LOW
**Tests**: All verification stages must pass after optimization

---

## B-002: CI/CD Pipeline

**Issue**: No automated CI/CD. Builds are manual via `build-all.bat`.

**Implementation**: GitHub Actions workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-backend:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt
      - run: pip install ruff mypy
      - run: ruff check backend/app/
      - run: mypy backend/app/ --ignore-missing-imports

  test-backend:
    needs: lint-backend
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: pytest backend/tests/ -v --cov=backend/app --cov-report=xml
      - uses: codecov/codecov-action@v3

  test-worker:
    needs: lint-backend
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r worker/requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest worker/tests/ -v --cov=worker/app --cov-report=xml

  lint-frontend:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint

  test-frontend:
    needs: lint-frontend
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npx vitest --run --coverage

  build-dry-run:
    needs: [test-backend, test-worker, test-frontend]
    runs-on: windows-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      # Verify build config is valid, don't full build
      - run: python -c "import build.config; print('Build config OK')"

  release:
    needs: build-dry-run
    runs-on: windows-latest
    if: github.ref == 'refs/heads/main' && startsWith(github.event.head_commit.message, 'release:')
    steps:
      - uses: actions/checkout@v4
      # Full build
      - run: python -m build.build --skip-sign
      # Upload artifacts
      - uses: actions/upload-artifact@v4
        with:
          name: release
          path: release/
```

**Stages**:
1. **Lint**: ruff (Python), oxlint (TypeScript), mypy (type checking)
2. **Test**: pytest (backend + worker), vitest (frontend)
3. **Build dry-run**: PR validation (config check only)
4. **Release**: Full build on tagged commits

**Files**: New `.github/workflows/ci.yml`
**Risk**: LOW
**Tests**: CI passes on PR

---

## Verification Updates

**Issue**: Post-build verification (10 stages) needs to include auth endpoint checks after Sprint 1.

**Add to `verify_api.py`**:
```python
# Verify protected endpoints require auth
def test_auth_check(ctx):
    """Verify that API endpoints require authentication."""
    url = f"http://localhost:{ctx.api_port}/api/v1/workers"
    resp = http_get(url)
    assert resp.status == 401, "Protected endpoint should return 401 without auth"
```

**Add to `verify_backend.py`**:
```python
# Verify worker registration requires auth
def test_worker_registration(ctx):
    url = f"http://localhost:{ctx.api_port}/api/v1/workers/register"
    resp = http_post(url, json={"name": "test", "hostname": "test", "ip": "0.0.0.0"})
    assert resp.status in (401, 403), "Unauthenticated registration should fail"
```

**Files**: `build/verification/verify_api.py`, `build/verification/verify_backend.py`
**Risk**: LOW

---

## Version Bump

**Files to update**:
- `VERSION`: `1.3.0` → `1.3.1`
- `CHANGELOG.md`: Add v1.3.1 section
- `build/modules/*_version.txt`: Generated by `version.py`, auto-updated

## Release Checklist Additions

After all Sprint 4 work is complete:
1. Run `python -m build.build --skip-sign` → must pass all stages
2. Run verification → all 10 stages PASS
3. Manual E2E test: auth flow, worker registration, job execution
4. Update VERSION to 1.3.1
5. Update CHANGELOG.md
6. Tag release: `git tag v1.3.1 && git push --tags`
7. CI/CD release job produces final artifacts
8. Manual: upload artifacts to GitHub Releases
