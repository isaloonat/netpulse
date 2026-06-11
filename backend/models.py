from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LatencySample(BaseModel):
    timestamp: datetime
    latency_ms: Optional[float] = None  # None means timeout / unreachable


class DeviceInfo(BaseModel):
    ip: str
    hostname: Optional[str] = None
    status: str  # "up" | "down"
    last_latency_ms: Optional[float] = None
    uptime_pct: float = 0.0


class DeviceHistory(DeviceInfo):
    samples: list[LatencySample] = []
