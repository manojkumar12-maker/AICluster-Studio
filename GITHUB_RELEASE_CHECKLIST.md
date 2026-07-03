# AICluster v1.3.0 — GitHub Release Checklist

> Use this checklist to verify every aspect of the release before tagging and pushing to GitHub.
> Check each box with `[x]` when the condition is satisfied.

---

## 1. Version & Metadata

- [ ] **Version file** — `VERSION` contains `1.3.0` (no trailing newline issues)
- [ ] **Version consistency** — Version matches across: `VERSION`, `CHANGELOG.md`, `pyproject.toml`, `backend/app/main_master_version.txt`, installer metadata (`setup_builder.py`)
- [ ] **CHANGELOG updated** — `CHANGELOG.md` includes all changes since v1.2.0 with sections: Added, Changed, Fixed, Removed
- [ ] **Release notes** — `RELEASE_v1.3.0.md` is complete with summary, highlights, upgrade instructions, and known issues

## 2. Documentation

- [ ] **README complete** — `README.md` is accurate: installation, quick start, architecture overview, links to docs/
- [ ] **Documentation organized** — All docs live under `docs/` with subdirectories: `Architecture/`, `Audit/`, `Deployment/`, `Development/`, `Images/`, `Models/`
- [ ] **Architecture docs up to date** — `API_REFERENCE.md`, `DATABASE.md`, `STARTUP_SEQUENCE.md`, `WORKER_ARCHITECTURE.md`, `UI_ARCHITECTURE.md` reflect current code
- [ ] **Mermaid diagrams** — `docs/Architecture/MERMAID_DIAGRAMS.md` contains all 12 system diagrams (a–l)

## 3. Legal & Governance

- [ ] **LICENSE file present** — MIT License at `LICENSE` with correct year and copyright holder
- [ ] **CONTRIBUTING.md present** — Contribution guidelines, code of conduct, PR process
- [ ] **SECURITY.md present** — Security policy, vulnerability reporting contact, supported versions

## 4. Repository Hygiene

- [ ] **.gitignore reviewed** — All generated/build artifacts excluded (see `GIT_STATUS_REPORT.md` for full list)
- [ ] **No temp/build artifacts committed** — Verify: no `dist/`, `release/`, `artifacts/`, `temp/`, `__pycache__/`, `*.spec`, `*.db` files tracked
- [ ] **No secrets committed** — Scan for API keys, passwords, tokens in tracked files (check `.env` is in `.gitignore`)
- [ ] **No large binary files** — No models (`*.bin`, `*.pt`, `*.pth`, `*.onnx`) tracked in git
- [ ] **Git tags cleaned** — Remove any stale local tags that might conflict

## 5. Build Verification

- [ ] **Build passes** — Run: `python -m build.build --verify-only`
      - Expected output: `Build verification complete: 0 errors`
- [ ] **PyInstaller builds succeed** — Master, Worker, CLI, Control Centers all build without errors
- [ ] **Tauri builds succeed** — AIClusterStudio, MasterControlCenter, WorkerControlCenter compile
- [ ] **Frontend builds** — `npm run build` in `frontend/` completes with 0 errors
- [ ] **Code signing** — All `.exe` files Authenticode-signed via `scripts/sign.py`
- [ ] **Installer builds** — Inno Setup installer generated via `setup_builder.py`
- [ ] **Installer verified** — `setup_validator.py` passes: install, launch, content audit

## 6. Testing

- [ ] **All unit tests pass** — `pytest backend/tests/ worker/tests/` — 0 failures
- [ ] **Integration tests pass** — `pytest backend/tests/integration/` — worker registration, heartbeat, job lifecycle tests green
- [ ] **Lint passes** — `ruff check .` — 0 errors
- [ ] **Type checking passes** — `mypy backend/ worker/ --strict` — 0 errors
- [ ] **Manual smoke test** — Master starts, worker registers, job executes, dashboard loads

## 7. Pre-Release Validation

- [ ] **Fresh install test** — Run installer on clean Windows VM → Master starts → Worker connects → Job runs
- [ ] **Upgrade test** — Install v1.2.0 → upgrade to v1.3.0 → verify data migration (if any)
- [ ] **Offline/reconnect test** — Kill master → workers retry → restart master → workers re-register
- [ ] **Edge case: empty DB** — Delete `data/aicluster.db` → master starts → tables created → admin seeded
- [ ] **Edge case: port conflict** — Start something on port 8000 → master logs error → graceful exit

## 8. Release Execution

- [ ] **Release notes finalized** — `RELEASE_v1.3.0.md` reviewed by team
- [ ] **Git tag created** — `git tag -a v1.3.0 -m "AICluster v1.3.0 — Project Audit & Production Readiness"`
- [ ] **Tag pushed** — `git push origin v1.3.0`
- [ ] **GitHub Release created** — Title: `AICluster v1.3.0 — Project Audit & Production Readiness`
- [ ] **Assets attached** — Installer `.exe`, `.sha256` checksums file, `RELEASE_v1.3.0.md`
- [ ] **Release published** — Set as latest release, not a pre-release

---

## Quick-Start Commands

```powershell
# Build & verify
python -m build.build --verify-only

# Run full test suite
pytest backend/tests/ worker/tests/ -v

# Lint & typecheck
ruff check .
mypy backend/ worker/ --strict

# Tag & push
git tag -a v1.3.0 -m "AICluster v1.3.0 — Project Audit & Production Readiness"
git push origin v1.3.0

# Create release (via GitHub CLI)
gh release create v1.3.0 release/AICluster-v1.3.0.exe release/AICluster-v1.3.0.sha256 `
  --title "AICluster v1.3.0 — Project Audit & Production Readiness" `
  --notes-file RELEASE_v1.3.0.md `
  --latest
```

---

*Last updated: 2026-07-03*
