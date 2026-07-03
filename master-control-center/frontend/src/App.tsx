import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useAppStore } from './stores/app-store';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardPage } from './pages/Dashboard';
import { WorkersPage } from './pages/Workers';
import { JobsPage } from './pages/Jobs';
import { ClusterPage } from './pages/Cluster';
import { DiscoveryPage } from './pages/Discovery';
import { BackupsPage } from './pages/Backups';
import { DiagnosticsPage } from './pages/Diagnostics';
import { NotificationsPage } from './pages/Notifications';
import { LogsPage } from './pages/Logs';
import { SettingsPage } from './pages/Settings';
import { AboutPage } from './pages/About';

const queryClient = new QueryClient();

function AppContent() {
  const currentPage = useAppStore((s) => s.currentPage);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    fetch('http://127.0.0.1:8800/api/health')
      .then((r) => r.json())
      .then(() => setReady(true))
      .catch(() => setTimeout(() => setReady(true), 3000));
  }, []);

  const pages: Record<string, React.FC> = {
    dashboard: DashboardPage, workers: WorkersPage, jobs: JobsPage, cluster: ClusterPage,
    discovery: DiscoveryPage, backups: BackupsPage, diagnostics: DiagnosticsPage,
    notifications: NotificationsPage, logs: LogsPage, settings: SettingsPage, about: AboutPage,
  };
  const Page = pages[currentPage] || DashboardPage;

  if (!ready) return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}><h2 style={{ color: '#6366f1' }}>Master Control Center</h2></div>;
  return <div className="app-layout"><Sidebar /><main className="main-content"><Page /></main></div>;
}

export default function App() {
  return <QueryClientProvider client={queryClient}><AppContent /></QueryClientProvider>;
}
