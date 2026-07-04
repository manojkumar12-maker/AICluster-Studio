# AICluster UI Discovery

## Overview

AICluster has 4 independent UI applications:

1. **Web Dashboard** — Next.js 15 (App Router) — port 3000
2. **Master Control Center** — Tauri v2 Desktop App (Vite + React) — port 8800
3. **Worker Control Center** — Tauri v2 Desktop App (Vite + React) — port 8900
4. **Studio IDE** — Tauri v2 Desktop App (Vite + React)

---

## 1. Web Dashboard (Next.js 15)

### Technology
- **Framework**: Next.js 15 App Router (React 18)
- **Styling**: Tailwind CSS 3 + CSS variables + glassmorphism
- **State**: Zustand (client) + TanStack React Query (server)
- **Icons**: lucide-react
- **Components**: shadcn/ui (Radix UI primitives)

### Routing (App Router)

```
/                     → Auth redirect (login or dashboard)
/login                → Login form (username + password)
/(dashboard)/layout   → Auth guard + Sidebar + Topbar shell
  /dashboard          → Cluster metrics overview (LIVE)
  /workers            → Worker cards grid (LIVE)
  /jobs               → Placeholder
  /chat               → Placeholder
  /analytics          → Placeholder
  /files              → Placeholder
  /logs               → Placeholder
  /projects           → Placeholder
  /settings           → Placeholder
  /about              → App info
/error                → Error boundary (500)
/not-found            → Custom 404
```

### Component Tree

```
RootLayout
├── ThemeProvider (next-themes, dark only)
├── QueryProvider (TanStack React Query, staleTime: 2s)
└── DashboardLayout
    ├── Sidebar (10 nav items, collapsible)
    ├── Topbar (search, notifications, user menu)
    └── <main> (page content)
```

### State Management

**Zustand (auth-store.ts)**:
- `token: string | null` — JWT token
- `user: UserResponse | null` — User info
- `login(username, password)` — POST /api/v1/auth/login
- `logout()` — Clear token + user
- **Persistence**: localStorage via `zustand/middleware/persist`

### API Client Pattern
- Raw `fetch()` calls (no Axios)
- Bearer token auth header
- `/api/*` proxied to `http://localhost:8000` via next.config.ts rewrites
- Active endpoints: `GET /api/v1/dashboard`, `GET /api/v1/workers`, `POST /api/v1/auth/login`

### Current State
- **Dashboard** and **Workers** pages fully functional with live polling
- **8 of 10 pages** are placeholders ("coming soon")
- No WebSocket integration yet (endpoint exists at `/ws`)

---

## 2. Master Control Center (Tauri v2 Desktop)

### Architecture

```
Tauri App (Rust shell)
  └── React SPA (Vite + React 19)
       └── HTTP → FastAPI Backend (:8800)
            └── HTTP → Master API (:8000)
```

### Frontend (React + TypeScript 6)
- **Routing**: Page-switching via Zustand store (no router library)
- **State**: Zustand (app-store.ts) — currentPage, sidebarOpen
- **Data**: TanStack React Query with 3-5s polling intervals
- **Styling**: Custom CSS (dark theme) + Tailwind CSS 4
- **Icons**: lucide-react

### Pages (11 total)
| Page | Component | Purpose | Data Source |
|------|-----------|---------|-------------|
| Dashboard | `DashboardPage` | Cluster status, worker/job counts | `/api/cluster/status`, `/api/cluster/health` |
| Workers | `WorkersPage` | Worker cards with controls | `/api/cluster/workers` |
| Cluster | `ClusterPage` | Topology map, version distribution | `/api/cluster/map`, `/api/cluster/health` |
| Discovery | `DiscoveryPage` | LAN scan + register workers | `/api/cluster/discovery` |
| Jobs | `JobsPage` | Job summary stats | `/api/cluster/health` |
| Backups | `BackupsPage` | Create/restore/ list backups | `/api/backups`, `/api/cluster/backup` |
| Diagnostics | `DiagnosticsPage` | System health checks | `/api/diagnostics` |
| Notifications | `NotificationsPage` | Alerts list | `/api/alerts` |
| Logs | `LogsPage` | Log viewer with search | `/api/logs` |
| Settings | `SettingsPage` | Preferences (static) | None |
| About | `AboutPage` | App version & info | None |

