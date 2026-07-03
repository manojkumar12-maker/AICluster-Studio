# AICluster UI Architecture

**Version:** 1.2.1  
**Last Updated:** 2026-07-03  
**Scope:** Web frontend (Next.js), Master Control Center (Tauri), Worker Control Center (Tauri), Studio (Tauri), Python backend (FastAPI)

---

## 1. How the UI Loads — Entry Points

AICluster has **four independent UI applications**, each with its own entry point and build pipeline:

| Application | Framework | Entry Point | Hosting Model |
|---|---|---|---|
| **Web Frontend** | Next.js 15 (App Router) | `frontend/src/app/layout.tsx` | Next.js server (dev) / static export (production) |
| **Master Control Center** | Vite + React 19 | `master-control-center/frontend/src/main.tsx` | Tauri WebView |
| **Worker Control Center** | Vite + React 19 | `worker-control-center/frontend/src/main.tsx` | Tauri WebView |
| **Studio** | Vite + React 19 | `studio/src/main.tsx` | Tauri WebView |

### 1.1 Next.js App (Web Frontend)

The web frontend uses Next.js 15's **App Router** (`frontend/src/app/`). The root layout (`layout.tsx`) is the outermost shell and wraps every page:

```
layout.tsx (RootLayout)
  ├── <html> with suppressHydrationWarning
  │   ├── <body>
  │   │   ├── ThemeProvider (next-themes)
  │   │   │   └── QueryProvider (TanStack React Query)
  │   │   │       └── {children} ← page content
```

The `{children}` slot is filled at runtime by Next.js based on the current route. The file-system directory structure defines the URL hierarchy:

- `app/page.tsx` → `/` (root — redirects to `/login` or `/dashboard`)
- `app/login/page.tsx` → `/login`
- `app/(dashboard)/layout.tsx` → shared dashboard shell with auth guard
- `app/(dashboard)/dashboard/page.tsx` → `/dashboard`
- `app/(dashboard)/workers/page.tsx` → `/workers`
- `app/(dashboard)/jobs/page.tsx` → `/jobs`
- ...etc for chat, projects, files, logs, analytics, settings, about

The `(dashboard)` route group is a **route group** (parentheses) — it does not add a segment to the URL but provides a shared layout.

### 1.2 Vite + React Apps (Tauri)

The three Tauri apps use Vite as their dev server and bundler. Each has an `index.html` at the project root containing a `<div id="root"></div>` mount point. The React entry points follow the same pattern:

**main.tsx** (all three Tauri apps):
```tsx
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

The `App.tsx` for each Tauri app wraps everything in a `QueryClientProvider` and renders `AppContent`, which is a page-router component driven by Zustand state (see section 12).

---

## 2. How the Frontend Starts

### 2.1 Next.js Server (Development)

```bash
cd frontend
npm run dev   # → next dev
```

This starts the Next.js development server on `http://localhost:3000` (default). It handles:
- **Server-Side Rendering (SSR)** — the root layout and metadata are rendered on the server
- **Client-side hydration** — `"use client"` components (login, dashboard, sidebar, etc.) hydrate in the browser
- **API rewrites** — `next.config.ts` defines a rewrite rule that proxies `/api/:path*` to the Python backend at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`)

```ts
// next.config.ts
async rewrites() {
  return [{
    source: "/api/:path*",
    destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
  }];
}
```

This means the frontend can call `/api/v1/dashboard` and Next.js proxies it to the backend, avoiding CORS issues in development.

### 2.2 Next.js Build & Static Export

```bash
cd frontend
npm run build   # → next build
npm run start   # → next start (production server)
```

The production build generates optimized static HTML + JS bundles. The `next start` command runs a Node.js server that serves the built output and still applies the API rewrites.

### 2.3 Vite Dev Server (Tauri Apps)

```bash
cd master-control-center/frontend
npm run dev   # → vite
```

Vite starts a dev server on port 5174 (master) or 5173 (worker) with HMR (Hot Module Replacement). During Tauri development, Tauri's dev mode (`cargo tauri dev`) launches the Vite dev server and opens a native window pointed at the dev URL (configured in `tauri.conf.json` as `devUrl`).

### 2.4 Vite Production Build (Tauri Apps)

When Tauri builds for distribution (`cargo tauri build`), it runs the `beforeBuildCommand` first:

```json
"beforeBuildCommand": "npm run build"
```

This runs `tsc -b && vite build`, which compiles TypeScript and outputs static files to `frontend/dist`. Tauri then embeds these files into the binary via the `frontendDist` path:

```json
"frontendDist": "../dist"
```

---

## 3. How React Starts

### 3.1 Next.js Web Frontend

React does not have an explicit `createRoot` call. Next.js 15's App Router manages the React lifecycle internally:

1. The server renders the `RootLayout` component tree to HTML
2. The client receives the pre-rendered HTML
3. Next.js hydration runtime calls `createRoot` internally on the `<body>` element
4. Client components (`"use client"`) are hydrated with interactivity
5. The `ThemeProvider` and `QueryProvider` mount and initialize their contexts

### 3.2 Tauri Apps (Vite + React)

All three Tauri apps use the explicit React 18+ `createRoot` API:

```tsx
// main.tsx (all Tauri apps)
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

