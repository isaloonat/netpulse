from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .demo import run_demo_loop
from .models import DeviceHistory, DeviceInfo
from .scanner import DeviceStore, run_monitoring_loop

store = DeviceStore()
_ws_clients: set[WebSocket] = set()


async def _broadcast(msg: dict[str, Any]) -> None:
    dead: set[WebSocket] = set()
    for ws in list(_ws_clients):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


@asynccontextmanager
async def lifespan(app: FastAPI):
    subnet = os.getenv("SUBNET", "192.168.1.0/24")
    interval = float(os.getenv("INTERVAL", "10"))

    if os.getenv("DEMO") == "1":
        task = asyncio.create_task(run_demo_loop(store, _broadcast))
    else:
        task = asyncio.create_task(
            run_monitoring_loop(store, _broadcast, subnet, interval)
        )
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="NetPulse", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/devices", response_model=list[DeviceInfo])
async def list_devices() -> list[DeviceInfo]:
    return store.all_info()


@app.get("/api/devices/{ip}/history", response_model=DeviceHistory)
async def device_history(ip: str) -> DeviceHistory:
    history = store.get_history(ip)
    if history is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return history


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        for device in store.all_info():
            await websocket.send_json({"type": "update", "device": device.model_dump()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)
