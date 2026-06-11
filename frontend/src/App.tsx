import { useState } from 'react';
import { useDevices } from './hooks/useDevices';
import { StatusBar } from './components/StatusBar';
import { DeviceGrid } from './components/DeviceGrid';
import { DetailView } from './components/DetailView';

export default function App() {
  const { devices, connected } = useDevices();
  const [selectedIp, setSelectedIp] = useState<string | null>(null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <StatusBar devices={devices} connected={connected} />
      <main style={{ flex: 1 }}>
        <DeviceGrid devices={devices} onSelect={setSelectedIp} />
      </main>
      {selectedIp !== null && (
        <DetailView ip={selectedIp} onClose={() => setSelectedIp(null)} />
      )}
    </div>
  );
}
