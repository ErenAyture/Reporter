import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
from config import settings

_executor = ThreadPoolExecutor(max_workers=2)

def notify_ws(group: str, msg_type: str, payload: dict):
    """
    Fire-and-forget WebSocket notify using async httpx in a background thread.
    Can be safely called from synchronous code.
    """
    async def _send():
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{settings.BASE_URL}/notify", json={
                    "group": group,
                    "type": msg_type,
                    "payload": payload,
                })
                res.raise_for_status()
        except Exception as e:
            print(f"[WS Notify] async post failed: {e}")

    def _run_async():
        asyncio.run(_send())

    _executor.submit(_run_async)