The component tree mounts:
1. `createRoot` attaches to the `<div id="root">` in `index.html`
2. `<React.StrictMode>` enables development warnings
3. `<App />` renders:
   - **Master:** `QueryClientProvider` → `AppContent` (page routing via Zustand)
   - **Worker:** `QueryClientProvider` → `AppContent` (page routing via Zustand)
   - **Studio:** Currently a starter template with counter state

---

## 4. How Tauri Loads

The Tauri loading sequence is a multi-step chain from OS binary to rendered React UI:

### 4.1 Build Chain

```
Cargo.toml → rustc → binary (e.g. MasterControlCenter.exe)
```

Each Tauri app has a Rust crate defined in `src-tauri/Cargo.toml`:

```toml
[dependencies]
tauri = { version = "2.0", features = [] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

### 4.2 Runtime Startup

```
User launches .exe
  ↓
Cargo `main()` → tauri::Builder::default()
  ↓
Tauri runtime initializes
  ↓
Creates WebView window (per tauri.conf.json window config)
  ↓
WebView loads `devUrl` (dev: http://localhost:5174) or `frontendDist` (prod: bundled files)
  ↓
Vite-built React app mounts → ReactDOM.createRoot
  ↓
App.tsx renders UI
```

Key `tauri.conf.json` window properties:

| Property | Master / Worker / Studio |
|---|---|
| Width | 1280px |
| Height | 800px |
| Min Width | 960px |
| Min Height | 600px |
| Resizable | true |
| CSP | null (disabled) |

The CSP is disabled (`null`) because the apps need to make `fetch` calls to local backend servers (`127.0.0.1:8000`, `127.0.0.1:8800`, `127.0.0.1:8900`). With strict CSP these cross-origin requests would be blocked.

### 4.3 Bundle Output

All three Tauri apps use NSIS (Nullsoft Scriptable Install System) for Windows distribution, configured in `tauri.conf.json`:

```json
"bundle": {
  "active": true,
  "targets": ["nsis"],
  "icon": ["icons/32x32.png", "icons/128x128.png", "icons/128x128@2x.png", "icons/icon.ico"]
}
```

---

## 5. How the Backend Connects

### 5.1 Web Frontend API Calls

The Next.js frontend uses the browser `fetch` API directly. The `NEXT_PUBLIC_API_URL` environment variable determines the backend target:

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

In development, the Next.js rewrite rule in `next.config.ts` proxies `/api/*` to the backend, so relative URLs like `/api/v1/dashboard` work transparently. In production, absolute URLs are used.

**Auth login call** (from `auth-store.ts`):
```ts
fetch(`${API_URL}/api/v1/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
```

**Authenticated dashboard call** (from `dashboard/page.tsx`):
```ts
fetch(`${API_URL}/api/v1/dashboard`, {
  headers: { Authorization: `Bearer ${token}` },
});
```

### 5.2 Tauri App API Calls

The Tauri apps connect to their respective local backend services using `fetch` directly (no Tauri IPC commands are used for HTTP — it's plain browser `fetch` from the WebView):

**Master Control Center** → `http://127.0.0.1:8800`  
**Worker Control Center** → `http://127.0.0.1:8900`

Each Tauri app performs a health check on mount:

```tsx
// App.tsx (Master)
useEffect(() => {
  fetch('http://127.0.0.1:8800/api/health')
    .then((r) => r.json())
    .then(() => setReady(true))
    .catch(() => setTimeout(() => setReady(true), 3000));
}, []);
```

The `3-second fallback` ensures the UI renders even if the backend is not yet available, preventing a permanent loading state.

### 5.3 Studio

The Studio app currently does not make backend API calls (it is a starter scaffold). It will presumably use the same pattern as the other Tauri apps once the Studio feature set is implemented.

---

## 6. How the API Connects — Authentication

### 6.1 Token-Based Auth Flow

1. **Login:** User submits credentials to `POST /api/v1/auth/login`
2. **Backend verification:** `AuthService.authenticate()` in `backend/app/services/auth.py` validates the password against bcrypt hash, then generates a **JWT** using `python-jose`:

   ```python
   token = jwt.encode({
       "sub": user.id,
       "role": user.role,
       "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
   }, settings.secret_key, algorithm=settings.algorithm)
   ```

3. **Response:** Returns `{ access_token, token_type, expires_in, user }` as the `TokenResponse`
4. **Storage:** The frontend stores the token in a Zustand store persisted to `localStorage` (see section 9)
5. **Subsequent requests:** Every authenticated API call includes:
   ```
   Authorization: Bearer <token>
   ```

### 6.2 Backend Validation

The backend uses FastAPI's `Depends()` with the `get_current_user` dependency:

```python
# backend/app/services/auth.py
security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
    user_id = payload.get("sub")
    # ... fetch user from DB, raise 401 if invalid
```

Protected routes include this dependency to extract the authenticated user.

### 6.3 Token Expiration Handling

The `dashboard/page.tsx` explicitly checks for 401 responses and forces logout:

```tsx
if (res.status === 401) {
  useAuthStore.getState().logout();
  window.location.href = "/login";
  throw new Error("Session expired");
}
```

---

## 7. How WebSocket Connects

### 7.1 Server-Side WebSocket

The FastAPI backend exposes a WebSocket endpoint at `/ws`:

```python
# backend/app/main.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # ... keep connection open, handle ping/pong
```

The `WebSocketManager` (in `backend/app/websocket/manager.py`) manages a set of active connections and provides broadcast methods:

- `broadcast(event_type, data)` — sends JSON to all connected clients
- `broadcast_worker_update(worker)` — worker status changes
- `broadcast_job_update(job)` — job lifecycle events
- `broadcast_dashboard(dashboard)` — dashboard metric updates

### 7.2 Client-Side WebSocket

The web frontend currently does **not** implement a WebSocket client. The dashboard page uses polling via React Query's `refetchInterval: 2000` (2-second polling) instead. This is a design choice that trades real-time push for simplicity. The WebSocket infrastructure exists on the backend and can be consumed by future clients (or the Tauri apps) when needed.

---

## 8. How the Dashboard Updates

The dashboard page (`frontend/src/app/(dashboard)/dashboard/page.tsx`) uses **TanStack React Query** for data fetching and auto-refresh:

```tsx
const { data: dash, isLoading, error } = useQuery({
  queryKey: ["dashboard"],
  queryFn: () => fetchDashboard(token),
  refetchInterval: 2000,   // ← polls every 2 seconds
  enabled: !!token,         // ← only runs when authenticated
});
```

### 8.1 React Query Configuration

The `QueryProvider` (in `frontend/src/components/layout/query-provider.tsx`) sets global defaults:

```tsx
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 2000,           // data is fresh for 2s
      retry: 2,                  // retry twice on failure
      refetchOnWindowFocus: false, // don't refetch on tab focus
    },
  },
})
```

### 8.2 Data Flow

```
DashboardPage renders
  ↓
useQuery(["dashboard"], ...) fires
  ↓
fetchDashboard(token) calls GET /api/v1/dashboard
  ↓
Backend WorkerManagerService + SchedulerService compute stats
  ↓
JSON response → DashboardData interface
  ↓
React Query caches result, sets staleTime=2s
  ↓
2s later, refetchInterval triggers automatic re-fetch
  ↓
UI re-renders with new data (no loading flash — cached data shown while refetching)
```

### 8.3 Loading & Error States

- **Loading:** Cards show `"..."` and skeleton placeholders pulse
- **Error:** A red banner with "Failed to load metrics. Make sure the backend is running."
- **Empty/offline:** Workers count shows `0`, values fall back to `"-"`

---

## 9. How Authentication Works

### 9.1 Zustand Auth Store with Persist

The `useAuthStore` (in `frontend/src/stores/auth-store.ts`) uses Zustand's `persist` middleware to save authentication state to `localStorage`:

```tsx
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      login: async (username, password) => {
        const res = await fetch(`${API_URL}/api/v1/auth/login`, { ... });
        const data = await res.json();
        set({ token: data.access_token, user: data.user });
      },
      logout: () => {
        set({ token: null, user: null });
      },
    }),
    {
      name: "aicluster-auth",    // localStorage key
      partialize: (state) => ({   // only persist token + user
        token: state.token,
        user: state.user,
      }),
    }
  )
);
```

### 9.2 localStorage Key

The store persists under the key `"aicluster-auth"` in `localStorage`. This is the canonical source of truth for "is the user logged in?".

### 9.3 Auth-Protected Flows

**Root page (`/`):**
```tsx
// page.tsx
useEffect(() => {
  const token = localStorage.getItem("aicluster_token");  // legacy check
  if (token) router.push("/dashboard");
  else router.push("/login");
}, [router]);
```

**Dashboard Layout (auth guard):**
```tsx
// (dashboard)/layout.tsx
const token = useAuthStore((s) => s.token);
const [hydrated, setHydrated] = useState(false);

useEffect(() => { setHydrated(true); }, []);  // wait for persist hydration
useEffect(() => {
  if (hydrated && !token) router.push("/login");
}, [hydrated, token, router]);
```

The `hydrated` flag prevents a flash of the unprotected content before Zustand has rehydrated from `localStorage`. During hydration, a spinner is shown.

**Login page:**
```tsx
// login/page.tsx
const token = useAuthStore((s) => s.token);
useEffect(() => {
  if (token) router.push("/dashboard");  // already logged in → redirect
}, [token, router]);
```

### 9.4 Logout Flow

```
User clicks logout button in Topbar
  ↓
useAuthStore.getState().logout() → sets token=null, user=null
  ↓
Zustand persist middleware writes null to localStorage
  ↓
Dashboard layout detects token is falsy → router.push("/login")
  ↓
Login page renders (no token → stays on login)
```

---

## 10. How Pages Communicate

### 10.1 Web Frontend (Next.js) — URL Routing

Pages communicate exclusively through **URL navigation**. The sidebar renders `<Link>` components from `next/link`, which trigger client-side transitions without a full page reload:

```tsx
<Link href="/dashboard">Dashboard</Link>
<Link href="/workers">Workers</Link>
<Link href="/jobs">Jobs</Link>
<!-- ... -->
```

Shared state between pages is limited to:
- Authentication state via the Zustand `useAuthStore` (persisted)
- React Query cache (shared across components within the same page)

There is no global "current page" store for the web frontend — the URL is the single source of truth.

### 10.2 Tauri Apps (Vite) — In-Memory Store

The Tauri apps use a Zustand `app-store` to track the current page **in memory**:

**Master Control Center** (`master-control-center/frontend/src/stores/app-store.ts`):
```tsx
interface AppState {
  currentPage: string;
  sidebarOpen: boolean;
  setPage: (page: string) => void;
  toggleSidebar: () => void;
}
```

**Worker Control Center** (`worker-control-center/frontend/src/stores/app-store.ts`):
```tsx
interface AppState {
  currentPage: string;
  sidebarOpen: boolean;
  darkMode: boolean;
  setPage: (page: string) => void;
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
}
```

These stores are **not persisted** (no `persist` middleware). State is lost on app restart, which is acceptable because the Tauri apps are single-window desktop applications where the user starts from the dashboard each time.

### 10.3 Page Mapping

Both Tauri apps use a `Record<string, React.FC>` dictionary to map page names to components:

**Master:**
```tsx
const pages: Record<string, React.FC> = {
  dashboard: DashboardPage,
  workers: WorkersPage,
  jobs: JobsPage,
  cluster: ClusterPage,
  discovery: DiscoveryPage,
  backups: BackupsPage,
  diagnostics: DiagnosticsPage,
  notifications: NotificationsPage,
  logs: LogsPage,
  settings: SettingsPage,
  about: AboutPage,
};
```

**Worker:**
```tsx
const pages: Record<string, React.FC> = {
  welcome: WelcomePage,
  installation: InstallationPage,
  configuration: ConfigurationPage,
  "connection-test": ConnectionTestPage,
  dashboard: DashboardPage,
  logs: LogsPage,
  diagnostics: DiagnosticsPage,
  settings: SettingsPage,
  about: AboutPage,
};
```

The active page is resolved as: `const Page = pages[currentPage] || DashboardPage;`

---

## 11. How Zustand Works

AICluster uses Zustand v5 for state management across all UI applications. There are three distinct stores:

### 11.1 `useAuthStore` (Web Frontend Only)

| State | Type | Persisted | Description |
|---|---|---|---|
| `token` | `string \| null` | Yes (localStorage) | JWT access token |
| `user` | `UserResponse \| null` | Yes (localStorage) | Current user object |
| `login(username, password)` | `async function` | — | Authenticates and sets token+user |
| `logout()` | `function` | — | Clears token+user |

**Persistence key:** `"aicluster-auth"`  
**Partialize:** Only `token` and `user` are persisted (not the action functions).

### 11.2 `useAppStore` (Master Control Center)

| State | Type | Persisted | Description |
|---|---|---|---|
| `currentPage` | `string` | No | Currently displayed page name |
| `sidebarOpen` | `boolean` | No | Sidebar visibility toggle |
| `setPage(page)` | `function` | — | Navigate to a page |
| `toggleSidebar()` | `function` | — | Toggle sidebar |

### 11.3 `useAppStore` (Worker Control Center)

Same as Master plus:

| State | Type | Persisted | Description |
|---|---|---|---|
| `darkMode` | `boolean` | No | Dark/light mode toggle |

### 11.4 Why No Persist on App Stores?

The Tauri app stores are intentionally **not persisted** because:
1. The Tauri apps are single-window — the user always starts at dashboard
2. Page navigation state is ephemeral; restoring it would be more confusing than helpful
3. Tauri apps have file-system access; a future enhancement could persist to a local config file

### 11.5 Consumption Pattern

All components use **selector-based subscriptions** to minimize re-renders:

```tsx
// Good: only re-renders when `token` changes
const token = useAuthStore((s) => s.token);

// Good: only re-renders when `currentPage` changes
const currentPage = useAppStore((s) => s.currentPage);
```

---

## 12. How Routing Works

### 12.1 Web Frontend — Next.js File-System Router

The Next.js App Router uses a **file-system-based routing** paradigm:

| File Path | URL Route | Component |
|---|---|---|
| `app/page.tsx` | `/` | `Home` (redirect logic) |
| `app/login/page.tsx` | `/login` | `LoginPage` |
| `app/(dashboard)/layout.tsx` | shared layout | `DashboardLayout` (auth guard) |
| `app/(dashboard)/dashboard/page.tsx` | `/dashboard` | `DashboardPage` |
| `app/(dashboard)/workers/page.tsx` | `/workers` | Workers page |
| `app/(dashboard)/jobs/page.tsx` | `/jobs` | Jobs page |
| `app/(dashboard)/chat/page.tsx` | `/chat` | Chat page |
| `app/(dashboard)/projects/page.tsx` | `/projects` | Projects page |
| `app/(dashboard)/files/page.tsx` | `/files` | Files page |
| `app/(dashboard)/logs/page.tsx` | `/logs` | Logs page |
| `app/(dashboard)/analytics/page.tsx` | `/analytics` | Analytics page |
| `app/(dashboard)/settings/page.tsx` | `/settings` | Settings page |
| `app/(dashboard)/about/page.tsx` | `/about` | About page |
| `app/not-found.tsx` | `*` | 404 page |
| `app/error.tsx` | `*` | Error boundary |

The `(dashboard)` route group applies the `DashboardLayout` to all pages within it without adding `/dashboard` to the URL path — the pages are at `/dashboard`, `/workers`, etc., not `/dashboard/dashboard`.

### 12.2 Tauri Apps — Zustand-Based "Routing"

The Tauri apps do **not** use a URL-based router like `react-router-dom`. Instead, they implement a simple **state-driven page switching** pattern:

1. `useAppStore` holds `currentPage`
2. The sidebar calls `setPage("dashboard")`, `setPage("workers")`, etc.
3. `AppContent` reads `currentPage` and renders the corresponding component from a lookup map
4. No URL changes, no browser history, no deep linking

This is appropriate for a desktop Tauri app where:
- There is no address bar
- Navigation is always through the sidebar UI
- There is no need for shareable URLs

---

## 13. How the API Client Works

### 13.1 Web Frontend — Direct Fetch

The web frontend does **not** use a centralized API client library. Each component or store makes direct `fetch` calls with manual header construction:

**Auth store pattern:**
```tsx
const res = await fetch(`${API_URL}/api/v1/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
```

**Dashboard page pattern:**
```tsx
const res = await fetch(`${API_URL}/api/v1/dashboard`, {
  headers: { Authorization: `Bearer ${token}` },
});
if (res.status === 401) {
  useAuthStore.getState().logout();
  window.location.href = "/login";
}
```

This is a deliberate simplicity choice — the frontend has a small number of API endpoints, so a thin wrapper is not yet warranted. Common patterns (auth header injection, 401 handling, error normalization) are duplicated across files and could be extracted into a shared client utility in a future refactor.

### 13.2 Tauri Apps — Direct Fetch

The Tauri apps use the same direct `fetch` pattern, targeting their respective local backends:

```tsx
fetch('http://127.0.0.1:8800/api/health')
```

### 13.3 Backend API Endpoints

| Method | Path | Auth Required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/login` | No | Authenticate user |
| GET | `/api/v1/health` | No | Health check |
| GET | `/api/v1/dashboard` | Yes | Dashboard metrics |
| GET | `/api/v1/workers` | Yes | List workers |
| GET/POST/PUT/DELETE | `/api/v1/jobs` | Yes | Job CRUD |
| GET | `/api/v1/logs` | Yes | Log entries |
| WebSocket | `/ws` | No | Real-time events |
| GET | `/docs` | No | Swagger UI |
| GET | `/` | No | Legacy dashboard.html |

### 13.4 API Proxy Layer

In Next.js development, a rewrite proxy (`next.config.ts`) forwards `/api/*` to the backend, avoiding CORS. In production, the frontend is served from a different origin, so CORS middleware on the backend is configured to allow the frontend's origin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 14. Component Tree

### 14.1 Web Frontend — Full Component Hierarchy

```
<RootLayout>                          (Server component — layout.tsx)
  <ThemeProvider>                      (next-themes)
    <QueryProvider>                    (TanStack Query)
      ├── Route: /
      │   └── <Home>                   (Client — page.tsx: redirect to /login or /dashboard)
      │
      ├── Route: /login
      │   └── <LoginPage>              (Client — login/page.tsx)
      │       ├── Form (username, password)
      │       ├── Error alert
      │       └── Submit button
      │
      ├── Route group: (dashboard)
      │   └── <DashboardLayout>        (Client — auth guard)
      │       ├── <Sidebar>             (Navigation links)
      │       │   ├── Logo + brand
      │       │   ├── Nav items (Link components)
      │       │   └── Version info
      │       ├── <Topbar>
      │       │   ├── Search input
      │       │   ├── Notifications bell
      │       │   ├── Settings button
      │       │   └── User avatar + logout
      │       └── <main>
      │           ├── Route: /dashboard → <DashboardPage>
      │           │   ├── Metric cards (workers, jobs, CPU, RAM)
      │           │   └── Status panels (worker status, cluster summary)
      │           ├── Route: /workers → Workers page
      │           ├── Route: /jobs → Jobs page
      │           ├── Route: /chat → Chat page
      │           ├── Route: /projects → Projects page
      │           ├── Route: /files → Files page
      │           ├── Route: /logs → Logs page
      │           ├── Route: /analytics → Analytics page
      │           ├── Route: /settings → Settings page
      │           └── Route: /about → About page
      │
      ├── Route: 404
      │   └── <NotFound>               (not-found.tsx)
      │
      └── Route: error
          └── <Error>                  (error.tsx — error boundary)
```

### 14.2 Tauri Apps — Component Hierarchy

**Master Control Center:**
```
<React.StrictMode>
  <QueryClientProvider>
    <AppContent>
      ├── [Health check gate — shows loading until backend responds]
      ├── <div.app-layout>
      │   ├── <Sidebar />
      │   └── <main.main-content>
      │       └── <Page />            (resolved from currentPage)
      │           ├── DashboardPage
      │           ├── WorkersPage
      │           ├── JobsPage
      │           ├── ClusterPage
      │           ├── DiscoveryPage
      │           ├── BackupsPage
      │           ├── DiagnosticsPage
      │           ├── NotificationsPage
      │           ├── LogsPage
      │           ├── SettingsPage
      │           └── AboutPage
```

**Worker Control Center:**
```
<React.StrictMode>
  <QueryClientProvider>
    <AppContent>
      ├── [Health check gate — loading until backend responds]
      ├── <div.app-layout>
      │   ├── <Sidebar />
      │   └── <main.main-content>
      │       └── <Page />            (resolved from currentPage)
      │           ├── WelcomePage
      │           ├── InstallationPage
      │           ├── ConfigurationPage
      │           ├── ConnectionTestPage
      │           ├── DashboardPage
      │           ├── LogsPage
      │           ├── DiagnosticsPage
      │           ├── SettingsPage
      │           └── AboutPage
```

### 14.3 Auth Guard Flow (Web Frontend)

```
User navigates to /dashboard
  ↓
DashboardLayout mounts
  ↓
useState(false) for hydrated flag
  ↓
useEffect: setHydrated(true)  (runs after mount)
  ↓
if hydrated && !token:
  → router.push("/login")   (redirect to login)
if hydrated && token:
  → render <Sidebar> + <Topbar> + {children}
if !hydrated:
  → render spinner (prevent flash)
```

---

## 15. Theme System

### 15.1 Web Frontend — next-themes

The web frontend uses `next-themes` for dark/light mode support. Configuration is in the root layout:

```tsx
<ThemeProvider
  attribute="class"          // applies 'dark'/'light' class to <html>
  defaultTheme="dark"        // default to dark mode
  enableSystem={false}       // don't follow OS preference
  disableTransitionOnChange  // prevent FOUC during theme switch
>
```

The `ThemeProvider` is a thin wrapper component at `frontend/src/components/layout/theme-provider.tsx` that re-exports `next-themes`'s `ThemeProvider` with proper TypeScript typing.

**How it works:**
1. `next-themes` adds a `dark` or `light` class to the `<html>` element
2. Tailwind CSS uses the `class` strategy (`darkMode: "class"` in `tailwind.config.ts`) to toggle styles
3. CSS variables defined in `globals.css` change based on the class:
   ```css
   :root { --bg-primary: #ffffff; }
   .dark { --bg-primary: #0f172a; }
   ```
4. Components use Tailwind classes like `bg-background`, `text-foreground` that reference these variables

### 15.2 Tauri Apps — Manual Dark Mode (Worker Only)

The Worker Control Center has a `darkMode` toggle in its `app-store.ts`:

```tsx
interface AppState {
  darkMode: boolean;
  toggleDarkMode: () => void;
}
```

This is managed manually via a `useState`/`useEffect` pattern (adding/removing a class on the document body). The Master Control Center does not have theme switching — it uses a fixed dark theme defined in CSS.

### 15.3 CSS Architecture

All apps use **Tailwind CSS** for styling:
- **Web frontend:** Tailwind v3 (`tailwind.config.ts`)
- **Master & Worker:** Tailwind v4 (`@tailwindcss/vite` plugin, `tailwindcss: "^4.3.2"`)
- **Studio:** Tailwind v4

The web frontend uses a `glass` utility class for frosted-glass card effects (seen in login page and dashboard cards), status dots (`status-dot.online`, `status-dot.offline`), and gradient text (`text-gradient`).

---

## Summary: Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WEB FRONTEND (Next.js 15)                       │
│                                                                         │
│  Browser → next dev (port 3000)                                         │
│    ↓ rewrite /api/* → http://localhost:8000/api/*                       │
│    ↓ auth-store.ts → POST /api/v1/auth/login                           │
│    ↓ dashboard → GET /api/v1/dashboard (2s polling via React Query)     │
│    ↓ Zustand persist → localStorage("aicluster-auth")                   │
│                                                                         │
│  [React 18] [next-themes dark/light] [TanStack Query] [Zustand]        │
└──────────────────────┬──────────────────────────────────────────────────┘
                       │ HTTP (fetch)
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (Python FastAPI)                          │
│                                                                         │
│  uvicorn → FastAPI app (port 8000)                                      │
│    ├── POST /api/v1/auth/login → AuthService → JWT                      │
│    ├── GET /api/v1/dashboard → WorkerManagerService + SchedulerService  │
│    ├── GET /api/v1/health → 200 OK                                      │
│    ├── WebSocket /ws → WebSocketManager (broadcast)                     │
│    ├── CORS middleware (allow frontend origins)                          │
│    └── Lifespan: init_db → seed admin → start offline checker           │
│                                                                         │
│  [SQLAlchemy async] [PostgreSQL/SQLite] [jose JWT] [bcrypt]             │
└──────────────────────┬──────────────────────────────────────────────────┘
                       │ HTTP (fetch)
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  TAURI DESKTOP APPS (Vite + React 19)                    │
│                                                                         │
│  Master Control Center (port 5174 / 8800)                               │
│  Worker Control Center (port 5173 / 8900)                               │
│  Studio (port 5173 / no backend yet)                                    │
│                                                                         │
│  Cargo binary → tauri::Builder → WebView → Vite-built React app         │
│    ↓ Health check on mount: GET /api/health                             │
│    ↓ Zustand app-store (in-memory page routing)                         │
│    ↓ TanStack Query for data fetching                                   │
│    ↓ No persist middleware (ephemeral state)                             │
│                                                                         │
│  [React 19] [TanStack Query] [Zustand] [Tailwind v4]                   │
└─────────────────────────────────────────────────────────────────────────┘
```
