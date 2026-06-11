from __future__ import annotations

import asyncio
import ipaddress
import platform
import re
import socket
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Callable, Optional

from .models import DeviceHistory, DeviceInfo, LatencySample

SAMPLE_MAX = 100
MONITOR_INTERVAL = 10.0
SCAN_CONCURRENCY = 50
PING_TIMEOUT = 2.0


def _ping_cmd(ip: str) -> list[str]:
    if platform.system() == "Windows":
        return ["ping", "-n", "1", "-w", "1000", ip]
    return ["ping", "-c", "1", "-W", "1", ip]


def _parse_latency(output: str) -> Optional[float]:
    """Extract RTT in ms from ping stdout (Windows and Linux/macOS formats)."""
    m = re.search(r"time[=<](\d+(?:\.\d+)?)\s*ms", output, re.IGNORECASE)
    return float(m.group(1)) if m else None


async def ping_host(ip: str) -> Optional[float]:
    """Async ping. Returns latency in ms or None on failure / timeout."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *_ping_cmd(ip),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=PING_TIMEOUT)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return None
        if proc.returncode != 0:
            return None
        return _parse_latency(stdout.decode(errors="replace"))
    except Exception:
        return None


def _resolve_hostname(ip: str) -> Optional[str]:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


async def scan_subnet(subnet: str) -> list[str]:
    """Ping-sweep a subnet concurrently; return list of live IPs."""
    network = ipaddress.ip_network(subnet, strict=False)
    sem = asyncio.Semaphore(SCAN_CONCURRENCY)

    async def check(ip_str: str) -> Optional[str]:
        async with sem:
            return ip_str if await ping_host(ip_str) is not None else None

    results = await asyncio.gather(*[check(str(h)) for h in network.hosts()])
    return [ip for ip in results if ip is not None]


class DeviceRecord:
    def __init__(self, ip: str, hostname: Optional[str] = None) -> None:
        self.ip = ip
        self.hostname = hostname
        self._samples: deque[LatencySample] = deque(maxlen=SAMPLE_MAX)
        self._lock = threading.Lock()

    def add_sample(self, latency_ms: Optional[float]) -> None:
        with self._lock:
            self._samples.append(
                LatencySample(
                    timestamp=datetime.now(timezone.utc), latency_ms=latency_ms
                )
            )

    @property
    def status(self) -> str:
        with self._lock:
            if not self._samples:
                return "down"
            return "up" if self._samples[-1].latency_ms is not None else "down"

    @property
    def last_latency_ms(self) -> Optional[float]:
        with self._lock:
            return self._samples[-1].latency_ms if self._samples else None

    @property
    def uptime_pct(self) -> float:
        with self._lock:
            if not self._samples:
                return 0.0
            up = sum(1 for s in self._samples if s.latency_ms is not None)
            return round(up / len(self._samples) * 100, 1)

    def to_info(self) -> DeviceInfo:
        return DeviceInfo(
            ip=self.ip,
            hostname=self.hostname,
            status=self.status,
            last_latency_ms=self.last_latency_ms,
            uptime_pct=self.uptime_pct,
        )

    def to_history(self) -> DeviceHistory:
        with self._lock:
            samples = list(self._samples)
        return DeviceHistory(
            ip=self.ip,
            hostname=self.hostname,
            status=self.status,
            last_latency_ms=self.last_latency_ms,
            uptime_pct=self.uptime_pct,
            samples=samples,
        )


class DeviceStore:
    def __init__(self) -> None:
        self._records: dict[str, DeviceRecord] = {}
        self._lock = threading.Lock()

    def get_or_create(self, ip: str, hostname: Optional[str] = None) -> DeviceRecord:
        with self._lock:
            if ip not in self._records:
                self._records[ip] = DeviceRecord(ip, hostname)
            return self._records[ip]

    def record(
        self,
        ip: str,
        latency_ms: Optional[float],
        hostname: Optional[str] = None,
    ) -> tuple[DeviceRecord, bool]:
        """Add a sample. Returns (record, status_changed)."""
        rec = self.get_or_create(ip, hostname)
        old_status = rec.status
        rec.add_sample(latency_ms)
        return rec, rec.status != old_status

    def all_info(self) -> list[DeviceInfo]:
        with self._lock:
            return [r.to_info() for r in self._records.values()]

    def get_history(self, ip: str) -> Optional[DeviceHistory]:
        with self._lock:
            rec = self._records.get(ip)
        return rec.to_history() if rec is not None else None


async def _probe(ip: str, store: DeviceStore, broadcast: Callable) -> None:
    latency = await ping_host(ip)
    rec, changed = store.record(ip, latency)
    await broadcast(
        {
            "type": "status_change" if changed else "update",
            "device": rec.to_info().model_dump(),
        }
    )


async def run_monitoring_loop(
    store: DeviceStore,
    broadcast: Callable,
    subnet: str = "192.168.1.0/24",
    interval: float = MONITOR_INTERVAL,
) -> None:
    loop = asyncio.get_running_loop()

    live_ips = await scan_subnet(subnet)
    for ip in live_ips:
        hostname = await loop.run_in_executor(None, _resolve_hostname, ip)
        store.get_or_create(ip, hostname)

    while True:
        with store._lock:
            ips = list(store._records.keys())
        await asyncio.gather(*[_probe(ip, store, broadcast) for ip in ips])
        await asyncio.sleep(interval)
