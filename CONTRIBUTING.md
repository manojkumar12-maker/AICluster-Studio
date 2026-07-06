# Contributing to AICluster

Thank you for your interest in contributing! AICluster is an open-source, offline-first AI cluster management platform for Windows.

## Repository Structure

```
AICluster/
├── backend/          FastAPI master server (Python 3.12+)
├── worker/           Worker agent (Python 3.12+)
├── studio/           Desktop IDE (Tauri v2 + React/TypeScript)
│   └── src-tauri/    Rust backend for Studio
├── frontend/         Web dashboard (Next.js 15)
├── build/            Build system (PyInstaller, Inno Setup, Tauri)
├── config/           Default configuration files
├── docs/             Documentation
├── scripts/          PowerShell/Python utility scripts
├── runtime/          Combined entry points
└── shared/           Shared Python utilities
```

## Getting Started

### Prerequisites

| Tool | Minimum Version |
|---|---|
| Python | 3.12+ |
| Node.js | 18+ |
| Rust | 1.70+ |
| PyInstaller | 6.x |
| Tauri CLI | 2.x |
| Inno Setup 6 | 6.4+ (for installer builds) |

### Setup

```bash
git clone https://github.com/manojkumar12-maker/AICluster-Studio.git
cd AICluster

# Python dependencies
pip install -r backend/requirements.txt

# Node dependencies
cd frontend && npm install && cd ..
cd studio && npm install && cd ..

# Run backend in development
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run Studio in development
cd studio
npm run tauri dev
```

## Coding Standards

### Python (Backend / Worker)
- Follow PEP 8
- Use type hints with `from __future__ import annotations`
- Use async/await for database and HTTP operations
- Pydantic v2 for all request/response models
- SQLAlchemy 2.0 with `Mapped[]` annotations
- Format with `ruff`, lint with `ruff check`

### TypeScript / React (Frontend / Studio)
- Functional components with hooks
- Zustand for state management
- All API types must match backend Pydantic schemas
- Use `string` for IDs (backends use UUIDs)
- Format with Prettier, lint with ESLint

### Rust (Studio Tauri Backend)
- `cargo fmt` and `cargo clippy` before committing
- Tauri commands should delegate to shared LifecycleManager
- Handle all error cases explicitly

### General
- **No `except Exception: pass`** — always log the error
- **No hardcoded secrets** — use environment variables or auto-generated keys
- **No hardcoded IP addresses** — use configurable defaults

## Branch Strategy

- `main` — Stable release branch
- `develop` — Integration branch
- `feature/*` — New features
- `fix/*` — Bug fixes
- `release/*` — Release preparation
- `docs/*` — Documentation changes

## Commit Messages

Follow Conventional Commits:
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `refactor:` — Code restructuring
- `perf:` — Performance
- `test:` — Tests
- `build:` — Build system
- `security:` — Security fix

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes following coding standards
4. Run tests: `cd backend && python -m pytest -v`
5. Open a Pull Request using the PR template

### PR Checklist
- [ ] Code follows coding standards
- [ ] Tests pass on Windows 10/11
- [ ] No new warnings or errors
- [ ] No breaking changes to REST API or database schema without discussion
- [ ] Documentation updated if needed

## Testing

```bash
# Backend tests
cd backend && python -m pytest -v

# Build verification
python -m build.verify
```

## Release Process

1. All changes merged to `main`
2. Version bumped in `VERSION`, `config.py`, `constants.py`
3. `CHANGELOG.md` updated
4. Full build: `build-all.bat`
5. Installer tested with silent install
6. Tag: `git tag -a v2.0.0 -m "AICluster v2.0.0 Stable"`
7. Release created on GitHub

## Questions?

- **Bugs**: Open a [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- **Features**: Open a [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
- **Security**: See [SECURITY.md](SECURITY.md)
