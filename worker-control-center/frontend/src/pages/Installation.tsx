import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Check, X, Loader, ArrowRight, ArrowLeft, Play, Cpu, Wifi } from 'lucide-react';
import { api } from '../lib/api';

const steps = ['Welcome', 'System Requirements', 'Install Dependencies', 'Configure Worker', 'Test Connection', 'Register Worker', 'Start Worker', 'Finish'];

export function InstallationPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const { data: sysInfo } = useQuery({ queryKey: ['sysinfo'], queryFn: api.getSystemInfo });
  const installMutation = useMutation({ mutationFn: api.runInstall });

  const checks = sysInfo ? [
    { label: 'Windows OS', ok: !!sysInfo.os },
    { label: 'Python Installed', ok: !!sysInfo.python_path },
    { label: 'Disk Space (>1GB)', ok: sysInfo.disk_free_gb > 1 },
    { label: 'RAM (>2GB)', ok: sysInfo.ram_total_gb > 2 },
    { label: 'CPU Cores (>1)', ok: (sysInfo.cpu_count ?? 0) > 1 },
    { label: 'Worker Folder', ok: sysInfo.worker_folder_exists },
  ] : [];

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Installation Wizard</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>Step {currentStep + 1} of {steps.length}: {steps[currentStep]}</p>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
        {steps.map((_, i) => (
          <div key={i} style={{ flex: 1, height: 4, borderRadius: 2, background: i <= currentStep ? 'var(--accent)' : 'var(--border-color)', transition: 'background 0.3s' }} />
        ))}
      </div>

      {currentStep === 0 && (
        <div className="card">
          <h2 style={{ fontSize: 18, marginBottom: 12 }}>Welcome to AICluster Worker Installation</h2>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            This wizard will guide you through installing and configuring an AICluster Worker node.
          </p>
        </div>
      )}

      {currentStep === 1 && (
        <div className="card">
          <h3 style={{ fontSize: 15, marginBottom: 12 }}>System Requirements</h3>
          {checks.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {checks.map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                  {c.ok ? <Check size={16} style={{ color: 'var(--success)' }} /> : <X size={16} style={{ color: 'var(--error)' }} />}
                  <span style={{ fontSize: 14 }}>{c.label}</span>
                </div>
              ))}
            </div>
          ) : <p style={{ color: 'var(--text-secondary)' }}>Checking system...</p>}
        </div>
      )}

      {currentStep === 2 && (
        <div className="card">
          <h3 style={{ fontSize: 15, marginBottom: 12 }}>Install Dependencies</h3>
          {installMutation.isPending ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Loader size={20} style={{ color: 'var(--accent)', animation: 'spin 1s linear infinite' }} />
              <span>Installing Python packages...</span>
            </div>
          ) : installMutation.isSuccess ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--success)' }}>
              <Check size={20} /> <span>{installMutation.data.message}</span>
            </div>
          ) : installMutation.isError ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--error)' }}>
              <X size={20} /> <span>{installMutation.error.message}</span>
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)' }}>Click install to begin.</p>
          )}
          {!installMutation.isSuccess && !installMutation.isPending && (
            <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => installMutation.mutate()}>
              <Play size={16} /> Install Dependencies
            </button>
          )}
        </div>
      )}

      {currentStep >= 3 && currentStep <= 6 && (
        <div className="card">
          <h3 style={{ fontSize: 15, marginBottom: 12 }}>{steps[currentStep]}</h3>
          <p style={{ color: 'var(--text-secondary)' }}>Use the Configuration, Connection Test, and Dashboard pages to complete this step.</p>
          {currentStep === 3 && <Cpu size={32} style={{ color: 'var(--accent)', marginTop: 12 }} />}
          {currentStep === 4 && <Wifi size={32} style={{ color: 'var(--accent)', marginTop: 12 }} />}
        </div>
      )}

      {currentStep === 7 && (
        <div className="card" style={{ textAlign: 'center', padding: 40 }}>
          <Check size={48} style={{ color: 'var(--success)', marginBottom: 16 }} />
          <h2 style={{ fontSize: 20, marginBottom: 8 }}>Installation Complete</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Your AICluster Worker is ready.</p>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 24 }}>
        <button className="btn btn-secondary" disabled={currentStep === 0} onClick={() => setCurrentStep(s => s - 1)}>
          <ArrowLeft size={16} /> Previous
        </button>
        <button className="btn btn-primary" disabled={currentStep === 7} onClick={() => setCurrentStep(s => s + 1)}>
          Next <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
