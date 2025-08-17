# router/ws.py
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from infrustructure.ws_bus import bus

ws_router = APIRouter(prefix="/ws", tags=["websocket"])

# ───────────── broadcast (all clients) ─────────────────────────
@ws_router.websocket("/broadcast")
async def websocket_broadcast(ws: WebSocket):
    await bus.connect("broadcast", ws)
    try:
        while True:
            await ws.receive_text()          # we don't expect data
    except WebSocketDisconnect:
        await bus.disconnect("broadcast", ws)

# ───────────── private per-user channel ────────────────────────
@ws_router.websocket("/user/{username}")
async def websocket_user(ws: WebSocket, username: str):
    group = f"user:{username}"
    await bus.connect(group, ws)
    try:
        while True:
            await asyncio.sleep(60)  # keep the loop alive passively
    except WebSocketDisconnect:
        await bus.disconnect(group, ws)
