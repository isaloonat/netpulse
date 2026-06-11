import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts';
import { DeviceHistory } from '../types';

interface Props {
  ip: string;
  onClose: () => void;
}

interface ChartPoint {
  time: string;
  ms: number | null;
}

export function DetailView({ ip, onClose }: Props) {
  const [history, setHistory] = useState<DeviceHistory | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setHistory(null);
    setError(null);
    fetch(`http://localhost:8000/api/devices/${ip}/history`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<DeviceHistory>;
      })
      .then(setHistory)
      .catch(() => setError('Failed to load device history.'));
  }, [ip]);

  const chartData: ChartPoint[] = (history?.samples ?? []).map(s => ({
    time: new Date(s.timestamp).toLocaleTimeString(),
    ms: s.latency_ms,
  }));

  const isUp = history?.status === 'up';

  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.panel} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={s.panelHeader}>
          <div>
            <div style={s.panelTitle}>{history?.hostname ?? ip}</div>
            <div style={s.panelIp}>{ip}</div>
          </div>
          <button style={s.closeBtn} onClick={onClose} aria-label="Close">✕</button>
        </div>

        {error && <p style={{ color: 'var(--down)', fontSize: 13 }}>{error}</p>}

        {history && (
          <div style={s.chips}>
            <Chip label="Status" value={history.status.toUpperCase()}
              color={isUp ? 'var(--up)' : 'var(--down)'} />
            <Chip label="Last latency"
              value={history.last_latency_ms != null ? `${history.last_latency_ms.toFixed(1)} ms` : '—'} />
            <Chip label="Uptime" value={`${history.uptime_pct}%`} />
            <Chip label="Samples" value={history.samples.length} />
          </div>
        )}

        {/* Chart */}
        <div style={s.chartWrap}>
          {chartData.length === 0 && !error && (
            <div style={s.chartPlaceholder}>Loading…</div>
          )}
          {chartData.length > 0 && (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                  interval="preserveStartEnd"
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                  unit=" ms"
                  width={54}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg)',
                    border: '1px solid var(--border)',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: 'var(--text-muted)', marginBottom: 4 }}
                  itemStyle={{ color: 'var(--accent)' }}
                  formatter={(v) => {
                    const ms = typeof v === 'number' ? `${v.toFixed(2)} ms` : '—';
                    return [ms, 'Latency'];
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="ms"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  dot={false}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

function Chip({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div style={s.chip}>
      <span style={s.chipLabel}>{label}</span>
      <span style={{ ...s.chipValue, color }}>{value}</span>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.65)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
    padding: 16,
  },
  panel: {
    background: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: 12,
    width: '100%',
    maxWidth: 700,
    maxHeight: '90vh',
    overflowY: 'auto',
    padding: 28,
    display: 'flex',
    flexDirection: 'column',
    gap: 22,
  },
  panelHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  panelTitle: { fontWeight: 700, fontSize: 22 },
  panelIp: { fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 4 },
  closeBtn: {
    background: 'none',
    border: '1px solid var(--border)',
    borderRadius: 6,
    color: 'var(--text-muted)',
    padding: '5px 10px',
    fontSize: 14,
    flexShrink: 0,
  },
  chips: { display: 'flex', gap: 10, flexWrap: 'wrap' },
  chip: {
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    padding: '10px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 3,
    minWidth: 100,
  },
  chipLabel: {
    fontSize: 10,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  },
  chipValue: { fontSize: 18, fontWeight: 700, fontVariantNumeric: 'tabular-nums' },
  chartWrap: { minHeight: 260 },
  chartPlaceholder: {
    height: 260,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--text-muted)',
    fontSize: 13,
  },
};
