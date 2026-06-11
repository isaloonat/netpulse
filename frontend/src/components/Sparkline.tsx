import { ResponsiveContainer, AreaChart, Area } from 'recharts';

interface Props {
  data: (number | null)[];
}

export function Sparkline({ data }: Props) {
  const chartData = data.map((v, i) => ({ i, v: v ?? 0 }));

  return (
    <ResponsiveContainer width="100%" height={36}>
      <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
        <Area
          type="monotone"
          dataKey="v"
          stroke="var(--accent)"
          strokeWidth={1.5}
          fill="rgba(129,140,248,0.15)"
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
