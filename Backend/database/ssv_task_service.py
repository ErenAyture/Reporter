# BACKEND/database/task_service.py
"""
Async helpers  → used by FastAPI routes
Sync  helpers  → used by Celery worker threads
"""
from __future__ import annotations
from typing import NamedTuple
from infrustructure.notifier import notify_ws

from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import case, func, select
from sqlalchemy.orm import selectinload

from database.db import async_session, SessionLocal            # ← BOTH stacks
from database.models_tasks import TaskGroup, TaskItem, SSVTask
from database.status import ItemStatus, GroupStatus

from infrustructure.ws_bus import bus
from .result_archiver import ResultArchiver
from tasks.mutex_lock import lock 

# ──────────────────────────────────────────────────────────
#  ASYNC PART  (FastAPI)
# ──────────────────────────────────────────────────────────
async def create_ssv_batch(
    username: str, sites: list[dict], db: AsyncSession
) -> TaskGroup:
    """
    *sites* = list of {"site_id": "...", "date": "...", "tech": "..."}
    """
    group = TaskGroup(username=username, status="queued")
    db.add(group)
    await db.flush()  # assign group.id

    tasks = [
        SSVTask(
            group_id=group.id,
            site_id=site["site_id"],
            site_date=site["date"],
            tech=site.get("tech", "LTE"),
        )
        for site in sites
    ]
    db.add_all(tasks)
    await db.commit()

    # reload group with its items
    stmt = select(TaskGroup).options(selectinload(TaskGroup.items)).where(TaskGroup.id == group.id)
    result = await db.execute(stmt)
    group = result.scalar_one()

    # notify WebSocket clients
    payload = {
        "group_id": group.id,
        "status": group.status.lower(),
        "data": [
            {
                "id": item.id,
                "site_id": item.site_id,
                "status": item.status.lower(),
                "tech": item.tech,
                "site_date": item.site_date.isoformat(),
            }
            for item in group.items
        ],
    }

    notify_ws("broadcast", "task_group_added", {
        "group_id": group.id,
        "status": group.status.lower(),
    })
    notify_ws(f"user:{username}", "task_group_added", payload)

    return group


async def mark_started(item_id: int, celery_uuid: str, db: AsyncSession) -> None:
    item: TaskItem = db.get(TaskItem, item_id)
    item.status = "STARTED"
    item.started_at = datetime.now(timezone.utc)
    item.celery_uuid = celery_uuid
    db.commit()


async def mark_done(
    item_id: int, db: AsyncSession, ok: bool, result: str | None
) -> None:
    item: TaskItem = db.get(TaskItem, item_id)
    item.status = "SUCCESS" if ok else "FAILURE"
    item.finished_at = datetime.now(timezone.utc)
    item.payload["result"] = result
    db.commit()



# ──────────────────────────────────────────────────────────
#  SYNC PART  (Celery – thread or prefork pool)
# ──────────────────────────────────────────────────────────
@contextmanager
def session_scope() -> Session:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()                    # ← **sync** engine
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _recalc_group_status(db: Session, group_id: int) -> None:
    """
    Re-evaluate a group *after* one child finishes.
    Emits websocket events **only when** the parent status changes.
    """
    totals_q = (
        select(
            func.count().label("total"),
            func.sum(case((TaskItem.status == ItemStatus.OK, 1), else_=0)).label("ok"),
            func.sum(case((TaskItem.status == ItemStatus.ERROR, 1), else_=0)).label("err"),
        ).where(TaskItem.group_id == group_id)
    )

    total, ok_cnt, err_cnt = db.execute(totals_q).one()
    finished = total > 0 and (ok_cnt + err_cnt) == total

    grp: TaskGroup | None = db.get(TaskGroup, group_id)
    if grp is None:
        return

    previous = grp.status

    if finished:
        if ok_cnt:
            grp.status = GroupStatus.DONE
            if previous != GroupStatus.DONE:           # first time → create zip
                    ResultArchiver().archive_group(group_id)
        else:
            grp.status = GroupStatus.ERROR
    else:
        grp.status = GroupStatus.RUNNING
        print("running")
        notify_ws("broadcast", "task_group_status", {"group_id": grp.id, "status": grp.status.lower()})
        notify_ws(f"user:{grp.username}", "task_group_status", {"group_id": grp.id, "status": grp.status.lower()})
            # notify_ws("broadcast", "task_group_status", {...})
    if grp.status != previous:                         # 🔔 broadcast once
        new_stat = grp.status.lower()
        print("abc")
        notify_ws("broadcast", "task_group_status", {"group_id": grp.id, "status": new_stat})
        notify_ws(f"user:{grp.username}", "task_group_status", {"group_id": grp.id, "status": new_stat})


# ────────────────────────────────────────────────────────────────
def mark_started_sync(item_id: int, celery_uuid: str) -> None:
    """Called *inside the Celery thread-pool* when an item really starts."""
    with session_scope() as db:
        item: TaskItem | None = db.get(TaskItem, item_id)
        if not item:
            return

        item.status = ItemStatus.RUNNING
        item.celery_uuid = celery_uuid

        grp: TaskGroup = db.get(TaskGroup, item.group_id)
        if grp.status != GroupStatus.RUNNING:
            grp.status = GroupStatus.RUNNING

        db.flush()  # push changes before we emit

        # ── websocket events ────────────────────────────────────
        notify_ws("broadcast", "task_item_started", {
            "item_id": item.id,
            "status": item.status
        })
        notify_ws(f"user:{grp.username}", "task_item_started", {
            "item_id": item.id,
            "status": item.status
        })
        with lock:
            _recalc_group_status(db, grp.id)



# ────────────────────────────────────────────────────────────────
def mark_done_sync(item_id: int, ok: bool, result: str) -> None:
    """Called from the Celery worker thread after the script finishes."""
    with session_scope() as db:
        item: TaskItem | None = db.get(TaskItem, item_id)
        if not item:
            return

        item.status = ItemStatus.OK if ok else ItemStatus.ERROR
        item.result = result

        db.flush()

        status_str = item.status.lower()

        # ── websocket events for the *item* ─────────────────────
        grp: TaskGroup = db.get(TaskGroup, item.group_id)
        print(status_str)
        notify_ws("broadcast", "task_item_finished", {"item_id": item.id, "status": status_str})
        notify_ws(f"user:{grp.username}", "task_item_finished", {"item_id": item.id, "status": status_str})
        # ── update / broadcast the *group* if needed ────────────
        with lock:
            _recalc_group_status(db, grp.id)

class SSVArgs(NamedTuple):
    group_id: int
    site_id: str
    date:    str     # or datetime.date if you store it as DATE
    tech:    str

def get_ssv_args_sync(item_id: int) -> SSVArgs:
    """
    Quick read-only fetch of the parameters the worker needs.
    Called from a Celery *sync* context.
    """
    with session_scope() as db:               # ← same sync session helper
        item: SSVTask = db.get(SSVTask, item_id)
        return SSVArgs(item.group_id, item.site_id, item.site_date, item.tech)
    
