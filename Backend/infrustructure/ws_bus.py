# Backend/infrastructure/ws_bus.py
from __future__ import annotations
import asyncio, json, logging
from collections import defaultdict
from typing import Any, Dict, Set
from fastapi import WebSocket

log = logging.getLogger("ws_bus")


class _Bus:
    def __init__(self) -> None:
        self._subs: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._main_loop: asyncio.AbstractEventLoop | None = None

    # ------------------------------------------------------------------ #
    #  FastAPI UYGULAMASINDA  ->  app.add_event_handler("startup", bus.startup)
    async def startup(self) -> None:
        """Ana asyncio loop referansını sakla (yalnızca 1 kez çağır)."""
        self._main_loop = asyncio.get_event_loop()
        log.info("[ws_bus] main event-loop stored")

    # ------------------------------------------------------------------ #
    async def connect(self, topic: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._subs[topic].add(ws)
        log.info("WS connected topic=%s   now=%d", topic, len(self._subs[topic]))

    async def disconnect(self, topic: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[topic].discard(ws)
        print(f'WS disconnected topic={topic}   now={len(self._subs[topic])}')
        log.info("WS disconnected topic=%s   now=%d", topic, len(self._subs[topic]))

    # ------------------------------------------------------------------ #
    async def _emit(self, topic: str, payload: str) -> None:
        print(f"📤 Emitting to 1")

        async with self._lock:
            conns: Set[WebSocket] = set(self._subs.get(topic, ()))
        if not conns:
            return

        dead: Set[WebSocket] = set()
        print(f"📤 Emitting to 2")
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.add(ws)
        print(f"📤 Emitting to 3")
        if dead:
            async with self._lock:
                for d in dead:
                    self._subs[topic].discard(d)

    # ------------------------------------------------------------------ #
    def emit_threadsafe(self, topic: str, event: str, data: Dict[str, Any]) -> None:
        """
        Her yerden (özellikle Celery thread-leri) güvenle çağrılabilir.
        """
        if self._main_loop is None:
            # Uygulama daha startup aşamasında mı?  Sessizce yoksay.
            log.warning("emit_threadsafe called before startup; dropping msg.")
            return

        payload = json.dumps({"event": event, "data": data})
        self._main_loop.call_soon_threadsafe(
            asyncio.create_task, self._emit(topic, payload)
        )


bus = _Bus()
