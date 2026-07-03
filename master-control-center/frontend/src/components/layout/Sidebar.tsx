import { BarChart3, Cpu, List, Globe, RefreshCw, Archive, AlertTriangle, Bell, FileText, Settings, Info, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../stores/app-store';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'workers', label: 'Workers', icon: Cpu },
  { id: 'jobs', label: 'Jobs', icon: List },
  { id: 'cluster', label: 'Cluster', icon: Globe },
  { id: 'discovery', label: 'Discovery', icon: RefreshCw },
  { id: 'backups', label: 'Backups', icon: Archive },
  { id: 'diagnostics', label: 'Diagnostics', icon: AlertTriangle },
  { id: 'notifications', label: 'Alerts', icon: Bell },
  { id: 'logs', label: 'Logs', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'about', label: 'About', icon: Info },
];

export function Sidebar() {
  const currentPage = useAppStore((s) => s.currentPage);
  const setPage = useAppStore((s) => s.setPage);
  const open = useAppStore((s) => s.sidebarOpen);
  const toggle = useAppStore((s) => s.toggleSidebar);

  return (
    <aside style={{ width: open ? 240 : 60, transition: 'width 0.2s', background: '#12121a', height: '100vh', borderRight: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column', padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        {open && <h2 style={{ fontSize: 16, fontWeight: 700, color: '#6366f1' }}>Master Control</h2>}
        <button className="btn btn-secondary" style={{ padding: 6, minWidth: 32 }} onClick={toggle}>
          {open ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button key={item.id} className={`sidebar-link${isActive ? ' active' : ''}`} style={{ justifyContent: open ? 'flex-start' : 'center' }} onClick={() => setPage(item.id)}>
              <Icon size={18} />
              {open && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
