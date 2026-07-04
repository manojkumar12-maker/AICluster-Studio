# AICluster v1.3.1 Implementation Graph

## Dependency Graph

```
Sprint 1: AUTH & SECURITY FOUNDATION
═══════════════════════════════════════
S-001 (JWT Secret)
  ├──→ S-003 (Auth Enforcement) [BLOCKING]
  ├──→ S-008 (WebSocket Auth) [BLOCKING]
  └──→ S-009 (Worker Auth) [BLOCKING]
        │
S-002 (Admin Creds)
  └──→ S-003 (Auth Enforcement) [BLOCKING]
        │
S-005 (CORS) ── independent ──→ no blocking
        │
C-005 (Double Commit) ── independent
C-006 (duration_ms) ── independent
C-008 (Scheduler Stop) ── independent


Sprint 2: WORKER & DATA STABILITY
═══════════════════════════════════
S-006 (Path Traversal) ── depends on C-002
S-008 (WebSocket Auth) ── depends on S-001
S-009 (Worker Auth) ── depends on S-001
S-012 (SQL Injection) ── independent
        │
C-001 (Dead Code) ── independent
C-002 (exec w/ progress) ── independent
C-003 (reporter None) ── independent
C-004 (poll type) ── independent
C-007 (Blocking IO) ── independent
        │
All Sprint 2 → Sprint 3


Sprint 3: HARDENING & INFRASTRUCTURE
═════════════════════════════════════
S-004 (Plugin RCE) ── depends on C-009
S-007 (Rate Limiting) ── depends on S-001
S-010 (HTTPS) ── depends on S-001
S-011 (Cookie Auth) ── depends on S-003
S-013 (Info Disclosure) ── independent
        │
C-009 (Empty Except) ── independent
        │
F-003 (WebSocket Frontend) ── depends on S-008
        │
All Sprint 3 → Sprint 4


Sprint 4: TESTING & POLISH
═══════════════════════════
T-001 (Subsystem Tests)
  ├── Depends on Sprint 1-3 fixes being stable
  └── Tests: workflow, repo, AI, agents, engineering, plugins, audit, WS

T-002 (Auth Integration Tests)
  └── Depends on S-003 (auth enforcement being live)

T-003 (Frontend Tests)
  └── Depends on F-001 (pages existing)

F-001 (Dashboard Pages)
  └── Independent (can be built against mock API)

F-002 (Studio Improvements)
  └── Independent

C-010 (Dedup IP Logic)
  └── Independent

B-001 (Binary Size)
  └── Independent

B-002 (CI/CD)
  └── Depends on T-001, T-002, T-003 passing


Sprint Dependency Flow
══════════════════════
Sprint 1 ───→ Sprint 2 ───→ Sprint 3 ───→ Sprint 4
   │              │              │              │
   │    ┌─────────┘              │              │
   │    │                        │              │
   │    ▼                        │              │
   └──→ S-008, S-009             │              │
        (need S-001 first)       │              │
                                 │              │
   S-004 ────────────────────────┘              │
   (needs C-009 from Sprint 3)                  │
                                                │
   B-002 ───────────────────────────────────────┘
   (needs all tests from Sprint 4)


File Dependency Graph
═════════════════════

backend/app/config.py:
  S-001 (JWT) ← affects Settings class
  S-005 (CORS) ← adds cors_origins field
  S-010 (HTTPS) ← adds tls_ fields

backend/app/main.py:
  S-003 (Auth) ← adds auth middleware
  S-005 (CORS) ← changes CORS config
  S-007 (Rate Limit) ← adds middleware
  S-008 (WS Auth) ← adds WS token check
  S-013 (Info Disclosure) ← adds error handlers

backend/app/api/v1/*.py (15 files):
  S-003 (Auth) ← adds Depends(get_current_user) to each route
  S-013 (Info Disclosure) ← sanitize errors
  Performance ← adds pagination params

backend/app/services/auth.py:
  S-001 (JWT) ← key management
  S-002 (Admin) ← password generation
  S-011 (Cookie) ← cookie-based auth

backend/app/services/scheduler.py:
  C-005 (Double Commit) ← fix commit logic
  C-008 (Scheduler) ← event-based stop

worker/app/main.py:
  C-002 (exec w/ progress) ← remove dead branch
  C-003 (reporter None) ← no-op reporter
  C-004 (poll type) ← type guard

worker/app/executor/handlers/*.py:
  S-006 (Path Traversal) ← path validation
  C-007 (Blocking IO) ← asyncio.to_thread()

frontend/src/app/(dashboard)/*.tsx (8 files):
  F-001 ← implement placeholder pages

frontend/src/lib/websocket.ts:
  F-003 ← new file

backend/app/plugins/loader/service.py:
  S-004 (Plugin RCE) ← sandbox

.github/workflows/ci.yml:
  B-002 ← new file


Build Step Impact
═════════════════

Stage 1 (Environment Verify): No change
Stage 2 (Clean): No change
Stage 3 (Build Frontends): + F-001, F-002, F-003 changes
Stage 4 (PyInstaller): + B-001 optimizations
Stage 5 (Tauri): No change
Stage 6 (Sign): No change
Stage 7 (PE Gate): + Auth check in verification
Stage 8 (Package): No change
Stage 9 (Installers): No change
Stage 10 (Setup): No change
Stage 11 (Final Verify): + Auth endpoint verification
Stage 12 (Release Verify): + Auth endpoint verification
