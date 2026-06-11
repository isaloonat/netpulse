import React from 'react';
import { DeviceState } from '../hooks/useDevices';
import { Sparkline } from './Sparkline';

interface Props {
  device: DeviceState;
  onClick: () => void;
}

export function DeviceCard({ device, onClick }: Props) {
  const isUp = device.status === 'up';
  const name = device.hostname ?? device.ip;
  const latency = device.last_latency_ms != null
    ? `${device.last_latency_ms.toFixed(1)} ms`
    : '—';

  return (
    <div className="device-card" onClick={onClick} role="button" tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onClick()}>
      <div style={s.header}>
        <div style={s.nameBlock}>
          <div style={s.name}>{name}</div>
          <div style={s.ip}>{device.ip}</div>
        </div>
        <span style={{
          ...s.badge,
          background: isUp ? 'rgba(74,222,128,0.12)' : 'rgba(248,113,113,0.12)',
          color: isUp ? 'var(--up)' : 'var(--down)',
        }}>
          {isUp ? 'UP' : 'DOWN'}
        </span>
      </div>

      <div style={s.metrics}>
        <Metric label="Latency" value={latency} />
        <Metric label="Uptime" value={`${device.uptime_pct}%`} />
      </div>

      <Sparkline data={device.sparkline} />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={s.metric}>
      <span style={s.metricLabel}>{label}</span>
      <span style={s.metricValue}>{value}</span>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  header: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 },
  nameBlock: { minWidth: 0 },
  name: { fontWeight: 600, fontSize: 15, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  ip: { fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 2 },
  badge: { fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', padding: '3px 8px', borderRadius: 4, flexShrink: 0 },
  metrics: { display: 'flex', gap: 24 },
  metric: { display: 'flex', flexDirection: 'column', gap: 1 },
  metricLabel: { fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' },
  metricValue: { fontSize: 15, fontWeight: 600, fontVariantNumeric: 'tabular-nums' },
};
