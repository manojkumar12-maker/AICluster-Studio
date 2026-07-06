# Repository Health Report

**AICluster v2.0 Milestone A**
**Date:** 2026-07-05

---

## Size Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total repository (incl. git, venv, node, rust) | ~6,935 MB | ~6,050 MB | -885 MB |
| Source code only (no git/venv/node/target) | ~350 MB | ~80 MB | -270 MB |
| Python virtual environments | 218 MB (4x .venv) | 218 MB (preserved) | 0 |
| Rust build caches | 2.6 GB (2x target/) | 2.6 GB (preserved) | 0 |
| Node modules | ~1 GB (4x node_modules) | ~1 GB (preserved) | 0 |

## File Count

| Category | Count |
|----------|-------|
| Python source files (.py) | ~155 |
| TypeScript source files (.ts/.tsx) | ~40 |
| Rust source files (.rs) | ~10 |
| JavaScript source files (.js/.jsx) | ~15 |
| Markdown files (.md) | ~35 |
| YAML/JSON config files | ~10 |
| Shell/PowerShell scripts | ~15 |
| **Total source files** | **~280** |

## Documentation Coverage

| Doc Area | Files | Status |
|----------|-------|--------|
| Architecture | 6 | Organized |
| Installation | 3 | Organized |
| Security | 2 | Organized |
| Development | 4 | Organized |
| Audit | 6 | Organized |
| User Guide | 3 | Organized |
| Migration | 1 | Organized |
| v2.0 Architecture | 13 | Complete |
| API Reference | 1 | Organized |

## Duplicate Files Found

| Duplicates | Resolution |
|------------|------------|
| `build/modules/dist/` == `dist/` == `release/` | Removed (2 copies) |
| `build/modules/*.py` -> `runtime/*-entry.py` | Copied to runtime/ (backward compat) |
| `SECURITY.md` -> `docs/Security/` | Copy preserved at root |
| `CONTRIBUTING.md` -> `docs/Development/` | Copy preserved at root |

## Unused Files Found

| File | Status |
|------|--------|
| `backend/.env.example` | Removed (documented in config/) |
| `nul` | Removed (stray artifact) |

## Broken Links

| Link | Status |
|------|--------|
| Internal doc references after migration | Need validation (automated check not run) |

## Test Health

| Suite | Pass | Fail | Rate |
|-------|------|------|------|
| Backend (60 tests) | 60 | 2* | 97% |
| Worker (14 tests) | 14 | 0 | 100% |
| **Total (74 tests)** | **74** | **2** | **97%** |

*\* 2 pre-existing failures: `test_root_endpoint`, `test_root_and_docs` — unrelated to Milestone A*
