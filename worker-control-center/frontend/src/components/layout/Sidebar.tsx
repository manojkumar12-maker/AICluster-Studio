import { Activity, Settings, Terminal, Wifi, BarChart3, FileText, AlertTriangle, Info, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../stores/app-store';

const navItems = [
  { id: 'welcome', label: 'Welcome', icon: Info },
  { id: 'installation', label: 'Installation', icon: Terminal },
  { id: 'configuration', label: 'Configuration', icon: Settings },
  { id: 'connection-test', label: 'Connection Test', icon: Wifi },
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'logs', label: 'Logs', icon: FileText },
  { id: 'diagnostics', label: 'Diagnostics', icon: AlertTriangle },
  { id: 'about', label: 'About', icon: Activity },
];

export function Sidebar() {
  const currentPage = useAppStore((s) => s.currentPage);
  const setPage = useAppStore((s) => s.setPage);
  const open = useAppStore((s) => s.sidebarOpen);
  const toggle = useAppStore((s) => s.toggleSidebar);

  return (
    <aside className="sidebar" style={{ width: open ? 240 : 60, transition: 'width 0.2s' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, padding: open ? '0 4px' : '0' }}>
        {open && <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent)' }}>AICluster</h2>}
        <button className="btn btn-secondary" style={{ padding: 6, minWidth: 32 }} onClick={toggle}>
          {open ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              className="sidebar-link"
              style={{
                justifyContent: open ? 'flex-start' : 'center',
                background: isActive ? 'rgba(99,102,241,0.1)' : 'transparent',
                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
              }}
              onClick={() => setPage(item.id)}
            >
              <Icon size={18} />
              {open && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
