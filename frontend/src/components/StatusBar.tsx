import React from 'react';
import { DeviceState } from '../hooks/useDevices';

interface Props {
  devices: DeviceState[];
  connected: boolean;
}

export function StatusBar({ devices, connected }: Props) {
  const up = devices.filter(d => d.status === 'up');
  const down = devices.filter(d => d.status === 'down');
  const avgLatency = up.length > 0
    ? (up.reduce((sum, d) => sum + (d.last_latency_ms ?? 0), 0) / up.length).toFixed(1)
    : null;

  return (
    <header style={s.bar}>
      <span style={s.brand}>NetPulse</span>
      <div style={s.stats}>
        <Stat label="Total" value={devices.length} />
        <Divider />
        <Stat label="Up" value={up.length} color={up.length > 0 ? 'var(--up)' : undefined} />
        <Stat label="Down" value={down.length} color={down.length > 0 ? 'var(--down)' : undefined} />
        <Divider />
        <Stat label="Avg latency" value={avgLatency != null ? `${avgLatency} ms` : '—'} />
        <Divider />
        <span style={{ ...s.liveTag, color: connected ? 'var(--up)' : 'var(--text-muted)' }}>
          <span style={{ ...s.dot, background: connected ? 'var(--up)' : 'var(--text-muted)' }} />
          {connected ? 'Live' : 'Connecting…'}
        </span>
      </div>
    </header>
  );
}

function Stat({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div style={s.stat}>
      <span style={s.statLabel}>{label}</span>
      <span style={{ ...s.statValue, color }}>{value}</span>
    </div>
  );
}

function Divider() {
  return <div style={s.divider} />;
}

const s: Record<string, React.CSSProperties> = {
  bar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 12,
    padding: '12px 24px',
    background: 'var(--bg-card)',
    borderBottom: '1px solid var(--border)',
    position: 'sticky',
    top: 0,
    zIndex: 10,
  },
  brand: {
    fontWeight: 800,
    fontSize: 18,
    color: 'var(--accent)',
    letterSpacing: '-0.03em',
  },
  stats: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    flexWrap: 'wrap',
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 1,
  },
  statLabel: {
    fontSize: 10,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
  },
  statValue: {
    fontSize: 15,
    fontWeight: 700,
    fontVariantNumeric: 'tabular-nums',
    color: 'var(--text)',
  },
  divider: {
    width: 1,
    height: 28,
    background: 'var(--border)',
  },
  liveTag: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    fontWeight: 600,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: '50%',
    display: 'inline-block',
  },
};
