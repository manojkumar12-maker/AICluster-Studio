import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardPage } from './pages/Dashboard';
import { WelcomePage } from './pages/Welcome';
import { InstallationPage } from './pages/Installation';
import { ConfigurationPage } from './pages/Configuration';
import { ConnectionTestPage } from './pages/ConnectionTest';
import { LogsPage } from './pages/Logs';
import { DiagnosticsPage } from './pages/Diagnostics';
import { SettingsPage } from './pages/Settings';
import { AboutPage } from './pages/About';
import { useAppStore } from './stores/app-store';

const queryClient = new QueryClient();

function AppContent() {
  const currentPage = useAppStore((s) => s.currentPage);
  const [ccReady, setCCReady] = useState(false);

  useEffect(() => {
    fetch('http://127.0.0.1:8900/api/health')
      .then((r) => r.json())
      .then(() => setCCReady(true))
      .catch(() => setTimeout(() => setCCReady(true), 3000));
  }, []);

  if (!ccReady) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: 'var(--accent)', marginBottom: 12 }}>AICluster Worker Control Center</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Connecting to local service...</p>
        </div>
      </div>
    );
  }

  const pages: Record<string, React.FC> = {
    welcome: WelcomePage,
    installation: InstallationPage,
    configuration: ConfigurationPage,
    'connection-test': ConnectionTestPage,
    dashboard: DashboardPage,
    logs: LogsPage,
    diagnostics: DiagnosticsPage,
    settings: SettingsPage,
    about: AboutPage,
  };

  const Page = pages[currentPage] || DashboardPage;

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Page />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
