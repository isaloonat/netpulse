\# NetPulse — LAN Monitoring Dashboard



Two parts in one repo: backend/ (Python FastAPI) and frontend/ (React + Vite + TypeScript).



\## Backend (Python, FastAPI)

\- Scans a configurable subnet (e.g. 192.168.1.0/24) using ping sweeps; discovers

&#x20; live hosts and resolves hostnames where possible

\- Pings every known device on an interval (default 10s); stores last 100 latency

&#x20; samples per device in memory

\- REST API: GET /api/devices (list with status up/down, last latency, uptime %),

&#x20; GET /api/devices/{ip}/history

\- WebSocket /ws that pushes status changes and new latency samples live

\- DEMO MODE (env var DEMO=1): generates 8 fake devices with realistic simulated

&#x20; latency, jitter, and occasional outages — so the app runs anywhere without a

&#x20; real network or admin rights

\- pytest tests for the scanner parsing, status logic, and demo generator



\## Frontend (React + TypeScript)

\- Device grid: card per device — name, IP, up/down badge, current latency,

&#x20; sparkline of recent latency

\- Detail view per device: latency chart over time (last 100 samples)

\- Live updates via WebSocket — no refresh needed

\- Status bar: total devices, up/down counts, average latency

\- Dark theme, responsive



\## Quality

\- Clean separation: scanning logic separate from API layer

\- README with architecture diagram, screenshots, and demo instructions

