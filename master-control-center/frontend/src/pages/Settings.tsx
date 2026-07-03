export function SettingsPage() {
  return (
    <div style={{ maxWidth: 600 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>Settings</h1>
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>General</h3>
        <div style={{ marginBottom: 12 }}><label>Cluster Name</label><input defaultValue="AICluster" /></div>
        <div style={{ marginBottom: 12 }}><label>Master Name</label><input defaultValue="Master-01" /></div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" defaultChecked style={{ width: 'auto' }} /> Auto-discover workers</label>
      </div>
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Backup</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" defaultChecked style={{ width: 'auto' }} /> Automatic daily backups</label>
      </div>
      <div className="card">
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Notifications</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" defaultChecked style={{ width: 'auto' }} /> Worker Connected</label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" defaultChecked style={{ width: 'auto' }} /> Worker Offline</label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" defaultChecked style={{ width: 'auto' }} /> Job Failed</label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" defaultChecked style={{ width: 'auto' }} /> Backup Complete</label>
        </div>
      </div>
    </div>
  );
}
