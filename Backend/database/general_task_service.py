"""database/general_task_service.py – generic task listing
----------------------------------------------------------------
Converts TaskGroup + TaskItem ORM rows to lightweight Pydantic DTOs
so that our FastAPI handler can safely return them **after** the DB
session is gone (no more lazy‑loads, thus no `MissingGreenlet`).

Only read‑access is required – nothing here writes to the database.
"""

from datetime import datetime, date
from typing import Any, Dict, List, Sequence
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select,delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_polymorphic

from database.result_archiver import ResultArchiver
from database.status import GroupStatus, ItemStatus
from database.db import NotFoundError
from database.models_tasks import TaskGroup, TaskItem  # *all* subclasses are imported via with_polymorphic
from database.models_tasks import SSVTask

from infrustructure.ws_bus import bus
# ────────────────────────────────────────────────────────────────
# 1.  Pydantic DTOs – completely decoupled from the ORM
# ────────────────────────────────────────────────────────────────
class TaskItemOut(BaseModel):
    """Generic projection of one item.

    * **data** is unconstrained → it may hold whatever the concrete
      subclass defines (SSV, KPI‑export, …).  Keep it simple: just
      a flat dict that the frontend can pattern‑match on *type*.
    """

    id: int
    status: ItemStatus
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class TaskGroupOut(BaseModel):
    group_id: int = Field(..., alias="id")
    created_at: datetime
    type: str                      # polymorphic discriminator, e.g. "ssv"
    status: GroupStatus
    items: List[TaskItemOut]

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ────────────────────────────────────────────────────────────────
# 2.  Helpers – safe Enum conversion & DTO mapping
# ────────────────────────────────────────────────────────────────
_STATUS_MAP_ITEM = {
    "success": ItemStatus.OK,
    "ok": ItemStatus.OK,
    "pending": ItemStatus.QUEUED,
    "queued": ItemStatus.QUEUED,
    "running": ItemStatus.RUNNING,
    "error": ItemStatus.ERROR,
    "failed": ItemStatus.ERROR,
}

_STATUS_MAP_GROUP = {
    "done": GroupStatus.DONE,
    "running": GroupStatus.RUNNING,
    "queued": GroupStatus.QUEUED,
    "error": GroupStatus.ERROR,
}


def _item_status(raw: str) -> ItemStatus:
    raw_lc = (raw or "").lower()
    return _STATUS_MAP_ITEM.get(raw_lc, ItemStatus.ERROR)


def _group_status(raw: str) -> GroupStatus:
    raw_lc = (raw or "").lower()
    return _STATUS_MAP_GROUP.get(raw_lc, GroupStatus.ERROR)


def _item_to_dto(row: TaskItem) -> TaskItemOut:
    """Convert *one* ORM TaskItem row to its DTO counterpart without
    triggering **any** further lazy DB access (→ greenlet‑safe).
    """

    data: Dict[str, Any]

    match row.type:
        # ── 2.1  SSV site measurements ───────────────────────
        case "ssv":
            data = {
                "site_id": row.__dict__.get("site_id"),
                "date": row.__dict__.get("site_date"),
                "tech": row.__dict__.get("tech"),
            }
        # ── 2.2  KPI export jobs (example – extend as needed) ─
        case "kpi_export":
            data = {
                "report": row.__dict__.get("report"),
                "period": row.__dict__.get("period"),
            }
        # ── 2.3  Coverage scans (example) ─────────────────────
        case "coverage_scan":
            data = {
                "cell_ids": row.__dict__.get("cell_ids"),
                "raster": row.__dict__.get("raster"),
            }
        # ── 2.4  Unknown → just echo JSON payload column ──────
        case _:
            data = row.__dict__.get("payload", {}) or {}

    return TaskItemOut(
        id=row.id,
        status=_item_status(row.status),
        data=data,
    )


def _group_to_dto(grp: TaskGroup) -> TaskGroupOut:
    child_types = {i.type for i in grp.items}
    grp_type = child_types.pop() if len(child_types) == 1 else "mixed"
    return TaskGroupOut(
        id=grp.id,
        created_at=grp.created_at,
        type=grp_type,                       # NEW field
        status=_group_status(grp.status),
        items=[_item_to_dto(i) for i in grp.items],
    )


