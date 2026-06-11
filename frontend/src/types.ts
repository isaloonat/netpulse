export interface LatencySample {
  timestamp: string;
  latency_ms: number | null;
}

export interface Device {
  ip: string;
  hostname: string | null;
  status: 'up' | 'down';
  last_latency_ms: number | null;
  uptime_pct: number;
}

export interface DeviceHistory extends Device {
  samples: LatencySample[];
}

export interface WsMessage {
  type: 'update' | 'status_change';
  device: Device;
}
