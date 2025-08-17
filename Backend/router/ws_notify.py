from fastapi import APIRouter
from pydantic import BaseModel
from infrustructure.ws_bus import bus  # typo fixed from "infrustructure"
from concurrent.futures import ThreadPoolExecutor


router = APIRouter()

class NotifyMsg(BaseModel):
    group: str
    type: str
    payload: dict

@router.post("/notify")
async def notify_ws(msg: NotifyMsg):
    await bus._emit(msg.group, {
        "type": msg.type,
        **msg.payload
    })
    return {"status": "ok"}
