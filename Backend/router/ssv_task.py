# BACKEND/router/ssv_runner.py
from datetime import date as dt
from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.db import async_session,get_db
from database.ssv_task_service import create_ssv_batch
from database.models_tasks import TaskGroup, TaskItem
from tasks.ssv_worker import process_one_item   # Celery task



router = APIRouter(prefix="/ssv_task", tags=["SSV Runner"])

# ──────────────── Pydantic request/response ─────────────────
class SiteIn(BaseModel):
    site_id: str = Field(..., examples=["TR-456"])
    date: dt   = Field(..., examples=["2025-06-18"])
    tech: str | None = Field(None, examples=["LTE"])

class BatchIn(BaseModel):
    username: str
    sites: List[SiteIn]

class BatchOut(BaseModel):
    group_id: int
    item_ids: List[int]
    percent_done: float



# ──────────────── POST /ssv/run ─────────────────────────────
@router.post(
    "/run",
    response_model=BatchOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create an SSV batch and queue Celery jobs",
)
async def run_batch(payload: BatchIn, db: AsyncSession = Depends(get_db)):
    # 1)  create TaskGroup + TaskItem rows
    print("📥 /ssv_task/run endpoint triggered")

    group = await create_ssv_batch(
        payload.username,
        [s.model_dump() for s in payload.sites],
        db,
    )
    print("A")
    # 2)  one Celery job per TaskItem
    for item in group.items:
        process_one_item.delay(item.id)
    print("B")
    return BatchOut(
        group_id=group.id,
        item_ids=[i.id for i in group.items],
        percent_done=group.percent_done,
    )

# ──────────────── GET /task-groups/{id} ─────────────────────
@router.get(
    "/group/{group_id}",
    response_model=BatchOut,
    summary="Check batch progress",
)
async def batch_status(group_id: int, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(TaskGroup).where(TaskGroup.id == group_id))
    group = q.scalar_one_or_none()
    if not group:
        raise HTTPException(404, detail="Group not found")
    return BatchOut(
        group_id=group.id,
        item_ids=[i.id for i in group.items],
        percent_done=group.percent_done,
    )
