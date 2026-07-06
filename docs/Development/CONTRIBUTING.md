# Contributing to AICluster

Thank you for your interest in contributing to AICluster. This document outlines the setup process, coding standards, and workflow for contributors.

---

## Setup Instructions

### Prerequisites

- **Python** 3.12+
- **Node.js** 20+
- **Rust** (stable) — only needed for Tauri desktop apps (Studio, Master Control Center, Worker Control Center)

### Clone and Install

```powershell
# Clone the repository
git clone https://github.com/your-org/AICluster.git
cd AICluster

# Backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -r requirements-dev.txt  # dev/lint/test dependencies

# Frontend (web dashboard)
cd ../frontend
npm install

# Studio (Tauri desktop app)
cd ../studio
npm install

# Master Control Center
cd ../master-control-center/frontend
npm install

# Worker Control Center
cd ../worker-control-center/frontend
npm install
```

---

## Coding Standards

### Python

- **Formatter**: [Black](https://github.com/psf/black) with default settings (line length 88)
- **Linter**: [ruff](https://github.com/astral-sh/ruff) with default rules
- **Type hints**: Required for all function signatures and public APIs
- **Style**: Follow [PEP 8](https://peps.python.org/pep-0008/) conventions

```bash
# Format and lint
cd backend
.venv\Scripts\black app/ tests/
.venv\Scripts\ruff check app/ tests/
```

### TypeScript / React

- **Formatter**: [Prettier](https://prettier.io/) with project settings
- **Linter**: [ESLint](https://eslint.org/) with TypeScript rules
- **TypeScript**: Strict mode enabled — all types must be explicit
- **Component style**: Functional components with hooks, no class components

```bash
# Format and lint
cd frontend
npx prettier --write src/
npx eslint src/
npx tsc --noEmit
```

### Rust (Tauri)

- **Formatter**: `rustfmt` with default settings
- **Linter**: `clippy` with default rules

```bash
# Format and lint
cd studio/src-tauri
cargo fmt
cargo clippy
```

---

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`
2. **Make your changes** following the coding standards above
3. **Write or update tests** for all changed functionality
4. **Run the full test suite** and confirm it passes
5. **Update documentation** if you changed public APIs, added features, or modified behavior
6. **Create a pull request** with a clear title and description

### PR checklist

- [ ] Code follows project coding standards
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated (API docs, architecture docs, etc.)
- [ ] No new lint warnings or TypeScript errors
- [ ] Commit messages follow conventional commits format
- [ ] Branch is up to date with target branch

### Review process

- At least one maintainer review is required
- All CI checks must pass
- Changes requiring documentation updates will be blocked until docs are complete

---

## Testing Requirements

```bash
# Backend tests (pytest)
cd backend
.venv\Scripts\pytest -v           # Unit tests
.venv\Scripts\python ..\scripts\run-integration-test.py  # Integration tests

# Frontend build check
cd frontend
npm run build
npm run lint

# Worker tests
cd worker
.venv\Scripts\pytest -v

# All Tauri apps must build without errors
cd studio
npm run tauri build
```

- All new features require unit tests
- API changes require integration tests
- Bug fixes require a regression test
- Test coverage should not decrease

---

## Documentation Requirements

- All new API endpoints must be added to `docs/Architecture/API_REFERENCE.md`
- New database tables must be documented in `docs/Architecture/DATABASE.md`
- Architectural changes must be reflected in `docs/Architecture/PROJECT_REVIEW.md`
- User-facing features should have corresponding documentation in the appropriate `docs/` subdirectory
- Update `docs/DOCUMENT_INDEX.md` when adding or removing documentation files

---

## Commit Message Style

AICluster uses **Conventional Commits**:

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

### Types

| Type | Usage |
|------|-------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Code style changes (formatting, linting) |
| `refactor` | Code refactoring without feature change or fix |
| `test` | Adding or updating tests |
| `chore` | Build process, dependencies, tooling |
| `perf` | Performance improvement |
| `sec` | Security fix |

### Examples

```
feat(worker): add GPU utilization reporting to heartbeat
fix(api): handle null assigned_worker in job listing
docs(audit): document new retention settings endpoint
test(workflow): add integration test for DAG cancellation
sec(auth): rotate JWT secret on password change
```

### Scope values

`backend`, `frontend`, `worker`, `studio`, `mcc` (master control center), `wcc` (worker control center), `build`, `docs`, `config`, `plugins`, `shared`, `scripts`, `audit`

---

## Questions

If you have questions about contributing, open a GitHub Discussion or contact the maintainers.
