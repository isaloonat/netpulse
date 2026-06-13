import { useState, useEffect } from 'react';
import { Device, WsMessage } from '../types';

const WS_URL = 'ws://localhost:8002/ws';
const SPARKLINE_MAX = 20;

export interface DeviceState extends Device {
  sparkline: (number | null)[];
}

export function useDevices() {
  const [devices, setDevices] = useState<Record<string, DeviceState>>({});
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket;
    let dead = false;
    let reconnectTimer: number;

    const connect = () => {
      if (dead) return;
      ws = new WebSocket(WS_URL);

      ws.onopen = () => setConnected(true);

      ws.onmessage = (e: MessageEvent) => {
        const { device } = JSON.parse(e.data as string) as WsMessage;
        setDevices(prev => {
          const existing = prev[device.ip];
          const sparkline = [
            ...(existing?.sparkline ?? []),
            device.last_latency_ms,
          ].slice(-SPARKLINE_MAX);
          return { ...prev, [device.ip]: { ...device, sparkline } };
        });
      };

      ws.onclose = () => {
        setConnected(false);
        if (!dead) reconnectTimer = window.setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      dead = true;
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  return { devices: Object.values(devices), connected };
}