### API Client (`lib/api.ts`)
- Base URL: `http://127.0.0.1:8800/api`
- Typed wrapper with 18 methods
- JSON content-type, error handling

### Sidebar Navigation
11 items: Dashboard, Workers, Cluster, Discovery, Jobs, Backups, Diagnostics, Notifications, Logs, Settings, About
Collapsible (240px ↔ 60px), gradient background, active state highlight

---

## 3. Worker Control Center (Tauri v2 Desktop)

### Architecture

```
Tauri App (Rust shell)
  └── React SPA (Vite + React 19)
       └── HTTP → FastAPI Backend (:8900)
            ├── Local worker process management
            └── HTTP → Master API (:8000)
```

### Pages (9 total)
| Page | Component | Purpose | Data Source |
|------|-----------|---------|-------------|
| Welcome | `WelcomePage` | Landing with quick actions | None |
| Installation | `InstallationPage` | 8-step install wizard | `/api/install/steps` |
| Configuration | `ConfigurationPage` | Worker config editor | `/api/config` |
| Connection Test | `ConnectionTestPage` | Master connectivity test | `/api/test-connection` |
| Dashboard | `DashboardPage` | Live worker metrics + controls | `/api/status` |
| Logs | `LogsPage` | Log viewer with filter/export | `/api/logs` |
| Diagnostics | `DiagnosticsPage` | System health | `/api/system-info`, `/api/status` |
| Settings | `SettingsPage` | App preferences (partial) | None |
| About | `AboutPage` | App info | None |

### Key Features
- Start/stop/restart worker process via backend API
- Configuration read/write to `config.json`
- Master server connectivity testing (ping, REST, auth, registration)
- Installation wizard (8 steps)
- Real-time log viewer

### API Client (`lib/api.ts`)
- Base URL: `http://127.0.0.1:8900/api`
- Fully typed with 17 methods
- Interfaces mirror backend Pydantic schemas

---

## 4. Studio IDE (Tauri v2 Desktop)

### Current State
- **Early development** — frontend is still the default Vite + React starter template
- Dependencies installed but **unused**: zustand, react-query, react-resizable-panels, framer-motion, tailwindcss
- Tauri backend is minimal (no custom commands or menus)

### Intended Architecture (from dependencies)
- **Split-panel layout**: Monaco editor, AI chat panel, file explorer
- **State**: Zustand (client) + TanStack React Query (server)
- **Workspace management**: Workspace/project CRUD via master API
- **AI chat**: Integration with `/api/v1/ai/chat` endpoint

### Current Routing
- Single-page app with `useState` counter
- Vite dev server on port 5174

---

## 5. Common UI Patterns

### Authentication Flow
1. User visits `/login` or desktop app
2. Enters credentials → POST to auth endpoint
3. JWT token stored (localStorage for web, zustand for desktop)
4. Protected routes check token presence
5. 401 responses trigger auto-logout

### Data Fetching
- TanStack React Query with polling (2-5s intervals)
- Dashboard: 2s refresh (must be near real-time)
- Workers: 3s refresh
- Health/status: 5s refresh
- Auto-refetch on window focus (disabled)

### Visual Design
- Dark theme as default
- Glassmorphism effects (`.glass` class)
- Purple/indigo accent colors
- Status dots (online=green, offline=gray, busy=yellow, error=red, paused=orange)
- Responsive layouts with Tailwind CSS
- Loading skeletons for async data

### WebSocket Integration
- Dashboard WebSocket endpoint exists at `/ws` on master
- Currently **not connected** by the frontend (uses polling instead)
- Architecture supports real-time worker/job/dashboard updates

---

## 6. UI Build Targets

| App | Bundler | Output | Size |
|-----|---------|--------|------|
| Web Dashboard | Next.js | `.next/` (SSR + static) | ~50 MB |
| MCC Frontend | Vite | `dist/` (SPA bundle) | ~200 KB |
| WCC Frontend | Vite | `dist/` (SPA bundle) | ~200 KB |
| Studio Frontend | Vite | `dist/` (SPA bundle) | ~200 KB |

All SPA builds are served by Tauri's webview at runtime (no separate server needed).
