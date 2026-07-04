# AICluster v1.3.1 UI Implementation Plan

## Current UI Status

| App | Pages | Status |
|-----|-------|--------|
| Web Dashboard (Next.js) | 12 routes | 2 live, 8 placeholders, 2 (error/404) |
| Master Control Center (Tauri) | 11 pages | All functional |
| Worker Control Center (Tauri) | 9 pages | All functional |
| Studio IDE (Tauri) | 1 | Starter template |

---

## F-001: Dashboard Placeholder Pages

**Issue**: 8 of 10 dashboard pages show "coming soon" placeholders.

**Pages to Implement**:

### 1. Jobs Page (`frontend/src/app/(dashboard)/jobs/page.tsx`)

**Current**: Placeholder with Briefcase icon.

**Implementation**:
- Fetch from: `GET /api/v1/jobs`
- Display: Table of jobs with columns: ID, Type, Status, Priority, Progress, Worker, Created
- Status badges: QUEUED (gray), RUNNING (blue), COMPLETED (green), FAILED (red), CANCELLED (orange)
- Actions: Cancel button for running/queued jobs
- Empty state: "No jobs yet"
- Loading: Table skeleton
- Error: Error message with retry

**API Requirements**: None beyond existing `GET /api/v1/jobs`

**Files**: `frontend/src/app/(dashboard)/jobs/page.tsx`
**Estimated time**: 2h

### 2. Logs Page (`frontend/src/app/(dashboard)/logs/page.tsx`)

**Current**: Placeholder with ScrollText icon.

**Implementation**:
- Fetch from: `GET /api/v1/logs?level=&limit=&offset=`
- Display: Scrollable log list with timestamps, levels (color-coded), source, message
- Filter: Level dropdown (ALL, INFO, WARNING, ERROR)
- Search: Filter by message text
- Auto-refresh: Every 10s
- Empty state: "No logs"
- Loading: Spinner

**Files**: `frontend/src/app/(dashboard)/logs/page.tsx`
**Estimated time**: 2h

### 3. Chat Page (`frontend/src/app/(dashboard)/chat/page.tsx`)

**Current**: Placeholder with Bot icon.

**Implementation**:
- Fetch from: `POST /api/v1/ai/chat`
- Display: Chat message list (user + assistant bubbles)
- Input: Text area + Send button
- Session management: Create session on first message
- Empty state: "Start a conversation"
- Loading: Typing indicator during AI response

**Files**: `frontend/src/app/(dashboard)/chat/page.tsx`
**Estimated time**: 3h

### 4. Projects Page (`frontend/src/app/(dashboard)/projects/page.tsx`)

**Current**: Placeholder with FolderTree icon.

**Implementation**:
- Fetch from: `GET /api/v1/studio/projects`
- Display: Project cards with name, description, language, created date
- Empty state: "No projects yet"
- Loading: Card skeletons

**Files**: `frontend/src/app/(dashboard)/projects/page.tsx`
**Estimated time**: 1.5h

### 5. Files Page (`frontend/src/app/(dashboard)/files/page.tsx`)

**Current**: Placeholder with Files icon.

**Implementation**:
- Fetch from: `GET /api/v1/repositories/{id}/files`
- Display: File browser with folder navigation
- Breadcrumb navigation
- File icons by type
- Read-only file viewer for source code
- Empty state: "Add a repository first"

**Files**: `frontend/src/app/(dashboard)/files/page.tsx`
**Estimated time**: 3h

### 6. Analytics Page (`frontend/src/app/(dashboard)/analytics/page.tsx`)

**Current**: Placeholder with BarChart3 icon.

**Implementation**:
- Fetch from: `GET /api/v1/dashboard`, `GET /api/v1/production/monitoring`
- Display: Charts using recharts (already installed):
  - Worker CPU utilization over time
  - Job completion rate
  - Worker status distribution (pie chart)
  - System resource trends
- Time range selector: 1h, 6h, 24h, 7d
- Loading: Chart skeletons

**Files**: `frontend/src/app/(dashboard)/analytics/page.tsx`
**Estimated time**: 4h

### 7. Settings Page (`frontend/src/app/(dashboard)/settings/page.tsx`)

**Current**: Placeholder with Settings icon.

**Implementation**:
- Display: Settings form (read-only for v1.3.1):
  - General: Cluster name, version
  - Auth: User management (list users)
  - Worker: Default limits, timeouts
  - System: Log level, auto-restart
- Note: v1.3.1 is read-only display of settings from API. Editing comes in v1.4.0.

