import React from 'react';
import { DeviceState } from '../hooks/useDevices';
import { DeviceCard } from './DeviceCard';

interface Props {
  devices: DeviceState[];
  onSelect: (ip: string) => void;
}

export function DeviceGrid({ devices, onSelect }: Props) {
  if (devices.length === 0) {
    return (
      <div style={s.empty}>
        <p style={{ fontSize: 16, fontWeight: 600 }}>Waiting for devices…</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 8 }}>
          Start the backend with <code style={s.code}>DEMO=1</code> to see simulated devices.
        </p>
      </div>
    );
  }

  return (
    <div style={s.grid}>
      {devices.map(d => (
        <DeviceCard key={d.ip} device={d} onClick={() => onSelect(d.ip)} />
      ))}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
    gap: 16,
    padding: 24,
  },
  empty: {
    textAlign: 'center',
    padding: 80,
    color: 'var(--text)',
  },
  code: {
    fontFamily: 'monospace',
    background: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: 4,
    padding: '1px 6px',
    fontSize: 12,
  },
};