# ────────────────────────────────────────────────────────────────
# 3.  Public service function – one single DB round‑trip
# ────────────────────────────────────────────────────────────────
async def groups_with_items(
    db: AsyncSession, *, username: str | None = None
) -> List[TaskGroupOut]:
    """Return **fully‑materialised** task groups (with children) so that the
    caller can safely close the session afterwards.
    """

    # load *all* concrete subclasses in one SELECT + one SELECT‑IN load
    item_poly = with_polymorphic(TaskItem, "*")

    stmt = (
        select(TaskGroup)
        .options(selectinload(TaskGroup.items.of_type(item_poly)))
        .order_by(TaskGroup.created_at.desc())
    )
    if username:
        stmt = stmt.where(TaskGroup.username == username)

    res = await db.execute(stmt)
    groups_orm = res.scalars().unique().all()

    if not groups_orm:
        raise NotFoundError(f"No task groups for user: {username}")

    # immediately translate – _NO_ ORM objects leave this function!
    return [_group_to_dto(g) for g in groups_orm]

# ────────────────────────────────────────────────────────────────
# running queued task statuses
# ────────────────────────────────────────────────────────────────

# ── Pydantic DTO for the new endpoint ────────────────────────────────
class TaskGroupSummary(BaseModel):
    group_id   : int              = Field(..., alias="id")
    created_at : datetime
    status     : GroupStatus
    type       : str | None       = Field(None, alias="task_type")  # 👈 here!

    model_config = ConfigDict(
        from_attributes   = True,   # read from SQLAlchemy object
        populate_by_name  = True,   # but output key is "type"
    )


# ── Service function --------------------------------------------------
ACTIVE_STATES = (GroupStatus.QUEUED, GroupStatus.RUNNING)

async def active_group_summaries(
    db: AsyncSession,
) -> List[TaskGroupSummary]:
    """
    Return only QUEUED + RUNNING task-groups, *without* loading children.

    Result: List[TaskGroupSummary] ordered newest-first.
    """

    subq_type = (
    select(TaskItem.type)
    .where(TaskItem.group_id == TaskGroup.id)
    .limit(1)
    .scalar_subquery()
)
    stmt = (
        select(
            TaskGroup.id,
            TaskGroup.created_at,
            TaskGroup.status,
            subq_type.label("type")          # or ".label('task_type')" if you kept the old name
        )
        .where(TaskGroup.status.in_(ACTIVE_STATES))
        .order_by(TaskGroup.created_at.desc())
    )

    res = await db.execute(stmt)

    # each row is just a RowMapping (dict-like) – feed it straight into Pydantic
    return [TaskGroupSummary.model_validate(r._mapping) for r in res]


async def get_group_or_404(db: AsyncSession, gid: int) -> TaskGroup:
    grp = await db.get(TaskGroup, gid)
    if grp is None:
        raise NotFoundError( f"group {gid} not found")
    return grp


async def delete_group_and_data(db: AsyncSession, gid: int) -> None:
    """
    Drop *all* artefacts that belong to a TaskGroup:
    - subtype rows  (ssv_task_items, kpi_export_items, …)
    - generic TaskItem rows
    - TaskGroup itself
    - result archive on disk
    """
    # 1) kill subtype rows first ───────────────────────────────────────────
    await db.execute(
        delete(SSVTask).where(
            SSVTask.id.in_(select(TaskItem.id)
                               .where(TaskItem.group_id == gid))
        )
    )

    # 2) generic TaskItems --------------------------------------------------
    await db.execute(delete(TaskItem).where(TaskItem.group_id == gid))

    # 3) TaskGroup ----------------------------------------------------------
    await db.execute(delete(TaskGroup).where(TaskGroup.id == gid))

    # 4) phys. archive file -------------------------------------------------
    try:
        archiver = ResultArchiver()
        archiver.remove_archive(group_id=gid)
    except FileNotFoundError:
        pass

    # 5) one single commit
    await db.commit()


async def ensure_group_archive(db: AsyncSession, gid: int) -> Path:
    """Return <results>/<gid>.zip – create it from outputs/ if necessary."""
    archiver = ResultArchiver()
    await get_group_or_404(db, gid)      # 404 if no such group

    zip_path = archiver.results_dir / f"{gid}.zip"
    if zip_path.exists():
        return zip_path

    # try to build it from raw outputs; raise if nothing to archive
    created = archiver.archive_group(gid)
    if created is None:
        raise NotFoundError(f"no artefacts f0or group {gid}")
    return created