**Files**: `frontend/src/app/(dashboard)/settings/page.tsx`
**Estimated time**: 2h

### 8. Chat Page (duplicate reference — same as #3 above)

**Files**: `frontend/src/app/(dashboard)/chat/page.tsx`
**Estimated time**: 3h

### Total Estimated Time: ~19h

---

## F-003: Frontend WebSocket Integration

**Issue**: Dashboard uses polling (2s interval) instead of WebSocket for real-time updates.

**Implementation**:

Create `frontend/src/lib/websocket.ts`:
```typescript
class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  constructor() {
    this.url = `ws://localhost:8000/ws?token=${localStorage.getItem('aicluster_token')}`;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => console.log('WS connected');
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const handlers = this.listeners.get(msg.type);
      handlers?.forEach(h => h(msg.data));
    };
    this.ws.onclose = () => this.scheduleReconnect();
    this.ws.onerror = () => this.ws?.close();
  }

  on(event: string, handler: (data: any) => void) {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(handler);
  }

  off(event: string, handler: (data: any) => void) {
    this.listeners.get(event)?.delete(handler);
  }

  private scheduleReconnect() {
    this.reconnectTimer = setTimeout(() => this.connect(), 5000);
  }

  disconnect() {
    this.ws?.close();
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
  }
}

export const wsClient = new WebSocketClient();
```

**Integration with Dashboard**:
- Replace React Query polling with WebSocket events
- `worker_update` → update workers list
- `job_update` → update jobs list
- `dashboard` → update metrics
- Keep polling as fallback if WebSocket disconnects

**Files**: `frontend/src/lib/websocket.ts`, `frontend/src/app/(dashboard)/dashboard/page.tsx`, `frontend/src/app/(dashboard)/workers/page.tsx`
**Estimated time**: 4h

---

## F-002: Studio IDE Improvements

**Issue**: Studio is default Vite starter template. All installed dependencies (zustand, react-query, resizable-panels, tailwindcss) are unused.

**Scope for v1.3.1**: Minimal implementation — not a full IDE.

**Implementation**:

1. Replace `src/App.tsx` with basic layout:
   - Sidebar with navigation: Workspaces, Projects, AI Chat
   - Main content area (routed by state)
   - Connect to master API

2. Workspace List page:
   - Fetch: `GET /api/v1/studio/workspaces`
   - Display workspace cards

3. Project List page:
   - Fetch: `GET /api/v1/studio/projects?workspace_id=X`
   - Display project cards

4. AI Chat page:
   - Fetch: `POST /api/v1/ai/chat`
   - Basic chat interface

**Files**: `studio/src/App.tsx`, `studio/src/App.css`, `studio/src/index.css`, new component files
**Estimated time**: 6h

---

## State Management Improvements

**Issue**: `auth-store.ts` stores JWT in localStorage (vulnerable to XSS).

**Fix for v1.3.1**: (in Sprint 3 with cookie auth)

1. Check for httpOnly cookie on app mount
2. If cookie present, decode JWT from cookie for user info
3. Fall back to Bearer token header for API calls
4. Implement CSRF token for state-changing requests

**Files**: `frontend/src/stores/auth-store.ts`, `frontend/src/lib/api.ts`
**Estimated time**: 3h

---

## UI Testing

**New Tests** (Sprint 4):

| File | Tests |
|------|-------|
| `frontend/src/__tests__/auth-store.test.ts` | Login, logout, token persistence |
| `frontend/src/__tests__/api.test.ts` | API client works |
| `frontend/src/app/login/__tests__/page.test.tsx` | Login form renders, submits |
| `frontend/src/components/layout/__tests__/sidebar.test.tsx` | Navigation items, active state |
| `frontend/src/app/(dashboard)/dashboard/__tests__/page.test.tsx` | Dashboard renders with data |

**Framework**: Vitest + @testing-library/react

---

## Summary

| Feature | Sprint | Effort | Risk |
|---------|--------|--------|------|
| Jobs page | 4 | 2h | LOW |
| Logs page | 4 | 2h | LOW |
| Chat page | 4 | 3h | LOW |
| Projects page | 4 | 1.5h | LOW |
| Files page | 4 | 3h | LOW |
| Analytics page | 4 | 4h | MEDIUM |
| Settings page | 4 | 2h | LOW |
| WebSocket integration | 3 | 4h | MEDIUM |
| Studio improvements | 4 | 6h | LOW |
| Cookie auth | 3 | 3h | MEDIUM |
| **Total** | | **~30.5h** | |
