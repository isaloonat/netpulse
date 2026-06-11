from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Callable, Optional

from .scanner import DeviceStore

DEMO_INTERVAL = 3.0


@dataclass
class DemoDevice:
    ip: str
    hostname: str
    base_latency: float   # ms
    jitter: float         # std-dev in ms
    outage_prob: float    # probability of a None (down) sample


DEMO_DEVICES: list[DemoDevice] = [
    DemoDevice("192.168.1.1", "router",      5.0,  1.0, 0.005),
    DemoDevice("192.168.1.2", "nas",         8.0,  2.0, 0.010),
    DemoDevice("192.168.1.3", "desktop",    15.0,  3.0, 0.020),
    DemoDevice("192.168.1.4", "laptop",     12.0,  4.0, 0.030),
    DemoDevice("192.168.1.5", "printer",    25.0,  5.0, 0.050),
    DemoDevice("192.168.1.6", "smart-tv",   20.0,  8.0, 0.040),
    DemoDevice("192.168.1.7", "pi",         10.0,  2.0, 0.010),
    DemoDevice("192.168.1.8", "thermostat", 30.0, 10.0, 0.150),
]


def generate_sample(device: DemoDevice) -> Optional[float]:
    """Return a simulated latency (ms) or None for a transient outage."""
    if random.random() < device.outage_prob:
        return None
    return max(0.1, round(random.gauss(device.base_latency, device.jitter), 2))


async def run_demo_loop(
    store: DeviceStore,
    broadcast: Callable,
    interval: float = DEMO_INTERVAL,
) -> None:
    """Continuously emit samples for all demo devices."""
    while True:
        for dev in DEMO_DEVICES:
            latency = generate_sample(dev)
            rec, changed = store.record(dev.ip, latency, dev.hostname)
            await broadcast(
                {
                    "type": "status_change" if changed else "update",
                    "device": rec.to_info().model_dump(),
                }
            )
        await asyncio.sleep(interval)
